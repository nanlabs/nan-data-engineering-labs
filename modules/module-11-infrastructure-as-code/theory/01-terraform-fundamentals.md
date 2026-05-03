# Terraform Fundamentals: Introducción a Infrastructure as Code

## Tabla de Contenidos
1. [¿Qué es Infrastructure as Code?](#qué-es-infrastructure-as-code)
2. [Beneficios de IaC](#beneficios-de-iac)
3. [Terraform vs Otras Herramientas](#terraform-vs-otras-herramientas)
4. [Arquitectura de Terraform](#arquitectura-de-terraform)
5. [HCL Syntax](#hcl-syntax)
6. [Terraform Workflow](#terraform-workflow)
7. [Providers](#providers)
8. [Resources](#resources)
9. [Data Sources](#data-sources)
10. [Variables](#variables)
11. [Outputs](#outputs)
12. [Terraform State](#terraform-state)
13. [Comandos Básicos](#comandos-básicos)
14. [Primer Proyecto Completo](#primer-proyecto-completo)

---

## ¿Qué es Infrastructure as Code?

**Infrastructure as Code (IaC)** es la práctica de gestionar y aprovisionar infraestructura de TI mediante archivos de definición legibles por máquinas, en lugar de configuration manual de hardware o herramientas de configuration interactivas.

### Conceptos Clave

En el paradigma tradicional, los ingenieros de infraestructura:
- Configuran servidores manualmente a través de consolas web
- Documentan steps en wikis o documentos de texto
- Repiten procesos manualmente para cada entorno
- Enfrentan inconsistencias entre entornos
- Tienen dificultad para rastrear cambios

Con Infrastructure as Code:
- La infraestructura se define en archivos de código versionables
- Los cambios se rastrean mediante control de versiones (Git)
- La infraestructura se puede replicar consistentemente
- Los despliegues son automatizables y repetibles
- Los errores se reducen significativamente

### Principios Fundamentales de IaC

1. **Declarativo vs Imperativo**: IaC puede ser declarativo (defines el estado deseado) o imperativo (defines los steps para llegar allí). Terraform es declarativo.

2. **Idempotencia**: Ejecutar el mismo código múltiples veces produce el mismo resultado.

3. **Versionado**: El código de infraestructura se versiona como cualquier código de aplicación.

4. **Automatización**: Los cambios se aplican automáticamente mediante pipelines de CI/CD.

5. **Inmutabilidad**: En lugar de modificar recursos existentes, se crean nuevos y se destruyen los antiguos.

### ¿Por Qué Usar IaC?

#### Problema: Gestión Manual de Infraestructura

Imagina que necesitas crear un entorno de producción con:
- 3 servidores web
- 1 base de datos
- 1 balanceador de carga
- Grupos de seguridad y networking
- Almacenamiento S3

Hacerlo manualmente implica:
- 45-60 minutes de trabajo por entorno
- Alto riesgo de errores humanos
- Difficulty para replicar en múltiples regiones
- Sin historial de cambios
- Documentación que queda obsoleta rápidamente

#### Solution: Infrastructure as Code

Con IaC:
```hcl
# Un archivo define TODO
resource "aws_instance" "web" {
  count         = 3
  instance_type = "t3.medium"
  ami           = var.ami_id
  # ... más configuration
}
```

- Despliegue en 5 minutes
- Cero errores de configuration
- Replicable en cualquier región
- Historial completo en Git
- La documentación ES el código

---

## Beneficios de IaC

### 1. Reproducibilidad

La capacidad de crear la misma infraestructura múltiples veces de manera consistente.

**Sin IaC:**
```
Ingeniero 1: "Creé el servidor de staging"
Ingeniero 2: "¿Qué configuration usaste?"
Ingeniero 1: "Umm... creo que era t2.medium... ¿o t3.medium?"
```

**Con IaC:**
```hcl
resource "aws_instance" "staging" {
  instance_type = "t3.medium"  # Definido claramente
  ami           = data.aws_ami.ubuntu.id

  tags = {
    Environment = "staging"
    Project     = "data-platform"
  }
}
```

### 2. Versionado

Cada cambio se registra en el control de versiones.

```bash
git log --oneline infrastructure/
a1b2c3d Aumentar instancia a t3.large
e4f5g6h Agregar grupo de seguridad para RDS
i7j8k9l Configuration inicial de VPC
```

Beneficios:
- Auditoría completa de cambios
- Rollback fácil a versiones anteriores
- Code review antes de aplicar cambios
- Blame para identificar quién hizo qué cambio

### 3. Colaboración

Múltiples ingenieros pueden trabajar en la misma infraestructura:

```hcl
# Engineer A trabaja en networking
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Engineer B trabaja en compute
resource "aws_instance" "app" {
  vpc_id = aws_vpc.main.id
  # ...
}
```

- Pull requests para revisar cambios
- CI/CD para validar antes de aplicar
- Comentarios y discusiones en el código

### 4. Consistencia Entre Entornos

```
Desarrollo ≈ Staging ≈ Producción
```

Usando el mismo código con diferentes variables:

```hcl
# variables-dev.tfvars
instance_count = 1
instance_type  = "t3.small"

# variables-prod.tfvars
instance_count = 5
instance_type  = "t3.xlarge"
```

### 5. Velocidad

- **Manual**: 1-2 hours para provisionar un entorno completo
- **IaC**: 5-10 minutes para el mismo entorno

### 6. Reducción de Errores

Los errores humanos en configuration manual son comunes:
- Puerto incorrecto abierto (security risk)
- Región equivocada seleccionada
- Tamaño de instancia incorrecto
- Configuration de red inconsistente

IaC elimina estos errores mediante:
- Validation automática
- Review de código
- Testing automatizado
- Idempotencia

### 7. Documentación Automática

El código ES la documentación:

```hcl
# Esta configuration crea nuestra arquitectura de microservicios
# con 3 tier: web, app, database

# Web tier - Expuesto a internet
resource "aws_instance" "web" {
  # ... configuration
}

# App tier - Solo accesible desde web tier
resource "aws_instance" "app" {
  # ... configuration
}

# Database tier - Solo accesible desde app tier
resource "aws_db_instance" "db" {
  # ... configuration
}
```

---

## Terraform vs Otras Herramientas

| Característica | Terraform | CloudFormation | Pulumi | Ansible |
|----------------|-----------|----------------|---------|---------|
| **Proveedor** | HashiCorp | AWS | Pulumi Corp | Red Hat |
| **Tipo** | Declarativo | Declarativo | Declarativo/Imperativo | Imperativo |
| **Lenguaje** | HCL | JSON/YAML | Python/TypeScript/Go | YAML |
| **Multi-cloud** | ✅ Sí | ❌ Solo AWS | ✅ Sí | ✅ Sí |
| **State Management** | ✅ Sí | ✅ Sí (automático) | ✅ Sí | ❌ No |
| **Comunidad** | Grande | Grande (AWS) | Creciente | Grande |
| **Curva de aprendizaje** | Moderada | Moderada | Baja (si sabes programar) | Baja |
| **Propósito principal** | Provisioning | Provisioning | Provisioning | Configuration Mgmt |

### Terraform: Pros y Contras

#### Ventajas

1. **Multi-cloud**: Soporta AWS, Azure, GCP, y cientos de otros providers
2. **HCL**: Lenguaje declarativo diseñado específicamente para infraestructura
3. **Modules**: Sistema robusto de modules reutilizables
4. **State management**: Control explícito del estado
5. **Plan antes de aplicar**: Ver cambios antes de ejecutarlos
6. **Comunidad**: Gran ecosistema de modules y providers
7. **HashiCorp**: Empresa sólida detrás del producto

#### Desventajas

1. **State management**: Requiere gestión cuidadosa del state file
2. **Curva de aprendizaje**: HCL es otro lenguaje que learn
3. **Errores crípticos**: Mensajes de error pueden ser confusos
4. **No es configuration management**: No reemplaza Ansible/Chef para configuration de SO

### CloudFormation

```yaml
# CloudFormation (YAML)
Resources:
  MyServer:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t3.medium
      ImageId: ami-12345678
```

**Pros:**
- Integración nativa con AWS
- No requiere state management explícito
- Gratis (solo pagas por recursos de AWS)
- Stack policies para protección

**Contras:**
- Solo AWS (vendor lock-in)
- JSON/YAML puede ser verboso
- Menos flexible que Terraform
- Comunidad más pequeña

### Pulumi

```python
# Pulumi (Python)
import pulumi_aws as aws

server = aws.ec2.Instance('my-server',
    instance_type='t3.medium',
    ami='ami-12345678'
)
```

**Pros:**
- Lenguajes de programación reales (Python, TypeScript, Go)
- Lógica compleja más fácil de implementar
- Type safety con TypeScript
- Testing con frameworks estándar

**Contras:**
- Comunidad más pequeña
- Menos modules disponibles
- Puede ser "demasiado" flexible
- Más complejo para equipos no developers

### Ansible

```yaml
# Ansible (YAML)
- name: Create EC2 instance
  ec2:
    instance_type: t3.medium
    image: ami-12345678
    state: present
```

**Pros:**
- Excelente para configuration management
- Sin agentes requeridos
- Sintaxis simple (YAML)
- Gran ecosistema de roles

**Contras:**
- Imperativo (defines steps, no estado)
- No tiene state management
- Menos apropiado para cloud provisioning
- Idempotencia no garantizada

### ¿Cuándo Usar Terraform?

✅ **Usa Terraform cuando:**
- Necesitas multi-cloud o múltiples providers
- Quieres infraestructura declarativa
- Necesitas state management robusto
- Buscas un ecosistema maduro
- Tu equipo prefiere learn HCL

❌ **Considera alternativas cuando:**
- Solo usas AWS y quieres integración nativa → CloudFormation
- Tu equipo son developers y prefieren Python/TypeScript → Pulumi
- Necesitas configuration management de servidores → Ansible
- Tienes infraestructura muy simple → Scripts de CLI

---

## Arquitectura de Terraform

Terraform tiene una arquitectura modular compuesta por tres componentes principales:

```
┌─────────────────────────────────────────────────┐
│                 Terraform CLI                    │
│                 (terraform)                      │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│ Terraform Core │    │   Providers     │
│  (terraform)   │    │ (aws, azure,etc)│
└───────┬────────┘    └────────┬────────┘
        │                      │
        │    ┌─────────────────┘
        │    │
┌───────▼────▼──────┐
│   State Backend   │
│  (local/remote)   │
└───────────────────┘
```

### 1. Terraform Core

**Funciones:**
- Lee configuration (archivos .tf)
- Construye el grafo de recursos y dependencias
- Determina el orden de operaciones
- Ejecuta el plan de cambios
- Actualiza el state

**Workflow interno:**
```
Load Config → Build Graph → Generate Plan → Execute Plan → Update State
```

### 2. Providers

Los providers son plugins que permiten a Terraform interactuar con APIs de servicios cloud y otros servicios.

**Providers Populares:**
- **aws**: Amazon Web Services
- **azurerm**: Microsoft Azure
- **google**: Google Cloud Platform
- **kubernetes**: Kubernetes
- **github**: GitHub
- **datadog**: Datadog
- **postgresql**: PostgreSQL

**Arquitectura de Provider:**
```
Terraform Core ←→ Provider Plugin ←→ Service API
                  (aws provider)      (AWS API)
```

Cada provider:
- Es un binario separado
- Se descarga automáticamente en `terraform init`
- Traduce HCL a llamadas API
- Maneja autenticación
- Implementa recursos y data sources específicos

### 3. State

El **state** es el mecanismo que Terraform usa para mapear recursos del mundo real a tu configuration.

```json
{
  "version": 4,
  "terraform_version": "1.5.0",
  "resources": [
    {
      "type": "aws_instance",
      "name": "example",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "attributes": {
            "id": "i-1234567890abcdef0",
            "instance_type": "t3.medium",
            "ami": "ami-12345678"
          }
        }
      ]
    }
  ]
}
```

**¿Por qué es necesario el State?**

1. **Mapeo**: Conecta recursos lógicos (en código) con recursos físicos (en AWS)
2. **Metadata**: Almacena información sobre dependencias
3. **Performance**: Cachea valores para no consultar API constantemente
4. **Colaboración**: Permite que múltiples usuarios trabajen juntos

---

## HCL Syntax

**HashiCorp Configuration Language (HCL)** es el lenguaje usado por Terraform. Es declarativo, legible y está diseñado específicamente para definir infraestructura.

### Estructura Básica

```hcl
# Esto es un comentario

// También es un comentario

/*
  Comentario
  multilínea
*/

# Bloque básico
<BLOCK_TYPE> "<BLOCK_LABEL>" "<BLOCK_LABEL>" {
  # Argumentos
  <IDENTIFIER> = <EXPRESSION>

  # Bloque anidado
  <NESTED_BLOCK> {
    <IDENTIFIER> = <EXPRESSION>
  }
}
```

### Bloques

Los bloques son contenedores de configuration. Ejemplo:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  tags = {
    Name = "WebServer"
  }
}
```

Componentes:
- **Tipo de bloque**: `resource`
- **Etiquetas**: `"aws_instance"` y `"web"`
- **Cuerpo**: Todo entre `{}`
- **Argumentos**: `ami = "..."`

### Tipos de Bloques Principales

```hcl
# 1. Terraform block - Configuration de Terraform mismo
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# 2. Provider block - Configuration de providers
provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project = "DataPlatform"
    }
  }
}

# 3. Resource block - Define un recurso
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

# 4. Data source block - Lee información existente
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
}

# 5. Variable block - Define input variables
variable "environment" {
  type    = string
  default = "dev"
}

# 6. Output block - Define outputs
output "bucket_name" {
  value = aws_s3_bucket.data.bucket
}

# 7. Locals block - Define valores locales
locals {
  common_tags = {
    Project = "DataPlatform"
    ManagedBy = "Terraform"
  }
}

# 8. Module block - Usa un module
module "vpc" {
  source = "./modules/vpc"

  cidr_block = "10.0.0.0/16"
}
```

### Argumentos

Los argumentos asignan valores a nombres:

```hcl
# Argumentos simples
instance_type = "t3.medium"
count         = 5
enable_monitoring = true

# Argumentos con expresiones
ami = var.ami_id
name = "${var.project}-server"
tags = merge(local.common_tags, var.additional_tags)
```

### Expresiones

#### Tipos de Datos

```hcl
# String
name = "my-server"
description = <<-EOT
  Este es un string
  multilínea
EOT

# Number
count = 3
port  = 443

# Boolean
enable_logging = true
public_access  = false

# List
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
ports = [80, 443, 8080]

# Map
tags = {
  Environment = "production"
  Team        = "data"
}

# Object (map con tipos específicos)
config = {
  name    = "app"
  version = "1.0"
  enabled = true
}
```

#### Referencias

```hcl
# Referencia a resource
aws_instance.web.id
aws_s3_bucket.data.arn

# Referencia a variable
var.environment
var.instance_type

# Referencia a local
local.common_tags
local.vpc_id

# Referencia a data source
data.aws_ami.ubuntu.id

# Referencia a module output
module.vpc.vpc_id
```

#### Interpolación

```hcl
# String interpolation
name = "${var.project}-${var.environment}-server"

# Para solo una variable, no es necesario ${}
ami = var.ami_id  # Preferido
ami = "${var.ami_id}"  # También funciona pero no necesario
```

#### Operadores

```hcl
# Aritméticos
count = var.base_count + 2
size  = var.base_size * 2

# Comparación
enabled = var.count > 0
large_instance = var.instance_type == "t3.large"

# Lógicos
create_resource = var.enabled && var.environment == "prod"
skip_resource = !var.enabled || var.count == 0

# Condicional (ternario)
instance_type = var.environment == "prod" ? "t3.large" : "t3.small"
count = var.enabled ? 1 : 0
```

#### Funciones

Terraform tiene muchas funciones built-in:

```hcl
# String functions
upper("hello")  # "HELLO"
lower("WORLD")  # "world"
join("-", ["a", "b", "c"])  # "a-b-c"
split("-", "a-b-c")  # ["a", "b", "c"]

# Collection functions
length(["a", "b", "c"])  # 3
concat([1, 2], [3, 4])  # [1, 2, 3, 4]
merge({a = 1}, {b = 2})  # {a = 1, b = 2}

# Numeric functions
min(1, 2, 3)  # 1
max(1, 2, 3)  # 3

# Filesystem functions
file("${path.module}/config.json")
templatefile("${path.module}/template.tpl", {name = "value"})

# Date functions
timestamp()  # "2024-03-07T12:34:56Z"

# Encoding functions
base64encode("hello")
jsonencode({key = "value"})
```

### For Expressions

```hcl
# List comprehension
[for s in var.subnets : upper(s)]

# Map comprehension
{for k, v in var.tags : k => upper(v)}

# Filtering
[for s in var.servers : s.name if s.enabled]

# Nested
[for subnet in var.subnets : [
  for zone in var.zones : "${subnet}-${zone}"
]]
```

---

## Terraform Workflow

El workflow de Terraform sigue un ciclo predecible:

```
┌─────────┐    ┌────────┐    ┌────────┐    ┌──────────┐
│  Write  │───▶│  Init  │───▶│  Plan  │───▶│  Apply   │
│  Code   │    │        │    │        │    │          │
└─────────┘    └────────┘    └────────┘    └──────────┘
                                                 │
                                                 ▼
                                           ┌──────────┐
                                           │ Destroy  │
                                           │ (opt.)   │
                                           └──────────┘
```

### 1. Write: Escribir Configuration

Crea archivos `.tf` con tu configuration:

```hcl
# main.tf
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
  region = var.region
}

resource "aws_s3_bucket" "data" {
  bucket = "${var.project}-data-${var.environment}"
}
```

### 2. Init: Inicializar

```bash
terraform init
```

**¿Qué hace `init`?**
- Descarga providers especificados
- Inicializa backend para state
- Descarga modules referenciados
- Crea `.terraform/` directory

**Output típico:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.25.0...
- Installed hashicorp/aws v5.25.0

Terraform has been successfully initialized!
```

**Cuándo ejecutar init:**
- Primera vez en un directorio nuevo
- Después de agregar nuevos providers
- Después de cambiar configuration de backend
- Al cambiar versiones de providers

### 3. Plan: Planificar Cambios

```bash
terraform plan
```

**¿Qué hace `plan`?**
- Lee configuration actual
- Lee state actual
- Consulta estado real de recursos (refresh)
- Calcula diferencias (diff)
- Muestra qué cambios se aplicarán

**Output típico:**
```
Terraform will perform the following actions:

  # aws_s3_bucket.data will be created
  + resource "aws_s3_bucket" "data" {
      + bucket                      = "myproject-data-dev"
      + id                          = (known after apply)
      + arn                         = (known after apply)
      + bucket_domain_name          = (known after apply)
      + hosted_zone_id              = (known after apply)
      + region                      = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

**Símbolos en plan:**
- `+` : Recurso será creado
- `-` : Recurso será destruido
- `~` : Recurso será modificado in-place
- `-/+` : Recurso será destruido y recreado
- `<=` : Recurso será leído durante apply

**Guardar plan:**
```bash
terraform plan -out=tfplan
```

Esto guarda el plan para aplicarlo después exactamente como se vio.

### 4. Apply: Aplicar Cambios

```bash
terraform apply
```

**¿Qué hace `apply`?**
- Ejecuta un `plan` (a menos que uses plan guardado)
- Pide confirmación
- Ejecuta cambios en el orden correcto (basado en dependencias)
- Actualiza state file

**Output típico:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

aws_s3_bucket.data: Creating...
aws_s3_bucket.data: Creation complete after 2s [id=myproject-data-dev]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

**Aplicar sin confirmación:**
```bash
terraform apply -auto-approve
```

**Aplicar plan guardado:**
```bash
terraform apply tfplan
```

### 5. Destroy: Destruir Infraestructura

```bash
terraform destroy
```

Elimina todos los recursos gestionados por Terraform.

**¿Cuándo usar?:**
- Entornos temporales (testing, demos)
- Limpiar recursos no utilizados
- Reconstruir desde cero

⚠️ **PELIGRO**: Este comando es irreversible.

### Workflow Completo Ejemplo

```bash
# 1. Clonar repositorio
git clone https://github.com/company/infrastructure.git
cd infrastructure/environments/dev

# 2. Inicializar
terraform init

# 3. Validar sintaxis
terraform validate

# 4. Formatear código
terraform fmt

# 5. Ver qué cambios se harían
terraform plan

# 6. Aplicar cambios
terraform apply

# 7. Ver outputs
terraform output

# 8. Verificar estado
terraform show

# 9. (Opcional) Ver lista de recursos
terraform state list

# 10. (Cuando ya no se necesita) Destruir
terraform destroy
```

---

## Providers

Los **providers** son plugins que permiten a Terraform interactuar con APIs de proveedores cloud, SaaS, y otros servicios.

### Configuration de Provider

#### Bloque Provider Básico

```hcl
provider "aws" {
  region = "us-east-1"
}
```

#### Configuration Completa

```hcl
provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  # Default tags para todos los recursos
  default_tags {
    tags = {
      Environment = "production"
      ManagedBy   = "Terraform"
      Project     = "DataPlatform"
    }
  }

  # Configuration de retry
  max_retries = 3

  # Ignorar tags específicos
  ignore_tags {
    keys = ["LastModified", "AutoScaling"]
  }
}
```

### Provider Requirements

Define qué providers necesitas y sus versiones:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Cualquier versión 5.x
    }

    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
  }
}
```

**Version constraints:**
- `= 1.0.0` : Exactamente la versión 1.0.0
- `!= 1.0.0` : Cualquiera excepto 1.0.0
- `> 1.0.0` : Mayor que 1.0.0
- `>= 1.0.0` : Mayor o igual que 1.0.0
- `< 2.0.0` : Menor que 2.0.0
- `<= 2.0.0` : Menor o igual que 2.0.0
- `~> 1.0` : Cualquier versión 1.x (pero no 2.0)
- `~> 1.0.0` : Cualquier versión 1.0.x (pero no 1.1)

### Múltiples Providers (Alias)

Puedes usar el mismo provider múltiples veces con diferentes configuraciones:

```hcl
# Provider por defecto (us-east-1)
provider "aws" {
  region = "us-east-1"
}

# Provider adicional para otra región
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

# Usar provider específico en un recurso
resource "aws_s3_bucket" "east" {
  bucket = "my-bucket-east"
  # Usa provider por defecto (us-east-1)
}

resource "aws_s3_bucket" "west" {
  provider = aws.west
  bucket   = "my-bucket-west"
}
```

### AWS Provider: Configuration Común

```hcl
provider "aws" {
  region  = var.aws_region
  profile = "mycompany"  # AWS CLI profile

  # Assume role
  assume_role {
    role_arn     = "arn:aws:iam::123456789012:role/TerraformRole"
    session_name = "terraform-session"
  }

  # Shared credentials file
  shared_credentials_files = ["~/.aws/credentials"]

  # Default tags
  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Project   = var.project_name
    }
  }
}
```

### Autenticación AWS

Terraform puede autenticarse con AWS de varias formas (en orden de precedencia):

1. **Parámetros en Provider Block**
```hcl
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
```
❌ **NO RECOMENDADO**: Credenciales en código

2. **Variables de Entorno**
```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_REGION="us-east-1"
```
✅ **RECOMENDADO** para CI/CD

3. **Shared Credentials File**
```bash
# ~/.aws/credentials
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[production]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE2
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2
```
✅ **RECOMENDADO** para desarrollo local

4. **IAM Role (EC2 Instance Profile)**
En instancias EC2 con IAM role asignado
✅ **RECOMENDADO** para ejecutar desde EC2

5. **ECS Task Role**
En ECS tasks con task role asignado
✅ **RECOMENDADO** para ejecutar desde ECS

### Providers Comunes

```hcl
# AWS
provider "aws" {
  region = "us-east-1"
}

# Azure
provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

# Google Cloud
provider "google" {
  project = var.gcp_project
  region  = "us-central1"
}

# Kubernetes
provider "kubernetes" {
  config_path = "~/.kube/config"
}

# GitHub
provider "github" {
  token = var.github_token
  owner = "myorganization"
}

# Random (útil para generar nombres únicos)
provider "random" {}

# Null (útil para provisioners)
provider "null" {}
```

---

## Resources

Los **resources** son el componente más importante de Terraform. Cada bloque de resource describe uno o más objetos de infraestructura.

### Sintaxis de Resource

```hcl
resource "<PROVIDER>_<TYPE>" "<NAME>" {
  <ARGUMENT> = <VALUE>

  <NESTED_BLOCK> {
    <ARGUMENT> = <VALUE>
  }
}
```

### Ejemplos de Resources

#### AWS S3 Bucket

```hcl
resource "aws_s3_bucket" "data_lake" {
  bucket = "my-company-data-lake"

  tags = {
    Name        = "Data Lake"
    Environment = "production"
  }
}

# Versioning separado (AWS provider 4.x+)
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}
```

#### AWS EC2 Instance

```hcl
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  # Network configuration
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  associate_public_ip_address = true

  # Storage
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  # User data script
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from Terraform</h1>" > /var/www/html/index.html
              EOF

  # Tags
  tags = {
    Name        = "WebServer"
    Environment = "production"
    Role        = "webserver"
  }

  # Lifecycle
  lifecycle {
    create_before_destroy = true
  }
}
```

#### AWS RDS Database

```hcl
resource "aws_db_instance" "postgres" {
  identifier = "myapp-database"

  # Engine
  engine         = "postgres"
  engine_version = "14.7"

  # Size and performance
  instance_class    = "db.t3.medium"
  allocated_storage = 100
  storage_type      = "gp3"
  storage_encrypted = true

  # Database
  db_name  = "myappdb"
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false

  # Backup
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn

  # Deletion protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "myapp-database-final-snapshot"

  tags = {
    Name        = "Application Database"
    Environment = "production"
  }
}
```

### Referencias Entre Resources

Los resources pueden referenciar atributos de otros resources:

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "main-vpc"
  }
}

# Subnet referencia VPC
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id  # ← Referencia
  cidr_block = "10.0.1.0/24"

  tags = {
    Name = "public-subnet"
  }
}

# Security Group referencia VPC
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id  # ← Referencia

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Instance referencia Subnet y Security Group
resource "aws_instance" "web" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id  # ← Referencia
  vpc_security_group_ids = [aws_security_group.web.id]  # ← Referencia
}
```

Terraform automáticamente crea el **grafo de dependencias** y crea recursos en el orden correcto.

### Resource Behavior

#### Create

Cuando ejecutas `terraform apply` por primera vez, Terraform crea todos los recursos.

#### Update (In-Place)

Algunos cambios pueden aplicarse sin recrear el recurso:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t3.medium"

  tags = {
    Name = "WebServer v1"  # Cambiar esto solo actualiza tags
  }
}
```

En el plan verás `~` (modificación):
```
~ resource "aws_instance" "web" {
    ~ tags = {
        ~ "Name" = "WebServer v1" -> "WebServer v2"
      }
  }
```

#### Replace (Destroy then Create)

Algunos cambios requieren recrear el recurso:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-12345"  # Cambiar AMI requiere recrear
  instance_type = "t3.medium"
}
```

En el plan verás `-/+` (reemplazo):
```
-/+ resource "aws_instance" "web" {
    ~ ami           = "ami-12345" -> "ami-67890"
      instance_type = "t3.medium"
  }
```

#### Destroy

Cuando eliminas un resource del código o ejecutas `terraform destroy`:

```
- resource "aws_instance" "web" {
    - ami           = "ami-12345"
    - instance_type = "t3.medium"
  }
```

---

## Data Sources

Los **data sources** permiten leer información desde fuentes externas y usarla en tu configuration.

### Diferencia: Resource vs Data Source

```hcl
# RESOURCE: Crea/gestiona un recurso
resource "aws_s3_bucket" "new_bucket" {
  bucket = "my-new-bucket"
}

# DATA SOURCE: Lee un recurso existente
data "aws_s3_bucket" "existing_bucket" {
  bucket = "already-exists-bucket"
}
```

### Sintaxis

```hcl
data "<PROVIDER>_<TYPE>" "<NAME>" {
  <FILTER_ARGUMENT> = <VALUE>
}

# Referencia: data.<TYPE>.<NAME>.<ATTRIBUTE>
```

### Ejemplos Comunes

#### AWS AMI (Amazon Machine Image)

```hcl
# Buscar la AMI más reciente de Ubuntu
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical (Ubuntu)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Usar en una instancia
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
}

# Output información de la AMI
output "ami_info" {
  value = {
    id           = data.aws_ami.ubuntu.id
    name         = data.aws_ami.ubuntu.name
    created_date = data.aws_ami.ubuntu.creation_date
  }
}
```

#### AWS Availability Zones

```hcl
# Obtener todas las AZs disponibles
data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# Usar para crear subnets en múltiples AZs
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "private-subnet-${count.index + 1}"
  }
}
```

#### AWS VPC Existente

```hcl
# Buscar VPC por tag
data "aws_vpc" "selected" {
  tags = {
    Name = "production-vpc"
  }
}

