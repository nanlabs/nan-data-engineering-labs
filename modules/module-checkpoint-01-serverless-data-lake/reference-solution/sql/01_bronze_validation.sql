-- ============================================================================
-- Bronze Zone Data Validation Queries
-- ============================================================================
-- Purpose: Validate raw data quality and completeness in Bronze zone
-- Database: cloudmart_data_lake
-- Zone: Bronze (raw data)
-- ============================================================================

USE cloudmart_data_lake;

-- ============================================================================
-- SECTION 1: DATA VOLUME AND COVERAGE VALIDATION
-- ============================================================================

-- Query 1: Count total records in raw_orders
-- Purpose: Verify data ingestion volume
SELECT
    'raw_orders' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT order_id) as unique_orders,
    COUNT(DISTINCT customer_id) as unique_customers,
    MIN(order_date) as earliest_order,
    MAX(order_date) as latest_order
FROM raw_orders;

-- Query 2: Count records by partition for raw_orders
-- Purpose: Verify partition distribution
SELECT
    year,
    month,
    day,
    COUNT(*) as record_count,
    COUNT(DISTINCT order_id) as unique_orders,
    ROUND(AVG(total_amount), 2) as avg_order_value
FROM raw_orders
GROUP BY year, month, day
ORDER BY year DESC, month DESC, day DESC;

-- Query 3: Count total records in raw_customers
-- Purpose: Verify customer data completeness
SELECT
    'raw_customers' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT email) as unique_emails,
    COUNT(DISTINCT country) as unique_countries
FROM raw_customers;

-- Query 4: Customer distribution by country
-- Purpose: Validate geographic coverage
SELECT
    country,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM raw_customers
GROUP BY country
ORDER BY customer_count DESC;

-- Query 5: Count total records in raw_products
-- Purpose: Verify product catalog size
SELECT
    'raw_products' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT product_id) as unique_products,
    COUNT(DISTINCT category) as unique_categories,
    SUM(stock_quantity) as total_stock
FROM raw_products;

-- Query 6: Product distribution by category
-- Purpose: Validate product catalog diversity
SELECT
    category,
    COUNT(*) as product_count,
    ROUND(AVG(price), 2) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    SUM(stock_quantity) as total_stock
FROM raw_products
GROUP BY category
ORDER BY product_count DESC;

-- Query 7: Count total events
-- Purpose: Verify event stream ingestion
SELECT
    'raw_events' as table_name,
    COUNT(*) as total_events,
    COUNT(DISTINCT event_id) as unique_events,
    COUNT(DISTINCT user_id) as unique_users,
    MIN(event_timestamp) as earliest_event,
    MAX(event_timestamp) as latest_event
FROM raw_events;

-- Query 8: Event distribution by type
-- Purpose: Validate event type coverage
SELECT
    event_type,
    COUNT(*) as event_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    COUNT(DISTINCT user_id) as unique_users
FROM raw_events
GROUP BY event_type
ORDER BY event_count DESC;

-- ============================================================================
-- SECTION 2: DATA QUALITY VALIDATION - NULL VALUES
-- ============================================================================

-- Query 9: Check for NULL values in raw_orders critical fields
-- Purpose: Identify data completeness issues
SELECT
    'raw_orders' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) as null_order_id,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id,
    SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) as null_order_date,
    SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END) as null_total_amount,
    SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) as null_status,
    ROUND(SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_order_id_pct
FROM raw_orders;

-- Query 10: Check for NULL values in raw_customers critical fields
-- Purpose: Identify customer data quality issues
SELECT
    'raw_customers' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id,
    SUM(CASE WHEN name IS NULL THEN 1 ELSE 0 END) as null_name,
    SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) as null_email,
    SUM(CASE WHEN country IS NULL THEN 1 ELSE 0 END) as null_country,
    SUM(CASE WHEN signup_date IS NULL THEN 1 ELSE 0 END) as null_signup_date,
    SUM(CASE WHEN segment IS NULL THEN 1 ELSE 0 END) as null_segment,
    ROUND(SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_email_pct
FROM raw_customers;

-- Query 11: Check for NULL or invalid values in raw_products
-- Purpose: Validate product data integrity
SELECT
    'raw_products' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id,
    SUM(CASE WHEN name IS NULL THEN 1 ELSE 0 END) as null_name,
    SUM(CASE WHEN category IS NULL THEN 1 ELSE 0 END) as null_category,
    SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) as null_price,
    SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END) as invalid_price,
    SUM(CASE WHEN stock_quantity IS NULL THEN 1 ELSE 0 END) as null_stock,
    SUM(CASE WHEN stock_quantity < 0 THEN 1 ELSE 0 END) as negative_stock
