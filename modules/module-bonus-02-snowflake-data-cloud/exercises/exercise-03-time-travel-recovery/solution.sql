-- ============================================================================
-- Exercise 03: Time Travel and Data Recovery - SOLUTION
-- ============================================================================
--
-- This solution demonstrates Snowflake's Time Travel and UNDROP capabilities
-- for data recovery, auditing, and disaster recovery scenarios.
-- ============================================================================

-- ============================================================================
-- SETUP: Create Database and Initial Tables
-- ============================================================================

CREATE OR REPLACE DATABASE time_travel_demo;
USE DATABASE time_travel_demo;
CREATE SCHEMA IF NOT EXISTS recovery;
USE SCHEMA recovery;

-- ============================================================================
-- TASK 1: Setup and Track Data Changes Over Time (15 points)
-- ============================================================================

-- Create orders table with 1000 initial records
CREATE OR REPLACE TABLE orders AS
SELECT
    SEQ4() as order_id,
    UNIFORM(1, 500, RANDOM()) as customer_id,
    UNIFORM(10, 5000, RANDOM()) / 10.0 as amount,
    DATEADD(day, -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()) as order_date,
    'pending' as status,
    CURRENT_TIMESTAMP() as created_at
FROM TABLE(GENERATOR(ROWCOUNT => 1000));

-- Record the initial timestamp (T0)
SET timestamp_t0 = (SELECT CURRENT_TIMESTAMP()::VARCHAR);
SELECT 'T0 - Initial Creation: ' || $timestamp_t0 as checkpoint;

-- Wait a moment to ensure distinct timestamps
CALL SYSTEM$WAIT(5);

-- First modification: Insert 200 more orders (T1)
INSERT INTO orders
SELECT
    SEQ4() + 1000 as order_id,
    UNIFORM(1, 500, RANDOM()) as customer_id,
    UNIFORM(10, 5000, RANDOM()) / 10.0 as amount,
    DATEADD(day, -UNIFORM(0, 180, RANDOM()), CURRENT_DATE()) as order_date,
    'pending' as status,
    CURRENT_TIMESTAMP() as created_at
FROM TABLE(GENERATOR(ROWCOUNT => 200));

SET timestamp_t1 = (SELECT CURRENT_TIMESTAMP()::VARCHAR);
SELECT 'T1 - After Insert: ' || $timestamp_t1 || ' (Row count: ' || (SELECT COUNT(*) FROM orders) || ')' as checkpoint;

-- Wait again
CALL SYSTEM$WAIT(5);

-- Second modification: Update order statuses (T2)
UPDATE orders
SET status = 'shipped',
    created_at = CURRENT_TIMESTAMP()
WHERE order_id % 5 = 0;

SET timestamp_t2 = (SELECT CURRENT_TIMESTAMP()::VARCHAR);
SELECT 'T2 - After Update: ' || $timestamp_t2 || ' (Shipped: ' || (SELECT COUNT(*) FROM orders WHERE status = 'shipped') || ')' as checkpoint;

-- Wait again
CALL SYSTEM$WAIT(5);

-- Third modification: Delete some old orders (T3)
DELETE FROM orders
WHERE order_date < DATEADD(day, -180, CURRENT_DATE());

SET timestamp_t3 = (SELECT CURRENT_TIMESTAMP()::VARCHAR);
SELECT 'T3 - After Delete: ' || $timestamp_t3 || ' (Row count: ' || (SELECT COUNT(*) FROM orders) || ')' as checkpoint;

-- Verify current state
SELECT
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
    COUNT(CASE WHEN status = 'shipped' THEN 1 END) as shipped_orders,
    MIN(order_date) as earliest_order,
    MAX(order_date) as latest_order
FROM orders;

-- ============================================================================
-- TASK 2: Query Historical Data States (20 points)
-- ============================================================================

