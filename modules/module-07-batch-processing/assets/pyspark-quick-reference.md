# PySpark Quick Reference

## 🚀 Session Creation

```python
from pyspark.sql import SparkSession

# Local mode
spark = SparkSession.builder \
    .appName("MyApp") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()

# Cluster mode (YARN)
spark = SparkSession.builder \
    .appName("MyApp") \
    .master("yarn") \
    .config("spark.executor.memory", "8g") \
    .config("spark.executor.cores", "4") \
    .config("spark.executor.instances", "10") \
    .getOrCreate()
```

## 📖 Reading Data

```python
# Parquet (recommended)
df = spark.read.parquet("s3://bucket/data/")

# CSV
df = spark.read.csv("path/to/file.csv", header=True, inferSchema=True)

# JSON
df = spark.read.json("path/to/file.json")

# With schema
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

schema = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), True)
])

df = spark.read.schema(schema).parquet("data/")

# Partitioned data
df = spark.read.parquet("data/year=2024/month=03/")
```

## 🔍 DataFrame Operations

### Selection & Filtering

```python
from pyspark.sql.functions import col

# Select columns
df.select("name", "age")
df.select(col("name"), col("age"))

# Filter rows
df.filter(df.age > 30)
df.filter(col("age") > 30)
df.where(col("status") == "active")

# Multiple conditions
df.filter((col("age") > 30) & (col("status") == "active"))
df.filter((col("age") < 18) | (col("age") > 65))
```

### Transformations

```python
from pyspark.sql.functions import *

# Add column
df.withColumn("age_plus_10", col("age") + 10)

# Rename column
df.withColumnRenamed("old_name", "new_name")

# Drop column
df.drop("column_to_remove")

# Cast type
df.withColumn("age", col("age").cast("integer"))
```

### Aggregations

```python
# Simple aggregation
df.groupBy("category").count()
df.groupBy("category").sum("amount")
df.groupBy("category").avg("amount")

# Multiple aggregations
df.groupBy("category").agg(
    sum("amount").alias("total"),
    count("*").alias("count"),
    avg("amount").alias("average"),
    min("amount").alias("min_val"),
    max("amount").alias("max_val")
)

# Global aggregation
df.agg(
    sum("amount").alias("total"),
    count("*").alias("count")
)
```

### Joins

```python
# Inner join
df1.join(df2, "user_id")
df1.join(df2, df1.user_id == df2.id)

# Left join
df1.join(df2, "user_id", "left")

# Right join
df1.join(df2, "user_id", "right")

# Outer join
df1.join(df2, "user_id", "outer")

# Multiple keys
df1.join(df2, ["user_id", "date"])

# Broadcast join (for small tables)
from pyspark.sql.functions import broadcast
df1.join(broadcast(df2), "id")
```

### Window Functions

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, dense_rank, lag, lead

# Define window
window = Window.partitionBy("category").orderBy(col("amount").desc())

# Ranking
df.withColumn("rank", rank().over(window))
df.withColumn("row_num", row_number().over(window))

# Running total
window_running = Window.partitionBy("category").orderBy("date") \
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)

df.withColumn("running_total", sum("amount").over(window_running))

# Moving average (3-day)
window_moving = Window.partitionBy("category").orderBy("date") \
    .rowsBetween(-2, 0)

df.withColumn("moving_avg", avg("amount").over(window_moving))

# Lag/Lead
df.withColumn("prev_amount", lag("amount", 1).over(window))
df.withColumn("next_amount", lead("amount", 1).over(window))
```

## 💾 Writing Data

```python
# Parquet
df.write.parquet("output/", mode="overwrite")

# Partitioned
df.write.partitionBy("year", "month").parquet("output/")

# With compression
df.write \
    .option("compression", "snappy") \
    .parquet("output/")

# CSV
df.write.csv("output/", header=True, mode="overwrite")

# Modes: overwrite, append, ignore, error
```

## ⚡ Performance Optimization

### Caching

```python
# Cache in memory
df_cached = df.cache()

# Persist with storage level
from pyspark import StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK)

# Unpersist
df.unpersist()
```

### Repartitioning

```python
# Increase partitions (triggers shuffle)
df.repartition(200)

# Repartition by column
df.repartition("category")

# Decrease partitions (no shuffle)
df.coalesce(10)
```

### Broadcast

```python
from pyspark.sql.functions import broadcast

