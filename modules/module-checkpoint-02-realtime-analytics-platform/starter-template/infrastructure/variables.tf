# ============================================================================
# TERRAFORM VARIABLES - CHECKPOINT 02: REAL-TIME ANALYTICS PLATFORM
# ============================================================================

# ============================================================================
# PROJECT CONFIGURATION
# ============================================================================

variable "project_name" {
  description = "Name of the project, used as prefix for all resources"
  type        = string
  default     = "rideshare-analytics"

  validation {
    condition     = length(var.project_name) <= 20 && can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric with hyphens, max 20 characters"
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be a valid region identifier (e.g., us-east-1)"
  }
}

# ============================================================================
# KINESIS CONFIGURATION
# ============================================================================

variable "kinesis_shard_count" {
  description = "Number of shards per Kinesis stream (for high-volume streams)"
  type        = number
  default     = 2

  validation {
    condition     = var.kinesis_shard_count >= 1 && var.kinesis_shard_count <= 100
    error_message = "Shard count must be between 1 and 100"
  }
}

variable "kinesis_retention_hours" {
  description = "Data retention period in hours for Kinesis streams (24-8760)"
  type        = number
  default     = 24

  validation {
    condition     = var.kinesis_retention_hours >= 24 && var.kinesis_retention_hours <= 8760
    error_message = "Retention must be between 24 hours (1 day) and 8760 hours (365 days)"
  }
}

variable "kinesis_enhanced_monitoring" {
  description = "Enable enhanced (shard-level) monitoring for Kinesis streams"
  type        = bool
  default     = true
}

# ============================================================================
# LAMBDA CONFIGURATION
# ============================================================================

variable "lambda_memory_mb" {
  description = "Memory allocation for Lambda functions in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_mb >= 128 && var.lambda_memory_mb <= 10240
    error_message = "Lambda memory must be between 128 MB and 10240 MB"
  }
}

variable "lambda_timeout_seconds" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 60

  validation {
    condition     = var.lambda_timeout_seconds >= 1 && var.lambda_timeout_seconds <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds (15 minutes)"
  }
}

variable "lambda_batch_size" {
  description = "Number of records to batch for Lambda processing from Kinesis"
  type        = number
  default     = 100

  validation {
    condition     = var.lambda_batch_size >= 1 && var.lambda_batch_size <= 10000
    error_message = "Batch size must be between 1 and 10,000 records"
  }
}

variable "lambda_parallelization_factor" {
  description = "Number of concurrent batches per shard for Lambda processing"
  type        = number
  default     = 10

  validation {
    condition     = var.lambda_parallelization_factor >= 1 && var.lambda_parallelization_factor <= 10
    error_message = "Parallelization factor must be between 1 and 10"
  }
}

variable "lambda_reserved_concurrency_rides" {
  description = "Reserved concurrent executions for ride processor Lambda"
  type        = number
  default     = 100

  validation {
    condition     = var.lambda_reserved_concurrency_rides >= 0
    error_message = "Reserved concurrency must be non-negative"
  }
}

variable "lambda_reserved_concurrency_locations" {
  description = "Reserved concurrent executions for location processor Lambda"
  type        = number
  default     = 100

  validation {
    condition     = var.lambda_reserved_concurrency_locations >= 0
    error_message = "Reserved concurrency must be non-negative"
  }
}

variable "lambda_reserved_concurrency_payments" {
  description = "Reserved concurrent executions for payment processor Lambda"
  type        = number
  default     = 50

  validation {
    condition     = var.lambda_reserved_concurrency_payments >= 0
    error_message = "Reserved concurrency must be non-negative"
  }
}

variable "lambda_reserved_concurrency_ratings" {
  description = "Reserved concurrent executions for rating processor Lambda"
  type        = number
  default     = 20

  validation {
    condition     = var.lambda_reserved_concurrency_ratings >= 0
    error_message = "Reserved concurrency must be non-negative"
  }
}

variable "lambda_log_retention_days" {
  description = "Number of days to retain Lambda CloudWatch logs"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.lambda_log_retention_days)
    error_message = "Log retention must be a valid CloudWatch Logs retention period"
  }
}

# ============================================================================
# DYNAMODB CONFIGURATION
# ============================================================================

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode: PAY_PER_REQUEST or PROVISIONED"
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.dynamodb_billing_mode)
    error_message = "Billing mode must be PAY_PER_REQUEST or PROVISIONED"
  }
}

variable "dynamodb_read_capacity" {
  description = "Provisioned read capacity units (only used if billing_mode is PROVISIONED)"
  type        = number
  default     = 5

  validation {
    condition     = var.dynamodb_read_capacity >= 1
    error_message = "Read capacity must be at least 1 RCU"
  }
}

variable "dynamodb_write_capacity" {
  description = "Provisioned write capacity units (only used if billing_mode is PROVISIONED)"
  type        = number
  default     = 5

  validation {
    condition     = var.dynamodb_write_capacity >= 1
    error_message = "Write capacity must be at least 1 WCU"
  }
}

variable "dynamodb_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB tables"
  type        = bool
  default     = true
}

variable "dynamodb_stream_enabled" {
  description = "Enable DynamoDB Streams for CDC"
  type        = bool
  default     = true
}

variable "dynamodb_ttl_enabled" {
  description = "Enable TTL for automatic item expiration"
  type        = bool
  default     = true
}

variable "rides_ttl_days" {
  description = "Number of days to keep ride records in DynamoDB before expiration"
  type        = number
  default     = 7

  validation {
    condition     = var.rides_ttl_days >= 1
    error_message = "TTL must be at least 1 day"
  }
}

