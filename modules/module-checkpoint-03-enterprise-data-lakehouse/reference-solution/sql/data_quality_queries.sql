-- =============================================================================
-- DATA QUALITY QUERIES - Enterprise Data Lakehouse
-- =============================================================================
-- Purpose: Comprehensive data quality monitoring queries to check completeness,
--          detect anomalies, identify schema drift, validate referential
--          integrity, and generate DQ scorecards
-- Database: lakehouse_gold, lakehouse_silver, lakehouse_bronze
-- Compatible: Amazon Athena, Presto, Trino
-- =============================================================================

-- =============================================================================
-- QUERY 1: Completeness Check - All Gold Tables
-- =============================================================================
-- Purpose: Check null values and completeness across all critical columns
-- =============================================================================

WITH customer_completeness AS (
    SELECT
        'dim_customer' AS table_name,
        COUNT(*) AS total_records,
        COUNT(customer_id) AS customer_id_count,
        COUNT(customer_name) AS customer_name_count,
        COUNT(email) AS email_count,
        COUNT(phone) AS phone_count,
        COUNT(state) AS state_count,
        COUNT(country) AS country_count,
        COUNT(customer_segment) AS segment_count,
        -- Calculate completeness percentages
        ROUND(COUNT(customer_id) * 100.0 / COUNT(*), 2) AS customer_id_completeness,
        ROUND(COUNT(customer_name) * 100.0 / COUNT(*), 2) AS customer_name_completeness,
        ROUND(COUNT(email) * 100.0 / COUNT(*), 2) AS email_completeness,
        ROUND(COUNT(phone) * 100.0 / COUNT(*), 2) AS phone_completeness,
        ROUND(COUNT(state) * 100.0 / COUNT(*), 2) AS state_completeness,
        ROUND(COUNT(country) * 100.0 / COUNT(*), 2) AS country_completeness
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true
),
product_completeness AS (
    SELECT
        'dim_product' AS table_name,
        COUNT(*) AS total_records,
        COUNT(product_id) AS product_id_count,
        COUNT(product_name) AS product_name_count,
        COUNT(category) AS category_count,
        COUNT(brand) AS brand_count,
        COUNT(unit_price) AS unit_price_count,
        COUNT(cost) AS cost_count,
        -- Calculate completeness percentages
        ROUND(COUNT(product_id) * 100.0 / COUNT(*), 2) AS product_id_completeness,
        ROUND(COUNT(product_name) * 100.0 / COUNT(*), 2) AS product_name_completeness,
        ROUND(COUNT(category) * 100.0 / COUNT(*), 2) AS category_completeness,
        ROUND(COUNT(brand) * 100.0 / COUNT(*), 2) AS brand_completeness,
        ROUND(COUNT(unit_price) * 100.0 / COUNT(*), 2) AS unit_price_completeness,
        ROUND(COUNT(cost) * 100.0 / COUNT(*), 2) AS cost_completeness
    FROM lakehouse_gold.dim_product
),
transaction_completeness AS (
    SELECT
        'fact_transactions' AS table_name,
        COUNT(*) AS total_records,
        COUNT(transaction_id) AS transaction_id_count,
        COUNT(customer_sk) AS customer_sk_count,
        COUNT(product_sk) AS product_sk_count,
        COUNT(date_sk) AS date_sk_count,
        COUNT(net_amount) AS net_amount_count,
        COUNT(quantity) AS quantity_count,
        -- Calculate completeness percentages
        ROUND(COUNT(transaction_id) * 100.0 / COUNT(*), 2) AS transaction_id_completeness,
        ROUND(COUNT(customer_sk) * 100.0 / COUNT(*), 2) AS customer_sk_completeness,
        ROUND(COUNT(product_sk) * 100.0 / COUNT(*), 2) AS product_sk_completeness,
        ROUND(COUNT(date_sk) * 100.0 / COUNT(*), 2) AS date_sk_completeness,
        ROUND(COUNT(net_amount) * 100.0 / COUNT(*), 2) AS net_amount_completeness,
        ROUND(COUNT(quantity) * 100.0 / COUNT(*), 2) AS quantity_completeness
    FROM lakehouse_gold.fact_transactions
)
SELECT
    table_name,
    total_records,
    -- Average completeness score
    ROUND((customer_id_completeness + customer_name_completeness +
           email_completeness + phone_completeness) / 4.0, 2) AS avg_completeness_score,
    -- Individual field completeness
    customer_id_completeness,
    customer_name_completeness,
    email_completeness,
    phone_completeness,
    state_completeness,
    country_completeness,
    -- Quality status
    CASE
        WHEN (customer_id_completeness + customer_name_completeness + email_completeness) / 3.0 >= 95 THEN 'Excellent'
        WHEN (customer_id_completeness + customer_name_completeness + email_completeness) / 3.0 >= 85 THEN 'Good'
        WHEN (customer_id_completeness + customer_name_completeness + email_completeness) / 3.0 >= 70 THEN 'Fair'
        ELSE 'Poor'
    END AS quality_status
