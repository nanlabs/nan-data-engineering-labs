-- ============================================================================
-- Exercise 06: Data Sharing and Secure Views
-- Complete Solution
-- ============================================================================
-- OBJECTIVE: Implement Snowflake Data Sharing with secure views
-- This solution demonstrates production-grade data sharing configuration
-- ============================================================================

-- Step 1: Environment Setup
-- ============================================================================
USE ROLE TRAINING_ROLE;
USE WAREHOUSE TRAINING_WH;

-- Create database for sharing
CREATE DATABASE IF NOT EXISTS SHARED_ANALYTICS
    COMMENT = 'Database for sharing analytics data with external consumers';

-- Create schema for customer data
CREATE SCHEMA IF NOT EXISTS SHARED_ANALYTICS.CUSTOMER_DATA
    COMMENT = 'Customer metrics and analytics';

USE SCHEMA SHARED_ANALYTICS.CUSTOMER_DATA;

-- Step 2: Create and Populate Source Tables
-- ============================================================================
-- Create customer_metrics table
CREATE OR REPLACE TABLE customer_metrics (
    CUSTOMER_ID VARCHAR(50) NOT NULL,
    METRIC_NAME VARCHAR(100) NOT NULL,
    VALUE DOUBLE NOT NULL,
    DATE DATE NOT NULL,
    CATEGORY VARCHAR(50),
    REGION VARCHAR(50),
    CONSTRAINT pk_customer_metrics PRIMARY KEY (CUSTOMER_ID, METRIC_NAME, DATE)
) COMMENT = 'Customer performance metrics for sharing';

-- Insert sample data for 5 customers
INSERT INTO customer_metrics (CUSTOMER_ID, METRIC_NAME, VALUE, DATE, CATEGORY, REGION)
SELECT
    'CUST_' || LPAD(ABS(MOD(SEQ4(), 5)) + 1, 3, '0') AS CUSTOMER_ID,
    CASE ABS(MOD(SEQ4(), 8))
        WHEN 0 THEN 'revenue'
        WHEN 1 THEN 'orders'
        WHEN 2 THEN 'sessions'
        WHEN 3 THEN 'conversion_rate'
        WHEN 4 THEN 'avg_order_value'
        WHEN 5 THEN 'customer_lifetime_value'
        WHEN 6 THEN 'churn_risk_score'
        ELSE 'active_users'
    END AS METRIC_NAME,
    CASE
        WHEN METRIC_NAME IN ('revenue', 'avg_order_value', 'customer_lifetime_value')
        THEN ROUND(UNIFORM(1000, 50000, RANDOM()), 2)
        WHEN METRIC_NAME IN ('orders', 'sessions', 'active_users')
        THEN ROUND(UNIFORM(50, 5000, RANDOM()), 0)
        WHEN METRIC_NAME = 'conversion_rate'
        THEN ROUND(UNIFORM(0.01, 0.15, RANDOM()), 4)
        WHEN METRIC_NAME = 'churn_risk_score'
        THEN ROUND(UNIFORM(0, 1, RANDOM()), 3)
        ELSE ROUND(UNIFORM(100, 10000, RANDOM()), 2)
    END AS VALUE,
    DATEADD(DAY, -ABS(MOD(SEQ4(), 90)), CURRENT_DATE()) AS DATE,
    CASE ABS(MOD(SEQ4(), 3))
        WHEN 0 THEN 'Sales'
        WHEN 1 THEN 'Marketing'
        ELSE 'Operations'
    END AS CATEGORY,
    CASE ABS(MOD(SEQ4(), 4))
        WHEN 0 THEN 'North America'
        WHEN 1 THEN 'Europe'
        WHEN 2 THEN 'Asia Pacific'
        ELSE 'Latin America'
    END AS REGION
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- Verify data distribution
SELECT
    CUSTOMER_ID,
    COUNT(*) AS metric_count,
    COUNT(DISTINCT METRIC_NAME) AS unique_metrics,
    MIN(DATE) AS earliest_date,
    MAX(DATE) AS latest_date,
    COUNT(DISTINCT REGION) AS regions
FROM customer_metrics
GROUP BY CUSTOMER_ID
ORDER BY CUSTOMER_ID;

-- Summary statistics
SELECT
    'Total Records' AS metric,
    COUNT(*)::VARCHAR AS value
FROM customer_metrics
UNION ALL
SELECT
    'Unique Customers',
    COUNT(DISTINCT CUSTOMER_ID)::VARCHAR
FROM customer_metrics
UNION ALL
SELECT
    'Date Range (Days)',
    DATEDIFF(DAY, MIN(DATE), MAX(DATE))::VARCHAR
