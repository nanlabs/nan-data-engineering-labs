"""
Schema Evolution Handler
Manages schema changes in Delta Lake tables.
Detects schema drift, performs ALTER TABLE operations,
migrates data, maintains backward compatibility, and logs changes.

Features: Schema drift detection, ALTER TABLE, data migration,
compatibility checks, audit logging.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit
from pyspark.sql.types import (
    StructType, StructField, DataType
)
from delta.tables import DeltaTable

from common.spark_utils import (
    create_spark_session, write_metadata_to_dynamodb,
    send_notification, error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaComparator:
    """Compares schemas to detect changes."""

    @staticmethod
    def compare_schemas(
        source_schema: StructType,
        target_schema: StructType
    ) -> Dict[str, Any]:
        """
        Compare two schemas and identify differences.

        Args:
            source_schema: New/source schema
            target_schema: Current/target schema

        Returns:
            Dictionary with schema differences
        """
        logger.info("Comparing schemas")

        source_fields = {field.name: field for field in source_schema.fields}
        target_fields = {field.name: field for field in target_schema.fields}

        # Find new columns
        new_columns = set(source_fields.keys()) - set(target_fields.keys())

        # Find removed columns
        removed_columns = set(target_fields.keys()) - set(source_fields.keys())

        # Find columns with type changes
        type_changes = []
        for field_name in set(source_fields.keys()) & set(target_fields.keys()):
            source_type = str(source_fields[field_name].dataType)
            target_type = str(target_fields[field_name].dataType)

            if source_type != target_type:
                type_changes.append({
                    'column': field_name,
                    'source_type': source_type,
                    'target_type': target_type
                })

        # Find columns with nullability changes
        nullability_changes = []
        for field_name in set(source_fields.keys()) & set(target_fields.keys()):
            source_nullable = source_fields[field_name].nullable
            target_nullable = target_fields[field_name].nullable

            if source_nullable != target_nullable:
                nullability_changes.append({
                    'column': field_name,
                    'source_nullable': source_nullable,
                    'target_nullable': target_nullable
                })

        has_changes = (
            len(new_columns) > 0 or
            len(removed_columns) > 0 or
            len(type_changes) > 0 or
            len(nullability_changes) > 0
        )

        result = {
            'has_changes': has_changes,
            'new_columns': list(new_columns),
            'removed_columns': list(removed_columns),
            'type_changes': type_changes,
            'nullability_changes': nullability_changes,
            'timestamp': datetime.now().isoformat()
        }

        if has_changes:
            logger.info(f"Schema differences detected: {result}")
        else:
            logger.info("No schema differences detected")

        return result

    @staticmethod
    def get_schema_fingerprint(schema: StructType) -> str:
        """
        Generate a fingerprint for schema versioning.

        Args:
            schema: StructType to fingerprint

        Returns:
            String fingerprint
        """
        import hashlib

        schema_string = str(sorted([
            (field.name, str(field.dataType), field.nullable)
            for field in schema.fields
        ]))

        return hashlib.md5(schema_string.encode()).hexdigest()


class SchemaEvolutionStrategy:
    """Determines strategy for handling schema changes."""

    @staticmethod
    def is_backward_compatible(schema_diff: Dict[str, Any]) -> bool:
        """
        Check if schema change is backward compatible.

        Args:
            schema_diff: Schema differences from SchemaComparator

        Returns:
            True if backward compatible
        """
        # Backward compatible changes:
        # - Adding new nullable columns
        # - Widening column types (e.g., int -> long)
        # - Making non-nullable columns nullable

        # Not backward compatible:
        # - Removing columns
        # - Changing column types incompatibly
        # - Making nullable columns non-nullable

        if len(schema_diff['removed_columns']) > 0:
            logger.warning("Schema has removed columns - not backward compatible")
            return False

        # Check type changes for compatibility
        for change in schema_diff['type_changes']:
            if not SchemaEvolutionStrategy._is_type_widening(
                change['target_type'],
                change['source_type']
            ):
                logger.warning(
                    f"Incompatible type change for {change['column']}: "
                    f"{change['target_type']} -> {change['source_type']}"
                )
                return False

        # Check nullability changes
        for change in schema_diff['nullability_changes']:
            if change['target_nullable'] and not change['source_nullable']:
                # Making nullable -> non-nullable is not backward compatible
                logger.warning(
                    f"Column {change['column']} changed from nullable to non-nullable"
                )
                return False

        logger.info("Schema changes are backward compatible")
        return True

    @staticmethod
    def _is_type_widening(from_type: str, to_type: str) -> bool:
        """Check if type change is a widening operation."""
        widening_rules = {
            'IntegerType': ['LongType', 'DoubleType', 'DecimalType'],
            'LongType': ['DoubleType', 'DecimalType'],
            'FloatType': ['DoubleType'],
            'StringType': []  # String can't be widened
        }

        for base_type, allowed_widenings in widening_rules.items():
            if base_type in from_type:
                return any(allowed in to_type for allowed in allowed_widenings)

        # If types are the same, it's compatible
        return from_type == to_type


class SchemaEvolutionExecutor:
    """Executes schema evolution operations."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def add_columns(
        self,
        table_path: str,
        new_columns: List[StructField],
        default_values: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add new columns to Delta table.

        Args:
            table_path: Path to Delta table
            new_columns: List of new StructField objects
            default_values: Optional default values for new columns
        """
        logger.info(f"Adding {len(new_columns)} new columns to {table_path}")

        delta_table = DeltaTable.forPath(self.spark, table_path)

        for field in new_columns:
            logger.info(f"Adding column: {field.name} ({field.dataType})")

            # Build ALTER TABLE statement
            sql = f"ALTER TABLE delta.`{table_path}` ADD COLUMNS ({field.name} {field.dataType})"

            try:
                self.spark.sql(sql)
                logger.info(f"Successfully added column: {field.name}")

                # Set default value if provided
                if default_values and field.name in default_values:
                    self._set_default_value(
                        table_path,
                        field.name,
                        default_values[field.name]
                    )

            except Exception as e:
                logger.error(f"Failed to add column {field.name}: {str(e)}")
                raise

    def _set_default_value(
        self,
        table_path: str,
        column_name: str,
        default_value: Any
    ) -> None:
        """Set default value for a column."""
        logger.info(f"Setting default value for {column_name}: {default_value}")

        # Read table
        df = self.spark.read.format("delta").load(table_path)

        # Update null values with default
        df = df.withColumn(
            column_name,
            when(col(column_name).isNull(), lit(default_value)).otherwise(col(column_name))
        )

        # Write back (this will create a new version)
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(table_path)

    def change_column_type(
        self,
        table_path: str,
        column_name: str,
        new_type: DataType
    ) -> None:
        """
        Change column data type.

        Args:
            table_path: Path to Delta table
            column_name: Column to change
            new_type: New data type
        """
        logger.info(f"Changing column type: {column_name} -> {new_type}")

        # Read table
        df = self.spark.read.format("delta").load(table_path)

        # Cast column to new type
        df = df.withColumn(column_name, col(column_name).cast(new_type))

        # Write back with schema overwrite
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(table_path)

        logger.info(f"Successfully changed column type for {column_name}")

    def remove_columns(
        self,
        table_path: str,
        columns_to_remove: List[str]
    ) -> None:
        """
        Remove columns from Delta table.

        Args:
            table_path: Path to Delta table
            columns_to_remove: List of column names to remove
        """
        logger.info(f"Removing columns: {columns_to_remove}")

        # Read table
        df = self.spark.read.format("delta").load(table_path)

        # Drop columns
        df = df.drop(*columns_to_remove)

        # Write back with schema overwrite
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(table_path)

        logger.info(f"Successfully removed columns: {columns_to_remove}")

    def rename_column(
        self,
        table_path: str,
        old_name: str,
        new_name: str
    ) -> None:
        """
        Rename a column.

        Args:
            table_path: Path to Delta table
            old_name: Current column name
            new_name: New column name
        """
        logger.info(f"Renaming column: {old_name} -> {new_name}")

        sql = f"ALTER TABLE delta.`{table_path}` RENAME COLUMN {old_name} TO {new_name}"

        try:
            self.spark.sql(sql)
            logger.info("Successfully renamed column")
        except Exception as e:
            logger.error(f"Failed to rename column: {str(e)}")
            raise


class SchemaMigrator:
    """Handles data migration during schema changes."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def migrate_data(
        self,
        source_df: DataFrame,
        target_schema: StructType,
        column_mappings: Optional[Dict[str, str]] = None,
        transformations: Optional[Dict[str, str]] = None
    ) -> DataFrame:
        """
        Migrate data to match target schema.

        Args:
            source_df: Source DataFrame
            target_schema: Target schema
            column_mappings: Optional dict of {source_col: target_col}
            transformations: Optional dict of {column: transformation_expr}

        Returns:
            Migrated DataFrame
        """
        logger.info("Migrating data to match target schema")

        df = source_df

        # Apply column mappings (renames)
        if column_mappings:
            for source_col, target_col in column_mappings.items():
                if source_col in df.columns:
                    df = df.withColumnRenamed(source_col, target_col)
                    logger.info(f"Mapped column: {source_col} -> {target_col}")

        # Apply transformations
        if transformations:
            for column, expr in transformations.items():
                df = df.withColumn(column, self.spark.sql(f"SELECT {expr}").first()[0])
                logger.info(f"Applied transformation to {column}")

        # Add missing columns with null values
        target_columns = {field.name: field for field in target_schema.fields}
        for col_name, field in target_columns.items():
            if col_name not in df.columns:
                logger.info(f"Adding missing column: {col_name} with null values")
                df = df.withColumn(col_name, lit(None).cast(field.dataType))

        # Remove extra columns
        extra_columns = set(df.columns) - set(target_columns.keys())
        if extra_columns:
            logger.info(f"Removing extra columns: {extra_columns}")
            df = df.drop(*extra_columns)

        # Reorder columns to match target schema
        df = df.select([field.name for field in target_schema.fields])

        logger.info("Data migration completed")
        return df


