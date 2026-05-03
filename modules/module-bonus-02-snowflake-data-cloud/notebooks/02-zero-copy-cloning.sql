-- ============================================================================
-- Module Bonus 02: Snowflake Data Cloud
-- Notebook 02: Zero-Copy Cloning
-- ============================================================================
-- Description: Master Snowflake's zero-copy cloning feature to create instant
--              database, schema, and table copies without duplicating storage.
--              Learn dev/test workflows, time-travel cloning, and cost tracking.
--
-- Prerequisites:
--   - Snowflake account with CREATE DATABASE privilege
--   - Understanding of Snowflake storage architecture
--   - Completed Virtual Warehouses notebook
--
-- Estimated Time: 75 minutes
-- ============================================================================

-- ============================================================================
-- SETUP: Create Production Environment
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Create a dedicated warehouse for cloning experiments
CREATE OR REPLACE WAREHOUSE clone_demo_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE clone_demo_wh;

-- Create production database with realistic data
CREATE OR REPLACE DATABASE prod_ecommerce;
USE DATABASE prod_ecommerce;

CREATE OR REPLACE SCHEMA sales;
USE SCHEMA sales;

-- Create production customers table
CREATE OR REPLACE TABLE customers (
    customer_id NUMBER(10,0) PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'USA',
    customer_since DATE,
    loyalty_tier VARCHAR(20),
    lifetime_value DECIMAL(12,2),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Generate 10,000 customer records
INSERT INTO customers
SELECT
    SEQ4() AS customer_id,
    CONCAT('user', SEQ4(), '@example.com') AS email,
    ARRAY_GET(PARSE_JSON('["John","Jane","Michael","Emily","David","Sarah","James","Emma","Robert","Lisa"]'),
              UNIFORM(0, 9, RANDOM())) AS first_name,
    ARRAY_GET(PARSE_JSON('["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez"]'),
              UNIFORM(0, 9, RANDOM())) AS last_name,
    CONCAT('555-', LPAD(UNIFORM(100, 999, RANDOM())::VARCHAR, 3, '0'), '-',
           LPAD(UNIFORM(1000, 9999, RANDOM())::VARCHAR, 4, '0')) AS phone,
    CONCAT(UNIFORM(100, 9999, RANDOM()), ' Main St') AS address,
    ARRAY_GET(PARSE_JSON('["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","San Jose"]'),
              UNIFORM(0, 9, RANDOM())) AS city,
    ARRAY_GET(PARSE_JSON('["NY","CA","IL","TX","AZ","PA","TX","CA","TX","CA"]'),
              UNIFORM(0, 9, RANDOM())) AS state,
    LPAD(UNIFORM(10000, 99999, RANDOM())::VARCHAR, 5, '0') AS zip_code,
    'USA' AS country,
    DATEADD(DAY, -UNIFORM(1, 1825, RANDOM()), CURRENT_DATE()) AS customer_since,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        ELSE 'Bronze'
    END AS loyalty_tier,
    UNIFORM(100, 50000, RANDOM()) AS lifetime_value,
    DATEADD(DAY, -UNIFORM(1, 1825, RANDOM()), CURRENT_TIMESTAMP()) AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- Verify customer data
SELECT COUNT(*) AS total_customers FROM customers;
-- Expected: 10000

SELECT * FROM customers LIMIT 5;


-- Create production orders table
CREATE OR REPLACE TABLE orders (
    order_id NUMBER(12,0) PRIMARY KEY,
    customer_id NUMBER(10,0) NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE NOT NULL,
    order_status VARCHAR(20),
    total_amount DECIMAL(12,2),
    tax_amount DECIMAL(10,2),
    shipping_amount DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    payment_method VARCHAR(30),
    shipping_address VARCHAR(200),
    shipping_city VARCHAR(50),
    shipping_state VARCHAR(2),
    shipping_zip VARCHAR(10),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Generate 50,000 order records
INSERT INTO orders
SELECT
    SEQ4() AS order_id,
    UNIFORM(0, 9999, RANDOM()) AS customer_id,
    CONCAT('ORD-', LPAD(SEQ4()::VARCHAR, 10, '0')) AS order_number,
    DATEADD(DAY, -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()) AS order_date,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'Pending'
        WHEN 2 THEN 'Processing'
        WHEN 3 THEN 'Shipped'
        WHEN 4 THEN 'Delivered'
        WHEN 5 THEN 'Cancelled'
        ELSE 'Delivered'
    END AS order_status,
    UNIFORM(50, 2000, RANDOM()) AS total_amount,
    UNIFORM(5, 200, RANDOM()) AS tax_amount,
    UNIFORM(0, 50, RANDOM()) AS shipping_amount,
    UNIFORM(0, 100, RANDOM()) AS discount_amount,
    ARRAY_GET(PARSE_JSON('["Credit Card","PayPal","Debit Card","Apple Pay","Google Pay"]'),
              UNIFORM(0, 4, RANDOM())) AS payment_method,
    CONCAT(UNIFORM(100, 9999, RANDOM()), ' Shipping Blvd') AS shipping_address,
    ARRAY_GET(PARSE_JSON('["New York","Los Angeles","Chicago","Houston","Phoenix"]'),
              UNIFORM(0, 4, RANDOM())) AS shipping_city,
    ARRAY_GET(PARSE_JSON('["NY","CA","IL","TX","AZ"]'),
              UNIFORM(0, 4, RANDOM())) AS shipping_state,
    LPAD(UNIFORM(10000, 99999, RANDOM())::VARCHAR, 5, '0') AS shipping_zip,
    DATEADD(DAY, -UNIFORM(0, 365, RANDOM()), CURRENT_TIMESTAMP()) AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM TABLE(GENERATOR(ROWCOUNT => 50000));

-- Verify order data
SELECT COUNT(*) AS total_orders FROM orders;
-- Expected: 50000

SELECT * FROM orders LIMIT 5;


-- Create order line items table
CREATE OR REPLACE TABLE order_items (
    item_id NUMBER(15,0) PRIMARY KEY,
    order_id NUMBER(12,0) NOT NULL,
    product_sku VARCHAR(50),
    product_name VARCHAR(200),
    category VARCHAR(50),
    quantity NUMBER(5,0),
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Generate 100,000 order item records
INSERT INTO order_items
SELECT
    SEQ4() AS item_id,
    UNIFORM(0, 49999, RANDOM()) AS order_id,
    CONCAT('SKU-', LPAD(UNIFORM(1, 5000, RANDOM())::VARCHAR, 8, '0')) AS product_sku,
    CONCAT('Product ', UNIFORM(1, 5000, RANDOM())) AS product_name,
    ARRAY_GET(PARSE_JSON('["Electronics","Clothing","Home & Garden","Sports","Books","Toys","Beauty","Automotive"]'),
              UNIFORM(0, 7, RANDOM())) AS category,
    UNIFORM(1, 5, RANDOM()) AS quantity,
    UNIFORM(10, 500, RANDOM()) AS unit_price,
    (UNIFORM(1, 5, RANDOM()) * UNIFORM(10, 500, RANDOM())) AS line_total,
    DATEADD(DAY, -UNIFORM(0, 365, RANDOM()), CURRENT_TIMESTAMP()) AS created_at
FROM TABLE(GENERATOR(ROWCOUNT => 100000));

-- Verify order items
SELECT COUNT(*) AS total_items FROM order_items;
-- Expected: 100000


-- Create analytics schema
CREATE SCHEMA IF NOT EXISTS analytics;
USE SCHEMA analytics;

-- Create aggregated view
CREATE OR REPLACE VIEW customer_summary AS
SELECT
    c.customer_id,
    c.email,
    c.first_name,
    c.last_name,
    c.loyalty_tier,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount) AS avg_order_value,
    MAX(o.order_date) AS last_order_date,
    DATEDIFF(DAY, MAX(o.order_date), CURRENT_DATE()) AS days_since_last_order
FROM prod_ecommerce.sales.customers c
LEFT JOIN prod_ecommerce.sales.orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.email, c.first_name, c.last_name, c.loyalty_tier;

SELECT * FROM customer_summary LIMIT 10;


-- Check production database size
SELECT
    'PROD_ECOMMERCE' AS database_name,
    COUNT(*) AS table_count,
    SUM(row_count) AS total_rows,
    SUM(bytes) / (1024*1024*1024) AS size_gb
FROM prod_ecommerce.information_schema.tables
WHERE table_type = 'BASE TABLE';

-- Expected Output:
-- DATABASE_NAME   | TABLE_COUNT | TOTAL_ROWS | SIZE_GB
-- ---------------+-------------+------------+---------
-- PROD_ECOMMERCE | 3           | 160000     | ~0.5


-- ============================================================================
-- SECTION 1: Clone Entire Database
-- ============================================================================
-- Zero-copy cloning creates an instant duplicate of database without copying
-- underlying data. The clone initially shares storage with source, diverging
-- only when data is modified.
-- ============================================================================

-- Clone production database to development (instant operation!)
CREATE OR REPLACE DATABASE dev_ecommerce
    CLONE prod_ecommerce;

-- Verify clone was created instantly
SHOW DATABASES LIKE '%ecommerce';
-- Shows both PROD_ECOMMERCE and DEV_ECOMMERCE

-- Check clone structure matches production
USE DATABASE dev_ecommerce;
SHOW SCHEMAS;
-- Expected: SALES, ANALYTICS, PUBLIC

USE SCHEMA sales;
SHOW TABLES;
-- Expected: CUSTOMERS, ORDERS, ORDER_ITEMS

-- Verify data was cloned
SELECT COUNT(*) AS customer_count FROM dev_ecommerce.sales.customers;
-- Expected: 10000 (same as production)

SELECT COUNT(*) AS order_count FROM dev_ecommerce.sales.orders;
-- Expected: 50000 (same as production)

SELECT COUNT(*) AS item_count FROM dev_ecommerce.sales.order_items;
-- Expected: 100000 (same as production)


-- Compare first 10 records between source and clone
SELECT 'PRODUCTION' AS source, * FROM prod_ecommerce.sales.customers ORDER BY customer_id LIMIT 10
UNION ALL
SELECT 'DEVELOPMENT' AS source, * FROM dev_ecommerce.sales.customers ORDER BY customer_id LIMIT 10;
-- Data should be identical


-- Check views were also cloned
USE SCHEMA dev_ecommerce.analytics;
SELECT * FROM customer_summary LIMIT 5;
-- View works in cloned database


-- Create staging clone for data quality testing
CREATE OR REPLACE DATABASE staging_ecommerce
    CLONE prod_ecommerce
    COMMENT = 'Staging environment for QA testing';

-- Create testing clone
CREATE OR REPLACE DATABASE test_ecommerce
    CLONE prod_ecommerce
    COMMENT = 'Test environment for development';


-- List all ecommerce databases
SHOW DATABASES LIKE '%ecommerce';
-- Shows: PROD_ECOMMERCE, DEV_ECOMMERCE, STAGING_ECOMMERCE, TEST_ECOMMERCE


-- Key insight: All clones created instantly, regardless of data size
-- Production database with 160K rows cloned in < 1 second!


-- ============================================================================
-- SECTION 2: Clone Individual Tables
-- ============================================================================
-- Clone specific tables for targeted testing or data exploration without
-- cloning entire database.
-- ============================================================================

USE DATABASE dev_ecommerce;
USE SCHEMA sales;

-- Clone a single table from production
CREATE OR REPLACE TABLE dev_customers_backup
    CLONE prod_ecommerce.sales.customers;

-- Verify table cloned
SELECT COUNT(*) FROM dev_customers_backup;
-- Expected: 10000

-- Clone with new name for experimentation
CREATE OR REPLACE TABLE customers_experiment
    CLONE prod_ecommerce.sales.customers;

-- Clone orders table to development
CREATE OR REPLACE TABLE dev_orders_backup
    CLONE prod_ecommerce.sales.orders;

SELECT COUNT(*) FROM dev_orders_backup;
-- Expected: 50000


-- Clone table to different database
CREATE OR REPLACE TABLE test_ecommerce.sales.customers_subset
    CLONE prod_ecommerce.sales.customers;

-- Verify cross-database clone
SELECT COUNT(*) FROM test_ecommerce.sales.customers_subset;
-- Expected: 10000


-- Clone with immediate modification
CREATE OR REPLACE TABLE customers_recent
    CLONE prod_ecommerce.sales.customers;

-- Filter to only recent customers in cloned table
DELETE FROM customers_recent
WHERE customer_since < DATEADD(YEAR, -1, CURRENT_DATE());

SELECT COUNT(*) FROM customers_recent;
-- Returns subset of customers (e.g., 2500)

-- Original production table unchanged
SELECT COUNT(*) FROM prod_ecommerce.sales.customers;
-- Still returns 10000


-- Create table clone for A/B testing
CREATE OR REPLACE TABLE customers_variant_a
    CLONE prod_ecommerce.sales.customers;

CREATE OR REPLACE TABLE customers_variant_b
    CLONE prod_ecommerce.sales.customers;

-- Apply different transformations to each variant
UPDATE customers_variant_a
SET loyalty_tier = 'Gold'
WHERE loyalty_tier = 'Silver'
  AND lifetime_value > 10000;

UPDATE customers_variant_b
SET loyalty_tier = 'Platinum'
WHERE loyalty_tier = 'Gold'
  AND lifetime_value > 20000;

-- Compare results of A/B test
SELECT
    'Variant A' AS variant,
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers_variant_a
GROUP BY loyalty_tier
UNION ALL
SELECT
    'Variant B' AS variant,
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers_variant_b
GROUP BY loyalty_tier
ORDER BY variant, loyalty_tier;


-- ============================================================================
-- SECTION 3: Clone Schemas
-- ============================================================================
-- Clone entire schemas to replicate related tables and views together.
-- ============================================================================

USE DATABASE dev_ecommerce;

-- Clone sales schema with all tables
CREATE OR REPLACE SCHEMA sales_backup
    CLONE prod_ecommerce.sales;

-- Verify all tables cloned
SHOW TABLES IN SCHEMA sales_backup;
-- Expected: CUSTOMERS, ORDERS, ORDER_ITEMS

SELECT COUNT(*) FROM sales_backup.customers;
-- Expected: 10000

SELECT COUNT(*) FROM sales_backup.orders;
-- Expected: 50000


-- Clone analytics schema
CREATE OR REPLACE SCHEMA analytics_backup
    CLONE prod_ecommerce.analytics;

-- Verify views cloned
SHOW VIEWS IN SCHEMA analytics_backup;
-- Expected: CUSTOMER_SUMMARY

SELECT COUNT(*) FROM analytics_backup.customer_summary;
-- Expected: 10000


-- Clone schema to different database
CREATE OR REPLACE SCHEMA staging_ecommerce.sales_v2
    CLONE prod_ecommerce.sales
    COMMENT = 'Sales schema clone for v2 testing';

-- Verify cross-database schema clone
USE DATABASE staging_ecommerce;
USE SCHEMA sales_v2;
SHOW TABLES;
-- Shows all sales tables


-- Clone schema and immediately modify structure
CREATE OR REPLACE SCHEMA dev_ecommerce.sales_expanded
    CLONE prod_ecommerce.sales;

-- Add new column to cloned schema (doesn't affect production)
ALTER TABLE dev_ecommerce.sales_expanded.customers
ADD COLUMN customer_segment VARCHAR(50);

-- Verify new column only in clone
DESC TABLE dev_ecommerce.sales_expanded.customers;
-- Shows CUSTOMER_SEGMENT column

DESC TABLE prod_ecommerce.sales.customers;
-- Does not show CUSTOMER_SEGMENT column


-- ============================================================================
-- SECTION 4: Modify Clones and Track Storage Divergence
-- ============================================================================
-- Once clones are modified, they begin consuming additional storage.
-- Track how storage diverges between source and clone.
-- ============================================================================

USE DATABASE dev_ecommerce;
USE SCHEMA sales;

-- Baseline: Check current clone storage (shared with production)
USE DATABASE dev_ecommerce;

-- Insert new records to development clone
INSERT INTO dev_ecommerce.sales.customers
SELECT
    customer_id + 10000 AS customer_id,
    CONCAT('devuser', customer_id, '@test.com') AS email,
    first_name,
    last_name,
    phone,
    address,
    city,
    state,
    zip_code,
    country,
    CURRENT_DATE() AS customer_since,
    'Bronze' AS loyalty_tier,
    0 AS lifetime_value,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM prod_ecommerce.sales.customers
WHERE customer_id < 1000;  -- Insert 1000 new records

-- Verify insert
SELECT COUNT(*) FROM dev_ecommerce.sales.customers;
-- Expected: 11000 (10000 original + 1000 new)

SELECT COUNT(*) FROM prod_ecommerce.sales.customers;
-- Still 10000 (production unchanged)


-- Update records in development clone
UPDATE dev_ecommerce.sales.customers
SET loyalty_tier = 'Test'
WHERE customer_id >= 10000;

-- Verify update only affected clone
SELECT loyalty_tier, COUNT(*)
FROM dev_ecommerce.sales.customers
GROUP BY loyalty_tier;
-- Shows 'Test' tier

SELECT loyalty_tier, COUNT(*)
FROM prod_ecommerce.sales.customers
GROUP BY loyalty_tier;
-- No 'Test' tier in production


-- Delete records from clone
DELETE FROM dev_ecommerce.sales.customers
WHERE customer_id BETWEEN 5000 AND 5500;

SELECT COUNT(*) FROM dev_ecommerce.sales.customers;
-- Expected: 10500 (11000 - 500 deleted)

SELECT COUNT(*) FROM prod_ecommerce.sales.customers;
-- Still 10000 (production unchanged)


-- Perform large update to simulate development work
UPDATE dev_ecommerce.sales.orders
SET order_status = 'Dev Testing'
WHERE order_id < 5000;

-- Verify production unaffected
SELECT DISTINCT order_status
FROM prod_ecommerce.sales.orders
ORDER BY order_status;
-- No 'Dev Testing' status

SELECT DISTINCT order_status
FROM dev_ecommerce.sales.orders
ORDER BY order_status;
-- Shows 'Dev Testing' status


-- Track table-level storage changes
SELECT
    'PROD - Customers' AS table_name,
    active_bytes / (1024*1024) AS active_mb,
    time_travel_bytes / (1024*1024) AS time_travel_mb,
    failsafe_bytes / (1024*1024) AS failsafe_mb
FROM prod_ecommerce.information_schema.table_storage_metrics
WHERE table_name = 'CUSTOMERS'
UNION ALL
SELECT
    'DEV - Customers' AS table_name,
    active_bytes / (1024*1024) AS active_mb,
    time_travel_bytes / (1024*1024) AS time_travel_mb,
    failsafe_bytes / (1024*1024) AS failsafe_mb
FROM dev_ecommerce.information_schema.table_storage_metrics
WHERE table_name = 'CUSTOMERS';
-- DEV will show higher storage due to modifications


-- Demonstrate storage efficiency: Clone + modify still cheaper than full copy
-- Full copy = 100% storage for source + 100% for destination = 200% total
-- Zero-copy clone = 100% shared + ~10% divergence = 110% total


-- ============================================================================
-- SECTION 5: Historical Cloning (Time Travel)
-- ============================================================================
-- Clone objects from a specific point in time using Time Travel.
-- Useful for recovering from errors or analyzing historical state.
-- ============================================================================

USE DATABASE prod_ecommerce;
USE SCHEMA sales;

-- Make changes to production (simulate accidental modifications)
-- Store timestamp before changes
SET before_changes_timestamp = CURRENT_TIMESTAMP();

-- Wait 2 seconds to ensure timestamp difference
CALL SYSTEM$WAIT(2);

-- Simulate accidental deletions
DELETE FROM prod_ecommerce.sales.orders
WHERE order_status = 'Cancelled';

SELECT COUNT(*) FROM prod_ecommerce.sales.orders;
-- Reduced count (some orders deleted)

-- Simulate accidental updates
UPDATE prod_ecommerce.sales.customers
SET loyalty_tier = 'ERROR'
WHERE customer_id < 100;

SELECT COUNT(*) FROM prod_ecommerce.sales.customers WHERE loyalty_tier = 'ERROR';
-- Shows 100 affected records


-- RECOVERY: Clone from before changes using timestamp
CREATE OR REPLACE TABLE orders_before_accident
    CLONE prod_ecommerce.sales.orders
    AT(TIMESTAMP => $before_changes_timestamp);

-- Verify recovery
SELECT COUNT(*) FROM orders_before_accident;
-- Original count restored

SELECT DISTINCT order_status FROM orders_before_accident ORDER BY order_status;
-- Shows 'Cancelled' orders that were deleted


-- RECOVERY: Clone using offset (seconds ago)
CREATE OR REPLACE TABLE customers_5min_ago
    CLONE prod_ecommerce.sales.customers
    AT(OFFSET => -300);  -- 300 seconds = 5 minutes ago

SELECT COUNT(*) FROM customers_5min_ago WHERE loyalty_tier = 'ERROR';
-- Returns 0 (before the accidental update)


-- Clone entire database from 1 hour ago
CREATE OR REPLACE DATABASE prod_ecommerce_1hr_ago
    CLONE prod_ecommerce
    AT(OFFSET => -3600);  -- 3600 seconds = 1 hour

-- Verify historical clone
SELECT COUNT(*) FROM prod_ecommerce_1hr_ago.sales.customers
WHERE loyalty_tier = 'ERROR';
-- Returns 0 (before error)


-- Clone from specific timestamp string
CREATE OR REPLACE TABLE customers_at_timestamp
    CLONE prod_ecommerce.sales.customers
    AT(TIMESTAMP => '2026-03-09 10:00:00'::TIMESTAMP_NTZ);

-- Note: Timestamp must be within retention period (1-90 days depending on edition)


-- Use BEFORE statement for cloning from just before a specific statement
-- First, get the query ID of the problematic update
SELECT query_id, query_text, start_time
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE query_text LIKE '%UPDATE%customers%ERROR%'
ORDER BY start_time DESC
LIMIT 1;

-- Clone from before that specific query (example query_id)
-- CREATE OR REPLACE TABLE customers_before_error
--     CLONE prod_ecommerce.sales.customers
--     BEFORE(STATEMENT => '01a4c123-0001-2345-0000-000012345678');


-- Compare current state vs historical state
SELECT
    'Current' AS state,
    loyalty_tier,
    COUNT(*) AS customer_count
FROM prod_ecommerce.sales.customers
GROUP BY loyalty_tier
UNION ALL
SELECT
    'Historical (5 min ago)' AS state,
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers_5min_ago
GROUP BY loyalty_tier
ORDER BY state, loyalty_tier;


-- ============================================================================
-- SECTION 6: Clone Use Cases
-- ============================================================================
-- Real-world applications of zero-copy cloning for common scenarios.
-- ============================================================================

-- USE CASE 1: Development/Test Environments
-- Create isolated environment for each developer

CREATE OR REPLACE DATABASE dev_sarah_workspace
    CLONE prod_ecommerce
    COMMENT = 'Sarah''s dev environment';

CREATE OR REPLACE DATABASE dev_mike_workspace
    CLONE prod_ecommerce
    COMMENT = 'Mike''s dev environment';

-- Each developer has full production dataset without storage duplication
-- They can modify freely without affecting production or each other


-- USE CASE 2: Data Backups
-- Create daily snapshot backups

CREATE OR REPLACE DATABASE prod_ecommerce_backup_20260309
    CLONE prod_ecommerce
    COMMENT = 'Daily backup for 2026-03-09';

-- Automate with task (simplified example)
CREATE OR REPLACE TASK daily_backup_task
    WAREHOUSE = clone_demo_wh
    SCHEDULE = 'USING CRON 0 2 * * * UTC'  -- 2 AM daily
AS
    CREATE OR REPLACE DATABASE prod_ecommerce_backup_latest
        CLONE prod_ecommerce;

-- ALTER TASK daily_backup_task RESUME;


-- USE CASE 3: A/B Testing
-- Create separate environments to test different data transformations

CREATE OR REPLACE DATABASE prod_ecommerce_scenario_a
    CLONE prod_ecommerce
    COMMENT = 'Scenario A: Aggressive discounting';

CREATE OR REPLACE DATABASE prod_ecommerce_scenario_b
    CLONE prod_ecommerce
    COMMENT = 'Scenario B: Premium pricing';

-- Apply different business logic to each scenario
USE DATABASE prod_ecommerce_scenario_a;
UPDATE sales.orders
SET discount_amount = discount_amount * 1.5
WHERE order_status = 'Pending';

USE DATABASE prod_ecommerce_scenario_b;
UPDATE sales.orders
SET total_amount = total_amount * 1.1,
    discount_amount = 0
WHERE order_status = 'Pending';

-- Compare outcomes
SELECT
    'Scenario A' AS scenario,
    SUM(total_amount) AS total_revenue,
    SUM(discount_amount) AS total_discounts
FROM prod_ecommerce_scenario_a.sales.orders
UNION ALL
SELECT
    'Scenario B' AS scenario,
    SUM(total_amount) AS total_revenue,
    SUM(discount_amount) AS total_discounts
FROM prod_ecommerce_scenario_b.sales.orders;


-- USE CASE 4: Data Analysis Sandboxes
-- Create temporary environments for data scientists

CREATE OR REPLACE DATABASE analytics_sandbox_ds123
    CLONE prod_ecommerce
    COMMENT = 'Temporary sandbox for ML model development';

-- Data scientist can experiment freely
USE DATABASE analytics_sandbox_ds123;
USE SCHEMA sales;

-- Create derived features
ALTER TABLE customers ADD COLUMN rfm_score NUMBER;

UPDATE customers
SET rfm_score = UNIFORM(1, 100, RANDOM());

-- When done, simply drop sandbox
-- DROP DATABASE analytics_sandbox_ds123;


-- USE CASE 5: QA/Staging Environment
-- Clone production to staging before each release

CREATE OR REPLACE DATABASE staging_ecommerce_v2
    CLONE prod_ecommerce
    COMMENT = 'Staging for v2.0 release';

-- QA team tests new features on production-like data
-- When release is approved, promote staging to production


-- USE CASE 6: Compliance and Audit
-- Create point-in-time snapshots for regulatory compliance

CREATE OR REPLACE DATABASE prod_ecommerce_eoy_2025
    CLONE prod_ecommerce
    AT(TIMESTAMP => '2025-12-31 23:59:59'::TIMESTAMP_NTZ)
    COMMENT = 'End of year 2025 snapshot for audit';

-- Auditors can query historical state without affecting production


-- USE CASE 7: Disaster Recovery Testing
-- Test recovery procedures without disrupting production

CREATE OR REPLACE DATABASE dr_test_ecommerce
    CLONE prod_ecommerce
    COMMENT = 'Disaster recovery test environment';

-- Simulate disaster scenario
USE DATABASE dr_test_ecommerce;
DROP TABLE sales.orders;  -- Simulate data loss

-- Test recovery procedure
CREATE OR REPLACE TABLE sales.orders
    CLONE prod_ecommerce.sales.orders;

-- Verify recovery successful
SELECT COUNT(*) FROM sales.orders;
-- Expected: 50000 (recovered)


-- ============================================================================
-- SECTION 7: Cost Tracking for Clones
-- ============================================================================
-- Monitor storage costs as clones diverge from source objects.
-- ============================================================================

-- Query table storage metrics for all ecommerce databases
SELECT
    table_catalog AS database_name,
    table_schema AS schema_name,
    table_name,
    active_bytes / (1024*1024*1024) AS active_gb,
    time_travel_bytes / (1024*1024*1024) AS time_travel_gb,
    failsafe_bytes / (1024*1024*1024) AS failsafe_gb,
    (active_bytes + time_travel_bytes + failsafe_bytes) / (1024*1024*1024) AS total_gb
FROM snowflake.information_schema.table_storage_metrics
WHERE table_catalog LIKE '%ECOMMERCE'
  AND table_schema = 'SALES'
ORDER BY table_catalog, table_name;


-- Calculate storage costs ($40 per TB-month on-demand)
WITH storage_summary AS (
    SELECT
        table_catalog AS database_name,
        SUM(active_bytes) AS total_active_bytes,
        SUM(time_travel_bytes) AS total_time_travel_bytes,
        SUM(failsafe_bytes) AS total_failsafe_bytes
    FROM snowflake.information_schema.table_storage_metrics
    WHERE table_catalog LIKE '%ECOMMERCE'
    GROUP BY table_catalog
)
SELECT
    database_name,
    total_active_bytes / (1024*1024*1024) AS active_gb,
    total_time_travel_bytes / (1024*1024*1024) AS time_travel_gb,
    total_failsafe_bytes / (1024*1024*1024) AS failsafe_gb,
    (total_active_bytes + total_time_travel_bytes + total_failsafe_bytes) / (1024*1024*1024) AS total_gb,
    ROUND(((total_active_bytes + time_travel_bytes + failsafe_bytes) / (1024*1024*1024*1024)) * 40, 2) AS estimated_monthly_cost_usd
FROM storage_summary
ORDER BY total_gb DESC;

-- Expected insight: Multiple clones cost fraction of full copies


-- Track storage growth over time
SELECT
    DATE(usage_date) AS date,
    database_name,
    AVG(average_bytes) / (1024*1024*1024) AS avg_storage_gb
FROM snowflake.account_usage.database_storage_usage_history
WHERE database_name LIKE '%ECOMMERCE'
  AND usage_date >= DATEADD(DAY, -7, CURRENT_DATE())
GROUP BY DATE(usage_date), database_name
ORDER BY date DESC, database_name;


-- Identify clones with high storage divergence
WITH clone_storage AS (
    SELECT
        table_catalog AS database_name,
        table_name,
        active_bytes / (1024*1024) AS active_mb
    FROM snowflake.information_schema.table_storage_metrics
    WHERE table_catalog LIKE '%ECOMMERCE'
      AND table_schema = 'SALES'
)
SELECT
    c.database_name,
    c.table_name,
    c.active_mb AS clone_active_mb,
    p.active_mb AS prod_active_mb,
    c.active_mb - p.active_mb AS storage_divergence_mb,
    ROUND(((c.active_mb - p.active_mb) / NULLIF(p.active_mb, 0)) * 100, 2) AS divergence_pct
FROM clone_storage c
JOIN clone_storage p
    ON c.table_name = p.table_name
    AND p.database_name = 'PROD_ECOMMERCE'
WHERE c.database_name LIKE 'DEV%'
  AND c.active_mb > p.active_mb
ORDER BY storage_divergence_mb DESC;


-- Best practice: Drop unused clones to reclaim storage
-- Identify stale clones (no queries in last 7 days)
SELECT DISTINCT
    table_catalog AS database_name,
    'No recent queries - candidate for deletion' AS recommendation
FROM snowflake.information_schema.tables
WHERE table_catalog LIKE '%ECOMMERCE'
  AND table_catalog NOT IN (
      SELECT DISTINCT database_name
      FROM snowflake.account_usage.query_history
      WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
        AND database_name LIKE '%ECOMMERCE'
  )
ORDER BY database_name;


-- ============================================================================
-- CLEANUP: Remove Training Resources
-- ============================================================================
-- Uncomment to clean up all created databases and warehouses

/*
DROP DATABASE IF EXISTS dev_ecommerce;
DROP DATABASE IF EXISTS staging_ecommerce;
DROP DATABASE IF EXISTS test_ecommerce;
DROP DATABASE IF EXISTS dev_sarah_workspace;
DROP DATABASE IF EXISTS dev_mike_workspace;
DROP DATABASE IF EXISTS prod_ecommerce_backup_20260309;
DROP DATABASE IF EXISTS prod_ecommerce_backup_latest;
DROP DATABASE IF EXISTS prod_ecommerce_scenario_a;
DROP DATABASE IF EXISTS prod_ecommerce_scenario_b;
DROP DATABASE IF EXISTS analytics_sandbox_ds123;
DROP DATABASE IF EXISTS staging_ecommerce_v2;
DROP DATABASE IF EXISTS prod_ecommerce_eoy_2025;
DROP DATABASE IF EXISTS dr_test_ecommerce;
DROP DATABASE IF EXISTS prod_ecommerce_1hr_ago;
DROP DATABASE IF EXISTS prod_ecommerce;
DROP WAREHOUSE IF EXISTS clone_demo_wh;
DROP TASK IF EXISTS daily_backup_task;
*/


-- ============================================================================
-- KEY TAKEAWAYS
-- ============================================================================
-- 1. Zero-copy cloning creates instant database/schema/table copies regardless
--    of data size. 100GB database clones in < 1 second.
--
-- 2. Clones initially share storage with source. They only consume additional
--    storage when data diverges through INSERT/UPDATE/DELETE.
--
-- 3. Use CLONE for dev/test environments, reducing storage costs by 80-90%
--    compared to full copies.
--
-- 4. Historical cloning with AT(TIMESTAMP => ...) or AT(OFFSET => ...)
--    enables point-in-time recovery within Time Travel retention period.
--
-- 5. Common use cases:
--    - Dev/test environments (isolated workspaces)
--    - Data backups (daily snapshots)
--    - A/B testing (parallel scenarios)
--    - QA/staging (production-like testing)
--    - Compliance (historical snapshots)
--
-- 6. Monitor storage divergence using TABLE_STORAGE_METRICS to identify
--    clones consuming excessive storage.
--
-- 7. Drop unused clones to reclaim storage. Clones are independent - dropping
--    a clone doesn't affect source or other clones.
--
-- 8. Best practice: Automate clone creation/deletion based on usage patterns.
--    Create clones on-demand, drop when no longer needed.
-- ============================================================================
