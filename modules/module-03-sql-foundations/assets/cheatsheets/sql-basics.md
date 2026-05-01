# SQL Basics Cheatsheet

## SELECT - Basic Query Structure

```sql
SELECT column1, column2, ...
FROM table_name
WHERE condition
ORDER BY column1 [ASC|DESC]
LIMIT n OFFSET m;
```

---

## 1. SELECT & Projection

### All Columns
```sql
SELECT * FROM users;
```

### Specific Columns
```sql
SELECT first_name, last_name, email FROM users;
```

### Column Aliases
```sql
SELECT
    first_name AS nombre,
    last_name AS apellido,
    price * 0.9 AS discounted_price
FROM products;
```

### Calculated Columns
```sql
SELECT
    product_name,
    price,
    price * 1.21 AS price_with_tax,
    ROUND(price * 1.21, 2) AS rounded_price
FROM products;
```

---

## 2. WHERE - Filtering

### Comparison Operators
```sql
-- Equal, not equal
WHERE price = 100
WHERE status != 'cancelled'
WHERE status <> 'cancelled'  -- Same as !=

-- Greater than, less than
WHERE price > 100
WHERE price >= 100
WHERE loyalty_points < 50
WHERE loyalty_points <= 50
```

### Logical Operators
```sql
-- AND (all conditions must be true)
WHERE country = 'US' AND is_active = TRUE

-- OR (at least one condition must be true)
WHERE country = 'US' OR country = 'GB'

-- NOT (negate condition)
WHERE NOT country = 'US'
WHERE country != 'US'  -- Same as above
```

### NULL Handling
```sql
-- Check for NULL
WHERE tracking_number IS NULL
WHERE tracking_number IS NOT NULL

-- ⚠️ WRONG: WHERE tracking_number = NULL  -- This doesn't work!
```

### IN Operator
```sql
-- Multiple values
WHERE country IN ('US', 'GB', 'CA')

-- Equivalent to:
WHERE country = 'US' OR country = 'GB' OR country = 'CA'

-- NOT IN
WHERE country NOT IN ('US', 'GB', 'CA')
```

### BETWEEN Operator
```sql
-- Range (inclusive)
WHERE price BETWEEN 20 AND 100

-- Equivalent to:
WHERE price >= 20 AND price <= 100

-- Dates
WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31'
```

### LIKE Pattern Matching
```sql
-- Wildcards:
-- % = any sequence of characters (0 or more)
-- _ = exactly one character

-- Starts with
WHERE product_name LIKE 'Laptop%'

-- Ends with
WHERE email LIKE '%@gmail.com'

-- Contains
WHERE product_name LIKE '%Book%'

-- Exactly 5 characters
WHERE code LIKE '_____'

-- Case-insensitive (PostgreSQL)
WHERE email ILIKE '%@GMAIL.COM'
```

---

## 3. ORDER BY - Sorting

### Basic Sorting
```sql
-- Ascending (default)
ORDER BY price
ORDER BY price ASC

-- Descending
ORDER BY price DESC
```

### Multiple Columns
```sql
-- Sort by country (ascending), then by loyalty_points (descending)
ORDER BY country ASC, loyalty_points DESC
```

### NULL Ordering (PostgreSQL)
```sql
-- NULLs at end
ORDER BY tracking_number NULLS LAST

-- NULLs at beginning
ORDER BY tracking_number NULLS FIRST
```

---

## 4. LIMIT & OFFSET - Pagination

### Basic Limit
```sql
-- First 10 rows
SELECT * FROM users LIMIT 10;
```

### Pagination
```sql
-- Page 1 (rows 1-10)
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 0;

-- Page 2 (rows 11-20)
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 10;

-- Page 3 (rows 21-30)
SELECT * FROM users ORDER BY user_id LIMIT 10 OFFSET 20;

-- Formula: OFFSET = (page_number - 1) * page_size
```

---

## 5. Aggregate Functions

```sql
-- Count rows
SELECT COUNT(*) FROM orders;
SELECT COUNT(DISTINCT user_id) FROM orders;  -- Unique users

-- Sum
SELECT SUM(total_amount) FROM orders;

-- Average
SELECT AVG(price) FROM products;

-- Min/Max
SELECT MIN(price), MAX(price) FROM products;

-- Multiple aggregates
SELECT
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    MIN(total_amount) AS min_order,
    MAX(total_amount) AS max_order
FROM orders;
```

---

## 6. GROUP BY - Grouping

### Basic GROUP BY
```sql
-- Orders per user
SELECT
    user_id,
    COUNT(*) AS num_orders
FROM orders
GROUP BY user_id;
```

### Multiple Grouping Columns
```sql
-- Orders per user per status
SELECT
    user_id,
    status,
    COUNT(*) AS num_orders,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY user_id, status
ORDER BY user_id, status;
```

