-- Exercise 02: Joins - INNER JOIN (SOLUTION)

-- Query 1: Órdenes con nombre completo del usuario
SELECT
    o.order_id,
    o.order_date,
    o.total_amount,
    u.first_name,
    u.last_name
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
ORDER BY o.order_date DESC;

-- Query 2: Items de orden con nombre del producto
SELECT
    oi.order_item_id,
    oi.order_id,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.product_id
ORDER BY oi.order_id, oi.order_item_id;

-- Query 3: Actividad de usuarios con nombre del usuario
SELECT
    ua.activity_id,
    ua.activity_timestamp,
    ua.activity_type,
    u.first_name || ' ' || u.last_name AS user_name,
    u.email
FROM user_activity ua
INNER JOIN users u ON ua.user_id = u.user_id
ORDER BY ua.activity_timestamp DESC
LIMIT 20;

-- Query 4: Órdenes con usuario y su email
SELECT
    o.order_id,
    o.order_date,
    o.total_amount,
    o.status,
    u.first_name,
    u.last_name,
    u.email
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
ORDER BY o.order_date DESC;
