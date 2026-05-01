# Storage Basics & Data Formats - Core Concepts

**Estimated Reading Time:** 45-60 minutes

## Table of Contents

1. [Introduction](#introduction)
2. [Data Lake Architecture](#data-lake-architecture)
3. [File Formats Deep Dive](#file-formats-deep-dive)
4. [Partitioning Strategies](#partitioning-strategies)
5. [Compression Techniques](#compression-techniques)
6. [Schema Evolution](#schema-evolution)
7. [Metadata Management](#metadata-management)
8. [Storage Optimization](#storage-optimization)
9. [Best Practices](#best-practices)

## Introduction

In the world of Data Engineering, choosing the correct storage format is one of the most critical decisions that impacts performance, costs and scalability. This module explores modern storage options and how to build efficient data lakes.

### Why Storage Matters

**Impact Areas:**
- **Query Performance:** 10-100x difference between optimized vs non-optimized formats
- **Storage Costs:** Compression can reduce costs 60-90%
- **Processing Speed:** 5-10x faster column formats for analytics
- **Schema Flexibility:** Ability to evolve without breaking changes

**Real-World Example:**
A company migrated 50TB of CSV data to Parquet with Snappy compression:
- Storage: 50TB → 12TB (76% reduction)
- Query time: 45 minutes → 3 minutes (93% improvement)
- Monthly cost: $1,150 → $276 (76% savings)

## Data Lake Architecture

### What is a Data Lake?

Un **data lake** es un repositorio centralizado que almacena datos estructurados, semi-estructurados y no estructurados a cualquier escala. A diferencia de data warehouses, acepta datos en formato raw.

**features:**
- **Schema-on-read:** Aplicas estructura cuando lees, no cuando escribes
- **Multi-format:** CSV, JSON, Parquet, Avro, ORC, binarios
- **Cost-effective:** storage en S3 desde $0.023/GB/mes
- **Scalable:** Petabytes sin limits de capacidad

### Medallion Architecture

The **Medallion** architecture organizes data lakes in layers (Bronze → Silver → Gold) to progressively improve quality.

```
┌─────────────────────────────────────────────────────────────┐
│                    MEDALLION ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐        │
│  │  BRONZE  │  -->  │  SILVER  │  -->  │   GOLD   │        │
│  │   RAW    │       │ CLEANED  │       │ CURATED  │        │
│  └──────────┘       └──────────┘       └──────────┘        │
│                                                               │
│  • Raw data         • Validated      • Aggregated           │
│  • No transform     • Deduplicated   • Business logic       │
│  • Historical       • Normalized     • Ready for BI         │
│  • Append-only      • Type-safe      • Performance-optimized│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Bronze Layer (Raw Zone)

**Purpose:** Almacenar datos tal como llegan de las fuentes.

**Characteristics:**
- Original format (CSV, JSON, logs)
- No transformations
- Append-only (immutable)
- Long-term retention (years)
- Lifecycle → Glacier after 90 days

**Example Structure:**
```
s3://datalake-bronze/
├── transactions/
│   └── dt=2024-02-02/
│       ├── batch_001.csv
│       ├── batch_002.csv
│       └── batch_003.csv
├── events/
│   └── dt=2024-02-02/
│       ├── hour=00/
│       │   └── events_00.json.gz
│       └── hour=01/
│           └── events_01.json.gz
└── logs/
    └── year=2024/month=02/day=02/
        └── application.log.gz
```

**Use Cases:**
- Data lineage and audit
- Reprocessing when downstream logic changes
- Compliance requirements (retain raw data)

#### Silver Layer (Cleaned Zone)

**Purpose:** Datos validados, deduplicados y normalizados.

**Transformations:**
- ✅ Schema validation
- ✅ Data type enforcement
- ✅ Deduplication
- ✅ Null handling
- ✅ Standardization (dates, formats)
- ❌ Business logic (not yet)

**Example Structure:**
```
s3://datalake-silver/
├── transactions/
│   └── year=2024/month=02/day=02/
│       └── data.parquet
├── events/
│   └── event_type=purchase/year=2024/month=02/
│       └── data.parquet
└── users/
    └── country=US/state=CA/
        └── data.parquet
```

**Format Changes:**
- Bronze: CSV, JSON → Silver: Parquet, Avro
- Compression: Gzip → Snappy (better for analytics)
- Partitioning: Date-based Hive partitions

#### Gold Layer (Curated Zone)

**Purpose:** Datos listos para consumo por BI, ML y aplicaciones.

**Transformations:**
- ✅ Aggregations (daily, weekly, monthly)
- ✅ Business logic applied
- ✅ Joins between datasets
- ✅ Feature engineering for ML
- ✅ Denormalization for performance

**Example Structure:**
```
s3://datalake-gold/
├── analytics/
│   ├── daily_sales_summary/
│   │   └── year=2024/month=02/
│   │       └── data.parquet
│   ├── customer_360/
│   │   └── snapshot_date=2024-02-02/
│   │       └── data.parquet
│   └── product_performance/
│       └── data.parquet
├── ml_features/
│   ├── customer_churn_features/
│   └── product_recommendation_features/
└── reporting/
    ├── executive_dashboard/
    └── operational_metrics/
```

**Optimization:**
- Pre-aggregated (fast queries)
- Heavily compressed
- Small file sizes (coalesced)
- Z-ordering on commonly filtered columns

### Data Lake vs Data Warehouse

| Aspect | Data Lake | Data Warehouse |
|--------|-----------|----------------|
| **Schema** | Schema-on-read | Schema-on-write |
| **Data Types** | Structured, semi, unstructured | Structured only |
| **Users** | Data scientists, engineers | Business analysts |
| **Storage Cost** | $0.023/GB/month | $25+/TB/month |
| **Query Speed** | Variable (optimizable) | Consistently fast |
| **Flexibility** | Very high | Lower |
| **Processing** | Spark, Presto, Athena | SQL engines |

## File Formats Deep Dive

Choosing the correct format is critical for performance and costs. Let's analyze the most important formats.

### CSV (Comma-Separated Values)

**Pros:**
- ✅ Universal compatibility
- ✅ Human-readable
- ✅ Simple to generate
- ✅ Every tool supports it

**Cons:**
- ❌ No schema enforcement
- ❌ No compression built-in
- ❌ Poor query performance
- ❌ No type information
- ❌Large file sizes

**Best Use Cases:**
- Data exchange between systems
- Bronze layer (raw ingestion)
- Small datasets (<10MB)
- Human inspection needed

**Example:**
```csv
transaction_id,user_id,amount,currency,timestamp
TXN001,USR123,99.99,USD,2024-02-02T10:30:00Z
TXN002,USR456,149.50,EUR,2024-02-02T10:31:15Z
```

**Performance Characteristics:**
- Read speed: **Slow** (sequential scan)
- Compression ratio: 60-70% with gzip
- Query pushdown: None
- Schema evolution: Not supported

### JSON (JavaScript Object Notation)

**Pros:**
- ✅ Self-describing (schema included)
- ✅ Nested structures
- ✅ Human-readable
- ✅ Standard Web APIs

**Cons:**
- ❌ Verbose (key names repeated)
- ❌ Slow to parse
- ❌Large file sizes
- ❌ No column pruning
- ❌Poor compression

**Best Use Cases:**
- API responses
- Event logs
- Semi-structured data
- Configuration files

**Example:**
```json
{
  "transaction_id": "TXN001",
  "user_id": "USR123",
  "amount": 99.99,
  "currency": "USD",
  "timestamp": "2024-02-02T10:30:00Z",
  "metadata": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0"
  }
}
```

**Performance Characteristics:**
- Read speed: **Very slow** (parse overhead)
- Compression ratio: 70-80% with gzip
- Query pushdown: Limited
- Schema evolution: Flexible

**JSON Lines (JSONL):**
Best for big data - each line is a complete JSON:
```jsonl
{"id": 1, "name": "Alice", "age": 30}
{"id": 2, "name": "Bob", "age": 25}
```

### Parquet (Apache Parquet)

**Pros:**
- ✅ Columnar format (fast analytics)
- ✅ Excellent compression (60-90%)
- ✅ Predicate pushdown
- ✅ Column pruning
- ✅ Schema included
- ✅ Industry standard

**Cons:**
- ❌Not human-readable
- ❌ Write latency higher
- ❌ Requires compatible tools
- ❌ Small files create overhead

**Best Use Cases:**
- **Analytics workloads** (main use case)
- Data warehouses
- OLAP queries
- Data lakes (Silver/Gold layers)

**Internal Structure:**
```
┌─────────────────────────────────────────┐
│         Parquet File Structure          │
├─────────────────────────────────────────┤
│  Magic Number: PAR1                     │
│                                          │
│  ┌────────────────────────────────┐    │
│  │     Row Group 1 (128MB)        │    │
│  ├────────────────────────────────┤    │
│  │  Column Chunk: user_id         │    │
│  │  Column Chunk: amount          │    │
│  │  Column Chunk: timestamp       │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │     Row Group 2 (128MB)        │    │
│  └────────────────────────────────┘    │
│                                          │
│  Footer (Metadata):                     │
│  - Schema                                │
│  - Column statistics (min, max, null)   │
│  - Row group offsets                    │
│                                          │
│  Magic Number: PAR1                     │
└─────────────────────────────────────────┘
```

**Key Features:**

1. **Columnar Storage:** Lee solo columns necesarias
```python
# Query: SELECT amount, timestamp FROM transactions WHERE amount > 100
# Parquet: Solo lee 2 columnas (amount, timestamp)
# CSV: Lee todas las columnas
```

2. **Predicate Pushdown:** Filtra en storage layer
```python
# WHERE amount > 100
# Parquet lee statistics en footer, skipea row groups completos
```

3. **Compression:** Por column
```python
# user_id: Dictionary encoding (muchos duplicados)
# amount: Delta encoding (valores cercanos)
# timestamp: Delta + RLE encoding
```

**Performance Characteristics:**
- Read speed: **Very fast** for analytics
- Compression ratio: 80-95% (excellent)
- Query pushdown: Full support
- Schema evolution: Supported (add columns)

**Example Usage:**
```python
import pyarrow.parquet as pq
import pandas as pd

# Write
df = pd.DataFrame({
    'id': [1, 2, 3],
    'value': [100, 200, 300]
})
df.to_parquet('data.parquet', compression='snappy')

# Read with column pruning
table = pq.read_table('data.parquet', columns=['value'])

# Read with predicate pushdown
table = pq.read_table('data.parquet', filters=[('value', '>', 150)])
```

### Avro (Apache Avro)

**Pros:**
- ✅ Row-based (good for writes)
- ✅ Schema evolution (backward/forward)
- ✅ Compact binary format
- ✅ Splittable (parallel processing)
- ✅ Schema registry integration

**Cons:**
- ❌ Not good for analytics
- ❌ No column pruning
- ❌ Requires schema files
- ❌ Less tooling support

**Best Use Cases:**
- **Streaming data** (Kafka)
- Write-heavy workloads
- Schema evolution requirements
- Data serialization

**Schema Definition:**
```json
{
  "type": "record",
  "name": "Transaction",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "amount", "type": "double"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"}
  ]
}
```

**Performance Characteristics:**
- Read speed: **Fast** for full rows
- Compression ratio: 70-85%
- Query pushdown: None
- Schema evolution: Excellent

**When to Use Avro vs Parquet:**
- **Avro:** Streaming, Kafka, write-heavy, need full rows
- **Parquet:** Analytics, batch processing, read-heavy, need columns

### ORC (Optimized Row Columnar)

**Pros:**
- ✅ Columnar (like Parquet)
- ✅ ACID transactions support
- ✅ Bloom filters
- ✅ Better compression than Parquet
- ✅ Native Hive support

**Cons:**
- ❌ Less ecosystem support
- ❌ Primarily Hadoop/Hive
- ❌ Limited Python tooling

**Best Use Cases:**
- Hive tables
- Hadoop ecosystem
- ACID requirements

**ORC vs Parquet:**
- **ORC:** Better for Hive, slightly better compression
- **Parquet:** Better ecosystem (Spark, Athena, etc.), more tooling

### Format Comparison Table

| Format | Type | Compression | Query Speed ​​| Write Speed ​​| Analytics | Streaming | Schema Evolution |
|--------|------|-------------|-------------|-------------|-----------|-----------|--------------|
| CSV | Text | Poor | Slow | Fast | ❌ | ❌ | ❌ |
| JSON | Text | Poor | Slow | Fast | ❌ | ✅ | ✅ |
| Parquet | Columnar | Excellent | Very Fast | Slow | ✅✅✅ | ❌ | ✅ |
| Avro | Row | Good | Medium | Fast | ❌ | ✅✅✅ | ✅✅✅ |
| ORC | Columnar | Excellent | Very Fast | Medium | ✅✅ | ❌ | ✅ |

### File Format Selection Matrix

**Choose CSV when:**
- Human readability required
- Universal compatibility needed
- Data exchange between unknown systems
- Temporary/exploratory work

**Choose JSON when:**
- Semi-structured data (nested)
- API integration
- Event logging
- Schema flexibility paramount

**Choose Parquet when:**
- **Analytics queries** (most common)
- Read-heavy workloads
- Large datasets (>1GB)
- S3 + Athena/Presto
- Cost optimization needed

**Choose Avro when:**
- Streaming pipelines (Kafka)
- Write-heavy workloads
- Schema evolution critical
- Row-based access pattern

**Choose ORC when:**
- Hive-based architecture
- ACID transactions needed
- Hadoop-centric ecosystem

## Partitioning Strategies

Partitioning divides data into logical subdirectories to improve query performance and reduce costs.

### Why Partition?

**Benefits:**
- ✅ **Query Performance:** Skip irrelevant data (10-100x faster)
- ✅ **Cost Reduction:** Athena charges per data scanned
- ✅ **Parallel Processing:** Process partitions concurrently
- ✅ **Data Management:** Delete old partitions easily

**Example Impact:**
```sql
-- Without partitioning: Scan 1TB, cost $5, time 5 minutes
SELECT * FROM transactions WHERE date = '2024-02-02';

-- With partitioning: Scan 3GB, cost $0.015, time 2 seconds
SELECT * FROM transactions WHERE date = '2024-02-02';
```

### Hive-Style Partitioning

Standard de facto en data lakes. Formato: `key=value/`

**Example:**
```
s3://bucket/table_name/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   └── data.parquet
│   │   ├── day=02/
│   │   │   └── data.parquet
│   │   └── day=03/
│   │       └── data.parquet
│   └── month=02/
│       └── day=01/
│           └── data.parquet
└── year=2023/
    └── month=12/
        └── day=31/
            └── data.parquet
```

**Registering in Glue/Athena:**
```sql
MSCK REPAIR TABLE transactions;
-- Auto-discovers all partitions
```

### Partition Key Selection

**Criteria:**
1. **Query patterns:** Partition on frequently filtered columns
2. **Cardinality:** Avoid too many or too few partitions
3. **Data distribution:** Aim for balanced partition sizes

**Common Patterns:**

#### 1. Date-Based (Most Common)
```
year=YYYY/month=MM/day=DD/
year=YYYY/month=MM/
year=YYYY/week=WW/
```

**Use when:**
- Time-series data
- Recent data queried more frequently
- Natural retention policies

#### 2. Geography-Based
```
country=US/state=CA/city=SF/
region=north-america/country=US/
```

**Use when:**
- Multi-region applications
- Data sovereignty requirements
- Regional analytics

#### 3. Category-Based
```
event_type=purchase/
product_category=electronics/
customer_segment=enterprise/
```

**Use when:**
- Distinct business domains
- Different retention per category
- Isolated processing

#### 4. Hybrid (Multiple Levels)
```
event_type=purchase/year=2024/month=02/day=02/
country=US/year=2024/month=02/
```

**Use when:**
- Complex query patterns
- Need flexibility

### Partition Anti-Patterns

❌ **Too Many Partitions:**
```
user_id=123456/  # Millions of users = millions of partitions
```
**Problem:** Metadata overhead, slow queries

❌ **Too Few Partitions:**
```
year=2024/  # Single partition per year
```
**Problem:** Can't skip data, no benefit

❌ **Unbalanced Partitions:**
```
country=US/       # 80% of data
country=Vatican/  # 0.001% of data
```
**Problem:** Skewed processing

### Partitioning Best Practices

1. **Partition Size:** 128MB - 1GB per partition (sweet spot)

2. **Cardinality:**
   - Minimum: 10 partitions
   - Maximum: 10,000 partitions per table

3. **File Count:**
   - Target: 1-10 files per partition
   - Avoid: 1000s of small files (<10MB)

4. **Schema:**
```python
# Good: Partition columns separate from data
data/
└── dt=2024-02-02/
    └── data.parquet  # Contains: id, name, amount (NOT dt)

# Bad: Partition column duplicated
data/
└── dt=2024-02-02/
    └── data.parquet  # Contains: id, name, amount, dt
```

## Compression Techniques

Compression reduce storage costs y puede mejorar query performance (menos I/O).

### Compression Algorithms

#### 1. Gzip

**Characteristics:**
- Compression ratio: **High** (70-80%)
- Compression speed: Slow
- Decompression speed: Medium
- Splittable: No (except with Hadoop codec)

**Best for:**
- Archival storage (Bronze layer)
- Infrequently accessed data
- Maximum compression needed

**Example:**
```bash
# Compress
gzip input.csv  # Creates input.csv.gz

# Compression: 1GB → 250MB (75% reduction)
# Time: 45 seconds
```

#### 2. Snappy

**Characteristics:**
- Compression ratio: **Medium** (50-60%)
- Compression speed: **Very Fast**
- Decompression speed: **Very Fast**
- Splittable: Yes (with container formats)

**Best for:**
- **Parquet files** (default)
- Real-time processing
- Analytics workloads

**Example:**
```python
import pyarrow.parquet as pq

# Snappy is default for Parquet
df.to_parquet('data.parquet', compression='snappy')

# Compression: 1GB → 400MB (60% reduction)
# Time: 5 seconds
```

#### 3. LZ4

**Characteristics:**
- Compression ratio: **Low** (40-50%)
- Compression speed: **Extremely Fast**
- Decompression speed: **Extremely Fast**
- Splittable: Yes

**Best for:**
- Streaming data
- Low-latency requirements
- High-throughput systems

#### 4. Zstd (Zstandard)

**Characteristics:**
- Compression ratio: **High** (65-75%)
- Compression speed: Fast
- Decompression speed: Fast
- Splittable: Yes
- Tunable levels (1-22)

**Best for:**
- Modern systems (newer algorithm)
- Balance compression + speed
- Flexible requirements

**Example:**
```python
# Zstd with compression level
df.to_parquet('data.parquet', compression='zstd', compression_level=3)

# Level 1: Fast, less compression
# Level 9: Slower, better compression
# Level 22: Very slow, maximum compression
```

### Compression Comparison

| Algorithm | Ratio | Comp Speed | Decomp Speed | CPU Usage | Best Use Case |
|-----------|-------|------------|--------------|-----------|---------------|
| **Gzip** | 75% | Slow | Medium | High | Archival |
| **Snappy** | 55% | Very Fast | Very Fast | Low | **Analytics** |
| **LZ4** | 45% | Extremely Fast | Extremely Fast | Very Low | Streaming |
| **Zstd** | 70% | Fast | Fast | Medium | Modern general-purpose |
| **Brotli** | 80% | Very Slow | Fast | High | Web assets |

### Compression Selection Matrix

**Choose Gzip when:**
- Archival storage (long-term retention)
- Infrequent access
- Bandwidth-limited transfers
- Maximum compression priority

**Choose Snappy when:**
- **Parquet files** (✅ recommended)
- Frequent analytics queries
- Athena/Presto/Spark workloads
- Balance of compression + performance

**Choose LZ4 when:**
- Real-time streaming
- Low latency critical
- High throughput needed
- CPU constrained

**Choose Zstd when:**
- Modern infrastructure
- Flexible tuning needed
- Better than Gzip, faster than Gzip
- General-purpose (replacing Gzip)

### Compression Best Practices

1. **Layer-Specific:**
   - **Bronze:** Gzip (max compression, rarely accessed)
   - **Silver:** Snappy (balance)
   - **Gold:** Snappy or Zstd (frequent access)

2. **File Format:**
   - **Parquet/ORC:** Snappy (default, optimal)
   - **Avro:** Snappy or Deflate
   - **CSV/JSON:** Gzip or Zstd

3. **Trade-offs:**
```python
# Scenario: 1TB CSV → Parquet conversion

# Option 1: Uncompressed
Size: 350GB
Write time: 5 min
Query time: 2 min
Monthly cost: $8.05

# Option 2: Snappy (RECOMMENDED)
Size: 140GB
Write time: 7 min
Query time: 1.5 min
Monthly cost: $3.22

# Option 3: Gzip
Size: 90GB
Write time: 25 min
Query time: 4 min
Monthly cost: $2.07
```

**Winner:** Snappy (best balance)

## Schema Evolution

Schema evolution permite cambiar estructura de datos sin breaking existing applications.

### Types of Schema Changes

#### 1. Backward Compatible (Safe)

**Add Optional Column:**
```python
# Old schema
schema_v1 = {
    'id': int,
    'name': str,
    'amount': float
}

# New schema
schema_v2 = {
    'id': int,
    'name': str,
    'amount': float,
    'category': str  # New optional field
}
```
✅ Old readers can still read new data (ignore new columns)

#### 2. Forward Compatible (Safe)

**Delete Column:**
```python
# Old readers can read new data (column removed)
schema_v2 = {
    'id': int,
    'name': str
    # 'amount' removed
}
```
✅ New data readable by old readers (missing columns = null)

#### 3. Full Compatible

Both backward and forward compatible.

#### 4. Breaking Changes (Unsafe)

❌ **Rename Column:**
```python
# 'name' → 'full_name'
# Old readers look for 'name', get error
```

❌ **Change Type:**
```python
# 'amount': float → int
# Precision loss
```

❌ **Remove Required Column:**
```python
# Old readers expect 'amount', get error
```

### Schema Evolution in Parquet

**Add Column (Supported):**
```python
# Write v1
df_v1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
df_v1.to_parquet('data_v1.parquet')

# Write v2 with new column
df_v2 = pd.DataFrame({
    'id': [3, 4],
    'name': ['C', 'D'],
    'age': [30, 25]  # New column
})
df_v2.to_parquet('data_v2.parquet')

# Read both (age will be null for v1)
df = pd.read_parquet(['data_v1.parquet', 'data_v2.parquet'])
#    id name   age
# 0   1    A   NaN
# 1   2    B   NaN
# 2   3    C  30.0
# 3   4    D  25.0
```

**Change Type (Not Recommended):**
```python
# v1: amount as float
# v2: amount as decimal

# Workaround: Create new column
df['amount_decimal'] = df['amount'].apply(Decimal)
# Keep both columns for transition period
```

### Schema Evolution Best Practices

1. **Version Your Schemas:**
```python
schemas = {
    'v1': {'id': int, 'name': str},
    'v2': {'id': int, 'name': str, 'email': str},
    'v3': {'id': int, 'name': str, 'email': str, 'phone': str}
}
```

2. **Use Schema Registry:** (Kafka, Glue Schema Registry)
```python
# Avro with schema registry
from confluent_kafka import avro

schema_registry = SchemaRegistryClient({'url': 'http://registry:8081'})
avro_producer = AvroProducer({...}, schema_registry=schema_registry)
```

3. **Document Changes:**
```markdown
## Schema Changelog

### v2.0.0 (2024-02-02)
- Added `customer_email` (string, optional)
- Added `loyalty_points` (integer, default 0)

### v1.1.0 (2024-01-15)
- Added `purchase_channel` (string, optional)
```

4. **Test Compatibility:**
```python
def test_schema_compatibility():
    # Write with old schema
    old_data = write_parquet(schema_v1, data)

    # Read with new schema
    new_df = read_parquet_with_schema(old_data, schema_v2)

    # Assert new columns have defaults
    assert new_df['new_column'].isna().all()
```

## Metadata Management

Metadata es "data about data" - critical para discovery, governance, and optimization.

### AWS Glue Data Catalog

Central metadata repository para AWS.

**Components:**
- **Databases:** Logical grouping of tables
- **Tables:** Schema + location + format
- **Partitions:** Partition metadata
- **Crawlers:** Auto-discover schemas

**Example:**
```python
import boto3

glue = boto3.client('glue')

# Create database
glue.create_database(
    DatabaseInput={'Name': 'ecommerce'}
)

# Create table
glue.create_table(
    DatabaseName='ecommerce',
    TableInput={
        'Name': 'transactions',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'id', 'Type': 'string'},
                {'Name': 'amount', 'Type': 'double'},
                {'Name': 'timestamp', 'Type': 'timestamp'}
            ],
            'Location': 's3://bucket/transactions/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'PartitionKeys': [
            {'Name': 'year', 'Type': 'string'},
            {'Name': 'month', 'Type': 'string'},
            {'Name': 'day', 'Type': 'string'}
        ]
    }
)

# Query with Athena
athena = boto3.client('athena')
response = athena.start_query_execution(
    QueryString='SELECT * FROM ecommerce.transactions WHERE year=2024',
    ResultConfiguration={'OutputLocation': 's3://results/'}
)
```

### Glue Crawlers

Auto-discover schemas and partitions.

**Configuration:**
```python
glue.create_crawler(
    Name='transactions-crawler',
    Role='arn:aws:iam::123456789012:role/GlueRole',
    DatabaseName='ecommerce',
    Targets={
        'S3Targets': [
            {'Path': 's3://bucket/transactions/'}
        ]
    },
    Schedule='cron(0 12 * * ? *)',  # Daily at noon
    SchemaChangePolicy={
        'UpdateBehavior': 'UPDATE_IN_DATABASE',
        'DeleteBehavior': 'LOG'
    }
)

# Run crawler
glue.start_crawler(Name='transactions-crawler')
```

## Storage Optimization

### Small Files Problem

**Problem:**
- 1000s of small files (<10MB) create overhead
- Slow queries (high latency per file)
- High S3 API costs (LIST, GET operations)

**Solution: Compaction**
```python
import pyarrow.parquet as pq

# Read many small files
table = pq.read_table('s3://bucket/small_files/')

# Write single large file
pq.write_table(table, 's3://bucket/compacted.parquet')

# Result: 1000 files @ 1MB → 1 file @ 1GB
```

### Cost Optimization

**Storage Tiers:**
```python
# Lifecycle policy
lifecycle_policy = {
    'Rules': [
        {
            'Id': 'Move to IA after 30 days',
            'Status': 'Enabled',
            'Transitions': [
                {
                    'Days': 30,
                    'StorageClass': 'STANDARD_IA'
                },
                {
                    'Days': 90,
                    'StorageClass': 'GLACIER'
                }
            ]
        }
    ]
}

s3.put_bucket_lifecycle_configuration(
    Bucket='bucket',
    LifecycleConfiguration=lifecycle_policy
)
```

**Cost Comparison:**
| Tier | Cost/GB/Month | Use Case |
|------|---------------|----------|
| S3 Standard | $0.023 | Hot data (< 30 days) |
| S3 IA | $0.0125 | Warm data (30-90 days) |
| S3 Glacier | $0.004 | Cold data (> 90 days) |
| S3 Deep Archive | $0.00099 | Archival (years) |

## Best Practices

### 1. File Naming Conventions

```
{environment}_{layer}_{domain}_{entity}_{version}_{timestamp}.{format}

Examples:
prod_silver_ecommerce_transactions_v2_20240202.parquet
dev_bronze_events_clickstream_v1_20240202.json.gz
```

### 2. Directory Structure

```
s3://{bucket}/
├── {layer}/              # bronze, silver, gold
│   └── {domain}/         # ecommerce, marketing, ops
│       └── {entity}/     # transactions, events, users
│           └── partitions/
```

### 3. Data Quality Checks

```python
def validate_parquet_file(path):
    """Validate Parquet file quality"""
    table = pq.read_table(path)

    # Check schema
    expected_columns = ['id', 'amount', 'timestamp']
    assert set(expected_columns).issubset(set(table.column_names))

    # Check null percentages
    for col in table.column_names:
        null_pct = table[col].null_count / len(table)
        assert null_pct < 0.1, f"{col} has {null_pct}% nulls"

    # Check file size
    file_size_mb = os.path.getsize(path) / (1024**2)
    assert 10 < file_size_mb < 1000, f"File size {file_size_mb}MB out of range"

    return True
```

### 4. Documentation

Every dataset should have:
- **README.md:** Description, schema, examples
- **CHANGELOG.md:** Schema version history
- **schema.json:** Formal schema definition

### 5. Monitoring

```python
# CloudWatch metrics
cloudwatch.put_metric_data(
    Namespace='DataLake',
    MetricData=[
        {
            'MetricName': 'FilesProcessed',
            'Value': 1000,
            'Unit': 'Count'
        },
        {
            'MetricName': 'DataSizeGB',
            'Value': 50.5,
            'Unit': 'Gigabytes'
        }
    ]
)
```

## Summary

### Key Takeaways

1. **Medallion Architecture:** Bronze (raw) → Silver (cleaned) → Gold (curated)

2. **Format Selection:**
   - CSV: Human-readable, interchange
   - JSON: Semi-structured, APIs
   - **Parquet: Analytics (primary choice)**
   - Avro: Streaming, schema evolution

3. **Partitioning:** Partition on frequently filtered columns, target 128MB-1GB per partition

4. **Compression:** Snappy for Parquet (best balance)

5. **Schema Evolution:** Add columns safely, avoid breaking changes

6. **Optimization:** Compact small files, use lifecycle policies, monitor costs

### Next Steps

- Complete Exercise 01: Design medallion data lake
- Complete Exercise 02: Convert between formats
- Complete Exercise 03: Implement partitioning
- Complete Exercise 04: Benchmark compression
- Complete Exercise 05: Test schema evolution
- Complete Exercise 06: Set up Glue Catalog

**Estimated Completion Time:** 8-10 hours

---

*This document covers foundational concepts for Module 02. For implementation details, see exercises and architecture documentation.*
