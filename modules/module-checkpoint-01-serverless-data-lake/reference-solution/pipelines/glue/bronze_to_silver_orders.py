"""
AWS Glue ETL Job: Bronze to Silver - Orders Processing
Reads raw orders data from Bronze layer, applies transformations and data quality checks,
and writes cleaned data to Silver layer.
"""

import sys
from datetime import datetime
import boto3
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, lit, when, to_date, trim, upper, row_number,
    year, month, dayofmonth
)
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StringType, IntegerType,
    DoubleType, TimestampType
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
    GlueLogger, log_job_metrics, validate_dataframe_schema,
    apply_data_quality_checks, calculate_data_quality_score, partition_dataframe
)


def get_job_parameters():
    """Extract job parameters from Glue arguments."""
    args = getResolvedOptions(
        sys.argv,
        [
            'JOB_NAME',
            'source_database',
            'source_table',
            'target_s3_path',
            'target_database',
            'target_table'
        ]
    )
    return args


def read_bronze_orders(glue_context: GlueContext, database: str, table: str, logger: GlueLogger) -> DataFrame:
    """
    Read orders data from Bronze layer (Glue Catalog table).

    Args:
        glue_context: AWS Glue context
        database: Source database name
        table: Source table name
        logger: Logger instance

    Returns:
        Spark DataFrame with raw orders data
    """
    logger.info(f"Reading from Bronze layer: {database}.{table}")

    try:
        # Read from Glue Catalog with job bookmark support
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_bronze_orders"
        )

        df = dynamic_frame.toDF()
        row_count = df.count()

        logger.info(
            "Successfully read Bronze orders data",
            row_count=row_count,
            columns=len(df.columns)
        )

        return df

    except Exception as e:
        logger.error("Failed to read Bronze orders data", exception=e)
        raise


