# ==================================================================================
# CloudMart Serverless Data Lake Infrastructure - STARTER TEMPLATE
# ==================================================================================
# Complete the TODO sections to create a serverless data lake architecture
# ==================================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.tags,
      {
        Project     = var.project_name
        Environment = var.environment
        ManagedBy   = "Terraform"
      }
    )
  }
}

# ==================================================================================
# Data Sources
# ==================================================================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# ==================================================================================
# S3 Buckets - Medallion Architecture (Bronze, Silver, Gold)
# ==================================================================================

# Bronze Layer - Raw Data Bucket
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.s3_bucket_prefix}-cloudmart-raw-${var.environment}"

  tags = {
    Name        = "CloudMart Raw Data (Bronze Zone)"
    Layer       = "Bronze"
    DataQuality = "Raw"
  }
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# TODO: Complete lifecycle configuration for raw_data bucket
# HINT: Add lifecycle rules to:
# 1. Transition to STANDARD_IA after 90 days
# 2. Transition to GLACIER after 180 days
# 3. Expire objects after 365 days
# 4. Delete incomplete multipart uploads after 7 days
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration
resource "aws_s3_bucket_lifecycle_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  # TODO: Add rule for archiving old raw data
  # rule {
  #   id     = "archive-old-raw-data"
  #   status = "Enabled"
  #
  #   transition {
  #     days          = ?
  #     storage_class = "?"
  #   }
  #   ...
  # }

  # TODO: Add rule for cleaning up incomplete multipart uploads
}

# Silver Layer - Processed Data Bucket
resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.s3_bucket_prefix}-cloudmart-processed-${var.environment}"

  tags = {
    Name        = "CloudMart Processed Data (Silver Zone)"
    Layer       = "Silver"
    DataQuality = "Cleaned"
  }
}

resource "aws_s3_bucket_versioning" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Gold Layer - Curated Data Bucket
resource "aws_s3_bucket" "curated_data" {
  bucket = "${var.s3_bucket_prefix}-cloudmart-curated-${var.environment}"

  tags = {
    Name        = "CloudMart Curated Data (Gold Zone)"
    Layer       = "Gold"
    DataQuality = "Business-Ready"
  }
}

resource "aws_s3_bucket_versioning" "curated_data" {
  bucket = aws_s3_bucket.curated_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "curated_data" {
  bucket = aws_s3_bucket.curated_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "curated_data" {
  bucket = aws_s3_bucket.curated_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Logs Bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.s3_bucket_prefix}-cloudmart-logs-${var.environment}"

  tags = {
    Name = "CloudMart Logs"
    Type = "Logs"
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Athena Results Bucket
resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.s3_bucket_prefix}-cloudmart-athena-results-${var.environment}"

  tags = {
    Name = "CloudMart Athena Query Results"
    Type = "QueryResults"
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ==================================================================================
# IAM Roles and Policies
# ==================================================================================

# TODO: Create IAM role for Lambda ingestion functions
# HINT: Lambda needs:
# - Trust policy allowing lambda.amazonaws.com to assume role
# - Permissions to read/write S3 buckets
# - Permissions to publish to SNS topics
# - Permissions to write CloudWatch logs and metrics
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role

resource "aws_iam_role" "lambda_ingestion" {
  name = "${var.project_name}-lambda-ingestion-${var.environment}"

  # TODO: Complete the assume_role_policy
  # HINT: Allow lambda.amazonaws.com service to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"  # TODO: Verify this is correct
        }
      }
    ]
  })

  tags = {
    Name = "Lambda Ingestion Role"
  }
}

# TODO: Create IAM policy for Lambda S3 access
resource "aws_iam_policy" "lambda_s3_access" {
  name        = "${var.project_name}-lambda-s3-access-${var.environment}"
  description = "Allows Lambda functions to access S3 buckets"

  # TODO: Complete the policy document
  # HINT: Need permissions for:
  # - s3:GetObject on raw_data bucket
  # - s3:PutObject on processed_data bucket
  # - s3:ListBucket on both buckets
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          # TODO: Add more S3 actions needed
        ]
        Resource = [
          "${aws_s3_bucket.raw_data.arn}/*",
          # TODO: Add more S3 resources
        ]
      },
      # TODO: Add ListBucket permission
    ]
  })
}

# TODO: Attach the policy to the Lambda role
resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.lambda_ingestion.name
  policy_arn = aws_iam_policy.lambda_s3_access.arn
}