-- Query orders at initial creation time (T0)
SELECT
    'T0 - Initial State' as time_point,
    COUNT(*) as row_count,
    COUNT(DISTINCT status) as status_types
FROM orders AT(TIMESTAMP => $timestamp_t0::TIMESTAMP_NTZ);

-- Query orders after first insert (T1) - should have 1200 rows
SELECT
    'T1 - After First Insert' as time_point,
    COUNT(*) as row_count,
    MIN(order_id) as min_order_id,
    MAX(order_id) as max_order_id
FROM orders AT(TIMESTAMP => $timestamp_t1::TIMESTAMP_NTZ);

-- Query orders after updates (T2) - should have shipped orders
SELECT
    'T2 - After Status Update' as time_point,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'shipped' THEN 1 END) as shipped_orders,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders
FROM orders AT(TIMESTAMP => $timestamp_t2::TIMESTAMP_NTZ);

-- Compare row counts across all time points
SELECT
    'T0 - Initial' as checkpoint,
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => $timestamp_t0::TIMESTAMP_NTZ)) as row_count
UNION ALL
SELECT
    'T1 - After Insert',
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => $timestamp_t1::TIMESTAMP_NTZ))
UNION ALL
SELECT
    'T2 - After Update',
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => $timestamp_t2::TIMESTAMP_NTZ))
UNION ALL
SELECT
    'T3 - After Delete',
    (SELECT COUNT(*) FROM orders AT(TIMESTAMP => $timestamp_t3::TIMESTAMP_NTZ))
UNION ALL
SELECT
    'Current State',
    (SELECT COUNT(*) FROM orders);

-- Show order status evolution over time
SELECT
    checkpoint,
    row_count,
    pending_count,
    shipped_count,
    ROUND(shipped_count / row_count * 100, 2) as shipped_percentage
FROM (
    SELECT
        'T1' as checkpoint,
        COUNT(*) as row_count,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
        COUNT(CASE WHEN status = 'shipped' THEN 1 END) as shipped_count
    FROM orders AT(TIMESTAMP => $timestamp_t1::TIMESTAMP_NTZ)
    UNION ALL
    SELECT
        'T2',
        COUNT(*),
        COUNT(CASE WHEN status = 'pending' THEN 1 END),
        COUNT(CASE WHEN status = 'shipped' THEN 1 END)
    FROM orders AT(TIMESTAMP => $timestamp_t2::TIMESTAMP_NTZ)
    UNION ALL
    SELECT
        'Current',
        COUNT(*),
        COUNT(CASE WHEN status = 'pending' THEN 1 END),
        COUNT(CASE WHEN status = 'shipped' THEN 1 END)
    FROM orders
);

-- Query using OFFSET (seconds ago) - 30 seconds ago
SELECT
    'Using OFFSET' as method,
    COUNT(*) as row_count
FROM orders AT(OFFSET => -30);

-- ============================================================================
-- TASK 3: UNDROP - Recover Dropped Objects (20 points)
-- ============================================================================

-- Create a test table with important customer data
CREATE OR REPLACE TABLE customer_data AS
SELECT
    SEQ4() as customer_id,
    'Customer_' || SEQ4() as customer_name,
    'customer' || SEQ4() || '@example.com' as email,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'Gold'
        WHEN 2 THEN 'Silver'
        WHEN 3 THEN 'Bronze'
        ELSE 'Platinum'
    END as tier,
    UNIFORM(0, 100000, RANDOM()) / 100.0 as account_balance,
    DATEADD(day, -UNIFORM(1, 1095, RANDOM()), CURRENT_DATE()) as signup_date
FROM TABLE(GENERATOR(ROWCOUNT => 500));

-- Verify the table exists and has data
SELECT
    'customer_data before drop' as status,
    COUNT(*) as row_count,
    SUM(account_balance) as total_balance,
    COUNT(DISTINCT tier) as tier_count
FROM customer_data;

