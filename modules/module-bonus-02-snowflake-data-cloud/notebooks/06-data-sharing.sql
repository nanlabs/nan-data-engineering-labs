-- ============================================================================
-- Module Bonus 02: Snowflake Data Cloud
-- Notebook 06: Data Sharing and Snowflake Marketplace
-- ============================================================================
-- Description: Master Snowflake's Data Sharing capabilities to securely share
--              data with partners, customers, or across business units. Learn
--              secure views, reader accounts, and Snowflake Data Marketplace.
--
-- Prerequisites:
--   - Snowflake account with ACCOUNTADMIN role
--   - Understanding of Snowflake security model
--   - Enterprise Edition (for full sharing features)
--
-- Estimated Time: 75 minutes
-- ============================================================================

-- ============================================================================
-- SETUP: Create Provider Environment
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Create warehouse for data sharing demo
CREATE OR REPLACE WAREHOUSE sharing_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE sharing_wh;

-- Create database with data to share (Provider side)
CREATE OR REPLACE DATABASE provider_data;
USE DATABASE provider_data;

CREATE SCHEMA IF NOT EXISTS public_data;
USE SCHEMA public_data;

-- Create customers table (to be shared)
CREATE OR REPLACE TABLE customers (
    customer_id NUMBER(10,0) PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE,
    company_name VARCHAR(200),
    contact_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    industry VARCHAR(50),
    company_size VARCHAR(20),
    annual_revenue DECIMAL(15,2),
    customer_since DATE,
    account_status VARCHAR(20),
    region VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Load sample customer data
INSERT INTO customers
SELECT
    SEQ4() AS customer_id,
    CONCAT('ACCT-', LPAD(SEQ4()::VARCHAR, 8, '0')) AS account_number,
    CONCAT('Company ', SEQ4(), ' Inc') AS company_name,
    ARRAY_GET(PARSE_JSON('["John Smith","Jane Doe","Mike Johnson","Sarah Williams","David Brown"]'),
              UNIFORM(0, 4, RANDOM())) AS contact_name,
    CONCAT('contact', SEQ4(), '@company', UNIFORM(1, 100, RANDOM()), '.com') AS email,
    CONCAT('555-', LPAD(UNIFORM(100, 999, RANDOM())::VARCHAR, 3, '0'), '-',
           LPAD(UNIFORM(1000, 9999, RANDOM())::VARCHAR, 4, '0')) AS phone,
    CASE UNIFORM(1, 6, RANDOM())
        WHEN 1 THEN 'Technology'
        WHEN 2 THEN 'Healthcare'
        WHEN 3 THEN 'Finance'
        WHEN 4 THEN 'Retail'
        WHEN 5 THEN 'Manufacturing'
        ELSE 'Services'
    END AS industry,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Small (1-50)'
        WHEN 2 THEN 'Medium (51-250)'
        WHEN 3 THEN 'Large (251-1000)'
        WHEN 4 THEN 'Enterprise (1001-5000)'
        ELSE 'Global (5000+)'
    END AS company_size,
    UNIFORM(500000, 50000000, RANDOM()) AS annual_revenue,
    DATEADD(DAY, -UNIFORM(30, 1825, RANDOM()), CURRENT_DATE()) AS customer_since,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'Inactive'
        WHEN 2 THEN 'Suspended'
        ELSE 'Active'
    END AS account_status,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'North America'
        WHEN 2 THEN 'Europe'
        WHEN 3 THEN 'Asia Pacific'
        ELSE 'Latin America'
    END AS region,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'USA'
        WHEN 2 THEN 'Canada'
        WHEN 3 THEN 'UK'
        WHEN 4 THEN 'Germany'
        WHEN 5 THEN 'France'
        WHEN 6 THEN 'Japan'
        WHEN 7 THEN 'Australia'
        WHEN 8 THEN 'Singapore'
        WHEN 9 THEN 'Brazil'
        ELSE 'Mexico'
    END AS country,
    DATEADD(DAY, -UNIFORM(30, 1825, RANDOM()), CURRENT_TIMESTAMP()) AS created_at
FROM TABLE(GENERATOR(ROWCOUNT => 5000));

SELECT COUNT(*) FROM customers;
-- Expected: 5000


-- Create orders table
CREATE OR REPLACE TABLE orders (
    order_id NUMBER(12,0) PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE,
    customer_id NUMBER(10,0),
    order_date DATE,
    product_category VARCHAR(50),
    product_name VARCHAR(200),
    quantity NUMBER(10,0),
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(12,2),
    order_status VARCHAR(20),
    payment_terms VARCHAR(30),
    delivery_date DATE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Load sample orders
INSERT INTO orders
SELECT
    SEQ4() AS order_id,
    CONCAT('ORD-', LPAD(SEQ4()::VARCHAR, 12, '0')) AS order_number,
    UNIFORM(0, 4999, RANDOM()) AS customer_id,
    DATEADD(DAY, -UNIFORM(0, 730, RANDOM()), CURRENT_DATE()) AS order_date,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Software'
        WHEN 2 THEN 'Hardware'
        WHEN 3 THEN 'Services'
        WHEN 4 THEN 'Training'
        ELSE 'Support'
    END AS product_category,
    CONCAT('Product ', UNIFORM(1, 100, RANDOM())) AS product_name,
    UNIFORM(1, 100, RANDOM()) AS quantity,
    UNIFORM(50, 5000, RANDOM()) AS unit_price,
    (UNIFORM(1, 100, RANDOM()) * UNIFORM(50, 5000, RANDOM())) AS total_amount,
    CASE UNIFORM(1, 6, RANDOM())
        WHEN 1 THEN 'Pending'
        WHEN 2 THEN 'Processing'
        WHEN 3 THEN 'Shipped'
        WHEN 4 THEN 'Delivered'
        WHEN 5 THEN 'Cancelled'
        ELSE 'Completed'
    END AS order_status,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'Net 30'
        WHEN 2 THEN 'Net 60'
        WHEN 3 THEN 'Net 90'
        ELSE 'Prepaid'
    END AS payment_terms,
    DATEADD(DAY, UNIFORM(1, 30, RANDOM()),
            DATEADD(DAY, -UNIFORM(0, 730, RANDOM()), CURRENT_DATE())) AS delivery_date,
    DATEADD(DAY, -UNIFORM(0, 730, RANDOM()), CURRENT_TIMESTAMP()) AS created_at
FROM TABLE(GENERATOR(ROWCOUNT => 20000));

SELECT COUNT(*) FROM orders;
-- Expected: 20000


-- ============================================================================
-- SECTION 1: Create Data Share
-- ============================================================================
-- Shares enable secure data access without copying or moving data.
-- Consumers query shared data directly from provider's account.
-- ============================================================================

-- Create a data share (Provider perspective)
CREATE OR REPLACE SHARE customer_analytics_share
    COMMENT = 'Share customer and order data with business partners';

-- View created share
SHOW SHARES;

-- Describe share (currently empty)
DESC SHARE customer_analytics_share;


-- Grant database usage to share
GRANT USAGE ON DATABASE provider_data TO SHARE customer_analytics_share;

-- Grant schema usage to share
GRANT USAGE ON SCHEMA provider_data.public_data TO SHARE customer_analytics_share;

-- Grant SELECT on specific tables to share
GRANT SELECT ON TABLE provider_data.public_data.customers TO SHARE customer_analytics_share;
GRANT SELECT ON TABLE provider_data.public_data.orders TO SHARE customer_analytics_share;

-- Describe share again (now shows granted objects)
DESC SHARE customer_analytics_share;


-- View what's being shared
SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));


