-- ============================================================================
-- Module Bonus 02: Snowflake Data Cloud
-- Notebook 03: Time Travel and Fail-safe
-- ============================================================================
-- Description: Master Snowflake's Time Travel feature to query historical data,
--              recover from accidental changes, and implement audit trails.
--              Learn retention periods, UNDROP operations, and Fail-safe recovery.
--
-- Prerequisites:
--   - Snowflake account with CREATE DATABASE privilege
--   - Understanding of Snowflake architecture
--   - Completed Zero-Copy Cloning notebook
--
-- Estimated Time: 90 minutes
-- ============================================================================

-- ============================================================================
-- SETUP: Create Environment for Time Travel Experiments
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Create dedicated warehouse
CREATE OR REPLACE WAREHOUSE timetravel_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE timetravel_wh;

-- Create database for time travel experiments
CREATE OR REPLACE DATABASE timetravel_lab;
USE DATABASE timetravel_lab;

CREATE SCHEMA IF NOT EXISTS sales;
USE SCHEMA sales;

-- Create orders table for time travel experiments
CREATE OR REPLACE TABLE orders (
    order_id NUMBER(12,0) PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE,
    customer_id NUMBER(10,0),
    customer_name VARCHAR(100),
    product_name VARCHAR(200),
    quantity NUMBER(5,0),
    unit_price DECIMAL(10,2),
    order_total DECIMAL(12,2),
    order_date DATE,
    order_status VARCHAR(20),
    payment_method VARCHAR(30),
    shipping_address VARCHAR(200),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) DATA_RETENTION_TIME_IN_DAYS = 1;  -- Standard Edition: 1 day default

-- Load initial dataset of 1000 orders
INSERT INTO orders
SELECT
    SEQ4() AS order_id,
    CONCAT('ORD-', LPAD(SEQ4()::VARCHAR, 10, '0')) AS order_number,
    UNIFORM(1, 500, RANDOM()) AS customer_id,
    CONCAT('Customer ', UNIFORM(1, 500, RANDOM())) AS customer_name,
    CONCAT('Product ', UNIFORM(1, 200, RANDOM())) AS product_name,
    UNIFORM(1, 10, RANDOM()) AS quantity,
    UNIFORM(10, 500, RANDOM()) AS unit_price,
    (UNIFORM(1, 10, RANDOM()) * UNIFORM(10, 500, RANDOM())) AS order_total,
    DATEADD(DAY, -UNIFORM(0, 90, RANDOM()), CURRENT_DATE()) AS order_date,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Pending'
        WHEN 2 THEN 'Processing'
        WHEN 3 THEN 'Shipped'
        WHEN 4 THEN 'Delivered'
        ELSE 'Completed'
    END AS order_status,
    ARRAY_GET(PARSE_JSON('["Credit Card","PayPal","Debit Card","Wire Transfer"]'),
              UNIFORM(0, 3, RANDOM())) AS payment_method,
    CONCAT(UNIFORM(100, 9999, RANDOM()), ' Main Street, City, State') AS shipping_address,
    DATEADD(MINUTE, -UNIFORM(0, 129600, RANDOM()), CURRENT_TIMESTAMP()) AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM TABLE(GENERATOR(ROWCOUNT => 1000));

-- Verify data loaded
SELECT COUNT(*) AS total_orders FROM orders;
-- Expected: 1000

SELECT * FROM orders LIMIT 10;

-- Create additional tables for comprehensive testing
CREATE OR REPLACE TABLE customers (
    customer_id NUMBER(10,0) PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    registration_date DATE,
    status VARCHAR(20),
    credit_limit DECIMAL(12,2),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) DATA_RETENTION_TIME_IN_DAYS = 1;

INSERT INTO customers
SELECT
    SEQ4() AS customer_id,
    CONCAT('Customer ', SEQ4()) AS customer_name,
    CONCAT('customer', SEQ4(), '@example.com') AS email,
    CONCAT('555-', LPAD(UNIFORM(100, 999, RANDOM())::VARCHAR, 3, '0'), '-',
           LPAD(UNIFORM(1000, 9999, RANDOM())::VARCHAR, 4, '0')) AS phone,
    DATEADD(DAY, -UNIFORM(0, 730, RANDOM()), CURRENT_DATE()) AS registration_date,
    CASE UNIFORM(1, 3, RANDOM())
        WHEN 1 THEN 'Active'
        WHEN 2 THEN 'Inactive'
        ELSE 'Pending'
    END AS status,
    UNIFORM(1000, 50000, RANDOM()) AS credit_limit,
    CURRENT_TIMESTAMP() AS created_at
FROM TABLE(GENERATOR(ROWCOUNT => 500));