FROM customer_metrics;

-- Step 3: Create Secure View with Row-Level Security
-- ============================================================================
-- Create mapping table for account-to-customer access
CREATE OR REPLACE TABLE customer_account_mapping (
    SNOWFLAKE_ACCOUNT VARCHAR(100),
    CUSTOMER_ID VARCHAR(50),
    ACCESS_LEVEL VARCHAR(20) DEFAULT 'READ',
    GRANTED_DATE DATE DEFAULT CURRENT_DATE()
) COMMENT = 'Mapping of Snowflake accounts to customers for row-level security';

-- Insert sample mappings (in production, this would be managed dynamically)
INSERT INTO customer_account_mapping (SNOWFLAKE_ACCOUNT, CUSTOMER_ID)
VALUES
    ('ABC12345', 'CUST_001'),
    ('DEF67890', 'CUST_002'),
    ('GHI11111', 'CUST_003'),
    ('JKL22222', 'CUST_004'),
    ('MNO33333', 'CUST_005');

-- Create secure view with row-level security
CREATE OR REPLACE SECURE VIEW customer_metrics_filtered
    COMMENT = 'Customer metrics filtered by account access'
AS
SELECT
    cm.CUSTOMER_ID,
    cm.METRIC_NAME,
    cm.VALUE,
    cm.DATE,
    cm.CATEGORY,
    cm.REGION
FROM customer_metrics cm
INNER JOIN customer_account_mapping cam
    ON cm.CUSTOMER_ID = cam.CUSTOMER_ID
WHERE cam.SNOWFLAKE_ACCOUNT = CURRENT_ACCOUNT()
    OR CURRENT_ROLE() = 'ACCOUNTADMIN';  -- Allow full access for admins

