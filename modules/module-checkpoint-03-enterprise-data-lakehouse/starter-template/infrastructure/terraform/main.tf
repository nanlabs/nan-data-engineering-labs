# ==========================================
# Enterprise Data Lakehouse - Main Terraform Configuration
# ==========================================
# This file contains the core infrastructure for the enterprise data lakehouse.
# Complete the TODOs to provision S3 buckets, Glue resources, IAM roles, and monitoring.
# ==========================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # TODO: Configure remote backend for state management
  # Uncomment and configure after creating S3 bucket and DynamoDB table for state locking
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "lakehouse/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
    }
  }
}

# ==========================================
# Local Variables
# ==========================================

locals {
  # TODO: Define local variables for resource naming
  # Example: bucket_prefix = "${var.project_name}-${var.environment}"

  bucket_prefix = "${var.project_name}-${var.environment}"

  # Common tags to be applied to all resources
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ==========================================
# S3 Buckets for Data Lakehouse Layers
# ==========================================

# TODO: Create S3 bucket for RAW data layer
# - This bucket stores raw data as ingested from source systems
# - Enable versioning for data protection
# - Configure lifecycle policies for cost optimization
# - Apply encryption at rest

# resource "aws_s3_bucket" "raw_data" {
#   bucket = "${local.bucket_prefix}-raw-data"
#   # Add configuration here
# }

# resource "aws_s3_bucket_versioning" "raw_data_versioning" {
#   bucket = aws_s3_bucket.raw_data.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# TODO: Create S3 bucket for BRONZE layer
# - Stores validated and cataloged raw data
# - Add partitioning strategy in folder structure
# - Enable server-side encryption

# resource "aws_s3_bucket" "bronze_layer" {
#   bucket = "${local.bucket_prefix}-bronze-layer"
#   # Add configuration here
# }

# TODO: Create S3 bucket for SILVER layer
# - Stores cleansed, conformed, and enriched data
# - Implement retention policies
# - Enable encryption with KMS (optional)

# resource "aws_s3_bucket" "silver_layer" {
#   bucket = "${local.bucket_prefix}-silver-layer"
#   # Add configuration here
# }

# TODO: Create S3 bucket for GOLD layer
# - Stores business-level aggregates and analytics-ready data
# - Optimize for query performance
# - Configure cross-region replication for DR (optional)

# resource "aws_s3_bucket" "gold_layer" {
#   bucket = "${local.bucket_prefix}-gold-layer"
#   # Add configuration here
# }

# TODO: Create S3 bucket for scripts and artifacts
# - Stores Glue job scripts, Lambda functions, and configuration files

# resource "aws_s3_bucket" "scripts" {
#   bucket = "${local.bucket_prefix}-scripts"
#   # Add configuration here
# }

# TODO: Create S3 bucket for temporary and staging data

# resource "aws_s3_bucket" "temp" {
#   bucket = "${local.bucket_prefix}-temp"
#   # Add configuration here
# }

# TODO: Configure S3 bucket encryption for all buckets
# Use aws_s3_bucket_server_side_encryption_configuration resource

# Example:
# resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data_encryption" {
#   bucket = aws_s3_bucket.raw_data.id
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#       # Or use KMS: sse_algorithm = "aws:kms"
#       # kms_master_key_id = aws_kms_key.lakehouse.arn
#     }
#   }
# }

# TODO: Configure S3 bucket public access block for all buckets
# resource "aws_s3_bucket_public_access_block" "raw_data_public_access" {
#   bucket = aws_s3_bucket.raw_data.id
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }

# TODO: Configure S3 lifecycle policies
# Example: Move old data to cheaper storage classes or delete after retention period
# resource "aws_s3_bucket_lifecycle_configuration" "raw_data_lifecycle" {
#   bucket = aws_s3_bucket.raw_data.id
#   rule {
#     id     = "archive-old-data"
#     status = "Enabled"
#     transition {
#       days          = 90
#       storage_class = "INTELLIGENT_TIERING"
#     }
#   }
# }

# ==========================================
# AWS Glue Data Catalog
# ==========================================

