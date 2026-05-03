# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook 01: Delta Lake Basics
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC By the end of this notebook, you will understand:
# MAGIC - How to create and query Delta Lake tables
# MAGIC - ACID transactions in action
# MAGIC - Time travel capabilities
# MAGIC - Schema evolution
# MAGIC - MERGE operations for UPSERT
# MAGIC - Delta Lake optimization techniques
# MAGIC
# MAGIC ## Prerequisites
# MAGIC - Databricks Runtime 14.3 LTS or higher
# MAGIC - Basic SQL and Python knowledge
# MAGIC
# MAGIC ## Estimated Time: 45-60 minutes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC First, let's set up our environment and create a database for our work.

# COMMAND ----------

# Import required libraries
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable

# COMMAND ----------

# Set up database and table paths
database_name = "training_delta_basics"
table_path = f"/tmp/{database_name}"

# Create database
spark.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
spark.sql(f"USE {database_name}")

print(f"✅ Using database: {database_name}")
print(f"✅ Tables will be stored at: {table_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Creating Your First Delta Lake Table
# MAGIC
# MAGIC Delta Lake tables can be created in several ways:
# MAGIC 1. From a DataFrame
# MAGIC 2. Using SQL DDL
# MAGIC 3. Converting existing Parquet files
# MAGIC
# MAGIC Let's explore each method.

# COMMAND ----------

# Method 1: Create Delta table from DataFrame
print("Creating sample customer data...")

customers_data = [
    (1, "John Doe", "john@email.com", "2023-01-15", "gold", 5000.00),
    (2, "Jane Smith", "jane@email.com", "2023-02-20", "silver", 3000.00),
    (3, "Bob Johnson", "bob@email.com", "2023-03-10", "bronze", 1500.00),
    (4, "Alice Williams", "alice@email.com", "2023-04-05", "platinum", 10000.00),
    (5, "Charlie Brown", "charlie@email.com", "2023-05-12", "gold", 4500.00)
]

schema = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("signup_date", StringType(), False),
    StructField("tier", StringType(), False),
    StructField("lifetime_value", DoubleType(), False)
])

customers_df = spark.createDataFrame(customers_data, schema)

# Write as Delta table
customers_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{table_path}/customers")

print("✅ Created Delta table: customers")

# COMMAND ----------

# Create a SQL table reference
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS customers
    USING DELTA
    LOCATION '{table_path}/customers'
