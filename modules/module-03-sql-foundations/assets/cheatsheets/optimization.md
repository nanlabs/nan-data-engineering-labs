# SQL Query Optimization Cheatsheet

## 1. EXPLAIN - Query Plan Analysis

### Basic EXPLAIN
```sql
EXPLAIN SELECT * FROM users WHERE country = 'US';
```

**Output includes**:
- Scan method (Seq Scan, Index Scan, etc.)
- Cost estimates (startup..total)
- Row estimates

### EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE country = 'US';
```

**Difference**: Actually executes query and shows:
- Actual execution time
- Actual row counts
- Difference between estimate and actual

### EXPLAIN Options (PostgreSQL)
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT JSON)
SELECT * FROM users WHERE country = 'US';
```

- **ANALYZE**: Execute and show actual times
- **BUFFERS**: Show I/O statistics
- **VERBOSE**: Show additional details
- **FORMAT JSON**: Output as JSON

---

## 2. Understanding Query Plans

### Scan Methods

| Method | Description | When Used | Performance |
|--------|-------------|-----------|-------------|
| **Seq Scan** | Full table scan | No index, small table, or fetching large % | Slow for large tables |
| **Index Scan** | Use index, fetch heap tuples | Selective query with index | Good for selective |
| **Index Only Scan** | All data in index | Covering index available | Best |
| **Bitmap Index Scan** | Build bitmap from index | Medium selectivity, multiple indexes | Good for moderate % |

### Join Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **Nested Loop** | For each left row, scan right | Small tables, indexed join key |
| **Hash Join** | Build hash table, probe | Large tables, equality join |
| **Merge Join** | Merge sorted inputs | Both inputs sorted, equality join |

### Example Plans

```sql
-- Sequential Scan (no index)
EXPLAIN SELECT * FROM users;
/*
Seq Scan on users  (cost=0.00..15.20 rows=1020 width=100)
*/

-- Index Scan (using index)
EXPLAIN SELECT * FROM users WHERE user_id = 123;
/*
Index Scan using users_pkey on users  (cost=0.28..8.29 rows=1 width=100)
  Index Cond: (user_id = 123)
*/

-- Bitmap Index Scan (medium selectivity)
EXPLAIN SELECT * FROM users WHERE country = 'US';
/*
Bitmap Heap Scan on users  (cost=5.00..50.00 rows=200 width=100)
  Recheck Cond: (country = 'US')
  -> Bitmap Index Scan on idx_users_country  (cost=0.00..4.95 rows=200)
        Index Cond: (country = 'US')
*/
```

---

## 3. Indexes

### B-Tree Index (Default)
```sql
-- Single column
CREATE INDEX idx_users_country ON users(country);

-- Multiple columns (composite)
CREATE INDEX idx_users_country_city ON users(country, city);

-- Order matters for composite:
-- Good for: WHERE country = 'US' AND city = 'NYC'
-- Good for: WHERE country = 'US'
-- BAD for: WHERE city = 'NYC' (can't use index)
```

**Use cases**:
- Equality (=), range (<, >, BETWEEN)
- ORDER BY, sorting
- Most general-purpose queries

### Unique Index
```sql
CREATE UNIQUE INDEX idx_users_email ON users(email);
```

Enforces uniqueness + provides index benefits.

### Partial Index
```sql
-- Index only active users
CREATE INDEX idx_users_active ON users(country)
WHERE is_active = TRUE;
```

**Benefits**: Smaller index, faster queries on subset

### Expression Index
```sql
-- Index on computed value
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- Now this can use index:
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
```

### Covering Index (Index-Only Scan)
```sql
-- Include additional columns
CREATE INDEX idx_users_country_name ON users(country)
INCLUDE (first_name, last_name);

-- Query can be satisfied from index alone:
SELECT first_name, last_name FROM users WHERE country = 'US';
```

---

## 4. Index Usage Patterns

### Good Index Candidates

✅ **WHERE clause columns**
```sql
-- Frequently filter by status
CREATE INDEX idx_orders_status ON orders(status);
```

