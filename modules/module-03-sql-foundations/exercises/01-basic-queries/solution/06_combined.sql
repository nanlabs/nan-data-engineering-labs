-- =====================================================
-- Exercise 01: Basic Queries - Combined (SOLUTIONS)
-- =====================================================

-- Query 1: Usuarios activos de US o GB con más de 100 puntos de lealtad
SELECT *
FROM users
WHERE is_active = TRUE
  AND country IN ('US', 'GB')
  AND loyalty_points > 100
ORDER BY loyalty_points DESC;

-- Query 2: Productos disponibles entre $20 y $100, ordenados por precio
SELECT *
FROM products
WHERE is_available = TRUE
  AND price BETWEEN 20 AND 100
ORDER BY price ASC;

-- Query 3: Últimas 10 órdenes completadas (delivered) con total > $100
SELECT *
FROM orders
WHERE status = 'delivered'
  AND total_amount > 100
ORDER BY order_date DESC
LIMIT 10;

-- Query 4: Productos de Electronics con stock, excluyendo los más caros que $500
SELECT *
FROM products
WHERE category = 'Electronics'
  AND stock_quantity > 0
  AND price <= 500
ORDER BY price DESC;

-- Query 5: Top 5 usuarios con más puntos de países específicos
SELECT *
FROM users
WHERE country IN ('US', 'GB', 'CA')
ORDER BY loyalty_points DESC
LIMIT 5;

-- Query 6: Productos cuyo nombre contiene "Book" o "Guide", disponibles
SELECT *
FROM products
WHERE is_available = TRUE
  AND (product_name LIKE '%Book%' OR product_name LIKE '%Guide%')
ORDER BY price ASC;

-- Query 7: Usuarios registrados en los últimos 6 meses de 2023, activos
SELECT *
FROM users
WHERE registration_date BETWEEN '2023-07-01' AND '2023-12-31'
  AND is_active = TRUE
ORDER BY registration_date DESC;

-- Query 8: Segunda página de productos de Books, ordenados alfabéticamente
SELECT *
FROM products
WHERE category = 'Books'
ORDER BY product_name ASC
LIMIT 10 OFFSET 10;

-- BONUS Challenge: Query complejo
SELECT *
FROM users
WHERE is_active = TRUE
  AND country NOT IN ('US')
  AND registration_date BETWEEN '2023-01-01' AND '2023-12-31'
  AND email LIKE '%@gmail.com'
  AND loyalty_points >= 50
ORDER BY loyalty_points DESC
LIMIT 10;
