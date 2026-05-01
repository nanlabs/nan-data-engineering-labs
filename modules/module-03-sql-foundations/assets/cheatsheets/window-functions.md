# Window Functions Cheatsheet

## Core Concept

**Window functions** perform calculations across a set of rows while **keeping all rows** (unlike GROUP BY which collapses rows).

```sql
<function>(<arguments>) OVER (
    [PARTITION BY <columns>]
    [ORDER BY <columns>]
    [<frame_clause>]
)
```

---

## 1. Ranking Functions

### ROW_NUMBER()
Assigns a unique sequential integer to each row (no ties).

```sql
-- Rank products by price
SELECT
    product_name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) AS row_num
FROM products;

-- Rank within categories
SELECT
    product_name,
    category,
    price,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS rank_in_category
FROM products;
```

**Use Case**: Pagination, unique numbering even with ties

---

### RANK()
Assigns rank with gaps after ties (1, 2, 2, 4...).

```sql
SELECT
    product_name,
    price,
    RANK() OVER (ORDER BY price DESC) AS rank
FROM products;
```

**Use Case**: Olympic-style ranking (gold, silver, silver, bronze skips to 4th)

---

### DENSE_RANK()
Assigns rank without gaps (1, 2, 2, 3...).

```sql
SELECT
    product_name,
    price,
    DENSE_RANK() OVER (ORDER BY price DESC) AS dense_rank
FROM products;
```

**Use Case**: Consecutive ranking (gold, silver, silver, bronze is 3rd)

---

### Comparison

| Price | ROW_NUMBER() | RANK() | DENSE_RANK() |
|-------|--------------|--------|--------------|
| $1000 | 1 | 1 | 1 |
| $500  | 2 | 2 | 2 |
| $500  | 3 | 2 | 2 |
| $100  | 4 | 4 | 3 |

---

### NTILE(n)
Divides rows into n groups.

```sql
-- Divide products into 4 price quartiles
SELECT
    product_name,
    price,
    NTILE(4) OVER (ORDER BY price) AS price_quartile
FROM products;

-- Result: Quartile 1 = cheapest 25%, Quartile 4 = most expensive 25%
```

**Use Case**: Percentiles, A/B testing groups, stratification

---

## 2. Analytical Functions

### LAG() - Previous Row Value
Access value from previous row.

```sql
LAG(<column>, <offset>, <default>) OVER ([PARTITION BY ...] ORDER BY ...)
```

```sql
-- Compare each order with previous one
SELECT
    order_date,
    total_amount,
    LAG(total_amount) OVER (ORDER BY order_date) AS prev_order,
    total_amount - LAG(total_amount) OVER (ORDER BY order_date) AS change
FROM orders;

-- Compare with order 2 rows back
SELECT
    order_date,
    total_amount,
    LAG(total_amount, 2) OVER (ORDER BY order_date) AS two_orders_ago
FROM orders;

-- With default for first row
SELECT
    order_date,
    total_amount,
    LAG(total_amount, 1, 0) OVER (ORDER BY order_date) AS prev_order
FROM orders;
```

**Use Case**: Month-over-month growth, compare with previous period

---

### LEAD() - Next Row Value
Access value from next row.

```sql
SELECT
    order_date,
    total_amount,
    LEAD(total_amount) OVER (ORDER BY order_date) AS next_order,
    LEAD(total_amount) - total_amount AS next_change
FROM orders;
```

**Use Case**: Predict trends, look-ahead comparisons

---

### FIRST_VALUE() - First Row in Window
Get first value in window.

```sql
SELECT
    product_name,
    category,
    price,
    FIRST_VALUE(product_name) OVER (
        PARTITION BY category
        ORDER BY price DESC
    ) AS most_expensive_in_category
FROM products;
```

**Use Case**: Compare to leader, benchmark against best

---

### LAST_VALUE() - Last Row in Window
Get last value in window.

```sql
-- ⚠️ Need proper frame to get actual last value
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

**Use Case**: Compare to minimum, baseline comparison

---

## 3. Aggregate Functions as Window Functions

Any aggregate (SUM, AVG, COUNT, MIN, MAX) can be used as window function.

### Running Total
```sql
SELECT
    order_date,
    total_amount,
    SUM(total_amount) OVER (ORDER BY order_date) AS running_total
FROM orders;
```

### Average per Group
```sql
SELECT
    product_name,
    category,
    price,
    AVG(price) OVER (PARTITION BY category) AS avg_category_price,
    price - AVG(price) OVER (PARTITION BY category) AS diff_from_avg
FROM products;
```

### Percentage of Total
```sql
SELECT
    product_name,
    price,
    ROUND(
        100.0 * price / SUM(price) OVER (),
        2
    ) AS pct_of_total
FROM products;
```

### Count
```sql
SELECT
    product_name,
    category,
    COUNT(*) OVER (PARTITION BY category) AS products_in_category
FROM products;
```

---

## 4. PARTITION BY

Divides result set into partitions. Window function applies separately to each partition.

```sql
-- Global ranking (no partition)
SELECT
    product_name,
    category,
    price,
    RANK() OVER (ORDER BY price DESC) AS global_rank
FROM products;

-- Ranking per category (with partition)
SELECT
    product_name,
    category,
    price,
    RANK() OVER (PARTITION BY category ORDER BY price DESC) AS category_rank
FROM products;
```

**Think of it as**: GROUP BY but keeping all rows

---

## 5. Frame Clauses

Define which rows are included in the window for each calculation.

### Frame Types

**ROWS**: Physical row offset
```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

