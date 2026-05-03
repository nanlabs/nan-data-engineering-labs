"""
Exercise 04: Real-Time Streaming Analytics - Validation Script
===============================================================

Validates the implementation of all streaming tasks.

Checks:
- Task 1: Bronze stream running and ingesting data
- Task 2: Silver transformations applied correctly
- Task 3: Windowed aggregations working
- Task 4: Watermarking configured
- Task 5: Streaming MERGE producing results
- Task 6: Monitoring metrics captured

Author: Training Team
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import os


# =============================================================================
# Setup
# =============================================================================

def setup_spark():
    """Initialize Spark session"""
    spark = SparkSession.builder \
        .appName("Exercise04-Validation") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")
    spark.sql("USE streaming_exercise")
    return spark


# =============================================================================
# Validation Functions
# =============================================================================

def validate_task1_bronze_stream(spark):
    """Validate Task 1: Stream to Bronze"""
    print("\n" + "=" * 80)
    print("Task 1: Stream to Bronze")
    print("=" * 80)

    score = 0
    max_score = 20

    # Check 1: Bronze table exists
    try:
        bronze_df = spark.read.format("delta").table("bronze_ride_events")
        count = bronze_df.count()
        print(f"✅ Bronze table exists with {count} rows")
        score += 5

        # Check 2: Has expected schema
        expected_cols = ["event_id", "event_type", "timestamp", "user_id", "ride_id",
                        "latitude", "longitude", "city"]
        actual_cols = bronze_df.columns
        missing = [c for c in expected_cols if c not in actual_cols]

        if not missing:
            print(f"✅ Schema is correct ({len(actual_cols)} columns)")
            score += 5
        else:
            print(f"❌ Missing columns: {missing}")

        # Check 3: Data is being ingested
        if count > 100:
            print(f"✅ Sufficient data ingested ({count} rows)")
            score += 5
        else:
            print(f"⚠️  Low data volume ({count} rows, expected > 100)")
            score += 2

        # Check 4: Checkpoint exists
        checkpoint_path = "/tmp/exercise04/checkpoints/bronze"
        if os.path.exists(checkpoint_path):
            print(f"✅ Checkpoint location exists: {checkpoint_path}")
            score += 5
        else:
            print(f"❌ Checkpoint location missing: {checkpoint_path}")

    except Exception as e:
        print(f"❌ Bronze table validation failed: {e}")

    print(f"\n📊 Task 1 Score: {score}/{max_score}")
    return score


def validate_task2_silver_transformations(spark):
    """Validate Task 2: Stream Transformations"""
    print("\n" + "=" * 80)
    print("Task 2: Stream Transformations (Bronze → Silver)")
    print("=" * 80)

    score = 0
    max_score = 20

    try:
        # Check 1: Silver table exists
        silver_df = spark.read.format("delta").table("silver_ride_events")
        count = silver_df.count()
        print(f"✅ Silver table exists with {count} rows")
        score += 5

        # Check 2: Enrichment columns added
        enrichment_cols = ["processing_latency_seconds", "is_late_event", "event_date", "event_hour"]
        actual_cols = silver_df.columns
        missing_enrichment = [c for c in enrichment_cols if c not in actual_cols]

        if not missing_enrichment:
            print(f"✅ Enrichment columns present: {', '.join(enrichment_cols)}")
            score += 5
        else:
            print(f"❌ Missing enrichment columns: {missing_enrichment}")
            score += 2

        # Check 3: Data quality - no invalid coordinates
        invalid_coords = silver_df.filter(
            ~col("latitude").between(-90, 90) |
            ~col("longitude").between(-180, 180)
        ).count()

        if invalid_coords == 0:
            print("✅ No invalid coordinates in Silver (data quality enforced)")
            score += 5
        else:
            print(f"⚠️  Found {invalid_coords} invalid coordinates")
            score += 2

        # Check 4: Quarantine table exists
        try:
            quarantine_df = spark.read.format("delta").table("silver_ride_events_quarantine")
            quarantine_count = quarantine_df.count()
            print(f"✅ Quarantine table exists with {quarantine_count} rejected records")
            score += 5
        except:
            print("❌ Quarantine table not found")

    except Exception as e:
        print(f"❌ Silver table validation failed: {e}")

    print(f"\n📊 Task 2 Score: {score}/{max_score}")
    return score


def validate_task3_windowed_aggregations(spark):
    """Validate Task 3: Windowed Aggregations"""
    print("\n" + "=" * 80)
    print("Task 3: Windowed Aggregations")
    print("=" * 80)

    score = 0
    max_score = 20

    # Check Gold Table 1: Event Funnel
    try:
        funnel_df = spark.read.format("delta").table("gold_event_funnel_5min")
        funnel_count = funnel_df.count()
        print(f"✅ gold_event_funnel_5min exists with {funnel_count} windows")
        score += 7

        # Validate has required columns
        required = ["window_start", "window_end", "total_requests", "total_accepts",
                   "acceptance_rate", "completion_rate"]
        if all(c in funnel_df.columns for c in required):
            print(f"   Schema correct: {', '.join(required)}")

            # Check rates are reasonable
            sample = funnel_df.select("acceptance_rate", "completion_rate").first()
            if sample:
                if 0 <= sample["acceptance_rate"] <= 100:
                    print(f"   Acceptance rate: {sample['acceptance_rate']:.1f}%")

    except Exception as e:
        print(f"❌ gold_event_funnel_5min validation failed: {e}")

    # Check Gold Table 2: City Demand
    try:
        demand_df = spark.read.format("delta").table("gold_city_demand_5min")
        demand_count = demand_df.count()
        print(f"✅ gold_city_demand_5min exists with {demand_count} windows")
        score += 7

        # Check has geographic buckets
        if "latitude_bucket" in demand_df.columns and "longitude_bucket" in demand_df.columns:
            print("   Geographic bucketing: ✅")

    except Exception as e:
        print(f"❌ gold_city_demand_5min validation failed: {e}")

    # Check Gold Table 3: Active Rides
    try:
        active_df = spark.read.format("delta").table("gold_active_rides_5min")
        active_count = active_df.count()
        print(f"✅ gold_active_rides_5min exists with {active_count} windows")
        score += 6

    except Exception as e:
        print(f"❌ gold_active_rides_5min validation failed: {e}")

    print(f"\n📊 Task 3 Score: {score}/{max_score}")
    return score


def validate_task4_watermarking(spark):
    """Validate Task 4: Watermarking"""
    print("\n" + "=" * 80)
    print("Task 4: Watermarking")
    print("=" * 80)

    score = 0
    max_score = 15

    # Check if streams have watermark configured
    active_streams = [s for s in spark.streams.active]

    if not active_streams:
        print("⚠️  No active streams found to check watermark")
        print("   Run solution.py first to start streams")
    else:
        print(f"✅ Found {len(active_streams)} active streaming queries")
        score += 5

        watermarked = 0
        for query in active_streams:
            try:
                progress = query.lastProgress
                if progress and "eventTime" in progress:
                    watermark = progress["eventTime"].get("watermark")
                    if watermark:
                        watermarked += 1
                        print(f"   Query {query.name or query.id[:8]}: Watermark = {watermark}")
            except:
                pass

        if watermarked > 0:
            print(f"✅ Found {watermarked} queries with watermark configured")
            score += 10
        else:
            print("❌ No queries have watermark configured")

    # Check if late events are being tracked
    try:
        silver_df = spark.read.format("delta").table("silver_ride_events")
        if "is_late_event" in silver_df.columns:
            late_count = silver_df.filter(col("is_late_event")).count()
            total = silver_df.count()
            late_pct = (late_count / total * 100) if total > 0 else 0
            print(f"✅ Late event tracking: {late_count} late events ({late_pct:.1f}%)")
    except:
        pass

    print(f"\n📊 Task 4 Score: {score}/{max_score}")
    return score


def validate_task5_streaming_merge(spark):
    """Validate Task 5: Streaming MERGE"""
    print("\n" + "=" * 80)
    print("Task 5: Streaming MERGE (foreachBatch UPSERT)")
    print("=" * 80)

    score = 0
    max_score = 15

    try:
        # Check 1: User profiles table exists
        profiles_df = spark.read.format("delta").table("gold_user_profiles")
        count = profiles_df.count()
        print(f"✅ gold_user_profiles table exists with {count} users")
        score += 5

        # Check 2: Has expected schema
        required_cols = ["user_id", "first_ride_date", "last_ride_date", "total_rides",
                        "total_spent", "last_updated"]
        missing = [c for c in required_cols if c not in profiles_df.columns]

        if not missing:
            print(f"✅ Schema correct: {', '.join(required_cols)}")
            score += 5
        else:
            print(f"❌ Missing columns: {missing}")

        # Check 3: Aggregations are reasonable
        if count > 0:
            sample = profiles_df.select("total_rides", "total_spent").first()
            if sample and sample["total_rides"] > 0:
                avg_fare = sample["total_spent"] / sample["total_rides"]
                print(f"✅ User aggregations working (avg fare: ${avg_fare:.2f})")
                score += 5

        # Display sample profiles
        print("\nSample user profiles:")
        profiles_df.select("user_id", "total_rides", "total_spent", "last_ride_date") \
            .orderBy(desc("total_rides")) \
            .limit(3) \
            .show(truncate=False)

    except Exception as e:
        print(f"❌ User profiles validation failed: {e}")

    print(f"\n📊 Task 5 Score: {score}/{max_score}")
    return score


def validate_task6_monitoring(spark):
    """Validate Task 6: Monitoring"""
    print("\n" + "=" * 80)
    print("Task 6: Monitoring")
    print("=" * 80)

    score = 0
    max_score = 10

    try:
        # Check 1: Metrics table exists
        metrics_df = spark.read.format("delta").table("streaming_metrics")
        count = metrics_df.count()
        print(f"✅ streaming_metrics table exists with {count} metric records")
        score += 5

        # Check 2: Has required metric columns
        required = ["query_id", "query_name", "input_rate", "process_rate",
                   "batch_duration_ms", "watermark"]
        missing = [c for c in required if c not in metrics_df.columns]

        if not missing:
            print("✅ Metric schema correct")
            score += 3
        else:
            print(f"❌ Missing metric columns: {missing}")

        # Check 3: Recent metrics captured
        recent = metrics_df.filter(
            col("metric_timestamp") >= current_timestamp() - expr("INTERVAL 10 MINUTES")
        ).count()

        if recent > 0:
            print(f"✅ Recent metrics captured ({recent} records)")
            score += 2
        else:
            print("⚠️  No recent metrics (run for longer)")

    except Exception as e:
        print(f"❌ Monitoring validation failed: {e}")

    # Show active queries
    active_streams = [s for s in spark.streams.active]
    if active_streams:
        print(f"\n📊 Active streaming queries: {len(active_streams)}")
        for query in active_streams:
            status = query.status
            print(f"   - {query.name or query.id[:8]}: {status.get('message', 'Running')}")

    print(f"\n📊 Task 6 Score: {score}/{max_score}")
    return score


# =============================================================================
# Summary Report
# =============================================================================

def generate_summary_report(spark, scores):
    """Generate comprehensive validation report"""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    total_score = sum(scores.values())
    max_total = sum([20, 20, 20, 15, 15, 10])

    print("\nTask Breakdown:")
    print(f"  Task 1 - Bronze Stream:           {scores['task1']}/20")
    print(f"  Task 2 - Silver Transformations:  {scores['task2']}/20")
    print(f"  Task 3 - Windowed Aggregations:   {scores['task3']}/20")
    print(f"  Task 4 - Watermarking:             {scores['task4']}/15")
    print(f"  Task 5 - Streaming MERGE:          {scores['task5']}/15")
    print(f"  Task 6 - Monitoring:               {scores['task6']}/10")
    print("  " + "-" * 40)
    print(f"  TOTAL:                             {total_score}/{max_total}")

    percentage = (total_score / max_total * 100)
    print(f"\n  Final Score: {percentage:.1f}%")

    # Grade
    if percentage >= 90:
        grade = "🎉 EXCELLENT"
    elif percentage >= 80:
        grade = "✅ GOOD"
    elif percentage >= 70:
        grade = "⚠️  PASSING"
    else:
        grade = "❌ NEEDS WORK"

    print(f"  Grade: {grade}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if scores['task1'] < 20:
        print("❗ Task 1: Ensure Bronze stream is running and checkpoints are configured")

    if scores['task2'] < 20:
        print("❗ Task 2: Add all enrichment columns and implement quarantine stream")

    if scores['task3'] < 20:
        print("❗ Task 3: Create all 3 Gold tables with proper windowed aggregations")

    if scores['task4'] < 15:
        print("❗ Task 4: Configure watermarking on all streaming aggregations")

    if scores['task5'] < 15:
        print("❗ Task 5: Implement foreachBatch with Delta MERGE for user profiles")

    if scores['task6'] < 10:
        print("❗ Task 6: Create monitoring metrics table and track query performance")

    if percentage >= 90:
        print("\n🎉 Excellent work! Your streaming pipeline is production-ready!")
        print("\nNext Steps:")
        print("  - Test failure recovery (stop and restart queries)")
        print("  - Monitor long-term performance (run for 1+ hour)")
        print("  - Implement alerting on SLA violations")
        print("  - Scale up data rate (increase rowsPerSecond)")


# =============================================================================
# Main Validation
# =============================================================================

def main():
    """Main validation orchestration"""
    print("=" * 80)
    print("Exercise 04: Real-Time Streaming Analytics - VALIDATION")
    print("=" * 80)

    spark = setup_spark()

    # Run validations
    scores = {
        'task1': validate_task1_bronze_stream(spark),
        'task2': validate_task2_silver_transformations(spark),
        'task3': validate_task3_windowed_aggregations(spark),
        'task4': validate_task4_watermarking(spark),
        'task5': validate_task5_streaming_merge(spark),
        'task6': validate_task6_monitoring(spark)
    }

    # Generate report
    generate_summary_report(spark, scores)

    print("\n" + "=" * 80)
    print("Validation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
