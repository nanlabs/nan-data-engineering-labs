# Real-Time Analytics Platform - Terraform Outputs
# TODO: Complete output definitions to export important resource information

# =============================================================================
# KINESIS OUTPUTS
# =============================================================================

# TODO: Export Kinesis stream ARN
# Used by: Lambda event source mapping, IAM policies, producer applications
# output "kinesis_stream_arn" {
#   description = "ARN of the Kinesis Data Stream for ride events"
#   value       = aws_kinesis_stream.ride_events.arn
# }

# TODO: Export Kinesis stream name
# Used by: Producer applications to send events
# output "kinesis_stream_name" {
#   description = "Name of the Kinesis Data Stream"
#   value       = aws_kinesis_stream.ride_events.name
# }

# TODO: Export Kinesis shard count
# Useful for: Monitoring and capacity planning
# output "kinesis_shard_count" {
#   description = "Number of shards in the Kinesis stream"
#   value       = aws_kinesis_stream.ride_events.shard_count
# }

# =============================================================================
# DYNAMODB OUTPUTS
# =============================================================================

# TODO: Export rides table name
# Used by: Lambda function environment variables
# output "rides_table_name" {
#   description = "Name of the DynamoDB table storing ride data"
#   value       = aws_dynamodb_table.rides.name
# }

# TODO: Export rides table ARN
# Used by: IAM policy resources
# output "rides_table_arn" {
#   description = "ARN of the rides DynamoDB table"
#   value       = aws_dynamodb_table.rides.arn
# }

# TODO: Export metrics table name
# Used by: Lambda function environment variables
# output "metrics_table_name" {
#   description = "Name of the DynamoDB table storing metrics"
#   value       = aws_dynamodb_table.metrics.name
# }

# TODO: Export metrics table ARN
# Used by: IAM policy resources
# output "metrics_table_arn" {
#   description = "ARN of the metrics DynamoDB table"
#   value       = aws_dynamodb_table.metrics.arn
# }

# =============================================================================
# S3 OUTPUTS
# =============================================================================

# TODO: Export raw events bucket name
# Used by: Lambda function for archiving raw events
# output "raw_events_bucket_name" {
#   description = "Name of S3 bucket for raw events"
#   value       = aws_s3_bucket.raw_events.bucket
# }

# TODO: Export raw events bucket ARN
# output "raw_events_bucket_arn" {
#   description = "ARN of raw events S3 bucket"
#   value       = aws_s3_bucket.raw_events.arn
# }

# TODO: Export processed events bucket name
# Used by: Lambda function, Glue crawler, Athena queries
# output "processed_events_bucket_name" {
#   description = "Name of S3 bucket for processed events"
#   value       = aws_s3_bucket.processed_events.bucket
# }

# TODO: Export processed events bucket ARN
# output "processed_events_bucket_arn" {
#   description = "ARN of processed events S3 bucket"
#   value       = aws_s3_bucket.processed_events.arn
# }

# TODO: Export Athena results bucket name
# Used by: Athena query execution, Airflow DAGs
# output "athena_results_bucket_name" {
#   description = "Name of S3 bucket for Athena query results"
#   value       = aws_s3_bucket.athena_results.bucket
# }

# =============================================================================
# LAMBDA OUTPUTS
# =============================================================================

# TODO: Export Lambda function name
# Used by: Testing, monitoring, manual invocations
# output "lambda_function_name" {
#   description = "Name of the rides processor Lambda function"
#   value       = aws_lambda_function.rides_processor.function_name
# }

# TODO: Export Lambda function ARN
# Used by: Event source mappings, IAM policies, CloudWatch alarms
# output "lambda_function_arn" {
#   description = "ARN of the rides processor Lambda function"
#   value       = aws_lambda_function.rides_processor.arn
# }

# TODO: Export Lambda IAM role ARN
# Used by: Debugging permissions issues
# output "lambda_role_arn" {
#   description = "ARN of the IAM role used by Lambda function"
#   value       = aws_iam_role.rides_processor_lambda.arn
# }

# =============================================================================
# GLUE OUTPUTS
# =============================================================================

# TODO: Export Glue database name
# Used by: Athena queries, Glue crawler
# output "glue_database_name" {
#   description = "Name of the Glue catalog database"
#   value       = aws_glue_catalog_database.ride_analytics.name
# }

# TODO: Export Glue crawler name
# Used by: Airflow DAGs to trigger crawler runs
# output "glue_crawler_name" {
#   description = "Name of the Glue crawler"
#   value       = aws_glue_crawler.ride_events.name
# }

# =============================================================================
# CLOUDWATCH OUTPUTS
# =============================================================================

# TODO: Export CloudWatch log group name
# Used by: Viewing logs, log analysis
# output "lambda_log_group_name" {
#   description = "Name of CloudWatch log group for Lambda function"
#   value       = aws_cloudwatch_log_group.rides_processor.name
# }

