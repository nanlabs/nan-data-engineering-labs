"""
Products Ingestion Lambda Handler - STARTER TEMPLATE
Processes products CSV files from landing zone and writes to processed zone as Parquet

SIMILAR TO ORDERS but with different schema for product catalog data

TODO SECTIONS:
1. Parse S3 event
2. Download CSV file
3. Validate product schema
4. Transform and categorize products
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

# Schema for products
REQUIRED_COLUMNS = [
    'product_id',
    'name',
    'category',
    'price',
    'stock_quantity'
]

OPTIONAL_COLUMNS = [
    'description',
    'supplier_id',
    'weight',
    'dimensions'
]

VALID_CATEGORIES = ['electronics', 'clothing', 'home', 'sports', 'books', 'toys', 'food']


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for products ingestion"""
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # TODO 1: Parse S3 Event (same as orders)
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

                # TODO 2: Download CSV from S3
                # TODO: Similar to orders - get_object and read Body
                file_content = None  # TODO

                if not file_content:
                    raise Exception("Failed to download file")

                # TODO 3: Parse CSV and Validate
                # HINT: pd.read_csv(BytesIO(file_content))
                # df = pd.read_csv(BytesIO(file_content))
                # records = df.to_dict('records')
                records = []  # TODO

                logger.info(f"Loaded {len(records)} products")

                # TODO: Validate schema
                # valid_records, invalid_records = validate_products_schema(records)
                valid_records = []
                invalid_records = []

                if invalid_records:
                    total_failed += len(invalid_records)

                # TODO 4: Transform Data
                if valid_records:
                    # df_transformed = transform_products_data(valid_records, key)
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
                'message': 'Products ingestion completed',
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
                'message': 'Products ingestion failed',
                'error': str(e)
            })
        }


def validate_products_schema(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """Validate products data schema"""
    valid_records = []
    invalid_records = []

    for record in records:
        errors = []

        # TODO: Check required columns
        # for col in REQUIRED_COLUMNS:
        #     if col not in record or not str(record[col]).strip():
        #         errors.append(f"Missing: {col}")

        # TODO: Validate price is positive number
        # try:
        #     price = float(record['price'])
        #     if price < 0:
        #         errors.append("Price must be positive")
        # except (ValueError, TypeError):
        #     errors.append("Price must be numeric")

        # TODO: Validate stock_quantity is non-negative integer
        # try:
        #     stock = int(record['stock_quantity'])
        #     if stock < 0:
        #         errors.append("Stock cannot be negative")
        # except (ValueError, TypeError):
        #     errors.append("Stock must be integer")

        # TODO: Validate category is in VALID_CATEGORIES
        # category = record.get('category', '').lower()
        # if category not in VALID_CATEGORIES:
        #     errors.append(f"Invalid category: {category}")

        if errors:
            record['_validation_errors'] = errors
            invalid_records.append(record)
        else:
            valid_records.append(record)

    return valid_records, invalid_records


def transform_products_data(records: List[Dict], source_file: str) -> pd.DataFrame:
    """Transform and enrich products data"""
    df = pd.DataFrame(records)

    # TODO: Standardize category to lowercase
    # df['category'] = df['category'].str.lower().str.strip()

    # TODO: Ensure price and stock are correct types
    # df['price'] = df['price'].astype(float)
    # df['stock_quantity'] = df['stock_quantity'].astype(int)

    # TODO: Add calculated fields
    # df['in_stock'] = df['stock_quantity'] > 0
    # df['price_category'] = pd.cut(df['price'],
    #     bins=[0, 10, 50, 100, float('inf')],
    #     labels=['budget', 'mid-range', 'premium', 'luxury'])

    # TODO: Add audit columns
    # df['processed_timestamp'] = datetime.utcnow()
    # df['source_file'] = source_file

    return df


def write_to_parquet(s3_client, df: pd.DataFrame, source_key: str) -> bool:
    """Write DataFrame to S3 as Parquet"""
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_key = f"products/products_{timestamp}.parquet"

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
