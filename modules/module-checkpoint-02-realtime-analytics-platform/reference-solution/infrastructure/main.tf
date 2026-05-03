# ============================================================================
# CHECKPOINT 02: REAL-TIME ANALYTICS PLATFORM - TERRAFORM INFRASTRUCTURE
# ============================================================================
# This Terraform configuration deploys a complete real-time analytics platform
# for processing rideshare events using AWS serverless services.
#
# Architecture Components:
# - Kinesis Data Streams for event ingestion
# - Lambda functions for stream processing
# - Kinesis Data Analytics for real-time transformations
# - DynamoDB for state management
# - S3 for data archival
# - Step Functions for orchestration
# - CloudWatch for monitoring
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
# PROVIDER CONFIGURATION
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
# DATA SOURCES
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# KMS ENCRYPTION KEYS
# ============================================================================

resource "aws_kms_key" "kinesis" {
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

resource "aws_kms_key" "dynamodb" {
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

resource "aws_kinesis_stream" "rides" {
  name             = "${var.project_name}-rides-stream-${var.environment}"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds"
  ]

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.arn

  tags = {
    Name        = "${var.project_name}-rides-stream"
    StreamType  = "rides"
    Criticality = "high"
  }
}

resource "aws_kinesis_stream" "locations" {
  name             = "${var.project_name}-locations-stream-${var.environment}"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds"
  ]

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.arn

  tags = {
    Name        = "${var.project_name}-locations-stream"
    StreamType  = "locations"
    Frequency   = "high"
    Criticality = "medium"
  }
}

resource "aws_kinesis_stream" "payments" {
  name             = "${var.project_name}-payments-stream-${var.environment}"
  shard_count      = 1  # Lower volume stream
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds"
  ]

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.arn

  tags = {
    Name        = "${var.project_name}-payments-stream"
    StreamType  = "payments"
    Criticality = "critical"
    Compliance  = "PCI-DSS"
  }
}

resource "aws_kinesis_stream" "ratings" {
  name             = "${var.project_name}-ratings-stream-${var.environment}"
  shard_count      = 1  # Low volume stream
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords"
  ]

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.arn

  tags = {
    Name        = "${var.project_name}-ratings-stream"
    StreamType  = "ratings"
    Criticality = "low"
  }
}

# ============================================================================
# IAM ROLES AND POLICIES
# ============================================================================

# Lambda Kinesis Role
resource "aws_iam_role" "lambda_kinesis" {
  name = "${var.project_name}-lambda-kinesis-role-${var.environment}"

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

  tags = {
    Name = "${var.project_name}-lambda-kinesis-role"
  }
}

