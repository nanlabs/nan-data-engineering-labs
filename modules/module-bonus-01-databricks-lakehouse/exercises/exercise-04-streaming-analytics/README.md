# Exercise 04: Real-Time Streaming Analytics

## Overview
Build a production-grade real-time streaming pipeline using Structured Streaming to process events from Bronze to Gold layers with windowed aggregations, late data handling, and streaming UPSERT operations.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Exercise 02 (ETL Pipelines), Module 08 (Streaming basics)

---

## Learning Objectives
By completing this exercise, you will be able to:
- Build streaming pipelines with Structured Streaming
- Process continuous data from readStream to writeStream
- Implement windowed aggregations (tumbling, sliding, session windows)
- Handle late-arriving data with watermarks
- Perform streaming MERGE operations with foreachBatch
- Monitor streaming query health and performance
- Implement exactly-once processing with checkpointing

---

## Scenario
You're building a real-time analytics platform for a ride-sharing service. Events stream continuously from mobile apps:
- Ride requests (user requests a ride)
- Driver acceptance (driver accepts request)
- Ride start (trip begins)
- Ride complete (trip ends with payment)

Requirements:
1. Ingest streaming events into Bronze layer
2. Clean and enrich in Silver layer (real-time)
3. Calculate 5-minute windowed metrics (active rides, requests per region)
4. Handle events arriving up to 10 minutes late
5. Maintain real-time user profiles with streaming MERGE
6. Monitor throughput, latency, and backlog

**Data Rate**: 100-500 events/second, 24/7 continuous stream

---

## Requirements

### Task 1: Stream to Bronze (20 min)
Set up streaming ingestion from source to Bronze Delta table.

**Requirements**:
- Create `bronze_ride_events` Delta table (streaming write)
- Read from JSON event source (simulated with rate source + transformations)
- Configure checkpointing for fault tolerance
- Append-only writes (no updates)

**Event Schema**:
```
event_id: STRING
event_type: STRING (ride_request, driver_accept, ride_start, ride_complete)
timestamp: TIMESTAMP
user_id: STRING
driver_id: STRING (null for ride_request)
ride_id: STRING
latitude: DOUBLE
longitude: DOUBLE
city: STRING
fare: DOUBLE (null until ride_complete)
distance_km: DOUBLE (null until ride_complete)
```

**Streaming Configuration**:
```python
# Read stream
stream_df = spark.readStream \
    .format("json") \
    .schema(event_schema) \
    .option("maxFilesPerTrigger", 10) \
    .load("/path/to/events")

# Write stream to Bronze
query = stream_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/checkpoints/bronze") \
    .trigger(processingTime="10 seconds") \
    .table("bronze_ride_events")
```

**Data Generation**:
- Simulate 500 events/second using `spark.readStream.format("rate")`
- Transform rate source into realistic ride events
- Include some late-arriving events (5-10% arrive 2-8 minutes late)

**Success Criteria**:
- ✅ Streaming query running continuously
- ✅ Bronze table receiving 500+ events/second
- ✅ Checkpoint directory created with metadata
- ✅ Can restart query and resume from checkpoint
- ✅ No data loss on failure (exactly-once semantics)

---

### Task 2: Stream Transformations (Bronze → Silver) (25 min)
Apply real-time cleaning and enrichment transformations.

**Requirements**:
- Create `silver_ride_events` streaming table
- Clean data (filter nulls, parse timestamps, validate coordinates)
- Enrich with computed columns:
  - `processing_latency_seconds` (current_timestamp - event_timestamp)
  - `is_late_event` (latency > 60 seconds)
  - `event_date` (date from timestamp)
  - `event_hour` (hour from timestamp)
- Deduplicate by event_id (use dropDuplicatesWithWatermark)

**Deduplication**:
```python
silver_stream = bronze_stream \
    .withWatermark("timestamp", "10 minutes") \
    .dropDuplicates(["event_id", "timestamp"])
```

**Data Quality**:
- Filter out events with:
  - NULL user_id or ride_id
  - Invalid coordinates (lat/lon outside reasonable bounds)
  - Future timestamps (timestamp > current_time + 5 minutes)

**Quarantine Stream**:
- Write filtered-out records to `silver_ride_events_quarantine`
- Include rejection reason

**Success Criteria**:
- ✅ Silver stream processes 450+ events/second (after filtering)
- ✅ Duplicates removed (test by sending duplicate event_id)
- ✅ Quarantine stream captures ~5-10% of bronze events
- ✅ Processing latency < 5 seconds average
- ✅ Enrichment columns populated correctly

---

