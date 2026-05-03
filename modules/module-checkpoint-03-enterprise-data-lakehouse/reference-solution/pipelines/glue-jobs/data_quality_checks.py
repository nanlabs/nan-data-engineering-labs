"""
Data Quality Checks Job
Comprehensive data quality framework using AWS Glue Data Quality.
Defines rulesets, executes checks, collects metrics, stores results,
sends alerts, and generates reports.

Features: Completeness, accuracy, consistency, timeliness checks,
DQ metrics storage, SNS alerts, HTML report generation.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import boto3

from awsglue.utils import getResolvedOptions
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, length, regexp_extract, to_date
)

from common.spark_utils import (
    create_spark_session, send_notification,
    write_metadata_to_dynamodb, error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataQualityRule:
    """Represents a single data quality rule."""

    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        rule_type: str,
        column: Optional[str] = None,
        threshold: Optional[float] = None,
        expression: Optional[str] = None,
        severity: str = "WARNING"
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.column = column
        self.threshold = threshold
        self.expression = expression
        self.severity = severity
        self.result = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'column': self.column,
            'threshold': self.threshold,
            'expression': self.expression,
            'severity': self.severity,
            'result': self.result
        }


class CompletenessChecker:
    """Checks data completeness."""

    @staticmethod
    def check_null_percentage(
        df: DataFrame,
        column: str,
        threshold: float = 5.0
    ) -> Dict[str, Any]:
        """
        Check if null percentage is below threshold.

        Args:
            df: DataFrame to check
            column: Column to check
            threshold: Maximum allowed null percentage

        Returns:
            Dictionary with check results
        """
        logger.info(f"Checking null percentage for column: {column}")

        total_count = df.count()
        null_count = df.filter(col(column).isNull()).count()
        null_percentage = (null_count / total_count * 100) if total_count > 0 else 0

        passed = null_percentage <= threshold

        result = {
            'check': 'null_percentage',
            'column': column,
            'total_records': total_count,
            'null_records': null_count,
            'null_percentage': null_percentage,
            'threshold': threshold,
            'passed': passed,
            'severity': 'ERROR' if not passed else 'PASS'
        }

        if not passed:
            logger.warning(
                f"Null percentage check failed: {column} has {null_percentage:.2f}% nulls "
                f"(threshold: {threshold}%)"
            )

        return result

    @staticmethod
    def check_empty_strings(
        df: DataFrame,
        column: str,
        threshold: float = 5.0
    ) -> Dict[str, Any]:
        """Check for empty string percentage."""
        logger.info(f"Checking empty strings for column: {column}")

        total_count = df.count()
        empty_count = df.filter(
            (col(column) == '') | (length(col(column)) == 0)
        ).count()
        empty_percentage = (empty_count / total_count * 100) if total_count > 0 else 0

        passed = empty_percentage <= threshold

        result = {
            'check': 'empty_strings',
            'column': column,
            'total_records': total_count,
            'empty_records': empty_count,
            'empty_percentage': empty_percentage,
            'threshold': threshold,
            'passed': passed,
            'severity': 'WARNING' if not passed else 'PASS'
        }

        return result

    @staticmethod
    def check_required_columns(
        df: DataFrame,
        required_columns: List[str]
    ) -> Dict[str, Any]:
        """Check if all required columns are present."""
        logger.info(f"Checking required columns: {required_columns}")

        missing_columns = [col for col in required_columns if col not in df.columns]
        passed = len(missing_columns) == 0

        result = {
            'check': 'required_columns',
            'required_columns': required_columns,
            'missing_columns': missing_columns,
            'passed': passed,
            'severity': 'ERROR' if not passed else 'PASS'
        }

        if not passed:
            logger.error(f"Missing required columns: {missing_columns}")

        return result


class AccuracyChecker:
    """Checks data accuracy."""

    @staticmethod
    def check_value_range(
        df: DataFrame,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """Check if values are within expected range."""
        logger.info(f"Checking value range for column: {column}")

        total_count = df.count()
        violations = 0

        if min_value is not None:
            violations += df.filter(col(column) < min_value).count()

        if max_value is not None:
            violations += df.filter(col(column) > max_value).count()

        violation_percentage = (violations / total_count * 100) if total_count > 0 else 0
        passed = violations == 0

        actual_min = df.agg({column: 'min'}).collect()[0][0]
        actual_max = df.agg({column: 'max'}).collect()[0][0]

        result = {
            'check': 'value_range',
            'column': column,
            'expected_min': min_value,
            'expected_max': max_value,
            'actual_min': actual_min,
            'actual_max': actual_max,
            'violations': violations,
            'violation_percentage': violation_percentage,
            'passed': passed,
            'severity': 'ERROR' if not passed else 'PASS'
        }

        if not passed:
            logger.warning(
                f"Value range check failed: {column} has {violations} violations "
                f"({violation_percentage:.2f}%)"
            )

        return result

    @staticmethod
    def check_format_pattern(
        df: DataFrame,
        column: str,
        pattern: str,
        pattern_name: str = "custom"
    ) -> Dict[str, Any]:
        """Check if values match a regex pattern."""
        logger.info(f"Checking format pattern for column: {column}")

        total_count = df.count()

        # Extract values that match pattern
        matched_count = df.filter(
            regexp_extract(col(column), pattern, 0) != ''
        ).count()

        match_percentage = (matched_count / total_count * 100) if total_count > 0 else 0
        passed = match_percentage >= 95.0  # 95% should match

        result = {
            'check': 'format_pattern',
            'column': column,
            'pattern': pattern,
            'pattern_name': pattern_name,
            'total_records': total_count,
            'matched_records': matched_count,
            'match_percentage': match_percentage,
            'passed': passed,
            'severity': 'WARNING' if not passed else 'PASS'
        }

        if not passed:
            logger.warning(
                f"Format pattern check failed: {column} only has {match_percentage:.2f}% "
                f"matching pattern {pattern_name}"
            )

        return result

    @staticmethod
    def check_valid_dates(
        df: DataFrame,
        column: str,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if dates are valid and within range."""
        logger.info(f"Checking valid dates for column: {column}")

        # Convert to date
        df_with_date = df.withColumn(f"{column}_parsed", to_date(col(column)))

        total_count = df.count()
        invalid_count = df_with_date.filter(col(f"{column}_parsed").isNull()).count()

        violations = 0
        if min_date:
            violations += df_with_date.filter(col(f"{column}_parsed") < lit(min_date)).count()
        if max_date:
            violations += df_with_date.filter(col(f"{column}_parsed") > lit(max_date)).count()

        total_issues = invalid_count + violations
        issue_percentage = (total_issues / total_count * 100) if total_count > 0 else 0
        passed = total_issues == 0

        result = {
            'check': 'valid_dates',
            'column': column,
            'total_records': total_count,
            'invalid_dates': invalid_count,
            'out_of_range': violations,
            'issue_percentage': issue_percentage,
            'passed': passed,
            'severity': 'ERROR' if not passed else 'PASS'
        }

        return result


