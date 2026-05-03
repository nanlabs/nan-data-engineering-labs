"""
Customers Ingestion Lambda Handler
Processes customers JSON files from landing zone and writes to processed zone as Parquet
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
    validate_date_format,
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
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'DataLake/Customers')

# Schema definition
REQUIRED_COLUMNS = [
    'customer_id',
    'name',
    'email',
    'country',
    'signup_date'
]

OPTIONAL_COLUMNS = [
    'phone',
    'address',
    'city',
    'state',
    'postal_code',
    'account_status'
]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for customers ingestion

    Args:
        event: S3 event notification
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

                # Parse JSON (support both single JSON and JSONL)
                records = parse_json_file(file_content)
                logger.info(f"Loaded {len(records)} records from JSON")

                # Validate schema
                valid_records, invalid_records = validate_customers_schema(records)
                logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")

                if invalid_records:
                    logger.warning(f"Found {len(invalid_records)} invalid records")
                    total_records_failed += len(invalid_records)

                # Transform and enrich data
                if valid_records:
                    df = transform_customers_data(valid_records, key)

                    # Write to Parquet in processed zone
                    write_to_parquet(s3_client, df, key)

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
                        'Customers Ingestion Failed',
                        f"Failed to process file: {key}\nError: {str(e)}",
                        {'severity': 'high', 'component': 'customers_ingestion'}
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
                'message': 'Customers ingestion completed',
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
                'Critical: Customers Ingestion Failed',
                f"Critical error in customers ingestion Lambda\nError: {str(e)}",
                {'severity': 'critical', 'component': 'customers_ingestion'}
            )

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Customers ingestion failed',
                'error': str(e)
            })
        }


def parse_json_file(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse JSON file (supports both single JSON array and JSONL format)

    Args:
        file_content: Raw file content as bytes

    Returns:
        List[Dict]: List of customer records
    """
    try:
        content_str = file_content.decode('utf-8')

        # Try parsing as single JSON array first
        try:
            data = json.loads(content_str)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass

        # If that fails, try JSONL format
        return parse_json_lines(file_content)

    except Exception as e:
        logger.error(f"Failed to parse JSON file: {str(e)}")
        raise


def validate_customers_schema(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate customers data schema and data quality

    Args:
        records: List of customer records

    Returns:
        Tuple: (valid_records, invalid_records)
    """
    valid_records = []
    invalid_records = []

    for idx, record in enumerate(records):
        errors = []

        # Check required columns
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in record or not record[col]]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        # Validate customer_id
        if 'customer_id' in record and record['customer_id']:
            customer_id = str(record['customer_id']).strip()
            if not customer_id:
                errors.append("customer_id cannot be empty")

        # Validate name
        if 'name' in record and record['name']:
            name = str(record['name']).strip()
            if len(name) < 2:
                errors.append("name must be at least 2 characters")

        # Validate email
        if 'email' in record and record['email']:
            email = str(record['email']).strip()
            if '@' not in email or '.' not in email:
                errors.append(f"Invalid email format: {email}")

        # Validate country
        if 'country' in record and record['country']:
            country = str(record['country']).strip()
            if len(country) < 2:
                errors.append("country must be at least 2 characters")

        # Validate signup_date
        if 'signup_date' in record and record['signup_date']:
            if not validate_date_format(str(record['signup_date'])):
                errors.append(f"Invalid signup_date format: {record['signup_date']}")

        if errors:
            logger.warning(f"Record {idx} validation failed: {errors}")
            invalid_records.append({
                'record': record,
                'errors': errors
            })
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_customers_data(records: List[Dict[str, Any]], source_file: str) -> pd.DataFrame:
    """
    Transform and enrich customers data

    Args:
        records: List of valid customer records
        source_file: Source file name

    Returns:
        pd.DataFrame: Transformed dataframe
    """
    df = pd.DataFrame(records)

    # Clean and standardize required columns
    df['customer_id'] = df['customer_id'].astype(str).str.strip()
    df['name'] = df['name'].astype(str).str.strip()
    df['email'] = df['email'].astype(str).str.lower().str.strip()
    df['country'] = df['country'].astype(str).str.strip()
    df['signup_date'] = pd.to_datetime(df['signup_date'])

    # Handle optional columns
    if 'phone' in df.columns:
        df['phone'] = df['phone'].fillna('').astype(str)
    else:
        df['phone'] = ''

    if 'account_status' in df.columns:
        df['account_status'] = df['account_status'].fillna('active').astype(str).str.lower()
    else:
        df['account_status'] = 'active'

    if 'city' in df.columns:
        df['city'] = df['city'].fillna('').astype(str)
    else:
        df['city'] = ''

    if 'state' in df.columns:
        df['state'] = df['state'].fillna('').astype(str)
    else:
        df['state'] = ''

    # Add metadata
    df['ingestion_timestamp'] = datetime.utcnow().isoformat()
    df['source_file'] = source_file

    # Add partition column (country)
    df['partition_country'] = df['country']

    logger.info(f"Transformed {len(df)} customer records")

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_file: str):
    """
    Write dataframe to Parquet format in S3 processed zone
    Partitioned by country

    Args:
        s3_client: S3 client
        df: Dataframe to write
        source_file: Original source file name
    """
    try:
        # Group by partition key (country)
        for country, group_df in df.groupby('partition_country'):
            # Generate output filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"customers_{timestamp}.parquet"

            # Create S3 key with partition
            s3_key = f"customers/country={country}/{filename}"

            # Convert to Parquet
            buffer = BytesIO()
            group_df.drop(columns=['partition_country'], inplace=True)
            group_df.to_parquet(buffer, engine='pyarrow', compression='snappy', index=False)
            buffer.seek(0)

            # Upload to S3
            metadata = {
                'source_file': source_file,
                'record_count': str(len(group_df)),
                'ingestion_date': datetime.utcnow().isoformat(),
                'partition_country': country
            }

            success = upload_to_s3(
                s3_client,
                PROCESSED_BUCKET,
                s3_key,
                buffer.getvalue(),
                metadata
            )

            if success:
                logger.info(f"Written {len(group_df)} records to s3://{PROCESSED_BUCKET}/{s3_key}")
            else:
                raise Exception(f"Failed to upload Parquet file: {s3_key}")

    except Exception as e:
        logger.error(f"Error writing to Parquet: {str(e)}")
        raise
