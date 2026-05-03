-- ============================================================================
-- SQL Exercises for CloudMart Data Lake - STARTER TEMPLATE
-- ============================================================================
-- Complete these SQL exercises to practice querying your data lake with Athena
-- Each exercise has a TODO section with hints
-- Test your queries and verify results make sense
-- ============================================================================

-- ============================================================================
-- SETUP: Set the working database
-- ============================================================================
USE cloudmart_silver_dev;

-- ============================================================================
-- EXERCISE 1: Count total orders by date
-- ============================================================================
-- TODO: Write a query to count the number of orders for each order_date
-- HINT: Use GROUP BY order_date and COUNT(*)
-- Expected output: date | order_count
-- ORDER BY date DESC

-- Your query here:




-- ============================================================================
-- EXERCISE 2: Calculate total revenue by country
-- ============================================================================
-- TODO: Join orders with customers and calculate total revenue by country
-- HINT: JOIN orders ON customer_id, GROUP BY country, SUM(total_amount)
-- Expected output: country | total_revenue
-- ORDER BY total_revenue DESC

-- Your query here:




-- ============================================================================
-- EXERCISE 3: Find top 10 customers by total spend
-- ============================================================================
-- TODO: Calculate total spend per customer and rank top 10
-- HINT: GROUP BY customer_id, JOIN with customers for name, ORDER BY total DESC, LIMIT 10
-- Expected output: customer_name | email | total_spent | order_count

-- Your query here:




-- ============================================================================
-- EXERCISE 4: Calculate average order value by month
-- ============================================================================
-- TODO: Calculate AVG(total_amount) grouped by year and month
-- HINT: Extract year and month from order_date,GROUP BY year, month
-- Expected output: year | month | avg_order_value | total_orders
-- Bonus: Add a column for total_revenue

-- Your query here:




-- ============================================================================
-- EXERCISE 5: Find orders with above-average value
-- ============================================================================
-- TODO: Select orders where total_amount > average of all orders
-- HINT: Use a subquery: SELECT * FROM orders WHERE total_amount > (SELECT AVG(total_amount) FROM orders)
-- Expected output: order_id | customer_id | total_amount | order_date

-- Your query here:




-- ============================================================================
-- EXERCISE 6: Calculate month-over-month revenue growth
-- ============================================================================
-- TODO: Calculate revenue by month and MoM growth percentage
-- HINT: Use LAG() window function to get previous month's revenue
-- Formula: (current_revenue - previous_revenue) / previous_revenue * 100
-- Expected output: year | month | revenue | prev_month_revenue | growth_pct

-- Your query here:
-- WITH monthly_revenue AS (
--   SELECT ...
-- )
-- SELECT
--   year, month, revenue,
--   LAG(revenue, 1) OVER (ORDER BY year, month) as prev_month_revenue,
--   ...
-- FROM monthly_revenue;




-- ============================================================================
-- EXERCISE 7: Customer retention analysis
-- ============================================================================
-- TODO: Find customers who made purchases in consecutive months
-- HINT: Self-join orders on customer_id where MONTH(order_date) differs by 1
-- Expected output: customer_id | month1 | month2 | retained

-- Your query here:




-- ============================================================================
-- EXERCISE 8: Product category performance
-- ============================================================================
-- TODO: Join orders with products and calculate metrics by category
-- HINT: GROUP BY product category, calculate total revenue, quantity, avg price
-- Expected output: category | total_revenue | total_quantity | avg_price | product_count

-- Your query here:




-- ============================================================================
-- EXERCISE 9: Identify dormant customers
-- ============================================================================
-- TODO: Find customers who haven't ordered in the last 90 days
-- HINT: Use MAX(order_date) per customer, filter where days difference > 90
-- Expected output: customer_id | email | last_order_date | days_since_last_order

-- Your query here:
-- SELECT
--   c.customer_id,
--   c.email,
--   MAX(o.order_date) as last_order_date,
--   DATE_DIFF('day', MAX(o.order_date), CURRENT_DATE) as days_since_last_order
-- FROM customers c
-- JOIN orders o ON ...
-- WHERE ...




-- ============================================================================
-- EXERCISE 10: Calculate customer lifetime value percentiles
-- ============================================================================
-- TODO: Calculate total spend per customer and find 25th, 50th, 75th, 90th percentiles
-- HINT: Use APPROX_PERCENTILE() function
-- Expected output: percentile_25 | percentile_50 | percentile_75 | percentile_90

-- Your query here:
-- WITH customer_spend AS (
--   SELECT customer_id, SUM(total_amount) as total_spent
--   FROM orders
--   GROUP BY customer_id
-- )
-- SELECT
--   APPROX_PERCENTILE(total_spent, 0.25) as percentile_25,
--   ...




-- ============================================================================
-- EXERCISE 11: Weekly sales trend with moving average
-- ============================================================================
-- TODO: Calculate weekly revenue and 4-week moving average
-- HINT: Use DATE_TRUNC('week', order_date) and AVG() with window function
-- Expected output: week | weekly_revenue | moving_avg_4weeks

