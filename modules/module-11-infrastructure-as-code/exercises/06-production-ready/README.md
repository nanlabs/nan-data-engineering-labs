# Exercise 06: Infrastructure Production-Ready

⏱️ **Duration estimada**: 3-4 hours
🎯 **Level**: Avanzado
📋 **Prerequisites**: Exercises 01-05 completeds

## 🎓 Objectives de Aprendizaje

Al completar este exercise, serás capaz de:
- ✅ Estructurar proyectos Terraform para enterprise
- ✅ Implementar testing automatizado con terratest
- ✅ Configurar CI/CD para Terraform
- ✅ Usar pre-commit hooks para validation
- ✅ Gestionar secrets de forma segura
- ✅ Implementar disaster recovery

## 📝 Context

Hasta ahora has aprendido los fundamentos. Ahora es tiempo de profesionalizar tu infraestructura para **producción real**, donde la confiabilidad, seguridad y colaboración son críticas.

**Este exercise cubre:**
- 🏗️ Arquitectura enterprise de proyectos Terraform
- 🧪 Testing automatizado
- 🔄 Pipelines CI/CD
- 🔒 Seguridad y compliance
- 📊 Disaster recovery

---

## Task 1: Estructura Enterprise de Proyecto

### Step 1.1: Árbol de Directorios Recomendado

```bash
mkdir -p terraform-production-project && cd terraform-production-project

# Crear estructura completa
mkdir -p {environments/{dev,staging,prod},modules/{networking,compute,data,security},tests,scripts,.github/workflows}

tree -L 3
```

**Estructura resultante:**

```
terraform-production-project/
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── Makefile
│
├── modules/                    # Modules reutilizables
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── README.md
│   │   └── versions.tf
│   │
│   ├── compute/
│   ├── data/
│   └── security/
│
├── environments/               # Un directorio por entorno
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   ├── backend.hcl
│   │   └── README.md
│   │
│   ├── staging/
│   └── prod/
│       ├── main.tf             # Configuration específica de producción
│       ├── variables.tf
│       ├── terraform.tfvars    # ⚠️ Nunca commitear (usar .tfvars.example)
│       ├── backend.hcl         # Backend config (partial backend)
│       └── README.md
│
├── tests/                      # Tests automatizados
│   ├── integration_test.go
│   ├── unit_test.go
│   └── go.mod
│
├── scripts/                    # Scripts de automatización
│   ├── setup.sh
│   ├── plan-all.sh
│   ├── validate.sh
│   └── disaster-recovery.sh
│
└── .github/
    └── workflows/
        ├── terraform-plan.yml
        ├── terraform-apply.yml
        └── terraform-destroy.yml
```

### Step 1.2: Configurar .gitignore

```bash
cat > .gitignore << 'EOF'
# Local .terraform directories
**/.terraform/*

# .tfstate files
*.tfstate
*.tfstate.*

# Crash log files
crash.log
crash.*.log

# Exclude all .tfvars files (contain secrets)
*.tfvars
*.tfvars.json

# Keep example file
!*.tfvars.example
!terraform.tfvars.example

# Ignore override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Ignore CLI configuration files
.terraformrc
terraform.rc

# Lock file (commit this for reproducibility)
# .terraform.lock.hcl  # Some teams commit, some don't

# Environment variables
.env
.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
EOF
```

### Step 1.3: Crear Module Reutilizable

**modules/data/s3-data-lake/main.tf:**

```hcl
# Module: S3 Data Lake
# Crea un data lake con capas bronze/silver/gold + seguridad

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  layers = ["bronze", "silver", "gold"]
  common_tags = merge(
    var.tags,
    {
      Module    = "s3-data-lake"
      ManagedBy = "Terraform"
    }
  )
}

# Buckets para cada capa
resource "aws_s3_bucket" "data_lake" {
  for_each = toset(local.layers)

  bucket = "${var.project_name}-datalake-${each.key}-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Layer = each.key
    }
  )
}

# Versionado
resource "aws_s3_bucket_versioning" "data_lake" {
  for_each = aws_s3_bucket.data_lake

  bucket = each.value.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Cifrado
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  for_each = aws_s3_bucket.data_lake

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "data_lake" {
  for_each = aws_s3_bucket.data_lake

  bucket = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules para optimización de costos
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  for_each = var.enable_lifecycle ? aws_s3_bucket.data_lake : {}

  bucket = each.value.id

  # Rule para bronze (datos crudos)
  rule {
    id     = "bronze-transition"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }

    expiration {
      days = var.bronze_retention_days
    }
  }

  # Rule para silver/gold
  dynamic "rule" {
    for_each = each.key == "bronze" ? [] : [1]

    content {
      id     = "${each.key}-archive"
      status = "Enabled"

      noncurrent_version_expiration {
        noncurrent_days = 30
      }
    }
  }
}
```

