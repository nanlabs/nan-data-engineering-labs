# Exercise 01: Lambda Architecture Implementation

⏱️ **Estimated Time:** 3 hours
🎯 **Difficulty:** ⭐⭐⭐⭐ Advanced
🏗️ **Pattern:** Batch Layer + Speed Layer + Serving Layer

## Learning Objectives

By completing this exercise, you will:

✅ Implement complete Lambda Architecture with 3 layers
✅ Build batch processing with AWS Glue/Spark
✅ Build real-time processing with Kinesis + Lambda
✅ Merge batch and real-time results at query time
✅ Understand trade-offs: complexity vs capabilities
✅ Calculate cost-performance characteristics

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Raw Events                              │
│   (User actions: page views, purchases, clicks)             │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
    ┌──────────────┴──────────────┐
    ↓                             ↓
┌─────────────────────┐   ┌─────────────────────┐
│   Batch Layer       │   │   Speed Layer       │
│                     │   │                     │
│ S3 (Raw Data)       │   │ Kinesis Stream      │
│   ↓                 │   │   ↓                 │
│ Glue Job (Spark)    │   │ Lambda Function     │
│   ↓                 │   │   ↓                 │
│ S3 (Batch Views)    │   │ DynamoDB (RT Views) │
│ Athena (Query)      │   │                     │
│                     │   │                     │
│ Runs: Daily 03:00   │   │ Runs: Real-time     │
│ Latency: Hours      │   │ Latency: <1 second  │
│ Accuracy: 100%      │   │ Accuracy: ~95%      │
└─────────┬───────────┘   └─────────┬───────────┘
          └─────────────┬───────────┘
                        ↓
              ┌──────────────────┐
              │  Serving Layer   │
              │                  │
              │ Merge Logic:     │
              │ - Batch (>24h)   │
              │ - Real-time (<24h)│
              │                  │
              │ Output: Unified  │
              │ analytics view   │
              └──────────────────┘
```

## Use Case: E-commerce User Analytics

**Business Question**: "What is the total revenue and order count per user?"

**Challenge**:
- **Historical accuracy**: Need perfect count from all-time data (batch)
- **Real-time freshness**: Need today's orders immediately (speed)

**Lambda Solution**:
- **Batch Layer**: Process all orders daily → accurate lifetime metrics
- **Speed Layer**: Process orders real-time → today's metrics
- **Serving Layer**: Merge batch (yesterday) + real-time (today) = complete view

## Prerequisites

- AWS Account (LocalStack supported)
- Python 3.9+
- boto3, pandas, pyarrow
- Docker (for LocalStack)

## Files in This Exercise

| File | Lines | Purpose |
|------|-------|---------|
| **batch_layer.py** | ~400 | Spark job for historical data processing |
| **speed_layer.py** | ~350 | Kinesis + Lambda real-time processing |
| **serving_layer.py** | ~300 | Query logic merging batch + real-time |
| **README.md** | ~600 | This file (instructions) |

**Total**: 4 files, ~1,650 lines

## Setup

### 1. Install Dependencies

```bash
pip install boto3 pandas pyarrow awswrangler
```

### 2. Start LocalStack (Optional)

```bash
# From infrastructure directory
docker-compose up -d

# Verify
aws --endpoint-url=http://localhost:4566 s3 ls
```

### 3. Initialize AWS Resources

```bash
# Run batch_layer.py once to create resources
python batch_layer.py --mode setup
```

This creates:
- S3 bucket: `lambda-arch-batch-views`
- S3 bucket: `lambda-arch-raw-data`
- Kinesis stream: `orders-stream` (1 shard)
- DynamoDB table: `realtime-user-metrics` (PAY_PER_REQUEST)
- Glue database: `lambda_arch_db`
- Glue table: `user_metrics` (points to S3 batch views)

## Part 1: Batch Layer (Historical Accuracy)

### Objective

Process ALL historical data to create accurate aggregate views.

### Implementation: batch_layer.py

#### **Step 1: Load Raw Data from S3**

```python
# Read all orders (Parquet format)
df = spark.read.parquet("s3://lambda-arch-raw-data/orders/")

