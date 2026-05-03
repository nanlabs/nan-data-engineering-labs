"""
AWS Glue ETL Job: Silver to Gold - Customer 360
Creates comprehensive customer view by joining customers with orders and events
to calculate lifetime value, RFM scores, and customer segmentation.
"""

import sys
from datetime import datetime
import boto3
from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    col, current_timestamp, lit, count, sum as spark_sum, avg, min as spark_min,
    max as spark_max, countDistinct, when, datediff, round as spark_round, ntile, concat_ws
)
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

# Import shared utilities
sys.path.append('/home/hadoop/common')
from common.glue_utils import (
    GlueLogger, log_job_metrics, partition_dataframe
)


def get_job_parameters():
    """Extract job parameters from Glue arguments."""
    args = getResolvedOptions(
        sys.argv,
        [
            'JOB_NAME',
            'customers_database',
            'customers_table',
            'orders_database',
            'orders_table',
            'events_database',
            'events_table',
            'target_s3_path',
            'target_database',
            'target_table'
        ]
    )
    return args


def read_silver_customers(
    glue_context: GlueContext,
    database: str,
    table: str,
    logger: GlueLogger
) -> DataFrame:
    """Read processed customers from Silver layer."""
    logger.info(f"Reading Silver customers: {database}.{table}")

    try:
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_silver_customers"
        )

        df = dynamic_frame.toDF()
        logger.info("Successfully read Silver customers", row_count=df.count())
        return df

    except Exception as e:
        logger.error("Failed to read Silver customers", exception=e)
        raise


def read_silver_orders(
    glue_context: GlueContext,
    database: str,
    table: str,
    logger: GlueLogger
) -> DataFrame:
    """Read processed orders from Silver layer."""
    logger.info(f"Reading Silver orders: {database}.{table}")

    try:
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_silver_orders"
        )

        df = dynamic_frame.toDF()
        logger.info("Successfully read Silver orders", row_count=df.count())
        return df

    except Exception as e:
        logger.error("Failed to read Silver orders", exception=e)
        raise