✅ **JOIN columns**
```sql
-- Foreign keys should always be indexed
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

✅ **ORDER BY columns**
```sql
-- Frequently sort by date
CREATE INDEX idx_orders_date ON orders(order_date DESC);
```

✅ **High cardinality columns**
```sql
-- email has many unique values (good)
CREATE INDEX idx_users_email ON users(email);
```

### Poor Index Candidates

❌ **Low cardinality columns**
```sql
-- gender typically has 2-3 values (poor candidate)
-- Index won't help much
CREATE INDEX idx_users_gender ON users(gender);  -- Not recommended
```

❌ **Small tables**
```sql
-- If table has < 1000 rows, index overhead > benefit
```

❌ **Columns with many NULLs**
```sql
-- If 90% of values are NULL, index is inefficient
```

---

## 5. Query Optimization Techniques

### SELECT Only What You Need
```sql
-- ❌ BAD: Fetches unnecessary data
SELECT * FROM users;

-- ✅ GOOD: Only fetch needed columns
SELECT user_id, first_name, last_name FROM users;
```

### Use WHERE to Filter Early
```sql
-- ❌ BAD: Filters after join
SELECT u.*, o.*
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
WHERE o.status = 'delivered';

-- ✅ BETTER: Pre-filter with subquery or CTE
WITH delivered_orders AS (
    SELECT * FROM orders WHERE status = 'delivered'
)
SELECT u.*, do.*
FROM users u
INNER JOIN delivered_orders do ON u.user_id = do.user_id;
```

### Avoid SELECT DISTINCT When Possible
```sql
-- ❌ SLOW: Requires sorting/deduplication
SELECT DISTINCT user_id FROM orders;

-- ✅ FASTER: Use GROUP BY or EXISTS
SELECT user_id FROM orders GROUP BY user_id;

-- Or if just checking existence:
SELECT user_id FROM orders WHERE EXISTS (
    SELECT 1 FROM users WHERE users.user_id = orders.user_id
);
```

### Use LIMIT for Testing
```sql
-- When developing query, use LIMIT to test quickly
SELECT * FROM large_table WHERE condition LIMIT 100;
```

### Avoid Functions on Indexed Columns in WHERE
```sql
-- ❌ BAD: Can't use index on email
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- ✅ GOOD: Use expression index or normalize data
CREATE INDEX idx_users_lower_email ON users(LOWER(email));
-- Now the above query can use index

-- OR normalize on INSERT:
INSERT INTO users (email) VALUES (LOWER('Test@Example.com'));
SELECT * FROM users WHERE email = 'test@example.com';
```

### EXISTS vs IN
```sql
-- For large subqueries, EXISTS is often faster
-- ❌ SLOWER: IN with large result set
SELECT * FROM users
WHERE user_id IN (SELECT user_id FROM orders WHERE total_amount > 100);

-- ✅ FASTER: EXISTS (stops at first match)
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.user_id AND o.total_amount > 100
);
```

### JOIN vs Subquery
```sql
-- JOIN is usually faster for small-medium datasets
-- ✅ GOOD: JOIN
SELECT DISTINCT u.*
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id;

-- Subquery can be better if relationship is 1:many and you want distinct
-- ✅ ALSO GOOD: EXISTS
SELECT u.*
FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id);
```

---

## 6. Avoiding Common Anti-Patterns

### Implicit Type Conversion
```sql
-- ❌ BAD: user_id is integer, comparing with string
SELECT * FROM users WHERE user_id = '123';

-- ✅ GOOD: Explicit type
SELECT * FROM users WHERE user_id = 123;
```

### OR with Different Columns (Can't Use Index)
```sql
-- ❌ SLOW: Can't efficiently use indexes
SELECT * FROM users WHERE country = 'US' OR city = 'London';

-- ✅ BETTER: UNION (each part can use index)
SELECT * FROM users WHERE country = 'US'
UNION
SELECT * FROM users WHERE city = 'London';
```

### NOT IN with NULLs
```sql
-- ❌ DANGEROUS: NOT IN returns no rows if subquery has NULL
SELECT * FROM users WHERE user_id NOT IN (SELECT user_id FROM blocked);

-- ✅ SAFE: Use NOT EXISTS
SELECT * FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM blocked b WHERE b.user_id = u.user_id
);
```

### Wildcard at Beginning of LIKE
```sql
-- ❌ CAN'T USE INDEX: Leading wildcard
SELECT * FROM users WHERE email LIKE '%@gmail.com';

-- ✅ CAN USE INDEX: Trailing wildcard
SELECT * FROM users WHERE email LIKE 'john%';

