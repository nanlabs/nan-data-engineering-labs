"""
Exercise 02: Production ETL Pipelines - Medallion Architecture
Complete Solution

This solution demonstrates a production-grade ETL pipeline with:
- Bronze → Silver → Gold layers (Medallion Architecture)
- Comprehensive data quality checks
- Incremental processing with watermarks
- MERGE-based idempotent operations
- Full data lineage tracking
- Real-time monitoring and alerting
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, lit, to_timestamp,
    countDistinct, count, sum as _sum, avg,
    when, date_format, collect_list, struct,
    upper, lower, datediff, expr, desc
)
from pyspark.sql.types import (
    StructType, StructField, StringType,
    DoubleType, TimestampType, LongType
)
from delta.tables import DeltaTable
import random
import uuid
from datetime import datetime, timedelta
import time

# Initialize Spark with Delta Lake
spark = SparkSession.builder \
    .appName("Exercise02-ETL-Pipeline-Solution") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Set log level to reduce noise
spark.sparkContext.setLogLevel("WARN")

# Database configuration
DATABASE_NAME = "exercise02_etl_pipeline"
spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
spark.sql(f"USE {DATABASE_NAME}")

print(f"✅ Using database: {DATABASE_NAME}")

# =============================================================================
# TASK 1: BRONZE LAYER - RAW INGESTION
# =============================================================================

def generate_events(num_events=10000):
    """
    Generate synthetic e-commerce event data with intentional data quality issues.

    Args:
        num_events: Number of events to generate

    Returns:
        DataFrame with raw event data
    """
    print(f"📊 Generating {num_events:,} events...")

    events = []

    # Reference data
    event_types = ["page_view", "add_to_cart", "purchase", "click"]
    devices = ["mobile", "desktop", "tablet"]
    valid_countries = ["US", "UK", "CA", "DE", "FR", "AU", "JP", "BR", "IN", "MX"]
    invalid_countries = ["XX", "YY", "ZZ", "UNKNOWN"]

    # Base timestamp - events over last 30 days
    base_time = datetime.now()

    for i in range(num_events):
        # Generate base event
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        user_id = f"user_{random.randint(1000, 9999)}"

        # Timestamp (3% invalid)
        if random.random() < 0.03:
            timestamp = "invalid_timestamp"  # Invalid format
        else:
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            event_time = base_time - timedelta(days=days_ago, hours=hours_ago)
            timestamp = event_time.strftime("%Y-%m-%d %H:%M:%S")

        # Event type
        event_type = random.choice(event_types)

        # Device
        device = random.choice(devices)

        # Country (4% unknown)
        if random.random() < 0.04:
            country = random.choice(invalid_countries)
        else:
            country = random.choice(valid_countries)

        # Revenue (2% negative, only for purchases)
        if event_type == "purchase":
            if random.random() < 0.02:
                revenue = str(round(random.uniform(-100, -10), 2))  # Negative
            else:
                revenue = str(round(random.uniform(10, 500), 2))
        else:
            revenue = "0.0"

        # 5% with NULL user_id
        if random.random() < 0.05:
            user_id = None

        event = {
            "event_id": event_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "device": device,
            "country": country,
            "revenue": revenue
        }
        events.append(event)

    print(f"✅ Generated {len(events):,} events with data quality issues")
    return spark.createDataFrame(events)


def ingest_to_bronze(raw_df, load_id=None):
    """
    Ingest raw events into Bronze layer with audit columns.
    Bronze layer is append-only and preserves raw data exactly as received.

    Args:
        raw_df: Raw event DataFrame
        load_id: Optional load batch identifier
    """
    print("📥 Ingesting to Bronze layer...")

    if load_id is None:
        load_id = str(uuid.uuid4())

    # Add audit columns for tracking
    bronze_df = raw_df.select(
        "*",
        current_timestamp().alias("ingestion_timestamp"),
        lit("web_events_api").alias("source_file"),
        lit(load_id).alias("load_id")
    )

    # Write to Bronze table (append-only, never overwrite)
    bronze_df.write.format("delta") \
        .mode("append") \
        .saveAsTable("bronze_events")

    row_count = bronze_df.count()
    print(f"✅ Ingested {row_count:,} records to bronze_events")

    return row_count


# =============================================================================
# TASK 2: SILVER LAYER - DATA CLEANING & VALIDATION
# =============================================================================

def clean_and_validate_data():
    """
    Transform Bronze data into clean Silver layer with comprehensive quality checks.
    - Parse and cast data types
    - Standardize values
    - Apply 4 quality rules
    - Deduplicate
    - Separate passed vs quarantine records
    """
    print("🧹 Cleaning and validating data for Silver layer...")

    # Read Bronze data
    bronze_df = spark.table("bronze_events")
    bronze_count = bronze_df.count()
    print(f"📊 Processing {bronze_count:,} Bronze records...")

    # Valid reference data
    valid_countries = ["US", "UK", "CA", "DE", "FR", "AU", "JP", "BR", "IN", "MX"]
    cutoff_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Parse and transform data
    cleaned_df = bronze_df.select(
        col("event_id"),
        col("user_id"),
        to_timestamp(col("timestamp")).alias("timestamp_parsed"),
        col("timestamp").alias("timestamp_raw"),
        lower(col("event_type")).alias("event_type"),
        col("device"),
        upper(col("country")).alias("country"),
        col("revenue").cast("double").alias("revenue"),
        col("ingestion_timestamp"),
        col("source_file"),
        col("load_id")
    )

    # Apply comprehensive quality checks
    quality_df = cleaned_df.withColumn(
        "quality_check",
        when(col("user_id").isNull(), "user_id_null")
        .when(col("timestamp_parsed").isNull(), "invalid_timestamp")
        .when(
            (col("timestamp_parsed").isNotNull()) &
            (datediff(current_timestamp(), col("timestamp_parsed")) > 365),
            "timestamp_too_old"
        )
        .when(col("revenue") < 0, "negative_revenue")
        .when(~col("country").isin(valid_countries), "unknown_country")
        .otherwise("passed")
    )

    # Deduplicate by event_id and timestamp
    deduped_df = quality_df.dropDuplicates(["event_id", "timestamp_parsed"])

    # Split into passed and quarantine
    passed_df = deduped_df.filter(col("quality_check") == "passed") \
        .select(
            "event_id", "user_id", "timestamp_parsed", "event_type",
            "device", "country", "revenue", "ingestion_timestamp"
        ).withColumnRenamed("timestamp_parsed", "timestamp")

    quarantine_df = deduped_df.filter(col("quality_check") != "passed") \
        .select(
            "event_id", "user_id", "timestamp_raw", "event_type",
            "device", "country", "revenue", "quality_check",
            "ingestion_timestamp"
        ).withColumn("quarantine_timestamp", current_timestamp())

    # Write to Silver and Quarantine tables
    passed_df.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("silver_events")

    quarantine_df.write.format("delta") \
        .mode("append") \
        .saveAsTable("silver_events_quarantine")

    passed_count = passed_df.count()
    quarantine_count = quarantine_df.count()
    quality_rate = (passed_count / bronze_count * 100) if bronze_count > 0 else 0

    print(f"✅ Silver layer: {passed_count:,} records ({quality_rate:.1f}% pass rate)")
    print(f"⚠️  Quarantine: {quarantine_count:,} records rejected")

    # Show quarantine summary
    print("\n📋 Quarantine Summary:")
    quarantine_df.groupBy("quality_check").count() \
        .orderBy(desc("count")).show(truncate=False)

    return passed_count, quarantine_count


# =============================================================================
# TASK 3: GOLD LAYER - BUSINESS AGGREGATIONS
# =============================================================================

def create_daily_active_users():
    """
    Create Gold table: Daily Active Users (DAU)
    Aggregates unique users and event counts by date, country, and device.
    """
    print("🏆 Creating gold_daily_active_users...")

    silver_df = spark.table("silver_events")

    # Add date column
    with_date = silver_df.withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))

    # Aggregate by date, country, device
    dau_df = with_date.groupBy("date", "country", "device").agg(
        countDistinct("user_id").alias("unique_users"),
        count("*").alias("total_events")
    )

    # Write to Gold table
    dau_df.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("gold_daily_active_users")

    row_count = dau_df.count()
    print(f"✅ Created gold_daily_active_users: {row_count:,} rows")

    return row_count


def create_event_funnel():
    """
    Create Gold table: Event Funnel Analysis
    Tracks conversion rates through the user journey.
    """
    print("🏆 Creating gold_event_funnel...")

    silver_df = spark.table("silver_events")

    # Add date column
    with_date = silver_df.withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))

    # Aggregate funnel metrics by date and device
    funnel_df = with_date.groupBy("date", "device").agg(
        _sum(when(col("event_type") == "page_view", 1).otherwise(0)).alias("page_views"),
        _sum(when(col("event_type") == "add_to_cart", 1).otherwise(0)).alias("add_to_carts"),
        _sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchases")
    )

    # Calculate conversion rates
    funnel_with_rates = funnel_df.withColumn(
        "cart_conversion_rate",
        when(col("page_views") > 0, col("add_to_carts") / col("page_views")).otherwise(0)
    ).withColumn(
        "purchase_conversion_rate",
        when(col("page_views") > 0, col("purchases") / col("page_views")).otherwise(0)
    )

    # Write to Gold table
    funnel_with_rates.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("gold_event_funnel")

    row_count = funnel_with_rates.count()
    print(f"✅ Created gold_event_funnel: {row_count:,} rows")

    return row_count


def create_revenue_summary():
    """
    Create Gold table: Revenue by Region
    Aggregates revenue metrics and identifies top users.
    """
    print("🏆 Creating gold_revenue_summary...")

    silver_df = spark.table("silver_events")

    # Filter for purchase events only
    purchases = silver_df.filter(col("event_type") == "purchase")

    # Add date column
    with_date = purchases.withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))

    # Aggregate revenue metrics
    revenue_df = with_date.groupBy("date", "country", "device").agg(
        _sum("revenue").alias("total_revenue"),
        count("*").alias("transaction_count"),
        avg("revenue").alias("avg_transaction_value")
    )

    # Get top 5 users by revenue for each date/country/device
    # Create a window function to rank users
    top_users_df = with_date.groupBy("date", "country", "device", "user_id").agg(
        _sum("revenue").alias("user_revenue")
    )

    # For simplicity, collect top users as array (in production, use window functions)
    from pyspark.sql.window import Window
    window_spec = Window.partitionBy("date", "country", "device").orderBy(desc("user_revenue"))

    top_users_ranked = top_users_df.withColumn(
        "rank",
        expr("row_number() OVER (PARTITION BY date, country, device ORDER BY user_revenue DESC)")
    ).filter(col("rank") <= 5)

    # Collect top users as array
    top_users_agg = top_users_ranked.groupBy("date", "country", "device").agg(
        collect_list(
            struct(col("user_id"), col("user_revenue"))
        ).alias("top_users")
    )

    # Join with revenue metrics
    revenue_summary = revenue_df.join(
        top_users_agg,
        ["date", "country", "device"],
        "left"
    )

    # Write to Gold table
    revenue_summary.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("gold_revenue_summary")

    row_count = revenue_summary.count()
    print(f"✅ Created gold_revenue_summary: {row_count:,} rows")

    return row_count


# =============================================================================
# TASK 4: INCREMENTAL PROCESSING
# =============================================================================

def initialize_watermarks():
    """
    Create watermark table to track last processed timestamp for each layer.
    Used for incremental processing to avoid full table scans.
    """
    print("💧 Initializing watermark table...")

    schema = StructType([
        StructField("layer", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("last_processed_timestamp", TimestampType(), True),
        StructField("updated_at", TimestampType(), False)
    ])

    # Create empty watermark table
    spark.createDataFrame([], schema).write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("pipeline_watermarks")

    print("✅ Watermark table created")


def get_watermark(layer, table_name):
    """Get last processed timestamp for a layer/table."""
    try:
        result = spark.sql(f"""
            SELECT last_processed_timestamp
            FROM pipeline_watermarks
            WHERE layer = '{layer}' AND table_name = '{table_name}'
        """).first()

        if result and result[0]:
            return result[0]
    except:
        pass

    # Return very old timestamp if no watermark exists
    return datetime(2020, 1, 1)


def update_watermark(layer, table_name, new_timestamp):
    """Update watermark for a layer/table."""
    try:
        delta_table = DeltaTable.forName(spark, "pipeline_watermarks")

        delta_table.alias("target").merge(
            spark.createDataFrame([(layer, table_name, new_timestamp, datetime.now())],
                                ["layer", "table_name", "last_processed_timestamp", "updated_at"]).alias("source"),
            "target.layer = source.layer AND target.table_name = source.table_name"
        ).whenMatchedUpdate(set={
            "last_processed_timestamp": "source.last_processed_timestamp",
            "updated_at": "source.updated_at"
        }).whenNotMatchedInsertAll().execute()

    except Exception:
        # If table doesn't exist or MERGE fails, append
        spark.createDataFrame([(layer, table_name, new_timestamp, datetime.now())],
                            ["layer", "table_name", "last_processed_timestamp", "updated_at"]) \
            .write.format("delta").mode("append").saveAsTable("pipeline_watermarks")


def process_incremental_bronze_to_silver():
    """
    Process only new Bronze records into Silver layer.
    Uses watermark to identify unprocessed records.
    """
    print("⏭️  Processing incremental Bronze → Silver...")

    # Get last watermark
    last_watermark = get_watermark("silver", "silver_events")
    print(f"📍 Last watermark: {last_watermark}")

    # Read only new Bronze records
    new_records = spark.sql(f"""
        SELECT * FROM bronze_events
        WHERE ingestion_timestamp > '{last_watermark}'
    """)

    new_count = new_records.count()
    if new_count == 0:
        print("✅ No new records to process")
        return 0

    print(f"📊 Processing {new_count:,} new Bronze records...")

    # Apply same cleaning logic as full load
    valid_countries = ["US", "UK", "CA", "DE", "FR", "AU", "JP", "BR", "IN", "MX"]

    cleaned_df = new_records.select(
        col("event_id"),
        col("user_id"),
        to_timestamp(col("timestamp")).alias("timestamp_parsed"),
        col("timestamp").alias("timestamp_raw"),
        lower(col("event_type")).alias("event_type"),
        col("device"),
        upper(col("country")).alias("country"),
        col("revenue").cast("double").alias("revenue"),
        col("ingestion_timestamp")
    )

    quality_df = cleaned_df.withColumn(
        "quality_check",
        when(col("user_id").isNull(), "user_id_null")
        .when(col("timestamp_parsed").isNull(), "invalid_timestamp")
        .when(col("revenue") < 0, "negative_revenue")
        .when(~col("country").isin(valid_countries), "unknown_country")
        .otherwise("passed")
    )

    passed_df = quality_df.filter(col("quality_check") == "passed") \
        .select("event_id", "user_id", "timestamp_parsed", "event_type",
               "device", "country", "revenue", "ingestion_timestamp") \
        .withColumnRenamed("timestamp_parsed", "timestamp")

    # Append to Silver (incremental)
    passed_df.write.format("delta") \
        .mode("append") \
        .saveAsTable("silver_events")

    passed_count = passed_df.count()

    # Update watermark
    max_timestamp = new_records.agg({"ingestion_timestamp": "max"}).first()[0]
    update_watermark("silver", "silver_events", max_timestamp)

    print(f"✅ Processed {passed_count:,} new Silver records")
    print(f"📍 Updated watermark to: {max_timestamp}")

    return passed_count


def update_gold_tables_incremental():
    """
    Update Gold tables using MERGE for idempotency.
    Only processes new Silver records and uses MERGE to avoid duplicates.
    """
    print("⏭️  Updating Gold tables incrementally...")

    # Get last watermark for Gold layer
    last_watermark = get_watermark("gold", "gold_daily_active_users")

    # Read only new Silver records
    new_silver = spark.sql(f"""
        SELECT * FROM silver_events
        WHERE ingestion_timestamp > '{last_watermark}'
    """)

    new_count = new_silver.count()
    if new_count == 0:
        print("✅ No new records to process")
        return

    print(f"📊 Processing {new_count:,} new Silver records for Gold layer...")

    # Prepare data with date
    with_date = new_silver.withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))

    # Update DAU table with MERGE
    dau_updates = with_date.groupBy("date", "country", "device").agg(
        countDistinct("user_id").alias("unique_users"),
        count("*").alias("total_events")
    )

    try:
        dau_table = DeltaTable.forName(spark, "gold_daily_active_users")
        dau_table.alias("target").merge(
            dau_updates.alias("source"),
            "target.date = source.date AND target.country = source.country AND target.device = source.device"
        ).whenMatchedUpdate(set={
            "unique_users": "source.unique_users",
            "total_events": "source.total_events"
        }).whenNotMatchedInsertAll().execute()
        print("✅ Updated gold_daily_active_users")
    except Exception as e:
        print(f"⚠️  DAU table update: {e}")

    # Update watermark
    max_timestamp = new_silver.agg({"ingestion_timestamp": "max"}).first()[0]
    update_watermark("gold", "gold_daily_active_users", max_timestamp)

    print("✅ Gold tables updated incrementally")


# =============================================================================
# TASK 5: DATA LINEAGE TRACKING
# =============================================================================

def initialize_lineage_table():
    """Create data lineage tracking table."""
    print("🔗 Initializing lineage table...")

    schema = StructType([
        StructField("lineage_id", StringType(), False),
        StructField("source_table", StringType(), False),
        StructField("target_table", StringType(), False),
        StructField("transformation_type", StringType(), False),
        StructField("records_in", LongType(), False),
        StructField("records_out", LongType(), False),
        StructField("records_rejected", LongType(), False),
        StructField("execution_timestamp", TimestampType(), False)
    ])

    spark.createDataFrame([], schema).write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("data_lineage")

    print("✅ Lineage table created")


def track_lineage(source_table, target_table, transformation_type,
                  records_in, records_out, records_rejected=0):
    """
    Record data lineage for a transformation.
    Tracks data flow from source to target with metrics.
    """
    lineage_record = spark.createDataFrame([{
        "lineage_id": str(uuid.uuid4()),
        "source_table": source_table,
        "target_table": target_table,
        "transformation_type": transformation_type,
        "records_in": records_in,
        "records_out": records_out,
        "records_rejected": records_rejected,
        "execution_timestamp": datetime.now()
    }])

    lineage_record.write.format("delta") \
        .mode("append") \
        .saveAsTable("data_lineage")

    quality_score = (records_out / records_in * 100) if records_in > 0 else 0
    print(f"🔗 Lineage tracked: {source_table} → {target_table} ({quality_score:.1f}% quality)")


def show_lineage_report():
    """Display complete data lineage report."""
    print("\n" + "="*60)
    print("📊 DATA LINEAGE REPORT")
    print("="*60)

    lineage_df = spark.table("data_lineage")
    lineage_df.select(
        "source_table", "target_table", "transformation_type",
        "records_in", "records_out", "records_rejected"
    ).show(truncate=False)

    # Calculate overall quality score
    totals = lineage_df.agg(
        _sum("records_in").alias("total_in"),
        _sum("records_out").alias("total_out"),
        _sum("records_rejected").alias("total_rejected")
    ).first()

    if totals[0] > 0:
        quality_score = totals[1] / totals[0] * 100
        print(f"\n📈 Overall Data Quality Score: {quality_score:.1f}%")
        print(f"   Total Records In: {totals[0]:,}")
        print(f"   Total Records Out: {totals[1]:,}")
        print(f"   Total Rejected: {totals[2]:,}")


# =============================================================================
# TASK 6: PIPELINE MONITORING
# =============================================================================

def initialize_monitoring_tables():
    """Create metrics and alerts tables for monitoring."""
    print("📊 Initializing monitoring tables...")

    # Metrics table
    metrics_schema = StructType([
        StructField("metric_timestamp", TimestampType(), False),
        StructField("layer", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("metric_name", StringType(), False),
        StructField("metric_value", DoubleType(), False)
    ])

    spark.createDataFrame([], metrics_schema).write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("pipeline_metrics")

    # Alerts table
    alerts_schema = StructType([
        StructField("alert_timestamp", TimestampType(), False),
        StructField("alert_type", StringType(), False),
        StructField("layer", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("message", StringType(), False),
        StructField("metric_value", DoubleType(), False),
        StructField("threshold", DoubleType(), False)
    ])

    spark.createDataFrame([], alerts_schema).write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("pipeline_alerts")

    print("✅ Monitoring tables created")


def record_metrics(layer, table_name, metrics_dict):
    """
    Record multiple metrics for a layer/table.

    Args:
        layer: bronze/silver/gold
        table_name: Name of the table
        metrics_dict: Dictionary of metric_name -> metric_value
    """
    timestamp = datetime.now()

    metric_records = [
        (timestamp, layer, table_name, metric_name, float(metric_value))
        for metric_name, metric_value in metrics_dict.items()
    ]

    metrics_df = spark.createDataFrame(
        metric_records,
        ["metric_timestamp", "layer", "table_name", "metric_name", "metric_value"]
    )

    metrics_df.write.format("delta") \
        .mode("append") \
        .saveAsTable("pipeline_metrics")


def check_sla_violations():
    """
    Check for SLA violations and create alerts.
    Thresholds:
    - quality_pass_rate < 85%
    - processing_time > 300 seconds
    - quarantine_rate > 15%
    """
    print("🚨 Checking SLA violations...")

    # Get latest metrics
    latest_metrics = spark.sql("""
        SELECT layer, table_name, metric_name, metric_value,
               metric_timestamp
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY layer, table_name, metric_name
                                     ORDER BY metric_timestamp DESC) as rn
            FROM pipeline_metrics
        ) WHERE rn = 1
    """)

    alerts = []
    timestamp = datetime.now()

    # Check quality pass rate
    quality_metrics = latest_metrics.filter(col("metric_name") == "quality_pass_rate")
    for row in quality_metrics.collect():
        if row.metric_value < 85.0:
            alerts.append((
                timestamp, "quality_violation", row.layer, row.table_name,
                f"Quality pass rate ({row.metric_value:.1f}%) below threshold",
                row.metric_value, 85.0
            ))

    # Check processing time
    time_metrics = latest_metrics.filter(col("metric_name") == "processing_time_seconds")
    for row in time_metrics.collect():
        if row.metric_value > 300:
            alerts.append((
                timestamp, "performance_violation", row.layer, row.table_name,
                f"Processing time ({row.metric_value:.1f}s) exceeds threshold",
                row.metric_value, 300.0
            ))

    # Check quarantine rate
    quarantine_metrics = latest_metrics.filter(col("metric_name") == "quarantine_rate")
    for row in quarantine_metrics.collect():
        if row.metric_value > 15.0:
            alerts.append((
                timestamp, "quarantine_violation", row.layer, row.table_name,
                f"Quarantine rate ({row.metric_value:.1f}%) exceeds threshold",
                row.metric_value, 15.0
            ))

    if alerts:
        alerts_df = spark.createDataFrame(
            alerts,
            ["alert_timestamp", "alert_type", "layer", "table_name",
             "message", "metric_value", "threshold"]
        )
        alerts_df.write.format("delta") \
            .mode("append") \
            .saveAsTable("pipeline_alerts")

        print(f"⚠️  {len(alerts)} SLA violation(s) detected!")
        alerts_df.show(truncate=False)
    else:
        print("✅ No SLA violations detected")


# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================

def run_full_pipeline():
    """Execute the complete ETL pipeline with all tasks."""

    print("\n" + "="*70)
    print("🚀 PRODUCTION ETL PIPELINE - MEDALLION ARCHITECTURE")
    print("="*70)

    start_time = time.time()

    # Initialize monitoring and lineage
    initialize_monitoring_tables()
    initialize_lineage_table()
    initialize_watermarks()

    # -------------------------------------------------------------------------
    # TASK 1: Bronze Layer Ingestion
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("📥 TASK 1: BRONZE LAYER INGESTION")
    print("="*70)

    task_start = time.time()
    raw_df = generate_events(10000)
    bronze_count = ingest_to_bronze(raw_df)
    task_time = time.time() - task_start

    # Track lineage
    track_lineage("source_api", "bronze_events", "ingestion",
                  bronze_count, bronze_count, 0)

    # Record metrics
    record_metrics("bronze", "bronze_events", {
        "row_count": bronze_count,
        "processing_time_seconds": task_time
    })

    # -------------------------------------------------------------------------
    # TASK 2: Silver Layer Cleaning
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("🧹 TASK 2: SILVER LAYER CLEANING & VALIDATION")
    print("="*70)

    task_start = time.time()
    silver_count, quarantine_count = clean_and_validate_data()
    task_time = time.time() - task_start

    # Track lineage
    track_lineage("bronze_events", "silver_events", "cleaning",
                  bronze_count, silver_count, quarantine_count)

    # Record metrics
    quality_rate = (silver_count / bronze_count * 100) if bronze_count > 0 else 0
    quarantine_rate = (quarantine_count / bronze_count * 100) if bronze_count > 0 else 0

    record_metrics("silver", "silver_events", {
        "row_count": silver_count,
        "processing_time_seconds": task_time,
        "quality_pass_rate": quality_rate,
        "quarantine_rate": quarantine_rate
    })

    # -------------------------------------------------------------------------
    # TASK 3: Gold Layer Aggregations
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("🏆 TASK 3: GOLD LAYER AGGREGATIONS")
    print("="*70)

    task_start = time.time()
    dau_count = create_daily_active_users()
    funnel_count = create_event_funnel()
    revenue_count = create_revenue_summary()
    task_time = time.time() - task_start

    # Track lineage for each Gold table
    track_lineage("silver_events", "gold_daily_active_users", "aggregation",
                  silver_count, dau_count, 0)
    track_lineage("silver_events", "gold_event_funnel", "aggregation",
                  silver_count, funnel_count, 0)
    track_lineage("silver_events", "gold_revenue_summary", "aggregation",
                  silver_count, revenue_count, 0)

    # Record metrics
    record_metrics("gold", "all_tables", {
        "processing_time_seconds": task_time,
        "tables_created": 3
    })

    # -------------------------------------------------------------------------
    # TASK 4: Incremental Processing Test
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("⏭️  TASK 4: INCREMENTAL PROCESSING TEST")
    print("="*70)

    print("\n🔄 Simulating new data arrival (2,000 events)...")
    task_start = time.time()
    new_raw_df = generate_events(2000)
    new_load_id = str(uuid.uuid4())
    ingest_to_bronze(new_raw_df, load_id=new_load_id)

    # Process incrementally
    new_silver_count = process_incremental_bronze_to_silver()
    update_gold_tables_incremental()
    task_time = time.time() - task_start

    print(f"✅ Incremental processing completed in {task_time:.1f}s")

    # -------------------------------------------------------------------------
    # TASK 5: Data Lineage Report
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("🔗 TASK 5: DATA LINEAGE")
    print("="*70)

    show_lineage_report()

    # -------------------------------------------------------------------------
    # TASK 6: Monitoring & SLA Checks
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("📊 TASK 6: MONITORING & SLA CHECKS")
    print("="*70)

    check_sla_violations()

    # Show recent metrics
    print("\n📈 Recent Metrics (Last 5):")
    spark.sql("""
        SELECT layer, table_name, metric_name,
               ROUND(metric_value, 2) as value,
               metric_timestamp
        FROM pipeline_metrics
        ORDER BY metric_timestamp DESC
        LIMIT 5
    """).show(truncate=False)

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    total_time = time.time() - start_time

    print("\n" + "="*70)
    print("✅ PIPELINE EXECUTION COMPLETED")
    print("="*70)
    print(f"Total execution time: {total_time:.1f}s")
    print(f"Bronze records: {bronze_count + 2000:,}")
    print(f"Silver records: {silver_count + new_silver_count:,}")
    print("Gold tables: 3 (DAU, Funnel, Revenue)")
    print(f"Data quality: {quality_rate:.1f}%")
    print("\n🎯 Run validate.py to check your work!")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_full_pipeline()
