# Data Lakehouse Architecture: Patterns and Optimizations

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Medallion Architecture](#medallion-architecture)
3. [Time Travel and Versioning](#time-travel-and-versioning)
4. [Schema Evolution](#schema-evolution)
5. [Partitioning Strategies](#partitioning-strategies)
6. [Performance Optimizations](#performance-optimizations)
7. [Data Lifecycle Management](#data-lifecycle-management)
8. [Ingestion Patterns](#ingestion-patterns)

---

## Introduction

The architecture of a Data Lakehouse is not just about choosing a table format (Delta Lake, Iceberg). It's about **designing reliable, efficient and scalable pipelines** that take advantage of the unique features of the lakehouse.

In this document we will explore:

- **Design patterns** tested in production
- **Optimization strategies** for performance
- **Industry best practices**

---

## Medallion Architecture

### 🥉🥈🥇 What is Medallion Architecture?

The Medallion architecture is a design pattern that organizes data into three progressively refined layers:

```
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
```

### 🥉 Bronze Layer (Raw Data)

**Purpose**: Preserve data as it arrives from sources, without loss of information.

**features**:
- ✅ **Append-only**: Solo se agregan datos, nunca se eliminan
- ✅ **Immutable**: Datos originales nunca se modifican
- ✅ **Full lineage**: Rastreo completo del origen
- ✅ **Schema minimal**: Only basic data types
- ✅ **Metadata**: timestamp de ingesta, source, filename

**Implementation example**:

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name

spark = SparkSession.builder.appName("Bronze Ingestion").getOrCreate()

# Leer datos crudos (pueden tener issues de calidad)
raw_df = spark.read.format("json").load("s3://raw-bucket/events/")

# Agregar metadata de ingesta
bronze_df = raw_df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_file", input_file_name())

# Escribir a Bronze layer (append-only)
bronze_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("date") \
    .save("s3://lakehouse/bronze/events/")
```

**Typical Bronze Scheme**:

```
events_bronze
├── event_id: string                  # Original data
├── user_id: string                   # Original data
├── event_type: string                # Original data
├── event_data: string (JSON)         # Original data (sin parsear)
├── timestamp: string                 # Original data (puede ser mal formato)
├── ingestion_timestamp: timestamp    # Metadata
├── source_file: string               # Metadata
└── date: date (partition)            # Partición
```

**Ventajas**:
- 🔄 **Reprocessing**: Si hay bug, reprocesas desde Bronze
- 📊 **Audit trail**: You know exactly what data arrived and when
- 🔒 **Compliance**: Datos originales preservados
- 🐛 **Debugging**: Puedes investigar issues en datos crudos

**What NOT to do in Bronze?**:
- ❌ NO filtrar datos (incluso si parecen malos)
- ❌ NO transformar tipos de datos agresivamente
- ❌ NO descartar columns
- ❌ NO hacer joins con otras tables

### 🥈 Silver Layer (Refined Data)

**Purpose**: Clean, validated and analytics-ready data.

**features**:
- ✅ **Cleaned**: Nulls manejados, formatos correctos
- ✅ **Validated**: Business rules aplicadas
- ✅ **Deduplicated**: Sin registros duplicados
- ✅ **Strongly typed**: Tipos de datos correctos
- ✅ **Enriched**: Puede incluir joins con dimensions

**Implementation example**:

```python
from pyspark.sql.functions import col, to_timestamp, when, regexp_replace
from delta.tables import DeltaTable

# Leer desde Bronze
bronze_df = spark.read.format("delta").load("s3://lakehouse/bronze/events/")

# Transformaciones de limpieza
silver_df = bronze_df \
    .filter(col("event_id").isNotNull()) \
    .filter(col("user_id").rlike("^[A-Z0-9]{10}$")) \
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

# Validaciones de negocio
silver_df = silver_df \
    .filter(col("timestamp") <= current_timestamp()) \
    .filter(col("event_type").isin(["click", "view", "purchase", "signup"]))

# Escribir a Silver layer
silver_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("date") \
    .option("mergeSchema", "true") \
    .save("s3://lakehouse/silver/events/")
```

**Typical Silver Schema**:

```
events_silver
├── event_id: string (NOT NULL)
├── user_id: string (NOT NULL, validated format)
├── event_type: string (enum: click|view|purchase|signup)
├── timestamp: timestamp (NOT NULL, valid range)
├── event_data: struct<...> (parsed JSON)
├── ingestion_timestamp: timestamp
└── date: date (partition)
```

**Validaciones comunes en Silver**:

1. **Nulls**:
```python
# Eliminar o llenar nulls según business rules
df.filter(col("user_id").isNotNull())
df.fillna({"country": "UNKNOWN"})
```

2. **Duplicados**:
```python
# Deduplicar por clave natural
df.dropDuplicates(["event_id"])

# O usar window function para quedarse con el más reciente
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window = Window.partitionBy("event_id").orderBy(col("timestamp").desc())
df.withColumn("rn", row_number().over(window)) \
  .filter(col("rn") == 1) \
  .drop("rn")
```

3. **Outliers**:
```python
# Filtrar valores fuera de rango válido
df.filter((col("age") >= 0) & (col("age") <= 120))
df.filter((col("amount") >= 0) & (col("amount") <= 1000000))
```

4. **Format standardization**:
```python
# Estandarizar emails, phone numbers, etc.
df.withColumn("email", lower(trim(col("email"))))
df.withColumn("phone", regexp_replace(col("phone"), "[^0-9]", ""))
```

**What NOT to do in Silver?**:
- ❌ NO agregar (SUM, AVG, etc.) - eso es Gold
- ❌ DO NOT create complex business metrics
- ❌ DO NOT do heavy joins (only basic enrichment)

### 🥇 Gold Layer (Business-Level Aggregates)

**Purpose**: Data optimized for consumption in BI, dashboards and ML.

**features**:
- ✅ **Aggregated**: SUMs, AVGs, COUNTs por dimensiones
- ✅ **Denormalized**: Optimized for specific queries
- ✅ **Business metrics**: KPIs, ratios, conversions
- ✅ **Dimensional models**: Star schema, fact/dimension tables
- ✅ **ML features**: Feature engineering aplicado

**Implementation example**:

```python
from pyspark.sql.functions import sum, avg, count, countDistinct, round

# Leer desde Silver
silver_df = spark.read.format("delta").load("s3://lakehouse/silver/events/")

# Agregar métricas de negocio
gold_df = silver_df \
    .groupBy("date", "event_type") \
    .agg(
        count("*").alias("total_events"),
        countDistinct("user_id").alias("unique_users"),
        round(count("*") / countDistinct("user_id"), 2).alias("events_per_user")
    )

# Escribir a Gold layer
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .save("s3://lakehouse/gold/daily_events_summary/")
```

**Ejemplos de tables Gold**:

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
```

2. **User Behavior Features** (ML):
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
```

3. **Executive Dashboard** (Denormalized):
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

**Optimizaciones en Gold**:

```python
# Z-ordering para queries específicos
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/gold/sales_summary/")
deltaTable.optimize().executeZOrderBy("product_category", "region")
```

### Flujo Completo Bronze → Silver → Gold

```python
def medallion_pipeline():
    """
    Pipeline completo de arquitectura Medallion
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
    
    print("✅ Medallion pipeline completed!")

# Ejecutar pipeline
medallion_pipeline()
```

---

## Time Travel y Versionado

### What is Time Travel?

**Time Travel** is the ability to access **historical versions** of a table. Each write creates a new version.

```
Version 0 ───→ Version 1 ───→ Version 2 ───→ Version 3 (current)
2024-02-01    2024-02-05     2024-02-10     2024-02-12
```

### How It Works at Delta Lake

Delta Lake mantiene un **transaction log** que registra cada cambio:

```
s3://bucket/table/_delta_log/
├── 00000000000000000000.json  # Version 0
├── 00000000000000000001.json  # Version 1
├── 00000000000000000002.json  # Version 2
└── 00000000000000000003.json  # Version 3 (actual)
```

Cada archivo JSON contiene:
- Archivos agregados/removidos
- Operation metadata
- Timestamp
- Metrics (rows, bytes)

### Queries con Time Travel

#### 1. Query por Timestamp

```python
# Leer datos de hace 1 hora
df = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-02-12 09:00:00") \
    .load("s3://lakehouse/silver/events/")

# Leer datos de ayer
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
df = spark.read \
    .format("delta") \
    .option("timestampAsOf", yesterday) \
    .load("s3://lakehouse/silver/events/")
```

#### 2. Query by Version

```python
# Leer versión específica
df = spark.read \
    .format("delta") \
    .option("versionAsOf", 5) \
    .load("s3://lakehouse/silver/events/")
```

### Ver Historial de Versiones

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Ver todas las versiones
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
```

### Rollback to Previous Version

```python
# Opción 1: Restore a versión específica
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")
deltaTable.restoreToVersion(5)  # Volver a versión 5

# Opción 2: Restore a timestamp
deltaTable.restoreToTimestamp("2024-02-10 10:00:00")
```

**⚠️ Caution**: Restore creates a new version, it does not delete subsequent ones.

```
Versiones: 0 → 1 → 2 → 3 → 4 → 5 → 6 (current)
Después de restoreToVersion(3):
Versiones: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 (copia de 3)
```

### Casos de Uso de Time Travel

#### 1. Audit and Compliance

```python
# Recrear estado exacto de datos para auditoría
# "¿Qué datos tenía esta tabla el 2024-01-15?"
df_audit = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-01-15 00:00:00") \
    .load("s3://lakehouse/gold/financial_summary/")

df_audit.write \
    .format("parquet") \
    .save("s3://audit-reports/2024-01-15/financial_summary/")
```

#### 2. Rollback after Error

```python
# Detectaste que el pipeline de ayer tenía un bug
# Rollback a versión anterior
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/transactions/")

# Ver qué pasó
deltaTable.history().filter(col("operation") == "MERGE").show()

# Rollback a versión antes del bug
deltaTable.restoreToVersion(45)  # Versión buena conocida
```

#### 3. Reproducibilidad en ML

```python
# Entrenar modelo con EXACTAMENTE los mismos datos
# Feature store con time travel
training_data = spark.read \
    .format("delta") \
    .option("versionAsOf", 10) \
    .load("s3://lakehouse/gold/user_features/")

model = train_model(training_data)

# Guardar versión usada en metadata del modelo
model_metadata = {
    "model_name": "user_churn_predictor",
    "training_data_version": 10,
    "training_timestamp": "2024-02-10 10:00:00"
}
```

#### 4. Comparar Versiones (Drift Detection)

```python
# Detectar drift en distribución de datos
current_data = spark.read.format("delta").load("s3://lakehouse/silver/events/")

last_week_data = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-02-05 10:00:00") \
    .load("s3://lakehouse/silver/events/")

# Comparar distribuciones
current_stats = current_data.describe()
last_week_stats = last_week_data.describe()

# Detectar cambios significativos
```

---

## Schema Evolution

### What is Schema Evolution?

**Schema Evolution** es la capacidad de **modificar el schema** de una table sin:
- Reescribir todos los datos
- Romper pipelines existentes
- Downtime

### Tipos de Schema Evolution

#### 1. Add Column (Most Common)

```python
# Schema actual:
# user_id, name, email

# Nuevo DataFrame con columna adicional
new_df = spark.read.csv("users_new.csv")
# user_id, name, email, phone

# Escribir con mergeSchema
new_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("s3://lakehouse/silver/users/")

# Resultado:
# Registros antiguos: phone = NULL
# Registros nuevos: phone = valor real
```

**⚠️ Importante**: `mergeSchema` debe estar habilitado.

```python
# Configuración global
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# O por operación
.option("mergeSchema", "true")
```

#### 2. Change Column Type (Cuidado)

Delta Lake permite **ampliar** tipos pero no **reducir**:

✅ **Permitido** (widening):
- `int` → `long`
- `float` → `double`
- `byte` → `int`

❌ **No permitido** (narrowing):
- `long` → `int`
- `double` → `float`
- `string` → `int`

```python
# Cambiar tipo de columna (widening)
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

deltaTable.alterColumn("user_id", "LONG")  # Si era INT
```

Para narrowing, necesitas:
1. Agregar nueva column con tipo deseado
2. Copiar y transformar datos
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
# Opción 1: Leer y reescribir sin la columna
df = spark.read.format("delta").load("s3://lakehouse/silver/users/")
df_without_col = df.drop("deprecated_column")

df_without_col.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("s3://lakehouse/silver/users/")

# Opción 2: Usar DELETE VECTORS (Delta Lake 2.0+)
# No requiere reescribir, marca columna como "deleted"
```

### Schema Enforcement

Delta Lake automatically validates that new data matches the schema:

```python
# Schema actual: user_id (string), name (string), age (int)

# Intento de escribir con schema incompatible
bad_df = spark.createDataFrame([
    ("U001", "John", "twenty-five")  # age es string, debería ser int
], ["user_id", "name", "age"])

try:
    bad_df.write.format("delta").mode("append").save("s3://lakehouse/silver/users/")
except Exception as e:
    print(f"❌ Schema mismatch: {e}")
    # Error: Cannot write data with schema incompatible with table schema
```

### Manejo de Breaking Changes

What to do when you need an incompatible change?

**Strategy 1: Dual Write (Gradual Transition)**

```python
# Paso 1: Crear nueva tabla con nuevo schema
new_users_df.write.format("delta").save("s3://lakehouse/silver/users_v2/")

# Paso 2: Dual write por período de transición
users_df.write.format("delta").mode("append").save("s3://lakehouse/silver/users/")     # Vieja
users_df.write.format("delta").mode("append").save("s3://lakehouse/silver/users_v2/")  # Nueva

# Paso 3: Migrar consumers a users_v2

# Paso 4: Deprecar users (antigua)
```

**Estrategia 2: Shadow Column**

```python
# Mantener ambas versiones de la columna temporalmente
df = df \
    .withColumn("amount_cents", (col("amount_dollars") * 100).cast("long")) \
    .withColumn("amount_dollars_deprecated", col("amount_dollars"))

# Eventualmente eliminar amount_dollars_deprecated
```

**Estrategia 3: Version en Table Name**

```python
# Crear versiones explícitas
s3://lakehouse/silver/events_v1/
s3://lakehouse/silver/events_v2/
s3://lakehouse/silver/events_v3/

# Consumers especifican versión que usan
```

---

## Partitioning Strategies

### Why Partition?

Partitioning physically divides data to:
- ✅ **Mejor performance**: Solo leer particiones necesarias
- ✅ **Better organization**: Data logically grouped
- ✅ **Better maintenance**: Delete old partitions easily

### Partitioning by Date (Most Common)

```python
# Particionar por año/mes/día
df.write \
    .format("delta") \
    .partitionBy("year", "month", "day") \
    .save("s3://lakehouse/silver/events/")

# Estructura física:
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
```

**Ventaja**: Queries con filtro de fecha solo leen particiones necesarias

```python
# Solo lee particiones de febrero 2024
df = spark.read \
    .format("delta") \
    .load("s3://lakehouse/silver/events/") \
    .filter((col("year") == 2024) & (col("month") == 2))

# Pruning: Evita escanear 365 días completos
```

### Category Partitioning

```python
# Particionar por columna categórica
df.write \
    .format("delta") \
    .partitionBy("country", "product_category") \
    .save("s3://lakehouse/silver/sales/")

# Estructura:
s3://lakehouse/silver/sales/
├── country=US/
│   ├── product_category=electronics/
│   ├── product_category=clothing/
│   └── product_category=food/
└── country=UK/
```

**Cuidado**: No particionar por columns con alta cardinalidad

❌ **Malo** (demasiadas particiones):
```python
# user_id tiene millones de valores únicos
df.partitionBy("user_id")  # ❌ Crea millones de directorios
```

✅ **Bueno** (cardinalidad moderada):
```python
# country tiene ~200 valores
df.partitionBy("country")  # ✅ 200 directorios manejables
```

### Reglas de Particionamiento

1. **Cardinalidad**: 100-10,000 particiones ideal
   - Menos de 100: Poco beneficio
   - More than 10,000: Metadata Overhead

2. **Partition size**: 1GB per partition ideal
   ```python
   # Muy pequeño ❌
   # 10,000 partitions × 10MB = 100GB total
   # Demasiadas particiones pequeñas
   
   # Ideal ✅
   # 100 partitions × 1GB = 100GB total
   ```

3. **Query patterns**: Particionar por columns filtradas frecuentemente
   ```python
   # Si queries siempre filtran por fecha y región
   SELECT * FROM events WHERE date = '2024-02-12' AND region = 'US'
   
   # Particionar por esas columnas
   df.partitionBy("date", "region")
   ```

4. **Evolution**: You cannot change partitioning without rewriting
   - Delta Lake: NO soporta partition evolution
   - Iceberg: YES supports partition evolution

### Partition Pruning

Spark automatically **removes partitions** that do not match filters:

```python
# Tabla particionada por date
df = spark.read.format("delta").load("s3://lakehouse/silver/events/")

# Query con filtro de date
result = df.filter(col("date") == "2024-02-12")

# Spark solo lee:
# s3://lakehouse/silver/events/date=2024-02-12/
# ✅ No escanea otras 364 fechas
```

**See pruning in action**:

```python
# Explain plan para ver pruning
df.filter(col("date") == "2024-02-12").explain()

# Output muestra:
# PartitionFilters: [isnotnull(date#0), (date#0 = 2024-02-12)]
# PushedFilters: []
# ReadSchema: struct<event_id:string, ...>
# (1 of 365 partitions)
```

---

## Optimizaciones de Performance

### 1. Z-Ordering

**Z-ordering** places related data physically close to improve **data skipping**.

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Optimizar por columnas frecuentemente filtradas
deltaTable.optimize().executeZOrderBy("user_id", "event_type")
```

**How ​​it works**:

```
Sin Z-ordering:
File 1: [user=A,type=click], [user=Z,type=view], [user=B,type=purchase]
File 2: [user=A,type=view], [user=Y,type=click], [user=C,type=purchase]
→ Query "user=A" debe leer ambos archivos

Con Z-ordering:
File 1: [user=A,type=click], [user=A,type=view], [user=B,type=click]
File 2: [user=Y,type=view], [user=Z,type=view], [user=C,type=purchase]
→ Query "user=A" solo lee File 1 ✅
```

**When to use**:
- columns filtradas frecuentemente
- Alta cardinalidad (user_id, product_id)
- NO usar para particiones (redundante)

### 2. Compaction

Over time, Delta tables accumulate many small files:

```
s3://lakehouse/silver/events/date=2024-02-12/
├── part-00001.parquet (10MB)
├── part-00002.parquet (8MB)
├── part-00003.parquet (15MB)
...
├── part-01000.parquet (5MB)
```

**Problem**: Reading 1000 small files is **much slower** than reading 10 large files.

**Solution**: Compaction (combine files)

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Compaction: Combinar archivos pequeños
deltaTable.optimize().executeCompaction()

# Resultado:
# part-00001.parquet (10MB) + part-00002.parquet (8MB) + ...
# → combined-00001.parquet (1GB)
```

**Configuration**:

```python
# Target file size (default: 1GB)
spark.conf.set("spark.databricks.delta.optimize.maxFileSize", "1073741824")  # 1GB

# Compaction automático en write
df.write \
    .format("delta") \
    .option("optimizeWrite", "true") \
    .save("s3://lakehouse/silver/events/")
```

### 3. Data Skipping

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

**Data skipping**: Skip archivos donde min/max no cumplen filtros

```python
# Query con filtro
df = spark.read.format("delta").load("s3://lakehouse/silver/events/") \
    .filter(col("user_id") == "M500")

# Delta Lake:
# - File 1: min=A001, max=K999 → SKIP ✅
# - File 2: min=L000, max=P999 → READ (contiene M500)
# - File 3: min=Q000, max=Z999 → SKIP ✅
```

**Habilitar data skipping stats**:

```python
spark.conf.set("spark.databricks.delta.properties.defaults.dataSkippingNumIndexedCols", "32")
```

### 4. Caching

Para queries repetitivos en mismos datos:

```python
# Cache DataFrame en memoria
df = spark.read.format("delta").load("s3://lakehouse/silver/events/")
df.cache()

# Queries subsecuentes son instantáneos
result1 = df.filter(col("event_type") == "click").count()  # Lee S3
result2 = df.filter(col("event_type") == "view").count()   # Lee cache ⚡

# Liberar cache cuando no se necesite más
df.unpersist()
```

**Automatic cache with OPTIMIZE**:

```python
# OPTIMIZE + CACHE juntos
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/gold/daily_summary/")
deltaTable.optimize().executeCompaction()

spark.read.format("delta").load("s3://lakehouse/gold/daily_summary/").cache()
```

---

## Data Lifecycle Management

### Vacuum: Eliminar Archivos Antiguos

Delta Lake mantiene **versiones antiguas** para time travel, pero ocupan espacio.

**VACUUM** elimina archivos no referenciados:

```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/events/")

# Eliminar archivos no usados hace más de 7 días
deltaTable.vacuum(retentionHours=168)  # 7 días × 24 horas

# Output:
# Deleted 1250 files (15.3 GB) from s3://lakehouse/silver/events/
```

**⚠️ Important**: You cannot do time travel beyond retentionHours

```python
# Después de vacuum(168):
df = spark.read \
    .format("delta") \
    .option("timestampAsOf", "2024-02-01") \  # Hace 15 días
    .load("s3://lakehouse/silver/events/")
# ❌ Error: Files no longer exist
```

**Safety check** (minimum retention 7 days):

```python
# Por defecto, no puedes vacuum con menos de 7 días
deltaTable.vacuum(24)  # ❌ Error

# Override (úsalo solo si sabes lo que haces)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
deltaTable.vacuum(0)  # Elimina TODO inmediatamente
```

### Retention Policies

Implement retention policies:

```python
def apply_retention_policy(table_path, retention_days):
    """
    Eliminar particiones antiguas según política de retención
    """
    from datetime import datetime, timedelta
    from delta.tables import DeltaTable
    
    # Fecha límite
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    
    # Leer tabla
    df = spark.read.format("delta").load(table_path)
    
    # Eliminar particiones antiguas
    deltaTable = DeltaTable.forPath(spark, table_path)
    deltaTable.delete(f"date < '{cutoff_date}'")
    
    # Vacuum para liberar espacio
    deltaTable.vacuum(retentionHours=24)
    
    print(f"✅ Deleted partitions older than {cutoff_date}")

# Aplicar políticas diferentes por capa
apply_retention_policy("s3://lakehouse/bronze/logs/", retention_days=30)    # 30 días
apply_retention_policy("s3://lakehouse/silver/events/", retention_days=90)  # 90 días
apply_retention_policy("s3://lakehouse/gold/summary/", retention_days=365)  # 1 año
```

---

## Patrones de Ingesta

### 1. Append-Only (Simpler)

```python
# Cada día agrega nuevos datos
df_today = spark.read.parquet("s3://raw/events/2024-02-12/")

df_today.write \
    .format("delta") \
    .mode("append") \
    .save("s3://lakehouse/bronze/events/")
```

**Pros**: Simple, fast, does not duplicate
**Cons**: No maneja updates/deletes

### 2. Upsert (MERGE)

```python
from delta.tables import DeltaTable

# Leer nuevos datos
new_data = spark.read.parquet("s3://raw/users/latest/")

# Tabla existente
deltaTable = DeltaTable.forPath(spark, "s3://lakehouse/silver/users/")

# MERGE: Insert si no existe, Update si existe
deltaTable.alias("target").merge(
    new_data.alias("source"),
    "target.user_id = source.user_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```

**Pros**: Maneja updates y inserts  
**Cons**: Slower than append

### 3. SCD Type 2 (Slowly Changing Dimensions)

Mantener historial completo de cambios:

```python
from pyspark.sql.functions import current_timestamp, lit

# Nuevos datos
new_data = spark.read.csv("users_updates.csv")

# Marcar registros actuales como expirados
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
```

---

## Resumen

### Key Takeaways

1. **Medallion Architecture**: Bronze (raw) → Silver (refined) → Gold (aggregated)
2. **Time Travel**: Access historical versions for auditing and reproducibility
3. **Schema Evolution**: Modifica schemas sin downtime con `mergeSchema`
4. **Partitioning**: Mejora performance con particiones de 1GB y cardinalidad moderada
5. **Optimizaciones**: Z-ordering, compaction, data skipping, caching
6. **Lifecycle**: VACUUM para liberar espacio, retention policies por capa
7. **Ingesta**: Append (simple), MERGE (upserts), SCD Type 2 (historial)

### Next Steps

Ahora que dominas la arquitectura y patrones, exploraremos:

- **resources adicionales** ([03-resources.md](03-resources.md))
- **Practical exercises** to implement everything learned

---

**Last update**: February 2026
**Tiempo de lectura**: ~60 minutos  
**Nivel**: Avanzado
