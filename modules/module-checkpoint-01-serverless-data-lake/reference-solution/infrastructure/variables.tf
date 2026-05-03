# ==================================================================================
# Variables for CloudMart Serverless Data Lake Infrastructure
# ==================================================================================
# This file defines all input variables used in the Terraform configuration.
# ==================================================================================

# ==================================================================================
# Project Configuration
# ==================================================================================

variable "project_name" {
  description = "Name of the project, used as a prefix for resource names"
  type        = string
  default     = "cloudmart-data-lake"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "CloudMart Data Lake"
    ManagedBy   = "Terraform"
    Owner       = "Data Engineering Team"
    CostCenter  = "Engineering"
    Application = "Data Lake"
  }
}

# ==================================================================================
# AWS Configuration
# ==================================================================================

variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"

  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be a valid region identifier (e.g., us-east-1)."
  }
}

# ==================================================================================
# S3 Configuration
# ==================================================================================

variable "s3_bucket_prefix" {
  description = "Prefix for S3 bucket names to ensure global uniqueness. Use your organization or account identifier."
  type        = string
  default     = "acme-corp"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.s3_bucket_prefix))
    error_message = "S3 bucket prefix must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "raw_data_bucket_name" {
  description = "Name for the raw data (Bronze zone) S3 bucket. If not specified, will be auto-generated."
  type        = string
  default     = ""
}

variable "processed_data_bucket_name" {
  description = "Name for the processed data (Silver zone) S3 bucket. If not specified, will be auto-generated."
  type        = string
  default     = ""
}

variable "curated_data_bucket_name" {
  description = "Name for the curated data (Gold zone) S3 bucket. If not specified, will be auto-generated."
  type        = string
  default     = ""
}

variable "enable_s3_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_enabled" {
  description = "Enable lifecycle policies for S3 buckets"
  type        = bool
  default     = true
}

variable "raw_data_retention_days" {
  description = "Number of days to retain raw data before expiration"
  type        = number
  default     = 365

  validation {
    condition     = var.raw_data_retention_days > 0
    error_message = "Retention days must be a positive number."
  }
}

# ==================================================================================
# Lambda Configuration
# ==================================================================================

variable "lambda_runtime" {
  description = "Runtime for Lambda functions"
  type        = string
  default     = "python3.11"

  validation {
    condition     = contains(["python3.9", "python3.10", "python3.11", "python3.12"], var.lambda_runtime)
    error_message = "Lambda runtime must be a supported Python version."
  }
}

variable "lambda_memory_mb" {
  description = "Memory allocation for Lambda functions in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_mb >= 128 && var.lambda_memory_mb <= 10240
    error_message = "Lambda memory must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout_seconds" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 300

  validation {
    condition     = var.lambda_timeout_seconds >= 1 && var.lambda_timeout_seconds <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_reserved_concurrent_executions" {
  description = "Number of reserved concurrent executions for Lambda functions. Set to -1 for no reservation."
  type        = number
  default     = -1
}

# ==================================================================================
# AWS Glue Configuration
# ==================================================================================

variable "glue_version" {
  description = "AWS Glue version to use for ETL jobs"
  type        = string
  default     = "4.0"

  validation {
    condition     = contains(["3.0", "4.0"], var.glue_version)
    error_message = "Glue version must be either 3.0 or 4.0."
  }
}

variable "glue_max_dpu" {
  description = "Maximum DPU (Data Processing Units) for Glue jobs"
  type        = number
  default     = 2

  validation {
    condition     = var.glue_max_dpu >= 2 && var.glue_max_dpu <= 100
    error_message = "Glue DPU must be between 2 and 100."
  }
}

variable "glue_worker_type" {
  description = "Type of predefined worker for Glue jobs (G.1X, G.2X, or G.025X)"
  type        = string
  default     = "G.1X"

  validation {
    condition     = contains(["G.1X", "G.2X", "G.025X"], var.glue_worker_type)
    error_message = "Glue worker type must be G.1X, G.2X, or G.025X."
  }
}

variable "glue_number_of_workers" {
  description = "Number of workers for Glue jobs"
  type        = number
  default     = 2

  validation {
    condition     = var.glue_number_of_workers >= 2
    error_message = "Number of Glue workers must be at least 2."
  }
}

variable "glue_job_timeout_minutes" {
  description = "Timeout for Glue jobs in minutes"
  type        = number
  default     = 60

  validation {
    condition     = var.glue_job_timeout_minutes >= 1
    error_message = "Glue job timeout must be at least 1 minute."
  }
}

variable "enable_glue_job_bookmarks" {
  description = "Enable job bookmarks for Glue ETL jobs to process incremental data"
  type        = bool
  default     = true
}

# ==================================================================================
# Athena Configuration
# ==================================================================================

variable "athena_output_bucket" {
  description = "S3 bucket name for Athena query results. If not specified, will be auto-generated."
  type        = string
  default     = ""
}

variable "athena_query_result_retention_days" {
  description = "Number of days to retain Athena query results"
  type        = number
  default     = 30

  validation {
    condition     = var.athena_query_result_retention_days > 0
    error_message = "Athena query result retention days must be a positive number."
  }
}

variable "athena_bytes_scanned_cutoff_per_query" {
  description = "The upper limit (cutoff) for the amount of bytes a single query in a workgroup is allowed to scan"
  type        = number
  default     = 10737418240 # 10 GB

  validation {
    condition     = var.athena_bytes_scanned_cutoff_per_query >= 0
    error_message = "Athena bytes scanned cutoff must be a non-negative number."
  }
}

# ==================================================================================
# CloudWatch Configuration
# ==================================================================================

variable "cloudwatch_log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.cloudwatch_log_retention_days)
    error_message = "CloudWatch log retention must be a valid value (1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653 days)."
  }
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

