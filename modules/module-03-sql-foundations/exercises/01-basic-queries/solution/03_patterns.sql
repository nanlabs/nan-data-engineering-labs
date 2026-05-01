-- =====================================================
-- Exercise 01: Basic Queries - Pattern Matching (SOLUTIONS)
-- =====================================================

-- Query 1: Usuarios con email de Gmail
SELECT *
FROM users
WHERE email LIKE '%@gmail.com';

-- Query 2: Productos que contienen "Laptop" en el nombre
SELECT *
FROM products
WHERE product_name LIKE '%Laptop%';

-- Query 3: Usuarios cuyo nombre comienza con 'J'
SELECT *
FROM users
WHERE first_name LIKE 'J%';

-- Query 4: Productos en categoría 'Electronics' o 'Books'
SELECT *
FROM products
WHERE category IN ('Electronics', 'Books');

-- Query 5: Productos con precio entre $20 y $100 (inclusive)
SELECT *
FROM products
WHERE price BETWEEN 20 AND 100;

-- Query 6: Usuarios registrados en 2023
SELECT *
FROM users
WHERE registration_date BETWEEN '2023-01-01' AND '2023-12-31';

-- Query 7: Órdenes sin número de tracking
SELECT *
FROM orders
WHERE tracking_number IS NULL;

-- Query 8: Productos cuyo nombre termina en "Book"
SELECT *
FROM products
WHERE product_name LIKE '%Book';
