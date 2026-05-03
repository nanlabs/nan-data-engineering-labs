"""
AWS Glue ETL Job: Bronze to Silver - Customers Processing
Reads raw customer data from Bronze layer, applies transformations and data quality checks,
and writes cleaned data to Silver layer.
"""

import sys
from datetime import datetime
import boto3
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, lit, trim, lower, upper,
    regexp_replace, row_number, when, year, to_date
)
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StringType, DoubleType, TimestampType
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


def read_bronze_customers(
    glue_context: GlueContext,
    database: str,
    table: str,
    logger: GlueLogger
) -> DataFrame:
    """
    Read customer data from Bronze layer (Glue Catalog table).

    Args:
        glue_context: AWS Glue context
        database: Source database name
        table: Source table name
        logger: Logger instance

    Returns:
        Spark DataFrame with raw customer data
    """
    logger.info(f"Reading from Bronze layer: {database}.{table}")

    try:
        # Read from Glue Catalog with partition support
        dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table,
            transformation_ctx="read_bronze_customers"
        )

        df = dynamic_frame.toDF()
        row_count = df.count()

        logger.info(
            "Successfully read Bronze customer data",
            row_count=row_count,
            columns=len(df.columns)
        )

        return df

    except Exception as e:
        logger.error("Failed to read Bronze customer data", exception=e)
        raise


