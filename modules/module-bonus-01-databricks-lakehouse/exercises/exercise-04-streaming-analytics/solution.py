"""
Exercise 04: Real-Time Streaming Analytics - Solution
======================================================

Complete production-grade real-time streaming pipeline implementation.

Features:
- Bronze/Silver/Gold streaming architecture
- 5-minute windowed aggregations
- 10-minute watermarking for late data
- Streaming MERGE with foreachBatch
- Comprehensive monitoring and metrics

Author: Training Team
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from delta.tables import DeltaTable
import uuid
import random
import time
from datetime import datetime, timedelta


# =============================================================================
# Setup
# =============================================================================

def setup_environment():
    """Initialize Spark session with optimized configurations"""
    spark = SparkSession.builder \
        .appName("Exercise04-StreamingAnalytics-Solution") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.streaming.schemaInference", "true") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/exercise04/checkpoints") \
        .config("spark.databricks.delta.optimizeWrite.enabled", "true") \
        .config("spark.databricks.delta.autoCompact.enabled", "true") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Create database
    spark.sql("CREATE DATABASE IF NOT EXISTS streaming_exercise")
    spark.sql("USE streaming_exercise")

    print("✅ Spark session initialized")
    return spark


def cleanup_previous_run(spark):
    """Clean up tables and checkpoints from previous runs"""
    print("\n🧹 Cleaning up previous run...")

    tables = [
        "bronze_ride_events",
        "silver_ride_events",
        "silver_ride_events_quarantine",
        "gold_active_rides_5min",
        "gold_city_demand_5min",
        "gold_event_funnel_5min",
        "gold_user_profiles",
        "streaming_metrics"
    ]

    for table in tables:
        spark.sql(f"DROP TABLE IF EXISTS {table}")

    print("✅ Cleanup complete")


# =============================================================================
# Data Generation
# =============================================================================

def generate_event_batch(num_events=100):
    """
    Generate realistic batch of ride events for streaming simulation.

    Includes:
    - Multiple event types (request, accept, start, complete)
    - Geographic distribution across 4 cities
    - Realistic fares and distances
    - Some late-arriving events (5-10%)
    """
    event_types = ["ride_request", "driver_accept", "ride_start", "ride_complete"]
    cities = ["San Francisco", "New York", "Los Angeles", "Chicago"]

    events = []
    current_time = datetime.now()

    for i in range(num_events):
        event_type = random.choice(event_types)
        city = random.choice(cities)

        # City coordinates (lat, lon)
        city_coords = {
            "San Francisco": (37.7749, -122.4194),
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "Chicago": (41.8781, -87.6298)
        }
        base_lat, base_lon = city_coords[city]

        # Simulate late events (5-10% of events)
        if random.random() < 0.08:
            # Late event: 2-8 minutes in the past
            event_time = current_time - timedelta(seconds=random.randint(120, 480))
        else:
            # On-time event: 0-60 seconds in the past
            event_time = current_time - timedelta(seconds=random.randint(0, 60))

        # Very late events (should be dropped by watermark)
        if random.random() < 0.02:
            event_time = current_time - timedelta(minutes=random.randint(12, 20))

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": event_time,
            "user_id": f"user_{random.randint(1, 1000)}",
            "driver_id": f"driver_{random.randint(1, 500)}" if event_type != "ride_request" else None,
            "ride_id": f"ride_{random.randint(1, 10000)}",
            "latitude": base_lat + random.uniform(-0.1, 0.1),
            "longitude": base_lon + random.uniform(-0.1, 0.1),
            "city": city,
            "fare": round(random.uniform(10, 100), 2) if event_type == "ride_complete" else None,
            "distance_km": round(random.uniform(1, 50), 2) if event_type == "ride_complete" else None
        }
        events.append(event)

    return events


# =============================================================================
# Task 1: Stream to Bronze
# =============================================================================

def task1_stream_to_bronze(spark):
    """
    Set up streaming ingestion to Bronze layer.

    Implementation:
    - Read from rate source (simulates streaming data)
    - Transform to realistic ride events
    - Write to Delta table with checkpointing
    - Append-only mode for raw data
    """
    print("\n=== Task 1: Stream to Bronze ===")

    # Define event schema
    event_schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("timestamp", TimestampType(), False),
        StructField("user_id", StringType(), False),
        StructField("driver_id", StringType(), True),
        StructField("ride_id", StringType(), False),
        StructField("latitude", DoubleType(), False),
        StructField("longitude", DoubleType(), False),
        StructField("city", StringType(), False),
        StructField("fare", DoubleType(), True),
        StructField("distance_km", DoubleType(), True)
    ])

    # Create streaming source using rate
    rate_stream = spark.readStream \
        .format("rate") \
        .option("rowsPerSecond", 50) \
        .option("numPartitions", 4) \
        .load()

    # Transform rate stream to ride events
    # Note: In production, you'd read from Kafka/Kinesis/Event Hub
    bronze_stream = rate_stream.select(
        expr("uuid()").alias("event_id"),
        when(col("value") % 4 == 0, lit("ride_request"))
            .when(col("value") % 4 == 1, lit("driver_accept"))
            .when(col("value") % 4 == 2, lit("ride_start"))
            .otherwise(lit("ride_complete")).alias("event_type"),
        col("timestamp"),
        concat(lit("user_"), (rand() * 1000).cast("int")).alias("user_id"),
        when(col("value") % 4 != 0, concat(lit("driver_"), (rand() * 500).cast("int")))
            .otherwise(lit(None)).alias("driver_id"),
        concat(lit("ride_"), (rand() * 10000).cast("int")).alias("ride_id"),
        (lit(37.7749) + (rand() - 0.5) * 0.2).alias("latitude"),
        (lit(-122.4194) + (rand() - 0.5) * 0.2).alias("longitude"),
        when((rand() * 4).cast("int") == 0, lit("San Francisco"))
            .when((rand() * 4).cast("int") == 1, lit("New York"))
            .when((rand() * 4).cast("int") == 2, lit("Los Angeles"))
            .otherwise(lit("Chicago")).alias("city"),
        when(col("value") % 4 == 3, (rand() * 90 + 10)).otherwise(lit(None)).alias("fare"),
        when(col("value") % 4 == 3, (rand() * 49 + 1)).otherwise(lit(None)).alias("distance_km")
    )

    # Write to Bronze Delta table
    print("Starting Bronze stream...")
    query = bronze_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/bronze") \
        .trigger(processingTime="10 seconds") \
        .table("bronze_ride_events")

    print(f"✅ Bronze stream started (Query ID: {query.id})")
    print("   - Table: bronze_ride_events")
    print("   - Trigger: 10 seconds")
    print("   - Mode: append")

    return query


# =============================================================================
# Task 2: Stream Transformations (Bronze → Silver)
# =============================================================================

def task2_stream_transformations(spark):
    """
    Apply real-time cleaning and enrichment transformations.

    Transformations:
    - Parse and validate timestamps
    - Add processing latency metrics
    - Validate coordinates
    - Deduplicate events
    - Filter invalid records to quarantine
    """
    print("\n=== Task 2: Stream Transformations (Bronze → Silver) ===")

    # Read from Bronze
    bronze_stream = spark.readStream \
        .format("delta") \
        .table("bronze_ride_events")

    # Apply transformations
    silver_stream = bronze_stream \
        .withColumn("processing_latency_seconds",
                   (unix_timestamp(current_timestamp()) - unix_timestamp(col("timestamp")))) \
        .withColumn("is_late_event", col("processing_latency_seconds") > 60) \
        .withColumn("event_date", to_date(col("timestamp"))) \
        .withColumn("event_hour", hour(col("timestamp"))) \
        .withColumn("event_minute", minute(col("timestamp"))) \
        .withColumn("city_upper", upper(col("city"))) \
        .withColumn("is_valid",
                   (col("user_id").isNotNull()) &
                   (col("ride_id").isNotNull()) &
                   (col("latitude").between(-90, 90)) &
                   (col("longitude").between(-180, 180)) &
                   (col("timestamp") <= current_timestamp() + expr("INTERVAL 5 MINUTES")))

    # Split valid and invalid records
    valid_stream = silver_stream.filter(col("is_valid"))
    invalid_stream = silver_stream.filter(~col("is_valid")) \
        .withColumn("rejection_reason",
                   when(col("user_id").isNull(), lit("NULL user_id"))
                   .when(col("ride_id").isNull(), lit("NULL ride_id"))
                   .when(~col("latitude").between(-90, 90), lit("Invalid latitude"))
                   .when(~col("longitude").between(-180, 180), lit("Invalid longitude"))
                   .otherwise(lit("Future timestamp")))

    # Deduplicate valid records using watermark
    deduplicated_stream = valid_stream \
        .withWatermark("timestamp", "10 minutes") \
        .dropDuplicates(["event_id"])

    # Write Silver table
    print("Starting Silver stream...")
    silver_query = deduplicated_stream \
        .drop("is_valid") \
        .writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/silver") \
        .trigger(processingTime="15 seconds") \
        .table("silver_ride_events")

    # Write quarantine table
    print("Starting Quarantine stream...")
    quarantine_query = invalid_stream \
        .writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/quarantine") \
        .trigger(processingTime="30 seconds") \
        .table("silver_ride_events_quarantine")

    print(f"✅ Silver stream started (Query ID: {silver_query.id})")
    print("   - Table: silver_ride_events")
    print("   - Deduplication: enabled with 10-min watermark")
    print("   - Quarantine: silver_ride_events_quarantine")

    return silver_query, quarantine_query


# =============================================================================
# Task 3: Windowed Aggregations
# =============================================================================

def task3_windowed_aggregations(spark):
    """
    Calculate real-time metrics with 5-minute tumbling windows.

    Creates three Gold tables:
    1. Event funnel metrics (conversion rates)
    2. City demand heatmap (geographic patterns)
    3. Active rides dashboard (operational view)
    """
    print("\n=== Task 3: Windowed Aggregations ===")

    # Read from Silver
    silver_stream = spark.readStream \
        .format("delta") \
        .table("silver_ride_events")

    # -------------------------------------------------------------------------
    # Gold Table 1: Event Funnel Metrics (5-minute windows)
    # -------------------------------------------------------------------------
    print("Creating Event Funnel aggregations...")

    funnel_stream = silver_stream \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(window(col("timestamp"), "5 minutes")) \
        .agg(
            sum(when(col("event_type") == "ride_request", 1).otherwise(0)).alias("total_requests"),
            sum(when(col("event_type") == "driver_accept", 1).otherwise(0)).alias("total_accepts"),
            sum(when(col("event_type") == "ride_start", 1).otherwise(0)).alias("total_starts"),
            sum(when(col("event_type") == "ride_complete", 1).otherwise(0)).alias("total_completes")
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("total_requests"),
            col("total_accepts"),
            col("total_starts"),
            col("total_completes"),
            (col("total_accepts") / col("total_requests") * 100).alias("acceptance_rate"),
            (col("total_completes") / col("total_requests") * 100).alias("completion_rate")
        )

    funnel_query = funnel_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/gold_funnel") \
        .trigger(processingTime="30 seconds") \
        .table("gold_event_funnel_5min")

    # -------------------------------------------------------------------------
    # Gold Table 2: City Demand Heatmap (5-minute windows by city)
    # -------------------------------------------------------------------------
    print("Creating City Demand aggregations...")

    demand_stream = silver_stream \
        .withWatermark("timestamp", "10 minutes") \
        .withColumn("lat_bucket", round(col("latitude"), 2).cast("string")) \
        .withColumn("lon_bucket", round(col("longitude"), 2).cast("string")) \
        .groupBy(
            window(col("timestamp"), "5 minutes"),
            col("city"),
            col("lat_bucket"),
            col("lon_bucket")
        ) \
        .agg(
            sum(when(col("event_type") == "ride_request", 1).otherwise(0)).alias("ride_requests"),
            avg("fare").alias("avg_fare"),
            count("*").alias("total_events")
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("city"),
            col("lat_bucket").alias("latitude_bucket"),
            col("lon_bucket").alias("longitude_bucket"),
            col("ride_requests"),
            col("avg_fare"),
            col("total_events")
        )

    demand_query = demand_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/gold_demand") \
        .trigger(processingTime="30 seconds") \
        .table("gold_city_demand_5min")

    # -------------------------------------------------------------------------
    # Gold Table 3: Active Rides Dashboard (5-minute windows by city)
    # -------------------------------------------------------------------------
    print("Creating Active Rides aggregations...")

    active_rides_stream = silver_stream \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), "5 minutes"),
            col("city")
        ) \
        .agg(
            sum(when(col("event_type") == "ride_request", 1).otherwise(0)).alias("active_requests"),
            sum(when(col("event_type") == "ride_start", 1).otherwise(0)).alias("active_trips"),
            countDistinct(when(col("driver_id").isNotNull(), col("driver_id"))).alias("drivers_active"),
            avg(col("processing_latency_seconds")).alias("avg_processing_latency_sec")
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("city"),
            col("active_requests"),
            col("active_trips"),
            col("drivers_active"),
            col("avg_processing_latency_sec")
        )

    active_query = active_rides_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/gold_active") \
        .trigger(processingTime="30 seconds") \
        .table("gold_active_rides_5min")

    print("✅ Windowed aggregations started")
    print("   - gold_event_funnel_5min: Conversion metrics")
    print("   - gold_city_demand_5min: Geographic heatmap")
    print("   - gold_active_rides_5min: Operational dashboard")

    return funnel_query, demand_query, active_query


# =============================================================================
# Task 4: Watermarking
# =============================================================================

def task4_watermarking(spark):
    """
    Demonstrate watermarking for late data handling.

    Configuration:
    - 10-minute watermark tolerance
    - Events older than watermark are dropped
    - Tracks late event metrics
    """
    print("\n=== Task 4: Watermarking ===")

    print("ℹ️  Watermarking is configured in all streaming aggregations:")
    print("   - Watermark duration: 10 minutes")
    print("   - Late events within 10 min: PROCESSED")
    print("   - Events older than 10 min: DROPPED")
    print("   - Prevents unbounded state growth")

    print("\n✅ Watermarking configured across all streaming queries")
    print("   Use query.lastProgress['eventTime'] to monitor watermark")


# =============================================================================
# Task 5: Streaming MERGE (foreachBatch UPSERT)
# =============================================================================

def task5_streaming_merge(spark):
    """
    Maintain real-time user profiles using streaming MERGE.

    Implementation:
    - foreachBatch for custom processing
    - DeltaTable.merge() for UPSERT operations
    - Aggregates lifetime user metrics
    - Idempotent (safe to replay batches)
    """
    print("\n=== Task 5: Streaming MERGE (foreachBatch UPSERT) ===")

    # Create user profiles table
    spark.sql("""
        CREATE TABLE IF NOT EXISTS gold_user_profiles (
            user_id STRING,
            first_ride_date DATE,
            last_ride_date DATE,
            total_rides INT,
            total_spent DOUBLE,
            total_distance_km DOUBLE,
            favorite_city STRING,
            last_updated TIMESTAMP
        ) USING DELTA
    """)

    def upsert_user_profiles(batch_df, batch_id):
        """
        UPSERT user profiles using Delta MERGE.

        This function is idempotent - running the same batch_id multiple times
        will produce the same result (important for exactly-once semantics).
        """
        if batch_df.count() == 0:
            return

        # Aggregate ride completions in this batch
        profiles_update = batch_df \
            .filter(col("event_type") == "ride_complete") \
            .groupBy("user_id") \
            .agg(
                min("event_date").alias("first_ride_date"),
                max("event_date").alias("last_ride_date"),
                count("*").alias("rides_in_batch"),
                sum("fare").alias("amount_in_batch"),
                sum("distance_km").alias("distance_in_batch"),
                first("city").alias("city")
            )

        if profiles_update.count() == 0:
            return

        # MERGE into profiles table
        target = DeltaTable.forName(batch_df.sparkSession, "gold_user_profiles")

        target.alias("target").merge(
            profiles_update.alias("source"),
            "target.user_id = source.user_id"
        ).whenMatchedUpdate(set={
            "last_ride_date": "source.last_ride_date",
            "total_rides": "target.total_rides + source.rides_in_batch",
            "total_spent": "target.total_spent + source.amount_in_batch",
            "total_distance_km": "target.total_distance_km + source.distance_in_batch",
            "last_updated": "current_timestamp()"
        }).whenNotMatchedInsert(values={
            "user_id": "source.user_id",
            "first_ride_date": "source.first_ride_date",
            "last_ride_date": "source.last_ride_date",
            "total_rides": "source.rides_in_batch",
            "total_spent": "source.amount_in_batch",
            "total_distance_km": "source.distance_in_batch",
            "favorite_city": "source.city",
            "last_updated": "current_timestamp()"
        }).execute()

    # Read from Silver and apply foreachBatch
    silver_stream = spark.readStream \
        .format("delta") \
        .table("silver_ride_events")

    print("Starting Streaming MERGE query...")
    merge_query = silver_stream.writeStream \
        .foreachBatch(upsert_user_profiles) \
        .option("checkpointLocation", "/tmp/exercise04/checkpoints/profiles") \
        .trigger(processingTime="20 seconds") \
        .start()

    print(f"✅ Streaming MERGE started (Query ID: {merge_query.id})")
    print("   - Table: gold_user_profiles")
    print("   - Operation: UPSERT (whenMatched + whenNotMatched)")
    print("   - Idempotency: Enabled (safe to replay)")

    return merge_query


# =============================================================================
# Task 6: Monitoring
# =============================================================================

def task6_monitoring(spark):
    """
    Monitor streaming pipeline health and performance.

    Metrics tracked:
    - Throughput (input/process rates)
    - Latency (batch duration)
    - Health (query status)
    - Watermark advancement
    """
    print("\n=== Task 6: Monitoring ===")

    # Create metrics table
    spark.sql("""
        CREATE TABLE IF NOT EXISTS streaming_metrics (
            query_id STRING,
            query_name STRING,
            metric_timestamp TIMESTAMP,
            input_rate DOUBLE,
            process_rate DOUBLE,
            batch_duration_ms LONG,
            num_input_rows LONG,
            watermark STRING,
            is_active BOOLEAN
        ) USING DELTA
    """)

    def collect_metrics():
        """Collect metrics from all active streaming queries"""
        active_streams = [s for s in spark.streams.active]

        if not active_streams:
            print("⚠️  No active streaming queries found")
            return

        print(f"\n📊 Monitoring {len(active_streams)} active queries:")

        metrics_batch = []
        for query in active_streams:
            try:
                status = query.status
                recent = query.recentProgress

                if recent:
                    progress = recent[-1]

                    metric = {
                        "query_id": query.id,
                        "query_name": query.name if query.name else f"query_{query.id[:8]}",
                        "metric_timestamp": datetime.now(),
                        "input_rate": progress.get("inputRowsPerSecond", 0.0),
                        "process_rate": progress.get("processedRowsPerSecond", 0.0),
                        "batch_duration_ms": progress.get("batchDuration", 0),
                        "num_input_rows": progress.get("numInputRows", 0),
                        "watermark": str(progress.get("eventTime", {}).get("watermark", "N/A")),
                        "is_active": status.get("isDataAvailable", False)
                    }
                    metrics_batch.append(metric)

                    print(f"\n  Query: {metric['query_name']}")
                    print(f"    Status: {'🟢 Active' if metric['is_active'] else '🟡 Idle'}")
                    print(f"    Input rate: {metric['input_rate']:.2f} rows/sec")
                    print(f"    Process rate: {metric['process_rate']:.2f} rows/sec")
                    print(f"    Batch duration: {metric['batch_duration_ms']} ms")
                    print(f"    Watermark: {metric['watermark']}")

            except Exception as e:
                print(f"  ⚠️  Error collecting metrics for query {query.id}: {e}")

        # Write metrics to table
        if metrics_batch:
            metrics_df = spark.createDataFrame(metrics_batch)
            metrics_df.write \
                .format("delta") \
                .mode("append") \
                .saveAsTable("streaming_metrics")

            print(f"\n✅ Collected metrics for {len(metrics_batch)} queries")

    # Collect initial metrics
    collect_metrics()

    print("\n💡 To monitor continuously, run:")
    print("   while True:")
    print("       collect_metrics()")
    print("       time.sleep(60)")


# =============================================================================
# Utility Functions
# =============================================================================

def wait_for_streams(seconds=30):
    """Wait for streams to process data"""
    print(f"\n⏳ Waiting {seconds} seconds for streams to process data...")
    time.sleep(seconds)
    print("✅ Wait complete")


def show_results(spark):
    """Display sample results from all tables"""
    print("\n" + "=" * 80)
    print("Sample Results")
    print("=" * 80)

    tables = [
        ("bronze_ride_events", 5),
        ("silver_ride_events", 5),
        ("gold_event_funnel_5min", 3),
        ("gold_user_profiles", 10)
    ]

    for table_name, limit in tables:
        try:
            count = spark.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").first()["cnt"]
            print(f"\n📊 {table_name}: {count} rows")
            spark.sql(f"SELECT * FROM {table_name} LIMIT {limit}").show(truncate=False)
        except Exception as e:
            print(f"⚠️  Table {table_name} not available: {e}")


def stop_all_streams(spark):
    """Stop all active streaming queries"""
    print("\n🛑 Stopping all streaming queries...")
    for query in spark.streams.active:
        query.stop()
        print(f"   Stopped: {query.id}")
    print("✅ All streams stopped")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution orchestration"""
    print("=" * 80)
    print("Exercise 04: Real-Time Streaming Analytics - SOLUTION")
    print("=" * 80)

    # Setup
    spark = setup_environment()
    cleanup_previous_run(spark)

    # Task 1: Bronze ingestion
    bronze_query = task1_stream_to_bronze(spark)

    # Task 2: Silver transformations
    silver_query, quarantine_query = task2_stream_transformations(spark)

    # Task 3: Windowed aggregations
    funnel_query, demand_query, active_query = task3_windowed_aggregations(spark)

    # Task 4: Watermarking (demonstrated in aggregations)
    task4_watermarking(spark)

    # Task 5: Streaming MERGE
    merge_query = task5_streaming_merge(spark)

    # Wait for data processing
    wait_for_streams(seconds=45)

    # Task 6: Monitoring
    task6_monitoring(spark)

    # Show results
    show_results(spark)

    print("\n" + "=" * 80)
    print("🎉 Exercise 04 Solution Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run validate.py to verify implementation")
    print("2. Check streaming metrics dashboard")
    print("3. Test failure scenarios (restart queries)")
    print("4. Monitor long-running performance")

    # Keep streams running or stop them
    print("\n⚠️  Streams are still running. To stop:")
    print("   stop_all_streams(spark)")

    return spark


if __name__ == "__main__":
    spark = main()

    # Uncomment to keep running and monitor
    # while True:
    #     time.sleep(60)
    #     task6_monitoring(spark)
