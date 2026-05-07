# Exercise 05: Gestión de Estado (State Management)

⏱️ **Duration estimada**: 2-3 hours
🎯 **Level**: Intermedio-Avanzado
📋 **Prerequisites**: Exercises 01-04 completeds

## 🎓 Objectives de Aprendizaje

Al completar este exercise, serás capaz de:

- ✅ Entender cómo funciona el state file de Terraform
- ✅ Configurar remote state con S3 y DynamoDB locking
- ✅ Usar workspaces para múltiples entornos
- ✅ Manipular el state: move, rm, import
- ✅ Implementar state locking para trabajo en equipo
- ✅ Proteger información sensible en el state

## 📝 Context

El manejo apropiado del state es **crítico** en Terraform. El state file es la fuente de verdad sobre tu infraestructura. Este exercise te enseña cómo gestionar el state de forma segura, especialmente cuando trabajas en equipo.

**⚠️ Problemas al no gestionar bien el state:**

- Múltiples personas aplicando cambios simultáneamente → corrupción
- State local perdido → Terraform no sabe qué recursos controla
- Credentials en state file → riesgo de seguridad
- Sin versionado → no hay rollback posible

---

## Task 1: Local State vs Remote State

### Step 1.1: Entender Local State

Create un proyecto simple:

```bash
mkdir -p ~/terraform-state-demo/local
cd ~/terraform-state-demo/local
```text

**main.tf:**

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
  region = "us-east-1"
}

resource "aws_s3_bucket" "state_demo" {
  bucket = "state-demo-local-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  tags = {
    Purpose = "State Management Demo"
  }
}
```text

```bash
terraform init
terraform apply -auto-approve

# Inspeccionar el state local
ls -lh terraform.tfstate
cat terraform.tfstate | jq '.resources'

# Ubicación: ./terraform.tfstate (mismo directorio)
```text

**Problemas del local state:**

- ❌ Un solo usuario puede trabajar a la vez
- ❌ Si pierdes el archivo, pierdes el tracking
- ❌ No hay locking → riesgo de corrupción
- ❌ State puede contener datos sensibles (passwords, keys)
- ❌ No hay versionado ni historial

### Step 1.2: Configurar Remote State con S3

**🎯 Objective**: Mover el state a S3 con locking usando DynamoDB

#### 1.2.1: Crear Backend Infrastructure

Primero, necesitamos create el bucket S3 y tabla DynamoDB para el backend:

**backend-resources.tf:**

```hcl
# Este archivo crea los recursos necesarios para el remote backend
# Ejecutar PRIMERO con local state, luego migrar

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Variables
locals {
  project_name = "terraform-state-backend"
  environment  = "shared"
}

# S3 Bucket para almacenar el state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${local.project_name}-${local.environment}"

  tags = {
    Name        = "Terraform State Backend"
    Environment = local.environment
    Purpose     = "Remote State Storage"
  }
}

# Versionado del bucket (crítico para rollback)
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Cifrado server-side obligatorio
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloquear acceso público
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB para state locking
resource "aws_dynamodb_table" "terraform_lock" {
  name         = "${local.project_name}-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Lock"
    Environment = local.environment
    Purpose     = "State Locking"
  }
}

# Outputs
output "s3_bucket_name" {
  value       = aws_s3_bucket.terraform_state.id
  description = "Nombre del bucket para remote state"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.terraform_lock.id
  description = "Nombre de la tabla DynamoDB para locking"
}

output "backend_config" {
  value = <<EOF

# Agregar esta configuration al bloque terraform {}:
backend "s3" {
  bucket         = "${aws_s3_bucket.terraform_state.id}"
  key            = "terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "${aws_dynamodb_table.terraform_lock.id}"
  encrypt        = true
}
EOF
  description = "Configuration del backend para copiar"
}
```

```bash
# Crear los recursos del backend
terraform init
terraform apply

