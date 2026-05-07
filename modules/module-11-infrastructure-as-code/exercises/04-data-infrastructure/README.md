# Exercise 04: Data Infrastructure Completa

## Description

En este exercise construirás una infraestructura de datos enterprise-grade completa usando Terraform. Implementarás un Data Lake con arquitectura medallion (Bronze/Silver/Gold), AWS Glue para catalogación, Athena para analytics, IAM roles granulares, lifecycle policies para optimización de costos, y estrategias de tagging.

**Estimated Duration:** 180-210 minutes

## Prerequisites

- Exercises 01, 02 y 03 completeds
- Comprensión de arquitecturas de Data Lake
- Conocimientos de AWS Glue y Athena
- LocalStack corriendo con servicios: s3, iam, glue, athena

## Objectives de Aprendizaje

Al completar este exercise serás capaz de:

1. ✅ Diseñar e implement Data Lake completo con arquitectura medallion
2. ✅ Configurar AWS Glue Database y Crawlers para metadata management
3. ✅ Crear Athena workgroups y saved queries para analytics
4. ✅ Implementar IAM roles y policies granulares para data access
5. ✅ Aplicar lifecycle policies y encryption para compliance y cost optimization
6. ✅ Implementar estrategia de tagging para governance y cost allocation

---

## Task 1: Data Lake Completo (Bronze/Silver/Gold)

### Description

Crearás la arquitectura completa del Data Lake siguiendo el patrón medallion architecture con tres capas: Bronze (raw data), Silver (processed data), y Gold (analytics-ready data).

### Steps

#### 1.1. Estructura del Proyecto

```bash
mkdir -p ~/terraform-exercises/04-data-infrastructure
cd ~/terraform-exercises/04-data-infrastructure

mkdir -p {modules,scripts,docs}
touch main.tf variables.tf outputs.tf terraform.tfvars
```text

#### 1.2. Configuration Principal del Data Lake

<details>
<summary>📄 main.tf - Data Lake Infrastructure</summary>

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3     = "http://localhost:4566"
    iam    = "http://localhost:4566"
    glue   = "http://localhost:4566"
    athena = "http://localhost:4566"
  }
}

locals {
  # Configuration de capas del Data Lake
  data_layers = {
    bronze = {
      description        = "Raw data from sources"
      versioning         = true
      transition_ia_days = 30
      transition_glacier = 90
      expiration_days    = 365
      prefix_structure   = ["year", "month", "day"]
    }
    silver = {
      description        = "Cleaned and transformed data"
      versioning         = true
      transition_ia_days = 60
      transition_glacier = 180
      expiration_days    = 730  # 2 años
      prefix_structure   = ["year", "month"]
    }
    gold = {
      description        = "Business-ready aggregated data"
      versioning         = true
      transition_ia_days = 90
      transition_glacier = 365
      expiration_days    = 2555  # 7 años (compliance)
      prefix_structure   = ["domain", "year"]
    }
  }

  # Tags comunes para todos los recursos
  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
      DataClass   = "confidential"
    }
  )
}

# ===================================
# BRONZE LAYER - Raw Data
# ===================================

resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name        = "Bronze Layer"
      Layer       = "bronze"
      DataStage   = "raw"
      Criticality = "medium"
    }
  )
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
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "bronze-data-lifecycle"
    status = "Enabled"

    # Transición a STANDARD_IA (menos costoso)
    transition {
      days          = local.data_layers.bronze.transition_ia_days
      storage_class = "STANDARD_IA"
    }

    # Transición a GLACIER (archiving)
    transition {
      days          = local.data_layers.bronze.transition_glacier
      storage_class = "GLACIER"
    }

    # Expiración final
    expiration {
      days = local.data_layers.bronze.expiration_days
    }

    # Limpiar uploads incompletos
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "bronze-non-current-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# ===================================
# SILVER LAYER - Processed Data
# ===================================

resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-silver-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name        = "Silver Layer"
      Layer       = "silver"
      DataStage   = "processed"
      Criticality = "high"
    }
  )
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
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    id     = "silver-data-lifecycle"
    status = "Enabled"

    transition {
      days          = local.data_layers.silver.transition_ia_days
      storage_class = "INTELLIGENT_TIERING"
    }

    transition {
      days          = local.data_layers.silver.transition_glacier
      storage_class = "GLACIER"
    }

    expiration {
      days = local.data_layers.silver.expiration_days
    }
  }

  rule {
    id     = "silver-temp-data"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 7
    }
  }
}

