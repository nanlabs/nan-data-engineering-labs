# Validation and Testing of Module 04

## Description

This directory contains the **integrated validation suite** for the entire Module 04: Python for Data Engineering.

## Structure

```text
validation/
├── README.md                    # Este file
├── conftest.py                  # Configuration global de pytest
├── test_integration.py          # Integration tests across exercises
├── test_data_quality.py         # Validation de calidad de datasets
├── test_module_completeness.py  # Verifies everything is complete
└── pytest.ini                   # Configuration de pytest
```text

---

## Tests Incluidos

### 1. Integration Tests (`test_integration.py`)

Validate that exercises work together:

- pipeline completo: leer CSV → limpiar → transformar → guardar
- Interoperability between functions from different exercises
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

- ✅ All exercises have their files
- ✅ Todos los READMEs existen
- ✅ Structure de directorios correcta
- ✅ Dependencias instalables

---

## Execution

### Run all validation tests

```bash
# From the module root
pytest validation/ -v

# Con coverage
pytest validation/ -v --cov=. --cov-report=html

# Integration tests only
pytest validation/test_integration.py -v

# Data validation only
pytest validation/test_data_quality.py -v

# Solo completitud
pytest validation/test_module_completeness.py -v
```text

### Run ALL module tests

```bash
# All exercises + validation (120+ tests)
pytest exercises/ validation/ -v

# Con reporte detallado
pytest exercises/ validation/ -v --tb=short

# Solo tests que fallan
pytest exercises/ validation/ -v --lf
```

---

## Quality Metrics

### Coverage Esperado

- **Exercises individuales**: >90% coverage
- **Integration tests**: >80% coverage
- **Total module**: >85% coverage

### Total Tests

- Exercise 01: 15 tests
- Exercise 02: 20 tests
- Exercise 03: 18 tests
- Exercise 04: 25 tests
- Exercise 05: 22 tests
- Exercise 06: 20 tests
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
```text

---

## Troubleshooting

### Problema: Tests fallan por imports

**Solution**: Run from the root of the workspace:

```bash
cd training-cloud-data
export PYTHONPATH=$PYTHONPATH:$PWD
pytest modules/module-04-python-for-data/validation/ -v
```text

### Problema: Datasets no encontrados

**Solution**: Verify that you are in the correct directory:

```bash
cd modules/module-04-python-for-data
ls data/raw/  # Debe mostrar los 5 datasets
```text

### Problema: Tests lentos

**Solution**: Use pytest-xdist to parallelize:

```bash
pip install pytest-xdist
pytest -n auto  # Usa todos los cores disponibles
```

---

## Next Steps

After validating the module:

1. ✅ Todos los tests pasan → Continuar con Step 7 (Assets)
2. ❌ Tests fallan → Review and fix exercises
3. 📊 Low coverage → Add more tests

---

## resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
