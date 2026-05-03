"""
Pytest configuration and shared fixtures for Checkpoint 02 acceptance tests.

This module provides fixtures for AWS clients, test data generation, and cleanup
operations for the Real-Time Analytics Platform.
"""

import os
import time
import pytest
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any
from faker import Faker
import random

# ============================================================================
# CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def aws_config() -> Dict[str, str]:
    """Load AWS configuration from environment variables."""
    return {
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "project_name": os.getenv("PROJECT_NAME", "rideshare-analytics"),
        "environment": os.getenv("ENVIRONMENT", "dev"),
    }


@pytest.fixture(scope="session")
def resource_prefix(aws_config: Dict[str, str]) -> str:
    """Generate resource prefix for resource naming."""
    return f"{aws_config['project_name']}-{aws_config['environment']}"


# ============================================================================
# AWS CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def kinesis_client(aws_config: Dict[str, str]):
    """Create Kinesis client."""
    return boto3.client("kinesis", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def lambda_client(aws_config: Dict[str, str]):
    """Create Lambda client."""
    return boto3.client("lambda", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def dynamodb_client(aws_config: Dict[str, str]):
    """Create DynamoDB client."""
    return boto3.client("dynamodb", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def dynamodb_resource(aws_config: Dict[str, str]):
    """Create DynamoDB resource for table operations."""
    return boto3.resource("dynamodb", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def s3_client(aws_config: Dict[str, str]):
    """Create S3 client."""
    return boto3.client("s3", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def stepfunctions_client(aws_config: Dict[str, str]):
    """Create Step Functions client."""
    return boto3.client("stepfunctions", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def cloudwatch_client(aws_config: Dict[str, str]):
    """Create CloudWatch client."""
    return boto3.client("cloudwatch", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def logs_client(aws_config: Dict[str, str]):
    """Create CloudWatch Logs client."""
    return boto3.client("logs", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def iam_client(aws_config: Dict[str, str]):
    """Create IAM client."""
    return boto3.client("iam", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def sns_client(aws_config: Dict[str, str]):
    """Create SNS client."""
    return boto3.client("sns", region_name=aws_config["region"])


@pytest.fixture(scope="session")
def sqs_client(aws_config: Dict[str, str]):
    """Create SQS client."""
    return boto3.client("sqs", region_name=aws_config["region"])


# ============================================================================
# TEST DATA GENERATION
# ============================================================================

@pytest.fixture
def test_data_generator():
    """Factory for generating test events."""
    fake = Faker()

    class TestDataGenerator:
        def __init__(self):
            self.fake = fake
            self.cities = ["New York", "San Francisco", "Chicago", "Los Angeles", "Seattle"]

        def generate_ride_request(self, ride_id: str = None) -> Dict[str, Any]:
            """Generate ride request event."""
            if ride_id is None:
                ride_id = f"ride-{self.fake.uuid4()}"

            return {
                "event_type": "ride_requested",
                "ride_id": ride_id,
                "rider_id": f"rider-{self.fake.random_int(1000, 9999)}",
                "timestamp": datetime.utcnow().isoformat(),
                "pickup_location": {
                    "lat": float(f"{self.fake.latitude():.6f}"),
                    "lon": float(f"{self.fake.longitude():.6f}"),
                    "address": self.fake.street_address(),
                    "city": random.choice(self.cities)
                },
                "dropoff_location": {
                    "lat": float(f"{self.fake.latitude():.6f}"),
                    "lon": float(f"{self.fake.longitude():.6f}"),
                    "address": self.fake.street_address(),
                    "city": random.choice(self.cities)
                },
                "ride_type": random.choice(["economy", "premium", "shared"]),
                "requested_at": datetime.utcnow().isoformat()
            }

        def generate_ride_started(self, ride_id: str) -> Dict[str, Any]:
            """Generate ride started event."""
            return {
                "event_type": "ride_started",
                "ride_id": ride_id,
                "driver_id": f"driver-{self.fake.random_int(1000, 9999)}",
                "timestamp": datetime.utcnow().isoformat(),
                "pickup_location": {
                    "lat": float(f"{self.fake.latitude():.6f}"),
                    "lon": float(f"{self.fake.longitude():.6f}")
                },
                "started_at": datetime.utcnow().isoformat()
            }

        def generate_ride_completed(self, ride_id: str) -> Dict[str, Any]:
            """Generate ride completed event."""
            distance_miles = round(random.uniform(1.0, 30.0), 2)
            duration_minutes = int(distance_miles * random.uniform(2, 4))
            base_fare = distance_miles * 2.5 + duration_minutes * 0.3

            return {
                "event_type": "ride_completed",
                "ride_id": ride_id,
                "timestamp": datetime.utcnow().isoformat(),
                "dropoff_location": {
                    "lat": float(f"{self.fake.latitude():.6f}"),
                    "lon": float(f"{self.fake.longitude():.6f}")
                },
                "distance_miles": distance_miles,
                "duration_minutes": duration_minutes,
                "fare": round(base_fare, 2),
                "surge_multiplier": round(random.uniform(1.0, 2.5), 1),
                "completed_at": datetime.utcnow().isoformat()
            }

        def generate_location_update(self, driver_id: str = None) -> Dict[str, Any]:
            """Generate driver location update event."""
            if driver_id is None:
                driver_id = f"driver-{self.fake.random_int(1000, 9999)}"

            return {
                "event_type": "location_update",
                "driver_id": driver_id,
                "timestamp": datetime.utcnow().isoformat(),
                "location": {
                    "lat": float(f"{self.fake.latitude():.6f}"),
                    "lon": float(f"{self.fake.longitude():.6f}"),
                    "accuracy": random.randint(5, 20)
                },
                "status": random.choice(["available", "on_ride", "offline"]),
                "city": random.choice(self.cities)
            }

        def generate_payment(self, ride_id: str) -> Dict[str, Any]:
            """Generate payment event."""
            amount = round(random.uniform(10.0, 100.0), 2)

            return {
                "event_type": "payment_processed",
                "payment_id": f"pay-{self.fake.uuid4()}",
                "ride_id": ride_id,
                "rider_id": f"rider-{self.fake.random_int(1000, 9999)}",
                "timestamp": datetime.utcnow().isoformat(),
                "amount": amount,
                "currency": "USD",
                "payment_method": random.choice(["credit_card", "debit_card", "wallet"]),
                "status": random.choice(["success", "pending"]),
                "processed_at": datetime.utcnow().isoformat()
            }

        def generate_suspicious_payment(self, ride_id: str) -> Dict[str, Any]:
            """Generate payment event with fraud indicators."""
            return {
                "event_type": "payment_processed",
                "payment_id": f"pay-{self.fake.uuid4()}",
                "ride_id": ride_id,
                "rider_id": f"rider-{self.fake.random_int(1000, 9999)}",
                "timestamp": datetime.utcnow().isoformat(),
                "amount": round(random.uniform(500.0, 1000.0), 2),  # Unusually high
                "currency": "USD",
                "payment_method": "credit_card",
                "status": "success",
                "fraud_indicators": {
                    "ip_country_mismatch": True,
                    "velocity_check_failed": True,
                    "cvv_match": False
                },
                "processed_at": datetime.utcnow().isoformat()
            }

        def generate_rating(self, ride_id: str, rating: int = None) -> Dict[str, Any]:
            """Generate rating event."""
            if rating is None:
                rating = random.randint(1, 5)

            return {
                "event_type": "rating_submitted",
                "rating_id": f"rating-{self.fake.uuid4()}",
                "ride_id": ride_id,
                "driver_id": f"driver-{self.fake.random_int(1000, 9999)}",
                "rider_id": f"rider-{self.fake.random_int(1000, 9999)}",
                "timestamp": datetime.utcnow().isoformat(),
                "rating": rating,
                "feedback": self.fake.sentence() if rating < 4 else "",
                "submitted_at": datetime.utcnow().isoformat()
            }

    return TestDataGenerator()


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture
def cleanup_kinesis_records():
    """Fixture to track and cleanup test records."""
    test_records = []

    yield test_records

    # Cleanup logic would go here if needed
    # For Kinesis, records expire automatically after retention period


@pytest.fixture
def cleanup_dynamodb_records(dynamodb_resource):
    """Fixture to cleanup DynamoDB test records after tests."""
    test_records = {"rides": [], "locations": [], "payments": []}

    yield test_records

    # Cleanup test records
    # Note: In practice, use test-specific partition keys for easy cleanup


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def wait_for_lambda_execution(logs_client, log_group_name: str, timeout: int = 30) -> bool:
    """Wait for Lambda function to execute and log."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            streams = logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy="LastEventTime",
                descending=True,
                limit=1
            )

            if streams.get("logStreams"):
                return True

        except Exception:
            pass

        time.sleep(2)

    return False


def get_cloudwatch_metric(cloudwatch_client, namespace: str, metric_name: str,
                          dimensions: List[Dict], minutes: int = 5) -> List[float]:
    """Retrieve CloudWatch metric datapoints."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes)

    response = cloudwatch_client.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=["Average", "Sum"]
    )

    return response.get("Datapoints", [])
