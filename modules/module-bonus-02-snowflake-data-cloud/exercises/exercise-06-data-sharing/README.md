# Exercise 06: Secure Data Sharing

## Overview
Master Snowflake's Data Sharing capabilities to securely distribute data to partners and consumers without copying data, implementing row-level security, and exploring the Snowflake Data Marketplace.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐ Intermediate
**Prerequisites**: Module 03 (SQL basics), understanding of data security concepts, Snowflake account (Standard or higher)

---

## Learning Objectives
By completing this exercise, you will be able to:
- Create and manage Snowflake shares
- Grant access to databases, schemas, tables, and views
- Implement secure views with row-level security
- Share data with external consumer accounts
- Monitor data sharing usage and costs
- Explore and utilize Snowflake Data Marketplace
- Implement column-level security with dynamic data masking

---

## Scenario
You're a SaaS analytics provider serving multiple client organizations. Each client should access their own analytics data without seeing other clients' data. Requirements:
- **Secure multi-tenancy**: Each client sees only their data
- **Zero data movement**: No copying data to client accounts
- **Real-time access**: Clients always see latest data
- **Cost tracking**: Monitor which clients consume compute
- **Governance**: Mask sensitive fields (PII)

Your goal is to implement a secure data sharing architecture using Snowflake shares and secure views.

---

## Requirements

### Task 1: Provider Setup (20 min)
Create a shared analytics database with sample customer metrics data.

**Create Shared Database**:
```sql
-- Use provider role
USE ROLE ACCOUNTADMIN;

-- Create database for sharing
CREATE OR REPLACE DATABASE shared_analytics
    COMMENT = 'Shared customer analytics for SaaS clients';

USE DATABASE shared_analytics;
USE SCHEMA public;
```

**Create Customer Metrics Table**:
```sql
CREATE OR REPLACE TABLE customer_metrics (
    metric_id INT AUTOINCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value FLOAT,
    metric_date DATE,
    category VARCHAR(50),

    -- Sensitive fields
    customer_email VARCHAR(200),
    revenue_usd DECIMAL(15,2),

    created_at TIMESTAMP DEFAULT current_timestamp()
);
```

**Load Sample Data** (10,000 rows for 5 customers):
```sql
INSERT INTO customer_metrics (customer_id, customer_name, metric_name, metric_value, metric_date, category, customer_email, revenue_usd)
SELECT
    'CUST_' || LPAD((uniform(1, 5, random()))::VARCHAR, 3, '0') as customer_id,
    CASE uniform(1, 5, random())
        WHEN 1 THEN 'Acme Corp'
        WHEN 2 THEN 'TechStart Inc'
        WHEN 3 THEN 'Global Solutions'
        WHEN 4 THEN 'CloudFirst LLC'
        ELSE 'DataDriven Co'
    END as customer_name,
    CASE uniform(1, 6, random())
        WHEN 1 THEN 'daily_active_users'
        WHEN 2 THEN 'session_duration'
        WHEN 3 THEN 'conversion_rate'
        WHEN 4 THEN 'churn_rate'
        WHEN 5 THEN 'customer_satisfaction'
        ELSE 'feature_adoption'
    END as metric_name,
    uniform(100, 10000, random()) / 100.0 as metric_value,
    dateadd(day, -uniform(1, 365, random()), current_date()) as metric_date,
    CASE uniform(1, 3, random())
        WHEN 1 THEN 'engagement'
        WHEN 2 THEN 'growth'
        ELSE 'retention'
    END as category,
    'contact@' || LOWER(customer_name) || '.com' as customer_email,
    uniform(1000, 50000, random()) as revenue_usd
FROM table(generator(rowcount => 10000));
```

**Verify Data Distribution**:
```sql
-- Check data by customer
SELECT
    customer_id,
    customer_name,
    COUNT(*) as metric_count,
    AVG(metric_value) as avg_value,
    AVG(revenue_usd) as avg_revenue
FROM customer_metrics
GROUP BY customer_id, customer_name
ORDER BY customer_id;

-- Sample records
SELECT * FROM customer_metrics LIMIT 20;
```

**Create Additional Supporting Objects**:
```sql
-- Aggregated view for quick insights
CREATE OR REPLACE VIEW customer_monthly_summary AS
SELECT
    customer_id,
    customer_name,
    DATE_TRUNC('month', metric_date) as month,
    metric_name,
    COUNT(*) as observations,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value
FROM customer_metrics
GROUP BY customer_id, customer_name, month, metric_name;

-- Query summary
SELECT * FROM customer_monthly_summary
WHERE customer_id = 'CUST_001'
ORDER BY month DESC, metric_name
LIMIT 10;
```

