-- =============================================================================
-- TABLE OPTIMIZATION & MAINTENANCE QUERIES - Enterprise Data Lakehouse
-- =============================================================================
-- Purpose: Maintenance queries for Athena/Delta Lake including OPTIMIZE,
--          VACUUM, statistics updates, partition management, and compaction
-- Database: lakehouse_gold, lakehouse_silver, lakehouse_bronze
-- Compatible: Amazon Athena (Iceberg), Delta Lake, AWS Glue
-- =============================================================================

-- NOTE: Some commands are Delta Lake specific, others are Iceberg/Athena specific
-- Adjust based on your table format (Delta, Iceberg, Parquet, etc.)

-- =============================================================================
-- SECTION 1: OPTIMIZE Commands for Gold Layer Tables (Delta Lake)
-- =============================================================================

-- =============================================================================
-- OPTIMIZE 1: fact_transactions - Critical fact table
-- =============================================================================
-- Purpose: Compact small files, optimize for query performance
-- Frequency: Daily
-- =============================================================================

-- Delta Lake OPTIMIZE command
OPTIMIZE lakehouse_gold.fact_transactions
ZORDER BY (transaction_date, customer_sk, product_sk);

-- Iceberg/Athena alternative (manual compaction query)
-- CREATE TABLE lakehouse_gold.fact_transactions_optimized
-- WITH (
--     format = 'PARQUET',
--     partitioned_by = ARRAY['year', 'month'],
--     bucketed_by = ARRAY['customer_sk'],
--     bucket_count = 16
-- )
-- AS SELECT * FROM lakehouse_gold.fact_transactions;

-- =============================================================================
-- OPTIMIZE 2: dim_customer - SCD Type 2 dimension
-- =============================================================================
-- Purpose: Optimize customer dimension with historical tracking
-- Frequency: Weekly
-- =============================================================================

OPTIMIZE lakehouse_gold.dim_customer
ZORDER BY (customer_id, effective_date, is_current);

-- Partition statistics for query planning
ANALYZE TABLE lakehouse_gold.dim_customer COMPUTE STATISTICS;

-- =============================================================================
-- OPTIMIZE 3: dim_product - Product catalog
-- =============================================================================
-- Purpose: Optimize product dimension for fast lookups
-- Frequency: Weekly
-- =============================================================================

OPTIMIZE lakehouse_gold.dim_product
ZORDER BY (product_id, category, brand);

-- =============================================================================
-- OPTIMIZE 4: dim_date - Date dimension
-- =============================================================================
-- Purpose: Optimize date dimension (rarely changes but heavily queried)
-- Frequency: Monthly or after updates
-- =============================================================================

OPTIMIZE lakehouse_gold.dim_date
ZORDER BY (date, year, month, quarter);

-- =============================================================================
-- OPTIMIZE 5: daily_metrics - Aggregated metrics table
-- =============================================================================
-- Purpose: Optimize pre-aggregated metrics for dashboard queries
-- Frequency: Daily
-- =============================================================================

OPTIMIZE lakehouse_gold.daily_metrics
ZORDER BY (metric_date, category, customer_segment);

-- =============================================================================
-- SECTION 2: VACUUM Commands - Remove Old Versions
-- =============================================================================

-- =============================================================================
-- VACUUM 1: fact_transactions - Remove old versions (7-day retention)
-- =============================================================================
-- Purpose: Clean up old file versions to save storage costs
-- WARNING: Cannot time-travel beyond retention period after VACUUM
-- =============================================================================

-- Set retention to 7 days (168 hours)
VACUUM lakehouse_gold.fact_transactions RETAIN 168 HOURS;

-- Dry run to see what would be deleted
-- VACUUM lakehouse_gold.fact_transactions RETAIN 168 HOURS DRY RUN;

-- =============================================================================
-- VACUUM 2: dim_customer - Longer retention for audit
-- =============================================================================
-- Purpose: Retain 30 days for SCD history and audit requirements
-- =============================================================================

VACUUM lakehouse_gold.dim_customer RETAIN 720 HOURS;

-- =============================================================================
-- VACUUM 3: dim_product - Standard retention
-- =============================================================================
VACUUM lakehouse_gold.dim_product RETAIN 168 HOURS;

