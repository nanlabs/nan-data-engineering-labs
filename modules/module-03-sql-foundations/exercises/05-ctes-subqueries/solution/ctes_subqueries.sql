-- Exercise 05: CTEs & Subqueries (SOLUTION)

-- Query 1: CTE básico - Órdenes de alto valor
WITH high_value_orders AS (
    SELECT * FROM orders WHERE total_amount > 500
)
SELECT
    u.first_name || ' ' || u.last_name AS customer,
    u.country,
    hvo.order_id,
    hvo.order_date,
    hvo.total_amount
FROM high_value_orders hvo
INNER JOIN users u ON hvo.user_id = u.user_id
ORDER BY hvo.total_amount DESC;

-- Query 2: Múltiples CTEs encadenados
WITH
user_order_stats AS (
    SELECT
        user_id,
        COUNT(*) AS num_orders,
        SUM(total_amount) AS total_spent,
        AVG(total_amount) AS avg_order_value
    FROM orders
    GROUP BY user_id
),
top_customers AS (
    SELECT *
    FROM user_order_stats
    WHERE num_orders >= 3
)
SELECT
    u.first_name || ' ' || u.last_name AS customer,
    u.email,
    tc.num_orders,
    tc.total_spent::DECIMAL(10,2),
    tc.avg_order_value::DECIMAL(10,2)
FROM users u
INNER JOIN top_customers tc ON u.user_id = tc.user_id
ORDER BY tc.total_spent DESC;

-- Query 3: Subquery en WHERE - Productos sobre promedio
SELECT
    product_name,
    category,
    price,
    (SELECT AVG(price) FROM products) AS avg_price,
    price - (SELECT AVG(price) FROM products) AS diff_from_avg
FROM products
WHERE price > (SELECT AVG(price) FROM products)
ORDER BY price DESC;

-- Query 4: Subquery en SELECT con comparación por categoría
SELECT
    product_name,
    category,
    price,
    (SELECT AVG(price) FROM products p2 WHERE p2.category = p1.category) AS avg_price_in_category,
    price - (SELECT AVG(price) FROM products p2 WHERE p2.category = p1.category) AS diff_from_category_avg
FROM products p1
ORDER BY category, price DESC;

-- Query 5: CTE recursivo - Ejemplo numérico (días de la semana)
WITH RECURSIVE date_series AS (
    SELECT
        CURRENT_DATE AS date,
        1 AS day_number
    UNION ALL
    SELECT
        date + INTERVAL '1 day',
        day_number + 1
    FROM date_series
    WHERE day_number < 7
)
SELECT
    date,
    TO_CHAR(date, 'Day') AS day_name,
    COUNT(o.order_id) AS num_orders
FROM date_series ds
LEFT JOIN orders o ON DATE(o.order_date) = ds.date
GROUP BY ds.date
ORDER BY ds.date;
