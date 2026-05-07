# 💡 Hints - Exercise 01: Delta Basics

this archivo contiene pistas progresivas for helprte to completar el exercise. **Intenta resolver cada tarea without mirar las pistas primero**. if te atascas, revela las pistas gradualmente.

---

## 🎯 Tarea 1: Crear table Delta

### Hint 1: Configurar SparkSession with Delta

<details>
<summary>Click for revelar Hint 1</summary>

for configurar Spark with Delta Lake, necesitas:

```python
from delta import configure_spark_with_delta_pIP

builder = SparkSession.builder \
    .appName("Mi App") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pIP(builder).getOrCreate()
```text

</details>

### Hint 2: Read JSON with limit

<details>
<summary>Click for revelar Hint 2</summary>

for leer only las primeras 10,000 rows:

```python
df = spark.read.json("path/to/file.json").limit(10000)
```text

</details>

### Hint 3: Convertir timestamp

<details>
<summary>Click for revelar Hint 3</summary>

The timestamp field comes as to string. Convert it:

```python
from pyspark.sql.functions import to_timestamp

df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
```text

Or if you use specific format:

```python
df = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
```

</details>

### Hint 4: Add ingestion date

<details>
<summary>Click for revelar Hint 4</summary>

Usa `current_date()` for agregar la fecha actual:

```python
from pyspark.sql.functions import current_date

df = df.withColumn("ingestion_date", current_date())
```text

</details>

### Hint 5: Guardar como Delta particionado

<details>
<summary>Click for revelar Hint 5</summary>

for guardar como Delta with particionamiento:

```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("country") \
    .save("s3a://bronze/transactions_delta")
```text

Make sure to use:

- `.format("delta")` - especifica formato Delta
- `.mode("overwrite")` - sobrescribe if existe (primera vez)
- `.partitionBy("country")`- create partitions by country
- `.save()` - guarda in la ruta especificada

</details>

---

## 🎯 Tarea 2: Append data

### Hint 1: Read specific rows

<details>
<summary>Click for revelar Hint 1</summary>

you can leer las siguientes 5,000 rows of dos formas:

**Option to - Using SQL with OFFSET**:

```python
df_all = spark.read.json("path/to/file.json")
df_all.createOrReplaceTempView("all_tx")
df_new = spark.sql("SELECT * FROM all_tx LIMIT 5000 OFFSET 10000")
```text

**Option B - Using window function**:

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

df_all = spark.read.json("path/to/file.json")
window = Window.orderBy("transaction_id")
df_numbenetwork = df_all.withColumn("row_num", row_number().over(window))
df_new = df_numbenetwork.filter((col("row_num") > 10000) & (col("row_num") <= 15000)) \
    .drop("row_num")
```

**Option C - Simple (for this case)**:

```python
df_all = spark.read.json("path/to/file.json")
df_new = df_all.limit(15000).subtract(df_all.limit(10000))
```text

</details>

### Hint 2: Modo append

<details>
<summary>Click for revelar Hint 2</summary>

for agregar datas without sobrescribir:

```python
df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("country") \
    .save("s3a://bronze/transactions_delta")
```text

**Importante**: El esquema and particionamiento deben coincidir with la table existente.
</details>

---

## 🎯 Tarea 3: Overwrite Partition

### Hint 1: Modificar campo condicionalmente

<details>
<summary>Click for revelar Hint 1</summary>

for cambiar valores condicionalmente, usa `when()`:

```python
from pyspark.sql.functions import when

df_modified = df.withColumn(
    "status",
    when(col("status") == "pending", "expinetwork")
    .otherwise(col("status"))
)
```text

</details>

### Hint 2: replaceWhere option

<details>
<summary>Click for revelar Hint 2</summary>

To overwrite only to specific partition:

```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", "country = 'USA'") \
    .save("s3a://bronze/transactions_delta")
```

**Key**: `replaceWhere`indicates which partitions to overwrite. This is VERY different than`.mode("overwrite")`only, that would overwrite the ENTIRE table.
</details>

### Hint 3: Verificar changes

<details>
<summary>Click for revelar Hint 3</summary>

To verify that only USA changed:

```python
# Antes
df_before = spark.read.format("delta").load(path)
count_before_usa = df_before.filter(col("country") == "USA").count()
pending_before_usa = df_before.filter(
    (col("country") == "USA") & (col("status") == "pending")
).count()

