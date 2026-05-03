# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook 02: ETL Pipeline with Medallion Architecture
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC By the end of this notebook, you will understand:
# MAGIC - Medallion Architecture (Bronze → Silver → Gold)
# MAGIC - Production ETL patterns
# MAGIC - Incremental processing
# MAGIC - Data quality checks
# MAGIC - Error handling strategies
# MAGIC
# MAGIC ## Architecture Overview
# MAGIC
# MAGIC ```
# MAGIC Bronze (Raw)           Silver (Cleaned)         Gold (Aggregated)
# MAGIC ┌──────────┐          ┌───────────┐            ┌──────────┐
# MAGIC │  JSON    │──────▶   │ Validated │───────▶    │ Business │
# MAGIC │  CSV     │  Ingest  │ Cleaned   │  Transform │ Metrics  │
# MAGIC │  Parquet │          │ Deduped   │            │ Reports  │
# MAGIC └──────────┘          └───────────┘            └──────────┘
# MAGIC ```
# MAGIC
# MAGIC ## Estimated Time: 60-75 minutes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from delta.tables import DeltaTable
from datetime import datetime, timedelta
import json

# Database and paths
database_name = "training_medallion"
bronze_path = f"/tmp/{database_name}/bronze"
silver_path = f"/tmp/{database_name}/silver"
gold_path = f"/tmp/{database_name}/gold"
checkpoint_path = f"/tmp/{database_name}/checkpoints"

# Create database
spark.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
spark.sql(f"USE {database_name}")

print("✅ Environment ready")
print(f"   Database: {database_name}")
print(f"   Bronze: {bronze_path}")
print(f"   Silver: {silver_path}")
print(f"   Gold: {gold_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Bronze Layer - Raw Data Ingestion
# MAGIC
# MAGIC The Bronze layer stores raw data exactly as received:
# MAGIC - Append-only (immutable)
# MAGIC - Minimal transformations
# MAGIC - Add audit columns (ingestion timestamp, source file)
# MAGIC - Preserve all data for reprocessing

# COMMAND ----------

# Generate sample raw event data (simulating streaming source)
print("Generating sample raw events...")

def generate_raw_events(num_events=1000):
    """Simulate raw event data from web application."""
    events = []
    base_time = datetime.now() - timedelta(hours=24)

    event_types = ["page_view", "add_to_cart", "purchase", "search", "logout"]
    pages = ["/home", "/products", "/cart", "/checkout", "/account"]
    devices = ["desktop", "mobile", "tablet"]

    for i in range(num_events):
        event_time = base_time + timedelta(seconds=i * 86)  # ~86 seconds apart

        # Introduce some data quality issues intentionally
        user_id = None if i % 100 == 0 else i % 500 + 1  # Some missing user_ids
        event_type = event_types[i % len(event_types)]

        event = {
            "event_id": f"evt_{i}",
            "user_id": user_id,
            "session_id": f"sess_{i // 10}",  # 10 events per session
            "event_type": event_type,
            "event_timestamp": event_time.isoformat(),
            "page_url": pages[i % len(pages)],
            "device_type": devices[i % len(devices)],
            "revenue": round((i % 100) * 1.5, 2) if event_type == "purchase" else None,
            # Data quality issues:
            "country": None if i % 50 == 0 else ["USA", "UK", "CA"][i % 3],  # Some missing
            "duplicate_marker": i % 20  # Will create duplicates
        }
        events.append(event)

    return events

raw_events = generate_raw_events(1000)
print(f"✅ Generated {len(raw_events)} raw events")

# Convert to JSON strings (simulating raw ingestion)
raw_json = [json.dumps(event) for event in raw_events]

# COMMAND ----------

# Ingest to Bronze layer
print("Ingesting to Bronze layer...")

# Create DataFrame from raw JSON
schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("user_id", IntegerType(), True),
    StructField("session_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("event_timestamp", StringType(), True),
    StructField("page_url", StringType(), True),
    StructField("device_type", StringType(), True),
    StructField("revenue", DoubleType(), True),
    StructField("country", StringType(), True),
    StructField("duplicate_marker", IntegerType(), True)
])

raw_df = spark.read.json(spark.sparkContext.parallelize(raw_json), schema=schema)

# Add audit columns
bronze_df = raw_df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_file", lit("api_stream_001")) \
    .withColumn("_bronze_created_at", current_timestamp())

# Write to Bronze (append-only)
bronze_df.write \
    .format("delta") \
    .mode("append") \
    .save(f"{bronze_path}/events")

# Register table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS bronze_events
    USING DELTA
    LOCATION '{bronze_path}/events'
