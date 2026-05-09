<!-- markdownlint-disable MD033 -->

# Exercise 01: Batch Processing Basics

## 🎯 Objectives

Learn the fundamentals of batch processing:

- Process large files that do not fit in memory
- Implement efficient chunking
- Manage memory with pandas
- Track progress
- Perform batch aggregations

## 📚 Conceptos

### Chunking

When you have a 10GB file but only 8GB of RAM, you need **chunking**:

````python
# ❌ Malo: Intenta cargar todo
df = pd.read_csv('huge_file.csv')  # OOM Error!

# ✅ Bueno: Procesa en chunks
for chunk in pd.read_csv('huge_file.csv', chunksize=100000):
    process(chunk)  # Procesa 100K records cada vez
```text

### Memory-Efficient DataTypes

```python
# Default dtypes usan mucha memoria
df['user_id'] = int64  # 8 bytes por valor

# Optimize dtypes
df['user_id'] = int32  # 4 bytes (suficiente para IDs)
df['category'] = 'category'  # Muy eficiente para strings repetidos
```text

## 🏋️ Exercises

### Part 1: Basic Chunking

**Archivo**: `starter/batch_reader.py`

Implement a `BatchReader` that:

1. Reads CSV files in chunks
2. Processes each chunk
3. Aggregates the results

```python
class BatchReader:
    def __init__(self, filepath: str, chunksize: int = 100000):
        """Initialize batch reader."""
        pass

    def process_chunks(self, transform_fn) -> pd.DataFrame:
        """Process file in chunks and aggregate results."""
        pass
```text

**Testing**:

```bash
python starter/batch_reader.py
````

**Expected**:

- Read the file in 100K chunks
- Apply a transformation to each chunk
- Return the aggregated result

### Part 2: Memory Optimization

**Archivo**: `starter/memory_optimizer.py`

Implement memory optimizations:

1. Detect optimal data types
1. Convert dtypes automatically
1. Report memory savings

````python
class MemoryOptimizer:
    @staticmethod
    def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame dtypes to reduce memory usage."""
        pass

    @staticmethod
    def memory_usage_mb(df: pd.DataFrame) -> float:
        """Calculate DataFrame memory usage in MB."""
        pass
```text

**Testing**:

```bash
python starter/memory_optimizer.py
```text

**Expected**:

- int64 → int32 when possible
- object → category for repeated strings
- float64 → float32 when precision not critical
- Savings report (e.g. "Reduced from 500MB to 150MB")

### Part 3: Progress Tracking

**Archivo**: `starter/progress_tracker.py`

Add progress bars and logging:

```python
from tqdm import tqdm

class BatchProcessor:
    def process_with_progress(self, filepath: str):
        """Process file with progress bar."""
        pass
```text

**Features**:

- Progress bar with tqdm
- ETA (estimated time remaining)
- Records-per-second throughput
- Metrics logging

### Part 4: Batch Aggregations

**Archivo**: `starter/batch_aggregator.py`

Implement incremental aggregations:

```python
class BatchAggregator:
    def __init__(self):
        self.results = {}

    def add_chunk(self, chunk: pd.DataFrame):
        """Process chunk and update aggregations."""
        pass

    def get_results(self) -> Dict[str, Any]:
        """Get final aggregated results."""
        pass
````

**Aggregations to implement**:

- Total records
- Sum of amounts
- Count by category
- Average amount
- Min/max amounts

## 📊 Dataset

Use the generated transactions dataset:

````bash
# Generate a small dataset for testing
cd ../../data/scripts
python generate_transactions.py \
  --total-records 1000000 \
  --days 7 \
  --format csv \
  --partition-by none \
  --output-dir ../raw/transactions_small
```text

## ✅ Validation

```bash
# Run tests
pytest test_batch_basics.py -v

# Run con coverage
pytest test_batch_basics.py --cov=starter --cov-report=html
```text

## 💡 Hints

<details>
<summary>Hint 1: Basic Chunking</summary>

```python
def process_chunks(filepath, chunksize=100000):
    results = []

    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        # Process chunk
        result = process(chunk)
        results.append(result)

    # Combine results
    return pd.concat(results, ignore_index=True)
```text

</details>

<details>
<summary>Hint 2: Optimize dtypes</summary>

```python
def optimize_ints(df, col):
    col_min = df[col].min()
    col_max = df[col].max()

    if col_min >= 0:
        if col_max < 255:
            return 'uint8'
        elif col_max < 65535:
            return 'uint16'
        elif col_max < 4294967295:
            return 'uint32'
    else:
        if col_min > -128 and col_max < 127:
            return 'int8'
        elif col_min > -32768 and col_max < 32767:
            return 'int16'
        elif col_min > -2147483648 and col_max < 2147483647:
            return 'int32'

    return 'int64'
````

</details>

<details>
<summary>Hint 3: Progress bar</summary>

````python
from tqdm import tqdm

# Get total lines
total_lines = sum(1 for _ in open(filepath)) - 1  # minus header

chunks = pd.read_csv(filepath, chunksize=chunksize)

with tqdm(total=total_lines, desc="Processing") as pbar:
    for chunk in chunks:
        process(chunk)
        pbar.update(len(chunk))
```text

</details>

<details>
<summary>Hint 4: Incremental aggregation</summary>

```python
class Aggregator:
    def __init__(self):
        self.count = 0
        self.sum = 0
        self.category_counts = {}

    def add_chunk(self, chunk):
        self.count += len(chunk)
        self.sum += chunk['amount'].sum()

        # Update category counts
        chunk_counts = chunk['category'].value_counts()
        for cat, count in chunk_counts.items():
            self.category_counts[cat] = self.category_counts.get(cat, 0) + count
```text

</details>

## 🎓 Learning Outcomes

After completing this exercise, you will know:

- ✅ How to process files > RAM with chunking
- ✅ Optimize memory usage with the right dtypes
- ✅ Implement professional progress tracking
- ✅ Perform incremental aggregations efficiently

## 📚 Referencias

- [Pandas Chunking](https://pandas.pydata.org/docs/user_guide/io.html#iterating-through-files-chunk-by-chunk)
- [Memory Usage](https://pandas.pydata.org/docs/user_guide/scale.html#scaling-to-large-datasets)
- [tqdm Progress Bars](https://tqdm.github.io/)

## ➡️ Next

Continue with [Exercise 02: Partitioning Strategies](../02-partitioning/)
````