# TODO: Create Glue Catalog Database for RAW layer
# resource "aws_glue_catalog_database" "raw" {
#   name        = "${var.project_name}_raw"
#   description = "Raw data layer - data as ingested from sources"
#   location_uri = "s3://${aws_s3_bucket.raw_data.id}/"
# }

# TODO: Create Glue Catalog Database for BRONZE layer
# resource "aws_glue_catalog_database" "bronze" {
#   name        = "${var.project_name}_bronze"
#   description = "Bronze layer - validated and cataloged data"
#   location_uri = "s3://${aws_s3_bucket.bronze_layer.id}/"
# }

# TODO: Create Glue Catalog Database for SILVER layer
# resource "aws_glue_catalog_database" "silver" {
#   name        = "${var.project_name}_silver"
#   description = "Silver layer - cleansed and conformed data"
#   location_uri = "s3://${aws_s3_bucket.silver_layer.id}/"
# }

# TODO: Create Glue Catalog Database for GOLD layer
# resource "aws_glue_catalog_database" "gold" {
#   name        = "${var.project_name}_gold"
#   description = "Gold layer - business-level aggregates ready for analytics"
#   location_uri = "s3://${aws_s3_bucket.gold_layer.id}/"
# }

# ==========================================
# IAM Roles and Policies
# ==========================================

# TODO: Create IAM role for AWS Glue jobs
# - Attach AWS managed policy: AWSGlueServiceRole
# - Add custom policy for S3 bucket access
# - Add policy for CloudWatch Logs

# resource "aws_iam_role" "glue_service_role" {
#   name               = "${var.project_name}-glue-service-role"
#   assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
# }

# data "aws_iam_policy_document" "glue_assume_role" {
#   statement {
#     actions = ["sts:AssumeRole"]
#     principals {
#       type        = "Service"
#       identifiers = ["glue.amazonaws.com"]
#     }
#   }
# }

# TODO: Attach AWS managed Glue service policy
# resource "aws_iam_role_policy_attachment" "glue_service" {
#   role       = aws_iam_role.glue_service_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
# }

# TODO: Create custom policy for S3 access
# resource "aws_iam_policy" "glue_s3_access" {
#   name        = "${var.project_name}-glue-s3-access"
#   description = "Allow Glue jobs to access lakehouse S3 buckets"
#   policy      = data.aws_iam_policy_document.glue_s3_access.json
# }

# data "aws_iam_policy_document" "glue_s3_access" {
#   statement {
#     actions = [
#       "s3:GetObject",
#       "s3:PutObject",
#       "s3:DeleteObject",
#       "s3:ListBucket"
#     ]
#     resources = [
#       # Add ARNs for all lakehouse buckets
#       # aws_s3_bucket.raw_data.arn,
#       # "${aws_s3_bucket.raw_data.arn}/*",
#       # ... add others
#     ]
#   }
# }

# TODO: Attach custom S3 policy to Glue role
# resource "aws_iam_role_policy_attachment" "glue_s3_access" {
#   role       = aws_iam_role.glue_service_role.name
#   policy_arn = aws_iam_policy.glue_s3_access.arn
# }

# TODO: Create IAM role for Lambda functions (for streaming processing)
# resource "aws_iam_role" "lambda_execution_role" {
#   name               = "${var.project_name}-lambda-execution-role"
#   assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
# }

# TODO: Create IAM role for Step Functions
# resource "aws_iam_role" "step_functions_role" {
#   name               = "${var.project_name}-step-functions-role"
#   assume_role_policy = data.aws_iam_policy_document.step_functions_assume_role.json
# }

# TODO: Create IAM role for Athena query execution
# resource "aws_iam_role" "athena_execution_role" {
#   name               = "${var.project_name}-athena-execution-role"
#   assume_role_policy = data.aws_iam_policy_document.athena_assume_role.json
# }

# ==========================================
# AWS Glue Jobs
# ==========================================

# TODO: Create Glue job for raw-to-bronze pipeline
# - Upload script to S3 first
# - Configure job properties (Glue version, DPUs, timeout)
# - Set job parameters

