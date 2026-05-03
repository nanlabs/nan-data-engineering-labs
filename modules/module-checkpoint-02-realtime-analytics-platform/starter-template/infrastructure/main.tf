# ============================================================================
# CHECKPOINT 02: REAL-TIME ANALYTICS PLATFORM - TERRAFORM INFRASTRUCTURE
# ============================================================================
# STARTER TEMPLATE - Complete the TODOs to deploy the infrastructure
#
# This file provides scaffolding for deploying a real-time analytics platform
# You'll need to complete the configuration blocks marked with TODO comments
# ============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# PROVIDER CONFIGURATION (COMPLETE)
# ============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Module      = "checkpoint-02-realtime-analytics"
    })
  }
}

# ============================================================================
# DATA SOURCES (COMPLETE)
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# KMS ENCRYPTION KEYS
# ============================================================================

# TODO 1: Create KMS key for Kinesis encryption
# Hints:
# - Use aws_kms_key resource
# - Set description = "KMS key for Kinesis Data Streams encryption"
# - Enable key rotation with enable_key_rotation = true
# - Set deletion_window_in_days = 30
resource "aws_kms_key" "kinesis" {
  # TODO: Complete this resource
  description             = "KMS key for Kinesis Data Streams encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-kinesis-key"
  }
}

resource "aws_kms_alias" "kinesis" {
  name          = "alias/${var.project_name}-kinesis"
  target_key_id = aws_kms_key.kinesis.key_id
}

# TODO 2: Create KMS keys for DynamoDB and S3
# Follow the same pattern as the Kinesis key above
resource "aws_kms_key" "dynamodb" {
  # TODO: Complete this resource
  description             = "KMS key for DynamoDB encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-dynamodb-key"
  }
}

resource "aws_kms_alias" "dynamodb" {
  name          = "alias/${var.project_name}-dynamodb"
  target_key_id = aws_kms_key.dynamodb.key_id
}

resource "aws_kms_key" "s3" {
  # TODO: Complete this resource
  description             = "KMS key for S3 encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-s3-key"
  }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${var.project_name}-s3"
  target_key_id = aws_kms_key.s3.key_id
}

# ============================================================================
# KINESIS DATA STREAMS
# ============================================================================

# TODO 3: Create Kinesis stream for ride events
# Hints:
# - Use aws_kinesis_stream resource
# - Set shard_count = var.kinesis_shard_count
# - Set retention_period = 24 (hours)
# - Enable encryption with encryption_type = "KMS"
# - Use kms_key_id = aws_kms_key.kinesis.key_id
resource "aws_kinesis_stream" "rides" {
  name             = "${var.project_name}-${var.environment}-rides-stream"

  # TODO: Configure shard count from variable
  shard_count      = var.kinesis_shard_count

  # TODO: Set retention period to 24 hours
  retention_period = 24

  # TODO: Enable KMS encryption
  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.key_id

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords"
  ]

  tags = {
    Name = "${var.project_name}-rides-stream"
  }
}

# TODO 4: Create additional Kinesis streams
# Create streams for: locations, payments, and ratings
# Follow the same pattern as rides stream above
resource "aws_kinesis_stream" "locations" {
  name             = "${var.project_name}-${var.environment}-locations-stream"

  # TODO: Complete configuration
  shard_count      = var.kinesis_shard_count
  retention_period = 24
  encryption_type  = "KMS"
  kms_key_id       = aws_kms_key.kinesis.key_id

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords"
  ]

  tags = {
    Name = "${var.project_name}-locations-stream"
  }
}

resource "aws_kinesis_stream" "payments" {
  name             = "${var.project_name}-${var.environment}-payments-stream"

  # TODO: Complete configuration
  shard_count      = 1  # Payments stream can have fewer shards
  retention_period = 24
  encryption_type  = "KMS"
  kms_key_id       = aws_kms_key.kinesis.key_id

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords"
  ]

  tags = {
    Name = "${var.project_name}-payments-stream"
  }
}