-- Record row count for verification
SET original_row_count = (SELECT COUNT(*) FROM customer_data);

-- Simulate accidental drop
DROP TABLE customer_data;

-- Verify the table is gone (this will fail)
-- SELECT COUNT(*) FROM customer_data;  -- Uncommenting this would cause an error

-- Show that table doesn't exist
SHOW TABLES LIKE 'customer_data';

-- Recover the table using UNDROP
UNDROP TABLE customer_data;

-- Verify data was recovered completely
SELECT
    'customer_data after UNDROP' as status,
    COUNT(*) as row_count,
    COUNT(*) = $original_row_count as data_intact
FROM customer_data;

-- Test UNDROP with schemas
CREATE SCHEMA test_schema;
CREATE TABLE test_schema.test_table AS SELECT 1 as id, 'test' as value;

-- Verify schema exists
SELECT COUNT(*) as table_count FROM test_schema.INFORMATION_SCHEMA.TABLES;

-- Drop and recover entire schema
DROP SCHEMA test_schema;

-- Schema is gone
-- SHOW TABLES IN SCHEMA test_schema;  -- Would fail

-- Recover schema
UNDROP SCHEMA test_schema;

-- Verify recovery
SELECT 'Schema recovered' as status, COUNT(*) as tables
FROM test_schema.INFORMATION_SCHEMA.TABLES;

-- ============================================================================
-- TASK 4: Point-in-Time Recovery (25 points)
-- ============================================================================

-- Create a critical transactions table
CREATE OR REPLACE TABLE financial_transactions AS
SELECT
    SEQ4() as transaction_id,
    UNIFORM(1, 100, RANDOM()) as account_id,
    UNIFORM(10, 10000, RANDOM()) / 100.0 as amount,
    CASE UNIFORM(1, 3, RANDOM())
        WHEN 1 THEN 'deposit'
        WHEN 2 THEN 'withdrawal'
        ELSE 'transfer'
    END as transaction_type,
    CURRENT_TIMESTAMP() as transaction_time
FROM TABLE(GENERATOR(ROWCOUNT => 500));

-- Verify initial state
SELECT
    'Initial State' as checkpoint,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM financial_transactions;

-- Record timestamp BEFORE corruption (recovery checkpoint)
CALL SYSTEM$WAIT(3);
SET recovery_checkpoint = (SELECT CURRENT_TIMESTAMP()::VARCHAR);
SELECT 'Recovery Checkpoint: ' || $recovery_checkpoint as message;

-- Record correct totals
SET correct_transaction_count = (SELECT COUNT(*) FROM financial_transactions);
SET correct_total_amount = (SELECT SUM(amount) FROM financial_transactions);

-- Wait to ensure distinct timestamp
CALL SYSTEM$WAIT(3);

-- Simulate data corruption - accidentally update all amounts to zero
UPDATE financial_transactions
SET amount = 0,
    transaction_type = 'corrupted'
WHERE transaction_id % 3 = 0;

-- Additional corruption - delete some records
DELETE FROM financial_transactions
WHERE transaction_id % 5 = 0;

-- Verify corruption occurred
SELECT
    'Corrupted State' as checkpoint,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    COUNT(CASE WHEN amount = 0 THEN 1 END) as zero_amount_count,
    COUNT(CASE WHEN transaction_type = 'corrupted' THEN 1 END) as corrupted_records
FROM financial_transactions;

-- Perform point-in-time recovery
-- Create a clean copy from before corruption
CREATE OR REPLACE TABLE financial_transactions_recovered CLONE financial_transactions
    AT(TIMESTAMP => $recovery_checkpoint::TIMESTAMP_NTZ);

-- Verify recovery was successful
SELECT
    'Recovered State' as checkpoint,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    COUNT(*) = $correct_transaction_count as row_count_matches,
    ABS(SUM(amount) - $correct_total_amount) < 0.01 as amount_matches
