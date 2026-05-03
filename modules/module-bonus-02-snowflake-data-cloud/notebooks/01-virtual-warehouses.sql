-- ============================================================================
-- Module Bonus 02: Snowflake Data Cloud
-- Notebook 01: Virtual Warehouses
-- ============================================================================
-- Description: Master Snowflake's compute layer with virtual warehouses.
--              Learn sizing, auto-suspend/resume, multi-cluster warehouses,
--              and credit optimization strategies.
--
-- Prerequisites:
--   - Snowflake account with ACCOUNTADMIN role
--   - Basic understanding of SQL
--   - Access to ACCOUNT_USAGE schema
--
-- Estimated Time: 60 minutes
-- ============================================================================

-- ============================================================================
-- SETUP: Initialize Environment
-- ============================================================================

-- Set the context for our training session
USE ROLE ACCOUNTADMIN;

-- Create a dedicated database for warehouse experiments
CREATE DATABASE IF NOT EXISTS warehouse_training;
USE DATABASE warehouse_training;

-- Create a schema for our exercises
CREATE SCHEMA IF NOT EXISTS compute_lab;
USE SCHEMA compute_lab;

-- Create a sample table for performance testing
CREATE OR REPLACE TABLE sales_data (
    sale_id NUMBER,
    customer_id NUMBER,
    product_name VARCHAR(100),
    category VARCHAR(50),
    sale_amount DECIMAL(10,2),
    sale_date DATE,
    region VARCHAR(50)
);

-- Generate 100,000 sample records for realistic testing
INSERT INTO sales_data
SELECT
    SEQ4() AS sale_id,
    UNIFORM(1, 10000, RANDOM()) AS customer_id,
    CONCAT('Product_', UNIFORM(1, 1000, RANDOM())) AS product_name,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Electronics'
        WHEN 2 THEN 'Clothing'
        WHEN 3 THEN 'Food'
        WHEN 4 THEN 'Books'
        ELSE 'Home & Garden'
    END AS category,
    UNIFORM(10, 1000, RANDOM()) AS sale_amount,
    DATEADD(DAY, -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()) AS sale_date,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'North'
        WHEN 2 THEN 'South'
        WHEN 3 THEN 'East'
        ELSE 'West'
    END AS region
FROM TABLE(GENERATOR(ROWCOUNT => 100000));

-- Verify data loaded successfully
SELECT COUNT(*) AS total_records FROM sales_data;
-- Expected Output: 100000

SELECT * FROM sales_data LIMIT 10;
-- Sample Output:
-- SALE_ID | CUSTOMER_ID | PRODUCT_NAME | CATEGORY    | SALE_AMOUNT | SALE_DATE  | REGION
-- --------+-------------+--------------+-------------+-------------+------------+--------
-- 0       | 5432        | Product_543  | Electronics | 543.00      | 2025-08-15 | North
-- 1       | 8901        | Product_234  | Clothing    | 123.50      | 2025-11-22 | West
-- ...


-- ============================================================================
-- SECTION 1: Create Virtual Warehouses
-- ============================================================================
-- Virtual warehouses are independent compute clusters that execute queries
-- and DML operations. They can be created, resized, suspended, and resumed
-- independently without affecting other warehouses or stored data.
-- ============================================================================

-- Create an X-Small warehouse for development and testing
-- X-Small: 1 server, ~8 credits per hour
CREATE OR REPLACE WAREHOUSE dev_xs_wh
WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60           -- Suspend after 1 minute of inactivity
    AUTO_RESUME = TRUE          -- Automatically resume when queries submitted
    INITIALLY_SUSPENDED = TRUE  -- Start in suspended state
    COMMENT = 'X-Small warehouse for development and testing';

-- Verify warehouse creation
SHOW WAREHOUSES LIKE 'dev_xs_wh';
-- Output shows: name, state, type, size, min_cluster_count, max_cluster_count, etc.

