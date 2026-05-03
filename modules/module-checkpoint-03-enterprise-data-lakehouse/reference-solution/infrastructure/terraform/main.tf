# ============================================================================
# Enterprise Data Lakehouse - Main Terraform Configuration
# ============================================================================
# Purpose: Primary infrastructure setup for multi-zone data lakehouse
# Components: VPC, S3, KMS, Glue, Lake Formation, Security, Monitoring
# ============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.region

  default_tags {
    tags = merge(
      var.common_tags,
      {
        Project     = var.project_name
        Environment = var.environment
        ManagedBy   = "Terraform"
        Repository  = "training-cloud-data"
        Module      = "checkpoint-03-enterprise-data-lakehouse"
        CostCenter  = var.cost_center
        CreatedDate = timestamp()
      }
    )
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# ============================================================================
# Random Resources for Unique Naming
# ============================================================================

resource "random_id" "suffix" {
  byte_length = 4
}

resource "random_string" "kms_alias_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ============================================================================
# VPC Configuration
# ============================================================================

resource "aws_vpc" "lakehouse" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.lakehouse.id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = var.public_subnet_count
  vpc_id                  = aws_vpc.lakehouse.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-subnet-${count.index + 1}"
    Tier = "Public"
  }
}

# Private Subnets (for EMR and Data Processing)
resource "aws_subnet" "private" {
  count             = var.private_subnet_count
  vpc_id            = aws_vpc.lakehouse.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + var.public_subnet_count)
  availability_zone = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]

  tags = {
    Name = "${var.project_name}-${var.environment}-private-subnet-${count.index + 1}"
    Tier = "Private"
  }
}

# Data Subnets (isolated for sensitive workloads)
resource "aws_subnet" "data" {
  count             = var.data_subnet_count
  vpc_id            = aws_vpc.lakehouse.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + var.public_subnet_count + var.private_subnet_count)
  availability_zone = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]

  tags = {
    Name = "${var.project_name}-${var.environment}-data-subnet-${count.index + 1}"
    Tier = "Data"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : var.private_subnet_count) : 0
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : var.private_subnet_count) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index % length(aws_subnet.public)].id

  tags = {
    Name = "${var.project_name}-${var.environment}-nat-gw-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lakehouse.id

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables
resource "aws_route_table" "private" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : var.private_subnet_count) : 1
  vpc_id = aws_vpc.lakehouse.id

  tags = {
    Name = "${var.project_name}-${var.environment}-private-rt-${count.index + 1}"
  }
}

resource "aws_route" "private_nat" {
  count                  = var.enable_nat_gateway ? length(aws_route_table.private) : 0
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index % length(aws_route_table.private)].id
}

# Data Route Tables (no NAT, only VPC endpoints)
resource "aws_route_table" "data" {
  count  = var.data_subnet_count
  vpc_id = aws_vpc.lakehouse.id

  tags = {
    Name = "${var.project_name}-${var.environment}-data-rt-${count.index + 1}"
  }
}

resource "aws_route_table_association" "data" {
  count          = length(aws_subnet.data)
  subnet_id      = aws_subnet.data[count.index].id
  route_table_id = aws_route_table.data[count.index].id
}

# ============================================================================
# VPC Endpoints (Gateway and Interface)
# ============================================================================

# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.lakehouse.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id,
    aws_route_table.data[*].id
  )

  tags = {
    Name = "${var.project_name}-${var.environment}-s3-endpoint"
  }
}

# DynamoDB Gateway Endpoint
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.lakehouse.id
  service_name      = "com.amazonaws.${var.region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id,
    aws_route_table.data[*].id
  )

  tags = {
    Name = "${var.project_name}-${var.environment}-dynamodb-endpoint"
  }
}

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.project_name}-${var.environment}-vpce-"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.lakehouse.id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-vpce-sg"
  }
}

# Glue Interface Endpoint
resource "aws_vpc_endpoint" "glue" {
  vpc_id              = aws_vpc.lakehouse.id
  service_name        = "com.amazonaws.${var.region}.glue"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-glue-endpoint"
  }
}

# STS Interface Endpoint
resource "aws_vpc_endpoint" "sts" {
  vpc_id              = aws_vpc.lakehouse.id
  service_name        = "com.amazonaws.${var.region}.sts"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-sts-endpoint"
  }
}

