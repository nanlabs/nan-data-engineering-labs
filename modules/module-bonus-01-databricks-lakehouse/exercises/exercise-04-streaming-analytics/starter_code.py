"""
Exercise 04: Real-Time Streaming Analytics - Starter Code
============================================================

Build a production-grade real-time streaming pipeline using Structured Streaming.

Tasks:
1. Stream to Bronze (readStream JSON, writeStream Delta)
2. Stream transformations (readStream Bronze, clean, writeStream Silver)
3. Windowed aggregations (5-minute tumbling windows, groupBy)
4. Watermarking (withWatermark 10 minutes)
5. Streaming MERGE (foreachBatch with UPSERT)
6. Monitoring (query.status, recentProgress metrics)

Estimated Time: 2 hours
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
import uuid
import random
from datetime import datetime, timedelta


# =============================================================================
# Setup
# =============================================================================

def setup_environment():
    """Initialize Spark session and configure environment"""
    spark = SparkSession.builder \
        .appName("Exercise04-StreamingAnalytics") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/exercise04/checkpoints") \
        .getOrCreate()

    # Create database
    spark.sql("CREATE DATABASE IF NOT EXISTS streaming_exercise")
    spark.sql("USE streaming_exercise")

    # Clean up previous run
    print("Cleaning up previous run...")
    spark.sql("DROP TABLE IF EXISTS bronze_ride_events")
    spark.sql("DROP TABLE IF EXISTS silver_ride_events")
    spark.sql("DROP TABLE IF EXISTS silver_ride_events_quarantine")
    spark.sql("DROP TABLE IF EXISTS gold_active_rides_5min")
    spark.sql("DROP TABLE IF EXISTS gold_city_demand_5min")
    spark.sql("DROP TABLE IF EXISTS gold_event_funnel_5min")
    spark.sql("DROP TABLE IF EXISTS gold_user_profiles")
    spark.sql("DROP TABLE IF EXISTS streaming_metrics")

    return spark


# =============================================================================
# Data Generation
# =============================================================================

def generate_event_batch(num_events=100):
    """Generate batch of ride events for streaming simulation"""
    event_types = ["ride_request", "driver_accept", "ride_start", "ride_complete"]
    cities = ["San Francisco", "New York", "Los Angeles", "Chicago"]

    events = []
    for i in range(num_events):
        event_type = random.choice(event_types)
        city = random.choice(cities)

        # Base coordinates for each city
        city_coords = {
            "San Francisco": (37.7749, -122.4194),
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "Chicago": (41.8781, -87.6298)
        }
        base_lat, base_lon = city_coords[city]

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now() - timedelta(seconds=random.randint(0, 300)),
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
# Task 1: Stream to Bronze (TODO)
# =============================================================================

def task1_stream_to_bronze(spark):
    """
    Set up streaming ingestion from source to Bronze Delta table.

    Requirements:
    - Create bronze_ride_events Delta table (streaming write)
    - Read from rate source and transform to ride events
    - Configure checkpointing for fault tolerance
    - Append-only writes

    TODO: Implement the streaming pipeline
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

    # TODO: Create streaming source using spark.readStream
    # Hint: Use format("rate") with option("rowsPerSecond", 50)
    # Then transform to ride events using generate_event_batch

    # TODO: Write stream to Bronze Delta table
    # Hint: Use writeStream.format("delta")
    #       .outputMode("append")
    #       .option("checkpointLocation", "/tmp/exercise04/checkpoints/bronze")
    #       .trigger(processingTime="10 seconds")
    #       .table("bronze_ride_events")

    print("⚠️  TODO: Implement bronze streaming ingestion")
    return None


# =============================================================================
# Task 2: Stream Transformations (Bronze → Silver) (TODO)
# =============================================================================

def task2_stream_transformations(spark):
    """
    Apply real-time cleaning and enrichment transformations.

    Requirements:
    - Create silver_ride_events streaming table
    - Clean data (filter nulls, parse timestamps, validate coordinates)
    - Enrich with computed columns
    - Deduplicate by event_id

    TODO: Implement Silver transformations
    """
    print("\n=== Task 2: Stream Transformations (Bronze → Silver) ===")

    # TODO: Read stream from Bronze table
    # Hint: spark.readStream.format("delta").table("bronze_ride_events")

    # TODO: Apply transformations
    # - Add processing_latency_seconds: current_timestamp - timestamp
    # - Add is_late_event: latency > 60 seconds
    # - Add event_date: cast timestamp to date
    # - Add event_hour: extract hour from timestamp
    # - Filter out NULL user_id or ride_id
    # - Filter out invalid coordinates (lat: -90 to 90, lon: -180 to 180)

    # TODO: Apply deduplication
    # Hint: Use withWatermark("timestamp", "10 minutes")
    #       .dropDuplicates(["event_id"])

    # TODO: Write stream to Silver table
    # Hint: Use outputMode("append") with trigger every 15 seconds

    print("⚠️  TODO: Implement Silver stream transformations")
    return None