### Task 3: Windowed Aggregations (30 min)
Calculate real-time metrics using tumbling windows.

**Requirements**:
Create three streaming aggregation tables with 5-minute tumbling windows:

**1. Active Rides Dashboard** (`gold_active_rides_5min`):
```
window_start: TIMESTAMP
window_end: TIMESTAMP
city: STRING
active_requests: LONG (ride_request events)
active_trips: LONG (ride_start - ride_complete events)
drivers_active: LONG (distinct drivers)
avg_wait_time_seconds: DOUBLE (request to accept)
```

**2. City Demand Heatmap** (`gold_city_demand_5min`):
```
window_start: TIMESTAMP
window_end: TIMESTAMP
city: STRING
latitude_bucket: STRING (rounded to 2 decimals)
longitude_bucket: STRING (rounded to 2 decimals)
ride_requests: LONG
avg_fare: DOUBLE
```

**3. Event Funnel Metrics** (`gold_event_funnel_5min`):
```
window_start: TIMESTAMP
window_end: TIMESTAMP
total_requests: LONG
total_accepts: LONG
total_starts: LONG
total_completes: LONG
acceptance_rate: DOUBLE (accepts / requests)
completion_rate: DOUBLE (completes / requests)
```

**Window Syntax**:
```python
from pyspark.sql.functions import window, col

windowed_df = silver_stream \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(
        window(col("timestamp"), "5 minutes"),
        col("city")
    ) \
    .agg(
        count("*").alias("total_events"),
        countDistinct("ride_id").alias("unique_rides")
    )
```

**Output Mode**:
- Use `outputMode("append")` for tumbling windows
- Use `outputMode("update")` for sliding windows (if needed)

**Success Criteria**:
- ✅ All 3 Gold tables updating every 5 minutes
- ✅ Window boundaries aligned to clock (00:00, 00:05, 00:10, etc.)
- ✅ Aggregations mathematically correct
- ✅ Acceptance rate between 0.7-0.95 (realistic)
- ✅ No duplicate windows (each 5-minute period appears once)

---

### Task 4: Watermarking for Late Data (20 min)
Handle late-arriving events with watermarking.

**Requirements**:
- Configure 10-minute watermark (events up to 10 min late are processed)
- Events older than watermark are dropped
- Test with intentionally delayed events

**Watermark Configuration**:
```python
stream_with_watermark = silver_stream \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(window("timestamp", "5 minutes"), "city") \
    .count()
```

**Testing Scenarios**:
1. **On-time event**: timestamp = current_time - 2 minutes → **Processed**
2. **Late event (within watermark)**: timestamp = current_time - 8 minutes → **Processed**
3. **Very late event (exceeds watermark)**: timestamp = current_time - 15 minutes → **Dropped**

**Monitoring Late Events**:
- Track percentage of late events (latency > 1 minute)
- Alert if late event rate > 10%
- Log dropped events for analysis

**Watermark Tracking**:
```python
# Get current watermark from query
query = stream_with_watermark.writeStream...
progress = query.lastProgress

print(f"Current watermark: {progress['eventTime']['watermark']}")
print(f"Latest event time: {progress['eventTime']['max']}")
print(f"Lag: {progress['eventTime']['lag']}")
```

**Success Criteria**:
- ✅ Watermark advances over time (check every 1 minute)
- ✅ Late events within 10 minutes are processed
- ✅ Events older than watermark are dropped
- ✅ No unbounded state growth
- ✅ Late event metrics tracked

---

### Task 5: Streaming MERGE (foreachBatch UPSERT) (25 min)
Maintain real-time user profiles with streaming MERGE.

**Requirements**:
- Create `gold_user_profiles` table (updated in real-time)
- UPSERT profile on each ride completion
- Track lifetime stats per user

**User Profile Schema**:
```
user_id: STRING (primary key)
first_ride_date: DATE
last_ride_date: DATE
total_rides: INT
total_spent: DOUBLE
total_distance_km: DOUBLE
avg_fare: DOUBLE
favorite_city: STRING (city with most rides)
last_updated: TIMESTAMP
```

