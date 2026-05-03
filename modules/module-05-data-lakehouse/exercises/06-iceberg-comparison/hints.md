# 💡 Hints - Exercise 06: Delta Lake vs Apache Iceberg

## 🎯 Conceptos Key

### Delta Lake
- **Origen**: Databricks (2019, open-source 2020)
- **Formato**: Parquet + Transaction Log (JSON)
- **Catalogo**: Delta Catalog or Hive Metastore
- **Optimizado for**: Spark/Databricks workloads

### Apache Iceberg
- **Origen**: Netflix → Apache (2018)
- **Formato**: Parquet/ORC + Metadata (Avro)
- **Catalogo**: Hive, Hadoop, AWS Glue, Nessie
- **Optimizado for**: Multi-engine environments

---

## 📝 comparison.py

### Configurar Spark with ambos
```python
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pIP

builder = SparkSession.builder.appName("Comparison") \
    .config("spark.sql.extensions", 
            "io.delta.sql.DeltaSparkSessionExtension,"
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", 
            "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.catalog.iceberg_catalog", 
            "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg_catalog.type", "hive") \
    .config("spark.sql.catalog.iceberg_catalog.uri", 
            "thrift://hive-metastore:9083") \
    .config("spark.sql.catalog.iceberg_catalog.warehouse", 
            "s3a://warehouse/iceberg")

spark = configure_spark_with_delta_pIP(builder).getOrCreate()
```

### 1. Delta Lake - Escribir and Leer
```python
import time

# Escribir
delta_path = "s3a://bronze/comparison_delta"

start = time.time()
df.write.format("delta").mode("overwrite").save(delta_path)
delta_write_time = time.time() - start

# Leer
start = time.time()
delta_df = spark.read.format("delta").load(delta_path)
delta_count = delta_df.count()  # Fuerza ejecución
delta_read_time = time.time() - start

print(f"Delta Write: {delta_write_time:.2f}s")
print(f"Delta Read: {delta_read_time:.2f}s")
print(f"Delta Count: {delta_count:,}")
```

### 2. Apache Iceberg - Escribir and Leer
```python
# Escribir - Opción 1: writeTo()
start = time.time()
df.writeTo("iceberg_catalog.default.comparison_iceberg") \
    .using("iceberg") \
    .create()
iceberg_write_time = time.time() - start

# Escribir - Opción 2: SQL
spark.sql("""
    CREATE TABLE iceberg_catalog.default.comparison_iceberg
    USING iceberg
    AS SELECT * FROM source_view
""")

# Leer - Opción 1: formato
start = time.time()
iceberg_df = spark.read.format("iceberg") \
    .load("iceberg_catalog.default.comparison_iceberg")
iceberg_count = iceberg_df.count()
iceberg_read_time = time.time() - start

# Leer - Opción 2: table
iceberg_df = spark.table("iceberg_catalog.default.comparison_iceberg")

print(f"Iceberg Write: {iceberg_write_time:.2f}s")
print(f"Iceberg Read: {iceberg_read_time:.2f}s")
print(f"Iceberg Count: {iceberg_count:,}")
```

### 3. Feature Comparison

#### Time Travel
```python
# Delta Lake
df_v0 = spark.read.format("delta") \
    .option("versionAsOf", 0) \
    .load(delta_path)

# Iceberg
df_snapshot = spark.read.format("iceberg") \
    .option("snapshot-id", snapshot_id) \
    .load("iceberg_catalog.default.table")

# or by timestamp
df_time = spark.read.format("iceberg") \
    .option("as-of-timestamp", "1609459200000") \
    .load("iceberg_catalog.default.table")
```

#### ACID Transactions
```python
# Delta Lake - UPDATE/DELETE/MERGE
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, delta_path)
delta_table.update(
    condition="status = 'pending'",
    set={"status": "'completed'"}
)

# Iceberg - SQL
spark.sql("""
    UPDATE iceberg_catalog.default.table
    SET status = 'completed'
    WHERE status = 'pending'
""")
```

#### Schema Evolution
```python
# Delta Lake
df_new_schema.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(delta_path)

# Iceberg - Schema evolution automática
df_new_schema.writeTo("iceberg_catalog.default.table") \
    .using("iceberg") \
    .append()  # Auto merge schema
```

#### Partitioning
```python
# Delta Lake - Explicit partitioning
df.write.format("delta") \
    .partitionBy("year", "month") \
    .save(delta_path)

# Iceberg - Hidden partitioning (more flexible)
spark.sql("""
    CREATE TABLE iceberg_catalog.default.table (
        id bigint,
        timestamp timestamp,
        data string
    )
    USING iceberg
    PARTITIONED BY (days(timestamp))  -- Partition function
""")

# Partition evolution (only Iceberg)
spark.sql("""
    ALTER TABLE iceberg_catalog.default.table
    REPLACE PARTITION FIELD days(timestamp) WITH months(timestamp)
""")
```

---

## 🚨 Errores Comunes

### Error 1: Iceberg JAR faltante
```
ClassNotFoundException: org.apache.iceberg.spark.SparkCatalog
```
**Solution:** Add Iceberg JAR:
```bash
--packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.0
```

### Error 2: Catalog not configurado
```
AnalysisException: Database 'default' not found
```
**Solution:** Verify catalog configuration:
```python
.config("spark.sql.catalog.iceberg_catalog.type", "hive")
.config("spark.sql.catalog.iceberg_catalog.uri", "thrift://...")
```

