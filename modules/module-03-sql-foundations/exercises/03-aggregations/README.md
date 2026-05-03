# Exercise 03: Aggregations

## 🎯 Objectives

- Use aggregation functions: COUNT, SUM, AVG, MIN, MAX
- Agrupar resultados con GROUP BY
- Filter groups with HAVING
- Combinar agregaciones con JOINs
- Entender diferencia entre WHERE y HAVING

## 📚 Conceptos

### Aggregation Functions
```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    MIN(total_amount) AS min_order,
    MAX(total_amount) AS max_order
FROM orders;
```

### GROUP BY
```sql
-- Ventas por usuario
SELECT
    user_id,
    COUNT(*) AS num_orders,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY user_id
ORDER BY total_spent DESC;
```

### HAVING
```sql
-- Users with more than 5 orders
SELECT
    user_id,
    COUNT(*) AS num_orders
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5;
```

## 🎓 Exercises

See starter/ files for detailed exercises.

## ⏱️ Tiempo Estimado: ~90 minutos
