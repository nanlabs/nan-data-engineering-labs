# Real-Time Analytics Platform - Terraform Variables
# TODO: Complete variable definitions with appropriate defaults and validation

# =============================================================================
# PROJECT CONFIGURATION
# =============================================================================

variable "project_name" {
  description = "Name of the project, used for resource naming"
  type        = string
  default     = "ride-analytics"

  # TODO: Add validation to ensure project name follows naming conventions
  # validation {
  #   condition     = can(regex("^[a-z0-9-]+$", var.project_name))
  #   error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  # }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  # TODO: Add validation to restrict to valid environments
  # validation {
  #   condition     = contains(["dev", "staging", "prod"], var.environment)
  #   error_message = "Environment must be one of: dev, staging, prod."
  # }
}

# =============================================================================
# AWS CONFIGURATION
# =============================================================================

variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"

  # TODO: Add validation for valid AWS regions
  # validation {
  #   condition = can(regex("^(us|eu|ap|sa|ca|me|af)-(north|south|east|west|central|northeast|southeast|southwest)-[0-9]$", var.aws_region))
  #   error_message = "Must be a valid AWS region name."
  # }
}

# TODO: Add variable for AWS profile (optional)
# variable "aws_profile" {
#   description = "AWS CLI profile to use for authentication"
#   type        = string
#   default     = "default"
# }

# =============================================================================
# KINESIS CONFIGURATION
# =============================================================================

variable "kinesis_shard_count" {
  description = "Number of shards for Kinesis Data Stream"
  type        = number
  default     = 2

  # TODO: Add validation for shard count range
  # validation {
  #   condition     = var.kinesis_shard_count >= 1 && var.kinesis_shard_count <= 100
  #   error_message = "Kinesis shard count must be between 1 and 100."
  # }
}

variable "kinesis_retention_hours" {
  description = "Data retention period for Kinesis stream in hours"
  type        = number
  default     = 24

  # TODO: Add validation (must be between 24 and 8760 hours)
  # validation {
  #   condition     = var.kinesis_retention_hours >= 24 && var.kinesis_retention_hours <= 8760
  #   error_message = "Kinesis retention must be between 24 hours (1 day) and 8760 hours (365 days)."
  # }
}

variable "kinesis_stream_mode" {
  description = "Kinesis stream capacity mode: PROVISIONED or ON_DEMAND"
  type        = string
  default     = "PROVISIONED"

  # TODO: Add validation
  # validation {
  #   condition     = contains(["PROVISIONED", "ON_DEMAND"], var.kinesis_stream_mode)
  #   error_message = "Kinesis stream mode must be PROVISIONED or ON_DEMAND."
  # }
}

# =============================================================================
# DYNAMODB CONFIGURATION
# =============================================================================

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode: PROVISIONED or PAY_PER_REQUEST"
  type        = string
  default     = "PAY_PER_REQUEST"

  # TODO: Add validation
  # validation {
  #   condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.dynamodb_billing_mode)
  #   error_message = "DynamoDB billing mode must be PROVISIONED or PAY_PER_REQUEST."
  # }
}

# TODO: Add variables for provisioned capacity (only used if billing_mode is PROVISIONED)
# variable "dynamodb_read_capacity" {
#   description = "Provisioned read capacity units for DynamoDB tables"
#   type        = number
#   default     = 5
# }
#
# variable "dynamodb_write_capacity" {
#   description = "Provisioned write capacity units for DynamoDB tables"
#   type        = number
#   default     = 5
# }

variable "enable_dynamodb_pitr" {
  description = "Enable point-in-time recovery for DynamoDB tables"
  type        = bool
  default     = true
}

variable "dynamodb_ttl_enabled" {
  description = "Enable TTL for DynamoDB tables"
  type        = bool
  default     = true
}

# =============================================================================
# S3 CONFIGURATION
# =============================================================================

variable "s3_versioning_enabled" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_encryption_type" {
  description = "S3 server-side encryption type: AES256 or aws:kms"
  type        = string
  default     = "AES256"

  # TODO: Add validation
  # validation {
  #   condition     = contains(["AES256", "aws:kms"], var.s3_encryption_type)
  #   error_message = "S3 encryption type must be AES256 or aws:kms."
  # }
}

# TODO: Add variable for S3 lifecycle policy days
# variable "s3_lifecycle_ia_days" {
#   description = "Number of days after which objects transition to Infrequent Access storage class"
#   type        = number
#   default     = 30
# }
#
# variable "s3_lifecycle_glacier_days" {
#   description = "Number of days after which objects transition to Glacier storage class"
#   type        = number
#   default     = 90
# }

