-- ============================================================================
-- Database Setup Script for CloudMart Data Lake
-- ============================================================================
-- This script creates the necessary databases and example table definitions
-- Run this in AWS Athena after your Glue crawlers have discovered the schema
-- ============================================================================

-- Create Bronze Database (if not exists from Terraform)
CREATE DATABASE IF NOT EXISTS cloudmart_bronze_dev
COMMENT 'Bronze layer - raw ingested data from source systems'
LOCATION 's3://your-bucket-prefix-cloudmart-raw-dev/';

-- Create Silver Database (if not exists from Terraform)
CREATE DATABASE IF NOT EXISTS cloudmart_silver_dev
COMMENT 'Silver layer - cleaned and validated data'
LOCATION 's3://your-bucket-prefix-cloudmart-processed-dev/';

-- Create Gold Database (if not exists from Terraform)
CREATE DATABASE IF NOT EXISTS cloudmart_gold_dev
COMMENT 'Gold layer - business-ready aggregated analytics'
LOCATION 's3://your-bucket-prefix-cloudmart-curated-dev/';

-- ============================================================================
-- Example Table Definitions (if crawlers haven't run yet)
-- ============================================================================

-- Bronze Orders Table
-- TODO: Update column definitions to match your actual data schema
CREATE EXTERNAL TABLE IF NOT EXISTS cloudmart_bronze_dev.orders (
  order_id STRING,
  customer_id STRING,
  order_date DATE,
  total_amount DOUBLE,
  status STRING,
  payment_method STRING,
  shipping_address STRING,
  processed_timestamp TIMESTAMP
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://your-bucket-prefix-cloudmart-raw-dev/orders/';

-- Bronze Customers Table
-- TODO: Complete the table definition
CREATE EXTERNAL TABLE IF NOT EXISTS cloudmart_bronze_dev.customers (
  customer_id STRING,
  email STRING,
  first_name STRING,
  last_name STRING,
  country STRING
  -- TODO: Add more columns as needed
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://your-bucket-prefix-cloudmart-raw-dev/customers/';

-- Silver Orders Table (partitioned by year/month)
-- TODO: Update to match your Silver schema with enrichments
CREATE EXTERNAL TABLE IF NOT EXISTS cloudmart_silver_dev.orders (
  order_id STRING,
  customer_id STRING,
  order_date DATE,
  total_amount DOUBLE,
  status STRING,
  processed_timestamp TIMESTAMP,
  is_high_value BOOLEAN,
  days_since_order INT
)
PARTITIONED BY (
  year INT,
  month INT
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://your-bucket-prefix-cloudmart-processed-dev/orders/';

-- Add partitions (run after data is loaded)
-- TODO: Update partition values based on your data
MSCK REPAIR TABLE cloudmart_silver_dev.orders;

-- Gold Sales Summary Table
-- TODO: Define aggregated sales metrics table
CREATE EXTERNAL TABLE IF NOT EXISTS cloudmart_gold_dev.sales_summary (
  order_date DATE,
  total_revenue DOUBLE,
  total_orders BIGINT,
  total_quantity BIGINT,
  avg_order_value DOUBLE,
  unique_customers BIGINT
)
PARTITIONED BY (
  year INT,
  month INT
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://your-bucket-prefix-cloudmart-curated-dev/sales_summary/';

-- Gold Customer 360 Table
-- TODO: Define customer analytics table
CREATE EXTERNAL TABLE IF NOT EXISTS cloudmart_gold_dev.customer_360 (
  customer_id STRING,
  email STRING,
  full_name STRING,
  country STRING,
  total_spent DOUBLE,
  total_orders BIGINT,
  avg_order_value DOUBLE,
  recency_days INT,
  frequency INT,
  monetary DOUBLE,
  rfm_segment STRING,
  favorite_category STRING
  -- TODO: Add more customer metrics
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://your-bucket-prefix-cloudmart-curated-dev/customer_360/';

-- ============================================================================
-- Useful Athena Commands
-- ============================================================================

-- Show all databases
SHOW DATABASES;

-- Show tables in a database
SHOW TABLES IN cloudmart_bronze_dev;

-- Describe table schema
DESCRIBE cloudmart_silver_dev.orders;

-- Show table properties
SHOW CREATE TABLE cloudmart_silver_dev.orders;

-- Show partitions
SHOW PARTITIONS cloudmart_silver_dev.orders;

-- Repair table partitions (discover new partitions)
MSCK REPAIR TABLE cloudmart_silver_dev.orders;

-- Drop table (careful!)
-- DROP TABLE IF EXISTS cloudmart_bronze_dev.temp_table;

-- ============================================================================
-- Data Quality Checks
-- ============================================================================

-- Check record counts per table
SELECT 'bronze_orders' as table_name, COUNT(*) as record_count
FROM cloudmart_bronze_dev.orders
UNION ALL
SELECT 'silver_orders', COUNT(*)
FROM cloudmart_silver_dev.orders
UNION ALL
SELECT 'bronze_customers', COUNT(*)
FROM cloudmart_bronze_dev.customers;

-- Check for nulls in key columns
SELECT
  COUNT(*) as total_records,
  COUNT(order_id) as non_null_order_id,
  COUNT(customer_id) as non_null_customer_id,
  COUNT(*) - COUNT(order_id) as null_order_id_count
FROM cloudmart_bronze_dev.orders;

-- Check data freshness
SELECT
  MAX(processed_timestamp) as latest_processed,
  MIN(processed_timestamp) as earliest_processed,
  DATE_DIFF('hour', MIN(processed_timestamp), MAX(processed_timestamp)) as hours_span
FROM cloudmart_bronze_dev.orders;

-- ============================================================================
-- Performance Optimization Tips
-- ============================================================================

-- 1. Always use partition filters when querying partitioned tables:
--    WHERE year = 2024 AND month = 3

-- 2. Use LIMIT for exploratory queries:
--    SELECT * FROM large_table LIMIT 100;

-- 3. Use columnar formats (Parquet) and compression

-- 4. Avoid SELECT * - specify only needed columns

-- 5. Use approximate functions for large datasets:
--    SELECT approx_distinct(customer_id) FROM orders;

-- ============================================================================
-- Notes
-- ============================================================================
-- - Replace 'your-bucket-prefix' with your actual S3 bucket prefix
-- - Update database names if you changed the environment variable
-- - Run MSCK REPAIR TABLE after loading new partitioned data
-- - These table definitions may be automatically created by Glue Crawlers
-- ============================================================================
