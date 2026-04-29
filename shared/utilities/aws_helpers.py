"""
AWS helper utilities for Cloud Data Engineering modules.

Provides convenience functions for interacting with AWS services
via boto3, with support for LocalStack endpoints.
"""

import boto3
import os
from typing import Optional, Dict, List
from pathlib import Path
import json


class AWSClientFactory:
    """Factory for creating AWS clients with LocalStack support."""

    @staticmethod
    def get_client(service_name: str, use_localstack: bool = True,
                   region_name: str = 'us-east-1') -> boto3.client:
        """
        Create AWS client with optional LocalStack endpoint.

        Args:
            service_name: AWS service name (e.g., 's3', 'lambda', 'dynamodb')
            use_localstack: Whether to use LocalStack endpoint
            region_name: AWS region

        Returns:
            boto3 client
        """
        config = {
            'region_name': region_name,
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY', 'test'),
        }

        if use_localstack:
            endpoint_url = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
            config['endpoint_url'] = endpoint_url

        return boto3.client(service_name, **config)

    @staticmethod
    def get_resource(service_name: str, use_localstack: bool = True,
                    region_name: str = 'us-east-1') -> boto3.resource:
        """Create AWS resource with optional LocalStack endpoint."""
        config = {
            'region_name': region_name,
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY', 'test'),
        }

        if use_localstack:
            endpoint_url = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
            config['endpoint_url'] = endpoint_url

        return boto3.resource(service_name, **config)


class S3Helper:
    """Helper functions for S3 operations."""

    def __init__(self, use_localstack: bool = True):
        self.s3_client = AWSClientFactory.get_client('s3', use_localstack)
        self.s3_resource = AWSClientFactory.get_resource('s3', use_localstack)

    def create_bucket(self, bucket_name: str) -> bool:
        """Create S3 bucket if it doesn't exist."""
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            print(f"✓ Created bucket: {bucket_name}")
            return True
        except self.s3_client.exceptions.BucketAlreadyOwnedByYou:
            print(f"ℹ Bucket already exists: {bucket_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to create bucket {bucket_name}: {e}")
            return False

    def upload_file(self, file_path: Path, bucket: str, key: str) -> bool:
        """Upload file to S3."""
        try:
            self.s3_client.upload_file(str(file_path), bucket, key)
            print(f"✓ Uploaded {file_path.name} to s3://{bucket}/{key}")
            return True
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return False

    def download_file(self, bucket: str, key: str, local_path: Path) -> bool:
        """Download file from S3."""
        try:
            self.s3_client.download_file(bucket, key, str(local_path))
            print(f"✓ Downloaded s3://{bucket}/{key} to {local_path}")
            return True
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return False

    def list_objects(self, bucket: str, prefix: str = '') -> List[str]:
        """List objects in S3 bucket with optional prefix."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            print(f"✗ List objects failed: {e}")
            return []

    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete S3 bucket (optionally force delete with contents)."""
        try:
            if force:
                # Delete all objects first
                bucket = self.s3_resource.Bucket(bucket_name)
                bucket.objects.all().delete()

            self.s3_client.delete_bucket(Bucket=bucket_name)
            print(f"✓ Deleted bucket: {bucket_name}")
            return True
        except Exception as e:
            print(f"✗ Delete bucket failed: {e}")
            return False


class LambdaHelper:
    """Helper functions for Lambda operations."""

    def __init__(self, use_localstack: bool = True):
        self.lambda_client = AWSClientFactory.get_client('lambda', use_localstack)

    def create_function(self, function_name: str, role_arn: str,
                       handler: str, runtime: str, zip_file: Path) -> Optional[str]:
        """Create Lambda function."""
        try:
            with open(zip_file, 'rb') as f:
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=runtime,
                    Role=role_arn,
                    Handler=handler,
                    Code={'ZipFile': f.read()}
                )
            function_arn = response['FunctionArn']
            print(f"✓ Created Lambda function: {function_name}")
            return function_arn
        except Exception as e:
            print(f"✗ Create function failed: {e}")
            return None

    def invoke_function(self, function_name: str, payload: Dict) -> Optional[Dict]:
        """Invoke Lambda function."""
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            result = json.loads(response['Payload'].read())
            print(f"✓ Invoked Lambda function: {function_name}")
            return result
        except Exception as e:
            print(f"✗ Invoke failed: {e}")
            return None


class DynamoDBHelper:
    """Helper functions for DynamoDB operations."""

    def __init__(self, use_localstack: bool = True):
        self.dynamodb = AWSClientFactory.get_resource('dynamodb', use_localstack)
        self.dynamodb_client = AWSClientFactory.get_client('dynamodb', use_localstack)

    def create_table(self, table_name: str, key_schema: List[Dict],
                    attribute_definitions: List[Dict]) -> bool:
        """Create DynamoDB table."""
        try:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            print(f"✓ Created DynamoDB table: {table_name}")
            return True
        except Exception as e:
            print(f"✗ Create table failed: {e}")
            return False

    def put_item(self, table_name: str, item: Dict) -> bool:
        """Put item in DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"✗ Put item failed: {e}")
            return False

    def scan_table(self, table_name: str) -> List[Dict]:
        """Scan all items from DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            response = table.scan()
            return response.get('Items', [])
        except Exception as e:
            print(f"✗ Scan failed: {e}")
            return []


class GlueHelper:
    """Helper functions for AWS Glue operations."""

    def __init__(self, use_localstack: bool = True):
        # Note: Glue is not in LocalStack Community - will need Pro or mocking
        self.glue_client = AWSClientFactory.get_client('glue', use_localstack)

    def create_database(self, database_name: str, description: str = "") -> bool:
        """Create Glue catalog database."""
        try:
            self.glue_client.create_database(
                DatabaseInput={
                    'Name': database_name,
                    'Description': description
                }
            )
            print(f"✓ Created Glue database: {database_name}")
            return True
        except Exception as e:
            if 'AlreadyExistsException' in str(e):
                print(f"ℹ Database already exists: {database_name}")
                return True
            print(f"✗ Create database failed: {e}")
            return False


def check_localstack_status() -> bool:
    """Check if LocalStack is running and accessible."""
    try:
        s3_client = AWSClientFactory.get_client('s3', use_localstack=True)
        s3_client.list_buckets()
        print("✓ LocalStack is running and accessible")
        return True
    except Exception as e:
        print(f"✗ LocalStack is not accessible: {e}")
        print("  💡 Run 'docker-compose up -d' to start LocalStack")
        return False


def setup_aws_credentials(profile_name: str = 'localstack'):
    """Set up AWS credentials for LocalStack."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    print("✓ AWS credentials configured for LocalStack")
