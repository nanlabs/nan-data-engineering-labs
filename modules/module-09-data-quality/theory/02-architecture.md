# Data Quality - Arquitecturas y Frameworks

## Introduction

Building a robust data quality system requires more than ad-hoc validations. We need **frameworks**, **architecture patterns** and **best practices** that scale with our data. In this document we explore the main tools and architectures to implement data quality in production.

---

## Great Expectations Framework

**Great Expectations** is the most popular open-source framework for data quality in Python. Provides a declarative language to define expectations about your data and automatically validate them.

### Conceptos Clave

**1. Expectations:**
Assertions about your data (e.g. "this column should not have nulls").

**2. Expectation Suites:**
Collections of expectations that define the quality contract of a dataset.

**3. Data Docs:**
Self-generated documentation with validation results.

**4. Checkpoints:**
Validation points in your pipeline that execute suites.

**5. Data Context:**
GE project core configuration.

### Installation and Setup

```bash
# Instalar Great Expectations
pip install great-expectations

# Inicializar proyecto
great_expectations init
```

Esto crea la estructura:
```
great_expectations/
├── great_expectations.yml          # Configuration principal
├── expectations/                   # Expectation suites
├── checkpoints/                    # Checkpoint configs
├── plugins/                        # Custom expectations
└── uncommitted/
    ├── data_docs/                  # Reportes HTML
    └── validations/                # Resultados de validaciones
```

### Creating Expectations

**Method 1: Programmatically**

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest

# Crear context
context = gx.get_context()

# Conectar a datos
datasource = context.sources.add_pandas("my_datasource")

# Crear expectation suite
suite = context.add_expectation_suite("transactions_suite")

# Agregar expectations
validator = context.get_validator(
    batch_request=RuntimeBatchRequest(
        datasource_name="my_datasource",
        data_asset_name="transactions",
        runtime_parameters={"batch_data": transactions_df},
        batch_identifiers={"default_identifier_name": "default_identifier"},
    ),
    expectation_suite_name="transactions_suite"
)

# Expectations básicas
validator.expect_table_row_count_to_be_between(min_value=1000, max_value=1000000)
validator.expect_table_column_count_to_equal(value=10)

# Expectations por columna
validator.expect_column_values_to_not_be_null(column="transaction_id")
validator.expect_column_values_to_be_unique(column="transaction_id")
validator.expect_column_values_to_be_between(
    column="amount",
    min_value=0,
    max_value=1000000
)
validator.expect_column_values_to_be_in_set(
    column="status",
    value_set=["pending", "completed", "failed", "refunded"]
)

# Guardar suite
validator.save_expectation_suite(discard_failed_expectations=False)
```

**Method 2: Interactively**

```bash
# Crear suite interactivamente
great_expectations suite new

# Seguir el asistente para:
# 1. Seleccionar datasource
# 2. Seleccionar batch de datos
# 3. Agregar expectations con autocompleted
```

**Method 3: Auto-profiling**

```python
from great_expectations.profile.user_configurable_profiler import (
    UserConfigurableProfiler
)

# Generar expectations automáticamente basado en los datos
profiler = UserConfigurableProfiler(
    profile_dataset=validator,
    excluded_expectations=[
        "expect_column_values_to_be_in_set"  # Excluir ciertos expectations
    ],
)

suite = profiler.build_suite()
validator.save_expectation_suite()
```

### Available Expectations

Great Expectations tiene 50+ built-in expectations:

**Table-level Expectations:**
```python
# Row counts
expect_table_row_count_to_be_between(min_value, max_value)
expect_table_row_count_to_equal(value)

# Column structure
expect_table_columns_to_match_ordered_list(column_list)
expect_table_column_count_to_equal(value)
```

**Column-level Expectations:**
```python
# Nulls
expect_column_values_to_not_be_null(column)
expect_column_proportion_of_unique_values_to_be_between(column, min_value, max_value)

# Data types
expect_column_values_to_be_of_type(column, type_)
expect_column_values_to_be_in_type_list(column, type_list)

# Ranges
expect_column_values_to_be_between(column, min_value, max_value)
expect_column_min_to_be_between(column, min_value, max_value)
expect_column_max_to_be_between(column, min_value, max_value)
expect_column_mean_to_be_between(column, min_value, max_value)
expect_column_median_to_be_between(column, min_value, max_value)
expect_column_stdev_to_be_between(column, min_value, max_value)

