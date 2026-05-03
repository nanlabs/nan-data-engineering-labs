"""
AWS Glue ETL Job: Bronze to Silver - Products Processing
Reads raw product data from Bronze layer, applies transformations and data quality checks,
and writes cleaned data to Silver layer.
"""

import sys
from datetime import datetime
import boto3
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, lit, trim, upper,
    regexp_replace, row_number, when, lower
)
from pyspark.sql.window import Window
from pyspark.sql.types import (
    IntegerType,
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


def read_bronze_products(
    glue_context: GlueContext,
    database: str,
    table: str,
    logger: GlueLogger
) -> DataFrame:
    """
    Read product data from Bronze layer (Glue Catalog table).

    Args:
        glue_context: AWS Glue context
        database: Source database name
        table: Source table name
        logger: Logger instance

    Returns:
        Spark DataFrame with raw product data
    """
    logger.info(f"Reading from Bronze layer: {database}.{table}")

    try:
        # Read from Glue Catalog with partition support
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_bronze_products"
        )

        df = dynamic_frame.toDF()
        row_count = df.count()

        logger.info(
            "Successfully read Bronze product data",
            row_count=row_count,
            columns=len(df.columns)
        )

        return df

    except Exception as e:
        logger.error("Failed to read Bronze product data", exception=e)
        raise


