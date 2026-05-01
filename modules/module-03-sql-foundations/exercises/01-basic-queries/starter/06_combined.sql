-- =====================================================
-- Exercise 01: Basic Queries - Combined Techniques
-- =====================================================
-- Combina todo lo aprendido: WHERE, LIKE, ORDER BY, LIMIT.

-- Query 1: Usuarios activos de US o GB con más de 100 puntos de lealtad
-- TODO: Escribe tu consulta aquí
-- Condiciones: is_active = TRUE, country IN ('US', 'GB'), loyalty_points > 100
-- Ordena por loyalty_points DESC




-- Query 2: Productos disponibles entre $20 y $100, ordenados por precio
-- TODO: Escribe tu consulta aquí
-- Condiciones: is_available = TRUE, price BETWEEN 20 AND 100
-- Ordena por price ASC




-- Query 3: Últimas 10 órdenes completadas (delivered) con total > $100
-- TODO: Escribe tu consulta aquí
-- Condiciones: status = 'delivered', total_amount > 100
-- Ordena por order_date DESC, limita a 10




-- Query 4: Productos de Electronics con stock, excluyendo los más caros que $500
-- TODO: Escribe tu consulta aquí
-- Condiciones: category = 'Electronics', stock_quantity > 0, price <= 500
-- Ordena por price DESC




-- Query 5: Top 5 usuarios con más puntos de cada país (US, GB, CA)
-- TODO: Escribe tu consulta aquí
-- Condiciones: country IN ('US', 'GB', 'CA')
-- Ordena por loyalty_points DESC, limita a 5
-- Nota: Esta query retorna top 5 global, no por país (eso requiere window functions)




-- Query 6: Productos cuyo nombre contiene "Book" o "Guide", disponibles, ordenados por precio
-- TODO: Escribe tu consulta aquí
-- Usa LIKE con OR, o dos condiciones LIKE




-- Query 7: Usuarios registrados en los últimos 6 meses de 2023, activos
-- TODO: Escribe tu consulta aquí
-- Condiciones: registration_date BETWEEN '2023-07-01' AND '2023-12-31'
-- is_active = TRUE
-- Ordena por registration_date DESC




-- Query 8: Segunda página de productos de Books, ordenados alfabéticamente
-- TODO: Escribe tu consulta aquí
-- Tamaño de página: 10
-- Condición: category = 'Books'
-- Ordena por product_name ASC




-- BONUS Challenge: Query complejo
-- Usuarios activos de países que no son US, registrados en 2023,
-- con email de Gmail, con al menos 50 puntos de lealtad,
-- ordenados por puntos (mayor a menor), limita a 10
-- TODO: Escribe tu consulta aquí