FROM customer_completeness

UNION ALL

SELECT
    table_name,
    total_records,
    ROUND((product_id_completeness + product_name_completeness +
           category_completeness + brand_completeness) / 4.0, 2) AS avg_completeness_score,
    product_id_completeness,
    product_name_completeness,
    category_completeness,
    brand_completeness,
    unit_price_completeness,
    cost_completeness,
    CASE
        WHEN (product_id_completeness + product_name_completeness + category_completeness) / 3.0 >= 95 THEN 'Excellent'
        WHEN (product_id_completeness + product_name_completeness + category_completeness) / 3.0 >= 85 THEN 'Good'
        WHEN (product_id_completeness + product_name_completeness + category_completeness) / 3.0 >= 70 THEN 'Fair'
        ELSE 'Poor'
    END AS quality_status
FROM product_completeness

UNION ALL

SELECT
    table_name,
    total_records,
    ROUND((transaction_id_completeness + customer_sk_completeness +
           product_sk_completeness + net_amount_completeness) / 4.0, 2) AS avg_completeness_score,
    transaction_id_completeness,
    customer_sk_completeness,
    product_sk_completeness,
    date_sk_completeness,
    net_amount_completeness,
    quantity_completeness,
    CASE
        WHEN (transaction_id_completeness + customer_sk_completeness +
              product_sk_completeness + net_amount_completeness) / 4.0 >= 95 THEN 'Excellent'
        WHEN (transaction_id_completeness + customer_sk_completeness +
              product_sk_completeness + net_amount_completeness) / 4.0 >= 85 THEN 'Good'
        WHEN (transaction_id_completeness + customer_sk_completeness +
              product_sk_completeness + net_amount_completeness) / 4.0 >= 70 THEN 'Fair'
        ELSE 'Poor'
    END AS quality_status
FROM transaction_completeness;

-- =============================================================================
-- QUERY 2: Duplicate Detection - Primary Keys & Business Keys
-- =============================================================================
-- Purpose: Identify duplicate records across all tables
-- =============================================================================

WITH customer_duplicates AS (
    SELECT
        'dim_customer' AS table_name,
        'customer_id' AS key_column,
        customer_id AS key_value,
        COUNT(*) AS duplicate_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true
    GROUP BY customer_id
    HAVING COUNT(*) > 1
),
email_duplicates AS (
    SELECT
        'dim_customer' AS table_name,
        'email' AS key_column,
        email AS key_value,
        COUNT(*) AS duplicate_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true AND email IS NOT NULL
    GROUP BY email
    HAVING COUNT(*) > 1
),
product_duplicates AS (
    SELECT
        'dim_product' AS table_name,
        'product_id' AS key_column,
        product_id AS key_value,
        COUNT(*) AS duplicate_count
    FROM lakehouse_gold.dim_product
    GROUP BY product_id
    HAVING COUNT(*) > 1
),
transaction_duplicates AS (
    SELECT
        'fact_transactions' AS table_name,
        'transaction_id' AS key_column,
        transaction_id AS key_value,
        COUNT(*) AS duplicate_count
    FROM lakehouse_gold.fact_transactions
    GROUP BY transaction_id
    HAVING COUNT(*) > 1
)
SELECT
    table_name,
    key_column,
    key_value,
    duplicate_count,
    CASE
        WHEN duplicate_count >= 10 THEN 'Critical'
        WHEN duplicate_count >= 5 THEN 'High'
        WHEN duplicate_count >= 2 THEN 'Medium'
        ELSE 'Low'
    END AS severity
