-- =====================================================
-- Exercise 01: Additional Examples
-- =====================================================
-- Ejemplos adicionales para practicar y experimentar

-- =============================================================================
-- EJEMPLO 1: Búsquedas con CASE INSENSITIVE
-- =============================================================================
-- PostgreSQL es case-sensitive por defecto en comparaciones
-- Usa ILIKE para búsquedas case-insensitive

-- Case-sensitive (solo encuentra "gmail.com", no "Gmail.com")
SELECT * FROM users WHERE email LIKE '%gmail.com';

-- Case-insensitive (encuentra gmail.com, Gmail.com, GMAIL.COM, etc.)
SELECT * FROM users WHERE email ILIKE '%gmail.com';

-- También puedes usar LOWER() o UPPER()
SELECT * FROM users WHERE LOWER(email) LIKE '%gmail.com';

-- =============================================================================
-- EJEMPLO 2: Expresiones en SELECT
-- =============================================================================
-- Puedes calcular valores en el SELECT

-- Calcular descuento del 10%
SELECT
    product_name,
    price AS precio_original,
    price * 0.9 AS precio_con_descuento,
    price - (price * 0.9) AS ahorro
FROM products
WHERE is_available = TRUE;

-- Concatenar strings
SELECT
    first_name || ' ' || last_name AS nombre_completo,
    email
FROM users;

-- Expresiones booleanas
SELECT
    product_name,
    price,
    CASE
        WHEN price < 50 THEN 'Económico'
        WHEN price BETWEEN 50 AND 200 THEN 'Moderado'
        ELSE 'Premium'
    END AS rango_precio
FROM products;

-- =============================================================================
-- EJEMPLO 3: Múltiples patrones con LIKE
-- =============================================================================
-- Combinar múltiples patrones de búsqueda

-- Productos que contienen "Laptop" O "Computer"
SELECT *
FROM products
WHERE product_name LIKE '%Laptop%'
   OR product_name LIKE '%Computer%';

-- Emails de Gmail O Outlook
SELECT *
FROM users
WHERE email LIKE '%@gmail.com'
   OR email LIKE '%@outlook.com';

-- Nombres que empiezan con J, M o S
SELECT *
FROM users
WHERE first_name LIKE 'J%'
   OR first_name LIKE 'M%'
   OR first_name LIKE 'S%';

-- =============================================================================
-- EJEMPLO 4: Filtros complejos con paréntesis
-- =============================================================================
-- Los paréntesis controlan la precedencia de AND/OR

-- Sin paréntesis (puede no dar el resultado esperado)
SELECT *
FROM users
WHERE country = 'US'
   OR country = 'GB'
  AND loyalty_points > 100;
-- Esto es equivalente a: country = 'US' OR (country = 'GB' AND loyalty_points > 100)

-- Con paréntesis (comportamiento correcto)
SELECT *
FROM users
WHERE (country = 'US' OR country = 'GB')
  AND loyalty_points > 100;

-- =============================================================================
-- EJEMPLO 5: COALESCE para manejar NULL
-- =============================================================================
-- COALESCE retorna el primer valor no-NULL

-- Mostrar "N/A" si el tracking number es NULL
SELECT
    order_id,
    order_date,
    COALESCE(tracking_number, 'N/A') AS tracking,
    status
FROM orders
ORDER BY order_date DESC
LIMIT 10;

-- Usar valor por defecto para columnas opcionales
SELECT
    product_name,
    COALESCE(description, 'Sin descripción') AS description,
    price
FROM products;

-- =============================================================================
-- EJEMPLO 6: Filtros de fecha avanzados
-- =============================================================================
-- Trabajar con diferentes partes de una fecha

-- Usuarios registrados en un mes específico
SELECT *
FROM users
WHERE EXTRACT(YEAR FROM registration_date) = 2023
  AND EXTRACT(MONTH FROM registration_date) = 6;

-- Órdenes de los últimos 30 días (si tuviéramos datos recientes)
SELECT *
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';

-- Órdenes de un trimestre específico (Q3 2023)
SELECT *
FROM orders
WHERE order_date >= '2023-07-01'
  AND order_date < '2023-10-01';

-- =============================================================================
-- EJEMPLO 7: DISTINCT para eliminar duplicados
-- =============================================================================
-- Obtener valores únicos

-- Lista de países de usuarios (sin duplicados)
SELECT DISTINCT country
FROM users
ORDER BY country;

-- Combinaciones únicas de categoría y disponibilidad
SELECT DISTINCT category, is_available
FROM products
ORDER BY category, is_available;

-- Contar usuarios únicos por país
SELECT country, COUNT(*) as num_users
FROM users
GROUP BY country
ORDER BY num_users DESC;

