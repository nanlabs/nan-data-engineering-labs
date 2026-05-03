"""
Raw to Bronze Layer ETL Job
Reads raw data from S3, validates schemas, converts to Parquet,
partitions by date, and writes to bronze layer with metadata tracking.

Handles: JSON, CSV, Avro files with schema validation, null checks,
duplicate detection, and statistics collection.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, lit, input_file_name,
    year, month, dayofmonth, concat_ws,
    sha2
)
from pyspark.sql.types import (
    StructType
)

from common.spark_utils import (
    create_spark_session, collect_stats,
    send_notification, write_metadata_to_dynamodb, error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates DataFrame schemas against expected schemas."""

    def __init__(self):
        self.validation_results = []

    def validate_schema(
        self,
        df: DataFrame,
        expected_schema: StructType,
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Validate DataFrame schema against expected schema.

        Args:
            df: DataFrame to validate
            expected_schema: Expected StructType
            strict: If True, requires exact match

        Returns:
            Dictionary with validation results
        """
        logger.info("Starting schema validation")

        actual_fields = {field.name: field.dataType for field in df.schema.fields}
        expected_fields = {field.name: field.dataType for field in expected_schema.fields}

        missing_fields = set(expected_fields.keys()) - set(actual_fields.keys())
        extra_fields = set(actual_fields.keys()) - set(expected_fields.keys())
        type_mismatches = []

        for field_name in set(actual_fields.keys()) & set(expected_fields.keys()):
            if str(actual_fields[field_name]) != str(expected_fields[field_name]):
                type_mismatches.append({
                    'field': field_name,
                    'expected': str(expected_fields[field_name]),
                    'actual': str(actual_fields[field_name])
                })

        is_valid = not missing_fields and not type_mismatches
        if strict:
            is_valid = is_valid and not extra_fields

        result = {
            'is_valid': is_valid,
            'missing_fields': list(missing_fields),
            'extra_fields': list(extra_fields),
            'type_mismatches': type_mismatches,
            'timestamp': datetime.now().isoformat()
        }

        self.validation_results.append(result)

        if is_valid:
            logger.info("Schema validation passed")
        else:
            logger.warning(f"Schema validation issues found: {result}")

        return result

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results."""
        return {
            'total_validations': len(self.validation_results),
            'passed': sum(1 for r in self.validation_results if r['is_valid']),
            'failed': sum(1 for r in self.validation_results if not r['is_valid']),
            'results': self.validation_results
        }


class DataQualityChecker:
    """Performs data quality checks on DataFrames."""

    def __init__(self, df: DataFrame):
        self.df = df
        self.checks = []

    def check_null_values(self, columns: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Check for null values in specified columns.

        Args:
            columns: List of columns to check (None = all columns)

        Returns:
            Dictionary mapping column names to null counts
        """
        logger.info("Checking for null values")

        cols_to_check = columns if columns else self.df.columns

        null_counts = {}
        for column in cols_to_check:
            null_count = self.df.filter(col(column).isNull()).count()
            null_counts[column] = null_count

            if null_count > 0:
                logger.warning(f"Column {column} has {null_count:,} null values")

        self.checks.append({
            'check_type': 'null_values',
            'results': null_counts,
            'timestamp': datetime.now().isoformat()
        })

        return null_counts

    def check_duplicates(self, key_columns: List[str]) -> Dict[str, Any]:
        """
        Check for duplicate records based on key columns.

        Args:
            key_columns: Columns that define uniqueness

        Returns:
            Dictionary with duplicate statistics
        """
        logger.info(f"Checking for duplicates on columns: {key_columns}")

        total_count = self.df.count()
        distinct_count = self.df.select(key_columns).distinct().count()
        duplicate_count = total_count - distinct_count

        result = {
            'total_records': total_count,
            'distinct_records': distinct_count,
            'duplicate_records': duplicate_count,
            'duplicate_percentage': (duplicate_count / total_count * 100) if total_count > 0 else 0
        }

        if duplicate_count > 0:
            logger.warning(f"Found {duplicate_count:,} duplicate records ({result['duplicate_percentage']:.2f}%)")
        else:
            logger.info("No duplicates found")

        self.checks.append({
            'check_type': 'duplicates',
            'key_columns': key_columns,
            'results': result,
            'timestamp': datetime.now().isoformat()
        })

        return result

    def check_value_ranges(
        self,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check if values are within expected range.

        Args:
            column: Column to check
            min_value: Minimum expected value
            max_value: Maximum expected value

        Returns:
            Dictionary with range validation results
        """
        logger.info(f"Checking value ranges for column: {column}")

        actual_min = self.df.agg({column: 'min'}).collect()[0][0]
        actual_max = self.df.agg({column: 'max'}).collect()[0][0]

        violations = 0
        if min_value is not None:
            violations += self.df.filter(col(column) < min_value).count()
        if max_value is not None:
            violations += self.df.filter(col(column) > max_value).count()

        result = {
            'column': column,
            'actual_min': actual_min,
            'actual_max': actual_max,
            'expected_min': min_value,
            'expected_max': max_value,
            'violations': violations
        }

        if violations > 0:
            logger.warning(f"Found {violations:,} range violations in column {column}")

        self.checks.append({
            'check_type': 'value_ranges',
            'results': result,
            'timestamp': datetime.now().isoformat()
        })

        return result

    def get_all_checks(self) -> List[Dict[str, Any]]:
        """Get all performed checks."""
        return self.checks


class RawDataReader:
    """Reads raw data from various formats."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def read_json(self, path: str, schema: Optional[StructType] = None) -> DataFrame:
        """Read JSON files from S3."""
        logger.info(f"Reading JSON from {path}")

        reader = self.spark.read.format("json")

        if schema:
            reader = reader.schema(schema)
        else:
            reader = reader.option("inferSchema", "true")

        reader = reader.option("multiLine", "true")
        reader = reader.option("mode", "PERMISSIVE")
        reader = reader.option("columnNameOfCorruptRecord", "_corrupt_record")

        df = reader.load(path)

        # Add source metadata
        df = df.withColumn("_source_file", input_file_name())
        df = df.withColumn("_ingestion_timestamp", current_timestamp())

        return df

    def read_csv(self, path: str, schema: Optional[StructType] = None) -> DataFrame:
        """Read CSV files from S3."""
        logger.info(f"Reading CSV from {path}")

        reader = self.spark.read.format("csv")

        if schema:
            reader = reader.schema(schema)
        else:
            reader = reader.option("inferSchema", "true")

        reader = reader.option("header", "true")
        reader = reader.option("mode", "PERMISSIVE")
        reader = reader.option("columnNameOfCorruptRecord", "_corrupt_record")
        reader = reader.option("encoding", "UTF-8")
        reader = reader.option("escape", "\\")
        reader = reader.option("quote", '"')

        df = reader.load(path)

        # Add source metadata
        df = df.withColumn("_source_file", input_file_name())
        df = df.withColumn("_ingestion_timestamp", current_timestamp())

        return df

    def read_avro(self, path: str) -> DataFrame:
        """Read Avro files from S3."""
        logger.info(f"Reading Avro from {path}")

        df = self.spark.read.format("avro").load(path)

        # Add source metadata
        df = df.withColumn("_source_file", input_file_name())
        df = df.withColumn("_ingestion_timestamp", current_timestamp())

        return df

    def read_with_format_detection(self, path: str) -> DataFrame:
        """Auto-detect format and read data."""
        logger.info(f"Auto-detecting format for path: {path}")

        if path.endswith('.json') or '/json/' in path:
            return self.read_json(path)
        elif path.endswith('.csv') or '/csv/' in path:
            return self.read_csv(path)
        elif path.endswith('.avro') or '/avro/' in path:
            return self.read_avro(path)
        else:
            # Try JSON as default
            logger.info("No specific format detected, trying JSON")
            return self.read_json(path)


def add_partitioning_columns(df: DataFrame, date_column: str = "_ingestion_timestamp") -> DataFrame:
    """
    Add year, month, day partitioning columns.

    Args:
        df: DataFrame to add columns to
        date_column: Column to derive partitions from

    Returns:
        DataFrame with partition columns
    """
    logger.info(f"Adding partitioning columns from {date_column}")

    df = df.withColumn("partition_year", year(col(date_column)))
    df = df.withColumn("partition_month", month(col(date_column)))
    df = df.withColumn("partition_day", dayofmonth(col(date_column)))

    return df


def add_record_hash(df: DataFrame, columns: Optional[List[str]] = None) -> DataFrame:
    """
    Add hash column for record identification and duplicate detection.

    Args:
        df: DataFrame to add hash to
        columns: Columns to include in hash (None = all columns)

    Returns:
        DataFrame with _record_hash column
    """
    logger.info("Adding record hash column")

    hash_columns = columns if columns else df.columns

    # Create concatenated string of all values
    df = df.withColumn(
        "_record_hash",
        sha2(concat_ws("|", *[col(c).cast("string") for c in hash_columns]), 256)
    )

    return df


def deduplicate_records(df: DataFrame, key_columns: List[str]) -> DataFrame:
    """
    Remove duplicate records keeping the first occurrence.

    Args:
        df: DataFrame to deduplicate
        key_columns: Columns defining uniqueness

    Returns:
        Deduplicated DataFrame
    """
    logger.info(f"Deduplicating records on columns: {key_columns}")

    initial_count = df.count()
    df_deduped = df.dropDuplicates(key_columns)
    final_count = df_deduped.count()

    duplicates_removed = initial_count - final_count

    if duplicates_removed > 0:
        logger.warning(f"Removed {duplicates_removed:,} duplicate records")
    else:
        logger.info("No duplicates found")

    return df_deduped


@error_handler(notify_on_error=True)
def main():
    """Main ETL job for raw to bronze layer."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'raw_bucket',
        'bronze_bucket',
        'raw_prefix',
        'source_format',
        'metadata_table',
        'sns_topic_arn'
    ])

    job_name = args['JOB_NAME']
    raw_bucket = args['raw_bucket']
    bronze_bucket = args['bronze_bucket']
    raw_prefix = args['raw_prefix']
    source_format = args['source_format']
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']

    logger.info(f"Starting {job_name}")
    logger.info(f"Raw bucket: s3://{raw_bucket}/{raw_prefix}")
    logger.info(f"Bronze bucket: s3://{bronze_bucket}")

    # Create Spark session
    spark = create_spark_session(
        app_name=job_name,
        additional_configs={
            "spark.sql.sources.partitionOverwriteMode": "dynamic"
        }
    )

    try:
        # Initialize components
        reader = RawDataReader(spark)
        validator = SchemaValidator()

        # Build raw data path
        raw_path = f"s3://{raw_bucket}/{raw_prefix}"

        # Read raw data based on format
        if source_format.lower() == 'json':
            df_raw = reader.read_json(raw_path)
        elif source_format.lower() == 'csv':
            df_raw = reader.read_csv(raw_path)
        elif source_format.lower() == 'avro':
            df_raw = reader.read_avro(raw_path)
        else:
            df_raw = reader.read_with_format_detection(raw_path)

        logger.info(f"Successfully read {df_raw.count():,} records from raw layer")

        # Check for corrupt records
        if "_corrupt_record" in df_raw.columns:
            corrupt_count = df_raw.filter(col("_corrupt_record").isNotNull()).count()
            if corrupt_count > 0:
                logger.error(f"Found {corrupt_count:,} corrupt records")
                # Write corrupt records to separate location
                corrupt_path = f"s3://{bronze_bucket}/corrupt/{raw_prefix}"
                df_raw.filter(col("_corrupt_record").isNotNull()).write.mode("append").json(corrupt_path)

            # Filter out corrupt records
            df_raw = df_raw.filter(col("_corrupt_record").isNull())

        # Perform data quality checks
        dq_checker = DataQualityChecker(df_raw)
        null_counts = dq_checker.check_null_values()

        # Add processing metadata
        df_bronze = df_raw.withColumn("_bronze_timestamp", current_timestamp())
        df_bronze = df_bronze.withColumn("_job_name", lit(job_name))
        df_bronze = df_bronze.withColumn("_job_run_id", lit(spark.sparkContext.applicationId))

        # Add record hash for duplicate detection
        df_bronze = add_record_hash(df_bronze)

        # Add partitioning columns
        df_bronze = add_partitioning_columns(df_bronze, "_ingestion_timestamp")

        # Collect statistics before writing
        stats = collect_stats(df_bronze)

        # Write to bronze layer in Parquet format
        bronze_path = f"s3://{bronze_bucket}/bronze/{raw_prefix}"

        df_bronze.write \
            .mode("append") \
            .partitionBy("partition_year", "partition_month", "partition_day") \
            .parquet(bronze_path)

        logger.info(f"Successfully wrote {stats['row_count']:,} records to bronze layer")

        # Write metadata to DynamoDB
        metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'source_path': raw_path,
            'target_path': bronze_path,
            'records_processed': stats['row_count'],
            'format': source_format,
            'statistics': json.dumps(stats),
            'quality_checks': json.dumps(dq_checker.get_all_checks()),
            'status': 'SUCCESS',
            'start_time': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, metadata)

        # Send success notification
        send_notification(
            topic_arn=sns_topic_arn,
            subject=f"Bronze Layer Load Success: {job_name}",
            message=f"Successfully processed {stats['row_count']:,} records\n"
                   f"Source: {raw_path}\n"
                   f"Target: {bronze_path}\n"
                   f"Statistics: {json.dumps(stats, indent=2)}",
            attributes={'status': 'SUCCESS', 'job': job_name}
        )

        logger.info(f"Job {job_name} completed successfully")

    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}")

        # Write failure metadata
        metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'status': 'FAILED',
            'error_message': str(e),
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, metadata)

        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