FROM (
    SELECT * FROM customer_duplicates
    UNION ALL
    SELECT * FROM email_duplicates
    UNION ALL
    SELECT * FROM product_duplicates
    UNION ALL
    SELECT * FROM transaction_duplicates
) all_duplicates
ORDER BY duplicate_count DESC;

-- =============================================================================
-- QUERY 3: Referential Integrity Check
-- =============================================================================
-- Purpose: Find orphan records and broken foreign key relationships
-- =============================================================================

WITH orphan_transactions_customer AS (
    SELECT
        'fact_transactions' AS fact_table,
        'customer_sk' AS foreign_key,
        'dim_customer' AS dimension_table,
        COUNT(*) AS orphan_count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM lakehouse_gold.fact_transactions) AS orphan_percentage
    FROM lakehouse_gold.fact_transactions f
    WHERE NOT EXISTS (
        SELECT 1
        FROM lakehouse_gold.dim_customer c
        WHERE c.customer_sk = f.customer_sk
    )
),
orphan_transactions_product AS (
    SELECT
        'fact_transactions' AS fact_table,
        'product_sk' AS foreign_key,
        'dim_product' AS dimension_table,
        COUNT(*) AS orphan_count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM lakehouse_gold.fact_transactions) AS orphan_percentage
    FROM lakehouse_gold.fact_transactions f
    WHERE NOT EXISTS (
        SELECT 1
        FROM lakehouse_gold.dim_product p
        WHERE p.product_sk = f.product_sk
    )
),
orphan_transactions_date AS (
    SELECT
        'fact_transactions' AS fact_table,
        'date_sk' AS foreign_key,
        'dim_date' AS dimension_table,
        COUNT(*) AS orphan_count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM lakehouse_gold.fact_transactions) AS orphan_percentage
    FROM lakehouse_gold.fact_transactions f
    WHERE NOT EXISTS (
        SELECT 1
        FROM lakehouse_gold.dim_date d
        WHERE d.date_sk = f.date_sk
    )
)
SELECT
    fact_table,
    foreign_key,
    dimension_table,
    orphan_count,
    ROUND(orphan_percentage, 4) AS orphan_percentage,
    CASE
        WHEN orphan_percentage = 0 THEN 'Perfect'
        WHEN orphan_percentage < 0.1 THEN 'Excellent'
        WHEN orphan_percentage < 1 THEN 'Good'
        WHEN orphan_percentage < 5 THEN 'Fair'
        ELSE 'Poor'
    END AS integrity_status
FROM (
    SELECT * FROM orphan_transactions_customer
    UNION ALL
    SELECT * FROM orphan_transactions_product
    UNION ALL
    SELECT * FROM orphan_transactions_date
) all_orphans;

-- =============================================================================
-- QUERY 4: Data Freshness Monitoring
-- =============================================================================
-- Purpose: Monitor data freshness and identify stale data
-- =============================================================================

WITH table_freshness AS (
    SELECT
        'dim_customer' AS table_name,
        MAX(updated_timestamp) AS last_update,
        MIN(updated_timestamp) AS first_update,
        DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) AS hours_since_update,
        COUNT(*) AS record_count,
        COUNT(DISTINCT DATE(updated_timestamp)) AS update_days
    FROM lakehouse_gold.dim_customer

    UNION ALL

    SELECT
        'dim_product' AS table_name,
        MAX(updated_timestamp) AS last_update,
        MIN(updated_timestamp) AS first_update,
        DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) AS hours_since_update,
        COUNT(*) AS record_count,
        COUNT(DISTINCT DATE(updated_timestamp)) AS update_days
    FROM lakehouse_gold.dim_product

    UNION ALL

    SELECT
        'fact_transactions' AS table_name,
        MAX(created_timestamp) AS last_update,
        MIN(created_timestamp) AS first_update,
        DATE_DIFF('hour', MAX(created_timestamp), CURRENT_TIMESTAMP) AS hours_since_update,
        COUNT(*) AS record_count,
        COUNT(DISTINCT DATE(created_timestamp)) AS update_days
    FROM lakehouse_gold.fact_transactions
)
SELECT
    table_name,
    last_update,
    first_update,
    hours_since_update,
    record_count,
    update_days,
    -- Freshness status
    CASE
        WHEN hours_since_update <= 1 THEN 'Real-time'
        WHEN hours_since_update <= 6 THEN 'Fresh'
        WHEN hours_since_update <= 24 THEN 'Acceptable'
        WHEN hours_since_update <= 48 THEN 'Stale'
        ELSE 'Critical'
    END AS freshness_status,
    -- SLA compliance (assuming 24-hour SLA)
    CASE
        WHEN hours_since_update <= 24 THEN 'Meeting SLA'
        ELSE 'Breaching SLA'
    END AS sla_status
