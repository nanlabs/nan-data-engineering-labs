# Data Quality Tests

Este directorio está reservado para tests de calidad de datos.

## 📊 Propósito

Validate la calidad, integridad y formato de los datos procesados por los exercises.

## 🎯 Tipos de Tests a Agregar

### Schema Validation

```python
def test_transaction_schema():
    """Validate que los datos cumplen con el schema JSON"""
    # Verify campos requeridos
    # Validate tipos de datos
    # Verify rangos de valores
```text

### Data Integrity

```python
def test_no_duplicates():
    """Verify que no hay transacciones duplicadas"""

def test_referential_integrity():
    """Verify relaciones entre datasets"""
```text

### Format Validation

```python
def test_csv_format():
    """Verify formato runcto de CSV"""

def test_json_format():
    """Verify JSON válido"""
```text

## 📝 Ejemplo de Test

```python
import json
import boto3
import pytest
from jsonschema import validate

def test_transaction_data_quality():
    """Verify calidad de datos de transacciones"""
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

    # Descargar datos
    response = s3.get_object(
        Bucket='quickmart-data-lake',
        Key='validated/transactions.csv'
    )
    data = response['Body'].read().decode('utf-8')

    # Validate
    assert len(data) > 0
    assert 'transaction_id' in data
    assert 'amount' in data
```

## 🚀 Run

```bash
pytest validation/data-quality/ -v
```text

## 📚 Herramientas Recomendadas

- [jsonschema](https://python-jsonschema.readthedocs.io/) - Validation de schemas
- [great_expectations](https://greatexpectations.io/) - Framework de calidad de datos
- [pandera](https://pandera.readthedocs.io/) - Validation de DataFrames
