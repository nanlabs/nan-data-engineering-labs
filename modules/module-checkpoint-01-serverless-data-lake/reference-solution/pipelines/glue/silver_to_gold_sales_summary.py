"""
AWS Glue ETL Job: Silver to Gold - Sales Summary
Joins orders, customers, and products from Silver layer to create aggregated sales summary
in Gold layer for business intelligence and reporting.
"""

import sys
from datetime import datetime
import boto3
from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    col, current_timestamp, lit, count, sum as spark_sum, avg, min as spark_min,
    max as spark_max, countDistinct, when, lag, rank, dense_rank, year, month, dayofmonth, round as spark_round
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
            'orders_database',
            'orders_table',
            'customers_database',
            'customers_table',
            'products_database',
            'products_table',
            'target_s3_path',
            'target_database',
            'target_table'
        ]
    )
    return args


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


def read_silver_products(
    glue_context: GlueContext,
    database: str,
    table: str,
    logger: GlueLogger
) -> DataFrame:
    """Read processed products from Silver layer."""
    logger.info(f"Reading Silver products: {database}.{table}")

    try:
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_silver_products"
        )

        df = dynamic_frame.toDF()
        logger.info("Successfully read Silver products", row_count=df.count())
        return df

    except Exception as e:
        logger.error("Failed to read Silver products", exception=e)
        raise


def join_orders_with_dimensions(
    df_orders: DataFrame,
    df_customers: DataFrame,
    df_products: DataFrame,
    logger: GlueLogger
) -> DataFrame:
    """
    Join orders with customer and product dimensions.

    Args:
        df_orders: Orders DataFrame from Silver layer
        df_customers: Customers DataFrame from Silver layer
        df_products: Products DataFrame from Silver layer
        logger: Logger instance

    Returns:
        Joined DataFrame with all dimensions
    """
    logger.info("Joining orders with customer and product dimensions")

    # Select relevant columns from each dimension
    df_orders_selected = df_orders.select(
        'order_id',
        'customer_id',
        'product_id',
        'order_date',
        'order_timestamp',
        'quantity',
        'unit_price',
        'total_amount',
        'order_status',
        'payment_method',
        'year',
        'month'
    )

    df_customers_selected = df_customers.select(
        col('customer_id').alias('cust_id'),
        col('country').alias('customer_country'),
        col('city').alias('customer_city'),
        col('account_status').alias('customer_account_status')
    )

    df_products_selected = df_products.select(
        col('product_id').alias('prod_id'),
        col('product_name'),
        col('category').alias('product_category'),
        col('brand').alias('product_brand'),
        col('price').alias('product_price')
    )

    # Perform LEFT JOINs to keep all orders
    df_joined = df_orders_selected \
        .join(df_customers_selected,
              df_orders_selected.customer_id == df_customers_selected.cust_id,
              'left') \
        .join(df_products_selected,
              df_orders_selected.product_id == df_products_selected.prod_id,
              'left')

    # Drop redundant join keys
    df_joined = df_joined.drop('cust_id', 'prod_id')

    # Log join statistics
    total_orders = df_orders_selected.count()
    joined_orders = df_joined.count()
    orders_with_customer = df_joined.filter(col('customer_country').isNotNull()).count()
    orders_with_product = df_joined.filter(col('product_category').isNotNull()).count()

    logger.info(
        "Join completed",
        total_orders=total_orders,
        joined_orders=joined_orders,
        orders_with_customer=orders_with_customer,
        orders_with_product=orders_with_product
    )

    return df_joined


