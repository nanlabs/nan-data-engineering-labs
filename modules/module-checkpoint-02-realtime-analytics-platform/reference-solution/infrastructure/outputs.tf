# ============================================================================
# TERRAFORM OUTPUTS - CHECKPOINT 02: REAL-TIME ANALYTICS PLATFORM
# ============================================================================

# ============================================================================
# KINESIS OUTPUTS
# ============================================================================

output "kinesis_rides_stream_arn" {
  description = "ARN of the rides Kinesis stream"
  value       = aws_kinesis_stream.rides.arn
}

output "kinesis_rides_stream_name" {
  description = "Name of the rides Kinesis stream"
  value       = aws_kinesis_stream.rides.name
}

output "kinesis_locations_stream_arn" {
  description = "ARN of the locations Kinesis stream"
  value       = aws_kinesis_stream.locations.arn
}

output "kinesis_locations_stream_name" {
  description = "Name of the locations Kinesis stream"
  value       = aws_kinesis_stream.locations.name
}

output "kinesis_payments_stream_arn" {
  description = "ARN of the payments Kinesis stream"
  value       = aws_kinesis_stream.payments.arn
}

output "kinesis_payments_stream_name" {
  description = "Name of the payments Kinesis stream"
  value       = aws_kinesis_stream.payments.name
}

output "kinesis_ratings_stream_arn" {
  description = "ARN of the ratings Kinesis stream"
  value       = aws_kinesis_stream.ratings.arn
}

output "kinesis_ratings_stream_name" {
  description = "Name of the ratings Kinesis stream"
  value       = aws_kinesis_stream.ratings.name
}

# ============================================================================
# LAMBDA OUTPUTS
# ============================================================================

output "lambda_ride_processor_arn" {
  description = "ARN of the ride processor Lambda function"
  value       = aws_lambda_function.ride_processor.arn
}

output "lambda_ride_processor_name" {
  description = "Name of the ride processor Lambda function"
  value       = aws_lambda_function.ride_processor.function_name
}

output "lambda_location_processor_arn" {
  description = "ARN of the location processor Lambda function"
  value       = aws_lambda_function.location_processor.arn
}

output "lambda_location_processor_name" {
  description = "Name of the location processor Lambda function"
  value       = aws_lambda_function.location_processor.function_name
}

output "lambda_payment_processor_arn" {
  description = "ARN of the payment processor Lambda function"
  value       = aws_lambda_function.payment_processor.arn
}

output "lambda_payment_processor_name" {
  description = "Name of the payment processor Lambda function"
  value       = aws_lambda_function.payment_processor.function_name
}

output "lambda_rating_processor_arn" {
  description = "ARN of the rating processor Lambda function"
  value       = aws_lambda_function.rating_processor.arn
}

output "lambda_rating_processor_name" {
  description = "Name of the rating processor Lambda function"
  value       = aws_lambda_function.rating_processor.function_name
}

# ============================================================================
# DYNAMODB OUTPUTS
# ============================================================================

output "dynamodb_rides_table_name" {
  description = "Name of the rides state DynamoDB table"
  value       = aws_dynamodb_table.rides_state.name
}

output "dynamodb_rides_table_arn" {
  description = "ARN of the rides state DynamoDB table"
  value       = aws_dynamodb_table.rides_state.arn
}

output "dynamodb_rides_stream_arn" {
  description = "ARN of the rides table DynamoDB stream"
  value       = aws_dynamodb_table.rides_state.stream_arn
}

output "dynamodb_drivers_table_name" {
  description = "Name of the driver availability DynamoDB table"
  value       = aws_dynamodb_table.driver_availability.name
}

output "dynamodb_drivers_table_arn" {
  description = "ARN of the driver availability DynamoDB table"
  value       = aws_dynamodb_table.driver_availability.arn
}

output "dynamodb_drivers_stream_arn" {
  description = "ARN of the drivers table DynamoDB stream"
  value       = aws_dynamodb_table.driver_availability.stream_arn
}

output "dynamodb_metrics_table_name" {
  description = "Name of the aggregated metrics DynamoDB table"
  value       = aws_dynamodb_table.aggregated_metrics.name
}

output "dynamodb_metrics_table_arn" {
  description = "ARN of the aggregated metrics DynamoDB table"
  value       = aws_dynamodb_table.aggregated_metrics.arn
}

