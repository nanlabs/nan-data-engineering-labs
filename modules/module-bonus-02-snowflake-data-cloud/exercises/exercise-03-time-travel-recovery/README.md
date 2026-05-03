# Exercise 03: Time Travel Recovery

## Overview
Implement disaster recovery strategies using Time Travel and Fail-safe to protect against data loss, corruption, and accidental deletions.

**Estimated Time**: 2.5 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Exercise 02 (Cloning), understanding of disaster recovery concepts

---

## Learning Objectives
By completing this exercise, you will be able to:
- Query historical data at specific timestamps and offsets
- Recover dropped tables using UNDROP command
- Restore data to specific points in time using cloning
- Configure data retention periods (Standard vs Enterprise)
- Implement comprehensive disaster recovery plans
- Calculate storage costs for historical data retention

---

## Scenario
**Production Incident Alert!**

Your e-commerce platform experienced a critical data incident:
- **10:00 AM**: Normal operations, 50,000 orders in database
- **10:15 AM**: Developer runs test DELETE query... against production table (Oops!)
- **10:20 AM**: Dashboards show zero revenue, customers complaining
- **10:30 AM**: Table accidentally DROPPED during panic recovery attempt
- **10:35 AM**: You're called to recover all data from 09:45 AM (before any issues)

Mission: Demonstrate Time Travel and recovery capabilities to restore the business.

---

## Requirements

### Task 1: Setup & Baseline (20 min)
Create production tables and establish baseline for recovery testing.

**Database Setup**:
```sql
-- Create production database
CREATE DATABASE PROD_RECOVERY_TEST;
USE DATABASE PROD_RECOVERY_TEST;
CREATE SCHEMA sales;
USE SCHEMA sales;
```

**Create Orders Table**:
```sql
CREATE TABLE orders (
    order_id INT,
    customer_id INT,
    order_date TIMESTAMP,
    order_total DECIMAL(10,2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**Load Baseline Data** (1,000 orders):
```sql
INSERT INTO orders
SELECT
    seq4() as order_id,
    uniform(1, 500, random()) as customer_id,
    dateadd(hour, -uniform(1, 720, random()), current_timestamp()) as order_date,
    uniform(10, 1000, random()) as order_total,
    CASE uniform(1, 5, random())
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'processing'
        WHEN 3 THEN 'shipped'
        WHEN 4 THEN 'delivered'
        ELSE 'cancelled'
    END as status,
    current_timestamp() as created_at
FROM table(generator(rowcount => 1000));
```

**Record Baseline Metrics**:
```sql
-- Save baseline for later comparison
CREATE TABLE baseline_metrics AS
SELECT
    COUNT(*) as total_orders,
    SUM(order_total) as total_revenue,
    COUNT(DISTINCT customer_id) as unique_customers,
    MIN(order_date) as earliest_order,
    MAX(order_date) as latest_order,
    current_timestamp() as snapshot_time
FROM orders;

SELECT * FROM baseline_metrics;
```

**Success Criteria**:
- ✅ Production database and schema created
- ✅ Orders table contains exactly 1,000 rows
- ✅ Baseline metrics recorded for comparison
- ✅ All order_total values are positive numbers

---

### Task 2: Historical Queries (30 min)
Practice querying data at different points in time.

**Query 1: Current State**:
```sql
-- Current data
SELECT COUNT(*) as current_count FROM orders;
```

**Simulate Time-Based Changes**:
```sql
-- Snapshot 1: Add 100 orders
INSERT INTO orders
SELECT
    seq4() + 1000 as order_id,
    uniform(1, 500, random()) as customer_id,
    dateadd(hour, -uniform(1, 24, random()), current_timestamp()) as order_date,
    uniform(10, 1000, random()) as order_total,
    'processing' as status,
    current_timestamp() as created_at
FROM table(generator(rowcount => 100));

-- Record timestamp
SET snapshot1_time = CURRENT_TIMESTAMP();

-- Wait a moment, then Snapshot 2: Update 50 orders
UPDATE orders
SET status = 'delivered',
    order_total = order_total * 1.1
WHERE order_id <= 50;

SET snapshot2_time = CURRENT_TIMESTAMP();