# Sets
expect_column_values_to_be_in_set(column, value_set)
expect_column_values_to_not_be_in_set(column, value_set)
expect_column_distinct_values_to_be_in_set(column, value_set)

# Regex
expect_column_values_to_match_regex(column, regex)
expect_column_values_to_not_match_regex(column, regex)
expect_column_values_to_match_regex_list(column, regex_list)

# Strings
expect_column_value_lengths_to_be_between(column, min_value, max_value)
expect_column_value_lengths_to_equal(column, value)

# Uniqueness
expect_column_values_to_be_unique(column)
expect_compound_columns_to_be_unique(column_list)
```

**Multi-column Expectations:**
```python
# Relationships
expect_column_pair_values_to_be_equal(column_A, column_B)
expect_column_pair_values_A_to_be_greater_than_B(column_A, column_B)

# Correlations
expect_column_pair_cramers_phi_value_to_be_less_than(column_A, column_B, threshold)
```

### Custom Expectations

```python
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.execution_engine import PandasExecutionEngine

class ExpectColumnValuesToBeValidEmail(ColumnMapExpectation):
    """Expect column values to be valid email addresses."""

    # Metadata
    map_metric = "column_values.match.email"
    success_keys = ("mostly",)

    # Implementation para Pandas
    @classmethod
    def _pandas(cls, column, **kwargs):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return column.str.match(email_regex)

    # Description
    library_metadata = {
        "maturity": "production",
        "tags": ["validation", "email"],
        "contributors": ["@yourname"],
    }

# Usar custom expectation
validator.expect_column_values_to_be_valid_email(column="email", mostly=0.95)
```

### Running Validations (Checkpoints)

```python
# Crear checkpoint
checkpoint_config = {
    "name": "transactions_checkpoint",
    "config_version": 1.0,
    "class_name": "SimpleCheckpoint",
    "validations": [
        {
            "batch_request": {
                "datasource_name": "my_datasource",
                "data_asset_name": "transactions",
            },
            "expectation_suite_name": "transactions_suite",
        }
    ],
}

context.add_checkpoint(**checkpoint_config)

# Ejecutar checkpoint
results = context.run_checkpoint(
    checkpoint_name="transactions_checkpoint",
    batch_request={
        "runtime_parameters": {"batch_data": transactions_df},
        "batch_identifiers": {"default_identifier_name": "default"},
    },
)

# Revisar resultados
if results["success"]:
    print("✅ Todas las validaciones pasaron")
else:
    print("❌ Algunas validaciones fallaron")
    for result in results.run_results.values():
        for validation_result in result["validation_result"]["results"]:
            if not validation_result["success"]:
                print(f"   - {validation_result['expectation_config']['expectation_type']}")
```

### Data Docs

Great Expectations generates HTML documentation automatically:

```python
# Construir data docs
context.build_data_docs()

# Abrir en navegador
context.open_data_docs()
```

Los Data Docs incluyen:
- **Overview** de todas las suites
- **Validation results** with graphs
- **Expectation details** con ejemplos
- **Historical trends** de quality metrics

### Integration with Data Pipelines

**Con Airflow:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import great_expectations as gx

def validate_data(**context):
    """Task para validar datos con GE."""
    ge_context = gx.get_context()

    results = ge_context.run_checkpoint(
        checkpoint_name="daily_transactions_checkpoint",
        batch_request={
            "runtime_parameters": {
                "query": "SELECT * FROM transactions WHERE date = '{{ ds }}'"
            }
        }
    )

    if not results["success"]:
        raise ValueError("Data quality validation failed!")

    return results

with DAG("etl_with_validation", schedule_interval="@daily") as dag:

    extract = PythonOperator(...)

    validate = PythonOperator(
        task_id="validate_quality",
        python_callable=validate_data
    )

    load = PythonOperator(...)

    extract >> validate >> load  # Validar antes de load
```

**Con dbt:**
```yaml
# models/schema.yml
version: 2

models:
  - name: transactions
    description: "Daily transactions"

    # dbt tests (se integran con GE)
    tests:
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          max_value: 1000000

      - dbt_expectations.expect_column_values_to_not_be_null:
          column_name: transaction_id

    columns:
      - name: amount
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
```

