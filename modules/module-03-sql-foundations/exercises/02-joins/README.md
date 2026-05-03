# Exercise 02: Joins

## 🎯 Learning Objectives

By completing this exercise, you will be able to:

- Conceptually understand how different types of JOINs work
- Combine data from multiple tables using INNER JOIN
- Usar LEFT JOIN para incluir todos los registros de la table izquierda
- Aplicar RIGHT JOIN y FULL OUTER JOIN cuando sea apropiado
- Escribir self-joins para relacionar table consigo misma
- Use multiple JOINs in a single query
- Aplicar filtros y ordenamiento en queries con JOINs
- Identify when to use each type of JOIN depending on the use case

## 📚 Conceptos Cubiertos

### 1. INNER JOIN
Retorna solo los registros que tienen coincidencias en ambas tables.

```sql
-- Basic syntax
SELECT columns
FROM table1
INNER JOIN table2 ON table1.key = table2.key;

-- Example: Orders with user information
SELECT
    o.order_id,
    o.order_date,
    u.first_name,
    u.last_name
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id;
```

**When to use**: When you only want records that exist in both tables.

### 2. LEFT JOIN (LEFT OUTER JOIN)
Retorna todos los registros de la table izquierda, con o sin coincidencias en la derecha.

```sql
-- All users and their orders (if any)
SELECT
    u.first_name,
    u.last_name,
    o.order_id,
    o.total_amount
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;

-- Users who have NOT placed orders
SELECT u.*
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_id IS NULL;
```

**When to use**: When you need all the records in the main table, whether they have relationships or not.

### 3. RIGHT JOIN (RIGHT OUTER JOIN)
Similar a LEFT JOIN pero retorna todos los registros de la table derecha.

```sql
-- All orders and their users
SELECT
    o.order_id,
    o.total_amount,
    u.first_name,
    u.last_name
FROM users u
RIGHT JOIN orders o ON u.user_id = o.user_id;
```

**Nota**: Generalmente se prefiere LEFT JOIN reorganizando las tables.

### 4. FULL OUTER JOIN
Retorna todos los registros de ambas tables, con o sin coincidencias.

```sql
-- All users and orders, whether related or not
SELECT
    u.user_id,
    u.first_name,
    o.order_id,
    o.total_amount
FROM users u
FULL OUTER JOIN orders o ON u.user_id = o.user_id;
```

**When to use**: Rarely. Useful for data integrity analysis.

### 5. Multiple JOINs
Combine 3 or more tables in a query.

```sql
-- Orders with user and product details
SELECT
    o.order_id,
    u.first_name || ' ' || u.last_name AS customer,
    p.product_name,
    oi.quantity,
    oi.subtotal
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id;
```

### 6. Self JOIN
Relacionar una table consigo misma.

```sql
-- Ejemplo conceptual: usuarios que compraron el mismo producto
SELECT DISTINCT
    u1.first_name AS customer1,
    u2.first_name AS customer2,
    p.product_name
FROM orders o1
INNER JOIN orders o2 ON o1.order_id != o2.order_id
INNER JOIN order_items oi1 ON o1.order_id = oi1.order_id
INNER JOIN order_items oi2 ON o2.order_id = oi2.order_id
                            AND oi1.product_id = oi2.product_id
INNER JOIN users u1 ON o1.user_id = u1.user_id
INNER JOIN users u2 ON o2.user_id = u2.user_id
INNER JOIN products p ON oi1.product_id = p.product_id
WHERE u1.user_id < u2.user_id;
```

## 🎓 Exercises

### Setup
1. Make sure you have the database running
2. Navigate to the exercise directory:
```bash
cd exercises/02-joins
```

### Exercise 1: Basic INNER JOIN
**Archivo**: `starter/01_inner_join.sql`

Escribe queries para:
- Orders with user name
- Products in orders with product name
- Items de orden con precio actual del producto
- Actividad de usuarios con nombre del usuario

### Exercise 2: LEFT JOIN
**Archivo**: `starter/02_left_join.sql`