# Buscar subnets de esa VPC
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  tags = {
    Tier = "private"
  }
}

# Usar en recursos
resource "aws_instance" "app" {
  ami           = "ami-12345"
  instance_type = "t3.medium"
  subnet_id     = tolist(data.aws_subnets.private.ids)[0]
}
```

#### AWS Caller Identity

```hcl
# Información sobre la cuenta AWS actual
data "aws_caller_identity" "current" {}

output "account_info" {
  value = {
    account_id = data.aws_caller_identity.current.account_id
    arn        = data.aws_caller_identity.current.arn
    user_id    = data.aws_caller_identity.current.user_id
  }
}

# Usar en policies
resource "aws_s3_bucket" "logs" {
  bucket = "logs-${data.aws_caller_identity.current.account_id}"
}
```

#### AWS IAM Policy Document

```hcl
# Construir policy document
data "aws_iam_policy_document" "s3_read" {
  statement {
    sid    = "AllowS3Read"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]

    resources = [
      "arn:aws:s3:::my-bucket",
      "arn:aws:s3:::my-bucket/*"
    ]
  }
}

# Usar en IAM policy
resource "aws_iam_policy" "s3_read" {
  name   = "s3-read-policy"
  policy = data.aws_iam_policy_document.s3_read.json
}
```

---

## Variables

Las **variables** (input variables) permiten parametrizar tu configuration de Terraform.

### Definición de Variables

```hcl
# variables.tf

