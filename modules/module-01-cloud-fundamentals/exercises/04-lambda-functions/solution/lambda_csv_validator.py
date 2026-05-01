#!/usr/bin/env python3
"""
Lambda Function: CSV Validator - Complete Solution
Validates transaction CSV files uploaded to S3
"""

import json
import boto3
import csv
import re
from io import StringIO
from datetime import datetime
from typing import Dict, List, Tuple

s3 = boto3.client('s3')


def lambda_handler(event, context):
    """
    Main Lambda handler triggered by S3 events

    Args:
        event: S3 event with bucket and object key
        context: Lambda context (not used)

    Returns:
        Response with status code and body
    """

    try:
        # Extract S3 information from event
        if 'Records' not in event or len(event['Records']) == 0:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No records in event'})
            }

        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        print(f"Processing s3://{bucket}/{key}")

        # Download file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        # Validate CSV content
        result = validate_csv(content)

        valid_count = len(result['valid'])
        invalid_count = len(result['invalid'])

        print(f"Validation complete: {valid_count} valid, {invalid_count} invalid")

        # Upload results to S3
        filename = key.split('/')[-1]
        upload_results(bucket, filename, result['valid'], result['invalid'])

        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Validation completed',
                'file': key,
                'valid_records': valid_count,
                'invalid_records': invalid_count,
                'success_rate': f"{(valid_count / (valid_count + invalid_count) * 100):.2f}%" if (valid_count + invalid_count) > 0 else "0%"
            })
        }

    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(f"ERROR: {error_msg}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'file': key if 'key' in locals() else 'unknown'
            })
        }


def validate_csv(content: str) -> Dict[str, List[Dict]]:
    """
    Parse and validate CSV content

    Args:
        content: CSV content as string

    Returns:
        Dictionary with 'valid' and 'invalid' lists
    """
    reader = csv.DictReader(StringIO(content))
    valid = []
    invalid = []

    seen_ids = set()

    for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
        is_valid, error_msg = validate_row(row, seen_ids)

        if is_valid:
            valid.append(row)
        else:
            row['error'] = error_msg
            row['row_number'] = row_num
            invalid.append(row)

    return {'valid': valid, 'invalid': invalid}


def validate_row(row: Dict, seen_ids: set) -> Tuple[bool, str]:
    """
    Validate a single transaction row

    Validation rules:
    - transaction_id: required, not empty, unique
    - user_id: format USER#### (4 digits)
    - product_id: format PROD#### (4 digits)
    - amount: numeric, > 0 and < 10000
    - timestamp: valid ISO 8601 format
    - country: 2-letter code

    Args:
        row: Dictionary representing a CSV row
        seen_ids: Set of transaction IDs seen so far (for duplicate check)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    errors = []

    # Check transaction_id
    transaction_id = row.get('transaction_id', '').strip()
    if not transaction_id:
        errors.append("transaction_id is required")
    elif transaction_id in seen_ids:
        errors.append(f"duplicate transaction_id: {transaction_id}")
    else:
        seen_ids.add(transaction_id)

    # Check user_id format
    user_id = row.get('user_id', '').strip()
    if not re.match(r'^USER\d{4}$', user_id):
        errors.append(f"user_id must match USER#### format, got: {user_id}")

    # Check product_id format
    product_id = row.get('product_id', '').strip()
    if not re.match(r'^PROD\d{4}$', product_id):
        errors.append(f"product_id must match PROD#### format, got: {product_id}")

    # Check amount
    try:
        amount = float(row.get('amount', 0))
        if amount <= 0:
            errors.append(f"amount must be greater than 0, got: {amount}")
        elif amount >= 10000:
            errors.append(f"amount must be less than 10000, got: {amount}")
    except (ValueError, TypeError):
        errors.append(f"amount must be a valid number, got: {row.get('amount')}")

    # Check timestamp
    try:
        timestamp = row.get('timestamp', '').strip()
        # Handle both 'Z' suffix and standard ISO format
        timestamp = timestamp.replace('Z', '+00:00')
        datetime.fromisoformat(timestamp)
    except (ValueError, AttributeError):
        errors.append(f"timestamp must be valid ISO 8601, got: {row.get('timestamp')}")

    # Check country code (optional but recommended)
    country = row.get('country', '').strip()
    if country and not re.match(r'^[A-Z]{2}$', country):
        errors.append(f"country must be 2-letter code, got: {country}")

    is_valid = len(errors) == 0
    error_message = "; ".join(errors) if errors else ""

    return (is_valid, error_message)


def upload_results(bucket: str, filename: str, valid_records: List[Dict], invalid_records: List[Dict]):
    """
    Upload validation results to S3

    Valid records go to: validated/{filename}
    Invalid records go to: rejected/{filename}-errors.csv

    Args:
        bucket: S3 bucket name
        filename: Original filename
        valid_records: List of valid transaction dictionaries
        invalid_records: List of invalid transaction dictionaries
    """

    # Upload valid records
    if valid_records:
        valid_csv = format_csv(valid_records)
        s3.put_object(
            Bucket=bucket,
            Key=f'validated/{filename}',
            Body=valid_csv.encode('utf-8'),
            ContentType='text/csv'
        )
        print(f"✓ Uploaded {len(valid_records)} valid records to validated/{filename}")
    else:
        print("⚠ No valid records to upload")

    # Upload invalid records
    if invalid_records:
        invalid_csv = format_csv(invalid_records)
        error_filename = filename.replace('.csv', '-errors.csv')
        s3.put_object(
            Bucket=bucket,
            Key=f'rejected/{error_filename}',
            Body=invalid_csv.encode('utf-8'),
            ContentType='text/csv'
        )
        print(f"✓ Uploaded {len(invalid_records)} invalid records to rejected/{error_filename}")


def format_csv(records: List[Dict]) -> str:
    """
    Convert list of dictionaries to CSV string

    Args:
        records: List of dictionaries

    Returns:
        CSV formatted string
    """
    if not records:
        return ""

    output = StringIO()

    # Use keys from first record
    fieldnames = list(records[0].keys())

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

    return output.getvalue()


# For local testing
if __name__ == "__main__":
    # Sample test event
    test_event = {
        "Records": [{
            "eventName": "ObjectCreated:Put",
            "s3": {
                "bucket": {"name": "quickmart-data"},
                "object": {"key": "uploads/transactions/test.csv"}
            }
        }]
    }

    # Note: This requires the file to exist in S3
    # For true local testing, you'd mock the S3 client
    print("To test locally, ensure test.csv exists in S3 or mock boto3")
    print(f"Test event: {json.dumps(test_event, indent=2)}")