class SchemaAuditor:
    """Audits and logs schema changes."""

    def __init__(self, audit_table: str):
        self.audit_table = audit_table

    def log_schema_change(
        self,
        spark: SparkSession,
        table_name: str,
        change_type: str,
        change_details: Dict[str, Any],
        user: str = "system"
    ) -> None:
        """
        Log schema change to audit table.

        Args:
            spark: SparkSession
            table_name: Name of table that changed
            change_type: Type of change (ADD_COLUMN, REMOVE_COLUMN, etc.)
            change_details: Details of the change
            user: User who made the change
        """
        logger.info(f"Logging schema change: {change_type} for {table_name}")

        audit_record = spark.createDataFrame([{
            'table_name': table_name,
            'change_type': change_type,
            'change_details': str(change_details),
            'changed_by': user,
            'change_timestamp': datetime.now().isoformat()
        }])

        # Write to audit table
        audit_record.write.mode("append").saveAsTable(self.audit_table)

        logger.info("Schema change logged to audit table")

    def get_schema_history(
        self,
        spark: SparkSession,
        table_name: str,
        limit: int = 10
    ) -> DataFrame:
        """
        Get schema change history for a table.

        Args:
            spark: SparkSession
            table_name: Table name
            limit: Maximum number of records to return

        Returns:
            DataFrame with schema history
        """
        logger.info(f"Retrieving schema history for {table_name}")

        query = f"""
            SELECT *
            FROM {self.audit_table}
            WHERE table_name = '{table_name}'
            ORDER BY change_timestamp DESC
            LIMIT {limit}
        """

        return spark.sql(query)


