# ==================================================================================
# Outputs for CloudMart Serverless Data Lake Infrastructure
# ==================================================================================
# This file defines all output values that will be displayed after Terraform apply.
# These outputs provide important information for accessing and managing resources.
# ==================================================================================

# ==================================================================================
# S3 Bucket Outputs
# ==================================================================================

output "raw_data_bucket_name" {
  description = "Name of the S3 bucket for raw data (Bronze zone)"
  value       = aws_s3_bucket.raw_data.id
}

output "raw_data_bucket_arn" {
  description = "ARN of the S3 bucket for raw data (Bronze zone)"
  value       = aws_s3_bucket.raw_data.arn
}

output "processed_data_bucket_name" {
  description = "Name of the S3 bucket for processed data (Silver zone)"
  value       = aws_s3_bucket.processed_data.id
}

output "processed_data_bucket_arn" {
  description = "ARN of the S3 bucket for processed data (Silver zone)"
  value       = aws_s3_bucket.processed_data.arn
}

output "curated_data_bucket_name" {
  description = "Name of the S3 bucket for curated data (Gold zone)"
  value       = aws_s3_bucket.curated_data.id
}

output "curated_data_bucket_arn" {
  description = "ARN of the S3 bucket for curated data (Gold zone)"
  value       = aws_s3_bucket.curated_data.arn
}

output "logs_bucket_name" {
  description = "Name of the S3 bucket for logs and temporary files"
  value       = aws_s3_bucket.logs.id
}

output "athena_results_bucket_name" {
  description = "Name of the S3 bucket for Athena query results"
  value       = aws_s3_bucket.athena_results.id
}

output "s3_bucket_summary" {
  description = "Summary of all S3 buckets created"
  value = {
    raw_data        = aws_s3_bucket.raw_data.id
    processed_data  = aws_s3_bucket.processed_data.id
    curated_data    = aws_s3_bucket.curated_data.id
    logs            = aws_s3_bucket.logs.id
    athena_results  = aws_s3_bucket.athena_results.id
  }
}

# ==================================================================================
# IAM Role Outputs
# ==================================================================================

output "lambda_ingestion_role_arn" {
  description = "ARN of the IAM role for Lambda ingestion functions"
  value       = aws_iam_role.lambda_ingestion.arn
}

output "lambda_ingestion_role_name" {
  description = "Name of the IAM role for Lambda ingestion functions"
  value       = aws_iam_role.lambda_ingestion.name
}

output "glue_etl_role_arn" {
  description = "ARN of the IAM role for Glue ETL jobs"
  value       = aws_iam_role.glue_etl.arn
}

output "glue_etl_role_name" {
  description = "Name of the IAM role for Glue ETL jobs"
  value       = aws_iam_role.glue_etl.name
}

output "athena_query_role_arn" {
  description = "ARN of the IAM role for Athena queries"
  value       = aws_iam_role.athena_query.arn
}

output "athena_query_role_name" {
  description = "Name of the IAM role for Athena queries"
  value       = aws_iam_role.athena_query.name
}

# ==================================================================================
# Lambda Function Outputs
# ==================================================================================

output "lambda_ingest_orders_arn" {
  description = "ARN of the Lambda function for orders ingestion"
  value       = aws_lambda_function.ingest_orders.arn
}

output "lambda_ingest_orders_name" {
  description = "Name of the Lambda function for orders ingestion"
  value       = aws_lambda_function.ingest_orders.function_name
}

output "lambda_ingest_customers_arn" {
  description = "ARN of the Lambda function for customers ingestion"
  value       = aws_lambda_function.ingest_customers.arn
}

output "lambda_ingest_customers_name" {
  description = "Name of the Lambda function for customers ingestion"
  value       = aws_lambda_function.ingest_customers.function_name
}

output "lambda_ingest_products_arn" {
  description = "ARN of the Lambda function for products ingestion"
  value       = aws_lambda_function.ingest_products.arn
}

output "lambda_ingest_products_name" {
  description = "Name of the Lambda function for products ingestion"
  value       = aws_lambda_function.ingest_products.function_name
}

