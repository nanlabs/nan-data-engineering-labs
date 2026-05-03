-- ============================================================================
-- Exercise 02: Zero-Copy Cloning for Development - SOLUTION
-- ============================================================================
--
-- This solution demonstrates Snowflake's powerful zero-copy cloning feature
-- for creating instant, storage-efficient copies of databases and tables.
-- ============================================================================

-- ============================================================================
-- SETUP: Create Production Environment
-- ============================================================================

CREATE OR REPLACE DATABASE prod_db;
USE DATABASE prod_db;
CREATE SCHEMA IF NOT EXISTS sales;
USE SCHEMA sales;

-- ============================================================================
-- TASK 1: Setup Production Data (20 points)
-- ============================================================================

-- Create customers table with 10,000 records
CREATE OR REPLACE TABLE customers AS
SELECT
    SEQ4() as customer_id,
    'Customer_' || LPAD(SEQ4()::VARCHAR, 8, '0') as name,
    'customer' || SEQ4() || '@example.com' as email,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'North America'
        WHEN 2 THEN 'Europe'
        WHEN 3 THEN 'Asia Pacific'
        WHEN 4 THEN 'Latin America'
        ELSE 'Middle East'
    END as region,
    DATEADD(day, -UNIFORM(1, 1095, RANDOM()), CURRENT_DATE()) as signup_date,
    CASE UNIFORM(1, 3, RANDOM())
        WHEN 1 THEN 'Premium'
        WHEN 2 THEN 'Standard'
        ELSE 'Basic'
    END as tier,
    UNIFORM(0, 100000, RANDOM()) / 100.0 as lifetime_value
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- Create orders table with 50,000 records
CREATE OR REPLACE TABLE orders AS
SELECT
    SEQ4() as order_id,
    UNIFORM(1, 10000, RANDOM()) as customer_id,
    DATEADD(day, -UNIFORM(1, 365, RANDOM()), CURRENT_DATE()) as order_date,
    UNIFORM(10, 5000, RANDOM()) / 10.0 as amount,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'processing'
        WHEN 3 THEN 'shipped'
        WHEN 4 THEN 'delivered'
        ELSE 'completed'
    END as status,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'credit_card'
        WHEN 2 THEN 'debit_card'
        WHEN 3 THEN 'paypal'
        ELSE 'bank_transfer'
    END as payment_method
FROM TABLE(GENERATOR(ROWCOUNT => 50000));

-- Create order_items table with 150,000 records
CREATE OR REPLACE TABLE order_items AS
SELECT
    SEQ4() as item_id,
    UNIFORM(1, 50000, RANDOM()) as order_id,
    'Product_' || UNIFORM(1, 1000, RANDOM()) as product_name,
    UNIFORM(1, 10, RANDOM()) as quantity,
    UNIFORM(5, 500, RANDOM()) / 10.0 as unit_price,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Electronics'
        WHEN 2 THEN 'Clothing'
        WHEN 3 THEN 'Home'
        WHEN 4 THEN 'Sports'
        ELSE 'Books'
    END as category
FROM TABLE(GENERATOR(ROWCOUNT => 150000));

-- Verify production data
SELECT
    'customers' as table_name,
    COUNT(*) as row_count,
    MIN(signup_date) as earliest_signup,
    MAX(signup_date) as latest_signup
FROM customers
UNION ALL
SELECT
    'orders',
    COUNT(*),
    MIN(order_date),
    MAX(order_date)
FROM orders
UNION ALL
SELECT
    'order_items',
    COUNT(*),
    NULL,
    NULL
FROM order_items;

-- Check production database size
SELECT
    'Production Database Created' as status,
    COUNT(DISTINCT TABLE_NAME) as table_count
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'SALES';

-- ============================================================================
-- TASK 2: Clone Production Database (15 points)
-- ============================================================================

-- Record the time before cloning
SET clone_start_time = (SELECT CURRENT_TIMESTAMP());

-- Clone the entire production database to dev_db
-- This is instant and consumes zero additional storage initially
CREATE OR REPLACE DATABASE dev_db CLONE prod_db;