def read_silver_events(
    glue_context: GlueContext,
    database: str,
    table: str,
    logger: GlueLogger
) -> DataFrame:
    """Read processed events from Silver layer."""
    logger.info(f"Reading Silver events: {database}.{table}")

    try:
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_silver_events"
        )

        df = dynamic_frame.toDF()
        logger.info("Successfully read Silver events", row_count=df.count())
        return df

    except Exception:
        logger.warning("Events table not available, continuing without event data")
        # Return empty DataFrame with expected schema
        schema = StructType([
            StructField("customer_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("event_timestamp", TimestampType(), True)
        ])
        return spark.createDataFrame([], schema)


def aggregate_order_metrics(df_orders: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Aggregate order metrics per customer.

    Args:
        df_orders: Orders DataFrame
        logger: Logger instance

    Returns:
        Aggregated order metrics by customer
    """
    logger.info("Aggregating order metrics per customer")

    df_order_agg = df_orders.groupBy('customer_id').agg(
        count('order_id').alias('total_orders'),
        spark_sum('total_amount').alias('total_spent'),
        avg('total_amount').alias('avg_order_value'),
        spark_min('order_date').alias('first_order_date'),
        spark_max('order_date').alias('last_order_date'),
        spark_sum('quantity').alias('total_items_purchased'),
        countDistinct('product_id').alias('unique_products_purchased')
    )

    # Round decimal values
    df_order_agg = df_order_agg \
        .withColumn('total_spent', spark_round(col('total_spent'), 2)) \
        .withColumn('avg_order_value', spark_round(col('avg_order_value'), 2))

    logger.info(
        "Order metrics aggregated",
        customers_with_orders=df_order_agg.count()
    )

    return df_order_agg


def aggregate_event_metrics(df_events: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Aggregate event metrics per customer.

    Args:
        df_events: Events DataFrame
        logger: Logger instance

    Returns:
        Aggregated event metrics by customer
    """
    logger.info("Aggregating event metrics per customer")

    if df_events.count() == 0:
        logger.warning("No event data available, returning empty metrics")
        # Return empty aggregation with schema
        return df_events.select(
            col('customer_id'),
            lit(0).alias('total_page_views'),
            lit(0).alias('total_clicks'),
            lit(None).cast(TimestampType()).alias('last_activity_date')
        ).limit(0)

    df_event_agg = df_events.groupBy('customer_id').agg(
        count(when(col('event_type') == 'page_view', 1)).alias('total_page_views'),
        count(when(col('event_type') == 'click', 1)).alias('total_clicks'),
        spark_max('event_timestamp').alias('last_activity_date')
    )

    logger.info(
        "Event metrics aggregated",
        customers_with_events=df_event_agg.count()
    )

    return df_event_agg


def join_customer_with_metrics(
    df_customers: DataFrame,
    df_order_metrics: DataFrame,
    df_event_metrics: DataFrame,
    logger: GlueLogger
) -> DataFrame:
    """
    Join customer base table with aggregated metrics.

    Args:
        df_customers: Base customer DataFrame
        df_order_metrics: Aggregated order metrics
        df_event_metrics: Aggregated event metrics
        logger: Logger instance

    Returns:
        Joined customer DataFrame with all metrics
    """
    logger.info("Joining customer data with order and event metrics")

    # Start with customers
    df_joined = df_customers.select(
        'customer_id',
        'first_name',
        'last_name',
        'email',
        'country',
        'city',
        'state',
        'signup_date',
        'account_status',
        'processing_timestamp'
    )

    # Left join with order metrics
    df_joined = df_joined.join(
        df_order_metrics,
        'customer_id',
        'left'
    )

    # Left join with event metrics (if available)
    if df_event_metrics.count() > 0:
        df_joined = df_joined.join(
            df_event_metrics,
            'customer_id',
            'left'
        )
    else:
        # Add empty event columns
        df_joined = df_joined \
            .withColumn('total_page_views', lit(0)) \
            .withColumn('total_clicks', lit(0)) \
            .withColumn('last_activity_date', lit(None).cast(TimestampType()))

    # Fill nulls for customers without orders
    df_joined = df_joined \
        .fillna(0, ['total_orders', 'total_spent', 'avg_order_value',
                   'total_items_purchased', 'unique_products_purchased',
                   'total_page_views', 'total_clicks'])

    logger.info(
        "Customer data joined",
        total_customers=df_joined.count()
    )

    return df_joined


def calculate_customer_lifetime_value(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Calculate customer lifetime value based on historical spending.

    Args:
        df: Customer DataFrame with order metrics
        logger: Logger instance

    Returns:
        DataFrame with CLV calculated
    """
    logger.info("Calculating customer lifetime value")

    # Simple CLV = total_spent + (avg_order_value * expected_future_orders)
    # For this example, we estimate 2 future orders per active customer
    df_with_clv = df.withColumn(
        'customer_lifetime_value',
        spark_round(
            col('total_spent') +
            when(col('total_orders') > 0, col('avg_order_value') * 2).otherwise(0),
            2
        )
    )

    logger.info("Customer lifetime value calculated")

    return df_with_clv


def calculate_recency_days(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Calculate days since last order (recency).

    Args:
        df: Customer DataFrame
        logger: Logger instance

    Returns:
        DataFrame with recency calculated
    """
    logger.info("Calculating recency (days since last order)")

    current_date = current_timestamp().cast('date')

    df_with_recency = df.withColumn(
        'days_since_last_order',
        when(
            col('last_order_date').isNotNull(),
            datediff(current_date, col('last_order_date'))
        ).otherwise(lit(None))
    )

    # Also calculate days since last activity
    df_with_recency = df_with_recency.withColumn(
        'days_since_last_activity',
        when(
            col('last_activity_date').isNotNull(),
            datediff(current_date, col('last_activity_date').cast('date'))
        ).otherwise(col('days_since_last_order'))
    )

    logger.info("Recency calculations completed")

    return df_with_recency


def calculate_rfm_score(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Calculate RFM (Recency, Frequency, Monetary) score for customer segmentation.

    Args:
        df: Customer DataFrame
        logger: Logger instance

    Returns:
        DataFrame with RFM scores
    """
    logger.info("Calculating RFM scores")

    # Define windows for percentile calculations
    window_spec = Window.orderBy(col('customer_id'))

    # Recency score (lower days is better, so we invert)
    # Divide customers into 5 quintiles
    df_rfm = df.withColumn(
        'recency_score',
        when(
            col('days_since_last_order').isNull(),
            lit(1)  # Lowest score for never ordered
        ).otherwise(
            6 - ntile(5).over(Window.orderBy(col('days_since_last_order').asc()))
        )
    )

    # Frequency score (more orders is better)
    df_rfm = df_rfm.withColumn(
        'frequency_score',
        when(
            col('total_orders') == 0,
            lit(1)
        ).otherwise(
            ntile(5).over(Window.orderBy(col('total_orders').asc()))
        )
    )

    # Monetary score (more spending is better)
    df_rfm = df_rfm.withColumn(
        'monetary_score',
        when(
            col('total_spent') == 0,
            lit(1)
        ).otherwise(
            ntile(5).over(Window.orderBy(col('total_spent').asc()))
        )
    )

    # Combined RFM score (1-15, where 15 is best)
    df_rfm = df_rfm.withColumn(
        'rfm_score',
        col('recency_score') + col('frequency_score') + col('monetary_score')
    )

    # RFM segment (concatenated scores for detailed segmentation)
    df_rfm = df_rfm.withColumn(
        'rfm_segment',
        concat_ws(
            '',
            col('recency_score').cast(StringType()),
            col('frequency_score').cast(StringType()),
            col('monetary_score').cast(StringType())
        )
    )

    logger.info("RFM scores calculated")

    return df_rfm


def apply_customer_segmentation(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Apply business-driven customer segmentation.

    Args:
        df: Customer DataFrame with RFM scores
        logger: Logger instance

    Returns:
        DataFrame with customer segments
    """
    logger.info("Applying customer segmentation")

    # Define segment logic
    df_segmented = df.withColumn(
        'customer_segment',
        when(
            (col('rfm_score') >= 12) & (col('total_orders') >= 5),
            lit('HIGH_VALUE')
        ).when(
            (col('rfm_score') >= 9) & (col('total_orders') >= 3),
            lit('PROMISING')
        ).when(
            (col('days_since_last_order') > 180) & (col('total_orders') > 0),
            lit('AT_RISK')
        ).when(
            (col('days_since_last_order') > 365) & (col('total_orders') > 0),
            lit('CHURNED')
        ).when(
            (col('total_orders') > 0) & (col('days_since_last_order') <= 90),
            lit('ACTIVE')
        ).when(
            (col('total_orders') == 1) & (col('days_since_last_order') <= 30),
            lit('NEW_CUSTOMER')
        ).when(
            col('total_orders') == 0,
            lit('PROSPECT')
        ).otherwise(
            lit('OCCASIONAL')
        )
    )

    # Add boolean flags for easier filtering
    df_segmented = df_segmented \
        .withColumn('is_high_value',
                   when(col('customer_segment') == 'HIGH_VALUE', True).otherwise(False)) \
        .withColumn('is_at_risk',
                   when(col('customer_segment') == 'AT_RISK', True).otherwise(False)) \
        .withColumn('is_new_customer',
                   when(col('customer_segment') == 'NEW_CUSTOMER', True).otherwise(False)) \
        .withColumn('is_active',
                   when(col('customer_segment') == 'ACTIVE', True).otherwise(False))

    # Log segment distribution
    segment_counts = df_segmented.groupBy('customer_segment').count().collect()
    logger.info("Customer segmentation completed", segment_distribution=str(segment_counts))

    return df_segmented


def enrich_with_metadata(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Add processing metadata and additional derived fields.

    Args:
        df: Customer 360 DataFrame
        logger: Logger instance

    Returns:
        Enriched DataFrame
    """
    logger.info("Enriching with metadata and derived fields")

    enriched_df = df \
        .withColumn('customer_360_timestamp', current_timestamp()) \
        .withColumn('customer_360_date', current_timestamp().cast('date')) \
        .withColumn('customer_age_days',
                   datediff(current_timestamp().cast('date'), col('signup_date'))) \
        .withColumn('has_purchased',
                   when(col('total_orders') > 0, True).otherwise(False)) \
        .withColumn('purchase_frequency_per_month',
                   when(
                       (col('customer_age_days') > 0) & (col('total_orders') > 0),
                       spark_round(col('total_orders') / (col('customer_age_days') / 30.0), 2)
                   ).otherwise(lit(0.0))) \
        .withColumn('engagement_score',
                   spark_round(
                       (col('total_page_views') * 0.1) +
                       (col('total_clicks') * 0.3) +
                       (col('total_orders') * 10.0),
                       2
                   ))

    # Customer value tier
    enriched_df = enriched_df.withColumn(
        'value_tier',
        when(col('customer_lifetime_value') < 100, lit('BRONZE'))
        .when(col('customer_lifetime_value').between(100, 500), lit('SILVER'))
        .when(col('customer_lifetime_value').between(500, 2000), lit('GOLD'))
        .otherwise(lit('PLATINUM'))
    )

    logger.info("Metadata enrichment completed")

    return enriched_df


def write_gold_customer_360(
    glue_context: GlueContext,
    df: DataFrame,
    target_s3_path: str,
    target_database: str,
    target_table: str,
    logger: GlueLogger
) -> None:
    """
    Write Customer 360 to Gold layer with partitioning by country.

    Args:
        glue_context: AWS Glue context
        df: DataFrame to write
        target_s3_path: S3 path for output
        target_database: Target database name
        target_table: Target table name
        logger: Logger instance
    """
    logger.info(f"Writing to Gold layer: {target_s3_path}")

    try:
        # Validate partition columns
        partition_columns = ['country']
        df_partitioned = partition_dataframe(df, partition_columns, logger)

        # Convert to DynamicFrame
        dynamic_frame = DynamicFrame.fromDF(
            df_partitioned,
            glue_context,
            "gold_customer_360_dynamic_frame"
        )

        # Write to S3 with partitioning
        glue_context.write_dynamic_frame.from_options(
            frame=dynamic_frame,
            connection_type="s3",
            connection_options={
                "path": target_s3_path,
                "partitionKeys": partition_columns
            },
            format="parquet",
            format_options={
                "compression": "snappy"
            },
            transformation_ctx="write_gold_customer_360"
        )

        logger.info(
            "Successfully wrote Gold Customer 360 data",
            row_count=df.count(),
            target_path=target_s3_path
        )

    except Exception as e:
        logger.error("Failed to write Gold Customer 360 data", exception=e)
        raise


def publish_cloudwatch_metrics(
    job_name: str,
    metrics: dict,
    logger: GlueLogger
) -> None:
    """Publish job metrics to CloudWatch."""
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

        log_job_metrics(
            cloudwatch_client=cloudwatch,
            job_name=job_name,
            namespace='DataLake/Glue/Customer360',
            metrics=metrics
        )

        logger.info("CloudWatch metrics published", metric_count=len(metrics))

    except Exception as e:
        logger.warning("Failed to publish CloudWatch metrics", exception=e)


def main():
    """Main ETL job execution."""

    # Initialize Glue context
    sc = SparkContext()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    # Get job parameters
    args = get_job_parameters()
    job_name = args['JOB_NAME']

    # Initialize job
    job = Job(glue_context)
    job.init(job_name, args)

    # Initialize logger
    run_id = args.get('JOB_RUN_ID', datetime.now().strftime('%Y%m%d%H%M%S'))
    logger = GlueLogger(job_name, run_id)

    logger.info(f"Starting ETL job: {job_name}")
    job_start_time = datetime.now()

    try:
        # Read Silver layer data
        df_customers = read_silver_customers(
            glue_context,
            args['customers_database'],
            args['customers_table'],
            logger
        )

        df_orders = read_silver_orders(
            glue_context,
            args['orders_database'],
            args['orders_table'],
            logger
        )

        df_events = read_silver_events(
            glue_context,
            args['events_database'],
            args['events_table'],
            logger
        )

        # Aggregate metrics
        df_order_metrics = aggregate_order_metrics(df_orders, logger)
        df_event_metrics = aggregate_event_metrics(df_events, logger)

        # Join customer with metrics
        df_joined = join_customer_with_metrics(
            df_customers,
            df_order_metrics,
            df_event_metrics,
            logger
        )

        # Calculate CLV and recency
        df_with_clv = calculate_customer_lifetime_value(df_joined, logger)
        df_with_recency = calculate_recency_days(df_with_clv, logger)

        # Calculate RFM scores
        df_with_rfm = calculate_rfm_score(df_with_recency, logger)

        # Apply segmentation
        df_segmented = apply_customer_segmentation(df_with_rfm, logger)

        # Enrich with metadata
        df_enriched = enrich_with_metadata(df_segmented, logger)

        # Write to Gold layer
        write_gold_customer_360(
            glue_context,
            df_enriched,
            args['target_s3_path'],
            args['target_database'],
            args['target_table'],
            logger
        )

        # Calculate job metrics
        job_end_time = datetime.now()
        processing_duration = (job_end_time - job_start_time).total_seconds()

        metrics = {
            'customers_processed': float(df_customers.count()),
            'customer_360_records_created': float(df_enriched.count()),
            'processing_duration_seconds': processing_duration,
            'high_value_customers': float(df_enriched.filter(col('is_high_value') == True).count()),
            'at_risk_customers': float(df_enriched.filter(col('is_at_risk') == True).count())
        }

        # Publish metrics
        publish_cloudwatch_metrics(job_name, metrics, logger)

        logger.info(
            "ETL job completed successfully",
            duration_seconds=processing_duration,
            records_created=metrics['customer_360_records_created']
        )

        # Commit job
        job.commit()

    except Exception as e:
        logger.error("ETL job failed", exception=e)
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
