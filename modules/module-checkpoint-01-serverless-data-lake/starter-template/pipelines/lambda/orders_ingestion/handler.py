"""
Orders Ingestion Lambda Handler - STARTER TEMPLATE
Processes orders CSV files from landing zone and writes to processed zone as Parquet

LEARNING OBJECTIVES:
- Parse S3 event notifications
- Download and process CSV files from S3
- Validate data schemas and quality
- Transform data with pandas
- Write Parquet files for analytics
- Handle errors and send alerts

TODO SECTIONS:
1. Parse S3 event
2. Download file from S3
3. Validate CSV schema
4. Transform and clean data
5. Write Parquet to processed zone
6. Send SNS alerts on errors
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

import pandas as pd

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# TODO: Get configuration from environment variables
# HINT: Use os.environ.get() to read environment variables safely
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', '')  # TODO: Read from environment
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'DataLake/Orders')

# Schema definition for orders
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
        event: S3 event notification with Records
        context: Lambda context object

    Returns:
        Dict: Response with status and metrics
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # ===================================================================
        # TODO 1: Parse S3 Event
        # ===================================================================
        # HINT: Extract bucket name and object key from event['Records'][0]['s3']
        # The S3 event structure is:
        # {
        #   'Records': [
        #     {
        #       's3': {
        #         'bucket': {'name': 'bucket-name'},
        #         'object': {'key': 'path/to/file.csv'}
        #       }
        #     }
        #   ]
        # }

        # TODO: Validate that event contains Records
        s3_records = event.get('Records', [])
        if not s3_records:
            raise ValueError("No S3 records found in event")

        results = []
        total_records_processed = 0
        total_records_failed = 0

        # TODO: Initialize S3 client
        # HINT: s3_client = boto3.client('s3')
        s3_client = None  # TODO: Replace with actual S3 client

        # Process each S3 record (usually just one per trigger)
        for record in s3_records:
            try:
                # TODO: Extract bucket and key from record
                # HINT: bucket = record['s3']['bucket']['name']
                #       key = record['s3']['object']['key']
                bucket = None  # TODO: Complete
                key = None     # TODO: Complete

                logger.info(f"Processing file: s3://{bucket}/{key}")

                # ===================================================================
                # TODO 2: Download File from S3
                # ===================================================================
                # HINT: Use s3_client.get_object(Bucket=bucket, Key=key)
                # Read the response body: response['Body'].read()

                # TODO: Download file
                # response = s3_client.get_object(Bucket=bucket, Key=key)
                # file_content = response['Body'].read()
                file_content = None  # TODO: Implement download

                if not file_content:
                    raise Exception("Failed to download file from S3")

                # ===================================================================
                # TODO 3: Parse and Validate CSV
                # ===================================================================
                # HINT: Use pd.read_csv() with BytesIO to read from bytes
                # Then validate schema using validate_orders_schema() function

                # TODO: Parse CSV into DataFrame
                # df = pd.read_csv(BytesIO(file_content))
                # records = df.to_dict('records')
                records = []  # TODO: Parse CSV

                logger.info(f"Loaded {len(records)} records from CSV")

                # TODO: Validate schema
                # valid_records, invalid_records = validate_orders_schema(records)
                valid_records = []   # TODO: Get valid records after validation
                invalid_records = [] # TODO: Get invalid records

                logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")

                if invalid_records:
                    logger.warning(f"Found {len(invalid_records)} invalid records")
                    total_records_failed += len(invalid_records)

                # ===================================================================
                # TODO 4: Transform Data
                # ===================================================================
                # HINT: Use transform_orders_data() function to clean and enrich

                if valid_records:
                    # TODO: Transform the valid records
                    # df_transformed = transform_orders_data(valid_records, key)
                    df_transformed = None  # TODO: Transform data

                    # ===================================================================
                    # TODO 5: Write to Parquet
                    # ===================================================================
                    # HINT: Use write_to_parquet() function to save to processed zone

                    # TODO: Write to S3 as Parquet
                    # success = write_to_parquet(s3_client, df_transformed, key)
                    success = False  # TODO: Write Parquet

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
                    raise ValueError("No valid records found after validation")

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")

                total_records_failed += len(records) if 'records' in locals() else 0
                results.append({
                    'file': key if 'key' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })

                # ===================================================================
                # TODO 6: Send SNS Alert on Error
                # ===================================================================
                # HINT: Use send_sns_alert() function

                # TODO: Send alert if SNS topic is configured
                # if SNS_TOPIC_ARN:
                #     send_sns_alert(
                #         SNS_TOPIC_ARN,
                #         'Orders Ingestion Failed',
                #         f"File: {key}\nError: {str(e)}"
                #     )

        # TODO: Log metrics to CloudWatch (optional)
        # HINT: Use CloudWatch client to put custom metrics

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

        # TODO: Send critical error alert

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
        records: List of order records from CSV

    Returns:
        Tuple: (valid_records, invalid_records)
    """
    valid_records = []
    invalid_records = []

    for record in records:
        errors = []

        # ===================================================================
        # TODO: Validate Required Columns
        # ===================================================================
        # HINT: Check if all REQUIRED_COLUMNS exist and are not empty

        # TODO: Check required columns
        # for col in REQUIRED_COLUMNS:
        #     if col not in record or record[col] is None or str(record[col]).strip() == '':
        #         errors.append(f"Missing required column: {col}")

        # ===================================================================
        # TODO: Validate Data Types and Values
        # ===================================================================
        # HINT: Check order_date format, total_amount is numeric, status is valid

        # TODO: Validate order_date format (YYYY-MM-DD)
        # try:
        #     datetime.strptime(str(record['order_date']), '%Y-%m-%d')
        # except ValueError:
        #     errors.append("Invalid order_date format")

        # TODO: Validate total_amount is positive number
        # try:
        #     amount = float(record['total_amount'])
        #     if amount < 0:
        #         errors.append("total_amount must be positive")
        # except (ValueError, TypeError):
        #     errors.append("total_amount must be numeric")

        # TODO: Validate status is in VALID_STATUSES list
        # if record.get('status', '').lower() not in VALID_STATUSES:
        #     errors.append(f"Invalid status: {record.get('status')}")

        # Classify record as valid or invalid
        if errors:
            record['_validation_errors'] = errors
            invalid_records.append(record)
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_orders_data(records: List[Dict], source_file: str) -> pd.DataFrame:
    """
    Transform and enrich orders data

    Args:
        records: List of validated order records
        source_file: Source S3 key for audit trail

    Returns:
        Transformed pandas DataFrame ready for Parquet
    """
    df = pd.DataFrame(records)

    # ===================================================================
    # TODO: Clean and Standardize Data
    # ===================================================================
    # HINT: Convert strings to proper case, trim whitespace, standardize formats

    # TODO: Convert order_date to datetime
    # df['order_date'] = pd.to_datetime(df['order_date'])

    # TODO: Standardize status to lowercase
    # df['status'] = df['status'].str.lower().str.strip()

    # TODO: Ensure numeric columns are correct type
    # df['total_amount'] = df['total_amount'].astype(float)
    # if 'discount_amount' in df.columns:
    #     df['discount_amount'] = df['discount_amount'].fillna(0).astype(float)

    # ===================================================================
    # TODO: Add Audit Columns
    # ===================================================================
    # HINT: Add metadata for tracking and debugging

    # TODO: Add processing timestamp
    # df['processed_timestamp'] = datetime.utcnow()

    # TODO: Add source file for audit trail
    # df['source_file'] = source_file

    # TODO: Add year/month/day partitioning columns
    # df['year'] = df['order_date'].dt.year
    # df['month'] = df['order_date'].dt.month
    # df['day'] = df['order_date'].dt.day

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_key: str) -> bool:
    """
    Write DataFrame to S3 as Parquet format in processed zone

    Args:
        s3_client: Boto3 S3 client
        df: DataFrame to write
        source_key: Original S3 key for naming

    Returns:
        bool: True if successful
    """
    try:
        # ===================================================================
        # TODO: Generate Output Path
        # ===================================================================
        # HINT: Use partitioning by year/month/day for query performance
        # Format: s3://bucket/orders/year=2024/month=03/day=09/file.parquet

        # TODO: Generate partitioned path
        # Example: orders/year=2024/month=03/day=09/orders_20240309_123456.parquet
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"orders_{timestamp}.parquet"

        # TODO: Create partitioned path (optional advanced feature)
        # output_key = f"orders/year={year}/month={month:02d}/day={day:02d}/{filename}"
        output_key = f"orders/{filename}"  # Simple path without partitioning

        # ===================================================================
        # TODO: Write Parquet to S3
        # ===================================================================
        # HINT: Use df.to_parquet() with BytesIO, then upload to S3

        # TODO: Convert DataFrame to Parquet bytes
        # parquet_buffer = BytesIO()
        # df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy', index=False)
        # parquet_buffer.seek(0)

        # TODO: Upload to S3
        # s3_client.put_object(
        #     Bucket=PROCESSED_BUCKET,
        #     Key=output_key,
        #     Body=parquet_buffer,
        #     ContentType='application/octet-stream'
        # )

        logger.info(f"Successfully wrote Parquet to s3://{PROCESSED_BUCKET}/{output_key}")
        return True

    except Exception as e:
        logger.error(f"Failed to write Parquet: {str(e)}")
        return False


def send_sns_alert(topic_arn: str, subject: str, message: str) -> bool:
    """
    Send SNS notification for errors or alerts

    Args:
        topic_arn: SNS topic ARN
        subject: Alert subject
        message: Alert message body

    Returns:
        bool: True if successful
    """
    try:
        # TODO: Send SNS message
        # HINT: Use boto3.client('sns').publish()

        # sns_client = boto3.client('sns')
        # response = sns_client.publish(
        #     TopicArn=topic_arn,
        #     Subject=subject,
        #     Message=message
        # )
        # logger.info(f"SNS alert sent: {response['MessageId']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send SNS alert: {str(e)}")
        return False
