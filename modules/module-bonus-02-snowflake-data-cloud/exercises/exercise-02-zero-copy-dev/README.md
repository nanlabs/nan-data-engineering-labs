# Exercise 02: Zero-Copy Dev Environments

## Overview
Use zero-copy cloning to create instant dev/test environments without duplicating storage, enabling isolated testing at minimal cost.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐ Intermediate
**Prerequisites**: Exercise 01 (Warehouse basics), understanding of storage costs

---

## Learning Objectives
By completing this exercise, you will be able to:
- Clone databases, schemas, and tables using zero-copy cloning
- Create instant dev/test environments from production data
- Track storage divergence and costs over time
- Implement historical cloning (from past timestamps)
- Design cost-effective dev/test strategies
- Understand when clones share storage vs. allocate new storage

---

## Scenario
Your production database is 10TB and growing. Your team needs:
- **Developers**: Isolated environments to test new features
- **QA Team**: Fresh production data for testing without affecting prod
- **Data Scientists**: Safe sandbox to explore and transform data
- **Training**: Realistic data for onboarding new team members

Traditional approach: Copy 10TB per environment = 40TB+ storage costs.
**Snowflake approach**: Clone 10TB instantly, share storage until modifications = minimal cost.

---

## Requirements

### Task 1: Production Setup (15 min)
Create a production database with realistic data.

**Database Structure**:
```sql
-- Create production database
CREATE DATABASE PROD_ECOMMERCE;
USE DATABASE PROD_ECOMMERCE;

-- Create schemas
CREATE SCHEMA sales;
CREATE SCHEMA inventory;
CREATE SCHEMA analytics;
```

**Load Sample Data**:
1. **CUSTOMERS** table (10,000 rows):
   - customer_id, name, email, country, signup_date, lifetime_value

2. **ORDERS** table (50,000 rows):
   - order_id, customer_id, order_date, order_total, status

3. **PRODUCTS** table (5,000 rows):
   - product_id, name, category, price, stock_quantity

**Data Generation**:
```sql
-- Use table generator for realistic volume
CREATE TABLE sales.customers AS
SELECT
    seq4() as customer_id,
    concat('Customer_', seq4()) as name,
    concat('user', seq4(), '@email.com') as email,
    -- ... more columns
FROM table(generator(rowcount => 10000));
```

**Success Criteria**:
- ✅ PROD_ECOMMERCE database created with 3 schemas
- ✅ 10,000 customers, 50,000 orders, 5,000 products loaded
- ✅ Verified row counts with `SELECT COUNT(*)`
- ✅ Documented total storage size from INFORMATION_SCHEMA

---

### Task 2: Clone Database (15 min)
Create instant copy of entire production database.

**Clone Operations**:
1. **Full Database Clone**:
   ```sql
   CREATE DATABASE DEV_ECOMMERCE CLONE PROD_ECOMMERCE;
   ```

2. **Verify Clone**:
   - Check all schemas exist
   - Verify row counts match production exactly
   - Confirm clone operation took < 5 seconds

3. **Measure Storage**:
   - Query storage before clone
   - Query storage immediately after clone
   - Observe: Clone uses **zero additional storage initially**

**Test Isolation**:
- Modify data in DEV_ECOMMERCE
- Verify PROD_ECOMMERCE unchanged
- Confirm databases are truly isolated

**Success Criteria**:
- ✅ Database cloned in < 5 seconds (instant regardless of size)
- ✅ All schemas and tables present in clone
- ✅ Row counts match production (10K, 50K, 5K)
- ✅ Zero additional storage used initially
- ✅ Modifications to clone don't affect production

---

### Task 3: Clone Tables (20 min)
Create granular clones at schema and table level.

**Cloning Scenarios**:

1. **Clone Single Table**:
   ```sql
   CREATE TABLE sales.dev_customers CLONE sales.customers;
   ```

2. **Clone Entire Schema**:
   ```sql
   CREATE SCHEMA dev_sales CLONE sales;
   ```

3. **Clone to Different Database**:
   ```sql
   CREATE TABLE test_db.sandbox.customers
   CLONE prod_ecommerce.sales.customers;
   ```

**Modification Testing**:
1. Update 1,000 rows in `dev_customers`
2. Insert 500 new rows in `dev_customers`
3. Delete 100 rows in `dev_customers`

**Verification**:
- Original `customers` table unchanged
- Clone has modifications
- Observe storage divergence beginning