SELECT COUNT(*) FROM customers;
-- Expected: 500


-- ============================================================================
-- SECTION 1: Query Historical Data
-- ============================================================================
-- Time Travel allows querying data as it existed at a specific point in time.
-- Use AT or BEFORE clauses with TIMESTAMP, OFFSET, or STATEMENT parameters.
-- ============================================================================

-- Capture current state as baseline
SELECT
    order_status,
    COUNT(*) AS order_count,
    SUM(order_total) AS total_revenue
FROM orders
GROUP BY order_status
ORDER BY order_status;

-- Store current timestamp for future reference
SET current_time = CURRENT_TIMESTAMP();
SELECT $current_time AS reference_timestamp;

-- Wait a few seconds to create time separation
CALL SYSTEM$WAIT(3);

-- Make changes to the data
UPDATE orders
SET order_status = 'Cancelled'
WHERE order_id < 50;

-- Verify changes applied
SELECT COUNT(*) FROM orders WHERE order_status = 'Cancelled';
-- Expected: 50


-- TECHNIQUE 1: Query using AT(TIMESTAMP => ...)
-- Query data as it existed at the stored timestamp (before UPDATE)
SELECT
    order_status,
    COUNT(*) AS order_count,
    SUM(order_total) AS total_revenue
FROM orders AT(TIMESTAMP => $current_time)
GROUP BY order_status
ORDER BY order_status;
-- No 'Cancelled' orders visible at this timestamp


-- Compare current vs historical state
SELECT
    'CURRENT' AS state,
    order_status,
    COUNT(*) AS order_count
FROM orders
GROUP BY order_status
UNION ALL
SELECT
    'HISTORICAL (5 sec ago)' AS state,
    order_status,
    COUNT(*) AS order_count
FROM orders AT(TIMESTAMP => $current_time)
GROUP BY order_status
ORDER BY state, order_status;


-- TECHNIQUE 2: Query using AT(OFFSET => ...)
-- Query data from X seconds ago
SELECT COUNT(*) AS current_cancelled
FROM orders
WHERE order_status = 'Cancelled';
-- Returns 50

SELECT COUNT(*) AS past_cancelled
FROM orders AT(OFFSET => -10)  -- 10 seconds ago
WHERE order_status = 'Cancelled';
-- Returns 0 (before cancellations)


-- Make more changes with timestamps
SET timestamp_before_bulk_update = CURRENT_TIMESTAMP();
CALL SYSTEM$WAIT(2);

UPDATE orders
SET order_total = order_total * 1.10
WHERE order_status = 'Processing';

-- Query before the price increase
SELECT
    AVG(order_total) AS avg_order_total
FROM orders AT(TIMESTAMP => $timestamp_before_bulk_update)
WHERE order_status = 'Processing';
-- Original prices

SELECT
    AVG(order_total) AS avg_order_total
FROM orders
WHERE order_status = 'Processing';
-- 10% higher prices


-- TECHNIQUE 3: Track changes over time
-- Create timeline of order status changes
WITH time_points AS (
    SELECT DATEADD(MINUTE, -5, CURRENT_TIMESTAMP()) AS time_5min_ago
    UNION ALL
    SELECT DATEADD(MINUTE, -3, CURRENT_TIMESTAMP())
    UNION ALL
    SELECT DATEADD(MINUTE, -1, CURRENT_TIMESTAMP())
    UNION ALL
    SELECT CURRENT_TIMESTAMP()
)
SELECT
    time_5min_ago AS query_time,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => t.time_5min_ago) WHERE order_status = 'Cancelled') AS cancelled_count,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => t.time_5min_ago) WHERE order_status = 'Processing') AS processing_count,
    (SELECT SUM(order_total) FROM orders AT(TIMESTAMP => t.time_5min_ago)) AS total_revenue
FROM time_points t
ORDER BY query_time;
-- Shows data evolution over time


-- Query specific orders to see exact changes
SELECT
    order_id,
    order_number,
    order_status AS current_status,
    order_total AS current_total
FROM orders
WHERE order_id < 10
ORDER BY order_id;

-- Compare with historical values
SELECT
    order_id,
    order_number,
    order_status AS historical_status,
    order_total AS historical_total
FROM orders AT(TIMESTAMP => $timestamp_before_bulk_update)
WHERE order_id < 10
ORDER BY order_id;


-- Identify which records changed
SELECT
    c.order_id,
    c.order_number,
    h.order_status AS old_status,
    c.order_status AS new_status,
    h.order_total AS old_total,
    c.order_total AS new_total,
    c.order_total - h.order_total AS price_change