# ============================================================================
# S3 OUTPUTS
# ============================================================================

output "s3_streaming_archive_bucket_name" {
  description = "Name of the streaming archive S3 bucket"
  value       = aws_s3_bucket.streaming_archive.id
}

output "s3_streaming_archive_bucket_arn" {
  description = "ARN of the streaming archive S3 bucket"
  value       = aws_s3_bucket.streaming_archive.arn
}

output "s3_analytics_output_bucket_name" {
  description = "Name of the analytics output S3 bucket"
  value       = aws_s3_bucket.analytics_output.id
}

output "s3_analytics_output_bucket_arn" {
  description = "ARN of the analytics output S3 bucket"
  value       = aws_s3_bucket.analytics_output.arn
}

output "s3_kinesis_analytics_output_bucket_name" {
  description = "Name of the Kinesis analytics output S3 bucket"
  value       = aws_s3_bucket.kinesis_analytics_output.id
}

output "s3_kinesis_analytics_output_bucket_arn" {
  description = "ARN of the Kinesis analytics output S3 bucket"
  value       = aws_s3_bucket.kinesis_analytics_output.arn
}

# ============================================================================
# IAM OUTPUTS
# ============================================================================

output "iam_lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_kinesis.arn
}

output "iam_lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_kinesis.name
}

output "iam_analytics_role_arn" {
  description = "ARN of the Kinesis Analytics role"
  value       = aws_iam_role.analytics.arn
}

output "iam_analytics_role_name" {
  description = "Name of the Kinesis Analytics role"
  value       = aws_iam_role.analytics.name
}

output "iam_step_functions_role_arn" {
  description = "ARN of the Step Functions execution role"
  value       = aws_iam_role.step_functions.arn
}

output "iam_step_functions_role_name" {
  description = "Name of the Step Functions execution role"
  value       = aws_iam_role.step_functions.name
}

# ============================================================================
# SQS OUTPUTS
# ============================================================================

output "sqs_ride_dlq_url" {
  description = "URL of the ride processor dead letter queue"
  value       = aws_sqs_queue.ride_dlq.url
}

output "sqs_ride_dlq_arn" {
  description = "ARN of the ride processor dead letter queue"
  value       = aws_sqs_queue.ride_dlq.arn
}

output "sqs_location_dlq_url" {
  description = "URL of the location processor dead letter queue"
  value       = aws_sqs_queue.location_dlq.url
}

output "sqs_location_dlq_arn" {
  description = "ARN of the location processor dead letter queue"
  value       = aws_sqs_queue.location_dlq.arn
}

output "sqs_payment_dlq_url" {
  description = "URL of the payment processor dead letter queue"
  value       = aws_sqs_queue.payment_dlq.url
}

output "sqs_payment_dlq_arn" {
  description = "ARN of the payment processor dead letter queue"
  value       = aws_sqs_queue.payment_dlq.arn
}

output "sqs_rating_dlq_url" {
  description = "URL of the rating processor dead letter queue"
  value       = aws_sqs_queue.rating_dlq.url
}

output "sqs_rating_dlq_arn" {
  description = "ARN of the rating processor dead letter queue"
  value       = aws_sqs_queue.rating_dlq.arn
}

# ============================================================================
# SNS OUTPUTS
# ============================================================================

output "sns_alerts_topic_arn" {
  description = "ARN of the alerts SNS topic"
  value       = aws_sns_topic.alerts.arn
}

output "sns_alerts_topic_name" {
  description = "Name of the alerts SNS topic"
  value       = aws_sns_topic.alerts.name
}

# ============================================================================
# KMS OUTPUTS
# ============================================================================

output "kms_kinesis_key_id" {
  description = "ID of the Kinesis encryption KMS key"
  value       = aws_kms_key.kinesis.id
}

output "kms_kinesis_key_arn" {
  description = "ARN of the Kinesis encryption KMS key"
  value       = aws_kms_key.kinesis.arn
}

output "kms_dynamodb_key_id" {
  description = "ID of the DynamoDB encryption KMS key"
  value       = aws_kms_key.dynamodb.id
}

output "kms_dynamodb_key_arn" {
  description = "ARN of the DynamoDB encryption KMS key"
  value       = aws_kms_key.dynamodb.arn
}

