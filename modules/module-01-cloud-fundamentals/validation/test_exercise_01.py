#!/usr/bin/env python3
"""
Validation tests for Exercise 01: S3 Basics
"""

import boto3
import pytest

# LocalStack configuration
ENDPOINT_URL = 'http://localhost:4566'
BUCKET_NAME = 'quickmart-data-lake-raw'

s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)


def test_bucket_exists():
    """Test that the required bucket exists"""
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        assert True
    except:
        pytest.fail(f"Bucket {BUCKET_NAME} does not exist")


def test_bucket_has_objects():
    """Test that bucket contains uploaded objects"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    assert 'Contents' in response, "Bucket is empty"
    assert len(response['Contents']) > 0, "No objects found in bucket"


def test_logs_folder_exists():
    """Test that logs/ folder structure exists"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='logs/')
    assert 'Contents' in response, "logs/ folder not found"


def test_transactions_folder_exists():
    """Test that transactions/ folder structure exists"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='transactions/')
    assert 'Contents' in response, "transactions/ folder not found"


def test_json_files_uploaded():
    """Test that JSON files were uploaded"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='logs/')
    if 'Contents' in response:
        json_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.json')]
        assert len(json_files) > 0, "No JSON files found in logs/"


def test_csv_files_uploaded():
    """Test that CSV files were uploaded"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='transactions/')
    if 'Contents' in response:
        csv_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.csv')]
        assert len(csv_files) > 0, "No CSV files found in transactions/"


def test_object_metadata():
    """Test that objects have proper metadata"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
    if 'Contents' in response:
        obj = response['Contents'][0]
        assert 'Size' in obj, "Object missing Size metadata"
        assert 'LastModified' in obj, "Object missing LastModified metadata"
        assert obj['Size'] > 0, "Object has zero size"


def test_copy_operation():
    """Test that copy operation works"""
    # Create a test object
    test_key = 'test-copy-source.txt'
    s3.put_object(Bucket=BUCKET_NAME, Key=test_key, Body=b'test content')

    # Try to copy it
    copy_source = {'Bucket': BUCKET_NAME, 'Key': test_key}
    dest_key = 'test-copy-dest.txt'
    s3.copy_object(CopySource=copy_source, Bucket=BUCKET_NAME, Key=dest_key)

    # Verify destination exists
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=dest_key)
        assert True
    except:
        pytest.fail("Copy operation failed")

    # Cleanup
    s3.delete_object(Bucket=BUCKET_NAME, Key=test_key)
    s3.delete_object(Bucket=BUCKET_NAME, Key=dest_key)


def test_download_capability():
    """Test that objects can be downloaded"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
    if 'Contents' in response:
        key = response['Contents'][0]['Key']
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            content = obj['Body'].read()
            assert len(content) > 0, "Downloaded object is empty"
        except Exception as e:
            pytest.fail(f"Failed to download object: {str(e)}")


def test_object_count_function():
    """Test that object counting works"""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    if 'Contents' in response:
        count = len(response['Contents'])
        assert count > 0, "No objects to count"
        # Should match what the script reports
        print(f"Found {count} objects in bucket")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