FROM orders c
JOIN orders AT(TIMESTAMP => $timestamp_before_bulk_update) h
    ON c.order_id = h.order_id
WHERE c.order_status != h.order_status
   OR c.order_total != h.order_total
ORDER BY c.order_id
LIMIT 20;


-- ============================================================================
-- SECTION 2: UNDROP Objects
-- ============================================================================
-- Snowflake keeps dropped objects available for restoration during the
-- Time Travel retention period. Use UNDROP to restore tables, schemas, or databases.
-- ============================================================================

-- Create a test table
CREATE OR REPLACE TABLE test_deletions (
    id NUMBER,
    description VARCHAR(100),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO test_deletions VALUES
    (1, 'Important record 1', CURRENT_TIMESTAMP()),
    (2, 'Important record 2', CURRENT_TIMESTAMP()),
    (3, 'Important record 3', CURRENT_TIMESTAMP());

SELECT * FROM test_deletions;
-- Shows 3 records


-- Simulate accidental table drop
SET drop_timestamp = CURRENT_TIMESTAMP();
DROP TABLE test_deletions;

-- Verify table is gone
SHOW TABLES LIKE 'test_deletions';
-- Returns empty (or shows dropped table with dropped_on timestamp)

-- Try to query dropped table (will fail)
-- SELECT * FROM test_deletions;
-- Error: Object does not exist


-- RESTORE using UNDROP
UNDROP TABLE test_deletions;

-- Verify restoration
SELECT * FROM test_deletions;
-- All 3 records restored!

SHOW TABLES LIKE 'test_deletions';
-- Table is active again


-- Test UNDROP with multiple drops
CREATE OR REPLACE TABLE multi_drop_test (data VARCHAR(50));
INSERT INTO multi_drop_test VALUES ('Version 1');

DROP TABLE multi_drop_test;

-- Create new table with same name
CREATE TABLE multi_drop_test (data VARCHAR(50));
INSERT INTO multi_drop_test VALUES ('Version 2');

DROP TABLE multi_drop_test;

-- UNDROP restores most recently dropped version
UNDROP TABLE multi_drop_test;

SELECT * FROM multi_drop_test;
-- Shows 'Version 2'


-- UNDROP schema
CREATE SCHEMA test_schema;
CREATE TABLE test_schema.important_data (id NUMBER, value VARCHAR(100));
INSERT INTO test_schema.important_data VALUES (1, 'Critical data');

-- Drop entire schema
DROP SCHEMA test_schema;

-- Restore schema and all contained objects
UNDROP SCHEMA test_schema;

-- Verify restoration
SELECT * FROM test_schema.important_data;
-- Data restored


-- UNDROP database
CREATE DATABASE test_database;
USE DATABASE test_database;
CREATE SCHEMA data_schema;
CREATE TABLE data_schema.records (id NUMBER, info VARCHAR(100));
INSERT INTO data_schema.records VALUES (1, 'Important info');

USE DATABASE timetravel_lab;  -- Switch away before dropping

-- Drop entire database
DROP DATABASE test_database;

-- Restore database with all schemas and tables
UNDROP DATABASE test_database;

-- Verify restoration
SELECT * FROM test_database.data_schema.records;
-- All data restored


-- View dropped objects history
SHOW TABLES HISTORY LIKE '%test%';
-- Shows all versions including dropped ones

SHOW SCHEMAS HISTORY;
-- Shows dropped schemas

SHOW DATABASES HISTORY;
-- Shows dropped databases


-- ============================================================================
-- SECTION 3: Clone from Historical Point
-- ============================================================================
-- Combine Time Travel with zero-copy cloning to create snapshots from
-- specific points in time. Perfect for recovery and analysis scenarios.
-- ============================================================================

USE DATABASE timetravel_lab;
USE SCHEMA sales;

-- Capture timestamp before making destructive changes
SET before_disaster_timestamp = CURRENT_TIMESTAMP();

SELECT $before_disaster_timestamp;

-- Wait to ensure timestamp separation
CALL SYSTEM$WAIT(3);

-- Simulate data disaster
DELETE FROM orders WHERE order_date < DATEADD(DAY, -30, CURRENT_DATE());

UPDATE orders
SET order_status = 'ERROR',
    order_total = 0
WHERE order_id BETWEEN 100 AND 200;

-- Check damage
SELECT COUNT(*) AS remaining_orders FROM orders;
-- Reduced count

SELECT COUNT(*) FROM orders WHERE order_status = 'ERROR';
-- Shows 100+ affected records


-- RECOVERY OPTION 1: Clone entire table from before disaster
CREATE OR REPLACE TABLE orders_backup
    CLONE orders AT(TIMESTAMP => $before_disaster_timestamp);

-- Verify backup has original data
SELECT COUNT(*) FROM orders_backup;
-- Original count (1000)

SELECT COUNT(*) FROM orders_backup WHERE order_status = 'ERROR';
-- Returns 0 (no errors in historical data)


-- RECOVERY OPTION 2: Clone using offset
CREATE OR REPLACE TABLE orders_2_hours_ago
    CLONE orders AT(OFFSET => -7200);  -- 2 hours = 7200 seconds

-- Verify recovery
SELECT
    'Current (Damaged)' AS state,
    COUNT(*) AS record_count,
    SUM(order_total) AS total_revenue
FROM orders
UNION ALL
SELECT
    'Backup (Restored)' AS state,
    COUNT(*) AS record_count,
    SUM(order_total) AS total_revenue
FROM orders_backup;


-- RECOVERY OPTION 3: Replace damaged table with historical clone
-- Drop damaged table
DROP TABLE orders;

-- Recreate from backup
CREATE TABLE orders CLONE orders_backup;

-- Verify full recovery
SELECT COUNT(*) FROM orders;
-- Original count restored

SELECT COUNT(*) FROM orders WHERE order_status = 'ERROR';
-- Returns 0


-- Clone database from specific time
CREATE OR REPLACE DATABASE timetravel_lab_yesterday
    CLONE timetravel_lab AT(OFFSET => -86400)  -- 24 hours ago
    COMMENT = 'Database snapshot from 24 hours ago';

-- Verify historical database structure
USE DATABASE timetravel_lab_yesterday;
SHOW TABLES;


-- Clone with partial data recovery
-- Create historical clone with filter applied
CREATE OR REPLACE TABLE orders_high_value_historical AS
SELECT *
FROM timetravel_lab.sales.orders AT(TIMESTAMP => $before_disaster_timestamp)
WHERE order_total > 1000;

SELECT COUNT(*) FROM orders_high_value_historical;
-- Subset of historical high-value orders


-- ============================================================================
-- SECTION 4: Compare Current vs Historical Versions
-- ============================================================================
-- Identify exactly what changed between two points in time for audit trails
-- and data quality monitoring.
-- ============================================================================

USE DATABASE timetravel_lab;
USE SCHEMA sales;

-- Create current snapshot for comparison
SET comparison_timestamp = CURRENT_TIMESTAMP();

-- Make changes
UPDATE orders
SET order_status = 'Shipped'
WHERE order_status = 'Processing'
  AND order_id < 150;

UPDATE customers
SET status = 'Active'
WHERE status = 'Pending';

CALL SYSTEM$WAIT(2);


-- COMPARISON 1: Identify all changed orders
WITH current_state AS (
    SELECT * FROM orders
),
historical_state AS (
    SELECT * FROM orders AT(TIMESTAMP => $comparison_timestamp)
)
SELECT
    c.order_id,
    c.order_number,
    h.order_status AS old_status,
    c.order_status AS new_status,
    h.order_total AS old_total,
    c.order_total AS new_total,
    c.updated_at AS change_time
FROM current_state c
JOIN historical_state h ON c.order_id = h.order_id
WHERE c.order_status != h.order_status
   OR c.order_total != h.order_total
ORDER BY c.order_id;


-- COMPARISON 2: Detect deleted records
WITH current_state AS (
    SELECT order_id FROM orders
),
historical_state AS (
    SELECT order_id FROM orders AT(TIMESTAMP => $comparison_timestamp)
)
SELECT
    h.order_id AS deleted_order_id,
    'Deleted since ' || $comparison_timestamp AS status
FROM historical_state h
LEFT JOIN current_state c ON h.order_id = c.order_id
WHERE c.order_id IS NULL;


-- COMPARISON 3: Detect newly inserted records
WITH current_state AS (
    SELECT order_id, order_number, order_status FROM orders
),
historical_state AS (
    SELECT order_id FROM orders AT(TIMESTAMP => $comparison_timestamp)
)
SELECT
    c.order_id AS new_order_id,
    c.order_number,
    c.order_status,
    'Inserted after ' || $comparison_timestamp AS status
FROM current_state c
LEFT JOIN historical_state h ON c.order_id = h.order_id
WHERE h.order_id IS NULL;


-- COMPARISON 4: Aggregate-level comparison
SELECT
    'CURRENT' AS state,
    order_status,
    COUNT(*) AS order_count,
    SUM(order_total) AS total_revenue,
    AVG(order_total) AS avg_order_value
FROM orders
GROUP BY order_status
UNION ALL
SELECT
    'HISTORICAL (5 min ago)' AS state,
    order_status,
    COUNT(*) AS order_count,
    SUM(order_total) AS total_revenue,
    AVG(order_total) AS avg_order_value
FROM orders AT(OFFSET => -300)
GROUP BY order_status
ORDER BY state, order_status;


-- COMPARISON 5: Revenue drift analysis
WITH hourly_snapshots AS (
    SELECT 0 AS hours_ago, CURRENT_TIMESTAMP() AS snapshot_time
    UNION ALL SELECT 1, DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
    UNION ALL SELECT 2, DATEADD(HOUR, -2, CURRENT_TIMESTAMP())
    UNION ALL SELECT 3, DATEADD(HOUR, -3, CURRENT_TIMESTAMP())
    UNION ALL SELECT 4, DATEADD(HOUR, -4, CURRENT_TIMESTAMP())
)
SELECT
    s.hours_ago,
    s.snapshot_time,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => s.snapshot_time)) AS order_count,
    (SELECT SUM(order_total) FROM orders AT(TIMESTAMP => s.snapshot_time)) AS total_revenue,
    (SELECT AVG(order_total) FROM orders AT(TIMESTAMP => s.snapshot_time)) AS avg_order_value
