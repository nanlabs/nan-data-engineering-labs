-- Exercise 02: Joins - Multiple JOINs (SOLUTION)

-- Query 1: Órdenes completas (usuario + items + productos)
SELECT
    o.order_id,
    o.order_date,
    o.status,
    u.first_name || ' ' || u.last_name AS customer,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
ORDER BY o.order_date DESC, o.order_id, oi.order_item_id;

-- Query 2: Resumen de compras por usuario con productos
SELECT
    u.first_name || ' ' || u.last_name AS customer,
    u.country,
    COUNT(DISTINCT o.order_id) AS num_orders,
    COUNT(oi.order_item_id) AS num_items,
    STRING_AGG(DISTINCT p.product_name, ', ') AS products_purchased,
    SUM(oi.subtotal) AS total_spent
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
GROUP BY u.user_id, u.first_name, u.last_name, u.country
ORDER BY total_spent DESC;

-- Query 3: Total gastado por usuario por categoría
SELECT
    u.first_name || ' ' || u.last_name AS customer,
    p.category,
    COUNT(DISTINCT o.order_id) AS num_orders,
    SUM(oi.quantity) AS total_items,
    SUM(oi.subtotal) AS total_spent
FROM users u
INNER JOIN orders o ON u.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
GROUP BY u.user_id, u.first_name, u.last_name, p.category
ORDER BY customer, total_spent DESC;
