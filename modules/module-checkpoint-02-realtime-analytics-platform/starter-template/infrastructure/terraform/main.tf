# Real-Time Analytics Platform - Terraform Main Configuration
# TODO: Complete this file by implementing all required infrastructure resources

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

# TODO: Configure the AWS provider
# - Set the region using var.aws_region
# - Add default tags for all resources (environment, project, managed_by)
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # TODO: Uncomment and configure backend for state management
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "ride-analytics/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  # TODO: Add default tags
  # default_tags {
  #   tags = {
  #     Environment = var.environment
  #     Project     = var.project_name
  #     ManagedBy   = "Terraform"
  #   }
  # }
}

# =============================================================================
# KINESIS DATA STREAM
# =============================================================================

# TODO: Create Kinesis Data Stream for ride events
# Requirements:
# - Stream name should use var.project_name and var.environment
# - Configure shard count using var.kinesis_shard_count
# - Set retention period to 24 hours
# - Enable encryption using AWS managed CMK
# - Set stream mode to PROVISIONED (or ON_DEMAND for auto-scaling)

# resource "aws_kinesis_stream" "ride_events" {
#   name             = "${var.project_name}-${var.environment}-ride-events-stream"
#   shard_count      = var.kinesis_shard_count
#   retention_period = 24
#
#   shard_level_metrics = [
#     "IncomingBytes",
#     "IncomingRecords",
#     "OutgoingBytes",
#     "OutgoingRecords",
#   ]
#
#   encryption_type = "KMS"
#   kms_key_id      = "alias/aws/kinesis"
#
#   tags = {
#     Name = "${var.project_name}-ride-events-stream"
#   }
# }

# =============================================================================
# DYNAMODB TABLES
# =============================================================================

# TODO: Create DynamoDB table for ride data
# Requirements:
# - Table name: ${var.project_name}-${var.environment}-rides
# - Partition key: ride_id (String)
# - Sort key: timestamp (Number)
# - Billing mode: Use var.dynamodb_billing_mode (PAY_PER_REQUEST or PROVISIONED)
# - Enable point-in-time recovery
# - Enable encryption at rest
# - Add Global Secondary Index on 'status' attribute
# - Configure TTL attribute: expires_at

# resource "aws_dynamodb_table" "rides" {
#   name           = "${var.project_name}-${var.environment}-rides"
#   billing_mode   = var.dynamodb_billing_mode
#   hash_key       = "ride_id"
#   range_key      = "timestamp"
#
#   # TODO: If using PROVISIONED mode, set read_capacity and write_capacity
#   # read_capacity  = 5
#   # write_capacity = 5
#
#   attribute {
#     name = "ride_id"
#     type = "S"
#   }
#
#   attribute {
#     name = "timestamp"
#     type = "N"
#   }
#
#   attribute {
#     name = "status"
#     type = "S"
#   }
#
#   # TODO: Add Global Secondary Index for querying by status
#   # global_secondary_index {
#   #   name            = "status-index"
#   #   hash_key        = "status"
#   #   range_key       = "timestamp"
#   #   projection_type = "ALL"
#   # }
#
#   ttl {
#     attribute_name = "expires_at"
#     enabled        = true
#   }
#
#   point_in_time_recovery {
#     enabled = true
#   }
#
#   server_side_encryption {
#     enabled = true
#   }
#
#   tags = {
#     Name = "${var.project_name}-rides-table"
#   }
# }

# TODO: Create DynamoDB table for metrics
# Requirements:
# - Table name: ${var.project_name}-${var.environment}-metrics
# - Partition key: metric_name (String)
# - Sort key: timestamp (Number)
# - Billing mode: Use var.dynamodb_billing_mode
# - Enable point-in-time recovery
# - Enable encryption at rest
# - Configure TTL: Keep metrics for 30 days

# resource "aws_dynamodb_table" "metrics" {
#   name           = "${var.project_name}-${var.environment}-metrics"
#   billing_mode   = var.dynamodb_billing_mode
#   hash_key       = "metric_name"
#   range_key      = "timestamp"
#
#   attribute {
#     name = "metric_name"
#     type = "S"
#   }
#
#   attribute {
#     name = "timestamp"
#     type = "N"
#   }
#
#   ttl {
#     attribute_name = "expires_at"
#     enabled        = true
#   }
#
#   point_in_time_recovery {
#     enabled = true
#   }
#
#   server_side_encryption {
#     enabled = true
#   }
#
#   tags = {
#     Name = "${var.project_name}-metrics-table"
#   }
# }

# =============================================================================
# S3 BUCKETS
# =============================================================================

# TODO: Create S3 bucket for raw events
# Requirements:
# - Bucket name follow AWS naming requirements (globally unique, lowercase)
# - Enable versioning
# - Enable server-side encryption (AES256 or aws:kms)
# - Block all public access
# - Configure lifecycle policy to transition to IA after 30 days

