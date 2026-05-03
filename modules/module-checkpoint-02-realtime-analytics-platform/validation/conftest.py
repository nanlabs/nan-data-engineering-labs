"""
Pytest Configuration and Fixtures for Real-Time Analytics Platform Tests

This module provides shared pytest fixtures for testing AWS infrastructure
and streaming pipelines. Includes boto3 clients, mock data generators,
and resource setup/teardown utilities.
"""

import json
import os
import random
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import boto3
import pytest
from moto import mock_kinesis, mock_dynamodb, mock_s3, mock_lambda, mock_iam, mock_cloudwatch


# ============================================================================
# CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def aws_region():
    """AWS region for testing."""
    return os.environ.get("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def project_name():
    """Project name prefix for resources."""
    return os.environ.get("PROJECT_NAME", "rideshare-analytics")


@pytest.fixture(scope="session")
def environment():
    """Deployment environment."""
    return os.environ.get("ENVIRONMENT", "test")


# ============================================================================
# AWS CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def kinesis_client(aws_region):
    """Kinesis client for testing."""
    with mock_kinesis():
        client = boto3.client("kinesis", region_name=aws_region)
        yield client


@pytest.fixture(scope="function")
def dynamodb_client(aws_region):
    """DynamoDB client for testing."""
    with mock_dynamodb():
        client = boto3.client("dynamodb", region_name=aws_region)
        yield client


@pytest.fixture(scope="function")
def dynamodb_resource(aws_region):
    """DynamoDB resource for testing."""
    with mock_dynamodb():
        resource = boto3.resource("dynamodb", region_name=aws_region)
        yield resource


@pytest.fixture(scope="function")
def s3_client(aws_region):
    """S3 client for testing."""
    with mock_s3():
        client = boto3.client("s3", region_name=aws_region)
        yield client


@pytest.fixture(scope="function")
def lambda_client(aws_region):
    """Lambda client for testing."""
    with mock_lambda():
        client = boto3.client("lambda", region_name=aws_region)
        yield client


@pytest.fixture(scope="function")
def cloudwatch_client(aws_region):
    """CloudWatch client for testing."""
    with mock_cloudwatch():
        client = boto3.client("cloudwatch", region_name=aws_region)
        yield client


@pytest.fixture(scope="function")
def iam_client(aws_region):
    """IAM client for testing."""
    with mock_iam():
        client = boto3.client("iam", region_name=aws_region)
        yield client


# ============================================================================
# REAL AWS CLIENTS (for integration tests)
# ============================================================================

@pytest.fixture(scope="session")
def real_kinesis_client(aws_region):
    """Real Kinesis client for integration tests."""
    return boto3.client("kinesis", region_name=aws_region)


@pytest.fixture(scope="session")
def real_dynamodb_client(aws_region):
    """Real DynamoDB client for integration tests."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(scope="session")
def real_s3_client(aws_region):
    """Real S3 client for integration tests."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def real_lambda_client(aws_region):
    """Real Lambda client for integration tests."""
    return boto3.client("lambda", region_name=aws_region)


# ============================================================================
# MOCK DATA GENERATORS
# ============================================================================

@pytest.fixture
def generate_ride_event():
    """Factory fixture to generate mock ride events."""

    def _generate(
        event_type: str = "ride_requested",
        ride_id: Optional[str] = None,
        driver_id: Optional[str] = None,
        rider_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        cities = ["San Francisco", "New York", "Seattle", "Austin", "Boston"]
        city = kwargs.get("city", random.choice(cities))

        # Base coordinates for major cities
        city_coords = {
            "San Francisco": (37.7749, -122.4194),
            "New York": (40.7128, -74.0060),
            "Seattle": (47.6062, -122.3321),
            "Austin": (30.2672, -97.7431),
            "Boston": (42.3601, -71.0589),
        }

        base_lat, base_lon = city_coords.get(city, (37.7749, -122.4194))

        event = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "ride_id": ride_id or str(uuid.uuid4()),
            "rider_id": rider_id or f"rider_{random.randint(1000, 9999)}",
            "timestamp": kwargs.get("timestamp", datetime.utcnow().isoformat()),
            "city": city,
        }

        if event_type == "ride_requested":
            event.update({
                "pickup_location": {
                    "latitude": base_lat + random.uniform(-0.1, 0.1),
                    "longitude": base_lon + random.uniform(-0.1, 0.1),
                    "address": kwargs.get("pickup_address", "123 Main St"),
                },
                "dropoff_location": {
                    "latitude": base_lat + random.uniform(-0.15, 0.15),
                    "longitude": base_lon + random.uniform(-0.15, 0.15),
                    "address": kwargs.get("dropoff_address", "456 Oak Ave"),
                },
                "ride_type": kwargs.get("ride_type", random.choice(["standard", "premium", "xl"])),
                "estimated_fare": round(random.uniform(10, 50), 2),
            })

        elif event_type == "ride_accepted":
            event.update({
                "driver_id": driver_id or f"driver_{random.randint(1000, 9999)}",
                "driver_location": {
                    "latitude": base_lat + random.uniform(-0.05, 0.05),
                    "longitude": base_lon + random.uniform(-0.05, 0.05),
                },
                "estimated_pickup_time": random.randint(3, 15),
            })

        elif event_type == "ride_started":
            event.update({
                "driver_id": driver_id or f"driver_{random.randint(1000, 9999)}",
                "start_location": {
                    "latitude": base_lat + random.uniform(-0.1, 0.1),
                    "longitude": base_lon + random.uniform(-0.1, 0.1),
                },
            })

        elif event_type == "ride_completed":
            event.update({
                "driver_id": driver_id or f"driver_{random.randint(1000, 9999)}",
                "end_location": {
                    "latitude": base_lat + random.uniform(-0.15, 0.15),
                    "longitude": base_lon + random.uniform(-0.15, 0.15),
                },
                "distance_miles": round(random.uniform(2, 20), 2),
                "duration_minutes": random.randint(10, 60),
                "fare": round(random.uniform(15, 80), 2),
            })

        event.update(kwargs)
        return event

    return _generate


@pytest.fixture
def generate_payment_event():
    """Factory fixture to generate mock payment events."""

    def _generate(
        event_type: str = "payment_processed",
        payment_id: Optional[str] = None,
        ride_id: Optional[str] = None,
        rider_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        event = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "payment_id": payment_id or str(uuid.uuid4()),
            "ride_id": ride_id or str(uuid.uuid4()),
            "rider_id": rider_id or f"rider_{random.randint(1000, 9999)}",
            "timestamp": kwargs.get("timestamp", datetime.utcnow().isoformat()),
            "amount": round(random.uniform(10, 100), 2),
            "currency": "USD",
            "payment_method": random.choice(["credit_card", "debit_card", "wallet"]),
            "status": kwargs.get("status", "success"),
        }

        if event_type == "payment_processed":
            event.update({
                "transaction_id": str(uuid.uuid4()),
                "processor": "stripe",
                "processing_time_ms": random.randint(100, 500),
            })

        elif event_type == "payment_failed":
            event.update({
                "error_code": kwargs.get("error_code", "insufficient_funds"),
                "error_message": kwargs.get("error_message", "Payment declined"),
            })

        event.update(kwargs)
        return event

    return _generate


@pytest.fixture
def generate_location_event():
    """Factory fixture to generate mock driver location events."""

    def _generate(
        driver_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        cities = ["San Francisco", "New York", "Seattle", "Austin", "Boston"]
        city = kwargs.get("city", random.choice(cities))

        city_coords = {
            "San Francisco": (37.7749, -122.4194),
            "New York": (40.7128, -74.0060),
            "Seattle": (47.6062, -122.3321),
            "Austin": (30.2672, -97.7431),
            "Boston": (42.3601, -71.0589),
        }

        base_lat, base_lon = city_coords.get(city, (37.7749, -122.4194))

        event = {
            "event_type": "location_update",
            "event_id": str(uuid.uuid4()),
            "driver_id": driver_id or f"driver_{random.randint(1000, 9999)}",
            "timestamp": kwargs.get("timestamp", datetime.utcnow().isoformat()),
            "latitude": base_lat + random.uniform(-0.1, 0.1),
            "longitude": base_lon + random.uniform(-0.1, 0.1),
            "city": city,
            "speed_mph": round(random.uniform(0, 60), 1),
            "heading": random.randint(0, 359),
            "accuracy_meters": random.randint(5, 50),
        }

        event.update(kwargs)
        return event

    return _generate


@pytest.fixture
def generate_rating_event():
    """Factory fixture to generate mock rating events."""

    def _generate(
        rating_id: Optional[str] = None,
        ride_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        event = {
            "event_type": "ride_rated",
            "event_id": str(uuid.uuid4()),
            "rating_id": rating_id or str(uuid.uuid4()),
            "ride_id": ride_id or str(uuid.uuid4()),
            "rider_id": f"rider_{random.randint(1000, 9999)}",
            "driver_id": f"driver_{random.randint(1000, 9999)}",
            "timestamp": kwargs.get("timestamp", datetime.utcnow().isoformat()),
            "rating": kwargs.get("rating", random.randint(1, 5)),
            "comment": kwargs.get("comment", "Great ride!"),
            "tags": kwargs.get("tags", random.sample(["clean", "safe", "friendly", "fast"], k=2)),
        }

        event.update(kwargs)
        return event

    return _generate


# ============================================================================
# RESOURCE SETUP FIXTURES
# ============================================================================

@pytest.fixture
def setup_kinesis_streams(kinesis_client, project_name, environment):
    """Setup Kinesis streams for testing."""
    stream_names = {
        "rides": f"{project_name}-rides-stream-{environment}",
        "locations": f"{project_name}-locations-stream-{environment}",
        "payments": f"{project_name}-payments-stream-{environment}",
        "ratings": f"{project_name}-ratings-stream-{environment}",
    }

    for stream_type, stream_name in stream_names.items():
        kinesis_client.create_stream(
            StreamName=stream_name,
            ShardCount=2 if stream_type in ["rides", "locations"] else 1
        )

    yield stream_names

    # Cleanup
    for stream_name in stream_names.values():
        try:
            kinesis_client.delete_stream(StreamName=stream_name)
        except Exception:
            pass


@pytest.fixture
def setup_dynamodb_tables(dynamodb_resource, project_name):
    """Setup DynamoDB tables for testing."""
    tables = {}

    # Rides State Table
    rides_table = dynamodb_resource.create_table(
        TableName=f"{project_name}-rides-state",
        KeySchema=[
            {"AttributeName": "ride_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "ride_id", "AttributeType": "S"},
            {"AttributeName": "rider_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "rider-timestamp-index",
                "KeySchema": [
                    {"AttributeName": "rider_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    tables["rides_state"] = rides_table

    # Driver Availability Table
    drivers_table = dynamodb_resource.create_table(
        TableName=f"{project_name}-driver-availability",
        KeySchema=[
            {"AttributeName": "driver_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "driver_id", "AttributeType": "S"},
            {"AttributeName": "city", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "city-index",
                "KeySchema": [
                    {"AttributeName": "city", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    tables["driver_availability"] = drivers_table

    # Aggregated Metrics Table
    metrics_table = dynamodb_resource.create_table(
        TableName=f"{project_name}-aggregated-metrics",
        KeySchema=[
            {"AttributeName": "metric_type", "KeyType": "HASH"},
            {"AttributeName": "window_timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "metric_type", "AttributeType": "S"},
            {"AttributeName": "window_timestamp", "AttributeType": "S"},
        ],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    tables["aggregated_metrics"] = metrics_table

    yield tables

    # Cleanup
    for table in tables.values():
        try:
            table.delete()
        except Exception:
            pass


@pytest.fixture
def setup_s3_buckets(s3_client, project_name):
    """Setup S3 buckets for testing."""
    bucket_names = {
        "streaming_archive": f"{project_name}-streaming-archive",
        "analytics_output": f"{project_name}-analytics-output",
        "kinesis_analytics": f"{project_name}-kinesis-analytics",
    }

    for bucket_name in bucket_names.values():
        s3_client.create_bucket(Bucket=bucket_name)

    yield bucket_names

    # Cleanup
    for bucket_name in bucket_names.values():
        try:
            # Delete all objects first
            objects = s3_client.list_objects_v2(Bucket=bucket_name)
            if "Contents" in objects:
                for obj in objects["Contents"]:
                    s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
            s3_client.delete_bucket(Bucket=bucket_name)
        except Exception:
            pass


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def wait_for_stream_active(kinesis_client):
    """Helper to wait for Kinesis stream to become active."""

    def _wait(stream_name: str, timeout: int = 30):
        import time
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = kinesis_client.describe_stream(StreamName=stream_name)
                if response["StreamDescription"]["StreamStatus"] == "ACTIVE":
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    return _wait


@pytest.fixture
def put_kinesis_records(kinesis_client):
    """Helper to put records to Kinesis stream."""

    def _put(stream_name: str, records: List[Dict[str, Any]]):
        kinesis_records = [
            {
                "Data": json.dumps(record),
                "PartitionKey": record.get("ride_id") or record.get("driver_id") or str(uuid.uuid4())
            }
            for record in records
        ]

        response = kinesis_client.put_records(
            StreamName=stream_name,
            Records=kinesis_records
        )

        return response

    return _put


@pytest.fixture
def seed_dynamodb_data(dynamodb_resource):
    """Helper to seed DynamoDB tables with test data."""

    def _seed(table_name: str, items: List[Dict[str, Any]]):
        table = dynamodb_resource.Table(table_name)

        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)

    return _seed
