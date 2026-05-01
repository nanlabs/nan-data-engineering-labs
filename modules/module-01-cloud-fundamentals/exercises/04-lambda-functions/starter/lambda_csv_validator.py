#!/usr/bin/env python3
"""
Lambda Function: CSV Validator
Validates transaction CSV files uploaded to S3
"""

import json
import boto3

s3 = boto3.client('s3')


def lambda_handler(event, context):
    """
    Main Lambda handler

    TODO: Extract bucket and key from event
    TODO: Download file from S3
    TODO: Validate CSV content
    TODO: Upload valid and invalid records to different S3 paths
    TODO: Return summary
    """

    try:
        # TODO: Parse S3 event
        # bucket = event['Records'][0]['s3']['bucket']['name']
        # key = event['Records'][0]['s3']['object']['key']

        pass

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def validate_csv(content: str) -> dict:
    """
    Validate CSV content

    Args:
        content: CSV content as string

    Returns:
        dict with 'valid' and 'invalid' lists

    TODO: Parse CSV
    TODO: Validate each row
    TODO: Separate valid from invalid
    """
    pass


def validate_row(row: dict) -> tuple:
    """
    Validate a single transaction row

    Required fields:
    - transaction_id: not empty
    - user_id: format USER####
    - product_id: format PROD####
    - amount: > 0 and < 10000
    - timestamp: valid ISO 8601
    - country: 2-letter code

    Returns:
        (is_valid: bool, error_message: str)

    TODO: Implement validation rules
    TODO: Return (True, "") if valid
    TODO: Return (False, "error description") if invalid
    """
    pass


def upload_results(bucket: str, original_key: str, valid_records: list, invalid_records: list):
    """
    Upload validated results to S3

    Valid records → validated/ folder
    Invalid records → rejected/ folder

    TODO: Convert records to CSV format
    TODO: Upload to S3 with appropriate keys
    """
    pass


def format_csv(records: list) -> str:
    """
    Convert list of dicts to CSV string

    TODO: Use csv.DictWriter with StringIO
    TODO: Return CSV as string
    """
    pass


# For local testing
if __name__ == "__main__":
    # Sample event from S3
    test_event = {
        "Records": [{
            "s3": {
                "bucket": {"name": "quickmart-data"},
                "object": {"key": "uploads/transactions/test.csv"}
            }
        }]
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