def create_sales_aggregations(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Create aggregated sales summary grouped by date, country, and category.

    Args:
        df: Joined DataFrame with orders and dimensions
        logger: Logger instance

    Returns:
        Aggregated sales summary DataFrame
    """
    logger.info("Creating sales aggregations")

    # Group by order_date, country, category
    df_aggregated = df.groupBy(
        'order_date',
        'customer_country',
        'product_category'
    ).agg(
        # Order metrics
        count('order_id').alias('total_orders'),
        countDistinct('order_id').alias('unique_orders'),
        countDistinct('customer_id').alias('unique_customers'),
        countDistinct('product_id').alias('unique_products'),

        # Revenue metrics
        spark_sum('total_amount').alias('total_revenue'),
        avg('total_amount').alias('average_order_value'),
        spark_min('total_amount').alias('min_order_value'),
        spark_max('total_amount').alias('max_order_value'),

        # Quantity metrics
        spark_sum('quantity').alias('total_quantity_sold'),
        avg('quantity').alias('average_quantity_per_order'),

        # Price metrics
        avg('unit_price').alias('average_unit_price')
    )

    # Round decimal values for better readability
    df_aggregated = df_aggregated \
        .withColumn('total_revenue', spark_round(col('total_revenue'), 2)) \
        .withColumn('average_order_value', spark_round(col('average_order_value'), 2)) \
        .withColumn('min_order_value', spark_round(col('min_order_value'), 2)) \
        .withColumn('max_order_value', spark_round(col('max_order_value'), 2)) \
        .withColumn('average_quantity_per_order', spark_round(col('average_quantity_per_order'), 2)) \
        .withColumn('average_unit_price', spark_round(col('average_unit_price'), 2))

    logger.info(
        "Sales aggregations created",
        aggregated_rows=df_aggregated.count()
    )

    return df_aggregated


def calculate_window_functions(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Calculate window functions for time-series analysis and rankings.

    Args:
        df: Aggregated sales DataFrame
        logger: Logger instance

    Returns:
        DataFrame with window function calculations
    """
    logger.info("Calculating window functions for time-series analysis")

    # Window for previous day comparison (partitioned by country and category)
    window_prev_day = Window \
        .partitionBy('customer_country', 'product_category') \
        .orderBy('order_date')

    # Calculate previous day metrics
    df_with_lag = df \
        .withColumn('prev_day_revenue',
                   lag('total_revenue', 1).over(window_prev_day)) \
        .withColumn('prev_day_orders',
                   lag('total_orders', 1).over(window_prev_day))

    # Calculate day-over-day changes
    df_with_lag = df_with_lag \
        .withColumn('revenue_change',
                   when(col('prev_day_revenue').isNotNull(),
                        col('total_revenue') - col('prev_day_revenue'))
                   .otherwise(lit(None))) \
        .withColumn('revenue_change_pct',
                   when(
                       (col('prev_day_revenue').isNotNull()) & (col('prev_day_revenue') > 0),
                       spark_round((col('total_revenue') - col('prev_day_revenue')) /
                                 col('prev_day_revenue') * 100, 2)
                   ).otherwise(lit(None))) \
        .withColumn('orders_change',
                   when(col('prev_day_orders').isNotNull(),
                        col('total_orders') - col('prev_day_orders'))
                   .otherwise(lit(None)))

    # Window for product category ranking within each date
    window_rank = Window \
        .partitionBy('order_date') \
        .orderBy(col('total_revenue').desc())

    # Add rankings
    df_with_rank = df_with_lag \
        .withColumn('revenue_rank', rank().over(window_rank)) \
        .withColumn('revenue_dense_rank', dense_rank().over(window_rank))

    # Window for moving averages (7-day)
    window_ma = Window \
        .partitionBy('customer_country', 'product_category') \
        .orderBy('order_date') \
        .rowsBetween(-6, 0)

    # Calculate 7-day moving averages
    df_with_ma = df_with_rank \
        .withColumn('revenue_7day_ma',
                   spark_round(avg('total_revenue').over(window_ma), 2)) \
        .withColumn('orders_7day_ma',
                   spark_round(avg('total_orders').over(window_ma), 2))

    logger.info("Window function calculations completed")

    return df_with_ma


def calculate_top_performers(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Identify top performing categories and flag them.

    Args:
        df: Sales DataFrame with rankings
        logger: Logger instance

    Returns:
        DataFrame with top performer flags
    """
    logger.info("Calculating top performer indicators")

    # Flag top 3 categories by revenue each day
    df_with_flags = df \
        .withColumn('is_top_revenue_category',
                   when(col('revenue_rank') <= 3, True).otherwise(False)) \
        .withColumn('is_high_growth',
                   when(col('revenue_change_pct') > 10, True).otherwise(False)) \
        .withColumn('is_declining',
                   when(col('revenue_change_pct') < -10, True).otherwise(False))

    logger.info("Top performer calculations completed")

    return df_with_flags


def enrich_with_metadata(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Add processing metadata and derived columns.

    Args:
        df: Sales summary DataFrame
        logger: Logger instance

    Returns:
        Enriched DataFrame
    """
    logger.info("Enriching with metadata columns")

    enriched_df = df \
        .withColumn('processing_timestamp', current_timestamp()) \
        .withColumn('processing_date', current_timestamp().cast('date')) \
        .withColumn('year', year(col('order_date'))) \
        .withColumn('month', month(col('order_date'))) \
        .withColumn('day', dayofmonth(col('order_date'))) \
        .withColumn('revenue_per_customer',
                   when(col('unique_customers') > 0,
                        spark_round(col('total_revenue') / col('unique_customers'), 2))
                   .otherwise(lit(0))) \
        .withColumn('revenue_per_order',
                   when(col('total_orders') > 0,
                        spark_round(col('total_revenue') / col('total_orders'), 2))
                   .otherwise(lit(0)))

    # Add business segment classification
    enriched_df = enriched_df \
        .withColumn('revenue_segment',
                   when(col('total_revenue') < 1000, lit('LOW'))
                   .when(col('total_revenue').between(1000, 10000), lit('MEDIUM'))
                   .when(col('total_revenue').between(10000, 50000), lit('HIGH'))
                   .otherwise(lit('VERY_HIGH')))

    logger.info("Metadata enrichment completed")

    return enriched_df


def write_gold_sales_summary(
    glue_context: GlueContext,
    df: DataFrame,
    target_s3_path: str,
    target_database: str,
    target_table: str,
    logger: GlueLogger
) -> None:
    """
    Write sales summary to Gold layer with partitioning by date.

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
        partition_columns = ['year', 'month']
        df_partitioned = partition_dataframe(df, partition_columns, logger)

        # Convert to DynamicFrame
        dynamic_frame = DynamicFrame.fromDF(
            df_partitioned,
            glue_context,
            "gold_sales_summary_dynamic_frame"
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
            transformation_ctx="write_gold_sales_summary"
        )

        logger.info(
            "Successfully wrote Gold sales summary",
            row_count=df.count(),
            target_path=target_s3_path
        )

    except Exception as e:
        logger.error("Failed to write Gold sales summary", exception=e)
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
            namespace='DataLake/Glue/SalesSummary',
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
        df_orders = read_silver_orders(
            glue_context,
            args['orders_database'],
            args['orders_table'],
            logger
        )

        df_customers = read_silver_customers(
            glue_context,
            args['customers_database'],
            args['customers_table'],
            logger
        )

        df_products = read_silver_products(
            glue_context,
            args['products_database'],
            args['products_table'],
            logger
        )

        # Join dimensions
        df_joined = join_orders_with_dimensions(
            df_orders,
            df_customers,
            df_products,
            logger
        )

        # Create aggregations
        df_aggregated = create_sales_aggregations(df_joined, logger)

        # Calculate window functions
        df_with_windows = calculate_window_functions(df_aggregated, logger)

        # Calculate top performers
        df_with_ranks = calculate_top_performers(df_with_windows, logger)

        # Enrich with metadata
        df_enriched = enrich_with_metadata(df_with_ranks, logger)

        # Write to Gold layer
        write_gold_sales_summary(
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
            'orders_processed': float(df_orders.count()),
            'summary_records_created': float(df_enriched.count()),
            'processing_duration_seconds': processing_duration
        }

        # Publish metrics
        publish_cloudwatch_metrics(job_name, metrics, logger)

        logger.info(
            "ETL job completed successfully",
            duration_seconds=processing_duration,
            records_created=metrics['summary_records_created']
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
