-- ============================================================================
-- Silver Zone Analytics Queries
-- ============================================================================
-- Purpose: Analytical queries on cleaned and conformed data in Silver zone
-- Database: cloudmart_data_lake
-- Zone: Silver (cleaned data)
-- ============================================================================

USE cloudmart_data_lake;

-- ============================================================================
-- SECTION 1: BASIC AGGREGATIONS AND METRICS
-- ============================================================================

-- Query 1: Daily order metrics
-- Purpose: Track daily order volume and revenue
SELECT
    order_date,
    COUNT(*) as total_orders,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    ROUND(MIN(total_amount), 2) as min_order_value,
    ROUND(MAX(total_amount), 2) as max_order_value,
    ROUND(STDDEV(total_amount), 2) as stddev_order_value
FROM processed_orders
WHERE year = 2024
GROUP BY order_date
ORDER BY order_date DESC;

-- Query 2: Weekly order trends
-- Purpose: Analyze weekly performance patterns
SELECT
    DATE_TRUNC('week', order_date) as week_start,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(SUM(total_amount) / COUNT(DISTINCT customer_id), 2) as revenue_per_customer
FROM processed_orders
WHERE year = 2024
GROUP BY DATE_TRUNC('week', order_date)
ORDER BY week_start DESC;

-- Query 3: Monthly revenue and growth trends
-- Purpose: Track monthly performance and growth
SELECT
    year,
    month,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers,
    LAG(SUM(total_amount)) OVER (ORDER BY year, month) as prev_month_revenue,
    ROUND(
        (SUM(total_amount) - LAG(SUM(total_amount)) OVER (ORDER BY year, month)) * 100.0 /
        NULLIF(LAG(SUM(total_amount)) OVER (ORDER BY year, month), 0),
        2
    ) as revenue_growth_pct
FROM processed_orders
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- Query 4: Order status breakdown
-- Purpose: Analyze order fulfillment metrics
SELECT
    status,
    COUNT(*) as order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM processed_orders
WHERE year = 2024 AND month >= 1
GROUP BY status
ORDER BY order_count DESC;

-- ============================================================================
-- SECTION 2: CUSTOMER ANALYTICS
-- ============================================================================

-- Query 5: Customer segment performance
-- Purpose: Compare metrics across customer segments
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id) as customer_count,
    COUNT(o.order_id) as total_orders,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    SUM(o.total_amount) as total_revenue,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer,
    ROUND(COUNT(o.order_id) * 1.0 / COUNT(DISTINCT c.customer_id), 2) as avg_orders_per_customer
FROM processed_customers c
LEFT JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE o.year = 2024
GROUP BY c.segment
ORDER BY total_revenue DESC;

-- Query 6: Customer cohort analysis by signup month
-- Purpose: Analyze customer behavior by acquisition cohort
SELECT
    DATE_TRUNC('month', c.signup_date) as cohort_month,
    COUNT(DISTINCT c.customer_id) as cohort_size,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    ROUND(COUNT(o.order_id) * 1.0 / COUNT(DISTINCT c.customer_id), 2) as orders_per_customer,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer
FROM processed_customers c
LEFT JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE c.signup_date >= DATE '2024-01-01'
GROUP BY DATE_TRUNC('month', c.signup_date)
ORDER BY cohort_month DESC;

-- Query 7: Top customers by revenue
-- Purpose: Identify highest value customers
SELECT
    c.customer_id,
    c.name,
    c.email,
    c.country,
    c.segment,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    MIN(o.order_date) as first_order_date,
    MAX(o.order_date) as last_order_date,
    DATE_DIFF('day', MAX(o.order_date), CURRENT_DATE) as days_since_last_order
FROM processed_customers c
INNER JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE o.year = 2024
GROUP BY c.customer_id, c.name, c.email, c.country, c.segment
ORDER BY total_revenue DESC
LIMIT 100;

-- Query 8: Customer purchase frequency distribution
-- Purpose: Understand customer engagement levels
SELECT
    order_frequency_bucket,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM (
    SELECT
        customer_id,
        CASE
            WHEN order_count = 1 THEN '1 order'
            WHEN order_count BETWEEN 2 AND 5 THEN '2-5 orders'
            WHEN order_count BETWEEN 6 AND 10 THEN '6-10 orders'
            WHEN order_count BETWEEN 11 AND 20 THEN '11-20 orders'
            ELSE '20+ orders'
        END as order_frequency_bucket
    FROM (
        SELECT
            customer_id,
            COUNT(*) as order_count
        FROM processed_orders
        WHERE year = 2024
        GROUP BY customer_id
    )
)
GROUP BY order_frequency_bucket
ORDER BY
    CASE order_frequency_bucket
        WHEN '1 order' THEN 1
        WHEN '2-5 orders' THEN 2
        WHEN '6-10 orders' THEN 3
        WHEN '11-20 orders' THEN 4
        ELSE 5
    END;

