-- ============================================================================
-- Gold Zone Business Metrics and KPIs
-- ============================================================================
-- Purpose: Advanced business intelligence queries on Gold zone aggregated data
-- Database: cloudmart_data_lake
-- Zone: Gold (business-ready aggregates)
-- ============================================================================

USE cloudmart_data_lake;

-- ============================================================================
-- SECTION 1: REVENUE TRENDS AND FORECASTING
-- ============================================================================

-- Query 1: Daily revenue with week-over-week comparison
-- Purpose: Track revenue trends with previous week comparison
SELECT
    order_date,
    total_revenue,
    total_orders,
    avg_order_value,
    LAG(total_revenue, 7) OVER (ORDER BY order_date) as revenue_7_days_ago,
    ROUND(
        (total_revenue - LAG(total_revenue, 7) OVER (ORDER BY order_date)) * 100.0 /
        NULLIF(LAG(total_revenue, 7) OVER (ORDER BY order_date), 0),
        2
    ) as wow_revenue_growth_pct,
    LAG(total_orders, 7) OVER (ORDER BY order_date) as orders_7_days_ago,
    ROUND(
        (total_orders - LAG(total_orders, 7) OVER (ORDER BY order_date)) * 100.0 /
        NULLIF(LAG(total_orders, 7) OVER (ORDER BY order_date), 0),
        2
    ) as wow_orders_growth_pct
FROM sales_summary
WHERE year = 2024
ORDER BY order_date DESC
LIMIT 90;

-- Query 2: Monthly revenue with month-over-month growth
-- Purpose: Track monthly performance trends
SELECT
    year,
    month,
    SUM(total_revenue) as monthly_revenue,
    SUM(total_orders) as monthly_orders,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    SUM(unique_customers) as total_unique_customers,
    LAG(SUM(total_revenue)) OVER (ORDER BY year, month) as prev_month_revenue,
    ROUND(
        (SUM(total_revenue) - LAG(SUM(total_revenue)) OVER (ORDER BY year, month)) * 100.0 /
        NULLIF(LAG(SUM(total_revenue)) OVER (ORDER BY year, month), 0),
        2
    ) as mom_growth_pct,
    ROUND(
        SUM(total_revenue) / SUM(unique_customers),
        2
    ) as revenue_per_customer