""")

print(f"✅ Bronze layer: {bronze_df.count()} records ingested")

# COMMAND ----------

# Inspect Bronze data
print("📊 Bronze Layer Sample:")
display(spark.table("bronze_events").limit(10))

# Check data quality issues
print("\n⚠️  Data Quality Issues in Bronze:")
bronze_quality = spark.sql("""
    SELECT
        COUNT(*) as total_records,
        SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as missing_user_id,
        SUM(CASE WHEN country IS NULL THEN 1 ELSE 0 END) as missing_country,
        COUNT(DISTINCT duplicate_marker) as unique_groups,
        COUNT(*) - COUNT(DISTINCT event_id) as potential_duplicates
    FROM bronze_events
""")
display(bronze_quality)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Silver Layer - Cleaned & Validated Data
# MAGIC
# MAGIC The Silver layer applies:
# MAGIC - Data validation and filtering
# MAGIC - Deduplication
# MAGIC - Data type conversions
# MAGIC - Standardization (e.g., lowercase country codes)
# MAGIC - Business rules
# MAGIC - **Idempotent**: Can reprocess safely

# COMMAND ----------

print("Processing Bronze → Silver...")

# Read from Bronze
bronze_events_df = spark.table("bronze_events")

# Silver transformations
silver_df = bronze_events_df \
    .filter(col("user_id").isNotNull()) \
    .filter(col("event_id").isNotNull()) \
    .withColumn("event_timestamp", to_timestamp(col("event_timestamp"))) \
    .withColumn("event_date", to_date(col("event_timestamp"))) \
    .withColumn("country", coalesce(col("country"), lit("UNKNOWN"))) \
    .withColumn("country", upper(col("country"))) \
    .withColumn("page_url", lower(trim(col("page_url")))) \
    .withColumn("device_type", lower(col("device_type"))) \
    .withColumn("_silver_created_at", current_timestamp())

# Deduplication: Keep most recent event for each event_id
window_spec = Window.partitionBy("event_id").orderBy(col("ingestion_timestamp").desc())

silver_deduped_df = silver_df \
    .withColumn("_row_num", row_number().over(window_spec)) \
    .filter(col("_row_num") == 1) \
    .drop("_row_num", "duplicate_marker")

# Data quality checks
print("\n🔍 Silver Data Quality Checks:")
quality_checks = {
    "total_records": silver_deduped_df.count(),
    "unique_events": silver_deduped_df.select("event_id").distinct().count(),
    "null_user_ids": silver_deduped_df.filter(col("user_id").isNull()).count(),
    "null_countries": silver_deduped_df.filter(col("country") == "UNKNOWN").count(),
    "future_dates": silver_deduped_df.filter(col("event_timestamp") > current_timestamp()).count()
}

for check, value in quality_checks.items():
    status = "✅" if value == 0 or check in ["total_records", "unique_events"] else "⚠️"
    print(f"  {status} {check}: {value}")

# COMMAND ----------

# Write to Silver layer
silver_deduped_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{silver_path}/events")

# Register table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS silver_events
    USING DELTA
    LOCATION '{silver_path}/events'
""")

print("✅ Silver layer complete")

# COMMAND ----------

# Compare Bronze vs Silver
print("📊 Bronze vs Silver Comparison:")
comparison = spark.sql("""
    SELECT
        'Bronze' as layer,
        COUNT(*) as record_count,
        COUNT(DISTINCT event_id) as unique_events,
        SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as null_user_ids
    FROM bronze_events

    UNION ALL

    SELECT
        'Silver' as layer,
        COUNT(*) as record_count,
        COUNT(DISTINCT event_id) as unique_events,
        SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as null_user_ids
    FROM silver_events
""")
display(comparison)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: Gold Layer - Business Aggregations
# MAGIC
# MAGIC The Gold layer contains:
# MAGIC - Aggregated metrics
# MAGIC - Denormalized tables for analytics
# MAGIC - Business KPIs
# MAGIC - Optimized for query performance
# MAGIC - Often in star schema or data mart structure

# COMMAND ----------

# Gold Aggregation 1: Daily Active Users (DAU)
print("Creating Gold table: Daily Active Users...")

gold_dau_df = spark.sql("""
    SELECT
        event_date,
        COUNT(DISTINCT user_id) as active_users,
        COUNT(*) as total_events,
        COUNT(DISTINCT session_id) as total_sessions,
        ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT user_id), 2) as avg_events_per_user,
        ROUND(COUNT(DISTINCT session_id) * 1.0 / COUNT(DISTINCT user_id), 2) as avg_sessions_per_user,
        current_timestamp() as _gold_created_at
    FROM silver_events
    GROUP BY event_date
    ORDER BY event_date
""")

gold_dau_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save(f"{gold_path}/daily_active_users")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold_daily_active_users
    USING DELTA
    LOCATION '{gold_path}/daily_active_users'
