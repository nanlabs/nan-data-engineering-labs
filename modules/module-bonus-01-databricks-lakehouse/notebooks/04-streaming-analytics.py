# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook 04: Streaming Analytics with Delta Lake
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC - Structured Streaming fundamentals
# MAGIC - Real-time data ingestion with Auto Loader
# MAGIC - Stream processing with Delta Lake
# MAGIC - Windowed aggregations
# MAGIC - Watermarking for late data
# MAGIC - Stream-to-batch joins
# MAGIC
# MAGIC ## Prerequisites
# MAGIC - Databricks Runtime 14.3 LTS or higher
# MAGIC - Understanding of Delta Lake basics
# MAGIC
# MAGIC ## Estimated Time: 60-75 minutes

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable
from datetime import datetime, timedelta
import time
import random

# Setup paths
database_name = "training_streaming"
stream_source_path = "/tmp/stream_source"
checkpoint_path = "/tmp/checkpoints"
bronze_path = "/tmp/streaming/bronze"
silver_path = "/tmp/streaming/silver"
gold_path = "/tmp/streaming/gold"

# Create database
spark.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
spark.sql(f"USE {database_name}")

print("✅ Streaming environment ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Structured Streaming Basics
# MAGIC
# MAGIC Structured Streaming treats stream as unbounded table:
# MAGIC - **Input**: Append-only DataFrame
# MAGIC - **Query**: Same transformations as batch
# MAGIC - **Output**: Incremental updates

# COMMAND ----------

# Generate streaming data source
print("Setting up streaming data generator...")

def generate_event_batch(batch_id, num_events=100):
    """Generate a batch of events."""
    base_time = datetime.now()
    events = []

    for i in range(num_events):
        event_time = (base_time - timedelta(seconds=random.randint(0, 300))).isoformat()
        events.append({
            "event_id": f"evt_{batch_id}_{i}",
            "user_id": random.randint(1, 1000),
            "session_id": f"sess_{random.randint(1, 100)}",
            "event_type": random.choice(["page_view", "click", "purchase", "search"]),
            "event_timestamp": event_time,
            "page_url": f"/page/{random.randint(1, 50)}",
            "revenue": round(random.uniform(10, 200), 2) if random.random() > 0.8 else None,
            "device_type": random.choice(["mobile", "desktop", "tablet"])
        })

    return events

# Create initial batch
initial_events = generate_event_batch(0, 1000)

# Write to source directory (simulating streaming source)
import json
dbutils.fs.mkdirs(stream_source_path)
dbutils.fs.put(
    f"{stream_source_path}/batch_0.json",
    "\n".join([json.dumps(e) for e in initial_events]),
    overwrite=True
)

print(f"✅ Initial batch written to {stream_source_path}")

# COMMAND ----------

# Define schema for streaming data
event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("user_id", IntegerType(), False),
    StructField("session_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("event_timestamp", StringType(), False),
    StructField("page_url", StringType(), False),
    StructField("revenue", DoubleType(), True),
    StructField("device_type", StringType(), False)
])

# Create streaming DataFrame
streaming_df = spark.readStream \
    .format("json") \
    .schema(event_schema) \
    .option("maxFilesPerTrigger", 1) \
    .load(stream_source_path)

print("✅ Streaming DataFrame created")
print("\nSchema:")
streaming_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Stream to Delta Lake (Bronze)

# COMMAND ----------

# Write stream to Delta Lake Bronze layer
print("Starting stream to Bronze...")

bronze_query = streaming_df \
    .withColumn("ingestion_time", current_timestamp()) \
    .withColumn("ingestion_date", current_date()) \
    .writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", f"{checkpoint_path}/bronze") \
    .trigger(processingTime="10 seconds") \
    .start(bronze_path)

print(f"✅ Stream started (ID: {bronze_query.id})")
print(f"   Status: {bronze_query.status}")
print("\nWaiting for initial data to arrive...")

# Wait for some data to be processed
time.sleep(15)

# Stop the stream for notebook flow
bronze_query.stop()
print("✅ Stream stopped (for demonstration)")

# COMMAND ----------

# Register Bronze table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS bronze_events
    USING DELTA
    LOCATION '{bronze_path}'