FROM sales_summary
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- Query 3: Rolling 7-day and 30-day revenue averages
-- Purpose: Smooth out daily volatility for trend analysis
SELECT
    order_date,
    total_revenue,
    ROUND(
        AVG(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) as rolling_7day_avg_revenue,
    ROUND(
        AVG(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ),
        2
    ) as rolling_30day_avg_revenue,
    ROUND(
        AVG(total_orders) OVER (
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) as rolling_7day_avg_orders
FROM sales_summary
WHERE year = 2024
ORDER BY order_date DESC
LIMIT 90;

-- Query 4: Year-over-year revenue comparison
-- Purpose: Compare performance across years
SELECT
    EXTRACT(MONTH FROM order_date) as month_number,
    EXTRACT(YEAR FROM order_date) as year,
    SUM(total_revenue) as monthly_revenue,
    SUM(total_orders) as monthly_orders,
    ROUND(AVG(avg_order_value), 2) as avg_order_value
FROM sales_summary
GROUP BY EXTRACT(YEAR FROM order_date), EXTRACT(MONTH FROM order_date)
ORDER BY month_number, year;

-- Query 5: Cumulative revenue tracking
-- Purpose: Track year-to-date revenue progress
SELECT
    order_date,
    year,
    month,
    total_revenue,
    SUM(total_revenue) OVER (
        PARTITION BY year
        ORDER BY order_date
    ) as ytd_revenue,
    ROUND(
        SUM(total_revenue) OVER (
            PARTITION BY year
            ORDER BY order_date
        ) / NULLIF(SUM(SUM(total_revenue)) OVER (PARTITION BY year), 0) * 100,
        2
    ) as ytd_revenue_pct
FROM sales_summary
WHERE year >= 2023
ORDER BY order_date DESC
LIMIT 100;

-- ============================================================================
-- SECTION 2: CUSTOMER RETENTION AND CHURN METRICS
-- ============================================================================

-- Query 6: Customer retention by cohort
-- Purpose: Track customer retention rates over time
SELECT
    customer_id,
    name,
    segment,
    total_orders,
    total_spent,
    first_order_date,
    last_order_date,
    days_since_last_order,
    CASE
        WHEN days_since_last_order <= 30 THEN 'Active'
        WHEN days_since_last_order <= 90 THEN 'At Risk'
        ELSE 'Churned'
    END as customer_status,
    churn_risk
FROM customer_360
WHERE total_orders >= 2
ORDER BY total_spent DESC;

-- Query 7: Customer churn analysis
-- Purpose: Identify and quantify customer churn
SELECT
    churn_risk,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    SUM(total_spent) as total_revenue,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(AVG(days_since_last_order), 1) as avg_days_since_last_order
FROM customer_360
GROUP BY churn_risk
ORDER BY
    CASE churn_risk
        WHEN 'Low' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'High' THEN 3
        ELSE 4
    END;

-- Query 8: Active vs inactive customer comparison
-- Purpose: Compare behavior of active and inactive customers
SELECT
    is_active,
    COUNT(*) as customer_count,
    SUM(total_orders) as total_orders,
    SUM(total_spent) as total_revenue,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(AVG(total_orders), 2) as avg_orders_per_customer,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    ROUND(AVG(days_since_last_order), 1) as avg_days_since_last_order
FROM customer_360
GROUP BY is_active
ORDER BY is_active DESC;

-- Query 9: Customer reactivation opportunities
-- Purpose: Identify customers for win-back campaigns
SELECT
    customer_id,
    name,
    email,
    segment,
    country,
    total_orders,
    total_spent,
    avg_order_value,
    last_order_date,
    days_since_last_order,
    favorite_category,
    churn_risk
FROM customer_360
WHERE is_active = false
    AND total_spent > 1000
    AND days_since_last_order BETWEEN 60 AND 180
ORDER BY total_spent DESC
LIMIT 100;

-- ============================================================================
-- SECTION 3: CUSTOMER SEGMENTATION AND LIFETIME VALUE
-- ============================================================================

-- Query 10: RFM (Recency, Frequency, Monetary) segmentation
-- Purpose: Segment customers based on RFM scores
SELECT
    customer_id,
    name,
    segment,
    total_orders as frequency,
    total_spent as monetary,
    days_since_last_order as recency,
    NTILE(5) OVER (ORDER BY days_since_last_order) as recency_score,
    NTILE(5) OVER (ORDER BY total_orders DESC) as frequency_score,
    NTILE(5) OVER (ORDER BY total_spent DESC) as monetary_score,
    NTILE(5) OVER (ORDER BY days_since_last_order) +
    NTILE(5) OVER (ORDER BY total_orders DESC) +
    NTILE(5) OVER (ORDER BY total_spent DESC) as rfm_score
FROM customer_360
WHERE total_orders >= 1
ORDER BY rfm_score DESC
LIMIT 100;

-- Query 11: Customer lifetime value by segment
-- Purpose: Compare CLV across customer segments
SELECT
    segment,
    COUNT(*) as customer_count,
    SUM(total_spent) as total_revenue,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_spent), 2) as median_lifetime_value,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_spent), 2) as p25_lifetime_value,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_spent), 2) as p75_lifetime_value,
    ROUND(AVG(total_orders), 2) as avg_orders,
    ROUND(AVG(avg_order_value), 2) as avg_order_value
FROM customer_360
GROUP BY segment
ORDER BY avg_lifetime_value DESC;

