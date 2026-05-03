"""
Orders Ingestion Lambda Handler
Processes orders CSV files from landing zone and writes to processed zone as Parquet
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
    parse_csv_with_encoding,
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
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'DataLake/Orders')

# Schema definition
REQUIRED_COLUMNS = [
    'order_id',
    'customer_id',
    'order_date',
    'total_amount',
    'status'
]

OPTIONAL_COLUMNS = [
    'payment_method',
    'shipping_address',
    'items',
    'discount_amount'
]

VALID_STATUSES = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for orders ingestion

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

                # Parse CSV
                records = parse_csv_with_encoding(file_content)
                logger.info(f"Loaded {len(records)} records from CSV")

                # Validate schema
                valid_records, invalid_records = validate_orders_schema(records)
                logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")

                if invalid_records:
                    logger.warning(f"Found {len(invalid_records)} invalid records")
                    total_records_failed += len(invalid_records)

                # Transform and enrich data
                if valid_records:
                    df = transform_orders_data(valid_records, key)

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
                        'Orders Ingestion Failed',
                        f"Failed to process file: {key}\nError: {str(e)}",
                        {'severity': 'high', 'component': 'orders_ingestion'}
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
                'message': 'Orders ingestion completed',
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
                'Critical: Orders Ingestion Failed',
                f"Critical error in orders ingestion Lambda\nError: {str(e)}",
                {'severity': 'critical', 'component': 'orders_ingestion'}
            )

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Orders ingestion failed',
                'error': str(e)
            })
        }


def validate_orders_schema(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate orders data schema and data quality

    Args:
        records: List of order records

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

        # Validate order_id
        if 'order_id' in record and record['order_id']:
            order_id = str(record['order_id']).strip()
            if not order_id:
                errors.append("order_id cannot be empty")

        # Validate customer_id
        if 'customer_id' in record and record['customer_id']:
            customer_id = str(record['customer_id']).strip()
            if not customer_id:
                errors.append("customer_id cannot be empty")

        # Validate order_date
        if 'order_date' in record and record['order_date']:
            if not validate_date_format(str(record['order_date'])):
                errors.append(f"Invalid order_date format: {record['order_date']}")

        # Validate total_amount
        if 'total_amount' in record and record['total_amount']:
            try:
                amount = float(record['total_amount'])
                if amount < 0:
                    errors.append(f"total_amount must be positive: {amount}")
            except (ValueError, TypeError):
                errors.append(f"Invalid total_amount: {record['total_amount']}")

        # Validate status
        if 'status' in record and record['status']:
            status = str(record['status']).lower().strip()
            if status not in VALID_STATUSES:
                errors.append(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")

        # Validate discount_amount if present
        if 'discount_amount' in record and record['discount_amount']:
            try:
                discount = float(record['discount_amount'])
                if discount < 0:
                    errors.append(f"discount_amount must be non-negative: {discount}")
            except (ValueError, TypeError):
                errors.append(f"Invalid discount_amount: {record['discount_amount']}")

        if errors:
            logger.warning(f"Record {idx} validation failed: {errors}")
            invalid_records.append({
                'record': record,
                'errors': errors
            })
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_orders_data(records: List[Dict[str, Any]], source_file: str) -> pd.DataFrame:
    """
    Transform and enrich orders data

    Args:
        records: List of valid order records
        source_file: Source file name

    Returns:
        pd.DataFrame: Transformed dataframe
    """
    df = pd.DataFrame(records)

    # Clean and standardize columns
    df['order_id'] = df['order_id'].astype(str).str.strip()
    df['customer_id'] = df['customer_id'].astype(str).str.strip()
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['total_amount'] = df['total_amount'].astype(float)
    df['status'] = df['status'].str.lower().str.strip()

    # Handle optional columns
    if 'discount_amount' in df.columns:
        df['discount_amount'] = df['discount_amount'].fillna(0).astype(float)
    else:
        df['discount_amount'] = 0.0

    if 'payment_method' in df.columns:
        df['payment_method'] = df['payment_method'].fillna('unknown').astype(str)
    else:
        df['payment_method'] = 'unknown'

    # Calculate net amount
    df['net_amount'] = df['total_amount'] - df['discount_amount']

    # Add metadata
    df['ingestion_timestamp'] = datetime.utcnow().isoformat()
    df['source_file'] = source_file

    # Add partition columns
    df['year'] = df['order_date'].dt.year
    df['month'] = df['order_date'].dt.month
    df['day'] = df['order_date'].dt.day

    logger.info(f"Transformed {len(df)} order records")

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_file: str):
    """
    Write dataframe to Parquet format in S3 processed zone

    Args:
        s3_client: S3 client
        df: Dataframe to write
        source_file: Original source file name
    """
    try:
        # Group by partition keys
        for (year, month, day), group_df in df.groupby(['year', 'month', 'day']):
            # Generate output filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"orders_{timestamp}.parquet"

            # Create S3 key with partitions
            s3_key = f"orders/year={year}/month={month:02d}/day={day:02d}/{filename}"

            # Convert to Parquet
            buffer = BytesIO()
            group_df.drop(columns=['year', 'month', 'day'], inplace=True)
            group_df.to_parquet(buffer, engine='pyarrow', compression='snappy', index=False)
            buffer.seek(0)

            # Upload to S3
            metadata = {
                'source_file': source_file,
                'record_count': str(len(group_df)),
                'ingestion_date': datetime.utcnow().isoformat()
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
