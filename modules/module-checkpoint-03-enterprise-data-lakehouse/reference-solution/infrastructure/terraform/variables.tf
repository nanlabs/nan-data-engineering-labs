# ============================================================================
# Terraform Variables - Enterprise Data Lakehouse
# ============================================================================
# Purpose: Define all configurable parameters for the infrastructure
# ============================================================================

# ============================================================================
# Project and Environment Variables
# ============================================================================

variable "project_name" {
  description = "Name of the project (used in resource naming)"
  type        = string
  default     = "enterprise-lakehouse"

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 30
    error_message = "Project name must be between 1 and 30 characters"
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

variable "region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.region))
    error_message = "Region must be a valid AWS region format (e.g., us-east-1)"
  }
}

variable "cost_center" {
  description = "Cost center for billing and tracking"
  type        = string
  default     = "data-engineering"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Terraform   = "true"
    Application = "data-lakehouse"
  }
}

# ============================================================================
# VPC and Network Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block"
  }
}

variable "public_subnet_count" {
  description = "Number of public subnets to create"
  type        = number
  default     = 2

  validation {
    condition     = var.public_subnet_count >= 1 && var.public_subnet_count <= 6
    error_message = "Public subnet count must be between 1 and 6"
  }
}

variable "private_subnet_count" {
  description = "Number of private subnets to create"
  type        = number
  default     = 3

  validation {
    condition     = var.private_subnet_count >= 1 && var.private_subnet_count <= 6
    error_message = "Private subnet count must be between 1 and 6"
  }
}

variable "data_subnet_count" {
  description = "Number of isolated data subnets to create"
  type        = number
  default     = 2

  validation {
    condition     = var.data_subnet_count >= 1 && var.data_subnet_count <= 6
    error_message = "Data subnet count must be between 1 and 6"
  }
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway for all private subnets"
  type        = bool
  default     = false
}

# ============================================================================
# S3 Bucket Configuration
# ============================================================================

variable "s3_noncurrent_version_expiration" {
  description = "Days until noncurrent object versions expire"
  type        = number
  default     = 90

  validation {
    condition     = var.s3_noncurrent_version_expiration >= 30 && var.s3_noncurrent_version_expiration <= 365
    error_message = "Noncurrent version expiration must be between 30 and 365 days"
  }
}

variable "enable_cross_region_replication" {
  description = "Enable cross-region replication for gold bucket"
  type        = bool
  default     = false
}

variable "logs_retention_days" {
  description = "CloudWatch logs retention in days"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.logs_retention_days)
    error_message = "Logs retention must be a valid CloudWatch retention value"
  }
}

# ============================================================================
# KMS Configuration
# ============================================================================

variable "kms_deletion_window" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 30

  validation {
    condition     = var.kms_deletion_window >= 7 && var.kms_deletion_window <= 30
    error_message = "KMS deletion window must be between 7 and 30 days"
  }
}

# ============================================================================
# Glue Configuration
# ============================================================================

variable "glue_version" {
  description = "AWS Glue version"
  type        = string
  default     = "4.0"

  validation {
    condition     = contains(["3.0", "4.0"], var.glue_version)
    error_message = "Glue version must be 3.0 or 4.0"
  }
}

variable "glue_worker_type" {
  description = "Type of Glue worker (G.1X, G.2X, G.4X, G.8X)"
  type        = string
  default     = "G.2X"

  validation {
    condition     = contains(["G.1X", "G.2X", "G.4X", "G.8X"], var.glue_worker_type)
    error_message = "Worker type must be G.1X, G.2X, G.4X, or G.8X"
  }
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 10

  validation {
    condition     = var.glue_number_of_workers >= 2 && var.glue_number_of_workers <= 100
    error_message = "Number of workers must be between 2 and 100"
  }
}

variable "glue_max_concurrent_runs" {
  description = "Maximum concurrent runs for Glue jobs"
  type        = number
  default     = 3

  validation {
    condition     = var.glue_max_concurrent_runs >= 1 && var.glue_max_concurrent_runs <= 10
    error_message = "Max concurrent runs must be between 1 and 10"
  }
}

variable "glue_max_retries" {
  description = "Maximum retries for failed Glue jobs"
  type        = number
  default     = 2

  validation {
    condition     = var.glue_max_retries >= 0 && var.glue_max_retries <= 10
    error_message = "Max retries must be between 0 and 10"
  }
}

variable "glue_job_timeout" {
  description = "Glue job timeout in minutes"
  type        = number
  default     = 120

  validation {
    condition     = var.glue_job_timeout >= 1 && var.glue_job_timeout <= 2880
    error_message = "Job timeout must be between 1 and 2880 minutes"
  }
}

