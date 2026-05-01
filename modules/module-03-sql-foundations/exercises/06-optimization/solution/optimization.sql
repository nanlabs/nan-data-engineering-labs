-- Exercise 06: Query Optimization (SOLUTION)

-- =====================================================
-- Query 1: Analizar query plan básico
-- =====================================================

-- Sin índice (Seq Scan)
EXPLAIN SELECT * FROM orders WHERE user_id = 5;

-- Versión con análisis de timing
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 5;

-- =====================================================
-- Query 2: Comparar con y sin índice
-- =====================================================

-- ANTES: Sin índice (debe hacer Seq Scan)
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = 10
ORDER BY order_date DESC;

-- Crear índice
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);

-- DESPUÉS: Con índice (debe usar Index Scan)
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = 10
ORDER BY order_date DESC;

-- Índice compuesto para mejorar aún más
CREATE INDEX IF NOT EXISTS idx_orders_user_date
ON orders(user_id, order_date DESC);

-- =====================================================
-- Query 3: Optimizar JOIN
-- =====================================================

-- INEFICIENTE: SELECT * con JOIN innecesario
EXPLAIN ANALYZE
SELECT *
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id;

-- EFICIENTE: Solo columnas necesarias
EXPLAIN ANALYZE
SELECT
    o.order_id,
    u.first_name,
    p.product_name,
    oi.quantity
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'delivered'
LIMIT 100;

-- =====================================================
-- Query 4: Subquery vs JOIN
-- =====================================================

-- Opción A: Subquery
EXPLAIN ANALYZE
SELECT *
FROM users u
WHERE user_id IN (
    SELECT DISTINCT user_id
    FROM orders
    WHERE total_amount > 100
);

-- Opción B: JOIN (generalmente más rápido)
EXPLAIN ANALYZE
SELECT DISTINCT u.*
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
WHERE o.total_amount > 100;

-- Opción C: EXISTS (mejor para casos grandes)
EXPLAIN ANALYZE
SELECT *
FROM users u
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.user_id = u.user_id
      AND o.total_amount > 100
);

-- =====================================================
-- Query 5: Caso real - Dashboard de ventas
-- =====================================================

-- INEFICIENTE: Múltiples subqueries
SELECT
    u.user_id,
    u.first_name,
    (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) AS num_orders,
    (SELECT SUM(total_amount) FROM orders o WHERE o.user_id = u.user_id) AS total_spent,
    (SELECT MAX(order_date) FROM orders o WHERE o.user_id = u.user_id) AS last_order_date
FROM users u
ORDER BY total_spent DESC;

-- EFICIENTE: Un solo JOIN con agregaciones
SELECT
    u.user_id,
    u.first_name,
    COUNT(o.order_id) AS num_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent,
    MAX(o.order_date) AS last_order_date
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.first_name
ORDER BY total_spent DESC;

-- =====================================================
-- Tips de Optimización
-- =====================================================

/*
1. ÍNDICES:
   - Crear en columnas de WHERE, JOIN, ORDER BY frecuentes
   - Índices compuestos para queries con múltiples filtros
   - No sobre-indexar (cada índice tiene costo en writes)

2. SELECT:
   - Evitar SELECT * en producción
   - Solo seleccionar columnas necesarias
   - Reduce transferencia de datos

3. JOINs:
   - INNER JOIN más rápido que LEFT JOIN (cuando aplique)
   - Filtrar antes de JOIN cuando sea posible
   - Orden de JOINs puede importar (tabla pequeña primero)

4. LÍMITES:
   - Usar LIMIT en development
   - Paginar resultados grandes
   - Considerar cursor para datasets muy grandes

5. AGREGACIONES:
   - Un JOIN con GROUP BY mejor que múltiples subqueries
   - Usar HAVING solo cuando sea necesario (WHERE es más rápido)

6. EXPLAIN:
   - EXPLAIN muestra plan, no ejecuta
   - EXPLAIN ANALYZE ejecuta y muestra timing real
   - Buscar: Seq Scan (malo), Index Scan (bueno), Bitmap Scan (medio)
*/

-- =====================================================
-- Verificar índices existentes
-- =====================================================

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- =====================================================
-- Estadísticas de uso de índices
-- =====================================================

SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