-- =============================================================================
-- VACUUM 4: Silver layer tables - Aggressive cleanup
-- =============================================================================
-- Purpose: Silver layer used for transformation, less retention needed
-- =============================================================================

VACUUM lakehouse_silver.transactions_silver RETAIN 72 HOURS;
VACUUM lakehouse_silver.customers_silver RETAIN 72 HOURS;
VACUUM lakehouse_silver.products_silver RETAIN 72 HOURS;

-- =============================================================================
-- SECTION 3: UPDATE STATISTICS - Table and Column Statistics
-- =============================================================================

-- =============================================================================
-- STATS 1: Comprehensive statistics for fact_transactions
-- =============================================================================
-- Purpose: Update statistics for better query planning and optimization
-- =============================================================================

-- Analyze entire table
ANALYZE TABLE lakehouse_gold.fact_transactions COMPUTE STATISTICS;

-- Analyze specific columns for better selectivity estimates
ANALYZE TABLE lakehouse_gold.fact_transactions COMPUTE STATISTICS FOR COLUMNS
    customer_sk, product_sk, date_sk, net_amount, quantity, profit_margin;

-- For partitioned tables, analyze partitions
-- ANALYZE TABLE lakehouse_gold.fact_transactions
-- PARTITION (year='2024', month='03') COMPUTE STATISTICS;

-- =============================================================================
-- STATS 2: Statistics for dimension tables
-- =============================================================================

ANALYZE TABLE lakehouse_gold.dim_customer COMPUTE STATISTICS;
ANALYZE TABLE lakehouse_gold.dim_customer COMPUTE STATISTICS FOR COLUMNS
    customer_id, customer_segment, state, country, loyalty_tier;

ANALYZE TABLE lakehouse_gold.dim_product COMPUTE STATISTICS;
ANALYZE TABLE lakehouse_gold.dim_product COMPUTE STATISTICS FOR COLUMNS
    product_id, category, subcategory, brand, status;

ANALYZE TABLE lakehouse_gold.dim_date COMPUTE STATISTICS;
ANALYZE TABLE lakehouse_gold.dim_date COMPUTE STATISTICS FOR COLUMNS
    date, year, month, quarter, day_of_week;

-- =============================================================================
-- STATS 3: View statistics summary
-- =============================================================================
-- Purpose: Review current statistics to identify stale stats
-- =============================================================================

-- Show table statistics
DESCRIBE EXTENDED lakehouse_gold.fact_transactions;

-- Show column statistics
DESCRIBE FORMATTED lakehouse_gold.fact_transactions customer_sk;

-- =============================================================================
-- SECTION 4: MSCK REPAIR TABLE - Partition Discovery
-- =============================================================================

-- =============================================================================
-- REPAIR 1: Discover new partitions in fact table
-- =============================================================================
-- Purpose: Add newly written partitions to Hive metastore
-- Use when external processes write data directly to S3
-- =============================================================================

MSCK REPAIR TABLE lakehouse_gold.fact_transactions;

-- Alternative: Add specific partition
-- ALTER TABLE lakehouse_gold.fact_transactions
-- ADD IF NOT EXISTS PARTITION (year='2024', month='03');

-- =============================================================================
-- REPAIR 2: Recover partitions for dimension tables
-- =============================================================================

MSCK REPAIR TABLE lakehouse_gold.dim_customer;
MSCK REPAIR TABLE lakehouse_gold.dim_product;

-- =============================================================================
-- REPAIR 3: Silver layer partition discovery
-- =============================================================================

MSCK REPAIR TABLE lakehouse_silver.transactions_silver;
MSCK REPAIR TABLE lakehouse_silver.customers_silver;
MSCK REPAIR TABLE lakehouse_silver.products_silver;

-- =============================================================================
-- SECTION 5: Compaction Strategies by Table Size
-- =============================================================================

-- =============================================================================
-- COMPACT 1: Large fact tables (>1TB) - Incremental compaction
-- =============================================================================
-- Purpose: Compact only recent partitions to minimize impact
-- =============================================================================

-- Compact last 7 days of data
OPTIMIZE lakehouse_gold.fact_transactions
WHERE transaction_date >= DATE_ADD('day', -7, CURRENT_DATE)
ZORDER BY (transaction_date, customer_sk);