FROM hourly_snapshots s
ORDER BY s.hours_ago;


-- COMPARISON 6: Customer status changes
SELECT
    c.customer_id,
    c.customer_name,
    h.status AS old_status,
    c.status AS new_status,
    h.credit_limit AS old_credit_limit,
    c.credit_limit AS new_credit_limit
FROM customers c
JOIN customers AT(TIMESTAMP => $comparison_timestamp) h
    ON c.customer_id = h.customer_id
WHERE c.status != h.status
   OR c.credit_limit != h.credit_limit
LIMIT 20;


-- ============================================================================
-- SECTION 5: Query DESCRIBE HISTORY
-- ============================================================================
-- View DDL changes and retention information for tables.
-- ============================================================================

-- Show complete history of orders table
SELECT * FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
    TABLE_NAME => 'TIMETRAVEL_LAB.SALES.ORDERS'
));


-- Get retention and Time Travel information
SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' FOR TABLE orders;
-- Shows current retention setting


-- View table DDL history (requires query history)
SELECT
    query_id,
    query_text,
    user_name,
    role_name,
    start_time,
    execution_status
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE query_text LIKE '%orders%'
  AND (query_text LIKE '%CREATE%'
       OR query_text LIKE '%ALTER%'
       OR query_text LIKE '%DROP%')
  AND database_name = 'TIMETRAVEL_LAB'
