# Exercise 01: Basic Queries

## 🎯 Objetivos de Aprendizaje

By completing this exercise, you will be able to:

- Write basic SELECT queries with column projection
- Filter data using WHERE clauses with multiple conditions
- Ordenar resultados con ORDER BY (ascendente y descendente)
- Limit results with LIMIT and OFFSET for pagination
- Use comparison and logical operators (AND, OR, NOT)
- Trabajar con operadores LIKE, IN, BETWEEN para patrones
- Manejar valores NULL correctamente con IS NULL / IS NOT NULL
- Aplicar alias a columns para mejorar legibilidad

## 📚 Conceptos Cubiertos

### 1. SELECT and Projection
```sql
-- Seleccionar todas las columnas
SELECT * FROM users;

-- Seleccionar columnas específicas
SELECT first_name, last_name, email FROM users;

-- Usar alias
SELECT first_name AS nombre, last_name AS apellido FROM users;
```

### 2. WHERE y Filtrado
```sql
-- Condición simple
SELECT * FROM users WHERE country = 'US';

-- Múltiples condiciones con AND
SELECT * FROM users WHERE country = 'US' AND is_active = TRUE;

-- Condiciones con OR
SELECT * FROM users WHERE country = 'US' OR country = 'GB';

-- Negación con NOT
SELECT * FROM users WHERE NOT country = 'US';
```

### 3. Comparison Operators
```sql
-- Igualdad y desigualdad
WHERE price = 100
WHERE price != 100
WHERE price <> 100  -- Equivalente a !=

-- Mayor/menor
WHERE loyalty_points > 100
WHERE loyalty_points >= 100
WHERE price < 50
WHERE price <= 50
```

### 4. Operadores Especiales
```sql
-- IN (lista de valores)
SELECT * FROM users WHERE country IN ('US', 'GB', 'CA');

-- BETWEEN (rango inclusivo)
SELECT * FROM products WHERE price BETWEEN 50 AND 100;

-- LIKE (pattern matching)
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT * FROM products WHERE product_name LIKE 'Laptop%';

-- NULL checks
SELECT * FROM orders WHERE tracking_number IS NULL;
SELECT * FROM orders WHERE tracking_number IS NOT NULL;
```

### 5. ORDER BY
```sql
-- Orden ascendente (por defecto)
SELECT * FROM users ORDER BY registration_date;
SELECT * FROM users ORDER BY registration_date ASC;

-- Orden descendente
SELECT * FROM products ORDER BY price DESC;

-- Ordenar por múltiples columnas
SELECT * FROM users ORDER BY country ASC, loyalty_points DESC;
```

### 6. LIMIT y OFFSET
```sql
-- Limitar resultados
SELECT * FROM users LIMIT 10;

-- Paginación
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 0;  -- Página 1
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 10; -- Página 2
```

## 🎓 Ejercicios

### Setup
1. Make sure you have the database running:
```bash
cd infrastructure
docker-compose up -d
```

2. Navega al directorio del ejercicio:
```bash
cd exercises/01-basic-queries
```

### Exercise 1: Basic Projection
**Archivo**: `starter/01_projection.sql`

Escribe querys para:
- Obtener todos los usuarios con solo nombre, apellido y email
- Obtain products with name and price, using descriptive aliases in Spanish
- Get the first 5 orders with id, date and total

### Ejercicio 2: Filtrado con WHERE
**Archivo**: `starter/02_filtering.sql`

Escribe querys para:
- Usuarios activos de Estados Unidos
- Productos con precio menor a $50
- Orders with status 'delivered' or 'shipped'
- Usuarios que NO son de US, GB o CA
- Productos sin stock (stock_quantity = 0)

### Ejercicio 3: Pattern Matching
**Archivo**: `starter/03_patterns.sql`

Escribe querys para:
- Usuarios con email de Gmail
- Productos que contienen "Laptop" en el nombre
- Usuarios cuyo nombre comienza con 'J'
- Products in 'Electronics' or 'Books' category
- Orders in a specific date range

### Ejercicio 4: Ordenamiento
**Archivo**: `starter/04_sorting.sql`

Escribe querys para:
- Usuarios ordenados por puntos de lealtad (mayor a menor)
- Productos ordenados por precio (menor a mayor)
- Most recent orders first
- Top 10 most expensive products
- Users by country and then by registration date

### Exercise 5: Pagination
**Archivo**: `starter/05_pagination.sql`

Escribe querys para:
- Primeros 10 usuarios
- Page 3 Users (records 21-30)
- Top 5 most expensive products
- Last 20 registered users

### Exercise 6: Combination of Techniques
**Archivo**: `starter/06_combined.sql`

queries complejas combinando todo lo aprendido:
- Active US or GB users with 100+ points, sorted by points
- Productos disponibles entre $20 y $100, ordenados por precio
- Last 10 orders completed with total > $100
- Electronics products in stock, excluding those more expensive than $500

## ✅ Success Criteria

Para cada query:
- ✓ Retorna los datos correctos
- ✓ Use valid SQL syntax
- ✓ Includes comments explaining the logic
- ✓ Follow formatting conventions (capital letters for keywords)
- ✓ Usa alias descriptivos cuando corresponda

## 🔍 Testing

Ejecuta tus querys:
```bash
# Ejecutar archivo individual
psql -h localhost -U dataengineer -d ecommerce -f starter/01_projection.sql

# Ejecutar todos los archivos
for f in starter/*.sql; do
    echo "=== Ejecutando $f ==="
    psql -h localhost -U dataengineer -d ecommerce -f "$f"
done
```

## 💡 Hints

Do you need help? query`hints.md`for clues without revealing the full solution.

## 📖 Soluciones

The complete solutions are in`solution/`. Intenta resolver los ejercicios por tu cuenta primero.

## 📚 Additional Resources

- [PostgreSQL SELECT Documentation](https://www.postgresql.org/docs/current/sql-select.html)
- [PostgreSQL Pattern Matching](https://www.postgresql.org/docs/current/functions-matching.html)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)

## ⏱️ Tiempo Estimado

- **Lectura**: 15 minutos
- **Ejercicios**: 45-60 minutos
- **Total**: ~75 minutos

## 🎯 Next Steps

Once you complete this exercise, continue with:
- **Exercise 02**: Joins - Combine data from multiple tables

---

**Tip**: Usa `\x` en psql para alternar entre formato vertical (mejor para ver registros individuales) y formato horizontal.
