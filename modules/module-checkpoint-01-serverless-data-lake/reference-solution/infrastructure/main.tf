# ==================================================================================
# CloudMart Serverless Data Lake Infrastructure
# ==================================================================================
# This Terraform configuration creates a complete serverless data lake architecture
# for CloudMart e-commerce company using AWS services with a medallion pattern.
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
        Project    = var.project_name
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

resource "aws_s3_bucket_lifecycle_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "archive-old-raw-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }

  rule {
    id     = "delete-incomplete-multipart-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
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

resource "aws_s3_bucket_lifecycle_configuration" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    id     = "optimize-processed-storage"
    status = "Enabled"

    transition {
      days          = 180
      storage_class = "STANDARD_IA"
    }
  }
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

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "delete-old-logs"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

# Athena Results Bucket
resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.s3_bucket_prefix}-cloudmart-athena-results-${var.environment}"

  tags = {
    Name = "CloudMart Athena Query Results"
    Type = "Analytics"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "cleanup-query-results"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

# ==================================================================================
# IAM Roles and Policies - Lambda Ingestion
# ==================================================================================

resource "aws_iam_role" "lambda_ingestion" {
  name = "${var.project_name}-lambda-ingestion-role-${var.environment}"

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
    Name = "Lambda Ingestion Role"
  }
}

resource "aws_iam_role_policy" "lambda_ingestion_s3" {
  name = "s3-access"
  role = aws_iam_role.lambda_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_ingestion_cloudwatch" {
  name = "cloudwatch-logs"
  role = aws_iam_role.lambda_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_ingestion_sns" {
  name = "sns-publish"
  role = aws_iam_role.lambda_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.pipeline_alerts.arn
      }
    ]
  })
}

# ==================================================================================
# IAM Roles and Policies - Glue ETL
# ==================================================================================

resource "aws_iam_role" "glue_etl" {
  name = "${var.project_name}-glue-etl-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Glue ETL Role"
  }
}

resource "aws_iam_role_policy" "glue_etl_s3" {
  name = "s3-access"
  role = aws_iam_role.glue_etl.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*",
          aws_s3_bucket.curated_data.arn,
          "${aws_s3_bucket.curated_data.arn}/*",
          aws_s3_bucket.logs.arn,
          "${aws_s3_bucket.logs.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service_policy" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_etl_cloudwatch" {
  name = "cloudwatch-logs"
  role = aws_iam_role.glue_etl.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ==================================================================================
# IAM Roles and Policies - Athena Query
# ==================================================================================

resource "aws_iam_role" "athena_query" {
  name = "${var.project_name}-athena-query-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "athena.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Athena Query Role"
  }
}

resource "aws_iam_role_policy" "athena_query_s3" {
  name = "s3-access"
  role = aws_iam_role.athena_query.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.curated_data.arn,
          "${aws_s3_bucket.curated_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      }
    ]
  })
}

# ==================================================================================
# Lambda Functions - Data Ingestion
# ==================================================================================