-- =============================================================================
-- COMPACT 2: Medium tables (100GB-1TB) - Selective compaction
-- =============================================================================
-- Purpose: Compact when file count exceeds threshold
-- =============================================================================

-- Check file count first
-- SELECT COUNT(*) AS file_count
-- FROM file_metadata('lakehouse_gold.daily_metrics');

-- Compact if needed
OPTIMIZE lakehouse_gold.daily_metrics
WHERE metric_date >= DATE_ADD('month', -1, CURRENT_DATE);

-- =============================================================================
-- COMPACT 3: Small tables (<100GB) - Full table compaction
-- =============================================================================
-- Purpose: Full optimization for smaller dimension tables
-- =============================================================================

-- Dimensions can be fully optimized
OPTIMIZE lakehouse_gold.dim_customer;
OPTIMIZE lakehouse_gold.dim_product;
OPTIMIZE lakehouse_gold.dim_date;

-- =============================================================================
-- COMPACT 4: Compaction with file size targets
-- =============================================================================
-- Purpose: Optimize file sizes for better query performance
-- Target: 256MB-1GB per file for best query performance
-- =============================================================================

-- Delta Lake: Configure target file size
-- ALTER TABLE lakehouse_gold.fact_transactions
-- SET TBLPROPERTIES ('delta.targetFileSize' = '1073741824'); -- 1GB

-- Then optimize
OPTIMIZE lakehouse_gold.fact_transactions;

-- =============================================================================
-- SECTION 6: Advanced Optimization - Z-Ordering Strategies
-- =============================================================================

-- =============================================================================
-- ZORDER 1: Multi-column Z-ordering for fact table
-- =============================================================================
-- Purpose: Optimize for common query patterns (date range + customer/product filters)
-- =============================================================================

OPTIMIZE lakehouse_gold.fact_transactions
ZORDER BY (transaction_date, customer_sk, product_sk, net_amount);

-- =============================================================================
-- ZORDER 2: Dimension tables with frequently filtered columns
-- =============================================================================

-- Customer dimension: optimize for segment and location queries
OPTIMIZE lakehouse_gold.dim_customer
ZORDER BY (customer_segment, state, country, loyalty_tier);

-- Product dimension: optimize for category and brand queries
OPTIMIZE lakehouse_gold.dim_product
ZORDER BY (category, brand, status);

-- =============================================================================
-- SECTION 7: Partition Management
-- =============================================================================

-- =============================================================================
-- PARTITION 1: Drop old partitions (data retention compliance)
-- =============================================================================
-- Purpose: Remove data beyond retention period (e.g., 7 years)
-- =============================================================================

-- Check partition age first
SELECT
    year,
    month,
    COUNT(*) AS record_count,
    MAX(transaction_date) AS latest_transaction,
    DATE_DIFF('day', MAX(transaction_date), CURRENT_DATE) AS days_old
FROM lakehouse_gold.fact_transactions
GROUP BY year, month
HAVING DATE_DIFF('day', MAX(transaction_date), CURRENT_DATE) > 2555  -- 7 years
ORDER BY year, month;

-- Drop old partitions beyond retention
-- ALTER TABLE lakehouse_gold.fact_transactions
-- DROP IF EXISTS PARTITION (year='2017', month='01');

-- =============================================================================
-- PARTITION 2: Archive old partitions to Glacier
-- =============================================================================
-- Purpose: Move old data to cheaper storage tier
-- This would typically be done via S3 lifecycle policies, not SQL
-- =============================================================================

-- Query to identify partitions for archival
SELECT
    's3://lakehouse-gold-bucket/gold/fact_transactions/year=' || year || '/month=' || month AS partition_path,
    year,
    month,
    COUNT(*) AS record_count,
    SUM(bytes) AS partition_size_bytes,
    DATE_DIFF('day', MAX(transaction_date), CURRENT_DATE) AS days_old,
    CASE
        WHEN DATE_DIFF('day', MAX(transaction_date), CURRENT_DATE) > 2190 THEN 'Glacier Deep Archive'
        WHEN DATE_DIFF('day', MAX(transaction_date), CURRENT_DATE) > 1095 THEN 'Glacier'
        WHEN DATE_DIFF('day', MAX(transaction_date), CURRENT_DATE) > 365 THEN 'Intelligent-Tiering'
        ELSE 'Standard/Infrequent Access'
    END AS recommended_storage_class