class ConsistencyChecker:
    """Checks data consistency."""

    @staticmethod
    def check_referential_integrity(
        df: DataFrame,
        parent_df: DataFrame,
        foreign_key: str,
        parent_key: str
    ) -> Dict[str, Any]:
        """Check referential integrity between tables."""
        logger.info(f"Checking referential integrity: {foreign_key} -> {parent_key}")

        # Find orphaned records
        orphaned = df.join(
            parent_df.select(parent_key).distinct(),
            df[foreign_key] == parent_df[parent_key],
            "left_anti"
        ).filter(col(foreign_key).isNotNull())

        total_count = df.count()
        orphaned_count = orphaned.count()
        orphan_percentage = (orphaned_count / total_count * 100) if total_count > 0 else 0

        passed = orphaned_count == 0

        result = {
            'check': 'referential_integrity',
            'foreign_key': foreign_key,
            'parent_key': parent_key,
            'total_records': total_count,
            'orphaned_records': orphaned_count,
            'orphan_percentage': orphan_percentage,
            'passed': passed,
            'severity': 'ERROR' if not passed else 'PASS'
        }

        if not passed:
            logger.warning(
                f"Referential integrity check failed: {orphaned_count} orphaned records "
                f"({orphan_percentage:.2f}%)"
            )

        return result

    @staticmethod
    def check_duplicate_keys(
        df: DataFrame,
        key_columns: List[str],
        threshold: float = 0.0
    ) -> Dict[str, Any]:
        """Check for duplicate keys."""
        logger.info(f"Checking duplicates on keys: {key_columns}")

        total_count = df.count()
        distinct_count = df.select(key_columns).distinct().count()
        duplicate_count = total_count - distinct_count
        duplicate_percentage = (duplicate_count / total_count * 100) if total_count > 0 else 0

        passed = duplicate_percentage <= threshold

        result = {
            'check': 'duplicate_keys',
            'key_columns': key_columns,
            'total_records': total_count,
            'distinct_records': distinct_count,
            'duplicate_records': duplicate_count,
            'duplicate_percentage': duplicate_percentage,
            'threshold': threshold,
            'passed': passed,
            'severity': 'ERROR' if not passed else 'PASS'
        }

        if not passed:
            logger.warning(
                f"Duplicate key check failed: {duplicate_count} duplicates "
                f"({duplicate_percentage:.2f}%)"
            )

        return result

    @staticmethod
    def check_cross_field_validation(
        df: DataFrame,
        field1: str,
        field2: str,
        condition: str
    ) -> Dict[str, Any]:
        """Check cross-field validation rules."""
        logger.info(f"Checking cross-field validation: {condition}")

        total_count = df.count()
        violations = df.filter(~col(condition)).count()
        violation_percentage = (violations / total_count * 100) if total_count > 0 else 0

        passed = violations == 0

        result = {
            'check': 'cross_field_validation',
            'field1': field1,
            'field2': field2,
            'condition': condition,
            'total_records': total_count,
            'violations': violations,
            'violation_percentage': violation_percentage,
            'passed': passed,
            'severity': 'WARNING' if not passed else 'PASS'
        }

        return result