-- Query 12: Top 20% customers by revenue (Pareto analysis)
-- Purpose: Identify highest value customer segment
WITH ranked_customers AS (
    SELECT
        customer_id,
        name,
        segment,
        total_spent,
        total_orders,
        SUM(total_spent) OVER (ORDER BY total_spent DESC) as cumulative_revenue,
        SUM(total_spent) OVER () as total_revenue,
        ROW_NUMBER() OVER (ORDER BY total_spent DESC) as customer_rank,
        COUNT(*) OVER () as total_customers
    FROM customer_360
)
SELECT
    customer_id,
    name,
    segment,
    total_spent,
    total_orders,
    customer_rank,
    ROUND(customer_rank * 100.0 / total_customers, 2) as customer_percentile,
    ROUND(cumulative_revenue * 100.0 / total_revenue, 2) as cumulative_revenue_pct
FROM ranked_customers
WHERE customer_rank * 100.0 / total_customers <= 20
ORDER BY customer_rank;

-- Query 13: Customer value quartiles
-- Purpose: Segment customers into value quartiles
SELECT
    value_quartile,
    COUNT(*) as customer_count,
    SUM(total_spent) as total_revenue,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(AVG(total_orders), 2) as avg_orders,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as customer_pct,
    ROUND(SUM(total_spent) * 100.0 / SUM(SUM(total_spent)) OVER(), 2) as revenue_pct
FROM (
    SELECT
        customer_id,
        total_spent,
        total_orders,
        avg_order_value,
        NTILE(4) OVER (ORDER BY total_spent) as value_quartile
    FROM customer_360
)
GROUP BY value_quartile
ORDER BY value_quartile DESC;

-- ============================================================================
-- SECTION 4: PRODUCT AND CATEGORY PERFORMANCE
-- ============================================================================

-- Query 14: Daily top performing categories
-- Purpose: Track which categories drive the most revenue each day
SELECT
    order_date,
    top_category,
    total_revenue,
    total_orders,
    RANK() OVER (PARTITION BY order_date ORDER BY total_revenue DESC) as category_rank
FROM sales_summary
WHERE year = 2024
    AND top_category IS NOT NULL
ORDER BY order_date DESC, total_revenue DESC
LIMIT 100;

-- Query 15: Category revenue trends
-- Purpose: Analyze category performance over time
SELECT
    DATE_TRUNC('week', order_date) as week_start,
    top_category,
    SUM(total_revenue) as weekly_revenue,
    SUM(total_orders) as weekly_orders,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    LAG(SUM(total_revenue)) OVER (
        PARTITION BY top_category
        ORDER BY DATE_TRUNC('week', order_date)
    ) as prev_week_revenue,
    ROUND(
        (SUM(total_revenue) - LAG(SUM(total_revenue)) OVER (
            PARTITION BY top_category
            ORDER BY DATE_TRUNC('week', order_date)
        )) * 100.0 /
        NULLIF(LAG(SUM(total_revenue)) OVER (
            PARTITION BY top_category
            ORDER BY DATE_TRUNC('week', order_date)
        ), 0),
        2
    ) as wow_growth_pct
FROM sales_summary
WHERE year = 2024 AND top_category IS NOT NULL
GROUP BY DATE_TRUNC('week', order_date), top_category
ORDER BY week_start DESC, weekly_revenue DESC;

-- Query 16: Customer favorite categories
-- Purpose: Analyze customer preferences by segment
SELECT
    segment,
    favorite_category,
    COUNT(*) as customer_count,
    ROUND(AVG(total_spent), 2) as avg_customer_value,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY segment), 2) as pct_of_segment
FROM customer_360
WHERE favorite_category IS NOT NULL
GROUP BY segment, favorite_category
ORDER BY segment, customer_count DESC;

-- ============================================================================
-- SECTION 5: ORDER FULFILLMENT AND OPERATIONAL METRICS
-- ============================================================================

-- Query 17: Order completion rate trends
-- Purpose: Track order fulfillment efficiency
SELECT
    order_date,
    total_orders,
    completed_orders,
    cancelled_orders,
    pending_orders,
    ROUND(completed_orders * 100.0 / NULLIF(total_orders, 0), 2) as completion_rate,
    ROUND(cancelled_orders * 100.0 / NULLIF(total_orders, 0), 2) as cancellation_rate,
    ROUND(pending_orders * 100.0 / NULLIF(total_orders, 0), 2) as pending_rate,
    total_revenue,
    ROUND(total_revenue * completed_orders / NULLIF(total_orders, 0), 2) as completed_revenue