# TODO: Attach AWS managed policy for Lambda basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_ingestion.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# TODO: Create IAM role for Glue ETL jobs
# HINT: Similar pattern to Lambda role, but trust policy uses glue.amazonaws.com
resource "aws_iam_role" "glue_etl" {
  name = "${var.project_name}-glue-etl-${var.environment}"

  # TODO: Complete assume role policy for Glue
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"  # TODO: Verify
        }
      }
    ]
  })

  tags = {
    Name = "Glue ETL Role"
  }
}

# TODO: Attach AWS managed Glue service role policy
# HINT: Use arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole
resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# TODO: Create custom policy for Glue to access all S3 buckets
resource "aws_iam_policy" "glue_s3_access" {
  name        = "${var.project_name}-glue-s3-access-${var.environment}"
  description = "Allows Glue jobs to access data lake S3 buckets"

  # TODO: Grant Glue read/write access to all three layers (bronze, silver, gold)
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # TODO: Add permissions
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_s3_access" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = aws_iam_policy.glue_s3_access.arn
}

# ==================================================================================
# SNS Topics for Notifications
# ==================================================================================

resource "aws_sns_topic" "data_pipeline_alerts" {
  name = "${var.project_name}-pipeline-alerts-${var.environment}"

  tags = {
    Name = "Data Pipeline Alerts"
  }
}

# TODO: Create SNS topic subscription for email notifications
# HINT: Use aws_sns_topic_subscription resource
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription
# resource "aws_sns_topic_subscription" "pipeline_alerts_email" {
#   topic_arn = aws_sns_topic.data_pipeline_alerts.arn
#   protocol  = "email"
#   endpoint  = var.alert_email  # TODO: Add this variable
# }

# ==================================================================================
# Lambda Functions
# ==================================================================================

# TODO: Create Lambda function for orders ingestion
# HINT: You need to:
# 1. Create a ZIP file with your handler code
# 2. Upload it to S3 or use terraform's archive_file data source
# 3. Configure runtime (python3.11), handler (handler.lambda_handler), timeout, memory
# 4. Set environment variables: PROCESSED_BUCKET, SNS_TOPIC_ARN
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function

# Data source for lambda deployment package
# TODO: Uncomment and configure
# data "archive_file" "orders_ingestion_lambda" {
#   type        = "zip"
#   source_dir  = "${path.module}/../pipelines/lambda/orders_ingestion"
#   output_path = "${path.module}/lambda_packages/orders_ingestion.zip"
# }

# resource "aws_lambda_function" "orders_ingestion" {
#   function_name = "${var.project_name}-orders-ingestion-${var.environment}"
#   role          = aws_iam_role.lambda_ingestion.arn
#
#   # TODO: Configure the deployment package
#   filename      = data.archive_file.orders_ingestion_lambda.output_path
#
#   # TODO: Set runtime and handler
#   runtime = "python3.11"
#   handler = "handler.lambda_handler"
#
#   # TODO: Configure timeout and memory
#   timeout     = 300
#   memory_size = 512
#
#   # TODO: Set environment variables
#   environment {
#     variables = {
#       PROCESSED_BUCKET = aws_s3_bucket.processed_data.id
#       SNS_TOPIC_ARN    = aws_sns_topic.data_pipeline_alerts.arn
#       # Add more as needed
#     }
#   }
#
#   tags = {
#     Name = "Orders Ingestion Lambda"
#   }
# }

# TODO: Create S3 bucket notification to trigger Lambda
# HINT: Use aws_s3_bucket_notification resource to trigger Lambda when files arrive
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_notification

# TODO: Create similar Lambda functions for:
# - customers_ingestion
# - products_ingestion
# - events_ingestion

# ==================================================================================
# AWS Glue Resources
# ==================================================================================

# Glue Catalog Database - Bronze Layer
resource "aws_glue_catalog_database" "bronze" {
  name = "${var.project_name}_bronze_${var.environment}"

  description = "Bronze layer - raw ingested data"

  tags = {
    Layer = "Bronze"
  }
}

# Glue Catalog Database - Silver Layer
resource "aws_glue_catalog_database" "silver" {
  name = "${var.project_name}_silver_${var.environment}"

  description = "Silver layer - cleaned and validated data"

  tags = {
    Layer = "Silver"
  }
}

# Glue Catalog Database - Gold Layer
resource "aws_glue_catalog_database" "gold" {
  name = "${var.project_name}_gold_${var.environment}"

  description = "Gold layer - business-ready aggregated data"

  tags = {
    Layer = "Gold"
  }
}

