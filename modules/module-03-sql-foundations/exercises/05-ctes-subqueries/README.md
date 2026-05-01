# Exercise 05: CTEs & Subqueries

## 🎯 Objetivos

- Crear Common Table Expressions (WITH clause)
- Usar subqueries en SELECT, FROM y WHERE
- Chain multiple CTEs
- Decide between CTE and subquery depending on the case

## 📚 Conceptos

### Basic CTE
```sql
WITH high_value_orders AS (
    SELECT * FROM orders WHERE total_amount > 500
)
SELECT
    u.first_name,
    hvo.order_id,
    hvo.total_amount
FROM high_value_orders hvo
INNER JOIN users u ON hvo.user_id = u.user_id;
```

### Multiple CTEs
```sql
WITH
user_stats AS (
    SELECT user_id, COUNT(*) AS num_orders
    FROM orders GROUP BY user_id
),
top_users AS (
    SELECT * FROM user_stats WHERE num_orders > 5
)
SELECT u.*, tu.num_orders
FROM users u
INNER JOIN top_users tu ON u.user_id = tu.user_id;
```

### Subquery en WHERE
```sql
-- Productos más caros que el promedio
SELECT * FROM products
WHERE price > (SELECT AVG(price) FROM products);
```

## 🎓 Ejercicios

See starter/ for exercises with recursive CTEs, correlated subqueries, and more.

## ⏱️ Tiempo Estimado: ~100 minutos