# resource "aws_glue_job" "raw_to_bronze" {
#   name     = "${var.project_name}-raw-to-bronze"
#   role_arn = aws_iam_role.glue_service_role.arn
#
#   command {
#     name            = "glueetl"
#     script_location = "s3://${aws_s3_bucket.scripts.id}/glue-jobs/raw_to_bronze.py"
#     python_version  = "3"
#   }
#
#   glue_version = "4.0"
#   max_capacity = 2.0  # TODO: Adjust based on workload
#   timeout      = 60   # TODO: Adjust timeout in minutes
#
#   default_arguments = {
#     "--job-language"        = "python"
#     "--enable-job-insights" = "true"
#     "--enable-metrics"      = "true"
#     # TODO: Add job-specific parameters
#   }
# }

# TODO: Create Glue job for bronze-to-silver pipeline
# resource "aws_glue_job" "bronze_to_silver" {
#   name     = "${var.project_name}-bronze-to-silver"
#   role_arn = aws_iam_role.glue_service_role.arn
#   # Add configuration similar to raw_to_bronze
# }

# TODO: Create Glue job for silver-to-gold pipeline
# resource "aws_glue_job" "silver_to_gold" {
#   name     = "${var.project_name}-silver-to-gold"
#   role_arn = aws_iam_role.glue_service_role.arn
#   # Add configuration similar to raw_to_bronze
# }

# ==========================================
# AWS Lake Formation
# ==========================================

# TODO: Register S3 locations with Lake Formation
# This enables Lake Formation to manage permissions for the data lake

# resource "aws_lakeformation_resource" "raw_data" {
#   arn = aws_s3_bucket.raw_data.arn
# }

# TODO: Configure Lake Formation database permissions
# Example: Grant data engineers full access to bronze/silver databases

# resource "aws_lakeformation_permissions" "data_engineer_bronze" {
#   principal   = aws_iam_role.data_engineer_role.arn
#   permissions = ["ALL"]
#
#   database {
#     name = aws_glue_catalog_database.bronze.name
#   }
# }

# ==========================================
# Amazon Kinesis (for Streaming)
# ==========================================

# TODO: Create Kinesis Data Stream for real-time ingestion
# resource "aws_kinesis_stream" "transactions" {
#   name             = "${var.project_name}-transactions-stream"
#   shard_count      = 1  # TODO: Adjust based on throughput requirements
#   retention_period = 24  # Hours
#
#   shard_level_metrics = [
#     "IncomingBytes",
#     "IncomingRecords",
#     "OutgoingBytes",
#     "OutgoingRecords",
#   ]
#
#   stream_mode_details {
#     stream_mode = "PROVISIONED"  # Or "ON_DEMAND"
#   }
# }

# TODO: Create Kinesis Firehose delivery stream
# resource "aws_kinesis_firehose_delivery_stream" "transactions_firehose" {
#   name        = "${var.project_name}-transactions-firehose"
#   destination = "extended_s3"
#
#   kinesis_source_configuration {
#     kinesis_stream_arn = aws_kinesis_stream.transactions.arn
#     role_arn          = aws_iam_role.firehose_role.arn
#   }
#
#   extended_s3_configuration {
#     role_arn   = aws_iam_role.firehose_role.arn
#     bucket_arn = aws_s3_bucket.raw_data.arn
#     prefix     = "streaming/transactions/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
#
#     buffering_size     = 5   # MB
#     buffering_interval = 60  # Seconds
#   }
# }

# ==========================================
# Amazon Athena
# ==========================================

# TODO: Create Athena workgroup
# resource "aws_athena_workgroup" "analytics" {
#   name        = "${var.project_name}-analytics"
#   description = "Workgroup for analytics queries on gold layer"
#
#   configuration {
#     enforce_workgroup_configuration    = true
#     publish_cloudwatch_metrics_enabled = true
#
#     result_configuration {
#       output_location = "s3://${aws_s3_bucket.temp.id}/athena-results/"
#
#       encryption_configuration {
#         encryption_option = "SSE_S3"
#       }
#     }
#   }
# }

# ==========================================
# CloudWatch Log Groups
# ==========================================