---

## PyDeequ (Amazon's Data Quality Library)

**PyDeequ** is a Python wrapper on **Deequ**, Amazon's data quality library built on Apache Spark. It is ideal for large datasets.

### Key Features

- **Scala-based**: Corre en Spark para big data
- **Profiling**: Auto-generation of statistics
- **Constraints**: Validaciones declarativas
- **Metrics Repository**: Metrics history
- **Anomaly Detection**: Statistical anomaly detection

### Setup

```python
from pyspark.sql import SparkSession
import pydeequ

# Crear Spark session con Deequ JARs
spark = (SparkSession
    .builder
    .config("spark.jars.packages", pydeequ.deequ_maven_coord)
    .config("spark.jars.excludes", pydeequ.f2j_maven_coord)
    .getOrCreate())

# Cargar datos
df = spark.read.parquet("s3://bucket/transactions/")
```

### Data Profiling

```python
from pydeequ.profiles import ColumnProfilerRunner

# Perfil completo del dataset
result = ColumnProfilerRunner(spark).onData(df).run()

# Ver perfil de cada columna
for col, profile in result.profiles.items():
    print(f"\nColumn: {col}")
    print(f"  Completeness: {profile.completeness}")
    print(f"  Approx distinct: {profile.approximateNumDistinctValues}")
    print(f"  Data type: {profile.dataType}")

    if profile.dataType == "Integral":
        print(f"  Min: {profile.minimum}")
        print(f"  Max: {profile.maximum}")
        print(f"  Mean: {profile.mean}")
        print(f"  Std dev: {profile.stdDev}")
```

### Constraint Verification

```python
from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationSuite, VerificationResult

# Definir checks
check = Check(spark, CheckLevel.Error, "Transaction Validation")

verification = (VerificationSuite(spark)
    .onData(df)
    .addCheck(
        check
        .hasSize(lambda x: x >= 1000)
        .hasMin("amount", lambda x: x == 0)
        .hasMax("amount", lambda x: x <= 1000000)
        .isComplete("transaction_id")
        .isUnique("transaction_id")
        .isContainedIn("status", ["pending", "completed", "failed"])
        .satisfies("amount > 0", "Amounts must be positive")
    )
    .run()
)

# Revisar resultados
verification_df = VerificationResult.checkResultsAsDataFrame(spark, verification)
verification_df.show(truncate=False)

if verification.status == "Success":
    print("✅ All checks passed")
else:
    print("❌ Some checks failed")
```

### Metrics Computation

```python
from pydeequ.analyzers import *

# Calcular métricas específicas
analysis = (AnalysisRunner(spark)
    .onData(df)
    .addAnalyzer(Size())
    .addAnalyzer(Completeness("customer_id"))
    .addAnalyzer(Uniqueness("transaction_id"))
    .addAnalyzer(Mean("amount"))
    .addAnalyzer(StandardDeviation("amount"))
    .addAnalyzer(Minimum("amount"))
    .addAnalyzer(Maximum("amount"))
    .addAnalyzer(CountDistinct("customer_id"))
    .addAnalyzer(Correlation("age", "total_spent"))
    .run()
)

# Convertir a DataFrame para análisis
metrics_df = AnalyzerContext.successMetricsAsDataFrame(spark, analysis)
metrics_df.show()
```

### Anomaly Detection

```python
from pydeequ.anomaly_detection import *

# Configurar repositorio de métricas
metricsRepository = FileSystemMetricsRepository(spark, "s3://bucket/metrics/")

# Guardar métricas con resultKey
resultKey = ResultKey(
    spark,
    dataSetDate=datetime.now().timestamp()
)

analysis = (AnalysisRunner(spark)
    .onData(df)
    .addAnalyzer(Size())
    .addAnalyzer(Completeness("amount"))
    .useRepository(metricsRepository)
    .saveOrAppendResult(resultKey)
    .run()
)

# Detectar anomalías basadas en historial
anomalyDetection = (AnomalyDetectionRunner(spark)
    .onData(df)
    .useRepository(metricsRepository)
    .addAnomalyCheck(
        AbsoluteChangeStrategy(maxRateIncrease=2.0),
        Size()
    )
    .run()
)
```

### PyDeequ vs Great Expectations