def standardize_customer_schema(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Standardize customer schema with proper column names and types.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with standardized schema
    """
    logger.info("Standardizing customer schema")

    # Column mapping
    column_mapping = {
        'customer_id': 'customer_id',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'email': 'email',
        'phone': 'phone',
        'address': 'address',
        'city': 'city',
        'state': 'state',
        'country': 'country',
        'postal_code': 'postal_code',
        'signup_date': 'signup_date',
        'account_status': 'account_status',
        'ingestion_timestamp': 'ingestion_timestamp'
    }

    # Select and rename columns
    df_mapped = df
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns and source_col != target_col:
            df_mapped = df_mapped.withColumnRenamed(source_col, target_col)

    # Cast to appropriate types
    df_typed = df_mapped \
        .withColumn('customer_id', col('customer_id').cast(StringType())) \
        .withColumn('first_name', trim(col('first_name'))) \
        .withColumn('last_name', trim(col('last_name'))) \
        .withColumn('email', lower(trim(col('email')))) \
        .withColumn('phone', regexp_replace(col('phone'), '[^0-9+]', '')) \
        .withColumn('address', trim(col('address'))) \
        .withColumn('city', trim(col('city'))) \
        .withColumn('state', upper(trim(col('state')))) \
        .withColumn('country', upper(trim(col('country')))) \
        .withColumn('postal_code', trim(col('postal_code'))) \
        .withColumn('signup_date', to_date(col('signup_date'))) \
        .withColumn('account_status', upper(trim(col('account_status')))) \
        .withColumn('ingestion_timestamp', col('ingestion_timestamp').cast(TimestampType()))

    logger.info("Schema standardization completed")

    return df_typed


def standardize_email_addresses(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Standardize email addresses to lowercase and validate format.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with standardized emails
    """
    logger.info("Standardizing email addresses")

    # Convert to lowercase and trim
    df_email = df.withColumn('email', lower(trim(col('email'))))

    # Extract valid email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Mark invalid emails
    df_email = df_email.withColumn(
        'is_valid_email',
        when(
            col('email').rlike(email_pattern),
            lit(True)
        ).otherwise(lit(False))
    )

    # Count invalid emails
    invalid_count = df_email.filter(col('is_valid_email') == False).count()

    logger.info(
        "Email standardization completed",
        invalid_email_count=invalid_count
    )

    return df_email


def standardize_country_codes(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Standardize country codes to ISO format.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        DataFrame with standardized country codes
    """
    logger.info("Standardizing country codes")

    # Map common country names to ISO codes
    country_mapping = {
        'UNITED STATES': 'US',
        'USA': 'US',
        'UNITED KINGDOM': 'UK',
        'GREAT BRITAIN': 'UK',
        'CANADA': 'CA',
        'MEXICO': 'MX',
        'GERMANY': 'DE',
        'FRANCE': 'FR',
        'SPAIN': 'ES',
        'ITALY': 'IT',
        'BRAZIL': 'BR',
        'ARGENTINA': 'AR',
        'JAPAN': 'JP',
        'CHINA': 'CN',
        'INDIA': 'IN',
        'AUSTRALIA': 'AU'
    }

    # Apply country mapping
    df_country = df.withColumn('country', upper(trim(col('country'))))

    for country_name, country_code in country_mapping.items():
        df_country = df_country.withColumn(
            'country',
            when(col('country') == country_name, lit(country_code))
            .otherwise(col('country'))
        )

    # For countries already in 2-letter format, keep as is
    df_country = df_country.withColumn(
        'country_standardized',
        when(col('country').rlike('^[A-Z]{2}$'), col('country'))
        .otherwise(col('country'))
    )

    logger.info("Country code standardization completed")

    return df_country.withColumn('country', col('country_standardized')).drop('country_standardized')


def deduplicate_customers(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Remove duplicate customers, keeping the latest by ingestion_timestamp.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Deduplicated DataFrame
    """
    logger.info("Deduplicating customers by customer_id")

    initial_count = df.count()

    # Create window partitioned by customer_id, ordered by ingestion_timestamp descending
    window_spec = Window.partitionBy('customer_id').orderBy(col('ingestion_timestamp').desc())

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


def perform_customer_quality_checks(df: DataFrame, logger: GlueLogger) -> tuple:
    """
    Perform comprehensive data quality checks on customer data.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Tuple of (DataFrame, quality_results_dict)
    """
    logger.info("Performing customer data quality checks")

    # Define data quality checks
    quality_checks = {
        'null_checks': ['customer_id', 'email', 'country'],
        'custom_checks': {
            'valid_email_format': col('is_valid_email') == True,
            'valid_signup_date': (
                (col('signup_date') >= lit('2015-01-01')) &
                (col('signup_date') <= current_timestamp().cast('date'))
            ),
            'valid_country_code': col('country').rlike('^[A-Z]{2}$')
        }
    }

    # Apply checks
    quality_results = apply_data_quality_checks(df, quality_checks, logger)

    # Calculate data quality score per row
    score_criteria = {
        'critical_columns': ['customer_id', 'email', 'first_name', 'last_name', 'country'],
        'range_penalties': {}
    }

    df_with_score = calculate_data_quality_score(df, score_criteria)

    # Add penalty for invalid email
    df_with_score = df_with_score.withColumn(
        'data_quality_score',
        when(col('is_valid_email') == False, col('data_quality_score') - 15)
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


def enrich_customers(df: DataFrame, logger: GlueLogger) -> DataFrame:
    """
    Add derived and enrichment columns to customer data.

    Args:
        df: Input DataFrame
        logger: Logger instance

    Returns:
        Enriched DataFrame
    """
    logger.info("Enriching customer data with derived columns")

    enriched_df = df \
        .withColumn('processing_timestamp', current_timestamp()) \
        .withColumn('processing_date', current_timestamp().cast('date')) \
        .withColumn('customer_lifetime_value', lit(0.0).cast(DoubleType())) \
        .withColumn('full_name',
                   concat_ws(' ', col('first_name'), col('last_name'))) \
        .withColumn('account_age_days',
                   datediff(current_timestamp().cast('date'), col('signup_date'))) \
        .withColumn('is_active',
                   when(col('account_status') == 'ACTIVE', True).otherwise(False)) \
        .withColumn('signup_year', year(col('signup_date')))

    # Mask PII for logging (keep first letter of names)
    enriched_df = enriched_df.withColumn(
        'first_name_masked',
        concat(substring(col('first_name'), 1, 1), lit('***'))
    ).withColumn(
        'last_name_masked',
        concat(substring(col('last_name'), 1, 1), lit('***'))
    )

    logger.info("Customer enrichment completed")

    return enriched_df


def mask_pii_for_logging(df: DataFrame, logger: GlueLogger) -> None:
    """
    Ensure PII is not logged by creating masked versions.

    Args:
        df: DataFrame with customer data
        logger: Logger instance
    """
    # Sample data with masked PII for validation
    sample_masked = df.select(
        'customer_id',
        'first_name_masked',
        'last_name_masked',
        'country',
        'is_valid_email'
    ).limit(5).collect()

    logger.info(
        "Sample customer records (PII masked)",
        sample_count=len(sample_masked)
    )

    # Note: Actual PII values are never logged


def write_silver_customers(
    glue_context: GlueContext,
    df: DataFrame,
    target_s3_path: str,
    target_database: str,
    target_table: str,
    logger: GlueLogger
) -> None:
    """
    Write processed customers to Silver layer with partitioning by country.

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
        # Drop masked columns before writing
        df_output = df.drop('first_name_masked', 'last_name_masked', 'is_valid_email')

        # Validate partition columns
        partition_columns = ['country']
        df_partitioned = partition_dataframe(df_output, partition_columns, logger)

        # Convert to DynamicFrame
        dynamic_frame = DynamicFrame.fromDF(
            df_partitioned,
            glue_context,
            "silver_customers_dynamic_frame"
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
            transformation_ctx="write_silver_customers"
        )

        logger.info(
            "Successfully wrote Silver customer data",
            row_count=df_output.count(),
            target_path=target_s3_path,
            partitions=partition_columns
        )

    except Exception as e:
        logger.error("Failed to write Silver customer data", exception=e)
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
            namespace='DataLake/Glue/Customers',
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
        df_bronze = read_bronze_customers(
            glue_context,
            args['source_database'],
            args['source_table'],
            logger
        )

        # Validate schema
        required_columns = [
            'customer_id', 'email', 'country', 'ingestion_timestamp'
        ]
        if not validate_dataframe_schema(df_bronze, required_columns, logger):
            raise ValueError("Schema validation failed")

        # Apply transformations
        df_standardized = standardize_customer_schema(df_bronze, logger)
        df_email = standardize_email_addresses(df_standardized, logger)
        df_country = standardize_country_codes(df_email, logger)
        df_deduped = deduplicate_customers(df_country, logger)
        df_quality, quality_results = perform_customer_quality_checks(df_deduped, logger)
        df_enriched = enrich_customers(df_quality, logger)

        # Ensure PII masking for logs
        mask_pii_for_logging(df_enriched, logger)

        # Write to Silver layer
        write_silver_customers(
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