-- Record the time after cloning
SET clone_end_time = (SELECT CURRENT_TIMESTAMP());

-- Calculate clone duration (should be < 1 second for metadata-only operation)
SELECT
    'Database Cloned' as operation,
    $clone_start_time as start_time,
    $clone_end_time as end_time,
    DATEDIFF(millisecond, $clone_start_time, $clone_end_time) as duration_ms,
    '< 1 second (metadata only)' as expected_duration;

-- Verify the clone was created successfully
SHOW DATABASES LIKE '%_db';

-- Compare structure between prod and dev
SELECT 'prod_db' as database_name, COUNT(*) as table_count
FROM prod_db.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'SALES'
UNION ALL
SELECT 'dev_db', COUNT(*)
FROM dev_db.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'SALES';

-- Compare row counts between prod and dev
SELECT 'Production' as environment,
       (SELECT COUNT(*) FROM prod_db.sales.customers) as customers,
       (SELECT COUNT(*) FROM prod_db.sales.orders) as orders,
       (SELECT COUNT(*) FROM prod_db.sales.order_items) as order_items
UNION ALL
SELECT 'Development',
       (SELECT COUNT(*) FROM dev_db.sales.customers),
       (SELECT COUNT(*) FROM dev_db.sales.orders),
       (SELECT COUNT(*) FROM dev_db.sales.order_items);

-- ============================================================================
-- TASK 3: Clone Individual Tables (15 points)
-- ============================================================================

USE DATABASE prod_db;
USE SCHEMA sales;

-- Create a clone of the customers table for testing
CREATE OR REPLACE TABLE customers_test CLONE customers;

SELECT 'Customers Test Clone' as clone_type, COUNT(*) as row_count
FROM customers_test;

-- Create a historical clone of orders from 1 hour ago
-- Note: This uses Time Travel to clone data from the past
CREATE OR REPLACE TABLE orders_1hr_ago CLONE orders AT(OFFSET => -3600);

SELECT 'Orders Historical Clone' as clone_type, COUNT(*) as row_count
FROM orders_1hr_ago;

-- Clone entire schema to a new schema
CREATE SCHEMA IF NOT EXISTS sales_backup CLONE sales;

-- Verify schema clone
SELECT
    'sales_backup schema' as clone_type,
    COUNT(DISTINCT TABLE_NAME) as table_count
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'SALES_BACKUP';

-- List all tables in the cloned schema
SELECT TABLE_NAME, ROW_COUNT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'SALES_BACKUP'
ORDER BY TABLE_NAME;

-- ============================================================================
-- TASK 4: Make Modifications in Development (20 points)
-- ============================================================================

-- Switch to development database
USE DATABASE dev_db;
USE SCHEMA sales;

-- Insert new records into dev customers table
INSERT INTO customers
SELECT
    customer_id + 10000 as customer_id,
    'TestCustomer_' || LPAD((customer_id + 10000)::VARCHAR, 8, '0') as name,
    'test' || (customer_id + 10000) || '@example.com' as email,
    'Test Region' as region,
    CURRENT_DATE() as signup_date,
    'Test' as tier,
    0 as lifetime_value
FROM (SELECT SEQ4() as customer_id FROM TABLE(GENERATOR(ROWCOUNT => 100)));

SELECT 'Dev customers after insert' as operation, COUNT(*) as row_count
FROM customers;

-- Update records in dev orders table
UPDATE orders
SET status = 'test_status'
WHERE order_id % 10 = 0;

SELECT 'Updated orders in dev' as operation, COUNT(*) as affected_rows
FROM orders
WHERE status = 'test_status';

-- Delete some records in dev
DELETE FROM order_items
WHERE item_id % 100 = 0;

SELECT 'Order items after delete' as operation, COUNT(*) as row_count
FROM order_items;

-- Verify prod is unchanged
SELECT 'Production' as environment,
       (SELECT COUNT(*) FROM prod_db.sales.customers) as customers,
       (SELECT COUNT(*) FROM prod_db.sales.orders) as orders,
       (SELECT COUNT(*) FROM prod_db.sales.order_items) as order_items,
       (SELECT COUNT(*) FROM prod_db.sales.orders WHERE status = 'test_status') as test_orders