FROM raw_products;

-- ============================================================================
-- SECTION 3: DUPLICATE DETECTION
-- ============================================================================

-- Query 12: Check for duplicate order IDs
-- Purpose: Identify potential data duplication issues
SELECT
    order_id,
    COUNT(*) as occurrences,
    MIN(order_date) as first_occurrence,
    MAX(order_date) as last_occurrence
FROM raw_orders
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 100;

-- Query 13: Check for duplicate customer IDs
-- Purpose: Identify customer data duplication
SELECT
    customer_id,
    COUNT(*) as occurrences,
    COUNT(DISTINCT email) as unique_emails,
    COUNT(DISTINCT country) as unique_countries
FROM raw_customers
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 100;

-- Query 14: Check for duplicate product IDs
-- Purpose: Identify product catalog duplication
SELECT
    product_id,
    COUNT(*) as occurrences,
    COUNT(DISTINCT name) as unique_names,
    COUNT(DISTINCT category) as unique_categories
FROM raw_products
GROUP BY product_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 100;

-- Query 15: Check for duplicate event IDs
-- Purpose: Identify event stream duplication
SELECT
    event_id,
    COUNT(*) as occurrences
FROM raw_events
GROUP BY event_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 100;

-- ============================================================================
-- SECTION 4: DATA CONSISTENCY VALIDATION
-- ============================================================================

-- Query 16: Check order status distribution
-- Purpose: Validate status values are within expected set
SELECT
    status,
    COUNT(*) as order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(AVG(total_amount), 2) as avg_order_value
FROM raw_orders
GROUP BY status
ORDER BY order_count DESC;

-- Query 17: Check customer segment distribution
-- Purpose: Validate segment values
SELECT
    segment,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM raw_customers
GROUP BY segment
ORDER BY customer_count DESC;

-- Query 18: Validate order amounts are reasonable
-- Purpose: Identify potential data entry errors
SELECT
    'Order Amount Validation' as check_name,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN total_amount <= 0 THEN 1 END) as zero_or_negative,
    COUNT(CASE WHEN total_amount > 10000 THEN 1 END) as extremely_high,
    ROUND(MIN(total_amount), 2) as min_amount,
    ROUND(AVG(total_amount), 2) as avg_amount,
    ROUND(MAX(total_amount), 2) as max_amount,
    ROUND(STDDEV(total_amount), 2) as stddev_amount
FROM raw_orders;

-- ============================================================================
-- SECTION 5: TEMPORAL VALIDATION
-- ============================================================================

-- Query 19: Check orders by date range
-- Purpose: Validate temporal coverage and identify gaps
SELECT
    DATE_TRUNC('month', CAST(order_date AS DATE)) as order_month,
    COUNT(*) as order_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(SUM(total_amount), 2) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value
FROM raw_orders
WHERE order_date >= '2024-01-01'
GROUP BY DATE_TRUNC('month', CAST(order_date AS DATE))
ORDER BY order_month DESC;

-- Query 20: Check customer signup trends
-- Purpose: Validate customer acquisition timeline
SELECT
    DATE_TRUNC('month', CAST(signup_date AS DATE)) as signup_month,
    COUNT(*) as new_customers,
    COUNT(DISTINCT country) as countries_represented
FROM raw_customers
WHERE signup_date >= '2022-01-01'
GROUP BY DATE_TRUNC('month', CAST(signup_date AS DATE))
ORDER BY signup_month DESC;

-- Query 21: Check ingestion freshness
-- Purpose: Verify data pipeline timeliness
SELECT
    'raw_orders' as table_name,
    MAX(ingestion_timestamp) as latest_ingestion,
    DATE_DIFF('hour', CAST(MAX(ingestion_timestamp) AS TIMESTAMP), CURRENT_TIMESTAMP) as hours_since_last_ingestion
FROM raw_orders
UNION ALL
SELECT
    'raw_customers' as table_name,
    MAX(ingestion_timestamp) as latest_ingestion,
    DATE_DIFF('hour', CAST(MAX(ingestion_timestamp) AS TIMESTAMP), CURRENT_TIMESTAMP) as hours_since_last_ingestion