-- Create a Small warehouse for regular analytical workloads
-- Small: 2 servers, ~16 credits per hour
CREATE OR REPLACE WAREHOUSE analytics_small_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300          -- Suspend after 5 minutes of inactivity
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Small warehouse for regular analytics';

-- Create a Medium warehouse for heavy analytical workloads
-- Medium: 4 servers, ~32 credits per hour
CREATE OR REPLACE WAREHOUSE analytics_medium_wh
WITH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 600          -- Suspend after 10 minutes of inactivity
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Medium warehouse for heavy analytical queries';

-- Create a Large warehouse for data loading and transformation
-- Large: 8 servers, ~64 credits per hour
CREATE OR REPLACE WAREHOUSE etl_large_wh
WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 120          -- Suspend after 2 minutes of inactivity
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Large warehouse for ETL operations';

-- List all warehouses we created
SHOW WAREHOUSES;

-- Get detailed information about a specific warehouse
DESCRIBE WAREHOUSE dev_xs_wh;
-- Returns configuration details including size, auto_suspend, auto_resume, etc.

-- Query warehouse configuration from metadata
SELECT
    name,
    state,
    type,
    size,
    auto_suspend,
    auto_resume,
    comment
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSES)
WHERE name IN ('DEV_XS_WH', 'ANALYTICS_SMALL_WH', 'ANALYTICS_MEDIUM_WH', 'ETL_LARGE_WH')
ORDER BY name;


-- ============================================================================
-- SECTION 2: Warehouse Sizing Comparison
-- ============================================================================
-- Compare query performance across different warehouse sizes to understand
-- when to scale up vs scale out. Larger warehouses complete queries faster
-- but cost more per hour.
-- ============================================================================

-- Test Query 1: Aggregation with grouping
-- Run on X-Small warehouse
USE WAREHOUSE dev_xs_wh;

-- Record start time
SELECT CURRENT_TIMESTAMP() AS query_start_time;

-- Execute aggregation query
SELECT
    category,
    region,
    COUNT(*) AS total_sales,
    SUM(sale_amount) AS total_revenue,
    AVG(sale_amount) AS avg_sale_amount,
    MIN(sale_amount) AS min_sale,
    MAX(sale_amount) AS max_sale
FROM sales_data
GROUP BY category, region
ORDER BY total_revenue DESC;

-- Expected Output (20 rows):
-- CATEGORY    | REGION | TOTAL_SALES | TOTAL_REVENUE | AVG_SALE_AMOUNT | MIN_SALE | MAX_SALE
-- ------------+--------+-------------+---------------+-----------------+----------+----------
-- Electronics | West   | 5123        | 2,543,234.50  | 496.32          | 10.00    | 999.00
-- ...

-- Record end time
SELECT CURRENT_TIMESTAMP() AS query_end_time;

-- Query the QUERY_HISTORY to get execution time
SELECT
    query_id,
    query_text,
    warehouse_name,
    warehouse_size,
    execution_status,
    total_elapsed_time / 1000 AS execution_seconds,
    bytes_scanned,
    bytes_written
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name = 'DEV_XS_WH'
  AND query_text LIKE '%FROM sales_data%'
ORDER BY start_time DESC
LIMIT 1;
-- Sample Output: execution_seconds = 2.5 seconds


-- Now run the SAME query on Medium warehouse
USE WAREHOUSE analytics_medium_wh;

SELECT CURRENT_TIMESTAMP() AS query_start_time;

SELECT
    category,
    region,
    COUNT(*) AS total_sales,
    SUM(sale_amount) AS total_revenue,
    AVG(sale_amount) AS avg_sale_amount,
    MIN(sale_amount) AS min_sale,
    MAX(sale_amount) AS max_sale
FROM sales_data
GROUP BY category, region
ORDER BY total_revenue DESC;

SELECT CURRENT_TIMESTAMP() AS query_end_time;

-- Check execution time on Medium warehouse
SELECT
    query_id,
    query_text,
    warehouse_name,
    warehouse_size,
    execution_status,
    total_elapsed_time / 1000 AS execution_seconds,
    bytes_scanned,
    bytes_written
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name = 'ANALYTICS_MEDIUM_WH'
  AND query_text LIKE '%FROM sales_data%'