-- Snapshot 3: Delete 25 orders
DELETE FROM orders WHERE order_id BETWEEN 51 AND 75;

SET snapshot3_time = CURRENT_TIMESTAMP();
```

**Query 2: Historical Queries with AT**:
```sql
-- Query from 1 hour ago
SELECT COUNT(*) as count_1h_ago
FROM orders AT(OFFSET => -3600);

-- Query from 30 minutes ago
SELECT COUNT(*) as count_30min_ago
FROM orders AT(OFFSET => -1800);

-- Query from specific timestamp (snapshot1)
SELECT COUNT(*) as count_at_snapshot1
FROM orders AT(TIMESTAMP => $snapshot1_time);

-- Compare changes over time
SELECT
    'Current' as timepoint,
    COUNT(*) as row_count,
    SUM(order_total) as revenue
FROM orders
UNION ALL
SELECT
    '1 hour ago' as timepoint,
    COUNT(*) as row_count,
    SUM(order_total) as revenue
FROM orders AT(OFFSET => -3600)
UNION ALL
SELECT
    'Snapshot 1' as timepoint,
    COUNT(*) as row_count,
    SUM(order_total) as revenue
FROM orders AT(TIMESTAMP => $snapshot1_time);
```

**Query 3: Track Specific Row Changes**:
```sql
-- See how order_id=10 changed over time
SELECT
    order_id,
    status,
    order_total,
    'Current' as version
FROM orders
WHERE order_id = 10
UNION ALL
SELECT
    order_id,
    status,
    order_total,
    'Snapshot 1' as version
FROM orders AT(TIMESTAMP => $snapshot1_time)
WHERE order_id = 10
UNION ALL
SELECT
    order_id,
    status,
    order_total,
    'Snapshot 2' as version
FROM orders AT(TIMESTAMP => $snapshot2_time)
WHERE order_id = 10;
```

**Use DESCRIBE HISTORY**:
```sql
-- View complete history of changes
SELECT
    query_id,
    query_text,
    rows_inserted,
    rows_updated,
    rows_deleted,
    bytes_written,
    created_on
FROM TABLE(information_schema.query_history())
WHERE query_text LIKE '%orders%'
    AND query_type IN ('INSERT', 'UPDATE', 'DELETE')
ORDER BY created_on DESC
LIMIT 20;
```

**Success Criteria**:
- ✅ Successfully queried data from 3 different timestamps
- ✅ Tracked changes to specific rows over time
- ✅ Used both AT(OFFSET) and AT(TIMESTAMP) syntax correctly
- ✅ DESCRIBE HISTORY shows all modifications

---

### Task 3: Accidental Delete (20 min)
Simulate and recover from accidental data deletion.

**The Accident**:
```sql
-- Developer meant to run:
-- DELETE FROM dev.orders WHERE status = 'cancelled';

-- But accidentally ran against production:
DELETE FROM orders WHERE status = 'cancelled';

-- Panic! How many rows deleted?
SELECT
    'Rows before delete' as description,
    (SELECT COUNT(*) FROM orders AT(OFFSET => -60)) as count
UNION ALL
SELECT
    'Rows after delete' as description,
    COUNT(*) as count
FROM orders;
```

**Recovery Option 1: UNDROP (if table dropped)**:
```sql
-- Worst case: Someone dropped the table
DROP TABLE orders;

-- Verify table is gone
SHOW TABLES LIKE 'orders';

-- 😱 Panic! But wait...
-- UNDROP restores the table (within retention period)
UNDROP TABLE orders;

-- Verify recovery
SELECT COUNT(*) FROM orders;
```

**Recovery Option 2: Restore from History**:
```sql
-- If data deleted but table still exists:
-- Strategy 1: Create backup from before delete
CREATE TABLE orders_backup CLONE orders
AT(OFFSET => -300);  -- 5 minutes ago

-- Strategy 2: Replace current with historical
CREATE OR REPLACE TABLE orders CLONE orders
AT(OFFSET => -300);

-- Or more surgically, insert deleted rows back
INSERT INTO orders
SELECT * FROM orders AT(OFFSET => -300)
WHERE status = 'cancelled';
```

**Verify Recovery**:
```sql
-- Compare with baseline
SELECT
    'Baseline' as source,
    total_orders,
    total_revenue
