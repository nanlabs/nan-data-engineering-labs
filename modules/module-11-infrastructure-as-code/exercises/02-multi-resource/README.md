# Exercise 02: Multi-Resource Infrastructure

## Description

En este exercise avanzarás en la gestión de infraestructura compleja, aprendiendo a orquestar múltiples recursos, gestionar dependencias entre ellos, y utilizar construcciones avanzadas como `count` y `for_each`. Crearás una infraestructura de datos con múltiples buckets S3, roles IAM, y políticas de acceso.

**Estimated Duration:** 120-150 minutes

## Prerequisites

- Exercise 01 completed
- Terraform instalado y funcionando
- LocalStack corriendo
- Comprensión básica de IAM en AWS

## Objectives de Aprendizaje

Al completar este exercise serás capaz de:

1. ✅ Gestionar múltiples recursos relacionados en una misma configuration
2. ✅ Definir y manejar dependencias explícitas e implícitas
3. ✅ Utilizar `count` para crear múltiples instancias de un recurso
4. ✅ Utilizar `for_each` para crear recursos dinámicamente
5. ✅ Implementar lifecycle rules avanzadas
6. ✅ Importar recursos existentes a Terraform

---

## Task 1: Múltiples Buckets S3 con Diferentes Configuraciones

### Description

Crearás una arquitectura de Data Lake con múltiples buckets S3 para diferentes propósitos (raw data, processed data, analytics, logs), cada uno con configuraciones específicas.

### Steps

#### 1.1. Estructura del Proyecto

```bash
# Crear directorio del exercise
mkdir -p ~/terraform-exercises/02-multi-resource
cd ~/terraform-exercises/02-multi-resource

# Crear estructura de archivos
touch main.tf variables.tf outputs.tf terraform.tfvars
mkdir -p modules
```

#### 1.2. Definir Variables

<details>
<summary>📄 variables.tf - Variables para Multi-Resource</summary>

```hcl
# variables.tf
# Variables para gestión de múltiples recursos

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "datalake"
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Ambiente debe ser: development, staging, o production."
  }
}

variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "data_layers" {
  description = "Capas del Data Lake"
  type        = map(object({
    description = string
    versioning  = bool
    lifecycle_days = number
    encryption  = bool
  }))
  default = {
    bronze = {
      description    = "Raw data layer"
      versioning     = true
      lifecycle_days = 90
      encryption     = true
    }
    silver = {
      description    = "Processed data layer"
      versioning     = true
      lifecycle_days = 180
      encryption     = true
    }
    gold = {
      description    = "Analytics-ready data layer"
      versioning     = true
      lifecycle_days = 365
      encryption     = true
    }
  }
}

variable "enable_logging" {
  description = "Habilitar logging para buckets"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags comunes para todos los recursos"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "DataLake"
  }
}
```

</details>

#### 1.3. Crear Múltiples Buckets

<details>
<summary>📄 main.tf - Configuration Multi-Bucket</summary>

```hcl
# main.tf
# Infraestructura multi-bucket para Data Lake

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
    s3  = "http://localhost:4566"
    iam = "http://localhost:4566"
  }
}

# ===================================
# DATA LAKE BUCKETS
# ===================================

# Buckets para cada capa del Data Lake usando for_each
resource "aws_s3_bucket" "data_layers" {
  for_each = var.data_layers

  bucket = "${var.project_name}-${each.key}-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${each.key}"
      Layer       = each.key
      Description = each.value.description
      Environment = var.environment
    }
  )
}

# Versionamiento para cada bucket
resource "aws_s3_bucket_versioning" "data_layers_versioning" {
  for_each = var.data_layers

  bucket = aws_s3_bucket.data_layers[each.key].id

  versioning_configuration {
    status = each.value.versioning ? "Enabled" : "Disabled"
  }
}

# Encriptación para cada bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "data_layers_encryption" {
  for_each = {
    for k, v in var.data_layers : k => v if v.encryption
  }

  bucket = aws_s3_bucket.data_layers[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle rules para cada bucket
resource "aws_s3_bucket_lifecycle_configuration" "data_layers_lifecycle" {
  for_each = var.data_layers

  bucket = aws_s3_bucket.data_layers[each.key].id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = each.value.lifecycle_days
      storage_class = "GLACIER"
    }

    expiration {
      days = each.value.lifecycle_days * 2
    }
  }

  rule {
    id     = "cleanup-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Public access block para todos los buckets
resource "aws_s3_bucket_public_access_block" "data_layers_public_block" {
  for_each = var.data_layers

  bucket = aws_s3_bucket.data_layers[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ===================================
# LOGGING BUCKET
# ===================================

# Bucket para logs
resource "aws_s3_bucket" "logs" {
  count = var.enable_logging ? 1 : 0

  bucket = "${var.project_name}-logs-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "Logs Bucket"
      Purpose     = "Access Logs"
      Environment = var.environment
    }
  )
}

# Configuration de logging para cada bucket de datos
resource "aws_s3_bucket_logging" "data_layers_logging" {
  for_each = var.enable_logging ? var.data_layers : {}

  bucket = aws_s3_bucket.data_layers[each.key].id

  target_bucket = aws_s3_bucket.logs[0].id
  target_prefix = "${each.key}-logs/"
}

# ===================================
# BACKUP BUCKET
# ===================================

# Bucket para backups con configuration especial
resource "aws_s3_bucket" "backup" {
  bucket = "${var.project_name}-backup-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "Backup Bucket"
      Purpose     = "Disaster Recovery"
      Environment = var.environment
      Critical    = "true"
    }
  )

  # Lifecycle: Prevenir destrucción accidental
  lifecycle {
    prevent_destroy = false  # En producción: true
  }
}

# Object Lock para backup (prevenir eliminación)
resource "aws_s3_bucket_versioning" "backup_versioning" {
  bucket = aws_s3_bucket.backup.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

</details>

#### 1.4. Definir Outputs

<details>
<summary>📄 outputs.tf - Outputs de Múltiples Recursos</summary>

```hcl
# outputs.tf
# Outputs para la infraestructura multi-bucket

# Información de todos los buckets de datos
output "data_layer_buckets" {
  description = "Información de todos los buckets de datos"
  value = {
    for k, bucket in aws_s3_bucket.data_layers : k => {
      id     = bucket.id
      arn    = bucket.arn
      region = bucket.region
    }
  }
}

# Lista de nombres de buckets
output "bucket_names" {
  description = "Lista de nombres de todos los buckets"
  value = [
    for bucket in aws_s3_bucket.data_layers : bucket.id
  ]
}

# Bucket de logs
output "logs_bucket" {
  description = "Información del bucket de logs"
  value = var.enable_logging ? {
    id  = aws_s3_bucket.logs[0].id
    arn = aws_s3_bucket.logs[0].arn
  } : null
}

# Bucket de backup
output "backup_bucket" {
  description = "Información del bucket de backup"
  value = {
    id  = aws_s3_bucket.backup.id
    arn = aws_s3_bucket.backup.arn
  }
}

