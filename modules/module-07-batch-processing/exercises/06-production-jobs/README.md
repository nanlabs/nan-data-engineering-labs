# Exercise 06: Production Batch Jobs

## 🎯 Objectives

Prepare batch jobs for production:

- Job scheduling y orchestration
- Monitoring y alerting
- Failure recovery y retry logic
- Data quality checks
- SLA management
- Deployment best practices

## 📚 Conceptos

### Production Requirements

✅ **Reliability**: Job debe completar exitosamente
✅ **Observability**: Logs, metrics, alerts
✅ **Recoverability**: Falla → retry → success
✅ **Maintainability**: Easy to debug and modify
✅ **Performance**: Cumple SLA

### Production Job Lifecycle

```text
Schedule → Start → Monitor → Complete → Validate → Alert
                ↓ Fail
            Retry → Success / Dead Letter
```text

## 🏋️ Exercises

### Parte 1: Production Job Framework

**Archivo**: `starter/production_job.py`

```python
class ProductionBatchJob:
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.metrics = {}
        self.status = "NOT_STARTED"

    def setup(self):
        """
        Setup resources:
        - Initialize Spark session
        - Validate config
        - Check input data exists
        - Setup logging
        """
        pass

    def run(self, execution_date: str) -> bool:
        """
        Run job with error handling.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.status = "RUNNING"

            # Execute pipeline
            self.extract()
            self.transform()
            self.load()

            # Validate output
            self.validate_output()

            self.status = "SUCCESS"
            return True

        except Exception as e:
            self.status = "FAILED"
            self.handle_failure(e)
            return False

        finally:
            self.cleanup()

    def validate_output(self):
        """
        Validate output data:
        - Record count within expected range
        - Required columns present
        - Data quality checks pass
        - File sizes reasonable
        """
        pass

    def cleanup(self):
        """
        Cleanup resources:
        - Stop Spark session
        - Close connections
        - Write metrics
        - Archive logs
        """
        pass
```text

### Parte 2: Retry Logic

**Archivo**: `starter/retry_handler.py`

```python
class RetryHandler:
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        max_backoff: int = 300
    ):
        """
        Initialize retry handler with exponential backoff.

        Args:
            max_retries: Maximum retry attempts
            backoff_factor: Multiplier for backoff (2.0 = exponential)
            max_backoff: Maximum backoff time in seconds
        """
        pass

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.

        Backoff schedule:
        - Attempt 1: immediate
        - Attempt 2: wait 2 seconds
        - Attempt 3: wait 4 seconds
        - Attempt 4: wait 8 seconds
        """
        pass

    def is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if error should trigger retry.

        Retryable:
        - Network errors
        - Timeout errors
        - Temporary resource unavailable

        Not retryable:
        - Data validation errors
        - Schema mismatches
        - Permission denied
        """
        pass
```

### Parte 3: Job Monitoring

**Archivo**: `starter/job_monitor.py`

```python
class JobMonitor:
    def __init__(self, job_name: str):
        self.job_name = job_name
        self.start_time = None
        self.metrics = {}

    def start(self):
        """Mark job start and initialize metrics."""
        pass

    def track_stage(
        self,
        stage_name: str,
        records_processed: int,
        duration: float
    ):
        """Track individual stage metrics."""
        pass

    def check_sla(self, sla_minutes: int) -> bool:
        """
        Check if job is within SLA.

        Returns:
            True if within SLA, False otherwise
        """
        pass

    def send_alert(
        self,
        severity: str,
        message: str,
        details: Dict = None
    ):
        """
        Send alert to monitoring system.

        Args:
            severity: INFO, WARNING, ERROR, CRITICAL
            message: Alert message
            details: Additional context
        """
        pass

    def write_metrics_to_cloudwatch(self):
        """Write metrics to AWS CloudWatch (or equivalent)."""
        pass

    def generate_run_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive run report.

        Returns:
            {
                'job_name': str,
                'execution_date': str,
                'status': str,
                'duration_minutes': float,
                'records_processed': int,
                'data_size_gb': float,
                'sla_met': bool,
                'errors': List[str]
            }
        """
        pass
```text

### Parte 4: Data Quality Checks

**Archivo**: `starter/quality_checks.py`

```python
class DataQualityChecker:
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.checks = []

    def check_record_count(
        self,
        df: DataFrame,
        min_count: int,
        max_count: Optional[int] = None
    ) -> bool:
        """Verify record count is within expected range."""
        pass

    def check_null_values(
        self,
        df: DataFrame,
        columns: List[str],
        max_null_pct: float = 0.01
    ) -> bool:
        """Check null percentage in critical columns."""
        pass

    def check_data_freshness(
        self,
        df: DataFrame,
        date_column: str,
        max_age_hours: int = 24
    ) -> bool:
        """Verify data is fresh (not too old)."""
        pass

    def check_duplicates(
        self,
        df: DataFrame,
        key_columns: List[str],
        max_dup_pct: float = 0.001
    ) -> bool:
        """Check for duplicate records."""
        pass

    def check_value_ranges(
        self,
        df: DataFrame,
        checks: Dict[str, Tuple[float, float]]
    ) -> bool:
        """
        Check values are within valid ranges.

        Example:
            checks = {
                'amount': (0, 10000),
                'age': (18, 100)
            }
        """
        pass

    def run_all_checks(self, df: DataFrame) -> Dict[str, bool]:
        """Run all configured checks and return results."""
        pass
```text

