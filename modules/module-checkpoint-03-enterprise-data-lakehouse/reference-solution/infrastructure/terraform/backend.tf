# ============================================================================
# Terraform Backend Configuration
# ============================================================================
# Purpose: Remote state management with S3 and DynamoDB locking
# Workspaces: dev, staging, prod
# ============================================================================

# ============================================================================
# Backend Configuration (Uncomment after S3 bucket creation)
# ============================================================================

# terraform {
#   backend "s3" {
#     # S3 bucket for state storage (replace with your bucket name)
#     bucket = "terraform-state-enterprise-lakehouse"
#     key    = "lakehouse/terraform.tfstate"
#     region = "us-east-1"
#
#     # DynamoDB table for state locking
#     dynamodb_table = "terraform-state-lock-enterprise-lakehouse"
#
#     # Encryption at rest
#     encrypt = true
#
#     # KMS key for encryption (optional)
#     # kms_key_id = "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
#
#     # Workspace prefix for multi-environment support
#     workspace_key_prefix = "environments"
#
#     # Enable versioning
#     versioning = true
#   }
# }

# ============================================================================
# Backend Initialization Resources
# ============================================================================

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = "terraform-state-${var.project_name}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "Terraform State Bucket"
    Purpose     = "terraform-state"
    Environment = "global"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Enable versioning for state bucket
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for state bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to state bucket
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for state bucket
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  rule {
    id     = "transition-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }
  }
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-lock-${var.project_name}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "Terraform State Lock Table"
    Purpose     = "terraform-locking"
    Environment = "global"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# ============================================================================
# Backend Configuration Output
# ============================================================================

output "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "terraform_state_bucket_arn" {
  description = "ARN of the Terraform state bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "terraform_locks_table" {
  description = "DynamoDB table for Terraform state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "terraform_locks_table_arn" {
  description = "ARN of the DynamoDB locks table"
  value       = aws_dynamodb_table.terraform_locks.arn
}

output "backend_configuration_instructions" {
  description = "Instructions for configuring the backend"
  value = <<-EOT
    ==========================================================================
    TERRAFORM BACKEND CONFIGURATION
    ==========================================================================

    The following resources have been created for Terraform state management:

    1. S3 Bucket: ${aws_s3_bucket.terraform_state.bucket}
    2. DynamoDB Table: ${aws_dynamodb_table.terraform_locks.name}

    To enable remote state, uncomment the backend block in backend.tf and update:

    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.bucket}"
        key            = "lakehouse/terraform.tfstate"
        region         = "${var.region}"
        dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
        encrypt        = true
      }
    }

    Then run:
      terraform init -migrate-state

    ==========================================================================
    WORKSPACE MANAGEMENT
    ==========================================================================

    To use workspaces for multiple environments:

    # Create workspaces
    terraform workspace new dev
    terraform workspace new staging
    terraform workspace new prod

    # Switch between workspaces
    terraform workspace select dev
    terraform workspace select staging
    terraform workspace select prod

    # List workspaces
    terraform workspace list

    # Current workspace
    terraform workspace show

    ==========================================================================
    WORKSPACE-SPECIFIC CONFIGURATIONS
    ==========================================================================

    Create environment-specific .tfvars files:

    - environments/dev.tfvars
    - environments/staging.tfvars
    - environments/prod.tfvars

    Example usage:
      terraform workspace select dev
      terraform plan -var-file="environments/dev.tfvars"
      terraform apply -var-file="environments/dev.tfvars"

    ==========================================================================
  EOT
}

# ============================================================================
# Workspace-Specific Local File for Environment Variables
# ============================================================================

resource "local_file" "workspace_example_dev" {
  filename = "${path.module}/environments/dev.tfvars.example"

  content = <<-EOT
    # Development Environment Configuration
    project_name = "enterprise-lakehouse"
    environment  = "dev"
    region       = "us-east-1"

    # VPC Configuration
    vpc_cidr              = "10.0.0.0/16"
    public_subnet_count   = 2
    private_subnet_count  = 2
    data_subnet_count     = 1
    enable_nat_gateway    = true
    single_nat_gateway    = true

    # Glue Configuration
    glue_version         = "4.0"
    glue_worker_type     = "G.1X"
    glue_number_of_workers = 5

    # EMR Configuration
    emr_release_label         = "emr-6.15.0"
    emr_initial_executor_count = 2
    emr_executor_cpu          = "2 vCPU"
    emr_executor_memory       = "8 GB"
    emr_auto_stop_enabled     = true
    emr_idle_timeout_minutes  = 10

    # Monitoring
    alert_email = "dev-team@example.com"

    # Cost Optimization
    logs_retention_days = 7
    enable_cross_region_replication = false
    enable_emr_studio = false
  EOT
}