""")

print("✅ Gold: daily_active_users created")
display(spark.table("gold_daily_active_users"))

# COMMAND ----------

# Gold Aggregation 2: Event Funnel Analysis
print("Creating Gold table: Event Funnel...")

gold_funnel_df = spark.sql("""
    SELECT
        event_date,
        device_type,
        SUM(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) as page_views,
        SUM(CASE WHEN event_type = 'search' THEN 1 ELSE 0 END) as searches,
        SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as add_to_carts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchases,
        -- Conversion rates
        ROUND(
            SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(SUM(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END), 0),
            2
        ) as view_to_cart_rate,
        ROUND(
            SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END), 0),
            2
        ) as cart_to_purchase_rate,
        current_timestamp() as _gold_created_at
    FROM silver_events
    GROUP BY event_date, device_type
    ORDER BY event_date, device_type
""")

gold_funnel_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save(f"{gold_path}/event_funnel")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold_event_funnel
    USING DELTA
    LOCATION '{gold_path}/event_funnel'
""")

print("✅ Gold: event_funnel created")
display(spark.table("gold_event_funnel"))

# COMMAND ----------

# Gold Aggregation 3: Revenue Summary
print("Creating Gold table: Revenue Summary...")

gold_revenue_df = spark.sql("""
    SELECT
        event_date,
        country,
        device_type,
        COUNT(DISTINCT user_id) as unique_customers,
        SUM(revenue) as total_revenue,
        AVG(revenue) as avg_revenue_per_transaction,
        COUNT(*) as purchase_count,
        current_timestamp() as _gold_created_at
    FROM silver_events
    WHERE event_type = 'purchase' AND revenue IS NOT NULL
    GROUP BY event_date, country, device_type
    ORDER BY event_date DESC, total_revenue DESC
""")

gold_revenue_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save(f"{gold_path}/revenue_summary")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold_revenue_summary
    USING DELTA
    LOCATION '{gold_path}/revenue_summary'
""")

print("✅ Gold: revenue_summary created")
display(spark.table("gold_revenue_summary"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 4: Incremental Processing
# MAGIC
# MAGIC Production ETL should be incremental:
# MAGIC - Process only new data
# MAGIC - Use watermarks for late-arriving data
# MAGIC - Maintain processing state

# COMMAND ----------

# Simulate incremental processing with watermark
print("Demonstrating incremental processing...")

# Get last processed timestamp from Silver
last_processed = spark.sql("""
    SELECT MAX(ingestion_timestamp) as max_time
    FROM silver_events
""").first()["max_time"]

print(f"Last processed timestamp: {last_processed}")

# Simulate new batch of events arriving
new_raw_events = generate_raw_events(100)  # New batch
new_raw_json = [json.dumps(event) for event in new_raw_events]
new_raw_df = spark.read.json(spark.sparkContext.parallelize(new_raw_json), schema=schema)

# Add to Bronze
new_bronze_df = new_raw_df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_file", lit("api_stream_002")) \
    .withColumn("_bronze_created_at", current_timestamp())

new_bronze_df.write \
    .format("delta") \
    .mode("append") \
    .save(f"{bronze_path}/events")

print(f"✅ Added {new_bronze_df.count()} new events to Bronze")

# COMMAND ----------

# Incremental Silver processing
print("Processing incremental data to Silver...")

# Only process new records
incremental_bronze = spark.sql(f"""
    SELECT *
    FROM bronze_events
    WHERE ingestion_timestamp > '{last_processed}'
