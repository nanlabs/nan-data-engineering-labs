# Databricks Lakehouse Platform - Core Concepts

This document covers the fundamental concepts of Databricks, Delta Lake, Unity Catalog, and the Lakehouse architecture.

## Table of Contents

1. [Databricks Platform Architecture](#databricks-platform-architecture)
2. [Delta Lake Fundamentals](#delta-lake-fundamentals)
3. [Unity Catalog](#unity-catalog)
4. [Medallion Architecture](#medallion-architecture)
5. [Databricks Components](#databricks-components)
6. [Performance Optimization](#performance-optimization)

---

## Databricks Platform Architecture

### What is Databricks?

**Databricks** is a unified analytics platform built on top of Apache Spark, providing:
- **Collaborative workspace** for data engineers, data scientists, and analysts
- **Managed Spark clusters** with auto-scaling and optimizations
- **Delta Lake** for reliable data lakes with ACID transactions
- **Unity Catalog** for data governance and security
- **MLflow** for ML lifecycle management
- **SQL Analytics** for BI and dashboards

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│         Databricks Workspace (Control Plane)        │
│  - Notebooks, Jobs, Clusters, SQL, ML, Repos        │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│      Databricks Runtime (Data Plane - Compute)      │
│  - Spark 3.5, Photon Engine, Delta Lake, MLlib     │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│        Cloud Storage (Data Plane - Storage)         │
│      - S3 (AWS), ADLS (Azure), GCS (Google)         │
└─────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Unified Platform**: Single platform for batch, streaming, ML, and SQL
2. **Performance**: 10-50x faster than open-source Spark (Photon engine)
3. **Collaboration**: Shared notebooks with live co-editing
4. **Governance**: Centralized access control and lineage (Unity Catalog)
5. **Managed Infrastructure**: No cluster management overhead
6. **Multi-Cloud**: Run on AWS, Azure, or GCP with same API

---

## Delta Lake Fundamentals

### What is Delta Lake?

**Delta Lake** is an open-source storage layer that brings ACID transactions to Apache Spark and big data workloads.

### Key Features

#### 1. ACID Transactions
```python
# Multiple writers can safely write to the same table
spark.sql("""
    MERGE INTO customers
    USING updates
    ON customers.id = updates.id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")
```

**Without Delta Lake:**
- Corrupted data if multiple writers
- No isolation between reads and writes
- Failed jobs leave partial data

**With Delta Lake:**
- Serializable isolation (no dirty reads)
- Atomic commits (all-or-nothing)
- Concurrent reads and writes safely

#### 2. Time Travel (Data Versioning)
```python
# Query data as it was 7 days ago
df = spark.read.format("delta") \
    .option("timestampAsOf", "2024-03-01") \
    .load("/path/to/table")

# Or by version number
df = spark.read.format("delta") \
    .option("versionAsOf", 5) \
    .load("/path/to/table")

# Restore table to previous version
spark.sql("RESTORE customers TO VERSION AS OF 10")
```

**Use Cases:**
- Rollback to previous known-good state
- Audit and compliance (who changed what when)
- Reproduce ML training data from specific dates
- Compare data across time periods

#### 3. Schema Evolution
```python
# Add new columns without breaking existing queries
df_with_new_column.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("/path/to/table")

# Automatically handles:
# - New columns (filled with NULL for old rows)
# - Column type changes (with validation)
# - Column reordering
```

#### 4. UPSERT (Merge) Support
```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, "/path/to/table")

delta_table.alias("target").merge(
    updates.alias("source"),
    "target.id = source.id"
).whenMatchedUpdate(set={
    "name": "source.name",
    "updated_at": "current_timestamp()"
}).whenNotMatchedInsert(values={
    "id": "source.id",
    "name": "source.name",
    "created_at": "current_timestamp()"
}).execute()
```

**Use Cases:**
- Change Data Capture (CDC) from databases
- Slowly Changing Dimensions (SCD)
- Incremental updates to analytical tables

#### 5. Data Skipping

Delta Lake automatically collects **min/max statistics** for each file:
```python
# Query with WHERE clause
df = spark.read.format("delta").load("/path/to/table") \
    .where("date >= '2024-01-01' AND region = 'US-EAST'")

# Delta Lake skips files that don't match:
# - Files where max(date) < '2024-01-01' (skipped)
# - Files where region != 'US-EAST' (skipped)
# Result: Read only 5% of files instead of 100%
```

**Impact:** 10-100x faster queries on large tables

#### 6. Z-Ordering (Multi-Dimensional Clustering)
```python
# Optimize table for common query patterns
spark.sql("""
    OPTIMIZE customers
    ZORDER BY (region, signup_date)
""")
```

**Before Z-Ordering:**
```
File1: region=[US, EU, ASIA], date=[2020-2024] (all over the place)
File2: region=[US, EU, ASIA], date=[2020-2024] (all over the place)
→ Must scan all files for region='US' AND date='2024'
```

**After Z-Ordering:**
```
File1: region=[US], date=[2024] (co-located)
File2: region=[EU], date=[2023] (co-located)
→ Scan only File1 (90% file skip rate)
```

**Performance Gain:** 2-10x faster queries

### Delta Lake Internals

#### Transaction Log (`_delta_log/`)

Every Delta table has a transaction log that records all changes:

```
my_table/
├── _delta_log/
│   ├── 00000000000000000000.json  ← Version 0 (initial commit)
│   ├── 00000000000000000001.json  ← Version 1 (append)
│   ├── 00000000000000000002.json  ← Version 2 (update)
│   └── 00000000000000000003.json  ← Version 3 (delete)
├── part-00000-xxx.parquet
├── part-00001-xxx.parquet
└── part-00002-xxx.parquet
```

Each log file contains:
- **Add**: New files added
- **Remove**: Files deleted (logically, not physically)
- **Metadata**: Schema, partitioning, properties
- **Protocol**: Delta Lake version

**Reading a Delta Table:**
1. Read transaction log from newest to oldest
2. Reconstruct current state (list of active files)
3. Read Parquet files
4. Apply schema and filters

**Writing to a Delta Table:**
1. Write Parquet files to storage
2. Append to transaction log (atomic)
3. If log write succeeds, commit succeeds
4. If log write fails, data files are orphaned (cleaned by VACUUM)

#### File Format

- **Storage**: Parquet files (columnar, compressed)
- **Metadata**: JSON transaction log
- **Checkpoints**: Every 10 commits, write a Parquet checkpoint for fast reads

### Delta Lake vs Parquet

| Feature | Parquet | Delta Lake |
|---------|---------|------------|
| **ACID Transactions** | ❌ No | ✅ Yes |
| **Schema Evolution** | ❌ Manual | ✅ Automatic |
| **Time Travel** | ❌ No | ✅ Yes (versioned) |
| **UPSERT/DELETE** | ❌ Read-all + Write-all | ✅ Efficient merge |
| **Data Quality** | ❌ Manual validation | ✅ Constraints + expectations |
| **Concurrent Writes** | ⚠️ Unsafe | ✅ Safe (optimistic concurrency) |
| **File Skipping** | ⚠️ Basic (partition pruning) | ✅ Advanced (stats, Z-ordering) |
| **Vacuum Old Versions** | ❌ N/A | ✅ `VACUUM` command |

**When to Use:**
- **Parquet**: Immutable archives, one-time writes
- **Delta Lake**: Production tables, frequent updates, multi-user access

---

## Unity Catalog

### What is Unity Catalog?

**Unity Catalog** is a unified governance solution for data and AI assets providing:
- **Fine-grained access control** (table, column, row-level)
- **Data lineage** (track data flows across pipelines)
- **Data discovery** (search and explore datasets)
- **Centralized metadata** (single source of truth)
- **Audit logging** (track all data access)

### Three-Level Namespace

Unity Catalog uses a **three-level namespace** (vs traditional two-level):

```
catalog.schema.table
   ↓      ↓      ↓
  dev.sales.customers
  prod.sales.customers
  test.analytics.revenue
```

**Traditional (Hive):**
```
database.table
   ↓      ↓
sales.customers (no environment separation)
```

**Benefits:**
1. **Environment isolation**: dev, staging, prod in same workspace
2. **Multi-tenant**: team1, team2, team3 catalogs
3. **Clear ownership**: Each catalog has owner
4. **Simplified migrations**: Promote from dev → staging → prod

### Permission Model

#### Hierarchy

```
Metastore (root)
└── Catalog
    └── Schema
        └── Table/View
            └── Column
```

**Grant permissions at any level** (inherited downward):

```sql
-- Catalog level
GRANT USE CATALOG ON CATALOG prod TO `data-analysts`;

-- Schema level
GRANT SELECT ON SCHEMA prod.sales TO `data-analysts`;

-- Table level
GRANT SELECT ON TABLE prod.sales.customers TO `data-analysts`;

-- Column level (mask PII)
GRANT SELECT(id, name, email) ON TABLE prod.sales.customers TO `external-partners`;
```

#### Row-Level Security

```sql
-- Create row filter
CREATE FUNCTION prod.sales.customer_filter()
RETURNS BOOLEAN
RETURN is_account_group_member('admin') OR current_user() = customer_owner;

-- Apply to table
ALTER TABLE prod.sales.customers SET ROW FILTER prod.sales.customer_filter ON (owner);
```

**Result:** Users can only see rows they own (unless admin)

#### Dynamic Views (Column-Level Security)

```sql
CREATE VIEW prod.sales.customers_masked AS
SELECT
  customer_id,
  name,
  CASE
    WHEN is_account_group_member('pii-access') THEN email
    ELSE 'REDACTED'
  END AS email,
  CASE
    WHEN is_account_group_member('pii-access') THEN ssn
    ELSE '***-**-' || RIGHT(ssn, 4)
  END AS ssn
FROM prod.sales.customers;

-- Grant access to masked view
GRANT SELECT ON VIEW prod.sales.customers_masked TO `data-analysts`;
```

### Data Lineage

Unity Catalog automatically tracks:
- **Column-level lineage**: Which downstream columns depend on which upstream columns
- **Table lineage**: Data flow through pipelines
- **Notebook lineage**: Which notebooks read/write which tables
- **Job lineage**: Which jobs produce which outputs

**Example:**
```
S3 raw data
  → Bronze table (ingestion notebook)
    → Silver table (transformation job)
      → Gold table (aggregation notebook)
        → Dashboard (SQL query)
```

**View in UI:**
- Data Explorer → Table → Lineage tab
- See all upstream sources and downstream consumers
- Track data quality issues to root cause

### Data Discovery

**Search capabilities:**
- Full-text search across table names, comments, tags
- Filter by catalog, schema, owner, modified date
- Browse by tags (e.g., "PII", "financial", "experimental")

**Metadata enrichment:**
```sql
-- Add table comment
COMMENT ON TABLE customers IS 'Customer master data from Salesforce';

-- Add column comments
ALTER TABLE customers ALTER COLUMN email COMMENT 'Customer email (PII)';

-- Add tags
ALTER TABLE customers SET TAGS ('pii' = 'high', 'department' = 'sales');
```

---

## Medallion Architecture

### What is Medallion Architecture?

A data design pattern that organizes data into **Bronze**, **Silver**, and **Gold** layers:

```
Bronze (Raw) → Silver (Cleaned) → Gold (Aggregated) → Analytics/ML
```

### Layer Breakdown

#### 🥉 Bronze Layer (Raw)

**Purpose:** Ingest raw data as-is, no transformations

**Characteristics:**
- Exact copy of source data
- All columns preserved
- Append-only (immutable)
- Audit columns: `_ingested_at`, `_source_file`

**Example:**
```python
# Ingest JSON from S3
df = spark.read.json("s3://raw-data/events/2024-03-09/")
df = df.withColumn("_ingested_at", current_timestamp())

df.write.format("delta") \
    .mode("append") \
    .save("/mnt/bronze/events")
```

**Benefits:**
- Fast ingestion (no processing)
- Complete history retained
- Re-process easily if logic changes

#### 🥈 Silver Layer (Cleaned)

**Purpose:** Clean, deduplicate, and conform data

**Transformations:**
- Remove duplicates
- Fix data types
- Standardize formats
- Apply business rules
- Filter invalid records

**Example:**
```python
bronze_df = spark.read.format("delta").load("/mnt/bronze/events")

silver_df = bronze_df \
    .dropDuplicates(["event_id"]) \
    .filter("event_type IS NOT NULL") \
    .withColumn("event_date", to_date("event_timestamp")) \
    .withColumn("user_id", col("user_id").cast("long"))

silver_df.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save("/mnt/silver/events")
```

**Benefits:**
- Single source of truth
- Consistent data quality
- Ready for joins and aggregations

#### 🥇 Gold Layer (Aggregated)

**Purpose:** Business-level aggregations for analytics and ML

**Characteristics:**
- Denormalized (star schema, wide tables)
- Pre-aggregated metrics
- Slowly Changing Dimensions (SCD)
- Optimized for queries

**Example:**
```python
silver_events = spark.read.format("delta").load("/mnt/silver/events")
silver_users = spark.read.format("delta").load("/mnt/silver/users")

# Create daily active users aggregation
gold_df = silver_events \
    .join(silver_users, "user_id") \
    .groupBy("event_date", "country") \
    .agg(
        countDistinct("user_id").alias("dau"),
        count("event_id").alias("total_events"),
        sum("revenue").alias("total_revenue")
    )

gold_df.write.format("delta") \
    .mode("overwrite") \
    .save("/mnt/gold/daily_active_users")
```

**Benefits:**
- Fast query performance
- Simple for analysts (no complex joins)
- Consistent metrics across teams

### Best Practices

1. **Bronze is append-only**: Never delete from Bronze (audit trail)
2. **Silver is idempotent**: Re-running should produce same result
3. **Gold is denormalized**: Optimize for read performance
4. **Incremental processing**: Use Delta Lake's `merge` for efficiency
5. **Data quality checks**: Validate at each layer

---

## Databricks Components

### 1. Workspace

**Purpose:** Collaborative environment for notebooks, jobs, clusters

**Features:**
- Folder organization
- Git integration (Repos)
- Access control (workspace ACLs)
- Shared notebooks (live co-editing)

### 2. Clusters

**Types:**
- **All-Purpose**: Interactive development, notebooks
- **Job Clusters**: Automated jobs (cheaper, ephemeral)
- **SQL Warehouses**: Optimized for SQL queries

**Cluster Modes:**
- **Standard**: Single user, full admin access
- **High Concurrency**: Multi-user, table ACLs, query isolation
- **Single Node**: No workers, for small data

**Auto-Scaling:**
```python
{
  "autoscale": {
    "min_workers": 2,
    "max_workers": 10
  },
  "autotermination_minutes": 30
}
```

### 3. Notebooks

**Languages Supported:**
- Python (PySpark)
- SQL
- Scala
- R

**Magic Commands:**
```python
%python  # Python cell
%sql     # SQL cell
%scala   # Scala cell
%sh      # Shell commands
%fs      # DBFS file system commands
%md      # Markdown documentation
```

**Collaborative Features:**
- Real-time co-editing
- Comments and threads
- Version control (Git integration)
- Parameter widgets for interactivity

### 4. Workflows (Jobs)

**Purpose:** Schedule and orchestrate data pipelines

**Features:**
- Task dependencies (DAG)
- Retry logic
- Email/webhook alerts
- Job clusters (auto-terminate)

**Example YAML:**
```yaml
tasks:
  - task_key: bronze_ingestion
    notebook_task:
      notebook_path: /Repos/project/ingest_bronze
    new_cluster: {...}

  - task_key: silver_transformation
    depends_on:
      - task_key: bronze_ingestion
    notebook_task:
      notebook_path: /Repos/project/transform_silver
    new_cluster: {...}
```

### 5. Databricks SQL

**Purpose:** BI and dashboards for analysts

**Features:**
- Visual query builder
- Dashboards with auto-refresh
- Alerts (e.g., "Sales < threshold")
- SQL endpoints (optimized for queries)

**Use Cases:**
- Executive dashboards
- Self-service analytics
- Scheduled reports

### 6. MLflow

**Purpose:** ML lifecycle management

**Components:**
- **Tracking**: Log experiments (params, metrics, artifacts)
- **Projects**: Package ML code for reproducibility
- **Models**: Model registry (staging, production)
- **Model Serving**: Deploy models as REST APIs

**Example:**
```python
import mlflow

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("learning_rate", 0.01)

    # Train model
    model = train_model(data)

    # Log metrics
    mlflow.log_metric("accuracy", 0.95)

    # Log model
    mlflow.sklearn.log_model(model, "model")
```

---

## Performance Optimization

### 1. Photon Engine

**What:** Vectorized query engine written in C++ (10-50x faster than Spark)

**Enabled by default** on Databricks Runtime 9.1+

**Best for:**
- SQL queries
- DataFrame operations (filter, join, aggregate)
- Parquet/Delta read/write

**Limitations:**
- User-defined functions (UDFs) fall back to JVM
- Some advanced Spark features not supported

### 2. Adaptive Query Execution (AQE)

**Automatic optimizations:**
- Dynamic partition pruning
- Join strategy changes (broadcast vs shuffle)
- Skew handling

**Enable:**
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
```

### 3. Caching

**Persist frequently-used DataFrames:**
```python
df.cache()  # Lazy (triggered on first action)
df.persist(StorageLevel.MEMORY_AND_DISK)  # Spill to disk if memory full
```

**Delta Cache (automatic):**
- Caches Delta/Parquet files on cluster SSD
- Transparent (no code changes)
- Speeds up repeated queries 2-10x

### 4. Partitioning

**Hive-style partitioning:**
```python
df.write.format("delta") \
    .partitionBy("year", "month") \
    .save("/path/to/table")

# Results in:
# /path/to/table/year=2024/month=01/part-xxx.parquet
# /path/to/table/year=2024/month=02/part-xxx.parquet
```

**Best practices:**
- Partition by commonly-filtered columns (date, region)
- Avoid over-partitioning (<1GB per partition ideal)
- Max 1000-2000 partitions per table

### 5. File Compaction

**Problem:** Small files slow down queries (more overhead)

**Solution:**
```python
# Optimize (combine small files into larger ones)
spark.sql("OPTIMIZE customers")

# Target file size: 1GB (configurable)
spark.conf.set("spark.databricks.delta.optimize.maxFileSize", 1073741824)
```

**Run weekly:** Part of maintenance workflows

### 6. Vacuum Old Versions

**Problem:** Time travel keeps old versions forever (storage cost)

**Solution:**
```python
# Delete files older than 7 days (after retention period)
spark.sql("VACUUM customers RETAIN 168 HOURS")  # 7 days = 168 hours
```

**Default retention:** 30 days (configurable)

---

## Summary

### Key Takeaways

1. **Databricks** = Unified analytics platform (Spark + Delta Lake + Unity Catalog + ML)
2. **Delta Lake** = ACID transactions + time travel + UPSERT for data lakes
3. **Unity Catalog** = Centralized governance (access control + lineage + discovery)
4. **Medallion Architecture** = Bronze (raw) → Silver (cleaned) → Gold (aggregated)
5. **Performance** = Photon engine + caching + partitioning + Z-ordering

### Databricks vs Open-Source Spark

| Feature | Open-Source Spark | Databricks |
|---------|-------------------|------------|
| **Cluster Management** | Manual (EMR, GKE) | Fully managed |
| **Performance** | Baseline | 10-50x faster (Photon) |
| **Collaboration** | None (local notebooks) | Real-time co-editing |
| **Governance** | DIY (Ranger, etc.) | Unity Catalog built-in |
| **ML Tracking** | Manual | MLflow integrated |
| **Cost** | Infrastructure only | Infrastructure + DBU |
| **Time to Value** | Weeks (setup) | Hours (sign up) |

### Next Steps

- Read [setup-guide.md](setup-guide.md) to create your Databricks account
- Explore [best-practices.md](best-practices.md) for development workflows
- Review [resources.md](resources.md) for official documentation

---

**Document Version:** 1.0
**Last Updated:** March 2026
**Databricks Runtime:** 14.3 LTS (Spark 3.5.x)
