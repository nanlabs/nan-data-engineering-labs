"""
Pytest Configuration and Fixtures for Enterprise Data Lakehouse Validation
===========================================================================

This module provides shared pytest fixtures for testing the enterprise data lakehouse
implementation including AWS service clients, mock data generators, and test helpers.

Fixtures:
---------
- AWS Clients: s3, glue, athena, lakeformation, emr, dynamodb, kms, iam, cloudwatch
- Test Data: sample datasets, PII data, test tables
- Helpers: cleanup utilities, data validators, mock generators

Usage:
------
    pytest validation/ -v
    pytest validation/test_infrastructure.py::TestS3Buckets -v
    pytest validation/ --cov=validation --cov-report=html
"""

import pytest
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import os
import tempfile
import shutil
from moto import (
    mock_s3, mock_glue, mock_athena, mock_lakeformation,
    mock_emr, mock_dynamodb, mock_kms, mock_iam, mock_cloudwatch,
    mock_sts, mock_ec2
)


# ============================================================================
# AWS Credentials and Configuration
# ============================================================================

@pytest.fixture(scope="session")
def aws_credentials():
    """Mock AWS credentials for testing with moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(scope="session")
def aws_region():
    """AWS region for testing."""
    return 'us-east-1'


@pytest.fixture(scope="session")
def project_config():
    """Project configuration for testing."""
    return {
        'project_name': 'enterprise-lakehouse',
        'environment': 'test',
        'region': 'us-east-1',
        'account_id': '123456789012',
        'data_lake_admin': 'arn:aws:iam::123456789012:role/DataLakeAdmin',
        'bronze_bucket': 'enterprise-lakehouse-bronze-test',
        'silver_bucket': 'enterprise-lakehouse-silver-test',
        'gold_bucket': 'enterprise-lakehouse-gold-test',
        'logs_bucket': 'enterprise-lakehouse-logs-test',
    }


# ============================================================================
# AWS Service Client Fixtures
# ============================================================================

@pytest.fixture
def s3_client(aws_credentials, aws_region):
    """Mocked S3 client."""
    with mock_s3():
        yield boto3.client('s3', region_name=aws_region)


@pytest.fixture
def glue_client(aws_credentials, aws_region):
    """Mocked Glue client."""
    with mock_glue():
        yield boto3.client('glue', region_name=aws_region)


@pytest.fixture
def athena_client(aws_credentials, aws_region):
    """Mocked Athena client."""
    with mock_athena():
        yield boto3.client('athena', region_name=aws_region)


@pytest.fixture
def lakeformation_client(aws_credentials, aws_region):
    """Mocked Lake Formation client."""
    with mock_lakeformation():
        yield boto3.client('lakeformation', region_name=aws_region)


@pytest.fixture
def emr_client(aws_credentials, aws_region):
    """Mocked EMR client."""
    with mock_emr():
        yield boto3.client('emr', region_name=aws_region)


@pytest.fixture
def dynamodb_client(aws_credentials, aws_region):
    """Mocked DynamoDB client."""
    with mock_dynamodb():
        yield boto3.client('dynamodb', region_name=aws_region)


@pytest.fixture
def kms_client(aws_credentials, aws_region):
    """Mocked KMS client."""
    with mock_kms():
        yield boto3.client('kms', region_name=aws_region)


@pytest.fixture
def iam_client(aws_credentials, aws_region):
    """Mocked IAM client."""
    with mock_iam():
        yield boto3.client('iam', region_name=aws_region)


@pytest.fixture
def cloudwatch_client(aws_credentials, aws_region):
    """Mocked CloudWatch client."""
    with mock_cloudwatch():
        yield boto3.client('cloudwatch', region_name=aws_region)


@pytest.fixture
def sts_client(aws_credentials, aws_region):
    """Mocked STS client."""
    with mock_sts():
        yield boto3.client('sts', region_name=aws_region)


@pytest.fixture
def ec2_client(aws_credentials, aws_region):
    """Mocked EC2 client."""
    with mock_ec2():
        yield boto3.client('ec2', region_name=aws_region)


# ============================================================================
# Test Bucket Fixtures
# ============================================================================

@pytest.fixture
def test_buckets(s3_client, project_config):
    """Create test S3 buckets for data lake layers."""
    buckets = [
        project_config['bronze_bucket'],
        project_config['silver_bucket'],
        project_config['gold_bucket'],
        project_config['logs_bucket'],
    ]

    for bucket in buckets:
        s3_client.create_bucket(Bucket=bucket)

        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket,
            VersioningConfiguration={'Status': 'Enabled'}
        )

        # Enable encryption
        s3_client.put_bucket_encryption(
            Bucket=bucket,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )

    return buckets


# ============================================================================
# Sample Data Generators
# ============================================================================

@pytest.fixture
def sample_customers_data():
    """Generate sample customer data with PII."""
    np.random.seed(42)

    data = {
        'customer_id': range(1, 101),
        'first_name': [f'FirstName{i}' for i in range(1, 101)],
        'last_name': [f'LastName{i}' for i in range(1, 101)],
        'email': [f'customer{i}@example.com' for i in range(1, 101)],
        'phone': [f'555-{1000+i:04d}' for i in range(1, 101)],
        'ssn': [f'{100+i:03d}-{20+i:02d}-{1000+i:04d}' for i in range(1, 101)],
        'credit_card': [f'4532-{1000+i:04d}-{2000+i:04d}-{3000+i:04d}' for i in range(1, 101)],
        'address': [f'{100+i} Main St' for i in range(1, 101)],
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], 100),
        'state': np.random.choice(['NY', 'CA', 'IL', 'TX', 'AZ'], 100),
        'zip_code': [f'{10000+i:05d}' for i in range(1, 101)],
        'created_at': [datetime.now() - timedelta(days=i) for i in range(100)],
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_orders_data():
    """Generate sample order data."""
    np.random.seed(42)

    data = {
        'order_id': range(1, 501),
        'customer_id': np.random.randint(1, 101, 500),
        'order_date': [datetime.now() - timedelta(days=np.random.randint(0, 365)) for _ in range(500)],
        'order_amount': np.random.uniform(10.0, 1000.0, 500).round(2),
        'product_category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books', 'Sports'], 500),
        'status': np.random.choice(['pending', 'shipped', 'delivered', 'cancelled'], 500, p=[0.1, 0.3, 0.5, 0.1]),
        'shipping_address': [f'{100+i} Main St' for i in range(500)],
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_products_data():
    """Generate sample product data."""
    np.random.seed(42)

    data = {
        'product_id': range(1, 201),
        'product_name': [f'Product {i}' for i in range(1, 201)],
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books', 'Sports'], 200),
        'price': np.random.uniform(5.0, 500.0, 200).round(2),
        'stock_quantity': np.random.randint(0, 1000, 200),
        'supplier_id': np.random.randint(1, 21, 200),
        'created_at': [datetime.now() - timedelta(days=i) for i in range(200)],
        'updated_at': [datetime.now() - timedelta(days=int(i/2)) for i in range(200)],
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_data_quality_issues():
    """Generate sample data with quality issues for testing."""
    data = {
        'id': [1, 2, 3, None, 5],  # Missing primary key
        'name': ['Alice', 'Bob', 'Charlie', 'David', None],  # Missing value
        'email': ['alice@test.com', 'invalid-email', 'charlie@test.com', None, 'eve@test.com'],  # Invalid format
        'age': [25, -5, 30, 150, 35],  # Invalid range
        'amount': [100.50, 200.75, None, 400.25, 500.00],  # Missing value
        'date': ['2024-01-01', '2024-13-32', '2024-03-15', '2024-04-20', None],  # Invalid date
    }

    return pd.DataFrame(data)


# ============================================================================
# Test Data Helpers
# ============================================================================

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def upload_sample_data(s3_client, test_buckets, sample_customers_data, sample_orders_data):
    """Upload sample data to test buckets."""
    def _upload(bucket_name: str, prefix: str, dataframe: pd.DataFrame, format: str = 'parquet'):
        """Upload dataframe to S3."""
        key = f"{prefix}/data.{format}"

        if format == 'parquet':
            buffer = dataframe.to_parquet(index=False)
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=buffer)
        elif format == 'csv':
            csv_buffer = dataframe.to_csv(index=False)
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=csv_buffer)
        elif format == 'json':
            json_buffer = dataframe.to_json(orient='records')
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=json_buffer)

        return f"s3://{bucket_name}/{key}"

    return _upload


# ============================================================================
# Mock Data Generators
# ============================================================================

def generate_mock_glue_table(database: str, table: str, location: str) -> Dict[str, Any]:
    """Generate mock Glue table definition."""
    return {
        'Name': table,
        'DatabaseName': database,
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'id', 'Type': 'bigint'},
                {'Name': 'name', 'Type': 'string'},
                {'Name': 'value', 'Type': 'double'},
                {'Name': 'date', 'Type': 'date'},
            ],
            'Location': location,
            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
            }
        },
        'PartitionKeys': [
            {'Name': 'year', 'Type': 'string'},
            {'Name': 'month', 'Type': 'string'},
        ]
    }


def generate_mock_crawler(crawler_name: str, database: str, s3_path: str, role_arn: str) -> Dict[str, Any]:
    """Generate mock Glue crawler definition."""
    return {
        'Name': crawler_name,
        'Role': role_arn,
        'DatabaseName': database,
        'Targets': {
            'S3Targets': [
                {'Path': s3_path}
            ]
        },
        'SchemaChangePolicy': {
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'LOG'
        }
    }


# ============================================================================
# Validation Helpers
# ============================================================================

class DataQualityValidator:
    """Helper class for data quality validations."""

    @staticmethod
    def check_completeness(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        """Check data completeness."""
        results = {}
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                null_pct = (null_count / len(df)) * 100
                results[col] = {
                    'null_count': int(null_count),
                    'null_percentage': float(null_pct),
                    'complete': null_pct == 0
                }
        return results

    @staticmethod
    def check_uniqueness(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Check uniqueness of columns."""
        results = {}
        for col in columns:
            if col in df.columns:
                total = len(df)
                unique = df[col].nunique()
                duplicate_count = total - unique
                results[col] = {
                    'total_rows': total,
                    'unique_values': unique,
                    'duplicate_count': duplicate_count,
                    'is_unique': duplicate_count == 0
                }
        return results

    @staticmethod
    def check_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> Dict[str, Any]:
        """Check if values are within expected range."""
        if column not in df.columns:
            return {'error': f'Column {column} not found'}

        out_of_range = df[(df[column] < min_val) | (df[column] > max_val)]
        return {
            'total_rows': len(df),
            'out_of_range_count': len(out_of_range),
            'out_of_range_percentage': (len(out_of_range) / len(df)) * 100,
            'in_range': len(out_of_range) == 0
        }

    @staticmethod
    def detect_pii(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential PII columns."""
        pii_patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'ssn': r'\d{3}-\d{2}-\d{4}',
            'phone': r'\d{3}-\d{3,4}-\d{4}',
            'credit_card': r'\d{4}-\d{4}-\d{4}-\d{4}',
        }

        detected_pii = []
        for col in df.columns:
            if df[col].dtype == 'object':
                for pii_type, pattern in pii_patterns.items():
                    matches = df[col].astype(str).str.match(pattern).sum()
                    if matches > 0:
                        detected_pii.append({
                            'column': col,
                            'pii_type': pii_type,
                            'matches': int(matches),
                            'percentage': (matches / len(df)) * 100
                        })

        return detected_pii


@pytest.fixture
def dq_validator():
    """Data quality validator helper."""
    return DataQualityValidator()


# ============================================================================
# Cleanup Utilities
# ============================================================================

@pytest.fixture
def cleanup_s3_resources(s3_client):
    """Cleanup S3 resources after tests."""
    created_buckets = []

    def _register_bucket(bucket_name: str):
        created_buckets.append(bucket_name)

    yield _register_bucket

    # Cleanup
    for bucket in created_buckets:
        try:
            # Delete all objects first
            paginator = s3_client.get_paginator('list_object_versions')
            for page in paginator.paginate(Bucket=bucket):
                objects = []
                if 'Versions' in page:
                    objects.extend([{'Key': v['Key'], 'VersionId': v['VersionId']} for v in page['Versions']])
                if 'DeleteMarkers' in page:
                    objects.extend([{'Key': m['Key'], 'VersionId': m['VersionId']} for m in page['DeleteMarkers']])

                if objects:
                    s3_client.delete_objects(Bucket=bucket, Delete={'Objects': objects})

            # Delete bucket
            s3_client.delete_bucket(Bucket=bucket)
        except Exception as e:
            print(f"Warning: Failed to cleanup bucket {bucket}: {e}")


# ============================================================================
# Module Path Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def module_root():
    """Get module root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def reference_solution_path(module_root):
    """Get reference solution directory."""
    return module_root / 'reference-solution'


@pytest.fixture(scope="session")
def starter_template_path(module_root):
    """Get starter template directory."""
    return module_root / 'starter-template'