**modules/data/s3-data-lake/variables.tf:**

```hcl
variable "project_name" {
  description = "Nombre del proyecto"
  type        = string

  validation {
    condition     = length(var.project_name) > 3 && length(var.project_name) < 30
    error_message = "Project name debe tener entre 3 y 30 caracteres."
  }
}

variable "environment" {
  description = "Entorno (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser dev, staging o prod."
  }
}

variable "enable_versioning" {
  description = "Habilitar versionado en buckets"
  type        = bool
  default     = true
}

variable "enable_lifecycle" {
  description = "Habilitar lifecycle rules"
  type        = bool
  default     = true
}

variable "bronze_retention_days" {
  description = "Días de retención para datos bronze"
  type        = number
  default     = 730  # 2 años
}

variable "kms_key_id" {
  description = "ARN de KMS key para cifrado (opcional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags adicionales"
  type        = map(string)
  default     = {}
}
```

**modules/data/s3-data-lake/outputs.tf:**

```hcl
output "bucket_names" {
  description = "Map de nombres de buckets por capa"
  value       = { for k, v in aws_s3_bucket.data_lake : k => v.id }
}

output "bucket_arns" {
  description = "Map de ARNs de buckets"
  value       = { for k, v in aws_s3_bucket.data_lake : k => v.arn }
}

output "bucket_domains" {
  description = "Map de domain names"
  value       = { for k, v in aws_s3_bucket.data_lake : k => v.bucket_domain_name }
}
```

**modules/data/s3-data-lake/README.md:**

```markdown
# S3 Data Lake Module

Module reutilizable para crear un Data Lake con capas bronze/silver/gold.

## Características

- ✅ Buckets separados por capa
- ✅ Versionado configurable
- ✅ Cifrado (AES256 o KMS)
- ✅ Block public access
- ✅ Lifecycle rules para optimización
- ✅ Tags personalizables

## Usage

\`\`\`hcl
module "data_lake" {
  source = "../../modules/data/s3-data-lake"

  project_name     = "analytics"
  environment      = "prod"
  enable_versioning = true
  enable_lifecycle  = true

  tags = {
    CostCenter = "DataEngineering"
    Owner      = "data-team"
  }
}
\`\`\`

## Inputs

| Name | Type | Default | Description |
|------|------|---------|-------------|
| project_name | string | - | Nombre del proyecto (requerido) |
| environment | string | - | dev/staging/prod (requerido) |
| enable_versioning | bool | true | Habilitar versionado |
| enable_lifecycle | bool | true | Lifecycle rules |
| bronze_retention_days | number | 730 | Retención datos bronze |
| kms_key_id | string | null | KMS key para cifrado |

## Outputs

| Name | Description |
|------|-------------|
| bucket_names | Map de nombres de buckets |
| bucket_arns | ARNs de los buckets |
```

### Step 1.4: Configurar Entorno de Producción

**environments/prod/main.tf:**

```hcl
terraform {
  required_version = ">= 1.7.0"

  # Partial backend config (completed en backend.hcl)
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "production"
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
      Owner       = var.owner_team
    }
  }
}

# Data Lake module
module "data_lake" {
  source = "../../modules/data/s3-data-lake"

  project_name          = var.project_name
  environment           = "prod"
  enable_versioning     = true
  enable_lifecycle      = true
  bronze_retention_days = 1095  # 3 años para prod
  kms_key_id           = aws_kms_key.data_lake.arn

  tags = {
    Compliance = "GDPR,SOC2"
    Backup     = "enabled"
  }
}

# KMS key para cifrado
resource "aws_kms_key" "data_lake" {
  description             = "KMS key for ${var.project_name} data lake encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-datalake-key"
  }
}

resource "aws_kms_alias" "data_lake" {
  name          = "alias/${var.project_name}-datalake"
  target_key_id = aws_kms_key.data_lake.key_id
}
```

**environments/prod/variables.tf:**