# Variable simple
variable "region" {
  type    = string
  default = "us-east-1"
}

# Variable con descripción
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

# Variable con validation
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"

  validation {
    condition     = contains(["t3.small", "t3.medium", "t3.large"], var.instance_type)
    error_message = "Instance type must be t3.small, t3.medium, or t3.large."
  }
}

# Variable sensible (no se muestra en logs)
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Variable tipo número
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 2
}

# Variable tipo boolean
variable "enable_monitoring" {
  description = "Enable CloudWatch detailed monitoring"
  type        = bool
  default     = true
}

# Variable tipo list
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# Variable tipo map
variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Project   = "DataPlatform"
    ManagedBy = "Terraform"
  }
}

# Variable tipo object
variable "database_config" {
  description = "Database configuration"
  type = object({
    engine         = string
    engine_version = string
    instance_class = string
    allocated_storage = number
  })
  default = {
    engine            = "postgres"
    engine_version    = "14.7"
    instance_class    = "db.t3.medium"
    allocated_storage = 100
  }
}
```

### Tipos de Variables

| Tipo | Description | Ejemplo |
|------|-------------|---------|
| `string` | Cadena de texto | `"hello"` |
| `number` | Número (int o float) | `42` o `3.14` |
| `bool` | Booleano | `true` o `false` |
| `list(<TYPE>)` | Lista de elementos | `["a", "b", "c"]` |
| `set(<TYPE>)` | Set de elementos únicos | `["unique", "values"]` |
| `map(<TYPE>)` | Mapa clave-valor | `{key = "value"}` |
| `object({...})` | Objeto con estructura definida | `{name = "x", count = 1}` |
| `tuple([...])` | Tupla (lista con tipos mixtos) | `["string", 123, true]` |
| `any` | Cualquier tipo | N/A |

### Uso de Variables

```hcl
# En recursos
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = var.tags
}