# CloudWatch Logs Interface Endpoint
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.lakehouse.id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-logs-endpoint"
  }
}

# CloudWatch Monitoring Interface Endpoint
resource "aws_vpc_endpoint" "monitoring" {
  vpc_id              = aws_vpc.lakehouse.id
  service_name        = "com.amazonaws.${var.region}.monitoring"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-monitoring-endpoint"
  }
}

# ============================================================================
# KMS Keys for Encryption
# ============================================================================

# Data Encryption Key
resource "aws_kms_key" "data" {
  description             = "KMS key for data lakehouse encryption"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-${var.environment}-data-key"
  }
}

resource "aws_kms_alias" "data" {
  name          = "alias/${var.project_name}-${var.environment}-data-${random_string.kms_alias_suffix.result}"
  target_key_id = aws_kms_key.data.key_id
}

# Catalog Encryption Key
resource "aws_kms_key" "catalog" {
  description             = "KMS key for Glue Data Catalog encryption"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-${var.environment}-catalog-key"
  }
}

resource "aws_kms_alias" "catalog" {
  name          = "alias/${var.project_name}-${var.environment}-catalog-${random_string.kms_alias_suffix.result}"
  target_key_id = aws_kms_key.catalog.key_id
}

# Logs Encryption Key
resource "aws_kms_key" "logs" {
  description             = "KMS key for CloudWatch Logs encryption"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-logs-key"
  }
}

resource "aws_kms_alias" "logs" {
  name          = "alias/${var.project_name}-${var.environment}-logs-${random_string.kms_alias_suffix.result}"
  target_key_id = aws_kms_key.logs.key_id
}

# ============================================================================
# S3 Buckets - Data Lake Zones
# ============================================================================

# Raw Zone Bucket
resource "aws_s3_bucket" "raw" {
  bucket = "${var.project_name}-${var.environment}-raw-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-raw"
    Zone = "raw"
  }
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket = aws_s3_bucket.raw.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    id     = "transition-to-intelligent-tiering"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.s3_noncurrent_version_expiration
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

resource "aws_s3_bucket_logging" "raw" {
  bucket = aws_s3_bucket.raw.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/raw/"
}

# Bronze Zone Bucket
resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-${var.environment}-bronze-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-bronze"
    Zone = "bronze"
  }
}

resource "aws_s3_bucket_versioning" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER_IR"
    }
  }

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.s3_noncurrent_version_expiration
    }
  }
}

resource "aws_s3_bucket_logging" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/bronze/"
}

# Silver Zone Bucket
resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-${var.environment}-silver-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-silver"
    Zone = "silver"
  }
}

resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "silver" {
  bucket = aws_s3_bucket.silver.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 60
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.s3_noncurrent_version_expiration
    }
  }
}

resource "aws_s3_bucket_logging" "silver" {
  bucket = aws_s3_bucket.silver.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/silver/"
}

# Gold Zone Bucket
resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-${var.environment}-gold-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-gold"
    Zone = "gold"
  }
}

resource "aws_s3_bucket_versioning" "gold" {
  bucket = aws_s3_bucket.gold.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "gold" {
  bucket = aws_s3_bucket.gold.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.s3_noncurrent_version_expiration
    }
  }
}

resource "aws_s3_bucket_logging" "gold" {
  bucket = aws_s3_bucket.gold.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/gold/"
}

# Cross-Region Replication for Gold Bucket (optional)
resource "aws_s3_bucket" "gold_replica" {
  count  = var.enable_cross_region_replication ? 1 : 0
  bucket = "${var.project_name}-${var.environment}-gold-replica-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  provider = aws.replica

  tags = {
    Name = "${var.project_name}-${var.environment}-gold-replica"
    Zone = "gold-replica"
  }
}

resource "aws_s3_bucket_versioning" "gold_replica" {
  count  = var.enable_cross_region_replication ? 1 : 0
  bucket = aws_s3_bucket.gold_replica[0].id

  provider = aws.replica

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_replication_configuration" "gold" {
  count = var.enable_cross_region_replication ? 1 : 0

  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.gold.id

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.gold_replica[0].arn
      storage_class = "STANDARD_IA"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.data.arn
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.gold]
}

