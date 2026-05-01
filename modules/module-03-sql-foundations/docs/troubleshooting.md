# SQL Foundations - Troubleshooting Guide

This guide helps you diagnose and fix common issues when working with the SQL Foundations module.

## Table of Contents

1. [Docker & Infrastructure Issues](#docker--infrastructure-issues)
2. [Database Connection Issues](#database-connection-issues)
3. [Data Loading Issues](#data-loading-issues)
4. [Test Execution Issues](#test-execution-issues)
5. [Query Performance Issues](#query-performance-issues)
6. [Exercise-Specific Issues](#exercise-specific-issues)
7. [General Debugging Tips](#general-debugging-tips)

---

## Docker & Infrastructure Issues

### Issue: Container Won't Start

**Symptoms**:
```bash
ERROR: Cannot start service postgres: driver failed programming external connectivity
```

**Causes**:
- Port 5432 already in use by another PostgreSQL instance
- Docker daemon not running
- Insufficient permissions

**Solutions**:

1. **Check if port is in use**:
```bash
# Linux/Mac
sudo lsof -i :5432

# Find process and kill it
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5433:5432"  # Use 5433 instead
```

2. **Restart Docker daemon**:
```bash
# Linux
sudo systemctl restart docker

# Mac
# Restart Docker Desktop from application menu
```

3. **Check Docker permissions**:
```bash
# Linux - add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

---

### Issue: Container Exits Immediately

**Symptoms**:
```bash
docker ps  # Container not listed
docker ps -a  # Shows "Exited (1)" status
```

**Solutions**:

1. **Check container logs**:
```bash
docker logs sql-foundations-db

# Common errors:
# - "initdb: error: directory "/var/lib/postgresql/data" exists but is not empty"
# - "FATAL: could not create shared memory segment"
```

2. **Remove volume and recreate**:
```bash
cd infrastructure/
docker-compose down -v  # Remove volumes
docker-compose up -d
```

3. **Check init.sql for errors**:
```bash
# Test SQL syntax
docker exec -i sql-foundations-db psql -U postgres -d ecommerce < infrastructure/init.sql
```

---

### Issue: Out of Disk Space

**Symptoms**:
```bash
ERROR: No space left on device
```

**Solutions**:

1. **Check Docker disk usage**:
```bash
docker system df
```

2. **Clean up unused resources**:
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Nuclear option: remove everything
docker system prune -a --volumes
```

---

## Database Connection Issues

### Issue: "Connection Refused"

**Symptoms**:
```python
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions**:

1. **Verify container is running**:
```bash
docker ps | grep sql-foundations-db

# If not running:
cd infrastructure/
docker-compose up -d
```

2. **Check database is ready**:
```bash
docker exec sql-foundations-db pg_isready -U postgres -d ecommerce

# Should output:
# /var/run/postgresql:5432 - accepting connections
```

3. **Test connection manually**:
```bash
docker exec -it sql-foundations-db psql -U postgres -d ecommerce

# If this works but Python can't connect, check:
# - Firewall rules
# - Connection string (should use localhost, not 127.0.0.1)
```

4. **Check .env configuration**:
```bash
cat infrastructure/.env

# Should have:
POSTGRES_HOST=localhost  # NOT the container name
POSTGRES_PORT=5432
POSTGRES_DB=ecommerce
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
```

---

### Issue: "Database Does Not Exist"

**Symptoms**:
```bash
FATAL: database "ecommerce" does not exist
```

**Solutions**:

1. **List available databases**:
```bash
docker exec sql-foundations-db psql -U postgres -l
```

2. **Create database if missing**:
```bash
docker exec sql-foundations-db psql -U postgres -c "CREATE DATABASE ecommerce;"

# Run init script
docker exec -i sql-foundations-db psql -U postgres -d ecommerce < infrastructure/init.sql
```

3. **Or use reset script**:
```bash
./scripts/reset_db.sh
```

---

### Issue: "Authentication Failed"

**Symptoms**:
```bash
FATAL: password authentication failed for user "postgres"
```

**Solutions**:

1. **Check password in .env**:
```bash
grep POSTGRES_PASSWORD infrastructure/.env
```

2. **Update test configuration** (validation/conftest.py):
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecommerce',
    'user': 'postgres',
    'password': 'postgres123'  # Match .env
}
```

3. **Recreate container with correct credentials**:
```bash
cd infrastructure/
docker-compose down -v
# Update .env with correct password
docker-compose up -d
```

---

## Data Loading Issues

### Issue: "No Data in Tables"

**Symptoms**:
```sql
SELECT COUNT(*) FROM users;
-- Returns: 0
```

**Solutions**:

1. **Check if data files exist**:
```bash
ls -la data/seeds/
# Should show: users.csv, products.csv
```

2. **Load data manually**:
```bash
./scripts/load_sample_data.sh --clear-first
```

3. **Verify CSV format**:
```bash
head data/seeds/users.csv
# Should have headers: user_id,first_name,last_name,email,...
```

4. **Check for loading errors**:
```bash
docker logs sql-foundations-db | grep ERROR
```

---

### Issue: "Duplicate Key Violations"

**Symptoms**:
```bash
ERROR: duplicate key value violates unique constraint "users_pkey"
```

**Solutions**:

1. **Clear existing data first**:
```bash
docker exec sql-foundations-db psql -U postgres -d ecommerce -c "TRUNCATE TABLE users CASCADE;"
```

2. **Or use reset script**:
```bash
./scripts/reset_db.sh
```

3. **Check for duplicate IDs in CSV**:
```bash
cut -d',' -f1 data/seeds/users.csv | sort | uniq -d
# Should return nothing if no duplicates
```

---

### Issue: "Foreign Key Constraint Violations"

**Symptoms**:
```bash
ERROR: insert or update on table "orders" violates foreign key constraint
```

**Solutions**:

1. **Load data in correct order**:
```bash
# Correct order:
# 1. users (parent)
# 2. products (parent)
# 3. orders (references users)
# 4. order_items (references orders and products)
# 5. user_activity (references users)
```

2. **Verify parent records exist**:
```sql
-- Check if user_id exists before inserting order
SELECT COUNT(*) FROM users WHERE user_id = 123;
```

3. **Use reset script which loads in correct order**:
```bash
./scripts/reset_db.sh
```

---

## Test Execution Issues

### Issue: "pytest: command not found"

**Symptoms**:
```bash
./scripts/validate.sh
# pytest: command not found
```

**Solutions**:

1. **Activate virtual environment**:
```bash
source venv/bin/activate

# Or if venv doesn't exist:
./scripts/setup.sh
```

2. **Install requirements**:
```bash
pip install -r requirements.txt
```

---

### Issue: "ImportError: No module named 'psycopg2'"

**Symptoms**:
```python
ImportError: No module named 'psycopg2'
```

**Solutions**:

1. **Install psycopg2-binary**:
```bash
pip install psycopg2-binary
```

2. **If that fails** (common on Mac M1/M2):
```bash
# Install PostgreSQL development files
brew install postgresql

# Then install psycopg2
pip install psycopg2
```

3. **Or use binary version**:
```bash
pip uninstall psycopg2
pip install psycopg2-binary
```

---

### Issue: "Tests Fail with 'No Data Found'"

**Symptoms**:
```python
AssertionError: Expected at least 1 row, got 0
```

**Solutions**:

1. **Verify data is loaded**:
```bash
docker exec sql-foundations-db psql -U postgres -d ecommerce -c "SELECT COUNT(*) FROM users;"
```

2. **Reload data**:
```bash
./scripts/load_sample_data.sh --clear-first
```

3. **Check test is using correct database**:
```python
# In validation/conftest.py
DB_CONFIG = {
    'host': 'localhost',  # Not 'sql-foundations-db'
    'database': 'ecommerce',  # Not 'test_db'
}
```

---

### Issue: "Tests Pass Locally But Fail in CI"

**Symptoms**:
```bash
# Local: All tests passed
# CI: Multiple failures
```

**Solutions**:

1. **Check database initialization in CI**:
```yaml
# .github/workflows/test.yml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

2. **Ensure init.sql runs in CI**:
```yaml
steps:
  - name: Initialize database
    run: |
      PGPASSWORD=postgres123 psql -h localhost -U postgres -d ecommerce < infrastructure/init.sql
```

3. **Load test data in CI**:
```yaml
  - name: Load test data
    run: |
      # Load seed data
      PGPASSWORD=postgres123 psql -h localhost -U postgres -d ecommerce -c "\COPY users(...) FROM 'data/seeds/users.csv' WITH CSV HEADER"
```

---

## Query Performance Issues

### Issue: "Query Takes Too Long"

**Symptoms**:
```sql
-- Query runs for minutes
SELECT * FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE u.country = 'US';
```

**Solutions**:

1. **Check query plan**:
```sql
EXPLAIN ANALYZE
SELECT * FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE u.country = 'US';

-- Look for:
-- - Seq Scan on large tables (bad)
-- - Index Scan (good)
-- - High cost values
```

2. **Add missing indexes**:
```sql
-- Index foreign keys
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Index frequently filtered columns
CREATE INDEX idx_users_country ON users(country);
```

3. **Analyze tables**:
```sql
ANALYZE users;
ANALYZE orders;
```

4. **Limit results during development**:
```sql
-- Add LIMIT while testing
SELECT * FROM orders LIMIT 100;
```

---

### Issue: "Index Not Being Used"

**Symptoms**:
```sql
EXPLAIN SELECT * FROM users WHERE country = 'US';
-- Shows: Seq Scan (not Index Scan)
```

**Solutions**:

1. **Check if index exists**:
```sql
\d users
-- Look for indexes in output
```

2. **Verify statistics are up to date**:
```sql
ANALYZE users;
```

3. **Check selectivity**:
```sql
-- If query returns >10% of rows, seq scan may be faster
SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users)
FROM users
WHERE country = 'US';

-- If >10%, seq scan is probably correct choice
```

4. **Force index usage (testing only)**:
```sql
SET enable_seqscan = OFF;
EXPLAIN SELECT * FROM users WHERE country = 'US';
SET enable_seqscan = ON;
```

---

## Exercise-Specific Issues

### Exercise 01: Basic Queries

**Issue**: "LIKE pattern not working"

```sql
-- Doesn't match anything
SELECT * FROM users WHERE email LIKE '%GMAIL.COM';
```

**Solution**: Use ILIKE for case-insensitive matching:
```sql
SELECT * FROM users WHERE email ILIKE '%gmail.com';
```

---

### Exercise 02: JOINs

**Issue**: "LEFT JOIN returns unexpected NULL values"

```sql
SELECT u.name, o.order_id
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;
-- All order_id values are NULL
```

**Solution**: Check column names match:
```sql
-- Verify column names
\d users
\d orders

-- Common mistake: joining on wrong columns
-- WRONG: ON u.id = o.user_id
-- RIGHT: ON u.user_id = o.user_id
```

---

### Exercise 03: Aggregations

**Issue**: "Column must appear in GROUP BY"

```sql
SELECT user_id, first_name, COUNT(*)
FROM orders
JOIN users ON orders.user_id = users.user_id
GROUP BY user_id;
-- ERROR: column "first_name" must appear in GROUP BY clause
```

**Solution**: Add all non-aggregated columns to GROUP BY:
```sql
SELECT user_id, first_name, COUNT(*)
FROM orders
JOIN users ON orders.user_id = users.user_id
GROUP BY user_id, first_name;
```

---

### Exercise 04: Window Functions

**Issue**: "LAST_VALUE returns current row"

```sql
SELECT product_name,
       FIRST_VALUE(product_name) OVER (ORDER BY price) AS cheapest,
       LAST_VALUE(product_name) OVER (ORDER BY price) AS most_expensive
FROM products;
-- LAST_VALUE returns wrong result
```

**Solution**: Specify complete frame:
```sql
SELECT product_name,
       FIRST_VALUE(product_name) OVER (ORDER BY price) AS cheapest,
       LAST_VALUE(product_name) OVER (
           ORDER BY price
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       ) AS most_expensive
FROM products;
```

---

### Exercise 05: CTEs

**Issue**: "WITH query must be referenced"

```sql
WITH high_value_orders AS (
    SELECT * FROM orders WHERE total_amount > 500
);
-- ERROR: WITH query "high_value_orders" was not referenced
```

**Solution**: Use the CTE in main query:
```sql
WITH high_value_orders AS (
    SELECT * FROM orders WHERE total_amount > 500
)
SELECT * FROM high_value_orders;  -- Reference it here
```

---

### Exercise 06: Optimization

**Issue**: "Can't see query plan"

```sql
EXPLAIN SELECT * FROM users;
-- Output is hard to read
```

**Solution**: Use EXPLAIN with options:
```sql
-- Better formatting
EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS)
SELECT * FROM users WHERE country = 'US';

-- Or visual format
EXPLAIN (FORMAT TEXT, ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM users WHERE country = 'US';
```

---

## General Debugging Tips

### Enable SQL Logging

```bash
# Edit docker-compose.yml
command:
  - "postgres"
  - "-c"
  - "log_statement=all"
  - "-c"
  - "log_duration=on"

# Restart container
docker-compose restart

# View logs
docker logs -f sql-foundations-db
```

---

### Check PostgreSQL Version

```bash
docker exec sql-foundations-db psql -U postgres -c "SELECT version();"
```

---

### Vacuum and Analyze

```sql
-- After bulk data changes
VACUUM ANALYZE;

-- Or specific table
VACUUM ANALYZE users;
```

---

### Check Table Sizes

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

### Reset Everything (Nuclear Option)

```bash
# Stop and remove containers and volumes
cd infrastructure/
docker-compose down -v

# Remove virtual environment
rm -rf venv/

# Start fresh
cd ..
./scripts/setup.sh
```

---

## Getting Help

If you're still stuck after trying these solutions:

1. **Check module STATUS.md**: Verify all steps completed
2. **Review logs**: `docker logs sql-foundations-db`
3. **Run validation**: `./scripts/validate.sh --verbose`
4. **Check documentation**: See docs/sql-guide.md for SQL reference
5. **Inspect database state**:
```bash
docker exec -it sql-foundations-db psql -U postgres -d ecommerce

-- List tables
\dt

-- Describe table
\d table_name

-- Check data
SELECT COUNT(*) FROM users;
```

---

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Container won't start | `docker-compose down -v && docker-compose up -d` |
| No data | `./scripts/load_sample_data.sh --clear-first` |
| Tests fail | `./scripts/validate.sh --verbose` |
| Slow queries | `ANALYZE; CREATE INDEX ...` |
| Complete reset | `./scripts/reset_db.sh` |
| Python issues | `source venv/bin/activate && pip install -r requirements.txt` |
| Permission denied | `chmod +x scripts/*.sh` |

---

**Remember**: When in doubt, check the logs and verify your assumptions with simple queries!