FROM sales_summary
WHERE year = 2024
ORDER BY order_date DESC
LIMIT 90;

-- Query 18: Weekly operational performance
-- Purpose: Aggregate weekly operational metrics
SELECT
    DATE_TRUNC('week', order_date) as week_start,
    SUM(total_orders) as weekly_orders,
    SUM(completed_orders) as weekly_completed,
    SUM(cancelled_orders) as weekly_cancelled,
    ROUND(SUM(completed_orders) * 100.0 / NULLIF(SUM(total_orders), 0), 2) as completion_rate,
    ROUND(SUM(cancelled_orders) * 100.0 / NULLIF(SUM(total_orders), 0), 2) as cancellation_rate,
    SUM(total_revenue) as weekly_revenue,
    ROUND(AVG(avg_order_value), 2) as avg_order_value
FROM sales_summary
WHERE year = 2024
GROUP BY DATE_TRUNC('week', order_date)
ORDER BY week_start DESC;

-- ============================================================================
-- SECTION 6: GEOGRAPHIC PERFORMANCE METRICS
-- ============================================================================

-- Query 19: Customer distribution and performance by country
-- Purpose: Analyze geographic market performance
SELECT
    country,
    COUNT(*) as customer_count,
    SUM(total_spent) as total_revenue,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    SUM(total_orders) as total_orders,
    ROUND(AVG(total_orders), 2) as avg_orders_per_customer,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    COUNT(CASE WHEN is_active THEN 1 END) as active_customers,
    ROUND(COUNT(CASE WHEN is_active THEN 1 END) * 100.0 / COUNT(*), 2) as active_customer_pct,
    RANK() OVER (ORDER BY SUM(total_spent) DESC) as country_rank
FROM customer_360
GROUP BY country
ORDER BY total_revenue DESC;

-- Query 20: Geographic expansion opportunities
-- Purpose: Identify markets with growth potential
SELECT
    country,
    segment,
    COUNT(*) as customer_count,
    SUM(total_spent) as total_revenue,
    ROUND(AVG(total_spent), 2) as avg_customer_value,
    COUNT(CASE WHEN is_active THEN 1 END) as active_customers,
    ROUND(SUM(total_spent) / COUNT(*) * COUNT(CASE WHEN is_active THEN 1 END), 2) as potential_revenue
FROM customer_360
GROUP BY country, segment
HAVING COUNT(*) >= 10
ORDER BY potential_revenue DESC
LIMIT 50;

-- ============================================================================
-- SECTION 7: ADVANCED COHORT AND RETENTION ANALYSIS
-- ============================================================================

-- Query 21: Monthly cohort retention matrix
-- Purpose: Track customer retention by signup cohort
SELECT
    DATE_TRUNC('month', signup_date) as cohort_month,
    COUNT(DISTINCT customer_id) as cohort_size,
    COUNT(DISTINCT CASE WHEN is_active THEN customer_id END) as still_active,
    ROUND(
        COUNT(DISTINCT CASE WHEN is_active THEN customer_id END) * 100.0 /
        NULLIF(COUNT(DISTINCT customer_id), 0),
        2
    ) as retention_rate,
    SUM(total_spent) as cohort_total_revenue,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(AVG(CAST(days_since_last_order AS DOUBLE)), 1) as avg_days_since_last_order
FROM customer_360
WHERE signup_date >= DATE '2023-01-01'
GROUP BY DATE_TRUNC('month', signup_date)
ORDER BY cohort_month DESC;

-- Query 22: Customer journey milestones
-- Purpose: Analyze customer progression through order milestones
SELECT
    order_milestone,
    COUNT(*) as customer_count,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    ROUND(AVG(days_since_last_order), 1) as avg_days_since_last_order,
    COUNT(CASE WHEN is_active THEN 1 END) as active_customers,
    ROUND(COUNT(CASE WHEN is_active THEN 1 END) * 100.0 / COUNT(*), 2) as active_pct
