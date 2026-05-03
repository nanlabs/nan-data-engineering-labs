# Herramientas y resources para Batch Processing

## 🛠️ Herramientas de Batch Processing

### 1. Apache Spark ⭐

**The de facto standard for distributed batch processing**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("BatchJob") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .getOrCreate()

df = spark.read.parquet("s3://bucket/data/")
result = df.groupBy("category").agg({"amount": "sum"})
result.write.parquet("s3://bucket/output/")
```

**features**:
- ✅ In-memory processing (100x faster que MapReduce)
- ✅ Lazy evaluation + query optimization
- ✅ Automatic fault tolerance
- ✅ APIs: Python, Scala, Java, R, SQL

**When to use**:
- Datasets > 100GB
- Procesamiento distribuido necesario
- Joins y aggregations complejas
- ML pipelines

**Ecosistema Spark**:
- **Spark SQL**: Queries SQL sobre DataFrames
- **Spark Streaming**: Micro-batch streaming
- **MLlib**: Machine learning
- **GraphX**: Graph processing

**Deployment**:
- Local mode (desarrollo)
- Standalone cluster
- YARN (Hadoop)
- Kubernetes
- Cloud-managed (EMR, Databricks, Dataproc)

### 2. Pandas (Single-Node)

**Para datasets que caben en memoria (~10GB)**

```python
import pandas as pd

# Read data
df = pd.read_parquet("data.parquet")

# Batch processing con chunking
chunk_size = 100000
for chunk in pd.read_csv("large_file.csv", chunksize=chunk_size):
    processed = transform(chunk)
    processed.to_parquet("output.parquet", mode="append")
```

**features**:
- ✅ Simple API
- ✅ Rich ecosystem
- ✅ Excelente para prototyping
- ❌ Single-machine (no distribuido)

**When to use**:
- Datasets < 10GB
- Rapid prototyping
- Single-machine suficiente
- Data science interactivo

**Extensiones**:
- **Dask**: Pandas-style API, distributed
- **Modin**: Drop-in replacement, parallelizado
- **Polars**: Rust-based, faster

### 3. Dask

**Pandas distribuido para datasets > RAM**

```python
import dask.dataframe as dd

# Dask DataFrame (lazy)
df = dd.read_parquet("s3://bucket/data/*.parquet")

# Operaciones como Pandas
result = df.groupby("category").amount.sum()

# Compute (ejecuta)
result_computed = result.compute()
```

**features**:
- ✅ Pandas-compatible API
- ✅ Escala a cluster
- ✅ Out-of-core processing
- ✅ Scheduler inteligente

**When to use**:
- Pandas code that does not scale
- Datasets 10GB - 10TB
- Quieres API familiar (Pandas)

### 4. Apache Beam

**Framework unificado batch + stream**

```python
import apache_beam as beam

with beam.Pipeline() as pipeline:
    (pipeline
     | "Read" >> beam.io.ReadFromText("input.txt")
     | "Parse" >> beam.Map(parse_line)
     | "Transform" >> beam.Map(transform)
     | "Write" >> beam.io.WriteToText("output.txt"))
```

**features**:
- ✅ Same code for batch and stream
- ✅ Portable (Spark, Flink, Dataflow)
- ✅ Windowing avanzado

**Runners**:
- DirectRunner (local)
- DataflowRunner (GCP)
- FlinkRunner
- SparkRunner

### 5. dbt (Data Build Tool)

**SQL-first transformation framework**

```sql
-- models/sales_summary.sql
{{ config(materialized='table') }}

SELECT
    date_trunc('day', order_date) as day,
    category,
    SUM(amount) as total_sales,
    COUNT(*) as num_orders
FROM {{ ref('orders') }}
WHERE status = 'completed'
GROUP BY 1, 2
```

**features**:
- ✅ SQL-based transformations
- ✅ Lineage tracking
- ✅ Testing framework
- ✅ Documentation auto-generada

**When to use**:
- Data warehouse transformations
- Analytics engineering
- SQL-first approach
- Data quality tests

---

## ☁️ Cloud Services para Batch

### AWS

#### 1. AWS EMR (Elastic MapReduce)

**Managed Spark/Hadoop cluster**

```bash
# Launch EMR cluster
aws emr create-cluster \
  --name "BatchCluster" \
  --release-label emr-6.15.0 \
  --applications Name=Spark Name=Hadoop \
  --instance-type m5.xlarge \
  --instance-count 3 \
  --use-default-roles
```

**features**:
- ✅ Managed Spark, Hive, Presto
- ✅ Auto-scaling
- ✅ S3 integration
- 💰 Pay per usage

#### 2. AWS Glue

**Serverless ETL service**

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

glueContext = GlueContext(SparkContext.getOrCreate())
spark = glueContext.spark_session

# Read from Glue Catalog
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="mydb",
    table_name="orders"
)

# Transform
df = datasource.toDF()
transformed = df.filter(df.amount > 100)

# Write
glueContext.write_dynamic_frame.from_options(
    frame=transformed,
    connection_type="s3",
    connection_options={"path": "s3://bucket/output/"}
)
```

