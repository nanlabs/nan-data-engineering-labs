"""
Shared utilities for AWS Glue ETL jobs.
Provides common functions for data quality, metrics, schema validation, and auditing.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, lit, when
)
from awsglue.transforms import *


class GlueLogger:
    """Custom logger for Glue jobs with CloudWatch integration."""

    def __init__(self, job_name: str, run_id: str):
        self.job_name = job_name
        self.run_id = run_id
        self.start_time = datetime.now()

    def info(self, message: str, **kwargs):
        """Log info message."""
        log_entry = f"[INFO] [{self.job_name}] [{self.run_id}] {message}"
        if kwargs:
            log_entry += f" | Context: {kwargs}"
        print(log_entry)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message."""
        log_entry = f"[ERROR] [{self.job_name}] [{self.run_id}] {message}"
        if exception:
            log_entry += f" | Exception: {str(exception)}"
        if kwargs:
            log_entry += f" | Context: {kwargs}"
        print(log_entry)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        log_entry = f"[WARNING] [{self.job_name}] [{self.run_id}] {message}"
        if kwargs:
            log_entry += f" | Context: {kwargs}"
        print(log_entry)


def log_job_metrics(
    cloudwatch_client,
    job_name: str,
    namespace: str,
    metrics: Dict[str, float],
    dimensions: Optional[List[Dict[str, str]]] = None
) -> None:
    """
    Log custom metrics to CloudWatch.

    Args:
        cloudwatch_client: Boto3 CloudWatch client
        job_name: Name of the Glue job
        namespace: CloudWatch namespace for metrics
        metrics: Dictionary of metric names and values
        dimensions: Additional dimensions for metrics
    """
    try:
        if dimensions is None:
            dimensions = []

        # Add job name as default dimension
        default_dimensions = [
            {'Name': 'JobName', 'Value': job_name},
            {'Name': 'Environment', 'Value': 'production'}
        ]
        all_dimensions = default_dimensions + dimensions

        metric_data = []
        for metric_name, metric_value in metrics.items():
            metric_data.append({
                'MetricName': metric_name,
                'Value': metric_value,
                'Unit': 'None',
                'Timestamp': datetime.utcnow(),
                'Dimensions': all_dimensions
            })

        # CloudWatch allows max 20 metrics per request
        for i in range(0, len(metric_data), 20):
            batch = metric_data[i:i+20]
            cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=batch
            )

        print(f"Successfully logged {len(metrics)} metrics to CloudWatch")

    except Exception as e:
        print(f"Error logging metrics to CloudWatch: {str(e)}")


def validate_dataframe_schema(
    df: DataFrame,
    required_columns: List[str],
    logger: GlueLogger
) -> bool:
    """
    Validate that DataFrame contains required columns.

    Args:
        df: Spark DataFrame to validate
        required_columns: List of required column names
        logger: GlueLogger instance

    Returns:
        True if schema is valid, False otherwise
    """
    df_columns = set(df.columns)
    required_set = set(required_columns)

    missing_columns = required_set - df_columns

    if missing_columns:
        logger.error(
            f"Schema validation failed. Missing columns: {missing_columns}",
            actual_columns=df_columns
        )
        return False

    logger.info(
        f"Schema validation passed. All {len(required_columns)} required columns present"
    )
    return True


