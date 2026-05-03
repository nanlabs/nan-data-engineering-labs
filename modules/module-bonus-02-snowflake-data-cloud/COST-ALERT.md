# 💰 Snowflake Cost Alert & Management

> ⚠️ **IMPORTANT**: This module uses Snowflake, a **commercial cloud data platform** with **pay-per-use pricing**. While Snowflake offers a **FREE 30-day trial with $400 credits** (enough for all exercises), you must understand costs and setup monitoring to avoid unexpected charges.

## 📋 Table of Contents

- [Trial Account (Recommended)](#trial-account-recommended)
- [Cost Structure Overview](#cost-structure-overview)
- [Warehouse Sizing & Costs](#warehouse-sizing--costs)
- [Exercise Cost Estimates](#exercise-cost-estimates)
- [Setting Up Resource Monitors](#setting-up-resource-monitors)
- [Cost Optimization Strategies](#cost-optimization-strategies)
- [Credit Tracking & Monitoring](#credit-tracking--monitoring)
- [Trial Expiration & Next Steps](#trial-expiration--next-steps)

---

## 🎁 Trial Account (Recommended)

### Free Trial Benefits

Snowflake offers a **30-day free trial** that is **perfect for this module**:

```
✅ $400 USD in free credits
✅ 30 days to complete all exercises
✅ Full enterprise features (no limitations)
✅ All cloud providers supported (AWS, Azure, GCP)
✅ No credit card required for signup
✅ Automatic trial conversion (opt-in)
```

### Trial Signup

1. **Visit**: https://signup.snowflake.com/
2. **Choose Cloud Provider**: AWS, Azure, or GCP
3. **Select Region**: Choose nearest region (e.g., `us-east-1`, `eu-west-1`)
4. **Provide Details**: Email, name, company (can use "Personal Learning")
5. **Verify Email**: Check inbox for verification link
6. **Account Created**: Receive account URL (e.g., `https://abc12345.snowflakecomputing.com`)

### Trial Coverage for This Module

```
Total Estimated Cost: $15-25 USD
Trial Credits: $400 USD
Coverage: 16-26x the needed amount
Conclusion: ALL EXERCISES ARE FREE WITH TRIAL
```

> 💡 **Pro Tip**: Complete all exercises within the 30-day trial period to avoid any charges.

---

## 💵 Cost Structure Overview

Snowflake has three main cost components:

### 1. Compute (Virtual Warehouses)

**Pricing Model**: Pay per credit consumed

```
Cost per Credit:
- Standard Edition: $2.00/credit
- Enterprise Edition: $3.00/credit
- Business Critical: $4.00/credit

Billing:
- Per-second billing (60-second minimum)
- Charged when warehouse is RUNNING
- Auto-suspend stops charges immediately
```

**Cost Formula**:

```
Cost = (Credits per Hour × Hours Running) × Price per Credit
```

### 2. Storage

**Pricing Model**: Pay per TB per month

```
Storage Costs (Monthly):
- Standard Tier: $23/TB (AWS), $25/TB (Azure/GCP)
- Compressed: ~10:1 ratio (1TB raw ≈ 100GB stored)

Included:
- Time Travel storage (1-90 days)
- Fail-safe storage (7 days)

Example:
- 50GB data → ~5GB compressed → $0.12/month
- 1TB data → ~100GB compressed → $2.30/month
```

### 3. Cloud Services

**Pricing Model**: Free if <10% of compute

```
Cloud Services Layer:
- Query optimization & planning
- Authentication & security
- Metadata operations
- Infrastructure management

Cost:
- FREE if <10% of daily compute spend
- Only charged if exceeds 10% threshold
- Typical workloads: 2-5% (always free)
```

### Total Cost Example

Typical learning workload (per day):

```
Component          Usage           Cost
─────────────────────────────────────────
Compute (X-Small)  2 hours/day     $4-6
Storage            50GB            $0.004
Cloud Services     Free (<10%)     $0
─────────────────────────────────────────
TOTAL PER DAY                      $4-6
TOTAL FOR MODULE (5 days)          $20-30
```

**With Trial**: $0 (covered by $400 credits)

---

## 📊 Warehouse Sizing & Costs

### Warehouse Size Table

| Size      | Credits/Hour | Clusters | Relative Power | Use Case                    | Hourly Cost*  |
|-----------|--------------|----------|----------------|-----------------------------|--------------:|
| X-Small   | 1            | 1        | 1x             | Dev, small queries          | $2-4          |
| Small     | 2            | 1        | 2x             | Light ETL, dashboards       | $4-8          |
| Medium    | 4            | 1        | 4x             | Standard ETL                | $8-16         |
| Large     | 8            | 1        | 8x             | Heavy ETL, ML               | $16-32        |
| X-Large   | 16           | 1        | 16x            | Very heavy workloads        | $32-64        |
| 2X-Large  | 32           | 1        | 32x            | Massive data processing     | $64-128       |
| 3X-Large  | 64           | 1        | 64x            | Enterprise batch jobs       | $128-256      |
| 4X-Large  | 128          | 1        | 128x           | Extreme workloads           | $256-512      |
| 5X-Large  | 256          | 1        | 256x           | Rare, specialized           | $512-1024     |
| 6X-Large  | 512          | 1        | 512x           | Rare, specialized           | $1024-2048    |

\* Cost range: Standard ($2/credit) to Business Critical ($4/credit)

### Multi-Cluster Warehouses

```sql
-- Multi-cluster auto-scaling (Enterprise+)
CREATE WAREHOUSE bi_warehouse WITH
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 5
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    SCALING_POLICY = 'STANDARD';

-- Cost scaling:
-- Min: 1 cluster = 1 × credits/hour
-- Max: 5 clusters = 5 × credits/hour
-- Auto-scales based on query queue
```

### Warehouse Sizing Recommendations

**Development & Learning (This Module)**:
```
Size: X-Small (1 credit/hour)
Auto-Suspend: 60-300 seconds
Auto-Resume: TRUE
Multi-Cluster: Not needed
Expected Cost: $2-6/hour × 0.5-2 hours/day = $1-12/day
```

**Production Workloads**:
```
ETL (Batch):     Small to Large (2-8 credits/hour)
BI Dashboards:   X-Small to Small (1-2 credits/hour)
Data Science:    Medium to X-Large (4-16 credits/hour)
Streaming:       X-Small to Small (1-2 credits/hour)
```

---

## 💰 Exercise Cost Estimates

### Per-Exercise Breakdown

| Exercise | Description                    | Warehouse | Runtime  | Credits | Cost*     |
|----------|--------------------------------|-----------|----------|---------|----------:|
| **01**   | Basic SQL & Warehouses         | X-Small   | 15 min   | 0.25    | $0.50-1   |
| **02**   | Zero-Copy Cloning              | X-Small   | 20 min   | 0.33    | $0.66-1.32|
| **03**   | Time Travel & Recovery         | X-Small   | 15 min   | 0.25    | $0.50-1   |
| **04**   | Data Loading (COPY INTO)       | Small     | 30 min   | 1.00    | $2-4      |
| **05**   | Streams & Tasks (CDC)          | X-Small   | 25 min   | 0.42    | $0.84-1.68|
| **06**   | Snowpipe Ingestion             | Serverless| 20 min   | 0.30    | $0.60-1.20|
| **07**   | External Tables                | X-Small   | 15 min   | 0.25    | $0.50-1   |
| **08**   | Secure Data Sharing            | X-Small   | 20 min   | 0.33    | $0.66-1.32|
| **09**   | Performance Optimization       | Small     | 30 min   | 1.00    | $2-4      |
| **10**   | Cost Monitoring & Governance   | X-Small   | 15 min   | 0.25    | $0.50-1   |
| -        | Storage (50GB compressed)      | -         | 30 days  | -       | $0.50     |
| -        | Cloud Services                 | -         | -        | -       | $0 (free) |

**Total Estimated Cost**: $15-25 USD (Standard Edition)
**With Trial**: **$0** (covered by $400 credits)

\* Range: Standard ($2/credit) to Business Critical ($4/credit)

### Cost-Saving Tips Per Exercise

1. **Exercise 01-03, 05, 07-08, 10**: Use X-Small warehouse, auto-suspend 60s
2. **Exercise 04, 09**: Use Small warehouse (needed for performance), suspend immediately after
3. **Exercise 06**: Snowpipe is serverless (pay only for files processed)
4. **All Exercises**: Enable query result caching (free for 24 hours)

---

## 🛡️ Setting Up Resource Monitors

Resource Monitors prevent unexpected costs by tracking credit usage and triggering alerts/actions.

### Step 1: Create Account-Level Monitor (Trial)

```sql
-- Use ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Create resource monitor for trial credits
CREATE RESOURCE MONITOR trial_monitor WITH
    CREDIT_QUOTA = 400              -- $400 trial credits
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 50 PERCENT DO NOTIFY      -- Alert at 50% ($200)
        ON 75 PERCENT DO NOTIFY      -- Alert at 75% ($300)
        ON 90 PERCENT DO NOTIFY      -- Alert at 90% ($360)
        ON 100 PERCENT DO SUSPEND    -- Suspend all at 100%
        ON 120 PERCENT DO SUSPEND_IMMEDIATE; -- Emergency stop

-- Apply to account (all warehouses)
ALTER ACCOUNT SET RESOURCE_MONITOR = trial_monitor;
```

### Step 2: Create Warehouse-Specific Monitor

```sql
-- Create monitor for specific warehouse
CREATE RESOURCE MONITOR training_wh_monitor WITH
    CREDIT_QUOTA = 50               -- $50-150 limit
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 75 PERCENT DO NOTIFY
        ON 90 PERCENT DO SUSPEND
        ON 100 PERCENT DO SUSPEND_IMMEDIATE;

-- Create warehouse with monitor
CREATE WAREHOUSE training_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60               -- 60 seconds
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    RESOURCE_MONITOR = training_wh_monitor;
```

### Step 3: Set Up Email Notifications

```sql
-- Create notification integration (requires ACCOUNTADMIN)
CREATE NOTIFICATION INTEGRATION email_integration
    TYPE = EMAIL
    ENABLED = TRUE;

-- Notifications are sent to account admin emails
-- Configure additional emails in Snowflake UI:
-- Account → Notifications → Add Email
```

### Step 4: Daily Budget Monitor

```sql
-- Daily budget monitor (aggressive cost control)
CREATE RESOURCE MONITOR daily_training_monitor WITH
    CREDIT_QUOTA = 5                -- $5-15/day limit
    FREQUENCY = DAILY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 80 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND;

-- Apply to training warehouse
ALTER WAREHOUSE training_wh SET RESOURCE_MONITOR = daily_training_monitor;
```

### Monitor Management

```sql
-- View all resource monitors
SHOW RESOURCE MONITORS;

-- Check monitor usage
SELECT *
FROM TABLE(INFORMATION_SCHEMA.RESOURCE_MONITOR_USAGE(
    DATE_RANGE_START => DATEADD('day', -7, CURRENT_DATE())
));

-- Modify monitor
ALTER RESOURCE MONITOR trial_monitor SET CREDIT_QUOTA = 300;

-- Suspend monitor temporarily
ALTER RESOURCE MONITOR trial_monitor SET FREQUENCY = NEVER;

-- Resume monitor
ALTER RESOURCE MONITOR trial_monitor SET FREQUENCY = MONTHLY;

-- Drop monitor
DROP RESOURCE MONITOR IF EXISTS old_monitor;
```

---

## 🎯 Cost Optimization Strategies

### 1. Warehouse Management

#### Auto-Suspend Configuration

```sql
-- Aggressive auto-suspend (development)
CREATE WAREHOUSE dev_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60               -- 1 minute (recommended)
    AUTO_RESUME = TRUE;

-- Standard auto-suspend (production BI)
CREATE WAREHOUSE bi_wh WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300              -- 5 minutes
    AUTO_RESUME = TRUE;

-- Minimal auto-suspend (heavy ETL)
CREATE WAREHOUSE etl_wh WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 600              -- 10 minutes (batch job)
    AUTO_RESUME = TRUE;
```

**Savings**: Auto-suspend at 60s vs. always-on = **up to 99% savings** during idle periods.

#### Right-Sizing Warehouses

```sql
-- Start small, scale up if needed
CREATE WAREHOUSE analysis_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL';     -- Start here

-- Monitor query performance
SELECT
    query_id,
    warehouse_size,
    execution_time / 1000 AS execution_seconds,
    bytes_scanned,
    bytes_spilled_to_local_storage,
    bytes_spilled_to_remote_storage  -- Sign to scale up
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE warehouse_name = 'ANALYSIS_WH'
    AND execution_status = 'SUCCESS'
ORDER BY start_time DESC
LIMIT 20;

-- Scale up only if:
-- 1. Spilling to remote storage (disk)
-- 2. Queries timeout frequently
-- 3. Execution time unacceptable
```

**Savings**: X-Small vs. Medium (unnecessary) = **75% cost reduction**.

### 2. Leverage Zero-Copy Cloning

```sql
-- Clone production for development (instant, free initially)
CREATE DATABASE dev_database CLONE prod_database;

-- Clone table for experiments (no storage cost until modified)
CREATE TABLE experiments.customer_test CLONE prod.customers;

-- Clone at historical point (Time Travel)
CREATE TABLE analysis.orders_backup
    CLONE prod.orders AT (TIMESTAMP => '2024-01-01 00:00:00'::timestamp);
```

**Savings**: Cloning vs. copying data = **90% storage savings** + instant creation.

### 3. Query Result Caching

```sql
-- Enable result cache (enabled by default)
ALTER SESSION SET USE_CACHED_RESULT = TRUE;

-- Cached results are FREE for 24 hours
-- Identical queries return immediately

-- Check if query used cache
SELECT
    query_id,
    query_text,
    execution_time / 1000 AS execution_seconds,
    bytes_scanned,
    percentage_scanned_from_cache,
    credits_used_cloud_services
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;
```

**Savings**: Cached results = **0 compute cost** for repeated queries.

### 4. Optimize Data Loading

```sql
-- Bulk load with COPY INTO (most cost-effective)
COPY INTO staging.orders
FROM @s3_stage/orders/
FILE_FORMAT = (TYPE = 'PARQUET')
ON_ERROR = 'CONTINUE';

-- Use optimal file sizes: 100-250 MB compressed
-- Avoid many small files (inefficient)

-- Snowpipe for continuous micro-batches
CREATE PIPE order_pipe AS
    COPY INTO staging.orders
    FROM @s3_stage/orders/
    FILE_FORMAT = (TYPE = 'PARQUET');

-- Snowpipe cost: $0.06 per 1,000 files processed
```

**Savings**: Parquet vs. CSV = **50-70% storage savings** + faster queries.

### 5. Use Multi-Table Insert

```sql
-- Insert into multiple tables in single scan
INSERT ALL
    WHEN order_status = 'completed' THEN
        INTO orders_completed VALUES (order_id, customer_id, total_amount)
    WHEN order_status = 'pending' THEN
        INTO orders_pending VALUES (order_id, customer_id, total_amount)
    WHEN order_status = 'cancelled' THEN
        INTO orders_cancelled VALUES (order_id, customer_id, total_amount)
SELECT order_id, customer_id, total_amount, order_status
FROM staging.orders_raw;
```

**Savings**: Multi-table insert vs. separate inserts = **70% compute savings**.

### 6. Partition Pruning & Clustering

```sql
-- Add clustering key for large tables (>100GB)
ALTER TABLE fact_sales
    CLUSTER BY (sale_date, region_id);

-- Automatic micro-partition pruning
SELECT SUM(amount)
FROM fact_sales
WHERE sale_date = '2024-01-15'  -- Only scans relevant micro-partitions
    AND region_id = 'US-WEST';

-- Check clustering depth (lower is better)
SELECT SYSTEM$CLUSTERING_INFORMATION('fact_sales', '(sale_date, region_id)');
```

**Savings**: Good clustering = **80-95% less data scanned** for filtered queries.

### 7. Materialized Views for Aggregations

```sql
-- Create materialized view (pre-computed)
CREATE MATERIALIZED VIEW analytics.daily_sales_summary AS
SELECT
    DATE_TRUNC('day', sale_date) AS day,
    region_id,
    product_category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_sales,
    AVG(amount) AS avg_sale_amount
FROM fact_sales
GROUP BY 1, 2, 3;

-- Queries use MV automatically (zero compute for aggregation)
SELECT day, SUM(total_sales)
FROM analytics.daily_sales_summary
WHERE day >= '2024-01-01'
GROUP BY day;
```

**Savings**: Materialized views = **90-99%** faster + cheaper for repeated aggregations.

### 8. Suspend Warehouses Manually

```sql
-- Suspend warehouse immediately after batch job
ALTER WAREHOUSE etl_wh SUSPEND;

-- Resume before next job
ALTER WAREHOUSE etl_wh RESUME;

-- Check warehouse status
SHOW WAREHOUSES;

-- Suspend all idle warehouses (script for cleanup)
SELECT
    'ALTER WAREHOUSE ' || warehouse_name || ' SUSPEND;' AS suspend_cmd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
    AND credits_used = 0;
```

### Cost Optimization Checklist

```
✅ Use X-Small warehouse for development
✅ Set auto-suspend to 60-300 seconds
✅ Enable query result caching
✅ Use zero-copy cloning for dev/test
✅ Load data in Parquet/ORC format
✅ Optimize file sizes (100-250MB)
✅ Add clustering keys to large tables
✅ Create materialized views for aggregations
✅ Set up resource monitors with alerts
✅ Review ACCOUNT_USAGE daily
✅ Suspend warehouses during off-hours
✅ Use Snowpipe for streaming (avoid dedicated warehouse)
✅ Leverage Time Travel instead of backups
✅ Share data instead of copying
```

---

## 📈 Credit Tracking & Monitoring

### Daily Credit Usage

```sql
-- Daily credit consumption by warehouse
SELECT
    DATE_TRUNC('day', start_time) AS usage_day,
    warehouse_name,
    SUM(credits_used) AS total_credits,
    SUM(credits_used) * 2.00 AS cost_standard_usd,  -- Adjust multiplier
    SUM(credits_used) * 3.00 AS cost_enterprise_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

### Credit Usage by Query Type

```sql
-- Top 20 most expensive queries (last 7 days)
SELECT
    query_id,
    user_name,
    warehouse_name,
    query_type,
    SUBSTR(query_text, 1, 100) AS query_preview,
    execution_time / 1000 AS execution_seconds,
    credits_used_cloud_services,
    bytes_scanned / POWER(1024, 3) AS gb_scanned,
    start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    AND execution_status = 'SUCCESS'
    AND credits_used_cloud_services > 0
ORDER BY credits_used_cloud_services DESC
LIMIT 20;
```

### Storage Costs Tracking

```sql
-- Database storage usage (average over last 30 days)
SELECT
    database_name,
    AVG(average_database_bytes) / POWER(1024, 3) AS avg_storage_gb,
    AVG(average_database_bytes) / POWER(1024, 4) AS avg_storage_tb,
    (AVG(average_database_bytes) / POWER(1024, 4)) * 23 AS monthly_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
WHERE usage_date >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY 1
ORDER BY 2 DESC;
```

### Monthly Cost Projection

```sql
-- Project monthly costs based on current usage
WITH daily_credits AS (
    SELECT
        DATE_TRUNC('day', start_time) AS usage_day,
        SUM(credits_used) AS daily_credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    GROUP BY 1
)
SELECT
    AVG(daily_credits) AS avg_daily_credits,
    AVG(daily_credits) * 30 AS projected_monthly_credits,
    AVG(daily_credits) * 30 * 2.00 AS projected_cost_standard_usd,
    AVG(daily_credits) * 30 * 3.00 AS projected_cost_enterprise_usd
FROM daily_credits;
```

### Real-Time Credit Monitoring

```sql
-- Today's credit usage so far
SELECT
    warehouse_name,
    SUM(credits_used) AS credits_today,
    SUM(credits_used) * 2.00 AS cost_today_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= CURRENT_DATE()
GROUP BY 1
ORDER BY 2 DESC;
```

### Resource Monitor Status

```sql
-- Check resource monitor limits and usage
SELECT
    name AS monitor_name,
    credit_quota,
    used_credits,
    remaining_credits,
    ROUND((used_credits / credit_quota) * 100, 2) AS percent_used,
    frequency,
    start_time,
    end_time
FROM SNOWFLAKE.ACCOUNT_USAGE.RESOURCE_MONITORS;
```

### Cost Dashboard Query Template

```sql
-- Comprehensive cost dashboard (last 7 days)
WITH warehouse_costs AS (
    SELECT
        warehouse_name,
        SUM(credits_used) AS total_credits,
        SUM(credits_used) * 2.00 AS cost_usd
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    GROUP BY 1
),
storage_costs AS (
    SELECT
        SUM(average_database_bytes) / POWER(1024, 4) AS total_tb,
        (SUM(average_database_bytes) / POWER(1024, 4)) * 23 / 30 * 7 AS cost_usd
    FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
    WHERE usage_date >= DATEADD('day', -7, CURRENT_DATE())
)
SELECT
    'Compute' AS cost_category,
    SUM(cost_usd) AS total_cost_usd
FROM warehouse_costs
UNION ALL
SELECT
    'Storage' AS cost_category,
    cost_usd
FROM storage_costs;
```

---

## ⏰ Trial Expiration & Next Steps

### Understanding Trial Expiration

```
Trial Duration: 30 days from signup
Credit Limit: $400 USD
Expiration Behavior:
- Account remains active
- Can continue with credit card
- No automatic charges without opt-in
```

### What Happens After Trial

**Scenario 1: Trial Credits Exhausted Before 30 Days**
```
→ Warehouses automatically suspend
→ Account enters "credit pause" state
→ Data remains accessible (read-only via UI)
→ Must add payment method to resume compute
→ Storage charges begin (~$23/TB/month)
```

**Scenario 2: 30 Days Expire with Credits Remaining**
```
→ Remaining credits forfeit
→ Account requires payment method
→ Same as Scenario 1
```

### Converting to Paid Account

```sql
-- Check remaining trial credits
SELECT
    credit_quota - used_credits AS remaining_credits,
    DATEDIFF('day', CURRENT_DATE(), end_time) AS days_remaining
FROM SNOWFLAKE.ACCOUNT_USAGE.RESOURCE_MONITORS
WHERE name = 'TRIAL_MONITOR';
```

**Steps to Add Payment Method**:
1. Navigate to **Account** → **Billing**
2. Click **Add Payment Method**
3. Enter credit card details
4. Set monthly spending limit (recommended: $50-100 for learning)
5. Resource monitors remain active

### Exporting Data Before Trial Ends

```sql
-- Export to S3/Azure/GCS (recommended)
COPY INTO @my_s3_stage/backup/customers/
FROM training_snowflake.analytics.customers
FILE_FORMAT = (TYPE = 'PARQUET' COMPRESSION = 'SNAPPY')
HEADER = TRUE
OVERWRITE = TRUE;

-- Or download via SnowSQL
snowsql -c my_connection -o output_format=csv -o header=true \
    -q "SELECT * FROM training_snowflake.analytics.customers" \
    > customers_backup.csv
```

### Continuing After This Module

**Options**:

1. **Keep Snowflake (Paid)**:
   - Add payment method
   - Set monthly budget ($50-100)
   - Build portfolio projects
   - Experiment with advanced features

2. **Pause Snowflake**:
   - Export all data
   - Drop databases/warehouses
   - Keep account (no charges if no resources)
   - Reactivate later

3. **Transition to Free Alternatives**:
   - DuckDB (local analytical queries)
   - PostgreSQL (if need persistence)
   - BigQuery (Google, limited free tier)
   - AWS Athena (pay-per-query)

### Post-Trial Cost Management

```sql
-- Minimal cost setup for occasional use
-- 1. Keep only essential data
DROP DATABASE IF EXISTS training_snowflake;
CREATE DATABASE portfolio_db;

-- 2. Use smallest warehouse
CREATE WAREHOUSE minimal_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- 3. Set strict resource monitor
CREATE RESOURCE MONITOR monthly_budget WITH
    CREDIT_QUOTA = 25              -- $50/month at Standard
    FREQUENCY = MONTHLY
    TRIGGERS
        ON 80 PERCENT DO NOTIFY
        ON 90 PERCENT DO SUSPEND
        ON 100 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE minimal_wh SET RESOURCE_MONITOR = monthly_budget;
```

**Expected Monthly Cost (Minimal Use)**:
```
Storage (10GB):      ~$0.25/month
Compute (1 hr/week): ~$8-12/month
Total:               ~$10-15/month
```

---

## 📞 Support & Questions

### Getting Help with Costs

- **Snowflake Community**: https://community.snowflake.com/
- **Documentation**: https://docs.snowflake.com/en/user-guide/cost-understanding
- **Support Portal**: https://support.snowflake.com/ (via Snowflake UI)
- **Trial Support**: support@snowflake.com

### Common Cost-Related Questions

**Q: Can I extend my free trial?**
A: No, but remaining exercises can be completed on a paid account with low cost.

**Q: Will I be charged automatically after trial?**
A: No, you must opt-in to paid usage. Account enters pause state without payment method.

**Q: How do I delete my account?**
A: Contact Snowflake support to request account closure.

**Q: Can I get a refund for unused credits?**
A: Trial credits are non-refundable. Paid credits depend on contract terms.

---

## ✅ Pre-Exercise Checklist

Before starting exercises, ensure:

```
✅ Signed up for Snowflake free trial ($400 credits)
✅ Account is active and accessible
✅ Created at least one resource monitor
✅ Set auto-suspend on warehouses (60-300 seconds)
✅ Understand per-exercise cost estimates
✅ Planned to complete module within 30-day trial
✅ Know how to check remaining credits
✅ Configured email notifications for alerts
```

---

## 🎯 Summary

- **FREE TRIAL**: $400 credits, 30 days, covers ALL exercises
- **Module Cost**: $15-25 total (FREE with trial)
- **Recommended Setup**: X-Small warehouse, 60s auto-suspend
- **Key Strategy**: Complete within trial period = $0 cost
- **Safety Net**: Resource monitors prevent overages
- **Post-Trial**: Export data or add payment with strict limits

> 💡 **Final Tip**: Snowflake's trial is generous. Complete exercises systematically, suspend warehouses when not in use, and you'll finish with $375+ credits remaining!

---

**Last Updated**: March 2026
**Module**: Bonus 02 - Snowflake Data Cloud
**Estimated Time**: 2-3 days (well within trial)
