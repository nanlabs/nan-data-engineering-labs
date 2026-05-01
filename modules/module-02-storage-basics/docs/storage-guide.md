# Storage Formats Deep Dive Guide

## Table of Contents
1. [Format Comparison Matrix](#format-comparison-matrix)
2. [CSV - Comma Separated Values](#csv)
3. [JSON - JavaScript Object Notation](#json)
4. [Parquet - Apache Parquet](#parquet)
5. [Avro - Apache Avro](#avro)
6. [ORC - Optimized Row Columnar](#orc)
7. [Decision Framework](#decision-framework)
8. [Real-World Examples](#real-world-examples)

## Format Comparison Matrix

| Feature | CSV | JSON | Parquet | Avro | ORC |
|---------|-----|------|---------|------|-----|
| **Storage Type** | Row | Row | Columnar | Row | Columnar |
| **Schema** | None | Flexible | Strict | Strict | Strict |
| **Compression** | Weak | Weak | Excellent | Good | Excellent |
| **Read Speed** | Slow | Slow | Very Fast | Fast | Very Fast |
| **Write Speed** | Fast | Fast | Medium | Fast | Medium |
| **Query Performance** | Poor | Poor | Excellent | Medium | Excellent |
| **Human Readable** | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Schema Evolution** | ❌ No | Partial | ✅ Yes | ✅ Excellent | ✅ Yes |
| **Nested Data** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Splittable** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Best For** | Exchange | APIs | Analytics | Streaming | Hive |

## CSV - Comma Separated Values

### Overview
- **Created**: 1970s
- **Type**: Row-based, plain text
- **Use Case**: Data exchange, human review

### Pros
✅ Universal compatibility
✅ Human-readable
✅ Simple to create and parse
✅ Works with Excel, databases, any tool

### Cons
❌ No schema enforcement
❌ Poor compression (text-based)
❌ No data types (everything is string)
❌ Slow to parse for large datasets
❌ Ambiguous delimiters (commas in data)
❌ No support for nested structures

### Technical Details
```csv
transaction_id,user_id,amount,timestamp,country
1,1001,125.50,2024-01-15T10:30:00,USA
2,1002,89.99,2024-01-15T11:15:00,UK
```

**File Size Example** (100K rows):
- Raw CSV: 15.8 MB
- Gzipped CSV: 3.2 MB (79.7% savings)

### When to Use
- Exchanging data with external systems
- One-time data exports for human review
- Bronze layer (preserving original format)
- Small datasets (<1 GB)

### When NOT to Use
- Large-scale analytics (use Parquet)
- Nested/complex structures (use JSON/Parquet)
- High-performance queries (use Parquet/ORC)

## JSON - JavaScript Object Notation

### Overview
- **Created**: 2001 (Douglas Crockford)
- **Type**: Row-based, text, semi-structured
- **Use Case**: APIs, configuration, event logs

### Pros
✅ Human-readable
✅ Supports nested objects/arrays
✅ Flexible schema
✅ Native to web applications
✅ Self-describing data

### Cons
❌ Larger than CSV (verbose syntax)
❌ Slow parsing
❌ No compression (text-based)
❌ Inefficient for analytics
❌ No schema validation (unless JSON Schema used)

### Technical Details
```json
{
  "transaction_id": 1,
  "user_id": 1001,
  "amount": 125.50,
  "timestamp": "2024-01-15T10:30:00",
  "country": "USA",
  "metadata": {
    "device": "mobile",
    "browser": "Chrome"
  }
}
```

**JSONL (JSON Lines)** - Better for big data:
```jsonl
{"transaction_id":1,"user_id":1001,"amount":125.50}
{"transaction_id":2,"user_id":1002,"amount":89.99}
```

**File Size Example** (100K rows):
- JSON: 18.5 MB (17% larger than CSV!)
- JSONL: 16.2 MB
- Gzipped JSONL: 2.8 MB

### When to Use
- API responses
- Event logs with variable structure
- Configuration files
- Semi-structured data
- Data with deep nesting

### When NOT to Use
- Large datasets (>10 GB) → use Parquet
- Analytics workloads → use Parquet
- When storage cost matters → use Parquet

## Parquet - Apache Parquet

### Overview
- **Created**: 2013 (Twitter & Cloudera)
- **Type**: Columnar, binary
- **Use Case**: Data lakes, analytics, BI tools

### Pros
✅ Excellent compression (70-90% savings)
✅ Fastest read for analytics (columnr)
✅ Predicate pushdown (read only needed columns)
✅ Schema enforcement
✅ Schema evolution support
✅ Supports nested data
✅ Splittable (MapReduce/Spark friendly)
✅ Industry standard for data lakes

### Cons
❌ Not human-readable (binary)
❌ Slower writes than CSV
❌ Requires specialized tools (PyArrow, Spark)

### Technical Details

**Columnar Storage**:
```
CSV (Row-based):
Row 1: [1, 1001, 125.50, 2024-01-15, USA]
Row 2: [2, 1002, 89.99, 2024-01-15, UK]

Parquet (Column-based):
transaction_id: [1, 2, 3, ...]
user_id:       [1001, 1002, 1003, ...]
amount:        [125.50, 89.99, 210.00, ...]
```

**Internal Structure**:
```
Parquet File
├── File Metadata
├── Row Group 1 (128 MB default)
│   ├── Column Chunk: transaction_id
│   │   ├── Data Pages (compressed)
│   │   └── Statistics (min, max, null count)
│   ├── Column Chunk: amount
│   └── Column Chunk: country
├── Row Group 2
└── Footer (schema, offsets)
```

**Compression Comparison** (100K rows):
- CSV: 15.8 MB
- Parquet (Snappy): 3.2 MB (79.7% compression)
- Parquet (Gzip): 2.1 MB (86.7% compression)
- Parquet (LZ4): 3.8 MB (75.9% compression)
- Parquet (Zstd): 2.3 MB (85.4% compression)

**Query Performance**:
```python
# CSV: Read entire file (15.8 MB)
df = pd.read_csv('data.csv')
result = df[df['country'] == 'USA']['amount'].sum()
# Time: 0.285s, Data scanned: 15.8 MB

# Parquet: Read only 'country' and 'amount' columns
df = pd.read_parquet('data.parquet', columns=['country', 'amount'])
result = df[df['country'] == 'USA']['amount'].sum()
# Time: 0.048s (6x faster!), Data scanned: 1.2 MB
```

### Compression Algorithms

| Algorithm | Ratio | Compression Speed | Decompression Speed | CPU | Best For |
|-----------|-------|-------------------|---------------------|-----|----------|
| **Snappy** | 55-60% | ⚡⚡⚡ Very Fast | ⚡⚡⚡ Very Fast | Low | **Default choice** |
| **Gzip** | 75-80% | 🐢 Slow | 🐢 Slow | High | Archival storage |
| **LZ4** | 50-55% | ⚡⚡⚡⚡ Fastest | ⚡⚡⚡⚡ Fastest | Very Low | Real-time ingestion |
| **Zstd** | 70-75% | ⚡⚡ Fast | ⚡⚡⚡ Very Fast | Medium | Modern balanced |

**Recommendation by Layer**:
- Bronze: Gzip (maximize storage savings, infrequent access)
- Silver: Snappy (balance of compression and speed)
- Gold: Snappy (optimized for fast queries)

### Schema Evolution

```python
# Version 1
schema_v1 = pa.schema([
    ('transaction_id', pa.int32()),
    ('amount', pa.float32())
])

# Version 2: Add new column (backward compatible)
schema_v2 = pa.schema([
    ('transaction_id', pa.int32()),
    ('amount', pa.float32()),
    ('loyalty_points', pa.int32())  # NEW
])

# Old readers can still read V2 files (ignores new column)
# New readers can read V1 files (loyalty_points = null)
```

### When to Use ⭐ HIGHLY RECOMMENDED
- Data lakes (Silver/Gold layers)
- Analytics workloads
- BI tools (Tableau, PowerBI, Looker)
- Query engines (Athena, Presto, Spark SQL)
- Any scenario with >1 GB data

### When NOT to Use
- Real-time streaming (consider Avro)
- Transactional updates (use database)
- Human need to read files (use CSV)

## Avro - Apache Avro

### Overview
- **Created**: 2009 (Doug Cutting)
- **Type**: Row-based, binary
- **Use Case**: Data serialization, Kafka, streaming

### Pros
✅ Excellent schema evolution
✅ Compact binary format
✅ Self-describing (schema in file)
✅ Splittable for MapReduce
✅ Fast serialization
✅ Dynamic typing support

### Cons
❌ Larger than Parquet (row-based)
❌ Slower for analytics than Parquet
❌ Less tool support than Parquet

### Technical Details

**Schema Definition** (JSON):
```json
{
  "type": "record",
  "name": "Transaction",
  "namespace": "com.globalmart.transactions",
  "fields": [
    {"name": "transaction_id", "type": "int"},
    {"name": "amount", "type": "double"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "country", "type": "string"},
    {"name": "metadata", "type": ["null", {
      "type": "record",
      "name": "Metadata",
      "fields": [
        {"name": "device", "type": "string"},
        {"name": "browser", "type": "string"}
      ]
    }], "default": null}
  ]
}
```

**File Size Example** (100K rows):
- CSV: 15.8 MB
- Avro: 8.2 MB (48% compression)
- Avro (Deflate): 2.5 MB (84% compression)

### Schema Evolution

**Backward Compatibility** (new code reads old data):
```json
// Old schema
{"fields": [{"name": "amount", "type": "double"}]}

// New schema (add field with default)
{"fields": [
  {"name": "amount", "type": "double"},
  {"name": "currency", "type": "string", "default": "USD"}
]}
```

**Forward Compatibility** (old code reads new data):
```json
// Add optional field
{"name": "loyalty_points", "type": ["null", "int"], "default": null}
```

### When to Use
- Kafka message serialization
- Event streaming (Kinesis, Pulsar)
- RPC systems (Hadoop)
- Data exchange between systems
- When strong schema evolution is needed

### When NOT to Use
- Analytics queries (use Parquet)
- Human-readable data (use JSON)
- Storage optimization critical (use Parquet)

## ORC - Optimized Row Columnar

### Overview
- **Created**: 2013 (Hortonworks)
- **Type**: Columnar, binary
- **Use Case**: Hive, Spark

### Pros
✅ Excellent compression
✅ Fast for analytics
✅ ACID transactions support
✅ Built-in indexes
✅ Bloom filters for fast lookups

### Cons
❌ Less ecosystem support than Parquet
❌ Primarily Hive-focused
❌ Complex to work with directly

### When to Use
- Hive data warehouses
- Spark jobs reading from Hive
- ACID transactional tables

### When NOT to Use
- General data lakes (use Parquet)
- Non-Hive ecosystems (use Parquet)

## Decision Framework

### Step 1: Determine Your Use Case

```
START
  │
  ├─ Human needs to read? ──> CSV
  │
  ├─ API/Event logs? ──> JSON/JSONL
  │
  ├─ Streaming data? ──> Avro
  │
  ├─ Analytics/BI? ──> Parquet ⭐
  │
  └─ Hive tables? ──> ORC
```

### Step 2: Data Size Threshold

```
< 100 MB      → CSV is fine
100 MB - 1 GB → CSV acceptable, Parquet better
1 GB - 10 GB  → Parquet recommended
> 10 GB       → Parquet required ⚡
```

### Step 3: Query Pattern

```
Full table scans        → Any format
Column-specific queries → Parquet/ORC ⭐
Row-by-row access      → Avro
One-time export        → CSV
```

## Real-World Examples

### Netflix
- **Bronze**: JSON (preserve raw events)
- **Silver**: Parquet with Snappy (cleaned data)
- **Gold**: Parquet with Snappy (aggregated metrics)
- **Result**: 70% storage reduction, 10x faster queries

### Uber
- **Transactional Data**: Avro in Kafka
- **Analytics Data**: Parquet in S3
- **Result**: Schema evolution without downtime

### Spotify
- **Event Logs**: JSON → Parquet daily
- **User Profiles**: Parquet partitioned by country
- **Result**: $2M/year savings in storage costs

## Conclusion

### The Clear Winner for Data Lakes: Parquet ⭐

**Why Parquet is #1**:
1. **Storage Efficiency**: 70-90% compression
2. **Query Speed**: 5-10x faster than CSV/JSON
3. **Industry Standard**: Supported by every tool
4. **Cost Savings**: Massive reduction in S3 costs
5. **Performance**: Columnar = perfect for analytics

**Golden Rule**:
> "If you're building a data lake, use Parquet.
> If you're not sure, use Parquet.
> If someone suggests CSV for big data, show them this guide."

### Quick Reference Card

| Scenario | Format | Why |
|----------|--------|-----|
| Data Lake (Silver/Gold) | Parquet | Best performance & compression |
| Data Exchange | CSV | Universal compatibility |
| API Responses | JSON | Web standard |
| Streaming/Kafka | Avro | Schema evolution |
| Hive Tables | ORC | Hive-optimized |
| Raw Data Ingestion | Original | Preserve lineage |

---

**Last Updated**: February 2, 2026
**Module**: 02 - Storage Basics
**Author**: Cloud Data Training Team