# En interpolación de strings
resource "aws_s3_bucket" "data" {
  bucket = "${var.project}-${var.environment}-data"
}

# En condicionales
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.environment == "prod" ? "t3.large" : "t3.small"
}

# En count
resource "aws_instance" "web" {
  count = var.instance_count

  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name = "web-${count.index + 1}"
  }
}
```

### Formas de Asignar Valores a Variables

#### 1. Valor por defecto en definición

```hcl
variable "region" {
  type    = string
  default = "us-east-1"
}
```

#### 2. Archivo terraform.tfvars

```hcl
# terraform.tfvars (se carga automáticamente)
region       = "us-west-2"
environment  = "production"
instance_count = 5
```

#### 3. Archivo .tfvars personalizado

```bash
# dev.tfvars
environment    = "dev"
instance_count = 1
instance_type  = "t3.small"
```

```bash
terraform apply -var-file="dev.tfvars"
```

#### 4. Línea de comandos

```bash
terraform apply -var="region=us-west-2" -var="environment=prod"
```

#### 5. Variables de entorno

```bash
export TF_VAR_region="us-west-2"
export TF_VAR_environment="production"
terraform apply
```

#### Orden de Precedencia (mayor a menor)

1. `-var` o `-var-file` en línea de comandos
2. `*.auto.tfvars` (alfabéticamente)
3. `terraform.tfvars`
4. Variables de entorno `TF_VAR_*`
5. Valor por defecto en variable definition

### Variables Locales (Locals)

Las **locals** son valores calculados que se usan internamente:

```hcl
locals {
  # Nombre del proyecto combinado con environment
  name_prefix = "${var.project}-${var.environment}"

  # Tags comunes
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedDate = timestamp()
  }

  # Lista de subnets privadas
  private_subnets = [
    for i in range(3) : "10.0.${i + 10}.0/24"
  ]

  # Configuration condicional
  instance_type = var.environment == "prod" ? "t3.large" : "t3.small"

  # Merge de configuraciones
  all_tags = merge(
    local.common_tags,
    var.additional_tags
  )
}

