# Databricks Best Practices

This document covers development workflows, optimization techniques, and production patterns for Databricks.

## Table of Contents

1. [Development Workflow](#development-workflow)
2. [Cluster Management](#cluster-management)
3. [Code Organization](#code-organization)
4. [Performance Optimization](#performance-optimization)
5. [Cost Optimization](#cost-optimization)
6. [Security & Governance](#security--governance)
7. [Production Deployment](#production-deployment)
8. [Monitoring & Debugging](#monitoring--debugging)

---

## Development Workflow

### 1. Environment Strategy

**Use three-level namespace for environments:**

```sql
-- Development
CREATE CATALOG dev;
CREATE SCHEMA dev.sales;

-- Staging
CREATE CATALOG staging;
CREATE SCHEMA staging.sales;

-- Production
CREATE CATALOG prod;
CREATE SCHEMA prod.sales;
```

**Benefits:**
- Clear isolation between environments
- Easy promotion: dev → staging → prod
- Prevent accidental production writes

### 2. Notebook Naming Conventions

```
01-bronze-ingestion.py       # Numbering shows execution order
02-silver-transformation.py
03-gold-aggregation.py

utils/
├── data_quality.py          # Shared utility functions
└── schema_definitions.py
```

**Notebook structure:**
```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: Customer Data Ingestion
# MAGIC
# MAGIC **Purpose:** Ingest raw customer data from S3
# MAGIC **Schedule:** Daily at 2 AM UTC
# MAGIC **Owner:** data-engineering-team@example.com

# COMMAND ----------
# Setup and configuration
from pyspark.sql import functions as F
from delta.tables import DeltaTable

# Parameters (use widgets for interactivity)
dbutils.widgets.text("run_date", "2024-03-09")
run_date = dbutils.widgets.get("run_date")

# COMMAND ----------
# Business logic
df = spark.read.parquet(f"s3://raw-data/customers/{run_date}/")
# ... transformations ...

# COMMAND ----------
# Write to Delta
df.write.format("delta").mode("append").save("/mnt/bronze/customers")

# COMMAND ----------
# Validation
row_count = spark.read.format("delta").load("/mnt/bronze/customers").count()
assert row_count > 0, "No data written!"
print(f"✅ Successfully ingested {row_count:,} rows")
```

### 3. Version Control with Git

**Best practice:** Use Repos (Git integration)

```bash
# Workspace → Repos → Add Repo
URL: https://github.com/your-org/databricks-pipelines
Branch: main
```

**Folder structure:**
```
/Repos/your-email/databricks-pipelines/
├── notebooks/
│   ├── ingestion/
│   ├── transformation/
│   └── aggregation/
├── tests/
├── config/
└── README.md
```

**Commit workflow:**
1. Develop in notebook
2. Run tests
3. Commit via Repos UI or CLI
4. Create pull request
5. CI/CD pipeline runs tests
6. Merge to main

### 4. Parameterization with Widgets

Make notebooks reusable:

```python
# Create widgets (interactive parameters)
dbutils.widgets.text("catalog", "dev", "Catalog")
dbutils.widgets.text("schema", "sales", "Schema")
dbutils.widgets.dropdown("mode", "incremental", ["full", "incremental"], "Load Mode")

# Use parameters
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
mode = dbutils.widgets.get("mode")

table_name = f"{catalog}.{schema}.customers"
print(f"Processing: {table_name} in {mode} mode")
```

**Run with parameters:**
```python
# Programmatically
dbutils.notebook.run(
    "/Repos/project/ingest_customers",
    timeout_seconds=3600,
    arguments={"catalog": "prod", "mode": "incremental"}
)
```

---

## Cluster Management

### 1. Cluster Types by Use Case

| Use Case | Cluster Type | Config |
|----------|--------------|--------|
| **Interactive development** | All-Purpose | Standard mode, auto-terminate 30 min |
| **Scheduled ETL** | Job Cluster | Jobs mode, terminate after job |
| **SQL dashboards** | SQL Warehouse | Serverless or Pro |
| **Ad-hoc queries** | All-Purpose | High Concurrency mode |
| **ML training** | All-Purpose or Job | ML Runtime, GPU instances |

### 2. Right-Sizing Clusters

**Data size guidelines:**
- <10GB: Single-node or 2 workers
- 10-100GB: 2-8 workers
- 100GB-1TB: 8-20 workers
- >1TB: 20+ workers with auto-scaling

**Monitor utilization:**
```python
# Check cluster metrics
%sql
SELECT
  cluster_id,
  SUM(executor_memory_used_mb) / SUM(executor_memory_total_mb) * 100 as memory_utilization_pct,
  SUM(executor_cpu_used_cores) / SUM(executor_cpu_total_cores) * 100 as cpu_utilization_pct
FROM system.compute.cluster_metrics
WHERE timestamp > current_timestamp() - INTERVAL 1 HOUR
GROUP BY cluster_id;
```

**Right-size if:**
- CPU < 30% consistently → downsize instance type
- Memory < 40% consistently → downsize memory
- CPU > 85% consistently → add workers or upsize
- Memory > 90% → add workers or increase memory

### 3. Auto-Termination

**Always enable** (prevent $$$$ overruns):

```python
{
  "autotermination_minutes": 30,  # Community: 120, Production: 30-60
  "spark_conf": {
    "spark.databricks.cluster.profile": "serverless",
    "spark.databricks.delta.autoOptimize.autoCompact": "true"
  }
}
```

### 4. Cluster Pools (Cost Optimization)

**Pre-allocated VMs** that start instantly:

```python
# Create pool
{
  "pool_name": "shared-pool",
  "min_idle_instances": 2,
  "max_capacity": 10,
  "idle_instance_auto_termination_minutes": 30
}

# Use pool in cluster
{
  "cluster_name": "fast-start-cluster",
  "instance_pool_id": "pool-abc123",
  "autoscale": {"min_workers": 2, "max_workers": 10}
}
```

**Benefits:**
- 80% faster cluster start (30 sec vs 5 min)
- Cost-neutral (pay same VM rates)
- Ideal for frequent interactive work

---

## Code Organization

### 1. Modular Functions

**Extract logic into reusable functions:**

```python
# utils/data_quality.py
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def validate_schema(df: DataFrame, expected_cols: list) -> DataFrame:
    """Validate DataFrame has expected columns."""
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df

def remove_duplicates(df: DataFrame, key_cols: list) -> DataFrame:
    """Remove duplicates based on key columns."""
    return df.dropDuplicates(key_cols)

def add_audit_columns(df: DataFrame) -> DataFrame:
    """Add standard audit columns."""
    return df \
        .withColumn("_ingested_at", F.current_timestamp()) \
        .withColumn("_ingested_by", F.current_user())
```

**Use in notebooks:**
```python
%run ./utils/data_quality

# Apply functions
df = validate_schema(df, ["id", "name", "email"])
df = remove_duplicates(df, ["id"])
df = add_audit_columns(df)
```

### 2. Configuration Management

**Centralize config in separate file:**

```python
# config/table_config.py
from dataclasses import dataclass

@dataclass
class TableConfig:
    catalog: str
    schema: str
    table: str
    path: str
    partition_by: list

# Define configs
TABLES = {
    "customers": TableConfig(
        catalog="prod",
        schema="sales",
        table="customers",
        path="/mnt/gold/customers",
        partition_by=["country", "signup_year"]
    ),
    "orders": TableConfig(
        catalog="prod",
        schema="sales",
        table="orders",
        path="/mnt/gold/orders",
        partition_by=["order_date"]
    )
}
```

**Use in notebooks:**
```python
from config.table_config import TABLES

config = TABLES["customers"]
df.write.format("delta") \
    .partitionBy(config.partition_by) \
    .save(config.path)
```

### 3. Testing Strategy

**Unit tests for utility functions:**

```python
# tests/test_data_quality.py
import pytest
from utils.data_quality import validate_schema, remove_duplicates

def test_validate_schema_success(spark):
    df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])
    result = validate_schema(df, ["id", "name"])
    assert result.count() == 2

def test_validate_schema_failure(spark):
    df = spark.createDataFrame([(1, "Alice")], ["id", "name"])
    with pytest.raises(ValueError, match="Missing columns"):
        validate_schema(df, ["id", "email"])

def test_remove_duplicates(spark):
    df = spark.createDataFrame([(1, "A"), (1, "A"), (2, "B")], ["id", "name"])
    result = remove_duplicates(df, ["id"])
    assert result.count() == 2
```

**Integration tests in notebook:**

```python
# COMMAND ----------
# Test: Bronze ingestion
df_bronze = spark.read.format("delta").load("/mnt/bronze/customers")
assert df_bronze.count() > 0, "Bronze table is empty"
assert "_ingested_at" in df_bronze.columns, "Missing audit column"

# Test: Silver transformation
df_silver = spark.read.format("delta").load("/mnt/silver/customers")
assert df_silver.where("email IS NULL").count() == 0, "Found NULL emails"
assert df_silver.where("id < 0").count() == 0, "Found invalid IDs"

print("✅ All tests passed")
```

---

## Performance Optimization

### 1. Delta Lake Optimization

**OPTIMIZE (file compaction):**
```sql
-- Compact small files into larger ones (target: 1GB)
OPTIMIZE customers;

-- With Z-ordering (co-locate related data)
OPTIMIZE customers ZORDER BY (country, signup_date);

-- Schedule weekly
-- Databricks can auto-optimize with liquid clustering (DBR 13.2+)
ALTER TABLE customers
SET TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');
```

**VACUUM (delete old versions):**
```sql
-- Delete files older than 7 days (save storage)
VACUUM customers RETAIN 168 HOURS;

-- Check what would be deleted (dry run)
VACUUM customers RETAIN 168 HOURS DRY RUN;
```

**Run monthly** as maintenance job.

### 2. Caching Strategies

**Delta Cache (automatic):**
- Enabled by default on all-purpose clusters
- Caches Parquet files on local SSD
- 2-10x speedup on repeated queries

**DataFrame caching (explicit):**
```python
# Cache frequently-used DataFrame
df.cache()  # Lazy (triggered on first action)

# Persist with storage level
from pyspark import StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK)  # Spill to disk if memory full

# Check if cached
df.is_cached  # True

# Unpersist when done
df.unpersist()
```

**When to cache:**
- DataFrame used multiple times in notebook
- Interactive exploration with filters
- Small reference tables (<1GB)

**When NOT to cache:**
- Large DataFrames (>50% of cluster memory)
- DataFrames used only once
- ETL pipelines (single-pass processing)

### 3. Partition Pruning

**Leverage Hive partitioning:**
```python
# Write with partitions
df.write.format("delta") \
    .partitionBy("year", "month", "day") \
    .save("/mnt/events")

# Read with partition filter (fast!)
df_filtered = spark.read.format("delta") \
    .load("/mnt/events") \
    .where("year = 2024 AND month = 3")  # Only scans March 2024 partition
```

**Partition best practices:**
- Partition by commonly-filtered columns (date, region, category)
- Target partition size: 500MB - 2GB
- Avoid over-partitioning (<100MB partitions are slow)
- Max 10,000 partitions per table

### 4. Broadcast Joins

**For small dimension tables (<100MB):**
```python
from pyspark.sql import functions as F

# Force broadcast join
df_large.join(
    F.broadcast(df_small),
    "customer_id"
)

# Auto-broadcast threshold (default: 10MB)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 104857600)  # 100MB
```

**Benefits:** 10-100x faster than shuffle joins

### 5. Adaptive Query Execution (AQE)

**Enable** (on by default in DBR 8.0+):
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

**AQE optimizations:**
- Dynamically coalesces shuffle partitions (reduce small files)
- Converts sort-merge join to broadcast join (if small)
- Handles skewed data (split large partitions)

---

## Cost Optimization

### 1. DBU Cost Reduction

**Use Jobs Compute (60% cheaper than All-Purpose):**
```python
# Databricks Workflow job
{
  "tasks": [{
    "task_key": "etl",
    "notebook_task": {
      "notebook_path": "/Repos/project/etl"
    },
    "new_cluster": {
      "spark_version": "14.3.x-scala2.12",
      "node_type_id": "m5.xlarge",
      "num_workers": 4,
      "cluster_log_conf": {...}
    }
  }]
}

# Cost: $0.15/DBU (Jobs) vs $0.40/DBU (All-Purpose)
```

### 2. Spot Instances (70% discount)

**For fault-tolerant workloads:**
```python
{
  "aws_attributes": {
    "availability": "SPOT",
    "zone_id": "us-west-2a",
    "spot_bid_price_percent": 100,  # Max price = on-demand price
    "ebs_volume_type": "GENERAL_PURPOSE_SSD",
    "ebs_volume_count": 1,
    "ebs_volume_size": 100
  }
}
```

**Use for:**
- ETL jobs (can retry if interrupted)
- ML training (checkpoint frequently)
- Ad-hoc analysis

**Avoid for:**
- Production streaming workloads
- SLA-critical jobs
- Jobs without checkpointing

### 3. Cluster Reuse

**Use Workflows instead of separate clusters:**

**Before (expensive):**
```
Job 1: Start cluster → Run → Terminate
Job 2: Start cluster → Run → Terminate
Job 3: Start cluster → Run → Terminate
Cost: 3× cluster startup overhead
```

**After (efficient):**
```
Workflow:
  Task 1 → Task 2 → Task 3 (same cluster)
Cost: 1× cluster startup
```

### 4. SQL Warehouse Right-Sizing

**Start small, scale up:**
```
Development: 2X-Small ($0.22/DBU)
Production: Small ($0.44/DBU) or Medium ($0.88/DBU)
```

**Enable auto-stop (save when idle):**
- Auto-stop after: 20 minutes
- Auto-resume: ON (start when query received)

### 5. Storage Optimization

**VACUUM old versions (storage cost):**
```sql
-- Keep only 7 days of history
VACUUM customers RETAIN 168 HOURS;

-- For large tables (1TB+), saves $20-50/month
```

**Compress data:**
```python
# Use Parquet with Snappy (default)
df.write.format("delta") \
    .option("compression", "snappy") \
    .save("/path")

# For archival (slower but smaller)
df.write.format("delta") \
    .option("compression", "zstd") \
    .save("/path")
```

---

## Security & Governance

### 1. Unity Catalog Access Control

**Grant permissions at catalog level:**
```sql
-- Read-only analyst
GRANT USE CATALOG ON CATALOG prod TO `analysts`;
GRANT USE SCHEMA ON SCHEMA prod.sales TO `analysts`;
GRANT SELECT ON TABLE prod.sales.customers TO `analysts`;

-- Data engineer (read/write)
GRANT USE CATALOG, CREATE SCHEMA ON CATALOG prod TO `data-engineers`;
GRANT ALL PRIVILEGES ON SCHEMA prod.sales TO `data-engineers`;
```

**Row-level security:**
```sql
-- Users can only see their region's data
CREATE FUNCTION prod.sales.region_filter()
RETURNS BOOLEAN
RETURN current_user_region() = region;

ALTER TABLE prod.sales.customers
SET ROW FILTER prod.sales.region_filter ON (region);
```

### 2. Secrets Management

**Store credentials securely:**
```python
# Create secret scope (one-time setup)
# databricks secrets create-scope --scope prod-secrets

# Add secret
# databricks secrets put --scope prod-secrets --key db-password

# Use in notebook
db_password = dbutils.secrets.get(scope="prod-secrets", key="db-password")

# Connect to external database
jdbc_url = "jdbc:mysql://db.example.com:3306/sales"
df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "customers") \
    .option("user", "etl_user") \
    .option("password", db_password) \
    .load()
```

**Never hardcode secrets** in notebooks!

### 3. Data Lineage

**View lineage in Unity Catalog:**
1. Data Explorer → Select table
2. Lineage tab → See upstream/downstream dependencies

**Programmatic lineage:**
```python
# Add lineage metadata
df.write.format("delta") \
    .option("userMetadata", "source=salesforce,pipeline=daily_sync") \
    .save("/mnt/gold/customers")
```

---

## Production Deployment

### 1. CI/CD Pipeline

**Example GitHub Actions workflow:**
```yaml
name: Deploy Databricks Pipeline

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install Databricks CLI
        run: pip install databricks-cli

      - name: Run tests
        run: pytest tests/

      - name: Deploy notebooks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks workspace import_dir \
            ./notebooks \
            /Repos/prod/pipelines \
            --overwrite

      - name: Update job
        run: databricks jobs reset --job-id 123 --json-file job-config.json
```

### 2. Promotion Strategy

**Environment promotion:**
```
Dev → Test → Staging → Production
```

**Automated promotion script:**
```python
# promote.py
def promote_table(source_catalog, target_catalog, schema, table):
    """Copy table from source to target catalog."""
    source = f"{source_catalog}.{schema}.{table}"
    target = f"{target_catalog}.{schema}.{table}"

    # Deep clone (copy data + history)
    spark.sql(f"CREATE TABLE IF NOT EXISTS {target} DEEP CLONE {source}")
    print(f"✅ Promoted {source} → {target}")

# Usage
promote_table("staging", "prod", "sales", "customers")
```

### 3. Monitoring

**Set up alerts:**
```python
# In Databricks SQL
-- Create alert: "Daily ETL failures"
SELECT
  COUNT(*) as failed_runs
FROM system.compute.job_runs
WHERE
  run_date = CURRENT_DATE()
  AND state = 'FAILED'
  AND job_name LIKE 'prod-%'
HAVING failed_runs > 0;

-- Alert condition: failed_runs > 0
-- Notification: Send email to data-eng-alerts@example.com
```

**Track data quality:**
```python
# Add data quality checks
from pyspark.sql import functions as F

def check_data_quality(df, table_name):
    """Run data quality checks and log results."""
    checks = {
        "row_count": df.count(),
        "null_count": df.where(df.id.isNull()).count(),
        "duplicate_count": df.count() - df.dropDuplicates(["id"]).count()
    }

    # Log to Delta table
    quality_df = spark.createDataFrame([{
        "table_name": table_name,
        "check_timestamp": F.current_timestamp(),
        **checks
    }])

    quality_df.write.format("delta").mode("append").saveAsTable("monitoring.data_quality_checks")

    # Alert if issues
    if checks["null_count"] > 0:
        print(f"⚠️ WARNING: {checks['null_count']} NULL IDs in {table_name}")
```

---

## Monitoring & Debugging

### 1. Spark UI

**Access:**
- Cluster → Spark UI tab
- View: Jobs, Stages, Storage, Executors

**Key metrics:**
- Job duration (target: consistent times)
- Shuffle size (minimize for performance)
- Task skew (some tasks much slower than others

)
- GC time (>10% of task time is bad)

### 2. Query Profiling

```python
# Enable query profiling
df = spark.read.format("delta").load("/mnt/customers")
df = df.where("country = 'US'").groupBy("state").count()

# Run query
result = df.collect()

# View execution plan
df.explain(mode="extended")

# Execution plan shows:
# - Partition pruning applied
# - Data skipping stats
# - Join strategy (broadcast vs shuffle)
```

### 3. Common Issues

**Issue: Slow joins**
- **Cause:** Large shuffle
- **Fix:** Broadcast small table, partition by join key

**Issue: Out of memory**
- **Cause:** Too much data cached, skewed partitions
- **Fix:** Unpersist unused DataFrames, repartition skewed data

**Issue: Skewed data**
- **Cause:** Some keys have way more data than others
- **Fix:** Salt keys, use AQE skew join optimization

---

## Summary Checklist

### Development
- [ ] Use three-level namespace (dev/staging/prod)
- [ ] Parameterize notebooks with widgets
- [ ] Version control with Git Repos
- [ ] Modular, reusable functions
- [ ] Unit and integration tests

### Performance
- [ ] OPTIMIZE tables weekly
- [ ] VACUUM old versions monthly
- [ ] Partition by commonly-filtered columns
- [ ] Cache frequently-used small DataFrames
- [ ] Enable Adaptive Query Execution

### Cost
- [ ] Auto-terminate clusters (30 min)
- [ ] Use Jobs Compute for ETL
- [ ] Use Spot instances for fault-tolerant workloads
- [ ] Right-size clusters (start small)
- [ ] SQL Warehouse auto-stop enabled

### Security
- [ ] Unity Catalog permissions configured
- [ ] Secrets stored in secret scopes
- [ ] Row/column-level security applied
- [ ] Data lineage tracked
- [ ] Audit logs reviewed monthly

### Production
- [ ] CI/CD pipeline configured
- [ ] Automated tests pass
- [ ] Monitoring and alerts set up
- [ ] Data quality checks in place
- [ ] Runbooks for common issues

---

**Best Practices Version:** 1.0
**Last Updated:** March 2026
**Databricks Runtime:** 14.3 LTS
