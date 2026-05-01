# 💡 Hints - Ejercicio 01: Delta Basics

Este archivo contiene pistas progresivas para ayudarte a completar el ejercicio. **Intenta resolver cada tarea sin mirar las pistas primero**. Si te atascas, revela las pistas gradualmente.

---

## 🎯 Tarea 1: Crear table Delta

### Hint 1: Configurar SparkSession con Delta

<details>
<summary>Click para revelar Hint 1</summary>

Para configurar Spark con Delta Lake, necesitas:
```python
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder \
    .appName("Mi App") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
```
</details>

### Hint 2: Read JSON with limit

<details>
<summary>Click para revelar Hint 2</summary>

Para leer solo las primeras 10,000 rows:
```python
df = spark.read.json("path/to/file.json").limit(10000)
```
</details>

### Hint 3: Convertir timestamp

<details>
<summary>Click para revelar Hint 3</summary>

The timestamp field comes as a string. Convert it:
```python
from pyspark.sql.functions import to_timestamp

df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
```

Or if you use specific format:
```python
df = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
```
</details>

### Hint 4: Add ingestion date

<details>
<summary>Click para revelar Hint 4</summary>

Usa `current_date()` para agregar la fecha actual:
```python
from pyspark.sql.functions import current_date

df = df.withColumn("ingestion_date", current_date())
```
</details>

### Hint 5: Guardar como Delta particionado

<details>
<summary>Click para revelar Hint 5</summary>

Para guardar como Delta con particionamiento:
```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("country") \
    .save("s3a://bronze/transactions_delta")
```

Make sure to use:
- `.format("delta")` - especifica formato Delta
- `.mode("overwrite")` - sobrescribe si existe (primera vez)
- `.partitionBy("country")`- create partitions by country
- `.save()` - guarda en la ruta especificada
</details>

---

## 🎯 Tarea 2: Append Data

### Hint 1: Read specific rows

<details>
<summary>Click para revelar Hint 1</summary>

Puedes leer las siguientes 5,000 rows de dos formas:

**Option A - Using SQL with OFFSET**:
```python
df_all = spark.read.json("path/to/file.json")
df_all.createOrReplaceTempView("all_tx")
df_new = spark.sql("SELECT * FROM all_tx LIMIT 5000 OFFSET 10000")
```

**Option B - Using window function**:
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

df_all = spark.read.json("path/to/file.json")
window = Window.orderBy("transaction_id")
df_numbered = df_all.withColumn("row_num", row_number().over(window))
df_new = df_numbered.filter((col("row_num") > 10000) & (col("row_num") <= 15000)) \
    .drop("row_num")
```

**Option C - Simple (for this case)**:
```python
df_all = spark.read.json("path/to/file.json")
df_new = df_all.limit(15000).subtract(df_all.limit(10000))
```
</details>

### Hint 2: Modo append

<details>
<summary>Click para revelar Hint 2</summary>

Para agregar datos sin sobrescribir:
```python
df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("country") \
    .save("s3a://bronze/transactions_delta")
```

**Importante**: El esquema y particionamiento deben coincidir con la table existente.
</details>

---

## 🎯 Tarea 3: Overwrite Partition

### Hint 1: Modificar campo condicionalmente

<details>
<summary>Click para revelar Hint 1</summary>

Para cambiar valores condicionalmente, usa `when()`:
```python
from pyspark.sql.functions import when

df_modified = df.withColumn(
    "status",
    when(col("status") == "pending", "expired")
    .otherwise(col("status"))
)
```
</details>

### Hint 2: replaceWhere option

<details>
<summary>Click para revelar Hint 2</summary>

To overwrite only a specific partition:
```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", "country = 'USA'") \
    .save("s3a://bronze/transactions_delta")