| Feature | PyDeequ | Great Expectations |
|---------|---------|-------------------|
| **Engine** | Spark (Scala) | Pandas, Spark, SQL |
| **Best for** | Big data (PB scale) | Medium data (GB-TB) |
| **Language** | Python wrapper | Pure Python |
| **Learning curve** | Steeper | Gentler |
| **Documentation** | Auto-generated | Rich Data Docs |
| **Anomaly detection** | Built-in | Plugin |
| **Profiling** | Fast (distributed) | Slower (single node) |

**Recommendation:**
- Use **PyDeequ** if you're already on Spark and have big data
- Use **Great Expectations** for most other cases (better DX, more mature)

---

## Pandera: Statistical Data Validation

**Pandera** is a DataFrames validation library with a focus on **data contracts** and static **type checking**.

### Key Features

- Schema-based validation
- Integration con mypy para type checking
- Hypothesis testing
- Statistical validation

### Basic Usage

```python
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check

# Definir schema
schema = DataFrameSchema(
    {
        "transaction_id": Column(pa.Int64, checks=Check.greater_than(0), unique=True),
        "customer_id": Column(pa.Int64, nullable=False),
        "amount": Column(pa.Float64, checks=[
            Check.greater_than_or_equal_to(0),
            Check.less_than_or_equal_to(1000000)
        ]),
        "status": Column(pa.String, checks=Check.isin([
            "pending", "completed", "failed", "refunded"
        ])),
        "timestamp": Column(pa.DateTime),
    },
    checks=[
        Check(lambda df: len(df) > 100, error="Insufficient rows")
    ],
    strict=True  # No permitir columnas extra
)

# Validar DataFrame
try:
    validated_df = schema.validate(df)
    print("✅ Validation passed")
except pa.errors.SchemaError as e:
    print(f"❌ Validation failed:\n{e}")
```

### Custom Checks

```python
# Check functions personalizadas
@pa.check_output(schema)
def process_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza que output cumple schema."""
    # ... processing ...
    return df

# Checks con lambda
schema = DataFrameSchema({
    "email": Column(pa.String, checks=Check(
        lambda s: s.str.match(r'^[^@]+@[^@]+\.[^@]+$'),
        error="Invalid email format"
    ))
})

# Checks estadísticos
schema = DataFrameSchema({
    "score": Column(pa.Float, checks=[
        Check(lambda s: s.mean() > 0.5, element_wise=False),
        Check(lambda s: s.std() < 0.2, element_wise=False)
    ])
})
```

### Hypothesis Testing

```python
from pandera import Hypothesis

schema = DataFrameSchema({
    "height": Column(pa.Float, checks=Hypothesis(
        test=Hypothesis.two_sample_ttest,
        samples=["group_A", "group_B"],
        relationship="greater_than",
        alpha=0.05
    ))
})
```

### DataFrameModel (Class-based API)

```python
from pandera import DataFrameModel
from pandera.typing import Series

class TransactionSchema(DataFrameModel):
    """Schema for transaction data."""

    transaction_id: Series[pa.Int64] = pa.Field(unique=True, gt=0)
    customer_id: Series[pa.Int64] = pa.Field(nullable=False)
    amount: Series[pa.Float64] = pa.Field(ge=0, le=1000000)
    status: Series[pa.String] = pa.Field(isin=["pending", "completed", "failed"])

    class Config:
        strict = True
        coerce = True  # Auto-convert types

# Uso
TransactionSchema.validate(df)
```

---

## Arquitecturas de Data Quality

### 1. Quality Gates en Pipelines

**Concept:** Validation points that must be passed before continuing.

```
[Extract] → [Gate 1: Schema] → [Transform] → [Gate 2: Business Rules] → [Load] → [Gate 3: Completeness]
```

**Implementation:**

