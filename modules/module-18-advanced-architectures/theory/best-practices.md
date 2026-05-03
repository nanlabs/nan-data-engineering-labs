# Best Practices for Advanced Data Architectures

## Table of Contents

1. [Design Principles](#design-principles)
2. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
3. [Schema Design](#schema-design)
4. [Error Handling](#error-handling)
5. [Monitoring & Observability](#monitoring--observability)
6. [Cost Optimization](#cost-optimization)
7. [Security & Compliance](#security--compliance)
8. [Testing Strategies](#testing-strategies)
9. [Migration Strategies](#migration-strategies)
10. [Decision Framework](#decision-framework)

---

## Design Principles

### 1. Start Simple, Evolve as Needed

**Anti-pattern**: Implement Lambda Architecture on day 1 for 1,000 users.

**Best Practice**: Evolution path

```
Phase 1 (MVP): Simple CRUD
- RDS PostgreSQL
- Monolithic application
- Cost: $500/month
- Team: 2 engineers

↓ (Growth: 10K users, slow queries)

Phase 2 (Scale): Add caching
- ElastiCache for hot data
- Cost: $1K/month
- Team: 3 engineers

↓ (Growth: 100K users, real-time needs)

Phase 3 (Real-time): Add streaming
- Kinesis + Lambda
- Kappa architecture
- Cost: $5K/month
- Team: 5 engineers

↓ (Growth: 1M users, complex analytics)

Phase 4 (Advanced): Lambda architecture
- Batch (Spark) + Speed (Kinesis)
- Cost: $15K/month
- Team: 10 engineers
```

**Key Insight**: Each phase justified by actual pain points, not speculation.

### 2. Loose Coupling via Events

**Bad**: Direct service-to-service calls

```python
# Order Service calls 5 services directly
def place_order(order):
    inventory.reserve(order.items)      # Coupling #1
    payment.process(order.amount)       # Coupling #2
    shipping.create(order.address)      # Coupling #3
    notification.send_email(order.user) # Coupling #4
    analytics.track(order)              # Coupling #5

    # If any service is down, entire order fails
    # If add new service (fraud detection), must modify this code
```

**Good**: Event-driven via EventBridge

```python
# Order Service publishes event
def place_order(order):
    event = create_event("OrderPlaced", order)
    eventbridge.put_events(Entries=[event])
    # Done! Other services subscribe independently

# Inventory Service subscribes
@eventbridge_listener("OrderPlaced")
def on_order_placed(event):
    inventory.reserve(event['items'])

# Adding new service (fraud detection): Zero changes to order service
@eventbridge_listener("OrderPlaced")
def on_order_placed_fraud(event):
    fraud_score = detect_fraud(event)
    if fraud_score > 0.9:
        eventbridge.put_events(Entries=[{
            'DetailType': 'FraudDetected',
            'Detail': json.dumps(event)
        }])
```

**Benefits**:
- Order service doesn't know about consumers
- Add consumers without modifying producer
- Services can fail independently
- Async execution (faster response)

### 3. Immutability for Data Lakes

**Bad**: Mutable S3 files

```python
# Overwrite file daily (lose history)
s3.put_object(
    Bucket='data-lake',
    Key='orders/latest.parquet',  # Same key every day
    Body=orders_df.to_parquet()
)

# Problem: Can't time travel ("show orders from last week")
```

**Good**: Immutable partition keys

```python
# Write to date-partitioned paths
s3.put_object(
    Bucket='data-lake',
    Key=f'orders/year={year}/month={month}/day={day}/data.parquet',
    Body=orders_df.to_parquet()
)

# Query any historical date
athena.execute("""
SELECT * FROM orders
WHERE year=2026 AND month=03 AND day=01
""")
```

**Benefits**:
- Time travel queries
- Reproducible analytics
- Audit trail
- Safe reprocessing (don't overwrite production data)

### 4. Idempotency for Exactly-Once Processing

**Problem**: Retry on failure causes duplicates

```python
# NOT idempotent
def process_order(order):
    order_id = generate_uuid()  # Different ID on retry!
    db.insert(order_id, order)

# Result: Retries create duplicate orders
```

**Solution 1**: Deterministic IDs

```python
# Idempotent with deterministic ID
def process_order(order):
    order_id = hash(order['user_id'] + order['timestamp'])  # Same on retry
    if db.exists(order_id):
        return db.get(order_id)  # Already processed
    db.insert(order_id, order)
```

**Solution 2**: DynamoDB Conditional Writes

```python
# Idempotent with condition
def process_order(order):
    try:
        dynamodb.put_item(
            TableName='orders',
            Item={'order_id': order_id, 'data': order},
            ConditionExpression='attribute_not_exists(order_id)'  # Only if not exists
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return dynamodb.get_item(TableName='orders', Key={'order_id': order_id})
        raise
```

### 5. Circuit Breaker for Resilience

**Problem**: Cascading failures

```
Service A calls Service B (slow/failing)
  ↓
Service A waits 30 seconds per call
  ↓
Service A thread pool exhausted
  ↓
Service A crashes
  ↓
All upstream services fail
```

**Solution**: Circuit breaker pattern

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
                self.state = 'HALF_OPEN'  # Try again
            else:
                raise CircuitBreakerOpenError("Circuit breaker open")

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

# Usage
inventory_circuit = CircuitBreaker()

def reserve_inventory(items):
    try:
        return inventory_circuit.call(inventory_api.reserve, items)
    except CircuitBreakerOpenError:
        # Fail fast instead of waiting 30 seconds
        return default_response()
```

**Result**: Service A survives Service B outage.

---

## Anti-Patterns to Avoid

### 1. Distributed Monolith

**Anti-pattern**: Microservices with tight coupling

```
Order Service → calls → Inventory Service (sync HTTP)
              → calls → Payment Service (sync HTTP)
              → calls → Shipping Service (sync HTTP)

Result:
- All services must be up (no resilience)
- Slow (sequential calls: 50ms + 50ms + 50ms = 150ms)
- Changes require coordinated deploys
```

**Fix**: Event-driven async communication

```
Order Service → publishes event → EventBridge
                                      ↓
                     ┌────────────────┼────────────────┐
                     ↓                ↓                ↓
            Inventory Service  Payment Service  Shipping Service
            (listens async)    (listens async)  (listens async)

Result:
- Services independent (resilient)
- Fast (async: 50ms total)
- No coordination needed
```

### 2. Chatty APIs

**Anti-pattern**: N+1 queries

```python
# Get user + all orders (10 orders = 11 API calls)
user = get_user(user_id)  # 1 call
for order_id in user['order_ids']:
    order = get_order(order_id)  # 10 calls

# 11 × 50ms = 550ms total latency
```

**Fix**: Batch API or denormalization

```python
# Option 1: Batch API
orders = get_orders_batch(user['order_ids'])  # 1 call, 50ms

# Option 2: Denormalize (store orders with user)
user_with_orders = get_user_denormalized(user_id)  # 1 call, 50ms
```

### 3. No Schema Versioning

**Anti-pattern**: Breaking changes without versioning

```python
# v1: Field name "email"
{"email": "john@example.com"}

# v2: Renamed to "email_address" (breaking change!)
{"email_address": "john@example.com"}

# Result: Old consumers crash
```

**Fix**: Schema registry + compatibility rules

```python
# Avro schema with backward compatibility
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "email", "type": "string", "default": ""},  # Keep old field
    {"name": "email_address", "type": "string"}           # Add new field
  ]
}

# Old consumers read "email"
# New consumers read "email_address"
# Transition period: 6 months, then deprecate "email"
```

### 4. Overly Complex Joins

**Anti-pattern**: 10-table join in stream processing

```sql
-- Flink SQL with 10 stream-to-table joins (slow, high memory)
SELECT *
FROM stream
JOIN table1 ON stream.id = table1.id
JOIN table2 ON table1.id = table2.id
JOIN table3 ON table2.id = table3.id
... (7 more joins)
```

**Fix**: Denormalize into wide stream

```python
# Pre-join into enriched stream (batch job)
enriched_stream = {
    "order_id": "123",
    "user_name": "John",      # From users table
    "product_name": "iPhone", # From products table
    "category": "Electronics", # From categories table
    # ... all fields needed
}

# Stream processor: No joins needed
SELECT order_id, user_name, SUM(amount)
FROM enriched_stream
GROUP BY order_id, user_name
```

**Trade-off**: More storage (duplicated data), but 10x faster queries.

### 5. No Backpressure Handling

**Anti-pattern**: Producer faster than consumer

```
Kinesis (1 MB/sec) → Lambda (0.1 MB/sec processing)

Result:
- Lambda throttled (too many invocations)
- Records pile up in Kinesis
- Delay increases (minutes to hours)
- Lambda errors: IteratorAge exceeded
```

**Fix**: Batch processing + concurrency limits

```python
# Lambda configuration
lambda_function.update_function_configuration(
    FunctionName='stream-processor',
    ReservedConcurrentExecutions=50,  # Limit concurrency
    Timeout=300  # 5 min timeout
)

# Batch records (process 100 at a time)
kinesis.create_event_source_mapping(
    FunctionName='stream-processor',
    EventSourceArn=kinesis_stream_arn,
    BatchSize=100,  # Process in batches
    MaximumBatchingWindowInSeconds=5  # Wait up to 5 sec
)
```

---

## Schema Design

### 1. Forward and Backward Compatibility

**Goal**: Old code reads new data, new code reads old data.

#### **Backward Compatible** (Add Fields Only)

```python
# Schema v1
{
  "name": "string",
  "email": "string"
}

# Schema v2 (backward compatible: add field with default)
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "default": ""  # Old readers ignore this field
}
```

✅ **Old reader reads v2 data**: Works (ignores "phone")
✅ **New reader reads v1 data**: Works (uses default for "phone")

#### **Forward Compatible** (Remove Fields with Defaults)

```python
# Schema v1
{
  "name": "string",
  "email": "string",
  "deprecated_field": "string"
}

# Schema v2 (forward compatible: add deprecated flag)
{
  "name": "string",
  "email": "string",
  "deprecated_field": "string"  # Mark as deprecated, remove in v3
}
```

**Migration Path**: v1 → v2 (both fields) → v3 (remove deprecated)

### 2. Partition Key Selection

#### **DynamoDB**

**Goal**: Distribute load evenly, enable efficient queries.

**Bad** (Hot Partition):
```python
# All writes go to same partition
partition_key = "status"  # Only 3 values: pending, completed, cancelled

# Result: 1 partition handles 100% of traffic (throttled)
```

**Good** (High Cardinality):
```python
# Unique partition key
partition_key = f"ORDER#{order_id}"  # Millions of unique values

# Result: Load distributed across thousands of partitions
```

**Best** (Composite with Sort Key):
```python
# Access pattern: Get orders by user + date range
partition_key = f"USER#{user_id}"
sort_key = f"ORDER#{timestamp}#{order_id}"

# Enables: Query all orders for user in date range
dynamodb.query(
    KeyConditionExpression="PK = :user AND SK BETWEEN :start AND :end",
    ExpressionAttributeValues={
        ':user': 'USER#123',
        ':start': 'ORDER#2026-03-01',
        ':end': 'ORDER#2026-03-31'
    }
)
```

#### **S3 / Data Lake**

**Bad** (No Partitioning):
```
s3://data-lake/orders/data.parquet  # Single file (100 GB)

# Athena scans entire file for any query ($5/TB × 0.1 = $0.50 per query)
SELECT * FROM orders WHERE date = '2026-03-09'  # Scans 100 GB
```

**Good** (Date Partitioning - Hive Style):
```
s3://data-lake/orders/year=2026/month=03/day=09/data.parquet

# Athena only scans 1 day (100 MB, not 100 GB)
SELECT * FROM orders WHERE year=2026 AND month=03 AND day=09
# Cost: $5/TB × 0.0001 = $0.0005 per query (1000x cheaper)
```

**Best** (Multi-Dimensional Partitioning):
```
s3://data-lake/orders/
  region=us/date=2026-03-09/hour=10/data.parquet
  region=eu/date=2026-03-09/hour=10/data.parquet

# Query: Orders from EU today
SELECT * FROM orders
WHERE region='eu' AND date='2026-03-09'
# Scans only EU partition (50% reduction)
```

**Avoid Over-Partitioning**:
```
❌ Too granular: year/month/day/hour/minute/second
   (10M partitions, slow to list)

✅ Right balance: year/month/day or date/hour
   (~1,000 partitions, fast queries)
```

### 3. Event Design

#### **Events Should Be**:

✅ **Immutable**: Never modify published events
✅ **Self-Contained**: All context needed to process
✅ **Versioned**: Schema version in event
✅ **Timestamped**: Include event_time and ingestion_time
✅ **Idempotent**: Include unique event_id for deduplication

**Example Event**:

```json
{
  "event_id": "evt_a1b2c3d4",
  "event_type": "OrderPlaced",
  "event_version": "2.0",
  "event_time": "2026-03-09T10:30:00.123Z",
  "ingestion_time": "2026-03-09T10:30:00.456Z",
  "source": "order-service",
  "trace_id": "trace_xyz789",  # Distributed tracing
  "data": {
    "order_id": "order_123",
    "user_id": "user_456",
    "items": [
      {"product_id": "prod_789", "quantity": 2, "price": 29.99}
    ],
    "total_amount": 59.98,
    "currency": "USD",
    "payment_method": "credit_card",
    "shipping_address": {
      "street": "123 Main St",
      "city": "Seattle",
      "postal_code": "98101",
      "country": "US"
    }
  }
}
```

### 4. Separation of Concerns

**Single Responsibility**: Each component does ONE thing well.

**Bad**: God service

```python
# OrderService does everything (2,000 lines)
class OrderService:
    def place_order(self):
        self.validate_inventory()      # Inventory concern
        self.process_payment()         # Payment concern
        self.calculate_tax()           # Tax concern
        self.allocate_warehouse()      # Logistics concern
        self.send_notification()       # Notification concern
        self.update_analytics()        # Analytics concern
```

**Good**: Microservices with clear boundaries

```python
# OrderService: Orchestration only (200 lines)
class OrderService:
    def place_order(self, order):
        eventbridge.put_events([{
            'DetailType': 'OrderPlaced',
            'Detail': json.dumps(order)
        }])

# InventoryService: Inventory logic (300 lines)
# PaymentService: Payment logic (400 lines)
# TaxService: Tax calculation (250 lines)
# Each service focused on single domain
```

---

## Error Handling

### 1. Retry Strategies

#### **Exponential Backoff**

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)  # 1, 2, 4, 8 seconds
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=5, base_delay=2)
def call_external_api():
    return requests.get("https://api.example.com/data")

# Retry schedule: 2s, 4s, 8s, 16s, 32s (5 attempts)
```

#### **Dead Letter Queue (DLQ)**

```python
# Lambda with DLQ
lambda_function.update_function_configuration(
    FunctionName='order-processor',
    DeadLetterConfig={
        'TargetArn': dlq_sqs_arn  # Failed events go here
    }
)

# Process DLQ separately
@sqs_listener(dlq_sqs_arn)
def handle_failed_events(event):
    # Log to CloudWatch
    logger.error(f"Failed event: {event}")

    # Send to manual review
    send_alert(f"Manual review needed: {event['event_id']}")

    # Optional: Retry with different strategy
    reprocess_with_fallback(event)
```

### 2. Graceful Degradation

**Principle**: Partial functionality better than total failure.

```python
def get_product_recommendations(user_id):
    try:
        # Try ML-based recommendations (slow, complex)
        recommendations = ml_service.get_recommendations(user_id)
    except (Timeout, ServiceUnavailable):
        # Fallback: Popular products (fast, simple)
        recommendations = get_popular_products()
        logger.warning(f"ML service unavailable, using fallback")

    return recommendations

# Result: Users still get recommendations (even if not personalized)
```

### 3. Timeout Configuration

**Rule**: Set timeouts for all external calls.

```python
# Lambda: 30 second default (too long!)
response = requests.get("https://api.example.com/data")
# If API hangs, Lambda waits 30 seconds, wastes money

# Fix: Set aggressive timeout
response = requests.get(
    "https://api.example.com/data",
    timeout=5  # 5 seconds max
)

# Lambda function timeout
lambda_function.update_function_configuration(
    FunctionName='api-caller',
    Timeout=10  # Kill after 10 seconds
)
```

**Timeout Tuning**:
- **API calls**: 5-10 seconds (fail fast)
- **Database queries**: 30 seconds (complex analytics)
- **Lambda**: 5 minutes (batch processing)
- **Step Functions**: 1 hour (long-running workflows)

---

## Monitoring & Observability

### 1. Golden Signals (Google SRE)

Monitor these 4 metrics for every service:

#### **Latency** (Response Time)

```python
# CloudWatch custom metric
cloudwatch.put_metric_data(
    Namespace='OrderService',
    MetricData=[{
        'MetricName': 'ResponseTime',
        'Value': response_time_ms,
        'Unit': 'Milliseconds',
        'Dimensions': [
            {'Name': 'Endpoint', 'Value': '/api/orders'},
            {'Name': 'StatusCode', 'Value': '200'}
        ]
    }]
)

# Alert: P99 latency > 1 second
alarm = cloudwatch.put_metric_alarm(
    AlarmName='HighLatency',
    MetricName='ResponseTime',
    Statistic='p99',
    Threshold=1000,
    ComparisonOperator='GreaterThanThreshold'
)
```

#### **Traffic** (Requests per Second)

```python
# Count requests
cloudwatch.put_metric_data(
    Namespace='OrderService',
    MetricData=[{
        'MetricName': 'RequestCount',
        'Value': 1,
        'Unit': 'Count'
    }]
)

# Alert: Traffic spike (>10K req/sec, possible DDoS)
alarm = cloudwatch.put_metric_alarm(
    AlarmName='TrafficSpike',
    MetricName='RequestCount',
    Statistic='Sum',
    Period=60,
    Threshold=10000,
    ComparisonOperator='GreaterThanThreshold'
)
```

#### **Errors** (Error Rate)

```python
# Track errors
cloudwatch.put_metric_data(
    Namespace='OrderService',
    MetricData=[{
        'MetricName': 'ErrorCount',
        'Value': 1 if error else 0,
        'Unit': 'Count',
        'Dimensions': [
            {'Name': 'ErrorType', 'Value': error.__class__.__name__}
        ]
    }]
)

# Alert: Error rate > 1%
alarm = cloudwatch.put_metric_alarm(
    AlarmName='HighErrorRate',
    Metrics=[{
        'Id': 'error_rate',
        'Expression': '(errors / requests) * 100'
    }],
    Threshold=1.0,
    ComparisonOperator='GreaterThanThreshold'
)
```

#### **Saturation** (Resource Utilization)

```python
# DynamoDB consumed capacity
consumed_rcu = response['ConsumedCapacity']['ReadCapacityUnits']
provisioned_rcu = table_config['ProvisionedThroughput']['ReadCapacityUnits']

saturation = (consumed_rcu / provisioned_rcu) * 100

cloudwatch.put_metric_data(
    Namespace='DynamoDB',
    MetricData=[{
        'MetricName': 'Saturation',
        'Value': saturation,
        'Unit': 'Percent',
        'Dimensions': [{'Name': 'TableName', 'Value': 'orders'}]
    }]
)

# Alert: >80% capacity (risk of throttling)
alarm = cloudwatch.put_metric_alarm(
    AlarmName='DynamoDBHighSaturation',
    Threshold=80.0
)
```

### 2. Distributed Tracing

**Problem**: Request spans 10 microservices, where is slowdown?

```
User Request → API Gateway → Order Service → Inventory → Payment → Shipping
(1000ms total, which service is slow?)
```

**Solution**: AWS X-Ray

```python
from aws_xray_sdk.core import xray_recorder

# Trace entire request
@xray_recorder.capture('place_order')
def place_order(order):
    # Trace external calls
    with xray_recorder.capture('check_inventory'):
        inventory_api.check(order['items'])

    with xray_recorder.capture('process_payment'):
        payment_api.charge(order['amount'])

    with xray_recorder.capture('create_shipment'):
        shipping_api.create(order['address'])

# X-Ray shows:
# - place_order: 850ms
#   - check_inventory: 300ms ← Bottleneck found!
#   - process_payment: 200ms
#   - create_shipment: 350ms
```

### 3. Log Aggregation

**Centralized Logging** with CloudWatch Logs Insights:

```python
# Structured logging (JSON)
import json
import logging

logger = logging.getLogger()
logger.info(json.dumps({
    'event': 'order_placed',
    'order_id': 'order_123',
    'user_id': 'user_456',
    'amount': 59.98,
    'timestamp': datetime.now().isoformat()
}))

# Query across all services
logs_insights.start_query(
    logGroupName='/aws/lambda/order-processor',
    startTime=int((datetime.now() - timedelta(hours=1)).timestamp()),
    endTime=int(datetime.now().timestamp()),
    queryString="""
    fields @timestamp, order_id, user_id, amount
    | filter event = "order_placed" and amount > 100
    | stats count() by user_id
    | sort count desc
    | limit 10
    """
)
```

---

## Cost Optimization

### 1. Right-Sizing Databases

**Anti-pattern**: Over-provisioned RDS

```
RDS: db.r5.8xlarge (32 vCPUs, 256 GB RAM)
Cost: $5,800/month
Actual usage: 10% CPU, 20% RAM

Waste: $4,600/month
```

**Solution**: Use CloudWatch metrics

```python
# Check actual utilization
metrics = cloudwatch.get_metric_statistics(
    Namespace='AWS/RDS',
    MetricName='CPUUtilization',
    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': 'prod-db'}],
    StartTime=datetime.now() - timedelta(days=7),
    EndTime=datetime.now(),
    Period=3600,
    Statistics=['Average', 'Maximum']
)

avg_cpu = mean([m['Average'] for m in metrics['Datapoints']])
max_cpu = max([m['Maximum'] for m in metrics['Datapoints']])

# Decision: If avg_cpu < 30% and max_cpu < 60%, downsize
if avg_cpu < 30:
    recommended_instance = 'db.r5.xlarge'  # 1/8 the size
    savings = 5800 - 725  # Save $5,075/month!
```

### 2. S3 Lifecycle Policies

**Anti-pattern**: All data in S3 Standard forever

```
Raw data: 100 TB × $0.023/GB = $2,300/month
(90% of data not accessed after 30 days)
```

**Solution**: Tiered storage

```python
s3.put_bucket_lifecycle_configuration(
    Bucket='data-lake',
    LifecycleConfiguration={
        'Rules': [{
            'Id': 'archive-old-data',
            'Status': 'Enabled',
            'Transitions': [
                # After 30 days → Infrequent Access (50% cheaper)
                {
                    'Days': 30,
                    'StorageClass': 'STANDARD_IA'  # $0.0125/GB
                },
                # After 90 days → Glacier (80% cheaper)
                {
                    'Days': 90,
                    'StorageClass': 'GLACIER'  # $0.004/GB
                },
                # After 365 days → Deep Archive (95% cheaper)
                {
                    'Days': 365,
                    'StorageClass': 'DEEP_ARCHIVE'  # $0.00099/GB
                }
            ],
            'Expiration': {
                'Days': 2555  # Delete after 7 years
            }
        }]
    }
)

# Cost breakdown (100 TB):
# 0-30 days (10 TB fresh): 10 TB × $0.023 = $230
# 30-90 days (20 TB): 20 TB × $0.0125 = $250
# 90-365 days (30 TB): 30 TB × $0.004 = $120
# 365+ days (40 TB): 40 TB × $0.00099 = $40
# Total: $640/month (vs $2,300) → 72% savings
```

### 3. Lambda Memory Optimization

**Fact**: Lambda cost = memory × duration, but more memory = faster execution.

```python
# Test: Process 10K records
# 128 MB memory: 120 seconds × $0.0000000021/MB-ms = $0.032
# 1024 MB memory: 20 seconds × $0.0000000021/MB-ms = $0.043 (appears more expensive)

# But with parallelism:
# 128 MB: 10 concurrent executions × 120s = 1200 exec-seconds
# 1024 MB: 10 concurrent executions × 20s = 200 exec-seconds

# Result: 1024 MB is 6x faster, only 34% more expensive
# Winner: 1024 MB (better user experience, worth $0.011 extra)
```

**Rule**: Profile Lambda with different memory settings, optimize for cost-performance.

---

## Security & Compliance

### 1. Encryption (Defense in Depth)

**Layers**:

```
1. Encryption at Rest (S3, EBS, RDS)
   - S3: AES-256 (SSE-S3 or SSE-KMS)
   - RDS: Transparent Data Encryption (TDE)

2. Encryption in Transit (TLS 1.2+)
   - HTTPS for all API calls
   - SSL for database connections

3. Encryption in Use (Future: AWS Nitro Enclaves)
   - Process data in secure enclave
```

**Implementation**:

```python
# S3: Server-side encryption with KMS
s3.put_object(
    Bucket='data-lake',
    Key='pii/users.parquet',
    Body=data,
    ServerSideEncryption='aws:kms',
    SSEKMSKeyId=kms_key_id
)

# DynamoDB: Encryption at rest
dynamodb.create_table(
    TableName='users',
    SSESpecification={
        'Enabled': True,
        'SSEType': 'KMS',
        'KMSMasterKeyId': kms_key_id
    }
)

# RDS: Enable encryption
rds.create_db_instance(
    DBInstanceIdentifier='prod-db',
    StorageEncrypted=True,
    KmsKeyId=kms_key_id
)
```

### 2. Least Privilege Access (Lake Formation)

**Anti-pattern**: Grant full S3 access

```json
{
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "arn:aws:s3:::data-lake/*"
}
// Analysts can read/write/delete everything!
```

**Best Practice**: Column-level permissions

```python
# Lake Formation: Grant column-level access
lakeformation.grant_permissions(
    Principal={'DataLakePrincipalIdentifier': analyst_role_arn},
    Resource={
        'Table': {
            'DatabaseName': 'sales',
            'TableName': 'customers'
        }
    },
    Permissions=['SELECT'],
    PermissionsWithGrantOption=[],
    DataCellsFilter={
        'TableCatalogId': account_id,
        'DatabaseName': 'sales',
        'TableName': 'customers',
        'Name': 'analysts-filter',
        'RowFilter': {
            'FilterExpression': 'region = "US"'  # Only US customers
        },
        'ColumnNames': ['customer_id', 'name', 'email'],  # No SSN!
        'ColumnWildcard': None  # Explicit columns only
    }
)

# Result: Analysts can read customer_id, name, email (no SSN, no EU customers)
```

### 3. PII Tokenization

**Anti-pattern**: Store plaintext SSN, credit cards

```python
# BAD: Plaintext PII in data lake
{
  "user_id": "user_123",
  "name": "John Smith",
  "ssn": "123-45-6789",  # ⚠️ GDPR violation
  "credit_card": "4111-1111-1111-1111"  # ⚠️ PCI-DSS violation
}
```

**Best Practice**: Tokenization

```python
# Tokenize before writing to data lake
def tokenize_pii(data):
    return {
        "user_id": data["user_id"],
        "name": data["name"],
        "ssn_token": tokenization_service.tokenize(data["ssn"]),
        # Token: "tok_a1b2c3d4" (no PII, reversible)
        "credit_card_last4": data["credit_card"][-4:]  # Only last 4 digits
    }

# Detokenize only when needed (with audit trail)
def detokenize_pii(token, reason):
    audit_log.write({
        'user': current_user,
        'action': 'detokenize',
        'token': token,
        'reason': reason,
        'timestamp': datetime.now()
    })
    return tokenization_service.detokenize(token)

# Usage: 99% of analytics work on tokens, not PII
SELECT ssn_token, COUNT(*) FROM users GROUP BY ssn_token
# No PII exposed, still useful for deduplication
```

---

## Testing Strategies

### 1. Unit Tests (Isolated)

```python
import pytest
from moto import mock_dynamodb

@mock_dynamodb
def test_place_order():
    # Mock DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='orders',
        KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}]
    )

    # Test function
    order_service = OrderService(dynamodb_table=table)
    result = order_service.place_order({
        'user_id': 'user_123',
        'items': [{'product_id': 'prod_456', 'quantity': 2}]
    })

    # Assert
    assert result['status'] == 'success'
    assert table.item_count == 1
```

### 2. Integration Tests (Real AWS)

```python
@pytest.mark.integration
def test_end_to_end_order_flow():
    # Use real AWS resources (staging environment)
    order = place_order_api.post({
        'user_id': 'test-user',
        'items': [{'product_id': 'test-product', 'quantity': 1}]
    })

    # Wait for async processing
    time.sleep(5)

    # Verify: Inventory decremented
    inventory = inventory_api.get(product_id='test-product')
    assert inventory['quantity'] == initial_quantity - 1

    # Verify: Payment processed
    payment = payment_api.get(order_id=order['order_id'])
    assert payment['status'] == 'completed'

    # Cleanup
    cleanup_test_data(order['order_id'])
```

### 3. Chaos Engineering (Resilience Testing)

```python
# Test: What happens if DynamoDB fails?
@chaos_test
def test_dynamodb_failure_resilience():
    # Inject failure (block DynamoDB traffic)
    chaos.block_service('dynamodb.amazonaws.com')

    try:
        # Attempt order placement
        response = place_order({'user_id': 'user_123'})

        # Should fail gracefully (not crash)
        assert response['status'] == 'error'
        assert response['message'] == 'Service temporarily unavailable'
        assert 'retry_after' in response

    finally:
        chaos.restore_service('dynamodb.amazonaws.com')
```

---

## Migration Strategies

### 1. Strangler Fig Pattern

**Goal**: Migrate from monolith to microservices gradually.

```
Phase 1: Monolith (100% traffic)
Phase 2: 90% monolith, 10% new service (test)
Phase 3: 50% monolith, 50% new service (validate)
Phase 4: 0% monolith, 100% new service (complete)
```

**Implementation**:

```python
# API Gateway: Route based on header
if request.headers.get('X-Use-New-Service') == 'true':
    response = new_order_service.place_order(order)
else:
    response = legacy_monolith.place_order(order)

# Gradually increase traffic to new service
rollout_percentage = 10  # Start with 10%
if random.random() < (rollout_percentage / 100):
    response = new_order_service.place_order(order)
else:
    response = legacy_monolith.place_order(order)
```

### 2. Dual Writes

**Goal**: Migrate from Database A to Database B without downtime.

```
Phase 1: Read from A, Write to A
Phase 2: Read from A, Write to A + B (dual write)
Phase 3: Backfill B with historical data
Phase 4: Read from B, Write to A + B (validate)
Phase 5: Read from B, Write to B only (complete)
```

**Example**: PostgreSQL → DynamoDB

```python
# Phase 2: Dual writes
def save_order(order):
    # Write to PostgreSQL (old)
    postgres.execute(
        "INSERT INTO orders (order_id, data) VALUES (%s, %s)",
        (order['order_id'], json.dumps(order))
    )

    # Write to DynamoDB (new)
    try:
        dynamodb.put_item(
            TableName='orders',
            Item=order
        )
    except Exception as e:
        # Don't fail if DynamoDB fails (still transitioning)
        logger.error(f"DynamoDB write failed: {e}")

# Phase 3: Backfill
def backfill_dynamodb():
    offset = 0
    batch_size = 1000
    while True:
        orders = postgres.execute(
            f"SELECT * FROM orders LIMIT {batch_size} OFFSET {offset}"
        )
        if not orders:
            break

        # Write to DynamoDB
        with dynamodb_table.batch_writer() as batch:
            for order in orders:
                batch.put_item(Item=order)

        offset += batch_size
```

---

## Decision Framework

### When to Add Complexity?

**Rule**: Add complexity only when justified by metrics.

#### **Example: Should we add caching?**

**Current State**:
- Database query: 200ms
- Query frequency: 100 req/sec
- Database cost: $500/month

**Option**: Add ElastiCache Redis

**Analysis**:

```python
# Cost calculation
redis_cost = 150  # per month (cache.m5.large)
database_cost_without_cache = 500  # Current
database_cost_with_cache = 200  # 60% reduction (fewer queries)

total_cost_with_cache = redis_cost + database_cost_with_cache
# = $150 + $200 = $350/month

savings = 500 - 350  # $150/month

# Performance improvement
query_latency_before = 200  # ms
query_latency_after = 2  # ms (cache hit)
cache_hit_rate = 0.8  # 80% cache hits

avg_latency_after = (0.8 * 2) + (0.2 * 200)  # 1.6 + 40 = 41.6ms

improvement = (200 - 41.6) / 200  # 79% faster

# Decision matrix
if savings > 0 or improvement > 0.5:
    decision = "ADD_CACHE"  # ✅ Justified (save $150 + 79% faster)
else:
    decision = "SKIP_CACHE"
```

#### **Example: Should we migrate to multi-region?**

**Current State**:
- Single region (us-east-1)
- EU users: 40% of traffic
- Latency (EU): 150ms
- Cost: $10K/month

**Option**: Add eu-west-1

**Analysis**:

```python
# Cost increase
multi_region_cost = 10000 * 2.5  # 2.5x (infrastructure + replication)
# = $25K/month
extra_cost = 15000  # per month

# Revenue impact
users_affected = 0.40  # 40% EU users
latency_improvement = 150 - 30  # 150ms → 30ms
conversion_lift = 0.001 * latency_improvement  # 0.1% per 10ms improvement
# = 0.12 (12% more conversions)

monthly_revenue = 100000  # $100K/month
revenue_gain = monthly_revenue * users_affected * conversion_lift
# = $100K × 0.4 × 0.12 = $4,800/month

# Decision
net_benefit = revenue_gain - extra_cost
# = $4,800 - $15,000 = -$10,200/month (NEGATIVE!)

decision = "SKIP_MULTI_REGION"  # ❌ Not justified (losing $10K/month)

# Revisit when revenue 3x higher ($300K/month)
```

---

## Common Mistakes & Fixes

### 1. Not Planning for Failure

**Mistake**: Assume everything works perfectly.

```python
# No error handling
def process_order(order):
    payment.charge(order['amount'])  # What if payment fails?
    inventory.decrement(order['items'])  # What if inventory service down?
    shipping.create(order)  # What if address invalid?
```

**Fix**: Saga pattern with compensation

```python
def process_order_with_saga(order):
    try:
        # Step 1: Reserve inventory
        reservation_id = inventory.reserve(order['items'])

        try:
            # Step 2: Process payment
            payment_id = payment.charge(order['amount'])

            try:
                # Step 3: Create shipment
                shipment_id = shipping.create(order)

                # All succeeded!
                return {'status': 'success'}

            except ShippingError:
                # Compensate: Refund payment
                payment.refund(payment_id)
                raise

        except PaymentError:
            # Compensate: Release inventory
            inventory.release(reservation_id)
            raise

    except InventoryError:
        # First step failed, nothing to compensate
        raise
```

### 2. Ignoring Data Quality

**Mistake**: Assume data is always clean.

```python
# No validation
def calculate_revenue(orders_df):
    return orders_df['amount'].sum()
# What if 'amount' has nulls? Negative values? Strings?
```

**Fix**: Great Expectations

```python
import great_expectations as ge

def calculate_revenue(orders_df):
    # Wrap in GE DataFrame
    df = ge.dataset.PandasDataset(orders_df)

    # Validate expectations
    assert df.expect_column_values_to_not_be_null('amount').success
    assert df.expect_column_values_to_be_between('amount', 0, 1000000).success
    assert df.expect_column_values_to_be_of_type('amount', 'float64').success

    # Now safe to calculate
    return df['amount'].sum()
```

### 3. No Monitoring

**Mistake**: Deploy and forget.

**Fix**: Comprehensive observability

```python
# Metrics
cloudwatch.put_metric_data(MetricName='OrdersProcessed', Value=count)

# Logs
logger.info(f"Order {order_id} placed successfully")

# Traces
xray_recorder.capture('place_order')

# Alarms
cloudwatch.put_metric_alarm(
    AlarmName='HighErrorRate',
    MetricName='ErrorRate',
    Threshold=1.0,  # 1% error rate
    ActionsEnabled=True,
    AlarmActions=[sns_topic_arn]  # Page on-call engineer
)
```

---

## Summary: Golden Rules

1. **Start Simple**: Don't over-engineer (YAGNI principle)
2. **Measure First**: Use metrics to justify complexity
3. **Fail Gracefully**: Circuit breakers, retries, DLQs
4. **Events Over Calls**: Loose coupling via events
5. **Immutable Data**: Never overwrite in data lake
6. **Idempotent Operations**: Safe retries
7. **Schema Versioning**: Backward/forward compatibility
8. **Least Privilege**: Column-level permissions
9. **Encryption Everywhere**: Rest + transit + use
10. **Monitor Everything**: Metrics, logs, traces, alarms

---

**Next**: Read [resources.md](resources.md) for learning materials and certification paths.