```

**Clave**: `replaceWhere`indicates which partitions to overwrite. This is VERY different than`.mode("overwrite")`only, that would overwrite the ENTIRE table.
</details>

### Hint 3: Verificar cambios

<details>
<summary>Click para revelar Hint 3</summary>

To verify that only USA changed:
```python
# Antes
df_before = spark.read.format("delta").load(path)
count_before_usa = df_before.filter(col("country") == "USA").count()
pending_before_usa = df_before.filter(
    (col("country") == "USA") & (col("status") == "pending")
).count()

# ... tu código de overwrite ...

# Después
df_after = spark.read.format("delta").load(path)
pending_after_usa = df_after.filter(
    (col("country") == "USA") & (col("status") == "pending")
).count()

# pending_after_usa debe ser 0
# Pero otros países deben tener pending intacto
```
</details>

---

## 🎯 Tarea 4: SQL Queries

### Hint 1: Registrar table temporal

<details>
<summary>Click para revelar Hint 1</summary>

Para poder usar SQL, registra la table:
```python
df = spark.read.format("delta").load("s3a://bronze/transactions_delta")
df.createOrReplaceTempView("transactions_delta")

# Ahora puedes usar SQL
result = spark.sql("SELECT * FROM transactions_delta LIMIT 10")
```
</details>

### Hint 2: Query 1 - Count by country

<details>
<summary>Click para revelar Hint 2</summary>

```sql
SELECT 
    country, 
    COUNT(*) as total_transactions
FROM transactions_delta
GROUP BY country
ORDER BY total_transactions DESC
```
</details>

### Hint 3: Query 2 - Metrics by status

<details>
<summary>Click para revelar Hint 3</summary>

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
<summary>Click para revelar Hint 4</summary>

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
```
</details>

### Hint 5: Query 4 - transactions por mes

<details>
<summary>Click para revelar Hint 5</summary>

```sql
SELECT 
    DATE_TRUNC('month', timestamp) as month,
    COUNT(*) as num_transactions,
    ROUND(SUM(amount), 2) as total_amount,
    ROUND(AVG(amount), 2) as avg_amount
FROM transactions_delta
GROUP BY DATE_TRUNC('month', timestamp)
ORDER BY month DESC
```

**Alternativa** si DATE_TRUNC no funciona:
```sql
SELECT 
    YEAR(timestamp) as year,
    MONTH(timestamp) as month,
    COUNT(*) as num_transactions,
    ROUND(SUM(amount), 2) as total_amount
FROM transactions_delta
GROUP BY YEAR(timestamp), MONTH(timestamp)
ORDER BY year DESC, month DESC
```
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
   # Debe ser s3a:// (no s3://)
   path = "s3a://bronze/transactions_delta"
   ```

3. Check S3 configuration in spark-defaults.conf
</details>

### Error: "AnalysisException: Path does not exist"

<details>
<summary>Solution</summary>

El archivo de datos no se encuentra. Verifica:
```python
# Ruta relativa correcta desde el ejercicio
path = "../../../data/raw/transactions.json"

# O ruta absoluta
path = "/opt/spark/work-dir/data/raw/transactions.json"
```
</details>

### Error: "Partitioning column not found"

<details>
<summary>Solution</summary>

Make sure the column`country` existe en el DataFrame antes de particionar:
```python
# Verifica columnas
print(df.columns)

# Verifica que 'country' está presente
assert 'country' in df.columns, "Falta columna country"
```
</details>

### Queries muy lentas

<details>
<summary>Solution</summary>

1. **Usa filtros en columns particionadas** (country) para aprovechar partition pruning
2. **Cache** if you are going to query multiple times:
   ```python
   df.cache()
   ```
3. **Increase resources** in docker-compose.yml (more cores/memory)
</details>

---

## 📚 Referencias

- [Delta Lake Python API](https://docs.delta.io/latest/api/python/index.html)
- [PySpark SQL Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Delta Lake Best Practices](https://docs.delta.io/latest/best-practices.html)

---

**Are you still stuck?** Check the folder`solution/`to see the full implementation. But try to solve without looking first!
