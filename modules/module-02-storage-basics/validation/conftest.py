"""
Pytest configuration and fixtures for Module 02 validation tests.
"""

import pytest
import pandas as pd
import boto3
from pathlib import Path
from moto import mock_s3, mock_glue
import tempfile
import shutil


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def sample_transactions():
    """Generate small sample transactions dataset."""
    data = {
        'transaction_id': range(1, 101),
        'user_id': [i % 20 + 1 for i in range(100)],
        'product_id': [i % 10 + 1 for i in range(100)],
        'amount': [10.0 + i * 0.5 for i in range(100)],
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D'),
        'country': ['USA' if i % 2 == 0 else 'UK' for i in range(100)],
        'status': ['completed'] * 100
    }
    return pd.DataFrame(data)


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto."""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def s3_client(aws_credentials):
    """Create mocked S3 client."""
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture
def glue_client(aws_credentials):
    """Create mocked Glue client."""
    with mock_glue():
        yield boto3.client('glue', region_name='us-east-1')


@pytest.fixture
def test_bucket(s3_client):
    """Create test S3 bucket."""
    bucket_name = 'test-data-lake-bucket'
    s3_client.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def module_root():
    """Get module root directory."""
    return Path(__file__).parent.parent