### Error 3: Namespace incorrecto
```python
# ❌ MAL
spark.read.format("iceberg").load("table_name")

# ✅ BIEN - incluir catalog.database
spark.read.format("iceberg").load("iceberg_catalog.default.table_name")
```

### Error 4: write() vs writeTo()
```python
# ❌ MAL - write() not funciona bien with Iceberg
df.write.format("iceberg").save("iceberg_catalog.default.table")

# ✅ BIEN - usar writeTo()
df.writeTo("iceberg_catalog.default.table").using("iceberg").create()
```

---

## 📊 Detailed Comparison

### Performance

| Aspecto | Delta Lake | Apache Iceberg |
|---------|------------|----------------|
| **Write Speed** | Fast (Spark optimized) | Similar |
| **Read Speed** | Fast (data skIPping) | Similar |
| **Metadata Overhead** | Bajo (JSON simple) | Medio (Avro + snapshots) |
| **Small Files** | Problem (necesita OPTIMIZE) | Similar |
| **Compaction** | Manual (OPTIMIZE) | Automatic or manual |

### Features

| Feature | Delta Lake | Apache Iceberg |
|---------|------------|----------------|
| **ACID** | ✅ Yes | ✅ Yes |
| **Time Travel** | ✅ Version/Timestamp | ✅ Snapshot/Timestamp |
| **Schema Evolution** | ✅ With mergeSchema | ✅ Automatic |
| **Partition Evolution** | ❌ not | ✅ Yes (major feature) |
| **Hidden Partitioning** | ❌ not | ✅ Yes |
| **Multi-Engine** | ⚠️ Limitado | ✅ Excelente |
| **Z-Ordering** | ✅ Yes | ❌ not (usa sorting) |
| **CDF (Change data Feed)** | ✅ Yes | ⚠️ Limitado |

### Ecosistopic

| Herramienta | Delta Lake | Iceberg |
|-------------|------------|---------|
| **Spark** | ✅ Nativo | ✅ Excelente |
| **Flink** | ⚠️ Experimental | ✅ Nativo |
| **Trill/Presto** | ⚠️ Basic | ✅ Excellent |
| **Databricks** | ✅ Optimizado | ⚠️ Soportado |
| **Snowflake** | ❌ not | ✅ Yes (Iceberg Tables) |
| **AWS Athena** | ⚠️ Limitado | ✅ Nativo |

---

## 🎓 Conceptos Avanzados

### Hidden Partitioning (Iceberg)
```python
# Problem in Delta Lake
df.filter("date = '2024-01-15'")  # User debe conocer particionamiento

# Solution in Iceberg
spark.sql("""
    CREATE TABLE iceberg_catalog.default.events (
        id bigint,
        timestamp timestamp,
        data string
    )
    USING iceberg
    PARTITIONED BY (days(timestamp))
""")

# Query transparente (user not necesita to know particionamiento)
spark.sql("SELECT * FROM iceberg_catalog.default.events WHERE timestamp = '2024-01-15'")
# Iceberg automáticamente usa partition pruning
```

### Partition Evolution (Iceberg)
```python
# Cambiar estrategia of particionamiento without reescribir datas
spark.sql("""
    ALTER TABLE iceberg_catalog.default.events
    REPLACE PARTITION FIELD days(timestamp) WITH months(timestamp)
""")

# Nuevos datas usan months(), pero datas viejos with days() siguen accesibles
# Iceberg maneja esto transparentemente
```

### Snapshot Management (Iceberg)
```python
# to see snapshots
spark.sql("""
    SELECT * FROM iceberg_catalog.default.events.snapshots
""").show()

# Rolelback to snapshot
spark.sql("""
    CALL iceberg_catalog.system.rolelback_to_snapshot(
        'default.events', 12345678
    )
""")

# Expire old snapshots
spark.sql("""
    CALL iceberg_catalog.system.expire_snapshots(
        table => 'default.events',
        older_than => TIMESTAMP '2024-01-01 00:00:00'
    )
""")
```

### Change data Feed (Delta Lake)
```python
# Habilitar CDF
spark.conf.set("spark.databricks.delta.properties.defaults.enableChangeDataFeed", "true")

# or by table
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")

# Leer changes
changes = spark.read.format("delta") \
    .option("readChangeFeed", "true") \
    .option("startingVersion", 0) \
    .load(delta_path)

changes.show()
# Muestra: _change_type (insert, update_preimage, update_postimage, delete)
```

---

## 🎯 When to Use Each One

### Usar Delta Lake when:
- ✅ You are in the Spark/Databricks ecosystem
- ✅ Necesitas Z-Ordering
- ✅ you want Change data Feed
- ✅ Performance in Spark is critical
- ✅ Team is already familiar with Delta

### Usar Apache Iceberg when:
- ✅ Necesitas multi-engine support (Flink, Trino, Presto)
- ✅ Partition evolution is importante
- ✅ Migras desde Hive
- ✅ Necesitas hidden partitioning
- ✅ you want vendor-neutrality

### Considerar ambos when:
- ⚠️ you have workloads mixtos (batch + streaming)
- ⚠️ Necesitas flexibility for cambiar engines
- ⚠️ You are building to new data platform

---

## ✅ Checklist of Completitud

- [ ] Spark configurado with Delta Lake + Iceberg
- [ ] table Delta Lake creada and medida
- [ ] table Iceberg creada and medida
- [ ] Write/Read times comparados
- [ ] Features key of ambos entendidos
- [ ] Casos of uso claros for cada formato
- [ ] Code runs without errors
- [ ] Comparison printed correctly
