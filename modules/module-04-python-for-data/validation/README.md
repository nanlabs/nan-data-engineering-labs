# Validation and Testing of Module 04

## Description

This directory contains the **integrated validation suite** for the entire Module 04: Python for Data Engineering.

## Estructura

```
validation/
├── README.md                    # Este archivo
├── conftest.py                  # Configuración global de pytest
├── test_integration.py          # Tests de integración entre ejercicios
├── test_data_quality.py         # Validación de calidad de datasets
├── test_module_completeness.py  # Verifica que todo esté completo
└── pytest.ini                   # Configuración de pytest
```

---

## Tests Incluidos

### 1. Integration Tests (`test_integration.py`)

Valida que los ejercicios funcionan juntos:

- pipeline completo: leer CSV → limpiar → transformar → guardar
- Interoperabilidad entre funciones de diferentes ejercicios
- Flujo end-to-end de un proyecto real

### 2. Data Validation (`test_data_quality.py`)

Verifica la calidad de los datasets:

- ✅ Todos los datasets existen
- ✅ Correct size (180K total records)
- ✅ Valid schemes
- ✅ Problemas de calidad intencionales presentes (duplicados, nulls)
- ✅ Relaciones entre datasets

### 3. Module Completeness (`test_module_completeness.py`)

Verify that the module is complete:

- ✅ Todos los ejercicios tienen sus archivos
- ✅ Todos los READMEs existen
- ✅ Estructura de directorios correcta
- ✅ Dependencias instalables

---

## Execution

### Run all validation tests

```bash
# Desde el root del módulo
pytest validation/ -v

# Con coverage
pytest validation/ -v --cov=. --cov-report=html

# Solo tests de integración
pytest validation/test_integration.py -v

# Solo validación de datos
pytest validation/test_data_quality.py -v

# Solo completitud
pytest validation/test_module_completeness.py -v
```

### Run ALL module tests

```bash
# Todos los ejercicios + validación (120+ tests)
pytest exercises/ validation/ -v

# Con reporte detallado
pytest exercises/ validation/ -v --tb=short

# Solo tests que fallan
pytest exercises/ validation/ -v --lf
```

---

## Quality Metrics

### Coverage Esperado

- **Ejercicios individuales**: >90% coverage
- **Integration tests**: >80% coverage
- **Total module**: >85% coverage

### Tests Totales

- Ejercicio 01: 15 tests
- Ejercicio 02: 20 tests
- Ejercicio 03: 18 tests
- Ejercicio 04: 25 tests
- Ejercicio 05: 22 tests
- Ejercicio 06: 20 tests
- **Validation suite**: 15+ tests
- **TOTAL**: ~135+ tests

---

## pytest configuration

Ver `pytest.ini`for configuration options:

- Markers para categorizar tests
- Timeouts para tests lentos
- Coverage settings
- Output format

---

## CI/CD

### GitHub Actions (ejemplo)

```yaml
name: Module 04 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest exercises/ validation/ -v --cov
```

---

## Troubleshooting

### Problema: Tests fallan por imports

**Solution**: Run from the root of the workspace:

```bash
cd /home/nquiroga/Documents/personal/training-cloud-data
export PYTHONPATH=$PYTHONPATH:$PWD
pytest modules/module-04-python-for-data/validation/ -v
```

### Problema: Datasets no encontrados

**Solution**: Verify that you are in the correct directory:

```bash
cd modules/module-04-python-for-data
ls data/raw/  # Debe mostrar los 5 datasets
```

### Problema: Tests lentos

**Solution**: Use pytest-xdist to parallelize:

```bash
pip install pytest-xdist
pytest -n auto  # Usa todos los cores disponibles
```

---

## Next Steps

After validating the module:

1. ✅ Todos los tests pasan → Continuar con Paso 7 (Assets)
2. ❌ Tests fallan → Revisar y corregir ejercicios
3. 📊 Low coverage → Add more tests

---

## resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