-- Query 9: Customer geographic distribution
-- Purpose: Analyze customer base by geography
SELECT
    c.country,
    COUNT(DISTINCT c.customer_id) as customer_count,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    ROUND(COUNT(o.order_id) * 1.0 / COUNT(DISTINCT c.customer_id), 2) as orders_per_customer,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as customer_pct
FROM processed_customers c
LEFT JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE o.year = 2024
GROUP BY c.country
ORDER BY total_revenue DESC;

-- Query 10: New vs returning customer analysis
-- Purpose: Track customer acquisition and retention
SELECT
    o.order_date,
    COUNT(DISTINCT o.customer_id) as total_customers,
    COUNT(DISTINCT CASE
        WHEN first_order.first_order_date = o.order_date
        THEN o.customer_id
    END) as new_customers,
    COUNT(DISTINCT CASE
        WHEN first_order.first_order_date < o.order_date
        THEN o.customer_id
    END) as returning_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN first_order.first_order_date = o.order_date THEN o.customer_id END) * 100.0 /
        COUNT(DISTINCT o.customer_id),
        2
    ) as new_customer_pct
FROM processed_orders o
INNER JOIN (
    SELECT
        customer_id,
        MIN(order_date) as first_order_date
    FROM processed_orders
    GROUP BY customer_id
) first_order ON o.customer_id = first_order.customer_id
WHERE o.year = 2024 AND o.month >= 1
GROUP BY o.order_date
ORDER BY o.order_date DESC;

-- ============================================================================
-- SECTION 3: PRODUCT ANALYTICS
-- ============================================================================

-- Query 11: Product category performance
-- Purpose: Analyze sales by product category
SELECT
    p.category,
    COUNT(DISTINCT p.product_id) as product_count,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    ROUND(AVG(p.price), 2) as avg_product_price,
    ROUND(SUM(o.total_amount) / COUNT(o.order_id), 2) as avg_order_value
FROM processed_products p
LEFT JOIN processed_orders o ON o.year = 2024
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Query 12: Top selling products
-- Purpose: Identify best performing products
-- Note: This assumes product_id can be extracted from order data
SELECT
    p.product_id,
    p.name,
    p.category,
    p.price,
    COUNT(*) as order_count,
    SUM(p.price) as total_revenue,
    p.stock_quantity
FROM processed_products p
WHERE p.year = 2024
GROUP BY p.product_id, p.name, p.category, p.price, p.stock_quantity
ORDER BY order_count DESC
LIMIT 50;

-- Query 13: Product price range analysis
-- Purpose: Analyze sales distribution by price points
SELECT
    price_range,
    COUNT(DISTINCT product_id) as product_count,
    ROUND(AVG(price), 2) as avg_price,
    SUM(stock_quantity) as total_stock
FROM (
    SELECT
        product_id,
        name,
        category,
        price,
        stock_quantity,
        CASE
            WHEN price < 50 THEN '$0-49'
            WHEN price BETWEEN 50 AND 99 THEN '$50-99'
            WHEN price BETWEEN 100 AND 199 THEN '$100-199'
            WHEN price BETWEEN 200 AND 499 THEN '$200-499'
            ELSE '$500+'
        END as price_range
    FROM processed_products
    WHERE year = 2024
)
GROUP BY price_range
ORDER BY
    CASE price_range
        WHEN '$0-49' THEN 1
        WHEN '$50-99' THEN 2
        WHEN '$100-199' THEN 3
        WHEN '$200-499' THEN 4
        ELSE 5
    END;

-- Query 14: Inventory analysis
-- Purpose: Identify stock levels and potential issues
SELECT
    category,
    COUNT(*) as total_products,
    SUM(stock_quantity) as total_stock,
    ROUND(AVG(stock_quantity), 2) as avg_stock_per_product,
    COUNT(CASE WHEN stock_quantity = 0 THEN 1 END) as out_of_stock_count,
    COUNT(CASE WHEN stock_quantity < 10 THEN 1 END) as low_stock_count,
    ROUND(COUNT(CASE WHEN stock_quantity = 0 THEN 1 END) * 100.0 / COUNT(*), 2) as out_of_stock_pct