# Lambda Function: Orders Ingestion
resource "aws_lambda_function" "ingest_orders" {
  filename      = "${path.module}/lambda_placeholder.zip"
  function_name = "${var.project_name}-ingest-orders-${var.environment}"
  role          = aws_iam_role.lambda_ingestion.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = var.lambda_memory_mb

  environment {
    variables = {
      TARGET_BUCKET = aws_s3_bucket.raw_data.id
      TARGET_PREFIX = "orders/"
      SNS_TOPIC_ARN = aws_sns_topic.pipeline_alerts.arn
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name     = "Orders Ingestion Lambda"
    DataType = "Orders"
  }
}

resource "aws_cloudwatch_log_group" "ingest_orders" {
  name              = "/aws/lambda/${aws_lambda_function.ingest_orders.function_name}"
  retention_in_days = 7

  tags = {
    Name = "Orders Ingestion Logs"
  }
}

# Lambda Function: Customers Ingestion
resource "aws_lambda_function" "ingest_customers" {
  filename      = "${path.module}/lambda_placeholder.zip"
  function_name = "${var.project_name}-ingest-customers-${var.environment}"
  role          = aws_iam_role.lambda_ingestion.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = var.lambda_memory_mb

  environment {
    variables = {
      TARGET_BUCKET = aws_s3_bucket.raw_data.id
      TARGET_PREFIX = "customers/"
      SNS_TOPIC_ARN = aws_sns_topic.pipeline_alerts.arn
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name     = "Customers Ingestion Lambda"
    DataType = "Customers"
  }
}

resource "aws_cloudwatch_log_group" "ingest_customers" {
  name              = "/aws/lambda/${aws_lambda_function.ingest_customers.function_name}"
  retention_in_days = 7

  tags = {
    Name = "Customers Ingestion Logs"
  }
}

# Lambda Function: Products Ingestion
resource "aws_lambda_function" "ingest_products" {
  filename      = "${path.module}/lambda_placeholder.zip"
  function_name = "${var.project_name}-ingest-products-${var.environment}"
  role          = aws_iam_role.lambda_ingestion.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = var.lambda_memory_mb

  environment {
    variables = {
      TARGET_BUCKET = aws_s3_bucket.raw_data.id
      TARGET_PREFIX = "products/"
      SNS_TOPIC_ARN = aws_sns_topic.pipeline_alerts.arn
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name     = "Products Ingestion Lambda"
    DataType = "Products"
  }
}

resource "aws_cloudwatch_log_group" "ingest_products" {
  name              = "/aws/lambda/${aws_lambda_function.ingest_products.function_name}"
  retention_in_days = 7

  tags = {
    Name = "Products Ingestion Logs"
  }
}

# Lambda Function: Events Ingestion
resource "aws_lambda_function" "ingest_events" {
  filename      = "${path.module}/lambda_placeholder.zip"
  function_name = "${var.project_name}-ingest-events-${var.environment}"
  role          = aws_iam_role.lambda_ingestion.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = var.lambda_memory_mb

  environment {
    variables = {
      TARGET_BUCKET = aws_s3_bucket.raw_data.id
      TARGET_PREFIX = "events/"
      SNS_TOPIC_ARN = aws_sns_topic.pipeline_alerts.arn
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name     = "Events Ingestion Lambda"
    DataType = "Events"
  }
}

resource "aws_cloudwatch_log_group" "ingest_events" {
  name              = "/aws/lambda/${aws_lambda_function.ingest_events.function_name}"
  retention_in_days = 7

  tags = {
    Name = "Events Ingestion Logs"
  }
}

# Create a placeholder Lambda deployment package
resource "null_resource" "lambda_placeholder" {
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p ${path.module}/lambda_temp
      echo 'def handler(event, context): return {"statusCode": 200, "body": "Placeholder"}' > ${path.module}/lambda_temp/index.py
      cd ${path.module}/lambda_temp && zip -r ../lambda_placeholder.zip index.py
      rm -rf ${path.module}/lambda_temp
    EOT
  }

  triggers = {
    always_run = timestamp()
  }
}

# ==================================================================================
# AWS Glue - Data Catalog Database
# ==================================================================================

resource "aws_glue_catalog_database" "cloudmart" {
  name        = "cloudmart_data_lake_${var.environment}"
  description = "CloudMart Data Lake catalog for ${var.environment} environment"

  tags = {
    Name = "CloudMart Data Lake Database"
  }
}

# ==================================================================================
# AWS Glue - Crawlers
# ==================================================================================

# Crawler for Bronze Zone (Raw Data)
resource "aws_glue_crawler" "raw_data" {
  name          = "${var.project_name}-raw-crawler-${var.environment}"
  role          = aws_iam_role.glue_etl.arn
  database_name = aws_glue_catalog_database.cloudmart.name

  s3_target {
    path = "s3://${aws_s3_bucket.raw_data.id}/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name  = "Raw Data Crawler"
    Layer = "Bronze"
  }
}

# Crawler for Silver Zone (Processed Data)
resource "aws_glue_crawler" "processed_data" {
  name          = "${var.project_name}-processed-crawler-${var.environment}"
  role          = aws_iam_role.glue_etl.arn
  database_name = aws_glue_catalog_database.cloudmart.name

  s3_target {
    path = "s3://${aws_s3_bucket.processed_data.id}/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name  = "Processed Data Crawler"
    Layer = "Silver"
  }
}

# Crawler for Gold Zone (Curated Data)
resource "aws_glue_crawler" "curated_data" {
  name          = "${var.project_name}-curated-crawler-${var.environment}"
  role          = aws_iam_role.glue_etl.arn
  database_name = aws_glue_catalog_database.cloudmart.name

  s3_target {
    path = "s3://${aws_s3_bucket.curated_data.id}/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name  = "Curated Data Crawler"
    Layer = "Gold"
  }
}

# ==================================================================================
# AWS Glue - ETL Jobs
# ==================================================================================

# Job 1: Bronze to Silver - Orders Processing
resource "aws_glue_job" "bronze_to_silver_orders" {
  name     = "${var.project_name}-bronze-to-silver-orders-${var.environment}"
  role_arn = aws_iam_role.glue_etl.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/bronze_to_silver_orders.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.id}/glue-spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.logs.id}/glue-temp/"
    "--SOURCE_DATABASE"                  = aws_glue_catalog_database.cloudmart.name
    "--SOURCE_BUCKET"                    = aws_s3_bucket.raw_data.id
    "--TARGET_BUCKET"                    = aws_s3_bucket.processed_data.id
  }

  max_capacity = var.glue_max_dpu

  timeout = 60

  tags = {
    Name     = "Bronze to Silver - Orders"
    Pipeline = "ETL"
    Layer    = "Silver"
  }
}

