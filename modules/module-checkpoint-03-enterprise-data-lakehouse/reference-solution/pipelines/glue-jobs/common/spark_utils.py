"""
Common Spark Utilities for Enterprise Data Lakehouse
Reusable functions for Spark session creation, Delta Lake operations,
optimization, statistics collection, and notifications.
"""

import logging
import functools
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import boto3

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, count, sum as spark_sum,
    avg, min as spark_min, max as spark_max, countDistinct
)
from pyspark.sql.types import StructType
from delta.tables import DeltaTable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SparkSessionBuilder:
    """Builder class for creating optimized Spark sessions with Delta Lake support."""

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.configs = {}
        self._set_default_configs()

    def _set_default_configs(self):
        """Set default Spark configurations for Delta Lake and optimization."""
        self.configs = {
            # Delta Lake configurations
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",

            # Performance optimizations
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.databricks.delta.optimizeWrite.enabled": "true",
            "spark.databricks.delta.autoCompact.enabled": "true",

            # Memory configurations
            "spark.sql.shuffle.partitions": "200",
            "spark.default.parallelism": "200",
            "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",

            # Delta Lake features
            "spark.databricks.delta.properties.defaults.enableChangeDataFeed": "true",
            "spark.databricks.delta.schema.autoMerge.enabled": "true",
            "spark.databricks.delta.merge.repartitionBeforeWrite.enabled": "true",

            # Parquet optimizations
            "spark.sql.parquet.compression.codec": "snappy",
            "spark.sql.parquet.mergeSchema": "false",
            "spark.sql.parquet.filterPushdown": "true",

            # S3 optimizations
            "spark.hadoop.fs.s3a.connection.maximum": "100",
            "spark.hadoop.fs.s3a.threads.max": "256",
            "spark.hadoop.fs.s3a.multiobjectdelete.enable": "true",
            "spark.hadoop.fs.s3a.fast.upload": "true",
        }

    def with_config(self, key: str, value: str):
        """Add or override a configuration."""
        self.configs[key] = value
        return self

    def with_configs(self, configs: Dict[str, str]):
        """Add or override multiple configurations."""
        self.configs.update(configs)
        return self

    def build(self) -> SparkSession:
        """Build and return the configured Spark session."""
        logger.info(f"Creating Spark session: {self.app_name}")

        builder = SparkSession.builder.appName(self.app_name)

        for key, value in self.configs.items():
            builder = builder.config(key, value)

        spark = builder.getOrCreate()

        # Set log level
        spark.sparkContext.setLogLevel("WARN")

        logger.info(f"Spark session created successfully - Version: {spark.version}")
        return spark


def create_spark_session(
    app_name: str,
    additional_configs: Optional[Dict[str, str]] = None
) -> SparkSession:
    """
    Create an optimized Spark session with Delta Lake support.

    Args:
        app_name: Name of the Spark application
        additional_configs: Optional dictionary of additional Spark configurations

    Returns:
        Configured SparkSession instance
    """
    builder = SparkSessionBuilder(app_name)

    if additional_configs:
        builder.with_configs(additional_configs)

    return builder.build()


def read_from_catalog(
    spark: SparkSession,
    database: str,
    table: str,
    filter_condition: Optional[str] = None
) -> DataFrame:
    """
    Read data from Glue Data Catalog.

    Args:
        spark: SparkSession instance
        database: Glue database name
        table: Table name
        filter_condition: Optional SQL filter condition

    Returns:
        DataFrame with the table data
    """
    logger.info(f"Reading from catalog: {database}.{table}")

    try:
        df = spark.table(f"{database}.{table}")

        if filter_condition:
            logger.info(f"Applying filter: {filter_condition}")
            df = df.filter(filter_condition)

        row_count = df.count()
        logger.info(f"Successfully read {row_count:,} rows from {database}.{table}")

        return df

    except Exception as e:
        logger.error(f"Error reading from catalog {database}.{table}: {str(e)}")
        raise