**Cross-Database Access**:
```sql
-- Query differences between prod and dev
SELECT 'PROD' as source, COUNT(*) as row_count
FROM prod_ecommerce.sales.customers
UNION ALL
SELECT 'DEV' as source, COUNT(*) as row_count
FROM dev_ecommerce.sales.dev_customers;
```

**Success Criteria**:
- ✅ Created table-level and schema-level clones
- ✅ Modified clone without affecting original
- ✅ Verified isolation between clones
- ✅ Documented when to use database vs table clones

---

### Task 4: Historical Cloning (25 min)
Clone from past timestamps for debugging and recovery.

**Scenario**: Production data was correct 2 hours ago, but recent changes introduced issues.

**Historical Clone Operations**:

1. **Clone from Time Offset**:
   ```sql
   -- Clone from 1 hour ago
   CREATE DATABASE PROD_1H_AGO
   CLONE PROD_ECOMMERCE
   AT(OFFSET => -3600);  -- seconds

   -- Clone from 3 hours ago
   CREATE TABLE sales.customers_3h_ago
   CLONE sales.customers
   AT(OFFSET => -10800);
   ```

2. **Clone from Specific Timestamp**:
   ```sql
   -- Clone from exact timestamp
   CREATE DATABASE PROD_MORNING
   CLONE PROD_ECOMMERCE
   AT(TIMESTAMP => '2026-03-09 08:00:00'::TIMESTAMP);
   ```

3. **Clone Before Specific Statement**:
   ```sql
   -- Find problematic query ID
   SELECT query_id, query_text, start_time
   FROM snowflake.account_usage.query_history
   WHERE query_text LIKE '%DELETE FROM customers%'
   ORDER BY start_time DESC
   LIMIT 1;

   -- Clone before that statement executed
   CREATE TABLE sales.customers_before_delete
   CLONE sales.customers
   BEFORE(STATEMENT => '<query_id>');
   ```

**Comparison Analysis**:
```sql
-- Compare data between timestamps
WITH current_data AS (
    SELECT customer_id, lifetime_value
    FROM sales.customers
),
historical_data AS (
    SELECT customer_id, lifetime_value
    FROM sales.customers_3h_ago
)
SELECT
    c.customer_id,
    h.lifetime_value as value_3h_ago,
    c.lifetime_value as value_current,
    c.lifetime_value - h.lifetime_value as change
FROM current_data c
JOIN historical_data h ON c.customer_id = h.customer_id
WHERE c.lifetime_value != h.lifetime_value
ORDER BY ABS(change) DESC
LIMIT 100;
```

**Success Criteria**:
- ✅ Created clones from 1 hour ago, 3 hours ago, specific timestamp
- ✅ Used BEFORE(STATEMENT) to clone before specific query
- ✅ Compared differences between current and historical data
- ✅ Documented retention period limits (1 day for Time Travel by default)

---

### Task 5: Track Storage Costs (25 min)
Monitor storage divergence as clones are modified.

**Storage Tracking Queries**:

1. **Table Storage Metrics**:
   ```sql
   SELECT
       table_catalog,
       table_schema,
       table_name,
       active_bytes / (1024*1024*1024) as active_gb,
       time_travel_bytes / (1024*1024*1024) as time_travel_gb,
       failsafe_bytes / (1024*1024*1024) as failsafe_gb,
       (active_bytes + time_travel_bytes + failsafe_bytes) / (1024*1024*1024) as total_gb
   FROM snowflake.account_usage.table_storage_metrics
   WHERE table_catalog IN ('PROD_ECOMMERCE', 'DEV_ECOMMERCE')
       AND table_schema = 'SALES'
   ORDER BY total_gb DESC;
   ```

2. **Clone-Specific Storage**:
   ```sql
   -- After modifying clones, track divergence
   SELECT
       table_name,
       clone_group_id,
       active_bytes / (1024*1024*1024) as unique_storage_gb,
       -- Bytes not shared with parent
       is_clone,
       deleted,
       created
   FROM snowflake.account_usage.table_storage_metrics
   WHERE table_catalog = 'DEV_ECOMMERCE'
   ORDER BY active_bytes DESC;
   ```

