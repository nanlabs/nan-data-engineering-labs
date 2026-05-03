"""
Customers Ingestion Lambda Handler - STARTER TEMPLATE
Processes customers JSON files from landing zone and writes to processed zone as Parquet

KEY DIFFERENCES FROM ORDERS:
- Input format: JSON (not CSV)
- Different schema validation
- May contain nested fields

TODO SECTIONS:
1. Parse S3 event
2. Download and parse JSON file
3. Validate customer schema
4. Transform and flatten nested data
5. Write Parquet to processed zone
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# TODO: Configuration from environment
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', '')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

# Schema definition for customers
REQUIRED_COLUMNS = [
    'customer_id',
    'email',
    'first_name',
    'last_name',
    'country'
]

OPTIONAL_COLUMNS = [
    'phone',
    'registration_date',
    'loyalty_tier',
    'address'
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
        # TODO 1: Parse S3 Event (same pattern as orders)
        s3_records = event.get('Records', [])
        if not s3_records:
            raise ValueError("No S3 records found in event")

        results = []
        total_records_processed = 0
        total_records_failed = 0

        # TODO: Initialize S3 client
        s3_client = None  # TODO: Create boto3 S3 client

        for record in s3_records:
            try:
                # TODO: Extract bucket and key
                bucket = None  # TODO: Get from record
                key = None     # TODO: Get from record

                logger.info(f"Processing file: s3://{bucket}/{key}")

                # ===================================================================
                # TODO 2: Download and Parse JSON File
                # ===================================================================
                # HINT: Download similar to orders, but parse as JSON
                # Use json.loads() to parse JSON string

                # TODO: Download file from S3
                # response = s3_client.get_object(Bucket=bucket, Key=key)
                # file_content = response['Body'].read()
                file_content = None  # TODO: Implement

                if not file_content:
                    raise Exception("Failed to download file from S3")

                # TODO: Parse JSON
                # HINT: JSON can be one object or array of objects
                # records = json.loads(file_content)
                # if isinstance(records, dict):  # Single object
                #     records = [records]
                records = []  # TODO: Parse JSON

                logger.info(f"Loaded {len(records)} records from JSON")

                # ===================================================================
                # TODO 3: Validate Schema
                # ===================================================================
                # HINT: Use validate_customers_schema() function

                # TODO: Validate
                # valid_records, invalid_records = validate_customers_schema(records)
                valid_records = []
                invalid_records = []

                logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")

                if invalid_records:
                    total_records_failed += len(invalid_records)

                # ===================================================================
                # TODO 4: Transform Data
                # ===================================================================
                # HINT: May need to flatten nested JSON structures

                if valid_records:
                    # TODO: Transform
                    # df_transformed = transform_customers_data(valid_records, key)
                    df_transformed = None  # TODO: Implement

                    # TODO 5: Write to Parquet
                    # success = write_to_parquet(s3_client, df_transformed, key)
                    success = False  # TODO: Implement

                    if success:
                        total_records_processed += len(valid_records)
                        results.append({
                            'file': key,
                            'status': 'success',
                            'records_processed': len(valid_records),
                            'records_failed': len(invalid_records)
                        })
                    else:
                        raise Exception("Failed to write Parquet file")
                else:
                    raise ValueError("No valid records found")

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                results.append({
                    'file': key if 'key' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })

                # TODO: Send SNS alert on error

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Customers ingestion completed',
                'results': results,
                'total_records_processed': total_records_processed,
                'total_records_failed': total_records_failed
            })
        }

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Customers ingestion failed',
                'error': str(e)
            })
        }


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

    for record in records:
        errors = []

        # TODO: Check required columns exist
        # for col in REQUIRED_COLUMNS:
        #     if col not in record or not record[col]:
        #         errors.append(f"Missing required column: {col}")

        # TODO: Validate email format
        # HINT: Check if '@' and '.' are in email
        # email = record.get('email', '')
        # if '@' not in email or '.' not in email:
        #     errors.append("Invalid email format")

        # TODO: Validate customer_id is not empty
        # if not str(record.get('customer_id', '')).strip():
        #     errors.append("customer_id cannot be empty")

        if errors:
            record['_validation_errors'] = errors
            invalid_records.append(record)
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_customers_data(records: List[Dict], source_file: str) -> pd.DataFrame:
    """
    Transform and enrich customers data

    Args:
        records: List of validated customer records
        source_file: Source S3 key

    Returns:
        Transformed DataFrame
    """
    df = pd.DataFrame(records)

    # TODO: Flatten nested address field if present
    # HINT: If 'address' is a dict, create columns like address_street, address_city
    # if 'address' in df.columns:
    #     address_df = pd.json_normalize(df['address'])
    #     address_df.columns = ['address_' + col for col in address_df.columns]
    #     df = pd.concat([df.drop('address', axis=1), address_df], axis=1)

    # TODO: Standardize names to title case
    # df['first_name'] = df['first_name'].str.title()
    # df['last_name'] = df['last_name'].str.title()

    # TODO: Lowercase email
    # df['email'] = df['email'].str.lower().str.strip()

    # TODO: Convert registration_date to datetime if present
    # if 'registration_date' in df.columns:
    #     df['registration_date'] = pd.to_datetime(df['registration_date'])

    # TODO: Add audit columns
    # df['processed_timestamp'] = datetime.utcnow()
    # df['source_file'] = source_file

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_key: str) -> bool:
    """
    Write DataFrame to S3 as Parquet

    Args:
        s3_client: Boto3 S3 client
        df: DataFrame to write
        source_key: Original S3 key

    Returns:
        bool: True if successful
    """
    try:
        # TODO: Generate output path
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_key = f"customers/customers_{timestamp}.parquet"

        # TODO: Write Parquet and upload to S3
        # parquet_buffer = BytesIO()
        # df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy', index=False)
        # parquet_buffer.seek(0)
        #
        # s3_client.put_object(
        #     Bucket=PROCESSED_BUCKET,
        #     Key=output_key,
        #     Body=parquet_buffer
        # )

        logger.info(f"Successfully wrote Parquet to s3://{PROCESSED_BUCKET}/{output_key}")
        return True

    except Exception as e:
        logger.error(f"Failed to write Parquet: {str(e)}")
        return False