# Usar locals
resource "aws_s3_bucket" "data" {
  bucket = "${local.name_prefix}-data"
  tags   = local.common_tags
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = local.instance_type
  tags          = local.all_tags
}
```

**Diferencia: Variables vs Locals**

| Aspecto | Variables | Locals |
|---------|-----------|--------|
| Definición | `variable` block | `locals` block |
| Propósito | Input del usuario | Cálculos internos |
| Valor | Asignado externamente | Calculado en código |
| Referencia | `var.<NAME>` | `local.<NAME>` |

---

## Outputs

Los **outputs** exponen valores de tu configuration de Terraform.

### Definición de Outputs

```hcl
# outputs.tf

# Output simple
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.data.bucket
}

# Output de ID de recurso
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

# Output de múltiples valores
output "database_info" {
  description = "Database connection information"
  value = {
    endpoint = aws_db_instance.postgres.endpoint
    port     = aws_db_instance.postgres.port
    database = aws_db_instance.postgres.db_name
  }
}

# Output sensible (no se muestra en console)
output "db_password" {
  description = "Database password"
  value       = aws_db_instance.postgres.password
  sensitive   = true
}

# Output condicional
output "public_ip" {
  description = "Public IP of instance (if applicable)"
  value       = var.assign_public_ip ? aws_instance.web.public_ip : null
}

