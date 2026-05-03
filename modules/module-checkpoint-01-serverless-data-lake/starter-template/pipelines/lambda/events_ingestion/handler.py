"""
Events Ingestion Lambda Handler - STARTER TEMPLATE
Processes events JSONL (JSON Lines) files from landing zone

KEY DIFFERENCES:
- Input format: JSONL (newline-delimited JSON, not CSV or single JSON)
- High volume streaming data (clickstream, page views, etc.)
- May need to batch process many small events

TODO SECTIONS:
1. Parse S3 event
2. Download and parse JSONL file
3. Validate event schema
4. Transform and enrich events
5. Write Parquet
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', '')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

# Schema for events
REQUIRED_COLUMNS = [
    'event_id',
    'event_type',
    'customer_id',
    'timestamp',
    'session_id'
]

OPTIONAL_COLUMNS = [
    'page_url',
    'product_id',
    'event_properties'
]

VALID_EVENT_TYPES = ['page_view', 'product_view', 'add_to_cart', 'purchase', 'search']


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for events ingestion"""
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # TODO 1: Parse S3 Event
        s3_records = event.get('Records', [])
        if not s3_records:
            raise ValueError("No S3 records found")

        results = []
        total_processed = 0
        total_failed = 0

        # TODO: Create S3 client
        s3_client = None  # TODO

        for record in s3_records:
            try:
                # TODO: Extract bucket and key
                bucket = None  # TODO
                key = None     # TODO

                logger.info(f"Processing: s3://{bucket}/{key}")

                # ===================================================================
                # TODO 2: Download and Parse JSONL File
                # ===================================================================
                # HINT: JSONL has one JSON object per line
                # Need to read line by line and parse each as JSON

                # TODO: Download file
                # response = s3_client.get_object(Bucket=bucket, Key=key)
                # file_content = response['Body'].read().decode('utf-8')
                file_content = None  # TODO

                if not file_content:
                    raise Exception("Failed to download file")

                # TODO: Parse JSONL (one JSON object per line)
                # HINT: Split by newline and parse each line as JSON
                # records = []
                # for line in file_content.strip().split('\n'):
                #     if line.strip():
                #         records.append(json.loads(line))
                records = []  # TODO: Parse JSONL

                logger.info(f"Loaded {len(records)} events from JSONL")

                # TODO 3: Validate Schema
                # valid_records, invalid_records = validate_events_schema(records)
                valid_records = []
                invalid_records = []

                if invalid_records:
                    logger.warning(f"Invalid records: {len(invalid_records)}")
                    total_failed += len(invalid_records)

                # TODO 4: Transform Data
                if valid_records:
                    # df_transformed = transform_events_data(valid_records, key)
                    df_transformed = None  # TODO

                    # TODO 5: Write Parquet
                    # success = write_to_parquet(s3_client, df_transformed, key)
                    success = False  # TODO

                    if success:
                        total_processed += len(valid_records)
                        results.append({
                            'file': key,
                            'status': 'success',
                            'records_processed': len(valid_records)
                        })
                    else:
                        raise Exception("Failed to write Parquet")
                else:
                    raise ValueError("No valid records")

            except Exception as e:
                logger.error(f"Error: {str(e)}")
                results.append({
                    'file': key if 'key' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Events ingestion completed',
                'results': results,
                'total_processed': total_processed,
                'total_failed': total_failed
            })
        }

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Events ingestion failed',
                'error': str(e)
            })
        }


def validate_events_schema(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """Validate events data schema"""
    valid_records = []
    invalid_records = []

    for record in records:
        errors = []

        # TODO: Check required columns
        # for col in REQUIRED_COLUMNS:
        #     if col not in record or not record[col]:
        #         errors.append(f"Missing: {col}")

        # TODO: Validate timestamp format
        # HINT: Try parsing with datetime.fromisoformat() or similar
        # try:
        #     datetime.fromisoformat(str(record['timestamp']).replace('Z', '+00:00'))
        # except (ValueError, TypeError):
        #     errors.append("Invalid timestamp format")

        # TODO: Validate event_type is in VALID_EVENT_TYPES
        # event_type = record.get('event_type', '').lower()
        # if event_type not in VALID_EVENT_TYPES:
        #     errors.append(f"Invalid event_type: {event_type}")

        # TODO: Validate event_id and session_id are not empty
        # if not str(record.get('event_id', '')).strip():
        #     errors.append("event_id cannot be empty")

        if errors:
            record['_validation_errors'] = errors
            invalid_records.append(record)
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_events_data(records: List[Dict], source_file: str) -> pd.DataFrame:
    """Transform and enrich events data"""
    df = pd.DataFrame(records)

    # TODO: Convert timestamp to datetime
    # df['timestamp'] = pd.to_datetime(df['timestamp'])

    # TODO: Standardize event_type to lowercase
    # df['event_type'] = df['event_type'].str.lower().str.strip()

    # TODO: Extract date components for partitioning
    # df['year'] = df['timestamp'].dt.year
    # df['month'] = df['timestamp'].dt.month
    # df['day'] = df['timestamp'].dt.day
    # df['hour'] = df['timestamp'].dt.hour

    # TODO: Flatten event_properties if it's nested JSON
    # HINT: Use pd.json_normalize() if event_properties is a dict
    # if 'event_properties' in df.columns:
    #     # Handle nested properties
    #     pass

    # TODO: Add audit columns
    # df['processed_timestamp'] = datetime.utcnow()
    # df['source_file'] = source_file

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_key: str) -> bool:
    """Write DataFrame to S3 as Parquet"""
    try:
        # TODO: Generate partitioned path for time-series data
        # HINT: Events are often partitioned by date/hour
        # Format: events/year=2024/month=03/day=09/hour=14/events_timestamp.parquet

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_key = f"events/events_{timestamp}.parquet"

        # TODO: Write Parquet and upload
        # parquet_buffer = BytesIO()
        # df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy', index=False)
        # parquet_buffer.seek(0)
        #
        # s3_client.put_object(
        #     Bucket=PROCESSED_BUCKET,
        #     Key=output_key,
        #     Body=parquet_buffer
        # )

        logger.info(f"Wrote Parquet to s3://{PROCESSED_BUCKET}/{output_key}")
        return True

    except Exception as e:
        logger.error(f"Failed to write Parquet: {str(e)}")
        return False