# =============================================================================
# Task 3: Windowed Aggregations (TODO)
# =============================================================================

def task3_windowed_aggregations(spark):
    """
    Calculate real-time metrics using 5-minute tumbling windows.

    Requirements:
    - Create 3 Gold tables with windowed aggregations
    - 5-minute tumbling windows
    - Various groupBy dimensions

    TODO: Implement windowed aggregations
    """
    print("\n=== Task 3: Windowed Aggregations ===")

    # TODO: Read from Silver stream

    # TODO: Create gold_event_funnel_5min
    # Aggregate by 5-minute window:
    # - total_requests (count where event_type = 'ride_request')
    # - total_accepts (count where event_type = 'driver_accept')
    # - total_starts (count where event_type = 'ride_start')
    # - total_completes (count where event_type = 'ride_complete')
    # - acceptance_rate (accepts / requests)
    # - completion_rate (completes / requests)
    # Hint: Use window(col("timestamp"), "5 minutes")

    print("⚠️  TODO: Implement windowed aggregations")
    return None


# =============================================================================
# Task 4: Watermarking (TODO)
# =============================================================================

def task4_watermarking(spark):
    """
    Handle late-arriving events with watermarking.

    Requirements:
    - Configure 10-minute watermark
    - Events older than watermark are dropped
    - Track late event metrics

    TODO: Implement watermarking
    """
    print("\n=== Task 4: Watermarking ===")

    # TODO: Read from Silver stream and apply watermark
    # Hint: withWatermark("timestamp", "10 minutes")

    # TODO: Create aggregation with watermark
    # Group by 5-minute window and city
    # Count events and track late arrivals

    # TODO: Monitor watermark advancement
    # Print progress.eventTime.watermark

    print("⚠️  TODO: Implement watermarking")
    return None


# =============================================================================
# Task 5: Streaming MERGE (foreachBatch UPSERT) (TODO)
# =============================================================================

def task5_streaming_merge(spark):
    """
    Maintain real-time user profiles with streaming MERGE.

    Requirements:
    - Create gold_user_profiles table
    - UPSERT profile on each ride completion
    - Track lifetime stats per user

    TODO: Implement streaming MERGE
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

    # TODO: Define foreachBatch function for UPSERT
    def upsert_profiles(batch_df, batch_id):
        """
        UPSERT user profiles using Delta MERGE

        TODO: Implement MERGE logic
        1. Filter for ride_complete events
        2. Aggregate by user_id
        3. Use DeltaTable.forName().merge() with whenMatchedUpdate and whenNotMatchedInsert
        """
        pass

    # TODO: Read from Silver stream and apply foreachBatch
    # Hint: writeStream.foreachBatch(upsert_profiles)
    #       .option("checkpointLocation", "/tmp/exercise04/checkpoints/profiles")

    print("⚠️  TODO: Implement streaming MERGE")
    return None


# =============================================================================
# Task 6: Monitoring (TODO)
# =============================================================================

def task6_monitoring(spark):
    """
    Monitor streaming pipeline health and performance.

    Requirements:
    - Track throughput metrics (input/process rates)
    - Track latency metrics
    - Track health metrics

    TODO: Implement monitoring
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
            watermark STRING
        ) USING DELTA
    """)

    # TODO: Get all active streams
    # Hint: spark.streams.active

    # TODO: For each query, extract metrics
    # - query.status
    # - query.recentProgress
    # - inputRowsPerSecond
    # - processedRowsPerSecond
    # - batchDuration

    # TODO: Log metrics to streaming_metrics table

    print("⚠️  TODO: Implement streaming monitoring")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution function"""
    print("=" * 80)
    print("Exercise 04: Real-Time Streaming Analytics - Starter Code")
    print("=" * 80)

    # Setup
    spark = setup_environment()

    # Execute tasks
    task1_stream_to_bronze(spark)
    task2_stream_transformations(spark)
    task3_windowed_aggregations(spark)
    task4_watermarking(spark)
    task5_streaming_merge(spark)
    task6_monitoring(spark)

    print("\n" + "=" * 80)
    print("Starter code execution complete!")
    print("Complete all TODOs and run validate.py to check your work.")
    print("=" * 80)


if __name__ == "__main__":
    main()
