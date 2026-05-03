# Exercise 03: Terraform Modules

## Description

En este exercise you will learn a create y utilizar modules de Terraform para hacer tu código más reutilizable, mantenible y organizado. Los modules son la clave para escalar tu infraestructura como código de manera profesional. Crearás modules personalizados y utilizarás modules públicos del Terraform Registry.

**Estimated Duration:** 150-180 minutes

## Prerequisites

- Exercises 01 y 02 completeds
- Comprensión de recursos y variables en Terraform
- Git instalado (para versionado de modules)
- Conocimiento básico de estructura de proyectos

## Objectives de Aprendizaje

Al completar este exercise serás capaz de:

1. ✅ Crear modules básicos reutilizables
2. ✅ Definir inputs y outputs de modules
3. ✅ Utilizar modules múltiples veces con diferentes configuraciones
4. ✅ Crear modules complejos con múltiples recursos
5. ✅ Consumir modules del Terraform Registry público
6. ✅ Implementar versionado y gestión de modules

---

## Task 1: Crear Module Básico (S3 Bucket)

### Description

Crearás tu primer module de Terraform: un bucket S3 configurable y reutilizable que encapsula las best practices de seguridad y configuration.

### Steps

#### 1.1. Estructura del Proyecto

```bash
# Crear estructura de directorios
mkdir -p ~/terraform-exercises/03-modules
cd ~/terraform-exercises/03-modules

# Estructura de modules
mkdir -p modules/s3-bucket
mkdir -p environments/dev
mkdir -p environments/prod

# Archivos principales
touch main.tf variables.tf outputs.tf terraform.tfvars
```

#### 1.2. Crear el Module S3 Bucket

<details>
<summary>📄 modules/s3-bucket/main.tf - Module S3</summary>

```hcl
# modules/s3-bucket/main.tf
# Module reutilizable para create buckets S3 con best practices

# Bucket principal
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  tags = merge(
    var.tags,
    {
      Name      = var.bucket_name
      Module    = "s3-bucket"
      ManagedBy = "Terraform"
    }
  )

  # Lifecycle rules del module
  lifecycle {
    prevent_destroy = var.prevent_destroy
  }
}

# Versionamiento
resource "aws_s3_bucket_versioning" "this" {
  count  = var.versioning_enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encriptación
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  count  = var.encryption_enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = var.bucket_key_enabled
  }
}

# Public Access Block (siempre habilitado por seguridad)
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = var.block_public_access
  block_public_policy     = var.block_public_access
  ignore_public_acls      = var.block_public_access
  restrict_public_buckets = var.block_public_access
}

# Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = var.lifecycle_rules

    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      # Filtro opcional
      dynamic "filter" {
        for_each = rule.value.prefix != null ? [1] : []

        content {
          prefix = rule.value.prefix
        }
      }

      # Transición a clases de almacenamiento económicas
      dynamic "transition" {
        for_each = rule.value.transitions

        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      # Expiración de objetos
      dynamic "expiration" {
        for_each = rule.value.expiration_days != null ? [1] : []

        content {
          days = rule.value.expiration_days
        }
      }

      # Limpiar uploads incompletos
      dynamic "abort_incomplete_multipart_upload" {
        for_each = rule.value.abort_incomplete_uploads_days != null ? [1] : []

        content {
          days_after_initiation = rule.value.abort_incomplete_uploads_days
        }
      }
    }
  }
}

# Logging (opcional)
resource "aws_s3_bucket_logging" "this" {
  count  = var.logging_bucket != null ? 1 : 0
  bucket = aws_s3_bucket.this.id

  target_bucket = var.logging_bucket
  target_prefix = var.logging_prefix
}

# CORS Configuration (opcional)
resource "aws_s3_bucket_cors_configuration" "this" {
  count  = length(var.cors_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "cors_rule" {
    for_each = var.cors_rules

    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# Bucket Policy (opcional)
resource "aws_s3_bucket_policy" "this" {
  count  = var.bucket_policy != null ? 1 : 0
  bucket = aws_s3_bucket.this.id
  policy = var.bucket_policy
}
```

</details>

<details>
<summary>📄 modules/s3-bucket/variables.tf - Variables del Module</summary>

```hcl
# modules/s3-bucket/variables.tf
# Variables de entrada del module S3

variable "bucket_name" {
  description = "Nombre del bucket S3 (debe ser globalmente único)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.bucket_name))
    error_message = "El nombre del bucket debe empezar y terminar con letra o número, y solo contener letras minúsculas, números y guiones."
  }

  validation {
    condition     = length(var.bucket_name) >= 3 && length(var.bucket_name) <= 63
    error_message = "El nombre del bucket debe tener entre 3 y 63 caracteres."
  }
}

variable "versioning_enabled" {
  description = "Habilitar versionamiento de objetos"
  type        = bool
  default     = true
}

variable "encryption_enabled" {
  description = "Habilitar encriptación server-side"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "ARN de la KMS key para encriptación (null = usar AES256)"
  type        = string
  default     = null
}

variable "bucket_key_enabled" {
  description = "Habilitar S3 Bucket Keys para reducir costos de KMS"
  type        = bool
  default     = true
}

variable "block_public_access" {
  description = "Bloquear todo acceso público al bucket"
  type        = bool
  default     = true
}

variable "prevent_destroy" {
  description = "Prevenir destrucción accidental del bucket"
  type        = bool
  default     = false
}

variable "lifecycle_rules" {
  description = "Reglas de lifecycle para el bucket"
  type = list(object({
    id                            = string
    enabled                       = bool
    prefix                        = optional(string)
    expiration_days               = optional(number)
    abort_incomplete_uploads_days = optional(number, 7)
    transitions = optional(list(object({
      days          = number
      storage_class = string
    })), [])
  }))
  default = []
}

variable "logging_bucket" {
  description = "Bucket de destino para access logs"
  type        = string
  default     = null
}

variable "logging_prefix" {
  description = "Prefijo para logs en el bucket de logging"
  type        = string
  default     = "logs/"
}

variable "cors_rules" {
  description = "Reglas CORS para el bucket"
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = optional(list(string), [])
    max_age_seconds = optional(number, 3000)
  }))
  default = []
}

variable "bucket_policy" {
  description = "Bucket policy en formato JSON"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags a aplicar al bucket"
  type        = map(string)
  default     = {}
}
```

</details>

<details>
<summary>📄 modules/s3-bucket/outputs.tf - Outputs del Module</summary>

```hcl
# modules/s3-bucket/outputs.tf
# Outputs del module S3

output "bucket_id" {
  description = "ID del bucket S3"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN del bucket S3"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "Domain name del bucket"
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name del bucket"
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "bucket_region" {
  description = "Región del bucket"
  value       = aws_s3_bucket.this.region
}

output "versioning_enabled" {
  description = "Estado del versionamiento"
  value       = var.versioning_enabled
}

output "encryption_enabled" {
  description = "Estado de la encriptación"
  value       = var.encryption_enabled
}

output "bucket_details" {
  description = "Detalles completos del bucket"
  value = {
    id                  = aws_s3_bucket.this.id
    arn                 = aws_s3_bucket.this.arn
    region              = aws_s3_bucket.this.region
    versioning_enabled  = var.versioning_enabled
    encryption_enabled  = var.encryption_enabled
    public_access_block = var.block_public_access
  }
}
```

</details>

<details>
<summary>📄 modules/s3-bucket/README.md - Documentación del Module</summary>

```markdown
# S3 Bucket Module

Module Terraform para create buckets S3 con best practices de seguridad y configuration.

## Features

- ✅ Versionamiento configurable
- ✅ Encriptación server-side (AES256 o KMS)
- ✅ Public Access Block activado por defecto
- ✅ Lifecycle rules personalizables
- ✅ Access logging opcional
- ✅ CORS configuration
- ✅ Bucket policies personalizadas
- ✅ Prevención de destrucción accidental

## Usage

```hcl
module "my_bucket" {
  source = "./modules/s3-bucket"

  bucket_name        = "my-application-bucket"
  versioning_enabled = true
  encryption_enabled = true