output "kms_s3_key_id" {
  description = "ID of the S3 encryption KMS key"
  value       = aws_kms_key.s3.id
}

output "kms_s3_key_arn" {
  description = "ARN of the S3 encryption KMS key"
  value       = aws_kms_key.s3.arn
}

# ============================================================================
# CLOUDWATCH OUTPUTS
# ============================================================================

output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "cloudwatch_log_group_ride_processor" {
  description = "Name of the ride processor Lambda log group"
  value       = aws_cloudwatch_log_group.ride_processor.name
}

output "cloudwatch_log_group_location_processor" {
  description = "Name of the location processor Lambda log group"
  value       = aws_cloudwatch_log_group.location_processor.name
}

output "cloudwatch_log_group_payment_processor" {
  description = "Name of the payment processor Lambda log group"
  value       = aws_cloudwatch_log_group.payment_processor.name
}

output "cloudwatch_log_group_rating_processor" {
  description = "Name of the rating processor Lambda log group"
  value       = aws_cloudwatch_log_group.rating_processor.name
}

# ============================================================================
# DEPLOYMENT INSTRUCTIONS
# ============================================================================

output "deployment_instructions" {
  description = "Next steps after infrastructure deployment"
  value = <<-EOT

    ╔════════════════════════════════════════════════════════════════════════╗
    ║  REAL-TIME ANALYTICS PLATFORM - DEPLOYMENT COMPLETE                    ║
    ╚════════════════════════════════════════════════════════════════════════╝

    Infrastructure has been successfully deployed!

    📋 NEXT STEPS:

    1. Upload Lambda Function Code
       - Package your Lambda functions with dependencies
       - Upload to each function using AWS CLI or console
       - Update environment variables if needed

    2. Test Event Ingestion
       aws kinesis put-record \
         --stream-name ${aws_kinesis_stream.rides.name} \
         --partition-key test-key \
         --data '{"ride_id":"123","status":"requested"}'

    3. Monitor Lambda Execution
       aws logs tail /aws/lambda/${aws_lambda_function.ride_processor.function_name} --follow

    4. Check DynamoDB Tables
       aws dynamodb scan --table-name ${aws_dynamodb_table.rides_state.name} --limit 10

    5. View CloudWatch Dashboard
       ${self.cloudwatch_dashboard_url}

    6. Configure SNS Subscriptions
       - Confirm email subscription sent to: ${var.alert_email}
       - Add additional subscribers if needed

    7. Deploy Kinesis Analytics Applications
       - Create surge pricing analytics app
       - Create real-time metrics analytics app
       - Create hot spots detection app

    8. Set Up QuickSight
       - Create datasets from DynamoDB and S3
       - Build dashboards for visualization
       - Configure scheduled refreshes

    9. Test End-to-End Flow
       - Generate test events
       - Verify processing in CloudWatch Logs
       - Check data in DynamoDB and S3
       - Validate metrics in dashboard

    10. Production Checklist
        ☐ Review IAM permissions (least privilege)
        ☐ Enable AWS CloudTrail for audit logs
        ☐ Configure VPC endpoints (if required)
        ☐ Set up backup and disaster recovery
        ☐ Document runbooks for operations
        ☐ Configure cost budgets and alerts
        ☐ Enable AWS Config for compliance
        ☐ Set up centralized logging

    📊 RESOURCE SUMMARY:
    - Kinesis Streams: 4
    - Lambda Functions: 4
    - DynamoDB Tables: 3
    - S3 Buckets: 3
    - CloudWatch Alarms: 3+
    - SNS Topics: 1
    - SQS Queues: 4 (DLQs)

    🔗 USEFUL LINKS:
    - Lambda Console: https://console.aws.amazon.com/lambda/home?region=${data.aws_region.current.name}
    - Kinesis Console: https://console.aws.amazon.com/kinesis/home?region=${data.aws_region.current.name}
    - DynamoDB Console: https://console.aws.amazon.com/dynamodb/home?region=${data.aws_region.current.name}
    - S3 Console: https://console.aws.amazon.com/s3/home?region=${data.aws_region.current.name}
    - CloudWatch Console: https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}

    📧 Support: For issues, check CloudWatch Logs and DLQs first

  EOT
}
