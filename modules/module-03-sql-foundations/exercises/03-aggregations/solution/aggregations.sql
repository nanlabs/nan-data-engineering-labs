-- Exercise 03: Aggregations (SOLUTION)

-- Query 1: Total de órdenes y revenue
SELECT
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount)::DECIMAL(10,2) AS avg_order_value,
    MIN(total_amount) AS min_order,
    MAX(total_amount) AS max_order
FROM orders;

-- Query 2: Ventas por usuario (con nombre)
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS customer_name,
    u.country,
    COUNT(o.order_id) AS num_orders,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount)::DECIMAL(10,2) AS avg_order_value
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.first_name, u.last_name, u.country
ORDER BY total_spent DESC;

-- Query 3: Productos más vendidos
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(oi.order_item_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.subtotal) AS total_revenue
FROM products p
INNER JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;

-- Query 4: Revenue por categoría de producto
SELECT
    p.category,
    COUNT(DISTINCT p.product_id) AS num_products,
    COUNT(oi.order_item_id) AS num_sales,
    SUM(oi.quantity) AS total_units_sold,
    SUM(oi.subtotal) AS total_revenue,
    AVG(oi.subtotal)::DECIMAL(10,2) AS avg_sale_value
FROM products p
INNER JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Query 5: Usuarios con más de 3 órdenes
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    COUNT(o.order_id) AS num_orders,
    SUM(o.total_amount) AS total_spent
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.first_name, u.last_name, u.email
HAVING COUNT(o.order_id) > 3
ORDER BY num_orders DESC;