""")

# Check Bronze data
print("📊 Bronze Layer Statistics:")
bronze_count = spark.table("bronze_events").count()
print(f"   Total events: {bronze_count}")

display(spark.table("bronze_events").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: Stream Processing with Transformations

# COMMAND ----------

# Read stream from Bronze
bronze_stream = spark.readStream \
    .format("delta") \
    .load(bronze_path)

# Apply transformations
silver_stream = bronze_stream \
    .withColumn("event_timestamp", to_timestamp(col("event_timestamp"))) \
    .withColumn("event_date", to_date(col("event_timestamp"))) \
    .withColumn("event_hour", hour(col("event_timestamp"))) \
    .filter(col("event_timestamp").isNotNull()) \
    .dropDuplicates(["event_id"])

print("✅ Silver transformations defined")

# COMMAND ----------

# Write to Silver layer
silver_query = silver_stream \
    .writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", f"{checkpoint_path}/silver") \
    .trigger(processingTime="15 seconds") \
    .start(silver_path)

print(f"✅ Silver stream started (ID: {silver_query.id})")

# Wait and stop
time.sleep(20)
silver_query.stop()

# COMMAND ----------

# Register and query Silver
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS silver_events
    USING DELTA
    LOCATION '{silver_path}'
""")

print("📊 Silver Layer:")
display(spark.table("silver_events").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 4: Windowed Aggregations
# MAGIC
# MAGIC Window types:
# MAGIC - **Tumbling**: Fixed, non-overlapping (e.g., 5-minute buckets)
# MAGIC - **Sliding**: Overlapping (e.g., 5-minute window, slide every 1 minute)
# MAGIC - **Session**: Dynamic based on inactivity gap

# COMMAND ----------

# Tumbling window: 5-minute aggregations
print("Creating tumbling window aggregation...")

silver_stream_for_agg = spark.readStream \
    .format("delta") \
    .load(silver_path)

# Tumbling window aggregation
tumbling_agg = silver_stream_for_agg \
    .withWatermark("event_timestamp", "10 minutes") \
    .groupBy(
        window(col("event_timestamp"), "5 minutes"),
        col("event_type"),
        col("device_type")
    ) \
    .agg(
        count("*").alias("event_count"),
        countDistinct("user_id").alias("unique_users"),
        avg("revenue").alias("avg_revenue"),
        sum("revenue").alias("total_revenue")
    ) \
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("event_type"),
        col("device_type"),
        col("event_count"),
        col("unique_users"),
        round(col("avg_revenue"), 2).alias("avg_revenue"),
        round(col("total_revenue"), 2).alias("total_revenue")
    )

print("✅ Tumbling window defined")

# COMMAND ----------

# Write tumbling window results
tumbling_query = tumbling_agg \
    .writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", f"{checkpoint_path}/tumbling") \
    .trigger(processingTime="20 seconds") \
    .start(f"{gold_path}/tumbling_metrics")

print("✅ Tumbling window stream started")

time.sleep(25)
tumbling_query.stop()

# COMMAND ----------

# Query tumbling window results
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold_tumbling_metrics
    USING DELTA
    LOCATION '{gold_path}/tumbling_metrics'
""")

print("📊 Tumbling Window Results:")
display(
    spark.table("gold_tumbling_metrics")
    .orderBy("window_start", "event_type", "device_type")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 5: Watermarking for Late Data
# MAGIC
# MAGIC Watermark defines how long to wait for late data:
# MAGIC - Events arriving after watermark are dropped
# MAGIC - Balance between latency and completeness

# COMMAND ----------

# Demonstrate watermarking
print("Watermarking example...")

# With 10-minute watermark: events up to 10 minutes late are processed
watermarked_stream = spark.readStream \
    .format("delta") \
    .load(silver_path) \
    .withWatermark("event_timestamp", "10 minutes") \
    .groupBy(
        window(col("event_timestamp"), "1 minute"),
        col("event_type")
    ) \
    .agg(
        count("*").alias("event_count"),
        min("event_timestamp").alias("earliest_event"),
        max("event_timestamp").alias("latest_event")
    )

print("✅ Watermarked stream defined")
print("\nHow it works:")
print("- Current time: 12:00")
print("- Watermark: 10 minutes")
print("- Events before 11:50 will be dropped as late")
print("- Events between 11:50-12:00 will be processed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 6: MERGE with Streaming (Upserts)
# MAGIC
# MAGIC Delta Lake supports streaming MERGE for:
# MAGIC - Deduplication
# MAGIC - Change Data Capture (CDC)
# MAGIC - Slowly Changing Dimensions (SCD)

# COMMAND ----------

# Create target table for MERGE
print("Setting up MERGE target table...")

# Initial user profiles
initial_profiles = [
    (1, "Alice", "alice@email.com", 0, datetime.now()),
    (2, "Bob", "bob@email.com", 0, datetime.now()),
    (3, "Carol", "carol@email.com", 0, datetime.now())
]

profile_schema = StructType([
    StructField("user_id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("total_events", IntegerType(), False),
    StructField("last_updated", TimestampType(), False)
])

profiles_df = spark.createDataFrame(initial_profiles, profile_schema)
profiles_df.write.format("delta").mode("overwrite").save(f"{gold_path}/user_profiles")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold_user_profiles
    USING DELTA
    LOCATION '{gold_path}/user_profiles'
""")