-- =============================================================================
-- EJEMPLO 8: Subconsultas en WHERE
-- =============================================================================
-- Usar resultado de una query en otra

-- Productos más caros que el promedio
SELECT *
FROM products
WHERE price > (SELECT AVG(price) FROM products);

-- Usuarios con más puntos que el promedio
SELECT *
FROM users
WHERE loyalty_points > (SELECT AVG(loyalty_points) FROM users)
ORDER BY loyalty_points DESC;

-- Productos de la categoría más popular
SELECT *
FROM products
WHERE category = (
    SELECT category
    FROM products
    GROUP BY category
    ORDER BY COUNT(*) DESC
    LIMIT 1
);

-- =============================================================================
-- EJEMPLO 9: Búsqueda con expresiones regulares (REGEX)
-- =============================================================================
-- PostgreSQL soporta regex con ~ (case-sensitive) y ~* (case-insensitive)

-- Emails que terminan en .com o .org
SELECT email
FROM users
WHERE email ~ '\.(com|org)$';

-- Nombres que contienen exactamente 4 letras
SELECT first_name
FROM users
WHERE first_name ~ '^[A-Za-z]{4}$';

-- Productos con números en el nombre
SELECT product_name
FROM products
WHERE product_name ~ '[0-9]';

-- =============================================================================
-- EJEMPLO 10: Análisis de datos con estadísticas
-- =============================================================================
-- Queries analíticas útiles

-- Resumen de productos por categoría
SELECT
    category,
    COUNT(*) AS num_productos,
    MIN(price) AS precio_min,
    MAX(price) AS precio_max,
    AVG(price)::DECIMAL(10,2) AS precio_promedio,
    SUM(stock_quantity) AS stock_total
FROM products
GROUP BY category
ORDER BY category;

-- Distribución de usuarios por país
SELECT
    country,
    COUNT(*) AS num_usuarios,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users) AS porcentaje
FROM users
GROUP BY country
ORDER BY num_usuarios DESC;

-- Estados de órdenes
SELECT
    status,
    COUNT(*) AS num_ordenes,
    SUM(total_amount) AS revenue_total,
    AVG(total_amount)::DECIMAL(10,2) AS ticket_promedio
FROM orders
GROUP BY status
ORDER BY num_ordenes DESC;

-- =============================================================================
-- EJEMPLO 11: Paginación con información de totales
-- =============================================================================
-- Mostrar información útil para UI de paginación

-- Página 1 con contador total
SELECT
    *,
    COUNT(*) OVER() AS total_registros
FROM users
ORDER BY user_id
LIMIT 10 OFFSET 0;

-- Calcular número total de páginas
SELECT
    CEIL(COUNT(*)::DECIMAL / 10) AS total_paginas,
    COUNT(*) AS total_registros
FROM users;

-- =============================================================================
-- EJEMPLO 12: Validación de integridad de datos
-- =============================================================================
-- Queries para encontrar datos problemáticos

-- Usuarios con emails potencialmente inválidos
SELECT *
FROM users
WHERE email NOT LIKE '%@%.%'
   OR email LIKE '%@%@%'  -- Múltiples @
   OR email LIKE '@%'     -- Empieza con @
   OR email LIKE '%@';    -- Termina con @

-- Productos con datos inconsistentes
SELECT *
FROM products
WHERE (stock_quantity = 0 AND is_available = TRUE)
   OR (price <= 0)
   OR (product_name IS NULL OR product_name = '');

-- Órdenes sin items (requiere join, lo veremos en próximo ejercicio)
-- Esta es una preview de lo que aprenderemos:
SELECT o.*
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.order_item_id IS NULL;

-- =============================================================================
-- TIPS FINALES
-- =============================================================================

/*
1. PERFORMANCE:
   - Usa índices en columnas de WHERE frecuentes
   - Evita funciones en WHERE cuando sea posible (LOWER, UPPER reduce performance)
   - LIMIT para testing, pero recuerda que sin ORDER BY el orden es indeterminado

2. LEGIBILIDAD:
   - Usa alias descriptivos
   - Indenta correctamente
   - Comenta queries complejos
   - Un concepto por línea

3. TESTING:
   - Empieza simple, agrega complejidad gradualmente
   - Usa COUNT(*) para verificar número de resultados
   - Usa LIMIT durante desarrollo
   - Valida con casos extremos (NULL, vacíos, límites)

4. DEBUGGING:
   - Si no retorna resultados, verifica cada condición individualmente
   - Usa SELECT DISTINCT para ver valores únicos
   - Revisa tipos de datos (strings requieren comillas)
   - Cuidado con case-sensitivity en comparaciones
*/
