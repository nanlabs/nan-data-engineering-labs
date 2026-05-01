# Validation Tests - Module 01

Este directorio contiene tests automatizados para validar el progreso y la correctitud de los ejercicios.

## 📋 Tests Disponibles

### Tests Principales

| Test | Ejercicio | Descripción | Tests |
|------|-----------|-------------|-------|
| `test_exercise_01.py` | S3 Basics | Verifica operaciones básicas de S3 | 10 |
| `test_exercise_02.py` | IAM Policies | Verifica configuración de IAM | 8 |

### Tests por Categoría

#### 1. Infrastructure Tests
Tests que verifican la configuración de infraestructura (buckets, roles, policies).

**Ubicación:** `validation/infrastructure/` (pendiente)

**Ejemplos:**
- Verificar que los buckets existen
- Verificar políticas de bucket
- Verificar roles y permisos

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
- Validar formato de CSV
- Validar JSON Schema
- Verificar integridad de datos

#### 4. Query Results Tests
Tests que verifican resultados de queries SQL o análisis.

**Ubicación:** `validation/query-results/` (pendiente)

**Ejemplos:**
- Comparar resultados con expected output
- Verificar agregaciones
- Validar transformaciones

## 🚀 Uso

### Ejecutar Todos los Tests

```bash
# Desde la raíz del módulo
pytest validation/ -v

# Con coverage
pytest validation/ --cov=. --cov-report=html
```

### Ejecutar Tests Específicos

```bash
# Solo Exercise 01
pytest validation/test_exercise_01.py -v

# Solo Exercise 02
pytest validation/test_exercise_02.py -v

# Test específico
pytest validation/test_exercise_01.py::test_bucket_exists -v
```

### Ejecutar con Filtros

```bash
# Solo tests que fallan
pytest validation/ -v --lf

# Solo tests marcados
pytest validation/ -v -m "s3"

# Con output detallado
pytest validation/ -vv -s
```

## 📦 Configuración

### conftest.py

Configuración compartida para todos los tests:
- Fixture `wait_for_localstack`: Espera a que LocalStack esté listo
- Configuración de boto3 para LocalStack
- Setup/teardown automático

### requirements.txt

Dependencias necesarias:
```
pytest>=7.4.0
boto3>=1.26.0
botocore>=1.29.0
```

Instalar:
```bash
pip install -r validation/requirements.txt
```

## ✅ Criterios de Aceptación

Para que un ejercicio se considere completo:

### Exercise 01: S3 Basics
- [x] Bucket existe
- [x] Estructura de carpetas correcta (logs/, transactions/, uploads/)
- [x] Archivos subidos correctamente
- [x] Metadata configurada
- [x] Operaciones de copia funcionan
- [x] 10/10 tests pasando

### Exercise 02: IAM Policies
- [x] 3 grupos creados
- [x] 3 políticas creadas
- [x] 5 usuarios creados
- [x] Usuarios en grupos correctos
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
- [ ] Validación funciona
- [ ] Tests pendientes

### Exercise 05: CloudFormation
- [ ] Stack creado exitosamente
- [ ] Recursos desplegados
- [ ] Outputs correctos
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
```

### Tests Fallan: "Timeout waiting for LocalStack"

Aumentar tiempo de espera en `conftest.py`:
```python
max_attempts = 60  # Cambiar de 30 a 60
```

### Tests Pasan Localmente pero Fallan en CI

Verificar:
1. LocalStack está instalado en CI
2. Puertos están disponibles
3. Timeout es suficiente

## 📊 Coverage Report

Generar reporte de cobertura:

```bash
pytest validation/ --cov=exercises --cov-report=html
open htmlcov/index.html
```

**Meta de cobertura:** 80%+

## 🎯 Agregar Nuevos Tests

### Template para Nuevo Test

```python
import boto3
import pytest

# Configurar cliente
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

def test_mi_nuevo_test(wait_for_localstack):
    """Descripción del test"""

    # Arrange
    bucket_name = 'test-bucket'

    # Act
    response = s3.create_bucket(Bucket=bucket_name)

    # Assert
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
```

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
