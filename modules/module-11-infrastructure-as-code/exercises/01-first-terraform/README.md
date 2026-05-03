# Exercise 01: First Terraform

## Description

Este exercise te introduce al mundo de Infrastructure as Code con Terraform. You will learn los conceptos fundamentales: instalación, configuration básica, gestión del ciclo de vida de recursos, y los comandos esenciales de Terraform. Crearás tu primer recurso en AWS (S3 bucket) usando LocalStack para desarrollo local sin costos.

**Estimated Duration:** 90-120 minutes

## Prerequisites

- Docker y Docker Compose instalados
- Editor de código (VS Code recomendado)
- Conocimientos básicos de línea de comandos
- Cuenta de AWS (opcional, usaremos LocalStack)

## Objectives de Aprendizaje

Al completar este exercise serás capaz de:

1. ✅ Instalar y configure Terraform en tu entorno local
2. ✅ Escribir configuraciones básicas de Terraform (HCL)
3. ✅ Crear y gestionar recursos de infraestructura con Terraform
4. ✅ Utilizar variables y outputs en tus configuraciones
5. ✅ Entender el ciclo de vida de los recursos: init, plan, apply, destroy
6. ✅ Comprender el archivo de estado (state file) y su importancia

---

## Task 1: Instalar Terraform y Verificar Instalación

### Description

Instalarás Terraform en tu sistema y verificarás que está funcionando correctamente. También configurarás LocalStack para simular servicios de AWS de forma local.

### Steps

#### 1.1. Instalar Terraform

**En Linux:**

```bash
# Descargar e instalar Terraform
wget https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip
unzip terraform_1.7.5_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verificar instalación
terraform version
```

**En macOS:**

```bash
# Usando Homebrew
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verificar instalación
terraform version
```

**En Windows:**

```powershell
# Usando Chocolatey
choco install terraform

# Verificar instalación
terraform version
```

#### 1.2. Configurar LocalStack

<details>
<summary>📄 docker-compose.yml - LocalStack Configuration</summary>

```yaml
version: '3.8'

services:
  localstack:
    image: localstack/localstack:3.1
    ports:
      - "4566:4566"            # LocalStack Gateway
      - "4510-4559:4510-4559"  # Servicios externos
    environment:
      - SERVICES=s3,iam,dynamodb,glue,athena
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
      - DOCKER_HOST=unix:///var/run/docker.sock
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-east-1
    volumes:
      - "./localstack-data:/tmp/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
    networks:
      - terraform-network

networks:
  terraform-network:
    driver: bridge
```

</details>

#### 1.3. Iniciar LocalStack

```bash
# Crear directorio para el exercise
mkdir -p ~/terraform-exercises/01-first-terraform
cd ~/terraform-exercises/01-first-terraform

# Copiar docker-compose.yml y iniciar
docker-compose up -d

# Verificar que LocalStack está corriendo
docker-compose ps
curl http://localhost:4566/_localstack/health
```

#### 1.4. Instalar AWS CLI (para testing)

```bash
# Linux/macOS
pip install awscli-local

# Verificar conexión con LocalStack
awslocal s3 ls
```

### Output Esperado

```plaintext
Terraform v1.7.5
on linux_amd64

LocalStack Health:
{
  "services": {
    "s3": "available",
    "iam": "available",
    "dynamodb": "available"
  }
}
```

### Conceptos Clave

- **Terraform**: Herramienta de IaC que permite definir infraestructura mediante código declarativo
- **LocalStack**: Emulador de servicios AWS para desarrollo y testing local
- **AWS CLI**: Herramienta de línea de comandos para interactuar con AWS/LocalStack

---

## Task 2: Crear Primer Recurso S3 Bucket

### Description

Crearás tu primera configuration de Terraform para provisionar un bucket S3 en LocalStack. You will learn la sintaxis básica de HCL (HashiCorp Configuration Language).

### Steps

#### 2.1. Crear Archivo de Configuration Principal

<details>
<summary>📄 main.tf - Primera Configuration de Terraform</summary>

```hcl
# main.tf
# Configuration del proveedor AWS para LocalStack

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configuration del proveedor AWS apuntando a LocalStack
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  # Endpoints personalizados para LocalStack
  endpoints {
    s3 = "http://localhost:4566"
  }
}

# Recurso: Bucket S3
resource "aws_s3_bucket" "my_first_bucket" {
  bucket = "mi-primer-bucket-terraform"

  tags = {
    Name        = "Mi Primer Bucket"
    Environment = "Learning"
    ManagedBy   = "Terraform"
    Creator     = "Student"
  }
}

# Configuration de versionamiento para el bucket
resource "aws_s3_bucket_versioning" "my_first_bucket_versioning" {
  bucket = aws_s3_bucket.my_first_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

</details>

#### 2.2. Inicializar Terraform

```bash
# Inicializar el directorio de trabajo
terraform init

