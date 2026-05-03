# Databricks notebook source
# MAGIC %md
# MAGIC # Exercise 01: Delta Lake Fundamentals - Starter Code
# MAGIC
# MAGIC **Instructions**: Complete all TODO sections below

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable
import time

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Create Database

# COMMAND ----------

spark.sql("CREATE DATABASE IF NOT EXISTS exercise_01_db")
spark.sql("USE exercise_01_db")

print("✅ Database created: exercise_01_db")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 1: Create Delta Table
# MAGIC
# MAGIC **TODO**: Create a Delta table with 1,000 customer records

# COMMAND ----------

# TODO: Generate sample customer data
def generate_customers(num_customers):
    """
    Generate sample customer data.

    Schema:
    - customer_id (INT)
    - name (STRING)
    - email (STRING)
    - country (STRING) - Use: USA, UK, Germany, France
    - signup_date (DATE) - Random dates in 2023
    - total_purchases (DOUBLE) - Random values 0-10000
    """
    # TODO: Implement data generation
    pass

# TODO: Generate 1,000 customers
customers_df = generate_customers(1000)

# TODO: Write as Delta table
# Hint: Use .write.format("delta").mode("overwrite").saveAsTable("customers")

# TODO: Verify table creation
print(f"✅ Table created with {spark.table('customers').count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 2: ACID Transactions
# MAGIC
# MAGIC **TODO**: Demonstrate ACID properties

# COMMAND ----------

# TODO: 2.1 Atomicity - Add 500 customers in single transaction
def demonstrate_atomicity():
    """
    Write 500 new customers atomically.
    Verify all 500 are added or none.
    """
    # TODO: Generate 500 new customers (IDs 1000-1499)
    # TODO: Write to Delta table
    # TODO: Count rows before and after
    pass

demonstrate_atomicity()

# COMMAND ----------

# TODO: 2.2 Consistency - Enforce data constraints
def demonstrate_consistency():
    """
    Try to write invalid data (negative total_purchases).
    Show that Delta Lake can enforce constraints.
    """
    # TODO: Create invalid data with negative purchases
    # TODO: Attempt to write (should fail or be rejected)
    pass

demonstrate_consistency()

# COMMAND ----------

# TODO: 2.3 Isolation - Concurrent writes
def demonstrate_isolation():
    """
    Simulate two concurrent write operations.
    Show they don't interfere with each other.
    """
    # TODO: Write to table from "session 1"
    # TODO: Write to table from "session 2"
    # TODO: Verify both writes succeeded independently
    pass

demonstrate_isolation()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 3: Time Travel
# MAGIC
# MAGIC **TODO**: Query historical versions

# COMMAND ----------

# TODO: Capture initial state (version 0 already exists)
initial_count = spark.table("customers").count()
print(f"Version 0: {initial_count} customers")

# TODO: Update 100 customers (increment total_purchases)
# Hint: Use SQL UPDATE or DataFrame merge

# TODO: Delete 50 customers
# Hint: Use SQL DELETE or DataFrame filter + overwrite

# TODO: Add 200 new customers

# COMMAND ----------

# TODO: Query different versions
# Query version 0
v0_count = # TODO: Use versionAsOf option
print(f"Version 0: {v0_count} customers")

# Query version 2
v2_count = # TODO
print(f"Version 2: {v2_count} customers")

# COMMAND ----------

# TODO: Show DESCRIBE HISTORY
spark.sql("DESCRIBE HISTORY customers").show(truncate=False)

# COMMAND ----------

# TODO: Restore to version 1
# Hint: Use RESTORE command or Delta Table API

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 4: Schema Evolution
# MAGIC
# MAGIC **TODO**: Add new columns to existing table

# COMMAND ----------

# TODO: Create DataFrame with new columns
# New columns: loyalty_tier (STRING), last_purchase_date (DATE)
new_customers_df = # TODO: Generate 100 customers with new columns

# TODO: Write with mergeSchema option
# Hint: .option("mergeSchema", "true")

# COMMAND ----------

# TODO: Verify schema evolution
spark.table("customers").printSchema()
print("✅ Schema evolution complete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 5: MERGE Operations
# MAGIC
# MAGIC **TODO**: Implement UPSERT with MERGE

# COMMAND ----------

# TODO: Create updates DataFrame
# - 100 existing customers with updated total_purchases (IDs 0-99)
# - 50 new customers (IDs 2000-2049)
updates_df = # TODO: Generate updates

# TODO: Perform MERGE
# Hint: Use DeltaTable.forName(spark, "customers").merge(...)

# COMMAND ----------

# TODO: Test idempotency - run MERGE again with same data
# Verify row count stays the same

# COMMAND ----------

# TODO: Verify results
final_count = spark.table("customers").count()
print(f"Final count: {final_count} (expected: 1,050)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 6: Optimize Performance
# MAGIC
# MAGIC **TODO**: Optimize table for better query performance

# COMMAND ----------

# TODO: Count files before OPTIMIZE
files_before = # TODO: Use DESCRIBE DETAIL to get file count
print(f"Files before OPTIMIZE: {files_before}")

# TODO: Run OPTIMIZE
spark.sql("OPTIMIZE customers")

# TODO: Count files after OPTIMIZE
files_after = # TODO
print(f"Files after OPTIMIZE: {files_after}")
print(f"Reduction: {(1 - files_after/files_before)*100:.1f}%")

# COMMAND ----------

# TODO: Measure query performance before ZORDER
import time

start = time.time()
spark.sql("SELECT COUNT(*) FROM customers WHERE country = 'USA'").collect()
time_before = time.time() - start
print(f"Query time before ZORDER: {time_before:.3f}s")

# COMMAND ----------

# TODO: Run OPTIMIZE with ZORDER
spark.sql("OPTIMIZE customers ZORDER BY (country)")

# TODO: Measure query performance after ZORDER
start = time.time()
spark.sql("SELECT COUNT(*) FROM customers WHERE country = 'USA'").collect()
time_after = time.time() - start
print(f"Query time after ZORDER: {time_after:.3f}s")
print(f"Improvement: {(1 - time_after/time_before)*100:.1f}%")

# COMMAND ----------

# TODO: Run VACUUM to clean old files
# Note: Requires disabling retention check for testing
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
spark.sql("VACUUM customers RETAIN 0 HOURS")

print("✅ VACUUM complete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC **TODO**: Run validation script to check your work:
# MAGIC ```bash
# MAGIC cd exercises/exercise-01-delta-lake-basics
# MAGIC python validate.py
# MAGIC ```
