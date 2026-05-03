#!/bin/bash

###############################################################################
# Module 18: Advanced Architectures - AWS Infrastructure Initialization
#
# This script initializes AWS resources for the advanced architectures
# exercises (Lambda, Kappa, Data Mesh, CQRS).
#
# What it creates:
# - S3 buckets for data lake layers
# - DynamoDB tables for event store and metadata
# - Kinesis streams for real-time processing
# - Glue databases and tables
# - IAM roles and policies
# - EventBridge event bus
#
# Usage:
#   ./infrastructure/init-aws.sh [--env localstack|aws] [--region us-east-1]
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
ENVIRONMENT="localstack"
REGION="us-east-1"
LOCALSTACK_ENDPOINT="http://localhost:4566"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# AWS CLI configuration
if [ "$ENVIRONMENT" = "localstack" ]; then
    AWS_CMD="aws --endpoint-url=$LOCALSTACK_ENDPOINT --region=$REGION"
else
    AWS_CMD="aws --region=$REGION"
fi

log_info "Starting AWS infrastructure initialization..."
log_info "Environment: $ENVIRONMENT"
log_info "Region: $REGION"
echo ""

###############################################################################
# 1. S3 Buckets
###############################################################################

log_info "Creating S3 buckets..."

BUCKETS=(
    "advanced-arch-raw"
    "advanced-arch-processed"
    "advanced-arch-curated"
    "advanced-arch-batch-views"
    "advanced-arch-stream-checkpoints"
)

for bucket in "${BUCKETS[@]}"; do
    if $AWS_CMD s3 mb "s3://$bucket" 2>/dev/null; then
        log_success "Created bucket: $bucket"
    else
        log_info "Bucket exists: $bucket"
    fi
done

###############################################################################
# 2. DynamoDB Tables
###############################################################################

log_info "Creating DynamoDB tables..."

# Event Store (CQRS Exercise)
$AWS_CMD dynamodb create-table \
    --table-name event_store \
    --attribute-definitions \
        AttributeName=aggregate_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=aggregate_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE \
    2>/dev/null && log_success "Created table: event_store" || log_info "Table exists: event_store"

# Event Snapshots
$AWS_CMD dynamodb create-table \
    --table-name event_snapshots \
    --attribute-definitions \
        AttributeName=aggregate_id,AttributeType=S \
    --key-schema \
        AttributeName=aggregate_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null && log_success "Created table: event_snapshots" || log_info "Table exists: event_snapshots"

# Speed Layer Metrics (Lambda Architecture)
$AWS_CMD dynamodb create-table \
    --table-name speed_layer_metrics \
    --attribute-definitions \
        AttributeName=metric_key,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=metric_key,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null && log_success "Created table: speed_layer_metrics" || log_info "Table exists: speed_layer_metrics"

# Materialized Views Metadata (Kappa Architecture)
$AWS_CMD dynamodb create-table \
    --table-name materialized_views \
    --attribute-definitions \
        AttributeName=view_name,AttributeType=S \
        AttributeName=version,AttributeType=N \
    --key-schema \
        AttributeName=view_name,KeyType=HASH \
        AttributeName=version,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null && log_success "Created table: materialized_views" || log_info "Table exists: materialized_views"

# Data Product Catalog (Data Mesh)
$AWS_CMD dynamodb create-table \
    --table-name data_product_catalog \
    --attribute-definitions \
        AttributeName=domain,AttributeType=S \
        AttributeName=product_name,AttributeType=S \
    --key-schema \
        AttributeName=domain,KeyType=HASH \
        AttributeName=product_name,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null && log_success "Created table: data_product_catalog" || log_info "Table exists: data_product_catalog"

###############################################################################
# 3. Kinesis Streams
###############################################################################

log_info "Creating Kinesis streams..."

STREAMS=(
    "raw-events-stream"
    "processed-events-stream"
    "aggregate-metrics-stream"
)

for stream in "${STREAMS[@]}"; do
    $AWS_CMD kinesis create-stream \
        --stream-name "$stream" \
        --shard-count 2 \
        2>/dev/null && log_success "Created stream: $stream" || log_info "Stream exists: $stream"
done

###############################################################################
# 4. Glue Databases
###############################################################################

log_info "Creating Glue databases..."

DATABASES=(
    "raw_zone"
    "processed_zone"
    "curated_zone"
    "batch_views"
    "product_domain"
    "sales_domain"
    "customer_domain"
)

for db in "${DATABASES[@]}"; do
    $AWS_CMD glue create-database \
        --database-input "{\"Name\": \"$db\"}" \
        2>/dev/null && log_success "Created database: $db" || log_info "Database exists: $db"
done

###############################################################################
# 5. EventBridge Event Bus
###############################################################################

log_info "Creating EventBridge event bus..."

$AWS_CMD events create-event-bus \
    --name data-mesh-events \
    2>/dev/null && log_success "Created event bus: data-mesh-events" || log_info "Event bus exists: data-mesh-events"

###############################################################################
# 6. IAM Roles (AWS only)
###############################################################################

if [ "$ENVIRONMENT" = "aws" ]; then
    log_info "Creating IAM roles..."

    # Lambda execution role
    LAMBDA_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

    aws iam create-role \
        --role-name AdvancedArchLambdaRole \
        --assume-role-policy-document "$LAMBDA_TRUST_POLICY" \
        2>/dev/null && log_success "Created role: AdvancedArchLambdaRole" || log_info "Role exists: AdvancedArchLambdaRole"

    # Attach policies
    aws iam attach-role-policy \
        --role-name AdvancedArchLambdaRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole \
        2>/dev/null

    aws iam attach-role-policy \
        --role-name AdvancedArchLambdaRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess \
        2>/dev/null

    log_success "Attached policies to Lambda role"
fi

###############################################################################
# Summary
###############################################################################

echo ""
log_success "AWS infrastructure initialization complete!"
echo ""
log_info "Created resources:"
echo "  - ${#BUCKETS[@]} S3 buckets"
echo "  - 5 DynamoDB tables"
echo "  - ${#STREAMS[@]} Kinesis streams"
echo "  - ${#DATABASES[@]} Glue databases"
echo "  - 1 EventBridge event bus"
echo ""
log_info "Next steps:"
echo "  1. Run setup script: ./scripts/setup.sh"
echo "  2. Start exercises: cd exercises/01-lambda-architecture"
echo "  3. Validate setup: ./scripts/validate.sh"
echo ""