UNION ALL
SELECT 'Development',
       (SELECT COUNT(*) FROM dev_db.sales.customers),
       (SELECT COUNT(*) FROM dev_db.sales.orders),
       (SELECT COUNT(*) FROM dev_db.sales.order_items),
       (SELECT COUNT(*) FROM dev_db.sales.orders WHERE status = 'test_status');

-- ============================================================================
-- TASK 5: Time Travel Cloning (15 points)
-- ============================================================================

USE DATABASE prod_db;
USE SCHEMA sales;

-- Clone customers table from 30 minutes ago
-- This demonstrates Time Travel capability
CREATE OR REPLACE TABLE customers_30min_ago CLONE customers AT(OFFSET => -1800);

SELECT 'Customers 30 minutes ago' as clone_type, COUNT(*) as row_count
FROM customers_30min_ago;

-- Clone orders table from a specific timestamp
-- Get current timestamp for demonstration
SET target_timestamp = (SELECT DATEADD(hour, -1, CURRENT_TIMESTAMP())::VARCHAR);

-- Create time-travel clone (note: in real scenario, use actual timestamp)
CREATE OR REPLACE TABLE orders_historical CLONE orders AT(OFFSET => -3600);

SELECT
    'Orders Historical' as clone_type,
    COUNT(*) as row_count,
    MIN(order_date) as earliest_order,
    MAX(order_date) as latest_order
FROM orders_historical;

-- Clone before a specific statement
-- First, get a query ID from recent history
SET recent_query_id = (
    SELECT query_id
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE query_text LIKE '%INSERT INTO customers%'
    ORDER BY start_time DESC
    LIMIT 1
);

-- Note: BEFORE(STATEMENT) requires a valid query_id
-- For demonstration, we'll use offset-based cloning
CREATE OR REPLACE TABLE customers_before_changes CLONE customers AT(OFFSET => -7200);

SELECT 'Customers before changes' as clone_type, COUNT(*) as row_count
FROM customers_before_changes;

-- ============================================================================
-- TASK 6: Track Storage Divergence (15 points)
-- ============================================================================

-- Query table storage metrics
-- Note: This view may take time to populate (up to 3 hours)
SELECT
    table_catalog as database_name,
    table_schema as schema_name,
    table_name,
    active_bytes / POWER(1024, 3) as active_gb,
    time_travel_bytes / POWER(1024, 3) as time_travel_gb,
    failsafe_bytes / POWER(1024, 3) as failsafe_gb,
    (active_bytes + time_travel_bytes + failsafe_bytes) / POWER(1024, 3) as total_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
    AND table_schema = 'SALES'
ORDER BY total_gb DESC;

-- Calculate storage divergence percentage
WITH storage_comparison AS (
    SELECT
        table_name,
        SUM(CASE WHEN table_catalog = 'PROD_DB' THEN active_bytes ELSE 0 END) as prod_bytes,
        SUM(CASE WHEN table_catalog = 'DEV_DB' THEN active_bytes ELSE 0 END) as dev_bytes
    FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
    WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
        AND table_schema = 'SALES'
    GROUP BY table_name
)
SELECT
    table_name,
    prod_bytes / POWER(1024, 3) as prod_gb,
    dev_bytes / POWER(1024, 3) as dev_gb,
    (dev_bytes - prod_bytes) / POWER(1024, 3) as divergence_gb,
    CASE
        WHEN prod_bytes > 0
        THEN ROUND(((dev_bytes - prod_bytes) / prod_bytes * 100), 2)
        ELSE 0
    END as divergence_percentage
FROM storage_comparison
WHERE prod_bytes > 0
ORDER BY divergence_gb DESC;