# Resumen completo
output "infrastructure_summary" {
  description = "Resumen completo de la infraestructura"
  value = {
    project           = var.project_name
    environment       = var.environment
    data_layers_count = length(aws_s3_bucket.data_layers)
    logging_enabled   = var.enable_logging
    total_buckets     = length(aws_s3_bucket.data_layers) + (var.enable_logging ? 1 : 0) + 1
  }
}
```

</details>

#### 1.5. Aplicar Configuration

```bash
# Inicializar
terraform init

# Ver plan
terraform plan

# Aplicar
terraform apply -auto-approve

# Ver outputs
terraform output
terraform output -json | jq '.'

# Verificar en LocalStack
awslocal s3 ls
```

### Output Esperado

```plaintext
Apply complete! Resources: 17 added, 0 changed, 0 destroyed.

Outputs:

bucket_names = [
  "datalake-bronze-development",
  "datalake-gold-development",
  "datalake-silver-development",
]
data_layer_buckets = {
  "bronze" = {
    "arn" = "arn:aws:s3:::datalake-bronze-development"
    "id" = "datalake-bronze-development"
    "region" = "us-east-1"
  }
  "gold" = {
    "arn" = "arn:aws:s3:::datalake-gold-development"
    "id" = "datalake-gold-development"
    "region" = "us-east-1"
  }
  "silver" = {
    "arn" = "arn:aws:s3:::datalake-silver-development"
    "id" = "datalake-silver-development"
    "region" = "us-east-1"
  }
}
infrastructure_summary = {
  "data_layers_count" = 3
  "environment" = "development"
  "logging_enabled" = true
  "project" = "datalake"
  "total_buckets" = 5
}
```

### Conceptos Clave

- **for_each**: Crear recursos dinámicamente desde un map o set
- **Conditional Resources**: Usar count para crear recursos condicionalmente
- **Resource References**: Referenciar otros recursos usando interpolación
- **Dynamic Blocks**: (Exploraremos más en tareas siguientes)

---

## Task 2: IAM Roles y Policies

### Description

Crearás roles IAM y políticas para controlar el acceso a los buckets del Data Lake, implementando principio de menor privilegio y segregación de accesos.

### Steps

#### 2.1. Crear Archivo IAM

<details>
<summary>📄 iam.tf - Roles y Políticas IAM</summary>

```hcl
# iam.tf
# Roles y políticas IAM para acceso al Data Lake

# ===================================
# DATA ENGINEERS ROLE
# ===================================

# Assume Role Policy para Data Engineers
data "aws_iam_policy_document" "data_engineer_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com", "lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Role para Data Engineers (acceso a bronze y silver)
resource "aws_iam_role" "data_engineer" {
  name               = "${var.project_name}-data-engineer-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.data_engineer_assume_role.json

  tags = merge(
    var.tags,
    {
      Name = "Data Engineer Role"
      Team = "Data Engineering"
    }
  )
}

# Policy para Data Engineers
data "aws_iam_policy_document" "data_engineer_policy" {
  # Acceso completo a bronze (raw data)
  statement {
    sid    = "BronzeFullAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.data_layers["bronze"].arn,
      "${aws_s3_bucket.data_layers["bronze"].arn}/*",
    ]
  }

  # Acceso completo a silver (processed data)
  statement {
    sid    = "SilverFullAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.data_layers["silver"].arn,
      "${aws_s3_bucket.data_layers["silver"].arn}/*",
    ]
  }

  # Solo lectura en gold (analytics)
  statement {
    sid    = "GoldReadOnly"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.data_layers["gold"].arn,
      "${aws_s3_bucket.data_layers["gold"].arn}/*",
    ]
  }
}

resource "aws_iam_policy" "data_engineer" {
  name        = "${var.project_name}-data-engineer-policy-${var.environment}"
  description = "Policy para Data Engineers"
  policy      = data.aws_iam_policy_document.data_engineer_policy.json
}

resource "aws_iam_role_policy_attachment" "data_engineer" {
  role       = aws_iam_role.data_engineer.name
  policy_arn = aws_iam_policy.data_engineer.arn
}

# ===================================
# DATA ANALYSTS ROLE
# ===================================

# Role para Data Analysts (solo lectura en gold)
resource "aws_iam_role" "data_analyst" {
  name               = "${var.project_name}-data-analyst-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.data_engineer_assume_role.json

  tags = merge(
    var.tags,
    {
      Name = "Data Analyst Role"
      Team = "Analytics"
    }
  )
}

# Policy para Data Analysts (solo lectura)
data "aws_iam_policy_document" "data_analyst_policy" {
  statement {
    sid    = "GoldReadAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:GetObjectVersion",
    ]

    resources = [
      aws_s3_bucket.data_layers["gold"].arn,
      "${aws_s3_bucket.data_layers["gold"].arn}/*",
    ]
  }

  # Acceso a queries de Athena (preparar para exercise futuro)
  statement {
    sid    = "AthenaAccess"
    effect = "Allow"

    actions = [
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StartQueryExecution",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "data_analyst" {
  name        = "${var.project_name}-data-analyst-policy-${var.environment}"
  description = "Policy para Data Analysts"
  policy      = data.aws_iam_policy_document.data_analyst_policy.json
}

resource "aws_iam_role_policy_attachment" "data_analyst" {
  role       = aws_iam_role.data_analyst.name
  policy_arn = aws_iam_policy.data_analyst.arn
}

# ===================================
# ADMIN ROLE
# ===================================

# Role para Administradores (acceso completo)
resource "aws_iam_role" "admin" {
  name               = "${var.project_name}-admin-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.data_engineer_assume_role.json

  tags = merge(
    var.tags,
    {
      Name = "Admin Role"
      Team = "Platform"
    }
  )
}

# Policy para Admins usando bucle
data "aws_iam_policy_document" "admin_policy" {
  # Acceso completo a todos los buckets del data lake
  dynamic "statement" {
    for_each = aws_s3_bucket.data_layers

    content {
      sid    = "FullAccess${title(statement.key)}"
      effect = "Allow"

      actions = ["s3:*"]

      resources = [
        statement.value.arn,
        "${statement.value.arn}/*",
      ]
    }
  }

  # Acceso a backup
  statement {
    sid    = "BackupFullAccess"
    effect = "Allow"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.backup.arn,
      "${aws_s3_bucket.backup.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "admin" {
  name        = "${var.project_name}-admin-policy-${var.environment}"
  description = "Policy para Administradores"
  policy      = data.aws_iam_policy_document.admin_policy.json
}

resource "aws_iam_role_policy_attachment" "admin" {
  role       = aws_iam_role.admin.name
  policy_arn = aws_iam_policy.admin.arn
}

# ===================================
# OUTPUTS
# ===================================

output "iam_roles" {
  description = "Roles IAM creados"
  value = {
    data_engineer = aws_iam_role.data_engineer.arn
    data_analyst  = aws_iam_role.data_analyst.arn
    admin         = aws_iam_role.admin.arn
  }
}

output "iam_policies" {
  description = "Políticas IAM creadas"
  value = {
    data_engineer = aws_iam_policy.data_engineer.arn
    data_analyst  = aws_iam_policy.data_analyst.arn
    admin         = aws_iam_policy.admin.arn
  }
}
```

</details>

#### 2.2. Aplicar Configuration IAM

```bash
# Ver plan (debería mostrar 9 nuevos recursos IAM)
terraform plan

# Aplicar
terraform apply -auto-approve

# Ver roles creados
terraform output iam_roles

# Verificar en LocalStack
awslocal iam list-roles
awslocal iam list-policies --scope Local
```

### Output Esperado

```plaintext
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:

iam_policies = {
  "admin" = "arn:aws:iam::000000000000:policy/datalake-admin-policy-development"
  "data_analyst" = "arn:aws:iam::000000000000:policy/datalake-data-analyst-policy-development"
  "data_engineer" = "arn:aws:iam::000000000000:policy/datalake-data-engineer-policy-development"
}
iam_roles = {
  "admin" = "arn:aws:iam::000000000000:role/datalake-admin-development"
  "data_analyst" = "arn:aws:iam::000000000000:role/datalake-data-analyst-development"
  "data_engineer" = "arn:aws:iam::000000000000:role/datalake-data-engineer-development"
}
```

### Conceptos Clave

- **data Source**: Obtener información existente o generar documentos (iam_policy_document)
- **dynamic Blocks**: Generar bloques dinámicamente con for_each
- **Policy Documents**: Definir políticas IAM de forma declarativa
- **Role Attachments**: Adjuntar políticas a roles

---

## Task 3: Dependencies Explícitas e Implícitas

### Description

You will learn a gestionar el orden de creación de recursos usando dependencias implícitas (referencias) y explícitas (`depends_on`).

### Steps

#### 3.1. Crear Archivo de Dependencias

<details>
<summary>📄 dependencies.tf - Gestión de Dependencias</summary>

```hcl
# dependencies.tf
# Ejemplos de dependencias explícitas e implícitas

# ===================================
# BUCKET CON NOTIFICACIONES
# ===================================

# Bucket que recibirá datos
resource "aws_s3_bucket" "incoming_data" {
  bucket = "${var.project_name}-incoming-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name    = "Incoming Data Bucket"
      Purpose = "Data Ingestion"
    }
  )
}