```hcl
variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
}

variable "owner_team" {
  description = "Team owner"
  type        = string
}
```

**environments/prod/terraform.tfvars.example:**

```hcl
# Copy to terraform.tfvars and fill values
# ⚠️ Never commit terraform.tfvars to Git!

project_name = "my-analytics-platform"
aws_region   = "us-east-1"
cost_center  = "data-engineering"
owner_team   = "platform-team"
```

**environments/prod/backend.hcl:**

```hcl
# Partial backend configuration
# Usage: terraform init -backend-config=backend.hcl

bucket         = "my-company-terraform-state"
key            = "production/data-platform/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-lock"
encrypt        = true
```

---

## Task 2: Testing con Terratest

### Step 2.1: Instalar Terratest

```bash
cd tests

# Inicializar module Go
go mod init terraform-production-project/tests

# Instalar Terratest
go get github.com/gruntwork-io/terratest/modules/terraform
go get github.com/stretchr/testify/assert
```

### Step 2.2: Escribir Test de Integración

**tests/data_lake_test.go:**

```go
package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestDataLakeModule(t *testing.T) {
	t.Parallel()

	// Configuration del module a testear
	terraformOptions := &terraform.Options{
		// Path al module
		TerraformDir: "../modules/data/s3-data-lake",

		// Variables para el test
		Vars: map[string]interface{}{
			"project_name":     "terratest",
			"environment":      "dev",
			"enable_versioning": true,
			"enable_lifecycle":  false,  // Simplificar para testing
		},

		// Variables de entorno para AWS (usa LocalStack o cuenta de testing)
		EnvVars: map[string]string{
			"AWS_DEFAULT_REGION": "us-east-1",
		},
	}

	// Cleanup al final del test
	defer terraform.Destroy(t, terraformOptions)

	// Init y Apply
	terraform.InitAndApply(t, terraformOptions)

	// TESTS

	// Test 1: Verificar que se crearon 3 buckets (bronze, silver, gold)
	bucketNames := terraform.OutputMap(t, terraformOptions, "bucket_names")
	assert.Equal(t, 3, len(bucketNames), "Should create 3 buckets")

	// Test 2: Verificar que existen las capas esperadas
	assert.Contains(t, bucketNames, "bronze")
	assert.Contains(t, bucketNames, "silver")
	assert.Contains(t, bucketNames, "gold")

	// Test 3: Verificar formato de los nombres
	for layer, name := range bucketNames {
		assert.Contains(t, name, "terratest-datalake")
		assert.Contains(t, name, layer)
		assert.Contains(t, name, "dev")
	}

	// Test 4: Verificar que los buckets tienen ARN
	bucketArns := terraform.OutputMap(t, terraformOptions, "bucket_arns")
	for layer, arn := range bucketArns {
		assert.NotEmpty(t, arn, "Bucket %s should have ARN", layer)
		assert.Contains(t, arn, "arn:aws:s3:::")
	}
}
```

### Step 2.3: Ejecutar Tests

```bash
cd tests

# Run tests
go test -v -timeout 30m

# Output esperado:
# === RUN   TestDataLakeModule
# TestDataLakeModule 2024-03-07T10:30:00Z terraform.go:Init Running: terraform init ...
# TestDataLakeModule 2024-03-07T10:30:05Z terraform.go:Apply Running: terraform apply ...
# TestDataLakeModule 2024-03-07T10:30:30Z terraform.go:Apply Apply complete! Resources: 12 added, 0 changed, 0 destroyed.
# TestDataLakeModule 2024-03-07T10:30:35Z terraform.go:Destroy Running: terraform destroy ...
# --- PASS: TestDataLakeModule (45.23s)
# PASS
# ok      terraform-production-project/tests      45.500s
```

### Step 2.4: Test para Validaciones

**tests/validation_test.go:**

```go
package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestProjectNameValidation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name        string
		projectName string
		expectError bool
	}{
		{"valid-name", "my-project", false},
		{"too-short", "ab", true},
		{"too-long", "this-is-a-very-long-project-name-that-exceeds-limits", true},
		{"valid-max", "project-name-max-length-ok", false},
	}

	for _, tc := range testCases {
		tc := tc  // capture range variable
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			terraformOptions := &terraform.Options{
				TerraformDir: "../modules/data/s3-data-lake",
				Vars: map[string]interface{}{
					"project_name": tc.projectName,
					"environment":  "dev",
				},
			}

			defer terraform.Destroy(t, terraformOptions)

			_, err := terraform.InitAndApplyE(t, terraformOptions)

			if tc.expectError {
				assert.Error(t, err, "Expected validation error for: %s", tc.projectName)
			} else {
				assert.NoError(t, err, "Should not error for: %s", tc.projectName)
			}
		})
	}
}
```

