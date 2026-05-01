# SQL Fundamentals: Core Concepts

## Table of Contents

1. [Introduction to SQL](#introduction-to-sql)
2. [Database Fundamentals](#database-fundamentals)
3. [SELECT Statement](#select-statement)
4. [Filtering with WHERE](#filtering-with-where)
5. [Sorting and Limiting](#sorting-and-limiting)
6. [JOIN Operations](#join-operations)
7. [Aggregations and GROUP BY](#aggregations-and-group-by)
8. [Window Functions](#window-functions)
9. [Common Table Expressions (CTEs)](#common-table-expressions-ctes)
10. [Subqueries](#subqueries)
11. [Data Types](#data-types)
12. [NULL Handling](#null-handling)
13. [String Operations](#string-operations)
14. [Date and Time Functions](#date-and-time-functions)
15. [CASE Expressions](#case-expressions)
16. [Set Operations](#set-operations)
17. [Data Modification](#data-modification)
18. [Transactions](#transactions)
19. [Best Practices](#best-practices)
20. [Common Patterns](#common-patterns)

---

## Introduction to SQL

### What is SQL?

**SQL (Structured Query Language)** is the standard language for interacting with relational databases. It allows you to:

- **Query data**: Retrieve specific information from databases
- **Manipulate data**: Insert, update, and delete records
- **Define structure**: Create and modify database schemas
- **Control access**: Manage permissions and security

SQL is declarative—you specify *what* you want, not *how* to get it. The database engine optimizes the execution plan.

### Why SQL for Data Engineering?

Data engineers use SQL extensively:

1. **Data Exploration**: Understanding datasets before building pipelines
2. **Data Transformation**: ETL/ELT processes in data warehouses
3. **Data Quality**: Validating and cleaning data
4. **Analytics**: Aggregating and summarizing for insights
5. **pipeline Orchestration**: Many tools (dbt, Airflow) use SQL heavily

### SQL Dialects

While SQL is standardized (ANSI SQL), implementations vary:

- **PostgreSQL**: Open-source, feature-rich, used in this module
- **MySQL**: Popular for web applications
- **SQL Server**: Microsoft's database
- **Oracle**: Enterprise database
- **SQLite**: Lightweight, embedded
- **Presto/Athena**: Query engines for data lakes
- **Spark SQL**: Distributed SQL processing
- **BigQuery**: Google's data warehouse

Most concepts transfer between dialects, but syntax details differ.

---

## Fundamentos de databases

### model de database Relacional

Las databases relacionales organizan datos en **tables** con:

- **rows (registros)**: Entradas individuales de datos
- **columns (campos)**: Atributos de los datos
- **Primary Key**: Unique identifier for each row
- **Foreign Key**: Reference to a primary key in another table

**Ejemplo: database de E-commerce**

```
Tabla Users:
+---------+----------------+------------+-----------+
| user_id | email          | first_name | last_name |
+---------+----------------+------------+-----------+
| 1       | john@email.com | John       | Smith     |
| 2       | jane@email.com | Jane       | Doe       |
+---------+----------------+------------+-----------+

Tabla Orders:
+----------+---------+------------+--------------+
| order_id | user_id | order_date | total_amount |
+----------+---------+------------+--------------+
| 101      | 1       | 2024-01-15 | 150.00       |
| 102      | 2       | 2024-01-16 | 200.00       |
+----------+---------+------------+--------------+
```

### Relaciones

**One to Many**: A user can have many orders
**Many to Many**: Many orders can contain many products (via join table)
**One to One**: A user has a (unique) profile

### Standardization

**Normalization** reduces data redundancy:

- **1NF**: Atomic values, without repeating groups
- **2NF**: Sin dependencias parciales de clave primaria
- **3NF**: Sin dependencias transitivas

Los data warehouses frecuentemente **desnormalizan** para performance de querys (esquemas estrella/copo de nieve).

### Propiedades ACID

Las transactions garantizan:

- **Atomicidad**: Todo o nada
- **Consistency**: Valid state transitions
- **Aislamiento**: transactions concurrentes no interfieren
- **Durabilidad**: Cambios confirmados persisten

---

## SELECT statement

### Basic SELECT

The `SELECT` statement retrieves data:

```sql
-- Select all columns
SELECT * FROM users;

-- Select specific columns
SELECT first_name, last_name FROM users;

-- Select with expressions
SELECT
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name) AS full_name
FROM users;
```

### Alias de columns

Usa `AS` para renombrar columns en resultados:

```sql
SELECT
    user_id AS id,
    email AS user_email,
    created_at AS registration_date
FROM users;
```

### DISTINCT

Eliminar valores duplicados:

```sql
-- Todos los países únicos
SELECT DISTINCT country FROM users;

-- Combinaciones únicas
SELECT DISTINCT country, city FROM users;
```

**Nota**: `DISTINCT` puede ser costoso en datasets grandes. Considera si realmente lo necesitas.

### Literales y Expresiones

```sql
SELECT
    'Welcome' AS greeting,
    42 AS magic_number,
    price * 0.9 AS discounted_price,
    CURRENT_DATE AS today
FROM products;
```

---

## Filtrado con WHERE

### Basic Filtering

`WHERE` filters rows based on conditions:

```sql
-- Single condition
SELECT * FROM products WHERE price > 100;

-- Multiple conditions with AND
SELECT * FROM products
WHERE price > 100 AND category = 'Electronics';

-- Multiple conditions with OR
SELECT * FROM products
WHERE category = 'Electronics' OR category = 'Books';
```

### Comparison Operators

```sql
=   -- Equal
<>  -- Not equal (also !=)
<   -- Less than
<=  -- Less than or equal
>   -- Greater than
>=  -- Greater than or equal
```

### IN Operator

```sql
-- Match any value in list
SELECT * FROM products
WHERE category IN ('Electronics', 'Books', 'Clothing');

-- Equivalent to multiple ORs:
WHERE category = 'Electronics'
   OR category = 'Books'
   OR category = 'Clothing'
```

### BETWEEN

```sql
-- Inclusive range
SELECT * FROM products
WHERE price BETWEEN 50 AND 100;

-- Equivalent to:
WHERE price >= 50 AND price <= 100

-- Dates
SELECT * FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31';
```

### LIKE Pattern Matching

```sql
-- % coincide con cualquier secuencia de caracteres
SELECT * FROM users WHERE email LIKE '%@gmail.com';

-- _ coincide con un solo carácter
SELECT * FROM users WHERE first_name LIKE 'J__n';  -- John, Joan

-- Insensible a mayúsculas: ILIKE (PostgreSQL)
SELECT * FROM users WHERE email ILIKE '%GMAIL.COM';
```

### IS NULL

```sql
-- Verificar valores NULL
SELECT * FROM users WHERE phone IS NULL;

-- Verificar valores no-NULL
SELECT * FROM users WHERE phone IS NOT NULL;
```

**Importante**: Usa `IS NULL`, no `= NULL` (las comparaciones NULL siempre retornan NULL, no verdadero/falso).

---

## Ordering and Limitation

### ORDER BY

Sort results:

```sql
-- Ascending (default)
SELECT * FROM products ORDER BY price;

-- Descending
SELECT * FROM products ORDER BY price DESC;

-- Multiple columns
SELECT * FROM products
ORDER BY category ASC, price DESC;

-- With expressions
SELECT * FROM products
ORDER BY (price * 0.9) DESC;
```

**Performance**: Sorting large datasets is expensive. Use indexes on frequently sorted columns.

### LIMIT and OFFSET

Pagination:

```sql
-- First 10 rows
SELECT * FROM products LIMIT 10;

-- Saltar primeras 20, obtener siguientes 10 (página 3)
SELECT * FROM products
ORDER BY product_id
LIMIT 10 OFFSET 20;
```

**MySQL/SQL Server**: Usa `LIMIT` (MySQL) o `TOP` (SQL Server).
**Standard SQL**:`FETCH FIRST n ROWS ONLY`

### FETCH (Standard SQL)

```sql
-- Paginación SQL estándar
SELECT * FROM products
ORDER BY product_id
OFFSET 20 ROWS
FETCH FIRST 10 ROWS ONLY;
```

---

## Operaciones JOIN

### Why JOINs?

Relational databases split data across tables to avoid redundancy. JOINs combine them:

```sql
-- Get order details with user information
SELECT
    orders.order_id,
    users.first_name,
    users.last_name,
    orders.total_amount
FROM orders
JOIN users ON orders.user_id = users.user_id;
```

### INNER JOIN

Returns only matching rows from both tables:

```sql
SELECT
    o.order_id,
    u.email,
    o.total_amount
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id;
```

**Visualization**:
```
Users (3 rows)     Orders (5 rows)
user_id  name      order_id  user_id  amount
1        John      101       1        100
2        Jane      102       2        200
3        Bob       103       1        150
                   104       2        300
                   105       4        400  <- no matching user

INNER JOIN Result (4 rows - only matching):
John - 101 - 100
Jane - 102 - 200
John - 103 - 150
Jane - 104 - 300
```

### LEFT JOIN (LEFT OUTER JOIN)

Retorna todas las rows de la table izquierda, con NULLs para rows no coincidentes de la table derecha:

```sql
SELECT
    u.user_id,
    u.first_name,
    o.order_id,
    o.total_amount
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;
```

**Use case**: Find all users, including those without orders.

**Display**:
```
Users         Orders
1  John       101  1  100
2  Jane       102  2  200
3  Bob        (ninguna)

Resultado LEFT JOIN:
1  John  101  100
2  Jane  102  200
3  Bob   NULL NULL
```

### RIGHT JOIN

Opuesto de LEFT JOIN:

```sql
SELECT
    u.first_name,
    o.order_id
FROM users u
RIGHT JOIN orders o ON u.user_id = o.user_id;
```

**Caso de uso**: Raramente usado; puedes reescribir como LEFT JOIN intercambiando tables.

### FULL OUTER JOIN

Retorna todas las rows de ambas tables:

```sql
SELECT
    u.user_id,
    u.first_name,
    o.order_id
FROM users u
FULL OUTER JOIN orders o ON u.user_id = o.user_id;
```

**Use case**: Find all users and all orders, showing which ones do not match.

### CROSS JOIN

Cartesian product (each combination):

```sql
SELECT
    colors.color_name,
    sizes.size_name
FROM colors
CROSS JOIN sizes;
```

**Caso de uso**: Generar todas las combinaciones (ej., variantes de producto).

**Advertencia**: El resultado tiene `rows(colors) × rows(sizes)`rows. It can explode quickly.

### Self JOIN

Unir table consigo misma:

```sql
-- Encontrar empleados y sus gerentes
SELECT
    e.name AS employee,
    m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;
```

### Multiple JOINs

```sql
SELECT
    u.first_name,
    o.order_id,
    oi.quantity,
    p.product_name
FROM users u
JOIN orders o ON u.user_id = o.user_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id;
```

**Order matters** for readability, not performance (optimizer decides).

### JOIN Conditions

```sql
-- Equality
ON orders.user_id = users.user_id

-- Multiple conditions
ON orders.user_id = users.user_id
AND orders.country = users.country

-- Non-equality (rare)
ON products.price > discounts.min_price
```

### JOIN Performance

- Index the join columns
- Filter early (WHERE before JOIN when possible)
- Understand cardinality (1:1, 1:many, many:many)
- Use EXPLAIN to see execution plan

---

## Aggregations and GROUP BY

### Aggregate Functions

Calculate summary statistics:

```sql
-- Count rows
SELECT COUNT(*) FROM orders;

-- Count non-NULL values
SELECT COUNT(user_id) FROM orders;

-- Sum
SELECT SUM(total_amount) FROM orders;

-- Average
SELECT AVG(price) FROM products;

-- Min/Max
SELECT MIN(price), MAX(price) FROM products;
```

### GROUP BY

Group rows and aggregate per group:

```sql
-- Total sales per user
SELECT
    user_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY user_id;
```

**Rule**: Every column in SELECT must be:
1. In GROUP BY, OR
2. Inside an aggregate function

```sql
-- WRONG: email not in GROUP BY or aggregate
SELECT user_id, email, COUNT(*) FROM orders GROUP BY user_id;

-- CORRECT:
SELECT user_id, COUNT(*) FROM orders GROUP BY user_id;
```

### Multiple GROUP BY Columns

```sql
-- Sales per country and category
SELECT
    country,
    category,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count
FROM sales
GROUP BY country, category;
```

### HAVING

Filter groups (like WHERE for aggregates):

```sql
-- Users with more than 5 orders
SELECT
    user_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5;
```

**WHERE vs HAVING**:
- `WHERE` filters rows before grouping
- `HAVING` filters groups after aggregation

```sql
-- Correct order: WHERE, GROUP BY, HAVING
SELECT
    category,
    AVG(price) AS avg_price
FROM products
WHERE stock > 0           -- Filter individual products
GROUP BY category
HAVING AVG(price) > 100;  -- Filter aggregated results
```

### DISTINCT in Aggregates

```sql
-- Unique users who placed orders
SELECT COUNT(DISTINCT user_id) FROM orders;

-- Average unique products per order
SELECT AVG(product_count) FROM (
    SELECT order_id, COUNT(DISTINCT product_id) AS product_count
    FROM order_items
    GROUP BY order_id
) subquery;
```

---

## Window Functions

### What are Window Functions?

Window functions perform calculations across rows **related** to the current row, without collapsing results like GROUP BY:

```sql
-- Add row number to each user's orders
SELECT
    user_id,
    order_id,
    order_date,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) AS order_sequence
FROM orders;
```

**Result**:
```
user_id  order_id  order_date   order_sequence
1        101       2024-01-15   1
1        103       2024-01-20   2
1        105       2024-01-25   3
2        102       2024-01-16   1
2        104       2024-01-21   2
```

### ROW_NUMBER()

Assigns unique sequential integers:

```sql
-- Number all orders
SELECT
    order_id,
    ROW_NUMBER() OVER (ORDER BY order_date) AS seq
FROM orders;
```

### RANK() and DENSE_RANK()

Handle ties differently:

```sql
SELECT
    name,
    score,
    RANK() OVER (ORDER BY score DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rank
FROM students;
```

**Result**:
```
name     score  rank  dense_rank
Alice    95     1     1
Bob      95     1     1   <- same score
Charlie  90     3     2   <- RANK skips, DENSE_RANK doesn't
David    85     4     3
```

### PARTITION BY

Restart calculation for each partition:

```sql
-- Rank products within each category
SELECT
    category,
    product_name,
    price,
    RANK() OVER (PARTITION BY category ORDER BY price DESC) AS price_rank
FROM products;
```

### LAG() and LEAD()

Access previous/next row values:

```sql
-- Compare each order to the previous one
SELECT
    user_id,
    order_date,
    total_amount,
    LAG(total_amount) OVER (PARTITION BY user_id ORDER BY order_date) AS previous_amount,
    total_amount - LAG(total_amount) OVER (PARTITION BY user_id ORDER BY order_date) AS difference
FROM orders;
```

### Running Totals

```sql
-- Cumulative sales by date
SELECT
    order_date,
    daily_sales,
    SUM(daily_sales) OVER (ORDER BY order_date) AS cumulative_sales
FROM (
    SELECT order_date, SUM(total_amount) AS daily_sales
    FROM orders
    GROUP BY order_date
) daily;
```

### Window Frames

Control which rows are included:

```sql
-- 7-day moving average
SELECT
    order_date,
    daily_sales,
    AVG(daily_sales) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM daily_sales;
```

Frame options:
- `ROWS BETWEEN ... AND ...`: Physical row count
- `RANGE BETWEEN ... AND ...`: Logical value range
- `UNBOUNDED PRECEDING`: Start of partition
- `CURRENT ROW`: Current row
- `n PRECEDING/FOLLOWING`: n rows before/after

### NTILE()

Divide rows into buckets:

```sql
-- Divide users into 4 quartiles by total spend
SELECT
    user_id,
    total_spent,
    NTILE(4) OVER (ORDER BY total_spent) AS quartile
FROM user_totals;
```

### FIRST_VALUE() and LAST_VALUE()

```sql
-- Show highest price in each category
SELECT
    category,
    product_name,
    price,
    FIRST_VALUE(product_name) OVER (
        PARTITION BY category
        ORDER BY price DESC
    ) AS top_product
FROM products;
```

---

## Common Table Expressions (CTEs)

### What is a CTE?

A **CTE** (Common Table Expression) is a named temporary result set:

```sql
WITH category_sales AS (
    SELECT
        category,
        SUM(amount) AS total_sales
    FROM sales
    GROUP BY category
)
SELECT * FROM category_sales WHERE total_sales > 10000;
```

**Benefits**:
- Improves readability
- Can be referenced multiple times
- Breaks complex queries into steps

### Multiple CTEs

```sql
WITH
user_totals AS (
    SELECT
        user_id,
        SUM(total_amount) AS total_spent
    FROM orders
    GROUP BY user_id
),
high_spenders AS (
    SELECT user_id FROM user_totals WHERE total_spent > 1000
)
SELECT
    u.first_name,
    u.email
FROM users u
JOIN high_spenders hs ON u.user_id = hs.user_id;
```

### Recursive CTEs

Generate hierarchical data:

```sql
-- Generate numbers 1 to 10
WITH RECURSIVE numbers AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 10
)
SELECT * FROM numbers;
```

**Use cases**:
- Organizational hierarchies
- Bill of materials
- Graph traversal
- Date series generation

### CTEs vs Subqueries

```sql
-- CTE (more readable)
WITH recent_orders AS (
    SELECT * FROM orders WHERE order_date > '2024-01-01'
)
SELECT user_id, COUNT(*) FROM recent_orders GROUP BY user_id;

-- Subquery (equivalent but less readable)
SELECT user_id, COUNT(*) FROM (
    SELECT * FROM orders WHERE order_date > '2024-01-01'
) AS recent_orders
GROUP BY user_id;
```

**When to use CTEs**:
- Multiple references to same subquery
- Complex logic that benefits from naming
- Recursive queries
- Readability is important

---

## Subqueries

### Scalar Subqueries

Return single value:

```sql
-- Compare to average
SELECT
    product_name,
    price,
    price - (SELECT AVG(price) FROM products) AS price_diff
FROM products;
```

### IN Subqueries

```sql
-- Users who placed orders
SELECT * FROM users
WHERE user_id IN (SELECT DISTINCT user_id FROM orders);
```

### EXISTS

Check if subquery returns any rows:

```sql
-- Users with at least one order
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.user_id
);
```

**EXISTS vs IN**:
- `EXISTS` stops at first match (faster)
- `IN` evaluates entire subquery
- Use `EXISTS` for correlated subqueries

### Correlated Subqueries

Reference outer query:

```sql
-- Each user's most recent order
SELECT
    user_id,
    order_id,
    order_date
FROM orders o1
WHERE order_date = (
    SELECT MAX(order_date)
    FROM orders o2
    WHERE o2.user_id = o1.user_id
);
```

**Performance**: Can be slow. Consider window functions instead.

### Subqueries in FROM

```sql
-- Average of daily averages
SELECT AVG(daily_avg) AS overall_avg
FROM (
    SELECT
        order_date,
        AVG(total_amount) AS daily_avg
    FROM orders
    GROUP BY order_date
) daily_stats;
```

---

## Data Types

### Numeric Types

```sql
-- Integers
SMALLINT        -- 2 bytes: -32,768 to 32,767
INTEGER (INT)   -- 4 bytes: -2B to 2B
BIGINT          -- 8 bytes: -9 quintillion to 9 quintillion

-- Decimals (exact)
DECIMAL(p, s)   -- p digits, s after decimal
NUMERIC(10, 2)  -- Example: 12345678.90

-- Floating point (approximate)
REAL            -- 4 bytes
DOUBLE PRECISION -- 8 bytes
```

**Use DECIMAL for money** (avoids floating-point errors).

### String Types

```sql
CHAR(n)         -- Fixed length, padded
VARCHAR(n)      -- Variable length, up to n
TEXT            -- Unlimited length
```

### Date and Time

```sql
DATE            -- 2024-01-15
TIME            -- 14:30:00
TIMESTAMP       -- 2024-01-15 14:30:00
TIMESTAMPTZ     -- With timezone (PostgreSQL)
INTERVAL        -- Duration: '2 days', '3 hours'
```

### Boolean

```sql
BOOLEAN         -- TRUE, FALSE, NULL
```

### JSON

```sql
JSON            -- Text representation
JSONB           -- Binary (PostgreSQL, faster, indexable)
```

### Arrays (PostgreSQL)

```sql
INTEGER[]       -- Array of integers
TEXT[]          -- Array of strings
```

### UUID

```sql
UUID            -- Universally unique identifier
```

### Type Casting

```sql
-- Explicit cast
SELECT CAST('123' AS INTEGER);
SELECT CAST('2024-01-15' AS DATE);

-- PostgreSQL shorthand
SELECT '123'::INTEGER;
SELECT '2024-01-15'::DATE;
```

---

## NULL Handling

### Understanding NULL

`NULL` represents **unknown** or **missing** data, not zero or empty string.

```sql
-- These are different:
NULL    -- Unknown
0       -- Zero
''      -- Empty string
```

### NULL Comparisons

```sql
-- Always use IS NULL / IS NOT NULL
WHERE column IS NULL
WHERE column IS NOT NULL

-- NEVER use = NULL (always returns NULL, not TRUE)
WHERE column = NULL  -- WRONG!
```

### NULL in Expressions

```sql
SELECT 10 + NULL;        -- NULL
SELECT 'Hello' || NULL;  -- NULL
SELECT NULL = NULL;      -- NULL (not TRUE!)
```

### COALESCE

Return first non-NULL value:

```sql
-- Provide default for NULL
SELECT COALESCE(phone, email, 'No contact') AS contact FROM users;

-- Equivalent to nested CASE
SELECT CASE
    WHEN phone IS NOT NULL THEN phone
    WHEN email IS NOT NULL THEN email
    ELSE 'No contact'
END AS contact FROM users;
```

### NULLIF

Return NULL if two values are equal:

```sql
-- Avoid division by zero
SELECT
    total_sales / NULLIF(total_orders, 0) AS avg_order_value
FROM metrics;
```

### NULL in Aggregates

```sql
-- Aggregates ignore NULL
SELECT
    COUNT(*) AS all_rows,
    COUNT(phone) AS rows_with_phone,
    AVG(rating) AS avg_rating  -- NULL ratings excluded
FROM users;
```

---

## String Operations

### Concatenation

```sql
-- CONCAT function
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;

-- || operator (standard SQL)
SELECT first_name || ' ' || last_name AS full_name FROM users;
```

### UPPER, LOWER, INITCAP

```sql
SELECT
    UPPER(name) AS uppercase,
    LOWER(name) AS lowercase,
    INITCAP(name) AS title_case
FROM products;
```

### TRIM

```sql
SELECT
    TRIM('  hello  ') AS trimmed,        -- 'hello'
    LTRIM('  hello  ') AS left_trimmed,  -- 'hello  '
    RTRIM('  hello  ') AS right_trimmed  -- '  hello'
```

### SUBSTRING

```sql
-- SUBSTRING(string FROM start FOR length)
SELECT SUBSTRING(email FROM 1 FOR 5) AS email_prefix FROM users;

-- PostgreSQL alternative
SELECT SUBSTR(email, 1, 5) AS email_prefix FROM users;
```

### LENGTH

```sql
SELECT LENGTH(description) AS desc_length FROM products;
```

### REPLACE

```sql
SELECT REPLACE(phone, '-', '') AS phone_clean FROM users;
```

### SPLIT_PART (PostgreSQL)

```sql
-- Split by delimiter, get part
SELECT SPLIT_PART(email, '@', 2) AS domain FROM users;
```

### Regular Expressions (PostgreSQL)

```sql
-- Match pattern
SELECT * FROM users WHERE email ~ '^[a-z]+@gmail\.com$';

-- Extract match
SELECT (REGEXP_MATCH(email, '([a-z]+)@'))[1] AS username FROM users;
```

---

## Date and Time Functions

### Current Date/Time

```sql
SELECT
    CURRENT_DATE AS today,
    CURRENT_TIME AS now_time,
    CURRENT_TIMESTAMP AS now,
    NOW() AS now_function;
```

### Extracting Parts

```sql
SELECT
    EXTRACT(YEAR FROM order_date) AS year,
    EXTRACT(MONTH FROM order_date) AS month,
    EXTRACT(DAY FROM order_date) AS day,
    EXTRACT(DOW FROM order_date) AS day_of_week  -- 0=Sunday
FROM orders;
```

### Date Arithmetic

```sql
-- Add interval
SELECT order_date + INTERVAL '7 days' AS one_week_later FROM orders;

-- Subtract dates
SELECT AGE(end_date, start_date) AS duration FROM events;

-- Days between
SELECT DATE_PART('day', end_date - start_date) AS days_diff FROM events;
```

### Formatting

```sql
-- Format date
SELECT TO_CHAR(order_date, 'YYYY-MM-DD') AS formatted FROM orders;
SELECT TO_CHAR(order_date, 'Mon DD, YYYY') AS readable FROM orders;

-- Parse string to date
SELECT TO_DATE('2024-01-15', 'YYYY-MM-DD') AS parsed;
```

### Truncating

```sql
-- Truncate to start of period
SELECT
    DATE_TRUNC('month', order_date) AS month_start,
    DATE_TRUNC('week', order_date) AS week_start
FROM orders;
```

### Time Zones

```sql
-- Convert to timezone
SELECT order_timestamp AT TIME ZONE 'America/New_York' AS ny_time FROM orders;
```

---

## CASE Expressions

### Simple CASE

```sql
SELECT
    product_name,
    CASE category
        WHEN 'Electronics' THEN 'Tech'
        WHEN 'Books' THEN 'Media'
        ELSE 'Other'
    END AS category_group
FROM products;
```

### Searched CASE

More flexible with conditions:

```sql
SELECT
    product_name,
    price,
    CASE
        WHEN price < 50 THEN 'Budget'
        WHEN price BETWEEN 50 AND 200 THEN 'Mid-range'
        ELSE 'Premium'
    END AS price_tier
FROM products;
```

### CASE in Aggregates

```sql
-- Conditional counting
SELECT
    COUNT(*) AS total_orders,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS completed,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) AS cancelled
FROM orders;
```

### Pivot with CASE

```sql
-- Convert rows to columns
SELECT
    order_date,
    SUM(CASE WHEN category = 'Electronics' THEN amount ELSE 0 END) AS electronics_sales,
    SUM(CASE WHEN category = 'Books' THEN amount ELSE 0 END) AS books_sales
FROM sales
GROUP BY order_date;
```

---

## Set Operations

### UNION

Combine results, removing duplicates:

```sql
SELECT user_id FROM orders_2023
UNION
SELECT user_id FROM orders_2024;
```

### UNION ALL

Keep duplicates (faster):

```sql
SELECT user_id FROM orders_2023
UNION ALL
SELECT user_id FROM orders_2024;
```

### INTERSECT

Rows in both queries:

```sql
-- Users who ordered in both years
SELECT user_id FROM orders_2023
INTERSECT
SELECT user_id FROM orders_2024;
```

### EXCEPT

Rows in first query but not second:

```sql
-- Users who ordered in 2023 but not 2024
SELECT user_id FROM orders_2023
EXCEPT
SELECT user_id FROM orders_2024;
```

**Requirements**:
- Same number of columns
- Compatible data types
- Column names from first query

---

## Data Modification

### INSERT

```sql
-- Single row
INSERT INTO users (first_name, last_name, email)
VALUES ('John', 'Smith', 'john@email.com');

-- Multiple rows
INSERT INTO users (first_name, last_name, email)
VALUES
    ('Jane', 'Doe', 'jane@email.com'),
    ('Bob', 'Wilson', 'bob@email.com');

-- From SELECT
INSERT INTO users_archive
SELECT * FROM users WHERE created_at < '2023-01-01';
```

### UPDATE

```sql
-- Update all rows
UPDATE products SET price = price * 1.1;

-- With condition
UPDATE products
SET price = price * 1.1
WHERE category = 'Electronics';

-- Multiple columns
UPDATE users
SET
    last_login = CURRENT_TIMESTAMP,
    login_count = login_count + 1
WHERE user_id = 123;
```

### DELETE

```sql
-- Delete specific rows
DELETE FROM orders WHERE status = 'cancelled';

-- Delete all rows (keep table structure)
DELETE FROM temp_table;

-- Faster alternative (truncate)
TRUNCATE TABLE temp_table;
```

### RETURNING (PostgreSQL)

Get modified rows:

```sql
INSERT INTO users (first_name, last_name)
VALUES ('New', 'User')
RETURNING user_id, created_at;

UPDATE products
SET price = price * 0.9
WHERE category = 'Books'
RETURNING product_id, product_name, price;
```

---

## Transactions

### What is a Transaction?

A **transaction** is a unit of work that either fully succeeds or fully fails.

```sql
BEGIN;  -- Start transaction

    UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;

COMMIT;  -- Save changes
```

If anything fails:

```sql
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
    -- Error occurs here
    UPDATE accounts SET balance = balance + 100 WHERE account_id = 999;  -- Doesn't exist
ROLLBACK;  -- Undo all changes
```

### Savepoints

```sql
BEGIN;
    INSERT INTO orders (...) VALUES (...);

    SAVEPOINT before_items;

    INSERT INTO order_items (...) VALUES (...);
    -- Error

    ROLLBACK TO SAVEPOINT before_items;  -- Keep order, undo items

COMMIT;
```

### Isolation Levels

Control how transactions see each other's changes:

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

---

## Best Practices

### 1. Use Explicit Column Names

```sql
-- DON'T:
SELECT * FROM users;

-- DO:
SELECT user_id, first_name, email FROM users;
```

**Why**: Schema changes won't break queries.

### 2. Filter Early

```sql
-- BETTER:
SELECT u.first_name, o.order_id
FROM users u
JOIN orders o ON u.user_id = o.user_id
WHERE o.order_date > '2024-01-01';

-- WORSE:
SELECT u.first_name, o.order_id
FROM users u
JOIN (SELECT * FROM orders WHERE order_date > '2024-01-01') o
ON u.user_id = o.user_id;
```

### 3. Use Appropriate Data Types

```sql
-- DON'T store money as FLOAT
CREATE TABLE products (price FLOAT);  -- Bad

-- DO use DECIMAL
CREATE TABLE products (price DECIMAL(10, 2));  -- Good
```

### 4. Index Frequently Queried Columns

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_date ON orders(order_date);
```

### 5. Use CTEs for Readability

```sql
-- Instead of nested subqueries, use CTEs
WITH active_users AS (...),
     recent_orders AS (...)
SELECT ...
```

### 6. Avoid SELECT DISTINCT on Large Tables

```sql
-- Expensive:
SELECT DISTINCT country FROM users;  -- 10M rows

-- Better: Use GROUP BY if you need counts
SELECT country, COUNT(*) FROM users GROUP BY country;
```

### 7. Use LIMIT for Exploration

```sql
-- Quick peek at data
SELECT * FROM huge_table LIMIT 100;
```

### 8. Comment Complex Queries

```sql
-- Calculate 30-day rolling average of sales
-- partitioned by product category
WITH daily_sales AS (...)
SELECT ...
```

### 9. Test with EXPLAIN

```sql
EXPLAIN ANALYZE
SELECT ... FROM ... WHERE ...;
```

### 10. Use Transactions for Data Integrity

```sql
BEGIN;
    -- Multiple related operations
COMMIT;
```

---

## Common Patterns

### Ranking Top N per Group

```sql
-- Top 3 products per category by sales
WITH ranked AS (
    SELECT
        category,
        product_name,
        sales,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC) AS rank
    FROM product_sales
)
SELECT * FROM ranked WHERE rank <= 3;
```

### Finding Gaps in Sequences

```sql
-- Missing order IDs
SELECT
    expected_id
FROM generate_series(
    (SELECT MIN(order_id) FROM orders),
    (SELECT MAX(order_id) FROM orders)
) AS expected_id
WHERE expected_id NOT IN (SELECT order_id FROM orders);
```

### Running Totals by Group

```sql
SELECT
    user_id,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY user_id
        ORDER BY order_date
    ) AS cumulative_spend
FROM orders;
```

### Pivot Table

```sql
SELECT
    product_id,
    SUM(CASE WHEN month = 1 THEN sales END) AS jan,
    SUM(CASE WHEN month = 2 THEN sales END) AS feb,
    SUM(CASE WHEN month = 3 THEN sales END) AS mar
FROM monthly_sales
GROUP BY product_id;
```

### Deduplication

```sql
-- Keep only first occurrence
DELETE FROM users
WHERE user_id NOT IN (
    SELECT MIN(user_id)
    FROM users
    GROUP BY email
);
```

### Date Ranges

```sql
-- Generate date series
SELECT
    date_series.date,
    COALESCE(sales.amount, 0) AS amount
FROM generate_series(
    '2024-01-01'::date,
    '2024-12-31'::date,
    '1 day'::interval
) AS date_series(date)
LEFT JOIN daily_sales sales ON date_series.date = sales.sale_date;
```

---

## Summary

This covers the core SQL concepts you need for data engineering:

1. **Fundamentals**: SELECT, WHERE, ORDER BY, LIMIT
2. **Joins**: Combine tables (INNER, LEFT, RIGHT, FULL, CROSS)
3. **Aggregations**: GROUP BY with COUNT, SUM, AVG, etc.
4. **Window Functions**: Analytical queries without collapsing rows
5. **CTEs**: Readable, maintainable complex queries
6. **Data Types**: Choose appropriate types for your data
7. **Best Practices**: Write efficient, maintainable SQL

**Next Steps**:

- Read `theory/architecture.md` for query execution internals
- Complete exercises to practice these concepts
- Study `theory/resources.md` for additional learning materials

---

**Document Version**: 1.0
**Last Updated**: February 2026
**Word Count**: ~8,500 words