# Show sample
# +----------+-----------+--------+------------+
# | order_id | user_id   | amount | order_date |
# +----------+-----------+--------+------------+
# | ord_001  | user_123  | 99.99  | 2025-01-15 |
# | ord_002  | user_123  | 49.50  | 2025-02-20 |
# | ord_003  | user_456  | 199.00 | 2025-03-01 |
# +----------+-----------+--------+------------+
```

#### **Step 2: Aggregate by User**

```python
# PySpark aggregations
user_metrics = df.groupBy("user_id").agg(
    F.count("order_id").alias("lifetime_orders"),
    F.sum("amount").alias("lifetime_revenue"),
    F.avg("amount").alias("avg_order_value"),
    F.min("order_date").alias("first_order_date"),
    F.max("order_date").alias("last_order_date")
)

# Result:
# +---------+----------------+-----------------+----------------+
# | user_id | lifetime_orders| lifetime_revenue| avg_order_value|
# +---------+----------------+-----------------+----------------+
# | user_123| 25             | 1,247.50        | 49.90          |
# | user_456| 10             | 890.00          | 89.00          |
# +---------+----------------+-----------------+----------------+
```

#### **Step 3: Write to Batch Views (S3 + Athena)**

```python
# Write partitioned by date (enables incremental updates)
user_metrics.write.mode("overwrite").partitionBy("batch_date").parquet(
    "s3://lambda-arch-batch-views/user_metrics/"
)

# Create Glue table for Athena queries
glue.create_table(
    DatabaseName='lambda_arch_db',
    TableInput={
        'Name': 'user_metrics',
        'StorageDescriptor': {
            'Location': 's3://lambda-arch-batch-views/user_metrics/',
            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
            'Columns': [
                {'Name': 'user_id', 'Type': 'string'},
                {'Name': 'lifetime_orders', 'Type': 'bigint'},
                {'Name': 'lifetime_revenue', 'Type': 'double'},
                {'Name': 'avg_order_value', 'Type': 'double'}
            ],
            'PartitionKeys': [
                {'Name': 'batch_date', 'Type': 'string'}
            ]
        }
    }
)
```

### Running Batch Layer

```bash
# Option 1: LocalStack (free, for testing)
python batch_layer.py --env localstack --date 2026-03-09

# Option 2: Real AWS (uses Glue job)
python batch_layer.py --env aws --date 2026-03-09 --dry-run false

# Option 3: Generate sample data first
python batch_layer.py --mode generate-data --records 100000
python batch_layer.py --mode batch-process
```

### Expected Output

```
=== Batch Layer Execution ===
📊 Processing Date: 2026-03-09
📁 Raw Data: s3://lambda-arch-raw-data/orders/year=2026/month=03/
   └─ Records: 1,247,893 orders

⚙️  Spark Job:
   ├─ Aggregating by user_id...
   ├─ Computing lifetime metrics...
   └─ Writing to s3://lambda-arch-batch-views/

✅ Batch Views Created:
   ├─ Users: 45,231
   ├─ Total Revenue: $4,892,450.75
   ├─ Avg Orders per User: 27.6
   └─ Output Size: 8.3 MB (Parquet, compressed)

⏱️  Execution Time: 8m 32s
💰 Estimated Cost: $0.85 (Glue DPUs)

🔍 Query Example (Athena):
   SELECT * FROM user_metrics WHERE user_id = 'user_123'
```

### Performance Tuning

**Slow Performance** (>1 hour for 10M orders):
1. Increase Glue DPUs: `--number-of-workers 10` (default: 2)
2. Partition raw data by date: `s3://.../year=2026/month=03/day=09/`
3. Use Delta Lake: `df.write.format("delta").save()` (faster updates)
4. Enable predicate pushdown: Query only needed partitions

---

## Part 2: Speed Layer (Real-Time Processing)

### Objective

Process recent events (last 24 hours) in real-time for immediate insights.

### Implementation: speed_layer.py

#### **Step 1: Send Events to Kinesis**

```python
# Simulate real-time orders
def send_order_event(order):
    kinesis.put_record(
        StreamName='orders-stream',
        Data=json.dumps(order),
        PartitionKey=order['user_id']  # Same user → same shard (ordering)
    )

# Example event
order_event = {
    "event_type": "OrderPlaced",
    "order_id": "ord_20260309_123",
    "user_id": "user_123",
    "amount": 79.99,
    "timestamp": "2026-03-09T10:30:45.123Z",
    "items": [
        {"product_id": "prod_456", "quantity": 2, "price": 39.99}
    ]
}

send_order_event(order_event)
```