# Guardar los outputs
terraform output backend_config
```text

#### 1.2.2: Migrar a Remote State

Ahora actualiza `main.tf` agregando el backend:

```hcl
terraform {
  required_version = ">= 1.0"

  # Backend configuration para remote state
  backend "s3" {
    bucket         = "terraform-state-backend-shared"  # Del output anterior
    key            = "demo/terraform.tfstate"         # Path dentro del bucket
    region         = "us-east-1"
    dynamodb_table = "terraform-state-backend-lock"  # Del output anterior
    encrypt        = true                            # Cifrado en reposo
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```text

```bash
# Reinicializar para migrar el state
terraform init -migrate-state

# Terraform preguntará:
# Do you want to copy existing state to the new backend?
#   Enter a value: yes

# Verificar que el state está en S3
aws s3 ls s3://terraform-state-backend-shared/demo/

# El archivo local puede ser eliminado
ls terraform.tfstate*
# Debería estar vacío o mostrar backup
```text

**✅ Ventajas del remote state:**

- ✅ Múltiples usuarios pueden trabajar
- ✅ Locking automático (gracias a DynamoDB)
- ✅ Versionado y rollback posible
- ✅ Cifrado en reposo y tránsito
- ✅ Backup automático

---

## Task 2: Workspaces para Múltiples Entornos

### Step 2.1: Crear Workspaces

Los workspaces permiten gestionar múltiples entornos (dev, staging, prod) con la misma configuration.

```bash
# Ver workspace actual
terraform workspace show
# Output: default

# Listar todos los workspaces
terraform workspace list
# Output:
# * default

# Crear workspace para desarrollo
terraform workspace new development

# Crear workspace para staging
terraform workspace new staging

# Crear workspace para producción
terraform workspace new production

# Listar workspaces
terraform workspace list
# Output:
#   default
#   development
# * production (active)
#   staging
```

### Step 2.2: Usar Workspace en Configuration

**main.tf:**

```hcl
locals {
  workspace_config = {
    development = {
      instance_type = "t2.micro"
      instance_count = 1
      enable_monitoring = false
    }
    staging = {
      instance_type = "t2.small"
      instance_count = 2
      enable_monitoring = true
    }
    production = {
      instance_type = "t2.medium"
      instance_count = 5
      enable_monitoring = true
    }
  }

  # Obtener configuration del workspace actual
  config = local.workspace_config[terraform.workspace]

  # Sufijo basado en workspace
  name_suffix = terraform.workspace == "default" ? "" : "-${terraform.workspace}"
}

resource "aws_s3_bucket" "app_data" {
  bucket = "my-app-data${local.name_suffix}-${formatdate("YYYYMMDD", timestamp())}"

  tags = {
    Environment = terraform.workspace
    ManagedBy   = "Terraform"
  }
}

output "workspace_info" {
  value = {
    current_workspace = terraform.workspace
    bucket_name       = aws_s3_bucket.app_data.id
    config            = local.config
  }
}
```text

### Step 2.3: Aplicar en Diferentes Workspaces

```bash
# Aplicar en development
terraform workspace select development
terraform apply -auto-approve

# Aplicar en staging
terraform workspace select staging
terraform apply -auto-approve

# Aplicar en production
terraform workspace select production
terraform apply -auto-approve

# Ver state files en S3 (cada workspace tiene su propio state)
aws s3 ls s3://terraform-state-backend-shared/demo/ --recursive
# Output:
# terraform.tfstate                    # workspace: default
# env:/development/terraform.tfstate   # workspace: development
# env:/staging/terraform.tfstate       # workspace: staging
# env:/production/terraform.tfstate    # workspace: production

# Ver recursos de cada workspace
terraform workspace select development
terraform state list

terraform workspace select production
terraform state list
```text

**📊 Cada workspace mantiene:**

- Su propio state file
- Sus propios recursos
- Su propia configuration

---

## Task 3: Manipulación de State

### Step 3.1: terraform state list/show

```bash
# Listar todos los recursos en el state
terraform state list

# Output ejemplo:
# aws_s3_bucket.app_data
# aws_s3_bucket_versioning.app_data_versioning

# Ver detalles de un recurso específico
terraform state show aws_s3_bucket.app_data
```text

### Step 3.2: terraform state mv (Refactoring)

Supón que quieres renombrar un recurso sin recrearlo:

```hcl
# ANTES:
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

# QUIERES CAMBIAR A:
resource "aws_s3_bucket" "analytics_data" {
  bucket = "my-data-bucket"
}
```

```bash
# Sin state mv, Terraform intentaría:
# - Destruir aws_s3_bucket.data
# - Crear aws_s3_bucket.analytics_data
# ⚠️ Esto eliminaría el bucket!

# CON state mv (refactoring seguro):
terraform state mv aws_s3_bucket.data aws_s3_bucket.analytics_data

# Ahora actualiza el código HCL y verifica:
terraform plan
# Output: No changes. Your infrastructure matches the configuration.
```text

### Step 3.3: terraform state rm (Remover del State)

Útil cuando quieres que Terraform deje de gestionar un recurso sin destruirlo:

```bash
# Remover recurso del state (el recurso permanece en AWS)
terraform state rm aws_s3_bucket.legacy_bucket

# Ahora Terraform no lo gestiona más
terraform state list  # No aparece

# El bucket sigue existiendo en AWS
aws s3 ls | grep legacy
```text

### Step 3.4: terraform import (Importar Recurso Existente)

Importa un recurso creado manualmente a Terraform:

**Ejemplo: Importar S3 bucket existente**

```hcl
# 1. Definir el recurso en código (sin detalles completos aún)
resource "aws_s3_bucket" "imported_bucket" {
  bucket = "my-manually-created-bucket"
  # Terraform completará los detalles al importar
}
```text

```bash
# 2. Importar el bucket al state
terraform import aws_s3_bucket.imported_bucket my-manually-created-bucket

# 3. Ver qué atributos tiene
terraform state show aws_s3_bucket.imported_bucket

# 4. Actualizar el código HCL con todos los atributos reales
# Ejecutar plan iterativamente hasta que no haya cambios
terraform plan

# 5. Cuando plan muestre "No changes", el import está completo
```

### Step 3.5: terraform state pull/push (Backup Manual)

```bash
# Descargar state actual a archivo local
terraform state pull > terraform.tfstate.backup

# Ver el state
cat terraform.tfstate.backup | jq '.'

# ⚠️ CUIDADO: Push solo en emergencias
# terraform state push terraform.tfstate.backup
```text

---

## Task 4: State Locking en Acción

### Step 4.1: Simular Bloqueo Concurrente

**Terminal 1:**

```bash
cd ~/terraform-state-demo/local
terraform workspace select development

# Iniciar apply (toma tiempo con sleep)
terraform apply -auto-approve
```text

**Terminal 2 (simultáneamente):**

```bash
cd ~/terraform-state-demo/local
terraform workspace select development

# Intentar apply concurrente
terraform apply -auto-approve
# Output:
# Error: Error acquiring the state lock
#
# Error message: ConditionalCheckFailedException: The conditional request failed
# Lock Info:
#   ID:        a1b2c3d4-5e6f-7890-abcd-ef1234567890
#   Path:      terraform-state-backend-shared/demo/env:/development/terraform.tfstate
#   Operation: OperationTypeApply
#   Who:       user@hostname
#   Version:   1.7.0
#   Created:   2024-03-07 10:30:15.123456789 +0000 UTC
#   Info:
#
# Terraform acquires a state lock to protect the state from being written
# by multiple users concurrently. Please resolve the issue above and try
# again. For most commands, you can disable locking with the "-lock=false"
# flag, but this is not recommended.
```text

**✅ State locking funciona!** El segundo apply está bloqueado hasta que el primero termine.

### Step 4.2: Forzar Unlock (Solo en Emergencias)

```bash
# Si un proceso murió y dejó el lock activo
terraform force-unlock <LOCK_ID>

# Ejemplo:
terraform force-unlock a1b2c3d4-5e6f-7890-abcd-ef1234567890

# ⚠️ Usar SOLO si estás seguro de que nadie más está ejecutando Terraform
```

---

## Task 5: Datos Sensibles en State

### Problema: El State Contiene Secrets

```hcl
resource "aws_db_instance" "database" {
  allocated_storage    = 20
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  username             = "admin"
  password             = "SuperSecretPassword123!"  # ⚠️ Aparecerá en el state!
}
```text

```bash
terraform apply

# Ver el state
terraform state pull | jq '.resources[] | select(.type == "aws_db_instance") | .instances[0].attributes.password'
# Output: "SuperSecretPassword123!"  # 😱 Password visible!
```text

### Soluciones

#### Solution 1: AWS Secrets Manager + Data Source

```hcl
# Almacenar password en Secrets Manager (fuera de Terraform)
# aws secretsmanager create-secret --name db-password --secret-string "SuperSecretPassword123!"

# Referenciarlo en Terraform
data "aws_secretsmanager_secret" "db_password" {
  name = "db-password"
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = data.aws_secretsmanager_secret.db_password.id
}

resource "aws_db_instance" "database" {
  # ... otras configuraciones ...
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}

# ⚠️ El password TODAVÍA aparece en el state, pero:
# - No está hardcodeado en código
# - Secrets Manager controla el acceso
# - Puedes rotar el secret sin tocar Terraform
```text

#### Solution 2: Sensitive Outputs

```hcl
output "database_password" {
  value     = aws_db_instance.database.password
  sensitive = true  # No muestra el valor en terraform output
}

# Terraform plan/apply no lo muestra:
# Outputs:
# database_password = <sensitive>
```

#### Solution 3: Cifrado del State File

El state en S3 **debe** tener cifrado obligatorio:

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
  }
}
```text

#### Solution 4: Constraints de Acceso al State

```hcl
# IAM policy para el bucket de state
resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::123456789012:role/terraform-role",
            "arn:aws:iam::123456789012:user/terraform-user"
          ]
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      }
    ]
  })
}
```text

---

## Task 6: Mejores Prácticas de State Management

### ✅ DO's (Hacer)

1. **Usar remote state siempre en equipo**

   ```hcl
   backend "s3" {
     bucket         = "terraform-state"
     key            = "project/terraform.tfstate"
     region         = "us-east-1"
     dynamodb_table = "terraform-lock"
     encrypt        = true
   }
   ```

2. **Habilitar versionado en S3**
   - Permite rollback si el state se corrompe

3. **Usar workspaces o directorios separados para entornos**

   ```text
   environments/
     ├── dev/
     ├── staging/
     └── production/
   ```

4. **Cifrar el state file** (S3 SSE, KMS mejor)

5. **Limitar acceso al state** (IAM policies restrictivas)

6. **Backup regular del state**

   ```bash
   terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate
   ```text

### ❌ DON'Ts (No Hacer)

1. **NO commitear terraform.tfstate a Git**

   ```gitignore
   # .gitignore
   *.tfstate
   *.tfstate.backup
   .terraform/
   ```

2. **NO editar terraform.tfstate manualmente**
   - Usar comandos `terraform state`

3. **NO usar local state en equipo**

4. **NO deshabilitar locking** (`-lock=false`)
   - Solo en emergencias

5. **NO almacenar secrets en variables** sin protección

6. **NO compartir state files por Slack/Email**
   - Contienen información sensible

---

## 🧹 Limpieza

```bash
# Destruir recursos en todos los workspaces
terraform workspace select development
terraform destroy -auto-approve

terraform workspace select staging
terraform destroy -auto-approve

terraform workspace select production
terraform destroy -auto-approve

# Volver al workspace default
terraform workspace select default

# Eliminar workspaces
terraform workspace delete development
terraform workspace delete staging
terraform workspace delete production

# Destruir backend resources (separado)
cd ../backend-setup
terraform destroy -auto-approve
```text

---

## ✅ Checklist

- [ ] Creaste remote state backend con S3 + DynamoDB
- [ ] Migraste local state a remote state
- [ ] Usaste workspaces para múltiples entornos
- [ ] Ejecutaste state mv, rm, import
- [ ] Verificaste que state locking funciona
- [ ] Implementaste protecciones para datos sensibles
- [ ] Entiendes cuándo usar workspaces vs directorios separados

---

## 📚 Recursos

- [Terraform State Documentation](https://developer.hashicorp.com/terraform/language/state)
- [Backend Configuration](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
- [Workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces)
- [Sensitive Data in State](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

**Siguiente**: [Exercise 06 - Production-Ready Infrastructure](../06-production-ready/README.md)
