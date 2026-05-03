# Exercise 01: Delta Lake Fundamentals

## Overview
Master Delta Lake basics by creating tables, demonstrating ACID transactions, using time travel, and optimizing performance.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐ Intermediate
**Prerequisites**: Module 07 (Spark basics)

---

## Learning Objectives
By completing this exercise, you will be able to:
- Create Delta tables from CSV and DataFrames
- Demonstrate ACID transaction properties
- Query historical versions with time travel
- Optimize tables with OPTIMIZE and ZORDER
- Implement schema evolution patterns
- Use MERGE for UPSERT operations

---

## Scenario
You're building a customer data platform. You need to:
1. Load customer data from CSV into a Delta table
2. Demonstrate data reliability with ACID properties
3. Track historical changes with time travel
4. Optimize query performance
5. Handle schema changes over time

---

## Requirements

### Task 1: Create Delta Table (15 min)
Create a Delta table named `customers` with this schema:
- `customer_id` (INT) - Primary key
- `name` (STRING)
- `email` (STRING)
- `country` (STRING)
- `signup_date` (DATE)
- `total_purchases` (DOUBLE)

**Data Source**: Generate 1,000 sample customer records

**Success Criteria**:
- ✅ Table exists in database `exercise_01_db`
- ✅ Exactly 1,000 rows
- ✅ Schema matches specification
- ✅ Table is in Delta format (not Parquet)

---

### Task 2: ACID Transactions (20 min)
Demonstrate ACID properties:

1. **Atomicity**: Write 500 new customers in a single transaction
   - Verify all 500 are added or none (no partial writes)

2. **Consistency**: Enforce constraint that `total_purchases >= 0`
   - Attempt to write negative values
   - Verify transaction fails and data stays consistent

3. **Isolation**: Run two concurrent write operations
   - Show they don't interfere with each other

4. **Durability**: Write critical data
   - Verify it persists after "crash" (restart Spark session)

**Success Criteria**:
- ✅ Demonstrate each ACID property with working code
- ✅ Add 500 customers atomically
- ✅ Show isolation between concurrent writes

---

### Task 3: Time Travel (20 min)
Implement time travel capabilities:

1. Capture initial state (version 0)
2. Update 100 customers (version 1)
3. Delete 50 customers (version 2)
4. Add 200 new customers (version 3)

**Query Requirements**:
- Query version 0 (initial state, 1,000 customers)
- Query version 2 (after delete, 950 customers)
- Query as of yesterday's timestamp
- Show DESCRIBE HISTORY output

**Restore Operation**:
- Restore table to version 1
- Verify row count matches version 1

**Success Criteria**:
- ✅ Can query 4 different versions
- ✅ DESCRIBE HISTORY shows all operations
- ✅ RESTORE works correctly

---

### Task 4: Schema Evolution (15 min)
Handle evolving schema:

1. Add new column `loyalty_tier` (STRING)
2. Add new column `last_purchase_date` (DATE)
3. Write data with these new columns using `mergeSchema` option

**Success Criteria**:
- ✅ Original 1,000 customers have NULL for new columns
- ✅ New customers have values for new columns
- ✅ Schema includes both old and new columns

---

### Task 5: MERGE Operations (25 min)
Implement UPSERT with MERGE:

**Scenario**: Daily customer updates arrive:
- 100 existing customers with updated `total_purchases`
- 50 new customers
- Must be idempotent (can run multiple times safely)

**MERGE Logic**:
```sql
MERGE INTO customers AS target
USING updates AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

**Test Idempotency**:
- Run MERGE twice with same data
- Verify row count stays same (no duplicates)

**Success Criteria**:
- ✅ 100 customers updated correctly
- ✅ 50 new customers inserted
- ✅ No duplicates after running MERGE twice
- ✅ Total row count is 1,050

---

### Task 6: Optimize Performance (25 min)
Optimize table for query performance:

1. **OPTIMIZE**: Compact small files
   - Run OPTIMIZE command
   - Show reduction in file count

2. **ZORDER**: Optimize for country-based queries
   - Run `OPTIMIZE customers ZORDER BY (country)`
   - Measure query performance improvement

3. **VACUUM**: Clean up old files
   - Run VACUUM with 0-hour retention (testing only)
   - Verify old versions are deleted

**Performance Test**:
```sql
-- Before OPTIMIZE
SELECT COUNT(*) FROM customers WHERE country = 'USA'
-- Record execution time

-- After OPTIMIZE + ZORDER
SELECT COUNT(*) FROM customers WHERE country = 'USA'
-- Compare execution times (should be faster)
```

**Success Criteria**:
- ✅ OPTIMIZE reduces file count by at least 50%
- ✅ ZORDER improves query time by at least 20%
- ✅ VACUUM deletes files older than retention period

---

## Hints

<details>
<summary>Hint 1: Creating Delta Table</summary>

```python
# Generate sample data
from pyspark.sql.functions import *

customers_df = spark.range(0, 1000).select(
    col("id").alias("customer_id"),
    concat(lit("User"), col("id")).alias("name"),
    concat(lit("user"), col("id"), lit("@example.com")).alias("email"),
    # ... more columns
)

# Write as Delta
customers_df.write.format("delta").mode("overwrite").saveAsTable("customers")
```
</details>

<details>
<summary>Hint 2: Time Travel Syntax</summary>

```python
# Query by version
spark.read.format("delta").option("versionAsOf", 0).table("customers")

# Query by timestamp
spark.read.format("delta").option("timestampAsOf", "2024-03-09").table("customers")

# Show history
spark.sql("DESCRIBE HISTORY customers")
```
</details>

<details>
<summary>Hint 3: MERGE Syntax</summary>

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forName(spark, "customers")

delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.customer_id = source.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```
</details>

<details>
<summary>Hint 4: OPTIMIZE Syntax</summary>

```sql
-- Compact files
OPTIMIZE customers;

-- ZORDER by country
OPTIMIZE customers ZORDER BY (country);

-- Clean old versions
VACUUM customers RETAIN 0 HOURS;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-01-delta-lake-basics
python validate.py
```

**Expected Output**:
```
✅ Task 1: Delta table created (1,000 rows)
✅ Task 2: ACID transactions demonstrated
✅ Task 3: Time travel working (4 versions found)
✅ Task 4: Schema evolution successful (2 new columns)
✅ Task 5: MERGE operation correct (1,050 rows, no duplicates)
✅ Task 6: Optimizations applied (60% file reduction, 35% query speedup)

🎉 Exercise 01 Complete! Total Score: 100/100
```

---

## Deliverables
Submit the following:
1. `solution.py` - Complete solution with all tasks
2. Screenshot of DESCRIBE HISTORY output
3. Performance comparison table (before/after OPTIMIZE)

---

## Resources
- [Delta Lake documentation](https://docs.delta.io/)
- [Databricks Delta Lake guide](https://docs.databricks.com/delta/)
- Notebook: `notebooks/01-delta-lake-basics.py`
- Diagram: `assets/diagrams/delta-lake-internals.mmd`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 02: Production ETL Pipelines (Medallion Architecture)
- Module 06: ETL Fundamentals (review if needed)
