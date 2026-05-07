# Validation Tests

This directory contains automated tests to validate the exercises in the SQL Foundations module.

## 📋 Contenido

```text
validation/
├── conftest.py              # Pytest configuration and fixtures
├── helpers.py               # Validation utilities
├── test_exercise_01.py      # Tests para Basic Queries
├── test_exercise_02.py      # Tests para Joins
├── test_exercises_03_06.py  # Tests para Aggregations, Window Functions, CTEs, Optimization
└── README.md                # Este archivo
```text

## 🚀 Setup

### 1. Instalar Dependencias

```bash
# Make sure you are in the module directory
cd modules/module-03-sql-foundations

# Instalar pytest y dependencias
pip install pytest pytest-postgresql psycopg2-binary python-dotenv
```text

### 2. Configurar database

The tests require that the database be running with data:

```bash
# Desde el directorio infrastructure/
cd infrastructure
docker-compose up -d

# Wait for PostgreSQL to be ready
sleep 5

# Verify that the DB has data
psql -h localhost -U dataengineer -d ecommerce -c "SELECT COUNT(*) FROM users;"
```

### 3. Configurar Variables de Entorno (Opcional)

Por defecto, los tests usan:

- Host: `localhost`
- Port: `5432`
- Database: `ecommerce`
- User: `dataengineer`
- Password: `training123`

Para personalizar, crea un archivo `.env`:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ecommerce
POSTGRES_USER=dataengineer
POSTGRES_PASSWORD=training123
```text

## 🧪 Run Tests

### All Tests

```bash
# From the module directory
pytest validation/ -v
```text

### Tests by Exercise

```bash
# Exercise 01: Basic Queries
pytest validation/ -v -m exercise01

# Exercise 02: Joins
pytest validation/ -v -m exercise02

# Exercise 03: Aggregations
pytest validation/ -v -m exercise03

# Exercise 04: Window Functions
pytest validation/ -v -m exercise04

# Exercise 05: CTEs & Subqueries
pytest validation/ -v -m exercise05

# Exercise 06: Optimization
pytest validation/ -v -m exercise06
```text

### Specific Tests

```bash
# Specific test by name
pytest validation/test_exercise_01.py::TestProjection::test_select_specific_columns -v

# Test class
pytest validation/test_exercise_01.py::TestProjection -v

# Full file
pytest validation/test_exercise_01.py -v
```

### Useful Options

```bash
# Show detailed output
pytest validation/ -v -s

# Stop on first failure
pytest validation/ -x

# Run tests in parallel (requires pytest-xdist)
pytest validation/ -n auto

# Exclude slow tests
pytest validation/ -v -m "not slow"

# Generate coverage report (requires pytest-cov)
pytest validation/ --cov=validation --cov-report=html
```text

## 📊 Test Structure

### conftest.py

Shared fixtures:

- `db_connection`: Database connection (scope: session)
- `db_cursor`: Cursor with auto-rollback (scope: function)
- `execute_query`: Helper to execute queries
- `execute_file`: Helper to execute SQL files
- `verify_db_setup`: Verify that the DB is configured

### helpers.py

Utilities:

- `compare_results()`: Compare query results
- `validate_schema()`: Validate expected columns
- `benchmark_query()`: Measure performance
- `assert_no_nulls()`: Verify absence of NULLs
- `assert_unique()`: Verify uniqueness
- `assert_range()`: Verify value ranges
- `get_query_plan()`: Get EXPLAIN plan
- `QueryValidator`: Common validations (pagination, JOIN integrity)

## 📝 Ejemplo de Usage

### Basic Test

```python
@pytest.mark.exercise01
def test_select_users(execute_query):
    """Test selecting users."""
    query = "SELECT * FROM users LIMIT 5"
    results = execute_query(query)

    assert len(results) == 5
    assert 'first_name' in results[0]
```text

### Test con Validaciones

```python
from conftest import assert_query_returns_columns

@pytest.mark.exercise01
def test_projection(execute_query):
    """Test column projection."""
    query = """
    SELECT first_name, last_name, email
    FROM users
    LIMIT 10
    """
    results = execute_query(query)

    assert_query_returns_columns(
        results,
        ['first_name', 'last_name', 'email']
    )
```text

### Test de Performance

```python
from helpers import benchmark_query

@pytest.mark.slow
def test_join_performance(db_cursor):
    """Benchmark JOIN query."""
    query = """
    SELECT o.*, u.first_name
    FROM orders o
    INNER JOIN users u ON o.user_id = u.user_id
    """

    stats = benchmark_query(db_cursor, query, iterations=5)

    # Verificar que promedio es razonable
    assert stats['avg'] < 1.0  # Less than 1 second