FROM financial_transactions_recovered;

-- Replace corrupted table with recovered data
DROP TABLE financial_transactions;
ALTER TABLE financial_transactions_recovered RENAME TO financial_transactions;

-- Final verification
SELECT
    'Final Verification' as status,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    COUNT(CASE WHEN amount = 0 THEN 1 END) as zero_amount_count,
    COUNT(CASE WHEN transaction_type = 'corrupted' THEN 1 END) as corrupted_records,
    'Recovery Successful' as result
FROM financial_transactions;

-- ============================================================================
-- TASK 5: Configure Retention Periods (10 points)
-- ============================================================================

-- Check default retention period
SELECT
    table_catalog,
    table_schema,
    table_name,
    retention_time
FROM INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'RECOVERY'
    AND table_name = 'ORDERS';

-- Set extended retention for critical financial data
-- Note: Requires Enterprise Edition or higher
ALTER TABLE financial_transactions
SET DATA_RETENTION_TIME_IN_DAYS = 90;

-- For staging/temporary tables, use minimal retention
CREATE OR REPLACE TABLE staging_temp_data AS
SELECT 1 as id;

ALTER TABLE staging_temp_data
SET DATA_RETENTION_TIME_IN_DAYS = 0;

-- View retention settings for all tables
SELECT
    table_name,
    retention_time as retention_days,
    CASE
        WHEN retention_time >= 90 THEN 'Critical - Extended Retention'
        WHEN retention_time >= 7 THEN 'Standard Retention'
        WHEN retention_time >= 1 THEN 'Minimal Retention'
        ELSE 'No Time Travel'
    END as retention_classification,
    table_type
FROM INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'RECOVERY'
ORDER BY retention_time DESC, table_name;

-- Check Time Travel availability
SELECT
    table_name,
    retention_time,
    CASE
        WHEN retention_time > 0
        THEN DATEADD(day, -retention_time, CURRENT_TIMESTAMP())
        ELSE NULL
    END as oldest_recoverable_timestamp
FROM INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'RECOVERY'
    AND table_name IN ('ORDERS', 'FINANCIAL_TRANSACTIONS');

-- ============================================================================
-- TASK 6: Design Disaster Recovery Plan (10 points)
-- ============================================================================