FROM (
    SELECT
        year,
        month,
        transaction_date,
        1024 AS bytes  -- Placeholder, would come from file metadata
    FROM lakehouse_gold.fact_transactions
) partition_metadata
GROUP BY year, month
ORDER BY days_old DESC;

-- =============================================================================
-- PARTITION 3: Partition pruning effectiveness check
-- =============================================================================
-- Purpose: Verify that queries are properly pruning partitions
-- =============================================================================

-- Check partition scan for a typical query
EXPLAIN
SELECT
    customer_sk,
    SUM(net_amount) AS total_spent
FROM lakehouse_gold.fact_transactions
WHERE transaction_date >= DATE_ADD('day', -30, CURRENT_DATE)
GROUP BY customer_sk;

-- =============================================================================
-- SECTION 8: File Management & Small File Compaction
-- =============================================================================

-- =============================================================================
-- FILE 1: Identify small file problem
-- =============================================================================
-- Purpose: Find tables with too many small files (< 134MB)
-- =============================================================================

-- Query to analyze file sizes (example for CloudWatch/S3 inventory)
WITH file_inventory AS (
    SELECT
        'fact_transactions' AS table_name,
        's3://lakehouse-gold-bucket/gold/fact_transactions/' AS table_path,
        1000 AS file_count,  -- Would come from actual S3 inventory
        524288000 AS total_bytes,  -- 500MB
        524288 AS avg_file_size_bytes  -- 500KB
)
SELECT
    table_name,
    file_count,
    total_bytes / (1024*1024*1024) AS total_size_gb,
    avg_file_size_bytes / (1024*1024) AS avg_file_size_mb,
    CASE
        WHEN avg_file_size_bytes < 134217728 THEN 'Small File Problem - Needs Compaction'
        WHEN avg_file_size_bytes < 268435456 THEN 'Acceptable - Consider Compaction'
        WHEN avg_file_size_bytes < 1073741824 THEN 'Optimal'
        ELSE 'Large Files - Consider Splitting'
    END AS file_size_assessment,
    -- Estimated query cost impact
    CASE
        WHEN file_count > 10000 THEN 'High Cost - Many S3 list operations'
        WHEN file_count > 1000 THEN 'Moderate Cost'
        ELSE 'Low Cost'
    END AS query_cost_impact
FROM file_inventory;

-- =============================================================================
-- FILE 2: Compact small files by partition
-- =============================================================================

-- Compact specific partition with many small files
OPTIMIZE lakehouse_gold.fact_transactions
WHERE transaction_date = DATE '2024-03-01';

-- =============================================================================
-- SECTION 9: Bloom Filter Optimization (Delta Lake)
-- =============================================================================

-- =============================================================================
-- BLOOM 1: Create bloom filter indexes for high-cardinality columns
-- =============================================================================
-- Purpose: Speed up point lookups on columns like IDs
-- =============================================================================

-- Enable bloom filter for customer lookups
CREATE BLOOMFILTER INDEX idx_customer
ON TABLE lakehouse_gold.fact_transactions
FOR COLUMNS (customer_sk)
OPTIONS (fpp = 0.01, numItems = 10000000);

-- Enable bloom filter for product lookups
CREATE BLOOMFILTER INDEX idx_product
ON TABLE lakehouse_gold.fact_transactions
FOR COLUMNS (product_sk)
OPTIONS (fpp = 0.01, numItems = 1000000);

-- =============================================================================
-- SECTION 10: Data Skipping Indexes (Delta Lake)
-- =============================================================================

-- =============================================================================
-- SKIP 1: Create min/max statistics for range queries
-- =============================================================================
-- Purpose: Skip files that don't contain values in query range
-- =============================================================================

-- This happens automatically with Delta Lake, but can be verified:
-- DESCRIBE DETAIL lakehouse_gold.fact_transactions;

-- =============================================================================
-- SECTION 11: Materialized View Refresh
-- =============================================================================

-- =============================================================================
-- REFRESH 1: Refresh aggregated views
-- =============================================================================
-- Purpose: Update materialized views for dashboard queries
-- =============================================================================