```python
class DataPipeline:
    """Pipeline con quality gates."""

    def __init__(self):
        self.gates = []
        self.data = None

    def add_gate(self, name: str, validator: callable):
        """Agrega quality gate."""
        self.gates.append({"name": name, "validator": validator})
        return self

    def run(self, input_data: pd.DataFrame):
        """Ejecuta pipeline con gates."""
        self.data = input_data

        for gate in self.gates:
            print(f"🚦 Quality Gate: {gate['name']}")

            result = gate['validator'](self.data)

            if not result['passed']:
                print(f"❌ GATE FAILED: {gate['name']}")
                print(f"   Reason: {result['reason']}")
                raise DataQualityException(
                    f"Quality gate '{gate['name']}' failed"
                )

            print(f"✅ GATE PASSED: {gate['name']}")

        return self.data

# Definir gates
def gate_schema(df):
    required_cols = ['id', 'amount', 'timestamp']
    missing = set(required_cols) - set(df.columns)
    return {
        'passed': len(missing) == 0,
        'reason': f"Missing columns: {missing}" if missing else None
    }

def gate_completeness(df):
    completeness = df.notna().sum().sum() / (df.shape[0] * df.shape[1])
    threshold = 0.95
    return {
        'passed': completeness >= threshold,
        'reason': f"Completeness {completeness:.2%} < {threshold:.2%}"
    }

def gate_business_rules(df):
    violations = df[df['amount'] < 0]
    return {
        'passed': len(violations) == 0,
        'reason': f"{len(violations)} negative amounts found"
    }

# Ejecutar pipeline
pipeline = (DataPipeline()
    .add_gate("Schema Validation", gate_schema)
    .add_gate("Completeness Check", gate_completeness)
    .add_gate("Business Rules", gate_business_rules)
)

try:
    clean_data = pipeline.run(raw_data)
except DataQualityException as e:
    # Handle failure (alertas, rollback, etc.)
    handle_quality_failure(e)
```

### 2. Data Quality Monitoring

**Continuous monitoring architecture:**

```
┌─────────────┐
│ Data Source │
└──────┬──────┘
       ▼
┌──────────────────┐
│  Quality Checks  │◄─── Great Expectations
│  (Real-time)     │
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Metrics Store   │◄─── Prometheus / CloudWatch
│  (Time-series)   │
└──────┬───────────┘
       ▼
┌──────────────────┐
│   Dashboards     │◄─── Grafana / Tableau
│   (Viz + Alerts) │
└──────────────────┘
```

**Implementation with Prometheus:**

```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time

# Métricas
validation_checks = Counter(
    'data_quality_checks_total',
    'Total quality checks run',
    ['dataset', 'check_type', 'status']
)

quality_score = Gauge(
    'data_quality_score',
    'Current quality score',
    ['dataset', 'dimension']
)

validation_duration = Histogram(
    'data_quality_validation_seconds',
    'Time spent in validation',
    ['dataset']
)

def validate_with_metrics(df: pd.DataFrame, dataset_name: str):
    """Validation con métricas."""
    start_time = time.time()

    try:
        # Run validations
        checks = {
            'completeness': check_completeness(df),
            'validity': check_validity(df),
            'uniqueness': check_uniqueness(df)
        }

        # Record metrics
        for check_type, result in checks.items():
            status = 'success' if result['passed'] else 'failure'
            validation_checks.labels(
                dataset=dataset_name,
                check_type=check_type,
                status=status
            ).inc()

            quality_score.labels(
                dataset=dataset_name,
                dimension=check_type
            ).set(result['score'])

    finally:
        duration = time.time() - start_time
        validation_duration.labels(dataset=dataset_name).observe(duration)

# Start metrics server
start_http_server(8000)
```

**Grafana Dashboard Query:**
```promql
# Quality score over time
avg(data_quality_score{dataset="transactions"}) by (dimension)

# Failure rate
rate(data_quality_checks_total{status="failure"}[5m])
  / rate(data_quality_checks_total[5m])

# P95 validation duration
histogram_quantile(0.95,
  rate(data_quality_validation_seconds_bucket[5m]))
```

### 3. Data Contracts

**Concept:** Formal contract between data producer and consumer.

```yaml
# data_contract.yaml
version: 1.0
dataset: customer_transactions
owner: data-engineering-team@company.com
description: "Daily customer transactions"

schema:
  columns:
    - name: transaction_id
      type: integer
      nullable: false
      unique: true
      description: "Unique transaction ID"

    - name: customer_id
      type: integer
      nullable: false
      description: "Customer ID (foreign key to customers.id)"

    - name: amount
      type: decimal(10,2)
      nullable: false
      constraints:
        min: 0
        max: 1000000

    - name: timestamp
      type: timestamp
      nullable: false

quality_sla:
  completeness: 99%
  uniqueness: 100%
  timeliness: 4h  # Max latency
  availability: 99.9%

delivery:
  schedule: "0 2 * * *"  # Daily at 2 AM
  format: parquet
  location: s3://bucket/transactions/dt={{ ds }}/
  partitioning: [date]

breaking_changes:
  - "2024-01-15: Migrated from CSV to Parquet"
  - "2024-01-01: Added 'payment_method' column"

consumers:
  - team: analytics
    contact: analytics@company.com
    usage: "Daily reporting dashboard"

  - team: ml-platform
    contact: ml@company.com
    usage: "Fraud detection model training"
```