  lifecycle_rules = [
    {
      id      = "archive-old-data"
      enabled = true
      transitions = [
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
      expiration_days = 365
    }
  ]

  tags = {
    Environment = "production"
    Application = "my-app"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| bucket_name | Nombre del bucket S3 | `string` | n/a | yes |
| versioning_enabled | Habilitar versionamiento | `bool` | `true` | no |
| encryption_enabled | Habilitar encriptación | `bool` | `true` | no |
| block_public_access | Bloquear acceso público | `bool` | `true` | no |
| lifecycle_rules | Lifecycle rules | `list(object)` | `[]` | no |
| tags | Tags a aplicar | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| bucket_id | ID del bucket |
| bucket_arn | ARN del bucket |
| bucket_details | Detalles completos del bucket |

## Examples

Ver `examples/` directory.
```

</details>

#### 1.3. Usar el Module

<details>
<summary>📄 main.tf - Usando el Module</summary>

```hcl
# main.tf
# Configuration principal usando modules

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
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = "http://localhost:4566"
  }
}

# Usar el module para create múltiples buckets
module "raw_data_bucket" {
  source = "./modules/s3-bucket"

  bucket_name        = "module-raw-data-dev"
  versioning_enabled = true
  encryption_enabled = true

  lifecycle_rules = [
    {
      id      = "archive-old-data"
      enabled = true
      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
      expiration_days               = 365
      abort_incomplete_uploads_days = 7
    }
  ]

  tags = {
    Environment = "development"
    Purpose     = "Raw Data Storage"
    Layer       = "bronze"
  }
}

module "processed_data_bucket" {
  source = "./modules/s3-bucket"

  bucket_name        = "module-processed-data-dev"
  versioning_enabled = true
  encryption_enabled = true

  lifecycle_rules = [
    {
      id      = "keep-recent"
      enabled = true
      transitions = [
        {
          days          = 60
          storage_class = "INTELLIGENT_TIERING"
        }
      ]
      expiration_days = 180
    }
  ]

  tags = {
    Environment = "development"
    Purpose     = "Processed Data"
    Layer       = "silver"
  }
}

module "analytics_bucket" {
  source = "./modules/s3-bucket"

  bucket_name        = "module-analytics-data-dev"
  versioning_enabled = true
  encryption_enabled = true
  prevent_destroy    = false  # true en producción

  lifecycle_rules = [
    {
      id                            = "long-term-retention"
      enabled                       = true
      expiration_days               = 2555  # ~7 años
      abort_incomplete_uploads_days = 3
      transitions                   = []
    }
  ]

  tags = {
    Environment = "development"
    Purpose     = "Analytics"
    Layer       = "gold"
    Critical    = "true"
  }
}
```

</details>

<details>
<summary>📄 outputs.tf - Outputs Principales</summary>

```hcl
# outputs.tf
# Outputs de los modules usados

output "raw_data_bucket" {
  description = "Detalles del bucket de datos raw"
  value       = module.raw_data_bucket.bucket_details
}

output "processed_data_bucket" {
  description = "Detalles del bucket de datos procesados"
  value       = module.processed_data_bucket.bucket_details
}

output "analytics_bucket" {
  description = "Detalles del bucket de analytics"
  value       = module.analytics_bucket.bucket_details
}

output "all_bucket_arns" {
  description = "ARNs de todos los buckets"
  value = [
    module.raw_data_bucket.bucket_arn,
    module.processed_data_bucket.bucket_arn,
    module.analytics_bucket.bucket_arn,
  ]
}
```

</details>

#### 1.4. Aplicar Configuration

```bash
# Inicializar (descargará los modules)
terraform init

# Ver plan
terraform plan

# Aplicar
terraform apply -auto-approve

# Ver outputs
terraform output

# Verificar modules
ls -la .terraform/modules/
```

### Output Esperado

```plaintext
Initializing modules...
- raw_data_bucket in modules/s3-bucket
- processed_data_bucket in modules/s3-bucket
- analytics_bucket in modules/s3-bucket

Apply complete! Resources: 12 added, 0 changed, 0 destroyed.

Outputs:

all_bucket_arns = [
  "arn:aws:s3:::module-raw-data-dev",
  "arn:aws:s3:::module-processed-data-dev",
  "arn:aws:s3:::module-analytics-data-dev",
]
```

### Conceptos Clave

- **Module**: Colección reutilizable de recursos de Terraform
- **module Block**: Cómo invocar un module
- **Module Source**: Ubicación del module (local, Git, registry)
- **Module Inputs**: Variables que se pasan al module
- **Module Outputs**: Valores que el module expone

---

## Task 2: Module Inputs y Outputs

### Description

Profundizarás en cómo diseñar interfaces de modules robustas con inputs bien documentados, validaciones, y outputs útiles.

### Steps

#### 2.1. Module con Validaciones Avanzadas

<details>
<summary>📄 modules/s3-bucket/variables-advanced.tf - Validaciones Avanzadas</summary>

```hcl
# modules/s3-bucket/variables-advanced.tf
# Variables con validaciones avanzadas

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser: dev, staging, o prod."
  }
}

variable "retention_policy" {
  description = "Política de retención de datos"
  type = object({
    mode                = string  # GOVERNANCE o COMPLIANCE
    retention_days      = number
    enable_object_lock  = bool
  })
  default = null

  validation {
    condition = (
      var.retention_policy == null ||
      contains(["GOVERNANCE", "COMPLIANCE"], var.retention_policy.mode)
    )
    error_message = "Retention mode debe ser GOVERNANCE o COMPLIANCE."
  }

  validation {
    condition = (
      var.retention_policy == null ||
      var.retention_policy.retention_days >= 1 && var.retention_policy.retention_days <= 36500
    )
    error_message = "Retention days debe estar entre 1 y 36500 (100 años)."
  }
}

variable "replication_configuration" {
  description = "Configuration de replicación cross-region"
  type = object({
    enabled             = bool
    destination_bucket  = string
    destination_region  = string
    replica_kms_key_id  = optional(string)
  })
  default = null

  validation {
    condition = (
      var.replication_configuration == null ||
      (var.replication_configuration.enabled && var.replication_configuration.destination_bucket != "")
    )
    error_message = "Si replication está enabled, destination_bucket es required."
  }
}

variable "notification_configuration" {
  description = "Configuration de notificaciones S3"
  type = object({
    sns_topic_arn   = optional(string)
    sqs_queue_arn   = optional(string)
    lambda_function_arn = optional(string)
    events          = list(string)
    filter_prefix   = optional(string)
    filter_suffix   = optional(string)
  })
  default = null

  validation {
    condition = (
      var.notification_configuration == null ||
      (
        var.notification_configuration.sns_topic_arn != null ||
        var.notification_configuration.sqs_queue_arn != null ||
        var.notification_configuration.lambda_function_arn != null
      )
    )
    error_message = "Al menos un destination (SNS, SQS, o Lambda) debe estar configurado."
  }

  validation {
    condition = (
      var.notification_configuration == null ||
      length(var.notification_configuration.events) > 0
    )
    error_message = "Al menos un event type debe estar especificado."
  }
}

variable =" "allowed_principals" {
  description = "Principals de IAM permitidos para acceder al bucket"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for principal in var.allowed_principals :
      can(regex("^arn:aws:iam::[0-9]{12}:(root|user|role)/.+$", principal))
    ])
    error_message = "Todos los principals deben ser ARNs válidos de IAM."
  }
}

variable "min_object_size" {
  description = "Tamaño mínimo de objetos en bytes (0 = sin límite)"
  type        = number
  default     = 0

  validation {
    condition     = var.min_object_size >= 0
    error_message = "min_object_size debe ser >= 0."
  }
}