# Esto descargará los plugins necesarios (provider AWS)
```

#### 2.3. Ver el Plan de Ejecución

```bash
# Ver qué recursos se crearán sin aplicar cambios
terraform plan

# Guardar el plan en un archivo
terraform plan -out=tfplan
```

#### 2.4. Aplicar la Configuration

```bash
# Aplicar los cambios y create el bucket
terraform apply

# O aplicar sin confirmación
terraform apply -auto-approve
```

#### 2.5. Verificar el Bucket Creado

```bash
# Listar buckets en LocalStack
awslocal s3 ls

# Obtener detalles del bucket
awslocal s3api get-bucket-versioning --bucket mi-primer-bucket-terraform
```

### Output Esperado

```plaintext
Terraform will perform the following actions:

  # aws_s3_bucket.my_first_bucket will be created
  + resource "aws_s3_bucket" "my_first_bucket" {
      + bucket                      = "mi-primer-bucket-terraform"
      + id                          = (known after apply)
      + tags                        = {
          + "Creator"     = "Student"
          + "Environment" = "Learning"
          + "ManagedBy"   = "Terraform"
          + "Name"        = "Mi Primer Bucket"
        }
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

### Conceptos Clave

- **terraform {}**: Bloque de configuration de Terraform (versión, providers)
- **provider**: Configuration del proveedor de infraestructura (AWS, Azure, GCP, etc.)
- **resource**: Componente de infraestructura que quieres create
- **HCL**: HashiCorp Configuration Language - sintaxis declarativa de Terraform

---

## Task 3: Variables y Outputs

### Description

You will learn a parametrizar tus configuraciones usando variables y a exponer información importante mediante outputs. Esto hace tu código más reutilizable y flexible.

### Steps

#### 3.1. Crear Archivo de Variables

<details>
<summary>📄 variables.tf - Definición de Variables</summary>

```hcl
# variables.tf
# Definición de variables de entrada

variable "aws_region" {
  description = "Región de AWS donde se desplegarán los recursos"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Nombre del bucket S3 a create"
  type        = string
  default     = "mi-bucket-terraform"

  validation {
    condition     = length(var.bucket_name) <= 63 && length(var.bucket_name) >= 3
    error_message = "El nombre del bucket debe tener entre 3 y 63 caracteres."
  }
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "El ambiente debe ser: development, staging, o production."
  }
}

variable "enable_versioning" {
  description = "Habilitar versionamiento en el bucket"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags comunes para todos los recursos"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "Learning-IaC"
  }
}
```

</details>

#### 3.2. Crear Archivo de Outputs

<details>
<summary>📄 outputs.tf - Definición de Outputs</summary>

```hcl
# outputs.tf
# Outputs para exponer información de los recursos creados

output "bucket_id" {
  description = "ID del bucket S3 creado"
  value       = aws_s3_bucket.my_first_bucket.id
}

output "bucket_arn" {
  description = "ARN del bucket S3"
  value       = aws_s3_bucket.my_first_bucket.arn
}

output "bucket_region" {
  description = "Región donde se creó el bucket"
  value       = aws_s3_bucket.my_first_bucket.region
}

output "bucket_domain_name" {
  description = "Domain name del bucket"
  value       = aws_s3_bucket.my_first_bucket.bucket_domain_name
}

output "versioning_status" {
  description = "Estado del versionamiento"
  value       = aws_s3_bucket_versioning.my_first_bucket_versioning.versioning_configuration[0].status
}

output "bucket_tags" {
  description = "Tags aplicados al bucket"
  value       = aws_s3_bucket.my_first_bucket.tags_all
}
```

</details>

#### 3.3. Actualizar main.tf para Usar Variables

<details>
<summary>📄 main.tf - Usando Variables</summary>

```hcl
# main.tf
# Configuration actualizada con variables

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
    s3 = "http://localhost:4566"
  }
}

# Recurso: Bucket S3 con variables
resource "aws_s3_bucket" "my_first_bucket" {
  bucket = var.bucket_name

  tags = merge(
    var.tags,
    {
      Name        = var.bucket_name
      Environment = var.environment
    }
  )
}

# Versionamiento condicional
resource "aws_s3_bucket_versioning" "my_first_bucket_versioning" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.my_first_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

</details>

#### 3.4. Crear Archivo de Valores (terraform.tfvars)

<details>
<summary>📄 terraform.tfvars - Valores de Variables</summary>

```hcl
# terraform.tfvars
# Valores personalizados para las variables

bucket_name        = "data-learning-bucket-2024"
environment        = "development"
enable_versioning  = true
aws_region         = "us-east-1"

tags = {
  ManagedBy   = "Terraform"
  Project     = "Learning-IaC"
  Team        = "Data-Engineering"
  CostCenter  = "Training"
}
```

</details>

#### 3.5. Aplicar con Variables

```bash
# Verificar el plan con las nuevas variables
terraform plan

# Aplicar
terraform apply -auto-approve

# Ver los outputs
terraform output

# Ver un output específico
terraform output bucket_arn

# Ver output en formato JSON
terraform output -json
```

### Output Esperado

```plaintext
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

bucket_arn = "arn:aws:s3:::data-learning-bucket-2024"
bucket_domain_name = "data-learning-bucket-2024.s3.amazonaws.com"
bucket_id = "data-learning-bucket-2024"
bucket_region = "us-east-1"
bucket_tags = {
  "CostCenter" = "Training"
  "Environment" = "development"
  "ManagedBy" = "Terraform"
  "Name" = "data-learning-bucket-2024"
  "Project" = "Learning-IaC"
  "Team" = "Data-Engineering"
}
versioning_status = "Enabled"
```

### Conceptos Clave

- **Variables**: Parámetros de entrada que hacen tu código reutilizable
- **Outputs**: Exponen información de los recursos creados
- **terraform.tfvars**: Archivo para valores de variables (no debe versionarse si contiene secretos)
- **Validations**: Reglas para validate valores de variables
- **merge()**: Función para combinar mapas/objetos

---

## Task 4: Terraform Init, Plan, Apply, Destroy

### Description

Dominarás el ciclo de vida completo de recursos en Terraform, comprendiendo cada comando y su propósito en el workflow de IaC.

### Steps

#### 4.1. Terraform Init - Inicialización

```bash
# Inicializar (si no lo has hecho)
terraform init

# Re-inicializar (útil después de cambiar providers)
terraform init -upgrade

# Ver qué hace init
ls -la .terraform/
cat .terraform.lock.hcl
```

**¿Qué hace `terraform init`?**
- Descarga providers definidos en `required_providers`
- Inicializa el backend (dónde se guarda el state)
- Create el directorio `.terraform/`
- Genera `.terraform.lock.hcl` (lockfile de dependencias)

#### 4.2. Terraform Plan - Previsualización

```bash
# Plan básico
terraform plan

# Plan con archivo de variables específico
terraform plan -var-file="dev.tfvars"

# Plan guardado (para aplicar exactamente lo planeado)
terraform plan -out=tfplan

# Plan con variables por línea de comandos
terraform plan -var="bucket_name=custom-bucket-name"

# Plan mostrando solo recursos específicos
terraform plan -target=aws_s3_bucket.my_first_bucket
```

#### 4.3. Terraform Apply - Aplicación

```bash
# Apply interactivo (pide confirmación)
terraform apply

# Apply automático
terraform apply -auto-approve

# Apply desde un plan guardado
terraform apply tfplan

# Apply con target específico
terraform apply -target=aws_s3_bucket.my_first_bucket
```

#### 4.4. Terraform Destroy - Eliminación

```bash
# Destroy interactivo
terraform destroy

# Destroy automático
terraform destroy -auto-approve

# Destroy de recurso específico
terraform destroy -target=aws_s3_bucket.my_first_bucket

# Plan de destroy (ver qué se eliminará)
terraform plan -destroy
```

#### 4.5. Otros Comandos Útiles

<details>
<summary>📄 comandos-utiles.sh - Comandos Terraform Importantes</summary>

```bash
#!/bin/bash
# Comandos útiles de Terraform

# Ver estado actual
terraform show

# Listar recursos en el state
terraform state list

# Ver detalles de un recurso específico
terraform state show aws_s3_bucket.my_first_bucket

# Validar configuration sintáctica
terraform validate

# Formatear archivos .tf
terraform fmt

# Formatear recursivamente
terraform fmt -recursive

# Ver versión
terraform version

# Ver providers instalados
terraform providers

# Ver outputs
terraform output

# Refresh del state (sincronizar con realidad)
terraform refresh

# Ver graph de dependencias (requiere graphviz)
terraform graph | dot -Tpng > graph.png

# Console interactiva para evaluar expresiones
terraform console
```

</details>

```bash
# Ejecutar comandos útiles
chmod +x comandos-utiles.sh
./comandos-utiles.sh
```

#### 4.6. Experimento: Ciclo de Vida Completo

<details>
<summary>📄 experiment.tf - Recurso de Test</summary>

```hcl
# experiment.tf
# Recurso adicional para experimentar con ciclo de vida

resource "aws_s3_bucket" "experiment" {
  bucket = "experiment-lifecycle-bucket"

  tags = {
    Name        = "Experimento"
    Purpose     = "Learning Lifecycle"
    Temporary   = "true"
  }
}

output "experiment_bucket" {
  description = "Bucket de experimento"
  value = {
    id  = aws_s3_bucket.experiment.id
    arn = aws_s3_bucket.experiment.arn
  }
}
```

</details>

```bash
# 1. Inicializar (si agregaste nuevo provider)
terraform init

# 2. Validar sintaxis
terraform validate

# 3. Formatear código
terraform fmt

# 4. Ver plan
terraform plan

# 5. Aplicar
terraform apply -auto-approve

# 6. Ver estado
terraform show

# 7. Verificar en LocalStack
awslocal s3 ls

# 8. Modificar el recurso en experiment.tf (cambiar un tag)
# Editar experiment.tf y cambiar Name = "Experimento Modificado"

# 9. Ver plan de cambios
terraform plan

# 10. Aplicar cambios
terraform apply -auto-approve

# 11. Destruir solo el recurso de experimento
terraform destroy -target=aws_s3_bucket.experiment -auto-approve

# 12. Verificar que se eliminó
awslocal s3 ls
terraform state list
```

### Output Esperado

```plaintext
# terraform init
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.40.0...

# terraform plan
Plan: 3 to add, 0 to change, 0 to destroy.

# terraform apply
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

# terraform destroy
Destroy complete! Resources: 3 destroyed.
```

### Conceptos Clave

- **init**: Primera etapa, descarga plugins y prepara backend
- **plan**: Previsualiza cambios sin aplicarlos (dry-run)
- **apply**: Execute cambios en la infraestructura real
- **destroy**: Elimina recursos gestionados por Terraform
- **state**: Archivo que mantiene el estado actual de la infraestructura

---

## Task 5: State File Básico

### Description

Comprenderás el archivo de estado (terraform.tfstate), su estructura, propósito e importancia en el funcionamiento de Terraform.

### Steps

#### 5.1. Entender el State File

```bash
# Ver el contenido del state file
cat terraform.tfstate

# Ver en formato legible (pretty print)
cat terraform.tfstate | jq '.'

# Listar recursos en el state
terraform state list

# Ver detalles de un recurso en el state
terraform state show aws_s3_bucket.my_first_bucket
```

#### 5.2. Estructura del State File

<details>
<summary>📄 state-structure.json - Estructura del State File</summary>

```json
{
  "version": 4,
  "terraform_version": "1.7.5",
  "serial": 1,
  "lineage": "unique-id-for-this-state",
  "outputs": {
    "bucket_id": {
      "value": "data-learning-bucket-2024",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_s3_bucket",
      "name": "my_first_bucket",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 0,
          "attributes": {
            "id": "data-learning-bucket-2024",
            "bucket": "data-learning-bucket-2024",
            "arn": "arn:aws:s3:::data-learning-bucket-2024",
            "tags": {
              "Name": "data-learning-bucket-2024",
              "Environment": "development"
            }
          }
        }
      ]
    }
  ]
}
```

</details>

#### 5.3. Comandos de Manipulación del State

<details>
<summary>📄 state-commands.sh - Comandos de State Management</summary>

```bash
#!/bin/bash
# Comandos para gestionar el state file

