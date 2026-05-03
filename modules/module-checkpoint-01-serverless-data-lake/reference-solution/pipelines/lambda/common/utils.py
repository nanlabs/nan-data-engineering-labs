"""
Common utilities for Lambda functions
Shared helper functions for S3, SNS, CloudWatch, and data processing
"""

import boto3
import logging
import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from io import StringIO
import chardet

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_s3_client():
    """
    Get S3 client with error handling

    Returns:
        boto3.client: Configured S3 client
    """
    try:
        return boto3.client('s3')
    except Exception as e:
        logger.error(f"Failed to create S3 client: {str(e)}")
        raise


def get_sns_client():
    """
    Get SNS client with error handling

    Returns:
        boto3.client: Configured SNS client
    """
    try:
        return boto3.client('sns')
    except Exception as e:
        logger.error(f"Failed to create SNS client: {str(e)}")
        raise


def get_cloudwatch_client():
    """
    Get CloudWatch client with error handling

    Returns:
        boto3.client: Configured CloudWatch client
    """
    try:
        return boto3.client('cloudwatch')
    except Exception as e:
        logger.error(f"Failed to create CloudWatch client: {str(e)}")
        raise


def send_sns_alert(topic_arn: str, subject: str, message: str,
                   attributes: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send SNS notification for errors or alerts

    Args:
        topic_arn: SNS topic ARN
        subject: Alert subject
        message: Alert message body
        attributes: Optional message attributes

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sns_client = get_sns_client()

        params = {
            'TopicArn': topic_arn,
            'Subject': subject,
            'Message': message
        }

        if attributes:
            params['MessageAttributes'] = {
                key: {'DataType': 'String', 'StringValue': str(value)}
                for key, value in attributes.items()
            }

        response = sns_client.publish(**params)
        logger.info(f"SNS alert sent successfully: {response['MessageId']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send SNS alert: {str(e)}")
        return False


def validate_date_format(date_string: str, date_format: str = '%Y-%m-%d') -> bool:
    """
    Validate if string matches expected date format

    Args:
        date_string: Date string to validate
        date_format: Expected date format (default: YYYY-MM-DD)

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_string, date_format)
        return True
    except (ValueError, TypeError):
        return False


def parse_csv_with_encoding(file_content: bytes, delimiter: str = ',') -> List[Dict[str, Any]]:
    """
    Parse CSV file with automatic encoding detection

    Args:
        file_content: Raw file content as bytes
        delimiter: CSV delimiter (default: comma)

    Returns:
        List[Dict]: List of records as dictionaries
    """
    try:
        # Detect encoding
        detected = chardet.detect(file_content)
        encoding = detected['encoding'] or 'utf-8'
        logger.info(f"Detected encoding: {encoding}")

        # Decode content
        content_str = file_content.decode(encoding)

        # Parse CSV
        csv_reader = csv.DictReader(StringIO(content_str), delimiter=delimiter)
        records = list(csv_reader)

        logger.info(f"Parsed {len(records)} records from CSV")
        return records

    except Exception as e:
        logger.error(f"Failed to parse CSV: {str(e)}")
        raise


def parse_json_lines(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse JSON Lines (JSONL) file

    Args:
        file_content: Raw file content as bytes

    Returns:
        List[Dict]: List of JSON objects
    """
    try:
        content_str = file_content.decode('utf-8')
        records = []

        for line_num, line in enumerate(content_str.strip().split('\n'), 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {str(e)}")
                    continue

        logger.info(f"Parsed {len(records)} records from JSONL")
        return records

    except Exception as e:
        logger.error(f"Failed to parse JSON Lines: {str(e)}")
        raise


def log_metrics_to_cloudwatch(namespace: str, metrics: Dict[str, float],
                               dimensions: Optional[List[Dict[str, str]]] = None):
    """
    Log custom metrics to CloudWatch

    Args:
        namespace: CloudWatch namespace
        metrics: Dictionary of metric name to value
        dimensions: Optional list of dimension dictionaries
    """
    try:
        cloudwatch = get_cloudwatch_client()

        metric_data = []
        for metric_name, value in metrics.items():
            metric = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            }

            if dimensions:
                metric['Dimensions'] = dimensions

            metric_data.append(metric)

        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )

        logger.info(f"Logged {len(metrics)} metrics to CloudWatch namespace: {namespace}")

    except Exception as e:
        logger.error(f"Failed to log metrics to CloudWatch: {str(e)}")


def generate_s3_path(bucket: str, prefix: str, partition_keys: Dict[str, str],
                     filename: str) -> str:
    """
    Generate partitioned S3 path

    Args:
        bucket: S3 bucket name
        prefix: Base prefix/path
        partition_keys: Dictionary of partition key/value pairs (e.g., {'date': '2024-01-01'})
        filename: Output filename

    Returns:
        str: Full S3 path with partitions
    """
    partition_path = '/'.join([f"{key}={value}" for key, value in partition_keys.items()])
    return f"s3://{bucket}/{prefix}/{partition_path}/{filename}"


def upload_to_s3(s3_client, bucket: str, key: str, data: bytes,
                 metadata: Optional[Dict[str, str]] = None) -> bool:
    """
    Upload data to S3 with error handling

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key
        data: Data to upload as bytes
        metadata: Optional metadata dictionary

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        params = {
            'Bucket': bucket,
            'Key': key,
            'Body': data
        }

        if metadata:
            params['Metadata'] = metadata

        s3_client.put_object(**params)
        logger.info(f"Successfully uploaded to s3://{bucket}/{key}")
        return True

    except Exception as e:
        logger.error(f"Failed to upload to S3: {str(e)}")
        return False


def download_from_s3(s3_client, bucket: str, key: str) -> Optional[bytes]:
    """
    Download file from S3 with error handling

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        bytes: File content or None if failed
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        logger.info(f"Successfully downloaded s3://{bucket}/{key}")
        return content

    except Exception as e:
        logger.error(f"Failed to download from S3: {str(e)}")
        return None