variable "max_object_size" {
  description = "Tamaño máximo de objetos en bytes (0 = sin límite, max 5TB)"
  type        = number
  default     = 0

  validation {
    condition = (
      var.max_object_size == 0 ||
      (var.max_object_size > 0 && var.max_object_size <= 5497558138880)
    )
    error_message = "max_object_size debe ser 0 o <= 5TB (5497558138880 bytes)."
  }

  validation {
    condition = (
      var.min_object_size == 0 ||
      var.max_object_size == 0 ||
      var.max_object_size > var.min_object_size
    )
    error_message = "max_object_size debe ser mayor que min_object_size."
  }
}
```

</details>

<details>
<summary>📄 modules/s3-bucket/outputs-advanced.tf - Outputs Avanzados</summary>

```hcl
# modules/s3-bucket/outputs-advanced.tf
# Outputs avanzados con información detallada

output "bucket_full_details" {
  description = "Todos los detalles del bucket en formato estructurado"
  value = {
    # Información básica
    basic = {
      id                  = aws_s3_bucket.this.id
      arn                 = aws_s3_bucket.this.arn
      region              = aws_s3_bucket.this.region
      domain_name         = aws_s3_bucket.this.bucket_domain_name
      regional_domain     = aws_s3_bucket.this.bucket_regional_domain_name
    }

    # Configuraciones de seguridad
    security = {
      versioning_enabled  = var.versioning_enabled
      encryption_enabled  = var.encryption_enabled
      encryption_type     = var.kms_key_id != null ? "KMS" : "AES256"
      kms_key_id          = var.kms_key_id
      public_access_block = var.block_public_access
      prevent_destroy     = var.prevent_destroy
    }

    # Configuraciones de almacenamiento
    storage = {
      lifecycle_rules_count = length(var.lifecycle_rules)
      logging_enabled       = var.logging_bucket != null
      cors_enabled          = length(var.cors_rules) > 0
    }

    # Tags
    tags = aws_s3_bucket.this.tags_all
  }
}

output "bucket_urls" {
  description = "URLs útiles del bucket"
  value = {
    s3_uri            = "s3://${aws_s3_bucket.this.id}"
    console_url       = "https://s3.console.aws.amazon.com/s3/buckets/${aws_s3_bucket.this.id}"
    website_endpoint  = "http://${aws_s3_bucket.this.id}.s3-website-${aws_s3_bucket.this.region}.amazonaws.com"
  }
}

output "bucket_access_json" {
  description = "Configuration de acceso en formato JSON (útil para otras tools)"
  value = jsonencode({
    bucket_name = aws_s3_bucket.this.id
    region      = aws_s3_bucket.this.region
    arn         = aws_s3_bucket.this.arn
  })
}

output "lifecycle_summary" {
  description = "Resumen de las lifecycle rules aplicadas"
  value = [
    for rule in var.lifecycle_rules : {
      id      = rule.id
      enabled = rule.enabled
      actions = {
        transitions   = length(rule.transitions)
        expiration    = rule.expiration_days != null
        abort_uploads = rule.abort_incomplete_uploads_days != null
      }
    }
  ]
}

output "estimated_monthly_cost" {
  description = "Estimación aproximada de costo mensual (placeholder)"
  value = {
    storage_standard_gb = "Depende del uso"
    requests            = "Depende del uso"
    data_transfer       = "Depende del uso"
    note                = "Use AWS Cost Calculator para estimación precisa"
  }
}

# Output sensible (marcado como sensitive)
output "bucket_policy" {
  description = "Bucket policy aplicada (sensitive)"
  value       = var.bucket_policy
  sensitive   = true  # No se muestra en logs
}
```

</details>

#### 2.2. Crear Ejemplo de Uso Completo

<details>
<summary>📄 examples/complete/main.tf - Ejemplo Completo</summary>

```hcl
# examples/complete/main.tf
# Ejemplo completo de uso del module con todas las features

module "complete_bucket" {
  source = "../../modules/s3-bucket"

  # Básico
  bucket_name = "complete-example-bucket-2024"

  # Seguridad
  versioning_enabled  = true
  encryption_enabled  = true
  block_public_access = true
  prevent_destroy     = false

  # Lifecycle
  lifecycle_rules = [
    {
      id      = "archive-and-expire"
      enabled = true
      prefix  = "data/"
      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        },
        {
          days          = 180
          storage_class = "DEEP_ARCHIVE"
        }
      ]
      expiration_days               = 365
      abort_incomplete_uploads_days = 7
    },
    {
      id      = "expire-temp"
      enabled = true
      prefix  = "temp/"
      expiration_days               = 7
      abort_incomplete_uploads_days = 1
      transitions                   = []
    }
  ]

  # CORS (para aplicaciones web)
  cors_rules = [
    {
      allowed_headers = ["*"]
      allowed_methods = ["GET", "HEAD"]
      allowed_origins = ["https://example.com", "https://app.example.com"]
      expose_headers  = ["ETag"]
      max_age_seconds = 3000
    }
  ]

  # Tags
  tags = {
    Environment = "development"
    Application = "data-platform"
    Team        = "data-engineering"
    CostCenter  = "engineering"
    Compliance  = "gdpr"
    Backup      = "daily"
  }
}

# Usar outputs del module
output "complete_example" {
  value = {
    bucket_details = module.complete_bucket.bucket_full_details
    urls           = module.complete_bucket.bucket_urls
    lifecycle      = module.complete_bucket.lifecycle_summary
  }
}
```

</details>

```bash
# Probar ejemplo completo
cd examples/complete
terraform init
terraform plan
terraform apply -auto-approve

# Ver outputs detallados
terraform output -json | jq '.'
```

### Output Esperado

```json
{
  "complete_example": {
    "value": {
      "bucket_details": {
        "basic": {
          "arn": "arn:aws:s3:::complete-example-bucket-2024",
          "domain_name": "complete-example-bucket-2024.s3.amazonaws.com",
          "id": "complete-example-bucket-2024",
          "region": "us-east-1"
        },
        "security": {
          "encryption_enabled": true,
          "encryption_type": "AES256",
          "prevent_destroy": false,
          "public_access_block": true,
          "versioning_enabled": true
        },
        "storage": {
          "cors_enabled": true,
          "lifecycle_rules_count": 2,
          "logging_enabled": false
        }
      },
      "lifecycle": [
        {
          "actions": {
            "abort_uploads": true,
            "expiration": true,
            "transitions": 3
          },
          "enabled": true,
          "id": "archive-and-expire"
        }
      ],
      "urls": {
        "console_url": "https://s3.console.aws.amazon.com/s3/buckets/complete-example-bucket-2024",
        "s3_uri": "s3://complete-example-bucket-2024"
      }
    }
  }
}
```

### Conceptos Clave

- **Input Validation**: Validar valores de variables en el module
- **Optional Attributes**: Usar `optional()` para atributos opcionales (Terraform 1.3+)
- **Complex Types**: object, list, map para configuraciones complejas
- **Sensitive Outputs**: Marcar outputs sensibles con `sensitive = true`
- **Output Transformation**: Transformar datos para outputs útiles

---

## Task 3: Usar Module Múltiples Veces

### Description

You will learn técnicas avanzadas para reutilizar modules con diferentes configuraciones, incluyendo uso con `for_each` y `count`.

### Steps

#### 3.1. Module con For_Each

<details>
<summary>📄 multi-instance.tf - Múltiples Instancias del Module</summary>

```hcl
# multi-instance.tf
# Usar el mismo module múltiples veces con for_each

locals {
  # Definir configuraciones de buckets
  buckets = {
    raw = {
      name    = "multi-raw-data"
      purpose = "Raw data ingestion"
      lifecycle_days = 90
      versioning = true
    }
    processed = {
      name    = "multi-processed-data"
      purpose = "Processed data"
      lifecycle_days = 180
      versioning = true
    }
    analytics = {
      name    = "multi-analytics"
      purpose = "Analytics queries"
      lifecycle_days = 365
      versioning = true
    }
    temporary = {
      name    = "multi-temp-storage"
      purpose = "Temporary files"
      lifecycle_days = 7
      versioning = false
    }
  }
}

# Crear todos los buckets usando for_each
module "data_lake_buckets" {
  source   = "./modules/s3-bucket"
  for_each = local.buckets

  bucket_name        = "${each.value.name}-dev"
  versioning_enabled = each.value.versioning
  encryption_enabled = true

