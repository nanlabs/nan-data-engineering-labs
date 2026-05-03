# ==================================================================================
# Outputs for CloudMart Serverless Data Lake Infrastructure - STARTER TEMPLATE
# ==================================================================================
# These outputs provide important information after Terraform deployment.
# Uncomment outputs as you complete the corresponding resources in main.tf
# ==================================================================================

# ==================================================================================
# S3 Bucket Outputs
# ==================================================================================

output "raw_data_bucket_name" {
  description = "Name of the S3 bucket for raw data (Bronze zone)"
  value       = aws_s3_bucket.raw_data.id
}

output "processed_data_bucket_name" {
  description = "Name of the S3 bucket for processed data (Silver zone)"
  value       = aws_s3_bucket.processed_data.id
}

output "curated_data_bucket_name" {
  description = "Name of the S3 bucket for curated data (Gold zone)"
  value       = aws_s3_bucket.curated_data.id
}

output "logs_bucket_name" {
  description = "Name of the S3 bucket for logs and temporary files"
  value       = aws_s3_bucket.logs.id
}

output "athena_results_bucket_name" {
  description = "Name of the S3 bucket for Athena query results"
  value       = aws_s3_bucket.athena_results.id
}

# ==================================================================================
# IAM Role Outputs
# ==================================================================================

output "lambda_ingestion_role_arn" {
  description = "ARN of the IAM role for Lambda ingestion functions"
  value       = aws_iam_role.lambda_ingestion.arn
}

output "glue_etl_role_arn" {
  description = "ARN of the IAM role for Glue ETL jobs"
  value       = aws_iam_role.glue_etl.arn
}

# TODO: Uncomment when you create Lambda functions
# output "lambda_functions_summary" {
#   description = "Summary of all Lambda functions"
#   value = {
#     orders_ingestion    = aws_lambda_function.orders_ingestion.function_name
#     customers_ingestion = aws_lambda_function.customers_ingestion.function_name
#     products_ingestion  = aws_lambda_function.products_ingestion.function_name
#     events_ingestion    = aws_lambda_function.events_ingestion.function_name
#   }
# }

# ==================================================================================
# AWS Glue Outputs
# ==================================================================================

output "glue_databases" {
  description = "Names of the Glue databases for each layer"
  value = {
    bronze = aws_glue_catalog_database.bronze.name
    silver = aws_glue_catalog_database.silver.name
    gold   = aws_glue_catalog_database.gold.name
  }
}

# TODO: Uncomment when you create Glue crawlers
# output "glue_crawlers_summary" {
#   description = "Summary of all Glue crawlers"
#   value = {
#     bronze_orders    = aws_glue_crawler.bronze_orders.name
#     bronze_customers = aws_glue_crawler.bronze_customers.name
#     # Add more crawlers
#   }
# }

# TODO: Uncomment when you create Glue jobs
# output "glue_jobs_summary" {
#   description = "Summary of all Glue ETL jobs"
#   value = {
#     bronze_to_silver_orders = aws_glue_job.bronze_to_silver_orders.name
#     # Add more jobs
#   }
# }

# ==================================================================================
# Athena Outputs
# ==================================================================================

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.primary.name
}

output "athena_query_results_location" {
  description = "S3 location for Athena query results"
  value       = "s3://${aws_s3_bucket.athena_results.id}/query-results/"
}

# ==================================================================================
# SNS Outputs
# ==================================================================================

output "sns_topic_arn" {
  description = "ARN of the SNS topic for pipeline alerts"
  value       = aws_sns_topic.data_pipeline_alerts.arn
}

# ==================================================================================
# Instructions
# ==================================================================================

output "next_steps" {
  description = "Instructions for next steps after deployment"
  value = <<-EOT
    ✓ Infrastructure deployed successfully!

    NEXT STEPS:
    1. Complete TODOs in main.tf to enable Lambda functions and Glue jobs
    2. Upload sample data to: s3://${aws_s3_bucket.raw_data.id}/
    3. Test Lambda ingestion by uploading files
    4. Run Glue crawlers to catalog data
    5. Query data using Athena workgroup: ${aws_athena_workgroup.primary.name}

    USEFUL COMMANDS:
    - Test deployment: terraform plan
    - Upload data: aws s3 cp local-file s3://${aws_s3_bucket.raw_data.id}/orders/
    - Start crawler: aws glue start-crawler --name <crawler-name>
    - Query Athena: Use AWS Console or AWS CLI
  EOT
}
