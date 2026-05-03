# ==================================================================================
# Terraform Backend Configuration
# ==================================================================================
# This file configures the Terraform backend for remote state storage and locking.
# Using S3 for state storage and DynamoDB for state locking ensures safe
# collaboration and prevents concurrent modifications.
# ==================================================================================

# ==================================================================================
# S3 Backend Configuration
# ==================================================================================
# IMPORTANT: Before using this backend configuration:
# 1. Create the S3 bucket manually or uncomment the resources below
# 2. Create the DynamoDB table manually or uncomment the resources below
# 3. Update the bucket name and dynamodb_table to match your setup
# 4. Run 'terraform init' to initialize the backend
# ==================================================================================

# Uncomment the terraform block below after creating the backend resources
/*
terraform {
  backend "s3" {
    # S3 bucket name for storing Terraform state
    # REPLACE WITH YOUR ACTUAL BUCKET NAME
    bucket = "your-org-terraform-state-cloudmart"

    # Path within the bucket where this project's state will be stored
    key = "cloudmart-data-lake/terraform.tfstate"

    # AWS region where the S3 bucket is located
    region = "us-east-1"

    # Enable encryption at rest for the state file
    encrypt = true

    # DynamoDB table name for state locking
    # REPLACE WITH YOUR ACTUAL TABLE NAME
    dynamodb_table = "terraform-state-lock-cloudmart"

    # Enable versioning to maintain state file history
    # This is configured on the S3 bucket itself
    # versioning = true
  }
}
*/

# ==================================================================================
# Backend Infrastructure Resources (Optional)
# ==================================================================================
# Uncomment these resources if you want Terraform to manage the backend resources.
# NOTE: This creates a chicken-and-egg problem. You'll need to:
# 1. First apply with local state (comment out the backend block above)
# 2. After resources are created, configure the backend and run 'terraform init'
# 3. Migrate the state when prompted
# ==================================================================================

/*
# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = "your-org-terraform-state-cloudmart"

  # Prevent accidental deletion of this bucket
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform State Bucket"
    Purpose     = "Infrastructure State Storage"
    Environment = "Global"
    ManagedBy   = "Terraform"
  }
}

# Enable versioning for state file history
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block all public access to the state bucket
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable lifecycle policy to manage old versions
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
    id     = "delete-incomplete-multipart-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "terraform-state-lock-cloudmart"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Prevent accidental deletion of this table
  lifecycle {
    prevent_destroy = true
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "Terraform State Lock Table"
    Purpose     = "State Locking"
    Environment = "Global"
    ManagedBy   = "Terraform"
  }
}
*/

# ==================================================================================
# Alternative: Local Backend (Default)
# ==================================================================================
# If you're working locally or in a single-user environment, Terraform will use
# a local backend by default (terraform.tfstate file in the current directory).
# No additional configuration is needed for local backend.
#
# Local backend is suitable for:
# - Development and testing
# - Single-user environments
# - Learning and experimentation
#
# For production or team environments, always use a remote backend (S3 + DynamoDB).
# ==================================================================================
