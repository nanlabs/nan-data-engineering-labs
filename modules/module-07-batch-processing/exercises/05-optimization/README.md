# Exercise 05: Performance Optimization

## 🎯 Objectives

Optimize batch jobs for maximum performance:
- Partition tuning
- Caching strategies
- Broadcast joins
- Predicate pushdown
- Data skew handling
- Performance benchmarking

## 📚 Conceptos

### Performance Bottlenecks

1. **Data Shuffle**: Moving data between executors (slow)
2. **Spills to Disk**: Out of memory (very slow)
3. **Data Skew**: Uneven partition sizes
4. **Small Files**: Too many small files (overhead)

### Optimization Strategies

```python
# ❌ Slow
df = spark.read.parquet("data/")
result = df.groupBy("category").sum("amount")

# ✅ Fast
df = spark.read.parquet("data/").repartition(200, "category")
result = df.groupBy("category").sum("amount")
```

## 🏋️ Exercises

### Parte 1: Partition Tuning

**Archivo**: `starter/partition_optimizer.py`

```python
class PartitionOptimizer:
    def __init__(self, spark: SparkSession):
        self.spark = spark

    def analyze_partitions(self, df: DataFrame) -> Dict[str, Any]:
        """
        Analyze partition distribution.

        Returns:
            {
                'num_partitions': int,
                'partition_sizes': List[int],
                'skew_ratio': float,  # max_size / avg_size
                'recommendation': str
            }
        """
        pass

    def repartition_by_size(
        self,
        df: DataFrame,
        target_partition_size_mb: int = 128
    ) -> DataFrame:
        """
        Repartition to achieve target partition size.

        Args:
            df: Input DataFrame
            target_partition_size_mb: Target size per partition

        Returns:
            Repartitioned DataFrame
        """
        pass

    def optimize_for_join(
        self,
        df: DataFrame,
        join_keys: List[str],
        num_partitions: Optional[int] = None
    ) -> DataFrame:
        """
        Repartition for efficient joins.

        Args:
            df: DataFrame
            join_keys: Columns to partition by
            num_partitions: Target partition count (auto if None)
        """
        pass
```

### Parte 2: Caching Strategy

**Archivo**: `starter/cache_manager.py`

```python
class CacheManager:
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.cached_dfs = {}

    def should_cache(self, df: DataFrame, reuse_count: int) -> bool:
        """
        Determine if DataFrame should be cached.

        Rules:
        - Cache if used > 1 time
        - Cache if > 100MB
        - Cache after expensive transformations
        """
        pass

    def cache_with_storage_level(
        self,
        df: DataFrame,
        storage_level: str = "MEMORY_AND_DISK"
    ) -> DataFrame:
        """
        Cache DataFrame with specific storage level.

        Levels:
        - MEMORY_ONLY: Fast but may evict
        - MEMORY_AND_DISK: Safe fallback
        - DISK_ONLY: For very large datasets
        """
        pass

    def unpersist_all(self):
        """Unpersist all cached DataFrames."""
        pass

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        pass
```

### Parte 3: Broadcast Joins

**Archivo**: `starter/broadcast_optimizer.py`

```python
class BroadcastOptimizer:
    def __init__(self, spark: SparkSession):
        self.spark = spark

    def analyze_join_candidates(
        self,
        df1: DataFrame,
        df2: DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze which table should be broadcast.

        Returns:
            {
                'df1_size_mb': float,
                'df2_size_mb': float,
                'recommendation': 'broadcast_df1' | 'broadcast_df2' | 'shuffle_join',
                'reason': str
            }
        """
        pass

    def broadcast_join(
        self,
        large_df: DataFrame,
        small_df: DataFrame,
        join_key: str,
        broadcast_threshold_mb: int = 10
    ) -> DataFrame:
        """
        Perform broadcast join if small table < threshold.

        Args:
            large_df: Large table
            small_df: Small table (will be broadcast)
            join_key: Join column
            broadcast_threshold_mb: Max size to broadcast
        """
        pass
```

### Parte 4: Data Skew Handler

**Archivo**: `starter/skew_handler.py`