variable "glue_crawler_schedule_raw" {
  description = "Cron schedule for raw crawler"
  type        = string
  default     = "cron(0 1 * * ? *)"
}

variable "glue_crawler_schedule_bronze" {
  description = "Cron schedule for bronze crawler"
  type        = string
  default     = "cron(0 3 * * ? *)"
}

variable "glue_crawler_schedule_silver" {
  description = "Cron schedule for silver crawler"
  type        = string
  default     = "cron(0 5 * * ? *)"
}

variable "glue_crawler_schedule_gold" {
  description = "Cron schedule for gold crawler"
  type        = string
  default     = "cron(0 7 * * ? *)"
}

# ============================================================================
# Glue Trigger Configuration
# ============================================================================

variable "enable_scheduled_triggers" {
  description = "Enable scheduled Glue triggers"
  type        = bool
  default     = true
}

variable "enable_conditional_triggers" {
  description = "Enable conditional Glue triggers"
  type        = bool
  default     = true
}

variable "enable_crawler_triggers" {
  description = "Enable crawler triggers"
  type        = bool
  default     = true
}

variable "raw_to_bronze_schedule" {
  description = "Schedule for raw to bronze job"
  type        = string
  default     = "cron(0 2 * * ? *)"
}

variable "data_quality_schedule" {
  description = "Schedule for data quality job"
  type        = string
  default     = "cron(0 8 * * ? *)"
}

variable "crawlers_schedule" {
  description = "Schedule for crawlers"
  type        = string
  default     = "cron(0 0 * * ? *)"
}

variable "workflow_max_concurrent_runs" {
  description = "Maximum concurrent workflow runs"
  type        = number
  default     = 1

  validation {
    condition     = var.workflow_max_concurrent_runs >= 1 && var.workflow_max_concurrent_runs <= 5
    error_message = "Workflow max concurrent runs must be between 1 and 5"
  }
}

# ============================================================================
# Data Quality Configuration
# ============================================================================

variable "dq_critical_threshold" {
  description = "Data quality critical threshold percentage"
  type        = number
  default     = 95.0

  validation {
    condition     = var.dq_critical_threshold >= 0 && var.dq_critical_threshold <= 100
    error_message = "DQ threshold must be between 0 and 100"
  }
}

variable "dq_warning_threshold" {
  description = "Data quality warning threshold percentage"
  type        = number
  default     = 90.0

  validation {
    condition     = var.dq_warning_threshold >= 0 && var.dq_warning_threshold <= 100
    error_message = "DQ threshold must be between 0 and 100"
  }
}

# ============================================================================
# ETL Job Configuration
# ============================================================================

variable "deduplication_keys" {
  description = "Comma-separated list of keys for deduplication"
  type        = string
  default     = "id,timestamp"
}

variable "partition_keys" {
  description = "Comma-separated list of partition keys"
  type        = string
  default     = "year,month,day"
}

variable "gold_aggregation_level" {
  description = "Aggregation level for gold layer (daily, weekly, monthly)"
  type        = string
  default     = "daily"

  validation {
    condition     = contains(["daily", "weekly", "monthly"], var.gold_aggregation_level)
    error_message = "Aggregation level must be daily, weekly, or monthly"
  }
}

variable "schema_evolution_auto_merge" {
  description = "Enable automatic schema merge on evolution"
  type        = bool
  default     = true
}

# ============================================================================
# Delta Lake Configuration
# ============================================================================

variable "delta_vacuum_retention_days" {
  description = "Delta Lake vacuum retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = var.delta_vacuum_retention_days >= 0 && var.delta_vacuum_retention_days <= 365
    error_message = "Vacuum retention must be between 0 and 365 days"
  }
}

variable "delta_auto_merge_schema" {
  description = "Enable Delta Lake automatic schema merge"
  type        = bool
  default     = true
}

variable "delta_enable_cdf" {
  description = "Enable Delta Lake Change Data Feed"
  type        = bool
  default     = true
}

# ============================================================================
# EMR Serverless Configuration
# ============================================================================

variable "emr_release_label" {
  description = "EMR release label"
  type        = string
  default     = "emr-6.15.0"

  validation {
    condition     = can(regex("^emr-[0-9]+\\.[0-9]+\\.[0-9]+$", var.emr_release_label))
    error_message = "EMR release label must be in format emr-X.Y.Z"
  }
}

variable "emr_initial_driver_count" {
  description = "Initial number of EMR drivers"
  type        = number
  default     = 1

  validation {
    condition     = var.emr_initial_driver_count >= 1 && var.emr_initial_driver_count <= 10
    error_message = "Driver count must be between 1 and 10"
  }
}