print("✅ Initial user profiles created")
display(spark.table("gold_user_profiles"))

# COMMAND ----------

# Streaming MERGE function
def merge_user_updates(micro_batch_df, batch_id):
    """
    Merge streaming updates into user profiles.
    This function is called for each micro-batch.
    """
    # Aggregate updates from micro-batch
    updates = micro_batch_df \
        .groupBy("user_id") \
        .agg(
            count("*").alias("new_events")
        )

    # Load Delta table
    target_table = DeltaTable.forPath(spark, f"{gold_path}/user_profiles")

    # MERGE logic
    target_table.alias("target").merge(
        updates.alias("source"),
        "target.user_id = source.user_id"
    ).whenMatchedUpdate(set={
        "total_events": "target.total_events + source.new_events",
        "last_updated": "current_timestamp()"
    }).whenNotMatchedInsert(values={
        "user_id": "source.user_id",
        "name": "lit('Unknown')",
        "email": "lit('unknown@email.com')",
        "total_events": "source.new_events",
        "last_updated": "current_timestamp()"
    }).execute()

    print(f"   Batch {batch_id}: Merged {updates.count()} user updates")

# Apply streaming MERGE
merge_query = spark.readStream \
    .format("delta") \
    .load(silver_path) \
    .select("user_id", "event_id") \
    .writeStream \
    .foreachBatch(merge_user_updates) \
    .option("checkpointLocation", f"{checkpoint_path}/merge") \
    .trigger(processingTime="15 seconds") \
    .start()

print("✅ Streaming MERGE started")

time.sleep(20)
merge_query.stop()

# COMMAND ----------