ORDER BY start_time DESC
LIMIT 20;


-- Track table modifications
SELECT
    query_id,
    query_text,
    start_time,
    end_time,
    rows_inserted,
    rows_updated,
    rows_deleted
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE query_text LIKE '%orders%'
  AND (query_text LIKE '%INSERT%'
       OR query_text LIKE '%UPDATE%'
       OR query_text LIKE '%DELETE%')
  AND database_name = 'TIMETRAVEL_LAB'
  AND execution_status = 'SUCCESS'
ORDER BY start_time DESC
LIMIT 20;


-- Create audit log from query history
CREATE OR REPLACE VIEW data_modification_audit AS
SELECT
    query_id,
    SUBSTRING(query_text, 1, 100) AS query_preview,
    user_name,
    role_name,
    database_name,
    schema_name,
    start_time,
    execution_status,
    rows_inserted,
    rows_updated,
    rows_deleted,
    (COALESCE(rows_inserted, 0) + COALESCE(rows_updated, 0) + COALESCE(rows_deleted, 0)) AS total_rows_affected
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE (rows_inserted > 0 OR rows_updated > 0 OR rows_deleted > 0)
  AND database_name = 'TIMETRAVEL_LAB'
ORDER BY start_time DESC;

SELECT * FROM data_modification_audit LIMIT 10;


-- ============================================================================
-- SECTION 6: Fail-safe Explanation and Recovery
-- ============================================================================
-- Fail-safe provides an additional 7 days of data recovery after Time Travel
-- retention expires. It's a disaster recovery feature, not self-service.
-- ============================================================================

-- Understanding the data protection timeline:
--
-- |<-------- Time Travel -------->|<------ Fail-safe ------>|
-- |  (1-90 days user-queryable)   |   (7 days Snowflake)   |
-- |                               |                         |
-- [Data Modified] -----> [Retention Period] -----> [Fail-safe] -----> [Permanently Deleted]
--
-- Time Travel: Self-service recovery via AT/BEFORE clauses or UNDROP
-- Fail-safe: Contact Snowflake Support for disaster recovery


-- Check current retention settings
SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' IN ACCOUNT;
-- Shows account-level default

SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' FOR DATABASE timetravel_lab;
-- Shows database-level setting

SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' FOR TABLE orders;
-- Shows table-level setting


-- Example Fail-safe scenario:
--
-- Day 0: Table accidentally dropped
-- Day 0-1: Can UNDROP table or query AT(TIMESTAMP)  [Time Travel]
-- Day 1: Time Travel retention expires (Standard Edition)
-- Day 1-8: Fail-safe period - contact Snowflake Support  [Fail-safe]
-- Day 8+: Data permanently deleted, cannot recover
--
-- Enterprise Edition: 90-day Time Travel possible
-- Day 0-90: Time Travel available
-- Day 90-97: Fail-safe period
-- Day 97+: Permanently deleted


-- Fail-safe is NOT queryable by users
-- This will work during Time Travel:
SELECT * FROM orders AT(OFFSET => -3600);

-- This will NOT work during Fail-safe (will error):
-- SELECT * FROM orders AT(OFFSET => -200000);  -- Beyond retention
-- Error: Historical data access outside retention period


-- Storage costs for Fail-safe
-- Both Time Travel and Fail-safe data consume storage and incur costs
SELECT
    table_name,
    active_bytes / (1024*1024*1024) AS active_gb,
    time_travel_bytes / (1024*1024*1024) AS time_travel_gb,
    failsafe_bytes / (1024*1024*1024) AS failsafe_gb,
    (active_bytes + time_travel_bytes + failsafe_bytes) / (1024*1024*1024) AS total_gb
FROM INFORMATION_SCHEMA.TABLE_STORAGE_METRICS
WHERE table_schema = 'SALES'
ORDER BY total_gb DESC;


-- Best Practices for Fail-safe:
CREATE OR REPLACE VIEW failsafe_best_practices AS
SELECT
    'Understand it''s NOT self-service' AS practice,
    'Must contact Snowflake Support for recovery' AS implementation,
    'Plan accordingly' AS benefit
UNION ALL
SELECT
    'Rely on Time Travel for regular recovery',
    'Use UNDROP and AT clauses for self-service',
    'Faster recovery without support tickets'
UNION ALL
SELECT
    'Treat Fail-safe as last resort',
    'Implement backup strategies within Time Travel window',
    'Better recovery time objectives'
UNION ALL
SELECT
    'Monitor storage costs',
    'Time Travel + Fail-safe both consume storage',
    'Control costs with appropriate retention'
UNION ALL
SELECT
    'Set appropriate retention periods',
    'Balance recovery needs vs storage costs',
    'Optimize cost-to-protection ratio';

SELECT * FROM failsafe_best_practices;


-- ============================================================================
-- SECTION 7: Configure Retention Periods
-- ============================================================================
-- Set data retention at account, database, schema, or table level.
-- Enterprise Edition supports up to 90 days; Standard supports 0-1 day.
-- ============================================================================

-- Check current edition and features
SELECT SYSTEM$GET_SNOWFLAKE_PLATFORM_INFO();


-- Account-level retention (requires ACCOUNTADMIN)
-- ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 1;  -- Standard Edition
-- ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 90; -- Enterprise Edition


-- Database-level retention
ALTER DATABASE timetravel_lab SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- Verify setting
SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' FOR DATABASE timetravel_lab;


-- Schema-level retention
ALTER SCHEMA sales SET DATA_RETENTION_TIME_IN_DAYS = 1;


-- Table-level retention (overrides database/schema settings)
-- Example: Critical financial data with extended retention
CREATE OR REPLACE TABLE financial_transactions (
    transaction_id NUMBER,
    account_id NUMBER,
    amount DECIMAL(15,2),
    transaction_date DATE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) DATA_RETENTION_TIME_IN_DAYS = 1;  -- Set at creation

-- Or modify existing table
ALTER TABLE orders SET DATA_RETENTION_TIME_IN_DAYS = 1;


-- For Enterprise Edition users (90-day retention):
-- ALTER TABLE critical_data SET DATA_RETENTION_TIME_IN_DAYS = 90;


-- View all tables with custom retention
SELECT
    table_catalog AS database_name,
    table_schema AS schema_name,
    table_name,
    retention_time
FROM INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'SALES'
  AND table_type = 'BASE TABLE'
ORDER BY retention_time DESC, table_name;


-- Retention considerations by data type:
CREATE OR REPLACE VIEW retention_guidelines AS
SELECT
    'Transient/Temporary Data' AS data_type,
    '0 days' AS recommended_retention,
    'Staging tables, ETL intermediates' AS use_case,
    'Minimize storage costs' AS rationale
