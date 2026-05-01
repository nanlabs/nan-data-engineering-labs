-- =====================================================
-- Exercise 01: Basic Queries - Projection (SOLUTIONS)
-- =====================================================

-- Query 1: Obtener nombre completo y email de todos los usuarios
SELECT
    first_name,
    last_name,
    email
FROM users;

-- Query 2: Obtener productos con nombre y precio, usando alias en español
SELECT
    product_name AS nombre_producto,
    price AS precio
FROM products;

-- Query 3: Obtener las primeras 5 órdenes con id, fecha y total
SELECT
    order_id,
    order_date AS fecha,
    total_amount AS total
FROM orders
LIMIT 5;

-- Query 4: Obtener user_id, email y puntos de lealtad
SELECT
    user_id,
    email,
    loyalty_points AS puntos_lealtad
FROM users;

-- Query 5: Obtener productos con todas las columnas EXCEPTO created_at y updated_at
SELECT
    product_id,
    product_name,
    category,
    price,
    stock_quantity,
    description,
    is_available
FROM products;