-- For Iceberg materialized views
-- REFRESH MATERIALIZED VIEW lakehouse_gold.mv_daily_revenue_summary;
-- REFRESH MATERIALIZED VIEW lakehouse_gold.mv_customer_lifetime_value;

-- =============================================================================
-- SECTION 12: Table Health Monitoring Queries
-- =============================================================================

-- =============================================================================
-- HEALTH 1: Table size and growth monitoring
-- =============================================================================

SELECT
    table_schema,
    table_name,
    SUM(bytes) / (1024*1024*1024) AS size_gb,
    COUNT(*) AS row_count,
    COUNT(DISTINCT partition_key) AS partition_count,
    AVG(bytes) AS avg_row_size_bytes,
    MIN(created_time) AS oldest_data,
    MAX(created_time) AS newest_data
FROM information_schema.tables t
INNER JOIN information_schema.partitions p ON t.table_name = p.table_name
WHERE table_schema = 'lakehouse_gold'
    AND table_type = 'BASE TABLE'
GROUP BY table_schema, table_name
ORDER BY size_gb DESC;

-- =============================================================================
-- HEALTH 2: Identify tables needing optimization
-- =============================================================================

WITH table_metrics AS (
    SELECT
        'fact_transactions' AS table_name,
        COUNT(*) AS file_count,
        SUM(file_size) AS total_size,
        AVG(file_size) AS avg_file_size,
        MIN(file_size) AS min_file_size,
        MAX(file_size) AS max_file_size,
        MAX(last_modified) AS last_optimized
    FROM delta_table_files('lakehouse_gold.fact_transactions')
    GROUP BY table_name
)
SELECT
    table_name,
    file_count,
    total_size / (1024*1024*1024) AS total_size_gb,
    avg_file_size / (1024*1024) AS avg_file_size_mb,
    min_file_size / (1024*1024) AS min_file_size_mb,
    max_file_size / (1024*1024) AS max_file_size_mb,
    DATE_DIFF('day', last_optimized, CURRENT_TIMESTAMP) AS days_since_optimization,
    -- Optimization recommendation
    CASE
        WHEN file_count > 10000 THEN 'CRITICAL: Too many files, compact immediately'
        WHEN avg_file_size < 134217728 THEN 'HIGH: Small files detected, compact soon'
        WHEN DATE_DIFF('day', last_optimized, CURRENT_TIMESTAMP) > 7 THEN 'MEDIUM: Regular maintenance needed'
        ELSE 'LOW: Table is healthy'
    END AS optimization_priority,
    -- Recommended action
    CASE
        WHEN file_count > 10000 THEN 'Run OPTIMIZE with WHERE clause for incremental compaction'
        WHEN avg_file_size < 134217728 THEN 'Run full OPTIMIZE with ZORDER'
        WHEN DATE_DIFF('day', last_optimized, CURRENT_TIMESTAMP) > 7 THEN 'Schedule routine OPTIMIZE'
        ELSE 'No action needed'
    END AS recommended_action
FROM table_metrics;

-- =============================================================================
-- HEALTH 3: Query performance metrics
-- =============================================================================

-- Analyze query performance (from query logs)
SELECT
    query_date,
    table_name,
    COUNT(*) AS query_count,
    AVG(query_duration_seconds) AS avg_duration,
    MAX(query_duration_seconds) AS max_duration,
    AVG(bytes_scanned / (1024*1024*1024)) AS avg_data_scanned_gb,
    AVG(bytes_scanned / NULLIF(bytes_returned, 0)) AS scan_efficiency_ratio
FROM query_execution_logs
WHERE table_name IN ('fact_transactions', 'dim_customer', 'dim_product')
    AND query_date >= DATE_ADD('day', -7, CURRENT_DATE)
GROUP BY query_date, table_name
HAVING avg_duration > 10  -- Queries taking more than 10 seconds
ORDER BY avg_duration DESC;

-- =============================================================================
-- SECTION 13: Automated Maintenance Script Recommendations
-- =============================================================================

-- =============================================================================
-- MAINTENANCE 1: Daily optimization routine
-- =============================================================================
-- Purpose: Daily maintenance for large fact tables
-- Schedule: Run at 2 AM daily via Glue workflow or Step Functions
-- =============================================================================