ORDER BY start_time DESC
LIMIT 1;
-- Sample Output: execution_seconds = 0.8 seconds (3x faster!)


-- Test Query 2: Complex join and window functions
USE WAREHOUSE dev_xs_wh;

WITH customer_stats AS (
    SELECT
        customer_id,
        COUNT(*) AS purchase_count,
        SUM(sale_amount) AS total_spent,
        AVG(sale_amount) AS avg_purchase,
        MIN(sale_date) AS first_purchase,
        MAX(sale_date) AS last_purchase
    FROM sales_data
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        purchase_count,
        total_spent,
        avg_purchase,
        ROW_NUMBER() OVER (ORDER BY total_spent DESC) AS rank,
        PERCENT_RANK() OVER (ORDER BY total_spent) AS percentile
    FROM customer_stats
)
SELECT
    customer_id,
    purchase_count,
    total_spent,
    avg_purchase,
    rank,
    ROUND(percentile * 100, 2) AS percentile_rank
FROM ranked_customers
WHERE rank <= 100
ORDER BY rank;

-- Time this query on X-Small
SELECT
    warehouse_name,
    warehouse_size,
    total_elapsed_time / 1000 AS execution_seconds
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name = 'DEV_XS_WH'
  AND query_text LIKE '%ranked_customers%'
ORDER BY start_time DESC
LIMIT 1;
-- Sample Output: 3.5 seconds


-- Run same complex query on Medium warehouse
USE WAREHOUSE analytics_medium_wh;

WITH customer_stats AS (
    SELECT
        customer_id,
        COUNT(*) AS purchase_count,
        SUM(sale_amount) AS total_spent,
        AVG(sale_amount) AS avg_purchase,
        MIN(sale_date) AS first_purchase,
        MAX(sale_date) AS last_purchase
    FROM sales_data
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        purchase_count,
        total_spent,
        avg_purchase,
        ROW_NUMBER() OVER (ORDER BY total_spent DESC) AS rank,
        PERCENT_RANK() OVER (ORDER BY total_spent) AS percentile
    FROM customer_stats
)
SELECT
    customer_id,
    purchase_count,
    total_spent,
    avg_purchase,
    rank,
    ROUND(percentile * 100, 2) AS percentile_rank
FROM ranked_customers
WHERE rank <= 100
ORDER BY rank;

-- Time this query on Medium
SELECT
    warehouse_name,
    warehouse_size,
    total_elapsed_time / 1000 AS execution_seconds
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name = 'ANALYTICS_MEDIUM_WH'
  AND query_text LIKE '%ranked_customers%'
ORDER BY start_time DESC
LIMIT 1;
-- Sample Output: 1.2 seconds (nearly 3x faster)