""")

# Query the table
display(spark.table("customers"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: ACID Transactions
# MAGIC
# MAGIC Delta Lake provides ACID guarantees:
# MAGIC - **Atomicity**: All changes succeed or fail together
# MAGIC - **Consistency**: Data is always in a valid state
# MAGIC - **Isolation**: Concurrent operations don't interfere
# MAGIC - **Durability**: Committed changes are permanent
# MAGIC
# MAGIC Let's demonstrate this with concurrent writes.

# COMMAND ----------

# Simulate concurrent write scenario
print("Testing ACID transactions...")

# Transaction 1: Add new customers
new_customers = [
    (6, "David Lee", "david@email.com", "2023-06-15", "silver", 2800.00),
    (7, "Emma Davis", "emma@email.com", "2023-07-20", "gold", 4200.00)
]

new_customers_df = spark.createDataFrame(new_customers, schema)

# Write atomically - either all rows are added or none
new_customers_df.write \
    .format("delta") \
    .mode("append") \
    .save(f"{table_path}/customers")

print("✅ New customers added atomically")

# Verify
customer_count = spark.table("customers").count()
print(f"Total customers: {customer_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: Time Travel
# MAGIC
# MAGIC Delta Lake maintains a transaction log that allows you to:
# MAGIC - Query previous versions of data
# MAGIC - Audit changes over time
# MAGIC - Rollback mistakes
# MAGIC
# MAGIC This is called "Time Travel"

# COMMAND ----------

# View version history
print("📜 Table History:")
history_df = spark.sql("DESCRIBE HISTORY customers")
display(history_df.select("version", "timestamp", "operation", "operationMetrics"))

# COMMAND ----------

# Query specific version (version 0 = first version)
print("\n📊 Version 0 (original data):")
version_0_df = spark.read \
    .format("delta") \
    .option("versionAsOf", 0) \
    .load(f"{table_path}/customers")

display(version_0_df)

# COMMAND ----------

# Query by timestamp
print("\n📊 Data as of specific timestamp:")

# Get timestamp from first version
first_timestamp = history_df.filter("version = 0").select("timestamp").first()[0]
print(f"Querying data as of: {first_timestamp}")

timestamp_df = spark.read \
    .format("delta") \
    .option("timestampAsOf", first_timestamp) \
    .load(f"{table_path}/customers")

display(timestamp_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 4: Schema Evolution
# MAGIC
# MAGIC Delta Lake can automatically handle schema changes:
# MAGIC - Add new columns
# MAGIC - Change column types (with restrictions)
# MAGIC - Maintain backward compatibility

# COMMAND ----------

# Add new column to existing table
print("Adding new columns with schema evolution...")

# Create new data with additional columns
evolved_customers = [
    (8, "Frank Miller", "frank@email.com", "2023-08-10", "bronze", 1200.00, "USA", True),
    (9, "Grace Wilson", "grace@email.com", "2023-09-05", "platinum", 8500.00, "Canada", True)
]

evolved_schema = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("signup_date", StringType(), False),
    StructField("tier", StringType(), False),
    StructField("lifetime_value", DoubleType(), False),
    StructField("country", StringType(), True),  # New column
    StructField("is_active", BooleanType(), True)  # New column
])

evolved_df = spark.createDataFrame(evolved_customers, evolved_schema)

# Write with schema merge
evolved_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(f"{table_path}/customers")

print("✅ Schema evolved - new columns added")

# COMMAND ----------

# Verify schema evolution
print("\n📋 Current schema:")
spark.table("customers").printSchema()

# Query data (old rows will have NULL for new columns)
display(spark.table("customers").orderBy("customer_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 5: MERGE Operations (UPSERT)
# MAGIC
# MAGIC Delta Lake supports MERGE (UPSERT) operations:
# MAGIC - Update existing records
# MAGIC - Insert new records
# MAGIC - Delete records (optional)
# MAGIC
# MAGIC This is critical for Change Data Capture (CDC) scenarios.

# COMMAND ----------

# Prepare updates and new records
print("Preparing UPSERT data...")

upsert_data = [
    # Update existing customer (ID 1)
    (1, "John Doe", "john.doe@email.com", "2023-01-15", "platinum", 12000.00, "USA", True),
    # Update existing customer (ID 2)
    (2, "Jane Smith", "jane.smith@email.com", "2023-02-20", "gold", 5500.00, "UK", True),
    # New customer (ID 10)
    (10, "Henry Taylor", "henry@email.com", "2023-10-15", "silver", 3200.00, "Australia", True)
]

updates_df = spark.createDataFrame(upsert_data, evolved_schema)

print("Updates to apply:")
display(updates_df)

# COMMAND ----------

# Perform MERGE operation

delta_table = DeltaTable.forPath(spark, f"{table_path}/customers")

# MERGE syntax
delta_table.alias("target") \
    .merge(
        updates_df.alias("source"),
        "target.customer_id = source.customer_id"
    ) \
    .whenMatchedUpdate(set={
        "email": "source.email",
        "tier": "source.tier",
        "lifetime_value": "source.lifetime_value",
        "country": "source.country",
        "is_active": "source.is_active"
    }) \
    .whenNotMatchedInsert(values={
        "customer_id": "source.customer_id",
        "name": "source.name",
        "email": "source.email",
        "signup_date": "source.signup_date",
        "tier": "source.tier",
        "lifetime_value": "source.lifetime_value",
        "country": "source.country",
        "is_active": "source.is_active"
    }) \
    .execute()

print("✅ MERGE completed")

# COMMAND ----------

# Verify MERGE results
print("\n📊 After MERGE:")
result_df = spark.table("customers").orderBy("customer_id")
display(result_df)

# Check specific updates
print("\nUpdated customers (ID 1 and 2):")
display(result_df.filter("customer_id IN (1, 2)"))

print("\nNew customer (ID 10):")
display(result_df.filter("customer_id = 10"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 6: Delta Lake Optimization
# MAGIC
# MAGIC Delta Lake provides several optimization commands:
# MAGIC - **OPTIMIZE**: Compacts small files
# MAGIC - **ZORDER**: Co-locates data for faster queries
# MAGIC - **VACUUM**: Removes old file versions

# COMMAND ----------

# Check current file stats
print("📊 Current file statistics:")
file_stats = spark.sql("""
    DESCRIBE DETAIL customers