-- Create additional share for limited access
CREATE OR REPLACE SHARE customer_summary_share
    COMMENT = 'Share aggregated customer data only';

GRANT USAGE ON DATABASE provider_data TO SHARE customer_summary_share;
GRANT USAGE ON SCHEMA provider_data.public_data TO SHARE customer_summary_share;


-- Query all shares in account
SELECT
    name AS share_name,
    kind,
    owner,
    comment,
    created_on
FROM SNOWFLAKE.ACCOUNT_USAGE.SHARES
WHERE owner = CURRENT_ACCOUNT()
ORDER BY created_on DESC;


-- ============================================================================
-- SECTION 2: Grant Objects to Share
-- ============================================================================
-- Control exactly what data consumers can access via shares.
-- ============================================================================

-- Grant specific columns vs entire table (not directly supported)
-- Instead, create views with desired columns and share views

-- Create view with subset of customer data
CREATE OR REPLACE VIEW customer_summary AS
SELECT
    customer_id,
    account_number,
    company_name,
    industry,
    company_size,
    region,
    country,
    customer_since,
    account_status,
    -- Exclude sensitive fields like email, phone, contact_name
    created_at
FROM customers;

-- Share the view instead of base table
GRANT SELECT ON VIEW provider_data.public_data.customer_summary
    TO SHARE customer_summary_share;