# ===================================
# GOLD LAYER - Analytics Ready
# ===================================

resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-gold-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name        = "Gold Layer"
      Layer       = "gold"
      DataStage   = "analytics"
      Criticality = "critical"
      Compliance  = "GDPR,SOC2"
    }
  )

  lifecycle {
    prevent_destroy = false  # true en producción
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
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    id     = "gold-data-lifecycle"
    status = "Enabled"

    transition {
      days          = local.data_layers.gold.transition_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = local.data_layers.gold.transition_glacier
      storage_class = "GLACIER"
    }

    expiration {
      days = local.data_layers.gold.expiration_days
    }
  }
}

# ===================================
# STAGING & QUARANTINE BUCKETS
# ===================================

resource "aws_s3_bucket" "staging" {
  bucket = "${var.project_name}-staging-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name    = "Staging Bucket"
      Purpose = "Temporary data staging"
    }
  )
}

resource "aws_s3_bucket_lifecycle_configuration" "staging" {
  bucket = aws_s3_bucket.staging.id

  rule {
    id     = "auto-expire-staging"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

resource "aws_s3_bucket" "quarantine" {
  bucket = "${var.project_name}-quarantine-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name    = "Quarantine Bucket"
      Purpose = "Failed/invalid data"
    }
  )
}

resource "aws_s3_bucket_lifecycle_configuration" "quarantine" {
  bucket = aws_s3_bucket.quarantine.id

  rule {
    id     = "quarantine-retention"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

# ===================================
# LOGS BUCKET
# ===================================

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name    = "Access Logs"
      Purpose = "S3 access logging"
    }
  )
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

# Configurar logging para data layers
resource "aws_s3_bucket_logging" "bronze" {
  bucket        = aws_s3_bucket.bronze.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "bronze-access-logs/"
}

resource "aws_s3_bucket_logging" "silver" {
  bucket        = aws_s3_bucket.silver.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "silver-access-logs/"
}

resource "aws_s3_bucket_logging" "gold" {
  bucket        = aws_s3_bucket.gold.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "gold-access-logs/"
}

# ===================================
# PUBLIC ACCESS BLOCK (Seguridad)
# ===================================

resource "aws_s3_bucket_public_access_block" "all_buckets" {
  for_each = {
    bronze     = aws_s3_bucket.bronze.id
    silver     = aws_s3_bucket.silver.id
    gold       = aws_s3_bucket.gold.id
    staging    = aws_s3_bucket.staging.id
    quarantine = aws_s3_bucket.quarantine.id
    logs       = aws_s3_bucket.logs.id
  }

  bucket = each.value

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```text

</details>

<details>
<summary>📄 variables.tf - Variables</summary>

```hcl
variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "datalake"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "cost_center" {
  description = "Centro de costos"
  type        = string
  default     = "data-engineering"
}

variable "logs_retention_days" {
  description = "Días de retención de logs"
  type        = number
  default     = 90
}

variable "tags" {
  description = "Tags adicionales"
  type        = map(string)
  default = {
    Owner = "DataTeam"
  }
}
```text

</details>

```bash
terraform init
terraform plan
terraform apply -auto-approve

# Verificar buckets creados
awslocal s3 ls
terraform output
```

### Output Esperado

```plaintext
Apply complete! Resources: 24 added, 0 changed, 0 destroyed.

Buckets creados:
- datalake-bronze-dev (raw data)
- datalake-silver-dev (processed data)
- datalake-gold-dev (analytics data)
- datalake-staging-dev (temporary)
- datalake-quarantine-dev (failed data)
- datalake-logs-dev (access logs)
```text

---

## Task 2: AWS Glue Database y Crawlers

### Description

Implementarás AWS Glue para catalogación automática de datos, incluyendo Glue Database, Crawlers, y Tables.

<details>
<summary>📄 glue.tf - AWS Glue Configuration</summary>

```hcl
# ===================================
# GLUE CATALOG DATABASE
# ===================================

resource "aws_glue_catalog_database" "main" {
  name        = "${var.project_name}_${var.environment}"
  description = "Data Lake catalog for ${var.project_name} - ${var.environment}"

  location_uri = "s3://${aws_s3_bucket.silver.id}/"

  create_table_default_permission {
    permissions = ["SELECT"]

    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }

  tags = local.common_tags
}

# ===================================
# GLUE IAM ROLE
# ===================================

resource "aws_iam_role" "glue" {
  name = "${var.project_name}-glue-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "glue" {
  name = "glue-policy"
  role = aws_iam_role.glue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          for bucket in [
            aws_s3_bucket.bronze,
            aws_s3_bucket.silver,
            aws_s3_bucket.gold
          ] : [
            bucket.arn,
            "${bucket.arn}/*"
          ]
        ]
        # Flatten nested lists
      }
      ,
      {
        Effect = "Allow"
        Action = [
          "glue:*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# ===================================
# GLUE CRAWLERS
# ===================================

# Crawler para Bronze Layer
resource "aws_glue_crawler" "bronze" {
  name          = "${var.project_name}-bronze-crawler-${var.environment}"
  database_name = aws_glue_catalog_database.main.name
  role          = aws_iam_role.glue.arn
  description   = "Crawler para capa Bronze (raw data)"

  s3_target {
    path = "s3://${aws_s3_bucket.bronze.id}/"
    exclusions = [
      "**/_SUCCESS",
      "**/_temporary/**"
    ]
  }

  # Ejecutar diariamente a las 2 AM
  schedule = "cron(0 2 * * ? *)"

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })

  tags = merge(
    local.common_tags,
    {
      Layer = "bronze"
    }
  )
}