**Success Criteria**:
- ✅ `shared_analytics` database created
- ✅ `customer_metrics` table populated with 10,000+ rows
- ✅ Data distributed across 5 customers
- ✅ Sample data includes sensitive fields (email, revenue)
- ✅ Supporting view `customer_monthly_summary` created

---

### Task 2: Create Share (20 min)
Create a Snowflake share object and grant access to database objects.

**Create Share**:
```sql
-- Create share (ACCOUNTADMIN required)
USE ROLE ACCOUNTADMIN;

CREATE SHARE IF NOT EXISTS client_analytics
    COMMENT = 'Share customer analytics with external clients';

-- View shares
SHOW SHARES;

-- Describe share
DESC SHARE client_analytics;
```

**Grant Database Access**:
```sql
-- Grant usage on database
GRANT USAGE ON DATABASE shared_analytics
TO SHARE client_analytics;

-- Grant usage on schema
GRANT USAGE ON SCHEMA shared_analytics.public
TO SHARE client_analytics;

-- Show what's in share (should be empty - no tables/views yet)
SHOW GRANTS TO SHARE client_analytics;
```

**Grant Table Access**:
```sql
-- Option 1: Share raw table (NOT recommended - no security)
-- GRANT SELECT ON TABLE shared_analytics.public.customer_metrics TO SHARE client_analytics;

-- Option 2: Share through secure view (recommended)
-- We'll create secure view in next task

-- For now, share the monthly summary view
GRANT SELECT ON VIEW shared_analytics.public.customer_monthly_summary
TO SHARE client_analytics;

-- Verify grants
SHOW GRANTS TO SHARE client_analytics;
```

**Share Metadata**:
```sql
-- View share details
SELECT
    'client_analytics' as share_name,
    CURRENT_ACCOUNT() as provider_account,
    DATABASE_NAME,
    SCHEMA_NAME,
    NAME as object_name,
    PRIVILEGE
FROM table(result_scan(last_query_id()))
WHERE COMMAND = 'GRANT'
ORDER BY DATABASE_NAME, SCHEMA_NAME, NAME;
```

**Success Criteria**:
- ✅ Share `client_analytics` created
- ✅ USAGE granted on database and schema
- ✅ SELECT granted on monthly_summary view
- ✅ Share metadata visible via SHOW GRANTS
- ✅ No consumer accounts added yet

---

### Task 3: Secure Views (30 min)
Create secure views with row-level security and column masking.

**Create Account Mapping Table** (maps consumer accounts to customer_ids):
```sql
CREATE OR REPLACE TABLE customer_account_mapping (
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    snowflake_account VARCHAR(50),  -- Consumer account ID
    account_locator VARCHAR(50),    -- Consumer account locator
    created_at TIMESTAMP DEFAULT current_timestamp()
);

-- Insert mappings (using example account IDs - replace with real accounts)
INSERT INTO customer_account_mapping (customer_id, customer_name, snowflake_account, account_locator)
VALUES
    ('CUST_001', 'Acme Corp', 'ABC12345', 'xy12345.us-east-1'),
    ('CUST_002', 'TechStart Inc', 'XYZ67890', 'ab67890.us-west-2'),
    ('CUST_003', 'Global Solutions', 'DEF11111', 'cd11111.eu-west-1'),
    ('CUST_004', 'CloudFirst LLC', 'GHI22222', 'ef22222.us-east-1'),
    ('CUST_005', 'DataDriven Co', 'JKL33333', 'gh33333.ap-southeast-2');

SELECT * FROM customer_account_mapping;
```

**Create Secure View with Row-Level Security**:
```sql
CREATE OR REPLACE SECURE VIEW customer_metrics_filtered AS
SELECT
    metric_id,
    customer_id,
    customer_name,
    metric_name,
    metric_value,
    metric_date,
    category,

    -- Mask sensitive email field
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN customer_email
        ELSE REGEXP_REPLACE(customer_email, '^(.{3}).*(@.*)$', '\\1***\\2')  -- m***@example.com
    END as customer_email,

    -- Mask revenue (show range only)
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN revenue_usd
        ELSE FLOOR(revenue_usd / 10000) * 10000  -- Round to nearest $10K
    END as revenue_usd_range,

    created_at
FROM customer_metrics
WHERE customer_id IN (
    -- Row-level filter: only show data for consumer's customer_id
    SELECT customer_id
    FROM customer_account_mapping
    WHERE snowflake_account = CURRENT_ACCOUNT()
       OR account_locator = CURRENT_ACCOUNT()
);

-- Test as provider (sees all data)
SELECT CURRENT_ACCOUNT() as my_account;
SELECT COUNT(*) as total_records FROM customer_metrics_filtered;
-- Should return 10,000 rows (provider sees all)
```