# resource "aws_s3_bucket" "raw_events" {
#   bucket = "${var.project_name}-${var.environment}-raw-events-${data.aws_caller_identity.current.account_id}"
#
#   tags = {
#     Name    = "Raw Events Bucket"
#     Purpose = "Store raw ride events from Kinesis"
#   }
# }
#
# resource "aws_s3_bucket_versioning" "raw_events" {
#   bucket = aws_s3_bucket.raw_events.id
#
#   versioning_configuration {
#     status = "Enabled"
#   }
# }
#
# resource "aws_s3_bucket_server_side_encryption_configuration" "raw_events" {
#   bucket = aws_s3_bucket.raw_events.id
#
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }
#
# resource "aws_s3_bucket_public_access_block" "raw_events" {
#   bucket = aws_s3_bucket.raw_events.id
#
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }
#
# resource "aws_s3_bucket_lifecycle_configuration" "raw_events" {
#   bucket = aws_s3_bucket.raw_events.id
#
#   rule {
#     id     = "transition-to-ia"
#     status = "Enabled"
#
#     transition {
#       days          = 30
#       storage_class = "STANDARD_IA"
#     }
#
#     transition {
#       days          = 90
#       storage_class = "GLACIER"
#     }
#   }
# }

# TODO: Create S3 bucket for processed events
# Same requirements as raw events bucket
# resource "aws_s3_bucket" "processed_events" {
#   bucket = "${var.project_name}-${var.environment}-processed-events-${data.aws_caller_identity.current.account_id}"
#
#   tags = {
#     Name    = "Processed Events Bucket"
#     Purpose = "Store processed ride events for analytics"
#   }
# }
# TODO: Add versioning, encryption, public access block, and lifecycle configuration

# TODO: Create S3 bucket for Athena query results
# resource "aws_s3_bucket" "athena_results" {
#   bucket = "${var.project_name}-${var.environment}-athena-results-${data.aws_caller_identity.current.account_id}"
#
#   tags = {
#     Name    = "Athena Query Results"
#     Purpose = "Store Athena query results"
#   }
# }
# TODO: Add encryption and lifecycle policy (delete after 7 days)

# =============================================================================
# AWS GLUE CATALOG
# =============================================================================

# TODO: Create Glue database for ride analytics
# resource "aws_glue_catalog_database" "ride_analytics" {
#   name        = "${var.project_name}_${var.environment}_ride_analytics_db"
#   description = "Database containing ride analytics tables"
# }

# TODO: Create IAM role for Glue Crawler
# resource "aws_iam_role" "glue_crawler" {
#   name = "${var.project_name}-${var.environment}-glue-crawler-role"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "glue.amazonaws.com"
#         }
#       }
#     ]
#   })
# }
#
# resource "aws_iam_role_policy_attachment" "glue_service" {
#   role       = aws_iam_role.glue_crawler.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
# }
#
# TODO: Add policy for S3 access to processed events bucket

# TODO: Create Glue Crawler
# resource "aws_glue_crawler" "ride_events" {
#   name          = "${var.project_name}-${var.environment}-ride-events-crawler"
#   role          = aws_iam_role.glue_crawler.arn
#   database_name = aws_glue_catalog_database.ride_analytics.name
#
#   s3_target {
#     path = "s3://${aws_s3_bucket.processed_events.bucket}/"
#   }
#
#   schedule = "cron(0 * * * ? *)"  # Run hourly
#
#   schema_change_policy {
#     delete_behavior = "LOG"
#     update_behavior = "UPDATE_IN_DATABASE"
#   }
#
#   configuration = jsonencode({
#     Version = 1.0
#     CrawlerOutput = {
#       Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
#     }
#   })
# }

# =============================================================================
# LAMBDA FUNCTION
# =============================================================================

# TODO: Create IAM role for Lambda function
# resource "aws_iam_role" "rides_processor_lambda" {
#   name = "${var.project_name}-${var.environment}-rides-processor-role"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "lambda.amazonaws.com"
#         }
#       }
#     ]
#   })
# }

# TODO: Create IAM policy for Lambda permissions
# Requirements:
# - Kinesis: GetRecords, GetShardIterator, DescribeStream, ListStreams
# - DynamoDB: PutItem, GetItem, UpdateItem, Query on both tables
# - S3: PutObject, GetObject on buckets
# - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents
# - CloudWatch Metrics: PutMetricData