def read_from_s3(
    spark: SparkSession,
    path: str,
    format: str = "parquet",
    schema: Optional[StructType] = None,
    options: Optional[Dict[str, str]] = None
) -> DataFrame:
    """
    Read data from S3.

    Args:
        spark: SparkSession instance
        path: S3 path to read from
        format: File format (parquet, csv, json, avro, delta)
        schema: Optional schema to enforce
        options: Optional reader options

    Returns:
        DataFrame with the data
    """
    logger.info(f"Reading {format} from S3: {path}")

    try:
        reader = spark.read.format(format)

        if schema:
            reader = reader.schema(schema)

        if options:
            for key, value in options.items():
                reader = reader.option(key, value)

        df = reader.load(path)
        row_count = df.count()
        logger.info(f"Successfully read {row_count:,} rows from {path}")

        return df

    except Exception as e:
        logger.error(f"Error reading from S3 {path}: {str(e)}")
        raise


def write_to_delta(
    df: DataFrame,
    path: str,
    mode: str = "append",
    partition_cols: Optional[List[str]] = None,
    merge_schema: bool = False,
    overwrite_schema: bool = False,
    optimize_write: bool = True
) -> None:
    """
    Write DataFrame to Delta Lake.

    Args:
        df: DataFrame to write
        path: S3 path for Delta table
        mode: Write mode (append, overwrite, ignore, error)
        partition_cols: Optional list of partition columns
        merge_schema: Whether to merge schemas
        overwrite_schema: Whether to overwrite schema
        optimize_write: Whether to enable optimized writes
    """
    logger.info(f"Writing to Delta table: {path}")
    logger.info(f"Mode: {mode}, Partitions: {partition_cols}")

    try:
        writer = df.write.format("delta").mode(mode)

        if partition_cols:
            writer = writer.partitionBy(*partition_cols)

        writer = writer.option("mergeSchema", str(merge_schema).lower())
        writer = writer.option("overwriteSchema", str(overwrite_schema).lower())

        if optimize_write:
            writer = writer.option("optimizeWrite", "true")
            writer = writer.option("autoCompact", "true")

        writer.save(path)

        row_count = df.count()
        logger.info(f"Successfully wrote {row_count:,} rows to {path}")

    except Exception as e:
        logger.error(f"Error writing to Delta table {path}: {str(e)}")
        raise


def optimize_table(
    spark: SparkSession,
    path: str,
    zorder_cols: Optional[List[str]] = None,
    vacuum_hours: int = 168
) -> Dict[str, Any]:
    """
    Optimize Delta table with OPTIMIZE and VACUUM commands.

    Args:
        spark: SparkSession instance
        path: Path to Delta table
        zorder_cols: Optional list of columns for Z-ordering
        vacuum_hours: Retention hours for VACUUM (default: 168 = 7 days)

    Returns:
        Dictionary with optimization metrics
    """
    logger.info(f"Optimizing Delta table: {path}")

    try:
        delta_table = DeltaTable.forPath(spark, path)

        # Run OPTIMIZE
        optimize_cmd = delta_table.optimize()

        if zorder_cols:
            logger.info(f"Applying Z-ORDER on columns: {zorder_cols}")
            optimize_result = optimize_cmd.executeZOrderBy(*zorder_cols)
        else:
            optimize_result = optimize_cmd.executeCompaction()

        metrics = optimize_result.collect()[0].asDict() if optimize_result else {}

        # Run VACUUM
        logger.info(f"Running VACUUM with {vacuum_hours} hours retention")
        delta_table.vacuum(vacuum_hours)

        logger.info(f"Table optimization completed for {path}")
        return metrics

    except Exception as e:
        logger.error(f"Error optimizing table {path}: {str(e)}")
        raise