**Create Simpler Filtered View** (alternative for specific customer):
```sql
-- Example: View for CUST_001 only
CREATE OR REPLACE SECURE VIEW customer_001_metrics AS
SELECT
    metric_id,
    customer_id,
    customer_name,
    metric_name,
    metric_value,
    metric_date,
    category
FROM customer_metrics
WHERE customer_id = 'CUST_001';

-- Verify
SELECT COUNT(*) FROM customer_001_metrics;
```

**Grant Secure View to Share**:
```sql
-- Add secure view to share
GRANT SELECT ON VIEW shared_analytics.public.customer_metrics_filtered
TO SHARE client_analytics;

-- Verify share contents
SHOW GRANTS TO SHARE client_analytics;
```

**Understanding SECURE Views**:
```sql
-- Regular view: Query plan visible (shows WHERE clause)
CREATE VIEW regular_view AS SELECT * FROM customer_metrics WHERE customer_id = 'CUST_001';

-- Secure view: Query plan hidden (protects filtering logic)
CREATE SECURE VIEW secure_view AS SELECT * FROM customer_metrics WHERE customer_id = 'CUST_001';

-- Show view definition (secure view definition is hidden from consumers)
SHOW VIEWS LIKE '%metrics%';
GET_DDL('VIEW', 'customer_metrics_filtered');
```

**Success Criteria**:
- ✅ Account mapping table created with 5 customer-account mappings
- ✅ Secure view `customer_metrics_filtered` implements row-level security
- ✅ Email field masked using REGEXP_REPLACE
- ✅ Revenue field bucketed to protect exact values
- ✅ WHERE clause filters by CURRENT_ACCOUNT()
- ✅ Secure view granted to share

---

### Task 4: Add Consumers (20 min)
Add consumer accounts to the share and document access setup.

**Add Consumer Accounts**:
```sql
-- Add consumer accounts to share
ALTER SHARE client_analytics
ADD ACCOUNTS = ABC12345;  -- Acme Corp

ALTER SHARE client_analytics
ADD ACCOUNTS = XYZ67890;  -- TechStart Inc

-- Add multiple at once
ALTER SHARE client_analytics
ADD ACCOUNTS = DEF11111, GHI22222, JKL33333;

-- View consumers
SHOW SHARES LIKE 'client_analytics';
DESC SHARE client_analytics;
```

**Document Consumer Setup Instructions**:
Create `consumer-setup-guide.md`:
```markdown
# Consumer Setup Guide

## Prerequisites
- Snowflake account (same cloud region as provider)
- ACCOUNTADMIN privileges

## Setup Steps

### 1. Create Database from Share
```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE client_analytics_db
FROM SHARE <provider_account>.client_analytics;
```

### 2. Grant Access to Roles
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE client_analytics_db
TO ROLE SYSADMIN;

GRANT IMPORTED PRIVILEGES ON DATABASE client_analytics_db
TO ROLE analyst_role;
```

### 3. Query Shared Data
```sql
USE DATABASE client_analytics_db;
USE SCHEMA public;

-- View available objects
SHOW TABLES;
SHOW VIEWS;

-- Query your metrics
SELECT * FROM customer_metrics_filtered
LIMIT 10;

-- Verify you only see your data
SELECT DISTINCT customer_id, customer_name
FROM customer_metrics_filtered;
```

### 4. Create Warehouse for Queries
```sql
-- Note: Consumers pay for compute (warehouse credits)
CREATE WAREHOUSE consumer_wh
WITH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

USE WAREHOUSE consumer_wh;
```

## Cost Notes
- **Provider**: No compute costs for shared data (zero-copy)
- **Consumer**: Pays for warehouse compute to query shared data
- **Storage**: Provider pays for storage, consumer doesn't