#### **Step 2: Lambda Processes Stream**

```python
# Lambda handler (invoked by Kinesis)
def lambda_handler(event, context):
    for record in event['Records']:
        # Decode Kinesis record
        payload = base64.b64decode(record['kinesis']['data'])
        order = json.loads(payload)

        # Update real-time metrics in DynamoDB
        update_realtime_metrics(order)

def update_realtime_metrics(order):
    # Atomic increment
    dynamodb.update_item(
        TableName='realtime-user-metrics',
        Key={'user_id': order['user_id']},
        UpdateExpression='''
            SET orders_today = if_not_exists(orders_today, :zero) + :one,
                revenue_today = if_not_exists(revenue_today, :zero) + :amount,
                last_order_time = :timestamp
        ''',
        ExpressionAttributeValues={
            ':zero': Decimal('0'),
            ':one': 1,
            ':amount': Decimal(str(order['amount'])),
            ':timestamp': order['timestamp']
        }
    )
```

#### **Step 3: Reset Daily** (Midnight Cron)

```python
# EventBridge rule: Trigger daily at midnight
def reset_realtime_metrics():
    # Scan all users
    response = dynamodb.scan(TableName='realtime-user-metrics')

    # Archive to S3 (before reset)
    archive_data = [{
        'user_id': item['user_id'],
        'orders_today': int(item['orders_today']),
        'revenue_today': float(item['revenue_today']),
        'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    }]

    s3.put_object(
        Bucket='lambda-arch-realtime-archive',
        Key=f"year={year}/month={month}/day={day}/metrics.json",
        Body=json.dumps(archive_data)
    )

    # Reset counters to 0
    for item in response['Items']:
        dynamodb.update_item(
            TableName='realtime-user-metrics',
            Key={'user_id': item['user_id']},
            UpdateExpression='SET orders_today = :zero, revenue_today = :zero',
            ExpressionAttributeValues={':zero': Decimal('0')}
        )
```

### Running Speed Layer

```bash
# Start producer (sends events to Kinesis)
python speed_layer.py --mode producer --rate 100
# Sends 100 events/second

# Start consumer (Lambda simulation locally)
python speed_layer.py --mode consumer --process-continuous

# Check DynamoDB metrics
python speed_layer.py --mode query --user-id user_123
```

### Expected Output

```
=== Speed Layer Execution ===
📡 Kinesis Stream: orders-stream
   ├─ Shards: 1 (1 MB/sec capacity)
   ├─ Retention: 24 hours
   └─ Enhanced Fan-out: Disabled

🚀 Producer Mode:
   ├─ Sending orders at 100 events/sec...
   ├─ Events sent: 1,000 (10 seconds)
   ├─ Bytes sent: 245 KB
   └─ PartitionKeys: 520 unique users

📥 Consumer Mode (Lambda Simulator):
   ├─ Processing records...
   ├─ Batch size: 100 records
   ├─ Processing time: 342ms
   └─ DynamoDB updates: 100 writes (atomic increments)

✅ Real-Time Metrics Updated:
   ├─ Users updated: 520
   ├─ Total orders today: 1,000
   ├─ Total revenue today: $45,782.50
   └─ Latency: <500ms (event → visible in DynamoDB)

💰 Estimated Cost (1M events/day):
   ├─ Kinesis: $19/day (1 MB/sec, 1 shard)
   ├─ Lambda: $4/day (1M invocations)
   ├─ DynamoDB: $8/day (writes)
   └─ Total: $31/day = $930/month
```

---

## Part 3: Serving Layer (Query Merging)

### Objective

Provide unified query interface merging batch + real-time data.

### Implementation: serving_layer.py

#### **Query Patterns**

##### **Pattern 1**: Recent data from Speed Layer

```python
def get_today_metrics(user_id):
    # Query DynamoDB (real-time)
    response = dynamodb.get_item(
        TableName='realtime-user-metrics',
        Key={'user_id': user_id}
    )

    return {
        'user_id': user_id,
        'orders_today': response['Item'].get('orders_today', 0),
        'revenue_today': float(response['Item'].get('revenue_today', 0))
    }
```

##### **Pattern 2**: Historical data from Batch Layer

