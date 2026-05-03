"""
Products Ingestion Lambda Handler
Processes products CSV files from landing zone and writes to processed zone as Parquet
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
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'DataLake/Products')

# Schema definition
REQUIRED_COLUMNS = [
    'product_id',
    'name',
    'category',
    'price',
    'stock_quantity'
]

OPTIONAL_COLUMNS = [
    'description',
    'brand',
    'weight',
    'dimensions',
    'manufacturer',
    'sku'
]

VALID_CATEGORIES = [
    'electronics',
    'clothing',
    'home',
    'sports',
    'books',
    'toys',
    'food',
    'beauty',
    'automotive',
    'other'
]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for products ingestion

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
                valid_records, invalid_records = validate_products_schema(records)
                logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")

                if invalid_records:
                    logger.warning(f"Found {len(invalid_records)} invalid records")
                    total_records_failed += len(invalid_records)

                # Transform and enrich data
                if valid_records:
                    df = transform_products_data(valid_records, key)

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
                        'Products Ingestion Failed',
                        f"Failed to process file: {key}\nError: {str(e)}",
                        {'severity': 'high', 'component': 'products_ingestion'}
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
                'message': 'Products ingestion completed',
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
                'Critical: Products Ingestion Failed',
                f"Critical error in products ingestion Lambda\nError: {str(e)}",
                {'severity': 'critical', 'component': 'products_ingestion'}
            )

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Products ingestion failed',
                'error': str(e)
            })
        }


def validate_products_schema(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate products data schema and data quality

    Args:
        records: List of product records

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

        # Validate product_id
        if 'product_id' in record and record['product_id']:
            product_id = str(record['product_id']).strip()
            if not product_id:
                errors.append("product_id cannot be empty")

        # Validate name
        if 'name' in record and record['name']:
            name = str(record['name']).strip()
            if len(name) < 2:
                errors.append("name must be at least 2 characters")

        # Validate category
        if 'category' in record and record['category']:
            category = str(record['category']).lower().strip()
            if category not in VALID_CATEGORIES:
                errors.append(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")

        # Validate price
        if 'price' in record and record['price']:
            try:
                price = float(record['price'])
                if price < 0:
                    errors.append(f"price must be non-negative: {price}")
            except (ValueError, TypeError):
                errors.append(f"Invalid price: {record['price']}")

        # Validate stock_quantity
        if 'stock_quantity' in record and record['stock_quantity']:
            try:
                stock = int(record['stock_quantity'])
                if stock < 0:
                    errors.append(f"stock_quantity must be non-negative: {stock}")
            except (ValueError, TypeError):
                errors.append(f"Invalid stock_quantity: {record['stock_quantity']}")

        if errors:
            logger.warning(f"Record {idx} validation failed: {errors}")
            invalid_records.append({
                'record': record,
                'errors': errors
            })
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_products_data(records: List[Dict[str, Any]], source_file: str) -> pd.DataFrame:
    """
    Transform and enrich products data

    Args:
        records: List of valid product records
        source_file: Source file name

    Returns:
        pd.DataFrame: Transformed dataframe
    """
    df = pd.DataFrame(records)

    # Clean and standardize required columns
    df['product_id'] = df['product_id'].astype(str).str.strip()
    df['name'] = df['name'].astype(str).str.strip()
    df['category'] = df['category'].astype(str).str.lower().str.strip()
    df['price'] = df['price'].astype(float)
    df['stock_quantity'] = df['stock_quantity'].astype(int)

    # Handle optional columns
    if 'description' in df.columns:
        df['description'] = df['description'].fillna('').astype(str)
    else:
        df['description'] = ''

    if 'brand' in df.columns:
        df['brand'] = df['brand'].fillna('unknown').astype(str)
    else:
        df['brand'] = 'unknown'

    if 'sku' in df.columns:
        df['sku'] = df['sku'].fillna('').astype(str)
    else:
        df['sku'] = ''

    # Calculate stock status
    df['stock_status'] = df['stock_quantity'].apply(
        lambda x: 'out_of_stock' if x == 0 else 'low_stock' if x < 10 else 'in_stock'
    )

    # Add metadata
    df['ingestion_timestamp'] = datetime.utcnow().isoformat()
    df['source_file'] = source_file

    # Add partition column (category)
    df['partition_category'] = df['category']

    logger.info(f"Transformed {len(df)} product records")

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_file: str):
    """
    Write dataframe to Parquet format in S3 processed zone
    Partitioned by category

    Args:
        s3_client: S3 client
        df: Dataframe to write
        source_file: Original source file name
    """
    try:
        # Group by partition key (category)
        for category, group_df in df.groupby('partition_category'):
            # Generate output filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"products_{timestamp}.parquet"

            # Create S3 key with partition
            s3_key = f"products/category={category}/{filename}"

            # Convert to Parquet
            buffer = BytesIO()
            group_df.drop(columns=['partition_category'], inplace=True)
            group_df.to_parquet(buffer, engine='pyarrow', compression='snappy', index=False)
            buffer.seek(0)

            # Upload to S3
            metadata = {
                'source_file': source_file,
                'record_count': str(len(group_df)),
                'ingestion_date': datetime.utcnow().isoformat(),
                'partition_category': category
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