# 1. Listar todos los recursos
echo "=== Recursos en el State ==="
terraform state list

# 2. Ver detalles de un recurso
echo -e "\n=== Detalles del Bucket ==="
terraform state show aws_s3_bucket.my_first_bucket

# 3. Hacer backup del state
echo -e "\n=== Backup del State ==="
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d-%H%M%S)

# 4. Pull del state (útil con remote state)
echo -e "\n=== Pull State ==="
terraform state pull > state-backup.json

# 5. Ver recursos en formato JSON
echo -e "\n=== State en JSON ==="
terraform show -json | jq '.values.root_module.resources[] | {type, name, values: .values.id}'

# 6. Validar el state
echo -e "\n=== Validar State ==="
terraform validate

# 7. Refresh del state (sincronizar con realidad)
echo -e "\n=== Refresh State ==="
terraform refresh

echo -e "\n✅ State management commands completed"
```

</details>

```bash
# Ejecutar comandos de state
chmod +x state-commands.sh
./state-commands.sh
```

#### 5.4. Experimentar con State Drift

<details>
<summary>📄 test-drift.sh - Detectar Drift en State</summary>

```bash
#!/bin/bash
# Script para experimentar con state drift

echo "=== 1. Crear recurso con Terraform ==="
terraform apply -auto-approve