3. **Calculate Divergence Percentage**:
   ```sql
   -- Compare original vs clone storage
   WITH storage_summary AS (
       SELECT
           CASE
               WHEN table_catalog = 'PROD_ECOMMERCE' THEN 'PROD'
               ELSE 'DEV'
           END as environment,
           SUM(active_bytes) as total_bytes
       FROM snowflake.account_usage.table_storage_metrics
       WHERE table_catalog IN ('PROD_ECOMMERCE', 'DEV_ECOMMERCE')
       GROUP BY environment
   )
   SELECT
       p.total_bytes / (1024*1024*1024) as prod_gb,
       d.total_bytes / (1024*1024*1024) as dev_gb,
       (d.total_bytes::FLOAT / p.total_bytes * 100) as divergence_pct
   FROM storage_summary p
   CROSS JOIN storage_summary d
   WHERE p.environment = 'PROD' AND d.environment = 'DEV';
   ```

4. **Monthly Cost Estimate**:
   ```sql
   -- Calculate monthly storage cost
   -- Snowflake on-demand: $40 per TB per month
   SELECT
       table_catalog,
       SUM(active_bytes + time_travel_bytes + failsafe_bytes) / (1024*1024*1024*1024) as total_tb,
       (SUM(active_bytes + time_travel_bytes + failsafe_bytes) / (1024*1024*1024*1024)) * 40 as monthly_cost_usd
   FROM snowflake.account_usage.table_storage_metrics
   WHERE table_catalog LIKE '%ECOMMERCE'
   GROUP BY table_catalog
   ORDER BY monthly_cost_usd DESC;
   ```

**Success Criteria**:
- ✅ Queried TABLE_STORAGE_METRICS successfully
- ✅ Calculated storage divergence percentage (< 10% expected for fresh clones)
- ✅ Estimated monthly storage cost for prod + clones
- ✅ Documented storage growth over 24-hour period

---

### Task 6: Dev/Test Strategy (20 min)
Implement 3 clone-based scenarios for different use cases.

**Scenario 1: Feature Testing**:
```sql
-- Developer needs to test risky schema change
CREATE DATABASE FEATURE_BRANCH_123 CLONE PROD_ECOMMERCE;

-- Test schema migration
ALTER TABLE feature_branch_123.sales.customers
ADD COLUMN loyalty_points INT DEFAULT 0;

-- Run tests, verify feature works
-- If successful: Apply to prod
-- If failed: DROP DATABASE, no cleanup needed
```

**Scenario 2: Data Migration Testing**:
```sql
-- QA needs to test ETL pipeline changes
CREATE DATABASE QA_MIGRATION_TEST CLONE PROD_ECOMMERCE;

-- Run migration script on clone
-- Verify data quality
-- Compare row counts, checksums
-- If valid: Proceed with production migration

-- Refresh clone daily for continuous testing
DROP DATABASE QA_MIGRATION_TEST;
CREATE DATABASE QA_MIGRATION_TEST CLONE PROD_ECOMMERCE;
```

**Scenario 3: Training Environment**:
```sql
-- Create training environment for new hires
CREATE DATABASE TRAINING_ENV CLONE PROD_ECOMMERCE;

-- Anonymize sensitive data
UPDATE training_env.sales.customers
SET email = concat('user', customer_id, '@training.local'),
    name = concat('Training User ', customer_id);

-- Trainees can experiment freely
-- Refresh weekly or as needed
```

**Automation Script**:
```sql
-- Create procedure to refresh dev environments nightly
CREATE OR REPLACE PROCEDURE refresh_dev_environments()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Drop old dev database
    DROP DATABASE IF EXISTS DEV_ECOMMERCE;

    -- Create fresh clone from prod
    CREATE DATABASE DEV_ECOMMERCE CLONE PROD_ECOMMERCE;

    -- Apply dev-specific configurations
    -- (e.g., smaller warehouses, cost limits)

    RETURN 'Dev environment refreshed successfully';
END;
$$;

-- Schedule with task (requires ACCOUNTADMIN)
CREATE OR REPLACE TASK refresh_dev_daily
    WAREHOUSE = WH_XSMALL_DEV
    SCHEDULE = 'USING CRON 0 2 * * * America/Los_Angeles'  -- 2 AM daily
AS
    CALL refresh_dev_environments();
```

**Cost-Benefit Analysis**:
```
Traditional Approach:
- 10TB prod + 10TB dev + 10TB QA + 10TB training = 40TB
- Cost: 40TB × $40 = $1,600/month

Zero-Copy Approach:
- 10TB prod + divergence only (estimated 5% = 1.5TB)
- Cost: 11.5TB × $40 = $460/month
- Savings: $1,140/month (71% reduction)
```

**Success Criteria**:
- ✅ Implemented 3 clone-based scenarios with working SQL
- ✅ Created automated refresh procedure
- ✅ Documented cost-benefit analysis (70%+ savings)
- ✅ Designed strategy for when to drop/refresh clones

