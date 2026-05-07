# Data Quality - resources y Herramientas

##

 Introduction

El ecosistema de data quality ha evolucionado significativamente. En este documento exploramos las herramientas disponibles, sus casos de uso, comparaciones, y resources para profundizar tu conocimiento.

---

## Herramientas y Frameworks

### 1. Great Expectations ⭐ (Recommended)

**Website:** <https://greatexpectations.io/>
**GitHub:** <https://github.com/great-expectations/great_expectations>
**Stars:** ~9k | **License:** Apache 2.0

**Pros:**

- ✅ API intuitiva y bien documentada
- ✅ Data Docs auto-generados (HTML)
- ✅ Integration with Airflow, dbt, Spark
- ✅ Checkpoints para CI/CD
- ✅ Comunidad activa

**Cons:**

- ⚠️ Puede ser lento en datasets grandes (usar Spark backend)
- ⚠️ Curva de aprendizaje inicial
- ⚠️ Extensive initial setup

**Cuando Usar:**

- Equipos que necesitan data docs para stakeholders
- Complex validations with multiple expectations
- Integration with existing pipelines (Airflow, dbt)

**Alternativas:**

- For small datasets: Pandera (lighter)
- Para big data en Spark: PyDeequ

---

### 2. Pandera

**Website:** <https://pandera.readthedocs.io/>
**GitHub:** <https://github.com/unionai-oss/pandera>
**Stars:** ~3k | **License:** MIT

**Pros:**

- ✅ Syntax compacta (menos verbose que GE)
- ✅ Integration with mypy (static type checking)
- ✅ Hypothesis testing built-in
- ✅ Quick setup

**Cons:**

- ⚠️ Sin Data Docs (solo errores)
- ⚠️ Menos features que Great Expectations
- ⚠️ Smaller community

**Basic Example:**

```python
import pandera as pa
from pandera import Column, DataFrameSchema

schema = DataFrameSchema({
    "transaction_id": Column(pa.Int, unique=True),
    "amount": Column(pa.Float, checks=pa.Check.greater_than(0))
})

validated_df = schema.validate(df)
```text

**Cuando Usar:**

- Proyectos Python puro (sin Spark)
- Small teams that value simplicity
- Integration with mypy/static typing

---

### 3. PyDeequ (Amazon)

**Website:** <https://github.com/awslabs/python-deequ>
**GitHub:** <https://github.com/awslabs/python-deequ>
**Stars:** ~700 | **License:** Apache 2.0

**Pros:**

- ✅ Designed for big data (PySpark)
- ✅ Advanced Anomaly detection
- ✅ Metrics repository (historical trends)
- ✅ Used in production on Amazon

**Cons:**

- ⚠️ Requiere Spark (overhead)
- ⚠️ Limited documentation
- ⚠️ More complex setup

**Basic Example:**

```python
from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationSuite

check = Check(spark, CheckLevel.Error, "Transaction Check")
verification = (VerificationSuite(spark)
    .onData(df)
    .addCheck(check
        .hasSize(lambda x: x >= 1000)
        .isComplete("transaction_id")
    )
    .run()
)
```text

**Cuando Usar:**

- Ya tienes infraestructura Spark
- Datasets grandes (GB-TB-PB)
- Necesitas anomaly detection empresarial

---

### 4. DuckDB for Data Quality

**Website:** <https://duckdb.org/>
**GitHub:** <https://github.com/duckdb/duckdb>

**Feature:** SQL sobre Parquet sin cargar en memoria.

**Uso para Quality Checks:**

```python
import duckdb

# Check completeness
result = duckdb.sql("""
    SELECT
        COUNT(*) as total,
        COUNT(customer_id) as non_null_customers,
        (COUNT(customer_id) * 100.0 / COUNT(*)) as completeness_pct
    FROM 'transactions.parquet'
""").df()

# Check duplicates
dupes = duckdb.sql("""
    SELECT transaction_id, COUNT(*) as count
    FROM 'transactions.parquet'
    GROUP BY transaction_id
    HAVING COUNT(*) > 1
""").df()

# Check business rules
violations = duckdb.sql("""
    SELECT *
    FROM 'transactions.parquet'
    WHERE amount < 0 OR amount > 1000000
""").df()
```text