FROM table_freshness
ORDER BY hours_since_update DESC;

-- =============================================================================
-- QUERY 5: Outlier Detection - Numerical Columns
-- =============================================================================
-- Purpose: Detect statistical outliers in key metrics
-- =============================================================================

WITH transaction_stats AS (
    SELECT
        AVG(net_amount) AS avg_amount,
        STDDEV(net_amount) AS stddev_amount,
        AVG(quantity) AS avg_quantity,
        STDDEV(quantity) AS stddev_quantity,
        AVG(profit_margin) AS avg_margin,
        STDDEV(profit_margin) AS stddev_margin
    FROM lakehouse_gold.fact_transactions
),
outlier_transactions AS (
    SELECT
        f.transaction_id,
        f.customer_sk,
        f.product_sk,
        f.net_amount,
        f.quantity,
        f.profit_margin,
        f.transaction_date,
        ts.avg_amount,
        ts.stddev_amount,
        -- Z-scores
        (f.net_amount - ts.avg_amount) / NULLIF(ts.stddev_amount, 0) AS amount_z_score,
        (f.quantity - ts.avg_quantity) / NULLIF(ts.stddev_quantity, 0) AS quantity_z_score,
        (f.profit_margin - ts.avg_margin) / NULLIF(ts.stddev_margin, 0) AS margin_z_score
    FROM lakehouse_gold.fact_transactions f
    CROSS JOIN transaction_stats ts
)
SELECT
    transaction_id,
    customer_sk,
    product_sk,
    net_amount,
    quantity,
    profit_margin,
    transaction_date,
    ROUND(amount_z_score, 2) AS amount_z_score,
    ROUND(quantity_z_score, 2) AS quantity_z_score,
    ROUND(margin_z_score, 2) AS margin_z_score,
    -- Outlier classification
    CASE
        WHEN ABS(amount_z_score) > 3 OR ABS(quantity_z_score) > 3 OR ABS(margin_z_score) > 3 THEN 'Extreme Outlier'
        WHEN ABS(amount_z_score) > 2 OR ABS(quantity_z_score) > 2 OR ABS(margin_z_score) > 2 THEN 'Moderate Outlier'
        ELSE 'Normal'
    END AS outlier_status,
    -- Specific outlier type
    CASE
        WHEN amount_z_score > 3 THEN 'Unusually High Amount'
        WHEN amount_z_score < -3 THEN 'Unusually Low Amount'
        WHEN quantity_z_score > 3 THEN 'Unusually High Quantity'
        WHEN quantity_z_score < -3 THEN 'Unusually Low Quantity'
        WHEN margin_z_score > 3 THEN 'Unusually High Margin'
        WHEN margin_z_score < -3 THEN 'Unusually Low Margin'
        ELSE 'Multiple Outliers'
    END AS outlier_type
FROM outlier_transactions
WHERE ABS(amount_z_score) > 2 OR ABS(quantity_z_score) > 2 OR ABS(margin_z_score) > 2
ORDER BY ABS(amount_z_score) DESC
LIMIT 1000;

-- =============================================================================
-- QUERY 6: Schema Drift Detection
-- =============================================================================
-- Purpose: Detect changes in data types, new columns, or schema modifications
-- =============================================================================

