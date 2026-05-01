# Validation and Testing

Suite completa de tests automatizados para validar ejercicios.

## 📂 Estructura

```
validation/
├── conftest.py              # Fixtures de Spark
├── test_01_delta_basics.py
├── test_02_medallion.py
├── test_03_time_travel.py
├── test_04_schema_evolution.py
├── test_05_optimization.py
├── test_06_iceberg_comparison.py
└── requirements.txt
```

## 🚀 Uso

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todos los tests
pytest -v

# Ejecutar test específico
pytest -v validation/test_01_delta_basics.py

# Generar reporte de cobertura
pytest --cov=../exercises --cov-report=html
```

## ✅ Cobertura

- **Ejercicio 01**: 8 tests (create, append, overwrite, query)
- **Ejercicio 02**: 6 tests (pipeline medallion completo)
- **Ejercicio 03**: 4 tests (time travel, rollback)
- **Ejercicio 04**: 3 tests (schema evolution)
- **Ejercicio 05**: 3 tests (optimization)
- **Ejercicio 06**: 2 tests (comparison)

**Total**: 26 tests automatizados