variable "metrics_ttl_days" {
  description = "Number of days to keep metrics in DynamoDB before expiration"
  type        = number
  default     = 30

  validation {
    condition     = var.metrics_ttl_days >= 1
    error_message = "TTL must be at least 1 day"
  }
}

# ============================================================================
# KINESIS DATA ANALYTICS CONFIGURATION
# ============================================================================

variable "analytics_kpu" {
  description = "Number of Kinesis Processing Units (KPU) for analytics applications"
  type        = number
  default     = 1

  validation {
    condition     = var.analytics_kpu >= 1 && var.analytics_kpu <= 32
    error_message = "KPU must be between 1 and 32"
  }
}

variable "analytics_parallelism" {
  description = "Parallelism for Kinesis Data Analytics applications"
  type        = number
  default     = 2

  validation {
    condition     = var.analytics_parallelism >= 1
    error_message = "Parallelism must be at least 1"
  }
}

variable "enable_surge_pricing_analytics" {
  description = "Enable surge pricing analytics application"
  type        = bool
  default     = true
}

variable "enable_realtime_metrics_analytics" {
  description = "Enable real-time metrics analytics application"
  type        = bool
  default     = true
}

variable "enable_hot_spots_analytics" {
  description = "Enable hot spots detection analytics application"
  type        = bool
  default     = true
}

# ============================================================================
# S3 CONFIGURATION
# ============================================================================

variable "s3_versioning_enabled" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_glacier_days" {
  description = "Number of days before transitioning to Glacier storage class"
  type        = number
  default     = 90

  validation {
    condition     = var.s3_lifecycle_glacier_days >= 30
    error_message = "Glacier transition must be at least 30 days"
  }
}

variable "s3_lifecycle_deep_archive_days" {
  description = "Number of days before transitioning to Deep Archive storage class"
  type        = number
  default     = 365

  validation {
    condition     = var.s3_lifecycle_deep_archive_days >= 90
    error_message = "Deep Archive transition must be at least 90 days"
  }
}

variable "s3_intelligent_tiering_enabled" {
  description = "Enable S3 Intelligent-Tiering for automatic cost optimization"
  type        = bool
  default     = false
}

# ============================================================================
# MONITORING & ALERTING CONFIGURATION
# ============================================================================

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications (leave empty to skip)"
  type        = string
  default     = ""

  validation {
    condition     = var.alert_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Must be a valid email address or empty string"
  }
}

variable "alert_slack_webhook" {
  description = "Slack webhook URL for notifications (leave empty to skip)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "cloudwatch_log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudwatch_log_retention_days)
    error_message = "Log retention must be a valid CloudWatch Logs retention period"
  }
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing for Lambda functions"
  type        = bool
  default     = true
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring (1-minute metrics)"
  type        = bool
  default     = true
}

variable "lambda_error_rate_threshold_percent" {
  description = "Threshold for Lambda error rate alarm (percentage)"
  type        = number
  default     = 5

  validation {
    condition     = var.lambda_error_rate_threshold_percent >= 0 && var.lambda_error_rate_threshold_percent <= 100
    error_message = "Error rate threshold must be between 0 and 100 percent"
  }
}

variable "kinesis_iterator_age_threshold_seconds" {
  description = "Threshold for Kinesis iterator age alarm (seconds)"
  type        = number
  default     = 60

  validation {
    condition     = var.kinesis_iterator_age_threshold_seconds >= 0
    error_message = "Iterator age threshold must be non-negative"
  }
}

variable "dlq_message_threshold" {
  description = "Threshold for DLQ message count alarm"
  type        = number
  default     = 10

  validation {
    condition     = var.dlq_message_threshold >= 0
    error_message = "DLQ threshold must be non-negative"
  }
}

# ============================================================================
# STEP FUNCTIONS CONFIGURATION
# ============================================================================

variable "enable_daily_aggregation" {
  description = "Enable daily aggregation Step Functions state machine"
  type        = bool
  default     = true
}

variable "daily_aggregation_schedule" {
  description = "Cron expression for daily aggregation (UTC)"
  type        = string
  default     = "cron(0 0 * * ? *)"  # Daily at midnight UTC
}

variable "enable_weekly_reporting" {
  description = "Enable weekly reporting Step Functions state machine"
  type        = bool
  default     = true
}

variable "weekly_reporting_schedule" {
  description = "Cron expression for weekly reporting (UTC)"
  type        = string
  default     = "cron(0 0 ? * SUN *)"  # Weekly on Sunday at midnight UTC
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

variable "kms_key_rotation_enabled" {
  description = "Enable automatic KMS key rotation"
  type        = bool
  default     = true
}

variable "kms_key_deletion_window_days" {
  description = "Number of days before KMS key deletion (7-30)"
  type        = number
  default     = 30

  validation {
    condition     = var.kms_key_deletion_window_days >= 7 && var.kms_key_deletion_window_days <= 30
    error_message = "Deletion window must be between 7 and 30 days"
  }
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services (requires VPC configuration)"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID for VPC endpoints (only used if enable_vpc_endpoints is true)"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for VPC endpoints"
  type        = list(string)
  default     = []
}

# ============================================================================
# COST OPTIMIZATION CONFIGURATION
# ============================================================================

variable "enable_cost_allocation_tags" {
  description = "Enable cost allocation tags for all resources"
  type        = bool
  default     = true
}

variable "cost_center" {
  description = "Cost center identifier for billing"
  type        = string
  default     = "engineering"
}

variable "owner" {
  description = "Owner or team responsible for the infrastructure"
  type        = string
  default     = "data-platform-team"
}

# ============================================================================
# TAGS
# ============================================================================

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default = {
    Terraform   = "true"
    Application = "real-time-analytics"
    Repository  = "training-cloud-data"
  }
}