echo -e "\n=== 2. Modificar recurso manualmente (fuera de Terraform) ==="
# Agregar un tag manualmente usando AWS CLI
awslocal s3api put-bucket-tagging \
  --bucket data-learning-bucket-2024 \
  --tagging 'TagSet=[{Key=ManualTag,Value=AddedOutsideTerraform}]'

echo -e "\n=== 3. Ver tags actuales en AWS ==="
awslocal s3api get-bucket-tagging --bucket data-learning-bucket-2024

echo -e "\n=== 4. Terraform Plan detecta el drift ==="
terraform plan

echo -e "\n=== 5. Refresh actualiza el state ==="
terraform refresh

echo -e "\n=== 6. Apply restaura la configuration deseada ==="
terraform apply -auto-approve

echo -e "\n=== 7. Verificar que el tag manual fue removido ==="
awslocal s3api get-bucket-tagging --bucket data-learning-bucket-2024
```

</details>

```bash
# Ejecutar experimento de drift
chmod +x test-drift.sh
./test-drift.sh
```

#### 5.5. State File Best Practices

<details>
<summary>📄 .gitignore - Proteger el State File</summary>

```gitignore
# .gitignore
# Archivos de Terraform que no deben versionarse

# State files
*.tfstate
*.tfstate.*
*.tfstate.backup