FROM baseline_metrics
UNION ALL
SELECT
    'After Recovery' as source,
    COUNT(*) as total_orders,
    SUM(order_total) as total_revenue
FROM orders;
```

**Success Criteria**:
- ✅ Successfully simulated accidental deletion
- ✅ Used UNDROP to restore dropped table
- ✅ Restored deleted data using historical cloning
- ✅ Verified recovery matches baseline counts

---

### Task 4: Point-in-Time Recovery (30 min)
Recover from data corruption to specific timestamp.

**Scenario**:
```sql
-- 09:45 AM: Good data (baseline)
CREATE TABLE orders_0945 CLONE orders AT(OFFSET => -7200);

-- 10:00 AM: Data corruption begins
-- Bad ETL pipeline multiplies all order totals by 100
UPDATE orders
SET order_total = order_total * 100
WHERE order_id <= 500;

-- 10:15 AM: More corruption
UPDATE orders
SET status = 'ERROR',
    customer_id = -1
WHERE order_id BETWEEN 501 AND 750;

-- 10:30 AM: Discovery!
-- Need to restore to 09:45 AM state
```

**Recovery Plan**:

1. **Identify Corruption Scope**:
   ```sql
   -- Find affected rows
   SELECT
       COUNT(*) as corrupted_count,
       AVG(order_total) as avg_total,
       COUNT(DISTINCT status) as status_count
   FROM orders
   WHERE order_total > 5000  -- Suspiciously high
       OR status = 'ERROR';
   ```

2. **Get Query ID of Corruption**:
   ```sql
   -- Find the problematic UPDATE
   SELECT
       query_id,
       query_text,
       start_time,
       rows_updated
   FROM TABLE(information_schema.query_history())
   WHERE query_text LIKE '%order_total = order_total * 100%'
   ORDER BY start_time DESC
   LIMIT 1;

   SET corruption_query_id = 'query_id_here';
   ```

3. **Clone Before Corruption**:
   ```sql
   -- Option 1: Clone from specific timestamp (09:45 AM)
   CREATE OR REPLACE TABLE orders_recovered
   CLONE orders
   AT(TIMESTAMP => '2026-03-09 09:45:00'::TIMESTAMP);

   -- Option 2: Clone before corrupting statement
   CREATE OR REPLACE TABLE orders_recovered
   CLONE orders
   BEFORE(STATEMENT => $corruption_query_id);
   ```

4. **Validate Recovery**:
   ```sql
   -- Compare recovered data to corrupted current
   SELECT
       'Corrupted Current' as version,
       COUNT(*) as total_orders,
       AVG(order_total) as avg_amount,
       MAX(order_total) as max_amount,
       COUNT(CASE WHEN status = 'ERROR' THEN 1 END) as error_count
   FROM orders
   UNION ALL
   SELECT
       'Recovered (09:45)' as version,
       COUNT(*) as total_orders,
       AVG(order_total) as avg_amount,
       MAX(order_total) as max_amount,
       COUNT(CASE WHEN status = 'ERROR' THEN 1 END) as error_count
   FROM orders_recovered;
   ```

5. **Atomic Swap**:
   ```sql
   -- Swap recovered table with current (atomic operation)
   ALTER TABLE orders RENAME TO orders_corrupted_backup;
   ALTER TABLE orders_recovered RENAME TO orders;

   -- Verify
   SELECT COUNT(*) FROM orders;  -- Should match baseline
   ```

**Success Criteria**:
- ✅ Identified corruption scope and timing
- ✅ Used BEFORE(STATEMENT) to clone before corruption
- ✅ Validated recovery data matches 09:45 AM baseline
- ✅ Performed atomic table swap
- ✅ Kept corrupted data as backup for analysis

---

### Task 5: Retention Configuration (20 min)
Configure and understand data retention periods.

**Default Retention**:
```sql
-- Check current retention
SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' IN ACCOUNT;

-- Default: 1 day (Standard Edition)
-- Enterprise: Up to 90 days configurable
```

**Configure Table-Level Retention**:
```sql
-- Set extended retention for critical table
ALTER TABLE orders
SET DATA_RETENTION_TIME_IN_DAYS = 7;