@error_handler(notify_on_error=True)
def main():
    """Main schema evolution handler job."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'source_schema_path',
        'target_table_path',
        'table_name',
        'audit_table',
        'metadata_table',
        'sns_topic_arn',
        'auto_evolve'
    ])

    job_name = args['JOB_NAME']
    source_schema_path = args['source_schema_path']
    target_table_path = args['target_table_path']
    table_name = args['table_name']
    audit_table = args['audit_table']
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']
    auto_evolve = args['auto_evolve'].lower() == 'true'

    logger.info(f"Starting schema evolution handler: {job_name}")
    logger.info(f"Table: {table_name}")
    logger.info(f"Auto-evolve: {auto_evolve}")

    # Create Spark session
    spark = create_spark_session(
        app_name=job_name,
        additional_configs={
            "spark.databricks.delta.schema.autoMerge.enabled": "true"
        }
    )

    try:
        # Read source data to get new schema
        df_source = spark.read.format("delta").load(source_schema_path)
        source_schema = df_source.schema

        # Read target table to get current schema
        df_target = spark.read.format("delta").load(target_table_path)
        target_schema = df_target.schema

        logger.info(f"Source schema: {source_schema}")
        logger.info(f"Target schema: {target_schema}")

        # Compare schemas
        comparator = SchemaComparator()
        schema_diff = comparator.compare_schemas(source_schema, target_schema)

        if not schema_diff['has_changes']:
            logger.info("No schema changes detected. Exiting.")
            return

        # Check backward compatibility
        strategy = SchemaEvolutionStrategy()
        is_compatible = strategy.is_backward_compatible(schema_diff)

        if not is_compatible and not auto_evolve:
            error_msg = "Schema changes are not backward compatible and auto-evolve is disabled"
            logger.error(error_msg)

            send_notification(
                topic_arn=sns_topic_arn,
                subject=f"Schema Evolution Failed: {table_name}",
                message=f"{error_msg}\nChanges: {schema_diff}",
                attributes={'status': 'ERROR', 'job': job_name}
            )

            raise Exception(error_msg)

        # Initialize components
        executor = SchemaEvolutionExecutor(spark)
        migrator = SchemaMigrator(spark)
        auditor = SchemaAuditor(audit_table)

        # Apply schema changes
        if schema_diff['new_columns']:
            logger.info(f"Adding new columns: {schema_diff['new_columns']}")

            new_fields = [
                field for field in source_schema.fields
                if field.name in schema_diff['new_columns']
            ]

            executor.add_columns(target_table_path, new_fields)

            auditor.log_schema_change(
                spark,
                table_name,
                'ADD_COLUMNS',
                {'columns': schema_diff['new_columns']}
            )

        if schema_diff['type_changes']:
            logger.info(f"Handling type changes: {schema_diff['type_changes']}")

            for change in schema_diff['type_changes']:
                source_field = [f for f in source_schema.fields if f.name == change['column']][0]

                if auto_evolve:
                    executor.change_column_type(
                        target_table_path,
                        change['column'],
                        source_field.dataType
                    )

                    auditor.log_schema_change(
                        spark,
                        table_name,
                        'CHANGE_TYPE',
                        change
                    )

        if schema_diff['removed_columns'] and auto_evolve:
            logger.warning(f"Removing columns: {schema_diff['removed_columns']}")

            executor.remove_columns(target_table_path, schema_diff['removed_columns'])

            auditor.log_schema_change(
                spark,
                table_name,
                'REMOVE_COLUMNS',
                {'columns': schema_diff['removed_columns']}
            )

        # Write metadata
        job_metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'table_name': table_name,
            'schema_changes': str(schema_diff),
            'is_backward_compatible': is_compatible,
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, job_metadata)

        # Send notification
        send_notification(
            topic_arn=sns_topic_arn,
            subject=f"Schema Evolution Complete: {table_name}",
            message=f"Schema evolution completed successfully\n"
                   f"New columns: {len(schema_diff['new_columns'])}\n"
                   f"Type changes: {len(schema_diff['type_changes'])}\n"
                   f"Removed columns: {len(schema_diff['removed_columns'])}\n"
                   f"Backward compatible: {is_compatible}",
            attributes={'status': 'SUCCESS', 'job': job_name}
        )

        logger.info("Schema evolution completed successfully")

    except Exception as e:
        logger.error(f"Schema evolution failed: {str(e)}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