-- Compare performance across warehouse sizes
SELECT
    warehouse_name,
    warehouse_size,
    COUNT(*) AS query_count,
    AVG(total_elapsed_time / 1000) AS avg_execution_seconds,
    MIN(total_elapsed_time / 1000) AS min_execution_seconds,
    MAX(total_elapsed_time / 1000) AS max_execution_seconds
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name IN ('DEV_XS_WH', 'ANALYTICS_MEDIUM_WH')
  AND execution_status = 'SUCCESS'
  AND start_time >= DATEADD(MINUTE, -10, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, warehouse_size
ORDER BY warehouse_name;


-- ============================================================================
-- SECTION 3: Auto-Suspend and Auto-Resume
-- ============================================================================
-- Auto-suspend automatically suspends warehouses after inactivity to save credits.
-- Auto-resume automatically starts suspended warehouses when queries are submitted.
-- Mastering these features is critical for cost optimization.
-- ============================================================================

-- Check current warehouse state
SHOW WAREHOUSES LIKE 'dev_xs_wh';
-- STATE column shows: STARTED, SUSPENDED, RESUMING, or SUSPENDING

-- Manually suspend a warehouse
ALTER WAREHOUSE dev_xs_wh SUSPEND;

-- Verify warehouse is suspended
SHOW WAREHOUSES LIKE 'dev_xs_wh';
-- STATE should show: SUSPENDED

-- Try to run a query on suspended warehouse (will auto-resume if AUTO_RESUME = TRUE)
USE WAREHOUSE dev_xs_wh;
SELECT COUNT(*) FROM sales_data;
-- The warehouse automatically resumes, query executes successfully
-- Expected Output: 100000

-- Check warehouse state again (should be STARTED)
SHOW WAREHOUSES LIKE 'dev_xs_wh';

-- Manually resume a warehouse (if suspended)
ALTER WAREHOUSE analytics_small_wh RESUME;

-- Configure auto-suspend timeout
-- Shorter timeout = more cost savings but potential query startup delays
ALTER WAREHOUSE dev_xs_wh SET AUTO_SUSPEND = 30;  -- 30 seconds

-- Configure longer auto-suspend for frequently used warehouse
ALTER WAREHOUSE analytics_medium_wh SET AUTO_SUSPEND = 600;  -- 10 minutes

-- Disable auto-suspend (not recommended - warehouse stays running and consuming credits)
-- ALTER WAREHOUSE etl_large_wh SET AUTO_SUSPEND = NULL;

-- Enable/disable auto-resume
ALTER WAREHOUSE dev_xs_wh SET AUTO_RESUME = TRUE;

-- View warehouse configuration
SELECT
    name,
    state,
    size,
    auto_suspend,
    auto_resume,
    CASE
        WHEN state = 'SUSPENDED' THEN 'Not consuming credits'
        WHEN state = 'STARTED' THEN 'Consuming credits'
        ELSE state
    END AS credit_status
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSES)
WHERE name LIKE '%_wh'
ORDER BY name;