```python
def get_lifetime_metrics(user_id):
    # Query Athena (batch views)
    query = f"""
    SELECT
        lifetime_orders,
        lifetime_revenue,
        avg_order_value,
        first_order_date,
        last_order_date
    FROM user_metrics
    WHERE user_id = '{user_id}'
      AND batch_date = (SELECT MAX(batch_date) FROM user_metrics)
    """

    result = athena.execute_query(query)
    return result[0] if result else {}
```

##### **Pattern 3**: Merged Complete View

```python
def get_complete_user_metrics(user_id):
    # Fetch from both layers (parallel)
    with ThreadPoolExecutor(max_workers=2) as executor:
        batch_future = executor.submit(get_lifetime_metrics, user_id)
        realtime_future = executor.submit(get_today_metrics, user_id)

        batch_data = batch_future.result()
        realtime_data = realtime_future.result()

    # Merge
    return {
        'user_id': user_id,

        # From batch (accurate, up to yesterday)
        'lifetime_orders': batch_data.get('lifetime_orders', 0),
        'lifetime_revenue': batch_data.get('lifetime_revenue', 0),
        'avg_order_value': batch_data.get('avg_order_value', 0),

        # From real-time (today only)
        'orders_today': realtime_data.get('orders_today', 0),
        'revenue_today': realtime_data.get('revenue_today', 0),

        # Combined (total = lifetime + today)
        'total_orders': batch_data.get('lifetime_orders', 0) + realtime_data.get('orders_today', 0),
        'total_revenue': batch_data.get('lifetime_revenue', 0) + realtime_data.get('revenue_today', 0),

        # Metadata
        'batch_cutoff': batch_data.get('last_batch_date', 'Unknown'),
        'realtime_updated_at': realtime_data.get('last_order_time', 'Never')
    }
```

### Advanced Query: Top 10 Users by Revenue

```python
def get_top_users_by_revenue(limit=10):
    # Step 1: Get top users from batch view (baseline)
    athena_query = f"""
    SELECT user_id, lifetime_revenue
    FROM user_metrics
    WHERE batch_date = (SELECT MAX(batch_date) FROM user_metrics)
    ORDER BY lifetime_revenue DESC
    LIMIT {limit * 2}  -- Get 2x, then rerank with realtime
    """

    batch_top_users = athena.execute_query(athena_query)

    # Step 2: Get today's revenue for these users from DynamoDB
    user_ids = [user['user_id'] for user in batch_top_users]

    batch_get_response = dynamodb.batch_get_item(
        RequestItems={
            'realtime-user-metrics': {
                'Keys': [{'user_id': uid} for uid in user_ids]
            }
        }
    )

    realtime_data = {
        item['user_id']: float(item.get('revenue_today', 0))
        for item in batch_get_response['Responses']['realtime-user-metrics']
    }

    # Step 3: Merge and rerank
    combined = []
    for user in batch_top_users:
        total_revenue = user['lifetime_revenue'] + realtime_data.get(user['user_id'], 0)
        combined.append({
            'user_id': user['user_id'],
            'total_revenue': total_revenue,
            'lifetime_revenue': user['lifetime_revenue'],
            'revenue_today': realtime_data.get(user['user_id'], 0)
        })

    # Sort by total revenue
    combined.sort(key=lambda x: x['total_revenue'], reverse=True)

    return combined[:limit]
```

### Running Serving Layer

```bash
# Query single user
python serving_layer.py --user-id user_123

# Query top users
python serving_layer.py --mode top-users --limit 10

# API server (FastAPI)
python serving_layer.py --mode api --port 8000
# Then: curl http://localhost:8000/api/users/user_123
```

### Expected Output

```
=== Serving Layer Query ===
👤 User: user_123

📊 Complete Metrics (Merged):
   ├─ Total Orders: 28 (lifetime: 25 + today: 3)
   ├─ Total Revenue: $1,487.47 (lifetime: $1,247.50 + today: $239.97)
   ├─ Avg Order Value: $53.12
   └─ Member Since: 2024-06-15 (630 days)

⏱️  Data Freshness:
   ├─ Batch Layer: Updated 2026-03-09 03:00 AM (7 hours ago)
   │  └─ Includes orders up to: 2026-03-08 23:59:59
   │
   └─ Speed Layer: Real-time (last update: 2s ago)
      └─ Includes orders from: 2026-03-09 00:00:00

🔍 Query Performance:
   ├─ Athena query: 1.2 seconds (scanned 8.3 MB)
   ├─ DynamoDB query: 12 ms (single item read)
   └─ Total: 1.21 seconds

💰 Query Cost:
   ├─ Athena: $0.000042 ($5/TB × 0.0000083 TB)
   ├─ DynamoDB: $0.00000025 (1 RCU × $0.00025/hour)
   └─ Total: $0.000042 per query
```

