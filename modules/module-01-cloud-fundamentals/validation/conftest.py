"""
Pytest configuration for Module 01 validation tests
"""

import pytest
import boto3
import time


@pytest.fixture(scope="session")
def wait_for_localstack():
    """Wait for LocalStack to be ready before running tests"""
    s3 = boto3.client(
        's3',
        endpoint_url='http://localhost:4566',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

    max_retries = 30
    for i in range(max_retries):
        try:
            s3.list_buckets()
            print("\n✓ LocalStack is ready")
            return
        except:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                pytest.fail("LocalStack not responding after 30 seconds")


@pytest.fixture(autouse=True)
def setup_localstack(wait_for_localstack):
    """Auto-use fixture to ensure LocalStack is ready"""
    pass
