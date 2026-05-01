# Hints - Ejercicio 02: Medallion Architecture

## Bronze Layer

<details>
<summary>Hint 1: Leer JSON</summary>

```python
df = spark.read.json("../../../data/raw/transactions.json")
```
</details>

<details>
<summary>Hint 2: Agregar metadata</summary>

```python
from pyspark.sql.functions import current_timestamp, lit, to_date, col

df_bronze = df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_file", lit("transactions.json")) \
    .withColumn("ingestion_date", to_date(col("ingestion_timestamp")))
```
</details>

<details>
<summary>Hint 3: Guardar Bronze</summary>

```python
df_bronze.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("ingestion_date") \
    .save("s3a://bronze/transactions_medallion")
```
</details>

## Silver Layer

<details>
<summary>Hint 1: Deduplicar</summary>

```python
df_dedup = df.dropDuplicates(["transaction_id"])
```
</details>

<details>
<summary>Hint 2: Filter invalid</summary>

```python
df_valid = df.filter(
    (col("amount").isNotNull()) & 
    (col("amount") > 0) & 
    (col("timestamp").isNotNull())
)
```
</details>

<details>
<summary>Hint 3: Normalizar</summary>

```python
df_normalized = df \
    .withColumn("status", lower(trim(col("status")))) \
    .withColumn("currency", upper(trim(col("currency"))))
```
</details>

## Gold Layer

<details>
<summary>Hint 1: Basic Aggregation</summary>

```python
df_gold = df.groupBy("date", "country").agg(
    count("*").alias("total_transactions"),
    sum("amount").alias("total_amount"),
    avg("amount").alias("avg_amount")
)
```
</details>

<details>
<summary>Hint 2: Metrics by status</summary>

```python
from pyspark.sql.functions import when

.agg(
    count(when(col("status") == "completed", 1)).alias("num_completed"),
    count(when(col("status") == "failed", 1)).alias("num_failed")
)
```
</details>

<details>
<summary>Hint 3: Percentiles</summary>

```python
from pyspark.sql.functions import expr

.agg(
    expr("percentile_approx(amount, 0.5)").alias("p50_amount"),
    expr("percentile_approx(amount, 0.9)").alias("p90_amount")
)
```
</details>
