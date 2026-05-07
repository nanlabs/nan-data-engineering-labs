# Patrones de Infrastructure as Code

## 📋 Tabla de Contenidos

1. [Introducción a Patrones IaC](#introducción-a-patrones-iac)
2. [CI/CD para Infrastructure as Code](#cicd-para-infrastructure-as-code)
3. [Seguridad y Compliance](#seguridad-y-compliance)
4. [Estrategias Multi-Entorno](#estrategias-multi-entorno)
5. [Disaster Recovery y Business Continuity](#disaster-recovery-y-business-continuity)
6. [GitOps para Infraestructura](#gitops-para-infraestructura)
7. [Policy as Code](#policy-as-code)
8. [Observabilidad de Infraestructura](#observabilidad-de-infraestructura)

---

## Introducción a Patrones IaC

### ¿Qué son los Patrones de IaC?

Los patrones de Infrastructure as Code son **solutions probadas y reutilizables** para problemas comunes en la gestión de infraestructura. Estos patrones emergen de experiencias reales en producción.

**Categorías principales:**

- 🔄 **Deployment Patterns**: Cómo desplegar cambios de forma segura
- 🏗️ **Organizational Patterns**: Cómo estructurar proyectos y equipos
- 🔒 **Security Patterns**: Cómo asegurar infraestructura y secretos
- 🌍 **Multi-Environment Patterns**: Cómo gestionar dev/staging/prod
- 📊 **Testing Patterns**: Cómo validate infraestructura

### Principios Fundamentales

#### 1. Immutable Infrastructure

**Concepto**: Nunca modificar infraestructura existente, siempre reemplazar.

```hcl
# ❌ MAL: Modificar un servidor existente
resource "aws_instance" "app" {
  ami           = "ami-old-version"
  instance_type = "t2.micro"

  # Cambiar el AMI causa que Terraform intente actualizar in-place
  # Esto puede fallar y dejar el servidor en estado inconsistente
}

# ✅ BIEN: Crear nueva instancia, destruir la vieja
resource "aws_launch_template" "app" {
  name_prefix   = "app-"
  image_id      = "ami-new-version"
  instance_type = "t2.micro"

  # Combinado con Auto Scaling Group, esto crea instancias nuevas
  # y termina las viejas automáticamente
}

resource "aws_autoscaling_group" "app" {
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  min_size = 2
  max_size = 5

  # Blue/green deployment
  lifecycle {
    create_before_destroy = true
  }
}
```text

**Ventajas:**

- ✅ Eliminadrift (divergencia) entre configuration y realidad
- ✅ Rollbacks más fáciles
- ✅ Testing más confiable
- ✅ Auditoría completa

#### 2. Declarative vs Imperative

**Declarative (Terraform)**: Describes el estado final deseado.

```hcl
# "Quiero 3 servidores"
resource "aws_instance" "web" {
  count         = 3
  instance_type = "t2.micro"
  ami           = "ami-12345678"
}
```text

**Imperative (Scripts)**: Describes los steps para llegar ahí.

```bash
# "Create servidor 1, crea servidor 2, crea servidor 3"
for i in {1..3}; do
  aws ec2 run-instances --instance-type t2.micro --image-id ami-12345678
done
```text

**Terraform es declarativo:**

- Terraform calcula automáticamente qué create/modificar/destruir
- El state file rastrea la realidad actual
- Idempotente: execute múltiples veces produce el mismo resultado

#### 3. DRY (Don't Repeat Yourself)

```hcl
# ❌ MAL: Código duplicado
resource "aws_s3_bucket" "data_dev" {
  bucket = "company-data-dev"
  versioning { enabled = true }
  encryption { rule { ... } }
  lifecycle_rule { ... }
  tags = { Environment = "dev" }
}

resource "aws_s3_bucket" "data_staging" {
  bucket = "company-data-staging"
  versioning { enabled = true }
  encryption { rule { ... } }  # Mismo código!
  lifecycle_rule { ... }
  tags = { Environment = "staging" }
}

# ✅ BIEN: Usar modules
module "data_bucket" {
  source = "./modules/s3-bucket"

  for_each = {
    dev     = { retention = 30 }
    staging = { retention = 90 }
    prod    = { retention = 365 }
  }

  bucket_name = "company-data-${each.key}"
  environment = each.key
  retention_days = each.value.retention
}
```

---

## CI/CD para Infrastructure as Code

### Pipeline Típico

```text
┌─────────────┐
│   Git Push  │
│  (feature)  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│  Pull Request Created        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  1. terraform fmt -check     │  ← Code formatting
│  2. terraform validate       │  ← Syntax validation
│  3. tflint                   │  ← Linting
│  4. tfsec                    │  ← Security scan
│  5. terraform plan           │  ← Preview changes
│  6. Post plan to PR comment  │  ← Visibility
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Code Review + Approval      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Merge to main               │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  terraform apply (dev)       │  ← Auto-apply to dev
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Manual Approval for Prod    │  ← Human gate
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  terraform apply (prod)      │
└──────────────────────────────┘
```text

### GitHub Actions - Production Grade

**.github/workflows/terraform-pipeline.yml:**

```yaml
name: 'Terraform Pipeline'

on:
  pull_request:
    branches: [main]
    paths:
      - 'terraform/**'
      - 'modules/**'
      - '.github/workflows/terraform-pipeline.yml'
  push:
    branches: [main]
    paths:
      - 'terraform/**'
      - 'modules/**'

permissions:
  id-token: write
  contents: read
  pull-requests: write

env:
  TF_VERSION: '1.7.5'
  AWS_REGION: 'us-east-1'

jobs:
  # JOB 1: Validation y Linting
  validate:
    name: 'Validate & Lint'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        id: fmt
        run: terraform fmt -check -recursive
        continue-on-error: true

      - name: Terraform Init
        run: terraform init -backend=false
        working-directory: terraform

      - name: Terraform Validate
        run: terraform validate
        working-directory: terraform

      - name: Setup TFLint
        uses: terraform-linters/setup-tflint@v4

      - name: TFLint
        run: tflint --recursive

      - name: tfsec Security Scan
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          working_directory: terraform
          soft_fail: false  # Fail on security issues

  # JOB 2: Plan por Entorno
  plan:
    name: 'Plan (${{ matrix.environment }})'
    needs: validate
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
          role-session-name: terraform-${{ matrix.environment }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: |
          terraform init \
            -backend-config="key=terraform/${{ matrix.environment }}/terraform.tfstate"
        working-directory: terraform/environments/${{ matrix.environment }}

      - name: Terraform Plan
        id: plan
        run: terraform plan -out=tfplan -no-color
        working-directory: terraform/environments/${{ matrix.environment }}

      - name: Save Plan Artifact
        uses: actions/upload-artifact@v3
        with:
          name: tfplan-${{ matrix.environment }}
          path: terraform/environments/${{ matrix.environment }}/tfplan
          retention-days: 5

      - name: Comment Plan on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = `${{ steps.plan.outputs.stdout }}`;

            const output = `### Terraform Plan: \`${{ matrix.environment }}\` 📝

            <details>
            <summary>Show Plan</summary>

            \`\`\`terraform
            ${plan}
            \`\`\`

            </details>
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

  # JOB 3: Apply (solo en push a main)
  apply-dev:
    name: 'Apply to Dev'
    needs: plan
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: dev  # GitHub Environment protection

    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Download Plan
        uses: actions/download-artifact@v3
        with:
          name: tfplan-dev
          path: terraform/environments/dev

      - name: Terraform Init
        run: terraform init -backend-config="key=terraform/dev/terraform.tfstate"
        working-directory: terraform/environments/dev

      - name: Terraform Apply
        run: terraform apply tfplan
        working-directory: terraform/environments/dev

      - name: Slack Notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Terraform Apply - Dev: ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Terraform Apply to Dev* ${{ job.status == 'success' && '✅' || '❌' }}\n*Commit:* <${{ github.event.head_commit.url }}|${{ github.event.head_commit.message }}>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

  apply-staging:
    name: 'Apply to Staging'
    needs: [apply-dev]
    runs-on: ubuntu-latest
    environment: staging  # Requiere aprobación manual en GitHub

    steps:
      # Similar a apply-dev pero para staging
      - uses: actions/checkout@v4
      # ... (mismo código que apply-dev)

  apply-prod:
    name: 'Apply to Production'
    needs: [apply-staging]
    runs-on: ubuntu-latest
    environment: production  # Requiere aprobación manual + mayor seguridad

    steps:
      # Similar a apply-dev pero con extra validaciones
      - uses: actions/checkout@v4

      # ... terraform init, download plan ...

      - name: Require Explicit Confirmation
        run: |
          echo "⚠️  DEPLOYING TO PRODUCTION"
          echo "Environment: production"
          echo "Commit: ${{ github.sha }}"
          # GitHub Environment protection rules ya requieren aprobación manual

      - name: Terraform Apply
        run: terraform apply tfplan
        working-directory: terraform/environments/prod
```text

### GitLab CI Pipeline

**.gitlab-ci.yml:**

```yaml
stages:
  - validate
  - plan
  - apply

variables:
  TF_VERSION: "1.7.5"
  TF_ROOT: "${CI_PROJECT_DIR}/terraform"
  TF_STATE_NAME: "${CI_ENVIRONMENT_NAME}"

# Template reutilizable
.terraform_template:
  image:
    name: hashicorp/terraform:${TF_VERSION}
    entrypoint: [""]

  before_script:
    - cd ${TF_ROOT}/environments/${CI_ENVIRONMENT_NAME}
    - terraform init

  cache:
    key: "${CI_COMMIT_REF_SLUG}"
    paths:
      - ${TF_ROOT}/.terraform

# JOB: Validate
terraform:validate:
  stage: validate
  extends: .terraform_template
  script:
    - terraform fmt -check -recursive
    - terraform validate
  rules:
    - if: '$CI_MERGE_REQUEST_ID'

# JOB: Plan por entorno
.terraform_plan:
  stage: plan
  extends: .terraform_template
  script:
    - terraform plan -out=tfplan
  artifacts:
    name: "tfplan-${CI_ENVIRONMENT_NAME}"
    paths:
      - ${TF_ROOT}/environments/${CI_ENVIRONMENT_NAME}/tfplan
    expire_in: 7 days

terraform:plan:dev:
  extends: .terraform_plan
  variables:
    CI_ENVIRONMENT_NAME: "dev"

terraform:plan:prod:
  extends: .terraform_plan
  variables:
    CI_ENVIRONMENT_NAME: "prod"
  only:
    - main

# JOB: Apply
terraform:apply:dev:
  stage: apply
  extends: .terraform_template
  script:
    - terraform apply -auto-approve tfplan
  dependencies:
    - terraform:plan:dev
  environment:
    name: dev
  only:
    - main

terraform:apply:prod:
  stage: apply
  extends: .terraform_template
  script:
    - terraform apply -auto-approve tfplan
  dependencies:
    - terraform:plan:prod
  environment:
    name: production
  when: manual  # Requiere aprobación manual
  only:
    - main
```

---

## Seguridad y Compliance

### 1. Secrets Management

#### Usar AWS Secrets Manager

```hcl
# ❌ NUNCA hardcodear secrets
resource "aws_db_instance" "db" {
  username = "admin"
  password = "SuperSecret123!"  # ⚠️ Esto aparecerá en Git, state file, logs!
}

# ✅ Usar Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.project}-db-password"

  recovery_window_in_days = 30
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
}

resource "aws_db_instance" "db" {
  username = "admin"
  password = data.aws_secretsmanager_secret_version.db_password.secret_string

  # ✅ Password se almacena en Secrets Manager
  # ✅ State file contiene referencia, no el valor
  # ✅ Rotación posible sin tocar Terraform
}
```text

#### Sensitive Variables y Outputs

```hcl
# Variables
variable "api_key" {
  description = "API Key for external service"
  type        = string
  sensitive   = true  # No se muestra en logs
}

# Outputs
output "database_password" {
  value     = aws_db_instance.db.password
  sensitive = true  # No se muestra en terraform output
}

# Usage
terraform output database_password
# <sensitive>

# Para ver el valor (solo cuando necesites):
terraform output -raw database_password
# SuperSecret123!
```text

### 2. Least Privilege IAM

```hcl
# ❌ MAL: Permisos demasiado amplios
resource "aws_iam_role_policy" "terraform" {
  role = aws_iam_role.terraform.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"  # ⚠️ Acceso a TODO!
      Resource = "*"
    }]
  })
}

# ✅ BIEN: Permisos específicos
resource "aws_iam_role_policy" "terraform" {
  role = aws_iam_role.terraform.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:GetBucketVersioning",
          "s3:PutBucketVersioning",
          "s3:PutEncryptionConfiguration"
        ]
        Resource = "arn:aws:s3:::my-project-*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
          "dynamodb:DescribeTable"
        ]
        Resource = "arn:aws:dynamodb:*:*:table/terraform-lock-*"
      }
    ]
  })
}
```text

### 3. State File Security

```hcl
# Backend con todas las protecciones
terraform {
  backend "s3" {
    bucket         = "terraform-state-production"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true                    # ✅ Cifrado en reposo
    kms_key_id     = "arn:aws:kms:..."      # ✅ KMS en lugar de AES256
    dynamodb_table = "terraform-lock"        # ✅ State locking

    # ✅ Server-side encryption
    # ✅ Versioning habilitado
    # ✅ MFA delete habilitado
    # ✅ Access logging habilitado
  }
}

# Bucket configuration
resource "aws_s3_bucket" "terraform_state" {
  bucket = "terraform-state-production"

  tags = {
    Name        = "Terraform State"
    Sensitivity = "High"
  }
}

# Versionado (permite rollback)
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status     = "Enabled"
    mfa_delete = "Enabled"  # Requiere MFA para eliminar versiones
  }
}

# Cifrado obligatorio
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

# KMS key con rotación
resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true  # Rotación automática anual

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
        Sid    = "Allow Terraform Role"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.terraform.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# Bloquear acceso público
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Logging de accesos
resource "aws_s3_bucket_logging" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  target_bucket = aws_s3_bucket.terraform_state_logs.id
  target_prefix = "state-access-logs/"
}

# Lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 180
      storage_class   = "GLACIER"
    }

    # Mantener versiones por 2 años
    noncurrent_version_expiration {
      noncurrent_days = 730
    }
  }
}
```

### 4. Compliance as Code (tfsec, Checkov)

**Ejecutar tfsec:**

```bash
# Instalar
brew install tfsec

# Escanear directorio
tfsec .

# Output ejemplo:
# Result 1
#
# [AWS003][ERROR]  Resource 'aws_s3_bucket.data' has no encryption
# /terraform/main.tf:15-20
#
# Result 2
#
# [AWS017][WARNING] Resource 'aws_s3_bucket.data' does not have versioning enabled
# /terraform/main.tf:15-20
#
# 2 potential problems detected.
```text

**Ejecutar Checkov:**

```bash
# Instalar
pip install checkov

# Escanear
checkov -d terraform/

# Output:
# Passed checks: 45, Failed checks: 3, Skipped checks: 0
#
# Failed checks:
#
# Check: CKV_AWS_19: "Ensure the S3 bucket has server-side encryption enabled"
#         FAILED for resource: aws_s3_bucket.data
#         File: /main.tf:15-20
#
# Check: CKV_AWS_21: "Ensure the S3 bucket has versioning enabled"
#         FAILED for resource: aws_s3_bucket.data
#         File: /main.tf:15-20
```text

**Configurar excepciones (cuando sean justificadas):**

```hcl
resource "aws_s3_bucket" "public_website" {
  bucket = "my-public-website"

  # checkov:skip=CKV_AWS_18:Public bucket is intentional for static website
  # tfsec:ignore:AWS002  # Skip public access warning
  acl = "public-read"

  website {
    index_document = "index.html"
  }
}
```text

---

## Estrategias Multi-Entorno

### Patrón 1: Workspaces

```bash
# Crear workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Usar en código
```

```hcl
locals {
  environment = terraform.workspace

  config = {
    dev = {
      instance_type   = "t2.micro"
      instance_count  = 1
      enable_backups  = false
    }
    staging = {
      instance_type   = "t2.small"
      instance_count  = 2
      enable_backups  = true
    }
    prod = {
      instance_type   = "t2.medium"
      instance_count  = 5
      enable_backups  = true
    }
  }

  env_config = local.config[local.environment]
}

resource "aws_instance" "app" {
  count         = local.env_config.instance_count
  instance_type = local.env_config.instance_type

  tags = {
    Environment = local.environment
  }
}
```text

**Ventajas:**

- ✅ Mismo código para todos los entornos
- ✅ Fácil de cambiar entre entornos

**Desventajas:**

- ❌ State files en la misma ubicación (riesgo)
- ❌ No se puede tener configuraciones radicalmente diferentes

### Patrón 2: Directorios Separados (Recomendado)

```text
terraform/
├── modules/
│   └── app/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── environments/
    ├── dev/
    │   ├── main.tf
    │   ├── terraform.tfvars
    │   └── backend.hcl
    │
    ├── staging/
    │   ├── main.tf
    │   ├── terraform.tfvars
    │   └── backend.hcl
    │
    └── prod/
        ├── main.tf
        ├── terraform.tfvars
        └── backend.hcl
```text

**environments/dev/main.tf:**

```hcl
terraform {
  backend "s3" {}  # Config en backend.hcl
}

module "app" {
  source = "../../modules/app"

  environment    = "dev"
  instance_type  = "t2.micro"
  instance_count = 1
  enable_backups = false
}
```

**environments/prod/main.tf:**

```hcl
terraform {
  backend "s3" {}
}

module "app" {
  source = "../../modules/app"

  environment    = "production"
  instance_type  = "t2.large"
  instance_count = 10
  enable_backups = true

  # Configuraciones adicionales solo para prod
  enable_multi_az     = true
  enable_monitoring   = true
  backup_retention    = 30
}
```text

**Ventajas:**

- ✅ State files completamente separados
- ✅ Configuraciones pueden ser radicalmente diferentes
- ✅ Mayor seguridad (menos riesgo de apply accidental en prod)

### Patrón 3: Terragrunt (DRY al máximo)

```hcl
# terragrunt.hcl (root)
remote_state {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "${path_relative_to_include()}/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

# environments/dev/terragrunt.hcl
include {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/app"
}

inputs = {
  environment = "dev"
  instance_type = "t2.micro"
}

# environments/prod/terragrunt.hcl
include {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/app"
}

inputs = {
  environment = "production"
  instance_type = "t2.large"
}
```text

```bash
# Usage
cd environments/dev
terragrunt apply

cd ../prod
terragrunt apply
```text

---

## Disaster Recovery y Business Continuity

### 1. Estado de Backup Automatizado

**Script: backup-state.sh**

```bash
#!/bin/bash
set -euo pipefail

PROJECT="my-project"
BACKUP_BUCKET="s3://${PROJECT}-disaster-recovery/state-backups"
DATE=$(date +%Y%m%d-%H%M%S)

echo "🔄 Backing up Terraform state..."

for env in dev staging prod; do
  echo "📦 Backing up ${env}..."

  aws s3 cp \
    "s3://${PROJECT}-terraform-state/${env}/terraform.tfstate" \
    "${BACKUP_BUCKET}/${DATE}/${env}/terraform.tfstate"

  aws s3 cp \
    "s3://${PROJECT}-terraform-state/${env}/terraform.tfstate" \
    "${BACKUP_BUCKET}/latest/${env}/terraform.tfstate"
done

echo "✅ Backup complete: ${BACKUP_BUCKET}/${DATE}/"

# Upload metadata
cat > backup-metadata.json <<EOF
{
  "timestamp": "${DATE}",
  "environments": ["dev", "staging", "prod"],
  "terraform_version": "$(terraform version -json | jq -r '.terraform_version')",
  "commit_sha": "${GITHUB_SHA:-unknown}"
}
EOF

aws s3 cp backup-metadata.json "${BACKUP_BUCKET}/${DATE}/metadata.json"
```

**Cron job (GitHub Actions scheduled):**

```yaml
name: 'Backup Terraform State'

on:
  schedule:
    - cron: '0 */6 * * *'  # Cada 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Run Backup Script
        run: ./scripts/backup-state.sh

      - name: Verify Backups
        run: |
          aws s3 ls s3://my-project-disaster-recovery/state-backups/latest/
```text

### 2. Plan de Recuperación

**Script: restore-state.sh**

```bash
#!/bin/bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <backup-date> <environment>"
  echo "Example: $0 20240307-153000 prod"
  exit 1
fi

BACKUP_DATE=$1
ENVIRONMENT=$2
PROJECT="my-project"

echo "⚠️  DISASTER RECOVERY: Restoring state for ${ENVIRONMENT}"
echo "Backup date: ${BACKUP_DATE}"
echo ""
read -p "Are you absolutely sure? (type 'yes'): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

# Download backup
echo "📥 Downloading backup..."
aws s3 cp \
  "s3://${PROJECT}-disaster-recovery/state-backups/${BACKUP_DATE}/${ENVIRONMENT}/terraform.tfstate" \
  "./restore-${BACKUP_DATE}.tfstate"

# Create backup of current state
echo "📦 Backing up current state first..."
cd "environments/${ENVIRONMENT}"
terraform state pull > "current-state-backup-$(date +%Y%m%d-%H%M%S).tfstate"

# Push restored state
echo "🔄 Restoring state..."
cat "../../restore-${BACKUP_DATE}.tfstate" | terraform state push -

echo "✅ State restored from backup: ${BACKUP_DATE}"
echo ""
echo "Next steps:"
echo "1. Run 'terraform plan' to verify"
echo "2. If needed, run 'terraform apply' to sync infrastructure"
```text

### 3. Runbook de DR

**docs/disaster-recovery-runbook.md:**

```markdown
# Disaster Recovery Runbook

## Scenarios

### Scenario 1: State File Corrupto

**Síntomas:**
- `terraform plan` falla con error de state parsing
- State file contiene JSON inválido

**Solution:**

1. NO entrar en pánico. El bucket tiene versionado.

2. Verificar versiones disponibles:
   \`\`\`bash
   aws s3api list-object-versions \
     --bucket my-project-terraform-state \
     --prefix prod/terraform.tfstate
   \`\`\`

3. Restaurar versión anterior:
   \`\`\`bash
   aws s3api get-object \
     --bucket my-project-terraform-state \
     --key prod/terraform.tfstate \
     --version-id <VERSION_ID> \
     terraform.tfstate

   terraform state push terraform.tfstate
   \`\`\`

4. Verificar:
   \`\`\`bash
   terraform plan
   \`\`\`

### Scenario 2: Eliminación Accidental de Recursos

**Síntomas:**
- Recursos críticos eliminados
- `terraform show` no muestra recursos esperados

**Solution:**

1. **NO execute `terraform apply` aún.**

2. Restaurar state backup más reciente:
   \`\`\`bash
   ./scripts/restore-state.sh <BACKUP_DATE> prod
   \`\`\`

3. Comparar con la realidad:
   \`\`\`bash
   terraform plan
   \`\`\`

4. Si los recursos fueron eliminados físicamente:
   \`\`\`bash
   terraform apply  # Recreará los recursos
   \`\`\`

5. Si los recursos aún existen:
   \`\`\`bash
   # El state ahora refleja la configuration correcta
   \`\`\`

### Scenario 3: State Lock Stuck

**Síntomas:**
- Error: "Error acquiring the state lock"
- Lock ID permanece activo

**Solution:**

1. Verificar que NADIE más está ejecutando Terraform:
   \`\`\`bash
   # Verificar en GitHub Actions, GitLab CI, Jenkins, etc.
   \`\`\`

2. Si estás seguro, forzar unlock:
   \`\`\`bash
   terraform force-unlock <LOCK_ID>
   \`\`\`

3. Verificar state integrity:
   \`\`\`bash
   terraform state pull | jq '.'
   \`\`\`

### Scenario 4: Pérdida Total del Bucket de State

**⚠️ CRITICAL:** Este es el peor scenario posible.

**Solution:**

1. Recovery desde disaster recovery bucket:
   \`\`\`bash
   # Listar backups disponibles
   aws s3 ls s3://my-project-disaster-recovery/state-backups/

   # Restaurar todos los environments
   for env in dev staging prod; do
     ./scripts/restore-state.sh latest $env
   done
   \`\`\`

2. Si no hay backups (💀 muy malo):
   - Opción A: Recrear state con `terraform import` (tedioso)
   - Opción B: Empezar de cero (destruir y recrear)

## Testing del Plan de DR

**Ejecutar quarterly (cada 3 meses):**

\`\`\`bash
# 1. Restaurar backup en ambiente de test
./scripts/restore-state.sh <RECENT_BACKUP> dev-dr-test

# 2. Verificar plan
terraform plan

# 3. Aplicar en ambiente aislado
terraform apply

# 4. Documentar tiempos y problemas
\`\`\`

## Métricas de Recovery

- **RTO (Recovery Time Objective)**: < 1 hora
- **RPO (Recovery Point Objective)**: < 6 hours (backups cada 6h)
- **MTTR (Mean Time To Recovery)**: < 2 hours

## Contactos de Emergencia

- **Equipo de Platform**: platform-team@company.com
- **On-call**: +1-555-ONCALL
- **Slack**: #incident-response
```text

---

## GitOps para Infraestructura

### Principios de GitOps

1. **Git como fuente de verdad**
2. **Pull vs Push** (el cluster pull changes, no push externo)
3. **Continuous reconciliation**
4. **Declarativo e inmutable**

### Implementación con Flux/ArgoCD + Terraform

```yaml
# flux-terraform.yaml
apiVersion: infra.contrib.fluxcd.io/v1alpha2
kind: Terraform
metadata:
  name: data-infrastructure
  namespace: flux-system
spec:
  interval: 10m

  sourceRef:
    kind: GitRepository
    name: infrastructure-repo

  path: ./terraform/environments/prod

  backendConfig:
    customConfiguration: |
      backend "s3" {
        bucket = "terraform-state"
        key    = "prod/terraform.tfstate"
        region = "us-east-1"
      }

  vars:
    - name: environment
      value: production

  varsFrom:
    - kind: Secret
      name: aws-credentials

  writeOutputsToSecret:
    name: terraform-outputs

  runnerPodTemplate:
    spec:
      serviceAccountName: terraform-runner
```

---

## Policy as Code

### Open Policy Agent (OPA) con Terraform

**policy/terraform.rego:**

```rego
package terraform.analysis

import input as tfplan

# Deny buckets sin cifrado
deny[msg] {
    resource := tfplan.resource_changes[_]
    resource.type == "aws_s3_bucket"
    not resource.change.after.server_side_encryption_configuration

    msg := sprintf("S3 bucket '%s' must have encryption enabled", [resource.name])
}

# Deny instancias públicas de RDS
deny[msg] {
    resource := tfplan.resource_changes[_]
    resource.type == "aws_db_instance"
    resource.change.after.publicly_accessible == true

    msg := sprintf("RDS instance '%s' must not be publicly accessible", [resource.name])
}

# Warn sobre instancias grandes en dev
warn[msg] {
    resource := tfplan.resource_changes[_]
    resource.type == "aws_instance"
    environment := tfplan.variables.environment.value
    environment == "dev"
    startswith(resource.change.after.instance_type, "m5.large")

    msg := sprintf("Instance '%s' uses large type in dev environment", [resource.name])
}

# Require tags obligatorios
required_tags := ["Environment", "Project", "Owner", "CostCenter"]

deny[msg] {
    resource := tfplan.resource_changes[_]
    resource.change.after.tags
    missing_tags := [tag | tag := required_tags[_]; not resource.change.after.tags[tag]]
    count(missing_tags) > 0

    msg := sprintf("Resource '%s' missing required tags: %v", [resource.name, missing_tags])
}
```text

**Ejecutar:**

```bash
# Generar plan JSON
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json

# Evaluar policies
opa eval --data policy/ --input tfplan.json "data.terraform.analysis.deny"

# Output:
# [
#   "S3 bucket 'data_raw' must have encryption enabled",
#   "Resource 'app_server' missing required tags: [\"CostCenter\"]"
# ]

# Integrar en CI/CD
if opa eval --data policy/ --input tfplan.json "data.terraform.analysis.deny" | jq -e 'length > 0'; then
  echo "❌ Policy violations detected. Apply blocked."
  exit 1
fi
```text

---

## Observabilidad de Infraestructura

### 1. Métricas de Terraform

```hcl
resource "datadog_monitor" "terraform_apply_failed" {
  name    = "Terraform Apply Failed"
  type    = "metric alert"
  message = "Terraform apply has failed. Check GitHub Actions logs. @platform-team"

  query = "sum(last_5m):sum:terraform.apply.failed{env:production} > 0"

  monitor_thresholds {
    critical = 0
  }

  tags = ["terraform", "infrastructure", "critical"]
}
```text

### 2. Drift Detection

```bash
#!/bin/bash
# drift-detection.sh

echo "🔍 Detecting infrastructure drift..."

cd terraform/environments/prod

# Get current state
terraform plan -detailed-exitcode -out=drift.plan

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ No drift detected"
elif [ $EXIT_CODE -eq 2 ]; then
  echo "⚠️  DRIFT DETECTED!"

  # Generate human-readable diff
  terraform show drift.plan > drift-report.txt

  # Send alert
  curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d '{
      "text": "🚨 Infrastructure Drift Detected in Production",
      "attachments": [{
        "color": "danger",
        "text": "'"$(cat drift-report.txt)"'"
      }]
    }'

  exit 1
else
  echo "❌ Terraform plan failed with error"
  exit $EXIT_CODE
fi
```

**Cron job diario:**

```yaml
name: 'Drift Detection'

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM
  workflow_dispatch:

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3

      - name: Check for Drift
        run: ./scripts/drift-detection.sh
```text

---

## Resumen de Patrones

| Patrón | Cuándo Usar | Complejidad |
|--------|-------------|-------------|
| **Workspaces** | Entornos similares, equipo pequeño | Baja |
| **Directorios Separados** | Producción, múltiples equipos | Media |
| **Terragrunt** | Proyectos grandes, DRY extremo | Alta |
| **GitOps** | Kubernetes + Terraform | Alta |
| **Policy as Code** | Compliance estricto, enterprise | Media |
| **Drift Detection** | Producción crítica | Baja |

---

## Checklist de Producción

- [ ] **Código**
  - [ ] Modules reutilizables
  - [ ] Variables validadas
  - [ ] Outputs documentados
  - [ ] Código formateado (`terraform fmt`)

- [ ] **Testing**
  - [ ] Tests unitarios (terratest)
  - [ ] Tests de integración
  - [ ] Validation de policies (OPA/Sentinel)

- [ ] **CI/CD**
  - [ ] Pipeline de plan en PRs
  - [ ] Pipeline de apply protegido
  - [ ] Aprobaciones manuales para prod
  - [ ] Notificaciones (Slack/Teams)

- [ ] **Seguridad**
  - [ ] State cifrado con KMS
  - [ ] Secrets en Secrets Manager
  - [ ] IAM least privilege
  - [ ] tfsec/checkov en pipeline
  - [ ] MFA para prod

- [ ] **Disaster Recovery**
  - [ ] Backups automatizados
  - [ ] Runbook documentado
  - [ ] DR testing quarterly
  - [ ] Versionado de state

- [ ] **Observabilidad**
  - [ ] Drift detection
  - [ ] Métricas de Terraform
  - [ ] Alertas configuradas
  - [ ] Logs centralizados

---

## Recursos

- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Terratest Documentation](https://terratest.gruntwork.io/)
- [Open Policy Agent](https://www.openpolicyagent.org/)
- [GitOps Principles](https://opengitops.dev/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

**¡Fin del Module!** 🎉

Ahora dominas no solo Terraform, sino también los patrones empresariales para gestionar infraestructura a gran escala de forma segura, confiable y eficiente.
