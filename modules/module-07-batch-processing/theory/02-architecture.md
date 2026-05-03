# Arquitectura de Batch Processing

## 🏗️ Arquitectura de pipeline Batch

### Basic Component

```
┌────────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐
│   Source   │ → │  Extract  │ → │ Transform │ → │  Load   │
└────────────┘    └───────────┘    └──────────┘    └─────────┘
   Database         Read data       Process         Write to
   Files            Validate        Clean           Data Lake
   APIs             Filter          Aggregate       Warehouse
```

### Multi-Stage pipeline

```
┌─────────┐
│ Source  │
└────┬────┘
     │
┌────▼────────┐
│  Stage 1    │  Raw Data Ingestion
│  Extract    │  - Read from sources
└────┬────────┘  - Basic validation
     │
┌────▼────────┐
│  Stage 2    │  Data Cleaning
│  Clean      │  - Remove duplicates
└────┬────────┘  - Handle nulls
     │
┌────▼────────┐
│  Stage 3    │  Transformation
│  Transform  │  - Business logic
└────┬────────┘  - Aggregations
     │
┌────▼────────┐
│  Stage 4    │  Load
│  Load       │  - Write to target
└─────────────┘  - Update metrics
```

---

## 🚀 Apache Spark for Batch Processing

### Why Spark?

**Spark** is the leading framework for distributed batch processing:

✅ **Distributed**: Procesa TB de datos en cluster
✅ **In-Memory**: 100x faster than MapReduce
✅ **Lazy Evaluation**: Optimiza execution plans
✅ **Fault Tolerant**: Automatic recovery

### Spark Architecture

```
┌─────────────────┐
│  Driver Program │
│   (SparkContext)│
└────────┬────────┘
         │
    ┌────┴────┐
    │ Cluster │
    │ Manager │
    └────┬────┘
         │
    ┌────┴────────────────┐
    │                     │
┌───▼────┐          ┌────▼───┐
│Executor│          │Executor│
│ Task 1 │          │ Task 3 │
│ Task 2 │          │ Task 4 │
└────────┘          └────────┘
```

**Componentes**:
- **Driver**: Coordina el trabajo
- **Executors**: Ejecutan tasks
- **Cluster Manager**: Gestiona resources (YARN, K8s, Mesos)

### Spark Core Concepts

#### RDD (Resilient Distributed Dataset)

```python
from pyspark import SparkContext

sc = SparkContext("local", "app")

# Create RDD
rdd = sc.parallelize([1, 2, 3, 4, 5])

# Transformations (lazy)
rdd2 = rdd.map(lambda x: x * 2)
rdd3 = rdd2.filter(lambda x: x > 5)

# Action (triggers computation)
result = rdd3.collect()  # [6, 8, 10]
```

**features RDD**:
- Immutable
- Lazily evaluated
- Fault-tolerant (lineage)

#### DataFrame API

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("batch").getOrCreate()

# Read data
df = spark.read.parquet("data/")

# Transformations (lazy)
df_filtered = df.filter(df.amount > 100)
df_grouped = df_filtered.groupBy("category").sum("amount")

# Action (triggers)
df_grouped.show()
```

**Ventajas DataFrame**:
- Simpler API than RDD
- Automatic optimizations (Catalyst)
- Schema enforcement

#### Dataset API (Typed)

```python
from pyspark.sql import Row

# Define schema
case class Transaction(id: Int, amount: Double, category: String)

# Create Dataset (Scala/Java)
ds = spark.read.json("data.json").as[Transaction]

# Type-safe operations
ds.filter(_.amount > 100).map(_.category)
```

**Nota**: Python usa DataFrame (no tiene Dataset tipado)

---

## ⚡ Spark Transformations vs Actions

### Transformations (Lazy)

No ejecutan inmediatamente, solo construyen execution plan:

```python
# Todas estas son lazy
df2 = df.filter(df.age > 18)           # Filter rows
df3 = df.select("name", "age")         # Select columns
df4 = df.withColumn("age2", df.age * 2) # Add column
df5 = df.groupBy("country").count()    # Group & aggregate
df6 = df.join(other, "id")             # Join datasets
```

**Common Transformations**:
- `filter()`, `where()`
- `select()`, `drop()`
- `withColumn()`, `withColumnRenamed()`
- `groupBy()`, `agg()`
- `join()`
- `orderBy()`, `sort()`
- `distinct()`
- `union()`

### Actions (Eager)

Trigger computation y retornan resultados:

```python
# Estas ejecutan el job
df.show()                    # Display rows
df.count()                   # Count rows
df.collect()                 # Return all rows to driver
df.take(10)                  # Return first 10 rows
df.first()                   # Return first row
df.write.parquet("output/")  # Write to storage
```

**Common Actions**:
- `show()`, `display()`
- `count()`
- `collect()`, `take()`, `first()`
- `write()`, `save()`
- `foreach()`

### Execution Plan

```python
# Ver execution plan
df.explain()