**Contract Validation:**

```python
import yaml
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DataContract:
    """Data contract specification."""
    version: str
    dataset: str
    owner: str
    schema: Dict
    quality_sla: Dict
    delivery: Dict

def validate_against_contract(df: pd.DataFrame, contract_path: str) -> Dict:
    """Valida datos contra contrato."""
    # Load contract
    with open(contract_path) as f:
        contract_spec = yaml.safe_load(f)

    contract = DataContract(**contract_spec)
    violations = []

    # Validate schema
    for col_spec in contract.schema['columns']:
        col_name = col_spec['name']

        if col_name not in df.columns:
            violations.append(f"Missing column: {col_name}")
            continue

        # Check nullability
        if not col_spec.get('nullable', True):
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                violations.append(
                    f"{col_name}: {null_count} nulls (not nullable)"
                )

        # Check uniqueness
        if col_spec.get('unique', False):
            dupes = df[col_name].duplicated().sum()
            if dupes > 0:
                violations.append(
                    f"{col_name}: {dupes} duplicates (must be unique)"
                )

        # Check constraints
        if 'constraints' in col_spec:
            constraints = col_spec['constraints']

            if 'min' in constraints:
                below_min = (df[col_name] < constraints['min']).sum()
                if below_min > 0:
                    violations.append(
                        f"{col_name}: {below_min} values < {constraints['min']}"
                    )

            if 'max' in constraints:
                above_max = (df[col_name] > constraints['max']).sum()
                if above_max > 0:
                    violations.append(
                        f"{col_name}: {above_max} values > {constraints['max']}"
                    )

    # Validate quality SLA
    completeness = df.notna().sum().sum() / (df.shape[0] * df.shape[1]) * 100
    sla_completeness = float(contract.quality_sla['completeness'].strip('%'))

    if completeness < sla_completeness:
        violations.append(
            f"Completeness {completeness:.1f}% < SLA {sla_completeness}%"
        )

    return {
        'contract_version': contract.version,
        'compliant': len(violations) == 0,
        'violations': violations
    }

# Uso en pipeline
result = validate_against_contract(df, 'contracts/transactions.yaml')
if not result['compliant']:
    send_alert_to_owner(contract.owner, result['violations'])
    raise DataContractViolation(result['violations'])
```

### 4. Quarantine Pattern

**Concept:** Isolate poor quality data without stopping the pipeline.

```
                    ┌─────────────┐
                    │   Extract   │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Validate   │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
          ┌─────────┤   Router    │──────────┐
          │         └─────────────┘          │
          ▼                                  ▼
  ┌──────────────┐                   ┌─────────────┐
  │ Valid Data   │                   │ Quarantine  │
  │  ─→ Load     │                   │  (Review)   │
  └──────────────┘                   └─────────────┘
```

**Implementation:**