-- Daily fact table optimization (last 7 days only)
OPTIMIZE lakehouse_gold.fact_transactions
WHERE transaction_date >= DATE_ADD('day', -7, CURRENT_DATE)
ZORDER BY (transaction_date, customer_sk, product_sk);

-- Update statistics
ANALYZE TABLE lakehouse_gold.fact_transactions COMPUTE STATISTICS;

-- =============================================================================
-- MAINTENANCE 2: Weekly optimization routine
-- =============================================================================
-- Purpose: Weekly deep optimization for dimensions and medium tables
-- Schedule: Run at 2 AM every Sunday
-- =============================================================================

-- Optimize all dimension tables
OPTIMIZE lakehouse_gold.dim_customer ZORDER BY (customer_id, customer_segment);
OPTIMIZE lakehouse_gold.dim_product ZORDER BY (product_id, category, brand);
OPTIMIZE lakehouse_gold.dim_date ZORDER BY (date, year, month);

-- Vacuum old versions (7-day retention)
VACUUM lakehouse_gold.fact_transactions RETAIN 168 HOURS;
VACUUM lakehouse_gold.dim_customer RETAIN 168 HOURS;
VACUUM lakehouse_gold.dim_product RETAIN 168 HOURS;

-- Update statistics for all tables
ANALYZE TABLE lakehouse_gold.dim_customer COMPUTE STATISTICS;
ANALYZE TABLE lakehouse_gold.dim_product COMPUTE STATISTICS;
ANALYZE TABLE lakehouse_gold.dim_date COMPUTE STATISTICS;

-- =============================================================================
-- MAINTENANCE 3: Monthly optimization routine
-- =============================================================================
-- Purpose: Monthly comprehensive optimization and cleanup
-- Schedule: Run at 2 AM on 1st of every month
-- =============================================================================

-- Full table optimization
OPTIMIZE lakehouse_gold.fact_transactions;
OPTIMIZE lakehouse_gold.daily_metrics;

-- Aggressive vacuum (remove everything older than 7 days)
VACUUM lakehouse_gold.fact_transactions RETAIN 168 HOURS;
VACUUM lakehouse_silver.transactions_silver RETAIN 72 HOURS;

-- Repair partitions
MSCK REPAIR TABLE lakehouse_gold.fact_transactions;
MSCK REPAIR TABLE lakehouse_silver.transactions_silver;

-- Update all statistics
ANALYZE TABLE lakehouse_gold.fact_transactions COMPUTE STATISTICS FOR ALL COLUMNS;

-- Check and report table health
SELECT
    'fact_transactions' AS table_name,
    COUNT(*) AS record_count,
    MAX(created_timestamp) AS last_updated,
    DATE_DIFF('hour', MAX(created_timestamp), CURRENT_TIMESTAMP) AS hours_since_update
FROM lakehouse_gold.fact_transactions;

-- =============================================================================
-- MAINTENANCE 4: Quarterly archival routine
-- =============================================================================
-- Purpose: Archive old data to cheaper storage (Glacier)
-- Schedule: Run quarterly (Jan 1, Apr 1, Jul 1, Oct 1)
-- =============================================================================

-- Identify old partitions for archival (> 2 years)
SELECT
    'ALTER TABLE lakehouse_gold.fact_transactions DROP PARTITION (year=' ||
    CAST(year AS VARCHAR) || ', month=' || CAST(month AS VARCHAR) || ');' AS drop_partition_sql
FROM (
    SELECT DISTINCT year, month
    FROM lakehouse_gold.fact_transactions
    WHERE transaction_date < DATE_ADD('year', -2, CURRENT_DATE)
) old_partitions
ORDER BY year, month;

-- Note: Actual archival would involve:
-- 1. Export old partitions to Glacier-backed S3 location
-- 2. Verify export success
-- 3. Drop partitions from hot storage
-- 4. Update documentation

-- =============================================================================
-- End of Table Optimization & Maintenance Queries
-- =============================================================================

-- Summary of maintenance schedules:
-- Daily: OPTIMIZE fact tables (recent partitions only), UPDATE STATISTICS
-- Weekly: OPTIMIZE dimensions, VACUUM old versions, UPDATE STATISTICS
-- Monthly: Full OPTIMIZE all tables, VACUUM, MSCK REPAIR, comprehensive stats
-- Quarterly: Archive old data, drop expired partitions, review storage costs