# Broadcast small table
df_large.join(broadcast(df_small), "id")

# Set broadcast threshold (default 10MB)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 10485760)
```

## 🔍 Inspecting Data

```python
# Show data
df.show()
df.show(20, truncate=False)

# Schema
df.printSchema()
df.dtypes

# Count
df.count()

# Describe
df.describe().show()

# Sample
df.sample(0.1).show()  # 10% sample
df.limit(100).show()

# Collect (bring to driver - use with caution!)
rows = df.collect()
first_row = df.first()
rows = df.take(10)
```

## 🛠️ Useful Functions

### String Operations

```python
from pyspark.sql.functions import *

# Upper/lower
df.withColumn("upper", upper("name"))
df.withColumn("lower", lower("name"))

# Trim
df.withColumn("trimmed", trim("name"))

# Substring
df.withColumn("first_3", substring("name", 1, 3))

# Concat
df.withColumn("full_name", concat(col("first"), lit(" "), col("last")))

# Replace
df.withColumn("cleaned", regexp_replace("text", "[^a-zA-Z]", ""))

# Split
df.withColumn("parts", split("text", ","))
```

### Date/Time Operations

```python
from pyspark.sql.functions import *

# Current timestamp
df.withColumn("now", current_timestamp())

# Parse date
df.withColumn("date", to_date("date_string", "yyyy-MM-dd"))

# Parse timestamp
df.withColumn("ts", to_timestamp("ts_string", "yyyy-MM-dd HH:mm:ss"))

# Extract components
df.withColumn("year", year("timestamp"))
df.withColumn("month", month("timestamp"))
df.withColumn("day", dayofmonth("timestamp"))
df.withColumn("hour", hour("timestamp"))

# Date arithmetic
df.withColumn("tomorrow", date_add("date", 1))
df.withColumn("yesterday", date_sub("date", 1))

# Date diff
df.withColumn("days_ago", datediff(current_date(), "date"))
```

### Null Handling

```python
from pyspark.sql.functions import *

# Fill nulls
df.fillna(0)  # All columns
df.fillna({"age": 0, "name": "Unknown"})  # Specific columns

# Drop nulls
df.dropna()  # Any null
df.dropna(how="all")  # All nulls
df.dropna(subset=["age", "name"])  # Specific columns

# Null checks
df.filter(col("age").isNull())
df.filter(col("age").isNotNull())

# Coalesce (first non-null)
df.withColumn("value", coalesce("col1", "col2", lit(0)))
```

### Conditional Logic

```python
from pyspark.sql.functions import when, col

# When/otherwise
df.withColumn("category",
    when(col("age") < 18, "minor")
    .when(col("age") < 65, "adult")
    .otherwise("senior")
)

# Case when
from pyspark.sql.functions import expr

df.withColumn("status", expr("""
    CASE
        WHEN amount > 1000 THEN 'high'
        WHEN amount > 100 THEN 'medium'
        ELSE 'low'
    END
"""))
```

## 📊 SQL Interface

```python
# Register as temp view
df.createOrReplaceTempView("transactions")

# SQL query
result = spark.sql("""
    SELECT category, SUM(amount) as total
    FROM transactions
    WHERE status = 'completed'
    GROUP BY category
    ORDER BY total DESC
""")
```

## 🐛 Debugging

```python
# Explain execution plan
df.explain()
df.explain(True)  # Extended

# Show DAG
df.rdd.toDebugString()

# Check partitions
df.rdd.getNumPartitions()
```

## ⚙️ Configuration

```python
# Get config
spark.conf.get("spark.sql.shuffle.partitions")

# Set config
spark.conf.set("spark.sql.shuffle.partitions", "200")

# Important configs
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
```

## 🎯 Best Practices

1. **Use Parquet**: Faster and smaller than CSV
2. **Partition data**: By date or frequently filtered columns
3. **Broadcast small tables**: < 10MB
4. **Cache wisely**: Only reused DataFrames
5. **Avoid collect()**: Use on small results only
6. **Optimize partitions**: 128MB - 1GB per partition
7. **Use column pruning**: Select only needed columns
8. **Predicate pushdown**: Filter early
9. **Check execution plans**: Use explain()
10. **Monitor Spark UI**: Identify bottlenecks

---

**Keep this reference handy when writing PySpark code!**