## Support
Contact: data-sharing@provider.com
```

**Verify Share Distribution**:
```sql
-- Query to see all consumers
SELECT
    'client_analytics' as share_name,
    DATABASE_NAME,
    object_name,
    consumer_accounts
FROM (
    SELECT
        DATABASE_NAME,
        NAME as object_name,
        ARRAY_AGG(DISTINCT grantee_name) as consumer_accounts
    FROM table(information_schema.object_privileges(
        USAGE_TYPE => 'shares'
    ))
    WHERE SHARE_NAME = 'client_analytics'
    GROUP BY DATABASE_NAME, NAME
);
```

**Remove Consumer** (if needed):
```sql
-- Remove access for specific account
ALTER SHARE client_analytics
REMOVE ACCOUNTS = ABC12345;

-- Consumer's database becomes inaccessible but not deleted
```

**Success Criteria**:
- ✅ 5 consumer accounts added to share
- ✅ Consumer account IDs documented
- ✅ Consumer setup guide created (consumer-setup-guide.md)
- ✅ Documented cost model (provider vs consumer)
- ✅ Tested removing and re-adding consumer

---

### Task 5: Consumer Access (25 min)
Simulate consumer experience by creating database from share (or document expected behavior).

**Simulated Consumer Setup** (if you have access to consumer account):
```sql
-- === IN CONSUMER ACCOUNT ===
USE ROLE ACCOUNTADMIN;

-- Create database from share
CREATE DATABASE client_analytics_shared
FROM SHARE <provider_account>.client_analytics;

-- Grant access
GRANT IMPORTED PRIVILEGES ON DATABASE client_analytics_shared
TO ROLE SYSADMIN;

USE ROLE SYSADMIN;
USE DATABASE client_analytics_shared;
USE SCHEMA public;

-- View available objects
SHOW TABLES;
SHOW VIEWS;

-- Query shared data
SELECT * FROM customer_metrics_filtered LIMIT 10;

-- Verify row-level security
SELECT
    customer_id,
    customer_name,
    COUNT(*) as my_metrics
FROM customer_metrics_filtered
GROUP BY customer_id, customer_name;
-- Should only see data for consumer's customer_id

-- Check monthly summary
SELECT * FROM customer_monthly_summary
WHERE month >= DATEADD(month, -3, CURRENT_DATE())
ORDER BY month DESC, metric_name;
```

**Consumer Limitations**:
```sql
-- === CONSUMER CANNOT: ===

-- 1. Create or modify objects in shared database
CREATE TABLE client_analytics_shared.public.my_table (id INT);
-- ERROR: Cannot create objects in shared database

-- 2. View secure view definition
GET_DDL('VIEW', 'customer_metrics_filtered');
-- Returns: Definition hidden for SECURE views

-- 3. See data for other customers
SELECT * FROM customer_metrics_filtered
WHERE customer_id = 'CUST_999';
-- Returns: 0 rows (filtered out)

-- === CONSUMER CAN: ===

-- 1. Query shared objects with their own warehouse
USE WAREHOUSE consumer_wh;
SELECT COUNT(*) FROM customer_metrics_filtered;

-- 2. Create views in their own database referencing shared data
USE DATABASE my_analytics;
CREATE VIEW my_analysis AS
SELECT
    metric_date,
    AVG(metric_value) as avg_daily_value
FROM client_analytics_shared.public.customer_metrics_filtered
GROUP BY metric_date;

-- 3. Join shared data with their own data
SELECT
    a.metric_date,
    a.metric_value,
    b.internal_notes
FROM client_analytics_shared.public.customer_metrics_filtered a
JOIN my_database.public.internal_data b
    ON a.metric_date = b.date;
```

**Document Consumer Experience**:
Create `consumer-experience.md`:
```markdown
# Consumer Experience Testing

## Access Verified
- ✅ Database created from share: client_analytics_shared
- ✅ Query permissions granted to SYSADMIN role
- ✅ Views visible: customer_metrics_filtered, customer_monthly_summary

## Data Access
- **Total records visible**: 2,147 (only CUST_001 data)
- **Customer ID**: CUST_001 (Acme Corp)
- **Date range**: Last 365 days
- **Metrics available**: 6 types (daily_active_users, session_duration, etc.)

## Security Observations
- ✅ Row-level filtering working (only see CUST_001)
- ✅ Email masking applied (m***@acmecorp.com)
- ✅ Revenue bucketed to $10K ranges
- ✅ Cannot see other customers' data
- ✅ Secure view definition hidden

