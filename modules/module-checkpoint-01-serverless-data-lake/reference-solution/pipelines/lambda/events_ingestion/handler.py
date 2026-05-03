"""
Events Ingestion Lambda Handler
Processes events JSON streaming data (clickstream) from landing zone
Writes to processed zone as Parquet with hourly partitions
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple
from io import BytesIO

import pandas as pd

# Add common utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.utils import (
    get_s3_client,
    send_sns_alert,
    parse_json_lines,
    log_metrics_to_cloudwatch,
    upload_to_s3,
    download_from_s3
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration from environment variables
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'serverless-data-lake-processed')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'DataLake/Events')
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '1000'))

# Schema definition
REQUIRED_COLUMNS = [
    'event_id',
    'user_id',
    'event_type',
    'timestamp',
    'properties'
]

OPTIONAL_COLUMNS = [
    'session_id',
    'device_type',
    'browser',
    'ip_address',
    'referrer'
]

VALID_EVENT_TYPES = [
    'page_view',
    'click',
    'scroll',
    'form_submit',
    'purchase',
    'add_to_cart',
    'search',
    'login',
    'logout',
    'signup'
]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for events ingestion

    Args:
        event: S3 event notification or direct invocation
        context: Lambda context

    Returns:
        Dict: Response with status and metrics
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Parse S3 event
        s3_records = event.get('Records', [])
        if not s3_records:
            raise ValueError("No S3 records found in event")

        results = []
        total_records_processed = 0
        total_records_failed = 0

        s3_client = get_s3_client()

        # Process each S3 record
        for record in s3_records:
            try:
                # Extract S3 information
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']

                logger.info(f"Processing file: s3://{bucket}/{key}")

                # Download file from S3
                file_content = download_from_s3(s3_client, bucket, key)
                if not file_content:
                    raise Exception("Failed to download file from S3")

                # Parse JSON Lines
                records = parse_json_lines(file_content)
                logger.info(f"Loaded {len(records)} records from JSONL")

                # Validate schema
                valid_records, invalid_records = validate_events_schema(records)
                logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")

                if invalid_records:
                    logger.warning(f"Found {len(invalid_records)} invalid records")
                    total_records_failed += len(invalid_records)

                # Transform and enrich data
                if valid_records:
                    df = transform_events_data(valid_records, key)

                    # Write to Parquet in batches if needed
                    write_to_parquet_batched(s3_client, df, key)

                    total_records_processed += len(valid_records)

                    results.append({
                        'file': key,
                        'status': 'success',
                        'records_processed': len(valid_records),
                        'records_failed': len(invalid_records)
                    })
                else:
                    raise ValueError("No valid records found after validation")

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                total_records_failed += len(records) if 'records' in locals() else 0

                results.append({
                    'file': key if 'key' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })

                # Send SNS alert for failure
                if SNS_TOPIC_ARN:
                    send_sns_alert(
                        SNS_TOPIC_ARN,
                        'Events Ingestion Failed',
                        f"Failed to process file: {key}\nError: {str(e)}",
                        {'severity': 'high', 'component': 'events_ingestion'}
                    )

        # Log metrics to CloudWatch
        log_metrics_to_cloudwatch(
            CLOUDWATCH_NAMESPACE,
            {
                'RecordsProcessed': total_records_processed,
                'RecordsFailed': total_records_failed,
                'FilesProcessed': len(s3_records)
            },
            [{'Name': 'Environment', 'Value': 'production'}]
        )

        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Events ingestion completed',
                'results': results,
                'total_records_processed': total_records_processed,
                'total_records_failed': total_records_failed
            })
        }

        logger.info(f"Ingestion completed: {response}")
        return response

    except Exception as e:
        logger.error(f"Critical error in lambda_handler: {str(e)}")

        # Send critical error alert
        if SNS_TOPIC_ARN:
            send_sns_alert(
                SNS_TOPIC_ARN,
                'Critical: Events Ingestion Failed',
                f"Critical error in events ingestion Lambda\nError: {str(e)}",
                {'severity': 'critical', 'component': 'events_ingestion'}
            )

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Events ingestion failed',
                'error': str(e)
            })
        }


def validate_events_schema(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate events data schema and data quality

    Args:
        records: List of event records

    Returns:
        Tuple: (valid_records, invalid_records)
    """
    valid_records = []
    invalid_records = []

    for idx, record in enumerate(records):
        errors = []

        # Check required columns
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in record or record[col] is None]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        # Validate event_id
        if 'event_id' in record and record['event_id']:
            event_id = str(record['event_id']).strip()
            if not event_id:
                errors.append("event_id cannot be empty")

        # Validate user_id
        if 'user_id' in record and record['user_id']:
            user_id = str(record['user_id']).strip()
            if not user_id:
                errors.append("user_id cannot be empty")

        # Validate event_type
        if 'event_type' in record and record['event_type']:
            event_type = str(record['event_type']).lower().strip()
            if event_type not in VALID_EVENT_TYPES:
                errors.append(f"Invalid event_type: {event_type}. Must be one of {VALID_EVENT_TYPES}")

        # Validate timestamp
        if 'timestamp' in record and record['timestamp']:
            try:
                # Try parsing ISO format timestamp
                datetime.fromisoformat(str(record['timestamp']).replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append(f"Invalid timestamp format: {record['timestamp']}")

        # Validate properties (must be dict or JSON string)
        if 'properties' in record and record['properties']:
            if not isinstance(record['properties'], (dict, str)):
                errors.append("properties must be a dict or JSON string")
            elif isinstance(record['properties'], str):
                try:
                    json.loads(record['properties'])
                except json.JSONDecodeError:
                    errors.append("properties is not valid JSON")

        if errors:
            logger.warning(f"Record {idx} validation failed: {errors}")
            invalid_records.append({
                'record': record,
                'errors': errors
            })
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_events_data(records: List[Dict[str, Any]], source_file: str) -> pd.DataFrame:
    """
    Transform and enrich events data

    Args:
        records: List of valid event records
        source_file: Source file name

    Returns:
        pd.DataFrame: Transformed dataframe
    """
    df = pd.DataFrame(records)

    # Clean and standardize required columns
    df['event_id'] = df['event_id'].astype(str).str.strip()
    df['user_id'] = df['user_id'].astype(str).str.strip()
    df['event_type'] = df['event_type'].astype(str).str.lower().str.strip()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Normalize properties column
    df['properties'] = df['properties'].apply(normalize_properties)

    # Handle optional columns
    if 'session_id' in df.columns:
        df['session_id'] = df['session_id'].fillna('').astype(str)
    else:
        df['session_id'] = ''

    if 'device_type' in df.columns:
        df['device_type'] = df['device_type'].fillna('unknown').astype(str).str.lower()
    else:
        df['device_type'] = 'unknown'

    if 'browser' in df.columns:
        df['browser'] = df['browser'].fillna('unknown').astype(str)
    else:
        df['browser'] = 'unknown'

    # Add metadata
    df['ingestion_timestamp'] = datetime.utcnow().isoformat()
    df['source_file'] = source_file

    # Add partition columns (date and hour)
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.month
    df['day'] = df['timestamp'].dt.day
    df['hour'] = df['timestamp'].dt.hour

    logger.info(f"Transformed {len(df)} event records")

    return df


def normalize_properties(properties: Any) -> str:
    """
    Normalize properties field to JSON string

    Args:
        properties: Properties field (dict or string)

    Returns:
        str: JSON string
    """
    if isinstance(properties, dict):
        return json.dumps(properties)
    elif isinstance(properties, str):
        # Validate it's proper JSON
        try:
            json.loads(properties)
            return properties
        except json.JSONDecodeError:
            return json.dumps({'raw': properties})
    else:
        return json.dumps({})


def write_to_parquet_batched(s3_client, df: pd.DataFrame, source_file: str):
    """
    Write dataframe to Parquet format in S3 processed zone
    Partitioned by date and hour, with batching for large datasets

    Args:
        s3_client: S3 client
        df: Dataframe to write
        source_file: Original source file name
    """
    try:
        # Group by partition keys (date and hour)
        for (year, month, day, hour), group_df in df.groupby(['year', 'month', 'day', 'hour']):
            # Process in batches if dataset is large
            num_batches = (len(group_df) + BATCH_SIZE - 1) // BATCH_SIZE

            for batch_idx in range(num_batches):
                start_idx = batch_idx * BATCH_SIZE
                end_idx = min((batch_idx + 1) * BATCH_SIZE, len(group_df))
                batch_df = group_df.iloc[start_idx:end_idx].copy()

                # Generate output filename
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                batch_suffix = f"_{batch_idx:04d}" if num_batches > 1 else ""
                filename = f"events_{timestamp}{batch_suffix}.parquet"

                # Create S3 key with partitions
                s3_key = f"events/year={year}/month={month:02d}/day={day:02d}/hour={hour:02d}/{filename}"

                # Convert to Parquet
                buffer = BytesIO()
                batch_df.drop(columns=['year', 'month', 'day', 'hour'], inplace=True)
                batch_df.to_parquet(buffer, engine='pyarrow', compression='snappy', index=False)
                buffer.seek(0)

                # Upload to S3
                metadata = {
                    'source_file': source_file,
                    'record_count': str(len(batch_df)),
                    'ingestion_date': datetime.utcnow().isoformat(),
                    'batch_index': str(batch_idx)
                }

                success = upload_to_s3(
                    s3_client,
                    PROCESSED_BUCKET,
                    s3_key,
                    buffer.getvalue(),
                    metadata
                )

                if success:
                    logger.info(f"Written {len(batch_df)} records to s3://{PROCESSED_BUCKET}/{s3_key}")
                else:
                    raise Exception(f"Failed to upload Parquet file: {s3_key}")

    except Exception as e:
        logger.error(f"Error writing to Parquet: {str(e)}")
        raise
