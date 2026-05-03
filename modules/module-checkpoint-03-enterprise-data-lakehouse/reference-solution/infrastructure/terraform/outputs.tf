# ============================================================================
# Terraform Outputs - Enterprise Data Lakehouse
# ============================================================================
# Purpose: Export resource information for external use and documentation
# ============================================================================

# ============================================================================
# VPC Outputs
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.lakehouse.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.lakehouse.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "data_subnet_ids" {
  description = "List of data subnet IDs"
  value       = aws_subnet.data[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# ============================================================================
# VPC Endpoint Outputs
# ============================================================================

output "s3_endpoint_id" {
  description = "ID of the S3 VPC endpoint"
  value       = aws_vpc_endpoint.s3.id
}

output "glue_endpoint_id" {
  description = "ID of the Glue VPC endpoint"
  value       = aws_vpc_endpoint.glue.id
}

output "sts_endpoint_id" {
  description = "ID of the STS VPC endpoint"
  value       = aws_vpc_endpoint.sts.id
}

# ============================================================================
# S3 Bucket Outputs
# ============================================================================

output "raw_bucket_name" {
  description = "Name of the raw data bucket"
  value       = aws_s3_bucket.raw.bucket
}

output "raw_bucket_arn" {
  description = "ARN of the raw data bucket"
  value       = aws_s3_bucket.raw.arn
}

output "bronze_bucket_name" {
  description = "Name of the bronze data bucket"
  value       = aws_s3_bucket.bronze.bucket
}

output "bronze_bucket_arn" {
  description = "ARN of the bronze data bucket"
  value       = aws_s3_bucket.bronze.arn
}

output "silver_bucket_name" {
  description = "Name of the silver data bucket"
  value       = aws_s3_bucket.silver.bucket
}

output "silver_bucket_arn" {
  description = "ARN of the silver data bucket"
  value       = aws_s3_bucket.silver.arn
}

output "gold_bucket_name" {
  description = "Name of the gold data bucket"
  value       = aws_s3_bucket.gold.bucket
}

output "gold_bucket_arn" {
  description = "ARN of the gold data bucket"
  value       = aws_s3_bucket.gold.arn
}

output "logs_bucket_name" {
  description = "Name of the logs bucket"
  value       = aws_s3_bucket.logs.bucket
}

output "logs_bucket_arn" {
  description = "ARN of the logs bucket"
  value       = aws_s3_bucket.logs.arn
}

output "scripts_bucket_name" {
  description = "Name of the scripts bucket"
  value       = aws_s3_bucket.scripts.bucket
}

output "scripts_bucket_arn" {
  description = "ARN of the scripts bucket"
  value       = aws_s3_bucket.scripts.arn
}

# ============================================================================
# KMS Key Outputs
# ============================================================================

output "data_kms_key_id" {
  description = "ID of the data encryption KMS key"
  value       = aws_kms_key.data.key_id
}

output "data_kms_key_arn" {
  description = "ARN of the data encryption KMS key"
  value       = aws_kms_key.data.arn
}

output "catalog_kms_key_id" {
  description = "ID of the catalog encryption KMS key"
  value       = aws_kms_key.catalog.key_id
}

output "catalog_kms_key_arn" {
  description = "ARN of the catalog encryption KMS key"
  value       = aws_kms_key.catalog.arn
}

output "logs_kms_key_id" {
  description = "ID of the logs encryption KMS key"
  value       = aws_kms_key.logs.key_id
}

output "logs_kms_key_arn" {
  description = "ARN of the logs encryption KMS key"
  value       = aws_kms_key.logs.arn
}

# ============================================================================
# Glue Catalog Outputs
# ============================================================================

output "raw_database_name" {
  description = "Name of the raw Glue database"
  value       = aws_glue_catalog_database.raw.name
}

output "bronze_database_name" {
  description = "Name of the bronze Glue database"
  value       = aws_glue_catalog_database.bronze.name
}

output "silver_database_name" {
  description = "Name of the silver Glue database"
  value       = aws_glue_catalog_database.silver.name
}

output "gold_database_name" {
  description = "Name of the gold Glue database"
  value       = aws_glue_catalog_database.gold.name
}

# ============================================================================
# Glue Crawler Outputs
# ============================================================================

output "raw_crawler_name" {
  description = "Name of the raw layer crawler"
  value       = aws_glue_crawler.raw.name
}

output "bronze_crawler_name" {
  description = "Name of the bronze layer crawler"
  value       = aws_glue_crawler.bronze.name
}

output "silver_crawler_name" {
  description = "Name of the silver layer crawler"
  value       = aws_glue_crawler.silver.name
}

output "gold_crawler_name" {
  description = "Name of the gold layer crawler"
  value       = aws_glue_crawler.gold.name
}

# ============================================================================
# Glue Job Outputs
# ============================================================================

output "raw_to_bronze_job_name" {
  description = "Name of the raw to bronze ETL job"
  value       = aws_glue_job.raw_to_bronze.name
}

output "bronze_to_silver_job_name" {
  description = "Name of the bronze to silver ETL job"
  value       = aws_glue_job.bronze_to_silver.name
}

output "silver_to_gold_job_name" {
  description = "Name of the silver to gold ETL job"
  value       = aws_glue_job.silver_to_gold.name
}

output "data_quality_job_name" {
  description = "Name of the data quality job"
  value       = aws_glue_job.data_quality.name
}

output "schema_evolution_job_name" {
  description = "Name of the schema evolution job"
  value       = aws_glue_job.schema_evolution.name
}

# ============================================================================
# Glue IAM Role Outputs
# ============================================================================

output "glue_service_role_arn" {
  description = "ARN of the Glue service role"
  value       = aws_iam_role.glue_service.arn
}

output "glue_crawler_role_arn" {
  description = "ARN of the Glue crawler role"
  value       = aws_iam_role.glue_crawler.arn
}

# ============================================================================
# Lake Formation Outputs
# ============================================================================

output "lakeformation_admin_role_arn" {
  description = "ARN of the Lake Formation admin role"
  value       = aws_iam_role.lakeformation_admin.arn
}

output "lakeformation_admin_role_name" {
  description = "Name of the Lake Formation admin role"
  value       = aws_iam_role.lakeformation_admin.name
}

# ============================================================================
# EMR Serverless Outputs
# ============================================================================

output "emr_application_id" {
  description = "ID of the EMR Serverless application"
  value       = aws_emrserverless_application.spark.id
}

output "emr_application_arn" {
  description = "ARN of the EMR Serverless application"
  value       = aws_emrserverless_application.spark.arn
}

output "emr_application_name" {
  description = "Name of the EMR Serverless application"
  value       = aws_emrserverless_application.spark.name
}

output "emr_job_runtime_role_arn" {
  description = "ARN of the EMR job runtime role"
  value       = aws_iam_role.emr_job_runtime.arn
}

output "emr_job_runtime_role_name" {
  description = "Name of the EMR job runtime role"
  value       = aws_iam_role.emr_job_runtime.name
}

output "emr_studio_id" {
  description = "ID of the EMR Studio (if enabled)"
  value       = var.enable_emr_studio ? aws_emr_studio.main[0].id : null
}

# ============================================================================
# Security Group Outputs
# ============================================================================

output "emr_master_security_group_id" {
  description = "ID of the EMR master security group"
  value       = aws_security_group.emr_master.id
}

output "emr_worker_security_group_id" {
  description = "ID of the EMR worker security group"
  value       = aws_security_group.emr_worker.id
}

output "emr_serverless_security_group_id" {
  description = "ID of the EMR Serverless security group"
  value       = aws_security_group.emr_serverless.id
}

output "vpc_endpoints_security_group_id" {
  description = "ID of the VPC endpoints security group"
  value       = aws_security_group.vpc_endpoints.id
}

# ============================================================================
# CloudWatch Outputs
# ============================================================================

output "glue_jobs_log_group_name" {
  description = "Name of the Glue jobs CloudWatch log group"
  value       = aws_cloudwatch_log_group.glue_jobs.name
}

output "glue_crawlers_log_group_name" {
  description = "Name of the Glue crawlers CloudWatch log group"
  value       = aws_cloudwatch_log_group.glue_crawlers.name
}

output "emr_serverless_log_group_name" {
  description = "Name of the EMR Serverless CloudWatch log group"
  value       = aws_cloudwatch_log_group.emr_serverless.name
}

output "lambda_log_group_name" {
  description = "Name of the Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda.name
}

# ============================================================================
# SNS Topic Outputs
# ============================================================================

output "alerts_topic_arn" {
  description = "ARN of the alerts SNS topic"
  value       = aws_sns_topic.alerts.arn
}

output "data_quality_topic_arn" {
  description = "ARN of the data quality SNS topic"
  value       = aws_sns_topic.data_quality.arn
}

# ============================================================================
# Glue Workflow Outputs
# ============================================================================

output "glue_workflow_name" {
  description = "Name of the main Glue workflow"
  value       = aws_glue_workflow.main.name
}

output "glue_workflow_arn" {
  description = "ARN of the main Glue workflow"
  value       = aws_glue_workflow.main.arn
}

# ============================================================================
# Usage Instructions and Quick Start
# ============================================================================

output "quick_start_commands" {
  description = "Quick start commands for using the infrastructure"
  value = {
    upload_data_to_raw = "aws s3 cp <local-file> s3://${aws_s3_bucket.raw.bucket}/data/"

    trigger_raw_to_bronze = "aws glue start-job-run --job-name ${aws_glue_job.raw_to_bronze.name}"

    trigger_bronze_to_silver = "aws glue start-job-run --job-name ${aws_glue_job.bronze_to_silver.name}"

    trigger_silver_to_gold = "aws glue start-job-run --job-name ${aws_glue_job.silver_to_gold.name}"

    run_data_quality = "aws glue start-job-run --job-name ${aws_glue_job.data_quality.name}"

    start_raw_crawler = "aws glue start-crawler --name ${aws_glue_crawler.raw.name}"

    query_catalog = "aws glue get-tables --database-name ${aws_glue_catalog_database.gold.name}"

    submit_emr_job = "aws emr-serverless start-job-run --application-id ${aws_emrserverless_application.spark.id} --execution-role-arn ${aws_iam_role.emr_job_runtime.arn} --job-driver '{\"sparkSubmit\":{\"entryPoint\":\"s3://${aws_s3_bucket.scripts.bucket}/emr-jobs/sample.py\"}}'"
  }
}

output "data_lake_paths" {
  description = "S3 paths for each data lake layer"
  value = {
    raw_layer    = "s3://${aws_s3_bucket.raw.bucket}/"
    bronze_layer = "s3://${aws_s3_bucket.bronze.bucket}/"
    silver_layer = "s3://${aws_s3_bucket.silver.bucket}/"
    gold_layer   = "s3://${aws_s3_bucket.gold.bucket}/"
    scripts      = "s3://${aws_s3_bucket.scripts.bucket}/"
    logs         = "s3://${aws_s3_bucket.logs.bucket}/"
  }
}

output "glue_catalog_info" {
  description = "Glue Data Catalog database information"
  value = {
    raw_database = {
      name     = aws_glue_catalog_database.raw.name
      location = aws_glue_catalog_database.raw.location_uri
    }
    bronze_database = {
      name     = aws_glue_catalog_database.bronze.name
      location = aws_glue_catalog_database.bronze.location_uri
    }
    silver_database = {
      name     = aws_glue_catalog_database.silver.name
      location = aws_glue_catalog_database.silver.location_uri
    }
    gold_database = {
      name     = aws_glue_catalog_database.gold.name
      location = aws_glue_catalog_database.gold.location_uri
    }
  }
}

output "emr_configuration" {
  description = "EMR Serverless configuration details"
  value = {
    application_id = aws_emrserverless_application.spark.id
    runtime_role   = aws_iam_role.emr_job_runtime.arn
    config_file    = "s3://${aws_s3_bucket.scripts.bucket}/config/delta-lake-init.conf"
    release_label  = aws_emrserverless_application.spark.release_label
  }
}

output "monitoring_dashboards" {
  description = "CloudWatch monitoring resources"
  value = {
    glue_jobs_logs      = "https://console.aws.amazon.com/cloudwatch/home?region=${var.region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.glue_jobs.name, "/", "$252F")}"
    glue_crawlers_logs  = "https://console.aws.amazon.com/cloudwatch/home?region=${var.region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.glue_crawlers.name, "/", "$252F")}"
    emr_serverless_logs = "https://console.aws.amazon.com/cloudwatch/home?region=${var.region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.emr_serverless.name, "/", "$252F")}"
  }
}

output "lake_formation_console" {
  description = "Lake Formation console URL"
  value       = "https://console.aws.amazon.com/lakeformation/home?region=${var.region}"
}

output "glue_console" {
  description = "AWS Glue console URL"
  value       = "https://console.aws.amazon.com/glue/home?region=${var.region}"
}

output "emr_console" {
  description = "EMR Serverless console URL"
  value       = "https://console.aws.amazon.com/emr/home?region=${var.region}#/serverless"
}

output "infrastructure_summary" {
  description = "High-level infrastructure summary"
  value = {
    project_name = var.project_name
    environment  = var.environment
    region       = var.region

    vpc = {
      id         = aws_vpc.lakehouse.id
      cidr_block = aws_vpc.lakehouse.cidr_block
    }

    data_lake = {
      raw_bucket    = aws_s3_bucket.raw.bucket
      bronze_bucket = aws_s3_bucket.bronze.bucket
      silver_bucket = aws_s3_bucket.silver.bucket
      gold_bucket   = aws_s3_bucket.gold.bucket
    }

    processing = {
      glue_jobs_count = 5
      emr_application = aws_emrserverless_application.spark.id
      crawlers_count  = 4
    }

    security = {
      kms_keys_count        = 3
      lake_formation_admin  = aws_iam_role.lakeformation_admin.name
    }
  }
}
