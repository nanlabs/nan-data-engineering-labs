-- =====================================================
-- Exercise 01: Basic Queries - Filtering (SOLUTIONS)
-- =====================================================

-- Query 1: Usuarios activos de Estados Unidos
SELECT *
FROM users
WHERE country = 'US'
  AND is_active = TRUE;

-- Query 2: Productos con precio menor a $50
SELECT *
FROM products
WHERE price < 50;

-- Query 3: Órdenes con status 'delivered' o 'shipped'
-- Opción 1: Usando OR
SELECT *
FROM orders
WHERE status = 'delivered'
   OR status = 'shipped';

-- Opción 2: Usando IN (preferido)
SELECT *
FROM orders
WHERE status IN ('delivered', 'shipped');

-- Query 4: Usuarios que NO son de US, GB o CA
SELECT *
FROM users
WHERE country NOT IN ('US', 'GB', 'CA');

-- Query 5: Productos sin stock disponible
SELECT *
FROM products
WHERE stock_quantity = 0;

-- Query 6: Usuarios con más de 100 puntos de lealtad
SELECT *
FROM users
WHERE loyalty_points > 100;

-- Query 7: Órdenes con total mayor a $500
SELECT *
FROM orders
WHERE total_amount > 500;

-- Query 8: Productos que NO están disponibles
SELECT *
FROM products
WHERE is_available = FALSE;