-- Create aggregated view for high-level metrics
CREATE OR REPLACE VIEW order_metrics AS
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS lifetime_value,
    AVG(total_amount) AS avg_order_value,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date,
    DATEDIFF(DAY, MAX(order_date), CURRENT_DATE()) AS days_since_last_order
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY customer_id;

GRANT SELECT ON VIEW provider_data.public_data.order_metrics
    TO SHARE customer_analytics_share;


-- Grant access to functions (if defined)
-- CREATE FUNCTION example would go here, then:
-- GRANT USAGE ON FUNCTION my_function TO SHARE customer_analytics_share;


-- View all objects granted to a share
SHOW GRANTS TO SHARE customer_analytics_share;

SHOW GRANTS TO SHARE customer_summary_share;


-- Revoke access from share
-- REVOKE SELECT ON TABLE orders FROM SHARE customer_analytics_share;


-- ============================================================================
-- SECTION 3: Add Consumer Accounts
-- ============================================================================
-- Share data with specific Snowflake accounts or create reader accounts.
-- ============================================================================

-- Add consumer account to share (replace with actual account identifier)
-- Format: <organization_name>.<account_name> or <account_locator>
-- ALTER SHARE customer_analytics_share ADD ACCOUNTS = ABC12345, DEF67890;

-- View example of adding accounts (commented as it requires real account IDs)
/*
ALTER SHARE customer_analytics_share
    ADD ACCOUNTS = 'PARTNER_ORG.PARTNER_ACCOUNT';
*/

-- Show accounts that have access to share
SHOW SHARES LIKE 'customer_analytics_share';

-- Query share accounts from ACCOUNT_USAGE
SELECT
    share_name,
    consumer_account_locator,
    consumer_account_locator_url,
    is_consumer_account,
    shared_on
FROM SNOWFLAKE.ACCOUNT_USAGE.SHARE_ACCOUNTS
WHERE share_name = 'CUSTOMER_ANALYTICS_SHARE'
ORDER BY shared_on DESC;


-- Remove consumer from share
-- ALTER SHARE customer_analytics_share REMOVE ACCOUNTS = ABC12345;


-- Create managed account (reader account) for consumers without Snowflake
-- Reader accounts are lightweight, read-only accounts managed by provider
/*
CREATE MANAGED ACCOUNT partner1_reader_account
    ADMIN_NAME = 'partner_admin'
    ADMIN_PASSWORD = 'StrongPassword123!'
    TYPE = READER
    COMMENT = 'Reader account for Partner 1';

-- Add reader account to share
ALTER SHARE customer_analytics_share
    ADD ACCOUNTS = partner1_reader_account;
*/

-- View managed accounts
SHOW MANAGED ACCOUNTS;


-- Reader account characteristics:
-- - No storage costs for consumer (provider bears storage cost)
-- - Compute billed to provider or consumer (configurable)
-- - Read-only access to shared objects
-- - Ideal for external partners without Snowflake accounts