FROM processed_products
WHERE year = 2024
GROUP BY category
ORDER BY out_of_stock_pct DESC;

-- ============================================================================
-- SECTION 4: TIME-BASED ANALYTICS
-- ============================================================================

-- Query 15: Day of week analysis
-- Purpose: Identify weekly patterns in order behavior
SELECT
    CASE EXTRACT(DOW FROM order_date)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_of_week,
    EXTRACT(DOW FROM order_date) as dow_number,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM processed_orders
WHERE year = 2024
GROUP BY EXTRACT(DOW FROM order_date)
ORDER BY dow_number;

-- Query 16: Hour of day analysis (from timestamp)
-- Purpose: Identify peak ordering times
SELECT
    EXTRACT(HOUR FROM order_timestamp) as hour_of_day,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM processed_orders
WHERE year = 2024
GROUP BY EXTRACT(HOUR FROM order_timestamp)
ORDER BY hour_of_day;

-- Query 17: Seasonal trends analysis
-- Purpose: Identify seasonal patterns in sales
SELECT
    CASE
        WHEN month IN (12, 1, 2) THEN 'Winter'
        WHEN month IN (3, 4, 5) THEN 'Spring'
        WHEN month IN (6, 7, 8) THEN 'Summer'
        WHEN month IN (9, 10, 11) THEN 'Fall'
    END as season,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM processed_orders
WHERE year = 2024
GROUP BY
    CASE
        WHEN month IN (12, 1, 2) THEN 'Winter'
        WHEN month IN (3, 4, 5) THEN 'Spring'
        WHEN month IN (6, 7, 8) THEN 'Summer'
        WHEN month IN (9, 10, 11) THEN 'Fall'
    END
ORDER BY total_revenue DESC;

-- ============================================================================
-- SECTION 5: MULTI-TABLE JOIN ANALYTICS
-- ============================================================================

-- Query 18: Customer-Order-Product combined analysis
-- Purpose: Comprehensive customer purchasing behavior
SELECT
    c.customer_id,
    c.name,
    c.segment,
    c.country,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    SUM(o.product_count) as total_items_purchased,
    ROUND(SUM(o.product_count) * 1.0 / COUNT(o.order_id), 2) as avg_items_per_order,
    DATE_DIFF('day', c.signup_date, MAX(o.order_date)) as customer_tenure_days,
    DATE_DIFF('day', MAX(o.order_date), CURRENT_DATE) as days_since_last_purchase
FROM processed_customers c
INNER JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE o.year = 2024
GROUP BY c.customer_id, c.name, c.segment, c.country, c.signup_date
HAVING COUNT(o.order_id) >= 5
ORDER BY total_spent DESC
LIMIT 100;

-- Query 19: Geographic revenue distribution
-- Purpose: Analyze revenue by geographic segments
SELECT
    c.country,
    c.segment,
    COUNT(DISTINCT c.customer_id) as customer_count,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer
FROM processed_customers c
INNER JOIN processed_orders o ON c.customer_id = o.customer_id
WHERE o.year = 2024
GROUP BY c.country, c.segment
ORDER BY total_revenue DESC;

-- Query 20: Customer lifetime value estimation
-- Purpose: Calculate customer value metrics
SELECT
    c.customer_id,
    c.name,
    c.segment,
    c.signup_date,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_lifetime_value,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    MIN(o.order_date) as first_order_date,
    MAX(o.order_date) as last_order_date,
    DATE_DIFF('day', MIN(o.order_date), MAX(o.order_date)) as active_days,
    CASE
        WHEN DATE_DIFF('day', MIN(o.order_date), MAX(o.order_date)) > 0
        THEN ROUND(SUM(o.total_amount) / DATE_DIFF('day', MIN(o.order_date), MAX(o.order_date)) * 30, 2)
        ELSE 0
    END as estimated_monthly_value
FROM processed_customers c
INNER JOIN processed_orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.segment, c.signup_date
HAVING COUNT(o.order_id) >= 3
ORDER BY total_lifetime_value DESC
LIMIT 100;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. Run these queries on Silver zone data for analytical insights
-- 2. Modify date filters and limits based on your analysis needs
-- 3. Use results to populate dashboards and reports
-- 4. Combine queries for deeper multi-dimensional analysis
-- 5. Export results for visualization in BI tools
--
-- Performance tips:
-- - Use partition filters (year, month) for better query performance
-- - Add date range filters to limit data scanned
-- - Create views for frequently used query patterns
-- - Consider materializing complex aggregations to Gold zone
-- ============================================================================
