"""
pytest configuration and shared fixtures for acceptance tests
Provides AWS clients, test data generators, and cleanup utilities
"""

import os
import pytest
import boto3
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Environment variables with defaults
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BUCKET_PREFIX = os.getenv('BUCKET_PREFIX', 'data-lake-checkpoint01')
PROJECT_NAME = os.getenv('PROJECT_NAME', 'serverless-data-lake')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'test')


@pytest.fixture(scope='session')
def aws_region():
    """Return AWS region for tests"""
    return AWS_REGION


@pytest.fixture(scope='session')
def aws_session():
    """
    Create boto3 session with credentials

    Returns:
        boto3.Session: Configured session
    """
    session = boto3.Session(region_name=AWS_REGION)
    logger.info(f"Created AWS session for region: {AWS_REGION}")
    return session


@pytest.fixture(scope='session')
def s3_client(aws_session):
    """
    Get S3 client for tests

    Returns:
        boto3.client: S3 client
    """
    client = aws_session.client('s3')
    logger.info("Created S3 client")
    return client


@pytest.fixture(scope='session')
def s3_resource(aws_session):
    """
    Get S3 resource for tests

    Returns:
        boto3.resource: S3 resource
    """
    resource = aws_session.resource('s3')
    logger.info("Created S3 resource")
    return resource


@pytest.fixture(scope='session')
def glue_client(aws_session):
    """
    Get Glue client for tests

    Returns:
        boto3.client: Glue client
    """
    client = aws_session.client('glue')
    logger.info("Created Glue client")
    return client


@pytest.fixture(scope='session')
def lambda_client(aws_session):
    """
    Get Lambda client for tests

    Returns:
        boto3.client: Lambda client
    """
    client = aws_session.client('lambda')
    logger.info("Created Lambda client")
    return client


@pytest.fixture(scope='session')
def iam_client(aws_session):
    """
    Get IAM client for tests

    Returns:
        boto3.client: IAM client
    """
    client = aws_session.client('iam')
    logger.info("Created IAM client")
    return client


@pytest.fixture(scope='session')
def athena_client(aws_session):
    """
    Get Athena client for tests

    Returns:
        boto3.client: Athena client
    """
    client = aws_session.client('athena')
    logger.info("Created Athena client")
    return client


@pytest.fixture(scope='session')
def logs_client(aws_session):
    """
    Get CloudWatch Logs client for tests

    Returns:
        boto3.client: CloudWatch Logs client
    """
    client = aws_session.client('logs')
    logger.info("Created CloudWatch Logs client")
    return client


@pytest.fixture(scope='session')
def cloudwatch_client(aws_session):
    """
    Get CloudWatch client for tests

    Returns:
        boto3.client: CloudWatch client
    """
    client = aws_session.client('cloudwatch')
    logger.info("Created CloudWatch client")
    return client


@pytest.fixture(scope='session')
def sns_client(aws_session):
    """
    Get SNS client for tests

    Returns:
        boto3.client: SNS client
    """
    client = aws_session.client('sns')
    logger.info("Created SNS client")
    return client


@pytest.fixture(scope='session')
def bucket_names():
    """
    Get expected bucket names

    Returns:
        dict: Dictionary of bucket names
    """
    return {
        'raw': f"{BUCKET_PREFIX}-raw-{ENVIRONMENT}",
        'processed': f"{BUCKET_PREFIX}-processed-{ENVIRONMENT}",
        'curated': f"{BUCKET_PREFIX}-curated-{ENVIRONMENT}",
        'logs': f"{BUCKET_PREFIX}-logs-{ENVIRONMENT}",
        'athena_results': f"{BUCKET_PREFIX}-athena-results-{ENVIRONMENT}"
    }


@pytest.fixture(scope='session')
def lambda_function_names():
    """
    Get expected Lambda function names

    Returns:
        dict: Dictionary of Lambda function names
    """
    return {
        'file_validator': f"{PROJECT_NAME}-file-validator-{ENVIRONMENT}",
        'metadata_extractor': f"{PROJECT_NAME}-metadata-extractor-{ENVIRONMENT}",
        'notification_handler': f"{PROJECT_NAME}-notification-handler-{ENVIRONMENT}",
        'quality_checker': f"{PROJECT_NAME}-quality-checker-{ENVIRONMENT}"
    }


@pytest.fixture
def test_data_generator():
    """
    Factory for generating test datasets

    Returns:
        function: Generator function
    """
    def generate_customers(count: int = 100) -> List[Dict[str, Any]]:
        """Generate customer test data"""
        customers = []
        for i in range(count):
            customers.append({
                'customer_id': f"CUST{i+1:05d}",
                'name': f"Test Customer {i+1}",
                'email': f"customer{i+1}@test.com",
                'country': random.choice(['US', 'UK', 'CA', 'AU', 'DE']),
                'signup_date': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                'is_active': random.choice([True, False])
            })
        return customers

    def generate_orders(count: int = 500, customer_count: int = 100) -> List[Dict[str, Any]]:
        """Generate order test data"""
        orders = []
        for i in range(count):
            orders.append({
                'order_id': f"ORD{i+1:06d}",
                'customer_id': f"CUST{random.randint(1, customer_count):05d}",
                'order_date': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
                'total_amount': round(random.uniform(10.0, 1000.0), 2),
                'status': random.choice(['pending', 'completed', 'cancelled']),
                'quantity': random.randint(1, 10)
            })
        return orders

    def generate_products(count: int = 50) -> List[Dict[str, Any]]:
        """Generate product test data"""
        products = []
        categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
        for i in range(count):
            products.append({
                'product_id': f"PROD{i+1:04d}",
                'name': f"Test Product {i+1}",
                'category': random.choice(categories),
                'price': round(random.uniform(5.0, 500.0), 2),
                'in_stock': random.choice([True, False]),
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d')
            })
        return products

    return {
        'customers': generate_customers,
        'orders': generate_orders,
        'products': generate_products
    }


@pytest.fixture
def cleanup_test_data(s3_client, bucket_names):
    """
    Fixture to cleanup test data after tests

    Yields control to test, then cleans up
    """
    test_keys = []

    def register_key(bucket: str, key: str):
        """Register a key for cleanup"""
        test_keys.append((bucket, key))

    yield register_key

    # Cleanup after test
    logger.info(f"Cleaning up {len(test_keys)} test objects")
    for bucket, key in test_keys:
        try:
            s3_client.delete_object(Bucket=bucket, Key=key)
            logger.debug(f"Deleted s3://{bucket}/{key}")
        except Exception as e:
            logger.warning(f"Failed to delete s3://{bucket}/{key}: {str(e)}")


@pytest.fixture
def athena_test_workgroup():
    """Get Athena workgroup name for tests"""
    return f"{PROJECT_NAME}-workgroup-{ENVIRONMENT}"


@pytest.fixture
def glue_database_name():
    """Get Glue database name for tests"""
    return f"{PROJECT_NAME.replace('-', '_')}_{ENVIRONMENT}"


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires AWS resources)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "expensive: mark test that may incur AWS costs"
    )