**Pros:**

- ✅ Extremely fast
- ✅ Does not require loading data into memory
- ✅ Standard SQL

**Cuando Usar:**

- Quality checks ad-hoc
- Exploratory data analysis
- Como complemento a otros frameworks

---

### 5. ydata-profiling (formerly pandas-profiling)

**Website:** <https://docs.profiling.ydata.ai/>
**GitHub:** <https://github.com/ydataai/ydata-profiling>
**Stars:** ~11k | **License:** MIT

**Feature:** Auto-generation of profiling reports.

```python
from ydata_profiling import ProfileReport

profile = ProfileReport(
    df,
    title="Transaction Data Quality Report",
    explorative=True
)

profile.to_file("report.html")
```

**El reporte incluye:**

- Overview (tipos, missing, duplicates)
- Variables (distribution, stats, extreme values)
- Correlations (Pearson, Spearman, Cramer's V)
- Missing values (matriz, dendrogram)
- Sample data

**Pros:**

- ✅ Genera reportes HTML hermosos
- ✅ Automatically identifies problems
- ✅ Minimal code

**Cons:**

- ⚠️ Lento en datasets grandes (>1M rows)
- ⚠️ Only for exploration, not for production

**Cuando Usar:**

- Exploratory analysis inicial
- Entender nuevo dataset
- Generate reports for non-technical stakeholders

---

### 6. Soda Core

**Website:** <https://www.soda.io/>
**GitHub:** <https://github.com/sodadata/soda-core>
**Stars:** ~1.5k | **License:** Apache 2.0

**Feature:** YAML-based data quality checks.

```yaml
# checks.yml
checks for transactions:
  - row_count > 1000
  - missing_count(customer_id) = 0
  - invalid_count(email) = 0:
      valid format: email
  - duplicate_count(transaction_id) = 0
  - min(amount) >= 0
  - max(amount) <= 1000000
```text

```bash
# Run checks
soda scan -d postgres -c config.yml checks.yml
```text

**Pros:**

- ✅ Syntax declarativa (YAML)
- ✅ Easy for non-programmers
- ✅ Integration with dbt, Airflow

**Cons:**

- ⚠️ Less flexible than Python code
- ⚠️ Cloud version is paid

---

### 7. Apache Griffin

**Website:** <https://griffin.apache.org/>
**GitHub:** <https://github.com/apache/griffin>

**Feature:** Data quality platform empresarial.

**Componentes:**

- Measure: Define quality metrics
- Service: Orchestration
- UI: Dashboards and visualization

**Pros:**

- ✅ Complete solution (not just library)
- ✅ Dashboard built-in
- ✅ Designed for big data

**Cons:**

- ⚠️ Setup complejo
- ⚠️ Limited documentation
- ⚠️ Small community

---

### 8. Talend Data Quality

**Website:** <https://www.talend.com/>
**License:** Comercial (Open Studio es open-source)

**Pros:**

- ✅ GUI para definir reglas
- ✅ Advanced Profiling
- ✅ Business integration

**Cons:**

- ⚠️ Costoso
- ⚠️ Vendor lock-in

---

## Tools Comparison

### Selection Matrix

| Tool | Use Cases | Data Scale | Ease | Cost |
|-------------|--------------|----------------|-----------|-------|
| **Great Expectations** | General purpose, pipelines | GB-TB (Spark: PB) | ⭐⭐⭐ | Gratis |
| **Pandera** | Python projects, type safety | GB | ⭐⭐⭐⭐⭐ | Gratis |
| **PyDeequ** | Big data, Spark | TB-PB | ⭐⭐ | Gratis |
| **DuckDB** | Ad-hoc checks, EDA | GB-TB | ⭐⭐⭐⭐⭐ | Gratis |
| **ydata-profiling** | EDA, reporting | GB | ⭐⭐⭐⭐⭐ | Gratis |
| **Soda Core** | YAML-based, simple | GB-TB | ⭐⭐⭐⭐ | Gratis/Pago |
| **Apache Griffin** | Enterprise platform | TB-PB | ⭐ | Gratis |
| **Talend** | Enterprise GUI | TB-PB | ⭐⭐⭐ | $$$ |

### Decision Tree

```text
¿Tienes Spark?
├─ SÍ → PyDeequ
└─ NO
   │
   ¿Dataset size?
   ├─ < 10GB → Pandera o Great Expectations
   ├─ 10GB-1TB → Great Expectations + Spark backend
   └─ > 1TB → Considera PyDeequ (vale la pena el overhead)

¿Necesitas Data Docs?
├─ SÍ → Great Expectations
└─ NO → Pandera (más simple)

¿Equipo no técnico?
├─ SÍ → Soda Core (YAML) o Talend (GUI)
└─ NO → Great Expectations o Pandera

¿Solo exploración?
└─ ydata-profiling + DuckDB
```

---

## Cloud Services

### AWS

**AWS Glue Data Quality**

- Built-in en AWS Glue ETL
- Ruleset-based (DQDL language)
- Integrated con Data Catalog

```python
# Glue Data Quality Rules
rulesets = """
    Rules = [
        RowCount > 1000,
        IsComplete "customer_id",
        ColumnValues "amount" > 0,
        CustomSQL "SELECT COUNT(*) FROM primary WHERE amount < 0" = 0
    ]
"""

# En Glue job
glueContext.evaluate_data_quality(
    rulesets,
    DynamicFrame.fromDF(df, glueContext, "df")
)
```text

**Amazon Deequ**

- Open-source (PyDeequ)
- Usado internamente en Amazon

---

### GCP

**Dataplex Data Quality**

- Managed service en GCP
- YAML-based rules
- Integration con BigQuery

```yaml
# Dataplex DQ rules
rules:
  - rule_type: NOT_NULL
    dimension: COMPLETENESS
    column: customer_id

  - rule_type: RANGE
    dimension: VALIDITY
    column: amount
    params:
      min_value: 0
      max_value: 1000000
```text

**Great Expectations on Dataproc**

- Run GE en Spark clusters
- Best practice para big data en GCP

---

### Azure

**Azure Purview Data Quality**

- Part of Microsoft Purview
- Scan and profile data
- Lineage tracking

**Synapse Data Quality**

- Built-in en Synapse Pipelines
- Validation activities

---

### Databricks

**Delta Live Tables (DLT) Expectations**

```python
import dlt
from pyspark.sql.functions import col

@dlt.table
@dlt.expect("valid_amount", "amount > 0")
@dlt.expect_or_drop("non_null_customer", "customer_id IS NOT NULL")
@dlt.expect_or_fail("unique_ids", "COUNT(DISTINCT transaction_id) = COUNT(*)")
def transactions_clean():
    return spark.read.table("transactions_bronze")
```text

**Pros:**

- ✅ Declarativo
- ✅ Auto-quarantine (expect_or_drop)
- ✅ Lineage tracking

---

## Python Libraries Complementarias

### Data Validation

```python
# Cerberus - Schema validation
from cerberus import Validator

schema = {
    'transaction_id': {'type': 'integer', 'required': True, 'min': 1},
    'amount': {'type': 'float', 'min': 0, 'max': 1000000}
}

v = Validator(schema)
v.validate({'transaction_id': 123, 'amount': 50.0})

# Pydantic - Data models
from pydantic import BaseModel, Field, validator

class Transaction(BaseModel):
    transaction_id: int = Field(gt=0)
    customer_id: int
    amount: float = Field(ge=0, le=1000000)

    @validator('amount')
    def amount_two_decimals(cls, v):
        if round(v, 2) != v:
            raise ValueError('Amount must have max 2 decimals')
        return v

# Uso
tx = Transaction(transaction_id=1, customer_id=100, amount=50.99)
```

### Anomaly Detection

```python
# PyOD - Python Outlier Detection
from pyod.models.iforest import IForest

# Isolation Forest
clf = IForest(contamination=0.1)
clf.fit(df[['amount', 'transaction_count']])

# Predict outliers
outliers = clf.predict(df[['amount', 'transaction_count']])
df['is_outlier'] = outliers

# scikit-learn
from sklearn.ensemble import IsolationForest

iso = IsolationForest(contamination=0.05)
predictions = iso.fit_predict(df[numeric_columns])
```text

### Statistical Testing

```python
# scipy
from scipy import stats

# Test normalidad
stat, p_value = stats.normaltest(df['amount'])

# Chi-square test (categorical)
contingency_table = pd.crosstab(df['category'], df['status'])
chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

# t-test (comparar grupos)
group_a = df[df['group'] == 'A']['amount']
group_b = df[df['group'] == 'B']['amount']
t_stat, p_value = stats.ttest_ind(group_a, group_b)
```text

---

## Development Tools

### IDE Extensions

**VS Code:**

- Python extension (Microsoft)
- Jupyter notebooks
- Great Expectations snippets

**PyCharm:**

- Data View para DataFrames
- Pytest integration
- Database tools

### Jupyter Extensions

```bash
# JupyterLab extensions útiles
pip install jupyterlab
pip install jupyterlab-execute-time          # Show execution time
pip install jupyterlab-spreadsheet-editor    # Edit CSVs
pip install jupyterlab_code_formatter        # Auto-format code
```text

### CLI Tools

```bash
# csvkit - CSV manipulation
pip install csvkit

csvstat transactions.csv              # Stats
csvgrep -c amount -m "100" data.csv  # Filter
csvsql --query "SELECT * FROM data WHERE amount > 100" data.csv

# xsv (Rust-based, faster)
sudo apt install xsv

xsv stats transactions.csv
xsv select customer_id,amount transactions.csv | xsv frequency
```

---

## Learning Resources

### Documentation

**Great Expectations:**

- Docs: <https://docs.greatexpectations.io/>
- Getting Started: <https://docs.greatexpectations.io/docs/tutorials/getting_started/>
- Expectations Gallery: <https://greatexpectations.io/expectations/>

**Pandera:**

- Docs: <https://pandera.readthedocs.io/>
- Examples: <https://github.com/unionai-oss/pandera/tree/main/examples>

**PyDeequ:**

- Docs: <https://github.com/awslabs/python-deequ>
- Deequ (Scala): <https://github.com/awslabs/deequ>

---

### Courses & Tutorials

**Free:**

1. **DataCamp: Data Quality in Python**
   - <https://www.datacamp.com/>

2. **Great Expectations University**
   - <https://greatexpectations.io/blog/ge-university/>

3. **Google Cloud Skills Boost: Data Quality**
   - <https://www.cloudskillsboost.google/>

**Paid:**

1. **Udemy: Complete Data Quality Fundamentals**
   - Focus en business + technical

2. **Coursera: Data Quality and Governance**
   - University of Colorado Boulder

---

### Books

1. **"Data Quality: The Accuracy Dimension"** by Jack E. Olson
   - Bible de data quality

2. **"Bad Data Handbook"** by Q. Ethan McCallum
   - Real-world problemas y solutions

3. **"Data Quality Assessment"** by Arkady Maydanchik
   - Frameworks and methodologies

4. **"The Data Warehouse Toolkit"** by Ralph Kimball
   - Includes extensive chapter on data quality

---

### Blogs & Articles

**Must-Read:**

1. **Great Expectations Blog**
   - <https://greatexpectations.io/blog/>

2. **Netflix Tech Blog - Data Quality**
   - <https://netflixtechblog.com/>

3. **Uber Engineering - Data Quality**
   - <https://eng.uber.com/>

4. **Airbnb Engineering - Data Quality**
   - <https://medium.com/airbnb-engineering>

**Key Articles:**

- "Data Quality at Airbnb" (Airbnb)
- "Netflix Data Quality" (Netflix)
- "Monitoring Data Quality at Scale" (Uber)
- "The Downfall of Data Quality" (Locally Optimistic)

---

### Conferences & Communities

**Conferences:**

- **Data Council** - <https://www.datacouncil.ai/>
- **Spark+AI Summit** - Tiene track de data quality
- **dbt Coalesce** - Focus en analytics engineering

**Communities:**

- **Great Expectations Slack** - <https://greatexpectations.io/slack>
- **dbt Community** - <https://www.getdbt.com/community/>
- **r/dataengineering** (Reddit)
- **Data Engineering Discord**

**Meetups:**

Busca "Data Quality" o "Data Engineering" en:

- <https://www.meetup.com/>
- LinkedIn Events

---

## Certifications

### AWS

**AWS Certified Data Analytics - Specialty**

- Incluye data quality en Glue y Lake Formation
- <https://aws.amazon.com/certification/certified-data-analytics-specialty/>

**AWS Certified Database - Specialty**

- Data integrity y quality checks

### GCP

**Professional Data Engineer**

- Incluye Dataplex Data Quality
- <https://cloud.google.com/certification/data-engineer>

### Microsoft

**Azure Data Engineer Associate (DP-203)**

- Purview y data quality

### Databricks

**Databricks Certified Data Engineer Professional**

- Delta Live Tables expectations

### Vendor-Neutral

**CDMP (Certified Data Management Professional)**

- DAMA International
- Comprehensive data quality curriculum

---

## Best Practices Checklist

### Getting Started

- [ ] Define critical quality dimensions for your domain
- [ ] Establecer baseline metrics (medir estado actual)
- [ ] Seleccionar framework (Great Expectations recommended)
- [ ] Implement 5-10 basic validations
- [ ] Configure alerts for failures

### Intermediate

- [ ] Create data contracts for critical datasets
- [ ] Implementar quality gates en pipelines
- [ ] Setup Data Docs / dashboards
- [ ] Define quality SLAs
- [ ] Implement quarantine pattern

### Advanced

- [ ] Automatic anomaly detection
- [ ] Historical quality metrics tracking
- [ ] Data lineage integration
- [ ] Custom expectations/rules
- [ ] ML-powered quality prediction

---

## Common Patterns

### Pattern 1: Staged Validation

```python
class StagedValidator:
    """Validation por etapas con diferente severidad."""

    stages = {
        'bronze': {  # Raw data - lax validation
            'severity': 'warning',
            'checks': ['schema', 'format']
        },
        'silver': {  # Cleaned data - strict validation
            'severity': 'error',
            'checks': ['schema', 'format', 'completeness', 'validity']
        },
        'gold': {  # Business data - very strict
            'severity': 'critical',
            'checks': ['schema', 'format', 'completeness', 'validity',
                      'uniqueness', 'business_rules']
        }
    }
```text

### Pattern 2: Progressive Rollout

```python
# Día 1: Warn only (no fails)
validate(df, mode='warn')

# Día 7: Fail con threshold alto
validate(df, mode='fail', threshold=0.80)  # 80% must pass

# Día 30: Fail estricto
validate(df, mode='fail', threshold=0.99)  # 99% must pass
```text

### Pattern 3: Data Quality Scoring

```python
def calculate_dq_score(df: pd.DataFrame) -> Dict:
    """Score multi-dimensional."""
    scores = {
        'completeness': completeness_score(df),
        'uniqueness': uniqueness_score(df),
        'validity': validity_score(df),
        'consistency': consistency_score(df),
        'timeliness': timeliness_score(df),
        'accuracy': accuracy_score(df)
    }

    # Weighted average
    weights = {
        'completeness': 0.20,
        'uniqueness': 0.15,
        'validity': 0.25,
        'consistency': 0.15,
        'timeliness': 0.15,
        'accuracy': 0.10
    }

    overall = sum(scores[dim] * weights[dim] for dim in scores)

    return {
        'scores': scores,
        'overall': overall,
        'grade': get_letter_grade(overall),
        'passed': overall >= 80.0
    }
```text

---

## Migration Guide

### From Manual Checks to Great Expectations

**Before (Manual):**

```python
# Scattered checks
assert df['id'].notna().all()
assert df['amount'].min() >= 0
if df.duplicated().any():
    raise ValueError("Duplicates found")
```

**After (Great Expectations):**

```python
validator = context.get_validator(...)

validator.expect_column_values_to_not_be_null("id")
validator.expect_column_values_to_be_between("amount", min_value=0)
validator.expect_compound_columns_to_be_unique(["id", "timestamp"])

results = validator.validate()
```text

**Benefits:**

- ✅ Reusable suites
- ✅ Auto-documentation
- ✅ Version control
- ✅ Historical tracking

---

## Troubleshooting

### Performance Issues

**Problem:** Great Expectations lento en large datasets

**Solutions:**

1. Use Spark backend:

   ```python
   datasource = context.sources.add_spark("my_spark_datasource")
   ```text

2. Sample data para profiling:

   ```python
   sample_df = df.sample(n=10000)
   profiler.build_suite(sample_df)
   ```

3. Disable expensive expectations:

   ```python
   # Evitar en datasets grandes:
   # - expect_column_values_to_be_in_set (si set es grande)
   # - expect_compound_columns_to_be_unique (costoso)
   ```text

### False Positives

**Problem:** Validations fail for legitimate edge cases

**Solution:** Use `mostly` parameter:

```python
validator.expect_column_values_to_not_be_null(
    "phone",
    mostly=0.95  # 95% deben ser no-null, 5% pueden ser null
)
```

### Schema Evolution

**Problem:** Schema changes rompen expectations

**Solution:** Version control + automated updates:

```python
# Detectar schema drift
old_schema = load_schema('v1.0')
new_schema = infer_schema(df)

if old_schema != new_schema:
    alert_data_steward()
    create_new_suite_version()
```text

---

## Future Trends

### 1. ML-Powered Data Quality

- **Automated expectation generation** usando ML
- **Anomaly prediction** basado en historical patterns
- **Smart sampling** para validaciones

### 2. Real-Time Data Quality

- **Streaming validation** (Kafka Streams, Flink)
- **Event-driven alerts**
- **Sub-second SLAs**

### 3. Data Contracts as Standard

- Industry-wide **contract schemas**
- **Automated SLA enforcement**
- **Self-service data products**

### 4. Integration with Data Mesh

- **Domain-specific quality rules**
- **Federated quality governance**
- **Quality as a service**

---

## Conclusion

The data quality ecosystem is maturing rapidly. **Great Expectations** is the most complete framework for most use cases. Complement it with:

- **Pandera** para schemas simples
- **PyDeequ** si ya tienes Spark
- **ydata-profiling** for exploration
- **DuckDB** para checks ad-hoc

**Next steps:**

1. Complete practical exercises in`exercises/`
2. Implementar quality gates en tu pipeline real
3. Compartir aprendizajes con tu equipo

---

## Quick Reference

### Essential Commands

```bash
# Great Expectations
great_expectations init
great_expectations suite new
great_expectations checkpoint new
great_expectations docs build

# Pandera
pandera schema infer --io-type csv data.csv > schema.py

# PyDeequ
# (Requiere PySpark session, ver theory/02-architecture.md)

# DuckDB
duckdb -c "SELECT * FROM 'data.parquet' WHERE col IS NULL"

# ydata-profiling
# (Ver theory/02-architecture.md o pypi.org/project/ydata-profiling)
```text

### Useful Links

- Great Expectations Docs: <https://docs.greatexpectations.io/>
- Pandera Docs: <https://pandera.readthedocs.io/>
- PyDeequ GitHub: <https://github.com/awslabs/python-deequ>
- DuckDB Docs: <https://duckdb.org/docs/>

---

**End of Theory Section**

➡️ **Next:** `exercises/`for hands-on practice
➡️ **Next:** `data/` para sample datasets
