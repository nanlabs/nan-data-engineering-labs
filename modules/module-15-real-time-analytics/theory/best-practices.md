# Real-Time Analytics: Production Best Practices

## Table of Contents

1. [Performance Optimization](#performance-optimization)
2. [Cost Management](#cost-management)
3. [Monitoring & Alerting](#monitoring--alerting)
4. [Error Handling & Reliability](#error-handling--reliability)
5. [Testing Strategies](#testing-strategies)
6. [Deployment Best Practices](#deployment-best-practices)
7. [Security Hardening](#security-hardening)
8. [Operational Excellence](#operational-excellence)

---

## Performance Optimization

### 1. Kinesis Shard Management

**Right-Sizing Shards**:
```
Throughput needed: 10 MB/sec writes, 20 MB/sec reads

Shard capacity:
- Write: 1 MB/sec per shard
- Read: 2 MB/sec per shard

Required shards:
- Write: 10 MB/sec ÷ 1 MB/sec = 10 shards
- Read: 20 MB/sec ÷ 2 MB/sec = 10 shards

Choose: 10 shards (max of both)
```

**Shard Splitting Strategy**:
```python
import boto3

def auto_scale_kinesis(stream_name, target_util=0.7):
    client = boto3.client('kinesis')

    # Get metrics from CloudWatch
    metrics = get_shard_metrics(stream_name)

    for shard_id, utilization in metrics.items():
        if utilization > target_util:
            # Split hot shard
            client.split_shard(
                StreamName=stream_name,
                ShardToSplit=shard_id,
                NewStartingHashKey=calculate_midpoint(shard_id)
            )
        elif utilization < 0.3 and can_merge(shard_id):
            # Merge cold shards
            client.merge_shards(
                StreamName=stream_name,
                ShardToMerge=shard_id,
                AdjacentShardToMerge=find_adjacent(shard_id)
            )
```

**Partition Key Strategy**:
```python
# Bad: All to one shard
partition_key = "static-key"

# Good: Distribute evenly
partition_key = hashlib.md5(user_id.encode()).hexdigest()

# Better: Composite key for related events
partition_key = f"{user_id}#{session_id}"
```

### 2. Flink Application Performance

**Parallelism Configuration**:
```python
env = StreamExecutionEnvironment.get_execution_environment()

# Set parallelism based on workload
env.set_parallelism(8)  # 8 parallel tasks

# Per-operator parallelism
stream \
    .map(transform).set_parallelism(4) \
    .key_by(lambda x: x['key']) \
    .window(...) \
    .aggregate(agg_function).set_parallelism(8)
```

**State Backend Optimization**:
```python
from pyflink.datastream.state_backend import RocksDBStateBackend

# Use RocksDB for large state
state_backend = RocksDBStateBackend("s3://my-bucket/checkpoints", True)
env.set_state_backend(state_backend)

# Tune RocksDB
state_backend.set_db_storage_path("/tmp/rocksdb")
state_backend.set_predefined_options("SPINNING_DISK_OPTIMIZED")
```

**Checkpointing Tuning**:
```python
# Enable checkpointing
env.enable_checkpointing(60000)  # 60 seconds

# Checkpoint configuration
checkpoint_config = env.get_checkpoint_config()
checkpoint_config.set_min_pause_between_checkpoints(30000)  # 30s min pause
checkpoint_config.set_checkpoint_timeout(300000)  # 5 min timeout
checkpoint_config.set_max_concurrent_checkpoints(1)

# Retain checkpoint on cancellation
checkpoint_config.enable_externalized_checkpoints(
    ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION
)
```

### 3. Window Optimization

**Choose Right Window Type**:
```sql
-- Tumbling: For most use cases (least memory)
SELECT
    TUMBLE_START(ts, INTERVAL '1' MINUTE),
    COUNT(*)
FROM events
GROUP BY TUMBLE(ts, INTERVAL '1' MINUTE);

-- Sliding: Only when overlap needed (more memory)
SELECT
    HOP_START(ts, INTERVAL '1' MINUTE, INTERVAL '5' MINUTE),
    AVG(value)
FROM events
GROUP BY HOP(ts, INTERVAL '1' MINUTE, INTERVAL '5' MINUTE);

-- Session: For user sessions (variable memory)
SELECT
    SESSION_START(ts, INTERVAL '30' MINUTE),
    COUNT(*)
FROM events
GROUP BY user_id, SESSION(ts, INTERVAL '30' MINUTE);
```

**Late Data Handling**:
```python
# Allow 5 minutes of lateness
stream \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .allowed_lateness(Time.minutes(5)) \
    .aggregate(agg_function)
```

### 4. Memory Management

**JVM Heap Tuning**:
```
# Flink TaskManager configuration
taskmanager.memory.process.size: 4096m
taskmanager.memory.flink.size: 3072m
taskmanager.memory.jvm-heap.size: 2048m
taskmanager.memory.managed.size: 1024m
taskmanager.memory.network.min: 256m
```

**Avoid Memory Leaks**:
```python
class BadFunction(KeyedProcessFunction):
    def __init__(self):
        self.cache = {}  # ❌ Unbounded cache, memory leak!

    def process_element(self, value, ctx):
        self.cache[value['key']] = value  # Never cleared
        yield value

class GoodFunction(KeyedProcessFunction):
    def open(self, runtime_context):
        # ✅ Use Flink state (managed, checkpointed)
        self.cache_state = runtime_context.get_map_state(
            MapStateDescriptor("cache", Types.STRING(), Types.PICKLED_BYTE_ARRAY())
        )

    def process_element(self, value, ctx):
        self.cache_state.put(value['key'], value)

        # Register timer to clean old entries
        ctx.timer_service().register_event_time_timer(
            ctx.timestamp() + 3600000  # 1 hour TTL
        )
        yield value

    def on_timer(self, timestamp, ctx):
        # Clean expired entries
        self.cache_state.remove(ctx.get_current_key())
```

---

## Cost Management

### 1. Cost Breakdown

**Monthly Cost Estimation**:
```
Service                     | Units           | Cost/Unit   | Total
────────────────────────────┼─────────────────┼─────────────┼────────
Kinesis Data Streams (4 sh) | 720 shard-hrs   | $0.015/hr   | $43
Kinesis PUT                  | 100M records    | $0.014/1M   | $1.40
Kinesis Data Analytics       | 2 KPUs × 720hrs | $0.11/KPU-hr| $158
DynamoDB (On-Demand)         | 10M reads       | $0.25/M     | $2.50
                             | 2M writes       | $1.25/M     | $2.50
S3 Standard                  | 100 GB          | $0.023/GB   | $2.30
CloudWatch (Metrics)         | 50 custom       | $0.30/each  | $15
────────────────────────────┴─────────────────┴─────────────┴────────
Total                                                          $225/mo
```

### 2. Optimization Strategies

**Strategy 1: On-Demand Kinesis**
```
Provisioned (4 shards):
- Cost: $43/month
- Best for: Steady workload

On-Demand:
- Cost: $0.04 per GB ingested + $0.015 per shard-hour
- For 10 GB/day: ~$30/month (30% savings)
- Best for: Variable workload, unpredictable spikes
```

**Strategy 2: Scale Analytics During Business Hours**
```python
import boto3
import schedule

def scale_up():
    client = boto3.client('kinesisanalyticsv2')
    client.update_application(
        ApplicationName='my-app',
        ApplicationConfigurationUpdate={
            'FlinkApplicationConfigurationUpdate': {
                'ParallelismConfigurationUpdate': {
                    'Parallelism': 8,  # Scale to 8 KPUs
                    'AutoScalingEnabled': True
                }
            }
        }
    )

def scale_down():
    # Scale to 1 KPU during off-hours
    client.update_application(..., Parallelism=1)

# Schedule (using Lambda + EventBridge in production)
schedule.every().day.at("08:00").do(scale_up)    # Business hours
schedule.every().day.at("18:00").do(scale_down)  # Off hours

# Save: 7 KPUs × 10 hours/day × 30 days × $0.11 = $231/month
```

**Strategy 3: Lifecycle Policies**
```python
# S3 lifecycle policy for checkpoint data
lifecycle_policy = {
    'Rules': [{
        'Id': 'MoveOldCheckpoints',
        'Status': 'Enabled',
        'Prefix': 'checkpoints/',
        'Transitions': [{
            'Days': 7,
            'StorageClass': 'INTELLIGENT_TIERING'  # Auto-tier based on access
        }],
        'Expiration': {
            'Days': 30  # Delete after 30 days
        }
    }]
}

s3.put_bucket_lifecycle_configuration(
    Bucket='flink-state',
    LifecycleConfiguration=lifecycle_policy
)
```

**Strategy 4: Query Optimization (Athena)**
```sql
-- Bad: Scan entire table ($5 per 1 TB)
SELECT * FROM events
WHERE date = '2024-03-01';

-- Good: Use partitions (scan only 1 day)
SELECT * FROM events
WHERE year='2024' AND month='03' AND day='01';
-- Cost: ~$0.02 (99.6% savings)

-- Better: Select only needed columns
SELECT user_id, event_type, timestamp
FROM events
WHERE year='2024' AND month='03' AND day='01';
-- Cost: ~$0.005 (75% savings from "Good")
```

### 3. Cost Alerts

```python
import boto3

def create_budget_alert():
    budgets = boto3.client('budgets')

    response = budgets.create_budget(
        AccountId='123456789012',
        Budget={
            'BudgetName': 'RealTimeAnalyticsBudget',
            'BudgetLimit': {
                'Amount': '500',
                'Unit': 'USD'
            },
            'TimeUnit': 'MONTHLY',
            'BudgetType': 'COST',
            'CostFilters': {
                'Service': ['Amazon Kinesis', 'AWS Lambda']
            }
        },
        NotificationsWithSubscribers=[{
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 80.0,  # Alert at 80%
                'ThresholdType': 'PERCENTAGE'
            },
            'Subscribers': [{
                'SubscriptionType': 'EMAIL',
                'Address': 'data-eng@company.com'
            }]
        }]
    )
```

---

## Monitoring & Alerting

### 1. Key Metrics to Track

**Kinesis Data Streams**:
```
Metric                           | Threshold      | Action
─────────────────────────────────┼────────────────┼─────────────────
IncomingRecords                  | -              | Track throughput
IncomingBytes                    | > 80% capacity | Add shards
GetRecords.IteratorAgeMilliseconds| > 60000 ms    | Scale consumers
ReadProvisionedThroughputExceeded| > 0           | Add shards / consumers
WriteProvisionedThroughputExceeded| > 0          | Add shards / batch
```

**Kinesis Data Analytics**:
```
Metric                           | Threshold      | Action
─────────────────────────────────┼────────────────┼─────────────────
KPUs                             | > 80% util     | Auto-scale or add KPUs
Downtime                         | > 0 seconds    | Alert & investigate
Checkpoints.Duration             | > 60 seconds   | Optimize state size
Checkpoints.Failed               | > 0           | Alert immediately
lastCheckpointDuration           | Increasing     | State growing too large
Records.numRecordsOutPerSecond   | Decreasing     | Performance degradation
Records.numRecordsInPerSecond    | -              | Track input rate
```

**Custom Application Metrics**:
```python
from pyflink.datastream.functions import ProcessFunction
import boto3

class MetricsCollector(ProcessFunction):
    def open(self, runtime_context):
        self.cloudwatch = boto3.client('cloudwatch')
        self.counter = 0
        self.errors = 0

    def process_element(self, value, ctx):
        self.counter += 1

        # Publish every 100 records
        if self.counter % 100 == 0:
            self.publish_metrics()

        try:
            result = process(value)
            yield result
        except Exception as e:
            self.errors += 1
            self.publish_error_metric()
            raise

    def publish_metrics(self):
        self.cloudwatch.put_metric_data(
            Namespace='RealTimeAnalytics/Custom',
            MetricData=[
                {
                    'MetricName': 'RecordsProcessed',
                    'Value': self.counter,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'ErrorRate',
                    'Value': self.errors / self.counter if self.counter > 0 else 0,
                    'Unit': 'Percent'
                }
            ]
        )
```

### 2. CloudWatch Alarms

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Alarm 1: High iterator age (consumer lag)
cloudwatch.put_metric_alarm(
    AlarmName='kinesis-high-iterator-age',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=2,
    MetricName='GetRecords.IteratorAgeMilliseconds',
    Namespace='AWS/Kinesis',
    Period=300,
    Statistic='Maximum',
    Threshold=60000,  # 60 seconds
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:data-ops'],
    Dimensions=[{
        'Name': 'StreamName',
        'Value': 'events-stream'
    }]
)

# Alarm 2: Analytics downtime
cloudwatch.put_metric_alarm(
    AlarmName='analytics-downtime',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=1,
    MetricName='downtime',
    Namespace='AWS/KinesisAnalytics',
    Period=60,
    Statistic='Maximum',
    Threshold=0,
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:critical-alerts'],
    Dimensions=[{
        'Name': 'Application',
        'Value': 'my-flink-app'
    }]
)

# Alarm 3: High error rate
cloudwatch.put_metric_alarm(
    AlarmName='high-error-rate',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=2,
    MetricName='ErrorRate',
    Namespace='RealTimeAnalytics/Custom',
    Period=300,
    Statistic='Average',
    Threshold=5.0,  # 5% error rate
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:data-ops']
)
```

### 3. Dashboards

**CloudWatch Dashboard (JSON)**:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Kinesis", "IncomingRecords", {"stat": "Sum", "label": "Records/min"}],
          [".", "IncomingBytes", {"stat": "Sum", "yAxis": "right"}]
        ],
        "period": 60,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Kinesis Throughput",
        "yAxis": {
          "left": {"label": "Records"},
          "right": {"label": "Bytes"}
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/KinesisAnalytics", "KPUs", {"stat": "Average"}],
          [".", "cpuUtilization", {"stat": "Average", "yAxis": "right"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Flink Resource Utilization"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/kinesis-analytics/my-flink-app' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
        "region": "us-east-1",
        "title": "Recent Errors"
      }
    }
  ]
}
```

---

## Error Handling & Reliability

### 1. Dead Letter Queues

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import ProcessFunction

class ErrorHandlingProcessor(ProcessFunction):
    def __init__(self):
        self.dlq_stream = None

    def open(self, runtime_context):
        # Initialize DLQ sink (Kinesis or S3)
        self.dlq_sink = create_dlq_sink()

    def process_element(self, value, ctx):
        try:
            # Process record
            result = transform(value)
            yield result

        except ValidationError as e:
            # Send to DLQ with error details
            self.dlq_sink.send({
                'original_record': value,
                'error_type': 'ValidationError',
                'error_message': str(e),
                'timestamp': ctx.timestamp(),
                'processing_time': int(time.time() * 1000)
            })

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error processing record: {e}")
            # Optionally: re-raise to fail loudly
            raise

# Main stream
main_stream = env.add_source(kinesis_source)

# Process with error handling
result_stream = main_stream.process(ErrorHandlingProcessor())

# DLQ can be monitored and reprocessed
dlq_stream = env.add_source(dlq_kinesis_source)
reprocessed = dlq_stream.map(lambda x: retry_processing(x['original_record']))
```

### 2. Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientProcessor(ProcessFunction):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def external_api_call(self, data):
        response = requests.post('https://api.example.com/process', json=data)
        response.raise_for_status()
        return response.json()

    def process_element(self, value, ctx):
        try:
            result = self.external_api_call(value)
            yield result
        except Exception as e:
            # After 3 retries, send to DLQ
            self.send_to_dlq(value, e)
```

### 3. Checkpointing for Fault Tolerance

```python
# Enable checkpointing
env.enable_checkpointing(60000)  # Every 60 seconds

# Checkpoint configuration
checkpoint_config = env.get_checkpoint_config()

# Exactly-once semantics
checkpoint_config.set_checkpointing_mode(CheckpointingMode.EXACTLY_ONCE)

# Min pause between checkpoints (avoid back-to-back checkpoints)
checkpoint_config.set_min_pause_between_checkpoints(30000)

# Checkpoint timeout
checkpoint_config.set_checkpoint_timeout(300000)  # 5 minutes

# Retain checkpoint on cancellation (for savepoints)
checkpoint_config.enable_externalized_checkpoints(
    ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION
)

# Max concurrent checkpoints
checkpoint_config.set_max_concurrent_checkpoints(1)

# Tolerate failed checkpoints
checkpoint_config.set_tolerable_checkpoint_failure_number(3)
```

### 4. Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)

            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'

            raise

class ResilientAPIProcessor(ProcessFunction):
    def open(self, runtime_context):
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    def process_element(self, value, ctx):
        try:
            result = self.circuit_breaker.call(
                external_api.process,
                value
            )
            yield result
        except Exception as e:
            # Fallback or DLQ
            yield {'status': 'fallback', 'data': value}
```

---

## Testing Strategies

### 1. Unit Testing Flink Functions

```python
import pytest
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def test_transformation_function():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # Create test data
    test_data = [
        {'user_id': 1, 'amount': 100},
        {'user_id': 2, 'amount': 200},
        {'user_id': 1, 'amount': 150}
    ]

    # Apply transformation
    stream = env.from_collection(test_data)
    result = stream.key_by(lambda x: x['user_id']) \
                   .reduce(lambda a, b: {
                       'user_id': a['user_id'],
                       'amount': a['amount'] + b['amount']
                   })

    # Collect results
    results = []
    result.add_sink(lambda x: results.append(x))

    env.execute("Test")

    # Assertions
    assert len(results) == 2
    assert any(r['user_id'] == 1 and r['amount'] == 250 for r in results)
    assert any(r['user_id'] == 2 and r['amount'] == 200 for r in results)
```

### 2. Integration Testing

```python
import boto3
import time

def test_end_to_end_pipeline():
    kinesis = boto3.client('kinesis')

    # 1. Write test data to Kinesis
    test_event = {
        'user_id': 'test-123',
        'event_type': 'purchase',
        'amount': 99.99,
        'timestamp': int(time.time() * 1000)
    }

    kinesis.put_record(
        StreamName='input-stream',
        Data=json.dumps(test_event),
        PartitionKey='test-123'
    )

    # 2. Wait for processing
    time.sleep(10)

    # 3. Verify output in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('analytics-results')

    response = table.get_item(Key={'user_id': 'test-123'})

    assert 'Item' in response
    assert response['Item']['total_purchases'] >= 99.99
```

### 3. Load Testing

```python
import boto3
from concurrent.futures import ThreadPoolExecutor
import random

def send_event(kinesis, stream_name, i):
    event = {
        'user_id': f'user-{random.randint(1, 10000)}',
        'event_type': random.choice(['page_view', 'click', 'purchase']),
        'timestamp': int(time.time() * 1000) + i
    }

    kinesis.put_record(
        StreamName=stream_name,
        Data=json.dumps(event),
        PartitionKey=event['user_id']
    )

def load_test(events_per_second=1000, duration_seconds=60):
    kinesis = boto3.client('kinesis')

    total_events = events_per_second * duration_seconds

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []

        for i in range(total_events):
            future = executor.submit(send_event, kinesis, 'test-stream', i)
            futures.append(future)

            # Pace requests
            if (i + 1) % events_per_second == 0:
                time.sleep(1)

        # Wait for completion
        for future in futures:
            future.result()

    print(f"Sent {total_events} events in {duration_seconds} seconds")
    print(f"Throughput: {events_per_second} events/sec")

# Run load test
load_test(events_per_second=5000, duration_seconds=300)  # 5K events/sec for 5 min
```

---

## Deployment Best Practices

### 1. Blue/Green Deployment

```bash
#!/bin/bash

APP_NAME="my-flink-app"
NEW_VERSION="v2"

# Step 1: Create snapshot from current application (Blue)
aws kinesisanalyticsv2 create-application-snapshot \
    --application-name $APP_NAME \
    --snapshot-name "pre-deploy-$(date +%Y%m%d-%H%M%S)"

# Step 2: Deploy new version (Green)
aws kinesisanalyticsv2 update-application \
    --application-name $APP_NAME \
    --application-configuration-update file://new-config.json

# Step 3: Start application
aws kinesisanalyticsv2 start-application \
    --application-name $APP_NAME \
    --run-configuration file://run-config.json

# Step 4: Monitor for 10 minutes
sleep 600

# Step 5: Check error metrics
ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/KinesisAnalytics \
    --metric-name Errors \
    --dimensions Name=Application,Value=$APP_NAME \
    --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 600 \
    --statistics Sum \
    --query 'Datapoints[0].Sum')

if [ "$ERROR_COUNT" -gt "10" ]; then
    echo "Deployment failed! Rolling back..."
    # Rollback to snapshot
    aws kinesisanalyticsv2 restore-application-from-snapshot \
        --application-name $APP_NAME \
        --snapshot-name "pre-deploy-*"
else
    echo "Deployment successful!"
fi
```

### 2. Infrastructure as Code (Terraform)

```hcl
# Kinesis Data Stream
resource "aws_kinesis_stream" "events" {
  name             = "events-stream"
  shard_count      = 4
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds"
  ]

  tags = {
    Environment = "production"
    Team        = "data-engineering"
  }
}

# Kinesis Data Analytics Application
resource "aws_kinesisanalyticsv2_application" "flink_app" {
  name                   = "my-flink-app"
  runtime_environment    = "FLINK-1_15"
  service_execution_role = aws_iam_role.analytics_role.arn

  application_configuration {
    application_code_configuration {
      code_content {
        s3_content_location {
          bucket_arn = aws_s3_bucket.code_bucket.arn
          file_key   = "flink-app.jar"
        }
      }
      code_content_type = "ZIPFILE"
    }

    flink_application_configuration {
      checkpoint_configuration {
        configuration_type = "CUSTOM"
        checkpointing_enabled = true
        checkpoint_interval = 60000
        min_pause_between_checkpoints = 30000
      }

      monitoring_configuration {
        configuration_type = "CUSTOM"
        log_level = "INFO"
        metrics_level = "APPLICATION"
      }

      parallelism_configuration {
        configuration_type = "CUSTOM"
        parallelism = 4
        parallelism_per_kpu = 1
        auto_scaling_enabled = true
      }
    }
  }

  cloudwatch_logging_options {
    log_stream_arn = aws_cloudwatch_log_stream.analytics.arn
  }

  tags = {
    Environment = "production"
  }
}
```

---

## Security Hardening

### 1. Least Privilege IAM

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadFromSource",
      "Effect": "Allow",
      "Action": [
        "kinesis:DescribeStream",
        "kinesis:GetShardIterator",
        "kinesis:GetRecords",
        "kinesis:ListShards"
      ],
      "Resource": "arn:aws:kinesis:us-east-1:123456789012:stream/input-stream"
    },
    {
      "Sid": "WriteToDestination",
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:us-east-1:123456789012:stream/output-stream"
    },
    {
      "Sid": "Checkpointing",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::flink-checkpoints/my-app/*"
    },
    {
      "Sid": "CloudWatchLogging",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/kinesis-analytics/my-app:*"
    }
  ]
}
```

### 2. Encryption

**Enable KMS Encryption**:
```python
import boto3

kinesis = boto3.client('kinesis')

# Enable server-side encryption
kinesis.start_stream_encryption(
    StreamName='events-stream',
    EncryptionType='KMS',
    KeyId='arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
)
```

**VPC Endpoints** (no internet traffic):
```hcl
resource "aws_vpc_endpoint" "kinesis" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.us-east-1.kinesis-streams"
  vpc_endpoint_type = "Interface"

  subnet_ids = [aws_subnet.private.id]

  security_group_ids = [aws_security_group.kinesis.id]

  private_dns_enabled = true
}
```

---

## Operational Excellence

### 1. Runbook for Common Issues

**Issue: High Iterator Age**
```
Symptom: GetRecords.IteratorAgeMilliseconds > 60000
Cause: Consumers can't keep up with incoming data
Solutions:
1. Add more shards (increase parallelism)
2. Optimize consumer code (reduce processing time)
3. Scale Flink application (add KPUs)
4. Check for stuck consumers (restart if needed)
```

**Issue: Checkpoint Failures**
```
Symptom: Checkpoints.Failed > 0
Cause: State too large, network issues, S3 throttling
Solutions:
1. Increase checkpoint timeout
2. Reduce state size (TTL on state, compaction)
3. Use RocksDB state backend (off-heap)
4. Check S3 request rates (add exponential backoff)
```

### 2. On-Call Procedures

**Escalation Levels**:
```
Level 1: Automated recovery (auto-scaling, restarts)
Level 2: On-call engineer notification (PagerDuty)
Level 3: Team lead escalation (repeated failures)
Level 4: Management escalation (SLA breach)
```

### 3. Documentation

**Key Documents**:
- Architecture Diagram
- Runbook for incidents
- Deployment Procedure
- Monitoring Dashboard Guide
- Cost Breakdown & Optimization
- Disaster Recovery Plan

---

## Summary

### Key Takeaways

**Performance**:
- Right-size shards and KPUs
- Use RocksDB for large state
- Tune checkpointing intervals
- Optimize window types

**Cost**:
- Use on-demand Kinesis for variable workloads
- Scale analytics during business hours
- Lifecycle policies for old data
- Query optimization (partition pruning)

**Reliability**:
- Implement dead letter queues
- Enable checkpointing (exactly-once)
- Retry logic with exponential backoff
- Circuit breaker for external calls

**Security**:
- Least privilege IAM roles
- Enable KMS encryption
- VPC endpoints for private traffic
- Audit logs (CloudTrail)

---

**Previous**: [architecture.md](./architecture.md) - AWS Architectures
** Next**: [resources.md](./resources.md) - Learning Resources