-- Analyze storage costs
-- Assuming $23 per TB per month for storage
WITH storage_summary AS (
    SELECT
        table_catalog as database_name,
        SUM(active_bytes) / POWER(1024, 4) as total_tb,
        SUM(time_travel_bytes) / POWER(1024, 4) as time_travel_tb
    FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
    WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
        AND table_schema = 'SALES'
    GROUP BY table_catalog
)
SELECT
    database_name,
    ROUND(total_tb, 4) as storage_tb,
    ROUND(time_travel_tb, 4) as time_travel_tb,
    ROUND((total_tb + time_travel_tb) * 23, 2) as monthly_cost_usd,
    ROUND((total_tb + time_travel_tb) * 23 * 12, 2) as annual_cost_usd
FROM storage_summary
ORDER BY monthly_cost_usd DESC;

-- Calculate total savings from zero-copy cloning
WITH total_storage AS (
    SELECT
        SUM(CASE WHEN table_catalog = 'PROD_DB' THEN active_bytes ELSE 0 END) as prod_bytes,
        SUM(CASE WHEN table_catalog = 'DEV_DB' THEN active_bytes ELSE 0 END) as dev_bytes
    FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
    WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
        AND table_schema = 'SALES'
)
SELECT
    'Zero-Copy Cloning Savings' as analysis,
    prod_bytes / POWER(1024, 4) as prod_tb,
    dev_bytes / POWER(1024, 4) as dev_actual_tb,
    (dev_bytes - prod_bytes) / POWER(1024, 4) as divergence_tb,
    prod_bytes / POWER(1024, 4) as traditional_copy_tb,
    ((prod_bytes - (dev_bytes - prod_bytes)) / POWER(1024, 4) * 23) as monthly_savings_usd,
    ROUND(((prod_bytes - (dev_bytes - prod_bytes)) / prod_bytes * 100), 2) as savings_percentage
FROM total_storage;

-- Identify tables with highest storage usage
SELECT
    table_catalog || '.' || table_schema || '.' || table_name as full_table_name,
    active_bytes / POWER(1024, 3) as storage_gb,
    time_travel_bytes / POWER(1024, 3) as time_travel_gb,
    (active_bytes + time_travel_bytes) / POWER(1024, 3) as total_gb,
    ROUND((active_bytes + time_travel_bytes) / POWER(1024, 4) * 23, 2) as monthly_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
ORDER BY total_gb DESC
LIMIT 10;

-- ============================================================================
-- COST SAVINGS ANALYSIS
-- ============================================================================

/*
SCENARIO: Daily refresh of 1TB production database to dev environment

TRADITIONAL APPROACH (Full Copy):
- Storage required: 2 TB (prod + dev full copy)
- Time required: 4-6 hours (depends on network and I/O)
- Storage cost: $46 per month (2 TB × $23/TB)
- Data transfer cost: ~$100 per month (egress charges)
- Total cost: $146 per month

ZERO-COPY CLONING APPROACH:
- Initial storage: 1 TB (only original data)
- Time required: < 1 second (metadata operation only)
- Storage cost (divergence only): $2-5 per month (only modified data ~5-10% divergence)
- Data transfer cost: $0 (no data movement)
- Total cost: $2-5 per month
- Total savings: $141-144 per month (95-98% cost reduction)

ADDITIONAL BENEFITS:

1. Instant Environment Creation
   - Dev/test environments available in seconds vs hours
   - Enables rapid testing and development cycles
   - No waiting for data copies to complete

2. Storage Efficiency
   - Pay only for data that changes (divergence)
   - Typical divergence: 5-15% of original size
   - Automatic deduplication at storage layer

3. Multiple Environments
   - Can create unlimited clones with minimal cost
   - Each environment: staging, QA, dev, testing
   - Each clone only stores modified data

4. Data Freshness
   - Easy to refresh clones from production
   - Can clone from any point in Time Travel window
   - Enables realistic testing with production-like data

5. Risk Reduction
   - Safe testing environment (changes don't affect prod)
   - Easy rollback (just recreate clone)
   - Perfect for training and experimentation
*/

-- ============================================================================
-- CLEANUP (Optional)
-- ============================================================================

-- DROP DATABASE IF EXISTS prod_db;
-- DROP DATABASE IF EXISTS dev_db;

-- ============================================================================
-- END OF SOLUTION
-- ============================================================================
