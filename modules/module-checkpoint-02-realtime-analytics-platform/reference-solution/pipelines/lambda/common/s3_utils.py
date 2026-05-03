"""
Common S3 utilities for Lambda processors.

Provides shared functions for writing data to S3 with partitioning.
"""

import logging
import json
import gzip
from datetime import datetime
from typing import List, Dict, Any
import io

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_client(region_name: str = 'us-east-1'):
    """
    Create and return an S3 client.

    Args:
        region_name: AWS region name

    Returns:
        boto3 S3 client
    """
    return boto3.client('s3', region_name=region_name)


def write_records_to_s3(
    bucket_name: str,
    prefix: str,
    records: List[Dict[str, Any]],
    partition_by_date: bool = True,
    partition_by_hour: bool = False,
    compress: bool = True,
    region_name: str = 'us-east-1',
    timestamp_field: str = 'timestamp'
) -> str:
    """
    Write records to S3 with date/hour partitioning.

    Args:
        bucket_name: S3 bucket name
        prefix: Prefix for S3 path (e.g., 'rides/', 'locations/')
        records: List of records to write
        partition_by_date: Whether to partition by date (year/month/day)
        partition_by_hour: Whether to partition by hour
        compress: Whether to gzip compress the data
        region_name: AWS region
        timestamp_field: Field to use for partitioning timestamp

    Returns:
        S3 key of written object
    """
    if not records:
        logger.warning("No records to write to S3")
        return None

    try:
        s3_client = get_s3_client(region_name)

        # Get current timestamp for partitioning
        now = datetime.utcnow()

        # Build S3 key with partitions
        key_parts = [prefix.rstrip('/')]

        if partition_by_date:
            key_parts.extend([
                f"year={now.year}",
                f"month={now.month:02d}",
                f"day={now.day:02d}"
            ])

        if partition_by_hour:
            key_parts.append(f"hour={now.hour:02d}")

        # Add filename with timestamp
        timestamp_str = now.strftime('%Y%m%d-%H%M%S-%f')[:-3]  # milliseconds
        filename = f"records_{timestamp_str}.json"

        if compress:
            filename += '.gz'

        key_parts.append(filename)
        s3_key = '/'.join(key_parts)

        # Prepare data
        data = '\n'.join([json.dumps(record, default=str) for record in records])

        # Compress if requested
        if compress:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
                gz.write(data.encode('utf-8'))
            data = buffer.getvalue()
            content_type = 'application/gzip'
        else:
            data = data.encode('utf-8')
            content_type = 'application/json'

        # Write to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=data,
            ContentType=content_type
        )

        logger.info(f"Wrote {len(records)} records to s3://{bucket_name}/{s3_key}")
        return s3_key

    except ClientError as e:
        logger.error(f"Error writing to S3: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing to S3: {e}")
        raise


def write_json_to_s3(
    bucket_name: str,
    key: str,
    data: Any,
    compress: bool = False,
    region_name: str = 'us-east-1'
) -> bool:
    """
    Write JSON data to S3.

    Args:
        bucket_name: S3 bucket name
        key: S3 object key
        data: Data to write (will be JSON serialized)
        compress: Whether to gzip compress
        region_name: AWS region

    Returns:
        True if successful
    """
    try:
        s3_client = get_s3_client(region_name)

        # Serialize to JSON
        json_data = json.dumps(data, default=str)

        # Compress if requested
        if compress:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
                gz.write(json_data.encode('utf-8'))
            body = buffer.getvalue()
            content_type = 'application/gzip'
        else:
            body = json_data.encode('utf-8')
            content_type = 'application/json'

        # Write to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type
        )

        logger.info(f"Wrote JSON to s3://{bucket_name}/{key}")
        return True

    except Exception as e:
        logger.error(f"Error writing JSON to S3: {e}")
        raise


def append_to_s3_file(
    bucket_name: str,
    key: str,
    new_records: List[Dict[str, Any]],
    region_name: str = 'us-east-1'
) -> bool:
    """
    Append records to an existing S3 file (newline-delimited JSON).

    Note: This downloads the existing file, appends, and re-uploads.
    For high-frequency appends, consider using batching instead.

    Args:
        bucket_name: S3 bucket name
        key: S3 object key
        new_records: Records to append
        region_name: AWS region

    Returns:
        True if successful
    """
    try:
        s3_client = get_s3_client(region_name)

        # Try to get existing file
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            existing_data = response['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                existing_data = ''
            else:
                raise

        # Append new records
        new_data = '\n'.join([json.dumps(record, default=str) for record in new_records])

        if existing_data:
            combined_data = existing_data + '\n' + new_data
        else:
            combined_data = new_data

        # Write back to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=combined_data.encode('utf-8'),
            ContentType='application/json'
        )

        logger.info(f"Appended {len(new_records)} records to s3://{bucket_name}/{key}")
        return True

    except Exception as e:
        logger.error(f"Error appending to S3 file: {e}")
        raise


def batch_records_by_partition(
    records: List[Dict[str, Any]],
    timestamp_field: str = 'timestamp'
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group records by date partition for efficient S3 writes.

    Args:
        records: List of records
        timestamp_field: Field containing timestamp

    Returns:
        Dictionary mapping partition keys to lists of records
    """
    partitions = {}

    for record in records:
        try:
            # Parse timestamp
            ts_str = record.get(timestamp_field, '')
            if ts_str:
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                partition_key = f"{dt.year}/{dt.month:02d}/{dt.day:02d}/{dt.hour:02d}"
            else:
                partition_key = 'unknown'

            if partition_key not in partitions:
                partitions[partition_key] = []

            partitions[partition_key].append(record)

        except Exception as e:
            logger.warning(f"Error parsing timestamp for record: {e}")
            if 'unknown' not in partitions:
                partitions['unknown'] = []
            partitions['unknown'].append(record)

    return partitions
