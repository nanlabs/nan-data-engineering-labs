"""
Exercise 02: Production ETL Pipelines - Medallion Architecture
Starter Code

Implement a production-grade ETL pipeline with:
- Bronze → Silver → Gold layers
- Data quality checks and quarantine
- Incremental processing with watermarks
- Data lineage tracking
- Comprehensive monitoring

Estimated time: 2.5 hours
"""

from pyspark.sql import SparkSession

# Initialize Spark with Delta Lake
spark = SparkSession.builder \
    .appName("Exercise02-ETL-Pipeline") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Database setup
DATABASE_NAME = "exercise02_etl_pipeline"
spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
spark.sql(f"USE {DATABASE_NAME}")

print(f"✅ Using database: {DATABASE_NAME}")

# =============================================================================
# TASK 1: BRONZE LAYER - RAW INGESTION (20 min)
# =============================================================================

def generate_events(num_events=10000):
    """
    Generate synthetic event data for e-commerce analytics.

    TODO: Implement event generation with:
    - event_id, user_id, timestamp, event_type, device, country, revenue
    - Include problematic data:
      * 5% with NULL user_id
      * 3% with invalid timestamps
      * 2% with negative revenue
      * 4% with unknown countries

    Hint: Use random.choice() for categorical values
    Hint: Use datetime.now() - timedelta() for timestamps
    """
    # TODO: Implement event generation
    events = []

    # Valid values for generation
    event_types = ["page_view", "add_to_cart", "purchase", "click"]
    devices = ["mobile", "desktop", "tablet"]
    valid_countries = ["US", "UK", "CA", "DE", "FR", "AU", "JP", "BR", "IN", "MX"]

    # TODO: Generate num_events events
    # for i in range(num_events):
    #     event = {
    #         "event_id": ...,
    #         "user_id": ...,  # 5% should be None
    #         "timestamp": ...,  # 3% should be invalid
    #         "event_type": ...,
    #         "device": ...,
    #         "country": ...,  # 4% should be unknown
    #         "revenue": ...  # 2% should be negative
    #     }
    #     events.append(event)

    pass  # TODO: Remove this line and implement

    # return spark.createDataFrame(events)


def ingest_to_bronze(raw_df):
    """
    Ingest raw events into Bronze layer with audit columns.

    TODO:
    - Add ingestion_timestamp (current_timestamp)
    - Add source_file (literal: "web_events_api")
    - Add load_id (unique identifier)
    - Append to bronze_events table

    Hint: Use current_timestamp(), lit(), and a UUID generator
    """
    # TODO: Add audit columns
    # bronze_df = raw_df.select(
    #     "*",
    #     ...  # Add audit columns here
    # )

    # TODO: Write to Delta table
    # bronze_df.write.format("delta") \
    #     .mode("append") \
    #     .saveAsTable("bronze_events")

    pass  # TODO: Implement


# =============================================================================
# TASK 2: SILVER LAYER - DATA CLEANING (30 min)
# =============================================================================

def clean_and_validate_data():
    """
    Transform Bronze data into clean Silver layer with quality checks.

    TODO:
    - Read from bronze_events
    - Parse timestamp column to TIMESTAMP type
    - Cast revenue to DOUBLE
    - Standardize: country → uppercase, event_type → lowercase
    - Implement 4 quality checks:
      1. user_id not NULL
      2. timestamp valid and within last 365 days
      3. revenue >= 0
      4. country in known list
    - Deduplicate by (event_id, timestamp)
    - Split into passed and quarantine tables

    Hint: Use when().otherwise() for quality checks
    Hint: Use filter() to split passed vs quarantine
    """
    # TODO: Read Bronze data
    # bronze_df = spark.table("bronze_events")

    # TODO: Parse and transform
    # cleaned_df = bronze_df.select(
    #     col("event_id"),
    #     col("user_id"),
    #     to_timestamp(col("timestamp")).alias("timestamp"),  # Parse timestamp
    #     ...  # Add transformations
    # )

    # TODO: Add quality check column
    valid_countries = ["US", "UK", "CA", "DE", "FR", "AU", "JP", "BR", "IN", "MX"]

    # quality_df = cleaned_df.withColumn(
    #     "quality_check",
    #     when(col("user_id").isNull(), "user_id_null")
    #     .when(...)  # Add more quality checks
    #     .otherwise("passed")
    # )

    # TODO: Deduplicate
    # deduped_df = quality_df.dropDuplicates(["event_id", "timestamp"])

    # TODO: Split and write
    # passed_df = ...
    # quarantine_df = ...

    pass  # TODO: Implement


# =============================================================================
# TASK 3: GOLD LAYER - BUSINESS AGGREGATIONS (30 min)
# =============================================================================

def create_daily_active_users():
    """
    Create Gold table: Daily Active Users (DAU)

    TODO: Aggregate by (date, country, device):
    - unique_users: count distinct user_id
    - total_events: count of events

    Hint: Use date_format() to extract date from timestamp
    Hint: Use countDistinct() for unique users
    """
    # TODO: Read Silver data
    # silver_df = spark.table("silver_events")

    # TODO: Add date column
    # with_date = silver_df.withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))

    # TODO: Aggregate
    # dau_df = with_date.groupBy("date", "country", "device").agg(
    #     ...
    # )

    # TODO: Write to Gold
    # dau_df.write.format("delta").mode("overwrite").saveAsTable("gold_daily_active_users")

    pass  # TODO: Implement


