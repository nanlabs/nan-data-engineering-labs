# ==========================================
# Enterprise Data Lakehouse - Terraform Variables
# ==========================================
# Define all variables used in the Terraform configuration.
# Complete the TODOs and set appropriate default values.
# Override defaults using terraform.tfvars or environment variables.
# ==========================================

# ==========================================
# Project Configuration
# ==========================================

variable "project_name" {
  description = "Name of the project - used for resource naming and tagging"
  type        = string
  default     = "enterprise-lakehouse"

  # TODO: Validate project name format (lowercase, hyphens only)
  # validation {
  #   condition     = can(regex("^[a-z0-9-]+$", var.project_name))
  #   error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  # }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  # TODO: Add validation to ensure valid environment values
  # validation {
  #   condition     = contains(["dev", "staging", "prod"], var.environment)
  #   error_message = "Environment must be dev, staging, or prod."
  # }
}

variable "cost_center" {
  description = "Cost center for billing and tracking"
  type        = string
  default     = "data-engineering"

  # TODO: Add your organization's cost center
}

# ==========================================
# AWS Configuration
# ==========================================

variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"

  # TODO: Choose your preferred AWS region
  # Common options: us-east-1, us-west-2, eu-west-1, ap-southeast-1
}

variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
  default     = "default"

  # TODO: Set to your AWS CLI profile name
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
  default     = ""

  # TODO: Add your AWS account ID (12-digit number)
  # validation {
  #   condition     = can(regex("^[0-9]{12}$", var.account_id))
  #   error_message = "Account ID must be a 12-digit number."
  # }
}

# ==========================================
# S3 Bucket Configuration
# ==========================================

variable "enable_versioning" {
  description = "Enable versioning on S3 buckets"
  type        = bool
  default     = true

  # TODO: Set to false if you want to disable versioning (not recommended for production)
}

variable "enable_encryption" {
  description = "Enable server-side encryption on S3 buckets"
  type        = bool
  default     = true
}

variable "encryption_algorithm" {
  description = "Encryption algorithm for S3 buckets (AES256 or aws:kms)"
  type        = string
  default     = "AES256"

  # TODO: Change to "aws:kms" if you want to use KMS encryption
  # validation {
  #   condition     = contains(["AES256", "aws:kms"], var.encryption_algorithm)
  #   error_message = "Encryption algorithm must be AES256 or aws:kms."
  # }
}

variable "kms_key_id" {
  description = "KMS key ID for S3 bucket encryption (required if encryption_algorithm is aws:kms)"
  type        = string
  default     = ""

  # TODO: Add KMS key ARN if using KMS encryption
}

variable "lifecycle_transition_days" {
  description = "Number of days before transitioning objects to INTELLIGENT_TIERING"
  type        = number
  default     = 90

  # TODO: Adjust based on your data access patterns
}

variable "lifecycle_expiration_days" {
  description = "Number of days before expiring objects (0 to disable)"
  type        = number
  default     = 0

  # TODO: Set retention period for temporary data
}

# ==========================================
# Glue Configuration
# ==========================================

variable "glue_version" {
  description = "AWS Glue version to use for jobs"
  type        = string
  default     = "4.0"

  # TODO: Check latest available Glue version
  # Options: "2.0", "3.0", "4.0"
}

variable "glue_python_version" {
  description = "Python version for Glue jobs"
  type        = string
  default     = "3"

  # TODO: Ensure compatibility with your scripts
}

variable "glue_max_capacity" {
  description = "Maximum DPU capacity for Glue jobs"
  type        = number
  default     = 2.0

  # TODO: Adjust based on data volume and processing requirements
  # Minimum: 2 DPUs for standard jobs
}

variable "glue_timeout" {
  description = "Timeout for Glue jobs in minutes"
  type        = number
  default     = 60

  # TODO: Set appropriate timeout for your longest-running job
}

variable "glue_max_retries" {
  description = "Maximum number of retries for Glue job failures"
  type        = number
  default     = 1

  # TODO: Adjust retry strategy
}

variable "enable_glue_job_insights" {
  description = "Enable AWS Glue job insights for monitoring"
  type        = bool
  default     = true
}

variable "enable_glue_metrics" {
  description = "Enable metrics for Glue jobs"
  type        = bool
  default     = true
}

# ==========================================
# Kinesis Configuration
# ==========================================

variable "enable_streaming" {
  description = "Enable real-time streaming with Kinesis"
  type        = bool
  default     = false

  # TODO: Set to true when implementing Phase 8
}

variable "kinesis_shard_count" {
  description = "Number of shards for Kinesis Data Stream"
  type        = number
  default     = 1

  # TODO: Calculate based on throughput requirements
  # Each shard: 1 MB/s input, 2 MB/s output
}

variable "kinesis_retention_hours" {
  description = "Data retention period for Kinesis stream in hours"
  type        = number
  default     = 24

  # TODO: Adjust based on processing latency requirements (24-8760 hours)
}

variable "kinesis_stream_mode" {
  description = "Kinesis stream mode (PROVISIONED or ON_DEMAND)"
  type        = string
  default     = "PROVISIONED"

  # TODO: Choose ON_DEMAND for variable workloads
}

variable "firehose_buffer_size" {
  description = "Firehose buffer size in MB"
  type        = number
  default     = 5

  # TODO: Tune for latency vs efficiency (1-128 MB)
}

