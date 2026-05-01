-- =====================================================
-- Exercise 01: Basic Queries - Pagination
-- =====================================================
-- Practica la paginación de resultados con LIMIT y OFFSET.

-- Query 1: Primeros 10 usuarios
-- TODO: Escribe tu consulta aquí
-- Usa LIMIT 10




-- Query 2: Usuarios de la página 2 (registros 11-20)
-- TODO: Escribe tu consulta aquí
-- Usa LIMIT 10 OFFSET 10




-- Query 3: Usuarios de la página 3 (registros 21-30)
-- TODO: Escribe tu consulta aquí
-- Calcula el OFFSET correcto




-- Query 4: Top 5 productos más caros
-- TODO: Escribe tu consulta aquí
-- Combina ORDER BY price DESC con LIMIT 5




-- Query 5: Últimos 20 usuarios registrados
-- TODO: Escribe tu consulta aquí
-- Ordena por registration_date DESC y limita a 20




-- Query 6: Productos en la página 2, ordenados por nombre
-- TODO: Escribe tu consulta aquí
-- Tamaño de página: 10 registros




-- Query 7: Segunda página de órdenes más recientes (11-20)
-- TODO: Escribe tu consulta aquí
-- Ordena por order_date DESC




-- BONUS: Escribe una función de paginación genérica
-- Dado: page_number (empezando en 1) y page_size
-- Calcular el OFFSET correcto
-- Formula: OFFSET = (page_number - 1) * page_size

-- Query 8: Página 4 con tamaño de página 15
-- TODO: Calcula el OFFSET y escribe la consulta
-- OFFSET = (4 - 1) * 15 = 45