""")

print(f"Incremental records to process: {incremental_bronze.count()}")

# Apply same Silver transformations
incremental_silver = incremental_bronze \
    .filter(col("user_id").isNotNull()) \
    .filter(col("event_id").isNotNull()) \
    .withColumn("event_timestamp", to_timestamp(col("event_timestamp"))) \
    .withColumn("event_date", to_date(col("event_timestamp"))) \
    .withColumn("country", coalesce(col("country"), lit("UNKNOWN"))) \
    .withColumn("country", upper(col("country"))) \
    .withColumn("page_url", lower(trim(col("page_url")))) \
    .withColumn("device_type", lower(col("device_type"))) \
    .withColumn("_silver_created_at", current_timestamp())

# Merge into Silver (UPSERT)
silver_table = DeltaTable.forPath(spark, f"{silver_path}/events")

silver_table.alias("target").merge(
    incremental_silver.alias("source"),
    "target.event_id = source.event_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

print("✅ Incremental Silver processing complete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 5: Error Handling & Data Quality
# MAGIC
# MAGIC Production pipelines need robust error handling:
# MAGIC - Quarantine bad records
# MAGIC - Data quality metrics
# MAGIC - Alerting thresholds

# COMMAND ----------

# Create data quality check framework
print("Running data quality checks...")

# Define quality rules
quality_rules = [
    {
        "rule_name": "user_id_not_null",
        "condition": "user_id IS NOT NULL",
        "severity": "critical"
    },
    {
        "rule_name": "event_timestamp_valid",
        "condition": "event_timestamp IS NOT NULL AND event_timestamp <= current_timestamp()",
        "severity": "critical"
    },
    {
        "rule_name": "revenue_positive",
        "condition": "revenue IS NULL OR revenue >= 0",
        "severity": "warning"
    },
    {
        "rule_name": "known_country",
        "condition": "country != 'UNKNOWN'",
        "severity": "warning"
    }
]

# Check quality
quality_results = []
silver_df_check = spark.table("silver_events")
total_records = silver_df_check.count()

for rule in quality_rules:
    passed = silver_df_check.filter(rule["condition"]).count()
    failed = total_records - passed
    pass_rate = round(passed * 100.0 / total_records, 2)

    quality_results.append({
        "rule_name": rule["rule_name"],
        "severity": rule["severity"],
        "total_records": total_records,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "status": "✅ PASS" if pass_rate >= 95 else "⚠️ WARNING" if pass_rate >= 80 else "❌ FAIL"
    })

# Display results
quality_df = spark.createDataFrame(quality_results)
display(quality_df)

# COMMAND ----------

# Quarantine bad records
print("Quarantining failed records...")

quarantine_df = spark.table("silver_events") \
    .filter(col("user_id").isNull() | (col("event_timestamp") > current_timestamp()))

quarantine_count = quarantine_df.count()
print(f"Records in quarantine: {quarantine_count}")

if quarantine_count > 0:
    quarantine_df.write \
        .format("delta") \
        .mode("append") \
        .save(f"{silver_path}/quarantine")

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS silver_quarantine
        USING DELTA
        LOCATION '{silver_path}/quarantine'
    """)

    print("✅ Quarantine table created")
    display(quarantine_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 6: Pipeline Orchestration Pattern
# MAGIC
# MAGIC Production pipelines follow this pattern:

# COMMAND ----------

def run_etl_pipeline(incremental=True):
    """
    Production ETL pipeline function.

    Can be called from Databricks Workflows or scheduled jobs.
    """
    pipeline_start = datetime.now()
    print(f"🚀 Pipeline started at {pipeline_start}")

    try:
        # Step 1: Bronze ingestion
        print("\n[1/4] Bronze ingestion...")
        # Code would read from actual source (S3, Kafka, API)
        bronze_count = spark.table("bronze_events").count()
        print(f"   Bronze records: {bronze_count}")

        # Step 2: Silver transformation
        print("\n[2/4] Silver transformation...")
        # Incremental processing logic
        silver_count = spark.table("silver_events").count()
        print(f"   Silver records: {silver_count}")

        # Step 3: Data quality checks
        print("\n[3/4] Data quality validation...")
        # Run quality checks
        print("   Quality checks passed")

        # Step 4: Gold aggregations
        print("\n[4/4] Gold aggregations...")
        gold_count = spark.table("gold_daily_active_users").count()
        print(f"   Gold records: {gold_count}")

        pipeline_end = datetime.now()
        duration = (pipeline_end - pipeline_start).total_seconds()

        print(f"\n✅ Pipeline completed successfully in {duration:.2f} seconds")

        return {
            "status": "success",
            "duration_seconds": duration,
            "bronze_count": bronze_count,
            "silver_count": silver_count,
            "gold_count": gold_count
        }

    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        # In production: Send alert, log to monitoring system
        return {
            "status": "failed",
            "error": str(e)
        }

# Run the pipeline
pipeline_result = run_etl_pipeline()
print(f"\nPipeline Result: {pipeline_result}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Key Takeaways
# MAGIC
# MAGIC ✅ **Medallion Architecture**
# MAGIC - **Bronze**: Raw, immutable, append-only
# MAGIC - **Silver**: Cleaned, validated, deduplicated
# MAGIC - **Gold**: Aggregated, business-ready metrics
# MAGIC
# MAGIC ✅ **Production Patterns**
# MAGIC - Incremental processing with watermarks
# MAGIC - MERGE for idempotent updates
# MAGIC - Data quality checks with quarantine
# MAGIC - Error handling and monitoring
# MAGIC
# MAGIC ✅ **Best Practices**
# MAGIC - Add audit columns (timestamps, source)
# MAGIC - Maintain data lineage
# MAGIC - Design for reprocessing
# MAGIC - Separate concerns by layer
# MAGIC
# MAGIC ## Next Steps
# MAGIC
# MAGIC Continue to Notebook 03: **Unity Catalog Governance**

# COMMAND ----------

# Cleanup (optional)
# spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE")
# dbutils.fs.rm(bronze_path, recurse=True)
# dbutils.fs.rm(silver_path, recurse=True)
# dbutils.fs.rm(gold_path, recurse=True)
# print("✅ Cleanup complete")
