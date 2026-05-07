# data Lakehouse Architecture: Patterns and Optimizations

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Medallion Architecture](#medallion-architecture)
3. [Time Travel and Versioning](#time-travel-and-versioning)
4. [Schema Evolution](#schema-evolution)
5. [Partitioning Strategies](#partitioning-strategies)
6. [Performance Optimizations](#performance-optimizations)
7. [data Lifecycle Management](#data-lifecycle-management)
8. [Ingestion Patterns](#ingestion-patterns)

---

## Introduction

The architecture of to data Lakehouse is not just about choosing to table format (Delta Lake, Iceberg). It's about **designing reliable, efficient and scalable pIPelines** that take advantage of the unique features of the lakehouse.

In this document we will explore:

- **Design patterns** tested in production
- **Optimization strategies** for performance
- **Industry best practices**

---

## Medallion Architecture

### 🥉🥈🥇 What is Medallion Architecture?

The Medallion architecture is to design pattern that organizes data into three progressively refined layers:

```text
┌─────────────────────────────────────────────────────────────┐
│                    MEDALLION ARCHITECTURE                    │
│                                                              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐         │
│  │  Bronze  │ ───→ │  Silver  │ ───→ │   Gold   │         │
│  │  (Raw)   │      │ (Refined)│      │(Business)│         │
│  └──────────┘      └──────────┘      └──────────┘         │
│                                                              │
│  • Append-only     • Cleaned       • Aggregated            │
│  • Immutable       • Validated     • Business metrics       │
│  • Full history    • Deduplicated  • Optimized for BI/ML   │
└─────────────────────────────────────────────────────────────┘
```text

### 🥉 Bronze Layer (Raw data)

**Purpose**: Preserve data as it arrives from sources, without loss of information.

**features**:

- ✅ **Append-only**: only se agregan datas, nunca se eliminan
- ✅ **Immutable**: Datas originales nunca se modifican
- ✅ **Full lineage**: Rastreo completo of the origen
- ✅ **Schema minimal**: Only basic data types
- ✅ **Metadata**: timestamp of ingesta, source, filename

**Implementation example**:

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name

spark = SparkSession.builder.appName("Bronze Ingestion").getOrCreate()

# Leer datas crudos (they can to have issues of calidad)
raw_df = spark.read.format("json").load("s3://raw-bucket/events/")

# Agregar metadata of ingesta
bronze_df = raw_df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_file", input_file_name())

# Escribir to Bronze layer (append-only)
bronze_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("date") \
    .save("s3://lakehouse/bronze/events/")
```text

**Typical Bronze Scheme**:

```
events_bronze
├── event_id: string                  # Original data
├── user_id: string                   # Original data
├── event_type: string                # Original data
├── event_data: string (JSON)         # Original data (without parsear)
├── timestamp: string                 # Original data (he/she can ser mal formato)
├── ingestion_timestamp: timestamp    # Metadata
├── source_file: string               # Metadata
└── date: date (partition)            # Partición
```text

**Ventajas**:

- 🔄 **Reprocessing**: if there is bug, reprocesas desde Bronze
- 📊 **Audit trail**: You know exactly what data arrived and when
- 🔒 **Compliance**: Datas originales preservados
- 🐛 **Debugging**: you can investigar issues in datas crudos

**What NOT to do in Bronze?**:

- ❌ not filtrar datas (incluso if parecen malos)
- ❌ not transformar tIPos of datas agresivamente
- ❌ not descartar columns
- ❌ not to make joins with otras tables

### 🥈 Silver Layer (Refined data)

**Purpose**: Clean, validated and analytics-ready data.

**features**:

- ✅ **Cleaned**: Nulls manejados, formatos correctos
- ✅ **Validated**: Business rules aplicadas
- ✅ **Deduplicated**: without records duplicados
- ✅ **Strongly typed**: TIPos of datas correctos
- ✅ **Enriched**: he/she can incluir joins with dimensions

**Implementation example**:

```python
from pyspark.sql.functions import col, to_timestamp, when, regexp_replace
from delta.tables import DeltaTable

# Leer desde Bronze
bronze_df = spark.read.format("delta").load("s3://lakehouse/bronze/events/")

# Transformaciones of limpieza
silver_df = bronze_df \
    .filter(col("event_id").isNotNull()) \
    .filter(col("user_id").rlike("^[to-Z0-9]{10}$")) \
    .withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss")) \
    .withColumn("event_type", regexp_replace(col("event_type"), "\\s+", "_")) \
    .dropDuplicates(["event_id"]) \
    .select(
        col("event_id"),
        col("user_id"),
        col("event_type"),
        col("timestamp"),
        col("event_data"),
        col("ingestion_timestamp")
    )

# Validaciones of negocio
silver_df = silver_df \
    .filter(col("timestamp") <= current_timestamp()) \
    .filter(col("event_type").isin(["click", "view", "purchase", "signup"]))

# Escribir to Silver layer
silver_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("date") \
    .option("mergeSchema", "true") \
    .save("s3://lakehouse/silver/events/")
```text

**Typical Silver Schema**:

```text
events_silver
├── event_id: string (NOT NULL)
├── user_id: string (NOT NULL, validated format)
├── event_type: string (enum: click|view|purchase|signup)
├── timestamp: timestamp (NOT NULL, valid range)
├── event_data: struct<...> (parsed JSON)
├── ingestion_timestamp: timestamp
└── date: date (partition)
```

**Validaciones comunes in Silver**:

1. **Nulls**:

```python
# Eliminar or llenar nulls según business rules
df.filter(col("user_id").isNotNull())
df.fillna({"country": "UNKNOWN"})
```text

1. **Duplicados**:

```python
# Deduplicar by key NATural
df.dropDuplicates(["event_id"])

# or usar window function for quedarse with el more reciente
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window = Window.partitionBy("event_id").orderBy(col("timestamp").desc())
df.withColumn("rn", row_number().over(window)) \
  .filter(col("rn") == 1) \
  .drop("rn")
```text

1. **Outliers**:

```python
# Filtrar valores fuera of rango válido
df.filter((col("age") >= 0) & (col("age") <= 120))
df.filter((col("amount") >= 0) & (col("amount") <= 1000000))
```text

1. **Format standardization**:

```python
# Estandarizar emails, phone numbers, etc.
df.withColumn("email", lower(trim(col("email"))))
df.withColumn("phone", regexp_replace(col("phone"), "[^0-9]", ""))
```

**What NOT to do in Silver?**:

- ❌ not agregar (SUM, AVG, etc.) - that is Gold
- ❌ DO NOT create complex business metrics
- ❌ DO NOT do heavy joins (only basic enrichment)

### 🥇 Gold Layer (Business-Level Aggregates)

**Purpose**: data optimized for consumption in BI, dashboards and ML.

**features**:

- ✅ **Aggregated**: SUMs, AVGs, COUNTs by dimensiones
- ✅ **Denormalized**: Optimized for specific queries
- ✅ **Business metrics**: KPIs, ratios, conversions
- ✅ **Dimensional models**: Star schema, fact/dimension tables
- ✅ **ML features**: Feature engineering aplicado

**Implementation example**:

```python
from pyspark.sql.functions import sum, avg, count, countDistinct, round

# Leer desde Silver
silver_df = spark.read.format("delta").load("s3://lakehouse/silver/events/")

# Agregar métricas of negocio
gold_df = silver_df \
    .groupBy("date", "event_type") \
    .agg(
        count("*").alias("total_events"),
        countDistinct("user_id").alias("unique_users"),
        round(count("*") / countDistinct("user_id"), 2).alias("events_per_user")
    )

# Escribir to Gold layer
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .save("s3://lakehouse/gold/daily_events_summary/")
```text

**Examples of tables Gold**:

1. **Daily Sales Summary** (BI):

```python
sales_gold = silver_sales \
    .groupBy("date", "product_category", "region") \
    .agg(
        sum("amount").alias("total_revenue"),
        count("order_id").alias("total_orders"),
        countDistinct("customer_id").alias("unique_customers"),
        (sum("amount") / count("order_id")).alias("avg_order_value")
    )
```text

1. **User Behavior Features** (ML):

```python
user_features_gold = silver_events \
    .groupBy("user_id") \
    .agg(
        count(when(col("event_type") == "click", 1)).alias("total_clicks"),
        count(when(col("event_type") == "purchase", 1)).alias("total_purchases"),
        (count(when(col("event_type") == "purchase", 1)) /
         count(when(col("event_type") == "click", 1))).alias("conversion_rate"),
        datediff(max("timestamp"), min("timestamp")).alias("days_active")
    )
```text

1. **Executive Dashboard** (Denormalized):

```python
exec_dashboard_gold = silver_sales \
    .join(dim_products, "product_id") \
    .join(dim_customers, "customer_id") \
    .join(dim_regions, "region_id") \
    .groupBy("year", "quarter", "product_category", "customer_segment") \
    .agg(
        sum("revenue").alias("total_revenue"),
        sum("profit").alias("total_profit"),
        (sum("profit") / sum("revenue") * 100).alias("profit_margin_pct")
    )
```

**Optimizaciones in Gold**:

```python
# Z-ordering for queries específicos
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/gold/sales_summary/")
deltaTable.optimize().executeZOrderBy("product_category", "region")
```text

### Flow Completo Bronze → Silver → Gold

```python
def medallion_pIPeline():
    """
    PIPeline completo of arquitectura Medallion
    """
    # ===== BRONZE LAYER =====
    print("📥 Ingesting raw data to Bronze...")
    raw_df = spark.read.format("json").load("s3://raw/events/")
    
    bronze_df = raw_df \
        .withColumn("ingestion_ts", current_timestamp()) \
        .withColumn("source_file", input_file_name())
    
    bronze_df.write \
        .format("delta") \
        .mode("append") \
        .save("s3://lakehouse/bronze/events/")
    
    # ===== SILVER LAYER =====
    print("🧹 Cleaning and validating data to Silver...")
    bronze_df_read = spark.read.format("delta").load("s3://lakehouse/bronze/events/")
    
    silver_df = bronze_df_read \
        .filter(col("event_id").isNotNull()) \
        .withColumn("timestamp", to_timestamp(col("timestamp"))) \
        .dropDuplicates(["event_id"]) \
        .filter(col("timestamp") <= current_timestamp())
    
    silver_df.write \
        .format("delta") \
        .mode("append") \
        .save("s3://lakehouse/silver/events/")
    
    # ===== GOLD LAYER =====
    print("📊 Aggregating business metrics to Gold...")
    silver_df_read = spark.read.format("delta").load("s3://lakehouse/silver/events/")
    
    gold_df = silver_df_read \
        .groupBy("date", "event_type") \
        .agg(
            count("*").alias("total_events"),
            countDistinct("user_id").alias("unique_users")
        )
    
    gold_df.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("date") \
        .save("s3://lakehouse/gold/events_summary/")
    
    print("✅ Medallion pIPeline completed!")

# Ejecutar pIPeline
medallion_pIPeline()
```text

---

## Time Travel and Versionado

### What is Time Travel?

**Time Travel** is the ability to access **historical versions** of to table. Each write creates to new version.

```text
Version 0 ───→ Version 1 ───→ Version 2 ───→ Version 3 (current)
2024-02-01    2024-02-05     2024-02-10     2024-02-12
```

### How It Works at Delta Lake

Delta Lake mantiene un **transaction log** que registra cada change:

```text
s3://bucket/table/_delta_log/
├── 00000000000000000000.json  # Version 0
├── 00000000000000000001.json  # Version 1
├── 00000000000000000002.json  # Version 2
└── 00000000000000000003.json  # Version 3 (actual)
```text

Cada archivo JSON contiene:

- Archivos aggregates/removidos
- Operation metadata
- Timestamp
- Metrics (rows, bytes)

### Queries with Time Travel

#### 1. Query by Timestamp

```python
# Leer datas of he/she makes 1 hora
df = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-02-12 09:00:00") \
    .load("s3://lakehouse/silver/events/")

# Leer datas of ayer
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).strftime("%and-%m-%d %H:%M:%S")
df = spark.read \
    .format("delta") \
    .option("timestampAsOf", yesterday) \
    .load("s3://lakehouse/silver/events/")
```text

#### 2. Query by Version

```python
# Leer version específica
df = spark.read \
    .format("delta") \
    .option("versionAsOf", 5) \
    .load("s3://lakehouse/silver/events/")
```

### to see Historial of Versiones

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# to see todas las versiones
history_df = deltaTable.history()
history_df.select("version", "timestamp", "operation", "operationMetrics").show()

# Output:
# +-------+-------------------+---------+---------------------------+
# |version|timestamp          |operation|operationMetrics           |
# +-------+-------------------+---------+---------------------------+
# |3      |2024-02-12 10:00:00|WRITE    |{numFiles: 10, rows: 50000}|
# |2      |2024-02-11 10:00:00|MERGE    |{numUpdated: 1000}         |
# |1      |2024-02-10 10:00:00|DELETE   |{numDeleted: 500}          |
# |0      |2024-02-09 10:00:00|WRITE    |{numFiles: 8, rows: 45000} |
# +-------+-------------------+---------+---------------------------+
```text

### Rolelback to Previous Version

```python
# Opción 1: Restore to version específica
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")
deltaTable.restoreToVersion(5)  # to return to version 5

# Opción 2: Restore to timestamp
deltaTable.restoreToTimestamp("2024-02-10 10:00:00")
```text

**⚠️ Caution**: Restore creates to new version, it does not delete subsequent ones.

```text
Versiones: 0 → 1 → 2 → 3 → 4 → 5 → 6 (current)
Después of restoreToVersion(3):
Versiones: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 (copia of 3)
```

### Casos of Uso of Time Travel

#### 1. Audit and Compliance

```python
# Recrear estado exacto of datas for auditoría
# "¿what datas tenía this table el 2024-01-15?"
df_audit = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-01-15 00:00:00") \
    .load("s3://lakehouse/gold/financial_summary/")

df_audit.write \
    .format("parquet") \
    .save("s3://audit-reports/2024-01-15/financial_summary/")
```text

#### 2. Rolelback after Error

```python
# Detectaste que el pIPeline of ayer tenía un bug
# Rolelback to version anterior
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/transactions/")

# to see what pasó
deltaTable.history().filter(col("operation") == "MERGE").show()

# Rolelback to version antes of the bug
deltaTable.restoreToVersion(45)  # Version buena conocida
```text

#### 3. Reproducibilidad in ML

```python
# Entrenar modelo with EXACTAMENTE los mismos datas
# Feature store with time travel
training_data = spark.read \
    .format("delta") \
    .option("versionAsOf", 10) \
    .load("s3://lakehouse/gold/user_features/")

model = train_model(training_data)

# Guardar version usada in metadata of the modelo
model_metadata = {
    "model_name": "user_churn_pnetworkictor",
    "training_data_version": 10,
    "training_timestamp": "2024-02-10 10:00:00"
}
```text

#### 4. Comparar Versiones (Drift Detection)

```python
# Detectar drift in distribución of datas
current_data = spark.read.format("delta").load("s3://lakehouse/silver/events/")

last_week_data = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-02-05 10:00:00") \
    .load("s3://lakehouse/silver/events/")

# Comparar distribuciones
current_stats = current_data.describe()
last_week_stats = last_week_data.describe()

# Detectar changes significativos
```

---

## Schema Evolution

### What is Schema Evolution?

**Schema Evolution** is la capacidad of **modificar el schema** of una table without:

- Reescribir todos los datas
- Romper pIPelines existentes
- Downtime

### TIPos of Schema Evolution

#### 1. Add Column (Most Common)

```python
# Schema actual:
# user_id, name, email

# Nuevo DataFrame with column adicional
new_df = spark.read.csv("users_new.csv")
# user_id, name, email, phone

# Escribir with mergeSchema
new_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("s3://lakehouse/silver/users/")

# Result:
# Records antiguos: phone = NULL
# Records nuevos: phone = valor real
```text

**⚠️ Importante**: `mergeSchema` debe to be habilitado.

```python
# Configuration global
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# or by operación
.option("mergeSchema", "true")
```text

#### 2. Change Column Type (Cuidado)

Delta Lake permite **ampliar** tIPos pero not **networkucir**:

✅ **Permitido** (widening):

- `int` → `long`
- `float` → `double`
- `byte` → `int`

❌ **not permitido** (narrowing):

- `long` → `int`
- `double` → `float`
- `string` → `int`

```python
# Cambiar tIPo of column (widening)
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

deltaTable.alterColumn("user_id", "LONG")  # if era INT
```text

for narrowing, necesitas:

1. Agregar nueva column with tIPo deseado
2. Copiar and transformar datas
3. Eliminar column anterior

#### 3. Rename Column

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/users/")

# Rename column
deltaTable.alterColumn("user_email", newName="email")
```

#### 4. Drop Column (Requiere Rewrite)

```python
# Opción 1: Leer and reescribir without la column
df = spark.read.format("delta").load("s3://lakehouse/silver/users/")
df_without_col = df.drop("deprecated_column")

df_without_col.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("s3://lakehouse/silver/users/")

# Opción 2: Usar DELETE VECTORS (Delta Lake 2.0+)
# not requiere reescribir, marca column como "deleted"
```text

### Schema Enforcement

Delta Lake automatically validates that new data matches the schema:

```python
# Schema actual: user_id (string), name (string), age (int)

# Intento of escribir with schema incompatible
bad_df = spark.createDataFrame([
    ("U001", "John", "twenty-five")  # age is string, debería ser int
], ["user_id", "name", "age"])

try:
    bad_df.write.format("delta").mode("append").save("s3://lakehouse/silver/users/")
except Exception as e:
    print(f"❌ Schema mismatch: {e}")
    # Error: Cannot write data with schema incompatible with table schema
```text

### Manejo of Breaking Changes

What to do when you need an incompatible change?

**Strategy 1: Dual Write (Gradual Transition)**

```python
# Paso 1: Crear nueva table with nuevo schema
new_users_df.write.format("delta").save("s3://lakehouse/silver/users_v2/")

# Paso 2: Dual write by período of transición
users_df.write.format("delta").mode("append").save("s3://lakehouse/silver/users/")     # Vieja
users_df.write.format("delta").mode("append").save("s3://lakehouse/silver/users_v2/")  # Nueva

# Paso 3: Migrar consumers to users_v2

# Paso 4: Deprecar users (antigua)
```text

**Estrategia 2: Shadow Column**

```python
# Mantener ambas versiones of la column temporalmente
df = df \
    .withColumn("amount_cents", (col("amount_dollars") * 100).cast("long")) \
    .withColumn("amount_dollars_deprecated", col("amount_dollars"))

# Eventualmente eliminar amount_dollars_deprecated
```

**Estrategia 3: Version in Table Name**

```python
# Crear versiones explícitas
s3://lakehouse/silver/events_v1/
s3://lakehouse/silver/events_v2/
s3://lakehouse/silver/events_v3/

# Consumers especifican version que usan
```text

---

## Partitioning Strategies

### Why Partition?

Partitioning physically divides data to:

- ✅ **Mejor performance**: only leer particiones necesarias
- ✅ **Better organization**: data logically grouped
- ✅ **Better maintenance**: Delete old partitions easily

### Partitioning by Date (Most Common)

```python
# Particionar by año/mes/día
df.write \
    .format("delta") \
    .partitionBy("year", "month", "day") \
    .save("s3://lakehouse/silver/events/")

# Structure física:
s3://lakehouse/silver/events/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   ├── part-00000.parquet
│   │   │   └── part-00001.parquet
│   │   ├── day=02/
│   │   └── day=03/
│   └── month=02/
└── year=2023/
```text

**Ventaja**: Queries with filter of fecha only leen particiones necesarias

```python
# only lee particiones of febrero 2024
df = spark.read \
    .format("delta") \
    .load("s3://lakehouse/silver/events/") \
    .filter((col("year") == 2024) & (col("month") == 2))

# Pruning: Evita escanear 365 días completos
```text

### Category Partitioning

```python
# Particionar by column categórica
df.write \
    .format("delta") \
    .partitionBy("country", "product_category") \
    .save("s3://lakehouse/silver/sales/")

# Structure:
s3://lakehouse/silver/sales/
├── country=US/
│   ├── product_category=electronics/
│   ├── product_category=clothing/
│   └── product_category=food/
└── country=UK/
```

**Cuidado**: not particionar by columns with alta cardinalidad

❌ **Malo** (demasiadas particiones):

```python
# user_id he/she has millones of valores únicos
df.partitionBy("user_id")  # ❌ Crea millones of directorios
```text

✅ **Bueno** (cardinalidad moderada):

```python
# country he/she has ~200 valores
df.partitionBy("country")  # ✅ 200 directorios manejables
```text

### Reglas of Particionamiento

1. **Cardinalidad**: 100-10,000 particiones ideal
   - less of 100: little beneficio
   - More than 10,000: Metadata Overhead

2. **Partition size**: 1GB per partition ideal

   ```python
   # Muy pequeño ❌
   # 10,000 partitions × 10MB = 100GB total
   # Demasiadas particiones pequeñas
   
   # Ideal ✅
   # 100 partitions × 1GB = 100GB total
   ```

3. **Query patterns**: Particionar by columns filtradas frecuentemente

   ```python
   # if queries siempre filtran by fecha and región
   SELECT * FROM events WHERE date = '2024-02-12' AND region = 'US'
   
   # Particionar by esas columns
   df.partitionBy("date", "region")
   ```text

4. **Evolution**: You cannot change partitioning without rewriting
   - Delta Lake: not soporta partition evolution
   - Iceberg: YES supports partition evolution

### Partition Pruning

Spark automatically **removes partitions** that do not match filters:

```python
# Table particionada by date
df = spark.read.format("delta").load("s3://lakehouse/silver/events/")

# Query with filter of date
result = df.filter(col("date") == "2024-02-12")

# Spark only lee:
# s3://lakehouse/silver/events/date=2024-02-12/
# ✅ not escanea otras 364 fechas
```text

**See pruning in action**:

```python
# Explain plan for to see pruning
df.filter(col("date") == "2024-02-12").explain()

# Output muestra:
# PartitionFilters: [isnotnull(date#0), (date#0 = 2024-02-12)]
# PushedFilters: []
# ReadSchema: struct<event_id:string, ...>
# (1 of 365 partitions)
```

---

## Optimizaciones of Performance

### 1. Z-Ordering

**Z-ordering** places related data physically close to improve **data skIPping**.

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Optimizar by columns frecuentemente filtradas
deltaTable.optimize().executeZOrderBy("user_id", "event_type")
```text

**How ​​it works**:

```text
without Z-ordering:
File 1: [user=to,type=click], [user=Z,type=view], [user=B,type=purchase]
File 2: [user=to,type=view], [user=and,type=click], [user=C,type=purchase]
→ Query "user=to" debe leer ambos archivos

with Z-ordering:
File 1: [user=to,type=click], [user=to,type=view], [user=B,type=click]
File 2: [user=and,type=view], [user=Z,type=view], [user=C,type=purchase]
→ Query "user=to" only lee File 1 ✅
```text

**When to use**:

- columns filtradas frecuentemente
- Alta cardinalidad (user_id, product_id)
- not usar for particiones (networkundante)

### 2. Compaction

Over time, Delta tables accumulate many small files:

```
s3://lakehouse/silver/events/date=2024-02-12/
├── part-00001.parquet (10MB)
├── part-00002.parquet (8MB)
├── part-00003.parquet (15MB)
...
├── part-01000.parquet (5MB)
```text

**Problem**: Reading 1000 small files is **much slower** than reading 10 large files.

**Solution**: Compaction (combine files)

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Compaction: Combinar archivos pequeños
deltaTable.optimize().executeCompaction()

# Result:
# part-00001.parquet (10MB) + part-00002.parquet (8MB) + ...
# → combined-00001.parquet (1GB)
```text

**Configuration**:

```python
# Target file size (default: 1GB)
spark.conf.set("spark.databricks.delta.optimize.maxFileSize", "1073741824")  # 1GB

# Compaction automático in write
df.write \
    .format("delta") \
    .option("optimizeWrite", "true") \
    .save("s3://lakehouse/silver/events/")
```text

### 3. data SkIPping

Delta Lake maintains **statistics** for each file:

```json
{
  "add": {
    "path": "part-00000.parquet",
    "stats": {
      "numRecords": 100000,
      "minValues": {"user_id": "A001", "timestamp": "2024-02-12 00:00:00"},
      "maxValues": {"user_id": "Z999", "timestamp": "2024-02-12 23:59:59"}
    }
  }
}
```

**data skIPping**: SkIP archivos where min/max not cumplen filters

```python
# Query with filter
df = spark.read.format("delta").load("s3://lakehouse/silver/events/") \
    .filter(col("user_id") == "M500")

# Delta Lake:
# - File 1: min=A001, max=K999 → SKIP ✅
# - File 2: min=L000, max=P999 → READ (contiene M500)
# - File 3: min=Q000, max=Z999 → SKIP ✅
```text

**Habilitar data skIPping stats**:

```python
spark.conf.set("spark.databricks.delta.properties.defaults.dataSkIPpingNumIndexedCols", "32")
```text

### 4. Caching

for queries repetitivos in mismos datas:

```python
# Cache DataFrame in memory
df = spark.read.format("delta").load("s3://lakehouse/silver/events/")
df.cache()

# Queries subsecuentes are instantáneos
result1 = df.filter(col("event_type") == "click").count()  # Lee S3
result2 = df.filter(col("event_type") == "view").count()   # Lee cache ⚡

# Liberar cache when not se necesite more
df.unpersist()
```text

**Automatic cache with OPTIMIZE**:

```python
# OPTIMIZE + CACHE juntos
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/gold/daily_summary/")
deltaTable.optimize().executeCompaction()

spark.read.format("delta").load("s3://lakehouse/gold/daily_summary/").cache()
```

---

## data Lifecycle Management

### Vacuum: Eliminar Archivos Antiguos

Delta Lake mantiene **versiones antiguas** for time travel, pero ocupan espacio.

**VACUUM** elimina archivos not referencedos:

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Eliminar archivos not usados he/she makes more of 7 días
deltaTable.vacuum(retentionHours=168)  # 7 días × 24 horas

# Output:
# Deleted 1250 files (15.3 GB) from s3://lakehouse/silver/events/
```text

**⚠️ Important**: You cannot do time travel beyond retentionHours

```python
# Después of vacuum(168):
df = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-02-01") \  # he/she makes 15 días
    .load("s3://lakehouse/silver/events/")
# ❌ Error: Files not longer exist
```text

**Safety check** (minimum retention 7 days):

```python
# by defecto, not you can vacuum with less of 7 días
deltaTable.vacuum(24)  # ❌ Error

# Override (úsalo only if you know lo que you make)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
deltaTable.vacuum(0)  # Elimina everything inmediatamente
```text

### Retention Policies

Implement retention policies:

```python
def apply_retention_policy(table_path, retention_days):
    """
    Eliminar particiones antiguas según política of retención
    """
    from datetime import datetime, timedelta
    from delta.tables import DeltaTable
    
    # Fecha limit
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime("%and-%m-%d")
    
    # Leer table
    df = spark.read.format("delta").load(table_path)
    
    # Eliminar particiones antiguas
    deltaTable = DeltaTable.forPath(spark, table_path)
    deltaTable.delete(f"date < '{cutoff_date}'")
    
    # Vacuum for liberar espacio
    deltaTable.vacuum(retentionHours=24)
    
    print(f"✅ Deleted partitions older than {cutoff_date}")

# Aplicar políticas diferentes by capa
apply_retention_policy("s3://lakehouse/bronze/logs/", retention_days=30)    # 30 días
apply_retention_policy("s3://lakehouse/silver/events/", retention_days=90)  # 90 días
apply_retention_policy("s3://lakehouse/gold/summary/", retention_days=365)  # 1 año
```

---

## Patrones of Ingesta

### 1. Append-Only (Simpler)

```python
# Cada día agrega nuevos datas
df_today = spark.read.parquet("s3://raw/events/2024-02-12/")

df_today.write \
    .format("delta") \
    .mode("append") \
    .save("s3://lakehouse/bronze/events/")
```text

**Pros**: Simple, fast, does not duplicate
**Cons**: not maneja updates/deletes

### 2. Upsert (MERGE)

```python
from delta.tables import DeltaTable

# Leer nuevos datas
new_data = spark.read.parquet("s3://raw/users/latest/")

# Table existente
deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/users/")

# MERGE: Insert if not existe, Update if existe
deltaTable.alias("target").merge(
    new_data.alias("source"),
    "target.user_id = source.user_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```text

**Pros**: Maneja updates and inserts  
**Cons**: Slower than append

### 3. SCD Type 2 (Slowly Changing Dimensions)

Mantener historial completo of changes:

```python
from pyspark.sql.functions import current_timestamp, lit

# Nuevos datas
new_data = spark.read.csv("users_updates.csv")

# Marcar records actuales como expirados
deltaTable.alias("target").merge(
    new_data.alias("source"),
    "target.user_id = source.user_id AND target.is_current = true"
).whenMatchedUpdate(set={
    "is_current": "false",
    "end_date": "current_timestamp()"
}).execute()

# Insertar nuevas versiones
new_data_with_metadata = new_data \
    .withColumn("is_current", lit(True)) \
    .withColumn("start_date", current_timestamp()) \
    .withColumn("end_date", lit(None).cast("timestamp"))

new_data_with_metadata.write \
    .format("delta") \
    .mode("append") \
    .save("s3://lakehouse/silver/users/")
```text

---

## Resumen

### Key Takeaways

1. **Medallion Architecture**: Bronze (raw) → Silver (refined) → Gold (aggregated)
2. **Time Travel**: Access historical versions for auditing and reproducibility
3. **Schema Evolution**: Modifica schemas without downtime with `mergeSchema`
4. **Partitioning**: Improvement performance with particiones of 1GB and cardinalidad moderada
5. **Optimizaciones**: Z-ordering, compaction, data skIPping, caching
6. **Lifecycle**: VACUUM for liberar espacio, retention policies by capa
7. **Ingesta**: Append (simple), MERGE (upserts), SCD Type 2 (historial)

### Next Steps

Ahora que dominas la arquitectura and patrones, exploraremos:

- **resources adicionales** ([03-resources.md](03-resources.md))
- **Practical exercises** to implement everything learned

---

**Last update**: February 2026
**Tiempo of reading**: ~60 minutos  
**Nivel**: Avanzado
