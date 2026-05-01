-- =====================================================
-- Exercise 01: Basic Queries - Sorting (SOLUTIONS)
-- =====================================================

-- Query 1: Usuarios ordenados por puntos de lealtad (mayor a menor)
SELECT *
FROM users
ORDER BY loyalty_points DESC;

-- Query 2: Productos ordenados por precio (menor a mayor)
SELECT *
FROM products
ORDER BY price ASC;
-- También válido: ORDER BY price (ASC es default)

-- Query 3: Órdenes más recientes primero
SELECT *
FROM orders
ORDER BY order_date DESC;

-- Query 4: Top 10 productos más caros
SELECT *
FROM products
ORDER BY price DESC
LIMIT 10;

-- Query 5: Usuarios por país (alfabético) y luego por fecha de registro
SELECT *
FROM users
ORDER BY country ASC, registration_date ASC;

-- Query 6: Productos disponibles ordenados por stock (menor a mayor)
SELECT *
FROM products
WHERE is_available = TRUE
ORDER BY stock_quantity ASC;

-- Query 7: Últimos 5 usuarios registrados
SELECT *
FROM users
ORDER BY registration_date DESC
LIMIT 5;

-- Query 8: Órdenes ordenadas por total (mayor a menor) y luego por fecha
SELECT *
FROM orders
ORDER BY total_amount DESC, order_date DESC;