-- Verify retention setting
SHOW TABLES LIKE 'orders';
-- Look for DATA_RETENTION_TIME_IN_DAYS column
```

**Configure Database-Level Retention**:
```sql
-- Set retention for entire database
ALTER DATABASE PROD_RECOVERY_TEST
SET DATA_RETENTION_TIME_IN_DAYS = 14;

-- All tables inherit this unless overridden
```

**Test Retention Limits**:
```sql
-- Try to query beyond retention period
-- This will fail if data is outside retention window
SELECT COUNT(*)
FROM orders
AT(OFFSET => -172800);  -- 2 days ago (fails if retention is 1 day)

-- Check retention limit
SELECT
    table_catalog,
    table_schema,
    table_name,
    retention_time
FROM information_schema.tables
WHERE table_name = 'ORDERS';
```

**Understand Fail-safe**:
```text
Time Travel: 1-90 days (configurable, queryable)
   ↓
Fail-safe: Additional 7 days (not queryable, Snowflake-only recovery)
   ↓
Permanent deletion
```

**Calculate Storage Impact**:
```sql
-- Estimate Time Travel storage costs
SELECT
    table_name,
    active_bytes / (1024*1024*1024) as active_gb,
    time_travel_bytes / (1024*1024*1024) as time_travel_gb,
    failsafe_bytes / (1024*1024*1024) as failsafe_gb,
    retention_time,
    -- Estimate monthly cost increase for extended retention
    (time_travel_bytes / (1024*1024*1024*1024)) * 40 * (retention_time / 1.0) as monthly_cost_usd
FROM snowflake.account_usage.table_storage_metrics
WHERE table_name = 'ORDERS'
ORDER BY time_travel_bytes DESC;
```

**Success Criteria**:
- ✅ Configured table-level retention (7 days)
- ✅ Configured database-level retention (14 days)
- ✅ Verified retention settings with SHOW command
- ✅ Understood difference between Time Travel and Fail-safe
- ✅ Calculated storage cost impact of extended retention

---

### Task 6: Disaster Recovery Plan (30 min)
Document comprehensive recovery procedures for 5 scenarios.

**Scenario 1: Accidental Table Drop**:
```sql
-- Recovery Procedure
-- Step 1: Verify table dropped
SHOW TABLES LIKE 'critical_table';

-- Step 2: Undrop immediately (within retention period)
UNDROP TABLE critical_table;

-- Step 3: Verify data integrity
SELECT COUNT(*), MAX(created_at) FROM critical_table;

-- Step 4: Review access logs
SELECT * FROM snowflake.account_usage.query_history
WHERE query_text ILIKE '%DROP TABLE critical_table%'
ORDER BY start_time DESC;

-- RTO: < 5 minutes
-- RPO: 0 (no data loss)
```

**Scenario 2: Mass Data Deletion**:
```sql
-- Recovery Procedure
-- Step 1: Identify deletion scope
SELECT COUNT(*) as deleted_rows
FROM critical_table AT(OFFSET => -300)
WHERE ...

-- Step 2: Clone from before deletion
CREATE TABLE critical_table_backup CLONE critical_table;
CREATE OR REPLACE TABLE critical_table
CLONE critical_table AT(OFFSET => -300);

-- Step 3: Validate recovery
-- Compare row counts, checksums

-- RTO: < 10 minutes
-- RPO: 5 minutes (time to identify and restore)
```

**Scenario 3: Data Corruption**:
```sql
-- Recovery Procedure
-- Step 1: Find corruption timestamp
SELECT query_id, start_time, query_text
FROM snowflake.account_usage.query_history
WHERE query_text LIKE '%UPDATE critical_table%'
ORDER BY start_time DESC;

-- Step 2: Clone before corruption
CREATE TABLE clean_data
CLONE critical_table
BEFORE(STATEMENT => 'query_id');

-- Step 3: Validate clean data
-- Step 4: Atomic swap
ALTER TABLE critical_table RENAME TO corrupted_backup;
ALTER TABLE clean_data RENAME TO critical_table;