def apply_schema_mapping(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Apply schema mapping to standardize column names and types.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with standardized schema
    """
    logger.info("Applying schema mapping and standardization")

    # Column mapping: source_name -> target_name
    column_mapping = {
        'order_id': 'order_id',
        'customer_id': 'customer_id',
        'product_id': 'product_id',
        'order_date': 'order_date',
        'order_timestamp': 'order_timestamp',
        'quantity': 'quantity',
        'unit_price': 'unit_price',
        'total_amount': 'total_amount',
        'order_status': 'order_status',
        'payment_method': 'payment_method',
        'shipping_address': 'shipping_address',
        'ingestion_timestamp': 'ingestion_timestamp'
    }

    # Select and rename columns
    df_mapped = df
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns and source_col != target_col:
            df_mapped = df_mapped.withColumnRenamed(source_col, target_col)

    # Ensure required columns exist
    required_columns = list(column_mapping.values())
    for col_name in required_columns:
        if col_name not in df_mapped.columns:
            logger.warning(f"Adding missing column: {col_name}")
            df_mapped = df_mapped.withColumn(col_name, lit(None))

    # Cast to appropriate types
    df_typed = df_mapped \
        .withColumn('order_id', col('order_id').cast(StringType())) \
        .withColumn('customer_id', col('customer_id').cast(StringType())) \
        .withColumn('product_id', col('product_id').cast(StringType())) \
        .withColumn('order_date', to_date(col('order_date'))) \
        .withColumn('order_timestamp', col('order_timestamp').cast(TimestampType())) \
        .withColumn('quantity', col('quantity').cast(IntegerType())) \
        .withColumn('unit_price', col('unit_price').cast(DoubleType())) \
        .withColumn('total_amount', col('total_amount').cast(DoubleType())) \
        .withColumn('order_status', upper(trim(col('order_status')))) \
        .withColumn('payment_method', upper(trim(col('payment_method')))) \
        .withColumn('ingestion_timestamp', col('ingestion_timestamp').cast(TimestampType()))

    logger.info("Schema mapping completed", mapped_columns=len(required_columns))

    return df_typed


def filter_invalid_rows(df: DataFrame, logger: GlueLogger) -> tuple:
    """
    Filter out invalid rows based on business rules.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Tuple of (valid_df, filtered_count)
    """
    logger.info("Filtering invalid rows")

    initial_count = df.count()

    # Define validation conditions
    valid_df = df.filter(
        # Must have order_id
        col('order_id').isNotNull() &
        # Must have customer_id
        col('customer_id').isNotNull() &
        # Must have order_date
        col('order_date').isNotNull() &
        # Order date must be reasonable (between 2020 and 2026)
        (year(col('order_date')) >= 2020) &
        (year(col('order_date')) <= 2026) &
        # Total amount must be positive
        (col('total_amount') > 0) &
        # Quantity must be positive
        (col('quantity') > 0)
    )

    final_count = valid_df.count()
    filtered_count = initial_count - final_count

    logger.info(
        "Row filtering completed",
        initial_count=initial_count,
        final_count=final_count,
        filtered_count=filtered_count,
        filter_percentage=round(filtered_count / initial_count * 100, 2) if initial_count > 0 else 0
    )

    return valid_df, filtered_count


def deduplicate_orders(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Remove duplicate orders, keeping the latest by ingestion_timestamp.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Deduplicated DataFrame
    """
    logger.info("Deduplicating orders by order_id")

    initial_count = df.count()

    # Create window partitioned by order_id, ordered by ingestion_timestamp descending
    window_spec = Window.partitionBy('order_id').orderBy(col('ingestion_timestamp').desc())

    # Add row number and keep only rank 1 (most recent)
    df_deduped = df.withColumn('row_num', row_number().over(window_spec)) \
                   .filter(col('row_num') == 1) \
                   .drop('row_num')

    final_count = df_deduped.count()
    duplicates_removed = initial_count - final_count

    logger.info(
        "Deduplication completed",
        initial_count=initial_count,
        final_count=final_count,
        duplicates_removed=duplicates_removed
    )

    return df_deduped


def perform_data_quality_checks(df: DataFrame, logger: GlueLogger) -> tuple:
    """
    Perform comprehensive data quality checks.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Tuple of (DataFrame, quality_results_dict)
    """
    logger.info("Performing data quality checks")

    # Define data quality checks
    quality_checks = {
        'null_checks': ['order_id', 'customer_id', 'order_date'],
        'range_checks': {
            'total_amount': (0.01, 1000000.0),
            'quantity': (1, 10000)
        },
        'custom_checks': {
            'valid_order_date': (
                (col('order_date') >= lit('2020-01-01')) &
                (col('order_date') <= lit('2026-12-31'))
            ),
            'price_quantity_match': (
                col('total_amount') >= (col('unit_price') * col('quantity') * 0.9)
            )
        }
    }

    # Apply checks
    quality_results = apply_data_quality_checks(df, quality_checks, logger)

    # Calculate data quality score per row
    score_criteria = {
        'critical_columns': ['order_id', 'customer_id', 'order_date', 'total_amount'],
        'range_penalties': {
            'total_amount': (0.01, 1000000.0, 10),
            'quantity': (1, 10000, 5)
        }
    }

    df_with_score = calculate_data_quality_score(df, score_criteria)

    # Log quality metrics
    avg_quality_score = df_with_score.agg(
        {'data_quality_score': 'avg'}
    ).collect()[0][0]

    logger.info(
        "Data quality checks completed",
        average_quality_score=round(avg_quality_score, 2)
    )

    return df_with_score, quality_results


def enrich_orders(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Add derived and enrichment columns.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Enriched DataFrame
    """
    logger.info("Enriching orders with derived columns")

    enriched_df = df \
        .withColumn('processing_timestamp', current_timestamp()) \
        .withColumn('processing_date', current_timestamp().cast('date')) \
        .withColumn('year', year(col('order_date'))) \
        .withColumn('month', month(col('order_date'))) \
        .withColumn('day', dayofmonth(col('order_date'))) \
        .withColumn('is_high_value', when(col('total_amount') > 1000, True).otherwise(False)) \
        .withColumn('discount_amount',
                   (col('unit_price') * col('quantity')) - col('total_amount')) \
        .withColumn('has_discount',
                   when(col('discount_amount') > 0, True).otherwise(False))

    logger.info("Order enrichment completed")

    return enriched_df


def write_silver_orders(
    glue_context: GlueContext,
    df: DataFrame,
    target_s3_path: str,
    target_database: str,
    target_table: str,
    logger: GlueLogger
) -> None:
    """
    Write processed orders to Silver layer with partitioning.

    Args:
        glue_context: AWS Glue context
        df: DataFrame to write
        target_s3_path: S3 path for output
        target_database: Target database name
        target_table: Target table name
        logger: Logger instance
    """
    logger.info(f"Writing to Silver layer: {target_s3_path}")

    try:
        # Validate partition columns
        partition_columns = ['year', 'month']
        df_partitioned = partition_dataframe(df, partition_columns, logger)

        # Convert to DynamicFrame
        dynamic_frame = DynamicFrame.fromDF(
            df_partitioned,
            glue_context,
            "silver_orders_dynamic_frame"
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
            transformation_ctx="write_silver_orders"
        )

        logger.info(
            "Successfully wrote Silver orders data",
            row_count=df.count(),
            target_path=target_s3_path,
            partitions=partition_columns
        )

    except Exception as e:
        logger.error("Failed to write Silver orders data", exception=e)
        raise


def publish_cloudwatch_metrics(
    job_name: str,
    metrics: dict,
    logger: GlueLogger
) -> None:
    """
    Publish job metrics to CloudWatch.

    Args:
        job_name: Name of the Glue job
        metrics: Dictionary of metrics to publish
        logger: Logger instance
    """
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

        log_job_metrics(
            cloudwatch_client=cloudwatch,
            job_name=job_name,
            namespace='DataLake/Glue/Orders',
            metrics=metrics
        )

        logger.info("CloudWatch metrics published successfully", metric_count=len(metrics))

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

    # Initialize job with bookmark support
    job = Job(glue_context)
    job.init(job_name, args)

    # Initialize logger
    run_id = args.get('JOB_RUN_ID', datetime.now().strftime('%Y%m%d%H%M%S'))
    logger = GlueLogger(job_name, run_id)

    logger.info(f"Starting ETL job: {job_name}")
    job_start_time = datetime.now()

    try:
        # Read Bronze data
        df_bronze = read_bronze_orders(
            glue_context,
            args['source_database'],
            args['source_table'],
            logger
        )

        # Validate schema
        required_columns = [
            'order_id', 'customer_id', 'product_id', 'order_date',
            'quantity', 'total_amount', 'ingestion_timestamp'
        ]
        if not validate_dataframe_schema(df_bronze, required_columns, logger):
            raise ValueError("Schema validation failed")

        # Apply transformations
        df_mapped = apply_schema_mapping(df_bronze, logger)
        df_filtered, filtered_count = filter_invalid_rows(df_mapped, logger)
        df_deduped = deduplicate_orders(df_filtered, logger)
        df_quality, quality_results = perform_data_quality_checks(df_deduped, logger)
        df_enriched = enrich_orders(df_quality, logger)

        # Write to Silver layer
        write_silver_orders(
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
            'rows_processed': float(df_bronze.count()),
            'rows_written': float(df_enriched.count()),
            'rows_filtered': float(filtered_count),
            'processing_duration_seconds': processing_duration,
            'data_quality_checks_passed': float(quality_results['checks_passed']),
            'data_quality_checks_failed': float(quality_results['checks_failed'])
        }

        # Publish metrics
        publish_cloudwatch_metrics(job_name, metrics, logger)

        logger.info(
            "ETL job completed successfully",
            duration_seconds=processing_duration,
            rows_processed=metrics['rows_processed'],
            rows_written=metrics['rows_written']
        )

        # Commit job bookmark
        job.commit()

    except Exception as e:
        logger.error("ETL job failed", exception=e)
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