**Streaming MERGE with foreachBatch**:
```python
from delta.tables import DeltaTable

def upsert_profiles(batch_df, batch_id):
    # Calculate aggregations from batch
    profiles_update = batch_df \
        .filter(col("event_type") == "ride_complete") \
        .groupBy("user_id") \
        .agg(
            min("event_date").alias("first_ride_date"),
            max("event_date").alias("last_ride_date"),
            count("*").alias("rides_in_batch"),
            sum("fare").alias("amount_in_batch")
        )

    # MERGE into profiles table
    target = DeltaTable.forName(spark, "gold_user_profiles")

    target.alias("target").merge(
        profiles_update.alias("source"),
        "target.user_id = source.user_id"
    ).whenMatchedUpdate(set={
        "total_rides": "target.total_rides + source.rides_in_batch",
        "total_spent": "target.total_spent + source.amount_in_batch",
        "last_ride_date": "source.last_ride_date",
        "last_updated": "current_timestamp()"
    }).whenNotMatchedInsert(values={
        "user_id": "source.user_id",
        "first_ride_date": "source.first_ride_date",
        "last_ride_date": "source.last_ride_date",
        "total_rides": "source.rides_in_batch",
        "total_spent": "source.amount_in_batch",
        "last_updated": "current_timestamp()"
    }).execute()

# Apply to stream
silver_stream.writeStream \
    .foreachBatch(upsert_profiles) \
    .option("checkpointLocation", "/checkpoints/profiles") \
    .start()
```

**Idempotency**:
- Running same batch_id twice should not duplicate counts
- Use merge semantics (not append)

**Success Criteria**:
- ✅ User profiles table exists and updates in real-time
- ✅ New users inserted, existing users updated
- ✅ Aggregations correct (total_rides, total_spent)
- ✅ Idempotent (can replay batches safely)
- ✅ Processing latency < 10 seconds

---

### Task 6: Monitoring Streaming Queries (20 min)
Monitor streaming pipeline health, performance, and SLAs.

**Requirements**:
Track these metrics for each streaming query:

**1. Throughput Metrics**:
- Input rows per second
- Processed rows per second
- Trigger durations

**2. Latency Metrics**:
- End-to-end latency (event time to processing time)
- Batch processing time
- Watermark lag

**3. Health Metrics**:
- Query status (active/stopped/failed)
- Number of active queries
- Checkpoint health

**Monitoring Queries**:
```python
# Get all active streams
active_streams = [s for s in spark.streams.active]
print(f"Active streaming queries: {len(active_streams)}")

# Monitor specific query
query = active_streams[0]
status = query.status
progress = query.recentProgress[-1]  # Last trigger

print(f"Query ID: {query.id}")
print(f"Status: {status['message']}")
print(f"Input rate: {progress['inputRowsPerSecond']:.2f} rows/sec")
print(f"Process rate: {progress['processedRowsPerSecond']:.2f} rows/sec")
print(f"Batch duration: {progress['batchDuration']} ms")
print(f"Trigger: {progress['timestamp']}")
```

**Create Monitoring Dashboard**:
```sql
-- Create metrics table
CREATE TABLE IF NOT EXISTS streaming_metrics (
  query_id STRING,
  query_name STRING,
  metric_timestamp TIMESTAMP,
  input_rate DOUBLE,
  process_rate DOUBLE,
  batch_duration_ms LONG,
  num_input_rows LONG,
  watermark TIMESTAMP
);

-- Dashboard query: Last hour performance
SELECT
  query_name,
  date_trunc('minute', metric_timestamp) as minute,
  avg(input_rate) as avg_input_rate,
  avg(process_rate) as avg_process_rate,
  max(batch_duration_ms) as max_batch_duration
FROM streaming_metrics
WHERE metric_timestamp >= current_timestamp() - interval 1 hour
GROUP BY query_name, minute
ORDER BY minute DESC;
```

**SLA Alerts**:
- Processing lag > 5 minutes → Alert
- Input rate > process rate for 10+ minutes → Alert (backlog building)
- Batch duration > 60 seconds → Alert (slow processing)
- Query failed or stopped → Critical alert

**Success Criteria**:
- ✅ All streams monitored (5+ queries tracked)
- ✅ Metrics collected every minute
- ✅ Dashboard queries working
- ✅ SLA alerts configured
- ✅ Can diagnose performance bottlenecks

---

## Hints

<details>
<summary>Hint 1: Setting Up Stream Sources</summary>

```python
from pyspark.sql.types import *
from pyspark.sql.functions import *

# Schema definition
event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("user_id", StringType(), False),
    StructField("ride_id", StringType(), False),
    StructField("city", StringType(), True),
    StructField("fare", DoubleType(), True)
])

# Simulate streaming source with rate
rate_stream = spark.readStream \
    .format("rate") \
    .option("rowsPerSecond", 500) \
    .load()

# Transform to ride events
events_stream = rate_stream.select(
    uuid().alias("event_id"),
    (rand() * 4).cast("int").alias("event_type_id"),
    col("timestamp"),
    concat(lit("user_"), (rand() * 1000).cast("int")).alias("user_id"),
    # ... more columns
)
```
</details>

