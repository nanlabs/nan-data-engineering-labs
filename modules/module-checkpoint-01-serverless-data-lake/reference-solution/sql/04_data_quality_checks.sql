-- ============================================================================
-- Data Quality Checks and Validation
-- ============================================================================
-- Purpose: Comprehensive data quality validation across Bronze, Silver, and Gold zones
-- Database: cloudmart_data_lake
-- ============================================================================

USE cloudmart_data_lake;

-- ============================================================================
-- SECTION 1: REFERENTIAL INTEGRITY CHECKS
-- ============================================================================

-- Query 1: Orders with missing customer references
-- Purpose: Identify orders that reference non-existent customers
SELECT
    'Orders with Invalid Customer Reference' as check_name,
    COUNT(*) as invalid_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM processed_orders), 4) as error_rate_pct
FROM processed_orders o
LEFT JOIN processed_customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
    AND o.year = 2024;

-- Query 2: Detailed list of orders with missing customer references
-- Purpose: Get specific records for investigation
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.total_amount,
    o.status,
    'Missing customer reference' as issue
FROM processed_orders o
LEFT JOIN processed_customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
    AND o.year = 2024
LIMIT 100;

-- Query 3: Check for orphaned customer records
-- Purpose: Identify customers with no orders
SELECT
    'Customers with No Orders' as check_name,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM processed_customers), 2) as percentage
FROM processed_customers c
LEFT JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;

-- Query 4: Cross-zone referential integrity (Bronze to Silver)
-- Purpose: Ensure all Bronze records are processed to Silver
SELECT
    'Bronze Orders Missing in Silver' as check_name,
    COUNT(DISTINCT rb.order_id) as bronze_count,
    COUNT(DISTINCT ps.order_id) as silver_count,
    COUNT(DISTINCT rb.order_id) - COUNT(DISTINCT ps.order_id) as missing_count,
    ROUND(
        (COUNT(DISTINCT rb.order_id) - COUNT(DISTINCT ps.order_id)) * 100.0 /
        NULLIF(COUNT(DISTINCT rb.order_id), 0),
        2
    ) as missing_pct
FROM raw_orders rb
LEFT JOIN processed_orders ps ON rb.order_id = ps.order_id
WHERE rb.year = 2024 AND rb.month = EXTRACT(MONTH FROM CURRENT_DATE);

-- Query 5: Silver to Gold referential integrity
-- Purpose: Verify Gold aggregations include all Silver data
WITH silver_daily_counts AS (
    SELECT
        order_date,
        COUNT(*) as silver_order_count,
        SUM(total_amount) as silver_revenue
    FROM processed_orders
    WHERE year = 2024
    GROUP BY order_date
)
SELECT
    s.order_date,
    s.silver_order_count,
    g.total_orders as gold_order_count,
    s.silver_order_count - g.total_orders as order_count_diff,
    ROUND(s.silver_revenue, 2) as silver_revenue,
    ROUND(g.total_revenue, 2) as gold_revenue,
    ROUND(s.silver_revenue - g.total_revenue, 2) as revenue_diff
FROM silver_daily_counts s
LEFT JOIN sales_summary g ON s.order_date = g.order_date
WHERE ABS(s.silver_order_count - COALESCE(g.total_orders, 0)) > 0
ORDER BY s.order_date DESC
LIMIT 50;

-- ============================================================================
-- SECTION 2: COMPLETENESS CHECKS
-- ============================================================================