# Job 2: Bronze to Silver - Customers Processing
resource "aws_glue_job" "bronze_to_silver_customers" {
  name     = "${var.project_name}-bronze-to-silver-customers-${var.environment}"
  role_arn = aws_iam_role.glue_etl.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/bronze_to_silver_customers.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.id}/glue-spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.logs.id}/glue-temp/"
    "--SOURCE_DATABASE"                  = aws_glue_catalog_database.cloudmart.name
    "--SOURCE_BUCKET"                    = aws_s3_bucket.raw_data.id
    "--TARGET_BUCKET"                    = aws_s3_bucket.processed_data.id
  }

  max_capacity = var.glue_max_dpu

  timeout = 60

  tags = {
    Name     = "Bronze to Silver - Customers"
    Pipeline = "ETL"
    Layer    = "Silver"
  }
}

# Job 3: Bronze to Silver - Products Processing
resource "aws_glue_job" "bronze_to_silver_products" {
  name     = "${var.project_name}-bronze-to-silver-products-${var.environment}"
  role_arn = aws_iam_role.glue_etl.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/bronze_to_silver_products.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.id}/glue-spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.logs.id}/glue-temp/"
    "--SOURCE_DATABASE"                  = aws_glue_catalog_database.cloudmart.name
    "--SOURCE_BUCKET"                    = aws_s3_bucket.raw_data.id
    "--TARGET_BUCKET"                    = aws_s3_bucket.processed_data.id
  }

  max_capacity = var.glue_max_dpu

  timeout = 60

  tags = {
    Name     = "Bronze to Silver - Products"
    Pipeline = "ETL"
    Layer    = "Silver"
  }
}

# Job 4: Silver to Gold - Sales Analytics
resource "aws_glue_job" "silver_to_gold_sales_analytics" {
  name     = "${var.project_name}-silver-to-gold-sales-${var.environment}"
  role_arn = aws_iam_role.glue_etl.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/silver_to_gold_sales.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.id}/glue-spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.logs.id}/glue-temp/"
    "--SOURCE_DATABASE"                  = aws_glue_catalog_database.cloudmart.name
    "--SOURCE_BUCKET"                    = aws_s3_bucket.processed_data.id
    "--TARGET_BUCKET"                    = aws_s3_bucket.curated_data.id
  }

  max_capacity = var.glue_max_dpu

  timeout = 90

  tags = {
    Name     = "Silver to Gold - Sales Analytics"
    Pipeline = "ETL"
    Layer    = "Gold"
  }
}

# Job 5: Silver to Gold - Customer Analytics
resource "aws_glue_job" "silver_to_gold_customer_analytics" {
  name     = "${var.project_name}-silver-to-gold-customers-${var.environment}"
  role_arn = aws_iam_role.glue_etl.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/silver_to_gold_customers.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.id}/glue-spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.logs.id}/glue-temp/"
    "--SOURCE_DATABASE"                  = aws_glue_catalog_database.cloudmart.name
    "--SOURCE_BUCKET"                    = aws_s3_bucket.processed_data.id
    "--TARGET_BUCKET"                    = aws_s3_bucket.curated_data.id
  }

  max_capacity = var.glue_max_dpu

  timeout = 90

  tags = {
    Name     = "Silver to Gold - Customer Analytics"
    Pipeline = "ETL"
    Layer    = "Gold"
  }
}

# ==================================================================================
# Amazon Athena - Workgroup
# ==================================================================================

resource "aws_athena_workgroup" "cloudmart_analytics" {
  name        = "${var.project_name}-analytics-${var.environment}"
  description = "Workgroup for CloudMart analytics queries"

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
      selected_engine_version = "AUTO"
    }
  }

  tags = {
    Name = "CloudMart Analytics Workgroup"
  }
}

# ==================================================================================
# Amazon SNS - Notifications
# ==================================================================================

resource "aws_sns_topic" "pipeline_alerts" {
  name              = "${var.project_name}-pipeline-alerts-${var.environment}"
  display_name      = "CloudMart Data Pipeline Alerts"
  kms_master_key_id = "alias/aws/sns"

  tags = {
    Name = "Pipeline Alerts Topic"
  }
}