# Output de lista (con count)
output "instance_ids" {
  description = "IDs of all web instances"
  value       = aws_instance.web[*].id
}

# Output calculated
output "vpc_cidr_blocks" {
  description = "CIDR blocks of all subnets"
  value = [
    for subnet in aws_subnet.private : subnet.cidr_block
  ]
}
```

### Uso de Outputs

#### Ver Outputs Después de Apply

```bash
$ terraform apply
...
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:

bucket_name = "myproject-prod-data"
database_info = {
  "database" = "myappdb"
  "endpoint" = "myapp-db.abc123.us-east-1.rds.amazonaws.com:5432"
  "port" = 5432
}
instance_id = "i-1234567890abcdef0"
instance_ids = [
  "i-1234567890abcdef0",
  "i-abcdef1234567890",
  "i-567890abcdef1234",
]
```

#### Ver Outputs Específico

```bash
# Ver todos los outputs
terraform output

# Ver un output específico
terraform output bucket_name

# Output en formato JSON
terraform output -json

# Output raw (sin comillas para strings)
terraform output -raw bucket_name
```

#### Usar Outputs en Scripts

```bash
#!/bin/bash

# Obtener bucket name de Terraform
BUCKET=$(terraform output -raw bucket_name)

# Subir archivo a S3
aws s3 cp data.csv s3://$BUCKET/
```

#### Outputs Entre Modules

```hcl
# modules/networking/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

# root main.tf
module "networking" {
  source = "./modules/networking"
}

module "compute" {
  source = "./modules/compute"

  # Usar outputs del module networking
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
}

