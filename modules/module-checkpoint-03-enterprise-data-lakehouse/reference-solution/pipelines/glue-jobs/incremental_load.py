"""
Incremental Load Job
Implements CDC and incremental processing using Delta Lake.
Detects changes using high-water marks, performs MERGE operations,
handles deletes, optimizes file sizes, and tracks processing metadata.

Features: High-water mark tracking, MERGE operations, CDC,
delete handling, file optimization, metadata tracking.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, lit, concat_ws, sha2
)
from delta.tables import DeltaTable

from common.spark_utils import (
    create_spark_session, collect_stats, send_notification,
    write_metadata_to_dynamodb, error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HighWaterMarkManager:
    """Manages high-water marks for incremental processing."""

    def __init__(self, spark: SparkSession, metadata_table: str):
        self.spark = spark
        self.metadata_table = metadata_table

    def get_high_water_mark(
        self,
        source_table: str,
        column: str
    ) -> Any:
        """
        Get the stored high-water mark for a table.

        Args:
            source_table: Source table name
            column: Column used for high-water mark

        Returns:
            High-water mark value or None
        """
        logger.info(f"Retrieving high-water mark for {source_table}.{column}")

        try:
            # Query metadata table for last processed value
            query = f"""
                SELECT high_water_mark
                FROM {self.metadata_table}
                WHERE source_table = '{source_table}'
                AND hwm_column = '{column}'
                ORDER BY updated_timestamp DESC
                LIMIT 1
            """

            result = self.spark.sql(query).collect()

            if result:
                hwm = result[0]['high_water_mark']
                logger.info(f"Found high-water mark: {hwm}")
                return hwm
            else:
                logger.info("No high-water mark found, starting from beginning")
                return None

        except Exception as e:
            logger.warning(f"Could not retrieve high-water mark: {str(e)}")
            return None

    def update_high_water_mark(
        self,
        source_table: str,
        column: str,
        value: Any
    ) -> None:
        """
        Update the high-water mark for a table.

        Args:
            source_table: Source table name
            column: Column used for high-water mark
            value: New high-water mark value
        """
        logger.info(f"Updating high-water mark for {source_table}.{column} to {value}")

        # Create update record
        update_data = [(source_table, column, str(value), datetime.now().isoformat())]
        df = self.spark.createDataFrame(
            update_data,
            ["source_table", "hwm_column", "high_water_mark", "updated_timestamp"]
        )

        # Write to metadata table (append mode)
        df.write.mode("append").saveAsTable(self.metadata_table)

        logger.info("High-water mark updated successfully")


class IncrementalLoader:
    """Handles incremental data loading."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def extract_incremental_data(
        self,
        source_path: str,
        high_water_mark: Any,
        hwm_column: str,
        format: str = "delta"
    ) -> DataFrame:
        """
        Extract incremental data based on high-water mark.

        Args:
            source_path: Path to source data
            high_water_mark: Last processed value
            hwm_column: Column to filter on
            format: Source format (delta, parquet, etc.)

        Returns:
            DataFrame with incremental data
        """
        logger.info(f"Extracting incremental data from {source_path}")
        logger.info(f"High-water mark: {high_water_mark} on column {hwm_column}")

        # Read source data
        df = self.spark.read.format(format).load(source_path)

        # Filter for incremental data
        if high_water_mark is not None:
            df_incremental = df.filter(col(hwm_column) > lit(high_water_mark))
        else:
            # First load - take all data
            df_incremental = df

        record_count = df_incremental.count()
        logger.info(f"Extracted {record_count:,} incremental records")

        return df_incremental

    def identify_changes(
        self,
        source_df: DataFrame,
        target_path: str,
        key_columns: List[str],
        compare_columns: Optional[List[str]] = None
    ) -> Dict[str, DataFrame]:
        """
        Identify inserts, updates, and deletes.

        Args:
            source_df: Source DataFrame with new/changed records
            target_path: Path to target Delta table
            key_columns: Business key columns
            compare_columns: Columns to compare for changes

        Returns:
            Dictionary with 'inserts', 'updates', 'deletes' DataFrames
        """
        logger.info("Identifying changes (inserts, updates, deletes)")

        try:
            # Read target table
            target_df = self.spark.read.format("delta").load(target_path)

            # Add hash columns for comparison
            if compare_columns:
                cols_to_hash = compare_columns
            else:
                cols_to_hash = [c for c in source_df.columns if c not in key_columns]

            source_with_hash = source_df.withColumn(
                "_source_hash",
                sha2(concat_ws("|", *[col(c).cast("string") for c in cols_to_hash]), 256)
            )

            target_with_hash = target_df.withColumn(
                "_target_hash",
                sha2(concat_ws("|", *[col(c).cast("string") for c in cols_to_hash]), 256)
            )

            # Join source and target
            joined = source_with_hash.alias("source").join(
                target_with_hash.alias("target"),
                key_columns,
                "full_outer"
            )

            # Identify inserts (in source but not in target)
            inserts = joined.filter(
                col("target." + key_columns[0]).isNull()
            ).select("source.*").drop("_source_hash")

            # Identify updates (in both but hash differs)
            updates = joined.filter(
                (col("source._source_hash").isNotNull()) &
                (col("target._target_hash").isNotNull()) &
                (col("source._source_hash") != col("target._target_hash"))
            ).select("source.*").drop("_source_hash")

            # Identify deletes (in target but not in source)
            # Note: This requires a full scan, may not be efficient for large datasets
            deletes = joined.filter(
                col("source." + key_columns[0]).isNull()
            ).select("target.*").drop("_target_hash")

            insert_count = inserts.count()
            update_count = updates.count()
            delete_count = deletes.count()

            logger.info(f"Identified changes: {insert_count:,} inserts, "
                       f"{update_count:,} updates, {delete_count:,} deletes")

            return {
                'inserts': inserts,
                'updates': updates,
                'deletes': deletes,
                'counts': {
                    'inserts': insert_count,
                    'updates': update_count,
                    'deletes': delete_count
                }
            }

        except Exception as e:
            logger.warning(f"Could not read target table: {str(e)}. Treating all as inserts.")

            # If target doesn't exist, all records are inserts
            return {
                'inserts': source_df,
                'updates': self.spark.createDataFrame([], source_df.schema),
                'deletes': self.spark.createDataFrame([], source_df.schema),
                'counts': {
                    'inserts': source_df.count(),
                    'updates': 0,
                    'deletes': 0
                }
            }


