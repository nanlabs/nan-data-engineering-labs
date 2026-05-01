-- Exercise 05: CTEs & Subqueries (STARTER)

-- Query 1: CTE básico - Órdenes de alto valor
-- TODO: WITH high_value_orders AS (SELECT...) luego JOIN con users




-- Query 2: Múltiples CTEs encadenados
-- TODO: user_stats CTE, luego top_users CTE, luego SELECT




-- Query 3: Subquery en WHERE - Productos sobre promedio
-- TODO: WHERE price > (SELECT AVG(price)...)




-- Query 4: Subquery en SELECT - Comparar con promedio
-- TODO: SELECT price, (SELECT AVG(price) FROM products) AS avg_price




-- Query 5: Subquery correlacionado - Items más caros de cada orden
-- TODO: WHERE price = (SELECT MAX(...) WHERE order_id = outer.order_id)