**features**:
- ✅ Serverless (no cluster management)
- ✅ Glue Catalog (metastore)
- ✅ Auto-scaling
- ✅ Pay per DPU-hour

#### 3. AWS Batch

**Managed batch computing**

```python
# Submit batch job
import boto3

batch = boto3.client('batch')

response = batch.submit_job(
    jobName='daily-processing',
    jobQueue='batch-queue',
    jobDefinition='batch-job-def',
    parameters={
        'date': '2024-03-07'
    }
)
```

**When to use**:
- Docker-based jobs
- HPC workloads
- Non-Spark batch jobs

### GCP

#### 1. Cloud Dataproc

**Managed Spark/Hadoop cluster**

```bash
# Create cluster
gcloud dataproc clusters create batch-cluster \
  --region=us-central1 \
  --num-workers=2 \
  --worker-machine-type=n1-standard-4

# Submit job
gcloud dataproc jobs submit pyspark script.py \
  --cluster=batch-cluster \
  --region=us-central1
```

#### 2. Cloud Dataflow

**Managed Apache Beam**

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(
    runner='DataflowRunner',
    project='my-project',
    region='us-central1',
    temp_location='gs://bucket/temp'
)

with beam.Pipeline(options=options) as pipeline:
    (pipeline
     | beam.io.ReadFromText('gs://bucket/input/*')
     | beam.Map(process)
     | beam.io.WriteToText('gs://bucket/output/'))
```

**features**:
- ✅ Unified batch + stream
- ✅ Auto-scaling
- ✅ Streaming SQL

### Azure

#### 1. Azure Synapse Analytics

**Integrated analytics service**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Batch").getOrCreate()

df = spark.read.parquet("abfss://container@account.dfs.core.windows.net/data/")
result = df.groupBy("category").sum("amount")
result.write.parquet("abfss://container@account.dfs.core.windows.net/output/")
```

#### 2. Azure Databricks

**Managed Spark + ML platform**

```python
# Databricks notebook
df = spark.read.format("delta").load("/mnt/data/")
df_transformed = df.filter(df.amount > 100)
df_transformed.write.format("delta").mode("overwrite").save("/mnt/output/")
```

---

## 📚 Useful Libraries

### Data Processing

```python
# pandas: Data manipulation
import pandas as pd

# pyarrow: Fast parquet read/write
import pyarrow.parquet as pq

# polars: Rust-based fast DataFrame
import polars as pl

# dask: Distributed pandas
import dask.dataframe as dd
```

### Data Quality

```python
# great_expectations: Data validation
import great_expectations as gx

context = gx.get_context()
suite = context.get_expectation_suite("sales_data")

# Add expectations
suite.expect_column_values_to_not_be_null("user_id")
suite.expect_column_values_to_be_between("amount", 0, 10000)

# Validate
results = context.run_checkpoint(checkpoint_name="daily_check")
```

### Monitoring

```python
# structlog: Structured logging
import structlog

logger = structlog.get_logger()

logger.info("batch_started",
           date="2024-03-07",
           records=1000000)

# tqdm: Progress bars
from tqdm import tqdm

for chunk in tqdm(chunks, desc="Processing"):
    process(chunk)
```

### Schema Management

```python
# pydantic: Data validation
from pydantic import BaseModel, validator

class Transaction(BaseModel):
    id: int
    amount: float
    user_id: str

    @validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('amount must be positive')
        return v

# Validate
transaction = Transaction(**data)
```

---

## 🎓 resources de Aprendizaje

### Official Documentation

