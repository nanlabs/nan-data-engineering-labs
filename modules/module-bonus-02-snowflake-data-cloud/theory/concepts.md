# 📚 Snowflake Core Concepts

> **Overview**: This document covers the fundamental architecture and concepts of Snowflake Data Cloud, including its unique multi-cluster shared data architecture, virtual warehouses, zero-copy cloning, Time Travel, data sharing, and streaming capabilities.

## 📋 Table of Contents

- [Snowflake Architecture](#snowflake-architecture)
- [Virtual Warehouses](#virtual-warehouses)
- [Zero-Copy Cloning](#zero-copy-cloning)
- [Time Travel & Fail-safe](#time-travel--fail-safe)
- [Secure Data Sharing](#secure-data-sharing)
- [Streams & Tasks](#streams--tasks)
- [Snowpipe](#snowpipe)
- [External Tables](#external-tables)
- [Advanced Concepts](#advanced-concepts)

---

## 🏗️ Snowflake Architecture

### Three-Layer Architecture

Snowflake's unique architecture separates compute, storage, and services into independent, scalable layers:

```
┌─────────────────────────────────────────────────────┐
│          CLOUD SERVICES LAYER                       │
│  (Query Optimization, Security, Metadata)           │
├─────────────────────────────────────────────────────┤
│          COMPUTE LAYER (Virtual Warehouses)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ WH-ETL   │  │  WH-BI   │  │ WH-DS    │  ...    │
│  └──────────┘  └──────────┘  └──────────┘         │
├─────────────────────────────────────────────────────┤
│          STORAGE LAYER (Database Objects)           │
│  (Micro-partitions, Columnar, Compressed)           │
└─────────────────────────────────────────────────────┘
           ↑                    ↑
           │                    │
      AWS S3 / Azure Blob / Google Cloud Storage
```

### 1. Storage Layer

**Characteristics**:
- **Fully Managed**: Snowflake handles all storage infrastructure
- **Columnar Format**: Data stored in compressed columnar micro-partitions
- **Micro-Partitions**: Immutable 50-500MB compressed blocks
- **Automatic Clustering**: Data is automatically organized
- **Encryption**: All data encrypted at rest (AES-256)

**Micro-Partition Structure**:

```sql
-- Logical table
CREATE TABLE sales (
    sale_id INTEGER,
    sale_date DATE,
    customer_id INTEGER,
    product_id INTEGER,
    amount DECIMAL(10,2),
    region VARCHAR(50)
);

-- Physical storage (automatic)
/*
Micro-Partition 1: 2024-01-01 to 2024-01-15
  ├─ Column: sale_id (compressed, min: 1, max: 15000)
  ├─ Column: sale_date (compressed, min: 2024-01-01, max: 2024-01-15)
  ├─ Column: customer_id (compressed, min: 100, max: 9500)
  └─ ... (metadata for pruning)

Micro-Partition 2: 2024-01-16 to 2024-01-31
  └─ ...
*/
```

**Automatic Pruning**:

```sql
-- Query with filter
SELECT SUM(amount)
FROM sales
WHERE sale_date = '2024-01-10'      -- Only scans Micro-Partition 1
    AND region = 'US-WEST';         -- Further filters within partition

-- Snowflake's query planner automatically:
-- 1. Reads micro-partition metadata
-- 2. Prunes partitions outside date range
-- 3. Scans only relevant partitions
-- Result: 95%+ data skipped
```

**Cost Implications**:
```
Storage Pricing: $23-40/TB/month (compressed)
Compression Ratio: Typically 10:1
Example: 1TB raw data → ~100GB stored → $2.30-4.00/month
```

### 2. Compute Layer (Virtual Warehouses)

**Characteristics**:
- **Elastic**: Scale up/down instantly
- **Concurrent**: Multiple warehouses access same data
- **Isolated**: No resource contention between warehouses
- **Stateless**: No data cached permanently (except intermediate results)

**Warehouse Components**:

```
Virtual Warehouse = Cluster of Compute Nodes

Single Cluster Warehouse:
┌──────────────────────────────┐
│  Virtual Warehouse (Size: M) │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│  │Node1│ │Node2│ │Node3│ │Node4│
│  └─────┘ └─────┘ └─────┘ └─────┘
└──────────────────────────────┘
    ↓         ↓        ↓       ↓
  Storage Layer (shared data)

Multi-Cluster Warehouse (Auto-Scaling):
┌──────────────────────────────┐
│  Cluster 1 (always running)  │
├──────────────────────────────┤
│  Cluster 2 (auto-scale)      │  ← Starts on query queue
├──────────────────────────────┤
│  Cluster 3 (auto-scale)      │  ← Starts on high concurrency
└──────────────────────────────┘
```

**Compute Isolation Benefits**:

```sql
-- ETL warehouse (doesn't affect BI users)
CREATE WAREHOUSE etl_wh WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 600;

-- BI warehouse (doesn't affect ETL jobs)
CREATE WAREHOUSE bi_wh WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 120
    MAX_CLUSTER_COUNT = 3;

-- Data science warehouse (isolated experiments)
CREATE WAREHOUSE ds_wh WITH
    WAREHOUSE_SIZE = 'X-LARGE'
    AUTO_SUSPEND = 300;

-- All warehouses read from same tables concurrently
-- No locking, no contention, independent scaling
```

### 3. Cloud Services Layer

**Responsibilities**:
- **Query Optimization**: Parse, optimize, generate execution plans
- **Security & Authentication**: SSO, MFA, RBAC, encryption
- **Metadata Management**: Table definitions, statistics, constraints
- **Infrastructure Management**: Automatic upgrades, monitoring
- **Transaction Management**: ACID compliance, concurrency control

**Cost Model**:
```
Cloud Services Cost:
- Free if usage < 10% of daily compute spend
- Typical workloads: 2-5% (always free)
- Only charged if exceeds 10% threshold

Example:
- Compute spend: $100/day
- Cloud services: $4 (4% of compute)
- Billed: $0 (below 10% threshold)
```

**Metadata Operations (Cloud Services)**:

```sql
-- These operations use Cloud Services Layer (typically free)

-- View table metadata
SHOW TABLES IN DATABASE training_db;
DESCRIBE TABLE customers;

-- Access information schema
SELECT *
FROM information_schema.tables
WHERE table_schema = 'PUBLIC';

-- Query history
SELECT *
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD('day', -1, CURRENT_TIMESTAMP());

-- Security operations
SHOW GRANTS ON TABLE customers;
SHOW ROLES;
```

### Multi-Cluster Shared Data Architecture

**Traditional Shared-Nothing Architecture**:
```
Problem: Data divided across nodes
          Scale compute = reshuffle data
          High concurrency = resource contention

┌─────────┐  ┌─────────┐  ┌─────────┐
│ Node 1  │  │ Node 2  │  │ Node 3  │
│ Data A  │  │ Data B  │  │ Data C  │  ← Data partitioned
└─────────┘  └─────────┘  └─────────┘
```

**Snowflake's Shared Data Architecture**:
```
Solution: Compute and storage fully separated
          Scale compute independently
          No data movement, instant elasticity

┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ WH 1 │  │ WH 2 │  │ WH 3 │  │ WH N │  ← Scale independently
└───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘
    └─────────┴──────────┴──────────┘
                  ↓
    ┌────────────────────────────┐
    │   Shared Storage Layer     │  ← Single source of truth
    │   (All data available)     │
    └────────────────────────────┘
```

**Benefits**:

1. **Instant Scaling**: Add/remove warehouses without data movement
2. **Zero Contention**: Workloads don't compete for resources
3. **Concurrent Access**: Unlimited users on same data
4. **Elastic Cost**: Pay only for compute used

---

## ⚡ Virtual Warehouses

### Warehouse Fundamentals

**What is a Virtual Warehouse?**
- Cluster of compute resources (CPU, memory, temporary storage)
- Executes SQL queries and DML operations
- Independent, on-demand, elastic
- Stateless (no permanent data storage)

### Warehouse Sizes & Performance

| Size      | Credits/Hour | Relative Power | Nodes | Use Case                          |
|-----------|--------------|----------------|-------|-----------------------------------|
| X-Small   | 1            | 1x             | 1     | Dev, small queries, learning      |
| Small     | 2            | 2x             | 2     | Light ETL, simple dashboards      |
| Medium    | 4            | 4x             | 4     | Standard ETL, moderate analytics  |
| Large     | 8            | 8x             | 8     | Heavy ETL, complex queries        |
| X-Large   | 16           | 16x            | 16    | Very large datasets, ML           |
| 2X-Large  | 32           | 32x            | 32    | Massive batch processing          |
| 3X-Large  | 64           | 64x            | 64    | Enterprise-scale workloads        |
| 4X-Large  | 128          | 128x           | 128   | Extreme processing (rare)         |

**Performance vs. Size**:
```
Linear scaling: 2x size ≈ 2x performance (for parallelizable queries)

Example: Complex aggregation on 1TB table
- X-Small: ~60 minutes
- Small:   ~30 minutes
- Medium:  ~15 minutes
- Large:   ~7.5 minutes
```

### Creating Warehouses

```sql
-- Development warehouse (minimal cost)
CREATE WAREHOUSE dev_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60                -- Suspend after 60 seconds idle
    AUTO_RESUME = TRUE               -- Auto-start on query
    INITIALLY_SUSPENDED = TRUE       -- Start in suspended state
    COMMENT = 'Development and testing';

-- Production ETL warehouse
CREATE WAREHOUSE etl_wh WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 600               -- 10 minutes (for batch jobs)
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1            -- Always at least 1 cluster
    MAX_CLUSTER_COUNT = 3            -- Scale to 3 for high load
    SCALING_POLICY = 'STANDARD'      -- Balance cost vs. concurrency
    STATEMENT_TIMEOUT_IN_SECONDS = 3600;  -- 1 hour max per query

-- BI dashboard warehouse (high concurrency)
CREATE WAREHOUSE bi_wh WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 120               -- 2 minutes
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 10           -- Support many concurrent users
    SCALING_POLICY = 'ECONOMY'       -- Favor cost over speed
    STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = 120;  -- Queue limit
```

### Multi-Cluster Warehouses

**Scaling Policies**:

1. **STANDARD** (default):
   - Starts new cluster when query queued
   - Aggressive scaling for performance
   - Higher cost during spikes

2. **ECONOMY**:
   - Waits for existing clusters to fill
   - Favors cost over immediate performance
   - Better for BI dashboards with variable load

```sql
-- Standard scaling (fast but costlier)
CREATE WAREHOUSE analysis_wh WITH
    WAREHOUSE_SIZE = 'MEDIUM'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 5
    SCALING_POLICY = 'STANDARD';

-- Scenario:
-- 10 queries arrive simultaneously
-- STANDARD: Starts 2-3 clusters immediately
-- Cost: Higher (more clusters)
-- Benefit: All queries start immediately

-- Economy scaling (slower but cheaper)
ALTER WAREHOUSE analysis_wh SET
    SCALING_POLICY = 'ECONOMY';

-- Same scenario:
-- 10 queries arrive simultaneously
-- ECONOMY: Queues queries, starts 1 cluster
-- Cost: Lower (fewer clusters)
-- Benefit: Reduced cost, some queries wait
```

### Warehouse Management

```sql
-- Modify warehouse
ALTER WAREHOUSE etl_wh SET
    WAREHOUSE_SIZE = 'X-LARGE'       -- Scale up for heavy job
    AUTO_SUSPEND = 1800;             -- 30 minutes for long batch

-- Suspend/resume manually
ALTER WAREHOUSE bi_wh SUSPEND;
ALTER WAREHOUSE bi_wh RESUME IF SUSPENDED;

-- View warehouse status
SHOW WAREHOUSES;
SHOW WAREHOUSES LIKE 'etl%';

-- Detailed warehouse info
DESCRIBE WAREHOUSE etl_wh;

-- Check active queries on warehouse
SELECT
    query_id,
    user_name,
    query_text,
    start_time,
    execution_status
FROM snowflake.account_usage.query_history
WHERE warehouse_name = 'ETL_WH'
    AND execution_status = 'RUNNING';

-- Rename warehouse
ALTER WAREHOUSE old_wh RENAME TO new_wh;

-- Drop warehouse
DROP WAREHOUSE IF EXISTS temp_wh;
```

### Warehouse Use Cases & Best Practices

**1. ETL/ELT Workloads**:
```sql
-- Size: Medium to X-Large (data volume dependent)
-- Auto-suspend: 10-30 minutes (batch job intervals)
-- Clusters: Single cluster (batch jobs run sequentially)

CREATE WAREHOUSE etl_nightly_wh WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 600
    AUTO_RESUME = TRUE;

-- Usage pattern:
USE WAREHOUSE etl_nightly_wh;

-- Extract
CREATE TABLE staging.raw_sales AS
SELECT * FROM external_stage.sales_data;

-- Transform
CREATE TABLE staging.transformed_sales AS
SELECT
    sale_id,
    sale_date,
    customer_id,
    SUM(amount) AS total_amount
FROM staging.raw_sales
GROUP BY 1, 2, 3;

-- Load
MERGE INTO analytics.sales target
USING staging.transformed_sales source
    ON target.sale_id = source.sale_id
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;

-- Warehouse auto-suspends 10 minutes after completion
```

**2. BI Dashboards**:
```sql
-- Size: X-Small to Small (queries pre-aggregated)
-- Auto-suspend: 2-5 minutes (frequent user activity)
-- Clusters: Multi-cluster (many concurrent users)

CREATE WAREHOUSE dashboard_wh WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 5
    SCALING_POLICY = 'ECONOMY';

-- Optimize with materialized views
CREATE MATERIALIZED VIEW dashboard_daily_sales AS
SELECT
    DATE_TRUNC('day', sale_date) AS day,
    region,
    SUM(amount) AS total_sales
FROM analytics.sales
GROUP BY 1, 2;

-- Dashboard queries are fast and cheap
SELECT * FROM dashboard_daily_sales
WHERE day >= DATEADD('month', -3, CURRENT_DATE());
```

**3. Data Science & ML**:
```sql
-- Size: Large to 2X-Large (complex computations)
-- Auto-suspend: 5-10 minutes (iterative analysis)
-- Clusters: Single cluster (dedicated resources)

CREATE WAREHOUSE datascience_wh WITH
    WAREHOUSE_SIZE = 'X-LARGE'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    MAX_CONCURRENCY_LEVEL = 8;  -- Limit concurrent queries per user

-- Example: Feature engineering
CREATE TABLE ml_features AS
SELECT
    customer_id,
    COUNT(*) AS purchase_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_order_value,
    DATEDIFF('day', MIN(sale_date), MAX(sale_date)) AS customer_lifetime_days,
    -- Complex window functions
    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY sale_date
        ROWS BETWEEN 10 PRECEDING AND CURRENT ROW
    ) AS moving_avg_10_orders
FROM analytics.sales
GROUP BY customer_id;
```

**4. Development & Testing**:
```sql
-- Size: X-Small (minimal cost)
-- Auto-suspend: 60 seconds (intermittent use)
-- Clusters: Single cluster

CREATE WAREHOUSE dev_sandbox_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- Clone production for testing (zero-copy, instant)
CREATE DATABASE dev_db CLONE prod_db;

USE WAREHOUSE dev_sandbox_wh;
USE DATABASE dev_db;

-- Test queries on cloned data (safe)
SELECT COUNT(*) FROM customers;
```

---

## 🔄 Zero-Copy Cloning

### What is Zero-Copy Cloning?

**Traditional Copy**:
```
Source Data (1TB) → Full Copy (1TB) → Destination
Time: Hours
Cost: Storage for 2TB
```

**Snowflake Zero-Copy Clone**:
```
Source Data (1TB) → Metadata Pointer → Destination
Time: Seconds
Cost: Storage for 1TB (until divergence)
```

### How Cloning Works

**Metadata-Based Cloning**:
```
Original Table:
┌────────────────────────────────────┐
│  Table Metadata                    │
│  └→ Micro-Partition 1 (immutable)  │
│  └→ Micro-Partition 2 (immutable)  │
│  └→ Micro-Partition 3 (immutable)  │
└────────────────────────────────────┘

Clone (at creation):
┌────────────────────────────────────┐
│  Cloned Table Metadata             │
│  └→ Micro-Partition 1 ←┐           │  (same physical data)
│  └→ Micro-Partition 2 ←┼─ shared   │
│  └→ Micro-Partition 3 ←┘           │
└────────────────────────────────────┘

After modifications to clone:
┌────────────────────────────────────┐
│  Cloned Table Metadata             │
│  └→ Micro-Partition 1 (shared)     │
│  └→ Micro-Partition 2 (shared)     │
│  └→ Micro-Partition 3 (shared)     │
│  └→ Micro-Partition 4 (new) ←─ divergence
└────────────────────────────────────┘
```

### Cloning Syntax

**Clone Database**:
```sql
-- Clone entire database (all schemas, tables, views)
CREATE DATABASE dev_database CLONE prod_database;

-- Clone as of specific time
CREATE DATABASE analytics_yesterday CLONE prod_database
    AT (TIMESTAMP => '2024-03-08 23:59:59'::timestamp);

-- Clone before accidental drop
CREATE DATABASE backup_before_migration CLONE prod_database;
```

**Clone Schema**:
```sql
-- Clone schema within same database
CREATE SCHEMA test_schema CLONE prod_schema;

-- Clone schema to different database
CREATE SCHEMA dev_db.prod_copy CLONE prod_db.public_schema;
```

**Clone Table**:
```sql
-- Clone table for testing
CREATE TABLE staging.customers_test CLONE prod.customers;

-- Clone with Time Travel
CREATE TABLE analytics.sales_march_1st CLONE prod.sales
    AT (TIMESTAMP => '2024-03-01 00:00:00'::timestamp);

-- Clone before update/delete operation
CREATE TABLE backup.customers_before_merge CLONE prod.customers;
```

**Clone View** (just metadata):
```sql
-- Cloning a view copies definition, not data
CREATE VIEW analytics.sales_summary_clone CLONE analytics.sales_summary;
```

### Use Cases

**1. Development & Testing**:
```sql
-- Production data for development (safe, instant)
CREATE DATABASE dev_maria CLONE prod_database;

-- Maria can modify without affecting production
USE DATABASE dev_maria;

UPDATE customers SET email = 'test@example.com' WHERE customer_id < 100;
DELETE FROM orders WHERE order_date < '2020-01-01';

-- Cost: Only storage for modifications
```

**2. QA & Staging Environments**:
```sql
-- Refresh staging with latest production data (instant)
DROP DATABASE IF EXISTS staging_database;
CREATE DATABASE staging_database CLONE prod_database;

-- Run automated tests
USE DATABASE staging_database;
-- ... test suite ...

-- Discard after testing (no impact on prod)
DROP DATABASE staging_database;
```

**3. Data Backup & Recovery**:
```sql
-- Pre-migration backup
CREATE DATABASE backup_pre_migration CLONE prod_database;

-- Risky operation
USE DATABASE prod_database;
-- ... perform migration ...

-- If migration fails, restore is instant
DROP DATABASE prod_database;
CREATE DATABASE prod_database CLONE backup_pre_migration;
```

**4. Experimentation**:
```sql
-- Clone for data science experiment
CREATE TABLE ds_experiment.customer_features
    CLONE prod.customers;

-- Try different feature engineering approaches
ALTER TABLE ds_experiment.customer_features
    ADD COLUMN lifetime_value NUMBER;

UPDATE ds_experiment.customer_features
SET lifetime_value = (SELECT SUM(amount) FROM orders ...);

-- Validate results, then apply to production
```

**5. Reporting & Analytics**:
```sql
-- Clone at specific point for consistent reporting
CREATE DATABASE monthly_report_feb CLONE prod_database
    AT (TIMESTAMP => '2024-02-29 23:59:59'::timestamp);

-- Generate reports from frozen snapshot
USE DATABASE monthly_report_feb;
SELECT SUM(revenue) FROM sales WHERE month = 'February';

-- Keep as historical reference (minimal storage cost)
```

### Cloning Performance & Costs

**Performance**:
```sql
-- Cloning is O(1) time - instant regardless of size

-- Clone 10GB database: ~5 seconds
CREATE DATABASE small_clone CLONE small_db;

-- Clone 10TB database: ~5 seconds (same metadata operation)
CREATE DATABASE huge_clone CLONE huge_db;
```

**Storage Costs**:
```sql
-- Initial clone: 0 additional storage
CREATE TABLE backup.orders_clone CLONE prod.orders;  -- 0 bytes initially

-- After modifications: charge only for divergence
INSERT INTO backup.orders_clone VALUES (...);  -- New micro-partitions
UPDATE backup.orders_clone SET status = 'X';   -- Modified micro-partitions

-- Cost formula:
-- Total Storage = Original Data + Diverged Data in Clone

-- Example:
-- Original: 1TB
-- Modified 10% in clone → 100GB new/modified micro-partitions
-- Total Storage: 1TB (original) + 100GB (divergence) = 1.1TB
-- Cost: 1.1TB × $23/month = $25.30/month
```

---

## ⏰ Time Travel & Fail-safe

### Time Travel Overview

**What is Time Travel?**
- Query historical data as it existed at any point in the past
- Retention period: 0-90 days (depends on edition)
- Restore dropped tables/schemas/databases
- Clone data from past state

**Retention Periods**:
```
Standard Edition: 1 day (configurable to 0)
Enterprise Edition: 90 days (configurable 0-90)
Business Critical: 90 days (configurable 0-90)
```

### Time Travel Queries

**Query Historical Data**:
```sql
-- Query table as of specific timestamp
SELECT *
FROM customers AT (TIMESTAMP => '2024-03-01 10:30:00'::timestamp)
WHERE region = 'US-WEST';

-- Query using offset (5 minutes ago)
SELECT *
FROM orders AT (OFFSET => -60*5);  -- 5 minutes ago

-- Query before specific statement (by query ID)
SELECT *
FROM customers BEFORE (STATEMENT => '019b9ee5-0502-7312-0043-4d83001b916a');
```

**Compare Historical vs. Current**:
```sql
-- Find deleted records
SELECT *
FROM customers AT (TIMESTAMP => '2024-03-08 09:00:00'::timestamp)
WHERE customer_id NOT IN (SELECT customer_id FROM customers);

-- Audit changes
SELECT
    current.customer_id,
    historical.email AS old_email,
    current.email AS new_email
FROM customers current
JOIN customers AT (TIMESTAMP => '2024-03-07 00:00:00'::timestamp) historical
    ON current.customer_id = historical.customer_id
WHERE current.email != historical.email;
```

### Restoring Dropped Objects

**Undrop Table**:
```sql
-- Accidentally drop table
DROP TABLE IF EXISTS customers;

-- Restore it (within Time Travel period)
UNDROP TABLE customers;

-- Verify restoration
SELECT COUNT(*) FROM customers;
```

**Undrop Schema**:
```sql
-- Drop schema
DROP SCHEMA IF EXISTS analytics;

-- Restore schema and all contained objects
UNDROP SCHEMA analytics;
```

**Undrop Database**:
```sql
-- Drop entire database
DROP DATABASE IF EXISTS prod_database;

-- Restore database
UNDROP DATABASE prod_database;

-- All schemas, tables, views restored
```

**Handle Name Conflicts**:
```sql
-- Scenario: Dropped table, created new one with same name
DROP TABLE customers;
CREATE TABLE customers (id INT);  -- New table

-- Cannot undrop directly (name conflict)
-- Solution: Restore to different name
ALTER TABLE customers RENAME TO customers_new;
UNDROP TABLE customers;
ALTER TABLE customers RENAME TO customers_restored;
ALTER TABLE customers_new RENAME TO customers;
```

### Cloning from Historical Point

```sql
-- Clone table from 7 days ago
CREATE TABLE analytics.customers_last_week
    CLONE prod.customers
    AT (TIMESTAMP => DATEADD('day', -7, CURRENT_TIMESTAMP()));

-- Clone database from before migration
CREATE DATABASE prod_before_migration
    CLONE prod_database
    AT (TIMESTAMP => '2024-03-08 18:00:00'::timestamp);

-- Clone to analyze historical state
CREATE TABLE investigation.orders_snapshot
    CLONE prod.orders
    AT (OFFSET => -60*60);  -- 1 hour ago
```

### Configuring Time Travel

```sql
-- Set Time Travel retention at table level
CREATE TABLE important_data (
    id INT,
    value VARCHAR
) DATA_RETENTION_TIME_IN_DAYS = 90;  -- Enterprise+ only

-- Modify retention for existing table
ALTER TABLE customers
    SET DATA_RETENTION_TIME_IN_DAYS = 30;

-- Set retention at schema level (applied to new tables)
ALTER SCHEMA prod_schema
    SET DATA_RETENTION_TIME_IN_DAYS = 60;

-- Set retention at database level
ALTER DATABASE prod_database
    SET DATA_RETENTION_TIME_IN_DAYS = 45;

-- Disable Time Travel (reduce storage costs)
ALTER TABLE temp_staging_table
    SET DATA_RETENTION_TIME_IN_DAYS = 0;  -- No historical versions kept
```

### Fail-safe Period

**What is Fail-safe?**
- Additional 7-day recovery period after Time Travel expires
- Non-queryable (Snowflake Support only)
- Disaster recovery for catastrophic failures
- Automatic, cannot be disabled

**Timeline**:
```
Day 0: Current data
  ↓
Day 1-90: Time Travel period (user-accessible)
  ├─ Query historical data
  ├─ Clone from past
  └─ Undrop objects
  ↓
Day 91-97: Fail-safe period (Snowflake Support only)
  └─ Contact support for recovery (rare, emergency)
  ↓
Day 98+: Data permanently deleted
```

**Example Scenario**:
```sql
-- Day 0: Create table
CREATE TABLE critical_data (id INT) DATA_RETENTION_TIME_IN_DAYS = 90;

-- Day 30: Accidentally drop table
DROP TABLE critical_data;

-- Day 30-120: Can undrop or clone
UNDROP TABLE critical_data;  -- ✅ Success

-- Day 121: Time Travel expired, in Fail-safe
UNDROP TABLE critical_data;  -- ❌ Error: outside Time Travel
-- Must contact Snowflake Support for recovery

-- Day 128: Fail-safe expired
-- ❌ Data permanently deleted, no recovery possible
```

### Time Travel Storage Costs

```sql
-- Storage cost = current data + historical versions

-- Example:
-- Table size: 100GB
-- Daily change: 5GB modified
-- Retention: 30 days
-- Historical data: 30 days × 5GB = 150GB
-- Total storage: 100GB (current) + 150GB (historical) = 250GB

-- Query to estimate Time Travel storage
SELECT
    table_name,
    active_bytes / POWER(1024, 3) AS current_gb,
    time_travel_bytes / POWER(1024, 3) AS time_travel_gb,
    failsafe_bytes / POWER(1024, 3) AS failsafe_gb
FROM snowflake.account_usage.table_storage_metrics
WHERE schema_name = 'PROD_SCHEMA'
ORDER BY time_travel_gb DESC;
```

---

## 🤝 Secure Data Sharing

### Data Sharing Architecture

**Traditional Data Sharing**:
```
Provider                    Consumer
   │                            │
   └──> Export to S3/FTP ───────┘
        ├─ Copy entire dataset (expensive)
        ├─ Data becomes stale immediately
        ├─ Security risks during transfer
        └─ Complex access control
```

**Snowflake Secure Sharing**:
```
Provider Database          Consumer Account
   │                            │
   └──> Share (metadata) ───────┘
        ├─ Zero data copying
        ├─ Live, real-time access
        ├─ Provider controls access
        └─ Query from own warehouse (separate billing)
```

### Creating Data Shares

**Provider Side**:
```sql
-- Step 1: Create share
CREATE SHARE sales_data_share;

-- Step 2: Grant database access
GRANT USAGE ON DATABASE prod_database TO SHARE sales_data_share;

-- Step 3: Grant schema access
GRANT USAGE ON SCHEMA prod_database.analytics TO SHARE sales_data_share;

-- Step 4: Grant table access
GRANT SELECT ON TABLE prod_database.analytics.sales
    TO SHARE sales_data_share;

GRANT SELECT ON TABLE prod_database.analytics.customers
    TO SHARE sales_data_share;

-- Step 5: Add consumer accounts
ALTER SHARE sales_data_share
    ADD ACCOUNTS = ABC12345, XYZ67890;  -- Consumer account identifiers

-- View share details
SHOW GRANTS TO SHARE sales_data_share;
DESC SHARE sales_data_share;
```

**Secure Views for Selective Sharing**:
```sql
-- Share only aggregated data (not raw records)
CREATE SECURE VIEW analytics.sales_summary AS
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    region,
    product_category,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count
FROM analytics.sales
GROUP BY 1, 2, 3;

-- Share view instead of table
GRANT SELECT ON VIEW analytics.sales_summary TO SHARE sales_data_share;

-- Consumer sees only aggregated data
```

**Row Access Policies for Sharing**:
```sql
-- Create row access policy
CREATE ROW ACCESS POLICY regional_access AS (region VARCHAR) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ACCOUNT() = 'ABC12345' THEN region = 'US-WEST'
        WHEN CURRENT_ACCOUNT() = 'XYZ67890' THEN region = 'EU-CENTRAL'
        ELSE FALSE
    END;

-- Apply policy to shared table
ALTER TABLE analytics.sales
    ADD ROW ACCESS POLICY regional_access ON (region);

-- Share table (each consumer sees only their region)
GRANT SELECT ON TABLE analytics.sales TO SHARE sales_data_share;
```

### Consumer Side

**Access Shared Data**:
```sql
-- Step 1: View available shares (from provider)
SHOW SHARES;

-- Step 2: Create database from share
CREATE DATABASE external_sales_data
    FROM SHARE PROVIDER_ACCOUNT.sales_data_share;

-- Step 3: Query shared data (using consumer's warehouse)
USE WAREHOUSE my_warehouse;  -- Consumer's compute
SELECT * FROM external_sales_data.analytics.sales;

-- Provider controls data, consumer pays for compute
```

**Consumer Isolation**:
```
Provider Account:
  └─ Database: prod_database
      └─ Table: sales (1TB)

Consumer A Account:
  └─ Database: external_sales (from share)
      └─ Warehouse: consumer_wh (10 credits/hour)
          └─ Queries sales table

Consumer B Account:
  └─ Database: partner_sales (from share)
      └─ Warehouse: partner_wh (5 credits/hour)
          └─ Queries sales table

Isolation:
- Same underlying data (1TB storage, provider pays)
- Separate compute (consumers pay for own warehouses)
- No data duplication
- Real-time updates both see
```

### Snowflake Data Marketplace

**Listing Data Products**:
```sql
-- Providers can list data in Marketplace
-- 1. Create share with sample data
CREATE SHARE marketplace_weather_data;
GRANT USAGE ON DATABASE weather_db TO SHARE marketplace_weather_data;
GRANT SELECT ON TABLE weather_db.public.forecasts
    TO SHARE marketplace_weather_data;

-- 2. Submit to Snowflake Marketplace
-- (via Web UI: Shares → Publish to Marketplace)
-- 3. Set pricing (free, paid, usage-based)
```

**Consuming Marketplace Data**:
```sql
-- Browse Marketplace (Web UI: Data → Marketplace)
-- Install free or paid datasets

-- Example: Install free COVID-19 dataset
CREATE DATABASE covid19_data
    FROM SHARE <marketplace_provider>.covid19_share;

-- Query instantly
SELECT *
FROM covid19_data.public.cases
WHERE country = 'United States'
ORDER BY date DESC
LIMIT 10;
```

### Use Cases for Data Sharing

**1. Multi-Tenant SaaS Applications**:
```sql
-- Provider (SaaS vendor) shares tenant-specific data

CREATE SHARE tenant_a_share;
CREATE SHARE tenant_b_share;

-- Tenant A sees only their data
CREATE SECURE VIEW tenant_a_view AS
SELECT * FROM saas_data.customers WHERE tenant_id = 'TENANT_A';

GRANT SELECT ON VIEW tenant_a_view TO SHARE tenant_a_share;
ALTER SHARE tenant_a_share ADD ACCOUNTS = TENANT_A_ACCOUNT;

-- Tenant B sees only their data
CREATE SECURE VIEW tenant_b_view AS
SELECT * FROM saas_data.customers WHERE tenant_id = 'TENANT_B';

GRANT SELECT ON VIEW tenant_b_view TO SHARE tenant_b_share;
ALTER SHARE tenant_b_share ADD ACCOUNTS = TENANT_B_ACCOUNT;
```

**2. Partner/Vendor Collaboration**:
```sql
-- Share inventory data with suppliers
CREATE SHARE supplier_inventory_share;
GRANT SELECT ON TABLE inventory.stock_levels TO SHARE supplier_inventory_share;
ALTER SHARE supplier_inventory_share ADD ACCOUNTS = SUPPLIER_ACCOUNT;

-- Supplier can check inventory in real-time (no API needed)
```

**3. Data Monetization**:
```sql
-- Sell financial data to subscribers
CREATE SHARE premium_financial_data;
GRANT SELECT ON TABLE market_data.stock_prices TO SHARE premium_financial_data;
GRANT SELECT ON TABLE market_data.fundamentals TO SHARE premium_financial_data;

-- Add paying customers
ALTER SHARE premium_financial_data ADD ACCOUNTS = SUBSCRIBER_1, SUBSCRIBER_2;

-- Charge based on usage via Snowflake Marketplace
```

---

## 🌊 Streams & Tasks

### Streams (Change Data Capture)

**What are Streams?**
- Track DML changes (INSERT, UPDATE, DELETE) on tables
- Enable incremental processing (CDC pattern)
- Consume changes without re-processing entire table
- Automatically managed change tracking

**Stream Types**:
1. **Standard Stream**: Tracks inserts, updates, deletes (w/ before/after)
2. **Append-Only Stream**: Tracks inserts only (simplest, cheapest)
3. **Insert-Only Stream**: Alias for append-only

**Creating Streams**:
```sql
-- Standard stream (full CDC)
CREATE STREAM orders_stream ON TABLE prod.orders;

-- Append-only stream (inserts only)
CREATE STREAM orders_insert_stream ON TABLE prod.orders
    APPEND_ONLY = TRUE;

-- Stream on view
CREATE STREAM customer_view_stream ON VIEW analytics.customer_summary;

-- Stream on external table
CREATE STREAM s3_data_stream ON EXTERNAL TABLE external.s3_orders;
```

**Reading Stream Data**:
```sql
-- Query stream (shows changes since last consumption)
SELECT
    *,
    METADATA$ACTION AS dml_action,         -- INSERT, DELETE
    METADATA$ISUPDATE AS is_update,        -- TRUE/FALSE
    METADATA$ROW_ID AS row_id              -- Unique change ID
FROM orders_stream;

-- Example output:
/*
order_id | customer_id | amount | dml_action | is_update
---------|-------------|--------|------------|----------
101      | 50          | 99.99  | INSERT     | FALSE
102      | 51          | 149.50 | INSERT     | FALSE
100      | 49          | 75.00  | DELETE     | FALSE
*/
```

**Consuming (Processing) Stream**:
```sql
-- Incremental processing
BEGIN TRANSACTION;

-- Process changes
INSERT INTO analytics.orders_summary (order_id, customer_id, amount)
SELECT order_id, customer_id, amount
FROM orders_stream
WHERE METADATA$ACTION = 'INSERT';

-- Mark changes as consumed (stream advances offset)
COMMIT;

-- Stream is now empty (until new changes occur)
SELECT COUNT(*) FROM orders_stream;  -- Returns 0
```

**Advanced CDC Pattern**:
```sql
-- Handle inserts, updates, deletes
MERGE INTO analytics.orders_summary target
USING (
    SELECT
        order_id,
        customer_id,
        amount,
        METADATA$ACTION AS action,
        METADATA$ISUPDATE AS is_update
    FROM orders_stream
) source
ON target.order_id = source.order_id
WHEN MATCHED AND source.action = 'DELETE' THEN
    DELETE
WHEN MATCHED AND source.action = 'INSERT' AND source.is_update = TRUE THEN
    UPDATE SET
        customer_id = source.customer_id,
        amount = source.amount,
        updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED AND source.action = 'INSERT' THEN
    INSERT (order_id, customer_id, amount, created_at)
    VALUES (source.order_id, source.customer_id, source.amount, CURRENT_TIMESTAMP());
```

### Tasks (Scheduling & Orchestration)

**What are Tasks?**
- Scheduled SQL statements or stored procedures
- Can trigger on schedule (cron) or when stream has data
- Build DAGs of dependent tasks
- Serverless compute option (no warehouse needed)

**Creating Tasks**:
```sql
-- Simple scheduled task (every hour)
CREATE TASK hourly_summary_task
    WAREHOUSE = etl_wh
    SCHEDULE = '60 MINUTE'
AS
    INSERT INTO analytics.hourly_sales_summary
    SELECT
        DATE_TRUNC('hour', sale_timestamp) AS hour,
        SUM(amount) AS total_sales
    FROM prod.sales
    WHERE sale_timestamp >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
    GROUP BY 1;

-- Enable task (tasks are suspended by default)
ALTER TASK hourly_summary_task RESUME;
```

**Cron-Based Schedule**:
```sql
-- Daily at 3 AM UTC
CREATE TASK daily_cleanup_task
    WAREHOUSE = maintenance_wh
    SCHEDULE = 'USING CRON 0 3 * * * UTC'
AS
    DELETE FROM staging.temp_data
    WHERE created_at < DATEADD('day', -7, CURRENT_TIMESTAMP());

-- Every 15 minutes
CREATE TASK frequent_sync_task
    WAREHOUSE = sync_wh
    SCHEDULE = 'USING CRON */15 * * * * UTC'
AS
    CALL sync_external_data_proc();
```

**Stream-Triggered Task**:
```sql
-- Trigger only when stream has new data
CREATE TASK process_orders_task
    WAREHOUSE = etl_wh
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')  -- Conditional execution
AS
    MERGE INTO analytics.orders_summary target
    USING orders_stream source
    ON target.order_id = source.order_id
    WHEN MATCHED THEN UPDATE SET ...
    WHEN NOT MATCHED THEN INSERT ...;

ALTER TASK process_orders_task RESUME;
```

**Task DAGs (Dependencies)**:
```sql
-- Root task (runs first)
CREATE TASK extract_task
    WAREHOUSE = etl_wh
    SCHEDULE = '60 MINUTE'
AS
    COPY INTO staging.raw_sales FROM @s3_stage/sales/;

-- Child task (runs after extract_task succeeds)
CREATE TASK transform_task
    WAREHOUSE = etl_wh
    AFTER extract_task  -- Dependency
AS
    CREATE OR REPLACE TABLE staging.transformed_sales AS
    SELECT * FROM staging.raw_sales WHERE amount > 0;

-- Grandchild task (runs after transform_task succeeds)
CREATE TASK load_task
    WAREHOUSE = etl_wh
    AFTER transform_task  -- Dependency
AS
    MERGE INTO analytics.sales target
    USING staging.transformed_sales source
    ON target.sale_id = source.sale_id
    WHEN MATCHED THEN UPDATE SET ...
    WHEN NOT MATCHED THEN INSERT ...;

-- Resume tasks (must resume child before parent)
ALTER TASK load_task RESUME;
ALTER TASK transform_task RESUME;
ALTER TASK extract_task RESUME;  -- Root task last
```

**Serverless Tasks** (no warehouse needed):
```sql
-- Task runs on Snowflake-managed compute
CREATE TASK serverless_task
    USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'  -- Serverless
    SCHEDULE = '10 MINUTE'
AS
    INSERT INTO logs.task_execution_log
    VALUES (CURRENT_TIMESTAMP(), 'Task executed');

-- Benefits:
-- - No warehouse management
-- - Auto-scales compute
-- - Pay only for actual execution time
-- - Cost: ~$0.17 per compute-second
```

**Task Management**:
```sql
-- View tasks
SHOW TASKS;
SHOW TASKS LIKE 'etl%';

-- Task details
DESCRIBE TASK hourly_summary_task;

-- Task history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => 'HOURLY_SUMMARY_TASK',
    SCHEDULED_TIME_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
ORDER BY scheduled_time DESC;

-- Suspend task
ALTER TASK hourly_summary_task SUSPEND;

-- Modify task schedule
ALTER TASK hourly_summary_task SET SCHEDULE = '30 MINUTE';

-- Drop task
DROP TASK IF EXISTS old_task;
```

---

## 📥 Snowpipe

### What is Snowpipe?

**Snowpipe** = Serverless, event-driven data ingestion service

**Characteristics**:
- Continuous, micro-batch loading (not batch ETL)
- Event-driven (S3/Azure/GCS file notifications)
- Serverless compute (no warehouse needed)
- Sub-minute latency
- Cost: $0.06 per 1,000 files processed

### Snowpipe Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Cloud Storage (S3/Azure Blob/GCS)                      │
│  ├─ folder/file_001.csv    (landed)                     │
│  ├─ folder/file_002.csv    (landed) ───┐                │
│  └─ folder/file_003.csv    (landed)    │                │
└────────────────────────────────────────┼────────────────┘
                                         │
                                         │ Event Notification
                                         ↓
          ┌──────────────────────────────────────────┐
          │  Snowpipe (Serverless Compute)           │
          │  ├─ Detects new files                    │
          │  ├─ Queues for loading                   │
          │  └─ Executes COPY INTO (micro-batches)   │
          └──────────────────────────────────────────┘
                         ↓
          ┌──────────────────────────────────────────┐
          │  Snowflake Table                         │
          │  (Data loaded continuously)              │
          └──────────────────────────────────────────┘
```

### Creating Snowpipe

**Step 1: Create Stage** (if not exists):
```sql
-- External stage pointing to S3
CREATE OR REPLACE STAGE s3_incoming_stage
    URL = 's3://my-bucket/incoming-data/'
    CREDENTIALS = (AWS_KEY_ID = 'xxx' AWS_SECRET_KEY = 'yyy')
    FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"');
```

**Step 2: Create Pipe**:
```sql
-- Pipe definition (COPY INTO command inside)
CREATE OR REPLACE PIPE orders_pipe
    AUTO_INGEST = TRUE  -- Enable event-driven loading
    AS
    COPY INTO prod.orders (order_id, customer_id, amount, order_date)
    FROM (
        SELECT
            $1::INTEGER,
            $2::INTEGER,
            $3::DECIMAL(10,2),
            $4::DATE
        FROM @s3_incoming_stage
    )
    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1)
    ON_ERROR = 'CONTINUE';  -- Skip bad records

-- Get pipe notification channel (for cloud provider integration)
DESC PIPE orders_pipe;
/*
notification_channel: arn:aws:sqs:us-east-1:123456789012:snowpipe-xxx
Use this SQS queue ARN to configure S3 event notifications
*/
```

**Step 3: Configure Cloud Event Notifications**:

For AWS S3:
```json
// S3 Bucket → Properties → Event Notifications
{
  "Event": ["s3:ObjectCreated:*"],
  "Prefix": "incoming-data/",
  "Destination": {
    "SQS": "arn:aws:sqs:us-east-1:123456789012:snowpipe-xxx"
  }
}
```

For Azure Blob:
```sql
-- Use Azure Event Grid subscription
-- Point to Snowpipe notification URL from DESC PIPE
```

### Using Snowpipe

**Manual Trigger** (for testing or REST API):
```sql
-- Manually trigger pipe to load specific files
ALTER PIPE orders_pipe REFRESH;

-- Load specific prefix
ALTER PIPE orders_pipe REFRESH PREFIX 'incoming-data/2024/03/';
```

**REST API Trigger** (for custom integrations):
```bash
# Insert files via REST API
curl -X POST \
  https://account.snowflakecomputing.com/v1/data/pipes/DB.SCHEMA.PIPE/insertFiles \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"path": "incoming-data/file_001.csv"},
      {"path": "incoming-data/file_002.csv"}
    ]
  }'
```

### Monitoring Snowpipe

**Pipe Status**:
```sql
-- View pipe details
SHOW PIPES;
DESC PIPE orders_pipe;

-- Check if pipe is running
SELECT SYSTEM$PIPE_STATUS('orders_pipe');
```

**Load History**:
```sql
-- Recent loads
SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'PROD.ORDERS',
    START_TIME => DATEADD('hours', -24, CURRENT_TIMESTAMP())
))
ORDER BY last_load_time DESC;

-- Files processed by pipe
SELECT *
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
    PIPE_NAME => 'ORDERS_PIPE',
    DATE_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
ORDER BY start_time DESC;
```

**Errors & Validation**:
```sql
-- Rows with errors
SELECT *
FROM TABLE(VALIDATE_PIPE_LOAD(
    PIPE_NAME => 'orders_pipe',
    START_TIME => DATEADD('hours', -1, CURRENT_TIMESTAMP())
))
WHERE ERROR_COUNT > 0;
```

### Snowpipe Cost & Optimization

**Pricing**:
```
Base Cost: $0.06 per 1,000 files processed
Compute: Serverless (included in base cost)

Example:
- 100,000 files/month → 100 × $0.06 = $6/month
- 1,000,000 files/month → 1,000 × $0.06 = $60/month
```

**Cost Optimization**:
```sql
-- 1. Batch small files before uploading
--    Single 100MB file < 100 × 1MB files (cost: $0.00006 vs $0.006)

-- 2. Use file format compression
FILE_FORMAT = (TYPE = 'CSV' COMPRESSION = 'GZIP')

-- 3. Filter files at stage level
CREATE PIPE filtered_pipe AS
COPY INTO prod.orders
FROM (
    SELECT * FROM @s3_stage
    WHERE METADATA$FILENAME LIKE '%orders%'  -- Only load relevant files
);
```

---

## 🗃️ External Tables

### What are External Tables?

**External Table** = Query data in S3/Azure/GCS without loading into Snowflake

**Use Cases**:
- Large historical archives (rarely queried)
- Data shared with other systems (avoid duplication)
- Cost optimization (query-only when needed)

**Trade-offs**:
```
Benefits:
✅ No storage cost in Snowflake
✅ Query data without loading
✅ Access multi-cloud data sources

Limitations:
❌ Slower than native tables (network I/O)
❌ No Time Travel or cloning
❌ No clustering or optimization
❌ Limited DML (read-only unless materialized)
```

### Creating External Tables

**Step 1: Create External Stage**:
```sql
-- S3 external stage
CREATE OR REPLACE EXTERNAL STAGE s3_archive_stage
    URL = 's3://my-data-lake/archive/'
    CREDENTIALS = (AWS_KEY_ID = 'xxx' AWS_SECRET_KEY = 'yyy');
```

**Step 2: Create External Table**:
```sql
-- External table (Parquet files)
CREATE OR REPLACE EXTERNAL TABLE external_sales
    WITH LOCATION = @s3_archive_stage/sales/
    FILE_FORMAT = (TYPE = 'PARQUET')
    PATTERN = '.*sales_.*[.]parquet'
    AUTO_REFRESH = TRUE  -- Automatically detect new files
    REFRESH_ON_CREATE = TRUE;

-- External table (CSV files with schema)
CREATE OR REPLACE EXTERNAL TABLE external_customers (
    customer_id INTEGER AS (VALUE:c1::INTEGER),
    name VARCHAR AS (VALUE:c2::VARCHAR),
    email VARCHAR AS (VALUE:c3::VARCHAR),
    created_date DATE AS (VALUE:c4::DATE)
)
    WITH LOCATION = @s3_archive_stage/customers/
    FILE_FORMAT = (TYPE = 'CSV')
    AUTO_REFRESH = FALSE;
```

**Step 3: Refresh Metadata** (if AUTO_REFRESH = FALSE):
```sql
-- Manually refresh to detect new files
ALTER EXTERNAL TABLE external_sales REFRESH;
```

### Querying External Tables

```sql
-- Query like normal table (slower due to remote reads)
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    SUM(amount) AS total_sales
FROM external_sales
WHERE sale_date >= '2023-01-01'
GROUP BY 1
ORDER BY 1;

-- Join external table with native table
SELECT
    c.name,
    SUM(s.amount) AS total_spent
FROM external_sales s
JOIN customers c ON s.customer_id = c.customer_id  -- Native table
WHERE s.sale_date >= '2024-01-01'
GROUP BY c.name;

-- Metadata columns
SELECT
    VALUE,                       -- Raw file content (JSON/Parquet)
    METADATA$FILENAME,          -- S3 file path
    METADATA$FILE_ROW_NUMBER    -- Row number within file
FROM external_sales
LIMIT 10;
```

### Materialized Views on External Tables

**Speed up queries by caching results**:
```sql
-- Create materialized view (data loaded into Snowflake)
CREATE MATERIALIZED VIEW external_sales_monthly AS
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    region,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count
FROM external_sales
GROUP BY 1, 2;

-- Query materialized view (fast, native Snowflake data)
SELECT * FROM external_sales_monthly
WHERE month >= '2024-01-01';

-- Storage cost: Only for materialized view data (aggregated, smaller)
```

---

## 🚀 Advanced Concepts

### Database Replication & Failover

```sql
-- Enable replication for disaster recovery
ALTER DATABASE prod_database ENABLE REPLICATION TO ACCOUNTS other_account;

-- In target account, create replica database
CREATE DATABASE prod_replica AS REPLICA OF source_account.prod_database;

-- Failover to replica (manual)
ALTER DATABASE prod_replica PRIMARY;
```

### Result Caching

**Automatic Result Caching**:
```sql
-- Enable (default)
ALTER SESSION SET USE_CACHED_RESULT = TRUE;

-- Same query within 24 hours = instant (0 compute cost)
SELECT COUNT(*) FROM large_table WHERE status = 'active';  -- 10 seconds, 2 credits
SELECT COUNT(*) FROM large_table WHERE status = 'active';  -- <1 second, 0 credits

-- Cache invalidated by:
-- 1. Table data changes
-- 2. 24-hour expiration
-- 3. Manual purge
```

### Query Acceleration Service

```sql
-- Enable query acceleration for BI dashboards
ALTER WAREHOUSE bi_wh SET ENABLE_QUERY_ACCELERATION = TRUE;

-- Automatically speeds up eligible queries (additional cost)
-- Best for: Dashboards with unpredictable scan patterns
```

### Search Optimization Service

```sql
-- Enable search optimization (for point lookups)
ALTER TABLE large_customers ADD SEARCH OPTIMIZATION;

-- Significantly faster for:
SELECT * FROM large_customers WHERE email = 'user@example.com';  -- Point lookup
SELECT * FROM large_customers WHERE name LIKE '%Smith%';         -- Substring search
```

---

## 📚 Summary

| Concept                | Key Benefit                        | Use Case                          |
|------------------------|------------------------------------|-----------------------------------|
| Virtual Warehouses     | Elastic, isolated compute          | Separate ETL/BI/DS workloads      |
| Zero-Copy Cloning      | Instant, free copies               | Dev/test environments             |
| Time Travel            | Query/restore historical data      | Auditing, recovery, compliance    |
| Secure Data Sharing    | Zero-copy, real-time sharing       | Partner collaboration, SaaS       |
| Streams & Tasks        | CDC + orchestration                | Incremental ETL pipelines         |
| Snowpipe               | Continuous, event-driven loading   | Real-time data ingestion          |
| External Tables        | Query without loading              | Cost optimization, data lakes     |

---

**Next Steps**:
1. Review [setup-guide.md](setup-guide.md) for hands-on environment setup
2. Follow exercises to practice each concept
3. Explore [best-practices.md](best-practices.md) for production guidance

**Last Updated**: March 2026
**Module**: Bonus 02 - Snowflake Data Cloud