# TODO: Create CloudWatch log group for Glue jobs
# resource "aws_cloudwatch_log_group" "glue_jobs" {
#   name              = "/aws/glue/${var.project_name}"
#   retention_in_days = 30  # TODO: Adjust retention period
# }

# TODO: Create CloudWatch log group for Lambda functions
# resource "aws_cloudwatch_log_group" "lambda_functions" {
#   name              = "/aws/lambda/${var.project_name}"
#   retention_in_days = 14
# }

# TODO: Create CloudWatch log group for Step Functions
# resource "aws_cloudwatch_log_group" "step_functions" {
#   name              = "/aws/states/${var.project_name}"
#   retention_in_days = 30
# }

# ==========================================
# CloudWatch Alarms
# ==========================================

# TODO: Create CloudWatch alarm for Glue job failures
# resource "aws_cloudwatch_metric_alarm" "glue_job_failure" {
#   alarm_name          = "${var.project_name}-glue-job-failure"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = "1"
#   metric_name         = "glue.driver.aggregate.numFailedTasks"
#   namespace           = "Glue"
#   period              = "300"
#   statistic           = "Sum"
#   threshold           = "0"
#   alarm_description   = "Alert when Glue job fails"
#   alarm_actions       = [aws_sns_topic.alerts.arn]
# }

# ==========================================
# SNS Topics for Notifications
# ==========================================

# TODO: Create SNS topic for pipeline alerts
# resource "aws_sns_topic" "alerts" {
#   name = "${var.project_name}-pipeline-alerts"
# }

# TODO: Subscribe email to SNS topic
# resource "aws_sns_topic_subscription" "email_alerts" {
#   topic_arn = aws_sns_topic.alerts.arn
#   protocol  = "email"
#   endpoint  = var.alert_email  # TODO: Define variable
# }

# ==========================================
# CloudTrail for Audit Logging
# ==========================================

# TODO: Create S3 bucket for CloudTrail logs
# resource "aws_s3_bucket" "cloudtrail" {
#   bucket = "${local.bucket_prefix}-cloudtrail"
# }

# TODO: Create CloudTrail
# resource "aws_cloudtrail" "lakehouse_audit" {
#   name                          = "${var.project_name}-audit-trail"
#   s3_bucket_name                = aws_s3_bucket.cloudtrail.id
#   include_global_service_events = true
#   is_multi_region_trail         = true
#   enable_log_file_validation    = true
#
#   event_selector {
#     read_write_type           = "All"
#     include_management_events = true
#   }
# }

# ==========================================
# Step Functions State Machine
# ==========================================

# TODO: Create Step Functions state machine for pipeline orchestration
# resource "aws_sfn_state_machine" "lakehouse_pipeline" {
#   name     = "${var.project_name}-pipeline"
#   role_arn = aws_iam_role.step_functions_role.arn
#
#   definition = jsonencode({
#     Comment = "Enterprise Lakehouse ETL Pipeline"
#     StartAt = "RawToBronze"
#     States = {
#       RawToBronze = {
#         Type     = "Task"
#         Resource = "arn:aws:states:::glue:startJobRun.sync"
#         Parameters = {
#           JobName = aws_glue_job.raw_to_bronze.name
#         }
#         Next = "BronzeToSilver"
#       }
#       # TODO: Add more states
#     }
#   })
# }

# ==========================================
# Outputs
# ==========================================

# TODO: Define outputs to display important resource information
# output "raw_data_bucket" {
#   description = "S3 bucket for raw data"
#   value       = aws_s3_bucket.raw_data.id
# }

# TODO: Output Glue database names
# TODO: Output IAM role ARNs
# TODO: Output Athena workgroup name

# ==========================================
# NOTES:
# ==========================================
# 1. Remove all TODO comments as you implement each resource
# 2. Test infrastructure incrementally - don't deploy everything at once
# 3. Use terraform plan before terraform apply
# 4. Tag all resources appropriately for cost tracking
# 5. Enable encryption for all data at rest
# 6. Follow least privilege principle for IAM roles
# 7. Consider using modules for reusable components
# 8. Document any deviations from the standard architecture
# ==========================================
