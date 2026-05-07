# Validation Tests - Module 01

Este directorio contiene tests automatizados para validate el progress y la runctness de los exercises.

## 📋 Tests Disponibles

### Tests Principales

| Test | Exercise | Descripción | Tests |
|------|-----------|-------------|-------|
| `test_exercise_01.py` | S3 Basics | Verifica operaciones básicas de S3 | 10 |
| `test_exercise_02.py` | IAM Policies | Verifica configuration de IAM | 8 |

### Tests por Categoría

#### 1. Infrastructure Tests

Tests que verifican la configuration de infraestructura (buckets, roles, policies).

**Ubicación:** `validation/infrastructure/` (pendiente)

**Ejemplos:**

- Verify que los buckets existen
- Verify políticas de bucket
- Verify roles y permisos

#### 2. Integration Tests

Tests que verifican la integración entre servicios (S3 → Lambda → SQS).

**Ubicación:** `validation/integration/` (pendiente)

**Ejemplos:**

- S3 event trigger → Lambda execution
- Lambda → SQS message delivery
- CloudWatch Logs generation

#### 3. Data Quality Tests

Tests que verifican la calidad de los datos procesados.

**Ubicación:** `validation/data-quality/` (pendiente)

**Ejemplos:**

- Validate formato de CSV
- Validate JSON Schema
- Verify integridad de datos

#### 4. Query Results Tests

Tests que verifican resultados de queries SQL o análisis.

**Ubicación:** `validation/query-results/` (pendiente)

**Ejemplos:**

- Comparar resultados con expected output
- Verify agregaciones
- Validate transformaciones

## 🚀 Uso

### Run Todos los Tests

```bash
# Desde la raíz del módulo
pytest validation/ -v

# Con coverage
pytest validation/ --cov=. --cov-report=html
```text

### Run Tests Específicos

```bash
# Solo Exercise 01
pytest validation/test_exercise_01.py -v

# Solo Exercise 02
pytest validation/test_exercise_02.py -v

# Test específico
pytest validation/test_exercise_01.py::test_bucket_exists -v
```text

### Run con Filtros

```bash
# Solo tests que fallan
pytest validation/ -v --lf

# Solo tests marcados
pytest validation/ -v -m "s3"

# Con output detallado
pytest validation/ -vv -s
```text

## 📦 Configuration

### conftest.py

Configuration compartida para todos los tests:

- Fixture `wait_for_localstack`: Espera a que LocalStack esté listo
- Configuration de boto3 para LocalStack
- Setup/teardown automático

### requirements.txt

Dependencias necessarys:

```
pytest>=7.4.0
boto3>=1.26.0
botocore>=1.29.0
```text

Instalar:

```bash
pip install -r validation/requirements.txt
```text

## ✅ Criterios de Aceptación

Para que un exercise se considere completo:

### Exercise 01: S3 Basics

- [x] Bucket existe
- [x] Estructura de carpetas runcta (logs/, transactions/, uploads/)
- [x] Archivos subidos runctamente
- [x] Metadata configurada
- [x] Operaciones de copia funcionan
- [x] 10/10 tests pasando

### Exercise 02: IAM Policies

- [x] 3 grupos creados
- [x] 3 políticas creadas
- [x] 5 usuarios creados
- [x] Usuarios en grupos runctos
- [x] Políticas adjuntas
- [x] Rol Lambda creado
- [x] 8/8 tests pasando

### Exercise 03: S3 Advanced

- [ ] Lifecycle policies configuradas
- [ ] Replication configurada
- [ ] Event notifications funcionando
- [ ] Tests pendientes

### Exercise 04: Lambda Functions

- [ ] Lambda desplegada
- [ ] S3 trigger configurado
- [ ] Validation funciona
- [ ] Tests pendientes

### Exercise 05: CloudFormation

- [ ] Stack creado exitosamente
- [ ] Recursos desplegados
- [ ] Outputs runctos
- [ ] Tests pendientes

### Exercise 06: Cost Optimization

- [ ] Análisis ejecutado
- [ ] Recomendaciones generadas
- [ ] Budgets configurados
- [ ] Tests pendientes

## 🐛 Troubleshooting

### Tests Fallan: "Connection refused"

LocalStack no está corriendo:

```bash
cd infrastructure/
docker-compose up -d
sleep 30
pytest ../validation/
```text

### Tests Fallan: "Timeout waiting for LocalStack"

Aumentar tiempo de espera en `conftest.py`:

```python
max_attempts = 60  # Cambiar de 30 a 60
```

### Tests Pasan Localmente pero Fallan en CI

Verify:

1. LocalStack está instalado en CI
2. Puertos están disponibles
3. Timeout es suficiente

## 📊 Coverage Report

Generar reporte de cobertura:

```bash
pytest validation/ --cov=exercises --cov-report=html
open htmlcov/index.html
```text

**Meta de cobertura:** 80%+

## 🎯 Agregar Nuevos Tests

### Template para Nuevo Test

```python
import boto3
import pytest

# Configure cliente
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

def test_mi_nuevo_test(wait_for_localstack):
    """Descripción del test"""

    # Arrange
    bucket_name = 'test-bucket'

    # Act
    response = s3.create_bucket(Bucket=bucket_name)

    # Assert
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
```text

### Mejores Prácticas

1. **Nombres descriptivos**: `test_bucket_has_versioning_enabled`
2. **Un concepto por test**: No mezclar múltiples verificaciones
3. **AAA Pattern**: Arrange, Act, Assert
4. **Cleanup**: Usar fixtures para limpieza
5. **Docstrings**: Explicar qué verifica el test

## 📚 Referencias

- [pytest Documentation](https://docs.pytest.org/)
- [boto3 Testing](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/testing.html)
- [LocalStack Testing](https://docs.localstack.cloud/user-guide/ci/)