-- Monitor warehouse activity to optimize auto-suspend settings
-- If warehouse frequently suspends/resumes, increase AUTO_SUSPEND timeout
SELECT
    warehouse_name,
    DATE_TRUNC('HOUR', start_time) AS hour,
    COUNT(*) AS query_count,
    SUM(CASE WHEN execution_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_queries,
    AVG(total_elapsed_time / 1000) AS avg_execution_seconds
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name = 'DEV_XS_WH'
  AND start_time >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, DATE_TRUNC('HOUR', start_time)
ORDER BY hour DESC;


-- Best practice: Set AUTO_SUSPEND based on usage patterns
-- Development/Testing: 30-60 seconds (infrequent use)
-- Regular Analytics: 5-10 minutes (moderate use)
-- Production ETL: 2-5 minutes (burst workloads)
-- Real-time Dashboards: 10-20 minutes (frequent queries)


-- ============================================================================
-- SECTION 4: Multi-Cluster Warehouses
-- ============================================================================
-- Multi-cluster warehouses automatically scale out (add clusters) to handle
-- concurrent query load. Enterprise Edition feature for high concurrency workloads.
-- ============================================================================

-- Create a multi-cluster X-Small warehouse
-- Scales from 1 to 3 clusters based on query load
CREATE OR REPLACE WAREHOUSE multi_xs_wh
WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    SCALING_POLICY = 'STANDARD'  -- Balance between performance and cost
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Multi-cluster warehouse for concurrent workloads';

-- Verify multi-cluster configuration
SHOW WAREHOUSES LIKE 'multi_xs_wh';
-- Shows: min_cluster_count = 1, max_cluster_count = 3

DESCRIBE WAREHOUSE multi_xs_wh;


-- Scaling policies explained:
-- STANDARD: Balances cost and performance, adds clusters when needed
-- ECONOMY: More conservative, waits longer before adding clusters (saves cost)

-- Create warehouse with ECONOMY scaling for cost savings
CREATE OR REPLACE WAREHOUSE multi_economy_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 4
    SCALING_POLICY = 'ECONOMY'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Economy scaling for cost-sensitive concurrent workloads';


-- Create warehouse with STANDARD scaling for performance
CREATE OR REPLACE WAREHOUSE multi_standard_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    MIN_CLUSTER_COUNT = 2
    MAX_CLUSTER_COUNT = 5
    SCALING_POLICY = 'STANDARD'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Standard scaling for performance-critical workloads';


-- Modify existing warehouse to use multi-cluster
ALTER WAREHOUSE analytics_small_wh SET
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 2
    SCALING_POLICY = 'ECONOMY';


-- Query to see cluster activity (requires running queries to see scaling)
SELECT
    warehouse_name,
    DATE_TRUNC('MINUTE', start_time) AS minute,
    AVG(cluster_number) AS avg_clusters,
    MAX(cluster_number) AS max_clusters,
    COUNT(*) AS query_count
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE warehouse_name = 'MULTI_XS_WH'
  AND start_time >= DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, DATE_TRUNC('MINUTE', start_time)
ORDER BY minute DESC;


-- When to use multi-cluster:
-- 1. High concurrency (many users running queries simultaneously)
-- 2. Unpredictable query load (bursts of activity)
-- 3. Need consistent query performance under varying load
-- 4. Cost of scaling out < cost of slow queries

-- When NOT to use multi-cluster:
-- 1. Single user or low concurrency
-- 2. Predictable, steady workload
-- 3. Large single queries (scale up instead)
-- 4. Development/testing environments


-- ============================================================================
-- SECTION 5: Monitor Credit Usage
-- ============================================================================
-- Track warehouse credit consumption to optimize costs and identify expensive
-- warehouses or queries. Use ACCOUNT_USAGE schema for historical analysis.
-- ============================================================================

-- Query warehouse credit usage (requires ACCOUNTADMIN role)
USE ROLE ACCOUNTADMIN;

-- View credit consumption by warehouse (last 7 days)
SELECT
    warehouse_name,
    SUM(credits_used) AS total_credits,
    SUM(credits_used_compute) AS compute_credits,
    SUM(credits_used_cloud_services) AS cloud_services_credits,
    COUNT(DISTINCT DATE(start_time)) AS active_days
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY total_credits DESC;

-- Expected Output:
-- WAREHOUSE_NAME       | TOTAL_CREDITS | COMPUTE_CREDITS | CLOUD_SERVICES_CREDITS | ACTIVE_DAYS
-- --------------------+---------------+-----------------+------------------------+-------------
-- ANALYTICS_MEDIUM_WH | 45.23         | 43.50           | 1.73                   | 5
-- ETL_LARGE_WH        | 32.17         | 31.00           | 1.17                   | 3
-- ...


-- Hourly credit consumption trend
SELECT
    warehouse_name,
    DATE_TRUNC('HOUR', start_time) AS hour,
    SUM(credits_used) AS credits_per_hour
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
  AND warehouse_name IN ('DEV_XS_WH', 'ANALYTICS_MEDIUM_WH')
GROUP BY warehouse_name, DATE_TRUNC('HOUR', start_time)
ORDER BY warehouse_name, hour DESC;


-- Calculate estimated monthly cost ($4 per credit on-demand pricing)
WITH warehouse_credits AS (
    SELECT
        warehouse_name,
        SUM(credits_used) AS total_credits_7days
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
    GROUP BY warehouse_name
)
SELECT
    warehouse_name,
    total_credits_7days,
    ROUND(total_credits_7days / 7 * 30, 2) AS estimated_monthly_credits,
    ROUND((total_credits_7days / 7 * 30) * 4, 2) AS estimated_monthly_cost_usd
FROM warehouse_credits
ORDER BY estimated_monthly_cost_usd DESC;

-- Sample Output:
-- WAREHOUSE_NAME       | TOTAL_CREDITS_7DAYS | ESTIMATED_MONTHLY_CREDITS | ESTIMATED_MONTHLY_COST_USD
-- --------------------+---------------------+---------------------------+---------------------------
-- ANALYTICS_MEDIUM_WH | 45.23               | 194.13                    | $776.52
-- ETL_LARGE_WH        | 32.17               | 138.16                    | $552.64
-- ...


-- Identify warehouses with high cloud services costs (should be < 10% of total)
SELECT
    warehouse_name,
    SUM(credits_used) AS total_credits,
    SUM(credits_used_cloud_services) AS cloud_services_credits,
    ROUND((SUM(credits_used_cloud_services) / NULLIF(SUM(credits_used), 0)) * 100, 2) AS cloud_services_pct
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
HAVING cloud_services_pct > 10
ORDER BY cloud_services_pct DESC;
-- If cloud services > 10%, optimize query patterns or increase warehouse size


-- Query execution cost analysis
SELECT
    warehouse_name,
    warehouse_size,
    COUNT(*) AS query_count,
    SUM(execution_time) / 1000 AS total_execution_seconds,
    SUM(credits_used_cloud_services) AS total_credits,
    AVG(credits_used_cloud_services) AS avg_credits_per_query
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
  AND execution_status = 'SUCCESS'
  AND warehouse_name IS NOT NULL
GROUP BY warehouse_name, warehouse_size
ORDER BY total_credits DESC;


-- Identify expensive queries (top 10 by credits)
SELECT
    query_id,
    user_name,
    warehouse_name,
    warehouse_size,
    query_type,
    total_elapsed_time / 1000 AS execution_seconds,
    credits_used_cloud_services AS credits_used,
    LEFT(query_text, 100) AS query_preview
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
  AND execution_status = 'SUCCESS'
ORDER BY credits_used_cloud_services DESC
LIMIT 10;


-- Warehouse utilization analysis
SELECT
    warehouse_name,
    DATE(start_time) AS date,
    COUNT(*) AS query_count,
    SUM(credits_used) AS credits,
    AVG(avg_running) AS avg_concurrent_queries,
    MAX(avg_running) AS max_concurrent_queries
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, DATE(start_time)
ORDER BY warehouse_name, date DESC;


-- Cost optimization opportunities
WITH warehouse_stats AS (
    SELECT
        warehouse_name,
        SUM(credits_used) AS total_credits,
        COUNT(DISTINCT DATE(start_time)) AS active_days,
        AVG(avg_running) AS avg_concurrency
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
    GROUP BY warehouse_name
)
SELECT
    warehouse_name,
    total_credits,
    active_days,
    ROUND(avg_concurrency, 2) AS avg_concurrency,
    CASE
        WHEN avg_concurrency < 0.3 THEN 'Consider reducing size or auto-suspend timeout'
        WHEN avg_concurrency > 0.8 THEN 'Consider increasing size or multi-cluster'
        ELSE 'Well-sized'
    END AS recommendation
FROM warehouse_stats
ORDER BY total_credits DESC;


-- ============================================================================
-- SECTION 6: Best Practices and Decision Framework
-- ============================================================================
-- Apply cost optimization strategies and sizing guidelines for various use cases.
-- ============================================================================

-- Decision Tree for Warehouse Sizing:
-- Use this query framework to determine optimal warehouse configuration

-- BEST PRACTICE 1: Right-size for workload type
-- Fast, simple queries (< 1 sec): X-Small or Small
-- Regular analytics (1-10 sec): Small or Medium
-- Complex analytics (10-60 sec): Medium or Large
-- ETL/batch processing: Large or X-Large


-- BEST PRACTICE 2: Scale up vs Scale out decision
CREATE OR REPLACE VIEW warehouse_sizing_guide AS
SELECT
    'Large single query' AS use_case,
    'Scale UP (larger warehouse)' AS recommendation,
    'Increase WAREHOUSE_SIZE' AS action,
    'Better performance for single query' AS benefit
UNION ALL
SELECT
    'Many concurrent queries',
    'Scale OUT (multi-cluster)',
    'Increase MAX_CLUSTER_COUNT',
    'Handle more concurrent users'
UNION ALL
SELECT
    'Slow aggregations',
    'Scale UP',
    'Increase WAREHOUSE_SIZE',
    'Faster query execution'
UNION ALL
SELECT
    'Queue wait times',
    'Scale OUT',
    'Enable multi-cluster',
    'Reduce query queuing'
UNION ALL
SELECT
    'Low utilization',
    'Scale DOWN',
    'Decrease WAREHOUSE_SIZE',
    'Reduce costs'
UNION ALL
SELECT
    'High cloud services %',
    'Scale UP or optimize queries',
    'Increase WAREHOUSE_SIZE or refactor SQL',
    'Reduce overhead costs';

SELECT * FROM warehouse_sizing_guide;


-- BEST PRACTICE 3: Auto-suspend configuration by use case
CREATE OR REPLACE VIEW auto_suspend_guide AS
SELECT
    'Development/Testing' AS use_case,
    'X-Small or Small' AS recommended_size,
    30 AS auto_suspend_seconds,
    'Infrequent use, maximize savings' AS rationale
UNION ALL
SELECT
    'Ad-hoc Analytics',
    'Small or Medium',
    300,
    'Moderate use, balance cost and UX'
UNION ALL
SELECT
    'Production Dashboards',
    'Small or Medium',
    600,
    'Frequent queries, minimize cold starts'
UNION ALL
SELECT
    'ETL/Batch Jobs',
    'Large or X-Large',
    120,
    'Burst workloads, quick shutdown'
UNION ALL
SELECT
    'Real-time Applications',
    'Medium',
    900,
    'Continuous load, stay warm';

SELECT * FROM auto_suspend_guide ORDER BY auto_suspend_seconds;


-- BEST PRACTICE 4: Cost optimization checklist
CREATE OR REPLACE VIEW cost_optimization_checklist AS
SELECT
    1 AS priority,
    'Enable AUTO_SUSPEND on all warehouses' AS action,
    'Prevent runaway costs from idle warehouses' AS impact,
    'High' AS cost_savings
UNION ALL
SELECT
    2,
    'Set AUTO_SUSPEND to appropriate timeout',
    'Balance cost savings with cold start delays',
    'High'
UNION ALL
SELECT
    3,
    'Right-size warehouses based on query patterns',
    'Avoid over-provisioning compute',
    'Medium to High'
UNION ALL
SELECT
    4,
    'Use ECONOMY scaling for multi-cluster',
    'Reduce unnecessary cluster scale-out',
    'Medium'
UNION ALL
SELECT
    5,
    'Monitor cloud services credit ratio',
    'Keep cloud services < 10% of total',
    'Low to Medium'
UNION ALL
SELECT
    6,
    'Consolidate workloads on fewer warehouses',
    'Better utilization, fewer idle resources',
    'Medium'
UNION ALL
SELECT
    7,
    'Separate workloads by SLA',
    'Critical queries get dedicated resources',
    'Performance improvement'
UNION ALL
SELECT
    8,
    'Use resource monitors for cost control',
    'Set spending limits and alerts',
    'Prevent overruns';

SELECT * FROM cost_optimization_checklist ORDER BY priority;


-- BEST PRACTICE 5: Monitoring query for warehouse health
CREATE OR REPLACE VIEW warehouse_health_dashboard AS
SELECT
    w.name AS warehouse_name,
    w.size AS warehouse_size,
    w.state AS current_state,
    w.auto_suspend AS auto_suspend_seconds,
    w.min_cluster_count,
    w.max_cluster_count,
    w.scaling_policy,
    CASE
        WHEN w.state = 'STARTED' THEN 'Consuming credits'
        WHEN w.state = 'SUSPENDED' THEN 'No cost'
        ELSE w.state
    END AS cost_status
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSES) w
WHERE w.name LIKE '%_wh'
ORDER BY w.name;