  lifecycle_rules = [
    {
      id              = "auto-expire"
      enabled         = true
      expiration_days = each.value.lifecycle_days
      transitions = each.value.lifecycle_days > 30 ? [
        {
          days          = floor(each.value.lifecycle_days / 3)
          storage_class = "STANDARD_IA"
        }
      ] : []
      abort_incomplete_uploads_days = 7
    }
  ]

  tags = {
    Environment = "development"
    Purpose     = each.value.purpose
    Layer       = each.key
    ManagedBy   = "Terraform-Module"
  }
}

# Outputs dinámicos
output "all_buckets" {
  description = "Todos los buckets creados"
  value = {
    for k, module in module.data_lake_buckets : k => {
      id      = module.bucket_id
      arn     = module.bucket_arn
      purpose = local.buckets[k].purpose
    }
  }
}

output "bucket_arns_list" {
  description = "Lista de ARNs"
  value = [
    for module in module.data_lake_buckets : module.bucket_arn
  ]
}
```

</details>

#### 3.2. Module Parametrizado por Ambiente

<details>
<summary>📄 multi-environment.tf - Multi-Ambiente</summary>

```hcl
# multi-environment.tf
# Usar modules para múltiples ambientes

variable "environments" {
  description = "Configuration por ambiente"
  type = map(object({
    versioning         = bool
    prevent_destroy    = bool
    lifecycle_days     = number
    enable_logging     = bool
  }))
  default = {
    dev = {
      versioning      = false
      prevent_destroy = false
      lifecycle_days  = 30
      enable_logging  = false
    }
    staging = {
      versioning      = true
      prevent_destroy = false
      lifecycle_days  = 90
      enable_logging  = true
    }
    prod = {
      versioning      = true
      prevent_destroy = true
      lifecycle_days  = 365
      enable_logging  = true
    }
  }
}

# Bucket principal por ambiente
module "app_bucket_per_env" {
  source   = "./modules/s3-bucket"
  for_each = var.environments

  bucket_name        = "myapp-data-${each.key}"
  versioning_enabled = each.value.versioning
  encryption_enabled = true
  prevent_destroy    = each.value.prevent_destroy

  lifecycle_rules = [
    {
      id              = "retention"
      enabled         = true
      expiration_days = each.value.lifecycle_days
      transitions = each.key == "prod" ? [
        {
          days          = 90
          storage_class = "STANDARD_IA"
        },
        {
          days          = 180
          storage_class = "GLACIER"
        }
      ] : []
      abort_incomplete_uploads_days = 7
    }
  ]

  tags = {
    Environment = each.key
    Application = "myapp"
    Tier        = each.key == "prod" ? "production" : "non-production"
  }
}

# Logging bucket (solo para staging y prod)
module "logging_bucket_per_env" {
  source   = "./modules/s3-bucket"
  for_each = {
    for k, v in var.environments : k => v if v.enable_logging
  }

  bucket_name        = "myapp-logs-${each.key}"
  versioning_enabled = false
  encryption_enabled = true

  lifecycle_rules = [
    {
      id              = "expire-logs"
      enabled         = true
      expiration_days = 90
      transitions     = []
      abort_incomplete_uploads_days = 3
    }
  ]

  tags = {
    Environment = each.key
    Purpose     = "Access Logs"
  }
}

output "environments_summary" {
  description = "Resumen por ambiente"
  value = {
    for env, config in var.environments : env => {
      app_bucket = {
        id              = module.app_bucket_per_env[env].bucket_id
        arn             = module.app_bucket_per_env[env].bucket_arn
        versioning      = config.versioning
        prevent_destroy = config.prevent_destroy
      }
      logging_bucket = config.enable_logging ? {
        id  = module.logging_bucket_per_env[env].bucket_id
        arn = module.logging_bucket_per_env[env].bucket_arn
      } : null
    }
  }
}
```

</details>

#### 3.3. Composición de Modules

<details>
<summary>📄 module-composition.tf - Composición de Modules</summary>

```hcl
# module-composition.tf
# Modules que usan otros modules

# Module de logging (usa el module s3-bucket internamente)
module "centralized_logging" {
  source = "./modules/s3-bucket"

  bucket_name        = "centralized-logs-bucket"
  versioning_enabled = true
  encryption_enabled = true

  lifecycle_rules = [
    {
      id              = "expire-old-logs"
      enabled         = true
      expiration_days = 90
      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        }
      ]
      abort_incomplete_uploads_days = 3
    }
  ]

  tags = {
    Purpose = "Centralized Logging"
    Type    = "infrastructure"
  }
}

# Buckets de aplicación que usan el bucket de logging
module "app_buckets_with_logging" {
  source   = "./modules/s3-bucket"
  for_each = toset(["api", "web", "mobile"])

  bucket_name        = "app-${each.value}-data"
  versioning_enabled = true
  encryption_enabled = true

  # Usar el bucket de logging creado anteriormente
  logging_bucket = module.centralized_logging.bucket_id
  logging_prefix = "${each.value}/"

  lifecycle_rules = [
    {
      id              = "standard"
      enabled         = true
      expiration_days = 180
      transitions     = []
      abort_incomplete_uploads_days = 7
    }
  ]

  tags = {
    Application = each.value
    Purpose     = "Application Data"
  }

  # Dependencia explícita
  depends_on = [module.centralized_logging]
}

output "logging_infrastructure" {
  value = {
    central_log_bucket = module.centralized_logging.bucket_id
    applications = {
      for app, module in module.app_buckets_with_logging : app => {
        bucket      = module.bucket_id
        logs_prefix = "${app}/"
      }
    }
  }
}
```

</details>

```bash
# Aplicar configuration multi-instancia
terraform apply -auto-approve

# Ver cuántos recursos se crearon
terraform state list | wc -l

# Ver detalles de un module específico
terraform state show 'module.data_lake_buckets["raw"].aws_s3_bucket.this'
```

### Output Esperado

```plaintext
Apply complete! Resources: 28 added, 0 changed, 0 destroyed.

all_buckets = {
  "analytics" = {
    "arn" = "arn:aws:s3:::multi-analytics-dev"
    "id" = "multi-analytics-dev"
    "purpose" = "Analytics queries"
  }
  "processed" = {
    "arn" = "arn:aws:s3:::multi-processed-data-dev"
    "id" = "multi-processed-data-dev"
    "purpose" = "Processed data"
  }
  "raw" = {
    "arn" = "arn:aws:s3:::multi-raw-data-dev"
    "id" = "multi-raw-data-dev"
    "purpose" = "Raw data ingestion"
  }
  "temporary" = {
    "arn" = "arn:aws:s3:::multi-temp-storage-dev"
    "id" = "multi-temp-storage-dev"
    "purpose" = "Temporary files"
  }
}
```

### Conceptos Clave

- **Module for_each**: Crear múltiples instancias de un module
- **Module Count**: Alternativa más simple (menos flexible)
- **Module Composition**: Modules que usan otros modules
- **Module Dependencies**: depends_on entre modules
- **Dynamic Configuration**: Configuration diferente por instancia

---

## Task 4: Module Complejo (Data Lake)

### Description

Crearás un module completo y complejo que orquesta múltiples recursos de AWS para implement un Data Lake con S3, Glue, y IAM.

### Steps

#### 4.1. Crear Module Data Lake

<details>
<summary>📄 modules/data-lake/main.tf - Module Data Lake Completo</summary>

```hcl
# modules/data-lake/main.tf
# Module complejo para Data Lake completo

# Buckets para las tres capas
module "bronze_bucket" {
  source = "../s3-bucket"

  bucket_name        = "${var.project_name}-bronze-${var.environment}"
  versioning_enabled = var.enable_versioning
  encryption_enabled = true

  lifecycle_rules = [
    {
      id              = "bronze-lifecycle"
      enabled         = true
      expiration_days = var.bronze_retention_days
      transitions = [
        {
          days          = floor(var.bronze_retention_days / 3)
          storage_class = "STANDARD_IA"
        }
      ]
      abort_incomplete_uploads_days = 7
    }
  ]

  logging_bucket = module.logs_bucket.bucket_id
  logging_prefix = "bronze/"