UNION ALL
SELECT
    'Development/Test Data',
    '1 day',
    'Dev environments, experiments',
    'Balance recovery with cost'
UNION ALL
SELECT
    'Production Operational',
    '7 days',
    'Sales, orders, inventory',
    'Cover weekly operations'
UNION ALL
SELECT
    'Financial/Audit Data',
    '30-90 days',
    'Financial transactions, audit logs',
    'Regulatory compliance'
UNION ALL
SELECT
    'Critical Reference Data',
    '90 days',
    'Master data, pricing history',
    'Extended recovery window';

SELECT * FROM retention_guidelines ORDER BY CAST(SPLIT_PART(recommended_retention, ' ', 1) AS NUMBER);


-- Calculate storage cost impact of retention settings
WITH retention_cost_estimate AS (
    SELECT
        table_name,
        retention_time AS retention_days,
        active_bytes / (1024*1024*1024) AS active_gb,
        time_travel_bytes / (1024*1024*1024) AS time_travel_gb,
        -- Estimate: Time Travel storage ~= active_gb * (retention_days / 7) * churn_rate
        -- Assuming 20% weekly churn rate
        (active_bytes / (1024*1024*1024)) * (retention_time / 7.0) * 0.20 AS estimated_time_travel_gb
    FROM INFORMATION_SCHEMA.TABLES t
    JOIN INFORMATION_SCHEMA.TABLE_STORAGE_METRICS m
        ON t.table_name = m.table_name
        AND t.table_schema = m.table_schema
    WHERE t.table_schema = 'SALES'
      AND t.table_type = 'BASE TABLE'
)
SELECT
    table_name,
    retention_days,
    active_gb,
    estimated_time_travel_gb,
    (active_gb + estimated_time_travel_gb) AS total_estimated_gb,
    ROUND((active_gb + estimated_time_travel_gb) * 40, 2) AS estimated_monthly_cost_usd
FROM retention_cost_estimate
ORDER BY estimated_monthly_cost_usd DESC;


-- ============================================================================
-- SECTION 8: Time Travel Use Cases
-- ============================================================================
-- Real-world applications of Time Travel for various business scenarios.
-- ============================================================================

-- USE CASE 1: Accidental Delete Recovery
-- Simulate accidental deletion
CREATE OR REPLACE TABLE important_products (
    product_id NUMBER,
    product_name VARCHAR(100),
    price DECIMAL(10,2)
);

INSERT INTO important_products VALUES
    (1, 'Premium Widget', 99.99),
    (2, 'Deluxe Gadget', 149.99),
    (3, 'Ultimate Tool', 199.99);

SET before_delete = CURRENT_TIMESTAMP();
CALL SYSTEM$WAIT(2);

-- Accidental delete
DELETE FROM important_products WHERE product_id = 2;

-- Realize mistake, recover
INSERT INTO important_products
SELECT * FROM important_products AT(TIMESTAMP => $before_delete)
WHERE product_id = 2;

SELECT * FROM important_products ORDER BY product_id;
-- Product 2 restored


-- USE CASE 2: Regulatory Compliance and Audit
-- Create audit trail for compliance reporting
CREATE OR REPLACE TABLE account_balances (
    account_id NUMBER,
    balance DECIMAL(15,2),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) DATA_RETENTION_TIME_IN_DAYS = 1;  -- Enterprise: 90 for compliance

INSERT INTO account_balances VALUES
    (101, 10000.00, CURRENT_TIMESTAMP()),
    (102, 25000.00, CURRENT_TIMESTAMP()),
    (103, 5000.00, CURRENT_TIMESTAMP());

-- Generate month-end snapshot for auditing
CREATE OR REPLACE TABLE account_balances_month_end
    CLONE account_balances;

-- Auditors can query historical balance at any point
-- SELECT * FROM account_balances AT(TIMESTAMP => '2026-02-28 23:59:59');


-- USE CASE 3: Debugging Data Pipeline Issues
-- Track data through pipeline stages
SET pipeline_start = CURRENT_TIMESTAMP();

-- Stage 1: Raw data load
CREATE OR REPLACE TABLE pipeline_raw (data VARCHAR(100));
INSERT INTO pipeline_raw VALUES ('Raw data 1'), ('Raw data 2');

CALL SYSTEM$WAIT(1);

-- Stage 2: Transformation (bug introduced)
CREATE OR REPLACE TABLE pipeline_transformed AS
SELECT UPPER(data) || '_TRANSFORMED' AS data FROM pipeline_raw;

CALL SYSTEM$WAIT(1);

-- Stage 3: Aggregation
CREATE OR REPLACE TABLE pipeline_final AS
SELECT COUNT(*) AS record_count FROM pipeline_transformed;

