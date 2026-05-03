"""
Pytest configuration and fixtures for serverless testing
"""
import pytest
import boto3
from moto import mock_s3, mock_dynamodb, mock_sqs
import os

@pytest.fixture
def aws_credentials():
    """Mock AWS Credentials for moto"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def s3_client(aws_credentials):
    """Create mock S3 client"""
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create mock DynamoDB client"""
    with mock_dynamodb():
        yield boto3.client('dynamodb', region_name='us-east-1')


@pytest.fixture
def sqs_client(aws_credentials):
    """Create mock SQS client"""
    with mock_sqs():
        yield boto3.client('sqs', region_name='us-east-1')


@pytest.fixture
def test_bucket(s3_client):
    """Create test S3 bucket"""
    bucket_name = 'test-bucket'
    s3_client.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def test_table(dynamodb_client):
    """Create test DynamoDB table"""
    table_name = 'test-table'
    dynamodb_client.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    return table_name


@pytest.fixture
def test_queue(sqs_client):
    """Create test SQS queue"""
    response = sqs_client.create_queue(QueueName='test-queue')
    return response['QueueUrl']