-- Query 6: Completeness check for critical fields in processed_orders
-- Purpose: Ensure all required fields are populated
SELECT
    'Processed Orders Completeness' as check_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) as missing_order_id,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as missing_customer_id,
    SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) as missing_order_date,
    SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END) as missing_amount,
    SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) as missing_status,
    ROUND(SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as missing_order_id_pct,
    ROUND(SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as missing_customer_id_pct,
    CASE
        WHEN SUM(CASE WHEN order_id IS NULL OR customer_id IS NULL OR order_date IS NULL THEN 1 ELSE 0 END) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END as quality_status
FROM processed_orders
WHERE year = 2024;

-- Query 7: Completeness check for customer records
-- Purpose: Validate customer data completeness
SELECT
    'Processed Customers Completeness' as check_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as missing_customer_id,
    SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as missing_name,
    SUM(CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END) as missing_email,
    SUM(CASE WHEN country IS NULL OR country = '' THEN 1 ELSE 0 END) as missing_country,
    SUM(CASE WHEN segment IS NULL OR segment = '' THEN 1 ELSE 0 END) as missing_segment,
    ROUND(SUM(CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as missing_email_pct,
    CASE
        WHEN SUM(CASE WHEN customer_id IS NULL OR email IS NULL THEN 1 ELSE 0 END) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END as quality_status
FROM processed_customers
WHERE year = 2024;

-- Query 8: Data coverage by date - identify gaps
-- Purpose: Detect missing days in data pipeline
WITH RECURSIVE date_series AS (
    SELECT DATE '2024-01-01' as expected_date
    UNION ALL
    SELECT expected_date + INTERVAL '1' DAY
    FROM date_series
    WHERE expected_date < CURRENT_DATE
)
SELECT
    ds.expected_date,
    COALESCE(COUNT(o.order_id), 0) as order_count,
    CASE
        WHEN COUNT(o.order_id) = 0 THEN 'MISSING DATA'
        WHEN COUNT(o.order_id) < 100 THEN 'LOW VOLUME'
        ELSE 'OK'
    END as status
FROM date_series ds
LEFT JOIN processed_orders o ON ds.expected_date = o.order_date
GROUP BY ds.expected_date
HAVING COUNT(o.order_id) = 0 OR COUNT(o.order_id) < 100
ORDER BY ds.expected_date DESC
LIMIT 30;

-- ============================================================================
-- SECTION 3: CONSISTENCY CHECKS
-- ============================================================================

-- Query 9: Check for inconsistent customer data
-- Purpose: Identify customers with conflicting information
SELECT
    customer_id,
    COUNT(DISTINCT name) as distinct_names,
    COUNT(DISTINCT email) as distinct_emails,
    COUNT(DISTINCT country) as distinct_countries,
    COUNT(DISTINCT segment) as distinct_segments,
    MAX(name) as name_example,
    MAX(email) as email_example
FROM processed_customers
GROUP BY customer_id
HAVING COUNT(DISTINCT name) > 1
    OR COUNT(DISTINCT email) > 1
    OR COUNT(DISTINCT country) > 1
LIMIT 100;

-- Query 10: Check for email format consistency
-- Purpose: Validate email format standards
SELECT
    'Email Format Validation' as check_name,
    COUNT(*) as total_customers,
    SUM(CASE WHEN email LIKE '%@%.%' THEN 1 ELSE 0 END) as valid_format,
    SUM(CASE WHEN email NOT LIKE '%@%' THEN 1 ELSE 0 END) as missing_at,
    SUM(CASE WHEN email NOT LIKE '%.%' THEN 1 ELSE 0 END) as missing_dot,
    SUM(CASE WHEN LENGTH(email) < 5 THEN 1 ELSE 0 END) as too_short,
    SUM(CASE WHEN email LIKE '% %' THEN 1 ELSE 0 END) as contains_space,
    ROUND(SUM(CASE WHEN email LIKE '%@%.%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as valid_pct,
    CASE
        WHEN SUM(CASE WHEN email LIKE '%@%.%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) >= 99
        THEN 'PASS'
        ELSE 'FAIL'
    END as quality_status
FROM processed_customers
WHERE year = 2024;

-- Query 11: Status value consistency
-- Purpose: Ensure status values are from expected set
SELECT
    status,
    COUNT(*) as count,
    CASE
        WHEN status IN ('completed', 'pending', 'cancelled') THEN 'VALID'
        ELSE 'INVALID'
    END as validity
FROM processed_orders
WHERE year = 2024
GROUP BY status
ORDER BY count DESC;

-- Query 12: Date consistency checks
-- Purpose: Ensure dates are logical and within expected ranges
SELECT
    'Date Consistency Check' as check_name,
    COUNT(*) as total_orders,
    SUM(CASE WHEN order_date > CURRENT_DATE THEN 1 ELSE 0 END) as future_dates,
    SUM(CASE WHEN order_date < DATE '2020-01-01' THEN 1 ELSE 0 END) as old_dates,
    SUM(CASE WHEN order_timestamp < CAST(order_date AS TIMESTAMP) THEN 1 ELSE 0 END) as timestamp_before_date,
    CASE
        WHEN SUM(CASE WHEN order_date > CURRENT_DATE OR order_date < DATE '2020-01-01' THEN 1 ELSE 0 END) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END as quality_status
FROM processed_orders
WHERE year = 2024;

-- ============================================================================
-- SECTION 4: ACCURACY CHECKS
-- ============================================================================

-- Query 13: Numeric range validation
-- Purpose: Check if numeric values are within reasonable bounds
SELECT
    'Numeric Range Validation' as check_name,
    COUNT(*) as total_orders,
    SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END) as zero_or_negative_amount,
    SUM(CASE WHEN total_amount > 50000 THEN 1 ELSE 0 END) as extremely_high_amount,
    SUM(CASE WHEN product_count <= 0 THEN 1 ELSE 0 END) as invalid_product_count,
    SUM(CASE WHEN product_count > 100 THEN 1 ELSE 0 END) as suspicious_product_count,
    ROUND(MIN(total_amount), 2) as min_amount,
    ROUND(MAX(total_amount), 2) as max_amount,
    ROUND(AVG(total_amount), 2) as avg_amount,
    CASE
        WHEN SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END as quality_status
FROM processed_orders
WHERE year = 2024;

-- Query 14: Statistical outlier detection
-- Purpose: Identify statistical outliers in order amounts
WITH stats AS (
    SELECT
        AVG(total_amount) as mean_amount,
        STDDEV(total_amount) as stddev_amount
    FROM processed_orders
    WHERE year = 2024
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.total_amount,
    ROUND((o.total_amount - s.mean_amount) / s.stddev_amount, 2) as z_score,
    CASE
        WHEN ABS((o.total_amount - s.mean_amount) / s.stddev_amount) > 3 THEN 'Extreme Outlier'
        WHEN ABS((o.total_amount - s.mean_amount) / s.stddev_amount) > 2 THEN 'Moderate Outlier'
        ELSE 'Normal'
    END as outlier_status
FROM processed_orders o, stats s
WHERE o.year = 2024
    AND ABS((o.total_amount - s.mean_amount) / s.stddev_amount) > 2
ORDER BY ABS((o.total_amount - s.mean_amount) / s.stddev_amount) DESC
LIMIT 100;

-- Query 15: Customer lifetime value validation
-- Purpose: Verify CLV calculations are accurate
SELECT
    c.customer_id,
    c.name,
    c.lifetime_value as stored_clv,
    SUM(o.total_amount) as calculated_clv,
    ROUND(ABS(c.lifetime_value - SUM(o.total_amount)), 2) as difference,
    CASE
        WHEN ABS(c.lifetime_value - SUM(o.total_amount)) < 0.01 THEN 'MATCH'
        WHEN ABS(c.lifetime_value - SUM(o.total_amount)) < 1.00 THEN 'MINOR_DIFF'
        ELSE 'MISMATCH'
    END as validation_status
FROM processed_customers c
LEFT JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE c.year = 2024
GROUP BY c.customer_id, c.name, c.lifetime_value
HAVING ABS(c.lifetime_value - COALESCE(SUM(o.total_amount), 0)) >= 0.01
ORDER BY difference DESC
LIMIT 100;

-- ============================================================================
-- SECTION 5: TIMELINESS CHECKS
-- ============================================================================

-- Query 16: Data freshness check
-- Purpose: Ensure data is being ingested in a timely manner
SELECT
    'Data Freshness Check' as check_name,
    zone,
    table_name,
    latest_processing_timestamp,
    ROUND(DATE_DIFF('hour', latest_processing_timestamp, CURRENT_TIMESTAMP), 1) as hours_old,
    CASE
        WHEN DATE_DIFF('hour', latest_processing_timestamp, CURRENT_TIMESTAMP) <= 2 THEN 'FRESH'
        WHEN DATE_DIFF('hour', latest_processing_timestamp, CURRENT_TIMESTAMP) <= 24 THEN 'ACCEPTABLE'
        ELSE 'STALE'
    END as freshness_status
FROM (
    SELECT
        'Silver' as zone,
        'processed_orders' as table_name,
        MAX(processing_timestamp) as latest_processing_timestamp
    FROM processed_orders
    UNION ALL
    SELECT
        'Silver' as zone,
        'processed_customers' as table_name,
        MAX(processing_timestamp) as latest_processing_timestamp
    FROM processed_customers
    UNION ALL
    SELECT
        'Gold' as zone,
        'sales_summary' as table_name,
        MAX(calculation_timestamp) as latest_processing_timestamp
    FROM sales_summary
    UNION ALL
    SELECT
        'Gold' as zone,
        'customer_360' as table_name,
        MAX(calculation_timestamp) as latest_processing_timestamp
    FROM customer_360
);

-- Query 17: Processing lag analysis
-- Purpose: Measure time between order date and processing
SELECT
    order_date,
    COUNT(*) as order_count,
    ROUND(AVG(DATE_DIFF('hour', order_timestamp, processing_timestamp)), 2) as avg_processing_lag_hours,
    ROUND(MAX(DATE_DIFF('hour', order_timestamp, processing_timestamp)), 2) as max_processing_lag_hours,
    CASE
        WHEN AVG(DATE_DIFF('hour', order_timestamp, processing_timestamp)) <= 2 THEN 'EXCELLENT'
        WHEN AVG(DATE_DIFF('hour', order_timestamp, processing_timestamp)) <= 6 THEN 'GOOD'
        WHEN AVG(DATE_DIFF('hour', order_timestamp, processing_timestamp)) <= 24 THEN 'ACCEPTABLE'
        ELSE 'POOR'
    END as lag_status
FROM processed_orders
WHERE year = 2024
    AND month >= EXTRACT(MONTH FROM CURRENT_DATE) - 1
GROUP BY order_date
ORDER BY order_date DESC;

-- Query 18: Late arriving data detection
-- Purpose: Identify data arriving significantly after event time
SELECT
    DATE(processing_timestamp) as processing_date,
    DATE(order_date) as order_date,
    COUNT(*) as record_count,
    DATE_DIFF('day', DATE(order_date), DATE(processing_timestamp)) as days_delay
FROM processed_orders
WHERE DATE_DIFF('day', DATE(order_date), DATE(processing_timestamp)) > 7
    AND year = 2024
GROUP BY DATE(processing_timestamp), DATE(order_date)
ORDER BY days_delay DESC, processing_date DESC
LIMIT 100;

-- ============================================================================
-- SECTION 6: UNIQUENESS CHECKS
-- ============================================================================

-- Query 19: Duplicate detection in processed_orders
-- Purpose: Identify duplicate order records
SELECT
    order_id,
    COUNT(*) as occurrence_count,
    MIN(order_date) as first_occurrence,
    MAX(order_date) as last_occurrence,
    MIN(processing_timestamp) as first_processing,
    MAX(processing_timestamp) as last_processing
FROM processed_orders
WHERE year = 2024
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC
LIMIT 100;

-- Query 20: Duplicate detection in customer records
-- Purpose: Identify duplicate or near-duplicate customers
SELECT
    email,
    COUNT(DISTINCT customer_id) as customer_count,
    ARRAY_AGG(DISTINCT customer_id) as customer_ids,
    ARRAY_AGG(DISTINCT name) as names
FROM processed_customers
WHERE year = 2024
GROUP BY email
HAVING COUNT(DISTINCT customer_id) > 1
ORDER BY customer_count DESC
LIMIT 100;

-- ============================================================================
-- SECTION 7: COMPREHENSIVE QUALITY SCORECARD
-- ============================================================================

-- Query 21: Overall data quality summary score
-- Purpose: Provide aggregated quality metrics across all checks
WITH quality_metrics AS (
    SELECT
        'Referential Integrity' as dimension,
        ROUND(
            (1 - COUNT(CASE WHEN c.customer_id IS NULL THEN 1 END) * 1.0 / COUNT(*)) * 100,
            2
        ) as score
    FROM processed_orders o
    LEFT JOIN processed_customers c ON o.customer_id = c.customer_id
    WHERE o.year = 2024

    UNION ALL

    SELECT
        'Completeness' as dimension,
        ROUND(
            (1 - SUM(CASE WHEN order_id IS NULL OR customer_id IS NULL OR order_date IS NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100,
            2
        ) as score
    FROM processed_orders
    WHERE year = 2024

    UNION ALL

    SELECT
        'Accuracy' as dimension,
        ROUND(
            (1 - SUM(CASE WHEN total_amount <= 0 OR product_count <= 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100,
            2
        ) as score
    FROM processed_orders
    WHERE year = 2024

    UNION ALL

    SELECT
        'Uniqueness' as dimension,
        ROUND(
            COUNT(DISTINCT order_id) * 100.0 / COUNT(*),
            2
        ) as score
    FROM processed_orders
    WHERE year = 2024

    UNION ALL

    SELECT
        'Email Validity' as dimension,
        ROUND(
            SUM(CASE WHEN email LIKE '%@%.%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) as score
    FROM processed_customers
    WHERE year = 2024
)
SELECT
    dimension,
    score,
    CASE
        WHEN score >= 99 THEN 'Excellent'
        WHEN score >= 95 THEN 'Good'
        WHEN score >= 90 THEN 'Acceptable'
        ELSE 'Poor'
    END as rating,
    CASE
        WHEN score >= 95 THEN 'PASS'
        ELSE 'FAIL'
    END as status
FROM quality_metrics
ORDER BY score ASC;

-- Query 22: Data quality trend over time
-- Purpose: Track data quality improvements or degradations
SELECT
    DATE_TRUNC('week', order_date) as week,
    COUNT(*) as total_records,
    COUNT(DISTINCT order_id) as unique_orders,
    ROUND(COUNT(DISTINCT order_id) * 100.0 / COUNT(*), 2) as uniqueness_pct,
    SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END) as invalid_amounts,
    ROUND(SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as invalid_amount_pct,
    ROUND(AVG(DATE_DIFF('hour', order_timestamp, processing_timestamp)), 2) as avg_processing_lag_hours
FROM processed_orders
WHERE year = 2024
GROUP BY DATE_TRUNC('week', order_date)
ORDER BY week DESC;

-- Query 23: Critical quality violations report
-- Purpose: List all critical data quality issues
SELECT
    'Critical Quality Violations' as report_title,
    violation_type,
    COUNT(*) as violation_count,
    severity
FROM (
    SELECT
        order_id,
        'Missing Customer Reference' as violation_type,
        'HIGH' as severity
    FROM processed_orders o
    LEFT JOIN processed_customers c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL AND o.year = 2024

    UNION ALL

    SELECT
        order_id,
        'Invalid Order Amount' as violation_type,
        'HIGH' as severity
    FROM processed_orders
    WHERE total_amount <= 0 AND year = 2024

    UNION ALL

    SELECT
        order_id,
        'Future Order Date' as violation_type,
        'HIGH' as severity
    FROM processed_orders
    WHERE order_date > CURRENT_DATE AND year = 2024

    UNION ALL

    SELECT
        customer_id,
        'Invalid Email Format' as violation_type,
        'MEDIUM' as severity
    FROM processed_customers
    WHERE email NOT LIKE '%@%.%' AND year = 2024

    UNION ALL

    SELECT
        order_id,
        'Duplicate Order ID' as violation_type,
        'MEDIUM' as severity
    FROM (
        SELECT order_id
        FROM processed_orders
        WHERE year = 2024
        GROUP BY order_id
        HAVING COUNT(*) > 1
    )
)
GROUP BY violation_type, severity
ORDER BY
    CASE severity
        WHEN 'HIGH' THEN 1
        WHEN 'MEDIUM' THEN 2
        ELSE 3
    END,
    violation_count DESC;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. Run these checks daily as part of data quality monitoring
-- 2. Set up alerts for FAIL statuses in quality_status fields
-- 3. Investigate and remediate issues found by these queries
-- 4. Track quality trends over time to measure improvements
-- 5. Include quality metrics in operational dashboards
--
-- Quality thresholds:
-- - Referential Integrity: 100% (no broken references)
-- - Completeness: >99% for critical fields
-- - Accuracy: >99% for numeric ranges
-- - Uniqueness: 100% for unique identifiers
-- - Timeliness: <2 hours for real-time pipelines, <24 hours for batch
--
-- Severity levels:
-- - HIGH: Data corruption, broken references, critical field nulls
-- - MEDIUM: Format violations, minor inconsistencies
-- - LOW: Non-critical missing optional fields
-- ============================================================================
