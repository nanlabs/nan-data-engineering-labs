# Exercise 02: Production ETL Pipelines

## Overview
Build a production-grade ETL pipeline implementing the Medallion Architecture (Bronze → Silver → Gold) with data quality checks, incremental processing, and comprehensive monitoring.

**Estimated Time**: 2.5 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Exercise 01 (Delta Lake basics)

---

## Learning Objectives
By completing this exercise, you will be able to:
- Implement Medallion Architecture (Bronze, Silver, Gold layers)
- Build data quality frameworks with validation rules
- Process data incrementally using watermarks
- Implement idempotent MERGE operations
- Track data lineage across transformation layers
- Monitor pipeline health with metrics and alerts
- Create quarantine mechanisms for bad data

---

## Scenario
You're building an e-commerce analytics platform. Raw event data arrives continuously from web and mobile apps. You need to:
1. Ingest raw events into a Bronze layer (append-only)
2. Clean and validate data in a Silver layer with quality checks
3. Create business aggregations in a Gold layer
4. Process only new data incrementally (not full reloads)
5. Track lineage from raw events to final reports
6. Monitor pipeline performance and data quality

**Data**: 10,000+ user events (page_view, add_to_cart, purchase, click) with user_id, timestamp, event_type, device, country, revenue.

---

## Requirements

### Task 1: Bronze Layer - Raw Ingestion (20 min)
Ingest raw event data into the Bronze layer with audit columns.

**Requirements**:
- Create `bronze_events` Delta table
- Append-only (no updates or deletes)
- Add metadata columns:
  - `ingestion_timestamp` (TIMESTAMP) - When record was loaded
  - `source_file` (STRING) - Origin identifier
  - `load_id` (STRING) - Batch identifier for tracking

**Schema**:
```
event_id: STRING
user_id: STRING
timestamp: STRING (raw, not parsed yet)
event_type: STRING
device: STRING
country: STRING
revenue: STRING (raw, may have invalid values)
```

**Data Generation**:
- Generate 10,000 initial events
- Include some problematic data:
  - 5% with NULL user_id
  - 3% with invalid timestamps
  - 2% with negative revenue
  - 4% with unknown countries

**Success Criteria**:
- ✅ Bronze table contains exactly 10,000 rows
- ✅ All audit columns populated
- ✅ No data transformation (raw format preserved)
- ✅ Schema includes both business and metadata columns

---

### Task 2: Silver Layer - Data Cleaning (30 min)
Transform Bronze data into clean, typed Silver layer with validation.

**Requirements**:
- Create `silver_events` Delta table
- Parse and cast data types correctly:
  - `timestamp` → TIMESTAMP
  - `revenue` → DOUBLE
- Standardize values:
  - `country` → uppercase
  - `event_type` → lowercase
- Deduplicate by (event_id, timestamp)

**Data Quality Rules** (implement 4 checks):
1. `user_id` must not be NULL
2. `timestamp` must be valid and within last 365 days
3. `revenue` must be >= 0
4. `country` must be in known list (US, UK, CA, DE, FR, AU, JP, etc.)

**Quarantine Handling**:
- Create `silver_events_quarantine` table
- Store rejected records with rejection reason
- Add `quality_check_failed` column indicating which rule failed

**Success Criteria**:
- ✅ Silver table has ~9,000 clean records (90% pass rate)
- ✅ ~1,000 records in quarantine table
- ✅ All Silver records pass quality checks
- ✅ Timestamps properly parsed
- ✅ Quarantine records have rejection reasons

---

### Task 3: Gold Layer - Business Aggregations (30 min)
Create three Gold tables with business metrics.

**Gold Table 1: Daily Active Users**
- Table: `gold_daily_active_users`
- Dimensions: date, country, device
- Metrics: unique_users, total_events
- Grain: One row per date/country/device

**Gold Table 2: Event Funnel**
- Table: `gold_event_funnel`
- Dimensions: date, device
- Metrics:
  - page_views (count)
  - add_to_carts (count)
  - purchases (count)
  - cart_conversion_rate (add_to_carts / page_views)
  - purchase_conversion_rate (purchases / page_views)
- Grain: One row per date/device

**Gold Table 3: Revenue by Region**
- Table: `gold_revenue_summary`
- Dimensions: date, country, device
- Metrics:
  - total_revenue
  - transaction_count
  - avg_transaction_value
  - top_users (array of top 5 users by revenue)
- Grain: One row per date/country/device