# Crash log files
crash.log
crash.*.log

# Variables files que puedan contener secretos
*.tfvars
*.tfvars.json

# CLI configuration files
.terraformrc
terraform.rc

# Directory for plugins
.terraform/
.terraform.lock.hcl

# Plans
*.tfplan

# Local environment files
.env
.env.local
```

</details>

#### 5.6. Crear Documentación del State

<details>
<summary>📄 STATE-EXPLAINED.md - Documentación del State</summary>

```markdown
# State File - Explicación Detallada

## ¿Qué es el State File?

El `terraform.tfstate` es un archivo JSON que mantiene el mapeo entre:
- Tu configuration de Terraform (.tf files)
- Los recursos reales en tu proveedor (AWS, Azure, etc.)

## ¿Por qué es importante?

1. **Tracking**: Terraform sabe qué recursos gestionó
2. **Performance**: No necesita consultar la API en cada operación
3. **Colaboración**: Estado compartido entre el equipo
4. **Metadata**: Guarda información adicional de los recursos

## Componentes del State

### 1. Version
```json
"version": 4
```
Versión del formato del state file.

### 2. Terraform Version
```json
"terraform_version": "1.7.5"
```
Versión de Terraform que creó/modificó el state.

### 3. Serial
```json
"serial": 1
```
Número incremental para cada modificación (previene conflictos).

### 4. Lineage
```json
"lineage": "unique-id"
```
ID único para este state (previene mezclar states diferentes).

### 5. Outputs
```json
"outputs": {
  "bucket_id": {
    "value": "my-bucket",
    "type": "string"
  }
}
```
Valores de los outputs definidos.

### 6. Resources
```json
"resources": [
  {
    "mode": "managed",
    "type": "aws_s3_bucket",
    "name": "my_bucket",
    "instances": [...]
  }
]
```
Lista de todos los recursos gestionados.

## Best Practices

✅ **DO:**
- Usar remote state en equipo
- Hacer backup antes de operaciones peligrosas
- Usar state locking
- Versionar tu configuration (.tf), no el state

❌ **DON'T:**
- Editar el state file manualmente
- Versionar el state en Git
- Compartir state por email/chat
- Eliminar el state sin backup

## State Drift

**Drift** = Cuando el estado real difiere del state file.

Causas comunes:
- Cambios manuales en la consola de AWS
- Scripts que modifican recursos
- Otro automation tool modificando recursos

Detección:
```bash
terraform plan  # Muestra diferencias
terraform refresh  # Actualiza el state
```

