# 🏆 Snowflake Best Practices

> **Overview**: Production-grade best practices for Snowflake covering performance optimization, cost management, security, and data loading strategies. Apply these patterns for efficient, secure, and cost-effective data operations.

## 📋 Table of Contents

- [Performance Optimization](#performance-optimization)
- [Cost Management](#cost-management)
- [Security Best Practices](#security-best-practices)
- [Data Loading Best Practices](#data-loading-best-practices)
- [Query Optimization](#query-optimization)
- [Schema Design](#schema-design)
- [Monitoring & Observability](#monitoring--observability)

---

## ⚡ Performance Optimization

### 1. Clustering Keys

**When to Use Clustering**:
```
✅ Use clustering when:
  - Table is large (>100GB, ideally >1TB)
  - Frequent queries filter on specific columns
  - Query performance degrades over time
  - High cardinality columns (date, timestamp, ID)

❌ Don't cluster when:
  - Table is small (<100GB)
  - No consistent query patterns
  - Low cardinality columns (boolean, status with few values)
```

**Choosing Clustering Keys**:
```sql
-- Analyze query patterns first
SELECT
    query_text,
    COUNT(*) AS query_count,
    AVG(execution_time) / 1000 AS avg_seconds,
    AVG(bytes_scanned) / POWER(1024, 3) AS avg_gb_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE table_name = 'FACT_SALES'
    AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY query_text
ORDER BY query_count DESC
LIMIT 10;

-- Most queries filter on sale_date and region?
-- Choose those as clustering keys
```

**Implementing Clustering**:
```sql
-- Add clustering key to existing table
ALTER TABLE fact_sales
    CLUSTER BY (sale_date, region_id);

-- Create table with clustering
CREATE TABLE fact_sales (
    sale_id BIGINT,
    sale_date DATE,
    region_id INTEGER,
    product_id INTEGER,
    amount DECIMAL(10,2)
)
CLUSTER BY (sale_date, region_id);

-- Check clustering quality (0-100, lower is better)
SELECT SYSTEM$CLUSTERING_INFORMATION('fact_sales', '(sale_date, region_id)');

-- Output example:
/*
{
  "cluster_by_keys": "LINEAR(sale_date, region_id)",
  "total_partition_count": 5432,
  "total_constant_partition_count": 102,
  "average_overlaps": 2.3,
  "average_depth": 3.1,
  "partition_depth_histogram": {...}
}

Good clustering: average_depth < 5
Needs reclustering: average_depth > 20
*/
```

**Clustering Trade-offs**:
```sql
-- Benefits:
-- - 50-90% reduction in data scanned for filtered queries
-- - Dramatically faster query execution
-- - Better for range scans (BETWEEN, >, <)

-- Costs:
-- - Automatic micro-partition reorganization (compute credits)
-- - Best for large, stable tables (not frequently updated)
-- - Overhead for small tables not worth it

-- Monitor clustering costs
SELECT
    DATE_TRUNC('day', start_time) AS day,
    SUM(credits_used) AS clustering_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.AUTOMATIC_CLUSTERING_HISTORY
WHERE table_name = 'FACT_SALES'
    AND start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY day
ORDER BY day DESC;
```

### 2. Materialized Views

**Use Cases**:
```sql
-- Slow aggregation query (runs frequently)
SELECT
    DATE_TRUNC('day', sale_date) AS day,
    region_id,
    product_category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_sales,
    AVG(amount) AS avg_sale_amount
FROM fact_sales
WHERE sale_date >= DATEADD('year', -1, CURRENT_DATE())
GROUP BY 1, 2, 3;
-- Execution time: 45 seconds, 500GB scanned

-- Create materialized view (pre-computed)
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    DATE_TRUNC('day', sale_date) AS day,
    region_id,
    product_category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_sales,
    AVG(amount) AS avg_sale_amount
FROM fact_sales
GROUP BY 1, 2, 3;

-- Query materialized view (automatic)
SELECT SUM(total_sales)
FROM mv_daily_sales
WHERE day >= '2024-01-01';
-- Execution time: 0.8 seconds, 5MB scanned (99% faster)
```

**Automatic Query Rewriting**:
```sql
-- Original query still works (Snowflake uses MV automatically)
SELECT
    DATE_TRUNC('day', sale_date) AS day,
    SUM(amount) AS total_sales
FROM fact_sales
WHERE sale_date >= '2024-03-01'
GROUP BY 1;

-- Snowflake query optimizer recognizes pattern
-- Automatically uses mv_daily_sales instead
-- Result: Same output, 95%+ faster
```

**Materialized View Maintenance**:
```sql
-- Check MV status
SHOW MATERIALIZED VIEWS;

-- MV automatically refreshes on base table changes
-- Maintenance costs (credits for refresh)

-- Suspend MV refresh (reduce costs)
ALTER MATERIALIZED VIEW mv_daily_sales SUSPEND;

-- Resume MV refresh
ALTER MATERIALIZED VIEW mv_daily_sales RESUME;

-- Drop if not needed
DROP MATERIALIZED VIEW IF EXISTS mv_daily_sales;
```

### 3. Query Result Caching

**Leveraging Result Cache**:
```sql
-- Enable result caching (default)
ALTER SESSION SET USE_CACHED_RESULT = TRUE;

-- Identical queries return cached results (24-hour TTL, 0 compute cost)
SELECT COUNT(*) FROM large_table;  -- First run: 10 seconds, 2 credits
SELECT COUNT(*) FROM large_table;  -- Cached: <1 second, 0 credits

-- Cache invalidated by:
-- 1. Base table data changes
-- 2. 24-hour expiration
-- 3. Manual session setting
```

**Cache Invalidation Strategies**:
```sql
-- Bypass cache for fresh data
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
SELECT COUNT(*) FROM large_table;  -- Forces re-execution
ALTER SESSION SET USE_CACHED_RESULT = TRUE;

-- Check if query used cache
SELECT
    query_id,
    query_text,
    execution_time / 1000 AS execution_seconds,
    bytes_scanned,
    percentage_scanned_from_cache,
    credits_used_cloud_services
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_id = '<query-id-here>';
-- percentage_scanned_from_cache = 100 → fully cached
```

### 4. Search Optimization Service

**Enable for Point Lookups**:
```sql
-- Optimize table for equality and substring searches
ALTER TABLE large_customers ADD SEARCH OPTIMIZATION;

-- Significantly faster for:
SELECT * FROM large_customers WHERE email = 'user@example.com';
SELECT * FROM large_customers WHERE name LIKE '%Smith%';
SELECT * FROM large_customers WHERE customer_id IN (123, 456, 789);

-- Not beneficial for:
-- - Aggregations (SUM, AVG, COUNT)
-- - Range scans (BETWEEN, >, <)
-- - Small tables (<1M rows)
```

**Cost Considerations**:
```sql
-- Search optimization incurs:
-- 1. Initial build cost (one-time)
-- 2. Maintenance cost (on data changes)
-- 3. Storage cost (search index structures)

-- Monitor costs
SELECT
    DATE_TRUNC('day', start_time) AS day,
    SUM(credits_used) AS search_opt_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.SEARCH_OPTIMIZATION_HISTORY
WHERE table_name = 'LARGE_CUSTOMERS'
    AND start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY day;

-- Remove if not providing value
ALTER TABLE large_customers DROP SEARCH OPTIMIZATION;
```

### 5. Partition Pruning

**Leverage Micro-Partition Metadata**:
```sql
-- Snowflake automatically prunes partitions based on filters

-- Good query (partition pruning)
SELECT *
FROM fact_sales
WHERE sale_date = '2024-03-08'  -- Prunes all other date partitions
    AND region_id = 5;

-- Query profile shows:
-- Partitions scanned: 3 out of 5,432 total (99.9% pruned)

-- Bad query (no pruning)
SELECT *
FROM fact_sales
WHERE DATE_PART('year', sale_date) = 2024;  -- Function prevents pruning
-- All partitions scanned (no pruning possible)

-- Fix: Use direct filter
SELECT *
FROM fact_sales
WHERE sale_date >= '2024-01-01' AND sale_date < '2025-01-01';
-- Partitions scanned: 365 out of 5,432 (93% pruned)
```

**Pruning Best Practices**:
```
✅ DO:
  - Filter on actual column: WHERE date_col >= '2024-01-01'
  - Use equality: WHERE region_id = 5
  - Use IN with constants: WHERE status IN ('active', 'pending')

❌ DON'T:
  - Apply functions: WHERE YEAR(date_col) = 2024
  - Use OR across columns: WHERE col1 = X OR col2 = Y
  - Use complex expressions: WHERE col1 + col2 > 100
```

---

## 💰 Cost Management

### 1. Right-Sizing Warehouses

**Start Small, Scale Up**:
```sql
-- Default approach: Start with X-Small
CREATE WAREHOUSE analysis_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'  -- 1 credit/hour
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Monitor query performance
SELECT
    warehouse_name,
    AVG(execution_time) / 1000 AS avg_exec_seconds,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time) / 1000 AS p95_seconds,
    AVG(bytes_spilled_to_local_storage) / POWER(1024, 3) AS avg_local_spill_gb,
    AVG(bytes_spilled_to_remote_storage) / POWER(1024, 3) AS avg_remote_spill_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE warehouse_name = 'ANALYSIS_WH'
    AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name;

-- Scale up if:
-- - remote_spill_gb > 0 (spilling to disk = needs more memory)
-- - p95_seconds > acceptable threshold
-- - Users complaining about slow queries
```

**Warehouse Sizing Decision Tree**:
```
Query performance acceptable? ─┬─ YES ── Keep current size (save costs)
                               │
                               └─ NO ──┐
                                       │
Spilling to remote storage? ───┬─ YES ─┴─ Scale UP (2x size)
                               │
                               └─ NO ──┐
                                       │
Query timeout/very slow? ──────┬─ YES ─┴─ Scale UP (2x size)
                               │
                               └─ NO ── Optimize query (not warehouse)
```

### 2. Auto-Suspend Optimization

**Aggressive Auto-Suspend**:
```sql
-- Development/sandbox (minimal idle time)
CREATE WAREHOUSE dev_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60        -- 1 minute (save 98% on idle time)
    AUTO_RESUME = TRUE;

-- BI dashboards (balance UX and cost)
CREATE WAREHOUSE bi_wh WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300       -- 5 minutes (warm for interactive use)
    AUTO_RESUME = TRUE;

-- ETL/batch jobs (long-running)
CREATE WAREHOUSE etl_wh WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 600       -- 10 minutes (batch job intervals)
    AUTO_RESUME = TRUE;

-- Data science (interactive, sporadic)
CREATE WAREHOUSE ds_wh WITH
    WAREHOUSE_SIZE = 'X-LARGE'
    AUTO_SUSPEND = 180       -- 3 minutes (balance warmth and cost)
    AUTO_RESUME = TRUE;
```

**Cost Impact Analysis**:
```sql
-- Calculate idle time waste
SELECT
    warehouse_name,
    SUM(credits_used) AS total_credits,
    SUM(CASE WHEN query_count = 0 THEN credits_used ELSE 0 END) AS idle_credits,
    ROUND((idle_credits / total_credits) * 100, 2) AS idle_percent
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY idle_credits DESC;

-- If idle_percent > 30%, reduce auto-suspend timeout
```

### 3. Multi-Cluster Warehouse Strategy

**When to Use Multi-Cluster**:
```
✅ Use multi-cluster when:
  - High concurrent user count (>20 users)
  - BI dashboards with variable load
  - Query queue delays unacceptable

❌ Don't use multi-cluster for:
  - Sequential batch jobs (no concurrency)
  - Low user count (<10 concurrent queries)
  - Development workloads
```

**Multi-Cluster Configuration**:
```sql
-- BI dashboard warehouse (auto-scale for users)
CREATE WAREHOUSE bi_dashboard_wh WITH
    WAREHOUSE_SIZE = 'SMALL'
    MIN_CLUSTER_COUNT = 1           -- Always 1 cluster running (baseline)
    MAX_CLUSTER_COUNT = 5           -- Scale to 5 for peak load
    SCALING_POLICY = 'ECONOMY'      -- Cost-optimized scaling
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE;

-- Scaling policy comparison:
-- STANDARD: Starts new cluster immediately when queue forms
--           Cost: Higher | Performance: Best | Use: Critical apps
--
-- ECONOMY: Waits to maximize cluster utilization before scaling
--          Cost: Lower | Performance: Adequate | Use: BI dashboards
```

**Multi-Cluster Cost Monitoring**:
```sql
-- Track cluster usage patterns
SELECT
    warehouse_name,
    DATE_TRUNC('hour', start_time) AS hour,
    AVG(avg_running) AS avg_clusters_running,
    MAX(avg_running) AS max_clusters_running,
    SUM(credits_used) AS credits_used
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY
WHERE warehouse_name = 'BI_DASHBOARD_WH'
    AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, hour
ORDER BY hour DESC;

-- Optimize MAX_CLUSTER_COUNT based on peak usage
-- If max_clusters_running rarely exceeds 3, reduce MAX to 3
```

### 4. Query Result Cache Strategy

**Maximize Cache Hits**:
```sql
-- Encourage dashboard queries to reuse cache
-- 1. Standardize query patterns (avoid slight variations)

-- ❌ BAD: Each query different (no cache reuse)
SELECT * FROM sales WHERE region = 'US-WEST' ORDER BY sale_date; -- User A
SELECT * FROM sales WHERE region='US-WEST' ORDER BY sale_date;   -- User B (different spacing)
SELECT * FROM sales WHERE region = 'US-WEST' ORDER BY 3;         -- User C (different ORDER BY)
-- Result: 3 query executions, 0 cache hits

-- ✅ GOOD: Identical queries (high cache reuse)
SELECT * FROM sales WHERE region = 'US-WEST' ORDER BY sale_date;
SELECT * FROM sales WHERE region = 'US-WEST' ORDER BY sale_date;
SELECT * FROM sales WHERE region = 'US-WEST' ORDER BY sale_date;
-- Result: 1 query execution, 2 cache hits (66% cost savings)

-- 2. Create views for common queries
CREATE VIEW vw_us_west_sales AS
SELECT * FROM sales WHERE region = 'US-WEST' ORDER BY sale_date;

-- Users query view (consistent SQL)
SELECT * FROM vw_us_west_sales WHERE sale_date >= '2024-03-01';
```

### 5. Monitoring & Alerting

**Daily Cost Monitoring Query**:
```sql
-- Daily credit consumption summary
CREATE OR REPLACE VIEW cost_monitoring.daily_credit_summary AS
SELECT
    DATE_TRUNC('day', start_time) AS day,
    warehouse_name,
    SUM(credits_used) AS total_credits,
    SUM(credits_used) * 2.00 AS cost_standard_usd,    -- Adjust for your edition
    COUNT(DISTINCT query_id) AS query_count,
    SUM(credits_used) / NULLIF(COUNT(DISTINCT query_id), 0) AS credits_per_query
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY wh
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
    ON wh.warehouse_name = qh.warehouse_name
    AND wh.start_time = DATE_TRUNC('hour', qh.start_time)
WHERE wh.start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY day, warehouse_name
ORDER BY day DESC, total_credits DESC;

-- Query daily
SELECT * FROM cost_monitoring.daily_credit_summary
WHERE day >= CURRENT_DATE() - 7;
```

**Cost Anomaly Detection**:
```sql
-- Alert when daily cost exceeds baseline by 50%
WITH daily_costs AS (
    SELECT
        DATE_TRUNC('day', start_time) AS day,
        SUM(credits_used) AS daily_credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
    GROUP BY day
),
baseline AS (
    SELECT AVG(daily_credits) AS avg_daily_credits
    FROM daily_costs
    WHERE day < CURRENT_DATE()
)
SELECT
    dc.day,
    dc.daily_credits,
    b.avg_daily_credits AS baseline_credits,
    dc.daily_credits - b.avg_daily_credits AS delta_credits,
    ROUND((dc.daily_credits / b.avg_daily_credits - 1) * 100, 2) AS percent_increase
FROM daily_costs dc
CROSS JOIN baseline b
WHERE dc.day = CURRENT_DATE()
    AND dc.daily_credits > b.avg_daily_credits * 1.5  -- 50% above baseline
ORDER BY dc.day DESC;

-- Schedule this query as a task, send alert if returns rows
```

---

## 🔒 Security Best Practices

### 1. Role-Based Access Control (RBAC)

**Hierarchical Role Design**:
```sql
-- Role hierarchy (least privilege principle)
/*
ACCOUNTADMIN (top-level, use sparingly)
    ├── SYSADMIN (system administration)
    │   ├── DATA_ENGINEER (ETL pipelines)
    │   └── DBA (database management)
    ├── SECURITYADMIN (security management)
    │   └── AUDITOR (read-only security)
    └── USERADMIN (user management)
        └── ANALYST (business users)
            ├── ANALYST_SALES
            ├── ANALYST_MARKETING
            └── ANALYST_FINANCE
*/

-- Create functional roles
USE ROLE SECURITYADMIN;

CREATE ROLE data_engineer COMMENT = 'ETL pipeline developers';
CREATE ROLE data_analyst COMMENT = 'Business intelligence analysts';
CREATE ROLE data_scientist COMMENT = 'ML and advanced analytics';
CREATE ROLE read_only COMMENT = 'Read-only access for reporting';

-- Grant role hierarchy
GRANT ROLE data_engineer TO ROLE SYSADMIN;
GRANT ROLE data_analyst TO ROLE SYSADMIN;
GRANT ROLE data_scientist TO ROLE SYSADMIN;
GRANT ROLE read_only TO ROLE SYSADMIN;

-- Grant roles to users
GRANT ROLE data_engineer TO USER john.doe@company.com;
GRANT ROLE data_analyst TO USER jane.smith@company.com;
GRANT ROLE read_only TO USER external.vendor@partner.com;
```

**Granular Permissions**:
```sql
-- Data Engineer role (full ETL access)
GRANT USAGE ON DATABASE prod_database TO ROLE data_engineer;
GRANT USAGE ON SCHEMA prod_database.staging TO ROLE data_engineer;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA prod_database.staging TO ROLE data_engineer;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA prod_database.staging TO ROLE data_engineer;
GRANT USAGE ON WAREHOUSE etl_wh TO ROLE data_engineer;

-- Data Analyst role (read-only analytics)
GRANT USAGE ON DATABASE prod_database TO ROLE data_analyst;
GRANT USAGE ON SCHEMA prod_database.analytics TO ROLE data_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA prod_database.analytics TO ROLE data_analyst;
GRANT SELECT ON FUTURE TABLES IN SCHEMA prod_database.analytics TO ROLE data_analyst;
GRANT USAGE ON WAREHOUSE bi_wh TO ROLE data_analyst;

-- Read-Only role (external partners)
GRANT USAGE ON DATABASE shared_database TO ROLE read_only;
GRANT USAGE ON SCHEMA shared_database.public_views TO ROLE read_only;
GRANT SELECT ON ALL VIEWS IN SCHEMA shared_database.public_views TO ROLE read_only;
GRANT USAGE ON WAREHOUSE partner_wh TO ROLE read_only;
```

### 2. Network Policies

**IP Whitelisting**:
```sql
USE ROLE SECURITYADMIN;

-- Create network policy (office + VPN IPs only)
CREATE NETWORK POLICY office_only
    ALLOWED_IP_LIST = ('203.0.113.0/24', '192.0.2.50', '198.51.100.0/22')
    BLOCKED_IP_LIST = ()
    COMMENT = 'Restrict access to office and VPN';

-- Apply to account (all users)
ALTER ACCOUNT SET NETWORK_POLICY = office_only;

-- OR apply to specific user
ALTER USER external.vendor@partner.com SET NETWORK_POLICY = office_only;

-- View network policies
SHOW NETWORK POLICIES;
DESC NETWORK POLICY office_only;
```

### 3. Multi-Factor Authentication (MFA)

**Enforce MFA for Admins**:
```sql
-- Require MFA for privileged roles (via UI or SCIM)
-- Account → Users → [Select User] → Security → Enforce MFA

-- Verify MFA status
SELECT
    name AS username,
    has_mfa AS mfa_enabled,
    ext_authn_duo AS duo_enabled
FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
WHERE deleted_on IS NULL
ORDER BY name;

-- Best practice: Enforce MFA for:
-- - ACCOUNTADMIN
-- - SECURITYADMIN
-- - Users with write access to production
```

### 4. Column-Level Security (Masking Policies)

**Dynamic Data Masking**:
```sql
-- Create masking policy for PII (email addresses)
CREATE MASKING POLICY email_mask AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'DATA_ENGINEER') THEN val
        WHEN CURRENT_ROLE() = 'DATA_ANALYST' THEN REGEXP_REPLACE(val, '.+@', '***@')
        ELSE '***MASKED***'
    END;

-- Apply to column
ALTER TABLE customers MODIFY COLUMN email
    SET MASKING POLICY email_mask;

-- Test as different roles
USE ROLE ACCOUNTADMIN;
SELECT email FROM customers LIMIT 1;  -- user@example.com (full)

USE ROLE DATA_ANALYST;
SELECT email FROM customers LIMIT 1;  -- ***@example.com (partial)

USE ROLE READ_ONLY;
SELECT email FROM customers LIMIT 1;  -- ***MASKED*** (hidden)
```

**Masking Policy for SSN/Credit Cards**:
```sql
-- Full masking except for authorized roles
CREATE MASKING POLICY ssn_mask AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'COMPLIANCE_OFFICER') THEN val
        ELSE 'XXX-XX-' || RIGHT(val, 4)  -- Show last 4 digits only
    END;

ALTER TABLE customers MODIFY COLUMN ssn
    SET MASKING POLICY ssn_mask;
```

### 5. Row Access Policies

**Row-Level Security**:
```sql
-- Create row access policy (region-based access)
CREATE ROW ACCESS POLICY regional_access AS (region VARCHAR) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TRUE
        WHEN CURRENT_ROLE() = 'ANALYST_US' AND region = 'US' THEN TRUE
        WHEN CURRENT_ROLE() = 'ANALYST_EU' AND region = 'EU' THEN TRUE
        ELSE FALSE
    END;

-- Apply to table
ALTER TABLE sales
    ADD ROW ACCESS POLICY regional_access ON (region);

-- Test
USE ROLE ANALYST_US;
SELECT COUNT(*) FROM sales;  -- Only sees US rows

USE ROLE ANALYST_EU;
SELECT COUNT(*) FROM sales;  -- Only sees EU rows
```

---

## 📦 Data Loading Best Practices

### 1. File Format Optimization

**Preferred Formats**:
```
Best:    Parquet, ORC     (columnar, compressed, splittable)
Good:    Avro, JSON       (structured, nested data support)
OK:      CSV, TSV         (simple, human-readable)
Avoid:   XML, large JSON  (verbose, slow parsing)
```

**File Format Examples**:
```sql
-- Parquet (best for analytics)
CREATE FILE FORMAT parquet_format
    TYPE = 'PARQUET'
    COMPRESSION = 'SNAPPY'  -- Already compressed
    BINARY_AS_TEXT = FALSE;

COPY INTO analytics.sales
FROM @s3_stage/sales/
FILE_FORMAT = parquet_format;

-- CSV (with optimizations)
CREATE FILE FORMAT csv_optimized
    TYPE = 'CSV'
    COMPRESSION = 'GZIP'              -- Compress CSV files
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    FIELD_DELIMITER = ','
    ESCAPE_UNENCLOSED_FIELD = NONE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

COPY INTO staging.raw_data
FROM @s3_stage/data/
FILE_FORMAT = csv_optimized
ON_ERROR = 'CONTINUE';
```

### 2. Optimal File Sizing

**File Size Guidelines**:
```
Ideal:   100-250 MB per file (compressed)
OK:      50-500 MB
Avoid:   <10 MB (too many small files, slow)
Avoid:   >5 GB (hard to parallelize)
```

**Why File Size Matters**:
```
Many small files (10,000 × 1MB):
  - 10,000 file operations (slow)
  - Limited parallelization
  - Higher Snowpipe costs ($0.06 per 1K files)

Fewer large files (50 × 200MB):
  - 50 file operations (fast)
  - Better parallelization
  - Lower Snowpipe costs
  - Optimal throughput
```

### 3. Bulk Loading (COPY INTO)

**Basic COPY INTO**:
```sql
-- Load from S3 stage
COPY INTO staging.orders
FROM @s3_stage/orders/
FILE_FORMAT = (TYPE = 'PARQUET')
ON_ERROR = 'CONTINUE'           -- Skip bad records
VALIDATION_MODE = 'RETURN_ERRORS';  -- Show errors without loading

-- Load with transformations
COPY INTO staging.customers
FROM (
    SELECT
        $1::INTEGER AS customer_id,
        $2::VARCHAR AS name,
        $3::VARCHAR AS email,
        UPPER($4::VARCHAR) AS country,
        CURRENT_TIMESTAMP() AS loaded_at
    FROM @s3_stage/customers/
)
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);
```

**Incremental Loading (Pattern Matching)**:
```sql
-- Load only new files (date-partitioned)
COPY INTO staging.sales
FROM @s3_stage/sales/
PATTERN = '.*/year=2024/month=03/.*[.]parquet'
FILE_FORMAT = (TYPE = 'PARQUET')
ON_ERROR = 'SKIP_FILE';  -- Skip entire file on first error
```

### 4. Streaming (Snowpipe)

**When to Use Snowpipe**:
```
✅ Use Snowpipe for:
  - Continuous data ingestion (IoT, logs, events)
  - Sub-minute latency requirements
  - Event-driven workflows
  - Micro-batch ingestion

❌ Use COPY INTO for:
  - Batch ETL (hourly, daily)
  - Large bulk loads
  - One-time data migration
```

**Snowpipe Setup**:
```sql
-- Create pipe
CREATE PIPE order_events_pipe
    AUTO_INGEST = TRUE
    AS
    COPY INTO streaming.order_events
    FROM @s3_stage/events/
    FILE_FORMAT = (TYPE = 'JSON')
    ON_ERROR = 'CONTINUE';

-- Configure S3 event notification with notification_channel from:
DESC PIPE order_events_pipe;

-- Monitor pipe
SELECT SYSTEM$PIPE_STATUS('order_events_pipe');

-- View load history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
    PIPE_NAME => 'ORDER_EVENTS_PIPE',
    DATE_RANGE_START => DATEADD('hour', -24, CURRENT_TIMESTAMP())
))
ORDER BY start_time DESC;
```

### 5. Incremental Loading (Streams & Merge)

**CDC Pattern with Streams**:
```sql
-- Create stream on source table
CREATE STREAM customer_changes_stream ON TABLE staging.customers_raw;

-- Process incremental changes (scheduled task)
MERGE INTO analytics.customers target
USING (
    SELECT
        customer_id,
        name,
        email,
        METADATA$ACTION AS action,
        METADATA$ISUPDATE AS is_update
    FROM customer_changes_stream
) source
ON target.customer_id = source.customer_id
WHEN MATCHED AND source.action = 'DELETE' THEN DELETE
WHEN MATCHED AND source.action = 'INSERT' AND source.is_update THEN
    UPDATE SET
        name = source.name,
        email = source.email,
        updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED AND source.action = 'INSERT' THEN
    INSERT (customer_id, name, email, created_at)
    VALUES (source.customer_id, source.name, source.email, CURRENT_TIMESTAMP());

-- Stream automatically consumed after successful commit
```

---

## 🔍 Query Optimization

### 1. Avoid SELECT *

```sql
-- ❌ BAD: Reads all columns (wastes I/O, memory, network)
SELECT * FROM large_table WHERE date = '2024-03-08';

-- ✅ GOOD: Read only needed columns
SELECT customer_id, order_id, amount
FROM large_table
WHERE date = '2024-03-08';

-- Impact: 70-90% less data scanned (if selecting 3/30 columns)
```

### 2. Use Query Profiler

```sql
-- Execute query in UI
SELECT
    customer_id,
    SUM(amount) AS total_spent
FROM sales
WHERE sale_date >= '2024-01-01'
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 10;

-- Click "Query Details" tab → "Profile" tab
-- Analyze:
-- - Partitions scanned vs. total (pruning effectiveness)
-- - Bytes scanned (cost indicator)
-- - Execution time breakdown (identify bottleneck)
-- - Spilling to disk (memory issue)
```

### 3. Filter Early, Aggregate Late

```sql
-- ❌ BAD: Aggregate then filter
SELECT *
FROM (
    SELECT customer_id, SUM(amount) AS total
    FROM sales
    GROUP BY customer_id
)
WHERE total > 1000;

-- ✅ GOOD: Filter then aggregate (fewer rows to aggregate)
SELECT customer_id, SUM(amount) AS total
FROM sales
WHERE amount > 10  -- Early filter reduces aggregation work
GROUP BY customer_id
HAVING total > 1000;
```

---

## 📚 Summary Checklist

### Performance
```
✅ Cluster keys on large tables (>100GB, high-cardinality columns)
✅ Materialized views for repeated aggregations
✅ Enable result caching (default)
✅ Search optimization for point lookups
✅ Direct column filters (avoid functions in WHERE)
```

### Cost
```
✅ Start with X-Small warehouses, scale up if needed
✅ Auto-suspend 60-300 seconds
✅ Multi-cluster only for high concurrency (>20 users)
✅ Monitor daily usage, set resource monitors
✅ Leverage zero-copy cloning for dev/test
```

### Security
```
✅ RBAC with functional roles (least privilege)
✅ Network policies (IP whitelist)
✅ MFA for admins and write access
✅ Masking policies for PII
✅ Row access policies for multi-tenant data
```

### Data Loading
```
✅ Parquet/ORC format (columnar, compressed)
✅ 100-250MB file sizes
✅ COPY INTO for batch, Snowpipe for streaming
✅ Streams + Tasks for CDC
✅ ON_ERROR strategies (CONTINUE, SKIP_FILE)
```

---

**Last Updated**: March 2026
**Module**: Bonus 02 - Snowflake Data Cloud