def apply_data_quality_checks(
    df: DataFrame,
    checks: Dict[str, Any],
    logger: GlueLogger
) -> Dict[str, Any]:
    """
    Apply data quality checks and return results.

    Args:
        df: Spark DataFrame to check
        checks: Dictionary of check configurations
        logger: GlueLogger instance

    Returns:
        Dictionary with check results and statistics
    """
    results = {
        'total_rows': df.count(),
        'checks_passed': 0,
        'checks_failed': 0,
        'check_details': []
    }

    # Null checks
    if 'null_checks' in checks:
        for column in checks['null_checks']:
            null_count = df.filter(col(column).isNull()).count()
            null_percentage = (null_count / results['total_rows'] * 100) if results['total_rows'] > 0 else 0

            check_result = {
                'check_type': 'null_check',
                'column': column,
                'null_count': null_count,
                'null_percentage': null_percentage,
                'passed': null_count == 0
            }

            results['check_details'].append(check_result)

            if check_result['passed']:
                results['checks_passed'] += 1
            else:
                results['checks_failed'] += 1
                logger.warning(
                    f"Null check failed for column '{column}'",
                    null_count=null_count,
                    null_percentage=null_percentage
                )

    # Range checks
    if 'range_checks' in checks:
        for column, (min_val, max_val) in checks['range_checks'].items():
            out_of_range = df.filter(
                (col(column) < min_val) | (col(column) > max_val)
            ).count()

            check_result = {
                'check_type': 'range_check',
                'column': column,
                'min_value': min_val,
                'max_value': max_val,
                'out_of_range_count': out_of_range,
                'passed': out_of_range == 0
            }

            results['check_details'].append(check_result)

            if check_result['passed']:
                results['checks_passed'] += 1
            else:
                results['checks_failed'] += 1
                logger.warning(
                    f"Range check failed for column '{column}'",
                    out_of_range_count=out_of_range
                )

    # Custom validation checks
    if 'custom_checks' in checks:
        for check_name, check_condition in checks['custom_checks'].items():
            failed_count = df.filter(~check_condition).count()

            check_result = {
                'check_type': 'custom_check',
                'check_name': check_name,
                'failed_count': failed_count,
                'passed': failed_count == 0
            }

            results['check_details'].append(check_result)

            if check_result['passed']:
                results['checks_passed'] += 1
            else:
                results['checks_failed'] += 1
                logger.warning(
                    f"Custom check '{check_name}' failed",
                    failed_count=failed_count
                )

    logger.info(
        "Data quality checks completed",
        total_checks=results['checks_passed'] + results['checks_failed'],
        passed=results['checks_passed'],
        failed=results['checks_failed']
    )

    return results


def create_audit_columns(df: DataFrame) -> DataFrame:
    """
    Add standard audit columns to DataFrame.

    Args:
        df: Spark DataFrame

    Returns:
        DataFrame with audit columns added
    """
    return df.withColumn('processing_timestamp', current_timestamp()) \
             .withColumn('processing_date', current_timestamp().cast('date'))


def calculate_data_quality_score(
    df: DataFrame,
    quality_checks: Dict[str, Any]
) -> DataFrame:
    """
    Calculate a data quality score for each row.

    Args:
        df: Spark DataFrame
        quality_checks: Dictionary defining quality criteria

    Returns:
        DataFrame with data_quality_score column added
    """
    score_expr = lit(100.0)

    # Deduct points for null values in important columns
    if 'critical_columns' in quality_checks:
        for column in quality_checks['critical_columns']:
            score_expr = when(
                col(column).isNull(),
                score_expr - 20
            ).otherwise(score_expr)

    # Deduct points for invalid ranges
    if 'range_penalties' in quality_checks:
        for column, (min_val, max_val, penalty) in quality_checks['range_penalties'].items():
            score_expr = when(
                (col(column) < min_val) | (col(column) > max_val),
                score_expr - penalty
            ).otherwise(score_expr)

    return df.withColumn('data_quality_score', score_expr)


def partition_dataframe(
    df: DataFrame,
    partition_columns: List[str],
    logger: GlueLogger
) -> DataFrame:
    """
    Prepare DataFrame for partitioned write by ensuring partition columns exist.

    Args:
        df: Spark DataFrame
        partition_columns: List of column names to partition by
        logger: GlueLogger instance

    Returns:
        DataFrame ready for partitioned write
    """
    for col_name in partition_columns:
        if col_name not in df.columns:
            logger.error(f"Partition column '{col_name}' not found in DataFrame")
            raise ValueError(f"Missing partition column: {col_name}")

    logger.info(f"DataFrame partitioning validated for columns: {partition_columns}")
    return df