---

## Task 3: CI/CD con GitHub Actions

### Step 3.1: Workflow para Terraform Plan (Pull Requests)

**.github/workflows/terraform-plan.yml:**

```yaml
name: 'Terraform Plan'

on:
  pull_request:
    branches:
      - main
    paths:
      - 'environments/**'
      - 'modules/**'
      - '.github/workflows/terraform-plan.yml'

env:
  TF_VERSION: '1.7.5'
  AWS_REGION: 'us-east-1'

jobs:
  plan:
    name: 'Terraform Plan'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]

    defaults:
      run:
        working-directory: environments/${{ matrix.environment }}

    permissions:
      id-token: write   # For OIDC
      contents: read
      pull-requests: write  # Para comentar en PR

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        id: fmt
        run: terraform fmt -check -recursive
        continue-on-error: true

      - name: Terraform Init
        id: init
        run: terraform init -backend-config=backend.hcl

      - name: Terraform Validate
        id: validate
        run: terraform validate -no-color

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        continue-on-error: true

      - name: Comment Plan on PR
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        env:
          PLAN: "${{ steps.plan.outputs.stdout }}"
        with:
          script: |
            const output = `#### Terraform Plan 📝 \`${{ matrix.environment }}\`

            <details><summary>Show Plan</summary>

            \`\`\`terraform
            ${process.env.PLAN}
            \`\`\`

            </details>

            *Pusher: @${{ github.actor }}, Action: \`${{ github.event_name }}\`*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })

      - name: Fail if Plan Failed
        if: steps.plan.outcome == 'failure'
        run: exit 1
```

### Step 3.2: Workflow para Terraform Apply (Main Branch)

**.github/workflows/terraform-apply.yml:**

```yaml
name: 'Terraform Apply'

on:
  push:
    branches:
      - main
    paths:
      - 'environments/**'
      - 'modules/**'
  workflow_dispatch:  # Manual trigger
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - dev
          - staging
          - prod

env:
  TF_VERSION: '1.7.5'
  AWS_REGION: 'us-east-1'

jobs:
  apply:
    name: 'Terraform Apply'
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'dev' }}

    defaults:
      run:
        working-directory: environments/${{ github.event.inputs.environment || 'dev' }}

    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: terraform init -backend-config=backend.hcl

      - name: Terraform Apply
        run: terraform apply -auto-approve

      - name: Notify Success
        if: success()
        run: |
          echo "✅ Terraform apply successful for ${{ github.event.inputs.environment || 'dev' }}"
```

---

## Task 4: Pre-commit Hooks

### Step 4.1: Instalar pre-commit

```bash
# Install pre-commit
pip install pre-commit

# O con homebrew (macOS)
brew install pre-commit
```

### Step 4.2: Configurar Hooks

**.pre-commit-config.yaml:**

```yaml
repos:
  # Terraform hooks
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.88.0
    hooks:
      - id: terraform_fmt
        name: Terraform format
        description: Rewrites all Terraform files to canonical format

      - id: terraform_validate
        name: Terraform validate
        description: Validates all Terraform configuration files

      - id: terraform_docs
        name: Terraform docs
        description: Inserts input/output documentation into README.md
        args:
          - '--args=--lockfile=false'

      - id: terraform_tflint
        name: Terraform lint
        description: Lints Terraform code

      - id: terraform_tfsec
        name: Terraform security scan
        description: Static analysis for security issues

  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key
        description: Detects private keys in code
```

### Step 4.3: Instalar y Usar Hooks

```bash
# Instalar hooks en tu repositorio
pre-commit install

# Ejecutar manualmente en todos los archivos
pre-commit run --all-files

# Output:
# Terraform format............................................................Passed
# Terraform validate..........................................................Passed
# Terraform docs..............................................................Passed
# Terraform lint..............................................................Passed
# Terraform security scan.....................................................Passed
# Trim Trailing Whitespace....................................................Passed
# Fix End of Files............................................................Passed
# Check Yaml..................................................................Passed

# Ahora en cada commit, los hooks se ejecutarán automáticamente
git add .
git commit -m "Add production infrastructure"
# [pre-commit hooks se ejecutan aquí]
```