resource "local_file" "workspace_example_staging" {
  filename = "${path.module}/environments/staging.tfvars.example"

  content = <<-EOT
    # Staging Environment Configuration
    project_name = "enterprise-lakehouse"
    environment  = "staging"
    region       = "us-east-1"

    # VPC Configuration
    vpc_cidr              = "10.1.0.0/16"
    public_subnet_count   = 2
    private_subnet_count  = 3
    data_subnet_count     = 2
    enable_nat_gateway    = true
    single_nat_gateway    = false

    # Glue Configuration
    glue_version         = "4.0"
    glue_worker_type     = "G.2X"
    glue_number_of_workers = 10

    # EMR Configuration
    emr_release_label         = "emr-6.15.0"
    emr_initial_executor_count = 5
    emr_executor_cpu          = "4 vCPU"
    emr_executor_memory       = "16 GB"
    emr_auto_stop_enabled     = true
    emr_idle_timeout_minutes  = 15

    # Monitoring
    alert_email = "staging-ops@example.com"

    # Data Quality
    dq_critical_threshold = 95.0
    dq_warning_threshold  = 90.0

    # Retention
    logs_retention_days = 30
    enable_cross_region_replication = false
    enable_emr_studio = true
  EOT
}

resource "local_file" "workspace_example_prod" {
  filename = "${path.module}/environments/prod.tfvars.example"

  content = <<-EOT
    # Production Environment Configuration
    project_name = "enterprise-lakehouse"
    environment  = "prod"
    region       = "us-east-1"

    # VPC Configuration
    vpc_cidr              = "10.2.0.0/16"
    public_subnet_count   = 3
    private_subnet_count  = 3
    data_subnet_count     = 3
    enable_nat_gateway    = true
    single_nat_gateway    = false

    # Glue Configuration
    glue_version         = "4.0"
    glue_worker_type     = "G.2X"
    glue_number_of_workers = 20
    glue_max_concurrent_runs = 5

    # EMR Configuration
    emr_release_label         = "emr-6.15.0"
    emr_initial_executor_count = 10
    emr_executor_cpu          = "4 vCPU"
    emr_executor_memory       = "16 GB"
    emr_executor_disk         = "200 GB"
    emr_max_cpu               = "400 vCPU"
    emr_max_memory            = "1600 GB"
    emr_auto_stop_enabled     = true
    emr_idle_timeout_minutes  = 30

    # Monitoring
    alert_email = "production-ops@example.com"

    # Data Quality
    dq_critical_threshold = 98.0
    dq_warning_threshold  = 95.0

    # Retention and Backup
    logs_retention_days = 90
    s3_noncurrent_version_expiration = 180
    enable_cross_region_replication = true
    enable_emr_studio = true

    # Delta Lake
    delta_vacuum_retention_days = 30
    delta_auto_merge_schema = true
    delta_enable_cdf = true
  EOT
}

# ============================================================================
# Initialization Script
# ============================================================================

resource "local_file" "backend_init_script" {
  filename = "${path.module}/scripts/init-backend.sh"

  content = <<-EOT
    #!/bin/bash
    # =========================================================================
    # Terraform Backend Initialization Script
    # =========================================================================

    set -e

    echo "=========================================================================="
    echo "Terraform Backend Initialization"
    echo "=========================================================================="

    # Colors
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'

    # Variables
    STATE_BUCKET="${aws_s3_bucket.terraform_state.bucket}"
    LOCKS_TABLE="${aws_dynamodb_table.terraform_locks.name}"
    REGION="${var.region}"

    echo ""
    echo "Configuration:"
    echo "  State Bucket: $STATE_BUCKET"
    echo "  Locks Table: $LOCKS_TABLE"
    echo "  Region: $REGION"
    echo ""

    # Step 1: Verify AWS CLI
    echo -e "$${YELLOW}Step 1: Verifying AWS CLI...$${NC}"
    if ! command -v aws &> /dev/null; then
        echo "Error: AWS CLI is not installed"
        exit 1
    fi
    echo -e "$${GREEN}✓ AWS CLI found$${NC}"

    # Step 2: Verify S3 bucket
    echo -e "$${YELLOW}Step 2: Verifying S3 bucket...$${NC}"
    if aws s3 ls "s3://$STATE_BUCKET" --region "$REGION" &> /dev/null; then
        echo -e "$${GREEN}✓ S3 bucket exists$${NC}"
    else
        echo "Error: S3 bucket does not exist"
        exit 1
    fi

    # Step 3: Verify DynamoDB table
    echo -e "$${YELLOW}Step 3: Verifying DynamoDB table...$${NC}"
    if aws dynamodb describe-table --table-name "$LOCKS_TABLE" --region "$REGION" &> /dev/null; then
        echo -e "$${GREEN}✓ DynamoDB table exists$${NC}"
    else
        echo "Error: DynamoDB table does not exist"
        exit 1
    fi

    # Step 4: Uncomment backend configuration
    echo -e "$${YELLOW}Step 4: Enabling backend configuration...$${NC}"
    echo "Please manually uncomment the backend block in backend.tf"
    echo ""

    # Step 5: Initialize Terraform
    echo -e "$${YELLOW}Step 5: Ready to initialize Terraform$${NC}"
    echo "Run the following commands:"
    echo ""
    echo "  terraform init -migrate-state"
    echo ""

    # Step 6: Create workspaces
    echo -e "$${YELLOW}Step 6: Create workspaces (optional)$${NC}"
    echo "To create environment-specific workspaces:"
    echo ""
    echo "  terraform workspace new dev"
    echo "  terraform workspace new staging"
    echo "  terraform workspace new prod"
    echo ""

    echo "=========================================================================="
    echo -e "$${GREEN}Backend initialization verification complete!$${NC}"
    echo "=========================================================================="
  EOT

  file_permission = "0755"
}