output "lambda_ingest_events_arn" {
  description = "ARN of the Lambda function for events ingestion"
  value       = aws_lambda_function.ingest_events.arn
}

output "lambda_ingest_events_name" {
  description = "Name of the Lambda function for events ingestion"
  value       = aws_lambda_function.ingest_events.function_name
}

output "lambda_functions_summary" {
  description = "Summary of all Lambda functions created"
  value = {
    ingest_orders    = aws_lambda_function.ingest_orders.function_name
    ingest_customers = aws_lambda_function.ingest_customers.function_name
    ingest_products  = aws_lambda_function.ingest_products.function_name
    ingest_events    = aws_lambda_function.ingest_events.function_name
  }
}

# ==================================================================================
# AWS Glue Outputs
# ==================================================================================

output "glue_database_name" {
  description = "Name of the Glue Data Catalog database"
  value       = aws_glue_catalog_database.cloudmart.name
}

output "glue_database_arn" {
  description = "ARN of the Glue Data Catalog database"
  value       = aws_glue_catalog_database.cloudmart.arn
}

output "glue_crawler_raw_name" {
  description = "Name of the Glue crawler for raw data (Bronze zone)"
  value       = aws_glue_crawler.raw_data.name
}

output "glue_crawler_processed_name" {
  description = "Name of the Glue crawler for processed data (Silver zone)"
  value       = aws_glue_crawler.processed_data.name
}

output "glue_crawler_curated_name" {
  description = "Name of the Glue crawler for curated data (Gold zone)"
  value       = aws_glue_crawler.curated_data.name
}

output "glue_crawlers_summary" {
  description = "Summary of all Glue crawlers created"
  value = {
    raw_data        = aws_glue_crawler.raw_data.name
    processed_data  = aws_glue_crawler.processed_data.name
    curated_data    = aws_glue_crawler.curated_data.name
  }
}

output "glue_job_bronze_to_silver_orders_name" {
  description = "Name of the Glue ETL job for processing orders (Bronze to Silver)"
  value       = aws_glue_job.bronze_to_silver_orders.name
}

output "glue_job_bronze_to_silver_customers_name" {
  description = "Name of the Glue ETL job for processing customers (Bronze to Silver)"
  value       = aws_glue_job.bronze_to_silver_customers.name
}

output "glue_job_bronze_to_silver_products_name" {
  description = "Name of the Glue ETL job for processing products (Bronze to Silver)"
  value       = aws_glue_job.bronze_to_silver_products.name
}

output "glue_job_silver_to_gold_sales_name" {
  description = "Name of the Glue ETL job for sales analytics (Silver to Gold)"
  value       = aws_glue_job.silver_to_gold_sales_analytics.name
}

output "glue_job_silver_to_gold_customers_name" {
  description = "Name of the Glue ETL job for customer analytics (Silver to Gold)"
  value       = aws_glue_job.silver_to_gold_customer_analytics.name
}

output "glue_jobs_summary" {
  description = "Summary of all Glue ETL jobs created"
  value = {
    bronze_to_silver_orders    = aws_glue_job.bronze_to_silver_orders.name
    bronze_to_silver_customers = aws_glue_job.bronze_to_silver_customers.name
    bronze_to_silver_products  = aws_glue_job.bronze_to_silver_products.name
    silver_to_gold_sales       = aws_glue_job.silver_to_gold_sales_analytics.name
    silver_to_gold_customers   = aws_glue_job.silver_to_gold_customer_analytics.name
  }
}

# ==================================================================================
# Athena Outputs
# ==================================================================================

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup for analytics queries"
  value       = aws_athena_workgroup.cloudmart_analytics.name
}

output "athena_workgroup_arn" {
  description = "ARN of the Athena workgroup"
  value       = aws_athena_workgroup.cloudmart_analytics.arn
}

output "athena_query_results_location" {
  description = "S3 location for Athena query results"
  value       = "s3://${aws_s3_bucket.athena_results.id}/query-results/"
}

# ==================================================================================
# SNS Outputs
# ==================================================================================

output "sns_topic_pipeline_alerts_arn" {
  description = "ARN of the SNS topic for data pipeline alerts"
  value       = aws_sns_topic.pipeline_alerts.arn
}