---

## Hints

<details>
<summary>Hint 1: Clone Syntax Options</summary>

```sql
-- Clone entire database
CREATE DATABASE dev_db CLONE prod_db;

-- Clone schema
CREATE SCHEMA dev_schema CLONE prod_schema;

-- Clone table
CREATE TABLE dev_table CLONE prod_table;

-- Clone from specific time
CREATE DATABASE dev_db CLONE prod_db
AT(TIMESTAMP => '2026-03-09 10:00:00'::TIMESTAMP);

-- Clone from time offset (seconds ago)
CREATE DATABASE dev_db CLONE prod_db
AT(OFFSET => -3600);  -- 1 hour ago

-- Clone before specific statement
CREATE TABLE backup_table CLONE original_table
BEFORE(STATEMENT => 'query_id_here');
```
</details>

<details>
<summary>Hint 2: Checking Clone Relationships</summary>

```sql
-- View clone lineage
SHOW CLONES;

-- Check if table is a clone
SELECT
    table_catalog,
    table_schema,
    table_name,
    is_clone,
    clone_group_id
FROM snowflake.account_usage.tables
WHERE table_name = 'CUSTOMERS'
ORDER BY created DESC;
```
</details>

<details>
<summary>Hint 3: Storage Monitoring</summary>

```sql
-- Current storage usage
SELECT
    table_catalog,
    SUM(active_bytes) / (1024*1024*1024) as active_gb,
    SUM(time_travel_bytes) / (1024*1024*1024) as time_travel_gb,
    SUM(failsafe_bytes) / (1024*1024*1024) as failsafe_gb
FROM snowflake.account_usage.table_storage_metrics
WHERE table_catalog IN ('PROD_ECOMMERCE', 'DEV_ECOMMERCE')
GROUP BY table_catalog;

-- Track storage growth over time
SELECT
    usage_date,
    database_name,
    average_database_bytes / (1024*1024*1024) as avg_gb
FROM snowflake.account_usage.database_storage_usage_history
WHERE database_name LIKE '%ECOMMERCE'
    AND usage_date >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY usage_date DESC, database_name;
```
</details>

<details>
<summary>Hint 4: Cleanup and Management</summary>

```sql
-- Drop clone (doesn't affect original)
DROP DATABASE DEV_ECOMMERCE;

-- Drop multiple clones
DROP DATABASE IF EXISTS DEV_ECOMMERCE;
DROP DATABASE IF EXISTS QA_ECOMMERCE;
DROP DATABASE IF EXISTS TRAINING_ENV;

-- Check database sizes before dropping
SELECT
    database_name,
    SUM(active_bytes) / (1024*1024*1024) as storage_gb,
    COUNT(DISTINCT table_name) as table_count
FROM snowflake.account_usage.table_storage_metrics
WHERE database_name LIKE '%ECOMMERCE'
GROUP BY database_name
ORDER BY storage_gb DESC;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-02-zero-copy-dev
bash validate.sh
```

**Expected Output**:
```
✅ Task 1: Production database created (10K + 50K + 5K rows)
✅ Task 2: Database cloned in < 5 seconds (zero initial storage)
✅ Task 3: Table and schema clones working (isolation verified)
✅ Task 4: Historical clones created (1h, 3h, specific timestamp)
✅ Task 5: Storage tracking queries working (divergence: 8%)
✅ Task 6: 3 dev/test scenarios implemented (71% cost savings)

🎉 Exercise 02 Complete! Estimated Storage Savings: $1,140/month
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All clone creation and verification commands
2. `storage-analysis.md` - Storage tracking results and cost calculations
3. `dev-test-strategy.md` - Document with 3 scenarios and automation plan
4. Screenshot of TABLE_STORAGE_METRICS showing clone divergence

---

## Resources
- Snowflake Documentation: [Cloning Objects](https://docs.snowflake.com/en/user-guide/object-clone)
- Snowflake Documentation: [Understanding Storage Costs](https://docs.snowflake.com/en/user-guide/tables-storage)
- Notebook: `notebooks/02-zero-copy-cloning.sql`
- Diagram: `assets/diagrams/zero-copy-cloning.mmd`
- Theory: `theory/concepts.md#zero-copy-cloning`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 03: Time Travel Recovery (disaster recovery patterns)
- ✅ Exercise 04: Data Sharing (share data without copying)
- Review Module 17: Cost Optimization for storage best practices