  tags = merge(
    var.tags,
    {
      Layer = "bronze"
      Stage = "raw"
    }
  )
}

module "silver_bucket" {
  source = "../s3-bucket"

  bucket_name        = "${var.project_name}-silver-${var.environment}"
  versioning_enabled = var.enable_versioning
  encryption_enabled = true

  lifecycle_rules = [
    {
      id              = "silver-lifecycle"
      enabled         = true
      expiration_days = var.silver_retention_days
      transitions = [
        {
          days          = floor(var.silver_retention_days / 2)
          storage_class = "INTELLIGENT_TIERING"
        }
      ]
      abort_incomplete_uploads_days = 7
    }
  ]

  logging_bucket = module.logs_bucket.bucket_id
  logging_prefix = "silver/"

  tags = merge(
    var.tags,
    {
      Layer = "silver"
      Stage = "processed"
    }
  )
}

module "gold_bucket" {
  source = "../s3-bucket"

  bucket_name        = "${var.project_name}-gold-${var.environment}"
  versioning_enabled = true
  encryption_enabled = true
  prevent_destroy    = var.environment == "production"

  lifecycle_rules = [
    {
      id              = "gold-lifecycle"
      enabled         = true
      expiration_days = var.gold_retention_days
      transitions = [
        {
          days          = 90
          storage_class = "STANDARD_IA"
        },
        {
          days          = 180
          storage_class = "GLACIER"
        }
      ]
      abort_incomplete_uploads_days = 3
    }
  ]

  logging_bucket = module.logs_bucket.bucket_id
  logging_prefix = "gold/"

  tags = merge(
    var.tags,
    {
      Layer    = "gold"
      Stage    = "analytics"
      Critical = "true"
    }
  )
}

# Bucket de logs
module "logs_bucket" {
  source = "../s3-bucket"

  bucket_name        = "${var.project_name}-access-logs-${var.environment}"
  versioning_enabled = false
  encryption_enabled = true

  lifecycle_rules = [
    {
      id              = "expire-logs"
      enabled         = true
      expiration_days = var.logs_retention_days
      transitions     = []
      abort_incomplete_uploads_days = 3
    }
  ]

  tags = merge(
    var.tags,
    {
      Purpose = "Access Logs"
    }
  )
}

# Glue Database
resource "aws_glue_catalog_database" "data_lake" {
  name        = "${var.project_name}_${var.environment}"
  description = "Data Lake database for ${var.project_name}"

  location_uri = "s3://${module.silver_bucket.bucket_id}/"

  create_table_default_permission {
    permissions = ["SELECT"]

    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

# Glue Crawler para Bronze
resource "aws_glue_crawler" "bronze" {
  count = var.enable_crawlers ? 1 : 0

  database_name = aws_glue_catalog_database.data_lake.name
  name          = "${var.project_name}-bronze-crawler-${var.environment}"
  role          = aws_iam_role.glue.arn

  s3_target {
    path = "s3://${module.bronze_bucket.bucket_id}/"
  }

  schedule = var.crawler_schedule

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = merge(
    var.tags,
    {
      Layer = "bronze"
    }
  )
}

# Glue Crawler para Silver
resource "aws_glue_crawler" "silver" {
  count = var.enable_crawlers ? 1 : 0

  database_name = aws_glue_catalog_database.data_lake.name
  name          = "${var.project_name}-silver-crawler-${var.environment}"
  role          = aws_iam_role.glue.arn

  s3_target {
    path = "s3://${module.silver_bucket.bucket_id}/"
  }

  schedule = var.crawler_schedule

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = merge(
    var.tags,
    {
      Layer = "silver"
    }
  )
}

# IAM Role para Glue
resource "aws_iam_role" "glue" {
  name = "${var.project_name}-glue-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Policy para Glue
resource "aws_iam_role_policy" "glue" {
  name = "${var.project_name}-glue-policy"
  role = aws_iam_role.glue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.bronze_bucket.bucket_arn,
          "${module.bronze_bucket.bucket_arn}/*",
          module.silver_bucket.bucket_arn,
          "${module.silver_bucket.bucket_arn}/*",
          module.gold_bucket.bucket_arn,
          "${module.gold_bucket.bucket_arn}/*"
        ]
      },
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

# Data Engineer Role
resource "aws_iam_role" "data_engineer" {
  name = "${var.project_name}-data-engineer-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ec2.amazonaws.com", "lambda.amazonaws.com"]
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Role = "DataEngineer"
    }
  )
}

resource "aws_iam_role_policy" "data_engineer" {
  name = "data-engineer-policy"
  role = aws_iam_role.data_engineer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:*"]
        Resource = [
          module.bronze_bucket.bucket_arn,
          "${module.bronze_bucket.bucket_arn}/*",
          module.silver_bucket.bucket_arn,
          "${module.silver_bucket.bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          module.gold_bucket.bucket_arn,
          "${module.gold_bucket.bucket_arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["glue:*"]
        Resource = "*"
      }
    ]
  })
}

# Data Analyst Role
resource "aws_iam_role" "data_analyst" {
  name = "${var.project_name}-data-analyst-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "athena.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Role = "DataAnalyst"
    }
  )
}

resource "aws_iam_role_policy" "data_analyst" {
  name = "data-analyst-policy"
  role = aws_iam_role.data_analyst.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          module.gold_bucket.bucket_arn,
          "${module.gold_bucket.bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions"
        ]
        Resource = "*"
      }
    ]
  })
}
```

</details>

<details>
<summary>📄 modules/data-lake/variables.tf - Variables del Data Lake</summary>

```hcl
# modules/data-lake/variables.tf

variable "project_name" {
  description = "Nombre del proyecto/data lake"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "El nombre del proyecto debe empezar con letra y solo contener letras minúsculas, números y guiones."
  }
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser: dev, staging, o prod."
  }
}

variable "enable_versioning" {
  description = "Habilitar versionamiento en buckets"
  type        = bool
  default     = true
}

variable "bronze_retention_days" {
  description = "Días de retención para capa bronze"
  type        = number
  default     = 90
}

variable "silver_retention_days" {
  description = "Días de retención para capa silver"
  type        = number
  default     = 180
}

variable "gold_retention_days" {
  description = "Días de retención para capa gold"
  type        = number
  default     = 365
}

variable "logs_retention_days" {
  description = "Días de retención para access logs"
  type        = number
  default     = 90
}

variable "enable_crawlers" {
  description = "Habilitar Glue Crawlers"
  type        = bool
  default     = true
}

variable "crawler_schedule" {
  description = "Schedule para Glue Crawlers (cron expression)"
  type        = string
  default     = "cron(0 1 * * ? *)"  # Diario a la 1 AM
}

variable "tags" {
  description = "Tags comunes"
  type        = map(string)
  default     = {}
}
```

</details>

<details>
<summary>📄 modules/data-lake/outputs.tf - Outputs del Data Lake</summary>

```hcl
# modules/data-lake/outputs.tf

output "buckets" {
  description = "Información de todos los buckets"
  value = {
    bronze = {
      id  = module.bronze_bucket.bucket_id
      arn = module.bronze_bucket.bucket_arn
    }
    silver = {
      id  = module.silver_bucket.bucket_id
      arn = module.silver_bucket.bucket_arn
    }
    gold = {
      id  = module.gold_bucket.bucket_id
      arn = module.gold_bucket.bucket_arn
    }
    logs = {
      id  = module.logs_bucket.bucket_id
      arn = module.logs_bucket.bucket_arn
    }
  }
}

output "glue_database" {
  description = "Glue Catalog Database"
  value = {
    name = aws_glue_catalog_database.data_lake.name
    id   = aws_glue_catalog_database.data_lake.id
  }
}

output "glue_crawlers" {
  description = "Glue Crawlers"
  value = var.enable_crawlers ? {
    bronze = aws_glue_crawler.bronze[0].name
    silver = aws_glue_crawler.silver[0].name
  } : null
}

output "iam_roles" {
  description = "Roles IAM crrados"
  value = {
    glue          = aws_iam_role.glue.arn
    data_engineer = aws_iam_role.data_engineer.arn
    data_analyst  = aws_iam_role.data_analyst.arn
  }
}