/*
COMPREHENSIVE DISASTER RECOVERY SCENARIOS AND SOLUTIONS

===========================================================================
SCENARIO 1: Accidental Table Drop
===========================================================================
Problem:
    A developer or analyst accidentally drops a production table during
    routine maintenance or cleanup operations.

Solution:
    Use UNDROP TABLE command to recover the dropped table instantly.
    All data and structure are preserved within the retention period.

SQL Example:
    -- Immediate recovery
    UNDROP TABLE critical_customer_data;

    -- Verify recovery
    SELECT COUNT(*) FROM critical_customer_data;

Recovery Time:
    < 1 second (instant metadata operation)

Best Practices:
    - Document table drops in change logs
    - Use separate dev/prod environments
    - Implement DROP protection with roles/permissions
    - Regular backup verification

===========================================================================
SCENARIO 2: Bulk Data Corruption
===========================================================================
Problem:
    A batch job or ETL process corrupts large amounts of data with
    incorrect values, affecting business operations and reporting.

Solution:
    Use Time Travel to clone data from before corruption occurred,
    then replace corrupted table with clean copy.

SQL Example:
    -- Identify corruption time (e.g., 2 hours ago)
    SET corruption_time = DATEADD(hour, -2, CURRENT_TIMESTAMP());

    -- Create clean copy from before corruption
    CREATE TABLE sales_clean CLONE sales
        AT(TIMESTAMP => $corruption_time);

    -- Verify clean data
    SELECT COUNT(*), SUM(amount) FROM sales_clean;

    -- Replace corrupted table
    DROP TABLE sales;
    ALTER TABLE sales_clean RENAME TO sales;

Recovery Time:
    1-5 minutes (depends on table size and metadata)

Best Practices:
    - Implement data validation checks
    - Use staging tables for transformations
    - Set appropriate retention periods (90 days for critical data)
    - Monitor data quality metrics

===========================================================================
SCENARIO 3: Malicious Data Deletion
===========================================================================
Problem:
    Unauthorized user or compromised account deletes critical business
    data, causing immediate operational impact.

Solution:
    Identify deletion timestamp from query history, then recover data
    using Time Travel to a point before the malicious activity.

SQL Example:
    -- Find deletion query in history
    SELECT query_id, query_text, start_time, user_name
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE query_text ILIKE '%DELETE FROM customer_orders%'
        AND start_time >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
    ORDER BY start_time DESC;

    -- Recover using BEFORE(STATEMENT)
    CREATE TABLE customer_orders_recovery CLONE customer_orders
        BEFORE(STATEMENT => '<query_id_from_above>');

    -- Verify and restore
    SELECT COUNT(*) FROM customer_orders_recovery;
    ALTER TABLE customer_orders SWAP WITH customer_orders_recovery;

Recovery Time:
    2-10 minutes (including investigation and verification)

Best Practices:
    - Enable query history monitoring
    - Implement row-level security
    - Use auth tokens with expiration
    - Regular access audits
    - Multi-factor authentication for production access

===========================================================================
SCENARIO 4: Application Bug Data Damage
===========================================================================
Problem:
    Application bug introduces systematic data errors over several hours,
    affecting multiple tables in a correlated manner.

Solution:
    Identify last known good state, clone all affected tables from that
    timestamp, and restore in a coordinated manner.

SQL Example:
    -- Set recovery point (last known good state)
    SET recovery_point = '2024-03-09 14:30:00'::TIMESTAMP_NTZ;

    -- Recover multiple related tables
    CREATE TABLE orders_restored CLONE orders
        AT(TIMESTAMP => $recovery_point);

    CREATE TABLE order_items_restored CLONE order_items
        AT(TIMESTAMP => $recovery_point);

    CREATE TABLE payments_restored CLONE payments
        AT(TIMESTAMP => $recovery_point);

    -- Verify referential integrity
    SELECT
        (SELECT COUNT(*) FROM orders_restored) as orders,
        (SELECT COUNT(*) FROM order_items_restored) as items,
        (SELECT COUNT(DISTINCT order_id) FROM order_items_restored) as orders_with_items;

    -- Coordinated restoration
    BEGIN TRANSACTION;
        DROP TABLE orders;
        DROP TABLE order_items;
        DROP TABLE payments;
        ALTER TABLE orders_restored RENAME TO orders;
        ALTER TABLE order_items_restored RENAME TO order_items;
        ALTER TABLE payments_restored RENAME TO payments;
    COMMIT;

Recovery Time:
    5-15 minutes (multiple table coordination)

Best Practices:
    - Thorough application testing before production
    - Implement application-level data validation
    - Use database constraints (FK, CHECK)
    - Staged rollouts with monitoring
    - Automated smoke tests after deployments

===========================================================================
SCENARIO 5: Incomplete Transaction Rollback
===========================================================================
Problem:
    Complex multi-statement transaction partially completes before failure,
    leaving database in inconsistent state requiring precise recovery.

Solution:
    Use query history to identify exact transaction boundaries, then
    restore to state before transaction began using Time Travel.

SQL Example:
    -- Find the transaction start time
    SELECT
        query_id,
        query_text,
        start_time,
        end_time,
        error_message
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE query_text ILIKE '%BEGIN%TRANSACTION%'
        AND start_time >= DATEADD(hour, -2, CURRENT_TIMESTAMP())
        AND session_id = <problematic_session_id>
    ORDER BY start_time DESC;

    -- Restore to before transaction
    CREATE TABLE inventory_pre_transaction CLONE inventory
        BEFORE(STATEMENT => '<transaction_query_id>');

    -- Verify consistency
    SELECT
        product_id,
        quantity,
        last_update
    FROM inventory_pre_transaction
    WHERE last_update < '<transaction_start_time>';

    -- Restore if verification passes
    BEGIN TRANSACTION;
        TRUNCATE TABLE inventory;
        INSERT INTO inventory SELECT * FROM inventory_pre_transaction;
    COMMIT;

Recovery Time:
    3-8 minutes (depends on transaction complexity)

Best Practices:
    - Use explicit transactions with proper error handling
    - Implement savepoints for complex operations
    - Log transaction boundaries
    - Use idempotent operations where possible
    - Automated transaction monitoring and alerting
*/