resource "aws_kinesis_stream" "ratings" {
  name             = "${var.project_name}-${var.environment}-ratings-stream"

  # TODO: Complete configuration
  shard_count      = 1  # Ratings stream can have fewer shards
  retention_period = 24
  encryption_type  = "KMS"
  kms_key_id       = aws_kms_key.kinesis.key_id

  tags = {
    Name = "${var.project_name}-ratings-stream"
  }
}

# ============================================================================
# S3 BUCKETS
# ============================================================================

# TODO 5: Create S3 bucket for data storage
# Hints:
# - Use aws_s3_bucket resource
# - Bucket name: "${var.project_name}-${var.environment}-data-${data.aws_region.current.name}"
# - Enable versioning with aws_s3_bucket_versioning
# - Enable encryption with aws_s3_bucket_server_side_encryption_configuration
resource "aws_s3_bucket" "data" {
  bucket = "${var.project_name}-${var.environment}-data-${data.aws_region.current.name}"

  tags = {
    Name = "${var.project_name}-data"
  }
}

# TODO 6: Enable versioning on S3 bucket
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"  # TODO: Enable versioning
  }
}

# TODO 7: Configure S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      # TODO: Configure KMS encryption
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}

# TODO 8: Configure S3 lifecycle policy
# Hints:
# - Transition raw data to Infrequent Access after 30 days
# - Transition to Glacier after 90 days
# - Expire after 365 days
resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "archive-raw-data"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      # TODO: Configure transition to IA after 30 days
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      # TODO: Configure transition to Glacier after 90 days
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      # TODO: Configure expiration after 365 days
      days = 365
    }
  }
}

# ============================================================================
# DYNAMODB TABLES
# ============================================================================

# TODO 9: Create DynamoDB table for rides
# Hints:
# - Use aws_dynamodb_table resource
# - Partition key: ride_id (String)
# - Billing mode: PAY_PER_REQUEST
# - Enable point_in_time_recovery
# - Enable server_side_encryption with KMS
resource "aws_dynamodb_table" "rides" {
  name         = "${var.project_name}-${var.environment}-rides"
  billing_mode = "PAY_PER_REQUEST"  # TODO: Set billing mode

  # TODO: Configure partition key
  hash_key = "ride_id"

  attribute {
    name = "ride_id"
    type = "S"
  }

  # TODO 10: Add GSI for querying by rider_id
  # Hints:
  # - Index name: rider-index
  # - Partition key: rider_id
  # - Projection type: ALL
  attribute {
    name = "rider_id"
    type = "S"
  }

  global_secondary_index {
    name            = "rider-index"
    hash_key        = "rider_id"
    projection_type = "ALL"
  }

  # TODO: Add GSI for querying by driver_id
  attribute {
    name = "driver_id"
    type = "S"
  }

  global_secondary_index {
    name            = "driver-index"
    hash_key        = "driver_id"
    projection_type = "ALL"
  }

  # TODO 11: Enable DynamoDB Streams
  # Hints:
  # - Set stream_enabled = true
  # - Set stream_view_type = "NEW_AND_OLD_IMAGES"
  stream_enabled   = true  # TODO: Enable streams
  stream_view_type = "NEW_AND_OLD_IMAGES"

  # TODO: Enable Point-in-Time Recovery
  point_in_time_recovery {
    enabled = true
  }

  # TODO: Enable encryption with KMS
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = {
    Name = "${var.project_name}-rides"
  }
}

