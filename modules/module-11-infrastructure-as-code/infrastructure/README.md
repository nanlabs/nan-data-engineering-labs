# Infrastructure Templates

Este directorio contiene configuraciones de referencia de Terraform para diferentes scenarios.

## Estructura

```text
infrastructure/
├── terraform/
│   ├── examples/       # Ejemplos completos
│   └── backend/        # Configuration de backend
│
├── modules/            # Modules reutilizables
│   ├── s3-bucket/
│   ├── data-lake/
│   └── iam-role/
│
└── environments/       # Configuraciones por entorno
    ├── dev/
    ├── staging/
    └── prod/
```text

## Uso

### 1. Backend Setup

Primero, crea el backend para almacenar el state:

```bash
cd terraform/backend
terraform init
terraform apply
```text

### 2. Usar Modules

```hcl
module "my_bucket" {
  source = "../../modules/s3-bucket"

  bucket_name = "my-data-bucket"
  environment = "dev"
  enable_versioning = true
}
```

### 3. Desplegar por Entorno

```bash
cd environments/dev
terraform init -backend-config=backend.hcl
terraform apply
```text

## Modules Disponibles

| Module | Description | Uso |
|--------|-------------|-----|
| s3-bucket | Bucket S3 con configuraciones de seguridad | Storage general |
| data-lake | Data lake bronze/silver/gold | Proyectos de datos |
| iam-role | Roles IAM con policies | Permisos |

## Ejemplos

Ver `terraform/examples/` para ejemplos completos funcionando.
