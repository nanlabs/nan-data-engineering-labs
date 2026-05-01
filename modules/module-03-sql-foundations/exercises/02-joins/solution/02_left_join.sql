-- Exercise 02: Joins - LEFT JOIN (SOLUTION)

-- Query 1: Todos los usuarios con conteo de órdenes
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    COUNT(o.order_id) AS num_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.first_name, u.last_name
ORDER BY num_orders DESC, total_spent DESC;

-- Query 2: Usuarios que NO han hecho órdenes
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    u.registration_date
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_id IS NULL
ORDER BY u.registration_date DESC;

-- Query 3: Todos los productos con total de ventas
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    COUNT(oi.order_item_id) AS times_sold,
    COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
    COALESCE(SUM(oi.subtotal), 0) AS total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category, p.price
ORDER BY total_revenue DESC;

-- Query 4: Productos nunca vendidos
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.stock_quantity
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL
ORDER BY p.product_name;