## Performance
- **Query time**: 1.2 seconds for full dataset
- **Warehouse**: XSMALL (1 credit/hour)
- **Estimated monthly cost**: $48 (1hr/day * 30 days * $2/credit)

## Limitations Tested
- ❌ Cannot create tables in shared database
- ❌ Cannot modify shared views
- ❌ Cannot see raw customer_metrics table (not shared)
- ✅ Can create local views referencing shared data
- ✅ Can join shared data with own data
```

**Success Criteria**:
- ✅ Consumer database created from share (or documented)
- ✅ Verified consumer sees only their customer data (row-level security)
- ✅ Verified email and revenue masking visible
- ✅ Consumer limitations documented (cannot create objects)
- ✅ Created local view joining shared + own data
- ✅ consumer-experience.md document created

---

### Task 6: Monitoring & Marketplace (25 min)
Monitor data sharing usage and explore Snowflake Data Marketplace.

**Monitor Data Transfer**:
```sql
-- View data transferred to consumers
SELECT
    TO_DATE(start_time) as transfer_date,
    source_database,
    target_account_name,
    target_account_locator,
    SUM(bytes_transferred) / (1024*1024*1024) as gb_transferred,
    SUM(transfer_cost) as estimated_cost
FROM snowflake.account_usage.data_transfer_history
WHERE source_database = 'SHARED_ANALYTICS'
    AND start_time >= DATEADD(day, -30, current_timestamp())
GROUP BY transfer_date, source_database, target_account_name, target_account_locator
ORDER BY transfer_date DESC;
```

**Monitor Consumer Usage**:
```sql
-- Track which consumers are querying shared data
SELECT
    TO_DATE(start_time) as query_date,
    user_name,
    warehouse_name,
    query_type,
    database_name,
    COUNT(*) as query_count,
    SUM(total_elapsed_time) / 1000 as total_seconds,
    SUM(rows_produced) as total_rows
FROM snowflake.account_usage.query_history
WHERE database_name = 'SHARED_ANALYTICS'
    AND start_time >= DATEADD(day, -7, current_timestamp())
GROUP BY query_date, user_name, warehouse_name, query_type, database_name
ORDER BY query_date DESC, total_seconds DESC;
```

**Share Access Audit**:
```sql
-- Audit share access history
SELECT
    share_name,
    granted_on,
    granted_to,
    grantee_name,
    privilege,
    granted_by
FROM snowflake.account_usage.grants_to_shares
WHERE share_name = 'CLIENT_ANALYTICS'
ORDER BY granted_on DESC;

-- Active shares
SELECT
    name as share_name,
    owner,
    kind,
    database_name,
    comment,
    created_on,
    TO_ARRAY(consumer_accounts) as consumers
FROM snowflake.account_usage.shares
WHERE name = 'CLIENT_ANALYTICS';
```

**Usage Dashboard**:
```sql
CREATE OR REPLACE VIEW v_share_usage_dashboard AS
SELECT
    'client_analytics' as share_name,

    -- Consumer count
    (SELECT COUNT(DISTINCT target_account_name)
     FROM snowflake.account_usage.data_transfer_history
     WHERE source_database = 'SHARED_ANALYTICS'
       AND start_time >= DATEADD(day, -30, current_timestamp())) as active_consumers_30d,

    -- Data transferred (last 30 days)
    (SELECT SUM(bytes_transferred) / (1024*1024*1024)
     FROM snowflake.account_usage.data_transfer_history
     WHERE source_database = 'SHARED_ANALYTICS'
       AND start_time >= DATEADD(day, -30, current_timestamp())) as gb_transferred_30d,

    -- Most active consumer
    (SELECT target_account_name
     FROM snowflake.account_usage.data_transfer_history
     WHERE source_database = 'SHARED_ANALYTICS'
       AND start_time >= DATEADD(day, -30, current_timestamp())
     GROUP BY target_account_name
     ORDER BY SUM(bytes_transferred) DESC
     LIMIT 1) as top_consumer,

    -- Last access
    (SELECT MAX(start_time)
     FROM snowflake.account_usage.data_transfer_history
     WHERE source_database = 'SHARED_ANALYTICS') as last_access_time,

    current_timestamp() as report_time;

-- Query dashboard
SELECT * FROM v_share_usage_dashboard;
```

**Explore Snowflake Data Marketplace**:
```sql
-- List available data marketplace listings (ACCOUNTADMIN)
USE ROLE ACCOUNTADMIN;