resource "aws_iam_role_policy" "lambda_kinesis" {
  name = "${var.project_name}-lambda-kinesis-policy"
  role = aws_iam_role.lambda_kinesis.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:DescribeStreamSummary",
          "kinesis:ListShards",
          "kinesis:ListStreams",
          "kinesis:SubscribeToShard"
        ]
        Resource = [
          aws_kinesis_stream.rides.arn,
          aws_kinesis_stream.locations.arn,
          aws_kinesis_stream.payments.arn,
          aws_kinesis_stream.ratings.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.rides_state.arn,
          "${aws_dynamodb_table.rides_state.arn}/index/*",
          aws_dynamodb_table.driver_availability.arn,
          "${aws_dynamodb_table.driver_availability.arn}/index/*",
          aws_dynamodb_table.aggregated_metrics.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.streaming_archive.arn}/*",
          "${aws_s3_bucket.analytics_output.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.kinesis.arn,
          aws_kms_key.dynamodb.arn,
          aws_kms_key.s3.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-*"
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
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.ride_dlq.arn,
          aws_sqs_queue.location_dlq.arn,
          aws_sqs_queue.payment_dlq.arn,
          aws_sqs_queue.rating_dlq.arn
        ]
      }
    ]
  })
}

# Kinesis Analytics Role
resource "aws_iam_role" "analytics" {
  name = "${var.project_name}-analytics-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "kinesisanalytics.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-analytics-role"
  }
}

resource "aws_iam_role_policy" "analytics" {
  name = "${var.project_name}-analytics-policy"
  role = aws_iam_role.analytics.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator",
          "kinesis:GetRecords",
          "kinesis:ListShards"
        ]
        Resource = [
          aws_kinesis_stream.rides.arn,
          aws_kinesis_stream.locations.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.kinesis_analytics_output.arn,
          "${aws_s3_bucket.kinesis_analytics_output.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.kinesis.arn,
          aws_kms_key.s3.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/kinesis-analytics/${var.project_name}-*"
      }
    ]
  })
}

# Step Functions Role
resource "aws_iam_role" "step_functions" {
  name = "${var.project_name}-step-functions-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-step-functions-role"
  }
}

resource "aws_iam_role_policy" "step_functions" {
  name = "${var.project_name}-step-functions-policy"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}

# ============================================================================
# SQS DEAD LETTER QUEUES
# ============================================================================

resource "aws_sqs_queue" "ride_dlq" {
  name                      = "${var.project_name}-ride-dlq-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144  # 256 KB
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 0

  tags = {
    Name = "${var.project_name}-ride-dlq"
  }
}

resource "aws_sqs_queue" "location_dlq" {
  name                      = "${var.project_name}-location-dlq-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 0

  tags = {
    Name = "${var.project_name}-location-dlq"
  }
}

resource "aws_sqs_queue" "payment_dlq" {
  name                      = "${var.project_name}-payment-dlq-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 0

  tags = {
    Name = "${var.project_name}-payment-dlq"
  }
}

resource "aws_sqs_queue" "rating_dlq" {
  name                      = "${var.project_name}-rating-dlq-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 0

  tags = {
    Name = "${var.project_name}-rating-dlq"
  }
}

# ============================================================================
# LAMBDA FUNCTIONS (Placeholder - actual code deployment separate)
# ============================================================================

resource "aws_cloudwatch_log_group" "ride_processor" {
  name              = "/aws/lambda/${var.project_name}-ride-processor-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-ride-processor-logs"
  }
}

resource "aws_lambda_function" "ride_processor" {
  function_name = "${var.project_name}-ride-processor-${var.environment}"
  role          = aws_iam_role.lambda_kinesis.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb

  # Placeholder code - replace with actual deployment
  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      RIDES_TABLE          = aws_dynamodb_table.rides_state.name
      METRICS_TABLE        = aws_dynamodb_table.aggregated_metrics.name
      ARCHIVE_BUCKET       = aws_s3_bucket.streaming_archive.id
      POWERTOOLS_SERVICE_NAME = "ride-processor"
    }
  }

  tracing_config {
    mode = "Active"
  }

  reserved_concurrent_executions = 100

  tags = {
    Name = "${var.project_name}-ride-processor"
  }

  depends_on = [aws_cloudwatch_log_group.ride_processor]
}

resource "aws_lambda_event_source_mapping" "ride_processor" {
  event_source_arn                   = aws_kinesis_stream.rides.arn
  function_name                      = aws_lambda_function.ride_processor.arn
  starting_position                  = "LATEST"
  batch_size                         = var.lambda_batch_size
  maximum_batching_window_in_seconds = 10
  parallelization_factor             = 10
  maximum_retry_attempts             = 3
  maximum_record_age_in_seconds      = 3600
  bisect_batch_on_function_error     = true

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.ride_dlq.arn
    }
  }
}

resource "aws_cloudwatch_log_group" "location_processor" {
  name              = "/aws/lambda/${var.project_name}-location-processor-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-location-processor-logs"
  }
}

resource "aws_lambda_function" "location_processor" {
  function_name = "${var.project_name}-location-processor-${var.environment}"
  role          = aws_iam_role.lambda_kinesis.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DRIVERS_TABLE       = aws_dynamodb_table.driver_availability.name
      ARCHIVE_BUCKET      = aws_s3_bucket.streaming_archive.id
      POWERTOOLS_SERVICE_NAME = "location-processor"
    }
  }

  tracing_config {
    mode = "Active"
  }

  reserved_concurrent_executions = 100

  tags = {
    Name = "${var.project_name}-location-processor"
  }

  depends_on = [aws_cloudwatch_log_group.location_processor]
}

resource "aws_lambda_event_source_mapping" "location_processor" {
  event_source_arn                   = aws_kinesis_stream.locations.arn
  function_name                      = aws_lambda_function.location_processor.arn
  starting_position                  = "LATEST"
  batch_size                         = var.lambda_batch_size
  maximum_batching_window_in_seconds = 5
  parallelization_factor             = 10
  maximum_retry_attempts             = 3
  maximum_record_age_in_seconds      = 1800
  bisect_batch_on_function_error     = true

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.location_dlq.arn
    }
  }
}

resource "aws_cloudwatch_log_group" "payment_processor" {
  name              = "/aws/lambda/${var.project_name}-payment-processor-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-payment-processor-logs"
  }
}

resource "aws_lambda_function" "payment_processor" {
  function_name = "${var.project_name}-payment-processor-${var.environment}"
  role          = aws_iam_role.lambda_kinesis.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      RIDES_TABLE         = aws_dynamodb_table.rides_state.name
      ARCHIVE_BUCKET      = aws_s3_bucket.streaming_archive.id
      POWERTOOLS_SERVICE_NAME = "payment-processor"
    }
  }

  tracing_config {
    mode = "Active"
  }

  reserved_concurrent_executions = 50

  tags = {
    Name = "${var.project_name}-payment-processor"
  }

  depends_on = [aws_cloudwatch_log_group.payment_processor]
}

resource "aws_lambda_event_source_mapping" "payment_processor" {
  event_source_arn                   = aws_kinesis_stream.payments.arn
  function_name                      = aws_lambda_function.payment_processor.arn
  starting_position                  = "LATEST"
  batch_size                         = var.lambda_batch_size
  maximum_batching_window_in_seconds = 10
  parallelization_factor             = 5
  maximum_retry_attempts             = 3
  maximum_record_age_in_seconds      = 3600
  bisect_batch_on_function_error     = true

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.payment_dlq.arn
    }
  }
}

resource "aws_cloudwatch_log_group" "rating_processor" {
  name              = "/aws/lambda/${var.project_name}-rating-processor-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-rating-processor-logs"
  }
}

resource "aws_lambda_function" "rating_processor" {
  function_name = "${var.project_name}-rating-processor-${var.environment}"
  role          = aws_iam_role.lambda_kinesis.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DRIVERS_TABLE       = aws_dynamodb_table.driver_availability.name
      POWERTOOLS_SERVICE_NAME = "rating-processor"
    }
  }

  tracing_config {
    mode = "Active"
  }

  reserved_concurrent_executions = 20

  tags = {
    Name = "${var.project_name}-rating-processor"
  }

  depends_on = [aws_cloudwatch_log_group.rating_processor]
}

resource "aws_lambda_event_source_mapping" "rating_processor" {
  event_source_arn                   = aws_kinesis_stream.ratings.arn
  function_name                      = aws_lambda_function.rating_processor.arn
  starting_position                  = "LATEST"
  batch_size                         = 50
  maximum_batching_window_in_seconds = 20
  parallelization_factor             = 5
  maximum_retry_attempts             = 2
  maximum_record_age_in_seconds      = 7200
  bisect_batch_on_function_error     = true

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.rating_dlq.arn
    }
  }
}

# Note: Placeholder Lambda deployment package creation
# In production, replace with actual Lambda code deployment via CI/CD
resource "null_resource" "lambda_placeholder" {
  provisioner "local-exec" {
    command = "echo 'def handler(event, context): pass' > index.py && zip lambda_placeholder.zip index.py"
  }

  triggers = {
    always_run = timestamp()
  }
}

# ============================================================================
# DYNAMODB TABLES
# ============================================================================

resource "aws_dynamodb_table" "rides_state" {
  name         = "${var.project_name}-rides-state-${var.environment}"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "ride_id"

  attribute {
    name = "ride_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "status-timestamp-index"
    hash_key        = "status"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl_timestamp"
    enabled        = true
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-rides-state"
  }
}

resource "aws_dynamodb_table" "driver_availability" {
  name         = "${var.project_name}-driver-availability-${var.environment}"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "driver_id"

  attribute {
    name = "driver_id"
    type = "S"
  }

  attribute {
    name = "geohash"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "location-index"
    hash_key        = "geohash"
    range_key       = "status"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-driver-availability"
  }
}

resource "aws_dynamodb_table" "aggregated_metrics" {
  name         = "${var.project_name}-aggregated-metrics-${var.environment}"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "metric_name"
  range_key    = "timestamp"

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

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-aggregated-metrics"
  }
}

# ============================================================================
# S3 BUCKETS
# ============================================================================

resource "aws_s3_bucket" "streaming_archive" {
  bucket = "${var.project_name}-streaming-archive-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-streaming-archive"
  }
}

resource "aws_s3_bucket_versioning" "streaming_archive" {
  bucket = aws_s3_bucket.streaming_archive.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "streaming_archive" {
  bucket = aws_s3_bucket.streaming_archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "streaming_archive" {
  bucket = aws_s3_bucket.streaming_archive.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

resource "aws_s3_bucket" "analytics_output" {
  bucket = "${var.project_name}-analytics-output-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-analytics-output"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "analytics_output" {
  bucket = aws_s3_bucket.analytics_output.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}

resource "aws_s3_bucket" "kinesis_analytics_output" {
  bucket = "${var.project_name}-kinesis-analytics-output-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-kinesis-analytics-output"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "kinesis_analytics_output" {
  bucket = aws_s3_bucket.kinesis_analytics_output.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}

# ============================================================================
# SNS TOPICS AND SUBSCRIPTIONS
# ============================================================================

resource "aws_sns_topic" "alerts" {
  name              = "${var.project_name}-alerts-${var.environment}"
  kms_master_key_id = aws_kms_key.s3.id

  tags = {
    Name = "${var.project_name}-alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================================================
# CLOUDWATCH ALARMS
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "lambda_errors_ride" {
  alarm_name          = "${var.project_name}-ride-processor-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alerts when ride processor Lambda errors exceed threshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.ride_processor.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "kinesis_iterator_age_rides" {
  alarm_name          = "${var.project_name}-rides-iterator-age-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = 300
  statistic           = "Maximum"
  threshold           = 60000  # 60 seconds
  alarm_description   = "Alerts when Kinesis iterator age exceeds 60 seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    StreamName = aws_kinesis_stream.rides.name
  }
}

resource "aws_cloudwatch_metric_alarm" "dlq_messages_ride" {
  alarm_name          = "${var.project_name}-ride-dlq-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alerts when ride DLQ has messages"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = aws_sqs_queue.ride_dlq.name
  }
}

# ============================================================================
# CLOUDWATCH DASHBOARD
# ============================================================================

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", { "stat" = "Sum", "period" = 300 }],
            [".", "IncomingBytes"],
            [".", "OutgoingRecords"],
            [".", "GetRecords.IteratorAgeMilliseconds", { "stat" = "Max" }]
          ]
          view    = "timeSeries"
          region  = data.aws_region.current.name
          title   = "Kinesis Streams Metrics"
          period  = 300
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { "stat" = "Sum" }],
            [".", "Errors"],
            [".", "Duration", { "stat" = "Average" }],
            [".", "ConcurrentExecutions", { "stat" = "Max" }]
          ]
          view    = "timeSeries"
          region  = data.aws_region.current.name
          title   = "Lambda Functions Metrics"
          period  = 300
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/DynamoDB", "UserErrors", { "stat" = "Sum" }],
            [".", "SystemErrors"],
            [".", "ConsumedReadCapacityUnits"],
            [".", "ConsumedWriteCapacityUnits"]
          ]
          view    = "timeSeries"
          region  = data.aws_region.current.name
          title   = "DynamoDB Metrics"
          period  = 300
        }
      }
    ]
  })
}
