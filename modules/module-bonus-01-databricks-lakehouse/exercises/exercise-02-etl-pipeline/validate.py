"""
Exercise 02: Production ETL Pipelines - Validation Script

This script validates your Medallion Architecture implementation across 6 tasks:
1. Bronze layer ingestion (20 points)
2. Silver layer cleaning (25 points)
3. Gold layer aggregations (20 points)
4. Incremental processing (15 points)
5. Data lineage tracking (10 points)
6. Pipeline monitoring (10 points)

Total: 100 points

Run: python validate.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import sys

# Initialize Spark
spark = SparkSession.builder \
    .appName("Exercise02-Validation") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

DATABASE_NAME = "exercise02_etl_pipeline"
score = 0
max_score = 100

def check_table_exists(table_name):
    """Check if a table exists."""
    try:
        spark.sql(f"USE {DATABASE_NAME}")
        spark.table(table_name)
        return True
    except:
        return False

def print_header(task_num, task_name):
    """Print task header."""
    print("\n" + "="*70)
    print(f"TASK {task_num}: {task_name}")
    print("="*70)

def print_result(check_name, passed, points=0, message=""):
    """Print validation result."""
    global score
    if passed:
        score += points
        status = "✅"
    else:
        status = "❌"

    points_str = f"[+{points}]" if points > 0 else ""
    msg_str = f" - {message}" if message else ""
    print(f"{status} {check_name} {points_str}{msg_str}")

# =============================================================================
# TASK 1: BRONZE LAYER VALIDATION (20 points)
# =============================================================================

print_header(1, "BRONZE LAYER INGESTION")

# Check 1.1: Bronze table exists
if check_table_exists("bronze_events"):
    print_result("Bronze table exists", True, 5)

    bronze_df = spark.table("bronze_events")
    row_count = bronze_df.count()

    # Check 1.2: Row count (should be ~10,000 initial + possible incremental)
    if row_count >= 10000:
        print_result(f"Bronze table has {row_count:,} rows", True, 5)
    else:
        print_result(f"Bronze table has only {row_count:,} rows (expected >= 10,000)", False)

    # Check 1.3: Audit columns present
    expected_columns = ["ingestion_timestamp", "source_file", "load_id"]
    actual_columns = bronze_df.columns

    audit_columns_present = all(col in actual_columns for col in expected_columns)
    if audit_columns_present:
        print_result("All audit columns present", True, 5)
    else:
        missing = [col for col in expected_columns if col not in actual_columns]
        print_result(f"Missing audit columns: {missing}", False)

    # Check 1.4: Raw data preserved (no transformations)
    if "timestamp" in actual_columns and "event_type" in actual_columns:
        sample = bronze_df.select("timestamp", "event_type").first()
        # Check if timestamp is still string format (not parsed)
        is_raw = isinstance(sample["timestamp"], str) if sample else False
        if is_raw:
            print_result("Raw data format preserved", True, 5)
        else:
            print_result("Data appears transformed (should be raw)", False)
    else:
        print_result("Required columns missing", False)
else:
    print_result("Bronze table not found", False)
    print("⚠️  Run solution.py first to create tables")

# =============================================================================
# TASK 2: SILVER LAYER VALIDATION (25 points)
# =============================================================================

print_header(2, "SILVER LAYER CLEANING & VALIDATION")

# Check 2.1: Silver table exists
if check_table_exists("silver_events"):
    print_result("Silver table exists", True, 5)

    silver_df = spark.table("silver_events")
    silver_count = silver_df.count()

    # Check 2.2: Data quality (should be ~85-95% pass rate)
    if check_table_exists("bronze_events"):
        bronze_count = spark.table("bronze_events").count()
        pass_rate = (silver_count / bronze_count * 100) if bronze_count > 0 else 0

        if 80 <= pass_rate <= 100:
            print_result(f"Quality pass rate: {pass_rate:.1f}%", True, 5,
                        f"{silver_count:,} of {bronze_count:,} records")
        else:
            print_result(f"Quality pass rate: {pass_rate:.1f}% (expected 80-100%)", False)

    # Check 2.3: Data types parsed correctly
    schema_dict = dict(silver_df.dtypes)
    timestamp_type = schema_dict.get("timestamp", "")
    revenue_type = schema_dict.get("revenue", "")

    types_correct = "timestamp" in timestamp_type.lower() and "double" in revenue_type.lower()
    if types_correct:
        print_result("Timestamp and revenue types correct", True, 5)
    else:
        print_result(f"Type issues: timestamp={timestamp_type}, revenue={revenue_type}", False)

    # Check 2.4: Deduplication applied
    dedupe_check = silver_df.groupBy("event_id").count().filter(col("count") > 1).count()
    if dedupe_check == 0:
        print_result("No duplicate event_ids found", True, 5)
    else:
        print_result(f"Found {dedupe_check} duplicate event_ids", False)

    # Check 2.5: Quarantine table exists
    if check_table_exists("silver_events_quarantine"):
        quarantine_df = spark.table("silver_events_quarantine")
        quarantine_count = quarantine_df.count()

        if quarantine_count > 0:
            print_result(f"Quarantine table exists with {quarantine_count:,} records", True, 5)

            # Show quarantine summary
            if "quality_check" in quarantine_df.columns:
                print("\n   Quarantine breakdown:")
                summary = quarantine_df.groupBy("quality_check").count() \
                    .orderBy(col("count").desc()).collect()
                for row in summary[:5]:
                    print(f"   - {row['quality_check']}: {row['count']:,}")
        else:
            print_result("Quarantine table empty (expected some rejections)", False)
    else:
        print_result("Quarantine table not found", False)
else:
    print_result("Silver table not found", False)

# =============================================================================
# TASK 3: GOLD LAYER VALIDATION (20 points)
# =============================================================================

print_header(3, "GOLD LAYER AGGREGATIONS")

gold_tables = [
    ("gold_daily_active_users", ["date", "country", "device", "unique_users", "total_events"]),
    ("gold_event_funnel", ["date", "device", "page_views", "add_to_carts", "purchases"]),
    ("gold_revenue_summary", ["date", "country", "device", "total_revenue", "transaction_count"])
]

gold_points = 6  # Points per Gold table (3 tables * ~6 points = 18)

for table_name, expected_cols in gold_tables:
    if check_table_exists(table_name):
        gold_df = spark.table(table_name)
        row_count = gold_df.count()

        # Check columns exist
        actual_cols = gold_df.columns
        cols_present = all(col in actual_cols for col in expected_cols)

        if cols_present and row_count > 0:
            print_result(f"{table_name}: {row_count:,} rows", True, gold_points)
        elif row_count == 0:
            print_result(f"{table_name}: Table empty", False)
        else:
            missing = [col for col in expected_cols if col not in actual_cols]
            print_result(f"{table_name}: Missing columns {missing}", False)
    else:
        print_result(f"{table_name} not found", False)

# Check aggregation correctness (bonus validation)
if check_table_exists("gold_daily_active_users") and check_table_exists("silver_events"):
    try:
        # Verify DAU matches silver distinct users
        dau_total_users = spark.sql("""
            SELECT SUM(unique_users) as total FROM gold_daily_active_users
        """).first()["total"]

        silver_total_users = spark.sql("""
            SELECT COUNT(DISTINCT user_id) as total FROM silver_events
        """).first()["total"]

        # DAU sum should be >= distinct users (can be higher due to same user on multiple days)
        if dau_total_users >= silver_total_users:
            print_result("DAU aggregation logic verified", True, 2)
        else:
            print_result("DAU aggregation seems incorrect", False)
    except:
        pass

# =============================================================================
# TASK 4: INCREMENTAL PROCESSING VALIDATION (15 points)
# =============================================================================

print_header(4, "INCREMENTAL PROCESSING")

# Check 4.1: Watermark table exists
if check_table_exists("pipeline_watermarks"):
    print_result("Watermark table exists", True, 5)

    watermark_df = spark.table("pipeline_watermarks")
    watermark_count = watermark_df.count()

    # Check 4.2: Watermarks recorded
    if watermark_count > 0:
        print_result(f"Watermarks recorded for {watermark_count} layer(s)", True, 5)

        # Show watermarks
        print("\n   Current watermarks:")
        watermarks = watermark_df.select("layer", "table_name", "last_processed_timestamp").collect()
        for w in watermarks[:5]:
            print(f"   - {w['layer']}/{w['table_name']}: {w['last_processed_timestamp']}")
    else:
        print_result("No watermarks recorded", False)

    # Check 4.3: Incremental logic implemented (check if MERGE was used)
    # This is inferred from table history if available
    try:
        # Check Delta table history for MERGE operations
        history = spark.sql("DESCRIBE HISTORY gold_daily_active_users LIMIT 10").collect()
        merge_operations = [h for h in history if "MERGE" in str(h["operation"]).upper()]

        if merge_operations:
            print_result("MERGE operations detected (idempotent updates)", True, 5)
        else:
            print_result("No MERGE operations found (should use MERGE for Gold updates)", False)
    except:
        print_result("Could not verify MERGE operations", False)
else:
    print_result("Watermark table not found", False)

# =============================================================================
# TASK 5: DATA LINEAGE VALIDATION (10 points)
# =============================================================================

print_header(5, "DATA LINEAGE TRACKING")

# Check 5.1: Lineage table exists
if check_table_exists("data_lineage"):
    print_result("Lineage table exists", True, 3)

    lineage_df = spark.table("data_lineage")
    lineage_count = lineage_df.count()

    # Check 5.2: Lineage records created
    if lineage_count >= 3:  # At least Bronze→Silver, Silver→Gold
        print_result(f"Lineage tracked: {lineage_count} transformation(s)", True, 4)

        # Check 5.3: Calculate data quality score
        try:
            totals = lineage_df.selectExpr(
                "SUM(records_in) as total_in",
                "SUM(records_out) as total_out",
                "SUM(records_rejected) as total_rejected"
            ).first()

            if totals["total_in"] > 0:
                quality_score = totals["total_out"] / totals["total_in"] * 100
                print_result(f"Data quality score: {quality_score:.1f}%", True, 3)
                print(f"   Records in: {totals['total_in']:,}")
                print(f"   Records out: {totals['total_out']:,}")
                print(f"   Records rejected: {totals['total_rejected']:,}")
            else:
                print_result("Cannot calculate quality score", False)
        except:
            print_result("Error calculating quality score", False)
    else:
        print_result(f"Only {lineage_count} lineage record(s) (expected >= 3)", False)
else:
    print_result("Lineage table not found", False)

# =============================================================================
# TASK 6: MONITORING VALIDATION (10 points)
# =============================================================================

print_header(6, "PIPELINE MONITORING")

# Check 6.1: Metrics table exists
if check_table_exists("pipeline_metrics"):
    print_result("Metrics table exists", True, 3)

    metrics_df = spark.table("pipeline_metrics")
    metrics_count = metrics_df.count()

    # Check 6.2: Metrics recorded
    if metrics_count >= 5:
        print_result(f"Metrics recorded: {metrics_count} metric(s)", True, 4)

        # Check for expected metric types
        metric_types = metrics_df.select("metric_name").distinct().collect()
        metric_names = [m["metric_name"] for m in metric_types]

        expected_metrics = ["row_count", "processing_time_seconds", "quality_pass_rate"]
        metrics_present = sum(1 for m in expected_metrics if m in metric_names)

        if metrics_present >= 2:
            print_result(f"Expected metric types found: {metrics_present}/3", True, 2)
        else:
            print_result("Missing expected metric types", False)
    else:
        print_result(f"Only {metrics_count} metrics recorded (expected >= 5)", False)

    # Check 6.3: Alerts table exists
    if check_table_exists("pipeline_alerts"):
        print_result("Alerts table exists", True, 1)
    else:
        print_result("Alerts table not found (optional)", False, 0)
else:
    print_result("Metrics table not found", False)

# =============================================================================
# FINAL SCORE
# =============================================================================

print("\n" + "="*70)
print("📊 VALIDATION SUMMARY")
print("="*70)

percentage = (score / max_score) * 100

print(f"\n🎯 Total Score: {score}/{max_score} ({percentage:.1f}%)\n")

if score >= 95:
    print("🎉 EXCELLENT! Production-grade implementation!")
    print("   Your ETL pipeline is ready for deployment.")
elif score >= 80:
    print("✅ GREAT JOB! Strong implementation with minor improvements needed.")
elif score >= 60:
    print("👍 GOOD WORK! Core functionality implemented, review failed checks.")
elif score >= 40:
    print("📚 PARTIAL COMPLETION. Review the requirements and try again.")
else:
    print("❌ INCOMPLETE. Please review the exercise requirements.")

print("\n" + "="*70)

# Return exit code based on score
if score >= 80:
    sys.exit(0)
else:
    sys.exit(1)
