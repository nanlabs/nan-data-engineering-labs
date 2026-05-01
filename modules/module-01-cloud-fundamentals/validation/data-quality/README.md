# Data Quality Tests

Este directorio está reservado para tests de calidad de datos.

## 📊 Propósito

Validar la calidad, integridad y formato de los datos procesados por los ejercicios.

## 🎯 Tipos de Tests a Agregar

### Schema Validation
```python
def test_transaction_schema():
    """Validar que los datos cumplen con el schema JSON"""
    # Verificar campos requeridos
    # Validar tipos de datos
    # Verificar rangos de valores
```

### Data Integrity
```python
def test_no_duplicates():
    """Verificar que no hay transacciones duplicadas"""

def test_referential_integrity():
    """Verificar relaciones entre datasets"""
```

### Format Validation
```python
def test_csv_format():
    """Verificar formato correcto de CSV"""

def test_json_format():
    """Verificar JSON válido"""
```

## 📝 Ejemplo de Test

```python
import json
import boto3
import pytest
from jsonschema import validate

def test_transaction_data_quality():
    """Verificar calidad de datos de transacciones"""
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

    # Descargar datos
    response = s3.get_object(
        Bucket='quickmart-data-lake',
        Key='validated/transactions.csv'
    )
    data = response['Body'].read().decode('utf-8')

    # Validar
    assert len(data) > 0
    assert 'transaction_id' in data
    assert 'amount' in data
```

## 🚀 Ejecutar

```bash
pytest validation/data-quality/ -v
```

## 📚 Herramientas Recomendadas

- [jsonschema](https://python-jsonschema.readthedocs.io/) - Validación de schemas
- [great_expectations](https://greatexpectations.io/) - Framework de calidad de datos
- [pandera](https://pandera.readthedocs.io/) - Validación de DataFrames
