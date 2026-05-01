# Query Results Tests

Este directorio está reservado para tests de resultados de queries y análisis.

## 📊 Propósito

Validar que los resultados de queries SQL, transformaciones de datos y análisis producen los resultados esperados.

## 🎯 Tipos de Tests a Agregar

### Expected Output Comparison
```python
def test_aggregation_matches_expected():
    """Comparar agregaciones con resultados esperados"""

def test_transformation_output_correct():
    """Verificar transformación de datos"""
```

### SQL Query Validation
```python
def test_sql_query_returns_correct_results():
    """Verificar resultados de query SQL"""
```

### Data Transformation Tests
```python
def test_csv_to_parquet_conversion():
    """Verificar conversión de formatos"""

def test_data_enrichment():
    """Verificar enriquecimiento de datos"""
```

## 📝 Ejemplo de Test

```python
import pandas as pd
import boto3
import pytest
from io import StringIO

def test_transaction_aggregation():
    """Verificar agregación de transacciones por país"""

    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

    # 1. Descargar datos procesados
    response = s3.get_object(
        Bucket='quickmart-data-lake',
        Key='processed/aggregated_by_country.csv'
    )

    # 2. Leer CSV
    df = pd.read_csv(StringIO(response['Body'].read().decode('utf-8')))

    # 3. Cargar expected results
    expected_df = pd.read_csv('validation/query-results/expected_aggregation.csv')

    # 4. Comparar
    pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)
```

## 📂 Estructura de Archivos Esperados

```
query-results/
├── expected_aggregation.csv
├── expected_enriched_data.json
├── expected_transformed.parquet
└── expected_metrics.json
```

## 🚀 Ejecutar

```bash
pytest validation/query-results/ -v
```

## 💡 Tips

1. **Almacenar expected outputs**: Guardar resultados correctos como fixtures
2. **Tolerar pequeñas diferencias**: Usar `atol` para valores numéricos
3. **Ordenar antes de comparar**: DataFrames pueden estar desordenados
4. **Comparar estructura primero**: Verificar columnas antes de valores

## 📚 Herramientas Recomendadas

- [pandas](https://pandas.pydata.org/) - Manipulación de datos
- [pytest-datadir](https://pypi.org/project/pytest-datadir/) - Test data fixtures
- [deepdiff](https://deepdiff.readthedocs.io/) - Comparación profunda de estructuras
