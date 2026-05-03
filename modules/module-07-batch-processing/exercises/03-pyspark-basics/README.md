# Exercise 03: PySpark Basics

## 🎯 Objectives

Introduction to Apache Spark for distributed batch processing:
- Setup de SparkSession
- DataFrames y transformations
- Actions y lazy evaluation
- Joins y aggregations distribuidas
- Basic performance optimization

## 📚 Conceptos

### Apache Spark

Spark is the leading framework for big data processing:
- **Distributed**: Procesa TB de datos en cluster
- **In-Memory**: 100x faster than MapReduce
- **Lazy Evaluation**: Optimiza execution plans
- **Fault Tolerant**: Automatic recovery

### DataFrame API

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("app").getOrCreate()

# Read
df = spark.read.parquet("data/")

# Transform (lazy)
df_filtered = df.filter(df.amount > 100)
df_grouped = df_filtered.groupBy("category").sum("amount")

# Action (executes)
df_grouped.show()
```

## 🏋️ Exercises

### Parte 1: Spark Session Setup

**Archivo**: `starter/spark_setup.py`

```python
class SparkManager:
    @staticmethod
    def create_session(
        app_name: str = "BatchProcessing",
        master: str = "local[*]",
        config: Dict[str, str] = None
    ) -> SparkSession:
        """Create configured Spark session."""
        pass

    @staticmethod
    def stop_session(spark: SparkSession):
        """Stop Spark session and cleanup."""
        pass
```

**Configuraciones importantes**:
- `spark.executor.memory`: Memoria por executor
- `spark.driver.memory`: Memoria del driver
- `spark.sql.shuffle.partitions`: Partitions para shuffle
- `spark.default.parallelism`: Parallelism level

### Parte 2: DataFrame Operations

**Archivo**: `starter/spark_operations.py`

Implementa operaciones comunes:

```python
class SparkOperations:
    def __init__(self, spark: SparkSession):
        self.spark = spark

    def filter_transactions(
        self,
        df: DataFrame,
        min_amount: float
    ) -> DataFrame:
        """Filter transactions by minimum amount."""
        pass

    def aggregate_by_category(
        self,
        df: DataFrame
    ) -> DataFrame:
        """Aggregate amounts by category."""
        pass

    def join_with_users(
        self,
        transactions: DataFrame,
        users: DataFrame
    ) -> DataFrame:
        """Join transactions with user data."""
        pass

    def window_top_n(
        self,
        df: DataFrame,
        partition_col: str,
        order_col: str,
        n: int = 10
    ) -> DataFrame:
        """Get top N per partition using window function."""
        pass
```

### Parte 3: Performance Optimization

**Archivo**: `starter/spark_optimization.py`

```python
class SparkOptimizer:
    @staticmethod
    def cache_dataframe(df: DataFrame) -> DataFrame:
        """Cache DataFrame for reuse."""
        pass

    @staticmethod
    def repartition_for_join(
        df: DataFrame,
        num_partitions: int,
        key_column: str
    ) -> DataFrame:
        """Repartition for efficient joins."""
        pass

    @staticmethod
    def broadcast_small_table(
        large_df: DataFrame,
        small_df: DataFrame,
        join_key: str
    ) -> DataFrame:
        """Broadcast join for small tables."""
        pass

    @staticmethod
    def explain_plan(df: DataFrame):
        """Show execution plan."""
        pass
```

### Parte 4: Batch pipeline

**Archivo**: `starter/spark_pipeline.py`

Crea un batch pipeline completo:

```python
class SparkBatchPipeline:
    def __init__(self, spark: SparkSession):
        self.spark = spark

    def run(
        self,
        transactions_path: str,
        users_path: str,
        output_path: str
    ):
        """
        Run complete batch pipeline:
        1. Read transactions and users
        2. Join data
        3. Filter and aggregate
        4. Write results
        """
        pass
```

**pipeline steps**:
1. Read partitioned transactions
2. Read users
3. Join on user_id
4. Filter completed transactions
5. Aggregate by country and category
6. Write results as Parquet

## 📊 Dataset

Use generated data:

```bash
# Ensure data is generated
cd ../../data/scripts
python generate_transactions.py
python generate_users.py
```

## ✅ Validation

```bash
pytest test_pyspark_basics.py -v
```

## 💡 Hints

<details>
<summary>Hint 1: SparkSession creation</summary>

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("BatchProcessing") \
    .master("local[*]") \
    .config("spark.executor.memory", "2g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "100") \
    .getOrCreate()
```
</details>

<details>
<summary>Hint 2: DataFrame operations</summary>

```python
from pyspark.sql.functions import col, sum, count, avg

# Filter
df_filtered = df.filter(col("amount") > 100)

# Aggregate
df_agg = df.groupBy("category").agg(
    sum("amount").alias("total"),
    count("*").alias("count"),
    avg("amount").alias("avg")
)

# Join
df_joined = df1.join(df2, "user_id", "inner")
```
</details>

<details>
<summary>Hint 3: Window functions</summary>

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, dense_rank

# Define window
window = Window.partitionBy("category").orderBy(col("amount").desc())

# Apply window function
df_ranked = df.withColumn("rank", rank().over(window))

# Get top N
df_top_n = df_ranked.filter(col("rank") <= 10)
```
</details>

<details>
<summary>Hint 4: Broadcast join</summary>

```python
from pyspark.sql.functions import broadcast

# Broadcast small table (< 10MB)
df_result = large_df.join(
    broadcast(small_df),
    "join_key"
)
```
</details>

## 🎓 Learning Outcomes

- ✅ Configurar y usar Spark Sessions
- ✅ Realizar transformations y actions en DataFrames
- ✅ Implementar joins y aggregations distribuidas
- ✅ Optimizar performance con caching y broadcast
- ✅ Construir batch pipelines con Spark

## 📚 Referencias

- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [DataFrame API](https://spark.apache.org/docs/latest/sql-getting-started.html)

## ➡️ Next

Continue with [Exercise 04: Batch ETL Pipeline](../04-batch-pipeline/)
