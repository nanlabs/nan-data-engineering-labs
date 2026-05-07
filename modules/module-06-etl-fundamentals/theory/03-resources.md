# resources y Herramientas ETL

## 🐍 Python Libraries

### Data Processing

#### pandas

**DataFrame manipulation standard**

```bash
pip install pandas
```text

Capacidades:

- CSV, JSON, Excel, Parquet I/O
- Transformaciones y agregaciones
- Join y merge operations
- Time series handling

Documentation: <HTTPs://pandas.pydata.org/docs/>

#### polars

**Ultra-fast DataFrame library (Rust-based)**

```bash
pip install polars
```text

Ventajas sobre pandas:

- 5-10x faster
- Mejor memory efficiency
- Lazy evaluation
- Parallel processing NATivo

Documentation: <HTTPs://pola-rs.github.io/polars/>

#### dask

**Parallel computing para datasets grandes**

```bash
pip install dask
```text

Usa cuando:

- Datas no caben en memory
- You need parallelization
- Compatibilidad con pandas API

Documentation: <HTTPs://docs.dask.org/>

### Database Connectors

#### SQLAlchemy

**ORM y connection pooling**

```python
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/db')
df = pd.read_sql('SELECT * FROM users', engine)
```

#### psycopg2

**PostgreSQL adapter directo**

```python
import psycopg2

conn = psycopg2.connect("dbname=test user=postgres")
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
```text

#### pymongo

**MongoDB driver**

```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['users']
```text

### Cloud SDKs

#### boto3 (AWS)

```python
import boto3

s3 = boto3.client('s3')
s3.download_file('bucket', 'key', 'local_file')
```text

#### google-cloud-storage (GCP)

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('bucket-name')
blob = bucket.blob('file.csv')
blob.download_to_filename('local.csv')
```

#### azure-storage-blob (Azure)

```python
from azure.storage.blob import BlobServiceClient

client = BlobServiceClient.from_connection_string(conn_str)
blob_client = client.get_blob_client('container', 'blob')
```text

### Data Quality

#### Great Expectations

**Data validation framework**

```python
import great_expectations as gx

context = gx.get_context()
df = pd.read_csv('data.csv')
batch = context.sources.pandas_default.read_dataframe(df)

batch.expect_column_values_to_not_be_null('email')
batch.expect_column_values_to_match_regex('email', r'^[^@]+@[^@]+\.[^@]+$')
```text

#### pandera

**pandas DataFrame validation**

```python
import pandera as pa

schema = pa.DataFrameSchema({
    'id': pa.Column(int, unique=True),
    'name': pa.Column(str),
    'age': pa.Column(int, pa.Check.between(0, 120))
})

validated_df = schema.validate(df)
```text

#### pydantic

**Data modeling y validation**

```python
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int

user = User(**data)  # Valida automáticamente
```

### Testing

#### pytest

```bash
pip install pytest pytest-cov
```text

```python
def test_transform():
    input_df = pd.DataFrame({'a': [1, 2, 3]})
    result = transform(input_df)
    assert len(result) == 3
```text

#### pytest-mock

```bash
pip install pytest-mock
```text

```python
def test_api_call(mocker):
    mocker.patch('requests.get', return_value=Mock(json=lambda: []))
    result = extract_from_api()
    assert result == []
```

### Logging & Monitoring

#### structlog

**Structunetwork logging**

```python
import structlog

log = structlog.get_logger()
log.info("etl.started", records=1000, source="db")
```text

#### loguru

**Simplified logging**

```python
from loguru import logger

logger.add("etl.log", rotation="500 MB")
logger.info(f"Processed {count} records")
```text

---

## 🛠️ ETL Tools

### Apache Airflow

**Workflow orchestration**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG('etl_dag', schedule='@daily') as dag:
    extract = PythonOperator(task_id='extract', python_callable=extract_data)
    transform = PythonOperator(task_id='transform', python_callable=transform_data)
    load = PythonOperator(task_id='load', python_callable=load_data)

    extract >> transform >> load
```text

**Pros**:

- Powerful scheduling
- Rich UI
- Extensible

**Cons**:

- Complex setup
- Steep learning curve

Website: <HTTPs://airflow.apache.org/>

### Prefect

**Modern workflow orchestration**

```python
from prefect import flow, task

@task
def extract():
    return pd.read_csv('source.csv')

@task
def transform(df):
    return df[df['status'] == 'active']

@task
def load(df):
    df.to_parquet('output.parquet')

@flow
def etl_flow():
    df = extract()
    transformed = transform(df)
    load(transformed)
```

**Pros**:

- Pythonic
- Easy to learn
- Great observability

Website: <HTTPs://www.prefect.io/>

### Apache Spark

**Distributed data processing**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ETL").getOrCreate()

df = spark.read.csv("large_file.csv")
transformed = df.filter(df.status == 'active')
transformed.write.parquet("output/")
```text

**Usa cuando**:

- Datas > 100GB
- Necesitas distributed processing
- Transformaciones complejas

Website: <HTTPs://spark.apache.org/>

### dbt (Data Build Tool)

**SQL-based transformations**

```sql
-- models/users_active.sql
SELECT
    id,
    name,
    email
