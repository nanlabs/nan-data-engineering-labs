"""
Silver to Gold Layer ETL Job
Creates aggregated, business-ready tables from silver layer.
Implements star schema with fact and dimension tables,
daily metrics, running totals, and window functions.

Features: Aggregations, star schema, fact/dimension tables,
window functions, optimized Delta Lake with partitioning.
"""

import sys
import logging
from typing import Dict, List

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import (
    col, current_timestamp, lit, sum as spark_sum, count,
    avg, max as spark_max, min as spark_min, stddev,
    lag, to_date, year, month, dayofmonth, weekofyear,
    quarter, dayofweek, last_day, date_add, datediff,
    monotonically_increasing_id,
    countDistinct, when
)
from pyspark.sql.types import TimestampType

from common.spark_utils import (
    create_spark_session, write_to_delta, optimize_table,
    send_notification, write_metadata_to_dynamodb,
    error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AggregationBuilder:
    """Builds various types of aggregations."""

    @staticmethod
    def create_daily_metrics(
        df: DataFrame,
        date_column: str,
        group_columns: List[str],
        metric_columns: Dict[str, List[str]]
    ) -> DataFrame:
        """
        Create daily aggregated metrics.

        Args:
            df: Source DataFrame
            date_column: Column containing dates
            group_columns: Columns to group by
            metric_columns: Dict of {metric_type: [columns]} where metric_type is
                          'sum', 'avg', 'count', 'min', 'max', 'stddev'

        Returns:
            DataFrame with daily metrics
        """
        logger.info("Creating daily metrics")

        # Extract date components
        df = df.withColumn("metric_date", to_date(col(date_column)))

        group_cols = ["metric_date"] + group_columns

        # Build aggregation expressions
        agg_exprs = []

        for metric_type, columns in metric_columns.items():
            for col_name in columns:
                if metric_type == 'sum':
                    agg_exprs.append(spark_sum(col(col_name)).alias(f"{col_name}_sum"))
                elif metric_type == 'avg':
                    agg_exprs.append(avg(col(col_name)).alias(f"{col_name}_avg"))
                elif metric_type == 'count':
                    agg_exprs.append(count(col(col_name)).alias(f"{col_name}_count"))
                elif metric_type == 'min':
                    agg_exprs.append(spark_min(col(col_name)).alias(f"{col_name}_min"))
                elif metric_type == 'max':
                    agg_exprs.append(spark_max(col(col_name)).alias(f"{col_name}_max"))
                elif metric_type == 'stddev':
                    agg_exprs.append(stddev(col(col_name)).alias(f"{col_name}_stddev"))
                elif metric_type == 'distinct':
                    agg_exprs.append(countDistinct(col(col_name)).alias(f"{col_name}_distinct"))

        # Perform aggregation
        df_daily = df.groupBy(*group_cols).agg(*agg_exprs)

        logger.info(f"Created daily metrics with {df_daily.count():,} rows")
        return df_daily

    @staticmethod
    def calculate_running_totals(
        df: DataFrame,
        partition_columns: List[str],
        order_column: str,
        value_columns: List[str]
    ) -> DataFrame:
        """
        Calculate running totals using window functions.

        Args:
            df: Source DataFrame
            partition_columns: Columns to partition by
            order_column: Column to order by
            value_columns: Columns to calculate running totals for

        Returns:
            DataFrame with running total columns
        """
        logger.info("Calculating running totals")

        window_spec = Window.partitionBy(*partition_columns).orderBy(col(order_column))

        for col_name in value_columns:
            df = df.withColumn(
                f"{col_name}_running_total",
                spark_sum(col(col_name)).over(window_spec)
            )

            df = df.withColumn(
                f"{col_name}_running_avg",
                avg(col(col_name)).over(window_spec)
            )

        return df

    @staticmethod
    def calculate_period_over_period(
        df: DataFrame,
        partition_columns: List[str],
        order_column: str,
        value_columns: List[str],
        periods: int = 1
    ) -> DataFrame:
        """
        Calculate period-over-period changes.

        Args:
            df: Source DataFrame
            partition_columns: Columns to partition by
            order_column: Column to order by (usually date)
            value_columns: Columns to calculate changes for
            periods: Number of periods to look back

        Returns:
            DataFrame with period-over-period columns
        """
        logger.info(f"Calculating period-over-period metrics ({periods} periods)")

        window_spec = Window.partitionBy(*partition_columns).orderBy(col(order_column))

        for col_name in value_columns:
            # Get previous period value
            df = df.withColumn(
                f"{col_name}_prev_{periods}",
                lag(col(col_name), periods).over(window_spec)
            )

            # Calculate absolute change
            df = df.withColumn(
                f"{col_name}_change",
                col(col_name) - col(f"{col_name}_prev_{periods}")
            )

            # Calculate percentage change
            df = df.withColumn(
                f"{col_name}_pct_change",
                when(col(f"{col_name}_prev_{periods}") != 0,
                     ((col(col_name) - col(f"{col_name}_prev_{periods}")) /
                      col(f"{col_name}_prev_{periods}") * 100)
                ).otherwise(None)
            )

        return df

    @staticmethod
    def calculate_moving_averages(
        df: DataFrame,
        partition_columns: List[str],
        order_column: str,
        value_columns: List[str],
        window_sizes: List[int] = [7, 30, 90]
    ) -> DataFrame:
        """
        Calculate moving averages for different window sizes.

        Args:
            df: Source DataFrame
            partition_columns: Columns to partition by
            order_column: Column to order by
            value_columns: Columns to calculate moving averages for
            window_sizes: List of window sizes (e.g., [7, 30, 90] for 7-day, 30-day, 90-day)

        Returns:
            DataFrame with moving average columns
        """
        logger.info(f"Calculating moving averages for windows: {window_sizes}")

        for window_size in window_sizes:
            window_spec = Window.partitionBy(*partition_columns).orderBy(
                col(order_column)
            ).rowsBetween(-window_size + 1, 0)

            for col_name in value_columns:
                df = df.withColumn(
                    f"{col_name}_ma_{window_size}",
                    avg(col(col_name)).over(window_spec)
                )

        return df


class StarSchemaBuilder:
    """Builds star schema with fact and dimension tables."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def create_dimension_customer(
        self,
        df: DataFrame,
        key_column: str = "customer_id"
    ) -> DataFrame:
        """
        Create customer dimension table.

        Args:
            df: Source DataFrame with customer data
            key_column: Business key column

        Returns:
            Customer dimension DataFrame
        """
        logger.info("Creating customer dimension")

        # Select distinct customers with their attributes
        dim_cols = [
            key_column,
            "customer_name",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "customer_segment",
            "registration_date",
            "status"
        ]

        # Filter to columns that exist
        available_cols = [c for c in dim_cols if c in df.columns]

        dim_customer = df.select(*available_cols).distinct()

        # Add surrogate key
        dim_customer = dim_customer.withColumn(
            "customer_sk",
            monotonically_increasing_id()
        )

        # Add SCD Type 2 columns
        dim_customer = dim_customer.withColumn("effective_date", current_timestamp())
        dim_customer = dim_customer.withColumn("end_date", lit(None).cast(TimestampType()))
        dim_customer = dim_customer.withColumn("is_current", lit(True))

        # Add metadata
        dim_customer = dim_customer.withColumn("created_timestamp", current_timestamp())
        dim_customer = dim_customer.withColumn("updated_timestamp", current_timestamp())

        logger.info(f"Created customer dimension with {dim_customer.count():,} rows")
        return dim_customer

    def create_dimension_product(
        self,
        df: DataFrame,
        key_column: str = "product_id"
    ) -> DataFrame:
        """
        Create product dimension table.

        Args:
            df: Source DataFrame with product data
            key_column: Business key column

        Returns:
            Product dimension DataFrame
        """
        logger.info("Creating product dimension")

        dim_cols = [
            key_column,
            "product_name",
            "product_category",
            "product_subcategory",
            "brand",
            "supplier",
            "unit_price",
            "cost",
            "status"
        ]

        available_cols = [c for c in dim_cols if c in df.columns]

        dim_product = df.select(*available_cols).distinct()

        # Add surrogate key
        dim_product = dim_product.withColumn(
            "product_sk",
            monotonically_increasing_id()
        )

        # Calculate margin
        if 'unit_price' in dim_product.columns and 'cost' in dim_product.columns:
            dim_product = dim_product.withColumn(
                "margin",
                (col("unit_price") - col("cost")) / col("unit_price") * 100
            )

        # Add metadata
        dim_product = dim_product.withColumn("created_timestamp", current_timestamp())
        dim_product = dim_product.withColumn("updated_timestamp", current_timestamp())

        logger.info(f"Created product dimension with {dim_product.count():,} rows")
        return dim_product

    def create_dimension_date(
        self,
        start_date: str,
        end_date: str
    ) -> DataFrame:
        """
        Create date dimension table.

        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format

        Returns:
            Date dimension DataFrame
        """
        logger.info(f"Creating date dimension from {start_date} to {end_date}")

        # Calculate number of days
        from datetime import datetime as dt
        start = dt.strptime(start_date, '%Y-%m-%d')
        end = dt.strptime(end_date, '%Y-%m-%d')
        num_days = (end - start).days + 1

        # Create date range
        dates_df = self.spark.range(num_days).select(
            date_add(lit(start_date), col("id")).alias("date")
        )

        # Add date components
        dim_date = dates_df.select(
            col("date"),
            year(col("date")).alias("year"),
            quarter(col("date")).alias("quarter"),
            month(col("date")).alias("month"),
            weekofyear(col("date")).alias("week_of_year"),
            dayofmonth(col("date")).alias("day_of_month"),
            dayofweek(col("date")).alias("day_of_week"),
            when(col("day_of_week").isin([1, 7]), "Weekend").otherwise("Weekday").alias("day_type"),
            last_day(col("date")).alias("last_day_of_month")
        )

        # Add fiscal year (assuming fiscal year starts in April)
        dim_date = dim_date.withColumn(
            "fiscal_year",
            when(col("month") >= 4, col("year")).otherwise(col("year") - 1)
        )

        # Add surrogate key
        dim_date = dim_date.withColumn(
            "date_sk",
            monotonically_increasing_id()
        )

        logger.info(f"Created date dimension with {dim_date.count():,} rows")
        return dim_date

    def create_fact_transactions(
        self,
        df: DataFrame,
        dim_customer: DataFrame,
        dim_product: DataFrame,
        dim_date: DataFrame
    ) -> DataFrame:
        """
        Create transaction fact table.

        Args:
            df: Source transaction data
            dim_customer: Customer dimension
            dim_product: Product dimension
            dim_date: Date dimension

        Returns:
            Transaction fact DataFrame
        """
        logger.info("Creating transaction fact table")

        # Convert transaction_date to date if needed
        if "transaction_date" in df.columns:
            df = df.withColumn("transaction_date", to_date(col("transaction_date")))

        # Join with customer dimension to get surrogate key
        fact = df.join(
            dim_customer.select("customer_id", "customer_sk"),
            "customer_id",
            "left"
        )

        # Join with product dimension
        fact = fact.join(
            dim_product.select("product_id", "product_sk"),
            "product_id",
            "left"
        )

        # Join with date dimension
        fact = fact.join(
            dim_date.select("date", "date_sk"),
            fact["transaction_date"] == dim_date["date"],
            "left"
        ).drop("date")

        # Select fact columns
        fact_cols = [
            "customer_sk",
            "product_sk",
            "date_sk",
            "transaction_id",
            "quantity",
            "unit_price",
            "total_amount",
            "discount_amount",
            "net_amount",
            "cost",
            "transaction_date",
            "transaction_timestamp"
        ]

        available_cols = [c for c in fact_cols if c in fact.columns]
        fact = fact.select(*available_cols)

        # Calculate derived metrics
        if "net_amount" in fact.columns and "cost" in fact.columns:
            fact = fact.withColumn(
                "profit",
                col("net_amount") - (col("cost") * col("quantity"))
            )
            fact = fact.withColumn(
                "profit_margin",
                (col("profit") / col("net_amount")) * 100
            )

        # Add fact surrogate key
        fact = fact.withColumn(
            "transaction_sk",
            monotonically_increasing_id()
        )

        # Add metadata
        fact = fact.withColumn("created_timestamp", current_timestamp())

        logger.info(f"Created transaction fact table with {fact.count():,} rows")
        return fact


class MetricsCalculator:
    """Calculates business metrics and KPIs."""

    @staticmethod
    def calculate_customer_lifetime_value(
        transactions_df: DataFrame,
        customer_column: str = "customer_id",
        amount_column: str = "net_amount",
        date_column: str = "transaction_date"
    ) -> DataFrame:
        """
        Calculate customer lifetime value (CLV).

        Args:
            transactions_df: Transaction data
            customer_column: Customer identifier column
            amount_column: Transaction amount column
            date_column: Transaction date column

        Returns:
            DataFrame with CLV metrics per customer
        """
        logger.info("Calculating customer lifetime value")

        clv_df = transactions_df.groupBy(customer_column).agg(
            spark_sum(amount_column).alias("total_revenue"),
            count("*").alias("transaction_count"),
            avg(amount_column).alias("avg_transaction_value"),
            spark_min(date_column).alias("first_transaction_date"),
            spark_max(date_column).alias("last_transaction_date")
        )

        # Calculate customer tenure in days
        clv_df = clv_df.withColumn(
            "customer_tenure_days",
            datediff(col("last_transaction_date"), col("first_transaction_date"))
        )

        # Calculate average order frequency
        clv_df = clv_df.withColumn(
            "avg_order_frequency",
            when(col("customer_tenure_days") > 0,
                 col("transaction_count") / (col("customer_tenure_days") / 365.0)
            ).otherwise(col("transaction_count"))
        )

        # Simple CLV calculation
        clv_df = clv_df.withColumn(
            "customer_lifetime_value",
            col("avg_transaction_value") * col("avg_order_frequency") * 3  # 3 year projection
        )

        return clv_df

    @staticmethod
    def calculate_product_performance(
        transactions_df: DataFrame,
        product_column: str = "product_id"
    ) -> DataFrame:
        """Calculate product performance metrics."""
        logger.info("Calculating product performance metrics")

        performance_df = transactions_df.groupBy(product_column).agg(
            spark_sum("quantity").alias("total_quantity_sold"),
            spark_sum("net_amount").alias("total_revenue"),
            spark_sum("profit").alias("total_profit"),
            count("*").alias("transaction_count"),
            avg("net_amount").alias("avg_transaction_value"),
            countDistinct("customer_id").alias("unique_customers")
        )

        # Calculate metrics
        performance_df = performance_df.withColumn(
            "avg_profit_per_unit",
            col("total_profit") / col("total_quantity_sold")
        )

        performance_df = performance_df.withColumn(
            "revenue_per_customer",
            col("total_revenue") / col("unique_customers")
        )

        return performance_df


@error_handler(notify_on_error=True)
def main():
    """Main ETL job for silver to gold layer."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'silver_bucket',
        'gold_bucket',
        'source_table',
        'metadata_table',
        'sns_topic_arn'
    ])

    job_name = args['JOB_NAME']
    silver_bucket = args['silver_bucket']
    gold_bucket = args['gold_bucket']
    source_table = args['source_table']
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']

    logger.info(f"Starting {job_name}")

    # Create Spark session
    spark = create_spark_session(
        app_name=job_name,
        additional_configs={
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true"
        }
    )

    try:
        # Read data from silver layer
        silver_path = f"s3://{silver_bucket}/silver/{source_table}"
        df_silver = spark.read.format("delta").load(silver_path)

        # Filter only current records
        df_silver = df_silver.filter(col("is_current") == True)

        logger.info(f"Read {df_silver.count():,} records from silver layer")

        # Initialize builders
        agg_builder = AggregationBuilder()
        star_schema_builder = StarSchemaBuilder(spark)
        metrics_calculator = MetricsCalculator()

        # Create dimension tables
        dim_customer = star_schema_builder.create_dimension_customer(df_silver)
        dim_product = star_schema_builder.create_dimension_product(df_silver)

        # Create date dimension for last 5 years
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=5*365)
        dim_date = star_schema_builder.create_dimension_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # Write dimension tables
        gold_path_base = f"s3://{gold_bucket}/gold"

        write_to_delta(
            dim_customer,
            f"{gold_path_base}/dim_customer",
            mode="overwrite",
            optimize_write=True
        )

        write_to_delta(
            dim_product,
            f"{gold_path_base}/dim_product",
            mode="overwrite",
            optimize_write=True
        )

        write_to_delta(
            dim_date,
            f"{gold_path_base}/dim_date",
            mode="overwrite",
            partition_cols=["year", "month"],
            optimize_write=True
        )

        # Create fact table
        fact_transactions = star_schema_builder.create_fact_transactions(
            df_silver,
            dim_customer,
            dim_product,
            dim_date
        )

        write_to_delta(
            fact_transactions,
            f"{gold_path_base}/fact_transactions",
            mode="append",
            partition_cols=["transaction_date"],
            optimize_write=True
        )

        # Create aggregated metrics tables
        if "transaction_date" in df_silver.columns:
            daily_metrics = agg_builder.create_daily_metrics(
                df_silver,
                date_column="transaction_date",
                group_columns=["customer_id", "product_id"],
                metric_columns={
                    'sum': ['quantity', 'net_amount'],
                    'avg': ['unit_price'],
                    'count': ['transaction_id'],
                    'distinct': ['customer_id']
                }
            )

            write_to_delta(
                daily_metrics,
                f"{gold_path_base}/daily_metrics",
                mode="overwrite",
                partition_cols=["metric_date"],
                optimize_write=True
            )

        # Optimize all gold tables
        for table in ['dim_customer', 'dim_product', 'dim_date', 'fact_transactions', 'daily_metrics']:
            table_path = f"{gold_path_base}/{table}"
            try:
                optimize_table(spark, table_path, vacuum_hours=168)
            except Exception as e:
                logger.warning(f"Could not optimize {table}: {str(e)}")

        # Collect statistics
        stats = {
            'dim_customer_count': dim_customer.count(),
            'dim_product_count': dim_product.count(),
            'dim_date_count': dim_date.count(),
            'fact_transactions_count': fact_transactions.count()
        }

        # Write metadata
        metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'source_path': silver_path,
            'target_path': gold_path_base,
            'statistics': str(stats),
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, metadata)

        # Send success notification
        send_notification(
            topic_arn=sns_topic_arn,
            subject=f"Gold Layer Load Success: {job_name}",
            message=f"Successfully created star schema and metrics\nStatistics: {stats}",
            attributes={'status': 'SUCCESS', 'job': job_name}
        )

        logger.info(f"Job {job_name} completed successfully")

    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