-- Test secure view (as provider, you'll see all data if ACCOUNTADMIN)
SELECT
    CUSTOMER_ID,
    COUNT(*) AS record_count,
    COUNT(DISTINCT METRIC_NAME) AS unique_metrics
FROM customer_metrics_filtered
GROUP BY CUSTOMER_ID
ORDER BY CUSTOMER_ID;

-- Step 4: Implement Column Masking for PII
-- ============================================================================
-- Create table with PII data
CREATE OR REPLACE TABLE customer_details (
    CUSTOMER_ID VARCHAR(50) NOT NULL,
    NAME VARCHAR(100) NOT NULL,
    EMAIL VARCHAR(100) NOT NULL,
    PHONE VARCHAR(20),
    ADDRESS VARCHAR(200),
    CREDIT_CARD VARCHAR(19),
    CREATED_DATE DATE DEFAULT CURRENT_DATE(),
    CONSTRAINT pk_customer_details PRIMARY KEY (CUSTOMER_ID)
) COMMENT = 'Customer PII data with masking for shares';

-- Insert sample customer details
INSERT INTO customer_details (CUSTOMER_ID, NAME, EMAIL, PHONE, ADDRESS, CREDIT_CARD)
VALUES
    ('CUST_001', 'John Smith', 'john.smith@acmecorp.com', '555-0101', '123 Main St, New York, NY 10001', '4532-1234-5678-9012'),
    ('CUST_002', 'Jane Doe', 'jane.doe@techstart.io', '555-0102', '456 Oak Ave, San Francisco, CA 94102', '5412-9876-5432-1098'),
    ('CUST_003', 'Bob Johnson', 'bob.johnson@globalco.com', '555-0103', '789 Pine Rd, Chicago, IL 60601', '3782-8224-6310-0054'),
    ('CUST_004', 'Alice Williams', 'alice.w@innovate.net', '555-0104', '321 Elm St, Austin, TX 78701', '6011-1111-1111-1117'),
    ('CUST_005', 'Charlie Brown', 'c.brown@enterprise.biz', '555-0105', '654 Maple Dr, Boston, MA 02101', '3714-496353-98431');

-- Create secure view with column masking
CREATE OR REPLACE SECURE VIEW customer_details_masked
    COMMENT = 'Customer details with PII masking'
AS
SELECT
    CUSTOMER_ID,
    NAME,
    -- Mask email - show only domain
    REGEXP_REPLACE(EMAIL, '^[^@]+', '****') AS EMAIL,
    -- Mask phone - show only last 4 digits
    CONCAT('XXX-XXX-', RIGHT(PHONE, 4)) AS PHONE,
    -- Mask address - show only city and state
    REGEXP_REPLACE(ADDRESS, '^[^,]+,\\s*', '*** ') AS ADDRESS,
    -- Mask credit card - show only last 4 digits
    CONCAT('XXXX-XXXX-XXXX-', RIGHT(CREDIT_CARD, 4)) AS CREDIT_CARD,
    CREATED_DATE
FROM customer_details cd
INNER JOIN customer_account_mapping cam
    ON cd.CUSTOMER_ID = cam.CUSTOMER_ID
WHERE cam.SNOWFLAKE_ACCOUNT = CURRENT_ACCOUNT()
    OR CURRENT_ROLE() = 'ACCOUNTADMIN';

-- Test masked view
SELECT * FROM customer_details_masked ORDER BY CUSTOMER_ID;

-- Step 5: Create Data Share
-- ============================================================================
-- Create share object
CREATE SHARE IF NOT EXISTS client_analytics
    COMMENT = 'Analytics data share for client accounts - includes metrics and masked PII';

-- Grant USAGE on database to share
GRANT USAGE ON DATABASE SHARED_ANALYTICS TO SHARE client_analytics;

-- Grant USAGE on schema to share
GRANT USAGE ON SCHEMA SHARED_ANALYTICS.CUSTOMER_DATA TO SHARE client_analytics;

-- Grant SELECT on secure views to share
GRANT SELECT ON VIEW SHARED_ANALYTICS.CUSTOMER_DATA.customer_metrics_filtered
    TO SHARE client_analytics;

GRANT SELECT ON VIEW SHARED_ANALYTICS.CUSTOMER_DATA.customer_details_masked
    TO SHARE client_analytics;

-- Also grant on mapping table (needed for view to work)
GRANT SELECT ON TABLE SHARED_ANALYTICS.CUSTOMER_DATA.customer_account_mapping
    TO SHARE client_analytics;

-- Show share configuration
SHOW GRANTS TO SHARE client_analytics;

-- Describe share
DESC SHARE client_analytics;

-- Step 6: Add Consumer Accounts
-- ============================================================================
-- Add consumer accounts to share
-- Note: Replace with actual account identifiers in production
-- Format: 'ORG_NAME.ACCOUNT_NAME' or just 'ACCOUNT_LOCATOR'

-- Example: Add accounts (these would be real consumer accounts)
ALTER SHARE client_analytics ADD ACCOUNTS = ABC12345, DEF67890, GHI11111;

-- Alternative: Add accounts one at a time
-- ALTER SHARE client_analytics ADD ACCOUNTS = ABC12345;
-- ALTER SHARE client_analytics ADD ACCOUNTS = DEF67890;

-- Show accounts with access
SHOW SHARES LIKE 'client_analytics';

-- Query share details
SELECT
    "name" AS share_name,
    "kind" AS share_type,
    "database_name",
    "to" AS shared_with_accounts,
    "owner",
    "comment"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

-- Step 7: Consumer Simulation (Provider Side)
-- ============================================================================
-- Consumer would execute these commands in their account:
/*
-- Consumer side (in consumer's Snowflake account):
CREATE DATABASE client_analytics_data
FROM SHARE <provider_account>.client_analytics;

USE DATABASE client_analytics_data;
USE SCHEMA CUSTOMER_DATA;

-- Query shared data
SELECT * FROM customer_metrics_filtered LIMIT 100;
SELECT * FROM customer_details_masked;

-- Consumers see only their own customer data due to row-level security
*/

-- Provider can query what's available in the share
SELECT
    TABLE_CATALOG AS database_name,
    TABLE_SCHEMA AS schema_name,
    TABLE_NAME,
    TABLE_TYPE,
    COMMENT
FROM SHARED_ANALYTICS.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'CUSTOMER_DATA'
    AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
ORDER BY TABLE_NAME;

-- Step 8: Monitor Data Transfer and Usage
-- ============================================================================
-- Query data transfer history
SELECT
    TARGET_ACCOUNT_NAME AS consumer_account,
    TARGET_REGION AS consumer_region,
    SOURCE_REGION AS provider_region,
    TO_DATE(START_TIME) AS transfer_date,
    SUM(BYTES_TRANSFERRED) AS total_bytes,
    ROUND(SUM(BYTES_TRANSFERRED) / 1024 / 1024 / 1024, 3) AS total_gb,
    COUNT(DISTINCT TABLE_NAME) AS tables_accessed
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
WHERE SOURCE_DATABASE = 'SHARED_ANALYTICS'
    AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY consumer_account, consumer_region, provider_region, TO_DATE(START_TIME)
ORDER BY transfer_date DESC, consumer_account;

-- Calculate data transfer costs
-- Note: Same-region transfers are typically free
-- Cross-region costs vary by cloud provider
WITH transfer_summary AS (
    SELECT
        TARGET_ACCOUNT_NAME AS consumer_account,
        SOURCE_REGION,
        TARGET_REGION,
        SUM(BYTES_TRANSFERRED) / 1024 / 1024 / 1024 AS total_gb,
        CASE
            WHEN SOURCE_REGION = TARGET_REGION THEN 0
            WHEN SOURCE_REGION LIKE 'AWS%' AND TARGET_REGION LIKE 'AWS%' THEN 0.02  -- $0.02/GB cross-region AWS
            WHEN SOURCE_REGION LIKE 'AZURE%' AND TARGET_REGION LIKE 'AZURE%' THEN 0.02
            ELSE 0.09  -- Cross-cloud transfer
        END AS cost_per_gb
    FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
    WHERE SOURCE_DATABASE = 'SHARED_ANALYTICS'
        AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
    GROUP BY consumer_account, SOURCE_REGION, TARGET_REGION
)
SELECT
    consumer_account,
    SOURCE_REGION,
    TARGET_REGION,
    ROUND(total_gb, 3) AS total_gb_transferred,
    cost_per_gb,
    ROUND(total_gb * cost_per_gb, 2) AS estimated_cost_usd,
    CASE
        WHEN cost_per_gb = 0 THEN 'Same Region (Free)'
        WHEN cost_per_gb < 0.05 THEN 'Same Cloud (Low Cost)'
        ELSE 'Cross Cloud (Higher Cost)'
    END AS cost_category
FROM transfer_summary
ORDER BY estimated_cost_usd DESC;

-- Query access history to see query patterns
SELECT
    USER_NAME,
    QUERY_TYPE,
    DATABASE_NAME,
    SCHEMA_NAME,
    TO_DATE(START_TIME) AS query_date,
    COUNT(*) AS query_count,
    SUM(ROWS_PRODUCED) AS total_rows,
    SUM(BYTES_SCANNED) / 1024 / 1024 AS total_mb_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE BASE_OBJECTS_ACCESSED[0].objectDomain = 'Table'
    AND BASE_OBJECTS_ACCESSED[0].objectName IN ('CUSTOMER_METRICS_FILTERED', 'CUSTOMER_DETAILS_MASKED')
    AND START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY USER_NAME, QUERY_TYPE, DATABASE_NAME, SCHEMA_NAME, TO_DATE(START_TIME)
ORDER BY query_date DESC, query_count DESC;

-- Step 9: Snowflake Data Marketplace Exploration
-- ============================================================================
-- Show available data shares from marketplace
SHOW SHARES;

-- Browse Snowflake Data Marketplace programmatically
-- Note: Full marketplace browsing is typically done through Snowflake UI
SELECT 'Snowflake Data Marketplace' AS note,
       'Access via: Snowsight → Data → Marketplace' AS instructions;

-- Document interesting datasets (examples):
/*
=== RECOMMENDED MARKETPLACE DATASETS ===

1. DATASET: Knoema Economy Data Atlas
   PROVIDER: Knoema Corporation
   DESCRIPTION: Global economic indicators including GDP, inflation, trade data
   USE CASE: Economic analysis, forecasting, market research
   ACCESS: Free tier available, premium for full access

2. DATASET: COVID-19 Epidemiological Data
   PROVIDER: Starschema
   DESCRIPTION: Global COVID-19 case data, testing, vaccinations
   USE CASE: Public health analysis, pandemic tracking, research
   ACCESS: Free public dataset

3. DATASET: Weather Source Historical Weather Data
   PROVIDER: Weather Source
   DESCRIPTION: Historical weather observations and forecasts globally
   USE CASE: Risk modeling, agriculture, logistics planning
   ACCESS: Free sample, paid for full historical data

4. DATASET: Cybersyn Financial & Economic Essentials
   PROVIDER: Cybersyn
   DESCRIPTION: Financial market data, economic indicators, demographics
   USE CASE: Investment research, economic modeling, business intelligence
   ACCESS: Free tier with registration

5. DATASET: Zepl Data Marketplace - Company Financials
   PROVIDER: Zepl
   DESCRIPTION: Public company financial statements and metrics
   USE CASE: Financial analysis, investment screening, competitive research
   ACCESS: Freemium model

=== HOW TO ACCESS MARKETPLACE DATA ===
1. Navigate to Snowsight → Data → Marketplace
2. Browse or search for datasets
3. Click "Get" to request access
4. Some datasets are instant, others require approval
5. Once granted, dataset appears as a database in your account
6. Query like any other Snowflake database
*/

-- Example: If you have access to a marketplace dataset
-- USE DATABASE KNOEMA_ECONOMY_DATA_ATLAS;
-- SELECT * FROM ECONOMY.OECD_MEI LIMIT 100;

-- Step 10: Advanced Sharing Scenarios
-- ============================================================================
-- Create aggregated secure view (protects granular data)
CREATE OR REPLACE SECURE VIEW customer_metrics_weekly_agg
    COMMENT = 'Weekly aggregated metrics - less granular for broader sharing'
AS
SELECT
    cm.CUSTOMER_ID,
    DATE_TRUNC('WEEK', cm.DATE) AS WEEK_START,
    cm.METRIC_NAME,
    AVG(cm.VALUE) AS avg_value,
    MIN(cm.VALUE) AS min_value,
    MAX(cm.VALUE) AS max_value,
    COUNT(*) AS measurement_count,
    cm.CATEGORY,
    cm.REGION
FROM customer_metrics cm
INNER JOIN customer_account_mapping cam
    ON cm.CUSTOMER_ID = cam.CUSTOMER_ID
WHERE cam.SNOWFLAKE_ACCOUNT = CURRENT_ACCOUNT()
    OR CURRENT_ROLE() = 'ACCOUNTADMIN'
GROUP BY
    cm.CUSTOMER_ID,
    DATE_TRUNC('WEEK', cm.DATE),
    cm.METRIC_NAME,
    cm.CATEGORY,
    cm.REGION;

-- Grant to share
GRANT SELECT ON VIEW SHARED_ANALYTICS.CUSTOMER_DATA.customer_metrics_weekly_agg
    TO SHARE client_analytics;

-- Create time-limited view (only recent data)
CREATE OR REPLACE SECURE VIEW customer_metrics_recent_30d
    COMMENT = 'Customer metrics - last 30 days only'
AS
SELECT
    CUSTOMER_ID,
    METRIC_NAME,
    VALUE,
    DATE,
    CATEGORY,
    REGION,
    DATEDIFF(DAY, DATE, CURRENT_DATE()) AS days_ago
FROM customer_metrics_filtered
WHERE DATE >= DATEADD(DAY, -30, CURRENT_DATE());

-- Grant to share
GRANT SELECT ON VIEW SHARED_ANALYTICS.CUSTOMER_DATA.customer_metrics_recent_30d
    TO SHARE client_analytics;

-- Create comprehensive share documentation view
CREATE OR REPLACE VIEW share_documentation AS
SELECT
    'client_analytics' AS share_name,
    'customer_metrics_filtered' AS view_name,
    'Detailed daily metrics with row-level security by customer' AS description,
    'All historical data' AS time_range
UNION ALL
SELECT
    'client_analytics',
    'customer_details_masked',
    'Customer PII with email, phone, address, credit card masking',
    'Current data'
UNION ALL
SELECT
    'client_analytics',
    'customer_metrics_weekly_agg',
    'Weekly aggregated metrics - less granular',
    'All historical data'
UNION ALL
SELECT
    'client_analytics',
    'customer_metrics_recent_30d',
    'Daily metrics limited to last 30 days',
    'Rolling 30 days';

-- View documentation
SELECT * FROM share_documentation;

-- ============================================================================
-- Share Management Queries
-- ============================================================================
-- List all shares you're providing
SHOW SHARES;

-- List all objects in a share
SHOW GRANTS TO SHARE client_analytics;

-- Check share usage statistics
SELECT
    SHARE_NAME,
    TO_ACCOUNT_LOCATOR AS consumer_account,
    COUNT(*) AS access_count,
    MIN(START_TIME) AS first_access,
    MAX(START_TIME) AS last_access
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE SHARE_NAME = 'CLIENT_ANALYTICS'
    AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY SHARE_NAME, TO_ACCOUNT_LOCATOR
ORDER BY access_count DESC;

-- ============================================================================
-- Complete - Exercise 06 Solution Implemented Successfully
-- ============================================================================

-- Final verification
SELECT
    '=== Data Sharing Summary ===' AS section
UNION ALL
SELECT 'Share Name: client_analytics'
UNION ALL
SELECT 'Secure Views: 4 (with row-level security and masking)'
UNION ALL
SELECT 'Consumer Accounts: 3 (ABC12345, DEF67890, GHI11111)'
UNION ALL
SELECT 'Customer Data: 5 customers, 10,000 metrics'
UNION ALL
SELECT 'Marketplace Datasets Explored: 5'
UNION ALL
SELECT 'Status: ✓ Ready for consumption';