-- Debugging: Compare each stage at different times
SELECT 'Raw' AS stage, * FROM pipeline_raw AT(TIMESTAMP => $pipeline_start)
UNION ALL
SELECT 'Transformed', data FROM pipeline_transformed AT(TIMESTAMP => $pipeline_start)
UNION ALL
SELECT 'Final', record_count::VARCHAR FROM pipeline_final AT(TIMESTAMP => $pipeline_start);


-- USE CASE 4: Comparison Testing
-- Test schema changes without affecting production
SET before_schema_change = CURRENT_TIMESTAMP();

-- Add new column
ALTER TABLE orders ADD COLUMN discount_percentage DECIMAL(5,2);

UPDATE orders
SET discount_percentage = UNIFORM(0, 25, RANDOM());

-- Compare revenue with/without discounts
SELECT
    'Without Discounts' AS scenario,
    SUM(order_total) AS total_revenue
FROM orders AT(TIMESTAMP => $before_schema_change)
UNION ALL
SELECT
    'With Discounts' AS scenario,
    SUM(order_total * (1 - COALESCE(discount_percentage, 0) / 100)) AS total_revenue
FROM orders;


-- USE CASE 5: Point-in-Time Reporting
-- Generate reports as of specific business dates
CREATE OR REPLACE FUNCTION get_monthly_report(report_date TIMESTAMP_NTZ)
RETURNS TABLE (
    order_status VARCHAR,
    order_count NUMBER,
    total_revenue NUMBER
)
AS
$$
    SELECT
        order_status,
        COUNT(*) AS order_count,
        SUM(order_total) AS total_revenue
    FROM orders AT(TIMESTAMP => report_date)
    GROUP BY order_status
$$;

-- Generate end-of-month report
SELECT * FROM TABLE(get_monthly_report('2026-02-28 23:59:59'::TIMESTAMP_NTZ));


-- USE CASE 6: Data Quality Monitoring
-- Detect when data quality degraded
CREATE OR REPLACE VIEW data_quality_timeline AS
WITH time_series AS (
    SELECT DATEADD(HOUR, -n, CURRENT_TIMESTAMP()) AS check_time
    FROM (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1 AS n
          FROM TABLE(GENERATOR(ROWCOUNT => 24)))
)
SELECT
    check_time,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => t.check_time)) AS total_orders,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => t.check_time) WHERE order_total <= 0) AS invalid_orders,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => t.check_time) WHERE order_status IS NULL) AS null_status_orders
FROM time_series t
ORDER BY check_time DESC;

SELECT * FROM data_quality_timeline LIMIT 24;


-- ============================================================================
-- CLEANUP: Remove Training Resources
-- ============================================================================

/*
DROP DATABASE IF EXISTS timetravel_lab;
DROP DATABASE IF EXISTS timetravel_lab_yesterday;
DROP DATABASE IF EXISTS test_database;
DROP WAREHOUSE IF EXISTS timetravel_wh;
*/


-- ============================================================================
-- KEY TAKEAWAYS
-- ============================================================================
-- 1. Time Travel allows querying historical data within retention period
--    (1 day Standard, up to 90 days Enterprise Edition).
--
-- 2. Use AT(TIMESTAMP => ...), AT(OFFSET => ...), or BEFORE(STATEMENT => ...)
--    to query historical states.
--
-- 3. UNDROP recovers dropped tables, schemas, and databases within
--    Time Travel retention period. Instant self-service recovery.
--
-- 4. Combine Time Travel with CLONE for point-in-time backups and recovery.
--    Create historical snapshots without storage duplication.
--
-- 5. Compare current vs historical data to identify changes, audit
--    modifications, and track data evolution.
--
-- 6. Fail-safe provides 7 days additional recovery after Time Travel expires.
--    Requires Snowflake Support - not self-service.
--
-- 7. Set retention periods based on data sensitivity and compliance needs:
--    - Transient: 0 days (minimize cost)
--    - Development: 1 day (quick recovery)
--    - Production: 7-30 days (operational recovery)
--    - Compliance: 90 days (regulatory requirements)
--
-- 8. Monitor storage costs - both Time Travel and Fail-safe consume storage.
--    Balance recovery needs with storage expenses.
--
-- 9. Common use cases:
--    - Accidental delete/update recovery
--    - Regulatory compliance and audit trails
--    - Debugging data pipeline issues
--    - Point-in-time reporting
--    - Data quality monitoring
--    - Schema change testing
--
-- 10. Best practice: Test recovery procedures regularly. Verify retention
--     settings match business requirements and SLAs.
-- ============================================================================