---

## Validation Tasks

### Task 1: Verify Batch Layer Accuracy

```bash
# Generate 10K orders with known totals
python batch_layer.py --mode generate-test-data --records 10000

# Expected users: 100
# Expected total revenue: $500,000 (avg $50/order)

# Run batch processing
python batch_layer.py --mode batch-process

# Query results
python serving_layer.py --mode validate-batch

# ✅ Validation: Total revenue matches expected ($500,000)
```

### Task 2: Verify Real-Time Latency

```bash
# Send order, measure time until visible in DynamoDB
python speed_layer.py --mode latency-test --samples 100

# Expected: <1 second (p50), <2 seconds (p99)
```

### Task 3: Verify Merge Logic

```bash
# User has:
# - Batch: 20 orders, $1,000 revenue (yesterday)
# - Real-time: 3 orders, $150 revenue (today)

# Query merged view
result = serving_layer.get_complete_user_metrics('user_test')

# ✅ Validation:
assert result['total_orders'] == 23  # 20 + 3
assert result['total_revenue'] == 1150.00  # $1,000 + $150
```

---

## Challenges

### Challenge 1: Incremental Batch Updates

**Problem**: Full reprocessing expensive (10M orders = $50/day).

**Task**: Implement incremental updates (only process new data).

**Hint**:
```python
# Instead of reading all data
df = spark.read.parquet("s3://raw-data/orders/")  # All-time (TB)

# Read only yesterday's partition
df = spark.read.parquet("s3://raw-data/orders/date=2026-03-08/")  # 1 day (GB)

# Merge with existing batch views (UPSERT logic)
```

### Challenge 2: Handle Late Events

**Problem**: Order placed at 23:58, arrives at speed layer at 00:02 (next day).

**Task**: Implement watermarks to handle late arrivals.

**Hint**:
```python
# Track event_time vs processing_time
event_time = datetime.fromisoformat(order['timestamp'])
processing_time = datetime.now()
delay = (processing_time - event_time).total_seconds()

if delay > 3600:  # 1 hour late
    # Don't update today's metrics (will be in tomorrow's batch)
    logger.warning(f"Late event: {delay}s delay")
else:
    update_realtime_metrics(order)
```

### Challenge 3: Cost Optimization

**Problem**: Kinesis $930/month expensive for startup.

**Task**: Calculate break-even vs batch-only.

**Analysis**:
```python
# Batch-only: 24-hour delay, $255/month (Glue)
# Lambda (batch + speed): <1 second delay, $1,185/month (Glue + Kinesis)
# Extra cost: $930/month

# When is real-time worth it?
# If 1-second data increases revenue by >$930/month → Worth it
# Example: Fraud detection (save $10K/month in fraud) → Justified
```

---

## Key Learnings

### Advantages of Lambda Architecture

✅ **Best of Both Worlds**: Accuracy (batch) + Speed (real-time)
✅ **Fault Tolerance**: Batch reprocessing fixes errors
✅ **Proven at Scale**: Netflix, LinkedIn (trillion events/day)
✅ **Incremental Migration**: Start with batch, add speed layer later

### Disadvantages

❌ **Complexity**: Two processing paradigms (Spark + Kinesis/Flink)
❌ **Code Duplication**: Similar logic in batch and speed layers
❌ **Storage Costs**: Data duplicated in batch views + real-time views
❌ **Operational Overhead**: Monitor/maintain 2 systems

### When to Use Lambda Architecture

**✅ Use When**:
- Accuracy is critical (banking, healthcare, financial reporting)
- Complex batch analytics (ML training, multi-table joins)
- Reprocessing is frequent (fix bugs, add features, change metrics)
- Team has expertise in both batch (Spark) and streaming (Kinesis/Flink)
- Cost of errors > cost of complexity (e.g., wrong fraud detection = lost $$$)