```

## ✅ What the Tests Validate

### Exercise 01: Basic Queries

- ✓ Projection of specific columns
- ✓ Usage de alias
- ✓ Filtering with WHERE (=, <, >, !=)
- ✓ Logical operators (AND, OR, NOT)
- ✓ Pattern matching (LIKE, IN, BETWEEN)
- ✓ NULL handling (IS NULL, IS NOT NULL)
- ✓ Ordenamiento (ORDER BY ASC/DESC)
- ✓ Pagination (LIMIT, OFFSET)
- ✓ Queries combinados

### Exercise 02: Joins

- ✓ INNER JOIN correctness
- ✓ LEFT JOIN preservation
- ✓ Finding unmatched records
- ✓ Multiple JOINs (3+ tables)
- ✓ Aggregations with JOINs
- ✓ JOIN cardinality

### Exercise 03: Aggregations

- ✓ COUNT, SUM, AVG, MIN, MAX
- ✓ GROUP BY
- ✓ HAVING clause
- ✓ Aggregations with JOINs

### Exercise 04: Window Functions

- ✓ ROW_NUMBER(), RANK(), DENSE_RANK()
- ✓ PARTITION BY
- ✓ LAG() and LEAD()
- ✓ Running totals
- ✓ Moving averages

### Exercise 05: CTEs & Subqueries

- ✓ Basic CTEs
- ✓ Multiple chained CTEs
- ✓ Subqueries in WHERE
- ✓ Subqueries in SELECT
- ✓ Recursive CTEs

### Exercise 06: Optimization

- ✓ EXPLAIN plan generation
- ✓ Index usage
- ✓ JOIN optimization
- ✓ LIMIT effectiveness
- ✓ EXISTS vs IN comparison

## 🐛 Troubleshooting

### Error: "Missing required tables"

**Causa**: database no inicializada.

**Solution**:

```bash
cd infrastructure
docker-compose down -v
docker-compose up -d
sleep 5
psql -h localhost -U dataengineer -d ecommerce -f init.sql
```text

### Error: "Connection refused"

**Cause**: PostgreSQL is not running.

**Solution**:

```bash
cd infrastructure
docker-compose up -d
docker-compose ps  # Verificar estado
```text

### Error: "Table is empty"

**Causa**: `init.sql`did not run correctly or does not have sample data.

**Solution**:

```bash
psql -h localhost -U dataengineer -d ecommerce -f infrastructure/init.sql
```text

### Tests Fallan Intermitentemente

**Causa**: Rollback no funciona correctamente.

**Solution**: Make sure`db_connection` tiene `autocommit=False`:

```python
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = False
```

### Tests Muy Lentos

**Solution**:

```bash
# Excluir tests marcados como slow
pytest validation/ -m "not slow"

# Or run in parallel
pytest validation/ -n auto
```text

## 📚 resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-postgresql](https://pytest-postgresql.readthedocs.io/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [PostgreSQL Testing Best Practices](https://www.postgresql.org/docs/current/regress.html)

## 🎯 Best Practices

### Escribir Tests

1. **Un concepto por test**: Cada test debe validar una sola cosa
2. **Nombres descriptivos**: `test_select_users_with_active_status` > `test_query1`
3. **Clear assertions**: Use helpers that give useful error messages
4. **Automatic Cleanup**: Use fixtures with rollback
5. **Consistent data**: Do not assume specific data, verify conditions

### Performance

1. **Usar markers**: Marca tests lentos con `@pytest.mark.slow`
2. **Fixtures con scope apropiado**: `session`for connection,`function` para cursor
3. **Evitar sleep**: Usar health checks en lugar de esperar tiempos fijos
4. **Limitar datasets**: Usa LIMIT en tests cuando sea posible

### Mantenibilidad

1. **Reusable Helpers**: Centralize common logic in`helpers.py`
2. **Fixtures compartidas**: Define en `conftest.py`
3. **Documentation**: Clear Docstrings in each test
4. **Organized Markers**: Use markers to group tests logically

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: ecommerce
          POSTGRES_USER: dataengineer
          POSTGRES_PASSWORD: training123
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Initialize database
        run: |
          psql -h localhost -U dataengineer -d ecommerce -f infrastructure/init.sql
        env:
          PGPASSWORD: training123

      - name: Run tests
        run: |
          pytest validation/ -v --junitxml=junit/test-results.xml
        env:
          POSTGRES_HOST: localhost
          POSTGRES_PORT: 5432
          POSTGRES_DB: ecommerce
          POSTGRES_USER: dataengineer
          POSTGRES_PASSWORD: training123

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: junit/test-results.xml
```text

---

**Last Update**: February 2026
**Mantenido por**: Equipo de Training Data Engineering