def standardize_product_schema(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Standardize product schema with proper column names and types.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with standardized schema
    """
    logger.info("Standardizing product schema")

    # Column mapping
    column_mapping = {
        'product_id': 'product_id',
        'product_name': 'product_name',
        'description': 'description',
        'category': 'category',
        'subcategory': 'subcategory',
        'brand': 'brand',
        'price': 'price',
        'cost': 'cost',
        'stock_quantity': 'stock_quantity',
        'sku': 'sku',
        'weight': 'weight',
        'dimensions': 'dimensions',
        'ingestion_timestamp': 'ingestion_timestamp'
    }

    # Select and rename columns
    df_mapped = df
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns and source_col != target_col:
            df_mapped = df_mapped.withColumnRenamed(source_col, target_col)

    # Add missing columns if needed
    for col_name in column_mapping.values():
        if col_name not in df_mapped.columns:
            df_mapped = df_mapped.withColumn(col_name, lit(None))

    logger.info("Schema standardization completed")

    return df_mapped


def clean_text_fields(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Clean and standardize text fields - trim whitespace and standardize case.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with cleaned text fields
    """
    logger.info("Cleaning text fields")

    df_cleaned = df \
        .withColumn('product_name', trim(col('product_name'))) \
        .withColumn('description', trim(col('description'))) \
        .withColumn('category', upper(trim(col('category')))) \
        .withColumn('subcategory', upper(trim(col('subcategory')))) \
        .withColumn('brand', trim(col('brand'))) \
        .withColumn('sku', upper(trim(col('sku'))))

    # Remove extra whitespace and special characters from product name
    df_cleaned = df_cleaned.withColumn(
        'product_name',
        regexp_replace(col('product_name'), '\\s+', ' ')
    )

    logger.info("Text field cleaning completed")

    return df_cleaned


def cast_numeric_fields(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Cast price and quantity fields to appropriate numeric types.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with properly typed numeric fields
    """
    logger.info("Casting numeric fields to appropriate types")

    df_typed = df \
        .withColumn('price', col('price').cast(DoubleType())) \
        .withColumn('cost', col('cost').cast(DoubleType())) \
        .withColumn('stock_quantity', col('stock_quantity').cast(IntegerType())) \
        .withColumn('weight', col('weight').cast(DoubleType())) \
        .withColumn('ingestion_timestamp', col('ingestion_timestamp').cast(TimestampType()))

    # Handle negative values - set to null
    df_typed = df_typed \
        .withColumn('price', when(col('price') < 0, lit(None)).otherwise(col('price'))) \
        .withColumn('cost', when(col('cost') < 0, lit(None)).otherwise(col('cost'))) \
        .withColumn('stock_quantity',
                   when(col('stock_quantity') < 0, lit(0)).otherwise(col('stock_quantity')))

    logger.info("Numeric field casting completed")

    return df_typed


def validate_categories(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Validate that product categories are in the allowed list.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with validated categories
    """
    logger.info("Validating product categories")

    # Define allowed categories
    allowed_categories = [
        'ELECTRONICS',
        'CLOTHING',
        'BOOKS',
        'HOME',
        'FOOD'
    ]

    # Mark valid categories
    df_validated = df.withColumn(
        'is_valid_category',
        col('category').isin(allowed_categories)
    )

    # Count invalid categories
    invalid_count = df_validated.filter(col('is_valid_category') == False).count()

    # Optionally map unknown categories to OTHER
    df_validated = df_validated.withColumn(
        'category',
        when(col('is_valid_category') == False, lit('OTHER'))
        .otherwise(col('category'))
    )

    logger.info(
        "Category validation completed",
        invalid_category_count=invalid_count,
        allowed_categories=allowed_categories
    )

    return df_validated


def perform_product_quality_checks(df: DataFrame, logger: GlueLogger) -> tuple:
    """
    Perform comprehensive data quality checks on product data.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Tuple of (DataFrame, quality_results_dict)
    """
    logger.info("Performing product data quality checks")

    # Define data quality checks
    quality_checks = {
        'null_checks': ['product_id', 'product_name', 'category', 'price'],
        'range_checks': {
            'price': (0.01, 100000.0),
            'stock_quantity': (0, 1000000)
        },
        'custom_checks': {
            'valid_price': col('price') > 0,
            'valid_stock': col('stock_quantity') >= 0,
            'valid_category': col('is_valid_category') == True,
            'price_greater_than_cost': (
                col('price').isNull() | col('cost').isNull() |
                (col('price') >= col('cost'))
            )
        }
    }

    # Apply checks
    quality_results = apply_data_quality_checks(df, quality_checks, logger)

    # Calculate data quality score per row
    score_criteria = {
        'critical_columns': ['product_id', 'product_name', 'category', 'price'],
        'range_penalties': {
            'price': (0.01, 100000.0, 20),
            'stock_quantity': (0, 1000000, 10)
        }
    }

    df_with_score = calculate_data_quality_score(df, score_criteria)

    # Additional penalties
    df_with_score = df_with_score.withColumn(
        'data_quality_score',
        when(col('is_valid_category') == False, col('data_quality_score') - 15)
        .otherwise(col('data_quality_score'))
    )

    # Log quality metrics
    avg_quality_score = df_with_score.agg(
        {'data_quality_score': 'avg'}
    ).collect()[0][0]

    logger.info(
        "Data quality checks completed",
        average_quality_score=round(avg_quality_score, 2)
    )

    return df_with_score, quality_results


def enrich_products(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Add derived and enrichment columns to product data.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Enriched DataFrame
    """
    logger.info("Enriching product data with derived columns")

    enriched_df = df \
        .withColumn('processing_timestamp', current_timestamp()) \
        .withColumn('processing_date', current_timestamp().cast('date')) \
        .withColumn('is_in_stock',
                   when(col('stock_quantity') > 0, True).otherwise(False)) \
        .withColumn('is_low_stock',
                   when(col('stock_quantity').between(1, 10), True).otherwise(False)) \
        .withColumn('profit_margin',
                   when(
                       col('price').isNotNull() & col('cost').isNotNull() & (col('price') > 0),
                       ((col('price') - col('cost')) / col('price') * 100)
                   ).otherwise(lit(None))) \
        .withColumn('price_tier',
                   when(col('price') < 20, lit('BUDGET'))
                   .when(col('price').between(20, 100), lit('STANDARD'))
                   .when(col('price').between(100, 500), lit('PREMIUM'))
                   .otherwise(lit('LUXURY')))

    # Create search-friendly product name (lowercase, no special chars)
    enriched_df = enriched_df.withColumn(
        'product_name_normalized',
        lower(regexp_replace(col('product_name'), '[^a-zA-Z0-9\\s]', ''))
    )

    logger.info("Product enrichment completed")

    return enriched_df


def deduplicate_products(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Remove duplicate products, keeping the latest by ingestion_timestamp.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Deduplicated DataFrame
    """
    logger.info("Deduplicating products by product_id")

    initial_count = df.count()

    # Create window partitioned by product_id, ordered by ingestion_timestamp descending
    window_spec = Window.partitionBy('product_id').orderBy(col('ingestion_timestamp').desc())

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


def write_silver_products(
    glue_context: GlueContext,
    df: DataFrame,
    target_s3_path: str,
    target_database: str,
    target_table: str,
    logger: GlueLogger
) -> None:
    """
    Write processed products to Silver layer with partitioning by category.

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
        # Drop temporary columns before writing
        df_output = df.drop('is_valid_category', 'product_name_normalized')

        # Validate partition columns
        partition_columns = ['category']
        df_partitioned = partition_dataframe(df_output, partition_columns, logger)

        # Convert to DynamicFrame
        dynamic_frame = DynamicFrame.fromDF(
            df_partitioned,
            glue_context,
            "silver_products_dynamic_frame"
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
            transformation_ctx="write_silver_products"
        )

        logger.info(
            "Successfully wrote Silver product data",
            row_count=df_output.count(),
            target_path=target_s3_path,
            partitions=partition_columns
        )

    except Exception as e:
        logger.error("Failed to write Silver product data", exception=e)
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
            namespace='DataLake/Glue/Products',
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
        df_bronze = read_bronze_products(
            glue_context,
            args['source_database'],
            args['source_table'],
            logger
        )

        # Validate schema
        required_columns = [
            'product_id', 'product_name', 'category', 'price', 'ingestion_timestamp'
        ]
        if not validate_dataframe_schema(df_bronze, required_columns, logger):
            raise ValueError("Schema validation failed")

        # Apply transformations
        df_standardized = standardize_product_schema(df_bronze, logger)
        df_cleaned = clean_text_fields(df_standardized, logger)
        df_typed = cast_numeric_fields(df_cleaned, logger)
        df_validated = validate_categories(df_typed, logger)
        df_deduped = deduplicate_products(df_validated, logger)
        df_quality, quality_results = perform_product_quality_checks(df_deduped, logger)
        df_enriched = enrich_products(df_quality, logger)

        # Write to Silver layer
        write_silver_products(
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