**❌ Don't Use When**:
- Simple analytics (single-table aggregations)
- Small team (<5 engineers, can't maintain 2 systems)
- Cost-sensitive (batch-only is 3x cheaper)
- Near-real-time acceptable (5-minute delay OK)

### Cost Comparison

**Lambda Architecture** (10M events/day):
- Batch: $255/month (Glue, daily)
- Speed: $930/month (Kinesis + Lambda)
- Storage: $150/month (S3 + DynamoDB)
- **Total: $1,335/month**

**Batch-Only** (10M events/day):
- Batch: $255/month (Glue, daily)
- Storage: $50/month (S3 only)
- **Total: $305/month**

**Difference**: $1,030/month (4.4x more expensive)

**Justification**: If real-time insights generate >$1,030/month extra revenue, Lambda arch is worth it.

---

## Real-World Examples

### Netflix: Personalization Lambda Architecture

**Batch Layer**:
- Spark job (daily): Collaborative filtering (all user-movie interactions)
- Output: Matrix factorization model (users × movies)
- Time: 4 hours (process 1B+ interactions)

**Speed Layer**:
- Kinesis: User viewing session (play, pause, stop)
- Lambda: Update current session preferences
- Time: <100ms (real-time)

**Serving Layer**:
- Merge: Batch recommendations + session boost
- Example: "Continue Watching" row (batch) + "Because you watched X" (session)

**Result**: <100ms recommendation latency, personalized for 200M users.

### LinkedIn: Feed Ranking Lambda Architecture

**Batch Layer**:
- Hadoop job (daily): Compute user-post relevance scores
- Output: Precomputed scores for 800M members

**Speed Layer**:
- Kafka: User interactions (like, comment, share)
- Samza: Update trending score (viral content)

**Serving Layer**:
- Merge: Batch (personal relevance) + Speed (trending) = Feed ranking

**Result**: Sub-second feed generation, 99.9% uptime.

---

## Next Steps

After completing Exercise 01:

1. ✅ **Compare with Kappa**: Move to Exercise 02 (stream-only alternative)
2. 🔄 **Refactor**: Simplify merge logic (extract to library)
3. 📊 **Dashboard**: Build QuickSight dashboard querying serving layer
4. 💰 **Cost Analysis**: Run for 1 week, analyze actual costs
5. 🛡️ **Production**: Add monitoring (CloudWatch alarms), error handling

**Estimated Savings vs Batch-Only**:
- **Latency Reduction**: 24 hours → <1 second (86,400x faster)
- **Business Value**: Enables real-time fraud detection, personalization
- **Extra Cost**: $1,030/month (must justify with revenue increase)

---

## Troubleshooting

### Issue 1: Batch Job Times Out

**Symptom**: Glue job fails after 2 hours.

**Solutions**:
1. Increase DPUs: `--number-of-workers 20`
2. Filter data: `df.where(F.col("date") >= "2026-01-01")`  # Only 1 year
3. Enable predicate pushdown: Partition raw data by date

### Issue 2: Kinesis Throttling

**Symptom**: `ProvisionedThroughputExceededException`

**Solutions**:
1. Increase shards: `kinesis.update_shard_count(StreamName='orders-stream', TargetShardCount=5)`
2. Use record aggregation: `kinesis_agg` library (100 records → 1 API call)
3. Batch writes: `put_records()` instead of `put_record()` (500 records/call)

### Issue 3: DynamoDB Hot Partition

**Symptom**: Some users have 1,000x more orders (celebrities).

**Solutions**:
1. Partition key: Change from `user_id` to `user_id#date` (distribute writes)
2. DynamoDB Accelerator (DAX): Cache hot items
3. Sharding: Split hot users across multiple items

### Issue 4: Query Latency > 10 seconds

**Symptom**: Serving layer slow.

**Solutions**:
1. Cache results: ElastiCache for frequent queries (user dashboards)
2. Materialize merged view: Run serving layer logic in batch (daily), cache results
3. Index optimization: Add GSI (Global Secondary Index) on DynamoDB

---

## Additional Resources

**AWS Documentation**:
- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/)
- [Kinesis Developer Guide](https://docs.aws.amazon.com/kinesis/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

**Blog Posts**:
- [Lambda Architecture at Uber](https://eng.uber.com/big-data-messaging/)
- [Netflix Lambda Processing](https://netflixtechblog.com/lambda-processing-f34b5e6b5f8c)

**Video**:
- [AWS re:Invent: Building Lambda Architecture on AWS](https://www.youtube.com/watch?v=example) (fictional link)

---

**Status**: 🚧 Ready to Implement
**Next Exercise**: Exercise 02 - Kappa Architecture (simpler alternative)