# TODO: Create Glue Crawler for Bronze layer orders
# HINT: Crawler needs:
# - database_name: bronze database
# - role: Glue ETL role ARN
# - s3_target: path to orders data in raw_data bucket
# - schedule: cron expression (e.g., "cron(0 */6 * * ? *)" for every 6 hours)
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/glue_crawler

# resource "aws_glue_crawler" "bronze_orders" {
#   name          = "${var.project_name}-bronze-orders-${var.environment}"
#   role          = aws_iam_role.glue_etl.arn
#   database_name = aws_glue_catalog_database.bronze.name
#
#   # TODO: Configure S3 target
#   s3_target {
#     path = "s3://${aws_s3_bucket.raw_data.id}/orders/"
#   }
#
#   # TODO: Set schedule (optional, can run on-demand)
#   # schedule = "cron(0 */6 * * ? *)"
#
#   tags = {
#     Name  = "Bronze Orders Crawler"
#     Layer = "Bronze"
#   }
# }

# TODO: Create Glue crawlers for:
# - bronze_customers
# - bronze_products
# - bronze_events
# - silver_orders
# - silver_customers
# - silver_products
# - gold_sales_summary
# - gold_customer_360

# TODO: Create Glue ETL Job for bronze_to_silver_orders transformation
# HINT: Glue job needs:
# - role: Glue ETL role ARN
# - command: type "glueetl", script_location in S3
# - default_arguments: job parameters, script arguments
# - glue_version: "4.0"
# - worker_type: "G.1X" or "G.2X"
# - number_of_workers: 2-10
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/glue_job

# First, upload scripts to S3
# resource "aws_s3_object" "glue_script_bronze_to_silver_orders" {
#   bucket = aws_s3_bucket.logs.id
#   key    = "glue-scripts/bronze_to_silver_orders.py"
#   source = "${path.module}/../pipelines/glue/bronze_to_silver_orders.py"
#   etag   = filemd5("${path.module}/../pipelines/glue/bronze_to_silver_orders.py")
# }

# resource "aws_glue_job" "bronze_to_silver_orders" {
#   name     = "${var.project_name}-bronze-to-silver-orders-${var.environment}"
#   role_arn = aws_iam_role.glue_etl.arn
#
#   # TODO: Configure command
#   command {
#     name            = "glueetl"
#     script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/bronze_to_silver_orders.py"
#     python_version  = "3"
#   }
#
#   # TODO: Configure default arguments
#   default_arguments = {
#     "--job-language"        = "python"
#     "--job-bookmark-option" = "job-bookmark-enable"
#     "--source_database"     = aws_glue_catalog_database.bronze.name
#     "--source_table"        = "orders"
#     "--target_s3_path"      = "s3://${aws_s3_bucket.processed_data.id}/orders/"
#     "--target_database"     = aws_glue_catalog_database.silver.name
#     "--target_table"        = "orders"
#   }
#
#   # TODO: Configure Glue version and workers
#   glue_version       = "4.0"
#   worker_type        = "G.1X"
#   number_of_workers  = 2
#   timeout            = 60
#
#   tags = {
#     Name = "Bronze to Silver - Orders"
#   }
# }

# TODO: Create Glue jobs for:
# - bronze_to_silver_customers
# - bronze_to_silver_products
# - silver_to_gold_sales_summary
# - silver_to_gold_customer_360

# ==================================================================================
# Amazon Athena Configuration
# ==================================================================================

resource "aws_athena_workgroup" "primary" {
  name = "${var.project_name}-primary-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/query-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }

  tags = {
    Name = "Primary Athena Workgroup"
  }
}

# ==================================================================================
# CloudWatch Alarms
# ==================================================================================

# TODO: Create CloudWatch alarm for Lambda errors
# HINT: Monitor Lambda function errors and send notification to SNS
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm

# resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
#   alarm_name          = "${var.project_name}-lambda-errors-${var.environment}"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = "1"
#   metric_name         = "Errors"
#   namespace           = "AWS/Lambda"
#   period              = "300"
#   statistic           = "Sum"
#   threshold           = "5"
#   alarm_description   = "Alert when Lambda functions have more than 5 errors in 5 minutes"
#
#   # TODO: Configure dimensions to monitor specific Lambda functions
#   dimensions = {
#     FunctionName = aws_lambda_function.orders_ingestion.function_name
#   }
#
#   # TODO: Link to SNS topic for notifications
#   alarm_actions = [aws_sns_topic.data_pipeline_alerts.arn]
#
#   tags = {
#     Name = "Lambda Errors Alarm"
#   }
# }

# TODO: Create CloudWatch alarms for:
# - Glue job failures
# - S3 bucket size monitoring
# - Data freshness monitoring
