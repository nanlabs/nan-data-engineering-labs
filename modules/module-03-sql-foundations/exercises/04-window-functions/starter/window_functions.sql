-- Exercise 04: Window Functions (STARTER)

-- Query 1: Ranking de productos por precio
-- TODO: ROW_NUMBER() OVER (ORDER BY price DESC)




-- Query 2: Top 3 productos más caros por categoría
-- TODO: PARTITION BY category, filtrar rank <= 3




-- Query 3: Running total de órdenes por fecha
-- TODO: SUM(total_amount) OVER (ORDER BY order_date)




-- Query 4: Comparar cada orden con la anterior del mismo usuario
-- TODO: LAG(total_amount) OVER (PARTITION BY user_id ORDER BY order_date)




-- Query 5: Percentiles de precios
-- TODO: NTILE(4) OVER (ORDER BY price) para cuartiles
