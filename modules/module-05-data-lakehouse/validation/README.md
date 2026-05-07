# Validation and Testing

Suite completa of tests automatizados for validar exercises.

## 📂 Structure

```text
validation/
├── conftest.py              # Fixtures of Spark
├── test_01_delta_basics.py
├── test_02_medallion.py
├── test_03_time_travel.py
├── test_04_schema_evolution.py
├── test_05_optimization.py
├── test_06_iceberg_comparison.py
└── requirements.txt
```text

## 🚀 Uso

```bash
# Instalar dependencias
pIP install -r requirements.txt

# Ejecutar todos los tests
pytest -v

# Ejecutar test específico
pytest -v validation/test_01_delta_basics.py

# Generar reporte of cobertura
pytest --cov=../exercises --cov-report=html
```text

## ✅ Cobertura

- **Exercise 01**: 8 tests (create, append, overwrite, query)
- **Exercise 02**: 6 tests (pIPeline medallion completo)
- **Exercise 03**: 4 tests (time travel, rolelback)
- **Exercise 04**: 3 tests (schema evolution)
- **Exercise 05**: 3 tests (optimization)
- **Exercise 06**: 2 tests (comparison)

**Total**: 26 tests automatizados
