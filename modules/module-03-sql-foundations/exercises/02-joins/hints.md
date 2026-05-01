# Hints - Exercise 02: Joins

## INNER JOIN (01)

**Query 1 - Orders with user**
- 💡 La foreign key en orders es `user_id`
- 💡 Sintaxis: `FROM orders o INNER JOIN users u ON o.user_id = u.user_id`
- 💡 Usa alias (o, u) para mejor legibilidad

**Query 2 - Items con productos**
- 💡 The relationship is order_items.product_id = products.product_id
- 💡 Selecciona columns de ambas tables

## LEFT JOIN (02)

**Query 1 - Conteo con LEFT JOIN**
- 💡 LEFT JOIN users with orders to include users without orders
- 💡 Use COUNT(o.order_id) not COUNT(*) - counts only real orders
- 💡 Necesitas GROUP BY en las columns de usuario

**Query 2 - Encontrar registros sin match**
- 💡 LEFT JOIN retorna NULL en columns de la table derecha cuando no hay match
- 💡 Filtra con `WHERE order_id IS NULL`
- 💡 Verifica columns de la table derecha (orders), no de la izquierda (users)

**Query 3 - COALESCE para valores NULL**
- 💡 `COALESCE(SUM(column), 0)` retorna 0 si SUM es NULL
- 💡 NULL aparece cuando no hay registros para agregar

## Multiple JOINs (03)

**Query 1 - Cadena de JOINs**
- 💡 Orden: orders → users, orders → order_items, order_items → products
- 💡 Cada JOIN usa la foreign key apropiada
- 💡 Puedes encadenar JOINs: FROM table1 JOIN table2 ON... JOIN table3 ON...

**Query 2 - STRING_AGG**
- 💡 `STRING_AGG(column, ', ')` concatena valores en una string
- 💡 Useful for displaying multiple values ​​in a row

## Tips Generales

- Siempre usa alias de table
- INNER JOIN cuando necesitas solo coincidencias
- LEFT JOIN cuando necesitas todos de la izquierda
- GROUP BY all columns that are not in aggregation functions
- COUNT(column) vs COUNT(*) - use specific column after LEFT JOIN
