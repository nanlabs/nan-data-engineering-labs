# Infrastructure Tests

Este directorio está reservado para tests de infraestructura cloud.

## 🏗️ Propósito

Validar que la infraestructura AWS (buckets, roles, políticas, funciones Lambda) está configurada correctamente.

## 🎯 Tipos de Tests a Agregar

### Resource Existence
```python
def test_s3_bucket_exists():
    """Verificar que el bucket S3 existe"""

def test_iam_role_exists():
    """Verificar que el rol IAM existe"""
```

### Configuration Validation
```python
def test_bucket_has_encryption():
    """Verificar que el bucket tiene encriptación habilitada"""

def test_bucket_versioning_enabled():
    """Verificar que el versionado está habilitado"""
```

### Policy Validation
```python
def test_bucket_policy_correct():
    """Verificar que la política del bucket es correcta"""

def test_iam_policy_least_privilege():
    """Verificar principio de privilegio mínimo"""
```

## 📝 Ejemplo de Test

```python
import boto3
import pytest

def test_data_lake_bucket_configuration():
    """Verificar configuración completa del data lake bucket"""
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    bucket_name = 'quickmart-data-lake-dev'

    # 1. Bucket existe
    response = s3.list_buckets()
    bucket_names = [b['Name'] for b in response['Buckets']]
    assert bucket_name in bucket_names

    # 2. Versioning habilitado
    versioning = s3.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get('Status') == 'Enabled'

    # 3. Lifecycle configurado
    lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    assert len(lifecycle['Rules']) > 0
```

## 🚀 Ejecutar

```bash
pytest validation/infrastructure/ -v
```

## 📚 Herramientas Recomendadas

- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - AWS SDK
- [moto](https://github.com/getmoto/moto) - Mock AWS services
- [localstack](https://localstack.cloud/) - Local AWS cloud
