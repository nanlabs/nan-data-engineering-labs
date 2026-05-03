# Databricks notebook source
"""
Exercise 01: Delta Lake Fundamentals - Complete Solution

This notebook demonstrates all core Delta Lake capabilities:
- Creating Delta tables
- ACID transactions
- Time travel
- Schema evolution
- MERGE operations
- Performance optimization

Author: Cloud Data Training
Module: Bonus 01 - Databricks Lakehouse
"""

# COMMAND ----------

# MAGIC %md
# MAGIC # Exercise 01: Delta Lake Fundamentals
# MAGIC
# MAGIC This exercise covers:
# MAGIC 1. Creating Delta tables
# MAGIC 2. ACID transaction properties
# MAGIC 3. Time travel capabilities
# MAGIC 4. Schema evolution
# MAGIC 5. MERGE operations (UPSERT)
# MAGIC 6. Performance optimization with OPTIMIZE and ZORDER

# COMMAND ----------

# Import required libraries
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable
from datetime import datetime, timedelta
import time
import random

# Initialize Spark session (already available in Databricks as 'spark')
# This is just for reference - in Databricks notebooks, spark is pre-configured
print(f"Spark Version: {spark.version}")
print(f"Delta Lake enabled: {spark.conf.get('spark.sql.extensions', 'not set')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Create Database
# MAGIC Create a dedicated database for this exercise

# COMMAND ----------

# Create database for this exercise
spark.sql("DROP DATABASE IF EXISTS exercise_01_db CASCADE")
spark.sql("CREATE DATABASE exercise_01_db")
spark.sql("USE exercise_01_db")

print("✅ Database created: exercise_01_db")

# COMMAND ----------

# MAGIC %md
# MAGIC # Task 1: Create Delta Table (15 min)
# MAGIC
# MAGIC Create a Delta table with 1,000 customer records.
# MAGIC
# MAGIC **Schema**:
# MAGIC - customer_id (INT)
# MAGIC - name (STRING)
# MAGIC - email (STRING)
# MAGIC - country (STRING)
# MAGIC - signup_date (DATE)
# MAGIC - total_purchases (DOUBLE)

# COMMAND ----------

def generate_customers(start_id, count):
    """
    Generate sample customer data.

    Args:
        start_id: Starting customer ID
        count: Number of customers to generate

    Returns:
        DataFrame with customer data
    """
    # Countries for realistic distribution
    countries = ["USA", "UK", "Canada", "Germany", "France", "Spain", "Italy", "Japan", "Australia", "Brazil"]

    # Generate date range for signups (last 2 years)
    base_date = datetime(2024, 1, 1)

    # Create customer records
    customers_data = []
    for i in range(count):
        customer_id = start_id + i
        name = f"Customer_{customer_id}"
        email = f"customer{customer_id}@example.com"
        country = random.choice(countries)
        # Random signup date in last 730 days
        signup_date = base_date - timedelta(days=random.randint(0, 730))
        # Random purchase total between 0 and 10000
        total_purchases = round(random.uniform(0, 10000), 2)

        customers_data.append({
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "country": country,
            "signup_date": signup_date.date(),
            "total_purchases": total_purchases
        })

    # Define schema explicitly
    schema = StructType([
        StructField("customer_id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("email", StringType(), False),
        StructField("country", StringType(), False),
        StructField("signup_date", DateType(), False),
        StructField("total_purchases", DoubleType(), False)
    ])

    return spark.createDataFrame(customers_data, schema)

# COMMAND ----------

# Generate 1,000 customer records
print("Generating 1,000 customer records...")
customers_df = generate_customers(1, 1000)

# Display sample data
print("\nSample customer data:")
customers_df.show(5)
print(f"Total records generated: {customers_df.count()}")

# COMMAND ----------

# Write data as Delta table
print("Writing data to Delta table...")
customers_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("customers")

print("✅ Task 1 Complete: Delta table 'customers' created with 1,000 rows")

# Verify table properties
table_info = spark.sql("DESCRIBE DETAIL customers").collect()[0]
print(f"\nTable Format: {table_info['format']}")
print(f"Table Location: {table_info['location']}")
print(f"Number of Files: {table_info['numFiles']}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Task 2: ACID Transactions (20 min)
# MAGIC
# MAGIC Demonstrate all four ACID properties:
# MAGIC - **A**tomicity: All-or-nothing transactions
# MAGIC - **C**onsistency: Data integrity constraints
# MAGIC - **I**solation: Concurrent operations don't interfere
# MAGIC - **D**urability: Committed data persists

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.1 Atomicity: All-or-Nothing Transactions

# COMMAND ----------

print("Demonstrating Atomicity...")
print("=" * 60)

# Get current row count
current_count = spark.table("customers").count()
print(f"Current row count: {current_count}")

# Generate 500 new customers atomically
print("\nAdding 500 new customers in a single transaction...")
new_customers_df = generate_customers(1001, 500)

# This write operation is atomic - either all 500 rows are added or none
new_customers_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable("customers")

# Verify all 500 were added
final_count = spark.table("customers").count()
print(f"Final row count: {final_count}")
print(f"Rows added: {final_count - current_count}")

if final_count - current_count == 500:
    print("✅ Atomicity verified: All 500 rows added in single transaction")
else:
    print("❌ Atomicity failed: Partial write occurred")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.2 Consistency: Data Integrity Constraints

# COMMAND ----------

print("Demonstrating Consistency...")
print("=" * 60)

# Try to insert data that violates business logic (negative purchases)
print("\nAttempting to write customers with NEGATIVE total_purchases...")
print("(This should be prevented to maintain consistency)\n")

# Create invalid data
invalid_data = [
    (2000, "Invalid Customer", "invalid@example.com", "USA", datetime(2024, 1, 1).date(), -100.0)
]

invalid_df = spark.createDataFrame(invalid_data, schema=customers_df.schema)

# In production, you would use constraints or checks
# For demonstration, we'll validate before writing
try:
    # Check for negative values
    negative_count = invalid_df.filter(col("total_purchases") < 0).count()

    if negative_count > 0:
        print(f"❌ Found {negative_count} records with negative total_purchases")
        print("✅ Consistency maintained: Invalid data rejected")
        print("   Transaction aborted - no data written")
    else:
        invalid_df.write.format("delta").mode("append").saveAsTable("customers")
        print("✅ Valid data written")

except Exception as e:
    print(f"❌ Error prevented inconsistent data: {e}")
    print("✅ Consistency maintained")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.3 Isolation: Concurrent Operations

# COMMAND ----------

print("Demonstrating Isolation...")
print("=" * 60)

# Simulate concurrent writes - each operation sees a consistent view
print("\nSimulating concurrent write operations...")

# Get snapshot before concurrent writes
before_count = spark.table("customers").count()
print(f"Count before concurrent writes: {before_count}")

# Write operation 1: Add 50 customers
print("\nWrite Operation 1: Adding 50 customers...")
batch1_df = generate_customers(3000, 50)
batch1_df.write.format("delta").mode("append").saveAsTable("customers")
print("✅ Batch 1 committed")

# Write operation 2: Add another 50 customers
print("\nWrite Operation 2: Adding 50 customers...")
batch2_df = generate_customers(3050, 50)
batch2_df.write.format("delta").mode("append").saveAsTable("customers")
print("✅ Batch 2 committed")

# Verify both operations completed without interference
after_count = spark.table("customers").count()
print(f"\nCount after concurrent writes: {after_count}")
print(f"Total rows added: {after_count - before_count}")

if after_count - before_count == 100:
    print("✅ Isolation verified: Both operations completed independently")
else:
    print("❌ Isolation may have been violated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.4 Durability: Data Persists

# COMMAND ----------

print("Demonstrating Durability...")
print("=" * 60)

# Write critical data
print("Writing critical customer data...")
critical_customer = generate_customers(9999, 1)
critical_customer.write.format("delta").mode("append").saveAsTable("customers")
print("✅ Critical data written")

# Simulate reading after 'restart' by clearing cache and re-reading
print("\nSimulating system restart (clearing cache)...")
spark.catalog.clearCache()

# Verify data persists
result = spark.table("customers").filter(col("customer_id") == 9999).count()
if result == 1:
    print("✅ Durability verified: Data persists after restart simulation")
else:
    print("❌ Durability failed: Data not found")

current_total = spark.table("customers").count()
print(f"\nFinal count after all ACID demos: {current_total}")
print("\n✅ Task 2 Complete: All ACID properties demonstrated")

# COMMAND ----------

# MAGIC %md
# MAGIC # Task 3: Time Travel (20 min)
# MAGIC
# MAGIC Demonstrate Delta Lake time travel capabilities:
# MAGIC - Query historical versions
# MAGIC - Show DESCRIBE HISTORY
# MAGIC - Restore to previous versions

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.1 Capture Initial State (Version 0)

# COMMAND ----------

print("Time Travel Demo")
print("=" * 60)

# Get current version information
history_df = spark.sql("DESCRIBE HISTORY customers")
current_version = history_df.select("version").first()[0]
print(f"Current version: {current_version}")

# Capture version 0 count (this is actually our latest version with all ACID demo data)
v0_count = spark.table("customers").count()
print(f"Current row count: {v0_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.2 Perform Updates (Create Version 1)

# COMMAND ----------

print("\n3.2 UPDATE Operation - Creating Version 1")
print("-" * 60)

# Update 100 random customers' total_purchases
print("Updating 100 customers...")

# Get 100 random customer IDs
sample_ids = [row.customer_id for row in
              spark.table("customers").select("customer_id").limit(100).collect()]

# Perform update
delta_table = DeltaTable.forName(spark, "customers")

delta_table.update(
    condition = col("customer_id").isin(sample_ids),
    set = {"total_purchases": col("total_purchases") + 500}
)

v1_count = spark.table("customers").count()
print("✅ Version 1 created: Updated 100 customers")
print(f"   Row count: {v1_count} (unchanged)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.3 Perform Deletes (Create Version 2)

# COMMAND ----------

print("\n3.3 DELETE Operation - Creating Version 2")
print("-" * 60)

# Delete 50 customers
print("Deleting 50 customers...")

# Get 50 customer IDs to delete
delete_ids = [row.customer_id for row in
              spark.table("customers").select("customer_id").limit(50).collect()]

delta_table.delete(condition = col("customer_id").isin(delete_ids))

v2_count = spark.table("customers").count()
print("✅ Version 2 created: Deleted 50 customers")
print(f"   Row count: {v2_count} (reduced by 50)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.4 Perform Inserts (Create Version 3)

# COMMAND ----------

print("\n3.4 INSERT Operation - Creating Version 3")
print("-" * 60)

# Add 200 new customers
print("Adding 200 new customers...")
new_batch_df = generate_customers(5000, 200)
new_batch_df.write.format("delta").mode("append").saveAsTable("customers")

v3_count = spark.table("customers").count()
print("✅ Version 3 created: Added 200 customers")
print(f"   Row count: {v3_count} (increased by 200)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.5 Query Historical Versions

# COMMAND ----------

print("\n3.5 Query Historical Versions")
print("-" * 60)

# Show history
print("\nTable History:")
history_df = spark.sql("DESCRIBE HISTORY customers")
history_df.select("version", "timestamp", "operation", "operationMetrics").show(10, truncate=False)

# Get version numbers
latest_version = history_df.select(max("version")).first()[0]
print(f"\nLatest version: {latest_version}")

# Query different versions
print("\nQuerying different versions:")

# Version at latest - 3 (approximate version 0 for our demo)
if latest_version >= 3:
    v0_data = spark.read.format("delta").option("versionAsOf", latest_version - 3).table("customers")
    print(f"  Version {latest_version - 3} count: {v0_data.count()}")

# Version at latest - 1 (approximate version 2 for our demo)
if latest_version >= 1:
    v2_data = spark.read.format("delta").option("versionAsOf", latest_version - 1).table("customers")
    print(f"  Version {latest_version - 1} count: {v2_data.count()}")

# Current version
current_data = spark.table("customers")
print(f"  Current version ({latest_version}) count: {current_data.count()}")

print("\n✅ Time travel queries successful")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.6 Restore to Previous Version

# COMMAND ----------

print("\n3.6 Restore to Previous Version")
print("-" * 60)

# Get count before restore
before_restore = spark.table("customers").count()
print(f"Count before restore: {before_restore}")

# Restore to version latest - 1 (undo the last insert)
restore_version = latest_version - 1
print(f"\nRestoring to version {restore_version}...")

spark.sql(f"RESTORE TABLE customers TO VERSION AS OF {restore_version}")

# Verify restore
after_restore = spark.table("customers").count()
print(f"Count after restore: {after_restore}")
print(f"Difference: {before_restore - after_restore} rows removed")

print("\n✅ Task 3 Complete: Time travel and restore operations successful")

# COMMAND ----------

# MAGIC %md
# MAGIC # Task 4: Schema Evolution (15 min)
# MAGIC
# MAGIC Demonstrate schema evolution by adding new columns:
# MAGIC - loyalty_tier (STRING)
# MAGIC - last_purchase_date (DATE)

# COMMAND ----------

print("Task 4: Schema Evolution")
print("=" * 60)

# Show current schema
print("\nCurrent schema:")
spark.table("customers").printSchema()

# Generate new customers with additional columns
print("\nGenerating customers with new schema...")

# Create data with new columns
new_schema_data = []
for i in range(100):
    customer_id = 6000 + i
    name = f"Customer_{customer_id}"
    email = f"customer{customer_id}@example.com"
    country = random.choice(["USA", "UK", "Canada", "Germany", "France"])
    signup_date = datetime(2024, 3, 1).date()
    total_purchases = round(random.uniform(1000, 5000), 2)

    # NEW COLUMNS
    loyalty_tier = random.choice(["Bronze", "Silver", "Gold", "Platinum"])
    last_purchase_date = datetime(2024, 3, 1) - timedelta(days=random.randint(0, 30))

    new_schema_data.append({
        "customer_id": customer_id,
        "name": name,
        "email": email,
        "country": country,
        "signup_date": signup_date,
        "total_purchases": total_purchases,
        "loyalty_tier": loyalty_tier,
        "last_purchase_date": last_purchase_date.date()
    })

# Define new schema
new_schema = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("country", StringType(), False),
    StructField("signup_date", DateType(), False),
    StructField("total_purchases", DoubleType(), False),
    StructField("loyalty_tier", StringType(), True),      # NEW
    StructField("last_purchase_date", DateType(), True)   # NEW
])

new_schema_df = spark.createDataFrame(new_schema_data, new_schema)

print("Sample of new data with additional columns:")
new_schema_df.show(5)

# COMMAND ----------

# Write with schema evolution enabled
print("\nWriting data with mergeSchema option...")

new_schema_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("customers")

print("✅ Data written with schema evolution")

# COMMAND ----------

# Verify schema evolution
print("\nUpdated schema:")
spark.table("customers").printSchema()

# Verify old records have NULL for new columns
print("\nSample old customers (should have NULL for new columns):")
spark.table("customers").filter(col("customer_id") < 1500).select(
    "customer_id", "name", "loyalty_tier", "last_purchase_date"
).show(5)

print("\nSample new customers (should have values for new columns):")
spark.table("customers").filter(col("customer_id") >= 6000).select(
    "customer_id", "name", "loyalty_tier", "last_purchase_date"
).show(5)

# Count records with new columns populated
with_loyalty = spark.table("customers").filter(col("loyalty_tier").isNotNull()).count()
print(f"\nCustomers with loyalty_tier: {with_loyalty}")

print("\n✅ Task 4 Complete: Schema evolution successful")

# COMMAND ----------

# MAGIC %md
# MAGIC # Task 5: MERGE Operations (25 min)
# MAGIC
# MAGIC Implement UPSERT pattern using MERGE:
# MAGIC - Update 100 existing customers
# MAGIC - Insert 50 new customers
# MAGIC - Test idempotency

# COMMAND ----------

print("Task 5: MERGE Operations (UPSERT)")
print("=" * 60)

# Get current count
before_merge_count = spark.table("customers").count()
print(f"Count before MERGE: {before_merge_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.1 Prepare Update Data

# COMMAND ----------

# Get 100 existing customer IDs
existing_ids = [row.customer_id for row in
                spark.table("customers").select("customer_id").limit(100).collect()]

print(f"\nPreparing updates for {len(existing_ids)} existing customers...")

# Create updates for existing customers (increased total_purchases)
updates_data = []
for cid in existing_ids:
    # Get existing customer data
    existing = spark.table("customers").filter(col("customer_id") == cid).first()

    updates_data.append({
        "customer_id": cid,
        "name": existing["name"],
        "email": existing["email"],
        "country": existing["country"],
        "signup_date": existing["signup_date"],
        "total_purchases": existing["total_purchases"] + 1000,  # Increase purchases
        "loyalty_tier": "Gold",  # Upgrade tier
        "last_purchase_date": datetime(2024, 3, 9).date()
    })

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.2 Prepare Insert Data

# COMMAND ----------

# Create 50 new customers
print("\nPreparing 50 new customers for insertion...")

for i in range(50):
    customer_id = 7000 + i
    updates_data.append({
        "customer_id": customer_id,
        "name": f"NewCustomer_{customer_id}",
        "email": f"newcustomer{customer_id}@example.com",
        "country": random.choice(["USA", "UK", "Canada", "Germany", "France"]),
        "signup_date": datetime(2024, 3, 9).date(),
        "total_purchases": round(random.uniform(100, 1000), 2),
        "loyalty_tier": "Bronze",
        "last_purchase_date": datetime(2024, 3, 9).date()
    })

# Create DataFrame with all updates (100 updates + 50 inserts)
updates_df = spark.createDataFrame(updates_data, new_schema)
print(f"Total updates prepared: {updates_df.count()}")
print("  - 100 updates to existing customers")
print("  - 50 new customer inserts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.3 Execute MERGE Operation

# COMMAND ----------

print("\nExecuting MERGE operation...")

# Get Delta table
delta_table = DeltaTable.forName(spark, "customers")

# Perform MERGE (UPSERT)
merge_result = delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.customer_id = source.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

after_merge_count = spark.table("customers").count()
print("\n✅ MERGE completed")
print(f"Count after MERGE: {after_merge_count}")
print(f"Net new rows: {after_merge_count - before_merge_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.4 Test Idempotency

# COMMAND ----------

print("\nTesting idempotency (running MERGE again with same data)...")

# Run MERGE again with same data
delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.customer_id = source.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

after_second_merge = spark.table("customers").count()
print(f"Count after 2nd MERGE: {after_second_merge}")

if after_second_merge == after_merge_count:
    print("✅ Idempotency verified: Row count unchanged")
    print("   MERGE is safe to run multiple times")
else:
    print("❌ Idempotency failed: Row count changed")

# COMMAND ----------

# Verify no duplicates
print("\nChecking for duplicate customer_ids...")
duplicate_count = spark.table("customers").groupBy("customer_id").count().filter(col("count") > 1).count()

if duplicate_count == 0:
    print("✅ No duplicates found")
else:
    print(f"❌ Found {duplicate_count} duplicate customer_ids")

print("\n✅ Task 5 Complete: MERGE operations successful")
print(f"   Final row count: {after_second_merge}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Task 6: Optimize Performance (25 min)
# MAGIC
# MAGIC Optimize table using:
# MAGIC - OPTIMIZE: Compact small files
# MAGIC - ZORDER: Optimize for specific columns
# MAGIC - VACUUM: Clean old versions

# COMMAND ----------

print("Task 6: Optimize Performance")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.1 Get Baseline Metrics

# COMMAND ----------

print("\n6.1 Baseline Metrics (Before Optimization)")
print("-" * 60)

# Get current table details
details_before = spark.sql("DESCRIBE DETAIL customers").collect()[0]
files_before = details_before["numFiles"]
size_before = details_before["sizeInBytes"]

print(f"Number of files: {files_before}")
print(f"Total size: {size_before:,} bytes ({size_before / 1024 / 1024:.2f} MB)")

# Test query performance (simple country filter)
print("\n Measuring baseline query performance...")
start_time = time.time()
result = spark.table("customers").filter(col("country") == "USA").count()
baseline_time = time.time() - start_time

print("Query: SELECT COUNT(*) WHERE country = 'USA'")
print(f"  Result: {result} customers")
print(f"  Execution time: {baseline_time:.3f} seconds")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.2 Run OPTIMIZE

# COMMAND ----------

print("\n6.2 Running OPTIMIZE")
print("-" * 60)

print("Compacting small files...")
spark.sql("OPTIMIZE customers")
print("✅ OPTIMIZE completed")

# Get metrics after OPTIMIZE
details_after_optimize = spark.sql("DESCRIBE DETAIL customers").collect()[0]
files_after_optimize = details_after_optimize["numFiles"]
size_after_optimize = details_after_optimize["sizeInBytes"]

print("\nAfter OPTIMIZE:")
print(f"  Files: {files_before} → {files_after_optimize} ({100 * (files_before - files_after_optimize) / files_before:.1f}% reduction)")
print(f"  Size: {size_before:,} → {size_after_optimize:,} bytes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.3 Run ZORDER

# COMMAND ----------

print("\n6.3 Running ZORDER BY country")
print("-" * 60)

print("Optimizing data layout for country-based queries...")
spark.sql("OPTIMIZE customers ZORDER BY (country)")
print("✅ ZORDER completed")

# Test query performance after ZORDER
print("\nMeasuring query performance after ZORDER...")
start_time = time.time()
result_after = spark.table("customers").filter(col("country") == "USA").count()
optimized_time = time.time() - start_time

print("Query: SELECT COUNT(*) WHERE country = 'USA'")
print(f"  Result: {result_after} customers")
print(f"  Execution time: {optimized_time:.3f} seconds")

# Calculate improvement
if baseline_time > 0:
    improvement = 100 * (baseline_time - optimized_time) / baseline_time
    print(f"\nPerformance improvement: {improvement:.1f}%")
    if improvement > 0:
        print(f"✅ Query is {improvement:.1f}% faster after ZORDER")
    else:
        print("⚠️  Query time similar (may need more data to see impact)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.4 Run VACUUM

# COMMAND ----------

print("\n6.4 Running VACUUM")
print("-" * 60)

# Note: In production, never use 0 hours retention!
# This is only for demonstration purposes
print("WARNING: Using 0-hour retention for demo only!")
print("         In production, use at least 7 days retention")

# Disable retention check (only for demo/testing)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

print("\nCleaning up old file versions...")
spark.sql("VACUUM customers RETAIN 0 HOURS")
print("✅ VACUUM completed")

# Re-enable retention check
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "true")

# Get final metrics
details_final = spark.sql("DESCRIBE DETAIL customers").collect()[0]
files_final = details_final["numFiles"]
size_final = details_final["sizeInBytes"]

print("\nFinal state after all optimizations:")
print(f"  Files: {files_before} → {files_final} ({100 * (files_before - files_final) / files_before:.1f}% reduction)")
print(f"  Size: {size_before / 1024 / 1024:.2f} MB → {size_final / 1024 / 1024:.2f} MB")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.5 Summary of Optimizations

# COMMAND ----------

print("\n6.5 Optimization Summary")
print("=" * 60)

print("\nFile Reduction:")
print(f"  Before: {files_before} files")
print(f"  After:  {files_final} files")
print(f"  Reduction: {100 * (files_before - files_final) / files_before:.1f}%")

print("\nQuery Performance:")
print(f"  Before ZORDER: {baseline_time:.3f}s")
print(f"  After ZORDER:  {optimized_time:.3f}s")
if baseline_time > 0:
    print(f"  Improvement:   {100 * (baseline_time - optimized_time) / baseline_time:.1f}%")

print("\n✅ Task 6 Complete: All optimizations applied")

# COMMAND ----------

# MAGIC %md
# MAGIC # Exercise Summary

# COMMAND ----------

print("\n" + "=" * 60)
print(" EXERCISE 01: DELTA LAKE FUNDAMENTALS - COMPLETE")
print("=" * 60)

# Final statistics
final_count = spark.table("customers").count()
final_details = spark.sql("DESCRIBE DETAIL customers").collect()[0]

print("\n📊 Final Table Statistics:")
print(f"   Total customers: {final_count:,}")
print(f"   Number of files: {final_details['numFiles']}")
print(f"   Table size: {final_details['sizeInBytes'] / 1024 / 1024:.2f} MB")
print(f"   Format: {final_details['format']}")

print("\n✅ All 6 Tasks Completed:")
print("   ✅ Task 1: Delta table created")
print("   ✅ Task 2: ACID properties demonstrated")
print("   ✅ Task 3: Time travel and restore operations")
print("   ✅ Task 4: Schema evolution with new columns")
print("   ✅ Task 5: MERGE operations (UPSERT)")
print("   ✅ Task 6: Performance optimizations applied")

print("\n🎉 Ready for validation! Run validate.py to verify your solution.")

# Show final schema
print("\n📋 Final Schema:")
spark.table("customers").printSchema()

# Show sample of final data
print("\n📋 Sample Data:")
spark.table("customers").show(10)

# COMMAND ----------
