"""
Common utilities for Kinesis producers.

This module provides shared functionality for interacting with AWS Kinesis,
including client creation, batch operations, CloudWatch metrics, and error handling.
"""

import time
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import boto3
from botocore.exceptions import ClientError, BotoCoreError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KinesisProducerError(Exception):
    """Custom exception for Kinesis producer errors."""
    pass


def get_kinesis_client(region_name: str = 'us-east-1'):
    """
    Create and return a Kinesis client.

    Args:
        region_name: AWS region name

    Returns:
        boto3 Kinesis client
    """
    try:
        client = boto3.client('kinesis', region_name=region_name)
        logger.info(f"Kinesis client created for region: {region_name}")
        return client
    except Exception as e:
        logger.error(f"Failed to create Kinesis client: {e}")
        raise KinesisProducerError(f"Client creation failed: {e}")


def get_cloudwatch_client(region_name: str = 'us-east-1'):
    """
    Create and return a CloudWatch client.

    Args:
        region_name: AWS region name

    Returns:
        boto3 CloudWatch client
    """
    try:
        client = boto3.client('cloudwatch', region_name=region_name)
        logger.info(f"CloudWatch client created for region: {region_name}")
        return client
    except Exception as e:
        logger.error(f"Failed to create CloudWatch client: {e}")
        raise KinesisProducerError(f"CloudWatch client creation failed: {e}")


def generate_partition_key(data: Dict[str, Any], key_field: str = 'id') -> str:
    """
    Generate a partition key for Kinesis from data.

    Uses SHA256 hash of the key field to ensure uniform distribution.

    Args:
        data: Event data dictionary
        key_field: Field to use for partition key

    Returns:
        Partition key string
    """
    try:
        key_value = str(data.get(key_field, ''))
        if not key_value:
            # Fallback to timestamp if key field not found
            key_value = str(int(time.time() * 1000000))

        # Hash to ensure uniform distribution
        hash_object = hashlib.sha256(key_value.encode())
        partition_key = hash_object.hexdigest()[:32]  # First 32 chars
        return partition_key
    except Exception as e:
        logger.warning(f"Failed to generate partition key: {e}, using timestamp")
        return str(int(time.time() * 1000000))