output "data_lake_summary" {
  description = "Resumen completo del Data Lake"
  value = {
    project         = var.project_name
    environment     = var.environment
    buckets_count   = 4
    glue_database   = aws_glue_catalog_database.data_lake.name
    crawlers_enabled = var.enable_crawlers
    versioning      = var.enable_versioning
  }
}
```

</details>

#### 4.2. Usar el Module Data Lake

<details>
<summary>📄 use-data-lake.tf - Usar Module Data Lake</summary>

```hcl
# use-data-lake.tf

module "my_data_lake" {
  source = "./modules/data-lake"

  project_name    = "analytics"
  environment     = "dev"
  enable_versioning = true

  bronze_retention_days = 60
  silver_retention_days = 180
  gold_retention_days   = 730  # 2 años

  enable_crawlers  = true
  crawler_schedule = "cron(0 2 * * ? *)"  # 2 AM daily

  tags = {
    Team       = "Data Engineering"
    CostCenter = "Analytics"
    Project    = "DataPlatform"
  }
}

output "data_lake_info" {
  value = module.my_data_lake.data_lake_summary
}

output "bucket_uris" {
  value = {
    bronze = "s3://${module.my_data_lake.buckets.bronze.id}"
    silver = "s3://${module.my_data_lake.buckets.silver.id}"
    gold   = "s3://${module.my_data_lake.buckets.gold.id}"
  }
}
```

</details>

```bash
# Aplicar el module complejo
terraform init
terraform plan
terraform apply -auto-approve

# Ver infraestructura creada
terraform output
terraform state list | grep module.my_data_lake
```

### Output Esperado

```plaintext
Apply complete! Resources: 23 added, 0 changed, 0 destroyed.

data_lake_info = {
  "buckets_count" = 4
  "crawlers_enabled" = true
  "environment" = "dev"
  "glue_database" = "analytics_dev"
  "project" = "analytics"
 "versioning" = true
}

bucket_uris = {
  "bronze" = "s3://analytics-bronze-dev"
  "gold" = "s3://analytics-gold-dev"
  "silver" = "s3://analytics-silver-dev"
}
```

### Conceptos Clave

- **Complex Modules**: Modules que gestionan múltiples recursos relacionados
- **Module Composition Advanced**: Modules usando otros modules
- **Resource Organization**: Organizar recursos lógicamente en modules
- **End-to-End Solutions**: Modules que proveen solutions completas

---

*Debido a la limitación de longitud, continuaré con las Tasks 5 y 6 en el siguiente mensaje...*

### Conceptos Clave para Modules Complejos

- **Modules Anidados**: Un module puede usar otros modules internamente
- **Abstracción de Complejidad**: Esconder implementación detallada
- **Configuration por Ambiente**: Adaptar comportamiento según environment
- **Gestión de Dependencias**: Manejar orden de creación correcto

---

## Task 5: Module Registry (Usar Module Público)

### Description

You will learn a consumir modules del Terraform Registry público, evaluarlos, y utilizarlos en tus proyectos.

### Steps

#### 5.1. Explorar Terraform Registry

```bash
# Navegar a: https://registry.terraform.io/
# Buscar modules populares de S3 y VPC

# Ejemplo: terraform-aws-modules/s3-bucket/aws
# URL: https://registry.terraform.io/modules/terraform-aws-modules/s3-bucket/aws
```

#### 5.2. Usar Module Público

<details>
<summary>📄 public-modules.tf - Usar Modules Públicos</summary>

```hcl
# public-modules.tf
# Ejemplos de uso de modules del Registry público

# Module oficial de S3 de AWS (terraform-aws-modules)
module "s3_bucket_public_module" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.15"

  bucket = "public-module-example-bucket"
  acl    = "private"

  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  lifecycle_rule = [
    {
      id      = "log"
      enabled = true

      transition = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 60
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = 90
      }
    }
  ]

  tags = {
    Name        = "Public Module Example"
    Source      = "Terraform Registry"
    Module      = "terraform-aws-modules/s3-bucket/aws"
  }
}

# Nota: Para LocalStack, este module puede no funcionar perfectamente
# En producción con AWS real, funciona excelentemente

output "public_module_bucket" {
  value = {
    id  = module.s3_bucket_public_module.s3_bucket_id
    arn = module.s3_bucket_public_module.s3_bucket_arn
  }
}
```

</details>

#### 5.3. Comparar Module Propio vs Público

<details>
<summary>📄 comparison-public-vs-custom.md - Comparación</summary>

```markdown
# Modules Públicos vs Modules Propios

## Modules del Terraform Registry

### ✅ Ventajas

1. **Mantenimiento**: Mantenidos por la comunidad o vendors oficiales
2. **Best Practices**: Implementan mejores prácticas establecidas
3. **Documentación**: Generalmente bien documentados
4. **Testing**: Probados por miles de usuarios
5. **Actualizaciones**: Reciben updates de seguridad y features
6. **Versionado Semántico**: Versiones claras y changelog

### ❌ Desventajas

1. **Menos Control**: No controlas implementación interna
2. **Dependencia Externa**: Dependen de maintainers terceros
3. **Overhead**: Pueden incluir features que no necesitas
4. **Compatibilidad**: Pueden no funcionar con LocalStack/testing
5. **Curva de Aprendizaje**: Necesitas learn su API específica

## Modules Propios

### ✅ Ventajas

1. **Control Total**: Control completo de implementación
2. **Personalización**: Adaptados exactamente a tus necesidades
3. **Sin Dependencias**: No dependes de terceros
4. **Optimización**: Solo incluyes lo que necesitas
5. **Testing Local**: Funciona con LocalStack

### ❌ Desventajas

1. **Mantenimiento**: Tú eres responsable del mantenimiento
2. **Tiempo de Desarrollo**: Requiere tiempo create y documentar
3. **Actualización**: Debes mantenerte al día con cambios de AWS
4. **Testing**: Debes create tus propios tests

## Cuándo Usar Cada Uno

### Usar Modules Públicos Cuando:
- Es un caso de uso común (VPC, S3, RDS)
- El module está bien mantenido (actualizaciones recientes)
- Tiene buen rating y muchos usuarios
- La funcionalidad es estándar

### Crear Modules Propios Cuando:
- Tienes requirements muy específicos
- Necesitas control granular
- Es lógica de negocio específica
- Trabajas con servicios customizados
- Testing con LocalStack es critical

## Hybrid Approach (Recomendado)

Use modules públicos para infraestructura base (VPC, networking)
y crea modules propios para lógica de aplicación específica.

```hcl
# Infraestructura base: module público
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  # ...
}

# Lógica de aplicación: module propio
module "my_data_pipeline" {
  source = "./modules/data-pipeline"
  # ...
}
```
```

</details>

#### 5.4. Evaluar Modules Públicos

<details>
<summary>📄 evaluate-modules.sh - Script para Evaluar Modules</summary>

```bash
#!/bin/bash
# Script para evaluar modules del Registry

MODULE_NAME=$1

if [ -z "$MODULE_NAME" ]; then
    echo "Uso: $0 <module-name>"
    echo "Ejemplo: $0 terraform-aws-modules/s3-bucket/aws"
    exit 1
fi

echo "=== Evaluando Module: $MODULE_NAME ==="

# 1. Información básica
echo -e "\n📦 Información del Module:"
echo "URL: https://registry.terraform.io/modules/$MODULE_NAME"

# 2. Descargar info (requiere API de Terraform Registry)
echo -e "\n🔍 Verificando versión más reciente..."
# La API pública de Terraform Registry
curl -s "https://registry.terraform.io/v1/modules/$MODULE_NAME" | jq -r '.version' 2>/dev/null || echo "No disponible"

# 3. Checklist de evaluación
echo -e "\n✅ Checklist de Evaluación:"
echo "[ ] Última actualización < 6 meses"
echo "[ ] Documentación completa"
echo "[ ] Ejemplos de uso disponibles"
echo "[ ] Tests incluidos"
echo "[ ] Número de downloads > 1000"
echo "[ ] Issues abiertas < 20"
echo "[ ] Versioning semántico"
echo "[ ] Changelog maintained"