variable "lambda_error_threshold" {
  description = "Threshold for Lambda error count to trigger alarm"
  type        = number
  default     = 5

  validation {
    condition     = var.lambda_error_threshold > 0
    error_message = "Lambda error threshold must be a positive number."
  }
}

variable "alarm_evaluation_periods" {
  description = "Number of periods to evaluate for alarms"
  type        = number
  default     = 1

  validation {
    condition     = var.alarm_evaluation_periods >= 1
    error_message = "Alarm evaluation periods must be at least 1."
  }
}

# ==================================================================================
# SNS Configuration
# ==================================================================================

variable "alert_email" {
  description = "Email address for SNS notifications and alerts. Leave empty to skip email subscription."
  type        = string
  default     = ""

  validation {
    condition     = var.alert_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address or empty."
  }
}

variable "enable_sns_encryption" {
  description = "Enable encryption for SNS topics using AWS KMS"
  type        = bool
  default     = true
}

# ==================================================================================
# EventBridge Schedule Configuration
# ==================================================================================

variable "raw_crawler_schedule" {
  description = "Schedule expression for raw data crawler (EventBridge syntax)"
  type        = string
  default     = "rate(6 hours)"

  validation {
    condition     = can(regex("^(rate\\(.*\\)|cron\\(.*\\))$", var.raw_crawler_schedule))
    error_message = "Schedule must be a valid EventBridge rate or cron expression."
  }
}

variable "processed_crawler_schedule" {
  description = "Schedule expression for processed data crawler (EventBridge syntax)"
  type        = string
  default     = "cron(0 2 * * ? *)" # Daily at 2 AM UTC

  validation {
    condition     = can(regex("^(rate\\(.*\\)|cron\\(.*\\))$", var.processed_crawler_schedule))
    error_message = "Schedule must be a valid EventBridge rate or cron expression."
  }
}

variable "curated_crawler_schedule" {
  description = "Schedule expression for curated data crawler (EventBridge syntax)"
  type        = string
  default     = "cron(0 3 * * ? *)" # Daily at 3 AM UTC

  validation {
    condition     = can(regex("^(rate\\(.*\\)|cron\\(.*\\))$", var.curated_crawler_schedule))
    error_message = "Schedule must be a valid EventBridge rate or cron expression."
  }
}

variable "enable_crawler_schedules" {
  description = "Enable automatic scheduling for Glue crawlers"
  type        = bool
  default     = true
}

# ==================================================================================
# Security Configuration
# ==================================================================================

variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for all services"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit for all services"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of KMS key to use for encryption. If not specified, AWS managed keys will be used."
  type        = string
  default     = ""
}
