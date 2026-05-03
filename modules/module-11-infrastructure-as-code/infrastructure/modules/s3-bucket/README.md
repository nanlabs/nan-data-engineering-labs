# Module: S3 Bucket

Module reutilizable para crear un bucket S3 con seguridad por defecto.

## Features

- ✅ Versionado configurable
- ✅ Cifrado obligatorio (AES256 o KMS)
- ✅ Block public access por defecto
- ✅ Lifecycle rules opcionales
- ✅ Access logging

## Usage

```hcl
module "my_bucket" {
  source = "./modules/s3-bucket"

  bucket_name       = "my-app-data"
  environment       = "production"
  enable_versioning = true
  enable_logging    = true

  lifecycle_rules = [{
    id      = "archive-old-data"
    enabled = true

    transition = [{
      days          = 90
      storage_class = "GLACIER"
    }]

    expiration = {
      days = 365
    }
  }]

  tags = {
    Project    = "DataPlatform"
    CostCenter = "Engineering"
  }
}

output "bucket_arn" {
  value = module.my_bucket.arn
}
```

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| bucket_name | string | - | yes | Nombre del bucket |
| environment | string | - | yes | Entorno (dev/staging/prod) |
| enable_versioning | bool | true | no | Habilitar versionado |
| enable_logging | bool | false | no | Habilitar access logs |
| kms_key_id | string | null | no | KMS key ARN para cifrado |
| lifecycle_rules | list | [] | no | Lifecycle rules |
| tags | map(string) | {} | no | Tags adicionales |

## Outputs

| Name | Description |
|------|-------------|
| id | Nombre del bucket |
| arn | ARN del bucket |
| domain_name | Domain name del bucket |