# 4. Cómo revisar
echo -e "\n🔎 Steps para Revisar:"
echo "1. Visitar: https://registry.terraform.io/modules/$MODULE_NAME"
echo "2. Revisar tab 'Example Usage'"
echo "3. Verificar tab 'Inputs' y 'Outputs'"
echo "4. Leer README en GitHub (link en la página)"
echo "5. Revisar Issues y PRs en GitHub"
echo "6. Verificar última release date"

echo -e "\n✨ Recomendación:"
echo "Solo usa modules con:"
echo "  - Mantenimiento activo (< 6 meses desde último update)"
echo "  - Documentación clara"
echo "  - Compatible con tu versión de Terraform"
echo "  - De fuentes confiables (terraform-aws-modules, HashiCorp, etc.)"
```

</details>

```bash
# Evaluar un module
chmod +x evaluate-modules.sh
./evaluate-modules.sh terraform-aws-modules/s3-bucket/aws
```

### Conceptos Clave

- **Terraform Registry**: Repositorio central de modules públicos
- **Module Versioning**: Usar version constraints (~>, >=, etc.)
- **Module Sources**: Registry, Git, HTTP, local
- **Module Evaluation**: Criterios para evaluar modules públicos
- **Trusted Publishers**: terraform-aws-modules, hashicorp, etc.

---

## Task 6: Versioning de Modules

### Description

You will learn a versionar tus modules propios, publicarlos en Git, y gestionar diferentes versiones en producción.

### Steps

#### 6.1. Preparar Module para Versionado

<details>
<summary>📄 modules/s3-bucket/VERSION - Semantic Versioning</summary>

```
1.0.0
```

</details>

<details>
<summary>📄 modules/s3-bucket/CHANGELOG.md - Changelog</summary>

```markdown
# Changelog

Todos los cambios notables en este module serán documentados aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2024-03-07

### Added
- Module inicial de S3 bucket
- Soporte para versionamiento
- Soporte para encriptación (AES256 y KMS)
- Lifecycle rules configurables
- Public access block
- Logging configuration
- CORS configuration
- Bucket policies
- Validaciones de inputs
- Outputs detallados
- Documentación completa
- Ejemplos de uso

### Security
- Public access bloqueado por defecto
- Encriptación enabled por defecto
- Versionamiento recomendado

## [0.1.0] - 2024-03-01

### Added
- Versión alpha inicial
- Funcionalidad básica de bucket
```

</details>

<details>
<summary>📄 version-module.sh - Script Versionado</summary>

```bash
#!/bin/bash
# Script para versionar modules

set -e

MODULE_DIR=${1:-"modules/s3-bucket"}
VERSION_TYPE=${2:-"patch"}  # major, minor, patch

if [ ! -d "$MODULE_DIR" ]; then
    echo "❌ Module no encontrado: $MODULE_DIR"
    exit 1
fi

cd "$MODULE_DIR"

# Leer versión actual
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
else
    CURRENT_VERSION="0.0.0"
fi

echo "📦 Module: $MODULE_DIR"
echo "🏷️  Versión actual: $CURRENT_VERSION"

# Parse version
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
MAJOR="${version_parts[0]}"
MINOR="${version_parts[1]}"
PATCH="${version_parts[2]}"

# Increment según tipo
case $VERSION_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "❌ Tipo de versión inválido: $VERSION_TYPE"
        echo "Uso: major, minor, o patch"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "🆕 Nueva versión: $NEW_VERSION"

# Actualizar VERSION file
echo "$NEW_VERSION" > VERSION

# Git operations (si es un repo git)
if [ -d ".git" ] || git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📝 Creando commit y tag..."

    git add VERSION CHANGELOG.md
    git commit -m "chore: bump version to $NEW_VERSION"
    git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION"

    echo "✅ Tag creado: v$NEW_VERSION"
    echo "📤 Para publicar: git push && git push --tags"
else
    echo "⚠️  No es un repositorio Git, solo actualicé VERSION file"
fi

echo -e "\n✨ Versionado completed"
echo "Actualiza CHANGELOG.md con los cambios de esta versión"
```

</details>

#### 6.2. Publicar Module en Git

<details>
<summary>📄 publish-module.sh - Publicar Module</summary>

```bash
#!/bin/bash
# Script para publicar module en Git

set -e

MODULE_NAME=${1:-"s3-bucket"}
GIT_REMOTE=${2:-"origin"}

echo "=== Publicando Module: $MODULE_NAME ==="

# 1. Verificar que estamos en un repo git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ No es un repositorio Git"
    echo "Inicializando..."
    git init
    git add .
    git commit -m "Initial commit: $MODULE_NAME module"
fi

# 2. Verificar que hay cambios para pushear
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working directory limpio"
else
    echo "⚠️  Hay cambios sin commitear"
    git status --short
    read -p "¿Commitear cambios? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        read -p "Mensaje del commit: " commit_msg
        git commit -m "$commit_msg"
    fi
fi

# 3. Verificar remote
if ! git remote get-url "$GIT_REMOTE" > /dev/null 2>&1; then
    echo "❌ Remote '$GIT_REMOTE' no configurado"
    read -p "URL del repositorio remoto: " remote_url
    git remote add "$GIT_REMOTE" "$remote_url"
fi

# 4. Push commits y tags
echo "📤 Pushing commits..."
git push "$GIT_REMOTE" main || git push "$GIT_REMOTE" master

echo "🏷️  Pushing tags..."
git push "$GIT_REMOTE" --tags

# 5. Información final
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "sin tags")
REMOTE_URL=$(git remote get-url "$GIT_REMOTE")

echo -e "\n✅ Module publicado exitosamente"
echo "📦 Nombre: $MODULE_NAME"
echo "🏷️  Última versión: $LATEST_TAG"
echo "🔗 Repositorio: $REMOTE_URL"

echo -e "\n💡 Para usar este module:"
echo "module \"$MODULE_NAME\" {"
echo "  source = \"git::$REMOTE_URL?ref=$LATEST_TAG\""
echo "  # ..."
echo "}"
```

</details>

#### 6.3. Usar Modules Versionados

<details>
<summary>📄 versioned-modules.tf - Usar Modules con Versiones</summary>

```hcl
# versioned-modules.tf
# Ejemplos de uso de modules con diferentes versioning strategies

# 1. Module local (desarrollo)
module "s3_local" {
  source = "./modules/s3-bucket"

  bucket_name = "local-dev-bucket"
  # ... configuration
}

# 2. Module desde Git con tag específico (producción)
module "s3_prod_stable" {
  source = "git::https://github.com/tu-org/terraform-modules.git//modules/s3-bucket?ref=v1.0.0"

  bucket_name = "prod-stable-bucket"
  # ... configuration
}

# 3. Module desde Git con branch (staging)
module "s3_staging" {
  source = "git::https://github.com/tu-org/terraform-modules.git//modules/s3-bucket?ref=develop"

  bucket_name = "staging-bucket"
  # ... configuration
}

# 4. Module desde Git con commit hash (máxima precisión)
module "s3_specific_commit" {
  source = "git::https://github.com/tu-org/terraform-modules.git//modules/s3-bucket?ref=abc123def"

  bucket_name = "specific-version-bucket"
  # ... configuration
}

# 5. Module desde HTTP (tarball)
module "s3_from_http" {
  source = "https://example.com/terraform-modules/s3-bucket-v1.0.0.tar.gz"

  bucket_name = "http-source-bucket"
  # ... configuration
}

# 6. Module desde Terraform Registry (si lo publicaste)
# module "s3_from_registry" {
#   source  = "tu-org/s3-bucket/aws"
#   version = "~> 1.0"
#
#   bucket_name = "registry-bucket"
# }