# Logs Bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-${var.environment}-logs-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.logs.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-logs"
    status = "Enabled"

    expiration {
      days = var.logs_retention_days
    }
  }
}

# Scripts Bucket
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project_name}-${var.environment}-scripts-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-scripts"
  }
}

resource "aws_s3_bucket_versioning" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# IAM Roles for S3 Replication
# ============================================================================

resource "aws_iam_role" "replication" {
  count = var.enable_cross_region_replication ? 1 : 0
  name  = "${var.project_name}-${var.environment}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "replication" {
  count = var.enable_cross_region_replication ? 1 : 0
  role  = aws_iam_role.replication[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.gold.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${aws_s3_bucket.gold.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = "${aws_s3_bucket.gold_replica[0].arn}/*"
      }
    ]
  })
}

# ============================================================================
# Glue Data Catalog Databases
# ============================================================================

resource "aws_glue_catalog_database" "raw" {
  name        = "${var.project_name}_${var.environment}_raw"
  description = "Raw layer - ingested data in original format"

  catalog_id = data.aws_caller_identity.current.account_id

  location_uri = "s3://${aws_s3_bucket.raw.bucket}/"
}

resource "aws_glue_catalog_database" "bronze" {
  name        = "${var.project_name}_${var.environment}_bronze"
  description = "Bronze layer - validated and deduplicated data"

  catalog_id = data.aws_caller_identity.current.account_id

  location_uri = "s3://${aws_s3_bucket.bronze.bucket}/"
}

resource "aws_glue_catalog_database" "silver" {
  name        = "${var.project_name}_${var.environment}_silver"
  description = "Silver layer - cleansed and conformed data"

  catalog_id = data.aws_caller_identity.current.account_id

  location_uri = "s3://${aws_s3_bucket.silver.bucket}/"
}

resource "aws_glue_catalog_database" "gold" {
  name        = "${var.project_name}_${var.environment}_gold"
  description = "Gold layer - business-level aggregates and features"

  catalog_id = data.aws_caller_identity.current.account_id

  location_uri = "s3://${aws_s3_bucket.gold.bucket}/"
}

# ============================================================================
# Lake Formation Configuration
# ============================================================================

# Lake Formation Data Lake Settings
resource "aws_lakeformation_data_lake_settings" "main" {
  admins = [aws_iam_role.lakeformation_admin.arn]

  create_database_default_permissions {
    permissions = []
    principal   = []
  }

  create_table_default_permissions {
    permissions = []
    principal   = []
  }
}