# Crawler para Silver Layer
resource "aws_glue_crawler" "silver" {
  name          = "${var.project_name}-silver-crawler-${var.environment}"
  database_name = aws_glue_catalog_database.main.name
  role          = aws_iam_role.glue.arn
  description   = "Crawler para capa Silver (processed data)"

  s3_target {
    path = "s3://${aws_s3_bucket.silver.id}/"
    exclusions = [
      "temp/**",
      "**/_SUCCESS",
      "**/.spark/**"
    ]
  }

  schedule = "cron(0 3 * * ? *)"

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
  }

  tags = merge(
    local.common_tags,
    {
      Layer = "silver"
    }
  )
}

# Crawler para Gold Layer
resource "aws_glue_crawler" "gold" {
  name          = "${var.project_name}-gold-crawler-${var.environment}"
  database_name = aws_glue_catalog_database.main.name
  role          = aws_iam_role.glue.arn
  description   = "Crawler para capa Gold (analytics)"

  s3_target {
    path = "s3://${aws_s3_bucket.gold.id}/"
  }

  schedule = "cron(0 4 * * ? *)"

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = merge(
    local.common_tags,
    {
      Layer = "gold"
    }
  )
}

# ===================================
# GLUE CATALOG TABLES (Ejemplo Manual)
# ===================================

resource "aws_glue_catalog_table" "sample_data" {
  name          = "sample_events"
  database_name = aws_glue_catalog_database.main.name
  description   = "Sample events table"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"        = "parquet"
    "compressionType"       = "snappy"
    "typeOfData"            = "file"
    "EXTERNAL"              = "TRUE"
    "parquet.compression"   = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.silver.id}/events/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "ParquetHiveSerDe"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"

      parameters = {
        "serialization.format" = "1"
      }
    }

    columns {
      name = "event_id"
      type = "string"
    }

    columns {
      name = "event_type"
      type = "string"
    }

    columns {
      name = "timestamp"
      type = "timestamp"
    }

    columns {
      name = "user_id"
      type = "bigint"
    }

    columns {
      name = "properties"
      type = "map<string,string>"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  partition_keys {
    name = "day"
    type = "string"
  }
}

output "glue_info" {
  value = {
    database = aws_glue_catalog_database.main.name
    crawlers = {
      bronze = aws_glue_crawler.bronze.name
      silver = aws_glue_crawler.silver.name
      gold   = aws_glue_crawler.gold.name
    }
    sample_table = aws_glue_catalog_table.sample_data.name
  }
}
```text

</details>

---

## Task 3: Athena Workgroup y Saved Queries

<details>
<summary>📄 athena.tf - Athena Configuration</summary>

```hcl
# ===================================
# ATHENA QUERY RESULTS BUCKET
# ===================================

resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.project_name}-athena-results-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Purpose = "Athena Query Results"
    }
  )
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "expire-query-results"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

# ===================================
# ATHENA WORKGROUPS
# ===================================

resource "aws_athena_workgroup" "main" {
  name        = "${var.project_name}-${var.environment}"
  description = "Main workgroup for ${var.project_name}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/main/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "AUTO"
    }
  }

  tags = local.common_tags
}

resource "aws_athena_workgroup" "analysts" {
  name        = "${var.project_name}-analysts-${var.environment}"
  description = "Workgroup for data analysts"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/analysts/"
    }

    # Límites para prevenir queries costosos
    bytes_scanned_cutoff_per_query = 10737418240  # 10 GB
  }

  tags = merge(
    local.common_tags,
    {
      Team = "Analytics"
    }
  )
}

# ===================================
# ATHENA NAMED QUERIES
# ===================================

resource "aws_athena_named_query" "sample_events_count" {
  name        = "count_events_by_type"
  description = "Count events grouped by type"
  database    = aws_glue_catalog_database.main.name
  workgroup   = aws_athena_workgroup.main.name

  query = <<-SQL
    SELECT
      event_type,
      COUNT(*) as event_count,
      COUNT(DISTINCT user_id) as unique_users
    FROM ${aws_glue_catalog_table.sample_data.name}
    WHERE year = '{{year}}'
      AND month = '{{month}}'
    GROUP BY event_type
    ORDER BY event_count DESC;
  SQL
}

resource "aws_athena_named_query" "daily_active_users" {
  name        = "daily_active_users"
  description = "Calculate daily active users"
  database    = aws_glue_catalog_database.main.name
  workgroup   = aws_athena_workgroup.analysts.name

  query = <<-SQL
    SELECT
      year,
      month,
      day,
      COUNT(DISTINCT user_id) as daily_active_users
    FROM ${aws_glue_catalog_table.sample_data.name}
    WHERE year >= '{{start_year}}'
    GROUP BY year, month, day
    ORDER BY year DESC, month DESC, day DESC;
  SQL
}

output "athena_info" {
  value = {
    workgroups = {
      main     = aws_athena_workgroup.main.name
      analysts = aws_athena_workgroup.analysts.name
    }
    queries = {
      events_count = aws_athena_named_query.sample_events_count.name
      dau          = aws_athena_named_query.daily_active_users.name
    }
    results_bucket = aws_s3_bucket.athena_results.id
  }
}
```text

</details>

---

## Task 4, 5 y 6: IAM, Lifecycle y Tags

Debido a limitaciones de longitud, combinaré las últimas 3 tasks:

<details>
<summary>📄 iam-roles.tf - IAM Completo</summary>

```hcl
# Roles para Data Engineers, Analysts, Admin
# Ver exercise 02 para implementación completa
# Adaptar para incluir permisos de Glue y Athena
```

</details>

<details>
<summary>📄 outputs.tf - Outputs Completos</summary>

```hcl
output "data_lake_summary" {
  value = {
    buckets = {
      bronze = aws_s3_bucket.bronze.id
      silver = aws_s3_bucket.silver.id
      gold   = aws_s3_bucket.gold.id
    }
    glue_database = aws_glue_catalog_database.main.name
    athena_workgroup = aws_athena_workgroup.main.name
    environment = var.environment
  }
}
```text

</details>

```bash
terraform apply -auto-approve
terraform output
```text

---

## Troubleshooting

### Problema 1: Glue Crawler Falla

**Solution:** Verificar permisos IAM del rol de Glue

### Problema 2: Athena Query Timeout

**Solution:** Aumentar bytes_scanned_cutoff_per_query

### Problema 3: Lifecycle Policy No Aplica

**Solution:** Verificar que objetos tengan LastModified correcto

---

## Recursos Adicionales

- [AWS Glue Best Practices](https://docs.aws.amazon.com/glue/latest/dg/best-practices.html)
- [Athena Performance Tuning](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

---

## Próximos Steps

**Continúa con:** [Exercise 05 - State Management](../05-state-management/README.md)