-- RTO: < 15 minutes
-- RPO: 0 (exact point before corruption)
```

**Scenario 4: Schema Change Gone Wrong**:
```sql
-- Recovery Procedure
-- Step 1: Find schema change
SELECT query_id, query_text, start_time
FROM snowflake.account_usage.query_history
WHERE query_text ILIKE '%ALTER TABLE%'
ORDER BY start_time DESC;

-- Step 2: Create clone with old schema
CREATE TABLE critical_table_old_schema
CLONE critical_table
BEFORE(STATEMENT => 'alter_query_id');

-- Step 3: Drop current, restore old
DROP TABLE critical_table;
UNDROP TABLE critical_table;  -- If needed
CREATE TABLE critical_table CLONE critical_table_old_schema;

-- RTO: < 10 minutes
-- RPO: 0
```

**Scenario 5: Complete Database Recovery**:
```sql
-- Recovery Procedure
-- Step 1: Assess scope (entire database)
-- Step 2: Clone entire database
CREATE DATABASE PROD_DB_RECOVERY
CLONE PROD_DB
AT(TIMESTAMP => '2026-03-09 09:00:00'::TIMESTAMP);

-- Step 3: Validate all schemas and tables
-- Step 4: Coordinate switchover
-- - Update connection strings
-- - Notify users of maintenance window
-- - Rename databases atomically

-- RTO: < 30 minutes
-- RPO: Based on recovery point chosen
```

**Recovery Runbook Template**:
```markdown
# Disaster Recovery Runbook

## Scenario: [Description]

### Detection
- Symptoms: [How was issue discovered?]
- Affected objects: [Tables, schemas, databases]
- Impact: [Users affected, data loss extent]

### Pre-Recovery Checklist
- [ ] Notify incident commander
- [ ] Document current state
- [ ] Identify recovery point
- [ ] Estimate RTO/RPO

### Recovery Steps
1. [Step 1 with SQL]
2. [Step 2 with SQL]
3. [Validation step]

### Post-Recovery
- [ ] Validate data integrity
- [ ] Notify stakeholders
- [ ] Document root cause
- [ ] Update runbook

### Storage Costs
- Time Travel storage: [X GB]
- Retention period: [Y days]
- Monthly cost: [$Z]
```

**Create Automated Recovery Script**:
```sql
-- Stored procedure for common recovery
CREATE OR REPLACE PROCEDURE emergency_table_recovery(
    table_name STRING,
    minutes_back INT
)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Create backup of current state
    LET backup_name := table_name || '_corrupted_backup';
    CREATE OR REPLACE TABLE IDENTIFIER(:backup_name)
    CLONE IDENTIFIER(:table_name);

    -- Restore from history
    CREATE OR REPLACE TABLE IDENTIFIER(:table_name)
    CLONE IDENTIFIER(:table_name)
    AT(OFFSET => (:minutes_back * -60));

    RETURN 'Recovery complete: ' || table_name || ' restored to ' || minutes_back || ' minutes ago';
END;
$$;

-- Usage
CALL emergency_table_recovery('orders', 30);  -- Restore to 30 min ago
```

**Success Criteria**:
- ✅ Documented 5 disaster recovery scenarios with SQL
- ✅ Created recovery runbook template
- ✅ Calculated RTO/RPO for each scenario
- ✅ Estimated storage costs for retention policies
- ✅ Created automated recovery stored procedure

---

## Hints

<details>
<summary>Hint 1: Time Travel Syntax Reference</summary>

```sql
-- Query historical data
SELECT * FROM table_name AT(OFFSET => -3600);  -- 1 hour ago (seconds)
SELECT * FROM table_name AT(TIMESTAMP => '2026-03-09 10:00:00'::TIMESTAMP);
SELECT * FROM table_name BEFORE(STATEMENT => 'query_id_here');

-- Clone historical data
CREATE TABLE backup CLONE original AT(OFFSET => -7200);
CREATE TABLE backup CLONE original AT(TIMESTAMP => '2026-03-09'::TIMESTAMP);
CREATE TABLE backup CLONE original BEFORE(STATEMENT => 'query_id');

