# Exercise 04: Batch ETL pipeline

## 🎯 Objectives

Construir un batch ETL pipeline completo con:
- Extract from multiple sources
- Transform with business logic
- Load to partitioned output
- Error handling y retry logic
- Monitoring y metrics
- Idempotent execution

## 📚 Conceptos

### Batch ETL pipeline

```
┌─────────────┐
│   Extract   │  Read from sources
└──────┬──────┘
       │
┌──────▼──────┐
│  Transform  │  Apply business logic
└──────┬──────┘
       │
┌──────▼──────┐
│    Load     │  Write to destination
└─────────────┘
```

### Idempotence

pipeline should produce same result if executed multiple times:

```python
# ✅ Idempotent (overwrite mode)
df.write.mode("overwrite").partitionBy("date").parquet(path)

# ❌ No idempotent (append mode sin dedup)
df.write.mode("append").parquet(path)  # Creates duplicates!
```

## 🏋️ Exercises

### Parte 1: ETL pipeline Class

**Archivo**: `starter/etl_pipeline.py`

```python
class BatchETLPipeline:
    def __init__(self, spark: SparkSession, config: Dict):
        """Initialize pipeline with Spark and configuration."""
        pass

    def extract(self) -> Dict[str, DataFrame]:
        """
        Extract data from sources.

        Returns:
            Dictionary of DataFrames by source name
        """
        pass

    def transform(self, sources: Dict[str, DataFrame]) -> DataFrame:
        """
        Apply business transformations.

        Args:
            sources: Dict of source DataFrames

        Returns:
            Transformed DataFrame
        """
        pass

    def load(self, df: DataFrame, output_path: str):
        """
        Load data to destination with partitioning.

        Args:
            df: DataFrame to write
            output_path: Output location
        """
        pass

    def run(self, execution_date: str):
        """
        Run complete ETL pipeline for execution date.

        Args:
            execution_date: Date to process (YYYY-MM-DD)
        """
        pass
```

### Parte 2: Business Transformations

**Archivo**: `starter/transformations.py`

Implementa transformaciones de negocio:

```python
class BusinessTransformations:
    @staticmethod
    def enrich_transactions(
        transactions: DataFrame,
        users: DataFrame,
        products: DataFrame
    ) -> DataFrame:
        """
        Enrich transactions with user and product data.

        Joins:
        - transactions + users (on user_id)
        - result + products (on product_id)

        Returns full enriched dataset
        """
        pass

    @staticmethod
    def calculate_metrics(df: DataFrame) -> DataFrame:
        """
        Calculate derived metrics:
        - discount_amount
        - final_price
        - user_lifetime_value
        - is_high_value (amount > $1000)
        """
        pass

    @staticmethod
    def apply_business_rules(df: DataFrame) -> DataFrame:
        """
        Apply business rules:
        - Filter failed transactions
        - Remove test users (email contains 'test')
        - Flag suspicious transactions (amount > $5000)
        - Standardize country codes
        """
        pass
```

### Parte 3: Error Handling

**Archivo**: `starter/error_handler.py`

```python
class PipelineErrorHandler:
    def __init__(self, logger):
        self.logger = logger
        self.errors = []

    def handle_extraction_error(self, source: str, error: Exception):
        """Handle errors during extraction."""
        pass

    def handle_transformation_error(self, error: Exception):
        """Handle errors during transformation."""
        pass

    def validate_output(self, df: DataFrame) -> bool:
        """
        Validate output before writing:
        - Non-empty DataFrame
        - Required columns present
        - No null values in critical columns
        - Amount values in valid range
        """
        pass

    def write_error_log(self, output_dir: str):
        """Write error log to file."""
        pass
```

### Parte 4: Metrics & Monitoring

**Archivo**: `starter/pipeline_metrics.py`

```python
class PipelineMetrics:
    def __init__(self):
        self.metrics = {}

    def track_extract(self, source: str, record_count: int, duration: float):
        """Track extraction metrics."""
        pass

    def track_transform(self, input_count: int, output_count: int, duration: float):
        """Track transformation metrics."""
        pass

    def track_load(self, record_count: int, bytes_written: int, duration: float):
        """Track load metrics."""
        pass

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        pass

    def write_metrics(self, output_path: str):
        """Write metrics to JSON file."""
        pass
```

### Parte 5: Configuration

**Archivo**: `config/pipeline_config.yaml`

```yaml
pipeline:
  name: daily_sales_pipeline
  version: 1.0.0

sources:
  transactions:
    path: data/raw/transactions
    format: parquet
    partition_columns: [year, month, day]

  users:
    path: data/raw/users.parquet
    format: parquet

  products:
    path: data/raw/products.parquet
    format: parquet

output:
  path: data/processed/enriched_transactions
  format: parquet
  partition_columns: [year, month]
  mode: overwrite
  compression: snappy

spark:
  app_name: daily_sales_etl
  executor_memory: 4g
  driver_memory: 2g
  shuffle_partitions: 200

validation:
  required_columns:
    - transaction_id
    - user_id
    - amount

  business_rules:
    max_amount: 10000
    min_amount: 0.01
```

## 📊 Dataset

Use full generated datasets:

```bash
cd ../../data/scripts

# Generate all data
python generate_transactions.py --total-records 10000000
python generate_users.py
python generate_products.py
```

## ✅ Validation

```bash
# Run pipeline
python solution/etl_pipeline.py --date 2024-03-07 --config config/pipeline_config.yaml

# Verify output
pytest test_batch_pipeline.py -v
```

## 💡 Hints

<details>
<summary>Hint 1: Load configuration</summary>

```python
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Access config
transactions_path = config['sources']['transactions']['path']
```
</details>

<details>
<summary>Hint 2: Idempotent writes</summary>

```python
# Overwrite specific partition
df.write \
  .mode("overwrite") \
  .partitionBy("year", "month", "day") \
  .parquet(output_path)

# Or use option for dynamic partition overwrite
df.write \
  .mode("overwrite") \
  .option("partitionOverwriteMode", "dynamic") \
  .partitionBy("year", "month") \
  .parquet(output_path)
```
</details>

<details>
<summary>Hint 3: Metrics tracking</summary>

```python
import time
import json

start_time = time.time()

# Extract
df = extract_data()
extract_duration = time.time() - start_time

# Track metrics
metrics = {
    'extract': {
        'duration_seconds': extract_duration,
        'records': df.count()
    }
}

# Write metrics
with open('metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
```
</details>

<details>
<summary>Hint 4: Data validation</summary>

```python
def validate_dataframe(df, required_columns, max_amount):
    # Check non-empty
    assert df.count() > 0, "Empty DataFrame"

    # Check required columns
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"Missing columns: {missing}"

    # Check business rules
    invalid_amounts = df.filter(
        (col("amount") < 0) | (col("amount") > max_amount)
    ).count()
    assert invalid_amounts == 0, f"Found {invalid_amounts} invalid amounts"

    return True
```
</details>

## 🎓 Learning Outcomes

- ✅ Design and implement complete batch ETL pipelines
- ✅ Aplicar business logic en transformaciones
- ✅ Implementar error handling robusto
- ✅ Trackear metrics y monitoring
- ✅ Garantizar idempotencia
- ✅ Usar configuration files

## 📚 Referencias

- [Spark ETL Patterns](https://spark.apache.org/docs/latest/sql-data-sources.html)
- [Pipeline Configuration Best Practices](https://12factor.net/config)

## ➡️ Next

Continue with [Exercise 05: Performance Optimization](../05-optimization/)