-- Note: Use Snowflake UI to browse marketplace
-- Snowsight -> Data -> Marketplace

-- Document findings in markdown
```

**Create `marketplace-research.md`**:
```markdown
# Snowflake Data Marketplace Research

## Objective
Identify 3 relevant public datasets that could enhance our analytics platform.

## Dataset 1: Weather Data
- **Provider**: Weather Source
- **Name**: OnPoint Weather Data
- **Description**: Historical and real-time weather data, 3B+ daily observations
- **Use Case**: Correlate customer behavior with weather patterns
- **Cost**: Free tier available, premium from $2K/year
- **Relevance**: High - impacts retail and logistics clients

## Dataset 2: Economic Indicators
- **Provider**: Knoema
- **Name**: World Economic Indicators
- **Description**: GDP, unemployment, inflation data for 200+ countries
- **Use Case**: Macro economic analysis for B2B clients
- **Cost**: Free (public data)
- **Relevance**: Medium - useful for enterprise segment

## Dataset 3: COVID-19 Data
- **Provider**: Starschema
- **Name**: COVID-19 Epidemiological Data
- **Description**: Daily cases, deaths, testing data globally
- **Use Case**: Healthcare and public sector clients
- **Cost**: Free
- **Relevance**: Medium - declining relevance but good example

## How to Access Marketplace Data

### 1. Browse Marketplace
- Navigate to Snowsight -> Data -> Marketplace
- Search by category, provider, or keyword
- Filter by cost (Free, Paid)

### 2. Get Dataset
- Click "Get" on desired dataset
- Accept provider terms
- Choose database name
- Grant access to roles

### 3. Query Marketplace Data
```sql
-- Example: Query COVID data
USE DATABASE covid19_epidemiological_data;
SHOW SCHEMAS;
USE SCHEMA public;
SHOW TABLES;

SELECT * FROM <table_name> LIMIT 10;
```

## Monetization Potential
- Could create data marketplace listing for our aggregated analytics
- Anonymized benchmark data (opt-in from customers)
- Revenue share: 70% provider, 30% Snowflake
```

**Success Criteria**:
- ✅ Data transfer monitoring query working
- ✅ Consumer usage tracked (queries, bytes transferred)
- ✅ Share access audit query shows all grants
- ✅ Usage dashboard view created
- ✅ Explored 3+ Data Marketplace datasets
- ✅ marketplace-research.md document created
- ✅ Documented how to access and monetize marketplace data

---

## Hints

<details>
<summary>Hint 1: Creating Shares</summary>

```sql
-- Create share
CREATE SHARE my_share
    COMMENT = 'Description of what is shared';

-- Grant database access
GRANT USAGE ON DATABASE my_db TO SHARE my_share;
GRANT USAGE ON SCHEMA my_db.public TO SHARE my_share;

-- Grant object access
GRANT SELECT ON TABLE my_db.public.my_table TO SHARE my_share;
GRANT SELECT ON VIEW my_db.public.my_view TO SHARE my_share;

-- Add consumers
ALTER SHARE my_share ADD ACCOUNTS = ABC12345, XYZ67890;

-- Remove consumer
ALTER SHARE my_share REMOVE ACCOUNTS = ABC12345;

-- Drop share
DROP SHARE my_share;
```
</details>

<details>
<summary>Hint 2: Secure Views</summary>

```sql
-- Create secure view (definition hidden from consumers)
CREATE SECURE VIEW secure_customer_view AS
SELECT
    customer_id,
    metric_name,
    metric_value
FROM customer_metrics
WHERE customer_id = (
    -- Row-level security: filter by consumer account
    SELECT customer_id
    FROM account_mapping
    WHERE snowflake_account = CURRENT_ACCOUNT()
);

-- Regular view (definition visible to consumers)
CREATE VIEW regular_view AS SELECT * FROM table;

-- Get current account
SELECT CURRENT_ACCOUNT();  -- Returns account locator
SELECT CURRENT_ROLE();     -- Returns current role name

-- View definitions
GET_DDL('VIEW', 'secure_customer_view');  -- Hidden for SECURE views
```
</details>

<details>
<summary>Hint 3: Data Masking Techniques</summary>

```sql
-- Email masking
SELECT
    customer_email,
    REGEXP_REPLACE(customer_email, '^(.{3}).*(@.*)$', '\\1***\\2') as masked_email
    -- abc@example.com -> abc***@example.com
