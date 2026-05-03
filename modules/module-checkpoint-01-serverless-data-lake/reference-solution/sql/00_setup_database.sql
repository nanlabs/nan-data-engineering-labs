-- ============================================================================
-- CloudMart Data Lake Setup Script
-- ============================================================================
-- Purpose: Initialize the CloudMart data lake database and external tables
-- Author: Data Engineering Team
-- Version: 1.0
-- Last Modified: 2024-03-09
-- ============================================================================

-- ============================================================================
-- SECTION 1: DATABASE SETUP
-- ============================================================================

-- Create the main database for CloudMart data lake
CREATE DATABASE IF NOT EXISTS cloudmart_data_lake
COMMENT 'CloudMart Serverless Data Lake - Bronze, Silver, Gold zones'
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/';

-- Use the database for subsequent operations
USE cloudmart_data_lake;

-- ============================================================================
-- SECTION 2: BRONZE ZONE - RAW DATA TABLES
-- ============================================================================
-- Bronze zone contains raw, unprocessed data ingested from source systems
-- Data is stored in its original format with minimal transformation

-- ----------------------------------------------------------------------------
-- Table: raw_orders
-- Description: Raw order transactions from e-commerce system
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS raw_orders (
    order_id STRING COMMENT 'Unique order identifier',
    customer_id STRING COMMENT 'Customer identifier',
    order_date STRING COMMENT 'Order placement date',
    total_amount DOUBLE COMMENT 'Total order amount in USD',
    status STRING COMMENT 'Order status (completed, pending, cancelled)',
    products STRING COMMENT 'JSON array of products in order',
    ingestion_timestamp STRING COMMENT 'Raw data ingestion timestamp'
)
COMMENT 'Raw orders data from source system'
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
   "separatorChar" = ",",
   "quoteChar"     = "\"",
   "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/bronze/orders/';

-- ----------------------------------------------------------------------------
-- Table: raw_customers
-- Description: Raw customer master data
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS raw_customers (
    customer_id STRING COMMENT 'Unique customer identifier',
    name STRING COMMENT 'Customer full name',
    email STRING COMMENT 'Customer email address',
    country STRING COMMENT 'Customer country code',
    city STRING COMMENT 'Customer city',
    signup_date STRING COMMENT 'Customer registration date',
    segment STRING COMMENT 'Customer segment (Premium, Standard, Basic)',
    ingestion_timestamp STRING COMMENT 'Raw data ingestion timestamp'
)
COMMENT 'Raw customer data from CRM system'
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
   "separatorChar" = ",",
   "quoteChar"     = "\"",
   "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/bronze/customers/';

-- ----------------------------------------------------------------------------
-- Table: raw_products
-- Description: Raw product catalog data
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS raw_products (
    product_id STRING COMMENT 'Unique product identifier',
    name STRING COMMENT 'Product name',
    category STRING COMMENT 'Product category',
    price DOUBLE COMMENT 'Product price in USD',
    stock_quantity INT COMMENT 'Available stock quantity',
    ingestion_timestamp STRING COMMENT 'Raw data ingestion timestamp'
)
COMMENT 'Raw product catalog from inventory system'
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
   "separatorChar" = ",",
   "quoteChar"     = "\"",
   "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/bronze/products/';

-- ----------------------------------------------------------------------------
-- Table: raw_events
-- Description: Raw clickstream and user behavior events
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS raw_events (
    event_id STRING COMMENT 'Unique event identifier',
    user_id STRING COMMENT 'User/customer identifier',
    event_type STRING COMMENT 'Type of event (page_view, add_to_cart, purchase, logout)',
    event_timestamp STRING COMMENT 'Event occurrence timestamp',
    properties STRING COMMENT 'JSON properties of the event',
    ingestion_timestamp STRING COMMENT 'Raw data ingestion timestamp'
)
COMMENT 'Raw clickstream events from web analytics'
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
   "separatorChar" = ",",
   "quoteChar"     = "\"",
   "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/bronze/events/';

-- ============================================================================
-- SECTION 3: SILVER ZONE - CLEANED AND ENRICHED DATA
-- ============================================================================
-- Silver zone contains validated, cleaned, and conformed data
-- Data quality rules applied, type conversions performed