### Parte 5: Job Configuration

**Archivo**: `config/production_job.yaml`

```yaml
job:
  name: daily_sales_batch
  version: 2.0.0
  owner: data-engineering-team
  schedule: "0 2 * * *"  # 2 AM daily
  sla_minutes: 240  # 4 hours
  retry:
    max_attempts: 3
    backoff_seconds: 60

spark:
  app_name: production_sales_batch
  master: yarn
  deploy_mode: cluster
  executor_memory: 8g
  executor_cores: 4
  num_executors: 10
  driver_memory: 4g

sources:
  transactions:
    path: s3://bucket/raw/transactions/
    format: parquet
  users:
    path: s3://bucket/master/users/
    format: parquet

output:
  path: s3://bucket/processed/daily_sales/
  format: parquet
  partition_by: [year, month, day]
  mode: overwrite

quality_checks:
  record_count:
    min: 100000
    max: 50000000

  null_checks:
    columns: [transaction_id, user_id, amount]
    max_null_percent: 0.1

  value_ranges:
    amount:
      min: 0.01
      max: 10000.00

monitoring:
  cloudwatch_namespace: DataEngineering/BatchJobs
  slack_webhook: https://hooks.slack.com/services/xxx
  email_alerts: [team@company.com]

alerts:
  - condition: job_failed
    severity: CRITICAL
    notify: [slack, email]

  - condition: sla_exceeded
    severity: WARNING
    notify: [slack]

  - condition: quality_check_failed
    severity: ERROR
    notify: [slack, email]
```text

## 📊 Testing

### Local Testing

```bash
# Test with small dataset
python production_job.py \
  --config config/production_job.yaml \
  --date 2024-03-07 \
  --env local \
  --dry-run
```

### Production Deployment

```bash
# Submit to cluster
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --num-executors 10 \
  --executor-memory 8g \
  --executor-cores 4 \
  --driver-memory 4g \
  --conf spark.sql.shuffle.partitions=200 \
  production_job.py \
  --config config/production_job.yaml \
  --date 2024-03-07
```text

## ✅ Validation

```bash
pytest test_production_jobs.py -v
```text

## 💡 Hints

<details>
<summary>Hint 1: Exponential backoff</summary>

```python
import time

def execute_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait_time = min(2 ** attempt, 300)  # Cap at 5 min
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
            time.sleep(wait_time)
```text

</details>

<details>
<summary>Hint 2: SLA monitoring</summary>

```python
import time

start = time.time()

# Run job
run_pipeline()

duration_minutes = (time.time() - start) / 60

if duration_minutes > SLA_MINUTES:
    send_alert(
        severity="WARNING",
        message=f"Job exceeded SLA: {duration_minutes:.1f}min > {SLA_MINUTES}min"
    )
```

</details>

<details>
<summary>Hint 3: Quality checks</summary>

```python
def validate_output(df, config):
    errors = []

    # Check count
    count = df.count()
    if count < config['min_count']:
        errors.append(f"Too few records: {count}")

    # Check nulls
    for col in config['required_columns']:
        null_count = df.filter(df[col].isNull()).count()
        if null_count > 0:
            errors.append(f"Nulls in {col}: {null_count}")

    if errors:
        raise ValueError(f"Quality checks failed: {errors}")
```text

</details>

<details>
<summary>Hint 4: Metrics publishing</summary>

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metrics(metrics):
    cloudwatch.put_metric_data(
        Namespace='DataEngineering/BatchJobs',
        MetricData=[
            {
                'MetricName': 'RecordsProcessed',
                'Value': metrics['records'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'Duration',
                'Value': metrics['duration_minutes'],
                'Unit': 'Minutes'
            }
        ]
    )
```text

</details>

## 🎓 Learning Outcomes

- ✅ Design production-ready jobs
- ✅ Implementar retry logic robusto
- ✅ Configurar monitoring y alerting
- ✅ Implementar data quality checks
- ✅ Manejar SLAs efectivamente
- ✅ Deploy to production clusters

## 📚 Referencias

- [Production Spark Best Practices](https://spark.apache.org/docs/latest/tuning.html)
- [AWS EMR Best Practices](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan.html)
- [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/)

## 🎉 Module Complete

Has completed todos los exercises de Batch Processing. Ahora dominas:

- Batch processing fundamentals
- Data partitioning strategies
- PySpark for distributed computing
- Complete ETL pipelines
- Performance optimization
- Production deployment

## ➡️ Next Module

Continue with **Module 08: Streaming Basics**