WITH current_schema AS (
    SELECT
        'fact_transactions' AS table_name,
        'customer_sk' AS column_name,
        'bigint' AS expected_type,
        COUNT(CASE WHEN TRY_CAST(customer_sk AS BIGINT) IS NULL THEN 1 END) AS type_mismatch_count
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    SELECT
        'fact_transactions' AS table_name,
        'net_amount' AS column_name,
        'double' AS expected_type,
        COUNT(CASE WHEN TRY_CAST(net_amount AS DOUBLE) IS NULL THEN 1 END) AS type_mismatch_count
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    SELECT
        'dim_customer' AS table_name,
        'email' AS column_name,
        'varchar' AS expected_type,
        COUNT(CASE WHEN email NOT LIKE '%@%' AND email IS NOT NULL THEN 1 END) AS type_mismatch_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true
)
SELECT
    table_name,
    column_name,
    expected_type,
    type_mismatch_count,
    CASE
        WHEN type_mismatch_count = 0 THEN 'Valid'
        WHEN type_mismatch_count < 10 THEN 'Minor Issues'
        WHEN type_mismatch_count < 100 THEN 'Moderate Issues'
        ELSE 'Critical Issues'
    END AS schema_health
FROM current_schema
ORDER BY type_mismatch_count DESC;

-- =============================================================================
-- QUERY 7: Data Validity Rules Validation
-- =============================================================================
-- Purpose: Validate business rules and data constraints
-- =============================================================================

