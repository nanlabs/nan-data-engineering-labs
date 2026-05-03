"""
Bronze to Silver Layer ETL Job
Cleans bronze data, applies transformations, joins across sources,
implements business rules, and maintains SCD Type 2 dimensions.

Features: Data cleaning, standardization, joins, SCD Type 2,
data quality detection, Delta Lake with Z-ordering.
"""

import sys
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import (
    col, current_timestamp, lit, trim, upper, lower,
    regexp_replace, when, coalesce, concat, concat_ws, substring, length, initcap,
    lag,
    max as spark_max, md5, datediff, current_date
)
from pyspark.sql.types import StringType, IntegerType, DateType
from delta.tables import DeltaTable

from common.spark_utils import (
    create_spark_session, read_from_s3, optimize_table, collect_stats, send_notification,
    write_metadata_to_dynamodb, error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCleaner:
    """Applies data cleaning and standardization transformations."""

    @staticmethod
    def trim_string_columns(df: DataFrame, columns: Optional[List[str]] = None) -> DataFrame:
        """Trim whitespace from string columns."""
        logger.info("Trimming string columns")

        cols_to_trim = columns if columns else [
            field.name for field in df.schema.fields
            if isinstance(field.dataType, StringType)
        ]

        for col_name in cols_to_trim:
            df = df.withColumn(col_name, trim(col(col_name)))

        return df

    @staticmethod
    def standardize_text(
        df: DataFrame,
        columns: List[str],
        case: str = 'upper'
    ) -> DataFrame:
        """
        Standardize text columns to upper or lower case.

        Args:
            df: DataFrame to clean
            columns: Columns to standardize
            case: 'upper', 'lower', or 'title'
        """
        logger.info(f"Standardizing text columns to {case} case: {columns}")

        for col_name in columns:
            if case == 'upper':
                df = df.withColumn(col_name, upper(col(col_name)))
            elif case == 'lower':
                df = df.withColumn(col_name, lower(col(col_name)))
            elif case == 'title':
                df = df.withColumn(col_name, initcap(col(col_name)))

        return df

    @staticmethod
    def remove_special_characters(
        df: DataFrame,
        columns: List[str],
        pattern: str = r'[^a-zA-Z0-9\s]'
    ) -> DataFrame:
        """Remove special characters from columns."""
        logger.info(f"Removing special characters from columns: {columns}")

        for col_name in columns:
            df = df.withColumn(
                col_name,
                regexp_replace(col(col_name), pattern, '')
            )

        return df

    @staticmethod
    def standardize_phone_numbers(df: DataFrame, column: str) -> DataFrame:
        """Standardize phone number format to (XXX) XXX-XXXX."""
        logger.info(f"Standardizing phone numbers in column: {column}")

        # Remove all non-numeric characters
        df = df.withColumn(
            f"{column}_cleaned",
            regexp_replace(col(column), r'[^0-9]', '')
        )

        # Format as (XXX) XXX-XXXX
        df = df.withColumn(
            column,
            when(length(col(f"{column}_cleaned")) == 10,
                 concat(
                     lit('('),
                     substring(col(f"{column}_cleaned"), 1, 3),
                     lit(') '),
                     substring(col(f"{column}_cleaned"), 4, 3),
                     lit('-'),
                     substring(col(f"{column}_cleaned"), 7, 4)
                 )
            ).otherwise(col(column))
        ).drop(f"{column}_cleaned")

        return df

    @staticmethod
    def standardize_email(df: DataFrame, column: str) -> DataFrame:
        """Standardize email to lowercase."""
        logger.info(f"Standardizing email in column: {column}")

        df = df.withColumn(column, lower(trim(col(column))))

        return df

    @staticmethod
    def handle_null_values(
        df: DataFrame,
        column: str,
        strategy: str = 'default',
        default_value: Any = None
    ) -> DataFrame:
        """
        Handle null values with various strategies.

        Args:
            df: DataFrame to process
            column: Column to handle nulls for
            strategy: 'default', 'drop', 'forward_fill'
            default_value: Value to use for 'default' strategy
        """
        logger.info(f"Handling null values in {column} with strategy: {strategy}")

        if strategy == 'default':
            df = df.withColumn(column, coalesce(col(column), lit(default_value)))
        elif strategy == 'drop':
            df = df.filter(col(column).isNotNull())
        elif strategy == 'forward_fill':
            window = Window.orderBy("_bronze_timestamp")
            df = df.withColumn(
                column,
                coalesce(col(column), lag(col(column)).over(window))
            )

        return df


class BusinessRulesEngine:
    """Applies business rules and transformations."""

    @staticmethod
    def calculate_age_from_birthdate(df: DataFrame, birthdate_col: str) -> DataFrame:
        """Calculate age from birthdate."""
        logger.info("Calculating age from birthdate")

        df = df.withColumn(
            "age",
            (datediff(current_date(), col(birthdate_col)) / 365.25).cast(IntegerType())
        )

        return df

    @staticmethod
    def categorize_by_value(
        df: DataFrame,
        source_col: str,
        target_col: str,
        categories: Dict[str, Any]
    ) -> DataFrame:
        """
        Categorize values based on rules.

        Args:
            df: DataFrame to process
            source_col: Source column to categorize
            target_col: Target column for category
            categories: Dict mapping conditions to category values
        """
        logger.info(f"Categorizing {source_col} into {target_col}")

        # Build when-otherwise chain
        expr = None
        for condition, category in categories.items():
            if expr is None:
                expr = when(col(source_col) == condition, category)
            else:
                expr = expr.when(col(source_col) == condition, category)

        expr = expr.otherwise("UNKNOWN")
        df = df.withColumn(target_col, expr)

        return df

    @staticmethod
    def flag_data_quality_issues(df: DataFrame) -> DataFrame:
        """Flag records with data quality issues."""
        logger.info("Flagging data quality issues")

        # Initialize quality flag as True (good quality)
        df = df.withColumn("_quality_flag", lit(True))

        # Check each column for common issues
        for field in df.schema.fields:
            col_name = field.name

            # Skip metadata columns
            if col_name.startswith('_'):
                continue

            # Flag null values in important columns
            if not field.nullable:
                df = df.withColumn(
                    "_quality_flag",
                    col("_quality_flag") & col(col_name).isNotNull()
                )

            # Flag empty strings
            if isinstance(field.dataType, StringType):
                df = df.withColumn(
                    "_quality_flag",
                    col("_quality_flag") & (length(col(col_name)) > 0)
                )

        return df

    @staticmethod
    def apply_business_calculations(df: DataFrame) -> DataFrame:
        """Apply common business calculations."""
        logger.info("Applying business calculations")

        # Example: Calculate total amount if quantity and price exist
        if 'quantity' in df.columns and 'unit_price' in df.columns:
            df = df.withColumn(
                "total_amount",
                col("quantity") * col("unit_price")
            )

        # Example: Calculate discount amount if applicable
        if 'total_amount' in df.columns and 'discount_percentage' in df.columns:
            df = df.withColumn(
                "discount_amount",
                col("total_amount") * (col("discount_percentage") / 100)
            )
            df = df.withColumn(
                "net_amount",
                col("total_amount") - col("discount_amount")
            )

        return df


class SCDType2Handler:
    """Implements Slowly Changing Dimension Type 2."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def apply_scd_type2(
        self,
        new_data: DataFrame,
        delta_table_path: str,
        business_keys: List[str],
        comparison_cols: List[str]
    ) -> None:
        """
        Apply SCD Type 2 logic to maintain historical records.

        Args:
            new_data: New data to merge
            delta_table_path: Path to Delta table
            business_keys: Columns that uniquely identify a record
            comparison_cols: Columns to compare for changes
        """
        logger.info(f"Applying SCD Type 2 for table: {delta_table_path}")
        logger.info(f"Business keys: {business_keys}")
        logger.info(f"Comparison columns: {comparison_cols}")

        # Add SCD columns to new data
        new_data = new_data.withColumn("effective_date", current_date())
        new_data = new_data.withColumn("end_date", lit(None).cast(DateType()))
        new_data = new_data.withColumn("is_current", lit(True))
        new_data = new_data.withColumn("version", lit(1))
        new_data = new_data.withColumn("_scd_processed_timestamp", current_timestamp())

        # Check if Delta table exists
        try:
            existing_table = DeltaTable.forPath(self.spark, delta_table_path)
            logger.info("Existing Delta table found, performing SCD Type 2 merge")

            # Build match condition
            match_condition = " AND ".join([
                f"existing.{key} = updates.{key}" for key in business_keys
            ])
            match_condition += " AND existing.is_current = true"

            # Build change detection condition
            change_conditions = [
                f"existing.{col} <> updates.{col} OR (existing.{col} IS NULL AND updates.{col} IS NOT NULL) OR (existing.{col} IS NOT NULL AND updates.{col} IS NULL)"
                for col in comparison_cols
            ]
            change_condition = " OR ".join(change_conditions)

            # Perform merge with SCD Type 2 logic
            existing_table.alias("existing").merge(
                new_data.alias("updates"),
                match_condition
            ).whenMatchedUpdate(
                condition=change_condition,
                set={
                    "end_date": "current_date()",
                    "is_current": "false"
                }
            ).whenNotMatchedInsertAll().execute()

            # Insert new versions of changed records
            # This is a two-step process: first close old records, then insert new ones
            # The insert happens in the whenNotMatchedInsertAll above for truly new records
            # For changed records, we need a separate insert

            changed_records = new_data.alias("new").join(
                self.spark.read.format("delta").load(delta_table_path).alias("old"),
                business_keys
            ).where(
                "old.is_current = false AND old.end_date = current_date()"
            ).select("new.*")

            if changed_records.count() > 0:
                # Get max version for each business key
                version_window = Window.partitionBy(*business_keys)

                existing_df = self.spark.read.format("delta").load(delta_table_path)
                max_versions = existing_df.groupBy(*business_keys).agg(
                    spark_max("version").alias("max_version")
                )

                changed_records = changed_records.join(max_versions, business_keys, "left")
                changed_records = changed_records.withColumn(
                    "version",
                    coalesce(col("max_version"), lit(0)) + 1
                ).drop("max_version")

                changed_records = changed_records.withColumn("effective_date", current_date())
                changed_records = changed_records.withColumn("end_date", lit(None).cast(DateType()))
                changed_records = changed_records.withColumn("is_current", lit(True))

                changed_records.write.format("delta").mode("append").save(delta_table_path)

                logger.info(f"Inserted {changed_records.count()} new versions of changed records")

        except Exception as e:
            logger.info(f"Delta table does not exist, creating new table: {str(e)}")

            # Write initial data
            new_data.write.format("delta").mode("overwrite").save(delta_table_path)
            logger.info("Created new SCD Type 2 Delta table")

    def get_current_records(self, delta_table_path: str) -> DataFrame:
        """Get only current (is_current = true) records."""
        logger.info(f"Reading current records from {delta_table_path}")

        df = self.spark.read.format("delta").load(delta_table_path)
        current_df = df.filter(col("is_current") == True)

        logger.info(f"Found {current_df.count():,} current records")
        return current_df

    def get_historical_records(
        self,
        delta_table_path: str,
        business_keys: Dict[str, Any],
        as_of_date: Optional[date] = None
    ) -> DataFrame:
        """Get historical records for specific business keys."""
        logger.info(f"Reading historical records from {delta_table_path}")

        df = self.spark.read.format("delta").load(delta_table_path)

        # Filter by business keys
        for key, value in business_keys.items():
            df = df.filter(col(key) == value)

        # Filter by date if provided
        if as_of_date:
            df = df.filter(
                (col("effective_date") <= lit(as_of_date)) &
                ((col("end_date").isNull()) | (col("end_date") > lit(as_of_date)))
            )

        return df


class DataJoiner:
    """Handles joining data from multiple sources."""

    @staticmethod
    def join_dataframes(
        left_df: DataFrame,
        right_df: DataFrame,
        join_keys: List[str],
        join_type: str = "inner",
        suffix: str = "_right"
    ) -> DataFrame:
        """
        Join two DataFrames with automatic column renaming for conflicts.

        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            join_keys: List of columns to join on
            join_type: Type of join (inner, left, right, outer)
            suffix: Suffix for conflicting columns from right DataFrame
        """
        logger.info(f"Joining DataFrames on keys: {join_keys} with {join_type} join")

        # Identify overlapping columns (excluding join keys)
        left_cols = set(left_df.columns)
        right_cols = set(right_df.columns)
        overlapping = (left_cols & right_cols) - set(join_keys)

        # Rename overlapping columns in right DataFrame
        for col_name in overlapping:
            right_df = right_df.withColumnRenamed(col_name, f"{col_name}{suffix}")

        # Perform join
        result = left_df.join(right_df, join_keys, join_type)

        logger.info(f"Join completed - Result has {result.count():,} rows")
        return result

    @staticmethod
    def enrich_with_lookup(
        df: DataFrame,
        lookup_df: DataFrame,
        join_key: str,
        lookup_columns: List[str]
    ) -> DataFrame:
        """
        Enrich DataFrame with columns from a lookup table.

        Args:
            df: DataFrame to enrich
            lookup_df: Lookup DataFrame
            join_key: Column to join on
            lookup_columns: Columns to add from lookup
        """
        logger.info(f"Enriching DataFrame with lookup on key: {join_key}")

        # Select only needed columns from lookup
        lookup_select = [join_key] + lookup_columns
        lookup_df = lookup_df.select(*lookup_select).distinct()

        # Perform left join
        result = df.join(lookup_df, join_key, "left")

        return result


@error_handler(notify_on_error=True)
def main():
    """Main ETL job for bronze to silver layer."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'bronze_bucket',
        'silver_bucket',
        'source_table',
        'target_table',
        'business_keys',
        'metadata_table',
        'sns_topic_arn'
    ])

    job_name = args['JOB_NAME']
    bronze_bucket = args['bronze_bucket']
    silver_bucket = args['silver_bucket']
    source_table = args['source_table']
    target_table = args['target_table']
    business_keys = args['business_keys'].split(',')
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']

    logger.info(f"Starting {job_name}")
    logger.info(f"Source: s3://{bronze_bucket}/bronze/{source_table}")
    logger.info(f"Target: s3://{silver_bucket}/silver/{target_table}")

    # Create Spark session with Delta Lake support
    spark = create_spark_session(
        app_name=job_name,
        additional_configs={
            "spark.databricks.delta.optimizeWrite.enabled": "true",
            "spark.databricks.delta.autoCompact.enabled": "true"
        }
    )

    try:
        # Read data from bronze layer
        bronze_path = f"s3://{bronze_bucket}/bronze/{source_table}"
        df_bronze = read_from_s3(spark, bronze_path, format="parquet")

        logger.info(f"Read {df_bronze.count():,} records from bronze layer")

        # Initialize components
        cleaner = DataCleaner()
        rules_engine = BusinessRulesEngine()
        scd_handler = SCDType2Handler(spark)

        # Apply data cleaning
        df_cleaned = cleaner.trim_string_columns(df_bronze)

        # Standardize specific columns (example)
        if 'email' in df_cleaned.columns:
            df_cleaned = cleaner.standardize_email(df_cleaned, 'email')

        if 'phone' in df_cleaned.columns:
            df_cleaned = cleaner.standardize_phone_numbers(df_cleaned, 'phone')

        # Apply business rules
        df_silver = rules_engine.apply_business_calculations(df_cleaned)
        df_silver = rules_engine.flag_data_quality_issues(df_silver)

        # Add silver layer metadata
        df_silver = df_silver.withColumn("_silver_timestamp", current_timestamp())
        df_silver = df_silver.withColumn("_silver_job_name", lit(job_name))

        # Add surrogate key
        df_silver = df_silver.withColumn(
            "_surrogate_key",
            md5(concat_ws("_", *business_keys))
        )

        # Write to silver layer with SCD Type 2
        silver_path = f"s3://{silver_bucket}/silver/{target_table}"

        # Determine columns to compare for changes (all non-metadata columns)
        comparison_cols = [
            col for col in df_silver.columns
            if not col.startswith('_') and col not in business_keys
        ]

        scd_handler.apply_scd_type2(
            new_data=df_silver,
            delta_table_path=silver_path,
            business_keys=business_keys,
            comparison_cols=comparison_cols
        )

        # Optimize Delta table with Z-ordering
        optimize_table(
            spark,
            silver_path,
            zorder_cols=business_keys,
            vacuum_hours=168
        )

        # Collect statistics
        stats = collect_stats(df_silver)

        # Write metadata
        metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'source_path': bronze_path,
            'target_path': silver_path,
            'records_processed': stats['row_count'],
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, metadata)

        # Send success notification
        send_notification(
            topic_arn=sns_topic_arn,
            subject=f"Silver Layer Load Success: {job_name}",
            message=f"Successfully processed {stats['row_count']:,} records with SCD Type 2",
            attributes={'status': 'SUCCESS', 'job': job_name}
        )

        logger.info(f"Job {job_name} completed successfully")

    except Exception as e:
        logger.error(f"Job failed: {str(e)}")

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
