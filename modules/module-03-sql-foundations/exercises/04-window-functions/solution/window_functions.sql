-- Exercise 04: Window Functions (SOLUTION)

-- Query 1: Ranking de productos por precio
SELECT
    product_id,
    product_name,
    category,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) AS price_rank,
    RANK() OVER (ORDER BY price DESC) AS price_rank_with_ties,
    DENSE_RANK() OVER (ORDER BY price DESC) AS dense_rank
FROM products
ORDER BY price DESC;

-- Query 2: Top 3 productos más caros por categoría
SELECT *
FROM (
    SELECT
        product_name,
        category,
        price,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS rank_in_category
    FROM products
) ranked
WHERE rank_in_category <= 3
ORDER BY category, rank_in_category;

-- Query 3: Running total de órdenes por fecha
SELECT
    order_id,
    order_date,
    total_amount,
    SUM(total_amount) OVER (ORDER BY order_date) AS running_total,
    AVG(total_amount) OVER (ORDER BY order_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3
FROM orders
ORDER BY order_date;

-- Query 4: Comparar cada orden con la anterior del mismo usuario
SELECT
    u.first_name || ' ' || u.last_name AS customer,
    o.order_id,
    o.order_date,
    o.total_amount,
    LAG(o.total_amount) OVER (PARTITION BY o.user_id ORDER BY o.order_date) AS previous_order_amount,
    o.total_amount - LAG(o.total_amount) OVER (PARTITION BY o.user_id ORDER BY o.order_date) AS difference,
    LEAD(o.order_date) OVER (PARTITION BY o.user_id ORDER BY o.order_date) AS next_order_date
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
ORDER BY u.user_id, o.order_date;

-- Query 5: Percentiles de precios
SELECT
    product_name,
    price,
    NTILE(4) OVER (ORDER BY price) AS price_quartile,
    CASE
        WHEN NTILE(4) OVER (ORDER BY price) = 1 THEN 'Budget'
        WHEN NTILE(4) OVER (ORDER BY price) = 2 THEN 'Economy'
        WHEN NTILE(4) OVER (ORDER BY price) = 3 THEN 'Standard'
        ELSE 'Premium'
    END AS price_tier
FROM products
ORDER BY price;