# ... tu code of overwrite ...

# Después
df_after = spark.read.format("delta").load(path)
pending_after_usa = df_after.filter(
    (col("country") == "USA") & (col("status") == "pending")
).count()

# pending_after_usa debe ser 0
# Pero otros países deben to have pending intacto
```text

</details>

---

## 🎯 Tarea 4: SQL Queries

### Hint 1: Registrar table temporal

<details>
<summary>Click for revelar Hint 1</summary>

for can usar SQL, registra la table:

```python
df = spark.read.format("delta").load("s3a://bronze/transactions_delta")
df.createOrReplaceTempView("transactions_delta")

# Ahora you can usar SQL
result = spark.sql("SELECT * FROM transactions_delta LIMIT 10")
```text

</details>

### Hint 2: Query 1 - Count by country

<details>
<summary>Click for revelar Hint 2</summary>

```sql
SELECT 
    country, 
    COUNT(*) as total_transactions
FROM transactions_delta
GROUP BY country
ORDER BY total_transactions DESC
```text

</details>

### Hint 3: Query 2 - Metrics by status

<details>
<summary>Click for revelar Hint 3</summary>

```sql
SELECT 
    status,
    COUNT(*) as count,
    ROUND(AVG(amount), 2) as avg_amount,
    ROUND(SUM(amount), 2) as total_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM transactions_delta
GROUP BY status
ORDER BY total_amount DESC
```

</details>

### Hint 4: Query 3 - Top 10 transactions

<details>
<summary>Click for revelar Hint 4</summary>

```sql
SELECT 
    transaction_id,
    user_id,
    amount,
    currency,
    country,
    status
FROM transactions_delta
ORDER BY amount DESC
LIMIT 10
```text

</details>

### Hint 5: Query 4 - transactions by mes

<details>
<summary>Click for revelar Hint 5</summary>

```sql
SELECT 
    DATE_TRUNC('month', timestamp) as month,
    COUNT(*) as num_transactions,
    ROUND(SUM(amount), 2) as total_amount,
    ROUND(AVG(amount), 2) as avg_amount
FROM transactions_delta
GROUP BY DATE_TRUNC('month', timestamp)
ORDER BY month DESC
```text

**AlterNATiva** if DATE_TRUNC not funciona:

```sql
SELECT 
    YEAR(timestamp) as year,
    MONTH(timestamp) as month,
    COUNT(*) as num_transactions,
    ROUND(SUM(amount), 2) as total_amount
FROM transactions_delta
GROUP BY YEAR(timestamp), MONTH(timestamp)
ORDER BY year DESC, month DESC
```text

</details>

---

## 🔧 Common Troubleshooting

### Error: "Table not found"

<details>
<summary>Solution</summary>

1. Verify that MinIO is running:

   ```bash
   docker ps | grep minio
   ```

2. Verifica la ruta:

   ```python
   # Debe ser s3a:// (not s3://)
   path = "s3a://bronze/transactions_delta"
   ```text

3. Check S3 configuration in spark-defaults.conf

</details>

### Error: "AnalysisException: Path does not exist"

<details>
<summary>Solution</summary>

The file of datas not se encuentra. Verifica:

```python
# Ruta relativa correcta desde el exercise
path = "../../../data/raw/transactions.json"

# or ruta absoluta
path = "/opt/spark/work-dir/data/raw/transactions.json"
```

</details>

### Error: "Partitioning column not found"

<details>
<summary>Solution</summary>

Make sure the column`country` existe in el DataFrame antes of particionar:

```python
# Verifica columns
print(df.columns)

# Verifica que 'country' is presente
assert 'country' in df.columns, "Falta column country"
```text

</details>

### Queries muy lentas

<details>
<summary>Solution</summary>

1. **Usa filters in columns particionadas** (country) for aprovechar partition pruning
2. **Cache** if you are going to query multIPle times:

   ```python
   df.cache()
   ```text

3. **Increase resources** in docker-compose.yml (more cores/memory)

</details>

---

## 📚 References

- [Delta Lake Python API](HTTPs://docs.delta.io/latest/api/python/index.html)
- [PySpark SQL Functions](HTTPs://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Delta Lake Best Practices](HTTPs://docs.delta.io/latest/best-practices.html)

---

**Are you still stuck?** Check the folder`solution/`to see the full implementation. But try to solve without looking first!
