# Exercise 03: Aggregations

## 🎯 Objetivos

- Use aggregation functions: COUNT, SUM, AVG, MIN, MAX
- Agrupar resultados con GROUP BY
- Filtrar grupos con HAVING
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
-- Usuarios con más de 5 órdenes
SELECT
    user_id,
    COUNT(*) AS num_orders
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5;
```

## 🎓 Ejercicios

Ver archivos starter/ para ejercicios detallados.

## ⏱️ Tiempo Estimado: ~90 minutos