variable "firehose_buffer_interval" {
  description = "Firehose buffer interval in seconds"
  type        = number
  default     = 60

  # TODO: Tune for latency requirements (60-900 seconds)
}

# ==========================================
# Athena Configuration
# ==========================================

variable "athena_workgroup_name" {
  description = "Name for Athena workgroup"
  type        = string
  default     = "analytics"
}

variable "enable_athena_metrics" {
  description = "Enable CloudWatch metrics for Athena"
  type        = bool
  default     = true
}

variable "athena_bytes_scanned_cutoff" {
  description = "Maximum bytes scanned per query (0 for unlimited)"
  type        = number
  default     = 0

  # TODO: Set limit to control query costs
}

# ==========================================
# CloudWatch Configuration
# ==========================================

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 30

  # TODO: Adjust based on compliance requirements
  # Options: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, etc.
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

variable "alarm_evaluation_periods" {
  description = "Number of evaluation periods for CloudWatch alarms"
  type        = number
  default     = 1

  # TODO: Increase for less sensitive alerts
}

# ==========================================
# SNS Configuration
# ==========================================

variable "alert_email" {
  description = "Email address for pipeline alerts"
  type        = string
  default     = ""

  # TODO: Add your email address for notifications
  # validation {
  #   condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
  #   error_message = "Must be a valid email address."
  # }
}

variable "enable_slack_notifications" {
  description = "Enable Slack notifications via SNS"
  type        = bool
  default     = false

  # TODO: Set to true if integrating with Slack
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true

  # TODO: Add Slack webhook URL if enabled
}

# ==========================================
# Lake Formation Configuration
# ==========================================

variable "enable_lake_formation" {
  description = "Enable AWS Lake Formation for data governance"
  type        = bool
  default     = false

  # TODO: Set to true when implementing Phase 6
}

variable "lake_formation_admin_arn" {
  description = "ARN of Lake Formation administrator"
  type        = string
  default     = ""

  # TODO: Add IAM user/role ARN for Lake Formation admin
}

# ==========================================
# Step Functions Configuration
# ==========================================

variable "enable_step_functions" {
  description = "Enable Step Functions for orchestration"
  type        = bool
  default     = false

  # TODO: Set to true when implementing Phase 9
}

variable "step_functions_log_level" {
  description = "Log level for Step Functions (ALL, ERROR, FATAL, OFF)"
  type        = string
  default     = "ERROR"

  # TODO: Set to ALL for debugging
}

# ==========================================
# Networking Configuration (Optional)
# ==========================================

variable "enable_vpc" {
  description = "Create VPC for Glue jobs (recommended for production)"
  type        = bool
  default     = false

  # TODO: Set to true for production deployments
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  # TODO: Adjust if you have specific network requirements
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]

  # TODO: Update based on your AWS region
}

# ==========================================
# Data Processing Configuration
# ==========================================

variable "batch_size" {
  description = "Number of records to process per batch"
  type        = number
  default     = 10000

  # TODO: Tune based on data volume and memory constraints
}

variable "partition_columns" {
  description = "Default partition columns for data"
  type        = list(string)
  default     = ["year", "month", "day"]

  # TODO: Adjust partitioning strategy
}

variable "compression_type" {
  description = "Compression type for Parquet files"
  type        = string
  default     = "snappy"

  # TODO: Choose compression: snappy, gzip, lzo, zstd
}

# ==========================================
# Data Quality Configuration
# ==========================================

variable "enable_data_quality_checks" {
  description = "Enable data quality validation"
  type        = bool
  default     = true
}

variable "data_quality_threshold" {
  description = "Minimum data quality score (0.0 - 1.0)"
  type        = number
  default     = 0.95

  # TODO: Set acceptable quality threshold
  # validation {
  #   condition     = var.data_quality_threshold >= 0.0 && var.data_quality_threshold <= 1.0
  #   error_message = "Data quality threshold must be between 0.0 and 1.0."
  # }
}

# ==========================================
# Cost Optimization Configuration
# ==========================================

variable "enable_s3_intelligent_tiering" {
  description = "Enable S3 Intelligent-Tiering for cost optimization"
  type        = bool
  default     = true
}

variable "spot_instances_enabled" {
  description = "Use Spot instances for Glue jobs (cost savings)"
  type        = bool
  default     = false

  # TODO: Enable for non-critical jobs to save costs
}

variable "budget_alert_threshold" {
  description = "Monthly budget threshold in USD"
  type        = number
  default     = 100

  # TODO: Set your monthly budget limit
}

# ==========================================
# Tags Configuration
# ==========================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}

  # TODO: Add organization-specific tags
  # Example:
  # additional_tags = {
  #   Owner       = "data-team"
  #   Department  = "Engineering"
  #   Compliance  = "Required"
  # }
}

# ==========================================
# Feature Flags
# ==========================================

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "enable_cost_anomaly_detection" {
  description = "Enable AWS Cost Anomaly Detection"
  type        = bool
  default     = false

  # TODO: Enable for production to detect unexpected costs
}

# ==========================================
# NOTES:
# ==========================================
# 1. Create a terraform.tfvars file to override these defaults
# 2. Never commit sensitive values (passwords, keys) to Git
# 3. Use AWS Secrets Manager or Parameter Store for secrets
# 4. Document any custom variables you add
# 5. Use validation blocks to catch errors early
# 6. Group related variables for better organization
# ==========================================