FROM (
    SELECT
        *,
        CASE
            WHEN total_orders = 1 THEN '1. First Purchase'
            WHEN total_orders BETWEEN 2 AND 3 THEN '2. Repeat (2-3)'
            WHEN total_orders BETWEEN 4 AND 9 THEN '3. Regular (4-9)'
            WHEN total_orders >= 10 THEN '4. Loyal (10+)'
        END as order_milestone
    FROM customer_360
)
GROUP BY order_milestone
ORDER BY order_milestone;

-- ============================================================================
-- SECTION 8: PREDICTIVE AND ANOMALY DETECTION QUERIES
-- ============================================================================

-- Query 23: Revenue anomaly detection
-- Purpose: Identify unusual revenue patterns
SELECT
    order_date,
    total_revenue,
    ROUND(AVG(total_revenue) OVER (
        ORDER BY order_date
        ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
    ), 2) as avg_revenue_30d,
    ROUND(STDDEV(total_revenue) OVER (
        ORDER BY order_date
        ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
    ), 2) as stddev_revenue_30d,
    ROUND(
        (total_revenue - AVG(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        )) / NULLIF(STDDEV(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ), 0),
        2
    ) as z_score,
    CASE
        WHEN ABS((total_revenue - AVG(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        )) / NULLIF(STDDEV(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ), 0)) > 2 THEN 'Anomaly'
        ELSE 'Normal'
    END as anomaly_flag
FROM sales_summary
WHERE year = 2024
ORDER BY order_date DESC
LIMIT 90;

-- Query 24: High-value customer risk assessment
-- Purpose: Identify at-risk high-value customers
SELECT
    customer_id,
    name,
    email,
    segment,
    total_spent,
    total_orders,
    avg_order_value,
    last_order_date,
    days_since_last_order,
    churn_risk,
    CASE
        WHEN total_spent >= 10000 AND days_since_last_order > 60 THEN 'Critical'
        WHEN total_spent >= 5000 AND days_since_last_order > 90 THEN 'High'
        WHEN total_spent >= 2000 AND days_since_last_order > 120 THEN 'Medium'
        ELSE 'Low'
    END as revenue_risk_level,
    ROUND(total_spent / NULLIF(DATE_DIFF('day', first_order_date, last_order_date), 0) * 365, 2) as annualized_value
FROM customer_360
WHERE total_spent >= 2000
    AND days_since_last_order > 60
ORDER BY total_spent DESC, days_since_last_order DESC
LIMIT 100;

-- Query 25: Executive dashboard summary
-- Purpose: Key metrics for executive reporting
SELECT
    'Executive Summary - Last 30 Days' as report_title,
    SUM(total_revenue) as total_revenue_30d,
    SUM(total_orders) as total_orders_30d,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    SUM(unique_customers) as total_customers_30d,
    SUM(completed_orders) as completed_orders,
    SUM(cancelled_orders) as cancelled_orders,
    ROUND(SUM(completed_orders) * 100.0 / NULLIF(SUM(total_orders), 0), 2) as completion_rate,
    (SELECT COUNT(*) FROM customer_360 WHERE is_active = true) as total_active_customers,
    (SELECT COUNT(*) FROM customer_360 WHERE churn_risk = 'High') as high_churn_risk_customers,
    (SELECT SUM(total_spent) FROM customer_360 WHERE churn_risk = 'High') as at_risk_revenue
FROM sales_summary
WHERE order_date >= CURRENT_DATE - INTERVAL '30' DAY;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. These queries are designed for Gold zone aggregated data
-- 2. Use for executive dashboards, KPI tracking, and strategic planning
-- 3. Queries include advanced window functions (LAG, LEAD, RANK, NTILE, PERCENTILE)
-- 4. Results are suitable for visualization in BI tools
-- 5. Combine with date filters for specific time periods
--
-- Performance considerations:
-- - Gold zone tables are pre-aggregated for optimal performance
-- - Use partition filters for large date ranges
-- - Consider materializing complex calculations as views
-- - Schedule regular refreshes of Gold zone tables
-- ============================================================================