""")
display(file_stats.select("format", "numFiles", "sizeInBytes"))

# COMMAND ----------

# OPTIMIZE: Compact small files into larger ones
print("🔧 Running OPTIMIZE...")

optimize_result = spark.sql("""
    OPTIMIZE customers
    ZORDER BY (customer_id, tier)
""")

display(optimize_result)

# COMMAND ----------

# Check file stats after optimization
print("\n📊 After OPTIMIZE:")
file_stats_after = spark.sql("""
    DESCRIBE DETAIL customers
""")
display(file_stats_after.select("format", "numFiles", "sizeInBytes"))

# COMMAND ----------

# VACUUM: Remove old file versions (retention default: 7 days)
print("🧹 Preparing VACUUM...")

# First, check what would be deleted (dry run)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

vacuum_preview = spark.sql("""
    VACUUM customers RETAIN 0 HOURS DRY RUN
""")

print("Files that would be deleted:")
display(vacuum_preview)

# COMMAND ----------

# MAGIC %md
# MAGIC ⚠️ **Warning**: VACUUM permanently deletes files!
# MAGIC
# MAGIC In production:
# MAGIC - Keep default 7-day retention for time travel
# MAGIC - Only reduce retention if you're sure you don't need history
# MAGIC - Always test with DRY RUN first

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 7: Advanced Delta Lake Features

# COMMAND ----------

# 1. RESTORE: Rollback to previous version
print("🔄 Demonstrating RESTORE...")

# Make a mistake (delete all platinum customers)
spark.sql("""
    DELETE FROM customers WHERE tier = 'platinum'
""")

print("\nAfter deletion:")
display(spark.table("customers").groupBy("tier").count())

# COMMAND ----------

# Restore to previous version
# Get version before deletion
history = spark.sql("DESCRIBE HISTORY customers")
previous_version = history.filter("operation != 'DELETE'").first()["version"]

print(f"\n🔄 Restoring to version {previous_version}...")

spark.sql(f"""
    RESTORE TABLE customers TO VERSION AS OF {previous_version}
""")

print("✅ Table restored!")
display(spark.table("customers").groupBy("tier").count())

# COMMAND ----------

# 2. Data Skipping Statistics
print("📊 Data Skipping Statistics:")

# Delta Lake maintains min/max statistics for each file
# This enables "data skipping" - avoiding reads of irrelevant files

stats_df = spark.sql("""
    DESCRIBE DETAIL customers
""")

display(stats_df.select("minReaderVersion", "minWriterVersion", "numFiles"))

# COMMAND ----------

# 3. Table Properties
print("⚙️ Table Properties:")

# View and set Delta table properties
spark.sql("""
    ALTER TABLE customers SET TBLPROPERTIES (
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true'
    )
""")

properties = spark.sql("SHOW TBLPROPERTIES customers")
display(properties)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Key Takeaways
# MAGIC
# MAGIC In this notebook, you learned:
# MAGIC
# MAGIC ✅ **Delta Lake Basics**
# MAGIC - Creating Delta tables from DataFrames
# MAGIC - Reading and writing Delta format
# MAGIC
# MAGIC ✅ **ACID Transactions**
# MAGIC - Atomic writes guarantee data consistency
# MAGIC - Concurrent operations are isolated
# MAGIC
# MAGIC ✅ **Time Travel**
# MAGIC - Query historical versions with `versionAsOf` or `timestampAsOf`
# MAGIC - Audit changes with `DESCRIBE HISTORY`
# MAGIC - Rollback with `RESTORE`
# MAGIC
# MAGIC ✅ **Schema Evolution**
# MAGIC - Add new columns with `mergeSchema` option
# MAGIC - Maintain backward compatibility
# MAGIC
# MAGIC ✅ **MERGE Operations**
# MAGIC - Efficient UPSERT (update + insert)
# MAGIC - Critical for CDC pipelines
# MAGIC
# MAGIC ✅ **Optimization**
# MAGIC - `OPTIMIZE` for file compaction
# MAGIC - `ZORDER` for data co-location
# MAGIC - `VACUUM` for cleanup
# MAGIC
# MAGIC ## Next Steps
# MAGIC
# MAGIC Continue to Notebook 02: **ETL Pipeline with Medallion Architecture**

# COMMAND ----------

# Cleanup (optional - comment out if you want to keep the data)
# spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE")
# dbutils.fs.rm(table_path, recurse=True)
# print("✅ Cleanup complete")