# Lake Formation Admin Role
resource "aws_iam_role" "lakeformation_admin" {
  name = "${var.project_name}-${var.environment}-lakeformation-admin"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lakeformation.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
      {
        Effect = "Allow"
        Principal = {
          AWS = data.aws_caller_identity.current.arn
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lakeformation_admin" {
  role       = aws_iam_role.lakeformation_admin.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLakeFormationDataAdmin"
}

# Register S3 Locations with Lake Formation
resource "aws_lakeformation_resource" "raw" {
  arn = aws_s3_bucket.raw.arn

  depends_on = [aws_lakeformation_data_lake_settings.main]
}

resource "aws_lakeformation_resource" "bronze" {
  arn = aws_s3_bucket.bronze.arn

  depends_on = [aws_lakeformation_data_lake_settings.main]
}

resource "aws_lakeformation_resource" "silver" {
  arn = aws_s3_bucket.silver.arn

  depends_on = [aws_lakeformation_data_lake_settings.main]
}

resource "aws_lakeformation_resource" "gold" {
  arn = aws_s3_bucket.gold.arn

  depends_on = [aws_lakeformation_data_lake_settings.main]
}

# Lake Formation Database Permissions
resource "aws_lakeformation_permissions" "raw_database" {
  principal   = aws_iam_role.glue_service.arn
  permissions = ["CREATE_TABLE", "ALTER", "DROP"]

  database {
    name       = aws_glue_catalog_database.raw.name
    catalog_id = data.aws_caller_identity.current.account_id
  }
}

resource "aws_lakeformation_permissions" "bronze_database" {
  principal   = aws_iam_role.glue_service.arn
  permissions = ["CREATE_TABLE", "ALTER", "DROP"]

  database {
    name       = aws_glue_catalog_database.bronze.name
    catalog_id = data.aws_caller_identity.current.account_id
  }
}

resource "aws_lakeformation_permissions" "silver_database" {
  principal   = aws_iam_role.glue_service.arn
  permissions = ["CREATE_TABLE", "ALTER", "DROP"]

  database {
    name       = aws_glue_catalog_database.silver.name
    catalog_id = data.aws_caller_identity.current.account_id
  }
}

resource "aws_lakeformation_permissions" "gold_database" {
  principal   = aws_iam_role.glue_service.arn
  permissions = ["CREATE_TABLE", "ALTER", "DROP"]

  database {
    name       = aws_glue_catalog_database.gold.name
    catalog_id = data.aws_caller_identity.current.account_id
  }
}

# ============================================================================
# IAM Role for Glue Service
# ============================================================================

resource "aws_iam_role" "glue_service" {
  name = "${var.project_name}-${var.environment}-glue-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-s3-access"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.raw.arn}/*",
          "${aws_s3_bucket.bronze.arn}/*",
          "${aws_s3_bucket.silver.arn}/*",
          "${aws_s3_bucket.gold.arn}/*",
          "${aws_s3_bucket.scripts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          aws_s3_bucket.bronze.arn,
          aws_s3_bucket.silver.arn,
          aws_s3_bucket.gold.arn,
          aws_s3_bucket.scripts.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.data.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"]
      }
    ]
  })
}

# ============================================================================
# Security Groups for EMR
# ============================================================================

resource "aws_security_group" "emr_master" {
  name_prefix = "${var.project_name}-${var.environment}-emr-master-"
  description = "Security group for EMR master nodes"
  vpc_id      = aws_vpc.lakehouse.id

  ingress {
    description     = "Allow from EMR workers"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.emr_worker.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-master-sg"
  }
}

resource "aws_security_group" "emr_worker" {
  name_prefix = "${var.project_name}-${var.environment}-emr-worker-"
  description = "Security group for EMR worker nodes"
  vpc_id      = aws_vpc.lakehouse.id

  ingress {
    description     = "Allow from EMR master"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.emr_master.id]
  }

  ingress {
    description = "Allow from other workers"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-worker-sg"
  }
}

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

resource "aws_cloudwatch_log_group" "glue_jobs" {
  name              = "/aws/glue/jobs/${var.project_name}-${var.environment}"
  retention_in_days = var.logs_retention_days
  kms_key_id        = aws_kms_key.logs.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-glue-jobs"
  }
}

resource "aws_cloudwatch_log_group" "glue_crawlers" {
  name              = "/aws/glue/crawlers/${var.project_name}-${var.environment}"
  retention_in_days = var.logs_retention_days
  kms_key_id        = aws_kms_key.logs.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-glue-crawlers"
  }
}

resource "aws_cloudwatch_log_group" "emr_serverless" {
  name              = "/aws/emr-serverless/${var.project_name}-${var.environment}"
  retention_in_days = var.logs_retention_days
  kms_key_id        = aws_kms_key.logs.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-serverless"
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}"
  retention_in_days = var.logs_retention_days
  kms_key_id        = aws_kms_key.logs.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda"
  }
}

# ============================================================================
# SNS Topics for Alerts
# ============================================================================

resource "aws_sns_topic" "alerts" {
  name              = "${var.project_name}-${var.environment}-alerts"
  display_name      = "Data Lakehouse Alerts"
  kms_master_key_id = aws_kms_key.logs.id

  tags = {
    Name = "${var.project_name}-${var.environment}-alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sns_topic" "data_quality" {
  name              = "${var.project_name}-${var.environment}-data-quality"
  display_name      = "Data Quality Notifications"
  kms_master_key_id = aws_kms_key.logs.id

  tags = {
    Name = "${var.project_name}-${var.environment}-data-quality"
  }
}

resource "aws_sns_topic_subscription" "data_quality_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.data_quality.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "glue_job_failures" {
  alarm_name          = "${var.project_name}-${var.environment}-glue-job-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "AWS/Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors Glue job failures"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Name = "${var.project_name}-${var.environment}-glue-job-failures"
  }
}

resource "aws_cloudwatch_metric_alarm" "s3_4xx_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-s3-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors S3 4xx errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Name = "${var.project_name}-${var.environment}-s3-4xx-errors"
  }
}