def create_event_funnel():
    """
    Create Gold table: Event Funnel Analysis

    TODO: Aggregate by (date, device):
    - page_views: count where event_type = 'page_view'
    - add_to_carts: count where event_type = 'add_to_cart'
    - purchases: count where event_type = 'purchase'
    - cart_conversion_rate: add_to_carts / page_views
    - purchase_conversion_rate: purchases / page_views

    Hint: Use sum(when(...)).alias() for conditional counts
    """
    # TODO: Implement funnel aggregations
    pass


def create_revenue_summary():
    """
    Create Gold table: Revenue by Region

    TODO: Aggregate by (date, country, device):
    - total_revenue: sum of revenue
    - transaction_count: count of purchase events
    - avg_transaction_value: average revenue per transaction
    - top_users: array of top 5 users by revenue

    Hint: Filter for event_type = 'purchase' only
    Hint: Use collect_list() for top users array
    """
    # TODO: Implement revenue aggregations
    pass


# =============================================================================
# TASK 4: INCREMENTAL PROCESSING (25 min)
# =============================================================================

def initialize_watermarks():
    """
    Create watermark table to track processing state.

    TODO: Create pipeline_watermarks table with columns:
    - layer (bronze/silver/gold)
    - table_name
    - last_processed_timestamp
    - updated_at
    """
    # TODO: Create watermark table
    pass


def process_incremental_bronze_to_silver():
    """
    Process only new Bronze records into Silver layer.

    TODO:
    - Get last watermark for silver_events
    - Read only new records from bronze_events
    - Apply cleaning and validation
    - Update watermark

    Hint: Use WHERE ingestion_timestamp > last_watermark
    """
    # TODO: Implement incremental processing
    pass


def update_gold_tables_incremental():
    """
    Update Gold tables using MERGE for idempotency.

    TODO:
    - Process only new Silver records
    - Use MERGE (not overwrite) to update Gold tables
    - Match on key columns (date, country, device)
    - Update if matched, insert if not matched

    Hint: Use DeltaTable.forName().merge()
    """
    # TODO: Implement MERGE operations for all 3 Gold tables
    pass


# =============================================================================
# TASK 5: DATA LINEAGE TRACKING (15 min)
# =============================================================================

def track_lineage(source_table, target_table, transformation_type,
                  records_in, records_out, records_rejected=0):
    """
    Record data lineage for transformations.

    TODO: Create data_lineage table and insert records:
    - lineage_id (UUID)
    - source_table, target_table
    - transformation_type (ingestion/cleaning/aggregation)
    - records_in, records_out, records_rejected
    - execution_timestamp

    Hint: Call this after each transformation step
    """
    # TODO: Create lineage table if not exists
    # TODO: Insert lineage record
    pass


# =============================================================================
# TASK 6: PIPELINE MONITORING (20 min)
# =============================================================================

def record_metrics(layer, table_name, metric_name, metric_value):
    """
    Record pipeline metrics for monitoring.

    TODO: Create pipeline_metrics table and insert:
    - metric_timestamp
    - layer, table_name
    - metric_name, metric_value

    Metrics to track:
    - row_count
    - processing_time_seconds
    - quality_pass_rate
    - quarantine_rate
    """
    # TODO: Implement metrics recording
    pass


def check_sla_violations():
    """
    Check for SLA violations and create alerts.

    TODO: Check thresholds:
    - quality_pass_rate < 85% → Alert
    - processing_time > 300 seconds → Alert
    - quarantine_rate > 15% → Alert

    Create pipeline_alerts table for violations
    """
    # TODO: Implement SLA checking
    pass


# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================

def run_full_pipeline():
    """Execute the complete ETL pipeline."""
    print("\n" + "="*60)
    print("RUNNING PRODUCTION ETL PIPELINE - MEDALLION ARCHITECTURE")
    print("="*60)

    # Task 1: Bronze Layer
    print("\n📥 Task 1: Ingesting to Bronze layer...")
    # TODO: Generate events and ingest to Bronze
    # raw_df = generate_events(10000)
    # ingest_to_bronze(raw_df)
    print("⚠️  TODO: Implement Bronze ingestion")

    # Task 2: Silver Layer
    print("\n🧹 Task 2: Cleaning to Silver layer...")
    # TODO: Clean and validate
    print("⚠️  TODO: Implement Silver cleaning")

    # Task 3: Gold Layer
    print("\n🏆 Task 3: Creating Gold aggregations...")
    # TODO: Create all 3 Gold tables
    print("⚠️  TODO: Implement Gold aggregations")

    # Task 4: Incremental Processing
    print("\n⏭️  Task 4: Testing incremental processing...")
    # TODO: Test with new data
    print("⚠️  TODO: Implement incremental processing")

    # Task 5: Lineage
    print("\n🔗 Task 5: Tracking data lineage...")
    # TODO: Record lineage
    print("⚠️  TODO: Implement lineage tracking")

    # Task 6: Monitoring
    print("\n📊 Task 6: Recording metrics...")
    # TODO: Record metrics and check SLAs
    print("⚠️  TODO: Implement monitoring")

    print("\n" + "="*60)
    print("✅ Pipeline execution completed!")
    print("Run validate.py to check your work")
    print("="*60)


if __name__ == "__main__":
    run_full_pipeline()