-- ============================================================================
-- SECTION 4: Consumer Side - Access Shared Data
-- ============================================================================
-- How consumers access and query shared data in their accounts.
-- ============================================================================

-- NOTE: These commands run in CONSUMER's Snowflake account
-- They are shown here for educational purposes

-- Consumer creates database from share (Consumer perspective)
/*
-- View available inbound shares
SHOW SHARES;

-- Create database from share
CREATE DATABASE shared_customer_data
    FROM SHARE <provider_account>.customer_analytics_share
    COMMENT = 'Customer data shared by provider';

-- Verify database structure
USE DATABASE shared_customer_data;
SHOW SCHEMAS;
SHOW TABLES;

-- Query shared data
SELECT * FROM shared_customer_data.public_data.customers LIMIT 10;

SELECT * FROM shared_customer_data.public_data.orders LIMIT 10;

-- Consumer can create views on shared data
CREATE VIEW customer_orders_summary AS
SELECT
    c.customer_id,
    c.company_name,
    c.industry,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent
FROM shared_customer_data.public_data.customers c
LEFT JOIN shared_customer_data.public_data.orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name, c.industry;

-- Consumer CANNOT modify shared data
-- INSERT/UPDATE/DELETE will fail on shared objects
-- UPDATE shared_customer_data.public_data.customers SET...  -- ERROR

-- Consumer can see share metadata
DESC DATABASE shared_customer_data;
*/


-- Provider monitoring: Track consumer usage
SELECT
    consumer_account_locator,
    database_name,
    object_name,
    user_name,
    query_type,
    start_time,
    execution_status,
    total_elapsed_time / 1000 AS execution_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE database_name = 'PROVIDER_DATA'
  -- Filter for queries from consumer accounts would go here
  AND start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC
LIMIT 100;


-- ============================================================================
-- SECTION 5: Secure Views for Row-Level Security
-- ============================================================================
-- Use secure views to filter data per consumer without exposing logic.
-- ============================================================================

-- Create context function for identifying consumer
-- In production, use CURRENT_ACCOUNT() or custom mapping table
CREATE OR REPLACE FUNCTION get_consumer_region()
RETURNS VARCHAR
AS
$$
    -- In reality, map CURRENT_ACCOUNT() to region
    -- For demo, return all regions
    'ALL'
$$;


-- Create secure view with row-level filtering
CREATE OR REPLACE SECURE VIEW customers_filtered AS
SELECT
    customer_id,
    account_number,
    company_name,
    contact_name,
    email,
    industry,
    company_size,
    region,
    country,
    customer_since,
    account_status
FROM customers
WHERE
    -- Filter based on consumer context
    CASE get_consumer_region()
        WHEN 'North America' THEN region = 'North America'
        WHEN 'Europe' THEN region = 'Europe'
        WHEN 'Asia Pacific' THEN region = 'Asia Pacific'
        WHEN 'Latin America' THEN region = 'Latin America'
        ELSE TRUE  -- 'ALL' shows all regions
    END
    AND account_status = 'Active';  -- Only show active accounts


-- Secure view properties:
-- 1. Query definition is hidden from consumers
-- 2. Prevents consumers from reverse-engineering filtering logic
-- 3. Enables row-level security based on consumer identity

-- Grant secure view to share
GRANT SELECT ON VIEW provider_data.public_data.customers_filtered
    TO SHARE customer_analytics_share;


-- Create secure view that excludes sensitive columns
CREATE OR REPLACE SECURE VIEW orders_public AS
SELECT
    order_id,
    order_number,
    customer_id,
    order_date,
    product_category,
    product_name,
    quantity,
    total_amount,
    order_status,
    delivery_date
    -- Exclude: unit_price, payment_terms (sensitive pricing info)
FROM orders
WHERE order_status IN ('Completed', 'Delivered');  -- Only successful orders