# TODO: Export SNS topic ARN for alerts
# Used by: Subscribing to alerts, additional alarm configurations
# output "alerts_sns_topic_arn" {
#   description = "ARN of SNS topic for CloudWatch alarms"
#   value       = aws_sns_topic.alerts.arn
# }

# =============================================================================
# GENERAL OUTPUTS
# =============================================================================

# TODO: Export AWS region
# Useful for: CLI commands, SDK configuration
# output "aws_region" {
#   description = "AWS region where resources are deployed"
#   value       = data.aws_region.current.name
# }

# TODO: Export AWS account ID
# Useful for: Cross-account access, resource ARN construction
# output "aws_account_id" {
#   description = "AWS account ID"
#   value       = data.aws_caller_identity.current.account_id
#   sensitive   = true  # Mark as sensitive to avoid accidental exposure
# }

# TODO: Export environment
# Useful for: CI/CD pipelines, testing different environments
# output "environment" {
#   description = "Current environment (dev, staging, prod)"
#   value       = var.environment
# }

# TODO: Export project name
# output "project_name" {
#   description = "Project name used for resource naming"
#   value       = var.project_name
# }

# =============================================================================
# PRODUCER HELPER OUTPUTS
# =============================================================================

# TODO: Create a formatted output for easy producer configuration
# This helps students quickly get the required configuration for running the producer
# output "producer_config" {
#   description = "Configuration for running the event producer"
#   value = {
#     stream_name = aws_kinesis_stream.ride_events.name
#     region      = data.aws_region.current.name
#     environment = var.environment
#   }
# }

# =============================================================================
# LAMBDA ENVIRONMENT VARIABLES OUTPUT
# =============================================================================

# TODO: Export all Lambda environment variables for reference
# Useful for: Debugging, local testing
# output "lambda_environment_variables" {
#   description = "Environment variables configured for Lambda function"
#   value       = aws_lambda_function.rides_processor.environment[0].variables
#   sensitive   = true  # May contain sensitive configuration
# }

# =============================================================================
# USEFUL COMMANDS OUTPUT
# =============================================================================

# TODO: Create helpful command outputs for students
# These outputs provide ready-to-use commands for common operations

# output "helpful_commands" {
#   description = "Useful AWS CLI commands for this deployment"
#   value = <<-EOT
#     # View Kinesis stream details
#     aws kinesis describe-stream --stream-name ${aws_kinesis_stream.ride_events.name} --region ${data.aws_region.current.name}
#
#     # View DynamoDB table
#     aws dynamodb describe-table --table-name ${aws_dynamodb_table.rides.name} --region ${data.aws_region.current.name}
#
#     # Tail Lambda logs
#     aws logs tail /aws/lambda/${aws_lambda_function.rides_processor.function_name} --follow --region ${data.aws_region.current.name}
#
#     # Run Glue crawler
#     aws glue start-crawler --name ${aws_glue_crawler.ride_events.name} --region ${data.aws_region.current.name}
#
#     # Query Athena
#     aws athena start-query-execution \
#       --query-string "SELECT * FROM ${aws_glue_catalog_database.ride_analytics.name}.ride_events LIMIT 10" \
#       --result-configuration "OutputLocation=s3://${aws_s3_bucket.athena_results.bucket}/" \
#       --query-execution-context "Database=${aws_glue_catalog_database.ride_analytics.name}" \
#       --region ${data.aws_region.current.name}
#   EOT
# }

# =============================================================================
# INSTRUCTIONS FOR STUDENTS
# =============================================================================

# WHAT ARE TERRAFORM OUTPUTS?
# Outputs are a way to extract and export information about your infrastructure
# after Terraform creates it. They are useful for:
# 1. Providing information to other Terraform configurations (modules)
# 2. Displaying important resource details after deployment
# 3. Passing values to external systems or scripts
# 4. Documentation and reference
#
# HOW TO USE OUTPUTS:
# After running `terraform apply`, outputs are displayed automatically.
# You can also view them anytime with: `terraform output`
# To get a specific output: `terraform output kinesis_stream_name`
# To get JSON format: `terraform output -json`
#
# OUTPUT ATTRIBUTES:
# - value: The actual value to output (required)
# - description: Human-readable description (recommended)
# - sensitive: Mark as sensitive to hide from console (optional)
#
# BEST PRACTICES:
# 1. Always add descriptions to outputs
# 2. Group related outputs together
# 3. Output both human-readable names and machine-readable ARNs
# 4. Mark sensitive data (passwords, keys) as sensitive
# 5. Consider creating formatted outputs for common use cases
# 6. Use outputs to generate helpful commands or configurations
#
# EXAMPLE USAGE IN OTHER MODULES:
# When using this as a module in another Terraform configuration:
#
# module "ride_analytics" {
#   source = "./modules/ride-analytics"
# }
#
# resource "aws_iam_policy" "external_access" {
#   # Reference output from module
#   policy = jsonencode({
#     Statement = [{
#       Effect   = "Allow"
#       Action   = ["kinesis:PutRecord"]
#       Resource = [module.ride_analytics.kinesis_stream_arn]
#     }]
#   })
# }
