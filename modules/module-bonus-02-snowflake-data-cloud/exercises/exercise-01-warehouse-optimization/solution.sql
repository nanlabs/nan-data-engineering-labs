-- ============================================================================
-- Exercise 01: Warehouse Optimization - SOLUTION
-- ============================================================================
--
-- This solution demonstrates best practices for warehouse configuration,
-- performance testing, and cost optimization in Snowflake.
-- ============================================================================

-- ============================================================================
-- SETUP: Create Database and Use Context
-- ============================================================================

CREATE DATABASE IF NOT EXISTS warehouse_optimization_db;
USE DATABASE warehouse_optimization_db;
CREATE SCHEMA IF NOT EXISTS performance_testing;
USE SCHEMA performance_testing;

-- ============================================================================
-- TASK 1: Create Warehouses with Different Sizes (20 points)
-- ============================================================================

-- Create X-Small warehouse for development and light workloads
CREATE OR REPLACE WAREHOUSE COMPUTE_WH_XSMALL
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60              -- Suspend after 1 minute
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Development warehouse for light workloads';

-- Create Medium warehouse for standard production workloads
CREATE OR REPLACE WAREHOUSE COMPUTE_WH_MEDIUM
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120             -- Suspend after 2 minutes
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Production warehouse for standard analytical queries';

-- Create Large warehouse for heavy analytical workloads
CREATE OR REPLACE WAREHOUSE COMPUTE_WH_LARGE
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 180             -- Suspend after 3 minutes
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Large warehouse for complex analytical workloads';

-- Verify warehouse creation
SHOW WAREHOUSES LIKE 'COMPUTE_WH_%';

-- Check warehouse configuration details
SELECT
    "name" as warehouse_name,
    "size" as warehouse_size,
    "auto_suspend" as auto_suspend_seconds,
    "auto_resume",
    "state",
    "comment"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "size";

-- ============================================================================
-- TASK 2: Setup Test Data for Performance Testing (15 points)
-- ============================================================================

-- Create fact table with 1 million sales transactions
CREATE OR REPLACE TABLE sales_fact AS
SELECT
    SEQ4() as transaction_id,
    UNIFORM(1, 100000, RANDOM()) as customer_id,
    UNIFORM(1, 10000, RANDOM()) as product_id,
    UNIFORM(1, 100, RANDOM()) as quantity,
    UNIFORM(10, 1000, RANDOM()) / 10.0 as unit_price,
    DATEADD(day, -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()) as transaction_date,
    UNIFORM(1, 50, RANDOM()) as store_id
FROM TABLE(GENERATOR(ROWCOUNT => 1000000));

-- Create dimension table with 100,000 customers
CREATE OR REPLACE TABLE customer_dimension AS
SELECT
    SEQ4() as customer_id,
    'Customer_' || SEQ4() as customer_name,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'North'
        WHEN 2 THEN 'South'
        WHEN 3 THEN 'East'
        ELSE 'West'
    END as region,
    CASE UNIFORM(1, 3, RANDOM())
        WHEN 1 THEN 'Gold'
        WHEN 2 THEN 'Silver'
        ELSE 'Bronze'
    END as tier,
    DATEADD(day, -UNIFORM(0, 3650, RANDOM()), CURRENT_DATE()) as signup_date
FROM TABLE(GENERATOR(ROWCOUNT => 100000));

-- Create product dimension
CREATE OR REPLACE TABLE product_dimension AS
SELECT
    SEQ4() as product_id,
    'Product_' || SEQ4() as product_name,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Electronics'
        WHEN 2 THEN 'Clothing'
        WHEN 3 THEN 'Food'
        WHEN 4 THEN 'Home'
        ELSE 'Sports'
    END as category,
    UNIFORM(100, 5000, RANDOM()) / 10.0 as standard_price
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- Verify data creation
SELECT 'sales_fact' as table_name, COUNT(*) as row_count FROM sales_fact
UNION ALL
SELECT 'customer_dimension', COUNT(*) FROM customer_dimension
UNION ALL
SELECT 'product_dimension', COUNT(*) FROM product_dimension;

-- ============================================================================
-- TASK 3: Performance Testing Across Warehouse Sizes (25 points)
-- ============================================================================