```python
class QuarantineHandler:
    """Maneja datos en cuarentena."""

    def __init__(self, quarantine_path: str):
        self.quarantine_path = quarantine_path
        self.quarantined_records = []

    def process_batch(self, df: pd.DataFrame, validations: List[callable]) -> tuple:
        """Procesa batch separando válidos de cuarentena."""
        valid_mask = pd.Series([True] * len(df))

        for validation in validations:
            validation_result = validation(df)
            valid_mask &= validation_result

        valid_df = df[valid_mask]
        quarantine_df = df[~valid_mask]

        if len(quarantine_df) > 0:
            self._save_to_quarantine(quarantine_df)
            self._send_alert(len(quarantine_df), len(df))

        return valid_df, quarantine_df

    def _save_to_quarantine(self, df: pd.DataFrame):
        """Guarda datos en cuarentena."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = f"{self.quarantine_path}/quarantine_{timestamp}.parquet"

        df['quarantine_timestamp'] = datetime.now()
        df['quarantine_reason'] = 'validation_failed'

        df.to_parquet(path)
        self.quarantined_records.append(path)

        print(f"📦 {len(df)} records quarantined: {path}")

    def _send_alert(self, quarantined_count: int, total_count: int):
        """Alerta sobre datos en cuarentena."""
        rate = (quarantined_count / total_count) * 100

        if rate > 10:  # Threshold
            send_pagerduty_alert(
                f"High quarantine rate: {rate:.1f}% ({quarantined_count}/{total_count})"
            )

    def review_quarantine(self) -> pd.DataFrame:
        """Review all quarantined data."""
        all_quarantined = []

        for path in self.quarantined_records:
            df = pd.read_parquet(path)
            all_quarantined.append(df)

        return pd.concat(all_quarantined, ignore_index=True)

# Uso
handler = QuarantineHandler('/data/quarantine')

valid, quarantined = handler.process_batch(
    df=raw_data,
    validations=[
        lambda df: df['amount'] > 0,
        lambda df: df['customer_id'].notna(),
        lambda df: df['email'].str.match(r'^[^@]+@[^@]+\.[^@]+$')
    ]
)

# Procesar solo datos válidos
load_to_warehouse(valid)

# Review cuarentena periódicamente
if datetime.now().hour == 9:  # Daily at 9 AM
    quarantine_report = handler.review_quarantine()
    send_to_data_stewards(quarantine_report)
```

---

## Best Practices Summary

### 1. Layered Validation

```
Input Layer     → Schema, format, required fields
Business Layer  → Business rules, referential integrity
Output Layer    → Aggregation checks, completeness
```

### 2. Fail vs. Warn

No todas las validaciones deben detener el pipeline:

```python
class ValidationSeverity:
    CRITICAL = "critical"  # Detiene pipeline
    WARNING = "warning"    # Alerta pero continúa
    INFO = "info"          # Solo log

validations = [
    {'check': lambda df: df['id'].notna().all(),
     'severity': ValidationSeverity.CRITICAL},

    {'check': lambda df: (df['amount'] > 0).all(),
     'severity': ValidationSeverity.CRITICAL},

    {'check': lambda df: df['phone'].notna().sum() / len(df) > 0.90,
     'severity': ValidationSeverity.WARNING},

    {'check': lambda df: df['notes'].notna().sum() / len(df) > 0.50,
     'severity': ValidationSeverity.INFO},
]
```

### 3. Version Control for Expectations

Treat expectations as code:

```bash
# Git history de expectation suites
git log expectations/transactions_suite.json

# Code review para cambios en validaciones
# Pull request para agregar/modificar expectations
```

### 4. Data Quality as Code

```python
# Definir en código, aplicar con CI/CD
from dataclasses import dataclass

@dataclass
class QualityRule:
    name: str
    dimension: str
    check: callable
    threshold: float
    severity: str

CUSTOMER_QUALITY_RULES = [
    QualityRule(
        name="email_completeness",
        dimension="completeness",
        check=lambda df: df['email'].notna().sum() / len(df),
        threshold=0.95,
        severity="critical"
    ),
    QualityRule(
        name="unique_customer_id",
        dimension="uniqueness",
        check=lambda df: df['customer_id'].nunique() / len(df),
        threshold=1.0,
        severity="critical"
    ),
]

def enforce_rules(df: pd.DataFrame, rules: List[QualityRule]):
    """Aplica reglas de calidad."""
    for rule in rules:
        score = rule.check(df)
        if score < rule.threshold:
            msg = f"{rule.name}: {score:.2%} < {rule.threshold:.2%}"
            if rule.severity == "critical":
                raise DataQualityException(msg)
            else:
                logging.warning(msg)
```

---

## Conclusion

Un sistema de data quality robusto requiere:
1. **Framework adecuado** (Great Expectations, PyDeequ, Pandera)
2. **Well designed architecture** (quality gates, monitoring, contracts)
3. **Automation** (CI/CD, alerts, dashboards)
4. **Cultura** (ownership, data contracts, continuous improvement)

En el siguiente documento exploramos herramientas adicionales y resources de aprendizaje.

➡️ **theory/03-resources.md**: Herramientas y resources adicionales