# root outputs.tf
output "vpc_id" {
  value = module.networking.vpc_id
}
```

---

## Terraform State

El **state** es la forma en que Terraform rastrea qué recursos ha creado y su estado actual.

### ¿Qué es el State?

El state es un archivo JSON que contiene:
- Mapeo entre recursos en código y recursos reales
- Metadata sobre recursos y dependencias
- Cach de valores de atributos de recursos

**Archivo state básico:**
```json
{
  "version": 4,
  "terraform_version": "1.5.0",
  "serial": 42,
  "lineage": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
  "outputs": {
    "bucket_name": {
      "value": "myproject-data",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_s3_bucket",
      "name": "data",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 0,
          "attributes": {
            "id": "myproject-data",
            "bucket": "myproject-data",
            "arn": "arn:aws:s3:::myproject-data",
            "region": "us-east-1"
          }
        }
      ]
    }
  ]
}
```

### ¿Por Qué es Importante el State?

1. **Mapeo**: Conecta código con infraestructura real
2. **Metadata**: Almacena dependencias entre recursos
3. **Performance**: Cachea valores para no consultarlos siempre
4. **Sincronización**: Permite colaboración en equipo

### State Local vs Remoto

#### State Local (Por Defecto)

```
.
├── main.tf
├── variables.tf
├── terraform.tfstate          ← State file
└── terraform.tfstate.backup   ← Backup del state anterior
```

**Problemas:**
- ❌ No se puede compartir fácilmente
- ❌ No tiene locking (múltiples personas pueden aplicar cambios simultáneamente)
- ❌ Sensible (contiene secrets)
- ❌ Fácil de perder

#### State Remoto (Recomendado)

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**Beneficios:**
- ✅ Compartido entre equipo
- ✅ Locking automático
- ✅ Encriptación
- ✅ Versionado
- ✅ Backup automático

### Comandos de State

#### terraform state list

Lista todos los recursos en el state:

```bash
$ terraform state list
aws_vpc.main
aws_subnet.private[0]
aws_subnet.private[1]
aws_subnet.public[0]
aws_instance.web[0]
aws_instance.web[1]
aws_s3_bucket.data
```

#### terraform state show

Muestra detalles de un recurso específico:

```bash
$ terraform state show aws_instance.web[0]
# aws_instance.web[0]:
resource "aws_instance" "web" {
    id                      = "i-1234567890abcdef0"
    ami                     = "ami-0c55b159cbfafe1f0"
    instance_type           = "t3.medium"
    availability_zone       = "us-east-1a"
    private_ip              = "10.0.1.10"
    public_ip               = "54.123.45.67"
    ...
}
```

#### terraform refresh

Actualiza state con el estado real actual sin modificar infraestructura:

```bash
terraform refresh
```

⚠️ Deprecated: Usa `terraform apply -refresh-only` en su lugar.

### Best Practices para State

1. **Siempre usa remote state en equipo**
2. **Nunca edites state file manualmente**
3. **Usa state locking**
4. **Encripta state (contiene secrets)**
5. **Versiona state files**
6. **Haz backup regular de state**
7. **No commitees state a Git**

**`.gitignore` recomendado:**
```gitignore
# Terraform
.terraform/
*.tfstate
*.tfstate.*
.terraform.lock.hcl
```

---

## Comandos Básicos

### terraform init

Inicializa directorio de trabajo de Terraform.

```bash
terraform init

# Opciones útiles
terraform init -upgrade           # Actualiza providers
terraform init -reconfigure       # Reconfigura backend
terraform init -migrate-state     # Migra state a nuevo backend
```

### terraform validate

Valida sintaxis de configuration.

```bash
terraform validate

# Output exitoso
Success! The configuration is valid.

# Output con error
Error: Unsupported argument

  on main.tf line 5, in resource "aws_instance" "web":
   5:   invalid_argument = "value"
```

### terraform fmt

Formatea código a estilo estándar.

```bash
terraform fmt

# Formatear recursivamente
terraform fmt -recursive

# Check (no modifica, solo verifica)
terraform fmt -check
```

### terraform plan

Muestra cambios que se aplicarían.

```bash
terraform plan

# Guardar plan
terraform plan -out=tfplan

# Plan para destruir
terraform plan -destroy

# Plan con variables
terraform plan -var="environment=prod" -var-file="prod.tfvars"

# Plan parcial (solo ciertos resources)
terraform plan -target=aws_instance.web
```

### terraform apply

Aplica cambios.

```bash
terraform apply

# Auto-approve (sin confirmación)
terraform apply -auto-approve

# Aplicar plan guardado
terraform apply tfplan

# Aplicar con variables
terraform apply -var="environment=prod"

# Aplicar parcialmente
terraform apply -target=aws_instance.web
```

### terraform destroy

Destruye todos los recursos gestionados.

```bash
terraform destroy

# Auto-approve
terraform destroy -auto-approve

# Destruir recursos específicos
terraform destroy -target=aws_instance.web
```

### terraform output

Muestra valores de outputs.

```bash
# Todos los outputs
terraform output

# Output específico
terraform output bucket_name

# JSON format
terraform output -json

# Raw (sin quotes)
terraform output -raw bucket_name
```

### terraform show

Muestra estado actual o plan guardado.

```bash
# Mostrar state actual
terraform show

# Mostrar plan guardado
terraform show tfplan

# JSON format
terraform show -json
```

### terraform console

Consola interactiva para evaluar expresiones.

```bash
$ terraform console
> var.environment
"production"
> aws_instance.web.id
"i-1234567890abcdef0"
> upper("hello")
"HELLO"
> [for i in range(3) : "subnet-${i}"]
[
  "subnet-0",
  "subnet-1",
  "subnet-2",
]
```

### terraform graph

Genera grafo de dependencias.

```bash
terraform graph | dot -Tpng > graph.png
```

---

## Primer Proyecto Completo

Vamos a crear un proyecto completo step a step: un entorno básico de aplicación web en AWS.

### Arquitectura

```
Internet
   │
   ▼
[Load Balancer]
   │
   ├─────────┬─────────┐
   ▼         ▼         ▼
[Web 1]  [Web 2]  [Web 3]
   │         │         │
   └─────────┴─────────┘
            │
            ▼
       [Database]
            │
            ▼
       [S3 Bucket]