class MergeOperationExecutor:
    """Executes MERGE operations on Delta tables."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def execute_merge(
        self,
        source_df: DataFrame,
        target_path: str,
        key_columns: List[str],
        update_columns: Optional[List[str]] = None,
        delete_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute MERGE operation on Delta table.

        Args:
            source_df: Source DataFrame with changes
            target_path: Path to target Delta table
            key_columns: Columns for matching records
            update_columns: Columns to update (None = all)
            delete_column: Column indicating deletes (e.g., 'is_deleted')

        Returns:
            Dictionary with merge metrics
        """
        logger.info(f"Executing MERGE operation on {target_path}")
        logger.info(f"Merge keys: {key_columns}")

        # Add processing metadata
        source_df = source_df.withColumn("_last_updated", current_timestamp())
        source_df = source_df.withColumn("_merge_operation", lit("MERGE"))

        try:
            # Get or create Delta table
            delta_table = DeltaTable.forPath(self.spark, target_path)

            # Build merge condition
            merge_condition = " AND ".join([
                f"target.{key} = source.{key}" for key in key_columns
            ])

            logger.info(f"Merge condition: {merge_condition}")

            # Build merge builder
            merge_builder = delta_table.alias("target").merge(
                source_df.alias("source"),
                merge_condition
            )

            # Handle deletes if delete column is specified
            if delete_column and delete_column in source_df.columns:
                logger.info(f"Handling deletes using column: {delete_column}")
                merge_builder = merge_builder.whenMatchedDelete(
                    condition=f"source.{delete_column} = true"
                )

            # Handle updates
            if update_columns:
                update_set = {col: f"source.{col}" for col in update_columns}
            else:
                update_set = {col: f"source.{col}" for col in source_df.columns}

            update_set["_last_updated"] = "current_timestamp()"

            merge_builder = merge_builder.whenMatchedUpdate(
                set=update_set
            )

            # Handle inserts
            merge_builder = merge_builder.whenNotMatchedInsertAll()

            # Execute merge
            logger.info("Executing merge operation...")
            merge_builder.execute()

            logger.info("Merge operation completed successfully")

            # Get metrics from Delta history
            history = delta_table.history(1).select("operationMetrics").collect()
            metrics = history[0]["operationMetrics"] if history else {}

            return {
                'status': 'SUCCESS',
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Merge operation failed: {str(e)}")

            # If table doesn't exist, create it
            if "Path does not exist" in str(e) or "is not a Delta table" in str(e):
                logger.info("Target table doesn't exist, creating new table")

                source_df.write.format("delta").mode("overwrite").save(target_path)

                return {
                    'status': 'SUCCESS',
                    'metrics': {'numOutputRows': source_df.count()},
                    'timestamp': datetime.now().isoformat(),
                    'note': 'Created new table'
                }
            else:
                raise

    def execute_upsert(
        self,
        source_df: DataFrame,
        target_path: str,
        key_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Execute simple upsert (insert or update) operation.

        Args:
            source_df: Source DataFrame
            target_path: Target Delta table path
            key_columns: Key columns for matching

        Returns:
            Dictionary with operation metrics
        """
        logger.info("Executing UPSERT operation")

        return self.execute_merge(
            source_df=source_df,
            target_path=target_path,
            key_columns=key_columns,
            delete_column=None
        )


class FileOptimizer:
    """Optimizes Delta table files."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def optimize_table_files(
        self,
        table_path: str,
        target_file_size_mb: int = 128,
        zorder_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Optimize Delta table file sizes.

        Args:
            table_path: Path to Delta table
            target_file_size_mb: Target file size in MB
            zorder_columns: Columns for Z-ordering

        Returns:
            Optimization metrics
        """
        logger.info(f"Optimizing table files: {table_path}")
        logger.info(f"Target file size: {target_file_size_mb} MB")

        # Get table metrics before optimization
        delta_table = DeltaTable.forPath(self.spark, table_path)

        # Count files before
        files_before = len(self.spark.read.format("delta").load(table_path).inputFiles())

        # Run OPTIMIZE
        optimize_cmd = delta_table.optimize()

        if zorder_columns:
            logger.info(f"Applying Z-ORDER on columns: {zorder_columns}")
            result = optimize_cmd.executeZOrderBy(*zorder_columns)
        else:
            result = optimize_cmd.executeCompaction()

        # Count files after
        files_after = len(self.spark.read.format("delta").load(table_path).inputFiles())

        metrics = {
            'files_before': files_before,
            'files_after': files_after,
            'files_removed': files_before - files_after,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Optimization completed: {files_before} -> {files_after} files")

        return metrics

    def vacuum_old_files(
        self,
        table_path: str,
        retention_hours: int = 168
    ) -> None:
        """
        Remove old files from Delta table.

        Args:
            table_path: Path to Delta table
            retention_hours: Retention period in hours (default: 168 = 7 days)
        """
        logger.info(f"Running VACUUM on {table_path} with {retention_hours}h retention")

        delta_table = DeltaTable.forPath(self.spark, table_path)
        delta_table.vacuum(retention_hours)

        logger.info("VACUUM completed successfully")


@error_handler(notify_on_error=True)
def main():
    """Main incremental load job."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'source_path',
        'target_path',
        'key_columns',
        'hwm_column',
        'hwm_metadata_table',
        'source_table',
        'metadata_table',
        'sns_topic_arn'
    ])

    job_name = args['JOB_NAME']
    source_path = args['source_path']
    target_path = args['target_path']
    key_columns = args['key_columns'].split(',')
    hwm_column = args['hwm_column']
    hwm_metadata_table = args['hwm_metadata_table']
    source_table = args['source_table']
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']

    logger.info(f"Starting incremental load: {job_name}")
    logger.info(f"Source: {source_path}")
    logger.info(f"Target: {target_path}")
    logger.info(f"Key columns: {key_columns}")
    logger.info(f"High-water mark column: {hwm_column}")

    # Create Spark session with Delta Lake support
    spark = create_spark_session(
        app_name=job_name,
        additional_configs={
            "spark.databricks.delta.merge.repartitionBeforeWrite.enabled": "true"
        }
    )

    try:
        # Initialize components
        hwm_manager = HighWaterMarkManager(spark, hwm_metadata_table)
        incremental_loader = IncrementalLoader(spark)
        merge_executor = MergeOperationExecutor(spark)
        file_optimizer = FileOptimizer(spark)

        # Get high-water mark
        last_hwm = hwm_manager.get_high_water_mark(source_table, hwm_column)

        # Extract incremental data
        df_incremental = incremental_loader.extract_incremental_data(
            source_path=source_path,
            high_water_mark=last_hwm,
            hwm_column=hwm_column,
            format="delta"
        )

        if df_incremental.count() == 0:
            logger.info("No new data to process")
            return

        # Execute merge operation
        merge_result = merge_executor.execute_merge(
            source_df=df_incremental,
            target_path=target_path,
            key_columns=key_columns
        )

        logger.info(f"Merge result: {merge_result}")

        # Get new high-water mark
        new_hwm = df_incremental.agg({hwm_column: 'max'}).collect()[0][0]

        # Update high-water mark
        hwm_manager.update_high_water_mark(source_table, hwm_column, new_hwm)

        # Optimize table files
        optimization_result = file_optimizer.optimize_table_files(
            table_path=target_path,
            target_file_size_mb=128,
            zorder_columns=key_columns
        )

        logger.info(f"Optimization result: {optimization_result}")

        # Vacuum old files
        file_optimizer.vacuum_old_files(target_path, retention_hours=168)

        # Collect statistics
        stats = collect_stats(df_incremental)

        # Write metadata
        job_metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'source_path': source_path,
            'target_path': target_path,
            'records_processed': stats['row_count'],
            'previous_hwm': str(last_hwm),
            'new_hwm': str(new_hwm),
            'merge_metrics': str(merge_result.get('metrics', {})),
            'optimization_metrics': str(optimization_result),
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, job_metadata)

        # Send success notification
        send_notification(
            topic_arn=sns_topic_arn,
            subject=f"Incremental Load Success: {job_name}",
            message=f"Successfully processed {stats['row_count']:,} incremental records\n"
                   f"Previous HWM: {last_hwm}\n"
                   f"New HWM: {new_hwm}\n"
                   f"Files optimized: {optimization_result['files_before']} -> {optimization_result['files_after']}",
            attributes={'status': 'SUCCESS', 'job': job_name}
        )

        logger.info("Incremental load job completed successfully")

    except Exception as e:
        logger.error(f"Incremental load job failed: {str(e)}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