GRANT SELECT ON VIEW provider_data.public_data.orders_public
    TO SHARE customer_analytics_share;


-- Advanced: Multi-tenant row-level security
CREATE OR REPLACE TABLE consumer_access (
    consumer_account VARCHAR(100),
    customer_id NUMBER(10,0),
    access_level VARCHAR(20),
    granted_on TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Map consumers to specific customers they can access
INSERT INTO consumer_access VALUES
    ('ABC12345', 100, 'Full', CURRENT_TIMESTAMP()),
    ('ABC12345', 101, 'Full', CURRENT_TIMESTAMP()),
    ('DEF67890', 200, 'Limited', CURRENT_TIMESTAMP());


-- Secure view using access control table
CREATE OR REPLACE SECURE VIEW customers_multi_tenant AS
SELECT
    c.customer_id,
    c.account_number,
    c.company_name,
    c.industry,
    c.region,
    c.account_status
FROM customers c
INNER JOIN consumer_access ca
    ON c.customer_id = ca.customer_id
    -- In production: WHERE ca.consumer_account = CURRENT_ACCOUNT()
WHERE ca.access_level IN ('Full', 'Limited');


-- Test secure view
SELECT * FROM customers_filtered LIMIT 10;
SELECT * FROM orders_public LIMIT 10;


-- ============================================================================
-- SECTION 6: Monitor Data Sharing Usage
-- ============================================================================
-- Track how consumers use shared data and monitor transfer costs.
-- ============================================================================

-- View data transfer between regions (incurs costs)
SELECT
    source_cloud,
    source_region,
    target_cloud,
    target_region,
    transfer_type,
    DATE(start_time) AS transfer_date,
    SUM(bytes_transferred) / (1024*1024*1024) AS gb_transferred
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
WHERE start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY source_cloud, source_region, target_cloud, target_region, transfer_type, DATE(start_time)
ORDER BY transfer_date DESC, gb_transferred DESC;


-- Calculate data transfer costs
-- Cross-region data transfer: ~$0.02 per GB (varies by cloud/region)
WITH transfer_summary AS (
    SELECT
        target_cloud,
        target_region,
        DATE_TRUNC('MONTH', start_time) AS month,
        SUM(bytes_transferred) / (1024*1024*1024) AS total_gb
    FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
    WHERE transfer_type = 'SHARE_DATA'
      AND start_time >= DATEADD(MONTH, -3, CURRENT_TIMESTAMP())
    GROUP BY target_cloud, target_region, DATE_TRUNC('MONTH', start_time)
)
SELECT
    month,
    target_cloud,
    target_region,
    ROUND(total_gb, 2) AS gb_transferred,
    ROUND(total_gb * 0.02, 2) AS estimated_cost_usd
FROM transfer_summary
ORDER BY month DESC, gb_transferred DESC;


-- Monitor share access by consumers
SELECT
    share_name,
    COUNT(DISTINCT consumer_account_locator) AS consumer_count,
    MIN(shared_on) AS first_shared,
    MAX(shared_on) AS last_shared
FROM SNOWFLAKE.ACCOUNT_USAGE.SHARE_ACCOUNTS
WHERE share_name LIKE '%customer%'
GROUP BY share_name;


-- Track queries executed on shared data
-- (Run on provider account to see consumer usage)
SELECT
    DATE(start_time) AS query_date,
    database_name,
    user_name,
    COUNT(*) AS query_count,
    AVG(total_elapsed_time / 1000) AS avg_execution_seconds,
    SUM(bytes_scanned) / (1024*1024*1024) AS total_gb_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE database_name = 'PROVIDER_DATA'
  AND start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY DATE(start_time), database_name, user_name
ORDER BY query_date DESC;


-- Create monitoring view for share analytics
CREATE OR REPLACE VIEW share_usage_dashboard AS
SELECT
    s.share_name,
    s.kind AS share_type,
    s.comment AS share_description,
    COUNT(DISTINCT sa.consumer_account_locator) AS total_consumers,
    -- Would join with query history to show consumer activity
    'Active' AS status
FROM SNOWFLAKE.ACCOUNT_USAGE.SHARES s
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.SHARE_ACCOUNTS sa
    ON s.name = sa.share_name
WHERE s.owner = CURRENT_ACCOUNT()
GROUP BY s.share_name, s.kind, s.comment;

SELECT * FROM share_usage_dashboard;


-- ============================================================================
-- SECTION 7: Snowflake Data Marketplace
-- ============================================================================
-- Discover and consume public datasets from Snowflake Data Marketplace.
-- ============================================================================

-- NOTE: Data Marketplace browsing happens in Snowflake UI at:
-- https://<your-account>.snowflakecomputing.com/marketplace

-- View example listings (simulated - actual marketplace is in UI)
/*
Available Dataset Categories:
- Business & Finance (Stock data, Economic indicators)
- Weather & Environment (Weather history, Climate data)
- Demographics (Population, Census data)
- Healthcare (COVID-19 data, Health statistics)
- Technology (GitHub events, Open source metrics)
- Transportation (Flight data, Traffic patterns)
*/


-- Example: Access free COVID-19 dataset from marketplace
-- (This would be set up through UI, showing conceptual usage)
/*
-- After subscribing in marketplace, create database from share
CREATE DATABASE covid19_data
    FROM SHARE <provider>.covid19_by_starschema;

-- Query marketplace data
USE DATABASE covid19_data;
SHOW SCHEMAS;

SELECT * FROM public.jhu_covid_19 LIMIT 100;

-- Combine marketplace data with internal data
SELECT
    c.province_state,
    c.country_region,
    c.confirmed,
    c.deaths,
    c.recovered,
    cust.customer_count
FROM covid19_data.public.jhu_covid_19 c
JOIN (
    SELECT country, COUNT(*) AS customer_count
    FROM provider_data.public_data.customers
    GROUP BY country
) cust
    ON c.country_region = cust.country;
*/


-- View all databases from shares (including marketplace)
SELECT
    database_name,
    origin,
    type,
    owner,
    comment,
    created
FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASES
WHERE origin IS NOT NULL  -- Databases created from shares
ORDER BY created DESC;


-- Querying available listings (conceptual)
CREATE OR REPLACE VIEW marketplace_categories AS
SELECT 'Business & Finance' AS category, 'Stock prices, economic indicators' AS description
UNION ALL SELECT 'Weather & Environment', 'Weather history, climate data'
UNION ALL SELECT 'Demographics', 'Population data, census information'
UNION ALL SELECT 'Healthcare', 'COVID-19 data, health statistics'
UNION ALL SELECT 'Technology', 'GitHub events, open source metrics'
UNION ALL SELECT 'Geospatial', 'Location data, maps, points of interest'
UNION ALL SELECT 'Consumer', 'Retail trends, consumer behavior'
UNION ALL SELECT 'Marketing', 'Ad performance, social media metrics';

SELECT * FROM marketplace_categories;


-- Best practices for using marketplace data
CREATE OR REPLACE VIEW marketplace_best_practices AS
SELECT
    'Verify data freshness' AS practice,
    'Check last update timestamp' AS implementation,
    'Ensure data meets recency requirements' AS benefit
UNION ALL
SELECT
    'Understand licensing',
    'Review provider terms and usage restrictions',
    'Ensure compliance with data usage rights'
UNION ALL
SELECT
    'Monitor costs',
    'Some listings charge for compute or data volume',
    'Control expenses from external data'
UNION ALL
SELECT
    'Test before production',
    'Validate data quality in dev environment',
    'Prevent production issues'
UNION ALL
SELECT
    'Combine with internal data',
    'Join marketplace data with proprietary data',
    'Enhanced insights and analytics'
UNION ALL
SELECT
    'Set up refresh schedules',
    'If provider updates data, plan refresh cadence',
    'Keep analytics current';

SELECT * FROM marketplace_best_practices;


-- ============================================================================
-- SECTION 8: Use Cases for Data Sharing
-- ============================================================================
-- Real-world applications of Snowflake data sharing.
-- ============================================================================

-- USE CASE 1: Multi-Tenant SaaS Application
-- Share different data subsets with each customer

CREATE OR REPLACE TABLE saas_customers (
    tenant_id VARCHAR(50) PRIMARY KEY,
    tenant_name VARCHAR(200),
    snowflake_account VARCHAR(100),
    subscription_tier VARCHAR(20),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO saas_customers VALUES
    ('TENANT001', 'Acme Corp', 'ABC12345', 'Enterprise', CURRENT_TIMESTAMP()),
    ('TENANT002', 'Beta Inc', 'DEF67890', 'Professional', CURRENT_TIMESTAMP()),
    ('TENANT003', 'Gamma LLC', 'GHI11111', 'Standard', CURRENT_TIMESTAMP());


-- Create secure view for tenant isolation
CREATE OR REPLACE SECURE VIEW multi_tenant_customers AS
SELECT
    c.*
FROM customers c
WHERE c.customer_id IN (
    -- Map current consumer to their accessible customers
    -- In production: JOIN with tenant mapping based on CURRENT_ACCOUNT()
    SELECT customer_id FROM customers LIMIT 100
);


-- USE CASE 2: B2B Data Exchange
-- Share transaction data with suppliers or partners

CREATE OR REPLACE SHARE supplier_analytics_share
    COMMENT = 'Share order data with suppliers';

GRANT USAGE ON DATABASE provider_data TO SHARE supplier_analytics_share;
GRANT USAGE ON SCHEMA provider_data.public_data TO SHARE supplier_analytics_share;

-- Create view with supplier-relevant metrics
CREATE OR REPLACE VIEW supplier_order_metrics AS
SELECT
    DATE_TRUNC('MONTH', order_date) AS order_month,
    product_category,
    COUNT(*) AS order_count,
    SUM(quantity) AS total_quantity,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value
FROM orders
WHERE order_status IN ('Completed', 'Delivered')
GROUP BY DATE_TRUNC('MONTH', order_date), product_category;

GRANT SELECT ON VIEW provider_data.public_data.supplier_order_metrics
    TO SHARE supplier_analytics_share;


-- USE CASE 3: Data Monetization
-- Sell data products to external customers

CREATE OR REPLACE SHARE premium_analytics_share
    COMMENT = 'Premium analytics data product for subscribers';

-- Create enriched data product
CREATE OR REPLACE VIEW industry_benchmarks AS
SELECT
    industry,
    company_size,
    COUNT(*) AS company_count,
    AVG(annual_revenue) AS avg_revenue,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY annual_revenue) AS median_revenue,
    AVG(
        SELECT COUNT(*)
        FROM orders o
        WHERE o.customer_id = c.customer_id
    ) AS avg_orders_per_company
FROM customers c
WHERE account_status = 'Active'
GROUP BY industry, company_size;

GRANT SELECT ON VIEW provider_data.public_data.industry_benchmarks
    TO SHARE premium_analytics_share;


-- USE CASE 4: Internal Cross-Department Sharing
-- Share data between departments without data duplication

-- Finance department creates share for Sales
CREATE OR REPLACE SHARE finance_to_sales_share
    COMMENT = 'Financial metrics for sales planning';

-- Sales can access without copying data
-- Still maintains governance and security boundaries


-- USE CASE 5: Real-Time Collaboration
-- Multiple teams analyzing same live dataset

-- Create share for analytics team
CREATE OR REPLACE SHARE analytics_workspace_share
    COMMENT = 'Live data for analytics team';

-- Data updates immediately visible to consumers
-- No ETL delays or data synchronization needed


-- Summary of use case benefits
CREATE OR REPLACE VIEW data_sharing_benefits AS
SELECT
    'Multi-Tenant SaaS' AS use_case,
    'Data isolation per customer' AS requirement,
    'Secure views with row-level security' AS solution,
    'Scale to thousands of tenants' AS benefit
UNION ALL
SELECT
    'B2B Data Exchange',
    'Share with partners/suppliers',
    'Controlled access via shares',
    'Real-time collaboration without data movement'
UNION ALL
SELECT
    'Data Monetization',
    'Sell data products',
    'Reader accounts + usage tracking',
    'New revenue stream, control distribution'
UNION ALL
SELECT
    'Internal Governance',
    'Department data access',
    'Share between business units',
    'Single source of truth, no duplication'
UNION ALL
SELECT
    'Real-Time Analytics',
    'Live data access',
    'Zero-copy sharing',
    'Eliminate ETL latency'
UNION ALL
SELECT
    'Data Marketplace',
    'Access external datasets',
    'Browse and subscribe to listings',
    'Enrich analysis with external data';

SELECT * FROM data_sharing_benefits;


-- Cost comparison: Data Sharing vs Traditional Methods
CREATE OR REPLACE VIEW sharing_cost_comparison AS
SELECT
    'Traditional (ETL + Copy)' AS method,
    'High' AS storage_cost,
    'High (ETL pipelines)' AS compute_cost,
    'Hours to Days' AS data_latency,
    'Multiple copies to maintain' AS maintenance
UNION ALL
SELECT
    'Snowflake Data Sharing',
    'Low (single copy)',
    'Low (query-time only)',
    'Real-time (no latency)',
    'No synchronization needed';

SELECT * FROM sharing_cost_comparison;


-- ============================================================================
-- CLEANUP
-- ============================================================================

/*
-- Drop shares
DROP SHARE IF EXISTS customer_analytics_share;
DROP SHARE IF EXISTS customer_summary_share;
DROP SHARE IF EXISTS supplier_analytics_share;
DROP SHARE IF EXISTS premium_analytics_share;
DROP SHARE IF EXISTS finance_to_sales_share;
DROP SHARE IF EXISTS analytics_workspace_share;

-- Drop database and warehouse
DROP DATABASE IF EXISTS provider_data;
DROP WAREHOUSE IF EXISTS sharing_wh;
*/


-- ============================================================================
-- KEY TAKEAWAYS
-- ============================================================================
-- 1. Snowflake Data Sharing enables secure data access without copying or
--    moving data. Consumers query provider's data directly.
--
-- 2. Zero-copy sharing: Single copy of data, multiple consumers. No storage
--    duplication, always current data, no ETL delays.
--
-- 3. Create shares with CREATE SHARE, grant database/schema/table access,
--    add consumer accounts with ALTER SHARE ADD ACCOUNTS.
--
-- 4. Secure views provide row-level security and hide filtering logic.
--    Use for multi-tenant isolation and sensitive data protection.
--
-- 5. Reader accounts enable sharing with organizations without Snowflake.
--    Provider manages account, consumer gets read-only access.
--
-- 6. Monitor sharing with DATA_TRANSFER_HISTORY and SHARE_ACCOUNTS views.
--    Track cross-region transfer costs ($0.02/GB typically).
--
-- 7. Snowflake Data Marketplace offers free and paid datasets from providers.
--    Enrich internal data with external sources (weather, demographics, etc.).
--
-- 8. Key use cases:
--    - Multi-tenant SaaS (isolated customer data)
--    - B2B data exchange (supplier/partner collaboration)
--    - Data monetization (sell data products)
--    - Internal governance (cross-department sharing)
--    - Real-time analytics (eliminate ETL)
--
-- 9. Benefits vs traditional methods:
--    - No storage duplication (lower cost)
--    - Real-time data access (no latency)
--    - No ETL maintenance (simplified operations)
--    - Secure and governed (built-in access controls)
--
-- 10. Best practices:
--     - Use secure views for row-level filtering
--     - Monitor cross-region transfer costs
--     - Document share contents and update policies
--     - Test consumer access before production
--     - Leverage marketplace for external data enrichment
-- ============================================================================