# Ver plan optimizado
df.explain(True)
```

---

## 🎯 Batch pipeline Architectures

### 1. Lambda Architecture

```
              ┌──────────────┐
              │ Data Source  │
              └──────┬───────┘
                     │
         ┌───────────┴────────────┐
         │                        │
    ┌────▼─────┐           ┌─────▼─────┐
    │  Batch   │           │  Stream   │
    │  Layer   │           │  Layer    │
    │ (Spark)  │           │  (Kafka)  │
    └────┬─────┘           └─────┬─────┘
         │                       │
         │   ┌─────────────┐     │
         └──►│   Serving   │◄────┘
             │    Layer    │
             └─────────────┘
```

**features**:
- **Batch Layer**: Processes the entire history (slow, accurate)
- **Speed Layer**: Procesa datos recientes (fast, approximate)
- **Serving Layer**: Combina batch + speed views

**Ventajas**:
- ✅ Fault tolerant
- ✅ Accurate (batch) + Fast (speed)

**Desventajas**:
- ❌ Logic duplication (batch + stream)
- ❌ Complejo de mantener

### 2. Kappa Architecture (Simplified Lambda)

```
┌──────────────┐
│ Data Source  │
└──────┬───────┘
       │
  ┌────▼─────┐
  │  Stream  │
  │  Layer   │
  │  (Kafka) │
  └────┬─────┘
       │
┌──────▼───────┐
│   Serving    │
│    Layer     │
└──────────────┘
```

**Philosophy**: Everything is stream (batch = bounded stream)

**Ventajas**:
- ✅ Single code path
- ✅ Simpler than Lambda

**Desventajas**:
- ❌ Requiere streaming infrastructure

### 3. Batch-Only Architecture (Simple)

```
┌──────────────┐
│ Data Source  │
└──────┬───────┘
       │
  ┌────▼─────┐
  │  Batch   │
  │  Layer   │
  │ (Spark)  │
  └────┬─────┘
       │
┌──────▼───────┐
│ Data Lake/   │
│ Warehouse    │
└──────────────┘
```

**features**:
- Solo batch processing
- latency alta (hours)
- Simple and economical

**When to use**:
- No necesitas real-time
- Budget limitado
- small team

---

## 📦 Batch Processing Patterns

### Pattern 1: Map-Reduce

```python
# Map phase: Transform cada elemento
mapped = rdd.map(lambda x: (x.category, x.amount))

# Reduce phase: Aggregate por key
reduced = mapped.reduceByKey(lambda a, b: a + b)
```

**Uso**: Aggregations distribuidas

### Pattern 2: Map-Filter-Reduce

```python
result = (rdd
    .map(lambda x: (x.category, x.amount))
    .filter(lambda x: x[1] > 100)  # Filter después de map
    .reduceByKey(lambda a, b: a + b))
```

### Pattern 3: Join Pattern

```python
# Join dos datasets
users = spark.read.parquet("users/")
orders = spark.read.parquet("orders/")

# Inner join
result = orders.join(users, orders.user_id == users.id)

# Left join
result = orders.join(users, "user_id", "left")
```

**Optimizaciones**:
- Broadcast join for small tables
- Partition pruning
- Predicate pushdown

### Pattern 4: Window Functions

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank

# Define ventana
window = Window.partitionBy("category").orderBy(desc("amount"))

# Aplica window function
df_ranked = df.withColumn("rank", rank().over(window))

# Top N por categoría
top_per_category = df_ranked.filter(col("rank") <= 10)
```

**Uso**: Ranking, running totals, moving averages

---

## 🔧 Batch Job Optimization

### 1. Partitioning

```python
# Write partitioned
df.write.partitionBy("year", "month").parquet("data/")

# Read with partition pruning
df = spark.read.parquet("data/").filter("year = 2024 AND month = 3")
```

**Beneficio**: Lee solo particiones relevantes

### 2. Caching

