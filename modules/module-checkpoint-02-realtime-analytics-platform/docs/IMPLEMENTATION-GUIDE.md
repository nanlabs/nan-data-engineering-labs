# Implementation Guide: Real-Time Analytics Platform

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
- [Phase 2: Event Ingestion](#phase-2-event-ingestion)
- [Phase 3: Stream Processing](#phase-3-stream-processing)
- [Phase 4: State Management](#phase-4-state-management)
- [Phase 5: Workflow Orchestration](#phase-5-workflow-orchestration)
- [Phase 6: Data Quality](#phase-6-data-quality)
- [Phase 7: Visualization](#phase-7-visualization)
- [Phase 8: Monitoring and Alerts](#phase-8-monitoring-and-alerts)
- [Phase 9: Optimization](#phase-9-optimization)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)
- [Best Practices](#best-practices)

## Overview

This guide provides step-by-step instructions to implement the Real-Time Analytics Platform for RideShare. Follow each phase sequentially, testing as you go.

**Estimated Time**: 25-30 hours over 4 weeks

**Approach**: Incremental implementation with testing after each phase

## Prerequisites

### Environment Setup

```bash
# 1. Verify AWS CLI installation and configuration
aws --version  # Should be v2.x
aws sts get-caller-identity  # Should return your account info

# 2. Verify Terraform installation
terraform --version  # Should be v1.0+

# 3. Verify Python installation
python3 --version  # Should be 3.9+

# 4. Create project directory
mkdir -p ~/rideshare-platform
cd ~/rideshare-platform

# 5. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 6. Install development dependencies
pip install boto3 botocore requests jsonschema pytest black flake8 aws-xray-sdk
```

### AWS Account Preparation

```bash
# 1. Set default region
export AWS_DEFAULT_REGION=us-east-1
echo 'export AWS_DEFAULT_REGION=us-east-1' >> ~/.bashrc

# 2. Create S3 bucket for Terraform state
aws s3 mb s3://rideshare-terraform-state-$(aws sts get-caller-identity --query Account --output text)

# 3. Create DynamoDB table for Terraform state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 4. Set up billing alerts
aws cloudwatch put-metric-alarm \
  --alarm-name RideshareMonthlyBudget \
  --alarm-description "Alert when monthly cost exceeds $80" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## Phase 1: Infrastructure Setup

**Duration**: 2-3 hours

**Objective**: Provision all AWS resources using Terraform

### Step 1.1: Create Terraform Project Structure

```bash
# Create directory structure
mkdir -p terraform/{modules,environments}
cd terraform

# Create main Terraform files
touch main.tf variables.tf outputs.tf backend.tf
touch iam.tf kinesis.tf lambda.tf dynamodb.tf s3.tf
touch step-functions.tf eventbridge.tf cloudwatch.tf sns.tf
```

### Step 1.2: Configure Terraform Backend

**File: `terraform/backend.tf`**

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "rideshare-terraform-state-ACCOUNT_ID"  # Replace with your account ID
    key            = "realtime-analytics/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "RideShare"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
```

### Step 1.3: Define Variables

**File: `terraform/variables.tf`**

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "rideshare"
}

# Kinesis configuration
variable "kinesis_retention_hours" {
  description = "Kinesis stream retention period in hours"
  type        = number
  default     = 24
}

variable "kinesis_shard_count" {
  description = "Map of stream names to shard counts"
  type        = map(number)
  default = {
    ride_events        = 4
    driver_locations   = 2
    payment_events     = 2
    rating_events      = 1
  }
}

# DynamoDB configuration
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode"
  type        = string
  default     = "PAY_PER_REQUEST"  # Use PAY_PER_REQUEST for dev, PROVISIONED for prod
}

# Lambda configuration
variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}
```

### Step 1.4: Create Kinesis Streams

**File: `terraform/kinesis.tf`**

```hcl
# Kinesis Data Streams
resource "aws_kinesis_stream" "ride_events" {
  name             = "${var.project_name}-ride-events-${var.environment}"
  shard_count      = var.kinesis_shard_count["ride_events"]
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"  # or "ON_DEMAND" for auto-scaling
  }

  encryption_type = "KMS"
  kms_key_id     = aws_kms_key.kinesis.id
}

resource "aws_kinesis_stream" "driver_locations" {
  name             = "${var.project_name}-driver-locations-${var.environment}"
  shard_count      = var.kinesis_shard_count["driver_locations"]
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id     = aws_kms_key.kinesis.id
}

resource "aws_kinesis_stream" "payment_events" {
  name             = "${var.project_name}-payment-events-${var.environment}"
  shard_count      = var.kinesis_shard_count["payment_events"]
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id     = aws_kms_key.kinesis.id
}

resource "aws_kinesis_stream" "rating_events" {
  name             = "${var.project_name}-rating-events-${var.environment}"
  shard_count      = var.kinesis_shard_count["rating_events"]
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id     = aws_kms_key.kinesis.id
}

# KMS key for Kinesis encryption
resource "aws_kms_key" "kinesis" {
  description             = "KMS key for Kinesis stream encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "kinesis" {
  name          = "alias/${var.project_name}-kinesis-${var.environment}"
  target_key_id = aws_kms_key.kinesis.key_id
}
```

### Step 1.5: Create DynamoDB Tables

**File: `terraform/dynamodb.tf`**

```hcl
# Rides state table
resource "aws_dynamodb_table" "rides_state" {
  name           = "${var.project_name}-rides-state-${var.environment}"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "ride_id"

  attribute {
    name = "ride_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "request_timestamp"
    type = "N"
  }

  # GSI for querying by status
  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    range_key       = "request_timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl_timestamp"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
}

# Driver availability table
resource "aws_dynamodb_table" "driver_availability" {
  name           = "${var.project_name}-driver-availability-${var.environment}"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "driver_id"

  attribute {
    name = "driver_id"
    type = "S"
  }

  attribute {
    name = "city"
    type = "S"
  }

  attribute {
    name = "available"
    type = "N"
  }

  # GSI for querying available drivers by city
  global_secondary_index {
    name            = "CityAvailableIndex"
    hash_key        = "city"
    range_key       = "available"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl_timestamp"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# Aggregated metrics table
resource "aws_dynamodb_table" "aggregated_metrics" {
  name           = "${var.project_name}-aggregated-metrics-${var.environment}"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "metric_name"
  range_key      = "timestamp"

  attribute {
    name = "metric_name"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  ttl {
    attribute_name = "ttl_timestamp"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}
```

### Step 1.6: Create S3 Buckets

**File: `terraform/s3.tf`**

```hcl
# S3 bucket for event archive
resource "aws_s3_bucket" "event_archive" {
  bucket = "${var.project_name}-event-archive-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "event_archive" {
  bucket = aws_s3_bucket.event_archive.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "event_archive" {
  bucket = aws_s3_bucket.event_archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "event_archive" {
  bucket = aws_s3_bucket.event_archive.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years
    }
  }
}

# S3 bucket for Lambda deployment packages
resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "${var.project_name}-lambda-artifacts-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_encryption" "lambda_artifacts" {
  bucket = aws_s3_bucket.lambda_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
```

### Step 1.7: Create IAM Roles

**File: `terraform/iam.tf`**

```hcl
# Lambda execution role for ride processor
resource "aws_iam_role" "lambda_ride_processor" {
  name = "${var.project_name}-lambda-ride-processor-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_ride_processor" {
  name = "lambda-ride-processor-policy"
  role = aws_iam_role.lambda_ride_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:ListStreams"
        ]
        Resource = aws_kinesis_stream.ride_events.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.rides_state.arn,
          "${aws_dynamodb_table.rides_state.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.event_archive.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# Additional IAM roles for other Lambda functions would follow similar pattern
# (driver_location_processor, payment_processor, rating_processor)
```

### Step 1.8: Deploy Infrastructure

```bash
# Initialize Terraform
cd terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan -out=tfplan

# Review the plan carefully!
# Verify:
# - All resources are being created correctly
# - No unexpected changes
# - Resource names follow naming convention

# Apply the plan
terraform apply tfplan

# Save outputs
terraform output > outputs.txt

# Verify resources in AWS Console or CLI
aws kinesis list-streams
aws dynamodb list-tables
aws s3 ls | grep rideshare
```

**Expected Results**:
- 4 Kinesis streams created
- 3 DynamoDB tables created
- 2 S3 buckets created
- Multiple IAM roles created
- Deployment completes in <30 minutes

## Phase 2: Event Ingestion

**Duration**: 3-4 hours

**Objective**: Create event producers that generate realistic events and send to Kinesis

### Step 2.1: Create Project Structure

```bash
# Create source code structure
cd ~/rideshare-platform
mkdir -p src/{producers,lambda,analytics,step-functions,common}
mkdir -p schemas tests/{unit,integration,load}
mkdir -p scripts data

# Create __init__.py files
touch src/__init__.py
touch src/producers/__init__.py
touch src/lambda/__init__.py
touch src/common/__init__.py
```

### Step 2.2: Create Base Producer Class

**File: `src/producers/base_producer.py`**

```python
import boto3
import json
import time
import logging
from typing import List, Dict, Any
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseProducer:
    """Base class for Kinesis event producers."""

    def __init__(self, stream_name: str, region: str = 'us-east-1'):
        self.stream_name = stream_name
        self.kinesis_client = boto3.client('kinesis', region_name=region)
        self.batch_size = 500  # Kinesis PutRecords limit
        self.max_retries = 3
        self.retry_base_delay = 1  # seconds

    def put_records(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Put records to Kinesis stream with batching and retry logic.

        Args:
            records: List of record dictionaries with 'data' and 'partition_key'

        Returns:
            Dictionary with success and failure counts
        """
        total_records = len(records)
        success_count = 0
        failure_count = 0

        # Batch records
        for i in range(0, total_records, self.batch_size):
            batch = records[i:i + self.batch_size]

            # Format records for Kinesis
            kinesis_records = [
                {
                    'Data': json.dumps(record['data']),
                    'PartitionKey': record['partition_key']
                }
                for record in batch
            ]

            # Put records with retry logic
            success, failed = self._put_records_with_retry(kinesis_records)
            success_count += success
            failure_count += failed

        logger.info(f"Put {success_count} records successfully, {failure_count} failed")

        return {
            'success': success_count,
            'failed': failure_count
        }

    def _put_records_with_retry(self, records: List[Dict[str, str]]) -> tuple:
        """Put records with exponential backoff retry."""
        retry_count = 0
        remaining_records = records
        success_count = 0

        while retry_count < self.max_retries and remaining_records:
            try:
                response = self.kinesis_client.put_records(
                    Records=remaining_records,
                    StreamName=self.stream_name
                )

                # Check for failed records
                failed_records = []
                for idx, record_result in enumerate(response['Records']):
                    if 'ErrorCode' in record_result:
                        failed_records.append(remaining_records[idx])
                        logger.warning(f"Failed to put record: {record_result['ErrorCode']}")
                    else:
                        success_count += 1

                # If all successful, break
                if not failed_records:
                    break

                # Retry failed records
                remaining_records = failed_records
                retry_count += 1

                if retry_count < self.max_retries:
                    delay = self.retry_base_delay * (2 ** retry_count)
                    logger.info(f"Retrying {len(failed_records)} failed records after {delay}s...")
                    time.sleep(delay)

            except ClientError as e:
                logger.error(f"Error putting records: {e}")
                retry_count += 1

                if retry_count < self.max_retries:
                    delay = self.retry_base_delay * (2 ** retry_count)
                    logger.info(f"Retrying after {delay}s...")
                    time.sleep(delay)

        failure_count = len(remaining_records)
        return success_count, failure_count
```

### Step 2.3: Create Ride Event Producer

**File: `src/producers/ride_event_producer.py`**

```python
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from base_producer import BaseProducer


class RideEventProducer(BaseProducer):
    """Producer for ride events."""

    def __init__(self, stream_name: str):
        super().__init__(stream_name)

        # NYC coordinates for demo
        self.cities = {
            'new_york': {
                'lat_range': (40.70, 40.80),
                'lon_range': (-74.02, -73.95)
            },
            'los_angeles': {
                'lat_range': (33.95, 34.05),
                'lon_range': (-118.35, -118.25)
            },
            'chicago': {
                'lat_range': (41.85, 41.95),
                'lon_range': (-87.70, -87.60)
            }
        }

        self.ride_types = ['standard', 'premium', 'shared']
        self.statuses = ['requested', 'started', 'completed', 'cancelled']

    def generate_ride_requested_events(self, count: int) -> List[Dict[str, Any]]:
        """Generate ride_requested events."""
        events = []

        for _ in range(count):
            city_name = random.choice(list(self.cities.keys()))
            city = self.cities[city_name]

            # Random pickup and dropoff locations within city
            pickup_lat = random.uniform(*city['lat_range'])
            pickup_lon = random.uniform(*city['lon_range'])
            dropoff_lat = random.uniform(*city['lat_range'])
            dropoff_lon = random.uniform(*city['lon_range'])

            # Calculate estimated values
            distance_km = self._calculate_distance(
                pickup_lat, pickup_lon, dropoff_lat, dropoff_lon
            )
            estimated_fare = 2.50 + (distance_km * 1.50)  # Base + per km
            estimated_duration = int(distance_km * 4)  # Rough estimate

            event = {
                'data': {
                    'event_type': 'ride_requested',
                    'event_id': str(uuid.uuid4()),
                    'event_timestamp': datetime.utcnow().isoformat() + 'Z',
                    'ride_id': f"ride_{uuid.uuid4().hex[:12]}",
                    'customer_id': f"usr_{random.randint(10000000, 99999999)}",
                    'pickup_location': {
                        'lat': round(pickup_lat, 6),
                        'lon': round(pickup_lon, 6),
                        'city': city_name
                    },
                    'dropoff_location': {
                        'lat': round(dropoff_lat, 6),
                        'lon': round(dropoff_lon, 6),
                        'city': city_name
                    },
                    'ride_type': random.choice(self.ride_types),
                    'estimated_fare': round(estimated_fare, 2),
                    'estimated_duration_minutes': estimated_duration
                },
                'partition_key': city_name  # Partition by city for even distribution
            }

            events.append(event)

        return events

    def _calculate_distance(self, lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two points (simplified)."""
        # Simple Euclidean distance for demo (not accurate for real geospatial)
        return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111  # Convert to km

    def run(self, events_per_second: int, duration_seconds: int):
        """Run producer continuously."""
        total_events = events_per_second * duration_seconds

        print(f"Generating {total_events} ride events over {duration_seconds} seconds...")
        print(f"Rate: {events_per_second} events/second")

        start_time = datetime.now()

        for second in range(duration_seconds):
            # Generate events for this second
            events = self.generate_ride_requested_events(events_per_second)

            # Put to Kinesis
            result = self.put_records(events)

            print(f"Second {second + 1}/{duration_seconds}: "
                  f"Success={result['success']}, Failed={result['failed']}")

            # Sleep until next second
            elapsed = (datetime.now() - start_time).total_seconds()
            sleep_time = (second + 1) - elapsed
            if sleep_time > 0:
                import time
                time.sleep(sleep_time)

        print("Producer finished!")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Ride Event Producer')
    parser.add_argument('--stream-name', required=True, help='Kinesis stream name')
    parser.add_argument('--rate', type=int, default=10, help='Events per second')
    parser.add_argument('--duration', type=int, default=60, help='Duration in seconds')

    args = parser.parse_args()

    producer = RideEventProducer(args.stream_name)
    producer.run(args.rate, args.duration)
```

### Step 2.4: Test Event Producers

```bash
# Test ride event producer
cd ~/rideshare-platform/src/producers
python ride_event_producer.py \
  --stream-name rideshare-ride-events-dev \
  --rate 10 \
  --duration 60

# Monitor Kinesis metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis \
  --metric-name IncomingRecords \
  --dimensions Name=StreamName,Value=rideshare-ride-events-dev \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum

# Verify records in stream
aws kinesis get-shard-iterator \
  --stream-name rideshare-ride-events-dev \
  --shard-id shardId-000000000000 \
  --shard-iterator-type LATEST

# Use the shard iterator to get records
aws kinesis get-records --shard-iterator <ITERATOR_FROM_PREVIOUS_COMMAND> | jq '.Records[0].Data' | base64 -d | jq .
```

**Follow similar patterns for**:
- `driver_location_producer.py`
- `payment_producer.py`
- `rating_producer.py`

## Phase 3: Stream Processing

**Duration**: 5-6 hours

**Objective**: Implement Lambda functions to process streaming events

### Step 3.1: Create Common Utilities

**File: `src/common/config.py`**

```python
import os


class Config:
    """Configuration management."""

    # AWS settings
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

    # DynamoDB tables
    RIDES_STATE_TABLE = os.environ.get('RIDES_STATE_TABLE',
                                      f'rideshare-rides-state-{ENVIRONMENT}')
    DRIVER_AVAILABILITY_TABLE = os.environ.get('DRIVER_AVAILABILITY_TABLE',
                                               f'rideshare-driver-availability-{ENVIRONMENT}')
    AGGREGATED_METRICS_TABLE = os.environ.get('AGGREGATED_METRICS_TABLE',
                                              f'rideshare-aggregated-metrics-{ENVIRONMENT}')

    # S3 buckets
    EVENT_ARCHIVE_BUCKET = os.environ.get('EVENT_ARCHIVE_BUCKET',
                                          f'rideshare-event-archive-{ENVIRONMENT}')

    # Processing settings
    BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100'))
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
```

**File: `src/common/logger.py`**

```python
import logging
import json
from pythonjsonlogger import jsonlogger


def get_logger(name: str) -> logging.Logger:
    """Get structured JSON logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
```

### Step 3.2: Implement Ride Processor Lambda

**File: `src/lambda/ride_processor/handler.py`**

```python
import json
import boto3
from decimal import Decimal
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.config import Config
from common.logger import get_logger

logger = get_logger(__name__)

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=Config.AWS_REGION)
rides_table = dynamodb.Table(Config.RIDES_STATE_TABLE)
metrics_table = dynamodb.Table(Config.AGGREGATED_METRICS_TABLE)
s3_client = boto3.client('s3', region_name=Config.AWS_REGION)


def lambda_handler(event, context):
    """
    Process ride events from Kinesis.

    Event structure:
    {
        'Records': [
            {
                'kinesis': {
                    'data': '<base64-encoded JSON>',
                    'partitionKey': '<partition-key>',
                    'sequenceNumber': '<sequence-number>'
                },
                'eventName': 'aws:kinesis:record'
            }
        ]
    }
    """
    logger.info(f"Processing {len(event['Records'])} records")

    success_count = 0
    error_count = 0

    for record in event['Records']:
        try:
            # Decode Kinesis record
            import base64
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            ride_event = json.loads(payload)

            # Process based on event type
            event_type = ride_event.get('event_type')

            if event_type == 'ride_requested':
                process_ride_requested(ride_event)
            elif event_type == 'ride_started':
                process_ride_started(ride_event)
            elif event_type == 'ride_completed':
                process_ride_completed(ride_event)
            elif event_type == 'ride_cancelled':
                process_ride_cancelled(ride_event)
            else:
                logger.warning(f"Unknown event type: {event_type}")

            success_count += 1

        except Exception as e:
            logger.error(f"Error processing record: {e}", exc_info=True)
            error_count += 1

    logger.info(f"Processed {success_count} successfully, {error_count} errors")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': success_count,
            'errors': error_count
        })
    }


def process_ride_requested(event: dict):
    """Process ride_requested event."""
    ride_id = event['ride_id']

    # Write to DynamoDB
    rides_table.put_item(
        Item={
            'ride_id': ride_id,
            'customer_id': event['customer_id'],
            'status': 'requested',
            'request_timestamp': int(datetime.fromisoformat(
                event['event_timestamp'].replace('Z', '+00:00')
            ).timestamp()),
            'pickup_location': event['pickup_location'],
            'dropoff_location': event['dropoff_location'],
            'ride_type': event['ride_type'],
            'estimated_fare': Decimal(str(event['estimated_fare'])),
            'created_at': event['event_timestamp'],
            'updated_at': event['event_timestamp'],
            'ttl_timestamp': int(datetime.utcnow().timestamp()) + (7 * 24 * 3600)
        }
    )

    # Update metrics
    update_metric('active_rides_total', 1, 'increment')
    update_metric(f"active_rides_{event['pickup_location']['city']}", 1, 'increment')

    logger.info(f"Processed ride_requested: {ride_id}")


def process_ride_started(event: dict):
    """Process ride_started event."""
    ride_id = event['ride_id']

    # Update ride in DynamoDB
    rides_table.update_item(
        Key={'ride_id': ride_id},
        UpdateExpression='SET #st = :status, driver_id = :driver_id, '
                        'start_timestamp = :start_ts, updated_at = :updated_at',
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={
            ':status': 'in_progress',
            ':driver_id': event['driver_id'],
            ':start_ts': int(datetime.fromisoformat(
                event['event_timestamp'].replace('Z', '+00:00')
            ).timestamp()),
            ':updated_at': event['event_timestamp']
        }
    )

    logger.info(f"Processed ride_started: {ride_id}")


def process_ride_completed(event: dict):
    """Process ride_completed event."""
    ride_id = event['ride_id']

    # Update ride in DynamoDB
    rides_table.update_item(
        Key={'ride_id': ride_id},
        UpdateExpression='SET #st = :status, end_timestamp = :end_ts, '
                        'distance_km = :distance, duration_minutes = :duration, '
                        'final_fare = :fare, updated_at = :updated_at',
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={
            ':status': 'completed',
            ':end_ts': int(datetime.fromisoformat(
                event['event_timestamp'].replace('Z', '+00:00')
            ).timestamp()),
            ':distance': Decimal(str(event['distance_km'])),
            ':duration': event['duration_minutes'],
            ':fare': Decimal(str(event['final_fare'])),
            ':updated_at': event['event_timestamp']
        }
    )

    # Update metrics
    update_metric('active_rides_total', -1, 'increment')
    update_metric('completed_rides_total', 1, 'increment')
    update_metric('revenue_total', float(event['final_fare']), 'increment')

    logger.info(f"Processed ride_completed: {ride_id}")


def process_ride_cancelled(event: dict):
    """Process ride_cancelled event."""
    ride_id = event['ride_id']

    # Update ride in DynamoDB
    rides_table.update_item(
        Key={'ride_id': ride_id},
        UpdateExpression='SET #st = :status, updated_at = :updated_at',
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={
            ':status': 'cancelled',
            ':updated_at': event['event_timestamp']
        }
    )

    # Update metrics
    update_metric('active_rides_total', -1, 'increment')
    update_metric('cancelled_rides_total', 1, 'increment')

    logger.info(f"Processed ride_cancelled: {ride_id}")


def update_metric(metric_name: str, value: float, operation: str = 'set'):
    """Update aggregated metric in DynamoDB."""
    timestamp = int(datetime.utcnow().timestamp() // 60) * 60  # Round to minute

    try:
        if operation == 'increment':
            metrics_table.update_item(
                Key={
                    'metric_name': metric_name,
                    'timestamp': timestamp
                },
                UpdateExpression='ADD #val :inc SET updated_at = :updated_at',
                ExpressionAttributeNames={'#val': 'value'},
                ExpressionAttributeValues={
                    ':inc': Decimal(str(value)),
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
        else:  # set
            metrics_table.put_item(
                Item={
                    'metric_name': metric_name,
                    'timestamp': timestamp,
                    'value': Decimal(str(value)),
                    'updated_at': datetime.utcnow().isoformat(),
                    'ttl_timestamp': timestamp + (30 * 24 * 3600)
                }
            )
    except Exception as e:
        logger.error(f"Error updating metric {metric_name}: {e}")
```

### Step 3.3: Package and Deploy Lambda

```bash
# Package Lambda function
cd src/lambda/ride_processor
pip install -r requirements.txt -t .
zip -r ride_processor.zip . -x "*.pyc" -x "__pycache__/*"

# Upload to S3
aws s3 cp ride_processor.zip s3://rideshare-lambda-artifacts-dev-ACCOUNT_ID/

# Update Terraform to create Lambda function
# (Add to terraform/lambda.tf)

# Deploy
cd ~/rideshare-platform/terraform
terraform apply
```

### Step 3.4: Configure Event Source Mapping

```bash
# Create event source mapping (Lambda to Kinesis)
aws lambda create-event-source-mapping \
  --function-name rideshare-ride-processor-dev \
  --event-source-arn $(aws kinesis describe-stream --stream-name rideshare-ride-events-dev --query 'StreamDescription.StreamARN' --output text) \
  --batch-size 100 \
  --starting-position LATEST \
  --maximum-batching-window-in-seconds 5
```

## Phase 4-9: Continue Implementation

Due to space constraints, the remaining phases (State Management, Workflow Orchestration, Data Quality, Visualization, Monitoring, and Optimization) follow similar patterns as demonstrated above.

**Key principles to follow**:
1. Implement incrementally
2. Test after each component
3. Monitor metrics and logs
4. Optimize for cost and performance
5. Document as you go

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_ride_processor.py
import pytest
from unittest.mock import Mock, patch
from src.lambda.ride_processor import handler


def test_process_ride_requested():
    """Test processing of ride_requested event."""
    event = {
        'Records': [
            {
                'kinesis': {
                    'data': base64.b64encode(json.dumps({
                        'event_type': 'ride_requested',
                        'ride_id': 'ride_test123',
                        'customer_id': 'usr_12345',
                        # ... rest of event data
                    }).encode('utf-8')).decode('utf-8')
                }
            }
        ]
    }

    with patch('handler.rides_table') as mock_table:
        result = handler.lambda_handler(event, None)
        assert result['statusCode'] == 200
        mock_table.put_item.assert_called_once()
```

### Integration Tests

```python
# tests/integration/test_end_to_end.py
import boto3
import time


def test_end_to_end_flow():
    """Test complete flow from Kinesis to DynamoDB."""
    kinesis = boto3.client('kinesis')
    dynamodb = boto3.resource('dynamodb')

    # Put test event to Kinesis
    ride_id = f"ride_test_{int(time.time())}"
    kinesis.put_record(
        StreamName='rideshare-ride-events-dev',
        Data=json.dumps({
            'event_type': 'ride_requested',
            'ride_id': ride_id,
            # ... event data
        }),
        PartitionKey=ride_id
    )

    # Wait for processing
    time.sleep(10)

    # Verify in DynamoDB
    table = dynamodb.Table('rideshare-rides-state-dev')
    response = table.get_item(Key={'ride_id': ride_id})

    assert 'Item' in response
    assert response['Item']['status'] == 'requested'
```

### Load Tests

```python
# tests/load/test_high_volume.py
from src.producers.ride_event_producer import RideEventProducer


def test_1000_events_per_second():
    """Test system handles 1000 events/second."""
    producer = RideEventProducer('rideshare-ride-events-dev')

    # Run for 5 minutes at 1000 events/second
    producer.run(events_per_second=1000, duration_seconds=300)

    # Verify metrics
    # Check CloudWatch for:
    # - No throttling errors
    # - Lambda invocations match event count
    # - DynamoDB writes successful
```

## Best Practices

1. **Idempotent Processing**: Design Lambda functions to handle duplicate events
2. **Error Handling**: Use try/except blocks, log errors, use DLQ
3. **Monitoring**: Instrument code with CloudWatch metrics and X-Ray traces
4. **Cost Optimization**: Right-size Lambda memory, optimize DynamoDB capacity
5. **Security**: Never hardcode credentials, use IAM roles, encrypt data
6. **Testing**: Write unit and integration tests, run load tests
7. **Documentation**: Comment complex logic, maintain runbooks
8. **Version Control**: Use Git, tag releases, review PRs
9. **Observability**: Structured logging, distributed tracing, metrics
10. **Scalability**: Design for horizontal scaling, use auto-scaling

---

**Next Steps**: Proceed to [ARCHITECTURE-DECISIONS.md](ARCHITECTURE-DECISIONS.md) to understand key architectural choices, and [COST-ESTIMATION.md](COST-ESTIMATION.md) for cost optimization strategies.