-- ============================================================================
-- BONUS: Advanced Time Travel Queries (Extra Credit)
-- ============================================================================

-- Query changes between two timestamps
-- Show what changed in a 10-minute window
WITH time_t1 AS (
    SELECT order_id, amount, status
    FROM orders AT(TIMESTAMP => $timestamp_t1::TIMESTAMP_NTZ)
),
time_t3 AS (
    SELECT order_id, amount, status
    FROM orders AT(TIMESTAMP => $timestamp_t3::TIMESTAMP_NTZ)
)
SELECT
    'Changes between T1 and T3' as analysis,
    (SELECT COUNT(*) FROM time_t1) as count_t1,
    (SELECT COUNT(*) FROM time_t3) as count_t3,
    (SELECT COUNT(*) FROM time_t1) - (SELECT COUNT(*) FROM time_t3) as net_change;

-- Track who made changes when
SELECT
    user_name,
    query_type,
    query_text,
    rows_inserted,
    rows_updated,
    rows_deleted,
    start_time,
    execution_time / 1000 as execution_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE database_name = 'TIME_TRAVEL_DEMO'
    AND schema_name = 'RECOVERY'
    AND query_type IN ('INSERT', 'UPDATE', 'DELETE', 'CREATE_TABLE', 'DROP_TABLE')
    AND start_time >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
ORDER BY start_time DESC
LIMIT 20;

-- Create audit trail using Time Travel
-- Compare current vs 1 hour ago to detect changes
SELECT
    'Audit Trail' as report,
    current.order_id,
    historical.amount as amount_1hr_ago,
    current.amount as amount_current,
    current.amount - historical.amount as amount_change,
    historical.status as status_1hr_ago,
    current.status as status_current
FROM orders current
LEFT JOIN orders AT(OFFSET => -3600) historical
    ON current.order_id = historical.order_id
WHERE current.amount != historical.amount
    OR current.status != historical.status
LIMIT 50;

-- ============================================================================
-- SUMMARY: Time Travel Best Practices
-- ============================================================================

/*
1. Retention Planning:
   - Critical data: 90 days (Enterprise Edition)
   - Standard data: 7-30 days
   - Temporary data: 0-1 days
   - Balance cost vs recovery needs

2. Recovery Procedures:
   - Document recovery procedures
   - Test recovery regularly
   - Monitor Time Travel storage costs
   - Train team on recovery tools

3. Cost Management:
   - Monitor Time Travel bytes in TABLE_STORAGE_METRICS
   - Set appropriate retention by data criticality
   - Clean up unnecessary historical data
   - Use TRANSIENT tables for staging data

4. Security:
   - Restrict DROP and TRUNCATE permissions
   - Audit sensitive data changes
   - Use query history for forensics
   - Implement change approval processes

5. Performance:
   - Use specific timestamps for better performance
   - Historical queries may be slower
   - Consider result caching
   - Monitor resource usage
*/

-- ============================================================================
-- CLEANUP (Optional)
-- ============================================================================

-- DROP DATABASE IF EXISTS time_travel_demo;

-- ============================================================================
-- END OF SOLUTION
-- ============================================================================