SELECT * FROM warehouse_health_dashboard;


-- Real-world example: E-commerce analytics setup
-- Separate warehouses by workload and SLA

-- 1. Ad-hoc analytics (low priority, cost-sensitive)
CREATE OR REPLACE WAREHOUSE adhoc_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 180
    AUTO_RESUME = TRUE
    COMMENT = 'For exploratory data analysis';

-- 2. Production dashboards (high availability)
CREATE OR REPLACE WAREHOUSE dashboard_wh
WITH
    WAREHOUSE_SIZE = 'MEDIUM'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    SCALING_POLICY = 'ECONOMY'
    AUTO_SUSPEND = 600
    AUTO_RESUME = TRUE
    COMMENT = 'For customer-facing dashboards';

-- 3. ETL pipelines (performance-critical)
CREATE OR REPLACE WAREHOUSE etl_wh
WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'For nightly data pipelines';

-- 4. Data science (variable workload)
CREATE OR REPLACE WAREHOUSE datascience_wh
WITH
    WAREHOUSE_SIZE = 'X-LARGE'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    COMMENT = 'For ML model training';


-- BEST PRACTICE 6: Create resource monitor for cost control
-- (Enterprise Edition feature)
-- This prevents runaway costs by suspending warehouses when credit limit reached

CREATE OR REPLACE RESOURCE MONITOR warehouse_training_monitor
WITH
    CREDIT_QUOTA = 100              -- 100 credits per month
    FREQUENCY = MONTHLY             -- Reset quota monthly
    START_TIMESTAMP = IMMEDIATELY   -- Start monitoring now
    TRIGGERS
        ON 75 PERCENT DO NOTIFY      -- Alert at 75% usage
        ON 90 PERCENT DO NOTIFY      -- Alert at 90% usage
        ON 100 PERCENT DO SUSPEND    -- Suspend warehouses at 100%
        ON 110 PERCENT DO SUSPEND_IMMEDIATE;  -- Immediate suspend at 110%