# Version Constraints Examples:
# version = "1.0.0"      # Exactamente 1.0.0
# version = ">= 1.0.0"   # 1.0.0 o mayor
# version = "~> 1.0"     # >= 1.0.0 y < 2.0.0
# version = "~> 1.0.4"   # >= 1.0.4 y < 1.1.0
# version = ">= 1.0, < 2.0"  # Entre 1.0 y 2.0
```

</details>

<details>
<summary>📄 module-upgrade-strategy.md - Estrategia de Actualización</summary>

```markdown
# Estrategia de Actualización de Modules

## Semantic Versioning

Seguimos [SemVer](https://semver.org/): MAJOR.MINOR.PATCH

- **MAJOR**: Cambios incompatibles en la API
- **MINOR**: Nuevas features compatibles hacia atrás
- **PATCH**: Bug fixes compatibles hacia atrás

## Version Constraints Recomendados

### Desarrollo
```hcl
module "dev" {
  source = "./modules/s3-bucket"  # Local, siempre latest
}
```

### Staging
```hcl
module "staging" {
  source = "git::...?ref=develop"  # Branch develop
  # O usar minor version constraint:
  # version = "~> 1.1"  # Acepta patches automaticamente
}
```

### Producción
```hcl
module "prod" {
  source = "git::...?ref=v1.0.5"  # Tag específico
  # O version constraint estricto:
  # version = "1.0.5"  # Exactamente esta versión
}
```

## Proceso de Actualización

### 1. Actualización de PATCH (1.0.0 → 1.0.1)
**Riesgo: Bajo** - Solo bug fixes

```bash
# Dev/Staging: automático con ~> constraint
terraform init -upgrade

# Producción: manual
1. Revisar CHANGELOG
2. Actualizar version en terraform code
3. terraform plan (revisar cambios)
4. Aplicar en horario de mantenimiento
```

### 2. Actualización de MINOR (1.0.0 → 1.1.0)
**Riesgo: Medio** - Nuevas features

```bash
1. Revisar CHANGELOG y nuevas features
2. Actualizar en dev environment primero
3. Testing completo
4. Actualizar staging
5. Esperar 1-2 weeks
6. Actualizar producción con plan/apply cuidadoso
```

### 3. Actualización de MAJOR (1.0.0 → 2.0.0)
**Riesgo: Alto** - Breaking changes

```bash
1. Leer UPGRADE GUIDE del module
2. Identificar breaking changes
3. Crear feature branch
4. Actualizar código según migration guide
5. Testing exhaustivo en dev
6. Staging deployment y testing
7. Crear plan de rollback
8. Producción en maintenance window
9. Monitorear post-deployment
```

## Testing de Actualizaciones

```bash
# 1. Plan con nueva versión
terraform plan -out=upgrade.tfplan

# 2. Revisar plan detalladamente
terraform show upgrade.tfplan

# 3. Verificar que no hay recursos destruidos inesperadamente
terraform show upgrade.tfplan | grep -E "(destroy|replace)"

# 4. Si todo OK, aplicar
terraform apply upgrade.tfplan
```

## Rollback Strategy

### Si algo sale mal:

```bash
# Opción 1: Revertir a versión anterior
1. Cambiar version/ref en código
2. terraform init -upgrade
3. terraform apply

# Opción 2: terraform state rollback (último recurso)
# Usar backup del state anterior

# Opción 3: Destruir y recrear
# Solo si no hay datos críticos
terraform destroy -target=module.problematic
# Revertir código
terraform apply
```

## Best Practices

1. **Pin Versions en Producción**: Siempre usar versions/tags específicos
2. **Automated Testing**: CI/CD con terraform plan en PRs
3. **Gradual Rollout**: Dev → Staging → Prod
4. **Changelog Review**: Leer siempre antes de actualizar
5. **Backup State**: Hacer backup antes de major updates
6. **Monitoring**: Monitorear después de actualizaciones
7. **Communication**: Notificar al equipo de cambios mayores

## Ejemplo de CI/CD para Modules

```yaml
# .github/workflows/module-release.yml
name: Release Module

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate Terraform
        run: |
          terraform init
          terraform validate

      - name: Run Tests
        run: |
          # Ejecutar terratest o similar
          go test -v ./tests/

      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          body: |
            Ver CHANGELOG.md para detalles
```
```

</details>

```bash
# Versionar module
chmod +x version-module.sh
./version-module.sh modules/s3-bucket patch

# Simular publicación (sin remote real)
echo "En producción, ejecutarías:"
echo "./publish-module.sh s3-bucket origin"
```

### Output Esperado

```plaintext
📦 Module: modules/s3-bucket
🏷️  Versión actual: 1.0.0
🆕 Nueva versión: 1.0.1
✅ Tag creado: v1.0.1

✨ Versionado completed
Actualiza CHANGELOG.md con los cambios de esta versión
```

### Conceptos Clave

- **Semantic Versioning**: MAJOR.MINOR.PATCH para versiones
- **Git Tags**: Marcar versiones específicas
- **Version Constraints**: ~>, >=, = para dependencias
- **Module Sources**: Git, HTTP, Registry como fuentes
- **Upgrade Strategy**: Proceso para actualizar modules seguramente
- **Changelog**: Documentar cambios entre versiones

---

## Troubleshooting

### Problema 1: Module Not Found

**Error:**
```
Error: Module not installed
```

**Solution:**
```bash
# Re-inicializar para descargar modules
terraform init
terraform init -upgrade  # Forzar actualización
```

### Problema 2: Module Version Conflict

**Error:**
```
Error: Unsatisfiable version constraints
```

**Solution:**
```hcl
# Revisar version constraints en todos los modules
# Ajustar para ser compatible
module "example" {
  version = ">= 1.0, < 2.0"  # Rango más amplio
}
```

### Problema 3: Circular Dependency en Modules

**Error:**
```
Error: Cycle: module.a, module.b
```

**Solution:**
```hcl
# Red iseñar arquitectura para eliminar ciclo
# O usar depends_on explícitamente si es válido
```

### Problema 4: Output No Disponible

**Error:**
```
Error: Unsupported attribute: module.x has no attribute "y"
```

**Solution:**
```hcl
# Verificar que el output existe en el module
# Ver modules/module-name/outputs.tf
```

### Problema 5: Module Cacheado

**Problema:** Cambios en module local no se reflejan

**Solution:**
```bash
# Limpiar cache de modules
rm -rf .terraform/modules
terraform init
```

---

## Recursos Adicionales

### Documentación

- [Terraform Modules](https://www.terraform.io/docs/language/modules/index.html)
- [Module Registry](https://registry.terraform.io/)
- [Publishing Modules](https://www.terraform.io/docs/registry/modules/publish.html)
- [Module Composition](https://www.terraform.io/docs/language/modules/develop/composition.html)

### Herramientas

- [terraform-docs](https://terraform-docs.io/) - Generar documentación automática
- [pre-commit-terraform](https://github.com/antonbabenko/pre-commit-terraform) - Hooks de calidad
- [terratest](https://terratest.gruntwork.io/) - Testing framework

### Ejemplos y Templates

- [terraform-aws-modules](https://github.com/terraform-aws-modules) - Modules oficiales AWS
- [Cloud Posse Modules](https://github.com/cloudposse) - Modules enterprise-grade
- [Gruntwork Modules](https://gruntwork.io/infrastructure-as-code-library/) - Modules comerciales

### Best Practices

- [Terraform Module Best Practices](https://www.terraform-best-practices.com/code-structure)
- [Google Cloud - Terraform Modules](https://cloud.google.com/docs/terraform/best-practices-for-terraform)

---

## Próximos Steps

¡Excelente trabajo! Has dominado los modules de Terraform. Ahora sabes:

✅ Crear modules básicos reutilizables
✅ Diseñar interfaces robustas con inputs/outputs
✅ Usar modules múltiples veces eficientemente
✅ Construir modules complejos multi-recurso
✅ Consumir modules del Registry público
✅ Versionar y publicar modules propios

**Continúa con:** [Exercise 04 - Data Infrastructure](../04-data-infrastructure/README.md)

En el próximo exercise aplicarás todo lo aprendido para construir una infraestructura completa de datos con:
- Data Lake multi-capa completo
- AWS Glue para catalogado
- Athena para queries
- IAM roles y policies
- Lifecycle y cost optimization
- Tagging estratégico