```

### Estructura de Archivos

```
project/
├── main.tf           # Recursos principales
├── variables.tf      # Definiciones de variables
├── outputs.tf        # Outputs
├── terraform.tfvars  # Valores de variables
└── README.md        # Documentación
```

### 1. variables.tf

```hcl
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "myapp"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}
```

### 2. main.tf

```hcl
# Configure Terraform
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Locals
locals {
  name_prefix = "${var.project}-${var.environment}"

  availability_zones = [
    "${var.region}a",
    "${var.region}b"
  ]

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Data Sources
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = local.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Tier = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = local.availability_zones[count.index]

  tags = {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Tier = "private"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

# Associate Public Subnets with Route Table
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for Web Servers
resource "aws_security_group" "web" {
  name        = "${local.name_prefix}-web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id

  # HTTP from anywhere
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS from anywhere
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH (for management - consider restricting)
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-web-sg"
  }
}

# Security Group for Database
resource "aws_security_group" "database" {
  name        = "${local.name_prefix}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL from web security group only
  ingress {
    description     = "PostgreSQL from web servers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-db-sg"
  }
}

# EC2 Instances
resource "aws_instance" "web" {
  count                  = var.instance_count
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[count.index % 2].id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from ${local.name_prefix} - Server ${count.index + 1}</h1>" > /var/www/html/index.html
              EOF

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${local.name_prefix}-web-${count.index + 1}"
  }
}

# S3 Bucket for Data
resource "aws_s3_bucket" "data" {
  bucket = "${local.name_prefix}-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${local.name_prefix}-data"
  }
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier        = "${local.name_prefix}-db"
  engine            = "postgres"
  engine_version    = "14.7"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_encrypted = true

  db_name  = "appdb"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period = 7
  skip_final_snapshot     = true

  tags = {
    Name = "${local.name_prefix}-db"
  }
}

# Data source for account ID
data "aws_caller_identity" "current" {}
```

### 3. outputs.tf

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "web_instance_ids" {
  description = "IDs of web server instances"
  value       = aws_instance.web[*].id
}

output "web_public_ips" {
  description = "Public IPs of web servers"
  value       = aws_instance.web[*].public_ip
}

output "s3_bucket_name" {
  description = "Name of S3 bucket"
  value       = aws_s3_bucket.data.id
}

output "database_endpoint" {
  description = "Database connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}
```

### 4. terraform.tfvars

```hcl
environment  = "dev"
project      = "myapp"
region       = "us-east-1"
instance_count = 2
instance_type  = "t3.micro"
db_username    = "admin"
db_password    = "ChangeMe123!"  # In real scenario, use secret management
```

### 5. Desplegar el Proyecto

```bash
# 1. Inicializar
terraform init

# 2. Validar
terraform validate

# 3. Formatear
terraform fmt

# 4. Ver plan
terraform plan

# 5. Aplicar
terraform apply

# Output
...
Apply complete! Resources: 20 added, 0 changed, 0 destroyed.

Outputs:

database_endpoint = "myapp-dev-db.abc123.us-east-1.rds.amazonaws.com:5432"
database_name = "appdb"
s3_bucket_name = "myapp-dev-data-123456789012"
web_instance_ids = [
  "i-1234567890abcdef0",
  "i-0abcdef1234567890",
]
web_public_ips = [
  "54.123.45.67",
  "54.234.56.78",
]
vpc_id = "vpc-abc123def456"

# 6. Probar
curl http://54.123.45.67
```

### 6. Limpiar Recursos

```bash
terraform destroy

# Confirmar con: yes
```

---

## Best Practices

### 1. Organización de Código

✅ **DO:**
- Separar código en múltiples archivos (.tf)
- Usar nombres descriptivos
- Agrupar recursos relacionados
- Usar modules para código reutilizable

❌ **DON'T:**
- Poner todo en un solo archivo gigante
- Usar nombres genéricos (like "resource1")

### 2. Variables y Outputs

✅ **DO:**
- Definir variables con descriptions
- Usar validation cuando sea apropiado
- Marcar variables sensibles como `sensitive = true`
- Proveer defaults razonables cuando sea posible

❌ **DON'T:**
- Hardcodear valores en recursos
- Exponer secrets en outputs no-sensitive

### 3. State Management

✅ **DO:**
- Usar remote state en equipo
- Habilitar state locking
- Encriptar state files
- Versionar state files

❌ **DON'T:**
- Commitear state a Git
- Editar state manualmente
- Compartir state via archivos locales

### 4. Seguridad

✅ **DO:**
- Usar IAM roles en lugar de access keys
- Encriptar datos sensibles
- Seguir principio de least privilege
- Usar recursos encriptados por defecto

❌ **DON'T:**
- Commitear credenciales al código
- Dar permisos excesivos
- Dejar recursos públicos sin intención

### 5. Testing y Validation

✅ **DO:**
- Ejecutar `terraform validate` regularmente
- Ejecutar `terraform fmt` antes de commits
- Revisar plans cuidadosamente antes de apply
- Probar cambios en entorno no-productivo primero

## Common Pitfalls

### 1. No Revisar el Plan

❌ **Problema**: Ejecutar `terraform apply` sin revisar el plan

✅ **Solution**: Siempre ejecuta `terraform plan` primero

### 2. State Corruption

❌ **Problema**: Múltiples personas ejecutan terraform simultáneamente

✅ **Solution**: Usa state locking con backend remoto

### 3. Resources Drift

❌ **Problema**: Cambios manuales en console causan discrepancies

✅ **Solution**: Siempre hacer cambios via Terraform, usa `terraform refresh`

### 4. Dependency Issues

❌ **Problema**: Terraform no detecta dependencias implícitas

✅ **Solution**: Usa `depends_on` para dependencias explícitas

---

## Recursos y Referencias

### Documentación Oficial
- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [HCL Configuration Language](https://www.terraform.io/docs/language/index.html)

### Tutoriales y Guías
- [HashiCorp Learn](https://learn.hashicorp.com/terraform)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

### Herramientas
- [Terraform Registry](https://registry.terraform.io/) - Providers y modules
- [tflint](https://github.com/terraform-linters/tflint) - Linter para Terraform
- [terraform-docs](https://terraform-docs.io/) - Generador de documentación

### Comunidad
- [Terraform Community Forum](https://discuss.hashicorp.com/c/terraform-core)
- [Terraform GitHub](https://github.com/hashicorp/terraform)

---

## Conclusión

En este module has aprendido los fundamentos de Terraform e Infrastructure as Code:

✅ **Qué es IaC** y sus beneficios
✅ **Arquitectura de Terraform** (Core, Providers, State)
✅ **HCL Syntax** y estructura de bloques
✅ **Terraform Workflow** (init, plan, apply, destroy)
✅ **Resources y Data Sources**
✅ **Variables y Outputs**
✅ **State Management**
✅ **Primer proyecto completo**

En el siguiente module (`02-terraform-advanced.md`), profundizaremos en temas avanzados como modules, funciones complejas, remote state, y workflows de equipo.

**¡Continúa practicando y experimentando con Terraform!**