-- Assign resource monitor to warehouses
ALTER WAREHOUSE dev_xs_wh SET RESOURCE_MONITOR = warehouse_training_monitor;
ALTER WAREHOUSE analytics_small_wh SET RESOURCE_MONITOR = warehouse_training_monitor;

-- View resource monitor status
SHOW RESOURCE MONITORS;


-- ============================================================================
-- CLEANUP: Remove Training Resources
-- ============================================================================
-- Uncomment these lines when training is complete to remove all created resources

/*
DROP WAREHOUSE IF EXISTS dev_xs_wh;
DROP WAREHOUSE IF EXISTS analytics_small_wh;
DROP WAREHOUSE IF EXISTS analytics_medium_wh;
DROP WAREHOUSE IF EXISTS etl_large_wh;
DROP WAREHOUSE IF EXISTS multi_xs_wh;
DROP WAREHOUSE IF EXISTS multi_economy_wh;
DROP WAREHOUSE IF EXISTS multi_standard_wh;
DROP WAREHOUSE IF EXISTS adhoc_wh;
DROP WAREHOUSE IF EXISTS dashboard_wh;
DROP WAREHOUSE IF EXISTS etl_wh;
DROP WAREHOUSE IF EXISTS datascience_wh;
DROP RESOURCE MONITOR IF EXISTS warehouse_training_monitor;
DROP DATABASE IF EXISTS warehouse_training;
*/


-- ============================================================================
-- KEY TAKEAWAYS
-- ============================================================================
-- 1. Virtual warehouses are independent compute clusters that can be sized,
--    suspended, and resumed independently.
--
-- 2. Larger warehouses complete queries faster but cost more per hour.
--    Test different sizes to find optimal cost/performance balance.
--
-- 3. AUTO_SUSPEND is critical for cost control. Set timeout based on usage:
--    - Development: 30-60 seconds
--    - Analytics: 5-10 minutes
--    - Production: 10-20 minutes
--
-- 4. Multi-cluster warehouses scale OUT for concurrency, not query speed.
--    Use ECONOMY scaling to balance cost and performance.
--
-- 5. Monitor credit consumption using WAREHOUSE_METERING_HISTORY.
--    Keep cloud services < 10% of total credits.
--
-- 6. Scale UP for large single queries, scale OUT for concurrent queries.
--
-- 7. Separate workloads by SLA using dedicated warehouses.
--
-- 8. Use resource monitors to prevent cost overruns.
-- ============================================================================