-- Your query here:




-- ============================================================================
-- EXERCISE 12: Customer segmentation by RFM
-- ============================================================================
-- TODO: Calculate RFM metrics per customer (Recency, Frequency, Monetary)
-- HINT: Use DATE_DIFF for recency, COUNT for frequency, SUM for monetary
-- Expected output: customer_id | recency_days | frequency | monetary

-- Your query here:
-- SELECT
--   customer_id,
--   DATE_DIFF('day', MAX(order_date), CURRENT_DATE) as recency_days,
--   COUNT(DISTINCT order_id) as frequency,
--   SUM(total_amount) as monetary
-- FROM orders
-- GROUP BY customer_id
-- ORDER BY monetary DESC;




-- ============================================================================
-- EXERCISE 13: Year-over-year comparison
-- ============================================================================
-- TODO: Compare revenue by month for current year vs previous year
-- HINT: Use CASE WHEN to pivot years, or use self-join
-- Expected output: month | revenue_2023 | revenue_2024 | yoy_growth_pct

-- Your query here:




-- ============================================================================
-- EXERCISE 14: Cohort analysis - First purchase month
-- ============================================================================
-- TODO: Group customers by their first purchase month and track retention
-- HINT: Find MIN(order_date) per customer as cohort_month
-- Expected output: cohort_month | customers | avg_lifetime_value

-- Your query here:
-- WITH first_purchase AS (
--   SELECT customer_id, MIN(order_date) as first_purchase_date
--   FROM orders
--   GROUP BY customer_id
-- ),
-- customer_metrics AS (
--   SELECT
--     fp.customer_id,
--     DATE_TRUNC('month', fp.first_purchase_date) as cohort_month,
--     SUM(o.total_amount) as lifetime_value
--   FROM first_purchase fp
--   JOIN orders o ON ...
--   GROUP BY ...
-- )
-- SELECT
--   cohort_month,
--   COUNT(DISTINCT customer_id) as customers,
--   AVG(lifetime_value) as avg_lifetime_value
-- FROM customer_metrics
-- GROUP BY cohort_month
-- ORDER BY cohort_month;




-- ============================================================================
-- EXERCISE 15: Advanced - Product recommendation pairs
-- ============================================================================
-- TODO: Find products frequently bought together
-- HINT: Self-join orders on customer_id where products are different
-- Count occurrences of product pairs
-- Expected output: product_1 | product_2 | times_bought_together

-- Your query here:
-- This is a market basket analysis query
-- SELECT
--   o1.product_id as product_1,
--   o2.product_id as product_2,
--   COUNT(*) as times_bought_together
-- FROM orders o1
-- JOIN orders o2
--   ON o1.customer_id = o2.customer_id
--   AND o1.order_id = o2.order_id
--   AND o1.product_id < o2.product_id  -- Avoid duplicates
-- GROUP BY o1.product_id, o2.product_id
-- HAVING COUNT(*) > 5
-- ORDER BY times_bought_together DESC
-- LIMIT 20;




-- ============================================================================
-- BONUS EXERCISES (Optional)
-- ============================================================================

-- BONUS 1: Calculate customer churn rate by cohort
-- TODO: For each first purchase month cohort, calculate % who haven't ordered in 90 days

-- BONUS 2: Identify anomalies in daily revenue
-- TODO: Find days where revenue is more than 2 standard deviations from average

-- BONUS 3: Product stock optimization
-- TODO: Identify products with high sales velocity and low stock

-- BONUS 4: Geographic expansion analysis
-- TODO: Identify countries with growing order trends but low customer penetration

-- BONUS 5: Dynamic pricing opportunity
-- TODO: Find products with high demand but stable pricing over time

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Check your results make sense:
-- 1. Do totals add up correctly?
-- 2. Are percentages between 0-100?
-- 3. Are dates in reasonable ranges?
-- 4. Do JOINs produce expected record counts?

-- Example validation:
-- SELECT COUNT(*) FROM orders;  -- Known total
-- SELECT SUM(total_revenue) FROM your_query;  -- Should match sum of orders

-- ============================================================================
-- PERFORMANCE TIPS
-- ============================================================================

-- 1. Use partition filters: WHERE year = 2024 AND month = 3
-- 2. Limit result sets: LIMIT 100
-- 3. Use EXPLAIN to see query plans: EXPLAIN SELECT ...
-- 4. Avoid SELECT * - specify columns you need
-- 5. Use approximate functions for large datasets: APPROX_DISTINCT, APPROX_PERCENTILE
-- 6. Create views for commonly used queries
-- 7. Consider materializing Gold tables for frequent aggregations

-- ============================================================================
-- SUBMISSION
-- ============================================================================
-- Save your completed queries to this file
-- Test each query to ensure it runs without errors
-- Verify results make business sense
-- Document any assumptions or data issues you found
-- ============================================================================