def collect_stats(
    df: DataFrame,
    numeric_cols: Optional[List[str]] = None,
    categorical_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Collect comprehensive statistics from a DataFrame.

    Args:
        df: DataFrame to analyze
        numeric_cols: Optional list of numeric columns for statistics
        categorical_cols: Optional list of categorical columns for cardinality

    Returns:
        Dictionary with statistics
    """
    logger.info("Collecting DataFrame statistics")

    stats = {
        "row_count": df.count(),
        "column_count": len(df.columns),
        "columns": df.columns,
        "timestamp": datetime.now().isoformat()
    }

    # Null counts for all columns
    null_counts = df.select([
        count(col(c)).alias(c) for c in df.columns
    ]).collect()[0].asDict()

    stats["null_counts"] = {
        col: stats["row_count"] - null_counts[col]
        for col in df.columns
    }

    # Numeric statistics
    if numeric_cols:
        numeric_stats = {}
        for col_name in numeric_cols:
            col_stats = df.select(
                spark_sum(col(col_name)).alias("sum"),
                avg(col(col_name)).alias("avg"),
                spark_min(col(col_name)).alias("min"),
                spark_max(col(col_name)).alias("max")
            ).collect()[0].asDict()
            numeric_stats[col_name] = col_stats

        stats["numeric_stats"] = numeric_stats

    # Cardinality for categorical columns
    if categorical_cols:
        cardinality = {}
        for col_name in categorical_cols:
            distinct_count = df.select(countDistinct(col(col_name))).collect()[0][0]
            cardinality[col_name] = distinct_count

        stats["cardinality"] = cardinality

    logger.info(f"Statistics collected: {stats['row_count']:,} rows, {stats['column_count']} columns")
    return stats


def send_notification(
    topic_arn: str,
    subject: str,
    message: str,
    attributes: Optional[Dict[str, str]] = None
) -> None:
    """
    Send SNS notification.

    Args:
        topic_arn: SNS topic ARN
        subject: Message subject
        message: Message body
        attributes: Optional message attributes
    """
    logger.info(f"Sending SNS notification to {topic_arn}")

    try:
        sns_client = boto3.client('sns')

        params = {
            'TopicArn': topic_arn,
            'Subject': subject,
            'Message': message
        }

        if attributes:
            params['MessageAttributes'] = {
                key: {'DataType': 'String', 'StringValue': value}
                for key, value in attributes.items()
            }

        response = sns_client.publish(**params)
        logger.info(f"Notification sent successfully - MessageId: {response['MessageId']}")

    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        # Don't raise - notifications should not fail the job


def write_metadata_to_dynamodb(
    table_name: str,
    item: Dict[str, Any]
) -> None:
    """
    Write metadata to DynamoDB.

    Args:
        table_name: DynamoDB table name
        item: Item to write
    """
    logger.info(f"Writing metadata to DynamoDB table: {table_name}")

    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)

        # Add timestamp if not present
        if 'timestamp' not in item:
            item['timestamp'] = datetime.now().isoformat()

        table.put_item(Item=item)
        logger.info("Metadata written successfully to DynamoDB")

    except Exception as e:
        logger.error(f"Error writing to DynamoDB: {str(e)}")
        raise


def error_handler(notify_on_error: bool = True, sns_topic_arn: Optional[str] = None):
    """
    Decorator for error handling with optional notifications.

    Args:
        notify_on_error: Whether to send SNS notification on error
        sns_topic_arn: SNS topic ARN for notifications
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.info(f"Starting execution of {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"Successfully completed {func.__name__}")
                return result

            except Exception as e:
                error_msg = f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)

                if notify_on_error and sns_topic_arn:
                    send_notification(
                        topic_arn=sns_topic_arn,
                        subject=f"Job Failed: {func.__name__}",
                        message=error_msg,
                        attributes={'severity': 'ERROR', 'job': func.__name__}
                    )

                raise

        return wrapper
    return decorator


def get_high_water_mark(
    spark: SparkSession,
    database: str,
    table: str,
    column: str
) -> Any:
    """
    Get the maximum value (high-water mark) from a column.

    Args:
        spark: SparkSession instance
        database: Database name
        table: Table name
        column: Column name to get max value from

    Returns:
        Maximum value from the column
    """
    logger.info(f"Getting high-water mark for {database}.{table}.{column}")

    try:
        result = spark.sql(f"""
            SELECT MAX({column}) as high_water_mark
            FROM {database}.{table}
        """).collect()[0]['high_water_mark']

        logger.info(f"High-water mark: {result}")
        return result

    except Exception as e:
        logger.warning(f"Could not get high-water mark: {str(e)}. Returning None")
        return None