FROM customers;

-- Phone masking
SELECT
    phone,
    CONCAT('***-***-', RIGHT(phone, 4)) as masked_phone
    -- 555-123-4567 -> ***-***-4567
FROM customers;

-- Credit card masking
SELECT
    card_number,
    CONCAT('****-****-****-', RIGHT(card_number, 4)) as masked_card
FROM payments;

-- Value bucketing
SELECT
    revenue,
    FLOOR(revenue / 10000) * 10000 as revenue_bucket
    -- $23,456 -> $20,000
FROM customers;

-- Role-based unmasking
SELECT
    CASE
        WHEN CURRENT_ROLE() IN ('ADMIN', 'FINANCE') THEN revenue
        ELSE NULL
    END as revenue
FROM customers;
```
</details>

<details>
<summary>Hint 4: Consumer Database Setup</summary>

```sql
-- === IN CONSUMER ACCOUNT ===

-- Step 1: Create database from share
CREATE DATABASE shared_data
FROM SHARE <provider_account>.<share_name>;

-- Step 2: Grant access to roles
GRANT IMPORTED PRIVILEGES ON DATABASE shared_data TO ROLE SYSADMIN;

-- Step 3: Query shared data
USE DATABASE shared_data;
SHOW SCHEMAS;
SHOW TABLES;
SHOW VIEWS;

SELECT * FROM <view_name> LIMIT 10;

-- Note: Consumer cannot:
-- - Create objects in shared database
-- - Modify shared objects
-- - See secure view definitions

-- Consumer can:
-- - Query shared objects
-- - Create local views referencing shared data
-- - Join shared data with own data
```
</details>

<details>
<summary>Hint 5: Monitoring Queries</summary>

```sql
-- Data transfer by share
SELECT
    DATE(start_time) as date,
    source_cloud,
    source_region,
    target_account_name,
    SUM(bytes_transferred) / (1024*1024*1024) as gb_transferred
FROM snowflake.account_usage.data_transfer_history
WHERE source_database = 'MY_DATABASE'
    AND start_time >= DATEADD(day, -30, current_timestamp())
GROUP BY date, source_cloud, source_region, target_account_name
ORDER BY date DESC;

-- Shares and consumers
SELECT
    name as share_name,
    kind,  -- 'OUTBOUND' or 'INBOUND'
    database_name,
    comment,
    consumer_accounts
FROM table(result_scan(last_query_id()))
WHERE COMMAND = 'SHOW SHARES';

-- Object privileges in share
SELECT *
FROM snowflake.account_usage.grants_to_shares
WHERE share_name = 'MY_SHARE'
ORDER BY granted_on;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-06-data-sharing
bash validate.sh
```

**Expected Output**:
```
✅ Task 1: shared_analytics database with 10K+ customer metrics
✅ Task 2: Share client_analytics created with grants
✅ Task 3: Secure view with row-level security and masking
✅ Task 4: 5 consumer accounts added to share
✅ Task 5: Consumer experience documented
✅ Task 6: Monitoring queries working, 3 marketplace datasets documented

🎉 Exercise 06 Complete! Secure data sharing operational.
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All share, view, and grant commands
2. `consumer-setup-guide.md` - Complete consumer onboarding documentation
3. `consumer-experience.md` - Document consumer access testing
4. `marketplace-research.md` - 3 relevant marketplace datasets
5. `monitoring-queries.sql` - Saved monitoring and audit queries
6. Diagram: `data-sharing-model.mmd` - Mermaid diagram showing provider/consumer architecture

---

## Resources
- Snowflake Documentation: [Data Sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro)
- Snowflake Documentation: [Secure Views](https://docs.snowflake.com/en/user-guide/views-secure)
- Snowflake Documentation: [Data Marketplace](https://docs.snowflake.com/en/user-guide/data-marketplace)
- Notebook: `notebooks/06-data-sharing.sql`
- Diagram: `assets/diagrams/data-sharing-model.mmd`
- Theory: `theory/concepts.md#data-sharing`

---

## Next Steps
After completing this exercise:
- Explore Data Exchange (invite-only data sharing)
- Implement listing in Snowflake Data Marketplace
- Set up cross-cloud/cross-region sharing
- Integrate with Snowflake Data Clean Rooms for privacy-safe collaboration
- Build reader accounts for non-Snowflake consumers (paid feature)
