# Exercise 06: Query Optimization

## 🎯 Objectives

- Analizar query plans con EXPLAIN
- Identificar problemas de performance
- Crear y usar indexs efectivamente
- Optimizar JOINs y subqueries
- Entender query costs y timing

## 📚 Conceptos

### EXPLAIN

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 1;

EXPLAIN ANALYZE SELECT * FROM orders
WHERE user_id = 1
ORDER BY order_date DESC;
```text

### indexes

```sql
-- Create index
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Composite index
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);

-- View existing indexes
\di+ orders
```text

### Optimization

- Evitar SELECT *
- Usar LIMIT apropiadamente
- Filter before JOIN when possible
- Consider materializing complex CTEs
- Use EXISTS instead of IN for large datasets

## 🎓 Exercises

See starter/ for performance analysis exercises, index creation, and query comparison.

## ⏱️ Tiempo Estimado: ~90 minutos