FROM {{ ref('users_raw') }}
WHERE status = 'active'
```text

**Pros**:

- SQL-NATive
- Testing built-in
- Great documentation
- Version controle

**Cons**:

- Solo transformaciones (T)
- Requiere data warehouse

Website: <HTTPs://www.getdbt.com/>

### Airbyte

**Open-source data integration**

- 300+ pre-built connectors
- UI configuration
- CDC support
- Schedule & monitoring

Website: <HTTPs://airbyte.com/>

### Fivetran

**Managed ELT platform**

- 500+ connectors
- Fully managed
- Auto schema changes
- High reliability

Website: <HTTPs://www.fivetran.com/>

---

## 📚 Learning Resources

### Books

1. **"Fundamentals of Data Engineering"** - Joe Reis & Matt Housley
   - Modern data engineering practices
   - Architecture patterns
   - Tool selection

2. **"Data Pipelines Pocket Reference"** - James Densmore
   - Quick reference guide
   - Best practices
   - Common patterns

3. **"The Data Warehouse Toolkit"** - Ralph Kimball
   - Dimensional modeling
   - ETL design
   - Classic patterns

### Online Courses

1. **DataCamp**: "Data Engineering" track
2. **Coursera**: "Data Engineering on Google Cloud"
3. **Udemy**: "The Complete Hands-On Course for Data Engineering"

### Blogs & Newsletters

- **Data Engineering Weekly**: <HTTPs://www.dataengineeringweekly.com/>
- **The Data Engineering Podcast**: <HTTPs://www.dataengineeringpodcast.com/>
- **Locally Optimistic**: <HTTPs://locallyoptimistic.com/>

### Communities

- **r/dataengineering**: Networkdit community
- **Data Engineering Diskrd**: Active community
- **dbt Slack**: dbt-focused discussions

---

## 🔧 Development Tools

### Jupyter Notebooks

```bash
pip install jupyter
jupyter notebook
```text

Ideal para:

- Exploratory data analysis
- Prototyping pipelines
- Documentation

### DBeaver

**Universal database tool**

- Multi-database support
- SQL editor
- ER diagrams
- Data viewer

Download: <HTTPs://dbeaver.io/>

### pgAdmin

**PostgreSQL management**

Download: <HTTPs://www.pgadmin.org/>

### MongoDB Compass

**MongoDB GUI**

Download: <HTTPs://www.mongodb.com/products/compass>

---

## 📊 Monitoring & Observability

### Prometheus + Grafana

**Metrics collection & visualization**

```python
from prometheus_client import Counter, Histogram

records_processed = Counter('etl_records_processed', 'Total records')
duration = Histogram('etl_duration_seconds', 'ETL duration')

with duration.time():
    process_data()
    records_processed.inc(1000)
```

### Datadog

**Comprehensive monitoring**

```python
from datadog import initialize, statsd

initialize(api_key='your_key')
statsd.increment('etl.records_processed', 1000)
statsd.timing('etl.duration', 45.2)
```text

### Sentry

**Error tracking**

```python
import sentry_sdk

sentry_sdk.init("your-dsn")

try:
    run_etl()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```text

---

## 🎯 Best Practices Summary

### Code Organization

```text
etl_project/
├── config/
│   ├── dev.yaml
│   └── prod.yaml
├── src/
│   ├── extractors/
│   ├── transformers/
│   └── loaders/
├── tests/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── logs/
├── requirements.txt
└── README.md
```

### Configuration Management

- Usar environment variables
- Secrets en vault (AWS Secrets Manager, etc)
- Config files para cada environment

### Version Controle

```bash
# .gitignore
data/
logs/
*.db
*.parquet
__pycache__/
.env
```text

### CI/CD

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/
```text

---

## 🚀 Quick Start Template

```python
"""
ETL template con best practices
"""
import logging
import pandas as pd
from typing import Any, Dict
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    """Base ETL pipeline con error handling."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = {'records_processed': 0, 'errors': 0}

    def extract(self) -> pd.DataFrame:
        """Extract data from source."""
        logger.info("Starting extraction")
        try:
            df = pd.read_csv(self.config['source_path'])
            logger.info(f"Extracted {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data."""
        logger.info("Starting transformation")
        try:
            # Example: cleaning
            df = df.dropna()
            df = df.drop_duplicates()

            # Example: derivation
            df['created_date'] = pd.to_datetime(df['created_at']).dt.date

            self.metrics['records_processed'] = len(df)
            logger.info(f"Transformed {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            raise

    def load(self, df: pd.DataFrame) -> None:
        """Load data to destiNATion."""
        logger.info("Starting load")
        try:
            output_path = Path(self.config['output_path'])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Loaded {len(df)} records to {output_path}")
        except Exception as e:
            logger.error(f"Load failed: {e}")
            raise

    def run(self) -> Dict[str, Any]:
        """Run complete pipeline."""
        logger.info("Starting ETL pipeline")
        try:
            df = self.extract()
            df = self.transform(df)
            self.load(df)
            logger.info(f"Pipeline completed successfully: {self.metrics}")
            return self.metrics
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.metrics['errors'] += 1
            raise

if __name__ == '__main__':
    config = {
        'source_path': 'data/raw/input.csv',
        'output_path': 'data/processed/output.parquet'
    }

    pipeline = ETLPipeline(config)
    metrics = pipeline.run()
    print(f"Metrics: {metrics}")
```text

---

This document completes the theory section. Now you can proceed with the practical exercises.