WITH validation_results AS (
    -- Rule 1: Transaction amount should be positive
    SELECT
        'Transaction Amount Positive' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN net_amount <= 0 THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN net_amount <= 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    -- Rule 2: Quantity should be positive
    SELECT
        'Quantity Positive' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    -- Rule 3: Profit margin should be between -100 and 100
    SELECT
        'Profit Margin Range' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN profit_margin NOT BETWEEN -100 AND 100 THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN profit_margin NOT BETWEEN -100 AND 100 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    -- Rule 4: Email format validation
    SELECT
        'Email Format Valid' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN email NOT LIKE '%@%.%' AND email IS NOT NULL THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN email NOT LIKE '%@%.%' AND email IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true

    UNION ALL

    -- Rule 5: Phone number format (basic check)
    SELECT
        'Phone Format Valid' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '')) NOT BETWEEN 10 AND 15
                 AND phone IS NOT NULL THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '')) NOT BETWEEN 10 AND 15
                      AND phone IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true

    UNION ALL

    -- Rule 6: Product price should be greater than cost
    SELECT
        'Price Greater Than Cost' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN unit_price <= cost THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN unit_price <= cost THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.dim_product
    WHERE unit_price IS NOT NULL AND cost IS NOT NULL

    UNION ALL

    -- Rule 7: Transaction date should not be in the future
    SELECT
        'Transaction Date Valid' AS rule_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN transaction_date > CURRENT_DATE THEN 1 ELSE 0 END) AS violations,
        ROUND(SUM(CASE WHEN transaction_date > CURRENT_DATE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS violation_rate
    FROM lakehouse_gold.fact_transactions
)
SELECT
    rule_name,
    total_records,
    violations,
    violation_rate,
    CASE
        WHEN violation_rate = 0 THEN 'Pass'
        WHEN violation_rate < 0.1 THEN 'Warning'
        WHEN violation_rate < 1 THEN 'Fail'
        ELSE 'Critical Fail'
    END AS validation_status
FROM validation_results
ORDER BY violations DESC;

-- =============================================================================
-- QUERY 8: Consistency Check Across Layers
-- =============================================================================
-- Purpose: Ensure data consistency from bronze to silver to gold
-- =============================================================================

WITH gold_transaction_counts AS (
    SELECT
        DATE(transaction_date) AS transaction_date,
        COUNT(*) AS gold_count,
        SUM(net_amount) AS gold_amount
    FROM lakehouse_gold.fact_transactions
    WHERE transaction_date >= DATE_ADD('day', -7, CURRENT_DATE)
    GROUP BY DATE(transaction_date)
)
SELECT
    gtc.transaction_date,
    gtc.gold_count,
    gtc.gold_amount,
    ROUND(gtc.gold_amount, 2) AS rounded_gold_amount,
    -- Note: Would compare with silver/bronze if those tables have consistent schemas
    CASE
        WHEN gtc.gold_count > 0 THEN 'Data Present'
        ELSE 'Missing Data'
    END AS consistency_status
FROM gold_transaction_counts gtc
ORDER BY gtc.transaction_date DESC;

-- =============================================================================
-- QUERY 9: Timeliness & Processing Lag Monitoring
-- =============================================================================
-- Purpose: Measure lag between transaction time and processing time
-- =============================================================================

SELECT
    DATE(transaction_date) AS transaction_date,
    COUNT(*) AS transactions,
    AVG(DATE_DIFF('hour', transaction_timestamp, created_timestamp)) AS avg_processing_lag_hours,
    MIN(DATE_DIFF('hour', transaction_timestamp, created_timestamp)) AS min_processing_lag_hours,
    MAX(DATE_DIFF('hour', transaction_timestamp, created_timestamp)) AS max_processing_lag_hours,
    STDDEV(DATE_DIFF('hour', transaction_timestamp, created_timestamp)) AS stddev_processing_lag,
    -- SLA compliance (assuming 24-hour SLA)
    SUM(CASE WHEN DATE_DIFF('hour', transaction_timestamp, created_timestamp) <= 24 THEN 1 ELSE 0 END) AS within_sla,
    SUM(CASE WHEN DATE_DIFF('hour', transaction_timestamp, created_timestamp) > 24 THEN 1 ELSE 0 END) AS breached_sla,
    ROUND(SUM(CASE WHEN DATE_DIFF('hour', transaction_timestamp, created_timestamp) <= 24 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS sla_compliance_rate
FROM lakehouse_gold.fact_transactions
WHERE transaction_date >= DATE_ADD('day', -30, CURRENT_DATE)
    AND transaction_timestamp IS NOT NULL
    AND created_timestamp IS NOT NULL
GROUP BY DATE(transaction_date)
ORDER BY transaction_date DESC;

-- =============================================================================
-- QUERY 10: Data Quality Scorecard - Comprehensive
-- =============================================================================
-- Purpose: Generate overall data quality score for each table
-- =============================================================================

WITH dq_metrics AS (
    SELECT
        'fact_transactions' AS table_name,
        COUNT(*) AS total_records,
        -- Completeness
        ROUND((COUNT(transaction_id) + COUNT(customer_sk) + COUNT(product_sk) +
               COUNT(net_amount)) * 100.0 / (COUNT(*) * 4), 2) AS completeness_score,
        -- Validity
        ROUND((COUNT(*) - SUM(CASE WHEN net_amount <= 0 OR quantity <= 0 THEN 1 ELSE 0 END)) * 100.0 / COUNT(*), 2) AS validity_score,
        -- Uniqueness (transactions should have unique IDs)
        ROUND((COUNT(DISTINCT transaction_id) * 100.0 / COUNT(*)), 2) AS uniqueness_score,
        -- Timeliness
        CASE
            WHEN DATE_DIFF('hour', MAX(created_timestamp), CURRENT_TIMESTAMP) <= 24 THEN 100.0
            WHEN DATE_DIFF('hour', MAX(created_timestamp), CURRENT_TIMESTAMP) <= 48 THEN 80.0
            WHEN DATE_DIFF('hour', MAX(created_timestamp), CURRENT_TIMESTAMP) <= 72 THEN 60.0
            ELSE 40.0
        END AS timeliness_score
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    SELECT
        'dim_customer' AS table_name,
        COUNT(*) AS total_records,
        ROUND((COUNT(customer_id) + COUNT(customer_name) + COUNT(email)) * 100.0 / (COUNT(*) * 3), 2) AS completeness_score,
        ROUND((COUNT(*) - SUM(CASE WHEN email NOT LIKE '%@%' AND email IS NOT NULL THEN 1 ELSE 0 END)) * 100.0 / COUNT(*), 2) AS validity_score,
        ROUND((COUNT(DISTINCT customer_id) * 100.0 / COUNT(*)), 2) AS uniqueness_score,
        CASE
            WHEN DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) <= 24 THEN 100.0
            WHEN DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) <= 48 THEN 80.0
            WHEN DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) <= 72 THEN 60.0
            ELSE 40.0
        END AS timeliness_score
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true

    UNION ALL

    SELECT
        'dim_product' AS table_name,
        COUNT(*) AS total_records,
        ROUND((COUNT(product_id) + COUNT(product_name) + COUNT(category)) * 100.0 / (COUNT(*) * 3), 2) AS completeness_score,
        ROUND((COUNT(*) - SUM(CASE WHEN unit_price <= 0 OR cost < 0 THEN 1 ELSE 0 END)) * 100.0 / COUNT(*), 2) AS validity_score,
        ROUND((COUNT(DISTINCT product_id) * 100.0 / COUNT(*)), 2) AS uniqueness_score,
        CASE
            WHEN DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) <= 24 THEN 100.0
            WHEN DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) <= 48 THEN 80.0
            WHEN DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) <= 72 THEN 60.0
            ELSE 40.0
        END AS timeliness_score
    FROM lakehouse_gold.dim_product
)
SELECT
    table_name,
    total_records,
    completeness_score,
    validity_score,
    uniqueness_score,
    timeliness_score,
    -- Overall DQ score (weighted average)
    ROUND((completeness_score * 0.30 +
           validity_score * 0.30 +
           uniqueness_score * 0.20 +
           timeliness_score * 0.20), 2) AS overall_dq_score,
    -- Grade
    CASE
        WHEN (completeness_score * 0.30 + validity_score * 0.30 +
              uniqueness_score * 0.20 + timeliness_score * 0.20) >= 90 THEN 'A (Excellent)'
        WHEN (completeness_score * 0.30 + validity_score * 0.30 +
              uniqueness_score * 0.20 + timeliness_score * 0.20) >= 80 THEN 'B (Good)'
        WHEN (completeness_score * 0.30 + validity_score * 0.30 +
              uniqueness_score * 0.20 + timeliness_score * 0.20) >= 70 THEN 'C (Fair)'
        WHEN (completeness_score * 0.30 + validity_score * 0.30 +
              uniqueness_score * 0.20 + timeliness_score * 0.20) >= 60 THEN 'D (Poor)'
        ELSE 'F (Failed)'
    END AS dq_grade,
    CURRENT_TIMESTAMP AS scorecard_generated_at