variable "emr_initial_executor_count" {
  description = "Initial number of EMR executors"
  type        = number
  default     = 2

  validation {
    condition     = var.emr_initial_executor_count >= 1 && var.emr_initial_executor_count <= 100
    error_message = "Executor count must be between 1 and 100"
  }
}

variable "emr_driver_cpu" {
  description = "Driver CPU cores (format: '4 vCPU')"
  type        = string
  default     = "4 vCPU"
}

variable "emr_driver_memory" {
  description = "Driver memory (format: '16 GB')"
  type        = string
  default     = "16 GB"
}

variable "emr_driver_disk" {
  description = "Driver disk size (format: '100 GB')"
  type        = string
  default     = "100 GB"
}

variable "emr_executor_cpu" {
  description = "Executor CPU cores (format: '4 vCPU')"
  type        = string
  default     = "4 vCPU"
}

variable "emr_executor_memory" {
  description = "Executor memory (format: '16 GB')"
  type        = string
  default     = "16 GB"
}

variable "emr_executor_disk" {
  description = "Executor disk size (format: '100 GB')"
  type        = string
  default     = "100 GB"
}

variable "emr_executor_cores" {
  description = "Number of cores per executor"
  type        = number
  default     = 4

  validation {
    condition     = var.emr_executor_cores >= 1 && var.emr_executor_cores <= 16
    error_message = "Executor cores must be between 1 and 16"
  }
}

variable "emr_executor_instances" {
  description = "Number of executor instances"
  type        = number
  default     = 10

  validation {
    condition     = var.emr_executor_instances >= 1 && var.emr_executor_instances <= 100
    error_message = "Executor instances must be between 1 and 100"
  }
}

variable "emr_max_cpu" {
  description = "Maximum CPU for EMR application (format: '200 vCPU')"
  type        = string
  default     = "200 vCPU"
}

variable "emr_max_memory" {
  description = "Maximum memory for EMR application (format: '800 GB')"
  type        = string
  default     = "800 GB"
}

variable "emr_max_disk" {
  description = "Maximum disk for EMR application (format: '2000 GB')"
  type        = string
  default     = "2000 GB"
}

variable "emr_auto_start_enabled" {
  description = "Enable EMR auto-start"
  type        = bool
  default     = true
}

variable "emr_auto_stop_enabled" {
  description = "Enable EMR auto-stop"
  type        = bool
  default     = true
}

variable "emr_idle_timeout_minutes" {
  description = "EMR idle timeout in minutes"
  type        = number
  default     = 15

  validation {
    condition     = var.emr_idle_timeout_minutes >= 1 && var.emr_idle_timeout_minutes <= 10080
    error_message = "Idle timeout must be between 1 and 10080 minutes"
  }
}

variable "emr_cpu_alarm_threshold" {
  description = "CPU utilization alarm threshold percentage"
  type        = number
  default     = 80

  validation {
    condition     = var.emr_cpu_alarm_threshold >= 0 && var.emr_cpu_alarm_threshold <= 100
    error_message = "CPU threshold must be between 0 and 100"
  }
}

variable "emr_memory_alarm_threshold" {
  description = "Memory utilization alarm threshold percentage"
  type        = number
  default     = 85

  validation {
    condition     = var.emr_memory_alarm_threshold >= 0 && var.emr_memory_alarm_threshold <= 100
    error_message = "Memory threshold must be between 0 and 100"
  }
}

# ============================================================================
# EMR Studio Configuration
# ============================================================================

variable "enable_emr_studio" {
  description = "Enable EMR Studio for interactive development"
  type        = bool
  default     = false
}

# ============================================================================
# Database Connection Configuration
# ============================================================================

variable "enable_rds_connection" {
  description = "Enable Glue connection to RDS"
  type        = bool
  default     = false
}

variable "rds_jdbc_url" {
  description = "JDBC URL for RDS connection"
  type        = string
  default     = ""
  sensitive   = true
}

variable "rds_username" {
  description = "RDS database username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "rds_password" {
  description = "RDS database password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_redshift_connection" {
  description = "Enable Glue connection to Redshift"
  type        = bool
  default     = false
}

variable "redshift_jdbc_url" {
  description = "JDBC URL for Redshift connection"
  type        = string
  default     = ""
  sensitive   = true
}

variable "redshift_username" {
  description = "Redshift username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "redshift_password" {
  description = "Redshift password"
  type        = string
  default     = ""
  sensitive   = true
}

# ============================================================================
# Monitoring and Alerting
# ============================================================================

variable "alert_email" {
  description = "Email address for alerts and notifications"
  type        = string
  default     = ""

  validation {
    condition     = var.alert_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address"
  }
}
