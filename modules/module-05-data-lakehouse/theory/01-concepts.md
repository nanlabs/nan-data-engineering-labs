# Fundamental Concepts of data Lakehouse

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Evolution of data Architectures](#evolution-of-data-architectures)
3. [data Lake: The First Paradigm](#data-lake-the-first-paradigm)
4. [data Warehouse: The Traditional Paradigm](#data-warehouse-the-traditional-paradigm)
5. [data Lakehouse: The Best of Both Worlds](#data-lakehouse-the-best-of-both-worlds)
6. [Table Formats in Lakehouse](#table-formats-in-lakehouse)
7. [ACID in Distributed Systems](#acid-in-distributed-systems)
8. [Use Cases and When to Use Each Architecture](#use-cases-and-when-to-use-each-architecture)

---

## Introduction

The **data Lakehouse** represents the most recent evolution in data storage and processing architectures. It combines the **flexibility and low cost** of data Lakes with the **reliability and performance** of data Warehouses, creating to unified platform for analytics, business intelligence and machine learning.

### Why did the data Lakehouse emerge?

Over the past decade, organizations faced to dilemma:

- **data Lakes**: Economical and flexible, but without quality or transactionality guarantees
- **data Warehouses**: Reliable and fast, but expensive and rigid

This dilemma led to complex architectures where data moved between multIPle systems:

```text
Sources → data Lake → ETL → data Warehouse → BI Tools
                   ↓
                  ML/AI Tools
```text

**Problems of this arquitectura**:

- 🔴 Duplicate data on multIPle systems
- 🔴 synchronization compleja and costosa
- 🔴 Inconsistencys entre sistopics
- 🔴 Altos costos of storage and transferencia
- 🔴 latency in la availability of datas

El **data Lakehouse** elimina this complejidad:

```text
Sources → data Lakehouse → BI Tools + ML/AI Tools
          (Single Source of Truth)
```

---

## Evolution of data Architectures

### 📊 Evolution Timeline

```text
1990s: data Warehouses
   ↓   (Teradata, Oracle, SQL Server)
   ↓   ✅ ACID, performance
   ↓   ❌ Costoso, rígido
   ↓
2010s: data Lakes
   ↓   (Hadoop, S3, Azure data Lake)
   ↓   ✅ Bajo costo, flexible
   ↓   ❌ without ACID, "data swamp"
   ↓
2015+: Lambda Architecture
   ↓   (Batch + Stream layers)
   ↓   ✅ Real-time + batch
   ↓   ❌ Complejidad operacional
   ↓
2020+: data Lakehouse
       (Delta Lake, Iceberg, Hudi)
       ✅ ACID + flexibilidad + bajo costo
       ✅ Unified batch + streaming
```text

### 🎯 Factores que Impulsaron el Change

1. **Cloud Storage**: S3, Azure Blob, GCS offer extremely economical storage
2. **Open Formats**: Parquet and ORC permiten readings eficientes
3. **Metadata Layers**: Delta Lake, Iceberg agregaron ACID sobre object storage
4. **Compute Separation**: Motores como Spark, Presto they can leer el mismo storage
5. **ML Workloads**: Necesidad of access directo to datas raw without ETL

---

## data Lake: El Primer Paradigma

### 🌊 Definition

to **data Lake** is to centralized repository that stores **all of an organization's data** in its NATive format (structunetwork, semi-structunetwork, unstructunetwork).

### Typical Architecture

```text
┌─────────────────────────────────────────────┐
│              data Lake (S3/HDFS)            │
│  ┌────────┐  ┌────────┐  ┌─────────┐      │
│  │  CSV   │  │  JSON  │  │ Parquet │      │
│  │ Files  │  │ Files  │  │  Files  │      │
│  └────────┘  └────────┘  └─────────┘      │
│                                             │
│  /raw/         /processed/    /curated/    │
└─────────────────────────────────────────────┘
         ↓              ↓              ↓
    Spark/Hive    Presto/Athena   Networkshift
```

### ✅ Ventajas

1. **Bajo costo**: ~$23/TB/mes in S3 Standard
2. **Flexibilidad**: Cualquier formato of datas
3. **scalability**: Petabytes without problems
4. **Schema-on-read**: not necesitas definir schema to the escribir
5. **ML-friendly**: Access directo for Python/Spark
6. **Decoupling**: Storage separado of compute

### ❌ Desventajas

1. **not ACID**: not atomic transactions

   ```python
   # Problem: Readings inconsistentes
   # Process 1 is escribiendo 100 archivos
   # Process 2 lee mientras se escribe → datas parciales ❌
   ```text

2. **without Time Travel**: not you can to return to versiones anteriores

   ```bash
   # if sobreescribes datas, se pierden for siempre
   $ aws s3 cp new_data.parquet s3://bucket/path/data.parquet
   # ❌ Los datas anteriores se perdieron
   ```

3. **without Schema Enforcement**: you can escribir basura

   ```python
   # Día 1: Schema correcto
   df1 = pd.DataFrame({"id": [1, 2], "amount": [100.0, 200.0]})
   
   # Día 2: someone cambia el schema (without to want)
   df2 = pd.DataFrame({"id": ["to", "b"], "amount": ["100", "200"]})
   # ❌ Ahora you have types inconsistentes
   ```text

4. **Metadata Pesada**: Leer 10,000 archivos is lento

   ```python
   # Spark necesita list todos los archivos
   spark.read.parquet("s3://bucket/partitioned-table/*/*/*/")
   # ⏱️ 30+ segundos only listando archivos
   ```

5. **"data Swamp"**: Without governance, it becomes chaotic
   - What data is current?
   - Who owns this dataset?
   - What does this column mean?

### 🎯 Caso of Uso Ideal

- **Archiving**: Store historical logs
- **data Science**: Ad-hoc exploration
- **Raw data**: Almacenar datas tal como llegan

---

## data Warehouse: El Paradigma Tradicional

### 🏢 Definition

to **data Warehouse** is an analytics-optimized database with pre-defined schema, complex queries, and high concurrency.

### Typical Architecture

```text
┌────────────────────────────────────────────┐
│       data Warehouse (Networkshift/Snowflake)  │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │      Columnr Storage Engine         │ │
│  │  ┌─────────┐  ┌──────────┐          │ │
│  │  │ Fact    │  │ Dimension│          │ │
│  │  │ Tables  │  │ Tables   │          │ │
│  │  └─────────┘  └──────────┘          │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  Features:                                 │
│  • ACID Transactions                       │
│  • Indexes & Materialized Views            │
│  • Query Optimizer                         │
│  • Compression                             │
└────────────────────────────────────────────┘
```text

### ✅ Ventajas

1. **Full ACID**: Transactional guarantees

   ```sql
   BEGIN TRANSACTION;
   UPDATE accounts SET balance = balance - 100 WHERE id = 1;
   UPDATE accounts SET balance = balance + 100 WHERE id = 2;
   COMMIT;
   -- ✅ or ambas suceden, or ninguna (atomicidad)
   ```

2. **Performance BI**: Optimizado for queries complejas

   ```sql
   -- Queries with múltIPles joins are rápidos
   SELECT
       d.year, d.month,
       p.category,
       SUM(f.revenue) as total_revenue
   FROM fact_sales f
   JOIN dim_date d ON f.date_id = d.id
   JOIN dim_product p ON f.product_id = p.id
   GROUP BY 1, 2, 3;
   -- ⚡ Segundos, not minutos
   ```text

3. **Schema Enforcement**: Automatic validation

   ```sql
   -- El warehouse valida tIPos and constraints
   INSERT INTO users (id, email, age)
   VALUES (1, 'invalid-email', -5);
   -- ❌ Error: email format invalid, age < 0
   ```

4. **Concurrency**: Thousands of simultaneous users
   - MVCC (Multi-Version Concurrency Controle)
   - Query queuing and prioritization

5. **Governance**: Audit, permissions, lineage

### ❌ Desventajas

1. **High Cost**: $3,000-$10,000+/TB/year

   ```text
   Networkshift: $0.25/hora × 24 × 365 = $2,190/año (mínimo)
   Snowflake: ~$40/TB/mes storage + $2-$4/cnetworkit compute
   ```

2. **Rigid Schema**: Difficult to change schema

   ```sql
   -- Agregar column he/she can tomar horas in tables grandes
   ALTER TABLE events ADD COLUMN user_segment VARCHAR(50);
   -- ⏱️ 4 horas in table of 10B rows
   ```text

3. **Structunetwork data only**: Does not support nested JSON, XML, images

   ```sql
   -- ❌ not you can to make esto eficientemente:
   SELECT json_extract(event_data, '$.user.preferences.notifications')
   FROM events;
   ```

4. **Not ML-Friendly**: Difficult to access for Python/Spark

   ```python
   # Necesitas exportar datas primero
   # Networkshift → S3 → Spark → Train model
   # ⏱️ Latency and costos of transferencia
   ```text

5. **Vendor Lock-in**: Formato propietario
   - You can't easily move between Snowflake ↔ Networkshift
   - Dependencia of the proveedor

### 🎯 Caso of Uso Ideal

- **BI/Dashboards**: Queries complejas, baja latency
- **Financial Reporting**: Critical ACID
- **High Concurrency**: Hundnetworks of simultaneous users

---

## data Lakehouse: Lo Mejor of Ambos Mundos

### 🏛️ Definition

Un **data Lakehouse** is una arquitectura que implementa structures and features of data warehouses **directamente sobre data lakes** utilizando formatos of table open-source.

### Arquitectura of the Lakehouse

```text
┌───────────────────────────────────────────────────────┐
│                   data LAKEHOUSE                       │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │         Table Format Layer                    │    │
│  │    (Delta Lake / Iceberg / Hudi)              │    │
│  │  • Transaction Log                            │    │
│  │  • Metadata Management                        │    │
│  │  • ACID Guarantees                            │    │
│  │  • Time Travel                                │    │
│  │  • Schema Evolution                           │    │
│  └──────────────────────────────────────────────┘    │
│                     ↓                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │         data Files (Parquet/ORC)              │    │
│  │  s3://bucket/table/                           │    │
│  │    ├── part-00000.parquet                     │    │
│  │    ├── part-00001.parquet                     │    │
│  │    └── part-00002.parquet                     │    │
│  └──────────────────────────────────────────────┘    │
│                     ↓                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │      Object Storage (S3/ADLS/GCS)             │    │
│  │  Bajo costo, escalable, durable               │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Query Engines (Multi-Engine Support):                │
│  ├─ Spark (Batch Processing)                          │
│  ├─ Presto/Trino (Interactive SQL)                    │
│  ├─ Flink (Streaming)                                 │
│  └─ Pandas/Dask (data Science)                        │
└───────────────────────────────────────────────────────┘
```

### 🎯 PrincIPios Key of the Lakehouse

#### 1. ACID Transactions

ACID guarantees on object storage (S3, ADLS, GCS):

```python
# Delta Lake example
from delta.tables import DeltaTable

# ✅ ACID Write - everything or nothing
df.write.format("delta").mode("overwrite").save("/path/to/table")

# ✅ ACID Update - transaction atómica
deltaTable = DeltaTable.forPath(spark, "/path/to/table")
deltaTable.update(
    condition="status = 'pending'",
    set={"status": "'processed'", "updated_at": "current_timestamp()"}
)
```text

**How ​​it works**:

- Transaction log (`_delta_log/`) rastrea todas las operaciones
- Atomic commit: either the entire batch is written, or nothing
- Isolation: lectores they see snapshot consistente

#### 2. Time Travel (data Versioning)

Access to historical versions:

```python
# Leer version 10 minutos atrás
df = spark.read.format("delta") \
    .option("timestampAsOf", "2024-02-12 10:00:00") \
    .load("/path/to/table")

# Leer version específica
df = spark.read.format("delta") \
    .option("versionAsOf", 5) \
    .load("/path/to/table")

# to see historial completo
deltaTable.history().show()
```text

**Casos of uso**:

- Audit and compliance
- Rolelback after errors
- Reproducibilidad in ML (entrenar with mismos datas)

#### 3. Schema Evolution

Evolucionar schema without romper pIPelines:

```python
# Agregar column automáticamente
df_with_new_col.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("/path/to/table")

# El schema anterior sigue siendo válido
# Nuevas columns aparecen como NULL in records anteriores
```text

#### 4. Unified Batch + Streaming

Misma table for ambos workloads:

```python
# Batch write
df_batch.write.format("delta").save("/path/to/table")

# Streaming write to la misma table
df_stream.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/checkpoints/") \
    .start("/path/to/table")

# Streaming read
df_stream_read = spark.readStream.format("delta").load("/path/to/table")
```

#### 5. Open Format

not vendor lock-in, multIPle engines:

```python
# Spark
df = spark.read.format("delta").load("s3://bucket/table")

# Presto/Trino
# SELECT * FROM delta.default.table

# Pandas (via deltalake library)
from deltalake import DeltaTable
dt = DeltaTable("s3://bucket/table")
df = dt.to_pandas()
```text

### ✅ Ventajas of the Lakehouse

| Aspecto | data Lake | data Warehouse | data Lakehouse |
|---------|-----------|----------------|----------------|
| **Costo** | 💰 $23/TB/mes | 💰💰💰 $250+/TB/mes | 💰💰 $40/TB/mes |
| **ACID** | ❌ not | ✅ Yes | ✅ Yes |
| **Performance** | ⚠️ Slow | ✅ Fast | ✅ Fast |
| **Flexibilidad** | ✅ Todos los formatos | ❌ only structunetwork | ✅ Todos los formatos |
| **Time Travel** | ❌ not | ⚠️ Limitado | ✅ Yes (completo) |
| **ML Support** | ✅ Excelente | ❌ Limitado | ✅ Excelente |
| **Schema Evolution** | ⚠️ Manual | ❌ Difficult | ✅ Automatic |
| **Streaming** | ⚠️ Complejo | ❌ not soportado | ✅ Nativo |
| **Open Format** | ✅ Yes | ❌ Propietario | ✅ Yes |

### ❌ Desventajas/Limitaciones

1. **Complejidad Inicial**: Curva of aprendizaje
2. **Overhead of Metadata**: Transaction log he/she can crecer
3. **Requiere Tuning**: Compaction, partitioning, etc.
4. **Maturity**: Less mature than traditional warehouses (but evolving quickly)

### 🎯 Caso of Uso Ideal

- **everything**: BI, ML, Real-time analytics in una plataforma
- **Networkucir costos** manteniendo reliability
- **Unificar arquitectura** (eliminar silos)

---

## Formatos of table in Lakehouse

Existen tres formatos princIPales of table open-source:

### 1. Delta Lake (Databricks)

**features**:

- Transaction log in JSON (`_delta_log/`)
- Optimistic concurrency controle
- ACID via single log
- Better integration with Spark

**Strengths**:

- ✅ Madurez and estabilidad
- ✅ Performance in Spark
- ✅ Documentation and community
- ✅ Upserts eficientes (MERGE)

**Weaknesses**:

- ⚠️ Optimizado for Spark (otros engines with limitaciones)
- ⚠️ Log he/she can crecer in tables with muchas actualizaciones

**When to use**:

- PIPelines batch pesados in Spark
- Necesitas MERGE/UPSERT frecuente
- Ecosistopic Databricks

### 2. Apache Iceberg (Netflix → Apache)

**features**:

- Metadata in Avro/Parquet
- Hidden partitioning (particiones transparentes)
- Partition evolution (cambiar estrategia without reescribir)
- Multi-engine by design

**Strengths**:

- ✅ Multi-engine (Spark, Flink, Presto, Trino)
- ✅ Partition evolution
- ✅ Hidden partitioning (easier for users)
- ✅ Snapshots eficientes

**Weaknesses**:

- ⚠️ less maduro que Delta
- ⚠️ Metadata complexity in tables grandes

**When to use**:

- MultIPle query engines
- Streaming with Flink
- Necesitas partition evolution

### 3. Apache Hudi (Uber → Apache)

**features**:

- Copy-on-Write and Merge-on-Read
- Incremental processing
- Record-level updates

**Strengths**:

- ✅ Updates incrementales eficientes
- ✅ CDC (Change data Capture) NATivo
- ✅ Easily configurable data retention

**Weaknesses**:

- ⚠️ Complejidad in tuning
- ⚠️ less adoption que Delta/Iceberg

**When to use**:

- CDC pIPelines
- Updates frecuentes row-level
- Ecosistopic AWS (EMR he/she has support NATivo)

### Direct Comparison

| feature | Delta Lake | Iceberg | Hudi |
|----------------|------------|---------|------|
| **ACID** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Time Travel** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Schema Evolution** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Partition Evolution** | ❌ not | ✅ Yes | ❌ not |
| **Hidden Partitioning** | ❌ not | ✅ Yes | ❌ not |
| **Multi-Engine** | ⚠️ Limitado | ✅ Excelente | ⚠️ Limitado |
| **Streaming** | ✅ Spark Streaming | ✅ Flink, Spark | ✅ Spark Streaming |
| **Upserts** | ✅ MERGE | ⚠️ Overwrite | ✅ Upsert (MoR) |
| **Madurez** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Comunit** | Grande | Grande | Mediana |

---

## ACID in Sistopics Distribuidos

### What is ACID?

ACID are fundamental guarantees in databases:

- **to**tomicity: everything or nothing
- **C**onsistency: Always valid business rules
- **I**solation: transactions concurrentes not interfieren
- **D**urability: Datas committed not se pierden

### The Challenge in Object Storage

Object storage (S3, ADLS, GCS) **no** provee ACID NATivamente:

```python
# ❌ Problem: not is atómico
for file in files:
    s3.put_object(Bucket='mybucket', Key=file, Body=data)
    # if falla in the file 50 of 100, ¿what pasa?
    # you have datas parciales ❌
```text

### How Delta Lake Implements ACID

Delta Lake usa un **transaction log** for coordinar escrituras:

```text
s3://bucket/table/
├── _delta_log/
│   ├── 00000000000000000000.json  # Version 0
│   ├── 00000000000000000001.json  # Version 1
│   ├── 00000000000000000002.json  # Version 2
│   └── 00000000000000000010.checkpoint.parquet
├── part-00000-abc123.snappy.parquet
├── part-00001-def456.snappy.parquet
└── part-00002-ghi789.snappy.parquet
```

#### Transaction Log

Cada commit genera un archivo JSON in `_delta_log/`:

```json
{
  "commitInfo": {
    "timestamp": 1707724800000,
    "operation": "WRITE",
    "operationMetrics": {"numFiles": "3", "numOutputRows": "1000000"}
  },
  "add": {
    "path": "part-00000-abc123.snappy.parquet",
    "size": 10485760,
    "modificationTime": 1707724800000,
    "dataChange": true,
    "stats": "{\"numRecords\": 500000, \"minValues\": {...}, \"maxValues\": {...}}"
  }
}
```text

#### Atomicidad

1. Escritor escribe archivos Parquet
2. Escritor crea archivo JSON in `_delta_log/`
3. **Atomic rename** (guaranteed by S3)
4. If it fails before rename → transaction did not happen
5. if rename exitoso → transaction committed

```python
# Delta Lake garantiza atomicidad
df.write.format("delta").mode("append").save("/path/to/table")
# or todos los records se escriben, or ninguno ✅
```text

#### Isolation

- **Optimistic Concurrency Controle** (OCC)
- MultIPle writers can work simultaneously
- in commit, se valida que not has conflictos
- If conflict → automatic retry

```python
# Writer 1 and Writer 2 escriben in paralelo
# Delta Lake detecta conflicto and he/she makes retry automático
# Ambos commits are serializables ✅
```text

#### Consistency & Durability

- **Consistency**: Schema enforcement + CHECK constraints
- **Durability**: Once committed, the log guarantees no-loss

---

## Use Cases and When to Use Each Architecture

### data Lake

**Usa when**:

- Archiving of historical data (logs, events)
- Ad-hoc exploration without defined schema
- Presupuesto limitado
- not necesitas ACID

**Examples**:

- Application logs (30 day retention)
- Archivos raw of IoT devices
- data science exploration

### data Warehouse

**Usa when**:

- Critical BI with strict SLAs (<1s)
- High concurrency (100+ users)
- Queries extremadamente complejas
- Budget is not to limitation

**Examples**:

- Dashboards ejecutivos
- Financial reporting
- Sales analytics with miles of users

### data Lakehouse

**Usa when**:

- you want unificar BI + ML in una plataforma
- Necesitas ACID + bajo costo
- you have workloads batch + streaming
- you want evitar silos of datas

**Examples**:

- Plataforma of analytics moderna
- ML feature stores
- Real-time + historical analytics
- Networkucir costos manteniendo calidad

### Quick Decision table

| Question | Lake | Warehouse | Lakehouse |
|----------|------|-----------|-----------|
| Do you need ACID? | ❌ | ✅ | ✅ |
| Limited budget? | ✅ | ❌ | ✅ |
| ML workloads? | ✅ | ❌ | ✅ |
| BI critical (<1s)? | ❌ | ✅ | ⚠️ |
| 100+ concurrent users? | ❌ | ✅ | ⚠️ |
| Streaming + batch? | ⚠️ | ❌ | ✅ |
| Flexible schema? | ✅ | ❌ | ✅ |
| Time travel necessary? | ❌ | ⚠️ | ✅ |

---

## Resumen

### Key Takeaways

1. **data Lakehouse** = data Lake + data Warehouse features
2. **Formatos of table** (Delta, Iceberg, Hudi) agregan ACID sobre object storage
3. **ACID in distributed systems** requiere transaction log and coordiNATion
4. **Delta Lake** is the most mature format (70% of this module)
5. **Apache Iceberg** stands out in multi-engine and partition evolution (30% of this module)
6. The choice depends on your specific requirements (cost, performance, features)

### Next Steps

Ahora que comprendes los conceptos fundamentales, continuaremos with:

1. **Arquitectura** ([02-architecture.md](02-architecture.md)): Patrones como Medallion, optimizaciones
2. **resources** ([03-resources.md](03-resources.md)): Official documentation, papers, guides
3. **Practical exercises**: Implement what you learned with Delta Lake and Iceberg

---

**Last update**: February 2026
**Tiempo of reading**: ~45 minutos  
**Nivel**: Intermedio-Avanzado