-- For leading wildcard, consider full-text search or trigram index
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_users_email_trgm ON users USING GIN (email gin_trgm_ops);
```

---

## 7. Monitoring & Maintenance

### Find Slow Queries
```sql
-- Enable slow query logging (postgresql.conf)
log_min_duration_statement = 1000  -- Log queries > 1 second
```

### Find Missing Indexes
```sql
-- Queries with seq scans on large tables
SELECT schemaname, tablename, seq_scan, seq_tup_read,
       idx_scan, seq_tup_read / seq_scan AS avg_seq_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND seq_tup_read / seq_scan > 10000
ORDER BY seq_tup_read DESC;
```

### Find Unused Indexes
```sql
-- Indexes that are never used (consider dropping)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE '%_pkey';
```

### Index Bloat
```sql
-- Rebuild bloated indexes
REINDEX INDEX idx_name;
REINDEX TABLE table_name;
```

### Update Statistics
```sql
-- Ensure query planner has accurate statistics
ANALYZE users;
ANALYZE;  -- All tables
```

---

## 8. Quick Optimization Checklist

**Before optimizing**:
1. ✅ Run EXPLAIN ANALYZE to understand current plan
2. ✅ Identify bottlenecks (seq scans, slow joins)
3. ✅ Check if statistics are up to date (ANALYZE)

**Common optimizations**:
1. ✅ Add indexes on WHERE/JOIN/ORDER BY columns
2. ✅ Use covering indexes for frequently accessed column sets
3. ✅ Ensure foreign keys are indexed
4. ✅ SELECT only needed columns
5. ✅ Filter early (push WHERE down)
6. ✅ Use appropriate join type
7. ✅ Avoid functions on indexed columns in WHERE
8. ✅ Use LIMIT for pagination

**After optimizing**:
1. ✅ Re-run EXPLAIN ANALYZE to verify improvement
2. ✅ Compare execution times
3. ✅ Monitor in production

---

## 9. Performance Benchmarks

```sql
-- Timing a query
\timing on  -- In psql
SELECT ...;
\timing off

-- Or use EXPLAIN ANALYZE
EXPLAIN ANALYZE SELECT ...;
```

### Compare Plans
```sql
-- Before optimization
EXPLAIN ANALYZE SELECT * FROM users WHERE country = 'US';
/*
Planning Time: 0.5 ms
Execution Time: 250.0 ms  ← Slow
*/

-- After adding index
CREATE INDEX idx_users_country ON users(country);
EXPLAIN ANALYZE SELECT * FROM users WHERE country = 'US';
/*
Planning Time: 0.3 ms
Execution Time: 5.2 ms  ← Fast!
*/
```

---

## 10. Cost Interpretation

```
Seq Scan on users  (cost=0.00..15406.00 rows=1000000 width=100) (actual time=0.100..200.500 rows=1000000 loops=1)
```

- **cost=0.00..15406.00**: Estimated startup cost..total cost (arbitrary units)
- **rows=1000000**: Estimated rows
- **width=100**: Estimated average row size (bytes)
- **actual time=0.100..200.500**: Actual startup..total time (ms)
- **rows=1000000**: Actual rows returned
- **loops=1**: How many times node executed

**Look for**:
- Large cost values
- Big difference between estimated and actual rows
- Seq Scans on large tables
- Nested loops with many iterations

---

## Quick Reference

| Technique | When to Use |
|-----------|-------------|
| **B-Tree Index** | Equality, ranges, sorting |
| **Covering Index** | Frequently accessed column sets |
| **Partial Index** | Subset of rows (e.g., is_active = TRUE) |
| **EXPLAIN ANALYZE** | Understand actual query performance |
| **EXISTS vs IN** | EXISTS for large subqueries |
| **JOIN vs Subquery** | JOIN for most cases, EXISTS for existence check |
| **LIMIT** | Pagination, top-N queries |
| **ANALYZE** | Update statistics after bulk changes |

## Rule of Thumb

1. **Index foreign keys** - Always
2. **Index WHERE columns** - High selectivity
3. **Index JOIN columns** - Both sides
4. **Index ORDER BY columns** - Frequent sorts
5. **Don't over-index** - Each index has maintenance cost
6. **Test with real data** - Production-like dataset
7. **Monitor in production** - Slow query logs
