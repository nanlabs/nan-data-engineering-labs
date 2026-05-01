# SQL Complete Reference Guide

A comprehensive SQL reference for the Module 03 - SQL Foundations exercises and beyond.

## Table of Contents

1. [SQL Fundamentals](#sql-fundamentals)
2. [Data Types](#data-types)
3. [DDL - Data Definition Language](#ddl---data-definition-language)
4. [DML - Data Manipulation Language](#dml---data-manipulation-language)
5. [Query Clauses](#query-clauses)
6. [Joins](#joins)
7. [Aggregate Functions](#aggregate-functions)
8. [Window Functions](#window-functions)
9. [Subqueries & CTEs](#subqueries--ctes)
10. [Advanced Features](#advanced-features)
11. [Performance & Optimization](#performance--optimization)
12. [PostgreSQL-Specific](#postgresql-specific)

---

## SQL Fundamentals

### Query Structure

```sql
SELECT <columns>
FROM <table>
[JOIN <other_table> ON <condition>]
[WHERE <filter_condition>]
[GROUP BY <grouping_columns>]
[HAVING <group_filter>]
[ORDER BY <sort_columns>]
[LIMIT <n> OFFSET <m>];
```

### Execution Order

Logical order SQL processes a query:

```
1. FROM & JOIN     -- Determine data sources
2. WHERE           -- Filter rows
3. GROUP BY        -- Group rows
4. HAVING          -- Filter groups
5. SELECT          -- Choose columns
6. DISTINCT        -- Remove duplicates
7. ORDER BY        -- Sort results
8. LIMIT/OFFSET    -- Paginate
```

---

## Data Types

### Numeric Types

```sql
-- Integer types
SMALLINT        -- 2 bytes, -32768 to 32767
INTEGER, INT    -- 4 bytes, -2147483648 to 2147483647
BIGINT          -- 8 bytes, -9223372036854775808 to 9223372036854775807

-- Arbitrary precision
NUMERIC(p, s)   -- p=precision, s=scale
DECIMAL(p, s)   -- Same as NUMERIC

-- Floating point
REAL            -- 4 bytes, 6 decimal digits precision
DOUBLE PRECISION -- 8 bytes, 15 decimal digits precision

-- Serial (auto-increment)
SMALLSERIAL     -- 2 bytes, auto-incrementing integer
SERIAL          -- 4 bytes, auto-incrementing integer
BIGSERIAL       -- 8 bytes, auto-incrementing integer
```

### String Types

```sql
CHAR(n)             -- Fixed-length, blank-padded
VARCHAR(n)          -- Variable-length with limit
TEXT                -- Variable unlimited length

-- Examples
name VARCHAR(100)   -- Max 100 characters
description TEXT    -- No limit
code CHAR(5)        -- Exactly 5 characters
```

### Date/Time Types

```sql
DATE                -- Date only: 2026-02-02
TIME                -- Time only: 14:30:00
TIMESTAMP           -- Date and time: 2026-02-02 14:30:00
TIMESTAMPTZ         -- Timestamp with timezone
INTERVAL            -- Time interval: '2 days', '3 hours'

-- Examples
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
expires_at TIMESTAMPTZ
duration INTERVAL
```

### Boolean

```sql
BOOLEAN             -- TRUE, FALSE, NULL

-- Examples
is_active BOOLEAN DEFAULT TRUE
has_orders BOOLEAN
```

### JSON Types

```sql
JSON                -- Stores JSON as text
JSONB               -- Binary JSON, faster queries

-- Examples
metadata JSONB
settings JSON
```

### Array Types

```sql
-- Array of any type
INTEGER[]           -- Array of integers
TEXT[]              -- Array of text
VARCHAR(50)[]       -- Array of varchar

-- Examples
tags TEXT[]
scores INTEGER[]
```

---

## DDL - Data Definition Language

### CREATE TABLE

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- With constraints
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) CHECK (total_amount >= 0),
    order_date DATE DEFAULT CURRENT_DATE,

    -- Foreign key
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    -- Check constraint
    CONSTRAINT valid_status CHECK (
        status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
    )
);
```

### ALTER TABLE

```sql
-- Add column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Drop column
ALTER TABLE users DROP COLUMN phone;

-- Modify column type
ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(200);

-- Set default
ALTER TABLE users ALTER COLUMN is_active SET DEFAULT TRUE;

-- Drop default
ALTER TABLE users ALTER COLUMN is_active DROP DEFAULT;

-- Add NOT NULL
ALTER TABLE users ALTER COLUMN email SET NOT NULL;

-- Drop NOT NULL
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;

-- Rename column
ALTER TABLE users RENAME COLUMN username TO user_name;

-- Add constraint
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);

-- Drop constraint
ALTER TABLE users DROP CONSTRAINT unique_email;
```

### DROP TABLE

```sql
-- Drop table
DROP TABLE users;

-- Drop if exists (no error if missing)
DROP TABLE IF EXISTS users;

-- Drop with cascade (also drop dependent objects)
DROP TABLE users CASCADE;
```

### CREATE INDEX

```sql
-- Basic index
CREATE INDEX idx_users_email ON users(email);

-- Unique index
CREATE UNIQUE INDEX idx_users_username ON users(username);

-- Composite index
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);

-- Partial index
CREATE INDEX idx_active_users ON users(email) WHERE is_active = TRUE;

-- Expression index
CREATE INDEX idx_lower_email ON users(LOWER(email));

-- Drop index
DROP INDEX idx_users_email;
```

---

## DML - Data Manipulation Language

### INSERT

```sql
-- Insert single row
INSERT INTO users (username, email)
VALUES ('john_doe', 'john@example.com');

-- Insert multiple rows
INSERT INTO users (username, email) VALUES
    ('jane_doe', 'jane@example.com'),
    ('bob_smith', 'bob@example.com');

-- Insert from SELECT
INSERT INTO archived_users
SELECT * FROM users WHERE created_at < '2020-01-01';

-- Insert and return inserted rows
INSERT INTO users (username, email)
VALUES ('new_user', 'new@example.com')
RETURNING user_id, username, created_at;

-- Insert with default values
INSERT INTO users (username, email)
VALUES ('user', 'user@example.com')
ON CONFLICT (email) DO NOTHING;
```

### UPDATE

```sql
-- Update single column
UPDATE users SET is_active = FALSE WHERE user_id = 123;

-- Update multiple columns
UPDATE users
SET
    email = 'newemail@example.com',
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 123;

-- Update with calculation
UPDATE products
SET price = price * 1.10
WHERE category = 'Electronics';

-- Update from another table
UPDATE orders o
SET status = 'cancelled'
FROM users u
WHERE o.user_id = u.user_id
  AND u.is_active = FALSE;

-- Update and return updated rows
UPDATE users
SET is_active = FALSE
WHERE last_login < '2023-01-01'
RETURNING user_id, username;
```

### DELETE

```sql
-- Delete specific rows
DELETE FROM users WHERE user_id = 123;

-- Delete with condition
DELETE FROM orders
WHERE status = 'cancelled'
  AND order_date < '2023-01-01';

-- Delete using subquery
DELETE FROM orders
WHERE user_id IN (
    SELECT user_id FROM users WHERE is_active = FALSE
);

-- Delete and return deleted rows
DELETE FROM users
WHERE created_at < '2020-01-01'
RETURNING user_id, username;

-- Delete all rows (dangerous!)
DELETE FROM users;

-- Faster alternative for deleting all
TRUNCATE TABLE users;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;
```

---

## Query Clauses

### SELECT

```sql
-- All columns
SELECT * FROM users;

-- Specific columns
SELECT user_id, username, email FROM users;

-- Calculated columns
SELECT
    product_name,
    price,
    price * 1.21 AS price_with_tax,
    price * 0.9 AS discounted_price
FROM products;

-- String concatenation
SELECT first_name || ' ' || last_name AS full_name FROM users;
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;

-- DISTINCT
SELECT DISTINCT country FROM users;
SELECT DISTINCT category, is_available FROM products;
```

### WHERE

```sql
-- Comparison operators
WHERE price = 100
WHERE price != 100  -- or <>
WHERE price > 100
WHERE price >= 100
WHERE price < 100
WHERE price <= 100

-- Logical operators
WHERE country = 'US' AND is_active = TRUE
WHERE country = 'US' OR country = 'GB'
WHERE NOT is_active
WHERE country = 'US' AND (age >= 18 OR has_parent_consent = TRUE)

-- IN
WHERE country IN ('US', 'GB', 'CA')
WHERE user_id NOT IN (1, 2, 3)

-- BETWEEN
WHERE price BETWEEN 50 AND 100
WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31'

-- LIKE (pattern matching)
WHERE email LIKE '%@gmail.com'      -- ends with
WHERE product_name LIKE 'Laptop%'   -- starts with
WHERE description LIKE '%sale%'     -- contains
WHERE code LIKE '_____'             -- exactly 5 characters
WHERE email ILIKE '%@GMAIL.COM'     -- case-insensitive

-- NULL handling
WHERE phone IS NULL
WHERE phone IS NOT NULL

-- Regular expressions (PostgreSQL)
WHERE email ~ '^[a-z]+@[a-z]+\.[a-z]{2,}$'
WHERE email !~ 'spam'
```

### ORDER BY

```sql
-- Single column
ORDER BY created_at
ORDER BY created_at ASC   -- Ascending (default)
ORDER BY created_at DESC  -- Descending

-- Multiple columns
ORDER BY country ASC, created_at DESC

-- By expression
ORDER BY LOWER(username)
ORDER BY price * quantity DESC

-- NULL positioning (PostgreSQL)
ORDER BY phone NULLS LAST
ORDER BY phone NULLS FIRST

-- By column position (not recommended)
SELECT username, email FROM users ORDER BY 1;  -- Orders by first column
```

### LIMIT & OFFSET

```sql
-- Top N rows
SELECT * FROM products ORDER BY price DESC LIMIT 10;

-- Pagination
-- Page 1
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 0;

-- Page 2
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 10;

-- Page N (formula: OFFSET = (page - 1) * page_size)
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 20;

-- Alternative syntax (PostgreSQL)
SELECT * FROM users ORDER BY user_id FETCH FIRST 10 ROWS ONLY;
```

---

## Joins

### INNER JOIN

```sql
-- Basic inner join
SELECT u.username, o.order_id, o.total_amount
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id;

-- Multiple joins
SELECT
    u.username,
    o.order_id,
    p.product_name,
    oi.quantity
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id;

-- Join with WHERE
SELECT u.username, o.order_id
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
WHERE o.status = 'delivered';
```

### LEFT JOIN (LEFT OUTER JOIN)

```sql
-- All users, with orders if they exist
SELECT u.username, o.order_id
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;

-- Find users without orders
SELECT u.username
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_id IS NULL;

-- Count per user (including 0)
SELECT
    u.username,
    COUNT(o.order_id) AS order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.username;
```

### RIGHT JOIN (RIGHT OUTER JOIN)

```sql
-- All orders, with users if they exist
SELECT u.username, o.order_id
FROM users u
RIGHT JOIN orders o ON u.user_id = o.user_id;

-- Find orphaned orders
SELECT o.order_id
FROM users u
RIGHT JOIN orders o ON u.user_id = o.user_id
WHERE u.user_id IS NULL;
```

### FULL OUTER JOIN

```sql
-- All users and all orders
SELECT
    COALESCE(u.user_id, o.user_id) AS user_id,
    u.username,
    o.order_id
FROM users u
FULL OUTER JOIN orders o ON u.user_id = o.user_id;

-- Find mismatched records
SELECT *
FROM users u
FULL OUTER JOIN orders o ON u.user_id = o.user_id
WHERE u.user_id IS NULL OR o.user_id IS NULL;
```

### CROSS JOIN

```sql
-- Cartesian product (every combination)
SELECT u.username, p.product_name
FROM users u
CROSS JOIN products p;

-- Generate combinations
SELECT
    d.day_name,
    s.shift_name
FROM days d
CROSS JOIN shifts s;
```

### SELF JOIN

```sql
-- Find employees and their managers
SELECT
    e.name AS employee,
    m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;

-- Find users from same country
SELECT
    u1.username AS user1,
    u2.username AS user2,
    u1.country
FROM users u1
INNER JOIN users u2 ON u1.country = u2.country
WHERE u1.user_id < u2.user_id;  -- Avoid duplicates
```

---

## Aggregate Functions

### Basic Aggregates

```sql
-- COUNT
SELECT COUNT(*) FROM users;                    -- All rows
SELECT COUNT(phone) FROM users;                -- Non-NULL values
SELECT COUNT(DISTINCT country) FROM users;     -- Unique values

-- SUM
SELECT SUM(total_amount) FROM orders;
SELECT SUM(price * quantity) FROM order_items;

-- AVG
SELECT AVG(price) FROM products;
SELECT AVG(loyalty_points) FROM users WHERE is_active = TRUE;

-- MIN / MAX
SELECT MIN(price), MAX(price) FROM products;
SELECT MIN(order_date), MAX(order_date) FROM orders;

-- Multiple aggregates
SELECT
    COUNT(*) AS total_orders,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS avg_order_value,
    MIN(total_amount) AS min_order,
    MAX(total_amount) AS max_order
FROM orders;
```

### GROUP BY

```sql
-- Group by single column
SELECT
    country,
    COUNT(*) AS user_count
FROM users
GROUP BY country
ORDER BY user_count DESC;

-- Group by multiple columns
SELECT
    country,
    is_active,
    COUNT(*) AS count
FROM users
GROUP BY country, is_active
ORDER BY country, is_active;

-- Group by expression
SELECT
    EXTRACT(YEAR FROM order_date) AS year,
    EXTRACT(MONTH FROM order_date) AS month,
    SUM(total_amount) AS monthly_revenue
FROM orders
GROUP BY EXTRACT(YEAR FROM order_date), EXTRACT(MONTH FROM order_date)
ORDER BY year, month;

-- GROUP BY with JOIN
SELECT
    u.username,
    COUNT(o.order_id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.username;
```

### HAVING

```sql
-- Filter groups
SELECT
    country,
    COUNT(*) AS user_count
FROM users
GROUP BY country
HAVING COUNT(*) > 100;

-- Multiple conditions
SELECT
    category,
    AVG(price) AS avg_price
FROM products
GROUP BY category
HAVING AVG(price) > 50 AND COUNT(*) >= 10;

-- HAVING with aggregate functions
SELECT
    user_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY user_id
HAVING SUM(total_amount) > 1000
ORDER BY total_spent DESC;

-- WHERE vs HAVING
SELECT
    country,
    COUNT(*) AS active_user_count
FROM users
WHERE is_active = TRUE          -- Filter rows before grouping
GROUP BY country
HAVING COUNT(*) > 50           -- Filter groups after aggregation
ORDER BY active_user_count DESC;
```

### String Aggregation

```sql
-- STRING_AGG (PostgreSQL)
SELECT
    user_id,
    STRING_AGG(product_name, ', ') AS products_ordered
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY user_id;

-- ARRAY_AGG (PostgreSQL)
SELECT
    category,
    ARRAY_AGG(product_name ORDER BY price DESC) AS products
FROM products
GROUP BY category;
```

---

## Window Functions

### Ranking Functions

```sql
-- ROW_NUMBER - unique sequential number
SELECT
    product_name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) AS row_num
FROM products;

-- RANK - with gaps after ties
SELECT
    product_name,
    price,
    RANK() OVER (ORDER BY price DESC) AS rank
FROM products;

-- DENSE_RANK - without gaps
SELECT
    product_name,
    price,
    DENSE_RANK() OVER (ORDER BY price DESC) AS dense_rank
FROM products;

-- NTILE - divide into N groups
SELECT
    product_name,
    price,
    NTILE(4) OVER (ORDER BY price) AS quartile
FROM products;

-- Ranking within partitions
SELECT
    category,
    product_name,
    price,
    RANK() OVER (PARTITION BY category ORDER BY price DESC) AS rank_in_category
FROM products;
```

### Analytical Functions

```sql
-- LAG - previous row value
SELECT
    order_date,
    total_amount,
    LAG(total_amount) OVER (ORDER BY order_date) AS prev_order,
    total_amount - LAG(total_amount) OVER (ORDER BY order_date) AS change
FROM orders;

-- LEAD - next row value
SELECT
    order_date,
    total_amount,
    LEAD(total_amount) OVER (ORDER BY order_date) AS next_order
FROM orders;

-- FIRST_VALUE - first in window
SELECT
    product_name,
    category,
    price,
    FIRST_VALUE(product_name) OVER (
        PARTITION BY category
        ORDER BY price DESC
    ) AS most_expensive_in_category
FROM products;

-- LAST_VALUE - last in window (need full frame)
SELECT
    product_name,
    category,
    price,
    LAST_VALUE(product_name) OVER (
        PARTITION BY category
        ORDER BY price DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS cheapest_in_category
FROM products;
```

### Aggregate Window Functions

```sql
-- Running total
SELECT
    order_date,
    total_amount,
    SUM(total_amount) OVER (ORDER BY order_date) AS running_total
FROM orders;

-- Moving average
SELECT
    order_date,
    total_amount,
    AVG(total_amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM orders;

-- Cumulative percentage
SELECT
    product_name,
    sales,
    SUM(sales) OVER (ORDER BY sales DESC) AS running_total,
    ROUND(
        100.0 * SUM(sales) OVER (ORDER BY sales DESC) / SUM(sales) OVER (),
        2
    ) AS cumulative_pct
FROM product_sales;

-- Average per group (without GROUP BY)
SELECT
    product_name,
    category,
    price,
    AVG(price) OVER (PARTITION BY category) AS avg_category_price,
    price - AVG(price) OVER (PARTITION BY category) AS diff_from_avg
FROM products;
```

---

## Subqueries & CTEs

### Subqueries in WHERE

```sql
-- Scalar subquery (returns single value)
SELECT *
FROM products
WHERE price > (SELECT AVG(price) FROM products);

-- IN subquery
SELECT *
FROM users
WHERE user_id IN (
    SELECT DISTINCT user_id FROM orders WHERE total_amount > 1000
);

-- NOT IN (be careful with NULLs!)
SELECT *
FROM products
WHERE product_id NOT IN (
    SELECT product_id FROM order_items
);

-- EXISTS (often faster than IN)
SELECT *
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.user_id AND o.status = 'delivered'
);

-- NOT EXISTS
SELECT *
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM order_items oi
    WHERE oi.product_id = p.product_id
);
```

### Subqueries in SELECT

```sql
-- Scalar subquery in SELECT
SELECT
    u.username,
    u.email,
    (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) AS order_count
FROM users u;

-- Multiple scalar subqueries
SELECT
    product_id,
    product_name,
    price,
    (SELECT AVG(price) FROM products) AS avg_price,
    price - (SELECT AVG(price) FROM products) AS diff
FROM products;
```

### Subqueries in FROM

```sql
-- Derived table
SELECT
    category,
    AVG(product_count) AS avg_products_per_user
FROM (
    SELECT
        p.category,
        u.user_id,
        COUNT(DISTINCT oi.product_id) AS product_count
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category, u.user_id
) user_category_purchases
GROUP BY category;
```

### CTEs (Common Table Expressions)

```sql
-- Basic CTE
WITH high_value_orders AS (
    SELECT * FROM orders WHERE total_amount > 500
)
SELECT
    u.username,
    hvo.order_id,
    hvo.total_amount
FROM high_value_orders hvo
JOIN users u ON hvo.user_id = u.user_id;

-- Multiple CTEs
WITH
active_users AS (
    SELECT * FROM users WHERE is_active = TRUE
),
recent_orders AS (
    SELECT * FROM orders WHERE order_date > CURRENT_DATE - INTERVAL '30 days'
)
SELECT
    au.username,
    COUNT(ro.order_id) AS recent_order_count
FROM active_users au
LEFT JOIN recent_orders ro ON au.user_id = ro.user_id
GROUP BY au.user_id, au.username;

-- Recursive CTE (hierarchy)
WITH RECURSIVE org_chart AS (
    -- Base case: top-level employees
    SELECT employee_id, name, manager_id, 1 AS level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: employees with managers
    SELECT e.employee_id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    INNER JOIN org_chart oc ON e.manager_id = oc.employee_id
)
SELECT * FROM org_chart ORDER BY level, name;
```

---

## Advanced Features

### CASE Expressions

```sql
-- Simple CASE
SELECT
    product_name,
    price,
    CASE
        WHEN price < 50 THEN 'Budget'
        WHEN price BETWEEN 50 AND 200 THEN 'Standard'
        ELSE 'Premium'
    END AS price_tier
FROM products;

-- CASE in aggregation
SELECT
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) AS delivered,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) AS cancelled
FROM orders;

-- CASE in ORDER BY
SELECT * FROM orders
ORDER BY
    CASE status
        WHEN 'pending' THEN 1
        WHEN 'processing' THEN 2
        WHEN 'shipped' THEN 3
        ELSE 4
    END;
```

### COALESCE & NULLIF

```sql
-- COALESCE - return first non-NULL
SELECT
    product_name,
    COALESCE(tracking_number, 'N/A') AS tracking,
    COALESCE(phone, email, 'No contact') AS contact
FROM orders;

-- NULLIF - return NULL if equal
SELECT
    product_name,
    price,
    NULLIF(discount, 0) AS discount  -- NULL when discount is 0
FROM products;
```

### UNION, INTERSECT, EXCEPT

```sql
-- UNION - combine results (remove duplicates)
SELECT user_id FROM orders WHERE status = 'delivered'
UNION
SELECT user_id FROM user_activity WHERE activity_type = 'purchase';

-- UNION ALL - include duplicates (faster)
SELECT user_id FROM orders
UNION ALL
SELECT user_id FROM user_activity;

-- INTERSECT - common rows
SELECT user_id FROM orders
INTERSECT
SELECT user_id FROM user_activity;

-- EXCEPT - in first but not second
SELECT user_id FROM users
EXCEPT
SELECT user_id FROM orders;
```

### Transactions

```sql
-- Basic transaction
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
COMMIT;

-- Rollback on error
BEGIN;
    -- operations
    IF error_condition THEN
        ROLLBACK;
    ELSE
        COMMIT;
    END IF;

-- Savepoints
BEGIN;
    INSERT INTO users (username) VALUES ('user1');
    SAVEPOINT sp1;
    INSERT INTO users (username) VALUES ('user2');
    ROLLBACK TO sp1;  -- Undo user2, keep user1
COMMIT;
```

---

## Performance & Optimization

See [assets/cheatsheets/optimization.md](../assets/cheatsheets/optimization.md) for complete optimization guide.

### Key Concepts

```sql
-- EXPLAIN - see query plan
EXPLAIN SELECT * FROM users WHERE country = 'US';

-- EXPLAIN ANALYZE - see actual execution
EXPLAIN ANALYZE SELECT * FROM users WHERE country = 'US';

-- Create indexes
CREATE INDEX idx_users_country ON users(country);
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);

-- Update statistics
ANALYZE users;
ANALYZE;  -- All tables

-- Vacuum
VACUUM ANALYZE users;
```

---

## PostgreSQL-Specific

### Array Operations

```sql
-- Array literal
SELECT ARRAY[1, 2, 3];
SELECT '{1, 2, 3}'::INTEGER[];

-- Array operations
SELECT tags @> ARRAY['sql']  -- Contains
SELECT tags && ARRAY['sql', 'python']  -- Overlaps
SELECT array_length(tags, 1)  -- Length
SELECT unnest(tags)  -- Expand to rows
```

### JSON/JSONB

```sql
-- Query JSON
SELECT metadata->>'name' AS name FROM products;
SELECT metadata->'attributes'->>'color' AS color FROM products;

-- JSON array element
SELECT metadata->'tags'->0 AS first_tag FROM products;

-- JSON path (PostgreSQL 12+)
SELECT metadata @@ '$.attributes[*] ? (@.color == "red")' FROM products;

-- JSONB operators
SELECT metadata @> '{"category": "electronics"}' FROM products;  -- Contains
```

### Full-Text Search

```sql
-- Create tsvector column
ALTER TABLE products ADD COLUMN search_vector tsvector;

-- Update search vector
UPDATE products
SET search_vector = to_tsvector('english', product_name || ' ' || description);

-- Create index
CREATE INDEX idx_search_vector ON products USING GIN(search_vector);

-- Search
SELECT * FROM products
WHERE search_vector @@ to_tsquery('english', 'laptop & wireless');

-- Ranking
SELECT
    product_name,
    ts_rank(search_vector, to_tsquery('laptop')) AS rank
FROM products
WHERE search_vector @@ to_tsquery('laptop')
ORDER BY rank DESC;
```

---

## Quick Reference Tables

### Comparison Operators

| Operator | Description |
|----------|-------------|
| `=` | Equal |
| `!=` or `<>` | Not equal |
| `>` | Greater than |
| `>=` | Greater than or equal |
| `<` | Less than |
| `<=` | Less than or equal |
| `BETWEEN` | Between range (inclusive) |
| `IN` | In list of values |
| `LIKE` | Pattern match |
| `ILIKE` | Case-insensitive pattern match |
| `IS NULL` | Is NULL |
| `IS NOT NULL` | Is not NULL |

### String Functions

| Function | Description |
|----------|-------------|
| `CONCAT(str1, str2, ...)` | Concatenate strings |
| `LOWER(str)` | Convert to lowercase |
| `UPPER(str)` | Convert to uppercase |
| `TRIM(str)` | Remove leading/trailing spaces |
| `LENGTH(str)` | String length |
| `SUBSTRING(str, start, length)` | Extract substring |
| `REPLACE(str, from, to)` | Replace substring |

### Date Functions

| Function | Description |
|----------|-------------|
| `CURRENT_DATE` | Today's date |
| `CURRENT_TIMESTAMP` | Current date and time |
| `NOW()` | Current date and time |
| `EXTRACT(part FROM date)` | Extract part (YEAR, MONTH, DAY) |
| `DATE_TRUNC(precision, date)` | Truncate to precision |
| `AGE(date1, date2)` | Interval between dates |

---

This guide covers the most common SQL patterns used in data engineering. For more specific topics, see:
- [SQL Basics Cheatsheet](../assets/cheatsheets/sql-basics.md)
- [Window Functions Cheatsheet](../assets/cheatsheets/window-functions.md)
- [Optimization Cheatsheet](../assets/cheatsheets/optimization.md)