```python
class SkewHandler:
    @staticmethod
    def detect_skew(
        df: DataFrame,
        partition_col: str,
        threshold: float = 3.0
    ) -> bool:
        """
        Detect data skew in partition column.

        Args:
            df: DataFrame
            partition_col: Column to check
            threshold: Skew ratio threshold (max/avg)

        Returns:
            True if skewed
        """
        pass

    @staticmethod
    def handle_skew_with_salting(
        df: DataFrame,
        skewed_col: str,
        num_salts: int = 10
    ) -> DataFrame:
        """
        Handle skew using salting technique.

        1. Add random salt to skewed keys
        2. Distribute across more partitions
        3. Aggregate results
        """
        pass

    @staticmethod
    def adaptive_repartition(
        df: DataFrame,
        col: str,
        skew_threshold: float = 3.0
    ) -> DataFrame:
        """
        Automatically handle skew if detected.
        """
        pass
```

### Parte 5: Performance Benchmark

**Archivo**: `starter/performance_benchmark.py`

```python
class PerformanceBenchmark:
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.results = []

    def benchmark_join_strategies(
        self,
        df1: DataFrame,
        df2: DataFrame,
        join_key: str
    ) -> pd.DataFrame:
        """
        Benchmark different join strategies:
        1. Default shuffle join
        2. Broadcast join
        3. Repartitioned join

        Returns DataFrame with results
        """
        pass

    def benchmark_partition_counts(
        self,
        df: DataFrame,
        operation: Callable,
        partition_counts: List[int]
    ) -> pd.DataFrame:
        """
        Benchmark operation with different partition counts.
        """
        pass

    def benchmark_caching_impact(
        self,
        df: DataFrame,
        operations: List[Callable]
    ) -> Dict[str, Any]:
        """
        Compare performance with/without caching.
        """
        pass

    def generate_report(self, output_path: str):
        """Generate HTML performance report."""
        pass
```

## 📊 Dataset

Use large dataset for performance testing:

```bash
cd ../../data/scripts

# Generate 50M records
python generate_transactions.py \
  --total-records 50000000 \
  --days 180
```

## ✅ Validation

```bash
# Run benchmarks
python solution/performance_benchmark.py

# Run tests
pytest test_optimization.py -v
```

## 💡 Hints

<details>
<summary>Hint 1: Calculate DataFrame size</summary>

```python
def estimate_size_mb(df):
    # Sample and estimate
    sample = df.limit(10000)
    sample_size = sample.rdd.map(lambda x: len(str(x))).sum()
    total_rows = df.count()
    estimated_size = (sample_size / 10000) * total_rows / (1024 * 1024)
    return estimated_size
```
</details>

<details>
<summary>Hint 2: Optimal partition count</summary>

```python
def calculate_optimal_partitions(
    data_size_mb: float,
    target_partition_size_mb: int = 128
) -> int:
    """
    Rule: 128MB per partition (sweet spot)
    """
    return max(1, int(data_size_mb / target_partition_size_mb))
```
</details>

<details>
<summary>Hint 3: Detect skew</summary>

```python
from pyspark.sql.functions import col, count

# Count by partition key
counts = df.groupBy("key").agg(count("*").alias("count"))

# Calculate skew
stats = counts.select(
    max("count").alias("max_count"),
    avg("count").alias("avg_count")
).collect()[0]

skew_ratio = stats["max_count"] / stats["avg_count"]

if skew_ratio > 3.0:
    print(f"SKEW DETECTED: {skew_ratio:.2f}x")
```
</details>

<details>
<summary>Hint 4: Salting for skew</summary>

```python
from pyspark.sql.functions import rand, lit

# Add salt to skewed keys
df_salted = df.withColumn(
    "salted_key",
    concat(col("skewed_key"), lit("_"), (rand() * 10).cast("int"))
)

# Aggregate with salted key
result = df_salted.groupBy("salted_key").agg(...)

# Remove salt from result
result = result.withColumn(
    "original_key",
    split(col("salted_key"), "_")[0]
)
```
</details>

## 🎓 Learning Outcomes

- ✅ Analizar y optimizar partitioning
- ✅ Implementar caching strategies efectivas
- ✅ Usar broadcast joins correctamente
- ✅ Detectar y manejar data skew
- ✅ Benchmark y comparar estrategias
- ✅ Optimizar queries con predicate pushdown

## 📚 Referencias

- [Spark Performance Tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
- [Spark UI Guide](https://spark.apache.org/docs/latest/web-ui.html)

## ➡️ Next

Continue with [Exercise 06: Production Batch Jobs](../06-production-jobs/)