**Success Criteria**:
- ✅ All 3 Gold tables created
- ✅ Aggregations mathematically correct
- ✅ Conversion rates between 0 and 1
- ✅ DAU counts match distinct users in Silver
- ✅ Revenue totals sum correctly

---

### Task 4: Incremental Processing (25 min)
Implement incremental processing to handle new data efficiently.

**Requirements**:
- Use watermark-based processing (track last processed timestamp)
- Create `pipeline_watermarks` table:
  - `layer` (bronze/silver/gold)
  - `table_name`
  - `last_processed_timestamp`
  - `updated_at`

**Incremental Logic**:
1. Bronze → Silver: Process only events after last Silver watermark
2. Silver → Gold: Process only events after last Gold watermark
3. Use MERGE (not overwrite) to update Gold tables

**Idempotency**:
- Running pipeline twice with same data should not create duplicates
- Use MERGE with proper key matching

**Testing**:
1. Load initial 10,000 events (full load)
2. Load 2,000 new events (incremental)
3. Verify only 2,000 new records processed
4. Re-run incremental load
5. Verify no duplicates created

**Success Criteria**:
- ✅ Watermark table tracks processing state
- ✅ Only new data processed (not full scan)
- ✅ Idempotent (safe to re-run)
- ✅ Processing time < 10 seconds for 2,000 incremental events
- ✅ Gold tables updated via MERGE (not overwrite)

---

### Task 5: Data Lineage (15 min)
Track data lineage across the Medallion Architecture.

**Requirements**:
- Create `data_lineage` table:
  - `lineage_id` (STRING)
  - `source_table` (STRING)
  - `target_table` (STRING)
  - `transformation_type` (STRING): 'ingestion', 'cleaning', 'aggregation'
  - `records_in` (LONG)
  - `records_out` (LONG)
  - `records_rejected` (LONG)
  - `execution_timestamp` (TIMESTAMP)

**Lineage Tracking**:
1. Source → Bronze: Track ingestion (10,000 in, 10,000 out, 0 rejected)
2. Bronze → Silver: Track cleaning (10,000 in, ~9,000 out, ~1,000 rejected)
3. Silver → Gold: Track aggregations for each Gold table

**Visualization**:
- Query lineage to show full Bronze → Silver → Gold path
- Calculate data quality score: (records_out / records_in) * 100

**Success Criteria**:
- ✅ Lineage recorded for all transformations
- ✅ Can trace event from Bronze to Gold
- ✅ Records counts accurate
- ✅ Data quality score calculated (should be ~90%)

---

### Task 6: Pipeline Monitoring (20 min)
Implement comprehensive monitoring and alerting.

**Requirements**:
- Create `pipeline_metrics` table:
  - `metric_timestamp` (TIMESTAMP)
  - `layer` (bronze/silver/gold)
  - `table_name` (STRING)
  - `metric_name` (STRING)
  - `metric_value` (DOUBLE)

**Metrics to Track**:
1. **Volume Metrics**:
   - Records processed per run
   - Records rejected per run
   - Total table row counts

2. **Performance Metrics**:
   - Processing duration (seconds)
   - Records per second throughput
   - Query execution time

3. **Quality Metrics**:
   - Data quality pass rate (%)
   - Quarantine rate (%)
   - Null value percentage

4. **SLA Metrics**:
   - Data freshness (minutes since last update)
   - Pipeline lag (ingestion time - event time)

**Alerting**:
- Define SLA thresholds:
  - Quality pass rate < 85% → Alert
  - Processing time > 5 minutes → Alert
  - Quarantine rate > 15% → Alert
- Create `pipeline_alerts` table for violations

**Dashboard Queries**:
Write 5 SQL queries for monitoring dashboard:
1. Last 7 days processing volume
2. Data quality trends (daily pass rate)
3. Performance trends (processing time)
4. Current SLA status
5. Top rejection reasons

**Success Criteria**:
- ✅ All metrics tracked for each run
- ✅ SLA alerts triggered correctly
- ✅ Dashboard queries return data
- ✅ Can identify performance bottlenecks
- ✅ Can track quality degradation over time

---

## Hints

<details>
<summary>Hint 1: Bronze Layer with Audit Columns</summary>

```python
from pyspark.sql.functions import current_timestamp, lit, uuid

# Add audit columns during ingestion
bronze_df = raw_df.select(
    "*",
    current_timestamp().alias("ingestion_timestamp"),
    lit("web_events_api").alias("source_file"),
    uuid().alias("load_id")
)

# Append to Bronze (never overwrite)
bronze_df.write.format("delta") \
    .mode("append") \
    .saveAsTable("bronze_events")
```
</details>