-- ----------------------------------------------------------------------------
-- Table: processed_orders
-- Description: Cleaned and validated orders
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS processed_orders (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    order_timestamp TIMESTAMP,
    total_amount DECIMAL(10,2),
    status STRING,
    product_count INT,
    processing_timestamp TIMESTAMP
)
COMMENT 'Cleaned and validated orders'
PARTITIONED BY (year INT, month INT)
STORED AS PARQUET
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/silver/orders/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- ----------------------------------------------------------------------------
-- Table: processed_customers
-- Description: Cleaned and enriched customer data
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS processed_customers (
    customer_id STRING,
    name STRING,
    email STRING,
    country STRING,
    city STRING,
    signup_date DATE,
    segment STRING,
    lifetime_value DECIMAL(10,2),
    processing_timestamp TIMESTAMP
)
COMMENT 'Cleaned customer master data'
PARTITIONED BY (year INT, month INT)
STORED AS PARQUET
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/silver/customers/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- ----------------------------------------------------------------------------
-- Table: processed_products
-- Description: Cleaned product catalog
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS processed_products (
    product_id STRING,
    name STRING,
    category STRING,
    price DECIMAL(10,2),
    stock_quantity INT,
    is_active BOOLEAN,
    processing_timestamp TIMESTAMP
)
COMMENT 'Cleaned product catalog'
PARTITIONED BY (year INT, month INT)
STORED AS PARQUET
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/silver/products/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- ============================================================================
-- SECTION 4: GOLD ZONE - BUSINESS-READY AGGREGATED DATA
-- ============================================================================
-- Gold zone contains pre-aggregated, business-ready datasets
-- Optimized for specific analytical use cases and reporting

-- ----------------------------------------------------------------------------
-- Table: sales_summary
-- Description: Daily sales metrics and KPIs
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS sales_summary (
    order_date DATE,
    total_orders INT,
    total_revenue DECIMAL(12,2),
    avg_order_value DECIMAL(10,2),
    unique_customers INT,
    completed_orders INT,
    cancelled_orders INT,
    pending_orders INT,
    top_category STRING,
    top_product STRING,
    calculation_timestamp TIMESTAMP
)
COMMENT 'Daily aggregated sales metrics'
PARTITIONED BY (year INT, month INT)
STORED AS PARQUET
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/gold/sales_summary/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- ----------------------------------------------------------------------------
-- Table: customer_360
-- Description: Comprehensive customer analytics
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS customer_360 (
    customer_id STRING,
    name STRING,
    email STRING,
    country STRING,
    segment STRING,
    signup_date DATE,
    total_orders INT,
    total_spent DECIMAL(12,2),
    avg_order_value DECIMAL(10,2),
    first_order_date DATE,
    last_order_date DATE,
    days_since_last_order INT,
    favorite_category STRING,
    is_active BOOLEAN,
    churn_risk STRING,
    calculation_timestamp TIMESTAMP
)
COMMENT 'Comprehensive customer 360 view'
STORED AS PARQUET
LOCATION 's3://cloudmart-data-lake-${account_id}-${region}/gold/customer_360/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- ============================================================================
-- SECTION 5: PARTITION DISCOVERY
-- ============================================================================
-- Discover and register partitions for all partitioned tables

-- Discover partitions for Bronze tables
MSCK REPAIR TABLE raw_orders;
MSCK REPAIR TABLE raw_customers;
MSCK REPAIR TABLE raw_products;
MSCK REPAIR TABLE raw_events;

-- Discover partitions for Silver tables
MSCK REPAIR TABLE processed_orders;
MSCK REPAIR TABLE processed_customers;
MSCK REPAIR TABLE processed_products;

-- Discover partitions for Gold tables
MSCK REPAIR TABLE sales_summary;

-- ============================================================================
-- SECTION 6: VERIFICATION QUERIES
-- ============================================================================

-- Verify database and table creation
SHOW TABLES IN cloudmart_data_lake;

-- Display table schemas
DESCRIBE FORMATTED raw_orders;
DESCRIBE FORMATTED processed_orders;
DESCRIBE FORMATTED sales_summary;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. Replace ${account_id} and ${region} with your AWS account ID and region
-- 2. Ensure S3 buckets exist before running this script
-- 3. Run from AWS Athena console or AWS CLI
-- 4. After data ingestion, run MSCK REPAIR TABLE to discover partitions
-- 5. Verify table creation with SHOW TABLES and DESCRIBE commands
--
-- Example AWS CLI usage:
-- aws athena start-query-execution \
--   --query-string file://00_setup_database.sql \
--   --result-configuration OutputLocation=s3://athena-results-bucket/ \
--   --query-execution-context Database=default
-- ============================================================================