-- Create results table to track performance
CREATE OR REPLACE TABLE performance_results (
    test_id INT AUTOINCREMENT,
    warehouse_size VARCHAR(20),
    query_description VARCHAR(200),
    execution_time_ms NUMBER,
    credits_used FLOAT,
    test_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ===== TEST 1: X-SMALL WAREHOUSE =====
USE WAREHOUSE COMPUTE_WH_XSMALL;

-- Complex analytical query with joins and aggregations
-- Note: Record start time
SET start_time_xsmall = (SELECT CURRENT_TIMESTAMP());

SELECT
    c.region,
    p.category,
    DATE_TRUNC('month', s.transaction_date) as month,
    COUNT(DISTINCT s.transaction_id) as transaction_count,
    COUNT(DISTINCT s.customer_id) as unique_customers,
    SUM(s.quantity * s.unit_price) as total_revenue,
    AVG(s.quantity * s.unit_price) as avg_transaction_value,
    STDDEV(s.quantity * s.unit_price) as revenue_stddev
FROM sales_fact s
JOIN customer_dimension c ON s.customer_id = c.customer_id
JOIN product_dimension p ON s.product_id = p.product_id
WHERE s.transaction_date >= DATEADD(day, -180, CURRENT_DATE())
GROUP BY c.region, p.category, DATE_TRUNC('month', s.transaction_date)
HAVING SUM(s.quantity * s.unit_price) > 1000
ORDER BY total_revenue DESC
LIMIT 100;

-- Record execution time
SET end_time_xsmall = (SELECT CURRENT_TIMESTAMP());
SET duration_xsmall = (SELECT DATEDIFF(millisecond, $start_time_xsmall, $end_time_xsmall));

-- Insert performance results
INSERT INTO performance_results (warehouse_size, query_description, execution_time_ms)
VALUES ('X-SMALL', 'Complex analytical query with joins and aggregations', $duration_xsmall);

-- ===== TEST 2: MEDIUM WAREHOUSE =====
USE WAREHOUSE COMPUTE_WH_MEDIUM;

SET start_time_medium = (SELECT CURRENT_TIMESTAMP());

SELECT
    c.region,
    p.category,
    DATE_TRUNC('month', s.transaction_date) as month,
    COUNT(DISTINCT s.transaction_id) as transaction_count,
    COUNT(DISTINCT s.customer_id) as unique_customers,
    SUM(s.quantity * s.unit_price) as total_revenue,
    AVG(s.quantity * s.unit_price) as avg_transaction_value,
    STDDEV(s.quantity * s.unit_price) as revenue_stddev
FROM sales_fact s
JOIN customer_dimension c ON s.customer_id = c.customer_id
JOIN product_dimension p ON s.product_id = p.product_id
WHERE s.transaction_date >= DATEADD(day, -180, CURRENT_DATE())
GROUP BY c.region, p.category, DATE_TRUNC('month', s.transaction_date)
HAVING SUM(s.quantity * s.unit_price) > 1000
ORDER BY total_revenue DESC
LIMIT 100;

SET end_time_medium = (SELECT CURRENT_TIMESTAMP());
SET duration_medium = (SELECT DATEDIFF(millisecond, $start_time_medium, $end_time_medium));

INSERT INTO performance_results (warehouse_size, query_description, execution_time_ms)
VALUES ('MEDIUM', 'Complex analytical query with joins and aggregations', $duration_medium);

-- ===== TEST 3: LARGE WAREHOUSE =====
USE WAREHOUSE COMPUTE_WH_LARGE;

SET start_time_large = (SELECT CURRENT_TIMESTAMP());

SELECT
    c.region,
    p.category,
    DATE_TRUNC('month', s.transaction_date) as month,
    COUNT(DISTINCT s.transaction_id) as transaction_count,
    COUNT(DISTINCT s.customer_id) as unique_customers,
    SUM(s.quantity * s.unit_price) as total_revenue,
    AVG(s.quantity * s.unit_price) as avg_transaction_value,
    STDDEV(s.quantity * s.unit_price) as revenue_stddev
FROM sales_fact s
JOIN customer_dimension c ON s.customer_id = c.customer_id
JOIN product_dimension p ON s.product_id = p.product_id
WHERE s.transaction_date >= DATEADD(day, -180, CURRENT_DATE())
GROUP BY c.region, p.category, DATE_TRUNC('month', s.transaction_date)
HAVING SUM(s.quantity * s.unit_price) > 1000
ORDER BY total_revenue DESC
LIMIT 100;

SET end_time_large = (SELECT CURRENT_TIMESTAMP());
SET duration_large = (SELECT DATEDIFF(millisecond, $start_time_large, $end_time_large));

INSERT INTO performance_results (warehouse_size, query_description, execution_time_ms)
VALUES ('LARGE', 'Complex analytical query with joins and aggregations', $duration_large);

-- Display performance comparison
SELECT
    warehouse_size,
    execution_time_ms,
    execution_time_ms / 1000.0 as execution_time_seconds,
    ROUND(execution_time_ms / MIN(execution_time_ms) OVER (), 2) as relative_performance,
    CASE warehouse_size
        WHEN 'X-SMALL' THEN 1
        WHEN 'MEDIUM' THEN 4
        WHEN 'LARGE' THEN 8
    END as credits_per_hour,
    test_timestamp
FROM performance_results
ORDER BY test_id DESC
LIMIT 3;

-- ============================================================================
-- TASK 4: Configure Auto-Suspend and Auto-Resume (15 points)
-- ============================================================================

-- Configure aggressive auto-suspend for development
ALTER WAREHOUSE COMPUTE_WH_XSMALL SET
    AUTO_SUSPEND = 60              -- 1 minute for dev/testing
    AUTO_RESUME = TRUE;

-- Configure moderate auto-suspend for production
ALTER WAREHOUSE COMPUTE_WH_MEDIUM SET
    AUTO_SUSPEND = 300             -- 5 minutes for production
    AUTO_RESUME = TRUE;

-- Configure conservative auto-suspend for large warehouse
ALTER WAREHOUSE COMPUTE_WH_LARGE SET
    AUTO_SUSPEND = 600             -- 10 minutes for expensive warehouse
    AUTO_RESUME = TRUE;

-- Test auto-suspend behavior
USE WAREHOUSE COMPUTE_WH_XSMALL;
SELECT 'Testing auto-suspend - warehouse should suspend after 60 seconds of inactivity';

-- Check warehouse status
SHOW WAREHOUSES LIKE 'COMPUTE_WH_%';

SELECT
    "name" as warehouse_name,
    "state" as current_state,
    "auto_suspend" / 60.0 as auto_suspend_minutes,
    "auto_resume"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "auto_suspend";

-- ============================================================================
-- TASK 5: Implement Multi-Cluster Warehouse (15 points)
-- ============================================================================

-- Create multi-cluster warehouse for concurrent workloads
CREATE OR REPLACE WAREHOUSE COMPUTE_WH_MULTI
    WAREHOUSE_SIZE = 'MEDIUM'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    SCALING_POLICY = 'STANDARD'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Multi-cluster warehouse for concurrent user queries';

-- Alternative: Economy mode for less aggressive scaling
ALTER WAREHOUSE COMPUTE_WH_MULTI SET
    SCALING_POLICY = 'ECONOMY';

-- Verify multi-cluster configuration
SHOW WAREHOUSES LIKE 'COMPUTE_WH_MULTI';

SELECT
    "name" as warehouse_name,
    "size" as warehouse_size,
    "min_cluster_count",
    "max_cluster_count",
    "scaling_policy",
    "comment"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

-- ============================================================================
-- TASK 6: Monitor Credit Usage and Costs (10 points)
-- ============================================================================

-- Query warehouse metering history for the last 7 days
SELECT
    warehouse_name,
    DATE_TRUNC('day', start_time) as usage_date,
    SUM(credits_used) as total_credits,
    COUNT(DISTINCT start_time) as query_count,
    AVG(credits_used) as avg_credits_per_query,
    MAX(credits_used) as max_credits_single_query
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
    AND warehouse_name LIKE 'COMPUTE_WH_%'
GROUP BY warehouse_name, DATE_TRUNC('day', start_time)
ORDER BY usage_date DESC, total_credits DESC;

-- Calculate estimated costs (assuming $2 per credit for Enterprise Edition)
SELECT
    warehouse_name,
    SUM(credits_used) as total_credits_7days,
    SUM(credits_used) * 2 as estimated_cost_usd,
    SUM(credits_used) * 2 * 52 / 7 as estimated_annual_cost_usd,
    COUNT(*) as active_hours
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
    AND warehouse_name LIKE 'COMPUTE_WH_%'
GROUP BY warehouse_name
ORDER BY total_credits_7days DESC;

-- Identify top cost drivers
SELECT
    warehouse_name,
    DATE_TRUNC('hour', start_time) as usage_hour,
    SUM(credits_used) as hourly_credits,
    SUM(credits_used) * 2 as hourly_cost_usd,
    COUNT(*) as queries_in_hour
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
    AND warehouse_name LIKE 'COMPUTE_WH_%'
GROUP BY warehouse_name, DATE_TRUNC('hour', start_time)
HAVING SUM(credits_used) > 1
ORDER BY hourly_credits DESC
LIMIT 20;

-- Warehouse utilization analysis
SELECT
    warehouse_name,
    COUNT(*) as total_queries,
    SUM(credits_used) as total_credits,
    AVG(credits_used) as avg_credits_per_query,
    MIN(start_time) as first_usage,
    MAX(start_time) as last_usage,
    DATEDIFF(hour, MIN(start_time), MAX(start_time)) as active_span_hours
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
    AND warehouse_name LIKE 'COMPUTE_WH_%'
GROUP BY warehouse_name
ORDER BY total_credits DESC;

-- ============================================================================
-- OPTIMIZATION STRATEGIES DOCUMENTATION
-- ============================================================================

/*
OPTIMIZATION STRATEGY 1: Right-Size Warehouses Based on Workload
Expected Savings: 30-40% reduction in compute costs
Implementation:
- Profile query performance across different warehouse sizes
- Use X-Small for development, light queries, and data exploration
- Use Medium for standard production analytical queries
- Use Large only for truly heavy workloads (large data scans, complex joins)
- Monitor query performance and adjust sizes accordingly
*/

/*
OPTIMIZATION STRATEGY 2: Aggressive Auto-Suspend Configuration
Expected Savings: 20-30% reduction in idle time costs
Implementation:
- Development warehouses: 60-second auto-suspend
- Production warehouses: 300-second (5-minute) auto-suspend
- Balance between cost savings and resume latency
- Monitor suspension patterns to optimize timing
- Consider workload patterns (batch vs. interactive)
*/

/*
OPTIMIZATION STRATEGY 3: Implement Query Result Caching
Expected Savings: 10-15% reduction through cache hits
Implementation:
- Educate users about 24-hour result cache
- Encourage rerunning identical queries within cache window
- Use result_scan() to access previous query results
- Structure dashboards to leverage cached results
- Monitor cache hit rates in query history
*/

/*
OPTIMIZATION STRATEGY 4: Multi-Cluster Warehouses with Economy Mode
Expected Savings: 15-25% for concurrent workload scenarios
Implementation:
- Use multi-cluster for concurrent user workloads
- Configure Economy scaling policy for cost-conscious scaling
- Set appropriate min (1) and max (3-5) cluster counts
- Monitor cluster scaling patterns
- Adjust scaling parameters based on actual concurrency needs
*/

/*
OPTIMIZATION STRATEGY 5: Workload Segregation and Scheduling
Expected Savings: 20-30% through better resource allocation
Implementation:
- Separate warehouses for ETL, reporting, and ad-hoc queries
- Schedule heavy batch jobs during off-peak hours
- Use smaller warehouses for scheduled, predictable workloads
- Implement resource monitors with credit quotas
- Create warehouse usage policies and governance
*/

-- ============================================================================
-- CLEANUP (Optional)
-- ============================================================================

-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_XSMALL;
-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_MEDIUM;
-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_LARGE;
-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_MULTI;
-- DROP DATABASE IF EXISTS warehouse_optimization_db;

-- ============================================================================
-- END OF SOLUTION
-- ============================================================================