-- Get query history
SELECT query_id, query_text, start_time, rows_inserted, rows_deleted
FROM TABLE(information_schema.query_history())
WHERE query_text LIKE '%orders%'
ORDER BY start_time DESC;
```
</details>

<details>
<summary>Hint 2: UNDROP Conditions</summary>

```sql
-- Undrop table (within retention period)
UNDROP TABLE table_name;

-- Undrop schema
UNDROP SCHEMA schema_name;

-- Undrop database
UNDROP DATABASE database_name;

-- Check what can be undropped
SHOW TABLES HISTORY;
SHOW SCHEMAS HISTORY;
SHOW DATABASES HISTORY;

-- Note: Cannot undrop if:
-- 1. Retention period expired
-- 2. New object created with same name
-- 3. In Fail-safe period (need Snowflake support)
```
</details>

<details>
<summary>Hint 3: Retention Configuration</summary>

```sql
-- Check current retention
SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS';

-- Set account-level retention (requires ACCOUNTADMIN)
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 7;

-- Set database-level retention
ALTER DATABASE my_database SET DATA_RETENTION_TIME_IN_DAYS = 14;

-- Set table-level retention
ALTER TABLE my_table SET DATA_RETENTION_TIME_IN_DAYS = 30;

-- Remove custom retention (inherit from parent)
ALTER TABLE my_table UNSET DATA_RETENTION_TIME_IN_DAYS;

-- Limits:
-- Standard Edition: 0-1 days
-- Enterprise Edition: 0-90 days
```
</details>

<details>
<summary>Hint 4: Storage Cost Analysis</summary>

```sql
-- Table storage breakdown
SELECT
    table_catalog,
    table_schema,
    table_name,
    active_bytes / POWER(1024, 3) as active_gb,
    time_travel_bytes / POWER(1024, 3) as time_travel_gb,
    failsafe_bytes / POWER(1024, 3) as failsafe_gb,
    (active_bytes + time_travel_bytes + failsafe_bytes) / POWER(1024, 4) as total_tb,
    -- Estimate cost: $40 per TB per month
    ((active_bytes + time_travel_bytes + failsafe_bytes) / POWER(1024, 4)) * 40 as monthly_cost_usd
FROM snowflake.account_usage.table_storage_metrics
WHERE table_catalog = 'PROD_RECOVERY_TEST'
ORDER BY total_tb DESC;

-- Time Travel growth over time
SELECT
    usage_date,
    table_name,
    time_travel_bytes / POWER(1024, 3) as time_travel_gb
FROM snowflake.account_usage.table_storage_usage_history
WHERE table_name = 'ORDERS'
    AND usage_date >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY usage_date DESC;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-03-time-travel-recovery
bash validate.sh
```

**Expected Output**:
```
✅ Task 1: Baseline created (1,000 orders, metrics recorded)
✅ Task 2: Historical queries working (3 timestamps queried)
✅ Task 3: UNDROP successful (table restored)
✅ Task 4: Point-in-time recovery complete (data matches 09:45 AM)
✅ Task 5: Retention configured (7 days table, 14 days database)
✅ Task 6: 5 recovery scenarios documented (RTO < 15 min avg)

🎉 Exercise 03 Complete! Disaster Recovery Plan Ready
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All Time Travel queries and recovery commands
2. `disaster-recovery-runbook.md` - Complete runbook with 5 scenarios
3. `retention-cost-analysis.md` - Storage cost calculations for retention policies
4. Screenshot of successful UNDROP operation
5. Screenshot of BEFORE(STATEMENT) clone validation

---

## Resources
- Snowflake Documentation: [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel)
- Snowflake Documentation: [Fail-safe](https://docs.snowflake.com/en/user-guide/data-failsafe)
- Snowflake Documentation: [Undrop](https://docs.snowflake.com/en/sql-reference/sql/undrop-table)
- Notebook: `notebooks/03-time-travel.sql`
- Diagram: `assets/diagrams/time-travel-failsafe.mmd`
- Theory: `theory/concepts.md#time-travel`
- Theory: `theory/concepts.md#fail-safe`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 04: Data Sharing (secure data sharing without copies)
- ✅ Exercise 05: Snowpipe Automation (continuous data ingestion)
- Review Module 16: Data Security & Compliance for protection strategies
