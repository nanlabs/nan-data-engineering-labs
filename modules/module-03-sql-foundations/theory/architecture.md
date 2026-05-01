# SQL Architecture and Query Optimization

## Table of Contents

1. [Database Architecture Overview](#database-architecture-overview)
2. [Query Execution Pipeline](#query-execution-pipeline)
3. [Query Parsing](#query-parsing)
4. [Query Planning](#query-planning)
5. [Query Execution](#query-execution)
6. [Indexes](#indexes)
7. [EXPLAIN and Query Analysis](#explain-and-query-analysis)
8. [Join Algorithms](#join-algorithms)
9. [Cost-Based Optimization](#cost-based-optimization)
10. [Statistics and Cardinality](#statistics-and-cardinality)
11. [Query Performance Patterns](#query-performance-patterns)
12. [Partitioning](#partitioning)
13. [Materialized Views](#materialized-views)
14. [Caching](#caching)
15. [Optimization Techniques](#optimization-techniques)

---

## Database Architecture Overview

### High-Level Components

A relational database consists of several layers:

```
┌──────────────────────────────────┐
│     Client Application           │
└────────────┬─────────────────────┘
             │ SQL Query
┌────────────▼─────────────────────┐
│     SQL Parser                   │  <- Syntax validation
└────────────┬─────────────────────┘
             │ Parse Tree
┌────────────▼─────────────────────┐
│     Query Rewriter               │  <- View expansion, rule application
└────────────┬─────────────────────┘
             │ Rewritten Query
┌────────────▼─────────────────────┐
│     Query Planner/Optimizer      │  <- Generate execution plan
└────────────┬─────────────────────┘
             │ Execution Plan
┌────────────▼─────────────────────┐
│     Query Executor               │  <- Execute plan
└────────────┬─────────────────────┘
             │ Access Layer
┌────────────▼─────────────────────┐
│     Storage Engine               │  <- Read/write data
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│     Disk Storage                 │  <- Persistent data
└──────────────────────────────────┘
```

### Storage Engine

**Responsibilities**:
- **Data storage**: Organize data on disk
- **Buffer management**: Keep frequently used data in memory
- **Transaction management**: ACID guarantees
- **Concurrency control**: Multiple users accessing same data
- **Crash recovery**: Restore consistent state after failures

**Key Structures**:
- **Heap files**: Unordered data pages
- **Indexes**: Fast lookup structures
- **WAL (Write-Ahead Log)**: Transaction durability
- **Buffer pool**: In-memory cache of data pages

### Memory Architecture

```
PostgreSQL Memory Layout:

┌─────────────────────────────────────┐
│         Shared Memory               │
│  ┌──────────────────────────────┐  │
│  │      Buffer Pool             │  │  <- Cached data pages
│  │  (shared_buffers parameter)  │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │      WAL Buffers             │  │  <- Transaction log
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Process-Local Memory           │
│  ┌──────────────────────────────┐  │
│  │   Work Memory               │  │  <- Sorts, joins
│  │   (work_mem parameter)       │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   Maintenance Work Mem       │  │  <- Index creation
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## Query Execution pipeline

### Step-by-Step Process

When you execute a query, it goes through these phases:

#### 1. **Connection & Authentication**
Client connects to database server, authenticates.

#### 2. **Query Parsing**
SQL string → Parse tree (syntax validation).

```sql
-- Input SQL
SELECT name FROM users WHERE age > 25;

-- Parse Tree (simplified)
SELECT_STMT
├── SELECT_LIST
│   └── COLUMN: name
├── FROM_CLAUSE
│   └── TABLE: users
└── WHERE_CLAUSE
    └── COMPARISON
        ├── COLUMN: age
        ├── OPERATOR: >
        └── LITERAL: 25
```

#### 3. **Query Rewriting**
- Expand views
- Apply rules
- Simplify expressions

```sql
-- Before rewriting
SELECT * FROM active_users WHERE country = 'US';

-- After rewriting (if active_users is a view)
SELECT user_id, name, email
FROM users
WHERE status = 'active' AND country = 'US';
```

#### 4. **Query Planning**
Generate optimal execution plan by:
- Enumerating possible plans
- Estimating cost of each plan
- Selecting lowest-cost plan

#### 5. **Query Execution**
Execute the plan, fetching data from storage.

#### 6. **Result Formatting**
Convert result to wire protocol, send to client.

---

## Query Parsing

### Lexical Analysis

Break SQL into tokens:

```sql
SELECT name FROM users WHERE age > 25
```

Tokens: `SELECT`, `name`, `FROM`, `users`, `WHERE`, `age`, `>`, `25`

### Syntactic Analysis

Build parse tree according to SQL grammar.

**Common Parse Errors**:
```sql
-- Missing FROM
SELECT name WHERE age > 25;
-- Error: syntax error at or near "WHERE"

-- Mismatched parentheses
SELECT * FROM users WHERE (age > 25;
-- Error: syntax error at or near ";"
```

### Semantic Analysis

Validate query makes sense:
- Do referenced tables exist?
- Do columns exist in those tables?
- Are data types compatible?

```sql
-- Semantic error: column doesn't exist
SELECT name, salary FROM users WHERE department = 'Sales';
-- Error: column "salary" does not exist

-- Type mismatch
SELECT * FROM users WHERE age = 'twenty-five';
-- Error: operator does not exist: integer = character varying
```

---

## Query Planning

### The Planner's Job

Given a query, generate the **execution plan** with:
1. **Access methods**: How to read each table (scan, index)
2. **Join order**: Which tables to join first
3. **Join algorithms**: How to perform joins (nested loop, hash, merge)
4. **Aggregation strategy**: How to group and aggregate

### Plan Enumeration

For a simple 3-table join:

```sql
SELECT * FROM A JOIN B ON A.id = B.a_id JOIN C ON B.id = C.b_id;
```

Possible join orders:
- `(A JOIN B) JOIN C`
- `(A JOIN C) JOIN B`
- `(B JOIN C) JOIN A`
- `A JOIN (B JOIN C)`
- `B JOIN (A JOIN C)`
- `C JOIN (A JOIN B)`

**Complexity**: For N tables, there are `(2N-2)! / (N-1)!` join orders.

**10 tables**: 17.6 million possible orders!

### Heuristics

Planners use heuristics to prune search space:
- Consider only left-deep trees initially
- Use dynamic programming to avoid recomputing
- Stop after finding "good enough" plan (genetic algorithms)

### Cost Estimation

For each plan, estimate:
- **I/O cost**: Disk reads
- **CPU cost**: Processing time
- **Memory cost**: RAM usage

**Example Cost Factors**:
```
Sequential Scan:   cost_per_page × num_pages + cost_per_row × num_rows
Index Scan:        cost_per_index_page × index_pages + cost_per_tuple × tuples
Hash Join:         cost_build_hash + cost_probe
```

---

## Query Execution

### Execution Models

#### Volcano Model (Iterator Model)

Each operator is an iterator with `open()`, `next()`, `close()`:

```python
# Pseudocode for Volcano execution

class SeqScan:
    def next(self):
        return next_row_from_table()

class Filter:
    def __init__(self, child, condition):
        self.child = child
        self.condition = condition

    def next(self):
        while True:
            row = self.child.next()
            if row is None:
                return None
            if self.condition(row):
                return row

class HashJoin:
    def open(self):
        # Build phase: load left side into hash table
        while row := self.left.next():
            self.hash_table.insert(row)

    def next(self):
        # Probe phase: match right side against hash table
        row = self.right.next()
        return self.hash_table.lookup(row.join_key)
```

**Flow**:
```
Result
  ↑ next()
HashJoin
  ↑ next()          ↑ next()
Filter          SeqScan(B)
  ↑ next()
SeqScan(A)
```

**Pros**: Simple, composable operators
**Cons**: Function call overhead per row

#### Vectorized Execution

Process batches of rows (vectors) instead of one row at a time.

```python
# Vectorized pseudocode
class VectorizedFilter:
    def next_batch(self):
        batch = self.child.next_batch()  # Get 1000 rows
        return [row for row in batch if self.condition(row)]
```

**Benefits**: Amortize function call overhead, better CPU cache usage.

### pipeline vs Materialization

**Pipelined**: Operators pass rows directly (streaming)
**Materialized**: Operators write intermediate results to disk

```sql
-- This can be fully pipelined
SELECT name FROM users WHERE age > 25;

-- Sort requires materialization (must see all rows before outputting sorted result)
SELECT name FROM users ORDER BY age;
```

---

## Indexes

### What is an Index?

An **index** is a data structure that speeds up lookups, similar to a book's index.

**Without index**:
```
SELECT * FROM users WHERE user_id = 12345;
```
→ Sequential scan: read all rows until finding user_id = 12345

**With index on user_id**:
→ Index lookup: jump directly to row

### B-Tree Index

Most common index type. Balanced tree structure.

```
                [50 | 100]
               /     |     \
         [25|37]  [75|87]  [120|150]
         /  |  \   /  |  \   /   |   \
    [Rows] ...    ...      ...  [Rows]
```

**Properties**:
- Balanced: All leaf nodes at same depth
- Sorted: Keys in order
- Fast: O(log N) lookups
- Supports: Range queries, sorting

**When to Use**:
- Equality: `WHERE id = 100`
- Range: `WHERE age BETWEEN 25 AND 40`
- Sorting: `ORDER BY name`
- Prefix matching: `WHERE name LIKE 'John%'`

### Hash Index

Hash table: key → row location

**Properties**:
- Very fast equality lookups: O(1)
- Cannot do range queries
- Cannot sort

**When to Use**:
- Only equality: `WHERE id = 100`
- High cardinality columns

### Other Index Types

#### GiST (Generalized Search Tree)
- Geometric data
- Full-text search
- Range types

#### GIN (Generalized Inverted Index)
- Array containment: `WHERE tags @> ARRAY['sql', 'postgres']`
- JSONB: `WHERE data->>'status' = 'active'`
- Full-text search

#### BRIN (Block Range Index)
- Large tables with natural clustering
- Very small index size
- Good for time-series data

### Composite Indexes

Index on multiple columns:

```sql
CREATE INDEX idx_users_country_city ON users(country, city);
```

**Can be used for**:
```sql
WHERE country = 'US'                    -- Uses index
WHERE country = 'US' AND city = 'NYC'  -- Uses index fully
WHERE city = 'NYC'                      -- Cannot use index
```

**Rule**: Index is useful if query filters on **leftmost columns** of index.

### Index Maintenance

**Trade-offs**:
- **Pros**: Faster queries
- **Cons**:
  - Slower writes (INSERT, UPDATE, DELETE must update index)
  - Extra storage space
  - Need to be maintained (VACUUM, REINDEX)

**Best Practices**:
- Index columns in WHERE, JOIN, ORDER BY
- Don't over-index (diminishing returns)
- Monitor index usage: `pg_stat_user_indexes`
- Remove unused indexes

---

## EXPLAIN and Query Analysis

### EXPLAIN Basics

`EXPLAIN` shows query execution plan:

```sql
EXPLAIN SELECT * FROM users WHERE email = 'john@example.com';
```

**Output**:
```
Seq Scan on users  (cost=0.00..15.50 rows=1 width=124)
  Filter: (email = 'john@example.com'::text)
```

**Parts**:
- **Operation**: `Seq Scan` (sequential scan)
- **Table**: `users`
- **Cost**: `0.00..15.50` (startup cost .. total cost)
- **Rows**: Estimated rows returned
- **Width**: Average row size in bytes

### EXPLAIN ANALYZE

Actually execute query and show real numbers:

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'john@example.com';
```

**Output**:
```
Seq Scan on users  (cost=0.00..15.50 rows=1 width=124)
                   (actual time=0.015..0.234 rows=1 loops=1)
  Filter: (email = 'john@example.com'::text)
  Rows Removed by Filter: 999
Planning Time: 0.123 ms
Execution Time: 0.267 ms
```

**Additional Info**:
- **actual time**: Real time spent (ms)
- **rows**: Actual rows returned
- **loops**: How many times node executed
- **Rows Removed**: Filtered out by condition

### Understanding Costs

**Cost Units**: Arbitrary units (not milliseconds)

**Default costs** (PostgreSQL):
- Sequential page read: 1.0
- Random page read: 4.0
- CPU processing per row: 0.01

**Total cost** = I/O cost + CPU cost

**Example**:
```
Seq Scan (cost=0.00..15.50 rows=100 width=50)
```
- 0.00: No startup cost
- 15.50: Total cost to return all rows
- 100: Estimated rows
- 50: Average row width (bytes)

### Common Plan Nodes

#### Seq Scan
Read entire table sequentially.

```
Seq Scan on products  (cost=0.00..100.00 rows=1000 width=50)
```

**When used**: No suitable index, small tables.

#### Index Scan
Use index to find rows.

```
Index Scan using idx_users_email on users  (cost=0.29..8.30 rows=1 width=124)
  Index Cond: (email = 'john@example.com'::text)
```

**When used**: Selective condition with index.

#### Index Only Scan
All needed columns are in index (no table access).

```
Index Only Scan using idx_users_email on users  (cost=0.29..4.31 rows=1 width=32)
  Index Cond: (email = 'john@example.com'::text)
```

**When used**: Query only needs indexed columns.

#### Bitmap Heap Scan
Two-phase: build bitmap of matching rows, then fetch in disk order.

```
Bitmap Heap Scan on products  (cost=5.04..100.00 rows=50 width=100)
  Recheck Cond: (category = 'Electronics'::text)
  ->  Bitmap Index Scan on idx_category  (cost=0.00..5.03 rows=50 width=0)
        Index Cond: (category = 'Electronics'::text)
```

**When used**: Many matching rows (index scan would be random I/O).

#### Nested Loop Join
For each row in outer table, scan inner table.

```
Nested Loop  (cost=0.29..50.00 rows=100 width=200)
  ->  Seq Scan on orders  (cost=0.00..10.00 rows=100 width=100)
  ->  Index Scan using users_pkey on users  (cost=0.29..0.39 rows=1 width=100)
        Index Cond: (user_id = orders.user_id)
```

**When used**: Small outer table, indexed inner table.

#### Hash Join
Build hash table from one side, probe with other side.

```
Hash Join  (cost=15.00..100.00 rows=1000 width=200)
  Hash Cond: (orders.user_id = users.user_id)
  ->  Seq Scan on orders  (cost=0.00..50.00 rows=1000 width=100)
  ->  Hash  (cost=10.00..10.00 rows=100 width=100)
        ->  Seq Scan on users  (cost=0.00..10.00 rows=100 width=100)
```

**When used**: No suitable indexes, equi-join.

#### Merge Join
Both inputs sorted, merge like merge sort.

```
Merge Join  (cost=50.00..100.00 rows=1000 width=200)
  Merge Cond: (orders.user_id = users.user_id)
  ->  Sort  (cost=25.00..27.50 rows=1000 width=100)
        Sort Key: orders.user_id
        ->  Seq Scan on orders  (cost=0.00..50.00 rows=1000 width=100)
  ->  Sort  (cost=20.00..20.50 rows=100 width=100)
        Sort Key: users.user_id
        ->  Seq Scan on users  (cost=0.00..10.00 rows=100 width=100)
```

**When used**: Both sides already sorted, or sort cost is acceptable.

---

## Join Algorithms

### Nested Loop Join

```python
# Pseudocode
for row_outer in outer_table:
    for row_inner in inner_table:
        if row_outer.key == row_inner.key:
            yield (row_outer, row_inner)
```

**Cost**: O(N × M) where N = outer rows, M = inner rows

**With index on inner**:
- Cost: O(N × log M)
- Much better!

**Best for**:
- Small outer table
- Indexed inner table
- Selective join

### Hash Join

```python
# Pseudocode

# Build phase
hash_table = {}
for row in build_side:
    hash_table[row.key].append(row)

# Probe phase
for row in probe_side:
    for match in hash_table[row.key]:
        yield (row, match)
```

**Cost**: O(N + M)

**Requirements**:
- Equi-join (equality condition)
- Enough memory for hash table

**Best for**:
- Large tables
- No suitable indexes
- Equi-join condition

### Merge Join

```python
# Pseudocode (both inputs sorted)
left_iter = iter(left_sorted)
right_iter = iter(right_sorted)

left_row = next(left_iter)
right_row = next(right_iter)

while left_row and right_row:
    if left_row.key == right_row.key:
        yield (left_row, right_row)
        right_row = next(right_iter)
    elif left_row.key < right_row.key:
        left_row = next(left_iter)
    else:
        right_row = next(right_iter)
```

**Cost**: O(N log N + M log M) if sorting needed, O(N + M) if pre-sorted

**Best for**:
- Already sorted inputs (indexed columns)
- Equality or inequality joins
- Merge join can do `<`, `>`, not just `=`

---

## Cost-Based Optimization

### Factors Affecting Cost

1. **Table size**: Number of rows and pages
2. **Index availability**: Which indexes exist
3. **Data distribution**: Skewed vs uniform
4. **Column correlation**: Are columns independent?
5. **Memory**: work_mem, shared_buffers
6. **Hardware**: SSD vs HDD affects random I/O cost

### Statistics

Planner relies on **statistics** about data:

```sql
-- Update statistics
ANALYZE users;

-- View statistics
SELECT * FROM pg_stats WHERE tablename = 'users';
```

**Collected Stats**:
- **n_distinct**: Number of unique values
- **most_common_vals**: Most frequent values
- **most_common_freqs**: Their frequencies
- **histogram_bounds**: Value distribution

### Selectivity Estimation

**Selectivity**: Fraction of rows matching condition

```sql
WHERE age > 25
```

**Estimation**:
- If statistics say 40% of rows have age > 25
- Selectivity = 0.4
- Estimated rows = total_rows × 0.4

**Join Selectivity**:
```sql
FROM orders JOIN users ON orders.user_id = users.user_id
```

Estimated rows = (orders rows × users rows) / MAX(distinct_orders.user_id, distinct_users.user_id)

### Cardinality Estimation

**Cardinality**: Number of distinct values

**Important for**:
- Hash join sizing
- Index selection
- Join order decisions

**Example**:
- users table: 1M rows, user_id has 1M distinct values (unique)
- orders table: 5M rows, user_id has 100K distinct values

Join cardinality ≈ 5M (each order joins to one user)

---

## Statistics and Cardinality

### Maintaining Statistics

```sql
-- Analyze single table
ANALYZE users;

-- Analyze entire database
ANALYZE;

-- Automatic analyze (autovacuum)
-- Configured in postgresql.conf
```

**When to run ANALYZE**:
- After bulk loads
- After significant data changes
- Before important queries

### Statistics Target

Control statistics detail:

```sql
-- Default: 100 histogram buckets
ALTER TABLE users ALTER COLUMN age SET STATISTICS 1000;

-- Then update stats
ANALYZE users;
```

Higher statistics target:
- More accurate estimates
- Slower ANALYZE
- Slightly more storage

### Extended Statistics

Handle correlated columns:

```sql
-- City and state are correlated
CREATE STATISTICS city_state_stats (dependencies)
ON city, state FROM addresses;

ANALYZE addresses;
```

Without extended stats, planner assumes independence (wrong for correlated columns).

---

## Query Performance Patterns

### Anti-Patterns

#### 1. SELECT *

```sql
-- BAD: Fetches unnecessary columns
SELECT * FROM large_table WHERE id = 123;

-- GOOD: Fetch only needed columns
SELECT id, name, email FROM large_table WHERE id = 123;
```

#### 2. Implicit Type Casting

```sql
-- BAD: Index on user_id (integer) won't be used
SELECT * FROM users WHERE user_id = '123';

-- GOOD: Use correct type
SELECT * FROM users WHERE user_id = 123;
```

#### 3. Function on Indexed Column

```sql
-- BAD: Index not used
SELECT * FROM users WHERE LOWER(email) = 'john@example.com';

-- GOOD: Store lowercase, or use functional index
CREATE INDEX idx_lower_email ON users(LOWER(email));
```

#### 4. OR Conditions

```sql
-- BAD: Hard to optimize
SELECT * FROM products WHERE category = 'Books' OR price < 10;

-- BETTER: UNION if appropriate
SELECT * FROM products WHERE category = 'Books'
UNION
SELECT * FROM products WHERE price < 10;
```

#### 5. Correlated Subqueries

```sql
-- BAD: Executes subquery for each row
SELECT
    user_id,
    (SELECT COUNT(*) FROM orders WHERE orders.user_id = users.user_id) AS order_count
FROM users;

-- GOOD: Use JOIN
SELECT
    u.user_id,
    COUNT(o.order_id) AS order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id;
```

### Performance Best Practices

#### 1. Index Strategically

```sql
-- Index foreign keys
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Index frequently filtered columns
CREATE INDEX idx_orders_date ON orders(order_date);

-- Composite index for common query pattern
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);
```

#### 2. Partition Large Tables

```sql
-- Range partitioning by date
CREATE TABLE orders (
    order_id BIGINT,
    user_id INTEGER,
    order_date DATE,
    ...
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

#### 3. Use Appropriate Data Types

```sql
-- GOOD: Right-sized types
user_id INTEGER
price DECIMAL(10, 2)
created_at TIMESTAMP

-- BAD: Oversized types waste space
user_id BIGINT  -- if you'll never exceed 2B users
price DECIMAL(20, 10)  -- unnecessary precision
```

#### 4. Limit Result Sets

```sql
-- Add LIMIT for pagination
SELECT * FROM products ORDER BY created_at DESC LIMIT 100;
```

#### 5. Use Connection Pooling

Don't create new connection for each query. Use pgbouncer, connection pools.

---

## Partitioning

### What is Partitioning?

Split large table into smaller **partitions** based on key.

**Benefits**:
- Query only relevant partitions
- Easier maintenance (drop old partitions)
- Parallel operations per partition

### Range Partitioning

```sql
CREATE TABLE logs (
    log_id BIGINT,
    log_date DATE,
    message TEXT
) PARTITION BY RANGE (log_date);

CREATE TABLE logs_2024_01 PARTITION OF logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE logs_2024_02 PARTITION OF logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

**Query**:
```sql
-- Only scans logs_2024_01 partition
SELECT * FROM logs WHERE log_date = '2024-01-15';
```

### List Partitioning

```sql
CREATE TABLE sales (
    sale_id BIGINT,
    country TEXT,
    amount DECIMAL
) PARTITION BY LIST (country);

CREATE TABLE sales_us PARTITION OF sales FOR VALUES IN ('US');
CREATE TABLE sales_eu PARTITION OF sales FOR VALUES IN ('GB', 'FR', 'DE');
```

### Hash Partitioning

```sql
CREATE TABLE users (
    user_id BIGINT,
    name TEXT
) PARTITION BY HASH (user_id);

CREATE TABLE users_p0 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE users_p1 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE users_p2 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE users_p3 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

**Use case**: Distribute load evenly.

### Partition Pruning

Optimizer eliminates irrelevant partitions:

```sql
EXPLAIN SELECT * FROM logs WHERE log_date = '2024-01-15';
```

**Output**:
```
Seq Scan on logs_2024_01  (cost=...)
  Filter: (log_date = '2024-01-15')
```

Only scans relevant partition!

---

## Materialized Views

### What is a Materialized View?

**View**: Virtual table, computed on query
**Materialized View**: Cached result of query

```sql
-- Create materialized view
CREATE MATERIALIZED VIEW daily_sales AS
SELECT
    order_date,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_sales
FROM orders
GROUP BY order_date;

-- Query it (fast, reads cached result)
SELECT * FROM daily_sales WHERE order_date = '2024-01-15';
```

### Refreshing

```sql
-- Refresh (recompute)
REFRESH MATERIALIZED VIEW daily_sales;

-- Concurrent refresh (doesn't lock view)
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales;
```

**For concurrent refresh**, need unique index:
```sql
CREATE UNIQUE INDEX ON daily_sales(order_date);
```

### Use Cases

- Expensive aggregations
- Pre-computed dashboards
- Data warehouse summary tables

**Trade-off**: Freshness vs speed. Data is stale until refreshed.

---

## Caching

### Query Result Caching

**Application-level caching** (Redis, Memcached):
```python
# Pseudocode
cache_key = "user_orders:123"
result = cache.get(cache_key)
if result is None:
    result = db.query("SELECT * FROM orders WHERE user_id = 123")
    cache.set(cache_key, result, ttl=300)  # 5 minutes
return result
```

### Buffer Cache

Database keeps frequently accessed pages in memory (shared_buffers).

**Check cache hit rate**:
```sql
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;
```

**Goal**: > 99% cache hit ratio for hot tables.

### Prepared Statements

Cache query plan:

```python
# Pseudocode
conn.prepare("get_user", "SELECT * FROM users WHERE user_id = $1")

# Execute multiple times (reuses plan)
conn.execute("get_user", 123)
conn.execute("get_user", 456)
```

---

## Optimization Techniques

### 1. Rewrite Queries

#### Use EXISTS Instead of IN for Subqueries

```sql
-- SLOWER: IN with subquery
SELECT * FROM users
WHERE user_id IN (SELECT user_id FROM orders);

-- FASTER: EXISTS (stops at first match)
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id);
```

#### Push Down Filters

```sql
-- WORSE: Filter after join
SELECT * FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE o.order_date > '2024-01-01';

-- BETTER: Filter early (optimizer usually does this automatically)
SELECT * FROM (
    SELECT * FROM orders WHERE order_date > '2024-01-01'
) o
JOIN users u ON o.user_id = u.user_id;
```

### 2. Denormalize When Appropriate

**Normalized** (3NF):
```sql
-- Requires JOIN
SELECT u.name, o.order_date, o.total
FROM orders o
JOIN users u ON o.user_id = u.user_id;
```

**Denormalized** (add user_name to orders):
```sql
-- No JOIN needed
SELECT user_name, order_date, total FROM orders;
```

**Trade-off**: Faster reads, more storage, risk of inconsistency.

### 3. Use Covering Indexes

Include all query columns in index:

```sql
-- Query
SELECT user_id, email FROM users WHERE country = 'US';

-- Covering index (includes email)
CREATE INDEX idx_users_country_email ON users(country, email);
```

Now query can use Index Only Scan (no table access).

### 4. Batch Operations

```sql
-- BAD: Individual INSERTs
INSERT INTO logs VALUES (1, 'msg1');
INSERT INTO logs VALUES (2, 'msg2');
-- ... 1000 times

-- GOOD: Batch INSERT
INSERT INTO logs VALUES
    (1, 'msg1'),
    (2, 'msg2'),
    ...
    (1000, 'msg1000');
```

### 5. Use Temp Tables for Complex Queries

```sql
-- Break complex query into steps
CREATE TEMP TABLE high_value_users AS
SELECT user_id FROM orders
GROUP BY user_id
HAVING SUM(total_amount) > 10000;

-- Now use temp table
SELECT u.name, u.email
FROM users u
JOIN high_value_users hvu ON u.user_id = hvu.user_id;
```

### 6. Parallel Query Execution

PostgreSQL can parallelize:
- Sequential scans
- Aggregations
- Joins

```sql
-- Enable parallelism
SET max_parallel_workers_per_gather = 4;

-- Query will use parallel workers if beneficial
SELECT COUNT(*) FROM large_table;
```

Check with `EXPLAIN`:
```
Finalize Aggregate  (cost=... rows=1 width=8)
  ->  Gather  (cost=... rows=4 width=8)
        Workers Planned: 4
        ->  Partial Aggregate  (cost=... rows=1 width=8)
              ->  Parallel Seq Scan on large_table
```

---

## Summary

Understanding SQL architecture and optimization:

1. **Query pipeline**: Parse → Plan → Execute
2. **Indexes**: Speed up lookups (B-Tree, Hash, GIN, etc.)
3. **EXPLAIN**: Analyze query plans
4. **Join Algorithms**: Nested Loop, Hash, Merge
5. **Cost-Based Optimization**: Statistics drive decisions
6. **Performance Patterns**: Avoid anti-patterns, use best practices
7. **Partitioning**: Split large tables for better performance
8. **Caching**: Buffer pool, materialized views, application-level

**Next Steps**:
- Practice with EXPLAIN on your queries
- Complete optimization exercises in module
- Study real query plans from your databases

---

**Document Version**: 1.0
**Last Updated**: February 2026
**Word Count**: ~5,000 words