## Comandos Útiles

```bash
# Ver lista de recursos
terraform state list

# Ver detalles de recurso
terraform state show RESOURCE

# Mover recurso en el state
terraform state mv SOURCE DEST

# Remover recurso del state
terraform state rm RESOURCE

# Pull state (remote)
terraform state pull

# Push state (remote)
terraform state push
```

## Próximo Step

En exercises posteriores you will learn:
- Remote state con S3
- State locking con DynamoDB
- Workspaces para múltiples ambientes
```

</details>

### Output Esperado

```plaintext
=== Recursos en el State ===
aws_s3_bucket.my_first_bucket
aws_s3_bucket_versioning.my_first_bucket_versioning

=== State Drift Detected ===
Terraform detected the following changes made outside of Terraform:
  # aws_s3_bucket.my_first_bucket has changed
  ~ tags     = {
      + "ManualTag" = "AddedOutsideTerraform"
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

### Conceptos Clave

- **State File**: Representación del estado actual de tu infraestructura
- **Serial**: Contador de versiones del state para prevenir conflictos
- **Drift Detection**: Terraform detecta cambios fuera de su control
- **State Commands**: terraform state list/show/mv/rm para manipular el state
- **Remote State**: (Próximo exercise) State almacenado centralmente

---

## Task 6: Modificar Recursos

### Description

You will learn cómo Terraform maneja modificaciones a recursos existentes, entendiendo cuándo actualiza in-place vs cuándo destruye y recrea recursos.

### Steps

#### 6.1. Crear Configuration Extendida

<details>
<summary>📄 complete-bucket.tf - Bucket con Configuraciones Adicionales</summary>

```hcl
# complete-bucket.tf
# Bucket S3 con múltiples configuraciones

# Bucket principal
resource "aws_s3_bucket" "data_bucket" {
  bucket = "complete-data-bucket-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "Data Bucket - ${var.environment}"
      Environment = var.environment
      Purpose     = "Data Storage"
    }
  )
}

# Versionamiento
resource "aws_s3_bucket_versioning" "data_bucket_versioning" {
  bucket = aws_s3_bucket.data_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "data_bucket_lifecycle" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    # Mover versiones antiguas a Glacier después de 90 days
    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    # Eliminar versiones antiguas después de 365 days
    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }

  rule {
    id     = "delete-incomplete-uploads"
    status = "Enabled"

    # Limpiar uploads incompletos después de 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data_bucket_encryption" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Public Access Block
resource "aws_s3_bucket_public_access_block" "data_bucket_public_block" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Logging
resource "aws_s3_bucket" "log_bucket" {
  bucket = "logs-${var.environment}-bucket"

  tags = merge(
    var.tags,
    {
      Name    = "Logs Bucket"
      Purpose = "Access Logs"
    }
  )
}

resource "aws_s3_bucket_logging" "data_bucket_logging" {
  bucket = aws_s3_bucket.data_bucket.id

  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "data-bucket-logs/"
}

# Outputs
output "data_bucket_details" {
  description = "Detalles completos del bucket"
  value = {
    id                  = aws_s3_bucket.data_bucket.id
    arn                 = aws_s3_bucket.data_bucket.arn
    region              = aws_s3_bucket.data_bucket.region
    versioning_enabled  = aws_s3_bucket_versioning.data_bucket_versioning.versioning_configuration[0].status
    encryption_enabled  = true
  }
}
```

</details>

#### 6.2. Aplicar Configuration Inicial

```bash
# Aplicar configuration completa
terraform apply -auto-approve

# Verificar recursos creados
terraform state list
awslocal s3 ls
```

#### 6.3. Modificaciones In-Place (Sin Recreación)

<details>
<summary>📄 Cambios que se Actualizan In-Place</summary>

```hcl
# Estos cambios NO destruyen el recurso, solo lo actualizan:

# 1. Cambiar TAGS (modificación in-place)
resource "aws_s3_bucket" "data_bucket" {
  bucket = "complete-data-bucket-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "Data Bucket - UPDATED"  # ← Cambio in-place
      Environment = var.environment
      Purpose     = "Data Storage and Analytics"  # ← Cambio in-place
      Version     = "2.0"  # ← Tag nuevo (in-place)
    }
  )
}

# 2. Cambiar configuration de lifecycle (modificación in-place)
resource "aws_s3_bucket_lifecycle_configuration" "data_bucket_lifecycle" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 60  # ← Cambio de 90 a 60 days (in-place)
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 180  # ← Cambio de 365 a 180 days (in-place)
    }
  }

  rule {
    id     = "delete-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 3  # ← Cambio de 7 a 3 days (in-place)
    }
  }
}
```

</details>

```bash
# Ver el plan (muestra ~ para modificaciones in-place)
terraform plan

# Aplicar cambios
terraform apply -auto-approve
```

#### 6.4. Modificaciones con Recreación (Destroy + Create)

<details>
<summary>📄 Cambios que Requieren Recreación</summary>

```hcl
# Estos cambios DESTRUYEN y RECREAN el recurso:

# 1. Cambiar el NOMBRE del bucket (requiere recreación)
resource "aws_s3_bucket" "data_bucket" {
  bucket = "new-complete-data-bucket-${var.environment}"  # ← Cambio de nombre
  # NOTA: Esto destruirá el bucket anterior y creará uno nuevo
  # ¡Todos los datos se perderán!

  tags = merge(
    var.tags,
    {
      Name        = "New Data Bucket"
      Environment = var.environment
    }
  )
}
```

</details>

```bash
# Ver el plan (muestra -/+ para recreación)
terraform plan

# ADVERTENCIA: Esto destruirá datos si el bucket tiene objetos
# En producción, NUNCA hacer esto sin backup
terraform apply
```

#### 6.5. Usar Lifecycle Rules para Prevenir Destrucción

<details>
<summary>📄 prevent-destroy.tf - Proteger Recursos Críticos</summary>

```hcl
# prevent-destroy.tf
# Prevenir destrucción accidental de recursos críticos

resource "aws_s3_bucket" "protected_bucket" {
  bucket = "protected-critical-data-bucket"

  tags = {
    Name      = "Protected Bucket"
    Critical  = "true"
    ManagedBy = "Terraform"
  }

  # Lifecycle: Prevenir destrucción
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket" "replaceable_bucket" {
  bucket = "temp-replaceable-bucket-${formatdate("YYYYMMDD", timestamp())}"

  tags = {
    Name      = "Temporary Bucket"
    Temporary = "true"
  }

  # Lifecycle: Crear antes de destruir
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_s3_bucket" "ignored_bucket" {
  bucket = "bucket-with-ignored-changes"

  tags = {
    Name        = "Ignored Changes Bucket"
    Environment = "test"
    # Este tag puede cambiar manualmente sin que Terraform lo revierta
    LastModified = "manual-change-allowed"
  }

  # Lifecycle: Ignorar cambios en tags específicos
  lifecycle {
    ignore_changes = [
      tags["LastModified"],
      tags["ManualTag"]
    ]
  }
}
```

</details>

#### 6.6. Replace vs Taint

```bash
# Método 1: Replace (Terraform 1.0+)
# Forzar reemplazo de un recurso específico
terraform apply -replace=aws_s3_bucket.data_bucket

# Método 2: Taint (obsoleto, pero común en versiones antiguas)
# Marcar recurso para recreación en el próximo apply
terraform taint aws_s3_bucket.data_bucket
terraform apply

# Untaint (remover marca de taint)
terraform untaint aws_s3_bucket.data_bucket
```

#### 6.7. Experimento Completo de Modificaciones

<details>
<summary>📄 modification-experiment.sh - Script de Experimentación</summary>

```bash
#!/bin/bash
# Experimento completo de modificaciones en Terraform

set -e

echo "=== Experimento: Modificaciones de Recursos en Terraform ==="

# Setup
EXPERIMENT_DIR="modification-experiment"
mkdir -p "$EXPERIMENT_DIR"
cd "$EXPERIMENT_DIR"

# Crear configuration inicial
cat > main.tf << 'EOF'
terraform {
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

resource "aws_s3_bucket" "test" {
  bucket = "modification-test-v1"

  tags = {
    Name    = "Original"
    Version = "1"
  }
}

output "bucket_id" {
  value = aws_s3_bucket.test.id
}
EOF

echo -e "\n1️⃣  Creando recurso inicial..."
terraform init
terraform apply -auto-approve

echo -e "\n2️⃣  Modificación in-place (cambiar tag)..."
sed -i 's/Version = "1"/Version = "2"/' main.tf
terraform plan
terraform apply -auto-approve

echo -e "\n3️⃣  Modificación que requiere recreación (cambiar nombre)..."
sed -i 's/bucket = "modification-test-v1"/bucket = "modification-test-v2"/' main.tf
terraform plan
echo "Nota: Muestra -/+ indicando destruir y recrear"

echo -e "\n4️⃣  Limpieza..."
terraform destroy -auto-approve
cd ..
rm -rf "$EXPERIMENT_DIR"

echo -e "\n✅ Experimento completed"
```

</details>

```bash
chmod +x modification-experiment.sh
./modification-experiment.sh
```

### Output Esperado

```plaintext
# Modificación in-place (~)
Terraform will perform the following actions:

  # aws_s3_bucket.data_bucket will be updated in-place
  ~ resource "aws_s3_bucket" "data_bucket" {
      ~ tags     = {
          ~ "Name" = "Data Bucket" -> "Data Bucket - UPDATED"
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.

# Recreación (-/+)
Terraform will perform the following actions:

  # aws_s3_bucket.data_bucket must be replaced
-/+ resource "aws_s3_bucket" "data_bucket" {
      ~ bucket = "old-bucket-name" -> "new-bucket-name" # forces replacement
      ~ id     = "old-bucket-name" -> (known after apply)
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

### Conceptos Clave

- **In-Place Updates**: Modificaciones que no requieren recrear el recurso (~)
- **Replace**: Destruir y recrear un recurso (-/+)
- **lifecycle.prevent_destroy**: Protección contra eliminación accidental
- **lifecycle.create_before_destroy**: Crear nuevo antes de eliminar antiguo
- **lifecycle.ignore_changes**: Ignorar cambios en atributos específicos
- **terraform replace**: Forzar reemplazo de recurso

---

## Troubleshooting

### Problema 1: Error de Inicialización

**Error:**
```
Error: Failed to install provider
```

**Solution:**
```bash
# Limpiar cache y reinicializar
rm -rf .terraform
rm .terraform.lock.hcl
terraform init
```

### Problema 2: LocalStack No Responde

**Error:**
```
Error: error creating S3 bucket: connection refused
```

**Solution:**
```bash
# Verificar estado de LocalStack
docker-compose ps
docker-compose logs localstack

# Reiniciar LocalStack
docker-compose restart localstack

# Verificar salud
curl http://localhost:4566/_localstack/health
```

### Problema 3: State Locked

**Error:**
```
Error: Error acquiring the state lock
```

**Solution:**
```bash
# Forzar unlock (usar con cuidado)
terraform force-unlock LOCK_ID

# O eliminar el lock manualmente si es local
rm .terraform.tfstate.lock.info
```

### Problema 4: Recursos Huérfanos

**Problema:** Recurso existe en AWS pero no en el state

**Solution:**
```bash
# Importar recurso existente al state
terraform import aws_s3_bucket.my_bucket nombre-del-bucket-existente
```

### Problema 5: Errores de Validation

**Error:**
```
Error: Invalid value for variable
```

**Solution:**
```bash
# Verificar validaciones en variables.tf
terraform validate

# Ver valores actuales de variables
terraform console
> var.bucket_name
```

---

## Recursos Adicionales

### Documentación Oficial

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [HCL Syntax](https://www.terraform.io/docs/language/syntax/configuration.html)
- [Terraform State](https://www.terraform.io/docs/language/state/index.html)

### Tutoriales y Guías

- [HashiCorp Learn - Terraform](https://learn.hashicorp.com/terraform)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [LocalStack Documentation](https://docs.localstack.cloud/)

### Herramientas Útiles

- [terraform-docs](https://terraform-docs.io/) - Generador de documentación
- [tflint](https://github.com/terraform-linters/tflint) - Linter para Terraform
- [checkov](https://www.checkov.io/) - Security scanner para IaC
- [terraformer](https://github.com/GoogleCloudPlatform/terraformer) - Importar infraestructura existente

### Comunidad

- [Terraform Community Forum](https://discuss.hashicorp.com/c/terraform-core)
- [Terraform GitHub](https://github.com/hashicorp/terraform)
- [r/terraform](https://www.reddit.com/r/Terraform/)

---

## Próximos Steps

¡Felicitaciones! Has completed tu primer exercise con Terraform. Ahora sabes:

✅ Instalar y configure Terraform
✅ Crear recursos con HCL
✅ Usar variables y outputs
✅ Gestionar el ciclo de vida de recursos
✅ Entender el state file
✅ Modificar recursos existentes

**Continúa con:** [Exercise 02 - Multi-Resource](../02-multi-resource/README.md)

En el próximo exercise you will learn a:
- Gestionar múltiples recursos
- Manejar dependencias
- Usar count y for_each
- Importar recursos existentes