**Apache Spark**:
- 📖 [Spark Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html)
- 📖 [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- 📖 [PySpark API](https://spark.apache.org/docs/latest/api/python/)

**Pandas**:
- 📖 [User Guide](https://pandas.pydata.org/docs/user_guide/index.html)
- 📖 [10 Minutes to pandas](https://pandas.pydata.org/docs/user_guide/10min.html)

**Dask**:
- 📖 [Best Practices](https://docs.dask.org/en/latest/best-practices.html)
- 📖 [DataFrame API](https://docs.dask.org/en/latest/dataframe.html)

### Libros

📚 **"Spark: The Definitive Guide"** - Matei Zaharia & Bill Chambers
El libro definitivo de los creadores de Spark

📚 **"Learning Spark"** - Jules Damji et al.
Handy to get started with Spark

📚 **"High Performance Spark"** - Holden Karau
Advanced Spark Optimization

📚 **"Data Pipelines Pocket Reference"** - James Densmore
Quick reference para data engineering

### Cursos

🎓 **Databricks Academy**
- Apache Spark Programming with Databricks
- Advanced Apache Spark
- Delta Lake

🎓 **Coursera**
- Big Data Specialization (UC San Diego)
- Data Engineering with Google Cloud

🎓 **edX**
- Big Data Analysis with Apache Spark (Berkeley)

### Blogs & Comunidades

🌐 **The Databricks Blog**
https://databricks.com/blog

🌐 **Netflix Tech Blog**
https://netflixtechblog.com/ (Data Platform posts)

🌐 **Airbnb Engineering**
https://medium.com/airbnb-engineering

🌐 **r/dataengineering** (Reddit)
Community Q&A

---

## 🔧 Development Tools

### IDEs

**Jupyter Notebooks**:
```bash
pip install jupyterlab
jupyter lab
```

**VS Code**:
- Python extension
- Jupyter extension
- Remote SSH para clusters

**DataSpell** (JetBrains):
- IDE especializado para data

### Development Workflow

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Develop locally
python batch_job.py --date 2024-03-07 --env local

# 3. Test
pytest tests/

# 4. Submit to cluster
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --num-executors 10 \
  --executor-memory 4g \
  batch_job.py --date 2024-03-07
```

### Debugging

```python
# Local Spark con UI
spark = SparkSession.builder \
    .master("local[*]") \
    .config("spark.ui.port", "4040") \
    .getOrCreate()

# Ver Spark UI en http://localhost:4040
```

**Spark UI Tabs**:
- **Jobs**: Jobs ejecutados
- **Stages**: Stages y tasks
- **Storage**: Cached RDDs/DataFrames
- **Environment**: Configuration
- **Executors**: Estado de executors
- **SQL**: Query execution plans

---

## 💡 Tips & Tricks

### 1. Use Parquet con Compression

```python
# ✅ Bueno
df.write.parquet("output.parquet", compression="snappy")

# ❌ Malo
df.to_csv("output.csv")  # 10x más grande y lento
```

**Comparison**:
- CSV: 10 GB, 20 min read
- Parquet (snappy): 2 GB, 2 min read

### 2. Partition Tuning

```python
# Regla: 2-4 partitions por CPU core

# Cluster con 10 nodes × 4 cores = 40 cores
# → 80-160 partitions óptimo

df.repartition(100)
```

### 3. Broadcast Small Tables

```python
from pyspark.sql.functions import broadcast

# Broadcast tabla < 10MB
result = large_df.join(broadcast(small_df), "key")
```

**Speedup**: 10-100x for small joins

### 4. Lazy Evaluation

```python
# ✅ Spark optimiza todo el plan
df_filtered = df.filter(df.amount > 100)
df_selected = df_filtered.select("id", "amount")
df_grouped = df_selected.groupBy("category").sum()
result = df_grouped.collect()  # Ejecuta todo optimizado

# vs

# ❌ No use collect() en medio del pipeline
df_filtered = df.filter(df.amount > 100).collect()  # Trae todo a driver
df_selected = pd.DataFrame(df_filtered).select("id", "amount")  # Ahora es Pandas
```

### 5. Monitoring

```python
# Track metrics
import time

start = time.time()
result = process_batch(df)
duration = time.time() - start

logger.info({
    "duration_seconds": duration,
    "records_processed": result.count(),
    "throughput": result.count() / duration
})
```

---

## 📊 Performance Benchmarks

### Spark vs Pandas

**Dataset**: 100M records, 5GB

| Operation | Pandas | Spark (10 nodes) | Speedup |
|-----------|--------|------------------|---------|
| Read CSV  | 180s   | 12s              | 15x     |
| Filter    | 45s    | 3s               | 15x     |
| GroupBy   | 120s   | 8s               | 15x     |
| Join      | 300s   | 15s              | 20x     |

### Parquet vs CSV

**Dataset**: 1GB

| Format | Size | Write Time | Read Time |
|--------|------|------------|-----------|
| CSV    | 1.0 GB | 30s      | 45s       |
| Parquet (no compress) | 0.8 GB | 15s | 10s |
| Parquet (snappy) | 0.3 GB | 18s | 8s |

**Winner**: Parquet con Snappy compression ⭐

---

## 🎯 Checklist de Batch Job

### Design
- [ ] Definir input/output schemas
- [ ] Design partitioning strategy
- [ ] Planificar error handling
- [ ] Documentar dependencies

### Implementation
- [ ] Usar formato columnr (Parquet)
- [ ] Implementar idempotencia
- [ ] Agregar logging estructurado
- [ ] Configurar checkpointing

### Testing
- [ ] Unit tests para transformations
- [ ] Integration tests end-to-end
- [ ] Performance tests con dataset realista
- [ ] Validar data quality

### Deployment
- [ ] Configurar cluster resources
- [ ] Setup monitoring & alerting
- [ ] Documentar runbook
- [ ] Planificar rollback strategy

### Operations
- [ ] Monitor duration y throughput
- [ ] Track data quality metrics
- [ ] Review Spark UI periodically
- [ ] Optimize based on metrics

---

Now you are ready for the practical exercises. Starts with [Exercise 01](../exercises/01-batch-basics/).
