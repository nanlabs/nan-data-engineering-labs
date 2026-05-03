# Exercise 03: Great Expectations

⏱️ **Estimated duration:** 2-3 hours
⭐⭐⭐ **Difficulty:** Intermediate

## 🎯 Goals

- Configurar Great Expectations en un proyecto
- Crear Expectation Suites
- Ejecutar validaciones con Checkpoints
- Generate automatic Data Docs
- Integrate GE into data pipelines
- Crear custom expectations

## 📚 Conceptos Clave

- **Expectations**: Assertions about data
- **Expectation Suites**: Colecciones de expectations
- **Checkpoints**: Validation points in pipeline
- **Data Docs**: Auto-generated documentation
- **Data Context**: GE Configuration

## 🚀 Setup

```bash
# Instalar Great Expectations
pip install great_expectations

# Inicializar GE context
cd exercises/03-great-expectations
great_expectations init

# Esto crea:
# great_expectations/
# ├── great_expectations.yml        # Config principal
# ├── expectations/                 # Suites
# ├── checkpoints/                  # Checkpoint configs
# └── uncommitted/
#     ├── data_docs/                # HTML reports
#     └── validations/              # Validation results
```

## 📝 Exercises

### Part 1: Setup and Configuration

**Task 1.1: Crear Datasource**

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest

# Obtener context
context = gx.get_context()

# Crear datasource para Pandas
datasource = context.sources.add_pandas("ecommerce_datasource")

print("✅ Datasource creado")
```

**Task 1.2: Create Expectation Suite - Programmatically**

```python
# Crear suite vacía
suite_name = "transactions_suite"
context.add_expectation_suite(suite_name)

# Crear validator
batch_request = RuntimeBatchRequest(
    datasource_name="ecommerce_datasource",
    data_asset_name="transactions",
    runtime_parameters={"batch_data": transactions_df},
    batch_identifiers={"default_identifier_name": "default_identifier"},
)

validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name=suite_name
)

# Agregar expectations
# Table-level
validator.expect_table_row_count_to_be_between(min_value=10000, max_value=100000)
validator.expect_table_column_count_to_equal(value=10)

# Column NULLs
validator.expect_column_values_to_not_be_null(column="transaction_id")
validator.expect_column_values_to_not_be_null(column="customer_id")
validator.expect_column_values_to_not_be_null(column="amount")

# Uniqueness
validator.expect_column_values_to_be_unique(column="transaction_id")

# Ranges
validator.expect_column_values_to_be_between(
    column="amount",
    min_value=0,
    max_value=1000000
)

validator.expect_column_values_to_be_between(
    column="quantity",
    min_value=1,
    max_value=1000
)

# Valid values (domain)
validator.expect_column_values_to_be_in_set(
    column="status",
    value_set=["completed", "pending", "failed", "refunded"]
)

validator.expect_column_values_to_be_in_set(
    column="payment_method",
    value_set=["credit_card", "debit_card", "paypal", "bank_transfer"]
)

# Guardar suite
validator.save_expectation_suite(discard_failed_expectations=False)
print(f"✅ Expectation suite '{suite_name}' creada con {len(validator.get_expectation_suite().expectations)} expectations")
```

**Task 1.3: Crear Expectation Suite - Customers**

```python
# TODO: Crear suite para customers con:
# - Row count entre 5000 y 20000
# - customer_id único y no null
# - email no null y formato válido (regex)
# - account_status en ['active', 'inactive', 'suspended', 'pending']
# - date_of_birth en el pasado

suite_name = "customers_suite"
# ... implement
```

**Task 1.4: Auto-Profiling**

```python
from great_expectations.profile.user_configurable_profiler import (
    UserConfigurableProfiler
)

# Auto-generar expectations basándose en los datos
profiler = UserConfigurableProfiler(
    profile_dataset=validator,
    excluded_expectations=[
        "expect_column_values_to_be_in_set"  # Puede generar sets muy grandes
    ],
)

suite = profiler.build_suite()
validator.save_expectation_suite()

print(f"✅ Suite auto-generada con {len(suite.expectations)} expectations")
```

---

### Parte 2: Ejecutar Validaciones

**Task 2.1: Validar con Validator**

```python
# Validar directamente
results = validator.validate()

if results["success"]:
    print("✅ Todas las validaciones pasaron")
else:
    print("❌ Algunas validaciones fallaron")

    # Ver failures
    for result in results["results"]:
        if not result["success"]:
            expectation_type = result["expectation_config"]["expectation_type"]
            kwargs = result["expectation_config"]["kwargs"]
            print(f"  - {expectation_type}: {kwargs}")
```

**Task 2.2: Crear Checkpoint**

```python
# Configuration de checkpoint
checkpoint_config = {
    "name": "transactions_checkpoint",
    "config_version": 1.0,
    "class_name": "SimpleCheckpoint",
    "validations": [
        {
            "batch_request": {
                "datasource_name": "ecommerce_datasource",
                "data_asset_name": "transactions",
            },
            "expectation_suite_name": "transactions_suite",
        }
    ],
}

# Crear checkpoint
context.add_checkpoint(**checkpoint_config)
print("✅ Checkpoint creado")
```

**Task 2.3: Ejecutar Checkpoint**

```python
# Ejecutar checkpoint
results = context.run_checkpoint(
    checkpoint_name="transactions_checkpoint",
    batch_request={
        "runtime_parameters": {"batch_data": transactions_df},
        "batch_identifiers": {"default_identifier_name": "default_identifier"},
    },
)

