-- Exercise 06: Athena Query Examples
-- Run these queries after setting up the Glue Catalog

-- 1. Basic SELECT: Get first 10 transactions
SELECT *
FROM globalmart.transactions
LIMIT 10;

-- 2. Aggregation: Total revenue by country
SELECT
    country,
    COUNT(*) as transaction_count,
    ROUND(SUM(amount), 2) as total_revenue,
    ROUND(AVG(amount), 2) as avg_transaction
FROM globalmart.transactions
WHERE status = 'completed'
GROUP BY country
ORDER BY total_revenue DESC;

-- 3. Time-based analysis: Revenue by month
SELECT
    year,
    month,
    COUNT(*) as transactions,
    ROUND(SUM(amount), 2) as revenue
FROM globalmart.transactions
WHERE status = 'completed'
GROUP BY year, month
ORDER BY year, month;

-- 4. Partition pruning: Query specific date (FAST!)
SELECT
    transaction_id,
    amount,
    timestamp,
    country
FROM globalmart.transactions
WHERE year = 2024
  AND month = 1
  AND day = 15
  AND status = 'completed'
ORDER BY amount DESC
LIMIT 20;

-- 5. JOIN: Transactions with user details
SELECT
    t.transaction_id,
    t.amount,
    t.timestamp,
    u.email,
    u.first_name,
    u.last_name,
    u.country
FROM globalmart.transactions t
JOIN globalmart.users u ON t.user_id = u.user_id
WHERE t.year = 2024
  AND t.month = 1
LIMIT 100;

-- 6. Window functions: Running total by country
SELECT
    country,
    DATE(timestamp) as date,
    amount,
    SUM(amount) OVER (
        PARTITION BY country
        ORDER BY timestamp
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as running_total
FROM globalmart.transactions
WHERE year = 2024 AND month = 1
ORDER BY country, timestamp
LIMIT 50;

-- 7. User cohort analysis
SELECT
    DATE_TRUNC('month', registration_date) as cohort_month,
    country,
    COUNT(*) as users,
    ROUND(AVG(age), 1) as avg_age
FROM globalmart.users
GROUP BY DATE_TRUNC('month', registration_date), country
ORDER BY cohort_month DESC, users DESC;

-- 8. Top customers by revenue
SELECT
    u.user_id,
    u.email,
    u.country,
    COUNT(t.transaction_id) as purchase_count,
    ROUND(SUM(t.amount), 2) as lifetime_value
FROM globalmart.users u
LEFT JOIN globalmart.transactions t ON u.user_id = t.user_id
WHERE t.status = 'completed'
GROUP BY u.user_id, u.email, u.country
HAVING COUNT(t.transaction_id) >= 5
ORDER BY lifetime_value DESC
LIMIT 20;

-- 9. Performance comparison: With vs Without partition filter
-- SLOW (scans entire dataset):
-- SELECT COUNT(*) FROM globalmart.transactions WHERE amount > 200;

-- FAST (uses partition pruning):
SELECT COUNT(*)
FROM globalmart.transactions
WHERE year = 2024
  AND month = 1
  AND amount > 200;

-- 10. CTAS: Create optimized table from query
CREATE TABLE globalmart.daily_summary
WITH (
    format = 'PARQUET',
    parquet_compression = 'SNAPPY',
    external_location = 's3://your-bucket/gold/daily_summary/'
) AS
SELECT
    DATE(timestamp) as date,
    country,
    COUNT(*) as transaction_count,
    ROUND(SUM(amount), 2) as total_revenue,
    ROUND(AVG(amount), 2) as avg_transaction,
    COUNT(DISTINCT user_id) as unique_users
FROM globalmart.transactions
WHERE status = 'completed'
  AND year = 2024
GROUP BY DATE(timestamp), country;

-- Useful maintenance queries:

-- Add partitions manually (if needed)
ALTER TABLE globalmart.transactions
ADD PARTITION (year=2024, month=1, day=1)
LOCATION 's3://your-bucket/silver/transactions/year=2024/month=1/day=1/';

-- Update statistics for better query performance
ANALYZE TABLE globalmart.transactions COMPUTE STATISTICS;

-- Show table properties
SHOW CREATE TABLE globalmart.transactions;

-- List all partitions
SHOW PARTITIONS globalmart.transactions;
