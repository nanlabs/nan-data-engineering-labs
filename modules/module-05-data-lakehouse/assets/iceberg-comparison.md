# Delta Lake vs Apache Iceberg: Comparison

## 📊 Feature Comparison

| Feature | Delta Lake | Apache Iceberg | Winner |
|---------|-----------|----------------|--------|
| **ACID Transactions** | ✅ Full ACID | ✅ Full ACID | 🤝 Tie |
| **Time Travel** | ✅ versionAsOf | ✅ snapshot-id | 🤝 Tie |
| **Schema Evolution** | ✅ mergeSchema | ✅ Schema evolution | 🤝 Tie |
| **Partition Evolution** | ⚠️ Limited | ✅ **Hidden partitioning** | 🏆 Iceberg |
| **Data Skipping** | ✅ Z-Ordering | ⚠️ Manual sorting | 🏆 Delta |
| **Multi-Engine Support** | ⚠️ Spark-focused | ✅ **Spark, Trino, Presto, Flink** | 🏆 Iceberg |
| **Governance** | Databricks | Apache Foundation | 🏆 Iceberg (open) |
| **Metadata Performance** | ✅ Fast (JSON log) | ⚠️ Slower (multiple files) | 🏆 Delta |
| **Optimization** | ✅ OPTIMIZE command | ⚠️ Manual | 🏆 Delta |
| **Streaming Support** | ✅ Excellent | ⚠️ Limited | 🏆 Delta |
| **Cloud Native** | ✅ S3, ADLS, GCS | ✅ S3, ADLS, GCS | 🤝 Tie |
| **Ecosystem** | Databricks, Spark | Multi-engine | 🏆 Iceberg |

## 🎯 Use Cases

### Usa Delta Lake cuando:

1. **Databricks Ecosystem**: Tu stack principal es Databricks
2. **Spark-Heavy**: Tu processing es principalmente PySpark
3. **Z-Ordering Critical**: Necesitas data skipping avanzado
4. **Streaming**: Procesamiento de streams continuo
5. **Simplicity**: You want a simpler setup
6. **Optimize Write**: You need automatic compaction

### Usa Apache Iceberg cuando:

1. **Multi-Engine**: You use Trino, Presto, Flink in addition to Spark
2. **Partition Evolution**: Cambias estructura de particiones frecuentemente
3. **Open Governance**: Prefieres Apache Foundation vs empresa
4. **Cross-Platform**: Integration with multiple platforms
5. **Analytics Engines**: Heavy use de query engines como Trino
6. **Future-Proofing**: Evitar vendor lock-in

## 💻 Code Comparison

### Write Operations

**Delta Lake**:
```python
df.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("country") \
    .save("s3a://bucket/table")
```

**Iceberg**:
```python
df.writeTo("catalog.db.table") \
    .using("iceberg") \
    .partitionedBy("country") \
    .create()
```

### Time Travel

**Delta Lake**:
```python
# By version
spark.read.format("delta") \
    .option("versionAsOf", 2) \
    .load("/path")

# By timestamp
spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-15") \
    .load("/path")
```

**Iceberg**:
```python
# By snapshot
spark.read.format("iceberg") \
    .option("snapshot-id", 12345) \
    .load("catalog.db.table")

# By timestamp
spark.read.format("iceberg") \
    .option("as-of-timestamp", "1642262400000") \
    .load("catalog.db.table")
```

### Schema Evolution

**Delta Lake**:
```python
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("/path")
```

**Iceberg**:
```python
from pyspark.sql.types import StringType
spark.sql("""
    ALTER TABLE catalog.db.table 
    ADD COLUMN new_col STRING
""")
```

### Optimization

**Delta Lake**:
```python
from delta.tables import DeltaTable
delta_table = DeltaTable.forPath(spark, "/path")

# Compaction
delta_table.optimize().executeCompaction()

# Z-Ordering
delta_table.optimize().executeZOrderBy("col1", "col2")

# Vacuum
delta_table.vacuum(168)  # hours
```

**Iceberg**:
```python
# Compaction (manual)
spark.sql("""
    CALL catalog.system.rewrite_data_files(
        table => 'db.table',
        options => map('target-file-size-bytes', '134217728')
    )
""")

# Expire snapshots
spark.sql("""
    CALL catalog.system.expire_snapshots(
        table => 'db.table',
        older_than => TIMESTAMP '2024-01-01 00:00:00'
    )
""")
```

## 🏗️ Architecture Differences

### Delta Lake Architecture

```
Delta Table
├── data/ (Parquet files)
└── _delta_log/
    ├── 00000000000000000000.json (V0)
    ├── 00000000000000000001.json (V1)
    └── 00000000000000000002.json (V2)
```

**Pros**:
- Simple and fast transaction log
- Lectura secuencial del log
- Checkpoint files para performance

### Iceberg Architecture

```
Iceberg Table
├── data/ (Parquet files)
└── metadata/
    ├── version-hint.text
    ├── v1.metadata.json
    ├── v2.metadata.json
    ├── snap-001.avro
    └── manifest-list-001.avro
```

**Pros**:
- More detailed metadata
- Partition evolution sin reescritura
- Hidden partitioning (abstraction)

## 📈 Performance Benchmarks

(Synthetic tests, YMMV)

| Operation | Delta Lake | Iceberg |
|-----------|-----------|---------|
| Write 1M rows | 12s | 15s |
| Read full table | 8s | 9s |
| Time Travel query | 2s | 3s |
| Metadata listing | **1s** | 3s |
| Schema evolution | 5s | 4s |
| Partition pruning | **3s** | 4s |

## 🔄 Migration Path

### Delta → Iceberg

```python
# 1. Export data from Delta
df = spark.read.format("delta").load("/delta/path")

# 2. Write to Iceberg
df.writeTo("catalog.db.table").using("iceberg").create()

# 3. Copy metadata (manually)
```

### Iceberg → Delta

```python
# 1. Export data from Iceberg
df = spark.read.format("iceberg").load("catalog.db.table")

# 2. Write to Delta
df.write.format("delta").save("/delta/path")
```

⚠️ **Note**: Time Travel history no se preserva en migration

## 💡 Recommendations

### For Enterprises
- **Heavy Databricks**: Delta Lake
- **Multi-Platform Analytics**: Iceberg
- **Hybrid**: Use both (Delta for streams, Iceberg for analytics)

### For Startups
- **Quick MVP**: Delta Lake (simpler)
- **Future flexibility**: Iceberg (menos vendor lock-in)

### For Data Engineers
- **Learn both**: Both are industry standard
- **Lakehouse pattern**: Aplica con ambos
- **Skills transferable**: Conceptos son similares

## 📚 Resources

- Delta Lake: https://delta.io
- Apache Iceberg: https://iceberg.apache.org
- Lakehouse Benchmarking: https://www.onehouse.ai/blog/apache-hudi-vs-delta-lake-vs-apache-iceberg-lakehouse-feature-comparison