---

## Task 5: Secrets Management

### Step 5.1: Usar AWS Secrets Manager

**environments/prod/secrets.tf:**

```hcl
# Crear secret en Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project_name}-db-password-prod"
  description             = "Database password for production"
  recovery_window_in_days = 30

  tags = {
    Environment = "production"
    Sensitive   = "true"
  }
}

# Versión del secret (valor se actualiza fuera de Terraform)
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.db_password.result
  })

  lifecycle {
    ignore_changes = [secret_string]  # Permitir rotación externa
  }
}

# Generar password aleatorio (solo primera vez)
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Uso en otros recursos
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
}

# No exponerlo en outputs
output "db_secret_arn" {
  value       = aws_secretsmanager_secret.db_password.arn
  description = "ARN del secret (no el valor)"
}
```

### Step 5.2: Rotar Secrets

```bash
# Comando para rotar un secret (fuera de Terraform)
aws secretsmanager update-secret \
  --secret-id my-analytics-platform-db-password-prod \
  --secret-string '{"username":"admin","password":"NewPassword123!"}'

# Terraform no detecta cambio (gracias a ignore_changes)
terraform plan
# Output: No changes. Infrastructure is up-to-date.
```

---

## Task 6: Disaster Recovery

### Step 6.1: Script de Backup

**scripts/disaster-recovery.sh:**

```bash
#!/bin/bash
set -e

PROJECT="my-analytics-platform"
BACKUP_DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups/${BACKUP_DATE}"

echo "🔄 Starting disaster recovery backup for ${PROJECT}"

mkdir -p "$BACKUP_DIR"

# 1. Backup Terraform state
echo "📦 Backing up Terraform state..."
for env in dev staging prod; do
  cd "environments/$env"
  terraform state pull > "../../${BACKUP_DIR}/state-${env}.json"
  terraform output -json > "../../${BACKUP_DIR}/outputs-${env}.json"
  cd -
done

# 2. Backup S3 buckets
echo "📦 Backing up S3 bucket list..."
aws s3api list-buckets --query "Buckets[?contains(Name, '${PROJECT}')].Name" \
  > "${BACKUP_DIR}/s3-buckets.json"

# 3. Export infrastructure as code
echo "📦 Exporting current infrastructure..."
# terraformer (optional)
# terraformer import aws --resources=s3,iam,kms --regions=us-east-1

# 4. Git commit backup
echo "📦 Committing backup..."
git add backups/
git commit -m "feat: disaster recovery backup ${BACKUP_DATE}"

# 5. Upload to secure location
echo "📦 Uploading to S3 backup bucket..."
aws s3 cp "${BACKUP_DIR}" \
  "s3://${PROJECT}-disaster-recovery/backups/${BACKUP_DATE}/" \
  --recursive \
  --server-side-encryption AES256

echo "✅ Backup complete: ${BACKUP_DIR}"
echo "🔗 S3: s3://${PROJECT}-disaster-recovery/backups/${BACKUP_DATE}/"
```

### Step 6.2: Script de Restore

**scripts/restore.sh:**

```bash
#!/bin/bash
set -e

if [ $# -eq 0 ]; then
  echo "Usage: $0 <backup-date> <environment>"
  echo "Example: $0 20240307-153000 prod"
  exit 1
fi

BACKUP_DATE=$1
ENVIRONMENT=$2
PROJECT="my-analytics-platform"

echo "⚠️  WARNING: This will restore infrastructure to backup: ${BACKUP_DATE}"
echo "Environment: ${ENVIRONMENT}"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

# Download backup from S3
echo "📥 Downloading backup..."
aws s3 cp \
  "s3://${PROJECT}-disaster-recovery/backups/${BACKUP_DATE}/" \
  "restore-${BACKUP_DATE}/" \
  --recursive

# Restore state
echo "🔄 Restoring Terraform state..."
cd "environments/${ENVIRONMENT}"
cat "../../restore-${BACKUP_DATE}/state-${ENVIRONMENT}.json" | terraform state push -

# Apply to ensure consistency
echo "🔄 Applying Terraform to sync infrastructure..."
terraform plan
read -p "Apply this plan? (yes/no): " apply_confirm

if [ "$apply_confirm" == "yes" ]; then
  terraform apply
  echo "✅ Restore complete"
else
  echo "⚠️  State restored but changes not applied"
fi
```