**RANGE**: Logical range based on value
```sql
RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
```

### Frame Boundaries

| Boundary | Meaning |
|----------|---------|
| `UNBOUNDED PRECEDING` | Start of partition |
| `n PRECEDING` | n rows before current |
| `CURRENT ROW` | Current row |
| `n FOLLOWING` | n rows after current |
| `UNBOUNDED FOLLOWING` | End of partition |

### Common Frames

```sql
-- Running total (default for ORDER BY)
SUM(amount) OVER (
    ORDER BY date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)

-- 3-row moving average (current + 2 before)
AVG(amount) OVER (
    ORDER BY date
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
)

-- 5-row centered window (2 before + current + 2 after)
AVG(amount) OVER (
    ORDER BY date
    ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
)

-- All rows in partition
SUM(amount) OVER (
    PARTITION BY category
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
```

---

## 6. Common Patterns

### Top N per Group
```sql
-- Top 3 products per category by price
SELECT *
FROM (
    SELECT
        product_name,
        category,
        price,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS rn
    FROM products
) ranked
WHERE rn <= 3;
```

### Moving Average (7-day)
```sql
SELECT
    date,
    sales,
    AVG(sales) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM daily_sales;
```

### Year-over-Year Comparison
```sql
SELECT
    order_date,
    SUM(total_amount) AS daily_total,
    LAG(SUM(total_amount), 365) OVER (ORDER BY order_date) AS same_day_last_year,
    SUM(total_amount) - LAG(SUM(total_amount), 365) OVER (ORDER BY order_date) AS yoy_change
FROM orders
GROUP BY order_date;
```

### Cumulative Percentage
```sql
SELECT
    product_name,
    sales,
    SUM(sales) OVER (ORDER BY sales DESC) AS running_total,
    ROUND(
        100.0 * SUM(sales) OVER (ORDER BY sales DESC) / SUM(sales) OVER (),
        2
    ) AS cumulative_pct
FROM product_sales;
```

### Gap and Island Problem (Find Consecutive Sequences)
```sql
-- Find sequences of consecutive dates
SELECT
    order_date,
    order_date - INTERVAL '1 day' * ROW_NUMBER() OVER (ORDER BY order_date) AS group_id
FROM orders
GROUP BY order_date;
```

### Ranking with Filtering
```sql
-- Best seller per category, but only categories with >10 products
SELECT *
FROM (
    SELECT
        product_name,
        category,
        sales,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC) AS rank,
        COUNT(*) OVER (PARTITION BY category) AS category_size
    FROM products
) ranked
WHERE rank = 1
  AND category_size > 10;
```

---

## 7. Performance Tips

### Reuse Window Definitions
```sql
-- Instead of repeating OVER clause:
SELECT
    product_name,
    price,
    AVG(price) OVER (PARTITION BY category ORDER BY price) AS avg,
    MIN(price) OVER (PARTITION BY category ORDER BY price) AS min
FROM products;

-- Use WINDOW clause:
SELECT
    product_name,
    price,
    AVG(price) OVER w AS avg,
    MIN(price) OVER w AS min
FROM products
WINDOW w AS (PARTITION BY category ORDER BY price);
```

### Index for ORDER BY
Create index on columns used in ORDER BY within OVER clause.

```sql
-- If you frequently use:
SELECT ... OVER (PARTITION BY category ORDER BY price DESC)

-- Create index:
CREATE INDEX idx_products_category_price ON products(category, price DESC);
```

---

## 8. Common Mistakes

### ❌ LAST_VALUE without proper frame
```sql
-- WRONG: Gets current row, not actual last
SELECT LAST_VALUE(price) OVER (ORDER BY price);

-- CORRECT: Specify full frame
SELECT LAST_VALUE(price) OVER (
    ORDER BY price
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
);
```

### ❌ Using window function in WHERE
```sql
-- WRONG: Can't use window function in WHERE
SELECT *
FROM products
WHERE ROW_NUMBER() OVER (ORDER BY price) <= 10;

-- CORRECT: Use subquery or CTE
SELECT *
FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY price) AS rn
    FROM products
) ranked
WHERE rn <= 10;
```

### ❌ Forgetting ORDER BY in ranking functions
```sql
-- WRONG: Order is undefined
SELECT ROW_NUMBER() OVER () FROM products;

-- CORRECT: Specify order
SELECT ROW_NUMBER() OVER (ORDER BY price DESC) FROM products;
```

---

## Quick Reference

| Function | Purpose | Key Behavior |
|----------|---------|--------------|
| `ROW_NUMBER()` | Unique sequential numbering | No ties |
| `RANK()` | Ranking with gaps | 1,2,2,4 |
| `DENSE_RANK()` | Ranking without gaps | 1,2,2,3 |
| `NTILE(n)` | Divide into n groups | Percentiles |
| `LAG()` | Previous row | Look back |
| `LEAD()` | Next row | Look ahead |
| `FIRST_VALUE()` | First in window | Min/max comparison |
| `LAST_VALUE()` | Last in window | Need full frame |
| `SUM() OVER` | Running total | Cumulative |
| `AVG() OVER` | Moving average | Smoothing |

## When to Use

- **GROUP BY**: When you want to collapse rows into summary
- **Window Functions**: When you want to keep all rows but add calculated columns

```sql
-- GROUP BY: 3 rows (one per category)
SELECT category, AVG(price)
FROM products
GROUP BY category;

-- Window Function: All rows kept
SELECT product_name, category, price,
       AVG(price) OVER (PARTITION BY category)
FROM products;
```