resource "aws_sns_topic_subscription" "pipeline_alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.pipeline_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ==================================================================================
# CloudWatch - Alarms
# ==================================================================================

# Lambda Error Alarm - Orders Ingestion
resource "aws_cloudwatch_metric_alarm" "lambda_orders_errors" {
  alarm_name          = "${var.project_name}-lambda-orders-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert when orders ingestion Lambda has more than 5 errors in 5 minutes"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.ingest_orders.function_name
  }

  tags = {
    Name = "Lambda Orders Errors Alarm"
  }
}

# Lambda Error Alarm - Customers Ingestion
resource "aws_cloudwatch_metric_alarm" "lambda_customers_errors" {
  alarm_name          = "${var.project_name}-lambda-customers-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert when customers ingestion Lambda has more than 5 errors in 5 minutes"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.ingest_customers.function_name
  }

  tags = {
    Name = "Lambda Customers Errors Alarm"
  }
}

# Glue Job Failure Alarm - Orders Processing
resource "aws_cloudwatch_metric_alarm" "glue_orders_failures" {
  alarm_name          = "${var.project_name}-glue-orders-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when orders processing Glue job has failed tasks"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    JobName = aws_glue_job.bronze_to_silver_orders.name
  }

  tags = {
    Name = "Glue Orders Job Failures Alarm"
  }
}

# Glue Job Failure Alarm - Sales Analytics
resource "aws_cloudwatch_metric_alarm" "glue_sales_failures" {
  alarm_name          = "${var.project_name}-glue-sales-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when sales analytics Glue job has failed tasks"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    JobName = aws_glue_job.silver_to_gold_sales_analytics.name
  }

  tags = {
    Name = "Glue Sales Job Failures Alarm"
  }
}

# ==================================================================================
# EventBridge - Scheduled Crawlers
# ==================================================================================

# Schedule for Raw Data Crawler (every 6 hours)
resource "aws_cloudwatch_event_rule" "raw_crawler_schedule" {
  name                = "${var.project_name}-raw-crawler-schedule-${var.environment}"
  description         = "Trigger raw data crawler every 6 hours"
  schedule_expression = "rate(6 hours)"

  tags = {
    Name = "Raw Crawler Schedule"
  }
}

resource "aws_cloudwatch_event_target" "raw_crawler_schedule" {
  rule     = aws_cloudwatch_event_rule.raw_crawler_schedule.name
  arn      = "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:crawler/${aws_glue_crawler.raw_data.name}"
  role_arn = aws_iam_role.eventbridge_glue.arn
}

# Schedule for Processed Data Crawler (daily at 2 AM)
resource "aws_cloudwatch_event_rule" "processed_crawler_schedule" {
  name                = "${var.project_name}-processed-crawler-schedule-${var.environment}"
  description         = "Trigger processed data crawler daily at 2 AM"
  schedule_expression = "cron(0 2 * * ? *)"

  tags = {
    Name = "Processed Crawler Schedule"
  }
}

resource "aws_cloudwatch_event_target" "processed_crawler_schedule" {
  rule     = aws_cloudwatch_event_rule.processed_crawler_schedule.name
  arn      = "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:crawler/${aws_glue_crawler.processed_data.name}"
  role_arn = aws_iam_role.eventbridge_glue.arn
}

# Schedule for Curated Data Crawler (daily at 3 AM)
resource "aws_cloudwatch_event_rule" "curated_crawler_schedule" {
  name                = "${var.project_name}-curated-crawler-schedule-${var.environment}"
  description         = "Trigger curated data crawler daily at 3 AM"
  schedule_expression = "cron(0 3 * * ? *)"

  tags = {
    Name = "Curated Crawler Schedule"
  }
}

resource "aws_cloudwatch_event_target" "curated_crawler_schedule" {
  rule     = aws_cloudwatch_event_rule.curated_crawler_schedule.name
  arn      = "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:crawler/${aws_glue_crawler.curated_data.name}"
  role_arn = aws_iam_role.eventbridge_glue.arn
}

# IAM Role for EventBridge to trigger Glue Crawlers
resource "aws_iam_role" "eventbridge_glue" {
  name = "${var.project_name}-eventbridge-glue-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "EventBridge Glue Role"
  }
}

resource "aws_iam_role_policy" "eventbridge_glue" {
  name = "glue-crawler-access"
  role = aws_iam_role.eventbridge_glue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartCrawler"
        ]
        Resource = [
          aws_glue_crawler.raw_data.arn,
          aws_glue_crawler.processed_data.arn,
          aws_glue_crawler.curated_data.arn
        ]
      }
    ]
  })
}