---

## Task 7: Makefile para Automatización

**Makefile:**

```makefile
.PHONY: help init plan apply destroy validate test fmt docs

# Variables
ENV ?= dev
TF_DIR = environments/$(ENV)

help:
	@echo "Terraform Production Project"
	@echo ""
	@echo "Usage:"
	@echo "  make init ENV=dev        - Initialize Terraform"
	@echo "  make plan ENV=staging    - Run Terraform plan"
	@echo "  make apply ENV=prod      - Apply changes"
	@echo "  make destroy ENV=dev     - Destroy infrastructure"
	@echo "  make validate            - Validate all configs"
	@echo "  make test                - Run tests"
	@echo "  make fmt                 - Format code"
	@echo "  make docs                - Generate documentation"

init:
	@echo "🔄 Initializing $(ENV) environment..."
	cd $(TF_DIR) && terraform init -backend-config=backend.hcl

plan: init
	@echo "📋 Planning $(ENV) environment..."
	cd $(TF_DIR) && terraform plan

apply: init
	@echo "🚀 Applying $(ENV) environment..."
	cd $(TF_DIR) && terraform apply

destroy: init
	@echo "⚠️  WARNING: Destroying $(ENV) environment..."
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		cd $(TF_DIR) && terraform destroy; \
	fi

validate:
	@echo "✅ Validating all environments..."
	@for env in dev staging prod; do \
		echo "Validating $$env..."; \
		cd environments/$$env && terraform init -backend=false && terraform validate || exit 1; \
		cd ../..; \
	done

test:
	@echo "🧪 Running tests..."
	cd tests && go test -v -timeout 30m

fmt:
	@echo "🎨 Formatting code..."
	terraform fmt -recursive .

docs:
	@echo "📚 Generating documentation..."
	terraform-docs markdown table --output-file README.md modules/data/s3-data-lake

plan-all:
	@for env in dev staging prod; do \
		echo "Planning $$env..."; \
		make plan ENV=$$env; \
	done
```

**Uso:**

```bash
# Ver ayuda
make help

# Plan para development
make plan ENV=dev

# Apply a staging
make apply ENV=staging

# Validar todos los entornos
make validate

# Run tests
make test

# Format all code
make fmt
```

---

## ✅ Checklist Final - Production Readiness

### 🏗️ Estructura
- [ ] Proyecto organizado en modules reutilizables
- [ ] Separación clara de entornos (dev/staging/prod)
- [ ] `.gitignore` configurado correctamente
- [ ] README detallado en cada module

### 🧪 Testing
- [ ] Tests unitarios con Terratest
- [ ] Tests de integración funcionando
- [ ] Validaciones en inputs de modules

### 🔄 CI/CD
- [ ] Pipeline de `terraform plan` en PRs
- [ ] Pipeline de `terraform apply` protegido
- [ ] Aprobaciones manuales para producción
- [ ] Notificaciones de deploment

### 🔒 Seguridad
- [ ] Secrets en AWS Secrets Manager
- [ ] State file cifrado
- [ ] KMS keys con rotación
- [ ] Pre-commit hooks con tfsec

### 📊 Observabilidad
- [ ] Tags consistentes en recursos
- [ ] Outputs documentados
- [ ] Logs de cambios en Git

### 🛡️ Disaster Recovery
- [ ] Backup automatizado de state
- [ ] Script de restore probado
- [ ] Versionado de S3 habilitado
- [ ] Documentación de recovery

---

## 📚 Recursos

- [Terratest Documentation](https://terratest.gruntwork.io/)
- [GitHub Actions for Terraform](https://github.com/hashicorp/setup-terraform)
- [Pre-commit Terraform Hooks](https://github.com/antonbabenko/pre-commit-terraform)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

---

**¡Felicidades! 🎉** Has completed el module de Infrastructure as Code. Ahora tienes las habilidades para gestionar infraestructura cloud a level enterprise con Terraform.

**Tu infraestructura ahora es:**
- ✅ Reproducible
- ✅ Versionada
- ✅ Testeada
- ✅ Segura
- ✅ Automatizada
- ✅ Lista para producción

**Próximos steps:**
- Aplicar estos patrones en proyectos reales
- Explorar Terragrunt para DRY configs
- Implementar policy-as-code con Sentinel/OPA
- Integrar con observability (DataDog, New Relic)