# resource "aws_iam_policy" "rides_processor_lambda" {
#   name        = "${var.project_name}-${var.environment}-rides-processor-policy"
#   description = "Policy for rides processor Lambda function"
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "kinesis:GetRecords",
#           "kinesis:GetShardIterator",
#           "kinesis:DescribeStream",
#           "kinesis:ListStreams",
#           "kinesis:ListShards"
#         ]
#         Resource = [aws_kinesis_stream.ride_events.arn]
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "dynamodb:PutItem",
#           "dynamodb:GetItem",
#           "dynamodb:UpdateItem",
#           "dynamodb:Query"
#         ]
#         Resource = [
#           aws_dynamodb_table.rides.arn,
#           aws_dynamodb_table.metrics.arn,
#           "${aws_dynamodb_table.rides.arn}/index/*"
#         ]
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "s3:PutObject",
#           "s3:GetObject"
#         ]
#         Resource = [
#           "${aws_s3_bucket.raw_events.arn}/*",
#           "${aws_s3_bucket.processed_events.arn}/*"
#         ]
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "logs:CreateLogGroup",
#           "logs:CreateLogStream",
#           "logs:PutLogEvents"
#         ]
#         Resource = ["arn:aws:logs:*:*:*"]
#       },
#       {
#         Effect = "Allow"
#         Action = ["cloudwatch:PutMetricData"]
#         Resource = ["*"]
#       }
#     ]
#   })
# }
#
# resource "aws_iam_role_policy_attachment" "rides_processor_lambda" {
#   role       = aws_iam_role.rides_processor_lambda.name
#   policy_arn = aws_iam_policy.rides_processor_lambda.arn
# }

# TODO: Create Lambda function
# NOTE: You need to package your Lambda code first
# Run: cd ../../pipelines/lambda && zip -r lambda_package.zip rides_processor/ common/

# resource "aws_lambda_function" "rides_processor" {
#   filename         = "../../pipelines/lambda/lambda_package.zip"
#   function_name    = "${var.project_name}-${var.environment}-rides-processor"
#   role            = aws_iam_role.rides_processor_lambda.arn
#   handler         = "handler.lambda_handler"
#   source_code_hash = filebase64sha256("../../pipelines/lambda/lambda_package.zip")
#   runtime         = "python3.9"
#   timeout         = 60
#   memory_size     = 512
#
#   environment {
#     variables = {
#       RIDES_TABLE_NAME        = aws_dynamodb_table.rides.name
#       METRICS_TABLE_NAME      = aws_dynamodb_table.metrics.name
#       RAW_EVENTS_BUCKET       = aws_s3_bucket.raw_events.bucket
#       PROCESSED_EVENTS_BUCKET = aws_s3_bucket.processed_events.bucket
#       LOG_LEVEL               = "INFO"
#       ENVIRONMENT             = var.environment
#     }
#   }
#
#   tags = {
#     Name = "${var.project_name}-rides-processor"
#   }
# }

# TODO: Create CloudWatch Log Group for Lambda
# resource "aws_cloudwatch_log_group" "rides_processor" {
#   name              = "/aws/lambda/${aws_lambda_function.rides_processor.function_name}"
#   retention_in_days = var.environment == "prod" ? 30 : 7
# }

# TODO: Create Lambda event source mapping for Kinesis
# resource "aws_lambda_event_source_mapping" "kinesis_to_lambda" {
#   event_source_arn  = aws_kinesis_stream.ride_events.arn
#   function_name     = aws_lambda_function.rides_processor.arn
#   starting_position = "LATEST"
#   batch_size        = 100
#   maximum_batching_window_in_seconds = 5
#
#   # Enable bisect on function error to isolate bad records
#   bisect_batch_on_function_error = true
#   maximum_retry_attempts         = 3
#   maximum_record_age_in_seconds  = 86400  # 24 hours
#
#   # TODO: Optional - Configure destination for failed records
#   # destination_config {
#   #   on_failure {
#   #     destination_arn = aws_sqs_queue.lambda_dlq.arn
#   #   }
#   # }
# }

# =============================================================================
# CLOUDWATCH ALARMS
# =============================================================================

# TODO: Create SNS topic for CloudWatch alarms
# resource "aws_sns_topic" "alerts" {
#   name = "${var.project_name}-${var.environment}-alerts"
# }
#
# resource "aws_sns_topic_subscription" "alerts_email" {
#   topic_arn = aws_sns_topic.alerts.arn
#   protocol  = "email"
#   endpoint  = var.alert_email  # TODO: Add this variable
# }

# TODO: Alarm 1 - High Lambda Error Rate
# resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
#   alarm_name          = "${var.project_name}-${var.environment}-lambda-high-errors"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = "2"
#   metric_name         = "Errors"
#   namespace           = "AWS/Lambda"
#   period              = "300"
#   statistic           = "Sum"
#   threshold           = var.environment == "prod" ? "10" : "5"
#   alarm_description   = "Lambda function error rate is too high"
#   alarm_actions       = [aws_sns_topic.alerts.arn]
#
#   dimensions = {
#     FunctionName = aws_lambda_function.rides_processor.function_name
#   }
# }

# TODO: Alarm 2 - DynamoDB Throttling
# TODO: Alarm 3 - High Kinesis Iterator Age
# TODO: Alarm 4 - Low Completion Rate (custom metric)

# =============================================================================
# DATA SOURCES
# =============================================================================

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}
