-- =====================================================
-- Exercise 01: Basic Queries - Pagination (SOLUTIONS)
-- =====================================================

-- Query 1: Primeros 10 usuarios
SELECT *
FROM users
ORDER BY user_id
LIMIT 10;

-- Query 2: Usuarios de la página 2 (registros 11-20)
SELECT *
FROM users
ORDER BY user_id
LIMIT 10 OFFSET 10;

-- Query 3: Usuarios de la página 3 (registros 21-30)
SELECT *
FROM users
ORDER BY user_id
LIMIT 10 OFFSET 20;

-- Query 4: Top 5 productos más caros
SELECT *
FROM products
ORDER BY price DESC
LIMIT 5;

-- Query 5: Últimos 20 usuarios registrados
SELECT *
FROM users
ORDER BY registration_date DESC
LIMIT 20;

-- Query 6: Productos en la página 2, ordenados por nombre
SELECT *
FROM products
ORDER BY product_name ASC
LIMIT 10 OFFSET 10;

-- Query 7: Segunda página de órdenes más recientes (11-20)
SELECT *
FROM orders
ORDER BY order_date DESC
LIMIT 10 OFFSET 10;

-- Query 8: Página 4 con tamaño de página 15
-- OFFSET = (page_number - 1) * page_size = (4 - 1) * 15 = 45
SELECT *
FROM users
ORDER BY user_id
LIMIT 15 OFFSET 45;

-- BONUS: Función de paginación genérica (comentada)
-- Para página N con tamaño P:
-- LIMIT P OFFSET (N - 1) * P
--
-- Ejemplos:
-- Página 1, tamaño 10: LIMIT 10 OFFSET 0
-- Página 2, tamaño 10: LIMIT 10 OFFSET 10
-- Página 3, tamaño 25: LIMIT 25 OFFSET 50
