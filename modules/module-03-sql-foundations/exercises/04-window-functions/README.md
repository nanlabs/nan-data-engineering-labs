# Exercise 04: Window Functions

## 🎯 Objetivos

- Usar ROW_NUMBER(), RANK(), DENSE_RANK()
- Apply analytical functions: LAG(), LEAD(), FIRST_VALUE(), LAST_VALUE()
- Usar agregaciones con OVER()
- Particionar datos con PARTITION BY
- Ordenar ventanas con ORDER BY

## 📚 Conceptos Clave

### ROW_NUMBER
```sql
-- Ranking de productos por precio
SELECT
    product_name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) AS rank
FROM products;
```

### PARTITION BY
```sql
-- Top 3 productos por categoría
SELECT *
FROM (
    SELECT
        product_name,
        category,
        price,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS rank_in_category
    FROM products
) ranked
WHERE rank_in_category <= 3;
```

### LAG y LEAD
```sql
-- Comparar con orden anterior
SELECT
    order_id,
    order_date,
    total_amount,
    LAG(total_amount) OVER (ORDER BY order_date) AS previous_order,
    total_amount - LAG(total_amount) OVER (ORDER BY order_date) AS difference
FROM orders;
```

## 🎓 Ejercicios

See starter/ for complete exercises with ranking, temporal analysis, and more.

## ⏱️ Tiempo Estimado: ~120 minutos