output "sns_topic_pipeline_alerts_name" {
  description = "Name of the SNS topic for data pipeline alerts"
  value       = aws_sns_topic.pipeline_alerts.name
}

# ==================================================================================
# CloudWatch Outputs
# ==================================================================================

output "cloudwatch_log_group_orders" {
  description = "Name of the CloudWatch log group for orders Lambda function"
  value       = aws_cloudwatch_log_group.ingest_orders.name
}

output "cloudwatch_log_group_customers" {
  description = "Name of the CloudWatch log group for customers Lambda function"
  value       = aws_cloudwatch_log_group.ingest_customers.name
}

output "cloudwatch_log_group_products" {
  description = "Name of the CloudWatch log group for products Lambda function"
  value       = aws_cloudwatch_log_group.ingest_products.name
}

output "cloudwatch_log_group_events" {
  description = "Name of the CloudWatch log group for events Lambda function"
  value       = aws_cloudwatch_log_group.ingest_events.name
}

# ==================================================================================
# EventBridge Outputs
# ==================================================================================

output "eventbridge_rule_raw_crawler_name" {
  description = "Name of the EventBridge rule for raw data crawler schedule"
  value       = aws_cloudwatch_event_rule.raw_crawler_schedule.name
}

output "eventbridge_rule_processed_crawler_name" {
  description = "Name of the EventBridge rule for processed data crawler schedule"
  value       = aws_cloudwatch_event_rule.processed_crawler_schedule.name
}

output "eventbridge_rule_curated_crawler_name" {
  description = "Name of the EventBridge rule for curated data crawler schedule"
  value       = aws_cloudwatch_event_rule.curated_crawler_schedule.name
}

# ==================================================================================
# Instructions and Next Steps
# ==================================================================================

output "deployment_instructions" {
  description = "Instructions for using the deployed infrastructure"
  value = <<-EOT
    CloudMart Serverless Data Lake has been successfully deployed!

    === NEXT STEPS ===

    1. UPLOAD GLUE ETL SCRIPTS:
       - Upload your Glue job scripts to: s3://${aws_s3_bucket.logs.id}/glue-scripts/
       - Required scripts:
         * bronze_to_silver_orders.py
         * bronze_to_silver_customers.py
         * bronze_to_silver_products.py
         * silver_to_gold_sales.py
         * silver_to_gold_customers.py

    2. UPDATE LAMBDA FUNCTIONS:
       - Replace the placeholder Lambda code with your actual ingestion logic
       - Lambda functions: ${aws_lambda_function.ingest_orders.function_name}, etc.

    3. VERIFY SNS SUBSCRIPTION:
       - Check your email (${var.alert_email}) for SNS subscription confirmation
       - Click the confirmation link to receive alerts

    4. START INGESTING DATA:
       - Upload raw data to: s3://${aws_s3_bucket.raw_data.id}/
       - Lambda functions will automatically process new data

    5. RUN GLUE CRAWLERS:
       - Crawlers will run on schedule, or run manually:
         * aws glue start-crawler --name ${aws_glue_crawler.raw_data.name}
         * aws glue start-crawler --name ${aws_glue_crawler.processed_data.name}
         * aws glue start-crawler --name ${aws_glue_crawler.curated_data.name}

    6. QUERY DATA WITH ATHENA:
       - Open Athena console
       - Select workgroup: ${aws_athena_workgroup.cloudmart_analytics.name}
       - Query database: ${aws_glue_catalog_database.cloudmart.name}
       - Results saved to: s3://${aws_s3_bucket.athena_results.id}/query-results/

    === DATA FLOW ===
    Raw Data (Bronze) → Glue ETL → Processed Data (Silver) → Glue ETL → Curated Data (Gold) → Athena Analytics
  EOT
}

output "resource_summary" {
  description = "Summary of all resources created"
  value = {
    s3_buckets      = 5
    lambda_functions = 4
    glue_crawlers   = 3
    glue_jobs       = 5
    iam_roles       = 4
    sns_topics      = 1
    athena_workgroups = 1
    cloudwatch_alarms = 4
    eventbridge_rules = 3
  }
}
