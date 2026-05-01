# Fundamental Concepts of Data Lakehouse

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Evolution of Data Architectures](#evolution-of-data-architectures)
3. [Data Lake: The First Paradigm](#data-lake-the-first-paradigm)
4. [Data Warehouse: The Traditional Paradigm](#data-warehouse-the-traditional-paradigm)
5. [Data Lakehouse: The Best of Both Worlds](#data-lakehouse-the-best-of-both-worlds)
6. [Table Formats in Lakehouse](#table-formats-in-lakehouse)
7. [ACID in Distributed Systems](#acid-in-distributed-systems)
8. [Use Cases and When to Use Each Architecture](#use-cases-and-when-to-use-each-architecture)

---

## Introduction

The **Data Lakehouse** represents the most recent evolution in data storage and processing architectures. It combines the **flexibility and low cost** of Data Lakes with the **reliability and performance** of Data Warehouses, creating a unified platform for analytics, business intelligence and machine learning.

### Why did the Data Lakehouse emerge?

Over the past decade, organizations faced a dilemma:

- **Data Lakes**: Economical and flexible, but without quality or transactionality guarantees
- **Data Warehouses**: Reliable and fast, but expensive and rigid

This dilemma led to complex architectures where data moved between multiple systems:

```
Sources → Data Lake → ETL → Data Warehouse → BI Tools
                   ↓
                  ML/AI Tools
```

**Problemas de esta arquitectura**:
- 🔴 Duplicate data on multiple systems
- 🔴 synchronization compleja y costosa
- 🔴 Inconsistencias entre sistemas
- 🔴 Altos costos de storage y transferencia
- 🔴 latency en la availability de datos

El **Data Lakehouse** elimina esta complejidad:

```
Sources → Data Lakehouse → BI Tools + ML/AI Tools
          (Single Source of Truth)
```

---

## Evolution of Data Architectures

### 📊 Evolution Timeline

```
1990s: Data Warehouses
   ↓   (Teradata, Oracle, SQL Server)
   ↓   ✅ ACID, performance
   ↓   ❌ Costoso, rígido
   ↓
2010s: Data Lakes
   ↓   (Hadoop, S3, Azure Data Lake)
   ↓   ✅ Bajo costo, flexible
   ↓   ❌ Sin ACID, "data swamp"
   ↓
2015+: Lambda Architecture
   ↓   (Batch + Stream layers)
   ↓   ✅ Real-time + batch
   ↓   ❌ Complejidad operacional
   ↓
2020+: Data Lakehouse
       (Delta Lake, Iceberg, Hudi)
       ✅ ACID + flexibilidad + bajo costo
       ✅ Unified batch + streaming
```

### 🎯 Factores que Impulsaron el Cambio

1. **Cloud Storage**: S3, Azure Blob, GCS offer extremely economical storage
2. **Open Formats**: Parquet y ORC permiten lecturas eficientes
3. **Metadata Layers**: Delta Lake, Iceberg agregaron ACID sobre object storage
4. **Compute Separation**: Motores como Spark, Presto pueden leer el mismo storage
5. **ML Workloads**: Necesidad de acceso directo a datos raw sin ETL

---

## Data Lake: El Primer Paradigma

### 🌊 Definition

A **Data Lake** is a centralized repository that stores **all of an organization's data** in its native format (structured, semi-structured, unstructured).

### Typical Architecture

```
┌─────────────────────────────────────────────┐
│              Data Lake (S3/HDFS)            │
│  ┌────────┐  ┌────────┐  ┌─────────┐      │
│  │  CSV   │  │  JSON  │  │ Parquet │      │
│  │ Files  │  │ Files  │  │  Files  │      │
│  └────────┘  └────────┘  └─────────┘      │
│                                             │
│  /raw/         /processed/    /curated/    │
└─────────────────────────────────────────────┘
         ↓              ↓              ↓
    Spark/Hive    Presto/Athena   Redshift
```

### ✅ Ventajas

1. **Bajo costo**: ~$23/TB/mes en S3 Standard
2. **Flexibilidad**: Cualquier formato de datos
3. **scalability**: Petabytes sin problemas
4. **Schema-on-read**: No necesitas definir schema al escribir
5. **ML-friendly**: Acceso directo para Python/Spark
6. **Decoupling**: Storage separado de compute

### ❌ Desventajas

1. **No ACID**: No atomic transactions
   ```python
   # Problema: Lecturas inconsistentes
   # Proceso 1 está escribiendo 100 archivos
   # Proceso 2 lee mientras se escribe → datos parciales ❌
   ```

2. **Sin Time Travel**: No puedes volver a versiones anteriores
   ```bash
   # Si sobreescribes datos, se pierden para siempre
   $ aws s3 cp new_data.parquet s3://bucket/path/data.parquet
   # ❌ Los datos anteriores se perdieron
   ```

3. **Sin Schema Enforcement**: Puedes escribir basura
   ```python
   # Día 1: Schema correcto
   df1 = pd.DataFrame({"id": [1, 2], "amount": [100.0, 200.0]})
   
   # Día 2: Alguien cambia el schema (sin querer)
   df2 = pd.DataFrame({"id": ["a", "b"], "amount": ["100", "200"]})
   # ❌ Ahora tienes types inconsistentes
   ```

4. **Metadata Pesada**: Leer 10,000 archivos es lento
   ```python
   # Spark necesita list todos los archivos
   spark.read.parquet("s3://bucket/partitioned-table/*/*/*/")
   # ⏱️ 30+ segundos solo listando archivos
   ```

5. **"Data Swamp"**: Without governance, it becomes chaotic
   - What data is current?
   - Who owns this dataset?
   - What does this column mean?

### 🎯 Caso de Uso Ideal

- **Archiving**: Store historical logs
- **Data Science**: Ad-hoc exploration
- **Raw Data**: Almacenar datos tal como llegan

---

## Data Warehouse: El Paradigma Tradicional

### 🏢 Definition

A **Data Warehouse** is an analytics-optimized database with pre-defined schema, complex queries, and high concurrency.

### Typical Architecture

```
┌────────────────────────────────────────────┐
│       Data Warehouse (Redshift/Snowflake)  │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │      Columnar Storage Engine         │ │
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
```

### ✅ Ventajas

1. **Full ACID**: Transactional guarantees
   ```sql
   BEGIN TRANSACTION;
   UPDATE accounts SET balance = balance - 100 WHERE id = 1;
   UPDATE accounts SET balance = balance + 100 WHERE id = 2;
   COMMIT;
   -- ✅ O ambas suceden, o ninguna (atomicidad)
   ```

2. **Performance BI**: Optimizado para queries complejas
   ```sql
   -- Queries con múltiples joins son rápidos
   SELECT
       d.year, d.month,
       p.category,
       SUM(f.revenue) as total_revenue
   FROM fact_sales f
   JOIN dim_date d ON f.date_id = d.id
   JOIN dim_product p ON f.product_id = p.id
   GROUP BY 1, 2, 3;
   -- ⚡ Segundos, no minutos
   ```

3. **Schema Enforcement**: Automatic validation
   ```sql
   -- El warehouse valida tipos y constraints
   INSERT INTO users (id, email, age)
   VALUES (1, 'invalid-email', -5);
   -- ❌ Error: email format invalid, age < 0
   ```

4. **Concurrency**: Thousands of simultaneous users
   - MVCC (Multi-Version Concurrency Control)
   - Query queuing and prioritization

5. **Governance**: Audit, permissions, lineage

### ❌ Desventajas

1. **High Cost**: $3,000-$10,000+/TB/year
   ```
   Redshift: $0.25/hora × 24 × 365 = $2,190/año (mínimo)
   Snowflake: ~$40/TB/mes storage + $2-$4/credit compute
   ```

2. **Rigid Schema**: Difficult to change schema
   ```sql
   -- Agregar columna puede tomar horas en tablas grandes
   ALTER TABLE events ADD COLUMN user_segment VARCHAR(50);
   -- ⏱️ 4 horas en tabla de 10B filas
   ```

3. **Structured Data only**: Does not support nested JSON, XML, images
   ```sql
   -- ❌ No puedes hacer esto eficientemente:
   SELECT json_extract(event_data, '$.user.preferences.notifications')
   FROM events;
   ```

4. **Not ML-Friendly**: Difficult to access for Python/Spark
   ```python
   # Necesitas exportar datos primero
   # Redshift → S3 → Spark → Train model
   # ⏱️ Latencia y costos de transferencia
   ```

5. **Vendor Lock-in**: Formato propietario
   - You can't easily move between Snowflake ↔ Redshift
   - Dependencia del proveedor

### 🎯 Caso de Uso Ideal

- **BI/Dashboards**: Queries complejas, baja latency
- **Financial Reporting**: Critical ACID
- **High Concurrency**: Hundreds of simultaneous users

---

## Data Lakehouse: Lo Mejor de Ambos Mundos

### 🏛️ Definition

Un **Data Lakehouse** es una arquitectura que implementa estructuras y features de data warehouses **directamente sobre data lakes** utilizando formatos de table open-source.

### Arquitectura del Lakehouse

```
┌───────────────────────────────────────────────────────┐
│                   DATA LAKEHOUSE                       │
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
│  │         Data Files (Parquet/ORC)              │    │
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
│  └─ Pandas/Dask (Data Science)                        │
└───────────────────────────────────────────────────────┘
```

### 🎯 Principios Clave del Lakehouse

#### 1. ACID Transactions

ACID guarantees on object storage (S3, ADLS, GCS):

```python
# Delta Lake example
from delta.tables import DeltaTable

# ✅ ACID Write - todo o nada
df.write.format("delta").mode("overwrite").save("/path/to/table")

# ✅ ACID Update - transacción atómica
deltaTable = DeltaTable.forPath(spark, "/path/to/table")
deltaTable.update(
    condition="status = 'pending'",
    set={"status": "'processed'", "updated_at": "current_timestamp()"}
)
```

**How ​​it works**:
- Transaction log (`_delta_log/`) rastrea todas las operaciones
- Atomic commit: either the entire batch is written, or nothing
- Isolation: lectores ven snapshot consistente

#### 2. Time Travel (Data Versioning)

Access to historical versions:

```python
# Leer versión 10 minutos atrás
df = spark.read.format("delta") \
    .option("timestampAsOf", "2024-02-12 10:00:00") \
    .load("/path/to/table")

# Leer versión específica
df = spark.read.format("delta") \
    .option("versionAsOf", 5) \
    .load("/path/to/table")

# Ver historial completo
deltaTable.history().show()
```

**Casos de uso**:
- Audit and compliance
- Rollback after errors
- Reproducibilidad en ML (entrenar con mismos datos)

#### 3. Schema Evolution

Evolucionar schema sin romper pipelines:

```python
# Agregar columna automáticamente
df_with_new_col.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("/path/to/table")

# El schema anterior sigue siendo válido
# Nuevas columnas aparecen como NULL en registros anteriores
```

#### 4. Unified Batch + Streaming

Misma table para ambos workloads:

```python
# Batch write
df_batch.write.format("delta").save("/path/to/table")

# Streaming write a la misma tabla
df_stream.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/checkpoints/") \
    .start("/path/to/table")

# Streaming read
df_stream_read = spark.readStream.format("delta").load("/path/to/table")
```

#### 5. Open Format

No vendor lock-in, multiple engines:

```python
# Spark
df = spark.read.format("delta").load("s3://bucket/table")

# Presto/Trino
# SELECT * FROM delta.default.table

# Pandas (via deltalake library)
from deltalake import DeltaTable
dt = DeltaTable("s3://bucket/table")
df = dt.to_pandas()
```

### ✅ Ventajas del Lakehouse

| Aspecto | Data Lake | Data Warehouse | Data Lakehouse |
|---------|-----------|----------------|----------------|
| **Costo** | 💰 $23/TB/mes | 💰💰💰 $250+/TB/mes | 💰💰 $40/TB/mes |
| **ACID** | ❌ No | ✅ Yes | ✅ Yes |
| **Performance** | ⚠️ Slow | ✅ Fast | ✅ Fast |
| **Flexibilidad** | ✅ Todos los formatos | ❌ Solo structured | ✅ Todos los formatos |
| **Time Travel** | ❌ No | ⚠️ Limitado | ✅ Yes (completo) |
| **ML Support** | ✅ Excelente | ❌ Limitado | ✅ Excelente |
| **Schema Evolution** | ⚠️ Manual | ❌ Difficult | ✅ Automatic |
| **Streaming** | ⚠️ Complejo | ❌ No soportado | ✅ Nativo |
| **Open Format** | ✅ Yes | ❌ Propietario | ✅ Yes |

### ❌ Desventajas/Limitaciones

1. **Complejidad Inicial**: Curva de aprendizaje
2. **Overhead de Metadata**: Transaction log puede crecer
3. **Requiere Tuning**: Compaction, partitioning, etc.
4. **Maturity**: Less mature than traditional warehouses (but evolving quickly)

### 🎯 Caso de Uso Ideal

- **Todo**: BI, ML, Real-time analytics en una plataforma
- **Reducir costos** manteniendo reliability
- **Unificar arquitectura** (eliminar silos)

---

## Formatos de table en Lakehouse

Existen tres formatos principales de table open-source:

### 1. Delta Lake (Databricks)

**features**:
- Transaction log en JSON (`_delta_log/`)
- Optimistic concurrency control
- ACID via single log
- Better integration with Spark

**Strengths**:
- ✅ Madurez y estabilidad
- ✅ Performance en Spark
- ✅ Documentation and community
- ✅ Upserts eficientes (MERGE)

**Weaknesses**:
- ⚠️ Optimizado para Spark (otros engines con limitaciones)
- ⚠️ Log puede crecer en tables con muchas actualizaciones

**When to use**:
- Pipelines batch pesados en Spark
- Necesitas MERGE/UPSERT frecuente
- Ecosistema Databricks

### 2. Apache Iceberg (Netflix → Apache)

**features**:
- Metadata en Avro/Parquet
- Hidden partitioning (particiones transparentes)
- Partition evolution (cambiar estrategia sin reescribir)
- Multi-engine by design

**Strengths**:
- ✅ Multi-engine (Spark, Flink, Presto, Trino)
- ✅ Partition evolution
- ✅ Hidden partitioning (easier for users)
- ✅ Snapshots eficientes

**Weaknesses**:
- ⚠️ Menos maduro que Delta
- ⚠️ Metadata complexity en tables grandes

**When to use**:
- Multiple query engines
- Streaming con Flink
- Necesitas partition evolution

### 3. Apache Hudi (Uber → Apache)

**features**:
- Copy-on-Write y Merge-on-Read
- Incremental processing
- Record-level updates

**Strengths**:
- ✅ Updates incrementales eficientes
- ✅ CDC (Change Data Capture) nativo
- ✅ Easily configurable data retention

**Weaknesses**:
- ⚠️ Complejidad en tuning
- ⚠️ Menos adoption que Delta/Iceberg

**When to use**:
- CDC pipelines
- Updates frecuentes row-level
- Ecosistema AWS (EMR tiene soporte nativo)

### Direct Comparison

| feature | Delta Lake | Iceberg | Hudi |
|----------------|------------|---------|------|
| **ACID** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Time Travel** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Schema Evolution** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Partition Evolution** | ❌ No | ✅ Yes | ❌ No |
| **Hidden Partitioning** | ❌ No | ✅ Yes | ❌ No |
| **Multi-Engine** | ⚠️ Limitado | ✅ Excelente | ⚠️ Limitado |
| **Streaming** | ✅ Spark Streaming | ✅ Flink, Spark | ✅ Spark Streaming |
| **Upserts** | ✅ MERGE | ⚠️ Overwrite | ✅ Upsert (MoR) |
| **Madurez** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Comunidad** | Grande | Grande | Mediana |

---

## ACID en Sistemas Distribuidos

### What is ACID?

ACID are fundamental guarantees in databases:

- **A**tomicity: Todo o nada
- **C**onsistency: Always valid business rules
- **I**solation: transactions concurrentes no interfieren
- **D**urability: Datos committed no se pierden

### The Challenge in Object Storage

Object storage (S3, ADLS, GCS) **NO** provee ACID nativamente:

```python
# ❌ Problema: No es atómico
for file in files:
    s3.put_object(Bucket='mybucket', Key=file, Body=data)
    # Si falla en el archivo 50 de 100, ¿qué pasa?
    # Tienes datos parciales ❌
```

### How Delta Lake Implements ACID

Delta Lake usa un **transaction log** para coordinar escrituras:

```
s3://bucket/table/
├── _delta_log/
│   ├── 00000000000000000000.json  # Versión 0
│   ├── 00000000000000000001.json  # Versión 1
│   ├── 00000000000000000002.json  # Versión 2
│   └── 00000000000000000010.checkpoint.parquet
├── part-00000-abc123.snappy.parquet
├── part-00001-def456.snappy.parquet
└── part-00002-ghi789.snappy.parquet
```

#### Transaction Log

Cada commit genera un archivo JSON en `_delta_log/`:

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
```

#### Atomicidad

1. Escritor escribe archivos Parquet
2. Escritor crea archivo JSON en `_delta_log/`
3. **Atomic rename** (guaranteed by S3)
4. If it fails before rename → transaction did not happen
5. Si rename exitoso → transaction committed

```python
# Delta Lake garantiza atomicidad
df.write.format("delta").mode("append").save("/path/to/table")
# O todos los registros se escriben, o ninguno ✅
```

#### Isolation

- **Optimistic Concurrency Control** (OCC)
- Multiple writers can work simultaneously
- En commit, se valida que no haya conflictos
- If conflict → automatic retry

```python
# Writer 1 y Writer 2 escriben en paralelo
# Delta Lake detecta conflicto y hace retry automático
# Ambos commits son serializables ✅
```

#### Consistency & Durability

- **Consistency**: Schema enforcement + CHECK constraints
- **Durability**: Once committed, the log guarantees no-loss

---

## Use Cases and When to Use Each Architecture

### Data Lake

**Usa cuando**:
- Archiving of historical data (logs, events)
- Ad-hoc exploration without defined schema
- Presupuesto limitado
- No necesitas ACID

**Ejemplos**:
- Application logs (30 day retention)
- Archivos raw de IoT devices
- Data science exploration

### Data Warehouse

**Usa cuando**:
- Critical BI with strict SLAs (<1s)
- High concurrency (100+ usuarios)
- Queries extremadamente complejas
- Budget is not a limitation

**Ejemplos**:
- Dashboards ejecutivos
- Financial reporting
- Sales analytics con miles de usuarios

### Data Lakehouse

**Usa cuando**:
- Quieres unificar BI + ML en una plataforma
- Necesitas ACID + bajo costo
- Tienes workloads batch + streaming
- Quieres evitar silos de datos

**Ejemplos**:
- Plataforma de analytics moderna
- ML feature stores
- Real-time + historical analytics
- Reducir costos manteniendo calidad

### Quick Decision table

| Pregunta | Lake | Warehouse | Lakehouse |
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

1. **Data Lakehouse** = Data Lake + Data Warehouse features
2. **Formatos de table** (Delta, Iceberg, Hudi) agregan ACID sobre object storage
3. **ACID en distributed systems** requiere transaction log y coordination
4. **Delta Lake** is the most mature format (70% of this module)
5. **Apache Iceberg** stands out in multi-engine and partition evolution (30% of this module)
6. The choice depends on your specific requirements (cost, performance, features)

### Next Steps

Ahora que comprendes los conceptos fundamentales, continuaremos con:

1. **Arquitectura** ([02-architecture.md](02-architecture.md)): Patrones como Medallion, optimizaciones
2. **resources** ([03-resources.md](03-resources.md)): Official documentation, papers, guides
3. **Practical exercises**: Implement what you learned with Delta Lake and Iceberg

---

**Last update**: February 2026
**Tiempo de lectura**: ~45 minutos  
**Nivel**: Intermedio-Avanzado