<details>
<summary>Hint 2: Windowed Aggregations</summary>

```python
from pyspark.sql.functions import window, col, count, avg, countDistinct

# 5-minute tumbling window aggregation
windowed_metrics = silver_stream \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(
        window(col("timestamp"), "5 minutes"),  # Tumbling window
        col("city")
    ) \
    .agg(
        count("*").alias("total_events"),
        countDistinct("ride_id").alias("unique_rides"),
        avg("fare").alias("avg_fare")
    ) \
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("city"),
        col("total_events"),
        col("unique_rides"),
        col("avg_fare")
    )

# Write to Gold table
query = windowed_metrics.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/checkpoints/gold_metrics") \
    .table("gold_city_metrics_5min")
```
</details>

<details>
<summary>Hint 3: Handling Late Data</summary>

```python
# Configure watermark for late data tolerance
stream_with_watermark = df \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(window("timestamp", "5 minutes")) \
    .count()

# Monitor late events
late_events_df = bronze_stream \
    .withColumn("latency_seconds",
                (current_timestamp().cast("long") - col("timestamp").cast("long"))) \
    .withColumn("is_late", col("latency_seconds") > 60)

late_stats = late_events_df \
    .groupBy(window("timestamp", "1 minute")) \
    .agg(
        count("*").alias("total_events"),
        sum(when(col("is_late"), 1).otherwise(0)).alias("late_events"),
        (col("late_events") / col("total_events") * 100).alias("late_percentage")
    )
```
</details>

<details>
<summary>Hint 4: Monitoring Streaming Queries</summary>

```python
import json
from datetime import datetime

def log_stream_metrics(query, query_name):
    """Log streaming query metrics to table"""
    progress = query.lastProgress

    if progress:
        metrics = {
            "query_id": query.id,
            "query_name": query_name,
            "metric_timestamp": datetime.now(),
            "input_rate": progress.get("inputRowsPerSecond", 0),
            "process_rate": progress.get("processedRowsPerSecond", 0),
            "batch_duration_ms": progress.get("batchDuration", 0),
            "num_input_rows": progress.get("numInputRows", 0),
            "watermark": progress.get("eventTime", {}).get("watermark", None)
        }

        # Write to metrics table
        spark.createDataFrame([metrics]).write \
            .format("delta") \
            .mode("append") \
            .saveAsTable("streaming_metrics")

# Call periodically (every minute)
import time
while True:
    for query in spark.streams.active:
        log_stream_metrics(query, query.name)
    time.sleep(60)
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-04-streaming-analytics
python validate.py
```

**Expected Output**:
```
✅ Task 1: Bronze stream running (498 events/sec average, checkpoint healthy)
✅ Task 2: Silver stream processing (447 events/sec, 10.2% filtered to quarantine)
   - Deduplication working (0 duplicates found)
   - Processing latency: 3.2 seconds average
✅ Task 3: Windowed aggregations (3 Gold tables updating every 5 minutes)
   - gold_active_rides_5min: 12 windows, avg 234 rides/window
   - gold_city_demand_5min: 48 windows (4 cities)
   - gold_event_funnel_5min: Acceptance rate 87.3%, Completion rate 82.1%
✅ Task 4: Watermarking configured (10-minute watermark, advancing correctly)
   - Late events (within watermark): 4.8%
   - Dropped events (exceeds watermark): 0.3%
✅ Task 5: Streaming MERGE working (1,247 user profiles, updates in real-time)
   - Idempotency verified (replay test passed)
✅ Task 6: Monitoring active (5 queries tracked, metrics logged)
   - Average latency: 4.1 seconds
   - No SLA violations in last hour

🎉 Exercise 04 Complete! Total Score: 100/100
```

---

## Deliverables
Submit the following:
1. `solution.py` - Complete streaming pipeline implementation
2. Streaming architecture diagram (Bronze → Silver → Gold flow)
3. Performance report (throughput, latency, watermark behavior)
4. Monitoring dashboard queries with sample results

---

## Resources
- [Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Watermarking and Late Data](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#handling-late-data-and-watermarking)
- [Streaming with Delta Lake](https://docs.delta.io/latest/delta-streaming.html)
- Notebook: `notebooks/04-streaming-analytics.py`
- Diagram: `assets/diagrams/streaming-architecture.mmd`
- Module 08: Streaming Basics review materials

---

## Next Steps
After completing this exercise:
- ✅ Exercise 05: SQL Analytics & Dashboards
- ✅ Exercise 06: ML with MLflow
- Review Module 15: Real-Time Analytics
- Explore Kafka integration for production streaming