def batch_put_records(
    kinesis_client,
    stream_name: str,
    records: List[Dict[str, Any]],
    partition_key_field: str = 'id',
    max_retries: int = 3,
    retry_delay: float = 0.5
) -> Dict[str, int]:
    """
    Batch put records to Kinesis with retry logic and exponential backoff.

    Args:
        kinesis_client: Boto3 Kinesis client
        stream_name: Name of the Kinesis stream
        records: List of record dictionaries to send
        partition_key_field: Field to use for partition key
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)

    Returns:
        Dictionary with success/failure counts
    """
    if not records:
        return {'success': 0, 'failed': 0}

    # Prepare records for Kinesis
    kinesis_records = []
    for record in records:
        try:
            partition_key = generate_partition_key(record, partition_key_field)
            data = json.dumps(record, default=str)

            kinesis_records.append({
                'Data': data.encode('utf-8'),
                'PartitionKey': partition_key
            })
        except Exception as e:
            logger.error(f"Failed to prepare record: {e}")
            continue

    if not kinesis_records:
        logger.warning("No valid records to send")
        return {'success': 0, 'failed': 0}

    # Split into batches of 500 (Kinesis limit)
    batch_size = 500
    batches = [kinesis_records[i:i + batch_size]
               for i in range(0, len(kinesis_records), batch_size)]

    total_success = 0
    total_failed = 0

    for batch_idx, batch in enumerate(batches):
        retry_count = 0
        current_batch = batch
        current_delay = retry_delay

        while retry_count <= max_retries:
            try:
                logger.debug(f"Sending batch {batch_idx + 1}/{len(batches)} "
                           f"with {len(current_batch)} records (attempt {retry_count + 1})")

                response = kinesis_client.put_records(
                    Records=current_batch,
                    StreamName=stream_name
                )

                failed_count = response.get('FailedRecordCount', 0)
                success_count = len(current_batch) - failed_count

                total_success += success_count

                if failed_count > 0:
                    logger.warning(f"Batch {batch_idx + 1}: {failed_count} records failed")

                    # Collect failed records for retry
                    failed_records = []
                    for idx, record_response in enumerate(response['Records']):
                        if 'ErrorCode' in record_response:
                            logger.debug(f"Record failed: {record_response.get('ErrorCode')} - "
                                       f"{record_response.get('ErrorMessage')}")
                            failed_records.append(current_batch[idx])

                    if retry_count < max_retries and failed_records:
                        logger.info(f"Retrying {len(failed_records)} failed records "
                                  f"after {current_delay}s delay")
                        time.sleep(current_delay)
                        current_batch = failed_records
                        current_delay *= 2  # Exponential backoff
                        retry_count += 1
                        continue
                    else:
                        total_failed += len(failed_records)
                        break
                else:
                    logger.debug(f"Batch {batch_idx + 1}: All {success_count} records succeeded")
                    break

            except ClientError as e:
                error_code = e.response['Error']['Code']
                logger.error(f"ClientError in batch {batch_idx + 1}: {error_code} - {e}")

                # Retry on throttling or provisioned throughput exceeded
                if error_code in ['ProvisionedThroughputExceededException', 'LimitExceededException']:
                    if retry_count < max_retries:
                        logger.info(f"Throttled, retrying after {current_delay}s delay")
                        time.sleep(current_delay)
                        current_delay *= 2
                        retry_count += 1
                        continue

                total_failed += len(current_batch)
                break

            except BotoCoreError as e:
                logger.error(f"BotoCoreError in batch {batch_idx + 1}: {e}")
                if retry_count < max_retries:
                    time.sleep(current_delay)
                    current_delay *= 2
                    retry_count += 1
                    continue
                total_failed += len(current_batch)
                break

            except Exception as e:
                logger.error(f"Unexpected error in batch {batch_idx + 1}: {e}")
                total_failed += len(current_batch)
                break

    logger.info(f"Batch put complete: {total_success} succeeded, {total_failed} failed")
    return {'success': total_success, 'failed': total_failed}


def publish_cloudwatch_metric(
    cloudwatch_client,
    namespace: str,
    metric_name: str,
    value: float,
    unit: str = 'Count',
    dimensions: Optional[List[Dict[str, str]]] = None,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    Publish a metric to CloudWatch.

    Args:
        cloudwatch_client: Boto3 CloudWatch client
        namespace: CloudWatch namespace
        metric_name: Name of the metric
        value: Metric value
        unit: Metric unit (Count, Seconds, Bytes, etc.)
        dimensions: List of dimension dictionaries
        timestamp: Metric timestamp (defaults to now)

    Returns:
        True if successful, False otherwise
    """
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': timestamp or datetime.utcnow()
        }

        if dimensions:
            metric_data['Dimensions'] = dimensions

        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )

        logger.debug(f"Published metric: {namespace}/{metric_name} = {value} {unit}")
        return True

    except Exception as e:
        logger.error(f"Failed to publish CloudWatch metric: {e}")
        return False


def validate_stream_exists(kinesis_client, stream_name: str) -> bool:
    """
    Validate that a Kinesis stream exists and is active.

    Args:
        kinesis_client: Boto3 Kinesis client
        stream_name: Name of the stream to validate

    Returns:
        True if stream exists and is active, False otherwise
    """
    try:
        response = kinesis_client.describe_stream(StreamName=stream_name)
        status = response['StreamDescription']['StreamStatus']

        if status == 'ACTIVE':
            logger.info(f"Stream '{stream_name}' is active")
            return True
        else:
            logger.warning(f"Stream '{stream_name}' exists but status is: {status}")
            return False

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error(f"Stream '{stream_name}' does not exist")
        else:
            logger.error(f"Error checking stream: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating stream: {e}")
        return False