class TimelinessChecker:
    """Checks data timeliness."""

    @staticmethod
    def check_data_freshness(
        df: DataFrame,
        timestamp_column: str,
        max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """Check if data is recent enough."""
        logger.info(f"Checking data freshness for column: {timestamp_column}")

        from datetime import datetime, timedelta

        threshold_time = datetime.now() - timedelta(hours=max_age_hours)

        total_count = df.count()
        stale_count = df.filter(col(timestamp_column) < lit(threshold_time)).count()
        stale_percentage = (stale_count / total_count * 100) if total_count > 0 else 0

        max_timestamp = df.agg({timestamp_column: 'max'}).collect()[0][0]

        passed = stale_percentage < 10.0  # Less than 10% stale

        result = {
            'check': 'data_freshness',
            'column': timestamp_column,
            'max_age_hours': max_age_hours,
            'max_timestamp': str(max_timestamp),
            'total_records': total_count,
            'stale_records': stale_count,
            'stale_percentage': stale_percentage,
            'passed': passed,
            'severity': 'WARNING' if not passed else 'PASS'
        }

        return result


class DataQualityMetrics:
    """Collects and stores data quality metrics."""

    def __init__(self):
        self.metrics = {
            'completeness': [],
            'accuracy': [],
            'consistency': [],
            'timeliness': [],
            'summary': {}
        }

    def add_check_result(self, category: str, result: Dict[str, Any]):
        """Add a check result to metrics."""
        if category in self.metrics:
            self.metrics[category].append(result)

    def calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary metrics."""
        total_checks = sum(len(checks) for checks in self.metrics.values() if isinstance(checks, list))
        passed_checks = sum(
            sum(1 for check in checks if check.get('passed', False))
            for checks in self.metrics.values()
            if isinstance(checks, list)
        )

        failed_checks = total_checks - passed_checks
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        # Count by severity
        errors = sum(
            sum(1 for check in checks if check.get('severity') == 'ERROR' and not check.get('passed', False))
            for checks in self.metrics.values()
            if isinstance(checks, list)
        )

        warnings = sum(
            sum(1 for check in checks if check.get('severity') == 'WARNING' and not check.get('passed', False))
            for checks in self.metrics.values()
            if isinstance(checks, list)
        )

        self.metrics['summary'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'pass_rate': pass_rate,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }

        return self.metrics['summary']

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics


class HTMLReportGenerator:
    """Generates HTML reports for data quality results."""

    @staticmethod
    def generate_report(metrics: Dict[str, Any], table_name: str) -> str:
        """Generate HTML report from metrics."""
        logger.info("Generating HTML data quality report")

        summary = metrics.get('summary', {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Quality Report - {table_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .metric {{ display: inline-block; margin-right: 30px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .error {{ background-color: #ffcccc; }}
        .warning {{ background-color: #fff4cc; }}
        .pass {{ background-color: #ccffcc; }}
    </style>
</head>
<body>
    <h1>Data Quality Report: {table_name}</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">Total Checks: <strong>{summary.get('total_checks', 0)}</strong></div>
        <div class="metric passed">Passed: <strong>{summary.get('passed_checks', 0)}</strong></div>
        <div class="metric failed">Failed: <strong>{summary.get('failed_checks', 0)}</strong></div>
        <div class="metric">Pass Rate: <strong>{summary.get('pass_rate', 0):.2f}%</strong></div>
        <div class="metric failed">Errors: <strong>{summary.get('errors', 0)}</strong></div>
        <div class="metric">Warnings: <strong>{summary.get('warnings', 0)}</strong></div>
    </div>
"""

        # Add tables for each category
        for category in ['completeness', 'accuracy', 'consistency', 'timeliness']:
            checks = metrics.get(category, [])
            if checks:
                html += f"<h2>{category.capitalize()} Checks</h2>\n<table>\n"
                html += "<tr><th>Check</th><th>Details</th><th>Result</th><th>Severity</th></tr>\n"

                for check in checks:
                    row_class = check.get('severity', 'PASS').lower()
                    result_text = "PASS" if check.get('passed', False) else "FAIL"

                    details = json.dumps({k: v for k, v in check.items() if k not in ['check', 'passed', 'severity']})

                    html += f"""
                    <tr class="{row_class}">
                        <td>{check.get('check', 'Unknown')}</td>
                        <td><pre>{details}</pre></td>
                        <td>{result_text}</td>
                        <td>{check.get('severity', 'UNKNOWN')}</td>
                    </tr>
"""

                html += "</table>\n"

        html += """
</body>
</html>
"""

        return html


@error_handler(notify_on_error=True)
def main():
    """Main data quality checks job."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'database',
        'table_name',
        'dq_results_bucket',
        'metadata_table',
        'sns_topic_arn'
    ])

    job_name = args['JOB_NAME']
    database = args['database']
    table_name = args['table_name']
    dq_results_bucket = args['dq_results_bucket']
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']

    logger.info(f"Starting Data Quality Checks: {job_name}")
    logger.info(f"Target table: {database}.{table_name}")

    # Create Spark session
    spark = create_spark_session(app_name=job_name)

    try:
        # Read data from table
        df = spark.table(f"{database}.{table_name}")
        logger.info(f"Read {df.count():,} records from {database}.{table_name}")

        # Initialize checkers and metrics
        completeness_checker = CompletenessChecker()
        accuracy_checker = AccuracyChecker()
        consistency_checker = ConsistencyChecker()
        timeliness_checker = TimelinessChecker()
        metrics = DataQualityMetrics()

        # Run completeness checks
        for column in df.columns:
            if not column.startswith('_'):
                result = completeness_checker.check_null_percentage(df, column, threshold=5.0)
                metrics.add_check_result('completeness', result)

        # Run accuracy checks (examples)
        numeric_columns = [
            field.name for field in df.schema.fields
            if str(field.dataType) in ['IntegerType', 'LongType', 'DoubleType', 'FloatType']
        ]

        for column in numeric_columns[:5]:  # Check first 5 numeric columns
            result = accuracy_checker.check_value_range(df, column)
            metrics.add_check_result('accuracy', result)

        # Run consistency checks
        # Example: Check for duplicates on key columns (if they exist)
        if 'id' in df.columns or 'customer_id' in df.columns:
            key_col = 'id' if 'id' in df.columns else 'customer_id'
            result = consistency_checker.check_duplicate_keys(df, [key_col])
            metrics.add_check_result('consistency', result)

        # Run timeliness checks
        timestamp_columns = [
            field.name for field in df.schema.fields
            if 'timestamp' in field.name.lower() or 'date' in field.name.lower()
        ]

        if timestamp_columns:
            result = timeliness_checker.check_data_freshness(df, timestamp_columns[0])
            metrics.add_check_result('timeliness', result)

        # Calculate summary
        summary = metrics.calculate_summary()
        logger.info(f"Data Quality Summary: {summary}")

        # Generate HTML report
        report_generator = HTMLReportGenerator()
        html_report = report_generator.generate_report(metrics.get_all_metrics(), table_name)

        # Upload report to S3
        s3_client = boto3.client('s3')
        report_key = f"dq-reports/{table_name}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_report.html"

        s3_client.put_object(
            Bucket=dq_results_bucket,
            Key=report_key,
            Body=html_report.encode('utf-8'),
            ContentType='text/html'
        )

        logger.info(f"Report uploaded to s3://{dq_results_bucket}/{report_key}")

        # Store results in DynamoDB
        dq_metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'table_name': f"{database}.{table_name}",
            'summary': json.dumps(summary),
            'report_location': f"s3://{dq_results_bucket}/{report_key}",
            'status': 'PASS' if summary['failed_checks'] == 0 else 'FAIL',
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, dq_metadata)

        # Send notification
        if summary['errors'] > 0:
            send_notification(
                topic_arn=sns_topic_arn,
                subject=f"Data Quality ERRORS Detected: {table_name}",
                message=f"Data quality checks found {summary['errors']} errors and {summary['warnings']} warnings.\n"
                       f"Pass rate: {summary['pass_rate']:.2f}%\n"
                       f"Report: s3://{dq_results_bucket}/{report_key}",
                attributes={'status': 'ERROR', 'job': job_name}
            )
        elif summary['warnings'] > 0:
            send_notification(
                topic_arn=sns_topic_arn,
                subject=f"Data Quality Warnings: {table_name}",
                message=f"Data quality checks found {summary['warnings']} warnings.\n"
                       f"Pass rate: {summary['pass_rate']:.2f}%\n"
                       f"Report: s3://{dq_results_bucket}/{report_key}",
                attributes={'status': 'WARNING', 'job': job_name}
            )

        logger.info("Data quality checks completed successfully")

    except Exception as e:
        logger.error(f"Data quality checks failed: {str(e)}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