FROM dq_metrics
ORDER BY overall_dq_score DESC;

-- =============================================================================
-- QUERY 11: Record Count Anomaly Detection
-- =============================================================================
-- Purpose: Detect unusual spikes or drops in record counts
-- =============================================================================

WITH daily_counts AS (
    SELECT
        DATE(transaction_date) AS transaction_date,
        COUNT(*) AS record_count
    FROM lakehouse_gold.fact_transactions
    WHERE transaction_date >= DATE_ADD('day', -90, CURRENT_DATE)
    GROUP BY DATE(transaction_date)
),
count_stats AS (
    SELECT
        AVG(record_count) AS avg_count,
        STDDEV(record_count) AS stddev_count
    FROM daily_counts
),
anomaly_detection AS (
    SELECT
        dc.transaction_date,
        dc.record_count,
        cs.avg_count,
        cs.stddev_count,
        (dc.record_count - cs.avg_count) / NULLIF(cs.stddev_count, 0) AS z_score,
        LAG(dc.record_count, 1) OVER (ORDER BY dc.transaction_date) AS prev_day_count
    FROM daily_counts dc
    CROSS JOIN count_stats cs
)
SELECT
    transaction_date,
    record_count,
    ROUND(avg_count, 0) AS expected_count,
    ROUND(z_score, 2) AS z_score,
    record_count - prev_day_count AS day_over_day_change,
    CASE
        WHEN prev_day_count > 0
        THEN ROUND((record_count - prev_day_count) * 100.0 / prev_day_count, 2)
        ELSE NULL
    END AS dod_change_pct,
    CASE
        WHEN ABS(z_score) > 3 THEN 'Critical Anomaly'
        WHEN ABS(z_score) > 2 THEN 'Significant Anomaly'
        WHEN ABS(z_score) > 1.5 THEN 'Minor Anomaly'
        ELSE 'Normal'
    END AS anomaly_status,
    CASE
        WHEN z_score > 0 THEN 'Higher than expected'
        WHEN z_score < 0 THEN 'Lower than expected'
        ELSE 'As expected'
    END AS variance_direction
FROM anomaly_detection
WHERE ABS(z_score) > 1.5
ORDER BY ABS(z_score) DESC;

-- =============================================================================
-- End of Data Quality Queries
-- =============================================================================