# Check updated user profiles
print("📊 Updated User Profiles:")
display(
    spark.table("gold_user_profiles")
    .orderBy(col("total_events").desc())
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 7: Stream-to-Batch Joins
# MAGIC
# MAGIC Join streaming data with static reference tables.

# COMMAND ----------

# Create reference table (product catalog)
products_data = [
    (1, "Premium Widget", 99.99, "Electronics"),
    (2, "Standard Widget", 49.99, "Electronics"),
    (3, "Budget Widget", 19.99, "Electronics"),
    (4, "Deluxe Gadget", 149.99, "Appliances"),
    (5, "Basic Gadget", 29.99, "Appliances")
]

products_schema = StructType([
    StructField("product_id", IntegerType(), False),
    StructField("product_name", StringType(), False),
    StructField("price", DoubleType(), False),
    StructField("category", StringType(), False)
])

products_df = spark.createDataFrame(products_data, products_schema)
products_df.write.format("delta").mode("overwrite").saveAsTable("product_catalog")

print("✅ Product catalog created")

# COMMAND ----------

# Stream-to-batch join
print("Performing stream-to-batch join...")

# Modify silver stream to include product_id
enriched_stream = spark.readStream \
    .format("delta") \
    .load(silver_path) \
    .withColumn("product_id", (hash(col("event_id")) % 5 + 1).cast("int"))

# Join with static product catalog
joined_stream = enriched_stream \
    .join(
        spark.table("product_catalog"),
        "product_id",
        "left"
    ) \
    .select(
        "event_id",
        "user_id",
        "event_type",
        "event_timestamp",
        "product_id",
        "product_name",
        "price",
        "category"
    )

print("✅ Stream-to-batch join defined")

# COMMAND ----------

# Write enriched stream
enriched_query = joined_stream \
    .writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", f"{checkpoint_path}/enriched") \
    .trigger(processingTime="20 seconds") \
    .start(f"{gold_path}/enriched_events")

print("✅ Enriched stream started")

time.sleep(25)
enriched_query.stop()

# COMMAND ----------

# Query enriched events
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold_enriched_events
    USING DELTA
    LOCATION '{gold_path}/enriched_events'
""")

print("📊 Enriched Events:")
display(spark.table("gold_enriched_events").limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 8: Monitoring Streaming Queries

# COMMAND ----------

# Query monitoring metrics
print("📊 Streaming Query Metrics:\n")

# Create a monitoring query
monitoring_stream = spark.readStream \
    .format("delta") \
    .load(silver_path)

# Start query with metrics
metrics_query = monitoring_stream \
    .writeStream \
    .format("memory") \
    .queryName("metrics_demo") \
    .outputMode("append") \
    .trigger(processingTime="10 seconds") \
    .start()

time.sleep(15)

# Get query status
status = metrics_query.status
print(f"Query ID: {status['id']}")
print(f"Status: {status['message']}")
print(f"Is Data Available: {status['isDataAvailable']}")
print(f"Is Trigger Active: {status['isTriggerActive']}")

# Get recent progress
recent_progress = metrics_query.recentProgress
if recent_progress:
    latest = recent_progress[-1]
    print("\nLatest Progress:")
    print(f"  Batch ID: {latest['batchId']}")
    print(f"  Num Input Rows: {latest['numInputRows']}")
    print(f"  Input Rows/Sec: {latest['inputRowsPerSecond']}")
    print(f"  Process Rows/Sec: {latest['processedRowsPerSecond']}")

metrics_query.stop()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 9: Production Streaming Pattern

# COMMAND ----------

# Production-ready streaming function
def start_production_stream(source_path, target_path, checkpoint_path, trigger_interval="1 minute"):
    """
    Production streaming pattern with error handling and monitoring.
    """
    print("🚀 Starting production stream...")
    print(f"   Source: {source_path}")
    print(f"   Target: {target_path}")
    print(f"   Checkpoint: {checkpoint_path}")

    try:
        query = spark.readStream \
            .format("delta") \
            .load(source_path) \
            .writeStream \
            .format("delta") \
            .outputMode("append") \
            .option("checkpointLocation", checkpoint_path) \
            .trigger(processingTime=trigger_interval) \
            .option("maxFilesPerTrigger", 1000) \
            .option("optimizeWrite", "true") \
            .option("autoCompact", "true") \
            .start(target_path)

        print(f"✅ Stream started successfully (ID: {query.id})")

        return query

    except Exception as e:
        print(f"❌ Stream failed to start: {e}")
        # In production: Send alert, log to monitoring
        raise

# Example usage (commented out for notebook)
# prod_query = start_production_stream(
#     source_path=silver_path,
#     target_path=f"{gold_path}/production_stream",
#     checkpoint_path=f"{checkpoint_path}/production"
# )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Key Takeaways
# MAGIC
# MAGIC ✅ **Structured Streaming**
# MAGIC - Treat streams as unbounded tables
# MAGIC - Same DataFrame API as batch
# MAGIC - Exactly-once processing guarantees
# MAGIC
# MAGIC ✅ **Delta Lake Integration**
# MAGIC - Append streams to Delta tables
# MAGIC - Streaming MERGE for upserts
# MAGIC - Read streams from Delta tables
# MAGIC
# MAGIC ✅ **Windowed Aggregations**
# MAGIC - Tumbling windows (fixed intervals)
# MAGIC - Sliding windows (overlapping)
# MAGIC - Watermarking for late data handling
# MAGIC
# MAGIC ✅ **Advanced Patterns**
# MAGIC - Stream-to-batch joins
# MAGIC - Deduplication
# MAGIC - Change Data Capture (CDC)
# MAGIC
# MAGIC ✅ **Production Best Practices**
# MAGIC - Checkpoint locations for fault tolerance
# MAGIC - Trigger intervals for cost control
# MAGIC - Monitoring with query metrics
# MAGIC - Auto-compaction for performance
# MAGIC
# MAGIC ## Next Steps
# MAGIC
# MAGIC Continue to Notebook 05: **SQL Analytics & Dashboards**

# COMMAND ----------

# Cleanup (optional)
# spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE")
# dbutils.fs.rm(stream_source_path, recurse=True)
# dbutils.fs.rm(checkpoint_path, recurse=True)
# dbutils.fs.rm(bronze_path, recurse=True)
# dbutils.fs.rm(silver_path, recurse=True)
# dbutils.fs.rm(gold_path, recurse=True)
# print("✅ Cleanup complete")