# SNS Topic para notificaciones (recurso independiente)
resource "aws_sns_topic" "bucket_notifications" {
  name = "${var.project_name}-bucket-notifications-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name    = "Bucket Notifications Topic"
      Purpose = "S3 Event Notifications"
    }
  )
}

# Policy para que S3 pueda publicar en SNS
# DEPENDENCIA IMPLÍCITA: Referencia a aws_s3_bucket.incoming_data y aws_sns_topic
data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.bucket_notifications.arn]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.incoming_data.arn]
    }
  }
}

resource "aws_sns_topic_policy" "bucket_notifications" {
  arn    = aws_sns_topic.bucket_notifications.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

# Notificaciones del bucket
# DEPENDENCIA EXPLÍCITA: Necesita que la policy del topic exista primero
resource "aws_s3_bucket_notification" "incoming_data_notification" {
  bucket = aws_s3_bucket.incoming_data.id

  # DEPENDENCIA EXPLÍCITA usando depends_on
  depends_on = [aws_sns_topic_policy.bucket_notifications]

  topic {
    topic_arn = aws_sns_topic.bucket_notifications.arn
    events    = ["s3:ObjectCreated:*"]
  }
}

# ===================================
# PROCESAMIENTO EN CADENA
# ===================================

# Bucket para procesamiento temporal
resource "aws_s3_bucket" "processing_temp" {
  bucket = "${var.project_name}-processing-temp-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name    = "Processing Temp Bucket"
      Purpose = "Temporary Processing"
    }
  )
}

# Lifecycle que limpia archivos temporales
# DEPENDENCIA IMPLÍCITA: Necesita que el bucket exista
resource "aws_s3_bucket_lifecycle_configuration" "processing_temp_lifecycle" {
  bucket = aws_s3_bucket.processing_temp.id

  rule {
    id     = "cleanup-temp-files"
    status = "Enabled"

    expiration {
      days = 1  # Eliminar después de 1 día
    }
  }
}

# Role para procesamiento
# DEPENDENCIA IMPLÍCITA: Referencias a buckets
resource "aws_iam_role" "processor" {
  name = "${var.project_name}-processor-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "Processor Role"
    }
  )
}