### HAVING - Filter Groups
```sql
-- Users with more than 5 orders
SELECT
    user_id,
    COUNT(*) AS num_orders
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5;

-- Difference between WHERE and HAVING:
-- WHERE: Filters rows BEFORE grouping
-- HAVING: Filters groups AFTER aggregation

-- Example combining both:
SELECT
    user_id,
    COUNT(*) AS num_orders
FROM orders
WHERE status = 'delivered'  -- Filter rows first
GROUP BY user_id
HAVING COUNT(*) > 3;  -- Then filter groups
```

---

## 7. JOINS

### INNER JOIN
```sql
-- Only matching rows
SELECT
    o.order_id,
    u.first_name,
    u.last_name
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id;
```

### LEFT JOIN
```sql
-- All from left table, matching from right
SELECT
    u.first_name,
    o.order_id
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;

-- Find users without orders
SELECT u.*
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_id IS NULL;
```

### Multiple JOINs
```sql
-- 3+ tables
SELECT
    o.order_id,
    u.first_name,
    p.product_name,
    oi.quantity
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id;
```

---

## 8. Subqueries

### Subquery in WHERE
```sql
-- Products more expensive than average
SELECT *
FROM products
WHERE price > (SELECT AVG(price) FROM products);
```

### Subquery with IN
```sql
-- Users who have placed orders
SELECT *
FROM users
WHERE user_id IN (SELECT DISTINCT user_id FROM orders);
```

### Subquery in SELECT
```sql
-- Compare each product to average
SELECT
    product_name,
    price,
    (SELECT AVG(price) FROM products) AS avg_price,
    price - (SELECT AVG(price) FROM products) AS diff
FROM products;
```

---

## 9. CTEs (WITH Clause)

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
    SELECT
        user_id,
        COUNT(*) AS num_orders
    FROM orders
    GROUP BY user_id
),
top_users AS (
    SELECT * FROM user_stats WHERE num_orders > 5
)
SELECT
    u.*,
    tu.num_orders
FROM users u
INNER JOIN top_users tu ON u.user_id = tu.user_id;
```

---

## 10. Common Functions

### String Functions
```sql
-- Concatenation
SELECT first_name || ' ' || last_name AS full_name FROM users;
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;

-- Case conversion
SELECT UPPER(email), LOWER(product_name) FROM users, products;

-- Substring
SELECT SUBSTRING(email FROM 1 FOR 5) FROM users;

-- Trim
SELECT TRIM(product_name) FROM products;

-- Length
SELECT LENGTH(product_name) FROM products;
```

### Date Functions
```sql
-- Current date/time
SELECT CURRENT_DATE, CURRENT_TIMESTAMP;

-- Extract parts
SELECT EXTRACT(YEAR FROM order_date) AS year FROM orders;
SELECT EXTRACT(MONTH FROM order_date) AS month FROM orders;

-- Date arithmetic
SELECT order_date + INTERVAL '7 days' AS delivery_estimate FROM orders;

-- Date formatting
SELECT TO_CHAR(order_date, 'YYYY-MM-DD') FROM orders;
```

### Math Functions
```sql
-- Rounding
SELECT ROUND(price, 2) FROM products;
SELECT CEIL(price) FROM products;   -- Round up
SELECT FLOOR(price) FROM products;  -- Round down

-- Absolute value
SELECT ABS(-10);

-- Power
SELECT POWER(2, 3);  -- 2^3 = 8
```

### NULL Functions
```sql
-- COALESCE - return first non-null
SELECT COALESCE(tracking_number, 'N/A') FROM orders;

-- NULLIF - return NULL if equal
SELECT NULLIF(quantity, 0) FROM order_items;  -- NULL when 0
```

---

## 11. CASE Expressions

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
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) AS delivered_orders,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending_orders
FROM orders;
```

---

## 12. DISTINCT

```sql
-- Unique values
SELECT DISTINCT country FROM users;

-- Count unique
SELECT COUNT(DISTINCT user_id) FROM orders;

-- DISTINCT on multiple columns
SELECT DISTINCT category, is_available FROM products;
```

---

## Quick Reference

| Operation | Syntax |
|-----------|--------|
| **Select all** | `SELECT * FROM table` |
| **Filter** | `WHERE condition` |
| **Sort** | `ORDER BY column [DESC]` |
| **Limit** | `LIMIT n` |
| **Paginate** | `LIMIT n OFFSET m` |
| **Group** | `GROUP BY column` |
| **Filter groups** | `HAVING condition` |
| **Join** | `INNER JOIN table2 ON condition` |
| **Left join** | `LEFT JOIN table2 ON condition` |
| **Subquery** | `WHERE col IN (SELECT ...)` |
| **CTE** | `WITH name AS (SELECT ...)` |

## Execution Order

```
FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

**Remember**: SQL keywords are case-insensitive, but convention is UPPERCASE for keywords.