# =============================================================================
# LAMBDA CONFIGURATION
# =============================================================================

variable "lambda_runtime" {
  description = "Lambda function runtime"
  type        = string
  default     = "python3.9"

  # TODO: Add validation for supported Python runtimes
}

variable "lambda_memory_size" {
  description = "Memory allocation for Lambda function in MB"
  type        = number
  default     = 512

  # TODO: Add validation (must be between 128 and 10240 in 1MB increments)
  # validation {
  #   condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
  #   error_message = "Lambda memory size must be between 128 MB and 10240 MB."
  # }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60

  # TODO: Add validation (max 900 seconds / 15 minutes)
  # validation {
  #   condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
  #   error_message = "Lambda timeout must be between 1 and 900 seconds."
  # }
}

variable "lambda_batch_size" {
  description = "Number of records to read from Kinesis per batch"
  type        = number
  default     = 100

  # TODO: Add validation (1-10000)
}

variable "lambda_max_retry_attempts" {
  description = "Maximum number of retry attempts for failed Lambda invocations"
  type        = number
  default     = 3

  # TODO: Add validation
}

# =============================================================================
# CLOUDWATCH CONFIGURATION
# =============================================================================

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 7

  # TODO: Add validation for valid retention periods
  # Valid values: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

# TODO: Add variable for alert email
# variable "alert_email" {
#   description = "Email address for CloudWatch alarm notifications"
#   type        = string
#   default     = ""
#
#   validation {
#     condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email)) || var.alert_email == ""
#     error_message = "Must be a valid email address or empty string."
#   }
# }

# =============================================================================
# GLUE CONFIGURATION
# =============================================================================

variable "glue_crawler_schedule" {
  description = "Cron expression for Glue crawler schedule"
  type        = string
  default     = "cron(0 * * * ? *)"  # Hourly

  # TODO: Add description of cron format for students
}

# =============================================================================
# TAGS CONFIGURATION
# =============================================================================

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "Real-Time Analytics Platform"
  }
}

# TODO: Add additional tags based on your organization's requirements
# variable "cost_center" {
#   description = "Cost center for billing purposes"
#   type        = string
#   default     = ""
# }
#
# variable "owner" {
#   description = "Owner of the resources"
#   type        = string
#   default     = ""
# }

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# TODO: Add feature flags for optional components

# variable "enable_dax" {
#   description = "Enable DynamoDB Accelerator (DAX) for caching"
#   type        = bool
#   default     = false
# }
#
# variable "enable_xray" {
#   description = "Enable AWS X-Ray tracing for Lambda"
#   type        = bool
#   default     = false
# }
#
# variable "enable_reserved_concurrency" {
#   description = "Enable reserved concurrency for Lambda function"
#   type        = bool
#   default     = false
# }
#
# variable "lambda_reserved_concurrency" {
#   description = "Number of concurrent executions reserved for Lambda (if enabled)"
#   type        = number
#   default     = 10
# }

# =============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# =============================================================================

# TODO: Create separate .tfvars files for each environment
# Example: dev.tfvars, staging.tfvars, prod.tfvars
#
# Usage:
# terraform plan -var-file=dev.tfvars
# terraform apply -var-file=prod.tfvars

# =============================================================================
# VALIDATION NOTES FOR STUDENTS
# =============================================================================

# IMPORTANT CONCEPTS:
# 1. Always validate user inputs to catch errors early
# 2. Provide clear error messages that guide users to fix issues
# 3. Use sensible defaults for development environments
# 4. Document the purpose and constraints of each variable
# 5. Group related variables together for better organization
# 6. Consider environment-specific values (dev vs prod)
#
# BEST PRACTICES:
# - Use descriptive variable names
# - Always include descriptions
# - Add validation rules where appropriate
# - Set conservative defaults for production safety
# - Document any dependencies between variables
# - Consider using variable type constraints (list, map, object)
#
# EXAMPLES OF ADVANCED VALIDATION:
#
# Complex object validation:
# variable "lambda_config" {
#   description = "Lambda function configuration"
#   type = object({
#     memory_size = number
#     timeout     = number
#     runtime     = string
#   })
#
#   validation {
#     condition     = var.lambda_config.memory_size >= 128 && var.lambda_config.timeout <= 900
#     error_message = "Invalid Lambda configuration."
#   }
# }
#
# List validation:
# variable "allowed_ips" {
#   description = "List of IP addresses allowed to access resources"
#   type        = list(string)
#   default     = []
#
#   validation {
#     condition     = alltrue([for ip in var.allowed_ips : can(regex("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$", ip))])
#     error_message = "All IPs must be in CIDR notation (e.g., 10.0.0.0/24)."
#   }
# }