# Analizar resultados
if results["success"]:
    print("✅ Checkpoint passed")
else:
    print("❌ Checkpoint failed")

    # Detalles de failures
    for run_result in results.run_results.values():
        validation_result = run_result["validation_result"]

        for result in validation_result["results"]:
            if not result["success"]:
                print(f"\nFailed Expectation:")
                print(f"  Type: {result['expectation_config']['expectation_type']}")
                print(f"  Column: {result['expectation_config']['kwargs'].get('column', 'N/A')}")
                print(f"  Observed: {result['result'].get('observed_value', 'N/A')}")
```

---

### Parte 3: Data Docs

**Task 3.1: Generar Data Docs**

```python
# Construir data docs
context.build_data_docs()

# Abrir en navegador
context.open_data_docs()
```

**Task 3.2: Personalizar Data Docs**

Editar `great_expectations/great_expectations.yml`:

```yaml
data_docs_sites:
  local_site:
    class_name: SiteBuilder
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/data_docs/local_site/
    site_index_builder:
      class_name: DefaultSiteIndexBuilder
      show_cta_footer: true
      site_name: "E-commerce Data Quality"
```

---

### Parte 4: Custom Expectations

**Task 4.1: Crear Custom Expectation**

```python
from greatexpectations.expectations.expectation import ColumnMapExpectation
from great_expectations.execution_engine import PandasExecutionEngine
import re

class ExpectColumnValuesToBeValidEmail(ColumnMapExpectation):
    """Expect column values to be valid email addresses."""

    map_metric = "column_values.match_email_pattern"
    success_keys = ("mostly",)

    @classmethod
    def _pandas(cls, column, **kwargs):
        """Pandas implementation."""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return column.str.match(email_regex, na=False)

    library_metadata = {
        "maturity": "production",
        "tags": ["validation", "email"],
        "contributors": ["@yourname"],
    }

# Registrar expectation
validator.expect_column_values_to_be_valid_email(
    column="email",
    mostly=0.95  # 95% deben ser válidos
)
```

**Task 4.2: Custom Expectation - Phone**

```python
# TODO: Crear ExpectColumnValuesToBeValidPhone
# - Validar que tenga al menos 10 dígitos numéricos
# - Permitir formatos: (555) 123-4567, 555-123-4567, 5551234567
pass
```

---

### Part 5: pipeline integration

**Task 5.1: pipeline con Quality Gates**

```python
def data_pipeline_with_quality_gates():
    """Pipeline con validaciones GE integradas."""

    print("Step 1: Extract")
    raw_data = extract_from_source()

    print("Step 2: Validate Raw Data")
    raw_validation = context.run_checkpoint(
        checkpoint_name="raw_data_checkpoint",
        batch_request={
            "runtime_parameters": {"batch_data": raw_data},
            "batch_identifiers": {"default_identifier_name": "raw"},
        },
    )

    if not raw_validation["success"]:
        raise ValueError("Raw data validation failed!")

    print("Step 3: Transform")
    transformed_data = transform(raw_data)

    print("Step 4: Validate Transformed Data")
    transformed_validation = context.run_checkpoint(
        checkpoint_name="transformed_data_checkpoint",
        batch_request={
            "runtime_parameters": {"batch_data": transformed_data},
            "batch_identifiers": {"default_identifier_name": "transformed"},
        },
    )

    if not transformed_validation["success"]:
        raise ValueError("Transformed data validation failed!")

    print("Step 5: Load")
    load_to_warehouse(transformed_data)

    print("✅ Pipeline completed successfully")

# Ejecutar pipeline
try:
    data_pipeline_with_quality_gates()
except ValueError as e:
    print(f"❌ Pipeline failed: {e}")
    # Send alert, log error, etc.
```

**Task 5.2: Airflow Integration**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import great_expectations as gx

def run_ge_validation(**context):
    """Airflow task para execute validation GE."""
    ge_context = gx.get_context()

    results = ge_context.run_checkpoint(
        checkpoint_name="daily_transactions_checkpoint",
        batch_request={
            "runtime_parameters": {
                "query": f"SELECT * FROM transactions WHERE date = '{context['ds']}'"
            }
        }
    )

    if not results["success"]:
        raise AirflowException("Data quality validation failed!")

    return results

with DAG("etl_with_ge_validation", schedule_interval="@daily") as dag:

    extract = PythonOperator(task_id="extract", python_callable=extract_data)

    validate = PythonOperator(
        task_id="validate_quality",
        python_callable=run_ge_validation,
        provide_context=True
    )

    load = PythonOperator(task_id="load", python_callable=load_data)

    extract >> validate >> load
```

---

## ✅ Success Criteria

- [ ] Configuraste Great Expectations
- [ ] Creaste expectation suites para 3 tables
- [ ] Ejecutaste validaciones con checkpoints
- [ ] Generaste Data Docs
- [ ] Creaste custom expectations
- [ ] Integraste GE en un pipeline

## 🎓 Conceptos Aprendidos

- Great Expectations framework
- Expectations y suites
- Checkpoints y validations
- Data Docs generation
- Custom expectations
- pipeline integration

## 📚 resources

- **GE Docs**: https://docs.greatexpectations.io/
- **Expectations Gallery**: https://greatexpectations.io/expectations/
- **Tutorials**: https://docs.greatexpectations.io/docs/tutorials/

## ➡️ Next Exercise

**Exercise 04: Anomaly Detection** - Detect statistical anomalies
