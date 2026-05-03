# ============================================================================
# TERRAFORM BACKEND CONFIGURATION - CHECKPOINT 02: REAL-TIME ANALYTICS PLATFORM
# ============================================================================
# This file configures the Terraform backend for remote state storage
# Using S3 for state file storage and DynamoDB for state locking
# ============================================================================

# NOTE: Before running terraform init, you must:
# 1. Create the S3 bucket for state storage
# 2. Create the DynamoDB table for state locking
# 3. Update the bucket name and region below

# ============================================================================
# S3 BACKEND FOR STATE STORAGE
# ============================================================================

terraform {
  backend "s3" {
    # S3 bucket for storing Terraform state
    # IMPORTANT: Replace with your actual bucket name
    bucket = "my-terraform-state-bucket-ACCOUNT_ID"

    # Key path within the bucket (unique per environment)
    key = "checkpoint-02/real-time-analytics/terraform.tfstate"

    # AWS region where the S3 bucket is located
    region = "us-east-1"

    # DynamoDB table for state locking (prevents concurrent operations)
    # IMPORTANT: Replace with your actual table name
    dynamodb_table = "terraform-state-lock"

    # Enable server-side encryption for state file
    encrypt = true

    # KMS key ID for encryption (optional - uses AWS managed key if not specified)
    # kms_key_id = "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"

    # Enable versioning for state file history
    # Note: Versioning must be enabled on the S3 bucket itself

    # Workspace prefix for multi-workspace setups (optional)
    # workspace_key_prefix = "workspaces"
  }
}

# ============================================================================
# BACKEND SETUP INSTRUCTIONS
# ============================================================================

# Step 1: Create S3 Bucket for State Storage
# -------------------------------------------
# Run this AWS CLI command (replace ACCOUNT_ID and REGION):
#
# aws s3api create-bucket \
#   --bucket my-terraform-state-bucket-ACCOUNT_ID \
#   --region us-east-1 \
#   --create-bucket-configuration LocationConstraint=us-east-1
#
# aws s3api put-bucket-versioning \
#   --bucket my-terraform-state-bucket-ACCOUNT_ID \
#   --versioning-configuration Status=Enabled
#
# aws s3api put-bucket-encryption \
#   --bucket my-terraform-state-bucket-ACCOUNT_ID \
#   --server-side-encryption-configuration '{
#     "Rules": [{
#       "ApplyServerSideEncryptionByDefault": {
#         "SSEAlgorithm": "AES256"
#       }
#     }]
#   }'
#
# aws s3api put-public-access-block \
#   --bucket my-terraform-state-bucket-ACCOUNT_ID \
#   --public-access-block-configuration \
#     "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Step 2: Create DynamoDB Table for State Locking
# ------------------------------------------------
# Run this AWS CLI command:
#
# aws dynamodb create-table \
#   --table-name terraform-state-lock \
#   --attribute-definitions AttributeName=LockID,AttributeType=S \
#   --key-schema AttributeName=LockID,KeyType=HASH \
#   --billing-mode PAY_PER_REQUEST \
#   --region us-east-1 \
#   --tags Key=Name,Value=terraform-state-lock \
#          Key=Purpose,Value=terraform-locking \
#          Key=ManagedBy,Value=manual

# Step 3: Initialize Terraform
# -----------------------------
# After creating the backend resources, run:
#
# terraform init
#
# This will:
# - Download required providers
# - Configure the S3 backend
# - Migrate any existing local state to S3 (if applicable)

# Step 4: Verify Backend Configuration
# -------------------------------------
# Check that state is stored remotely:
#
# aws s3 ls s3://my-terraform-state-bucket-ACCOUNT_ID/checkpoint-02/real-time-analytics/
#
# Check DynamoDB lock table:
#
# aws dynamodb describe-table --table-name terraform-state-lock

# ============================================================================
# ALTERNATIVE: LOCAL BACKEND (Development Only)
# ============================================================================
# For local development without remote state, comment out the backend "s3"
# block above and use local backend (default):
#
# terraform {
#   backend "local" {
#     path = "terraform.tfstate"
#   }
# }
#
# WARNING: Local backend is not recommended for production or team environments
# - No state locking
# - No collaboration support
# - Risk of state file loss
# - No encryption at rest

# ============================================================================
# MULTI-ENVIRONMENT SETUP
# ============================================================================
# For managing multiple environments (dev, staging, prod), use workspaces:
#
# Create workspaces:
# terraform workspace new dev
# terraform workspace new staging
# terraform workspace new prod
#
# Switch between workspaces:
# terraform workspace select dev
#
# List workspaces:
# terraform workspace list
#
# Current workspace:
# terraform workspace show
#
# State files will be stored at:
# s3://bucket/env:/WORKSPACE_NAME/key

# ============================================================================
# BACKEND MIGRATION
# ============================================================================
# To migrate from local to remote backend:
# 1. Configure the backend block above
# 2. Run: terraform init -migrate-state
# 3. Confirm the migration when prompted
#
# To migrate from remote back to local:
# 1. Comment out the backend "s3" block
# 2. Run: terraform init -migrate-state
# 3. Confirm the migration when prompted

# ============================================================================
# STATE FILE SECURITY BEST PRACTICES
# ============================================================================
# 1. Enable S3 bucket versioning (state file history)
# 2. Enable server-side encryption (AES256 or KMS)
# 3. Block public access to S3 bucket
# 4. Use IAM roles with least privilege access
# 5. Enable S3 bucket logging for audit trail
# 6. Enable MFA delete for production state files
# 7. Regularly backup state files
# 8. Use separate state files per environment
# 9. Never commit state files to version control
# 10. Use DynamoDB for state locking (prevent corruption)

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
# Error: "Failed to get existing workspaces"
# - Ensure S3 bucket exists and you have access
# - Verify AWS credentials are configured
# - Check S3 bucket permissions
#
# Error: "Error acquiring the state lock"
# - Another user is running terraform
# - Previous run crashed and left a lock
# - Manually remove lock from DynamoDB (use with caution):
#   aws dynamodb delete-item \
#     --table-name terraform-state-lock \
#     --key '{"LockID":{"S":"BUCKET/KEY"}}'
#
# Error: "NoSuchBucket"
# - S3 bucket doesn't exist
# - Bucket name is incorrect
# - Bucket is in a different region
#
# Error: "AccessDenied"
# - IAM permissions insufficient
# - Bucket policy blocks access
# - Check AWS credentials
