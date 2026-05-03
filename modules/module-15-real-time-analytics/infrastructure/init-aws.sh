#!/bin/bash

# Module 15: Real-Time Analytics - AWS LocalStack Initialization
# This script initializes AWS services in LocalStack for real-time analytics exercises

set -e

echo "====================================="
echo "Module 15: Initializing AWS Services"
echo "====================================="

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
until curl -s http://localhost:4566/_localstack/health | grep -q '"kinesis": "available"'; do
    echo "Waiting for LocalStack services..."
    sleep 2
done
echo "✓ LocalStack is ready"

# AWS endpoint configuration
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT="http://localhost:4566"

echo ""
echo "1. Creating Kinesis Data Streams..."

# Main event stream (4 shards for scalability)
awslocal kinesis create-stream \
    --stream-name events-stream \
    --shard-count 4 \
    --region us-east-1 || echo "Stream events-stream may already exist"

# Aggregated results stream (2 shards)
awslocal kinesis create-stream \
    --stream-name aggregated-stream \
    --shard-count 2 \
    --region us-east-1 || echo "Stream aggregated-stream may already exist"

# Fraud alerts stream (1 shard - low volume)
awslocal kinesis create-stream \
    --stream-name fraud-alerts-stream \
    --shard-count 1 \
    --region us-east-1 || echo "Stream fraud-alerts-stream may already exist"

# Dead letter queue stream
awslocal kinesis create-stream \
    --stream-name dlq-stream \
    --shard-count 1 \
    --region us-east-1 || echo "Stream dlq-stream may already exist"

echo "✓ Kinesis streams created"

echo ""
echo "2. Creating DynamoDB tables..."

# Real-time aggregates table
awslocal dynamodb create-table \
    --table-name realtime-aggregates \
    --attribute-definitions \
        AttributeName=metric_name,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=metric_name,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 || echo "Table realtime-aggregates may already exist"

# User sessions table
awslocal dynamodb create-table \
    --table-name user-sessions \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
        AttributeName=session_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 || echo "Table user-sessions may already exist"

# Fraud detection results
awslocal dynamodb create-table \
    --table-name fraud-detections \
    --attribute-definitions \
        AttributeName=transaction_id,AttributeType=S \
        AttributeName=detected_at,AttributeType=N \
    --key-schema \
        AttributeName=transaction_id,KeyType=HASH \
        AttributeName=detected_at,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 || echo "Table fraud-detections may already exist"

echo "✓ DynamoDB tables created"

echo ""
echo "3. Creating S3 buckets..."

# Analytics checkpoints bucket
awslocal s3 mb s3://analytics-checkpoints --region us-east-1 || echo "Bucket may already exist"

# Analytics savepoints bucket
awslocal s3 mb s3://analytics-savepoints --region us-east-1 || echo "Bucket may already exist"

# Data lake bucket for archived analytics
awslocal s3 mb s3://analytics-data-lake --region us-east-1 || echo "Bucket may already exist"

echo "✓ S3 buckets created"

echo ""
echo "4. Creating SNS topics for alerts..."

# Fraud alert notifications
awslocal sns create-topic \
    --name fraud-alerts \
    --region us-east-1 || echo "Topic may already exist"

# System health alerts
awslocal sns create-topic \
    --name system-health-alerts \
    --region us-east-1 || echo "Topic may already exist"

# Cost anomaly alerts
awslocal sns create-topic \
    --name cost-anomaly-alerts \
    --region us-east-1 || echo "Topic may already exist"

echo "✓ SNS topics created"

echo ""
echo "5. Creating SQS queues..."

# Processing queue for async tasks
awslocal sqs create-queue \
    --queue-name analytics-processing-queue \
    --region us-east-1 || echo "Queue may already exist"

# Dead letter queue
awslocal sqs create-queue \
    --queue-name analytics-dlq \
    --region us-east-1 || echo "Queue may already exist"

echo "✓ SQS queues created"

echo ""
echo "6. Setting up CloudWatch Log Groups..."

# Flink application logs
awslocal logs create-log-group \
    --log-group-name /aws/kinesis-analytics/flink-apps \
    --region us-east-1 || echo "Log group may already exist"

# Lambda function logs (if using Lambda consumers)
awslocal logs create-log-group \
    --log-group-name /aws/lambda/analytics-consumer \
    --region us-east-1 || echo "Log group may already exist"

echo "✓ CloudWatch log groups created"

echo ""
echo "7. Creating IAM roles (LocalStack simulation)..."

# Create basic IAM role for Kinesis Analytics
ROLE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "kinesisanalytics.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

awslocal iam create-role \
    --role-name KinesisAnalyticsRole \
    --assume-role-policy-document "$ROLE_POLICY" \
    --region us-east-1 || echo "Role may already exist"

echo "✓ IAM roles created"

echo ""
echo "====================================="
echo "AWS Services Initialization Complete!"
echo "====================================="
echo ""
echo "Available Resources:"
echo "  - Kinesis Streams: events-stream (4 shards), aggregated-stream (2 shards)"
echo "  - DynamoDB Tables: realtime-aggregates, user-sessions, fraud-detections"
echo "  - S3 Buckets: analytics-checkpoints, analytics-savepoints, analytics-data-lake"
echo "  - SNS Topics: fraud-alerts, system-health-alerts, cost-anomaly-alerts"
echo "  - SQS Queues: analytics-processing-queue, analytics-dlq"
echo ""
echo "Verify installation:"
echo "  awslocal kinesis list-streams"
echo "  awslocal dynamodb list-tables"
echo "  awslocal s3 ls"
echo ""
echo "Flink Web UI: http://localhost:8081"
echo "Grafana: http://localhost:3000 (admin/admin123)"
echo ""