<details>
<summary>Hint 2: Data Quality Framework</summary>

```python
from pyspark.sql.functions import col, when, to_timestamp

# Define quality rules
quality_df = bronze_df.withColumn(
    "quality_check",
    when(col("user_id").isNull(), "user_id_null")
    .when(to_timestamp(col("timestamp")).isNull(), "invalid_timestamp")
    .when(col("revenue").cast("double") < 0, "negative_revenue")
    .when(~col("country").isin(valid_countries), "unknown_country")
    .otherwise("passed")
)

# Split into passed and quarantine
passed_df = quality_df.filter(col("quality_check") == "passed")
quarantine_df = quality_df.filter(col("quality_check") != "passed")

# Write to Silver and Quarantine
passed_df.write.format("delta").mode("overwrite").saveAsTable("silver_events")
quarantine_df.write.format("delta").mode("append").saveAsTable("silver_events_quarantine")
```
</details>

<details>
<summary>Hint 3: Incremental Processing with Watermarks</summary>

```python
from delta.tables import DeltaTable

# Get last processed timestamp
last_watermark = spark.sql("""
    SELECT max(last_processed_timestamp) as watermark
    FROM pipeline_watermarks
    WHERE layer = 'silver' AND table_name = 'silver_events'
""").first()["watermark"]

# Process only new records
new_records = spark.sql(f"""
    SELECT * FROM bronze_events
    WHERE ingestion_timestamp > '{last_watermark}'
""")

# Update watermark after processing
new_watermark = new_records.agg({"ingestion_timestamp": "max"}).first()[0]
spark.sql(f"""
    MERGE INTO pipeline_watermarks AS target
    USING (SELECT '{new_watermark}' as ts) AS source
    ON target.layer = 'silver' AND target.table_name = 'silver_events'
    WHEN MATCHED THEN UPDATE SET last_processed_timestamp = source.ts
""")
```
</details>

<details>
<summary>Hint 4: Gold Layer MERGE for Idempotency</summary>

```python
# Daily aggregation
daily_aggregation = silver_df.groupBy("date", "country", "device").agg(
    countDistinct("user_id").alias("unique_users"),
    count("*").alias("total_events")
)

# MERGE into Gold (idempotent)
gold_table = DeltaTable.forName(spark, "gold_daily_active_users")

gold_table.alias("target").merge(
    daily_aggregation.alias("source"),
    "target.date = source.date AND target.country = source.country AND target.device = source.device"
).whenMatchedUpdate(set={
    "unique_users": "source.unique_users",
    "total_events": "source.total_events"
}).whenNotMatchedInsertAll().execute()
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-02-etl-pipeline
python validate.py
```

**Expected Output**:
```
✅ Task 1: Bronze layer created (10,000 raw events with audit columns)
✅ Task 2: Silver layer cleaned (9,046 records, 954 quarantined)
   - user_id nulls: 500 rejected
   - Invalid timestamps: 300 rejected
   - Negative revenue: 154 rejected
✅ Task 3: Gold tables created (3 tables, aggregations correct)
   - DAU: 1,234 unique users on 2026-03-09
   - Funnel: 15.2% cart conversion, 3.8% purchase conversion
   - Revenue: $45,321.50 total
✅ Task 4: Incremental processing (2,000 new events processed in 4.2s)
   - Idempotent: No duplicates on re-run
✅ Task 5: Data lineage tracked (3 transformations, 90.5% quality score)
✅ Task 6: Monitoring active (24 metrics tracked, 0 SLA violations)

🎉 Exercise 02 Complete! Total Score: 100/100
```

---

## Deliverables
Submit the following:
1. `solution.py` - Complete medallion pipeline implementation
2. Data quality report (quarantine summary by rejection reason)
3. Lineage diagram (Bronze → Silver → Gold flow)
4. Monitoring dashboard (5 SQL queries with results)

---

## Resources
- [Medallion Architecture Guide](https://www.databricks.com/glossary/medallion-architecture)
- [Delta Lake MERGE](https://docs.delta.io/latest/delta-update.html#upsert-into-a-table-using-merge)
- Notebook: `notebooks/02-medallion-architecture.py`
- Diagram: `assets/diagrams/medallion-pipeline.mmd`
- Sample data generator: `scripts/generate_events.py`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 03: Unity Catalog Governance (requires Enterprise edition)
- ✅ Exercise 04: Real-Time Streaming
- Review Module 06: ETL Fundamentals for batch processing patterns