Escribe queries para:
- All users with order count (even without orders)
- Todos los productos con total vendido (incluso sin ventas)
- Users who have NOT placed orders
- Productos que NO han sido vendidos

### Exercise 3: Multiple JOINs
**Archivo**: `starter/03_multiple_joins.sql`

queries complejas con 3+ tables:
- Complete orders (user + items + products)
- Resumen de compras por usuario
- Most purchased products with order information
- Actividad de usuarios con productos relacionados

### Exercise 4: Agregaciones con JOIN
**Archivo**: `starter/04_aggregations.sql`

Combine JOINs with aggregation functions:
- Total gastado por usuario
- Number of orders per product
- Most popular products by country
- Revenue by product category

### Exercise 5: Special Cases
**Archivo**: `starter/05_special_cases.sql`

Situaciones avanzadas:
- Self-join: users from the same country
- Orders without items (data integrity)
- Cross-tabulation con JOINs
- Queries con filtros en tables unidas

### Exercise 6: Real Use Cases
**Archivo**: `starter/06_real_world.sql`

Practical queries for analytics:
- Dashboard de ventas
- User behavior analysis
- Reportes de inventario
- E-commerce metrics

## 📊 Diagrama del Esquema

```
users (1) ----< (N) orders
                     ^
                     |
                  order_id
                     |
                     v
products (1) ----< (N) order_items (N) >---- (1) orders

users (1) ----< (N) user_activity (N) >---- (0..1) products
```

**Relaciones**:
- A user has many orders (1:N)
- Una orden tiene muchos items (1:N)
- Un producto aparece en muchos items (1:N)
- Un usuario tiene muchas actividades (1:N)
- Una actividad puede relacionarse con un producto (N:0..1)

## ✅ Success Criteria

Para cada query:
- ✓ Correct JOIN (INNER vs LEFT depending on the case)
- ✓ ON clause precisa con las claves correctas
- ✓ Alias de table para legibilidad
- ✓ Appropriate selection of columns
- ✓ Correctly applied filters
- ✓ Ordered results when applicable

## 🔍 Visualizar JOINs

```sql
-- INNER JOIN: Solo coincidencias
-- users: A, B, C (have orders)
-- orders: orders from A, B, C
-- Result: A, B, C with their orders

-- LEFT JOIN: Todos de la izquierda
-- users: A, B, C, D (D without orders)
-- orders: orders from A, B, C
-- Result: A, B, C with orders, D with NULL in order columns

-- RIGHT JOIN: Todos de la derecha
-- users: A, B, C
-- orders: orders from A, B, C, and one orphan order X
-- Result: A, B, C with orders, X with NULL in user columns

-- FULL OUTER JOIN: Todos de ambos lados
-- Result: All users (with/without orders) + all orders (with/without user)
```

## 🔍 Testing

```bash
# Run individual file
psql -h localhost -U dataengineer -d ecommerce -f starter/01_inner_join.sql

# Comparar con soluciones
diff <(psql -h localhost -U dataengineer -d ecommerce -f starter/01_inner_join.sql) \
     <(psql -h localhost -U dataengineer -d ecommerce -f solution/01_inner_join.sql)
```

## 💡 Hints

Do you need help? query`hints.md` para pistas.

## 📖 Soluciones

The complete solutions are in`solution/`.

## 📚 Additional Resources

- [PostgreSQL JOIN Documentation](https://www.postgresql.org/docs/current/tutorial-join.html)
- [Visual JOIN Explanation](https://www.postgresqltutorial.com/postgresql-tutorial/postgresql-joins/)
- [JOIN Performance Tips](https://www.postgresql.org/docs/current/explicit-joins.html)

## ⏱️ Tiempo Estimado

- **Lectura**: 20 minutos
- **Exercises**: 60-90 minutos
- **Total**: ~110 minutos

## 🎯 Next Steps

Once you complete this exercise, continue with:
- **Exercise 03**: Aggregations - GROUP BY and aggregation functions

---

**Tip**: Usa `EXPLAIN`to see the execution plan of queries with JOINs and understand how PostgreSQL optimizes them.