```python
# Cache dataset usado múltiples veces
df_cached = df.filter(df.amount > 100).cache()

# Múltiples acciones sobre cached data
count = df_cached.count()
sum_amount = df_cached.agg({"amount": "sum"}).collect()

# Liberar memoria
df_cached.unpersist()
```

**When to search**:
- Dataset usado > 1 vez
- After expensive transformations
- Before multiple actions

### 3. Broadcast Join

```python
from pyspark.sql.functions import broadcast

# Small table (< 10MB)
small_df = spark.read.parquet("categories/")

# Broadcast join (evita shuffle)
result = large_df.join(broadcast(small_df), "category_id")
```

**Benefit**: 10-100x faster for joins with small tables

### 4. Repartitioning

```python
# Repartition para mejor paralelización
df_repart = df.repartition(200)  # 200 partitions

# Coalesce para reducir particiones (no shuffle)
df_coal = df.coalesce(10)
```

**Regla**: 2-4 partitions por core

### 5. Predicate Pushdown

```python
# ✅ Filter antes de join
df1_filtered = df1.filter(df1.year == 2024)
df2_filtered = df2.filter(df2.amount > 100)
result = df1_filtered.join(df2_filtered, "id")

# ❌ Filter después de join (más lento)
result = df1.join(df2, "id").filter(
    (col("year") == 2024) & (col("amount") > 100)
)
```

---

## 📊 Batch Job Monitoring

### Key Metrics

```python
import time
from datetime import datetime

def monitor_batch_job():
    start_time = time.time()
    start_dt = datetime.now()

    # Process
    result = process_batch(df)

    # Métricas
    duration = time.time() - start_time
    records_processed = result.count()
    throughput = records_processed / duration

    # Log metrics
    metrics = {
        'timestamp': start_dt.isoformat(),
        'duration_seconds': duration,
        'records_processed': records_processed,
        'throughput_records_per_sec': throughput,
        'status': 'SUCCESS'
    }

    log_metrics(metrics)
    return result
```

**Metrics to monitor**:
- ⏱️ Duration
- 📊 Records processed
- 🚀 throughput (records/sec)
- 💾 Data volume (GB)
- ⚠️ Error rate
- 💰 Cost

### Alerting

```python
def process_with_alerts(df):
    try:
        result = process_batch(df)

        # Check SLA
        if duration > SLA_THRESHOLD:
            alert("Batch job exceeded SLA", severity="WARNING")

        return result

    except Exception as e:
        alert(f"Batch job failed: {e}", severity="CRITICAL")
        raise
```

---

## 🎯 Best Practices

### 1. Design for Failure

```python
def resilient_batch():
    try:
        # Intenta procesar
        result = process_batch()

        # Valida resultado
        if not validate(result):
            raise ValidationError("Data quality check failed")

        return result

    except Exception as e:
        # Log error
        logger.error(f"Batch failed: {e}")

        # Cleanup
        cleanup_partial_output()

        # Re-raise para alerting
        raise
```

### 2. Usa Checkpointing

```python
def batch_with_checkpoint(partitions):
    checkpoint_file = "checkpoint.json"

    # Load checkpoint
    completed = load_checkpoint(checkpoint_file)

    for partition in partitions:
        if partition in completed:
            continue  # Skip ya procesadas

        process_partition(partition)

        # Save checkpoint
        completed.add(partition)
        save_checkpoint(checkpoint_file, completed)
```

### 3. Implementa Idempotencia

```python
def idempotent_write(df, date):
    # Output path incluye fecha
    output_path = f"data/year={date.year}/month={date.month}/day={date.day}/"

    # Overwrite partition (garantiza idempotencia)
    df.write.mode("overwrite").parquet(output_path)
```

### 4. Valida Inputs y Outputs

```python
def validated_batch(input_path, output_path):
    # Valida input existe
    if not input_exists(input_path):
        raise InputError(f"Input not found: {input_path}")

    # Process
    df = spark.read.parquet(input_path)
    result = transform(df)

    # Valida output
    assert result.count() > 0, "Empty output"
    assert not result.filter(col("id").isNull()).count(), "Null IDs"

    # Write
    result.write.parquet(output_path)
```

### 5. Documenta Dependencies

```yaml
# batch_job.yaml
job: daily_sales_report
schedule: "0 2 * * *"  # 2am daily
dependencies:
  - raw_sales_data
  - customer_master
outputs:
  - sales_summary
  - customer_aggregates
sla_hours: 4
```

---

Continue with [03-resources.md](./03-resources.md) for tools and resources.