# Policy que permite leer de incoming y escribir a processing_temp
# DEPENDENCIA IMPLÍCITA: Referencia a múltiples buckets
resource "aws_iam_policy" "processor" {
  name        = "${var.project_name}-processor-policy-${var.environment}"
  description = "Policy para procesador"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadFromIncoming"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.incoming_data.arn,
          "${aws_s3_bucket.incoming_data.arn}/*"
        ]
      },
      {
        Sid    = "WriteToTemp"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.processing_temp.arn}/*"
        ]
      },
      {
        Sid    = "WriteToDataLayers"
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        # DEPENDENCIA IMPLÍCITA: for expression con buckets
        Resource = [
          for bucket in aws_s3_bucket.data_layers : "${bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "processor" {
  role       = aws_iam_role.processor.name
  policy_arn = aws_iam_policy.processor.arn
}

# ===================================
# NULL RESOURCE PARA DEPENDENCIAS COMPLEJAS
# ===================================

# Null resource que espera a que toda la infraestructura esté lista
resource "null_resource" "infrastructure_ready" {
  # DEPENDENCIA EXPLÍCITA: Espera a múltiples recursos
  depends_on = [
    aws_s3_bucket.data_layers,
    aws_s3_bucket.incoming_data,
    aws_s3_bucket.processing_temp,
    aws_iam_role.data_engineer,
    aws_iam_role.data_analyst,
    aws_iam_role.processor,
    aws_s3_bucket_notification.incoming_data_notification,
  ]

  # Trigger: Se ejecuta cuando cambia cualquier bucket
  triggers = {
    bucket_ids = join(",", [
      for bucket in aws_s3_bucket.data_layers : bucket.id
    ])
  }

  # Provisioner que se ejecuta cuando todo está listo
  provisioner "local-exec" {
    command = <<EOT
      echo "✅ Infraestructura completa desplegada"
      echo "Buckets de datos: ${length(aws_s3_bucket.data_layers)}"
      echo "Roles IAM: 4"
      echo "Timestamp: $(date)"
    EOT
  }
}

# ===================================
# OUTPUTS
# ===================================

output "dependency_chain" {
  description = "Cadena de dependencias"
  value = {
    incoming_bucket    = aws_s3_bucket.incoming_data.id
    notification_topic = aws_sns_topic.bucket_notifications.arn
    processor_role     = aws_iam_role.processor.arn
    temp_bucket        = aws_s3_bucket.processing_temp.id
  }
}
```

</details>

#### 3.2. Visualizar Dependencias

<details>
<summary>📄 visualize-dependencies.sh - Visualizar Graph</summary>

```bash
#!/bin/bash
# Script para visualizar dependencias de Terraform

echo "=== Generando Graph de Dependencias ==="

# Instalar graphviz si no está instalado
if ! command -v dot &> /dev/null; then
    echo "Instalando graphviz..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y graphviz
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install graphviz
    fi
fi

# Generar graph
terraform graph > dependency-graph.dot

# Convertir a formato visual
terraform graph | dot -Tpng > dependency-graph.png
terraform graph | dot -Tsvg > dependency-graph.svg

echo "✅ Graphs generados:"
echo "  - dependency-graph.dot (texto)"
echo "  - dependency-graph.png (imagen)"
echo "  - dependency-graph.svg (svg)"

# Abrir imagen (opcional)
if command -v xdg-open &> /dev/null; then
    xdg-open dependency-graph.png
elif command -v open &> /dev/null; then
    open dependency-graph.png
fi
```

</details>

```bash
# Aplicar recursos con dependencias
terraform apply -auto-approve

# Generar y visualizar graph
chmod +x visualize-dependencies.sh
./visualize-dependencies.sh

# Ver orden de creación en los logs
terraform apply -auto-approve 2>&1 | grep "Creating..."
```

### Output Esperado

```plaintext
null_resource.infrastructure_ready: Creating...
null_resource.infrastructure_ready: Provisioning with 'local-exec'...
null_resource.infrastructure_ready (local-exec): ✅ Infraestructura completa desplegada
null_resource.infrastructure_ready (local-exec): Buckets de datos: 3
null_resource.infrastructure_ready (local-exec): Roles IAM: 4
null_resource.infrastructure_ready (local-exec): Timestamp: 2024-03-07 10:30:00

Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
```

### Conceptos Clave

- **Implicit Dependencies**: Terraform detecta automáticamente cuando un recurso referencia a otro
- **Explicit Dependencies**: `depends_on` para forzar orden cuando no hay referencia directa
- **null_resource**: Recurso ficticio útil para dependencias y provisioners
- **terraform graph**: Visualizar el grafo de dependencias

---

## Task 4: Count y For_Each

### Description

Dominarás las construcciones `count` y `for_each` para crear recursos dinámicamente, entendiendo cuándo usar cada una.

### Steps

#### 4.1. Crear Archivo de Ejemplos

<details>
<summary>📄 count-foreach.tf - Count vs For_Each</summary>

```hcl
# count-foreach.tf
# Comparación y ejemplos de count vs for_each

# ===================================
# EJEMPLO 1: COUNT
# ===================================

# Variables para ejemplos
variable "environment_count" {
  description = "Número de ambientes"
  type        = number
  default     = 3
}

variable "environments_list" {
  description = "Lista de ambientes"
  type        = list(string)
  default     = ["dev", "staging", "prod"]
}

# Usar COUNT: Crear N buckets idénticos
resource "aws_s3_bucket" "count_example" {
  count = var.environment_count

  bucket = "${var.project_name}-count-example-${count.index}"

  tags = merge(
    var.tags,
    {
      Name  = "Count Example ${count.index}"
      Index = count.index
    }
  )
}

# Problema con COUNT: Si eliminas un elemento del medio, recrea todos los siguientes
# Por ejemplo, eliminar el ambiente 1 haría que:
#   - Bucket índice 1 se destruya
#   - Bucket índice 2 se destruya y recree como índice 1
#   - Bucket índice 3 se destruya y recree como índice 2

# ===================================
# EJEMPLO 2: FOR_EACH con LIST (convertida a SET)
# ===================================

# Usar FOR_EACH con lista: Mejor para elementos con identidad
resource "aws_s3_bucket" "foreach_list_example" {
  for_each = toset(var.environments_list)

  bucket = "${var.project_name}-foreach-${each.value}"

  tags = merge(
    var.tags,
    {
      Name        = "ForEach Example - ${each.value}"
      Environment = each.value
      Key         = each.key  # En set, key == value
    }
  )
}

# Ventaja de FOR_EACH: Eliminar "staging" solo destruye ese bucket,
# no afecta a "dev" ni "prod"

# ===================================
# EJEMPLO 3: FOR_EACH con MAP (más potente)
# ===================================

variable "app_buckets" {
  description = "Buckets para aplicaciones con configuration específica"
  type = map(object({
    versioning = bool
    lifecycle_days = number
    purpose = string
  }))
  default = {
    web_assets = {
      versioning     = false
      lifecycle_days = 30
      purpose        = "Static website assets"
    }
    user_uploads = {
      versioning     = true
      lifecycle_days = 90
      purpose        = "User generated content"
    }
    api_responses = {
      versioning     = false
      lifecycle_days = 7
      purpose        = "Cached API responses"
    }
  }
}

# FOR_EACH con MAP: Configuration específica por recurso
resource "aws_s3_bucket" "app_buckets" {
  for_each = var.app_buckets

  bucket = "${var.project_name}-${each.key}-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "App Bucket - ${each.key}"
      Purpose     = each.value.purpose
      Environment = var.environment
    }
  )
}

resource "aws_s3_bucket_versioning" "app_buckets_versioning" {
  for_each = {
    for k, v in var.app_buckets : k => v if v.versioning
  }

  bucket = aws_s3_bucket.app_buckets[each.key].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "app_buckets_lifecycle" {
  for_each = var.app_buckets

  bucket = aws_s3_bucket.app_buckets[each.key].id

  rule {
    id     = "expire-old-files"
    status = "Enabled"

    expiration {
      days = each.value.lifecycle_days
    }
  }
}

# ===================================
# EJEMPLO 4: COUNT CONDICIONAL
# ===================================

variable "create_monitoring" {
  description = "Crear bucket de monitoreo"
  type        = bool
  default     = true
}

# COUNT para recursos condicionales (0 o 1)
resource "aws_s3_bucket" "monitoring" {
  count = var.create_monitoring ? 1 : 0

  bucket = "${var.project_name}-monitoring-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name    = "Monitoring Bucket"
      Purpose = "Metrics and Logs"
    }
  )
}

# Referencia a recurso con count: usar [0]
output "monitoring_bucket" {
  description = "Bucket de monitoreo (si existe)"
  value       = var.create_monitoring ? aws_s3_bucket.monitoring[0].id : "Not created"
}

# ===================================
# EJEMPLO 5: FOR_EACH AVANZADO
# ===================================

# Crear buckets para múltiples proyectos y ambientes
variable "projects" {
  description = "Proyectos con sus ambientes"
  type = map(list(string))
  default = {
    api = ["dev", "prod"]
    web = ["dev", "staging", "prod"]
    ml  = ["dev"]
  }
}

# Flatten: Convertir estructura compleja en flat map
locals {
  # Crear combinaciones proyecto-ambiente
  project_envs = flatten([
    for project, envs in var.projects : [
      for env in envs : {
        project = project
        env     = env
        key     = "${project}-${env}"
      }
    ]
  ])

  # Convertir a map para for_each
  project_envs_map = {
    for item in local.project_envs : item.key => item
  }
}

resource "aws_s3_bucket" "project_environments" {
  for_each = local.project_envs_map

  bucket = "${var.project_name}-${each.value.project}-${each.value.env}"

  tags = merge(
    var.tags,
    {
      Name        = "${each.value.project} - ${each.value.env}"
      Project     = each.value.project
      Environment = each.value.env
    }
  )
}

# ===================================
# OUTPUTS COMPARATIVOS
# ===================================

output "count_example_buckets" {
  description = "Buckets creados con count (lista)"
  value       = aws_s3_bucket.count_example[*].id
}

output "foreach_list_example_buckets" {
  description = "Buckets creados con for_each list (map)"
  value = {
    for k, bucket in aws_s3_bucket.foreach_list_example : k => bucket.id
  }
}

output "app_buckets" {
  description = "Buckets de aplicaciones"
  value = {
    for k, bucket in aws_s3_bucket.app_buckets : k => {
      id             = bucket.id
      versioning     = contains(keys(aws_s3_bucket_versioning.app_buckets_versioning), k)
      lifecycle_days = var.app_buckets[k].lifecycle_days
    }
  }
}

output "project_environment_buckets" {
  description = "Buckets por proyecto y ambiente"
  value = {
    for k, bucket in aws_s3_bucket.project_environments : k => bucket.id
  }
}

# ===================================
# COMPARATIVA: CUÁNDO USAR QUÉ
# ===================================

# COUNT:
# ✅ Recursos idénticos
# ✅ Número fijo conocido de antemano
# ✅ Recursos condicionales (0 o 1)
# ❌ Cuando el orden importa
# ❌ Cuando puedes remover del medio

# FOR_EACH:
# ✅ Recursos con identidad única (key)
# ✅ Configuration diferente por recurso
# ✅ Lista dinámica que puede cambiar
# ✅ Map con configuraciones complejas
# ❌ Cuando necesitas índice numérico
```

</details>

#### 4.2. Experimentar con Count y For_Each

<details>
<summary>📄 test-count-foreach.sh - Script de Prueba</summary>

```bash
#!/bin/bash
# Script para experimentar con count y for_each

set -e

echo "=== Experimento: Count vs For_Each ==="

# 1. Aplicar configuration inicial
echo -e "\n1️⃣  Aplicando configuration inicial..."
terraform apply -auto-approve

# 2. Listar buckets creados con count
echo -e "\n2️⃣  Buckets creados con COUNT:"
terraform output count_example_buckets

# 3. Listar buckets creados con for_each
echo -e "\n3️⃣  Buckets creados con FOR_EACH:"
terraform output foreach_list_example_buckets

# 4. Listar todos los buckets
echo -e "\n4️⃣  Todos los buckets en LocalStack:"
awslocal s3 ls

# 5. Simulación: Remover elemento del medio con COUNT
echo -e "\n5️⃣  PROBLEMA CON COUNT: Remover elemento del medio..."
echo "Cambiando environment_count de 3 a 2..."
# (En la práctica, editarías terraform.tfvars)
# Esto haría que el bucket con índice 2 se destruya
terraform plan -var="environment_count=2"

# 6. Simulación: Remover elemento con FOR_EACH
echo -e "\n6️⃣  VENTAJA FOR_EACH: Remover elemento específico..."
echo "Removiendo 'staging' de la lista..."
# (En la práctica, editarías terraform.tfvars)
# Esto solo destruye el bucket 'staging', no afecta a los demás
terraform plan -var='environments_list=["dev","prod"]'

echo -e "\n✅ Experimento completed"
echo "Observa las diferencias en los planes de Terraform"
```

</details>

```bash
# Aplicar y experimentar
terraform apply -auto-approve

# Ejecutar experimento
chmod +x test-count-foreach.sh
./test-count-foreach.sh
```

### Output Esperado

```plaintext
count_example_buckets = [
  "datalake-count-example-0",
  "datalake-count-example-1",
  "datalake-count-example-2",
]

foreach_list_example_buckets = {
  "dev" = "datalake-foreach-dev"
  "prod" = "datalake-foreach-prod"
  "staging" = "datalake-foreach-staging"
}

app_buckets = {
  "api_responses" = {
    "id" = "datalake-api_responses-development"
    "lifecycle_days" = 7
    "versioning" = false
  }
  "user_uploads" = {
    "id" = "datalake-user_uploads-development"
    "lifecycle_days" = 90
    "versioning" = true
  }
  "web_assets" = {
    "id" = "datalake-web_assets-development"
    "lifecycle_days" = 30
    "versioning" = false
  }
}
```

### Conceptos Clave

- **count**: Índice numérico, mejor para N recursos idénticos
- **for_each**: Map o set, mejor para recursos con identidad única
- **toset()**: Convertir lista a set para for_each
- **Splat operator (*)**:Referencia a todos los elementos de count
- **locals**: Transformaciones complejas de datos

---

## Task 5: Lifecycle Rules

### Description

Explorarás las lifecycle rules de Terraform que controlan el comportamiento de creación, actualización y destrucción de recursos.

### Steps

#### 5.1. Crear Archivo de Lifecycle

<details>
<summary>📄 lifecycle-rules.tf - Lifecycle Configuration</summary>

```hcl
# lifecycle-rules.tf
# Ejemplos completos de lifecycle rules

# ===================================
# 1. PREVENT_DESTROY
# ===================================

# Bucket critico que NO debe ser destruido
resource "aws_s3_bucket" "critical_data" {
  bucket = "${var.project_name}-critical-data-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name     = "Critical Data - NO DELETE"
      Critical = "true"
      Backup   = "required"
    }
  )

  lifecycle {
    # Prevenir destrucción accidental
    prevent_destroy = false  # true en producción

    # Si intentas terraform destroy, obtendrás un error:
    # Error: Instance cannot be destroyed
  }
}

# ===================================
# 2. CREATE_BEFORE_DESTROY
# ===================================

# Bucket que debe tener zero downtime en recreación
resource "aws_s3_bucket" "zero_downtime" {
  bucket = "${var.project_name}-zero-downtime-${var.environment}-v2"

  tags = merge(
    var.tags,
    {
      Name        = "Zero Downtime Bucket"
      Version     = "2"
      UseCase     = "High Availability"
    }
  )

  lifecycle {
    # Crear nuevo recurso ANTES de destruir el antiguo
    create_before_destroy = true

    # Útil para recursos que other recursos dependen activamente
    # Evita ventanas de indisponibilidad
  }
}

# ===================================
# 3. IGNORE_CHANGES
# ===================================

# Bucket que permite cambios manuales en ciertos atributos
resource "aws_s3_bucket" "hybrid_management" {
  bucket = "${var.project_name}-hybrid-mgmt-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name           = "Hybrid Management"
      ManagedBy      = "Terraform"
      # Estos tags pueden ser modificados manualmente
      LastAccessed   = "manual"
      MaintenanceWin = "manual"
    }
  )

  lifecycle {
    # Ignorar cambios en tags específicos
    ignore_changes = [
      tags["LastAccessed"],
      tags["MaintenanceWin"],
      tags["Cost"],  # Si se agrega manualmente
    ]

    # Terraform no revertirá cambios manuales en estos atributos
  }
}

# ===================================
# 4. REPLACE_TRIGGERED_BY
# ===================================

# Recursos que se recrean cuando otro cambia (Terraform 1.2+)
resource "aws_s3_bucket" "primary" {
  bucket = "${var.project_name}-primary-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name = "Primary Bucket"
      Type = "primary"
    }
  )
}

# Este bucket se recrea si el primary cambia
resource "aws_s3_bucket" "replica" {
  bucket = "${var.project_name}-replica-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name       = "Replica Bucket"
      Type       = "replica"
      ReplicaOf  = aws_s3_bucket.primary.id
    }
  )

  lifecycle {
    # Recrear este recurso si primary es reemplazado (Terraform 1.2+)
    # replace_triggered_by = [aws_s3_bucket.primary]

    # Nota: Esta feature requiere Terraform >= 1.2
    # Para versiones anteriores, usar null_resource con triggers
  }
}

# ===================================
# 5. PRECONDITION y POSTCONDITION
# ===================================

# Bucket con validaciones de lifecycle (Terraform 1.2+)
variable "data_retention_days" {
  description = "Días de retención de datos"
  type        = number
  default     = 30
}

resource "aws_s3_bucket" "validated" {
  bucket = "${var.project_name}-validated-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name           = "Validated Bucket"
      RetentionDays  = var.data_retention_days
    }
  )

  lifecycle {
    # Precondición: Validar ANTES de crear/modificar
    precondition {
      condition     = var.data_retention_days >= 7
      error_message = "Los datos deben retenerse mínimo 7 días (compliance requirement)."
    }

    precondition {
      condition     = var.data_retention_days <= 2555  # ~7 años
      error_message = "Retención máxima es 7 años (2555 días)."
    }

    # Postcondición: Validar DESPUÉS de crear
    postcondition {
      condition     = self.bucket_domain_name != ""
      error_message = "El bucket no se creó correctamente (domain name vacío)."
    }
  }
}

# ===================================
# 6. COMBINANDO MÚLTIPLES RULES
# ===================================

# Bucket con múltiples lifecycle rules
resource "aws_s3_bucket" "complex_lifecycle" {
  bucket = "${var.project_name}-complex-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "Complex Lifecycle Bucket"
      Environment = var.environment
      Managed     = "terraform"
      CostCenter  = "analytics"
    }
  )

  lifecycle {
    # 1. Crear antes de destruir (zero downtime)
    create_before_destroy = true

    # 2. Ignorar cambios en tags de costo (agregados por AWS Cost Explorer)
    ignore_changes = [
      tags["CostCenter"],
      tags["CostAllocation"],
      tags["aws:createdBy"],
    ]

    # 3. Prevenir destrucción en producción
    prevent_destroy = var.environment == "production"

    # 4. Precondiciones
    precondition {
      condition     = var.environment != ""
      error_message = "El ambiente no puede estar vacío."
    }
  }
}

# ===================================
# 7. NULL_RESOURCE CON TRIGGERS
# ===================================

# Alternativa para replace_triggered_by en versiones antiguas
resource "null_resource" "bucket_config_monitor" {
  # Triggers: Se ejecuta cuando cambian estos valores
  triggers = {
    bucket_id   = aws_s3_bucket.primary.id
    bucket_tags = jsonencode(aws_s3_bucket.primary.tags)
    timestamp   = timestamp()  # Siempre cambia (para testing)
  }

  # Provisioner que se ejecuta en cada cambio
  provisioner "local-exec" {
    command = <<EOT
      echo "🔄 Configuration del bucket cambió"
      echo "Bucket ID: ${aws_s3_bucket.primary.id}"
      echo "Timestamp: ${timestamp()}"

      # Aquí podrías ejecutar scripts de sincronización, notificaciones, etc.
    EOT
  }
}

# ===================================
# OUTPUTS
# ===================================

output "lifecycle_examples" {
  description = "Ejemplos de lifecycle rules"
  value = {
    critical_data = {
      id              = aws_s3_bucket.critical_data.id
      prevent_destroy = "enabled (false para demo)"
    }
    zero_downtime = {
      id  = aws_s3_bucket.zero_downtime.id
      cbd = "create_before_destroy enabled"
    }
    hybrid_management = {
      id             = aws_s3_bucket.hybrid_management.id
      ignore_changes = "tags[LastAccessed, MaintenanceWin]"
    }
    validated = {
      id                = aws_s3_bucket.validated.id
      retention_days    = var.data_retention_days
      has_preconditions = true
    }
  }
}
```

</details>

#### 5.2. Probar Lifecycle Rules

<details>
<summary>📄 test-lifecycle.sh - Pruebas de Lifecycle</summary>

```bash
#!/bin/bash
# Script para probar lifecycle rules

set -e

echo "=== Pruebas de Lifecycle Rules ==="

# 1. Aplicar configuration
echo -e "\n1️⃣  Aplicando configuration con lifecycle rules..."
terraform apply -auto-approve

# 2. Intentar destruir bucket con prevent_destroy
echo -e "\n2️⃣  Intentando destruir bucket crítico (debería fallar)..."
# Descomentar para probar en producción:
# terraform destroy -target=aws_s3_bucket.critical_data

# 3. Probar ignore_changes
echo -e "\n3️⃣  Modificando tag manual en hybrid_management bucket..."
awslocal s3api put-bucket-tagging \
  --bucket datalake-hybrid-mgmt-development \
  --tagging 'TagSet=[{Key=LastAccessed,Value=2024-03-07},{Key=ManagedBy,Value=Terraform}]'

echo "Tags actuales:"
awslocal s3api get-bucket-tagging --bucket datalake-hybrid-mgmt-development

echo -e "\nEjecutando terraform plan (no debería detectar cambio en LastAccessed):"
terraform plan -target=aws_s3_bucket.hybrid_management

# 4. Probar validaciones
echo -e "\n4️⃣  Probando validaciones (preconditions)..."
echo "Intentando con retention_days=3 (debería fallar)..."
terraform plan -var="data_retention_days=3" -target=aws_s3_bucket.validated || echo "❌ Falló como esperado"

echo -e "\nIntet ando con retention_days=30 (debería pasar)..."
terraform plan -var="data_retention_days=30" -target=aws_s3_bucket.validated

# 5. Ver triggers de null_resource
echo -e "\n5️⃣  Triggers del null_resource:"
terraform state show null_resource.bucket_config_monitor | grep -A 3 "triggers"

echo -e "\n✅ Pruebas de lifecycle completadas"
```

</details>

```bash
# Ejecutar pruebas
chmod +x test-lifecycle.sh
./test-lifecycle.sh
```

### Output Esperado

```plaintext
# Cuando prevent_destroy está habilitado:
Error: Instance cannot be destroyed

on lifecycle-rules.tf line 8, in resource "aws_s3_bucket" "critical_data":
   8: resource "aws_s3_bucket" "critical_data" {

Resource aws_s3_bucket.critical_data has lifecycle.prevent_destroy set,
but the plan calls for this resource to be destroyed.

# Cuando ignore_changes funciona:
No changes. Your infrastructure matches the configuration.

# Cuandovalidation falla:
Error: Resource precondition failed

on lifecycle-rules.tf line 95, in resource "aws_s3_bucket" "validated":
   95:     precondition {
   96:       condition     = var.data_retention_days >= 7
   97:       error_message = "Los datos deben retenerse mínimo 7 días (compliance requirement)."
   98:     }

Los datos deben retenerse mínimo 7 días (compliance requirement).
```

### Conceptos Clave

- **prevent_destroy**: Protección contra eliminación accidental
- **create_before_destroy**: Evitar downtime en recreaciones
- **ignore_changes**: Permitir drift en atributos específicos
- **precondition/postcondition**: Validaciones en lifecycle (Terraform 1.2+)
- **null_resource triggers**: Ejecutar acciones en cambios específicos

---

## Task 6: Importing Existing Resources

### Description

You will learn a importar recursos existentes (creados fuera de Terraform) a tu configuration de Terraform, permitiendo gestionar infraestructura legacy.

### Steps

#### 6.1. Crear Recursos Manualmente

<details>
<summary>📄 create-manual-resources.sh - Crear Recursos Existentes</summary>

```hcl
#!/bin/bash
# Script para crear recursos "existentes" (simulación)

set -e

echo "=== Creando recursos 'existentes' fuera de Terraform ==="

# 1. Crear bucket manualmente con AWS CLI
echo -e "\n1️⃣  Creando bucket existente..."
awslocal s3 mb s3://legacy-bucket-to-import

# 2. Configurar versionamiento
echo -e "\n2️⃣  Habilitando versionamiento..."
awslocal s3api put-bucket-versioning \
  --bucket legacy-bucket-to-import \
  --versioning-configuration Status=Enabled

# 3. Agregar tags
echo -e "\n3️⃣  Agregando tags..."
awslocal s3api put-bucket-tagging \
  --bucket legacy-bucket-to-import \
  --tagging 'TagSet=[
    {Key=Name,Value=Legacy Bucket},
    {Key=CreatedBy,Value=Manual},
    {Key=Purpose,Value=Import Demo}
  ]'

# 4. Crear rol IAM manualmente
echo -e "\n4️⃣  Creando rol IAM existente..."
awslocal iam create-role \
  --role-name legacy-role-to-import \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 5. Crear policy y adjuntar al rol
echo -e "\n5️⃣  Creando y adjuntando policy..."
awslocal iam create-policy \
  --policy-name legacy-policy-to-import \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": "*"
    }]
  }'

POLICY_ARN=$(awslocal iam list-policies --scope Local --query 'Policies[?PolicyName==`legacy-policy-to-import`].Arn' --output text)

awslocal iam attach-role-policy \
  --role-name legacy-role-to-import \
  --policy-arn "$POLICY_ARN"

# 6. Listar recursos creados
echo -e "\n6️⃣  Recursos existentes creados:"
echo "Buckets:"
awslocal s3 ls
echo -e "\nRoles:"
awslocal iam list-roles --query 'Roles[?RoleName==`legacy-role-to-import`].RoleName' --output text

echo -e "\n✅ Recursos 'existentes' creados exitosamente"
echo "Ahora puedes importarlos a Terraform"
```

</details>

```bash
# Crear recursos existentes
chmod +x create-manual-resources.sh
./create-manual-resources.sh
```

#### 6.2. Escribir Configuration para Import

<details>
<summary>📄 import.tf - Configuration para Recursos Importados</summary>

```hcl
# import.tf
# Configuration para recursos que serán importados

# ===================================
# BUCKET A IMPORTAR
# ===================================

# 1. Primero, escribir la configuration que MATCHEA el recurso existente
resource "aws_s3_bucket" "imported_legacy" {
  bucket = "legacy-bucket-to-import"

  tags = {
    Name      = "Legacy Bucket"
    CreatedBy = "Manual"
    Purpose   = "Import Demo"
    ManagedBy = "Terraform"  # Agregamos este tag después del import
  }

  # Nota: La configuration debe matchear el estado actual del recurso
  # Si no matchea, terraform plan mostrará diferencias después del import
}

# 2. También importamos su versionamiento
resource "aws_s3_bucket_versioning" "imported_legacy_versioning" {
  bucket = aws_s3_bucket.imported_legacy.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ===================================
# ROL IAM A IMPORTAR
# ===================================

resource "aws_iam_role" "imported_legacy" {
  name = "legacy-role-to-import"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name      = "Legacy Role"
    ManagedBy = "Terraform"
  }
}

# Policy adjunta al rol
resource "aws_iam_policy" "imported_legacy" {
  name        = "legacy-policy-to-import"
  description = "Legacy policy imported to Terraform"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "imported_legacy" {
  role       = aws_iam_role.imported_legacy.name
  policy_arn = aws_iam_policy.imported_legacy.arn
}

# ===================================
# OUTPUTS
# ===================================

output "imported_resources" {
  description = "Recursos importados"
  value = {
    bucket = {
      id  = aws_s3_bucket.imported_legacy.id
      arn = aws_s3_bucket.imported_legacy.arn
    }
    role = {
      name = aws_iam_role.imported_legacy.name
      arn  = aws_iam_role.imported_legacy.arn
    }
  }
}
```

</details>

#### 6.3. Importar Recursos

<details>
<summary>📄 import-resources.sh - Script de Importación</summary>

```bash
#!/bin/bash
# Script para importar recursos existentes a Terraform

set -e

echo "=== Importando Recursos Existentes a Terraform ==="

# 1. Verificar que los recursos existen
echo -e "\n1️⃣  Verificando recursos existentes..."
awslocal s3 ls | grep legacy-bucket-to-import || echo "❌ Bucket no encontrado"
awslocal iam get-role --role-name legacy-role-to-import || echo "❌ Rol no encontrado"

# 2. Importar bucket S3
echo -e "\n2️⃣  Importando bucket S3..."
terraform import aws_s3_bucket.imported_legacy legacy-bucket-to-import

# 3. Importar versionamiento del bucket
echo -e "\n3️⃣  Importando versionamiento..."
terraform import aws_s3_bucket_versioning.imported_legacy_versioning legacy-bucket-to-import

# 4. Importar rol IAM
echo -e "\n4️⃣  Importando rol IAM..."
terraform import aws_iam_role.imported_legacy legacy-role-to-import

# 5. Importar policy
echo -e "\n5️⃣  Importando policy IAM..."
# Obtener ARN de la policy
POLICY_ARN=$(awslocal iam list-policies --scope Local --query 'Policies[?PolicyName==`legacy-policy-to-import`].Arn' --output text)
terraform import aws_iam_policy.imported_legacy "$POLICY_ARN"

# 6. Importar role policy attachment
echo -e "\n6️⃣  Importando role policy attachment..."
terraform import aws_iam_role_policy_attachment.imported_legacy "legacy-role-to-import/$POLICY_ARN"

# 7. Verificar con terraform plan
echo -e "\n7️⃣  Verificando con terraform plan..."
terraform plan -target=aws_s3_bucket.imported_legacy \
              -target=aws_s3_bucket_versioning.imported_legacy_versioning \
              -target=aws_iam_role.imported_legacy \
              -target=aws_iam_policy.imported_legacy \
              -target=aws_iam_role_policy_attachment.imported_legacy

# 8. Ver state
echo -e "\n8️⃣  Recursos en el state después del import:"
terraform state list | grep imported

echo -e "\n✅ Importación completada"
echo "Los recursos ahora están gestionados por Terraform"
```

</details>

```bash
# Ejecutar importación
chmod +x import-resources.sh
./import-resources.sh
```

#### 6.4. Importación Masiva con Script

<details>
<summary>📄 bulk-import.sh - Importación en Lote</summary>

```bash
#!/bin/bash
# Script para importar múltiples recursos en lote

set -e

echo "=== Importación Masiva de Recursos ==="

# Array de recursos a importar
declare -A RESOURCES=(
  ["aws_s3_bucket.imported_legacy"]="legacy-bucket-to-import"
  ["aws_s3_bucket_versioning.imported_legacy_versioning"]="legacy-bucket-to-import"
  ["aws_iam_role.imported_legacy"]="legacy-role-to-import"
)

# Función para importar con retry
import_resource() {
  local resource_address=$1
  local resource_id=$2
  local max_retries=3
  local retry=0

  echo "Importando: $resource_address ($resource_id)"

  while [ $retry -lt $max_retries ]; do
    if terraform import "$resource_address" "$resource_id" 2>&1; then
      echo "✅ Importado: $resource_address"
      return 0
    else
      retry=$((retry + 1))
      echo "⚠️  Reintento $retry/$max_retries..."
      sleep 2
    fi
  done

  echo "❌ Falló después de $max_retries intentos: $resource_address"
  return 1
}

# Importar todos los recursos
echo "Comenzando importación en lote..."
for resource_address in "${!RESOURCES[@]}"; do
  resource_id="${RESOURCES[$resource_address]}"
  import_resource "$resource_address" "$resource_id" || true
done

# Verificar imports
echo -e "\n=== Recursos Importados ==="
terraform state list | grep imported

# Generar reporte
echo -e "\n=== Reporte de Importación ===" > import-report.txt
date >> import-report.txt
echo -e "\nRecursos importados:" >> import-report.txt
terraform state list | grep imported >> import-report.txt
echo -e "\n✅ Reporte generado: import-report.txt"
```

</details>

#### 6.5. Herramienta Alternativa: Terraformer

```bash
# Terraformer: Herramienta para importar infraestructura completa automáticamente

# Instalar Terraformer
# Linux:
curl -LO https://github.com/GoogleCloudPlatform/terraformer/releases/download/$(curl -s https://api.github.com/repos/GoogleCloudPlatform/terraformer/releases/latest | grep tag_name | cut -d '"' -f 4)/terraformer-linux-amd64
chmod +x terraformer-linux-amd64
sudo mv terraformer-linux-amd64 /usr/local/bin/terraformer

# Ejemplo de uso (requiere AWS real, no LocalStack):
# terraformer import aws --resources=s3,iam --regions=us-east-1

# Terraformer genera automáticamente:
# - Archivos .tf con la configuration
# - terraform.tfstate con los recursos importados
```

### Output Esperado

```plaintext
=== Importando Recursos Existentes a Terraform ===

2️⃣  Importando bucket S3...
aws_s3_bucket.imported_legacy: Importing from ID "legacy-bucket-to-import"...
aws_s3_bucket.imported_legacy: Import prepared!
aws_s3_bucket.imported_legacy: Import complete!

3️⃣  Importando versionamiento...
aws_s3_bucket_versioning.imported_legacy_versioning: Import prepared!
aws_s3_bucket_versioning.imported_legacy_versioning: Import complete!

4️⃣  Importando rol IAM...
aws_iam_role.imported_legacy: Import prepared!
aws_iam_role.imported_legacy: Import complete!

✅ Importación completada
Los recursos ahora están gestionados por Terraform
```

### Conceptos Clave

- **terraform import**: Comando para importar recursos existentes al state
- **Import ID**: Identificador específico del recurso (variable por tipo)
- **Configuration Matching**: La config debe matchear el estado real del recurso
- **Terraformer**: Herramienta de terceros para automatizar imports masivos
- **State After Import**: El recurso está en el state pero puede diferir de la config

---

## Troubleshooting

### Problema 1: For_Each con Lista que Cambia de Orden

**Error:**
```
Error: Invalid for_each argument
```

**Solution:**
```hcl
# Convertir lista a set (elimina orden)
resource "aws_s3_bucket" "example" {
  for_each = toset(var.bucket_names)  # ← toset()
  bucket   = each.value
}
```

### Problema 2: Count Index Shift

**Problema:** Eliminar elemento del medio causa recreación de todos los siguientes

**Solution:**
```hcl
# Usar for_each en lugar de count
resource "aws_s3_bucket" "example" {
  for_each = var.bucket_map  # ← Usar map con keys únicas
  bucket   = each.key
}
```

### Problema 3: Import Falla

**Error:**
```
Error: Resource already exists in state
```

**Solution:**
```bash
# Remover del state primero
terraform state rm aws_s3_bucket.example

# Re-importar
terraform import aws_s3_bucket.example bucket-name
```

### Problema 4: Circular Dependency

**Error:**
```
Error: Cycle: aws_s3_bucket.a, aws_s3_bucket.b
```

**Solution:**
```hcl
# Revisar dependencias y usar depends_on explícitamente si es necesario
# O reformular la arquitectura para eliminar el ciclo
```

### Problema 5: Lifecycle Prevent_Destroy No Funciona

**Problema:** `prevent_destroy = true` pero terraform destroy sí destruye

**Causa:** prevent_destroy solo funciona con recursos individuales (-target)

**Solution:**
```bash
# destroy completo (with -force o -auto-approve) ignora prevent_destroy
# Protección real requiere policies a level de cuenta AWS/Azure/GCP
```

---

## Recursos Adicionales

### Documentación

- [Terraform for_each](https://www.terraform.io/docs/language/meta-arguments/for_each.html)
- [Terraform count](https://www.terraform.io/docs/language/meta-arguments/count.html)
- [Lifecycle Meta-Argument](https://www.terraform.io/docs/language/meta-arguments/lifecycle.html)
- [Terraform Import](https://www.terraform.io/docs/cli/import/index.html)

### Herramientas

- [Terraformer](https://github.com/GoogleCloudPlatform/terraformer) - Import masivo
- [terraform-docs](https://terraform-docs.io/) - Documentación automática
- [tflint](https://github.com/terraform-linters/tflint) - Linter

### Best Practices

- Preferir `for_each` sobre `count` en la mayoría de casos
- Usar `prevent_destroy` en recursos críticos de producción
- Documentar dependencias explícitas con comentarios
- Hacer backup del state antes de imports complejos
- Usar modules para recursos que siempre van juntos

---

## Próximos Steps

¡Excelente! Has dominado la gestión multi-recurso en Terraform. Ahora sabes:

✅ Crear y gestionar múltiples recursos relacionados
✅ Implementar IAM roles y policies
✅ Manejar dependencias explícitas e implícitas
✅ Usar count y for_each efectivamente
✅ Aplicar lifecycle rules avanzadas
✅ Importar infraestructura existente

**Continúa con:** [Exercise 03 - Modules](../03-modules/README.md)

En el próximo exercise you will learn a:
- Crear modules reutilizables
- Publicar modules en registries
- Usar modules de terceros
- Versionar modules
