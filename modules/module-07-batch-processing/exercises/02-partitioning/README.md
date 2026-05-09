# Exercise 02: Data Partitioning Strategies

## 🎯 Objectives

Learn estrategias de particionamiento para batch processing eficiente:

- Particionamiento por fecha (time-based)
- Particionamiento por rango (range-based)
- Particionamiento por hash (hash-based)
- Partition pruning y query optimization

## 📚 Conceptos

### Why Partition?

1. **Performance**: Read solo particiones relevantes (partition pruning)
1. **Parallelization**: Process partitions in parallel
1. **Maintainability**: Delete old data easily
1. **Cost Optimization**: Reduce data scanned en cloud

### Partition Layout

````text
data/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   └── file.parquet
│   │   └── day=02/
│   └── month=02/
```text

## 🏋️ Exercises

### Parte 1: Date Partitioning

**Archivo**: `starter/date_partitioner.py`

Implement date-based partitioning:

```python
class DatePartitioner:
    def write_partitioned(
        self,
        df: pd.DataFrame,
        output_dir: str,
        date_column: str = 'timestamp'
    ):
        """Write DataFrame partitioned by date."""
        pass

    def read_partition(
        self,
        input_dir: str,
        year: int,
        month: int,
        day: int
    ) -> pd.DataFrame:
        """Read specific date partition."""
        pass

    def read_date_range(
        self,
        input_dir: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Read multiple partitions for date range."""
        pass
```text

**Features**:

- Extrae year/month/day de timestamp
- Create estructura de directorios
- Write Parquet por partition
- Read specific partitions

### Parte 2: Range Partitioning

**Archivo**: `starter/range_partitioner.py`

Partition by value ranges:

```python
class RangePartitioner:
    def __init__(self, ranges: List[Tuple[float, float, str]]):
        """
        Initialize with ranges.

        Example:
            ranges = [
                (0, 100, 'low'),
                (100, 1000, 'medium'),
                (1000, float('inf'), 'high')
            ]
        """
        pass

    def partition_value(self, value: float) -> str:
        """Determine partition for value."""
        pass

    def write_partitioned(
        self,
        df: pd.DataFrame,
        column: str,
        output_dir: str
    ):
        """Write DataFrame partitioned by ranges."""
        pass
````

**Use cases**:

- Transaction amounts (small/medium/large)
- User ages (young/adult/senior)
- Product prices

### Parte 3: Hash Partitioning

**Archivo**: `starter/hash_partitioner.py`

Partition using hash function:

````python
class HashPartitioner:
    def __init__(self, num_partitions: int = 10):
        """Initialize with number of partitions."""
        pass

    def hash_key(self, key: str) -> int:
        """Hash key to partition number."""
        pass

    def write_partitioned(
        self,
        df: pd.DataFrame,
        key_column: str,
        output_dir: str
    ):
        """Write DataFrame partitioned by hash."""
        pass
```text

**Benefits**:

- Uniform distribution
- Good for joins (co-located keys)
- Avoids data skew

### Parte 4: Partition Pruning Benchmark

**Archivo**: `starter/partition_benchmark.py`

Compare performance:

```python
def benchmark_partitioning():
    """Compare non-partitioned vs partitioned reads."""

    # Write same data both ways
    # 1. Single large file
    # 2. Date partitioned

    # Benchmark queries:
    # - Read all
    # - Read specific date
    # - Read date range

    # Report speedup
    pass
```text

## 📊 Dataset

Use partitioned transactions:

```bash
cd ../../data/scripts

# Generate partitioned data
python generate_transactions.py \
  --total-records 5000000 \
  --days 30 \
  --partition-by date \
  --output-dir ../raw/transactions_partitioned
```text

## ✅ Validation

```bash
pytest test_partitioning.py -v
````

## 💡 Hints

<details>
<summary>Hint 1: Extracting date components</summary>

````python
# Pandas
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['year'] = df['timestamp'].dt.year
df['month'] = df['timestamp'].dt.month
df['day'] = df['timestamp'].dt.day

# Group by date components
for (year, month, day), group in df.groupby(['year', 'month', 'day']):
    # Write group to partition
    partition_dir = f"year={year}/month={month:02d}/day={day:02d}"
    group.to_parquet(f"{output_dir}/{partition_dir}/data.parquet")
```text

</details>

<details>
<summary>Hint 2: Range partitioning</summary>

```python
def partition_value(value, ranges):
    for min_val, max_val, name in ranges:
        if min_val <= value < max_val:
            return name
    return 'unknown'

# Apply partitioning
df['partition'] = df['amount'].apply(lambda x: partition_value(x, ranges))

# Write each partition
for partition_name, group in df.groupby('partition'):
    group.to_parquet(f"{output_dir}/{partition_name}/data.parquet")
```text

</details>

<details>
<summary>Hint 3: Hash partitioning</summary>

```python
import hashlib

def hash_partition(key, num_partitions):
    # Use hashlib for consistent hashing
    hash_val = int(hashlib.md5(str(key).encode()).hexdigest(), 16)
    return hash_val % num_partitions

# Apply
df['partition'] = df['user_id'].apply(lambda x: hash_partition(x, 10))
```text

</details>

## 🎓 Learning Outcomes

- ✅ Implement date, range, and hash partitioning
- ✅ Understand partition pruning benefits
- ✅ Choose the right partitioning strategy
- ✅ Optimize queries using partitioning

## 📚 Referencias

- [Parquet Partitioning](https://arrow.apache.org/docs/python/parquet.html#partitioned-datasets)
- [Spark Partitioning](https://spark.apache.org/docs/latest/sql-performance-tuning.html#partition-discovery)

## ➡️ Next

Continue with [Exercise 03: PySpark Basics](../03-pyspark-basics/)
````