FROM raw_customers
UNION ALL
SELECT
    'raw_products' as table_name,
    MAX(ingestion_timestamp) as latest_ingestion,
    DATE_DIFF('hour', CAST(MAX(ingestion_timestamp) AS TIMESTAMP), CURRENT_TIMESTAMP) as hours_since_last_ingestion
FROM raw_products
UNION ALL
SELECT
    'raw_events' as table_name,
    MAX(ingestion_timestamp) as latest_ingestion,
    DATE_DIFF('hour', CAST(MAX(ingestion_timestamp) AS TIMESTAMP), CURRENT_TIMESTAMP) as hours_since_last_ingestion
FROM raw_events;

-- ============================================================================
-- SECTION 6: EMAIL AND FORMAT VALIDATION
-- ============================================================================

-- Query 22: Check email format validity
-- Purpose: Identify potentially invalid email addresses
SELECT
    'Email Validation' as check_name,
    COUNT(*) as total_customers,
    COUNT(CASE WHEN email NOT LIKE '%@%' THEN 1 END) as missing_at_symbol,
    COUNT(CASE WHEN email NOT LIKE '%.%' THEN 1 END) as missing_dot,
    COUNT(CASE WHEN LENGTH(email) < 5 THEN 1 END) as too_short,
    COUNT(CASE WHEN email LIKE '%@%.%' THEN 1 END) as valid_format
FROM raw_customers;

-- Query 23: Check for suspicious patterns in order data
-- Purpose: Identify potential fraud or data quality issues
SELECT
    customer_id,
    COUNT(*) as order_count,
    SUM(total_amount) as total_spent,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    MIN(order_date) as first_order,
    MAX(order_date) as last_order,
    DATE_DIFF('day', CAST(MIN(order_date) AS DATE), CAST(MAX(order_date) AS DATE)) as days_between_first_last
FROM raw_orders
GROUP BY customer_id
HAVING COUNT(*) > 50 OR SUM(total_amount) > 50000
ORDER BY total_spent DESC
LIMIT 50;

-- ============================================================================
-- SECTION 7: SCHEMA VALIDATION
-- ============================================================================

-- Query 24: Validate data types can be cast properly
-- Purpose: Check if string fields can be converted to appropriate types
SELECT
    'Data Type Validation' as check_name,
    COUNT(*) as total_orders,
    COUNT(CASE
        WHEN TRY_CAST(order_date AS DATE) IS NULL
        THEN 1
    END) as invalid_date_format,
    COUNT(CASE
        WHEN TRY_CAST(total_amount AS DECIMAL(10,2)) IS NULL
        THEN 1
    END) as invalid_amount_format
FROM raw_orders;

-- Query 25: Summary validation report
-- Purpose: Overall data quality score for Bronze zone
SELECT
    'Bronze Zone Quality Summary' as report_title,
    (SELECT COUNT(*) FROM raw_orders) as total_orders,
    (SELECT COUNT(*) FROM raw_customers) as total_customers,
    (SELECT COUNT(*) FROM raw_products) as total_products,
    (SELECT COUNT(*) FROM raw_events) as total_events,
    (SELECT COUNT(DISTINCT order_id) FROM raw_orders) as unique_order_ids,
    (SELECT COUNT(DISTINCT customer_id) FROM raw_customers) as unique_customer_ids,
    ROUND(
        (SELECT COUNT(DISTINCT order_id) FROM raw_orders) * 100.0 /
        NULLIF((SELECT COUNT(*) FROM raw_orders), 0),
        2
    ) as order_uniqueness_pct,
    ROUND(
        (SELECT COUNT(DISTINCT customer_id) FROM raw_customers) * 100.0 /
        NULLIF((SELECT COUNT(*) FROM raw_customers), 0),
        2
    ) as customer_uniqueness_pct;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. Run these queries after data ingestion to Bronze zone
-- 2. Review results to identify data quality issues
-- 3. Document any anomalies or unexpected patterns
-- 4. Use results to inform data cleansing rules for Silver zone
-- 5. Schedule regular execution as part of data quality monitoring
--
-- Expected thresholds:
-- - Uniqueness: >99% for IDs
-- - Null values: <1% for critical fields
-- - Invalid formats: <0.1%
-- - Duplicate records: 0% for unique identifiers
-- ============================================================================