# TODO 12: Create DynamoDB tables for drivers and payments
# Follow similar pattern as rides table
resource "aws_dynamodb_table" "drivers" {
  name         = "${var.project_name}-${var.environment}-drivers"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "driver_id"

  attribute {
    name = "driver_id"
    type = "S"
  }

  # TODO: Add GSI for querying by city
  attribute {
    name = "city"
    type = "S"
  }

  global_secondary_index {
    name            = "city-index"
    hash_key        = "city"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = {
    Name = "${var.project_name}-drivers"
  }
}

resource "aws_dynamodb_table" "payments" {
  name         = "${var.project_name}-${var.environment}-payments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "payment_id"

  attribute {
    name = "payment_id"
    type = "S"
  }

  # TODO: Add GSI for querying by ride_id
  attribute {
    name = "ride_id"
    type = "S"
  }

  global_secondary_index {
    name            = "ride-index"
    hash_key        = "ride_id"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = {
    Name = "${var.project_name}-payments"
  }
}

# ============================================================================
# IAM ROLES FOR LAMBDA FUNCTIONS
# ============================================================================

# TODO 13: Create IAM role for Lambda execution
# Hints:
# - Use aws_iam_role resource
# - Trust policy should allow lambda.amazonaws.com to assume the role
# - Attach AWSLambdaBasicExecutionRole policy
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-${var.environment}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"  # TODO: Set Lambda service principal
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-execution"
  }
}

# TODO 14: Attach policies to Lambda execution role
# Hints:
# - Kinesis read permissions
# - DynamoDB write permissions
# - S3 write permissions
# - CloudWatch Logs write permissions
resource "aws_iam_role_policy" "lambda_kinesis_dynamodb" {
  name = "lambda-kinesis-dynamodb-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # TODO: Add Kinesis permissions
        Effect = "Allow"
        Action = [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:ListShards",
          "kinesis:ListStreams"
        ]
        Resource = [
          aws_kinesis_stream.rides.arn,
          aws_kinesis_stream.locations.arn,
          aws_kinesis_stream.payments.arn,
          aws_kinesis_stream.ratings.arn
        ]
      },
      {
        # TODO: Add DynamoDB permissions
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.rides.arn,
          aws_dynamodb_table.drivers.arn,
          aws_dynamodb_table.payments.arn,
          "${aws_dynamodb_table.rides.arn}/index/*",
          "${aws_dynamodb_table.drivers.arn}/index/*",
          "${aws_dynamodb_table.payments.arn}/index/*"
        ]
      },
      {
        # TODO: Add S3 permissions
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/*"
      }
    ]
  })
}

# Attach CloudWatch Logs policy
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ============================================================================
# LAMBDA FUNCTIONS (PLACEHOLDER)
# ============================================================================

# TODO 15: Create Lambda function for rides processing
# Hints:
# - Use aws_lambda_function resource
# - Runtime: python3.11
# - Handler: handler.lambda_handler
# - Memory: 512 MB
# - Timeout: 60 seconds
# - Environment variables: DYNAMODB_TABLE_PREFIX, S3_BUCKET, AWS_REGION
# NOTE: You'll need to package and upload the Lambda code separately
# For now, create a placeholder zip file

# Placeholder Lambda package (referenced in README)
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda_placeholder.zip"

  source {
    content  = "# Placeholder - replace with actual Lambda code"
    filename = "handler.py"
  }
}

# TODO 16: Create Lambda functions
# You'll need to create separate functions for:
# - rides_processor
# - locations_processor
# - payments_processor
# - ratings_processor

# ============================================================================
# CLOUDWATCH LOG GROUPS
# ============================================================================

# TODO 17: Create CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_rides" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-rides-processor"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-rides-processor-logs"
  }
}

# TODO: Create log groups for other Lambda functions

# ============================================================================
# OUTPUTS
# ============================================================================

output "kinesis_streams" {
  description = "Kinesis stream names and ARNs"
  value = {
    rides     = aws_kinesis_stream.rides.name
    locations = aws_kinesis_stream.locations.name
    payments  = aws_kinesis_stream.payments.name
    ratings   = aws_kinesis_stream.ratings.name
  }
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    rides    = aws_dynamodb_table.rides.name
    drivers  = aws_dynamodb_table.drivers.name
    payments = aws_dynamodb_table.payments.name
  }
}

output "s3_bucket" {
  description = "S3 bucket for data storage"
  value       = aws_s3_bucket.data.id
}
