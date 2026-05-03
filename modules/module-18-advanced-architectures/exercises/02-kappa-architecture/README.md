# Exercise 02: Kappa Architecture Implementation

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐⭐ Advanced
🏗️ **Pattern:** Stream-Only Processing with Reprocessing Capability

## Learning Objectives

By completing this exercise, you will:

✅ Implement Kappa Architecture (stream-only alternative to Lambda)
✅ Build stream processing with Kinesis + Flink SQL
✅ Manage materialized views with blue-green deployments
✅ Implement reprocessing by replaying stream
✅ Compare Kappa vs Lambda complexity/cost

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Stream                              │
│         (Kinesis: 365-day retention)                        │
│   All data = immutable append-only log                      │
└────────────────────┬────────────────────────────────────────┘
                     ↓
         ┌───────────┴───────────┐
         ↓                       ↓
┌──────────────────┐    ┌──────────────────┐
│ Stream Processor │    │ Reprocessing Job │
│ (Version 1)      │    │ (Version 2)      │
│                  │    │                  │
│ Kinesis Flink    │    │ Same code!       │
│   ↓              │    │   ↓              │
│ Materialized     │    │ New Materialized │
│ View v1          │    │ View v2          │
│ (DynamoDB)       │    │ (DynamoDB_v2)    │
│                  │    │                  │
│ Reads: Prod API  │    │ Reads: Testing   │
└──────────────────┘    └──────────────────┘
         │                       │
         └───────────┬───────────┘
                     ↓
              Blue-Green Swap
           (Switch API to v2)
```

**Key Difference from Lambda Architecture**:
- ❌ No separate batch layer
- ✅ Single stream processing logic
- ✅ Reprocessing = replay stream with new code

## Advantages Over Lambda Architecture

| Aspect | Lambda Arch | Kappa Arch |
|--------|-------------|------------|
| **Code Duplication** | Batch + Speed (2 codebases) | Stream only (1 codebase) |
| **Operational Complexity** | High (2 systems) | Medium (1 system) |
| **Reprocessing** | Batch job (hours) | Replay stream (minutes to hours) |
| **Storage Cost** | S3 + DynamoDB | Kinesis extended retention |
| **Team Size** | 5+ engineers | 2-3 engineers |
| **Cost (10M events/day)** | $1,335/month | $890/month (33% cheaper) |

**When to Use Kappa**:
- ✅ Simple aggregations (count, sum, average)
- ✅ Small team (<5 engineers)
- ✅ Frequent reprocessing (change metrics often)
- ✅ Cost-sensitive (no separate batch layer)

**When NOT to Use Kappa**:
- ❌ Complex batch analytics (multi-table joins, ML training)
- ❌ Stream retention insufficient (<365 days history needed)
- ❌ Interactive queries (Kappa = write path, not ad-hoc SQL)

## Use Case: Real-Time E-commerce Dashboards

**Business Question**: "What are current sales by category?"

**Kappa Solution**:
1. **Event Stream**: All orders → Kinesis (365-day retention)
2. **Stream Processor**: Flink job → aggregate by category
3. **Materialized View**: DynamoDB table (category metrics)
4. **API**: Query DynamoDB for dashboard

**Reprocessing Example** (add new metric):
1. Write new Flink job (add average_discount column)
2. Deploy to new DynamoDB table (`category_metrics_v2`)
3. Replay last 365 days from Kinesis
4. Validate new view
5. Swap API to use `category_metrics_v2`
6. Delete old view (`category_metrics_v1`)

## Prerequisites

- AWS Account (LocalStack supported)
- Python 3.9+
- Docker (for Flink local testing)
- boto3, pandas, kafka-python (for stream simulation)

## Files in This Exercise

| File | Lines | Purpose |
|------|-------|---------|
| **stream_processor.py** | ~450 | Kinesis + Flink stream processing |
| **materialized_views.py** | ~400 | View management (create, update, swap) |
| **replay_handler.py** | ~350 | Reprocessing via stream replay |
| **README.md** | ~700 | This file (instructions) |

**Total**: 4 files, ~1,900 lines

## Setup

### 1. Install Dependencies

```bash
pip install boto3 pandas kafka-python
```

### 2. Start LocalStack with Kinesis

```bash
# From infrastructure directory
docker-compose up -d

# Create stream with extended retention
aws --endpoint-url=http://localhost:4566 kinesis create-stream \
  --stream-name orders-kappa \
  --shard-count 2

# Set retention to 365 days (max)
aws --endpoint-url=http://localhost:4566 kinesis increase-stream-retention-period \
  --stream-name orders-kappa \
  --retention-period-hours 8760  # 365 days
```

### 3. Initialize Resources

```bash
python stream_processor.py --mode setup
```

---

## Part 1: Stream Processor (Stateful Aggregations)

### Objective

Process event stream continuously to maintain up-to-date materialized views.

### Implementation: stream_processor.py

#### **Flink SQL Query** (Tumbling Windows)

```sql
-- Category sales (5-minute tumbling window)
CREATE TABLE category_sales_5min AS
SELECT
    window_start,
    window_end,
    category,
    COUNT(*) as order_count,
    SUM(amount) as revenue,
    AVG(amount) as avg_order_value,
    COUNT(DISTINCT user_id) as unique_buyers
FROM TABLE(
    TUMBLE(TABLE orders, DESCRIPTOR(order_timestamp), INTERVAL '5' MINUTES)
)
GROUP BY window_start, window_end, category;
```

#### **Output to DynamoDB** (Sink Connector)

```python
def write_to_dynamodb_sink(window_result):
    """
    Write Flink window result to DynamoDB.

    Args:
        window_result: Dict with aggregated metrics
    """
    dynamodb.update_item(
        TableName='category_metrics_v1',
        Key={
            'category': window_result['category'],
            'window_start': window_result['window_start']
        },
        UpdateExpression='''
            SET order_count = :orders,
                revenue = :revenue,
                avg_order_value = :avg,
                unique_buyers = :buyers,
                updated_at = :now
        ''',
        ExpressionAttributeValues={
            ':orders': window_result['order_count'],
            ':revenue': Decimal(str(window_result['revenue'])),
            ':avg': Decimal(str(window_result['avg_order_value'])),
            ':buyers': window_result['unique_buyers'],
            ':now': datetime.now().isoformat()
        }
    )
```

### Running Stream Processor

```bash
# Start processor (runs continuously)
python stream_processor.py --mode process --window-minutes 5

# Monitor metrics
python stream_processor.py --mode monitor

# Query current state
python stream_processor.py --mode query --category Electronics
```

### Expected Output

```
=== Kappa Stream Processor ===
📊 Mode: Continuous Processing
⏱️  Window Size: 5 minutes (tumbling)
📡 Source: Kinesis stream (orders-kappa)
💾 Sink: DynamoDB table (category_metrics_v1)

🚀 Starting processor...
   ├─ Flink Application: kappa-processor-v1
   ├─ Parallelism: 2
   └─ Checkpointing: Every 60 seconds (S3)

⚙️  Processing windows:
   [10:00-10:05] Electronics:  142 orders, $8,492.50 revenue
   [10:00-10:05] Clothing:     89 orders, $4,231.00 revenue
   [10:00-10:05] Home:         67 orders, $3,125.75 revenue

   [10:05-10:10] Electronics:  156 orders, $9,284.25 revenue
   [10:05-10:10] Clothing:     92 orders, $4,512.00 revenue
   ...

✅ Metrics written to DynamoDB
⏱️  Processing Latency: <5 seconds (event → visible)
💰 Cost: $15.30/day (Kinesis + Flink)
```

---

## Part 2: Materialized View Management

### Objective

Manage multiple versions of materialized views for blue-green deployments.

### Implementation: materialized_views.py

#### **View Versioning**

```python
class MaterializedViewManager:
    """Manage versioned materialized views."""

    def create_view_version(self, version: int) -> str:
        """
        Create new DynamoDB table for materialized view.

        Args:
            version: View version number

        Returns:
            Table name
        """
        table_name = f"category_metrics_v{version}"

        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'category', 'KeyType': 'HASH'},
                {'AttributeName': 'window_start', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'category', 'AttributeType': 'S'},
                {'AttributeName': 'window_start', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        logger.info(f"✅ Created view: {table_name}")
        return table_name

    def swap_active_view(self, old_version: int, new_version: int) -> None:
        """
        Blue-green deployment: Switch API to use new view.

        Args:
            old_version: Current version
            new_version: New version to activate
        """
        # Update parameter store (API reads from here)
        ssm.put_parameter(
            Name='/kappa/active_view_version',
            Value=str(new_version),
            Type='String',
            Overwrite=True
        )

        logger.info(f"✅ Swapped active view: v{old_version} → v{new_version}")

        # Wait 5 minutes (ensure API picked up change)
        time.sleep(300)

        # Delete old view
        dynamodb.delete_table(TableName=f"category_metrics_v{old_version}")
        logger.info(f"🗑️  Deleted old view: v{old_version}")
```

### Blue-Green Deployment Flow

```
Step 1: Current State
   API → category_metrics_v1 (production)

Step 2: Create New View
   API → category_metrics_v1 (production)
   Reprocessing → category_metrics_v2 (filling)

Step 3: Validate New View
   API → category_metrics_v1 (production)
   category_metrics_v2 (ready, validated)

Step 4: Swap Active View
   API → category_metrics_v2 (production)
   category_metrics_v1 (old, will delete)

Step 5: Clean Up
   API → category_metrics_v2 (production)
   category_metrics_v1 (deleted)
```

---

## Part 3: Reprocessing via Replay

### Objective

Reprocess historical data by replaying event stream.

### Implementation: replay_handler.py

#### **Replay Process**

```python
def replay_stream(
    stream_name: str,
    start_timestamp: datetime,
    end_timestamp: datetime,
    target_table: str
) -> Dict[str, Any]:
    """
    Replay events from Kinesis stream.

    Args:
        stream_name: Kinesis stream name
        start_timestamp: Start time
        end_timestamp: End time
        target_table: DynamoDB table for output

    Returns:
        Dict with replay statistics
    """
    logger.info("=== Starting Stream Replay ===")
    logger.info(f"   Stream: {stream_name}")
    logger.info(f"   Time Range: {start_timestamp} to {end_timestamp}")
    logger.info(f"   Target: {target_table}")

    # Get shard iterator at timestamp
    response = kinesis.describe_stream(StreamName=stream_name)
    shards = response['StreamDescription']['Shards']

    total_replayed = 0

    for shard in shards:
        shard_id = shard['ShardId']

        # Get iterator at start timestamp
        iterator_response = kinesis.get_shard_iterator(
            StreamName=stream_name,
            ShardId=shard_id,
            ShardIteratorType='AT_TIMESTAMP',
            Timestamp=start_timestamp
        )

        shard_iterator = iterator_response['ShardIterator']

        # Read until end timestamp
        while shard_iterator:
            records_response = kinesis.get_records(
                ShardIterator=shard_iterator,
                Limit=1000
            )

            records = records_response['Records']

            if not records:
                break

            # Check if we've passed end timestamp
            last_record_time = records[-1]['ApproximateArrivalTimestamp']
            if last_record_time >= end_timestamp:
                # Filter records within range
                records = [
                    r for r in records
                    if r['ApproximateArrivalTimestamp'] <= end_timestamp
                ]

            # Process records (same logic as stream processor)
            for record in records:
                event = json.loads(record['Data'])
                process_event(event, target_table)
                total_replayed += 1

            # Update iterator
            shard_iterator = records_response.get('NextShardIterator')

            # Stop if past end time
            if last_record_time >= end_timestamp:
                break

    logger.info(f"✅ Replayed {total_replayed:,} events")

    return {'replayed_events': total_replayed}
```

### Reprocessing Scenario

**Initial Deployment** (v1):
```python
# v1: Calculate simple metrics
flink_sql_v1 = """
SELECT
    category,
    COUNT(*) as order_count,
    SUM(amount) as revenue
FROM orders
GROUP BY category
"""
```

**Add New Metric** (v2):
```python
# v2: Add average discount
flink_sql_v2 = """
SELECT
    category,
    COUNT(*) as order_count,
    SUM(amount) as revenue,
    AVG(discount_percent) as avg_discount  -- NEW COLUMN
FROM orders
GROUP BY category
"""
```

**Reprocessing Steps**:
1. Deploy v2 code (writes to `category_metrics_v2`)
2. Replay last 365 days from Kinesis
3. Validate v2 results (spot check numbers)
4. Swap API to read from v2
5. Delete v1

### Running Replay

```bash
# Replay last 7 days
python replay_handler.py \
  --start "2026-03-02" \
  --end "2026-03-09" \
  --target-table category_metrics_v2

# Replay specific time window
python replay_handler.py \
  --start "2026-03-09T00:00:00" \
  --end "2026-03-09T12:00:00" \
  --target-table category_metrics_v2
```

### Expected Output

```
=== Stream Replay Handler ===
📅 Time Range: 2026-03-02 00:00:00 to 2026-03-09 23:59:59
   └─ Duration: 7 days (168 hours)

📡 Kinesis Stream: orders-kappa
   ├─ Shards: 2
   ├─ Retention: 365 days (8,760 hours)
   └─ Estimated events: ~70,000,000 (10M/day × 7 days)

🔄 Replay Progress:
   [========================================] 100%

   Shard 0: 35,241,823 events replayed
   Shard 1: 34,892,451 events replayed

   Total: 70,134,274 events

💾 Materialized View: category_metrics_v2
   ├─ Categories: 8
   ├─ Windows: 2,016 (7 days × 24 hours × 12 windows/hour)
   └─ Total Records: 16,128

⏱️  Replay Time: 42 minutes
💰 Replay Cost: $0 (no additional Kinesis cost for reads)

✅ Replay Complete
   Next: Validate v2, then swap active view
```

---

## Validation Tasks

### Task 1: Compare Kappa vs Lambda Complexity

**Metrics**:
- Lines of code (LoC)
- Number of services
- Operational overhead (monitoring dashboards, alerts)

**Expected**:
```
Lambda Architecture:
  ├─ Batch Layer: 500 LoC
  ├─ Speed Layer: 400 LoC
  ├─ Serving Layer: 300 LoC
  └─ Total: 1,200 LoC, 5 services (EMR, Kinesis, Lambda, Redshift, DynamoDB)

Kappa Architecture:
  ├─ Stream Processor: 450 LoC
  ├─ View Manager: 400 LoC
  ├─ Replay Handler: 350 LoC
  └─ Total: 1,200 LoC, 2 services (Kinesis, DynamoDB)

✅ Kappa: 60% fewer services (operational simplicity)
```

### Task 2: Validate Reprocessing

```bash
# Step 1: Deploy v1 (simple metrics)
python stream_processor.py --version 1 --deploy

# Step 2: Let it run for 1 hour (accumulate data)

# Step 3: Deploy v2 (new metric added)
python stream_processor.py --version 2 --deploy

# Step 4: Replay last hour
python replay_handler.py --start "1 hour ago" --target-table category_metrics_v2

# Step 5: Validate v2 has new column
python materialized_views.py --table category_metrics_v2 --validate

# ✅ Expected: v2 includes avg_discount column
```

### Task 3: Measure Replay Time

```bash
# Replay different time ranges
python replay_handler.py --start "1 day ago" --benchmark
# Expected: ~6 minutes

python replay_handler.py --start "7 days ago" --benchmark
# Expected: ~42 minutes

python replay_handler.py --start "30 days ago" --benchmark
# Expected: ~3 hours

# Rule of thumb: 10M events/day × 30 days = 300M events → ~3 hours replay
```

---

## Challenges

### Challenge 1: Handle Stream Throughput Limits

**Problem**: Kinesis replay limited to 2 MB/sec per shard.

**Task**: Calculate replay time for 1TB of data.

**Solution**:
```python
# Data: 1 TB = 1,048,576 MB
# Shards: 10 (each 2 MB/sec read capacity)
# Throughput: 10 shards × 2 MB/sec = 20 MB/sec
# Time: 1,048,576 MB ÷ 20 MB/sec = 52,428 seconds = 14.6 hours

# Optimization: Increase shards (costs $0.015/shard-hour)
# 50 shards: 100 MB/sec → 2.9 hours (11.6 hours saved)
# Extra cost: 40 shards × 14.6 hours × $0.015 = $8.76 (worth it!)
```

### Challenge 2: Blue-Green Deployment

**Problem**: Switching from v1 to v2 without downtime.

**Task**: Implement gradual rollout (canary deployment).

**Solution**:
```python
# Phase 1: Route 10% traffic to v2
if random.random() < 0.10:
    active_table = 'category_metrics_v2'
else:
    active_table = 'category_metrics_v1'

# Phase 2: Monitor v2 error rate (CloudWatch)
# If error_rate_v2 < error_rate_v1: Increase to 50%

# Phase 3: Full rollout (100% to v2)
# Phase 4: Delete v1
```

### Challenge 3: Schema Evolution

**Problem**: Add new field to event (breaking change).

**Task**: Support both old and new schemas during transition.

**Solution**:
```python
def process_event(event):
    # Old schema (legacy events)
    if 'discount_percent' not in event:
        event['discount_percent'] = 0.0  # Default for old events

    # New schema (current events)
    # Has discount_percent field

    # Process unified schema
    update_metrics(event)
```

---

## Cost Analysis

### Kappa Architecture (10M events/day)

**Kinesis Stream** (365-day retention):
- Shards: 2 (2 MB/sec capacity)
- Cost: 2 shards × $0.015/hour × 24 hours × 30 days = $21.60/month
- PUT cost: 10M events/day × 30 days × $0.000014/25 KB = $168/month
- **Total**: $189.60/month

**Kinesis Analytics** (Flink):
- KPUs: 2 (2 GB memory, 1 vCPU each)
- Cost: 2 KPUs × $0.11/hour × 24 hours × 30 days = $158.40/month

**DynamoDB** (materialized views):
- Write: 500 writes/sec (window updates)
- Read: 100 reads/sec (API queries)
- Cost: ~$320/month (auto-scaling)

**Lambda** (replay orchestration):
- Negligible (<$1/month)

**Total**: $668/month

**vs Lambda Architecture**: $1,335/month
**Savings**: $667/month (50% cheaper) ✅

---

## Real-World Examples

### LinkedIn: Kafka-Based Kappa Architecture

**Event Stream**: Kafka (7-day retention originally, now 30 days)

**Stream Processors**:
- Samza jobs (LinkedIn's stream processing framework)
- Materialized views: Espresso (NoSQL database)

**Reprocessing**:
- Replay Kafka topic from offset
- Run new Samza job version
- Blue-green deployment

**Scale**:
- 1 trillion messages/day
- 1,400 Kafka brokers
- <100ms latency

### Uber: Kappa for Real-Time Pricing

**Event Stream**: Kafka (ride requests, GPS updates)

**Stream Processors**:
- Flink jobs (demand calculation)
- Materialized views: Cassandra (current pricing by area)

**Reprocessing** (ML model updates):
- Train new pricing model
- Replay last 24 hours
- A/B test new model (10% traffic)
- Full rollout

**Result**: Dynamic pricing adjusts in <500ms.

---

## Advantages of Kappa vs Lambda

### 1. Simpler Codebase

**Lambda** (2 implementations):
```python
# batch_layer.py (Spark)
df.groupBy("category").sum("amount")

# speed_layer.py (Kinesis)
UPDATE metrics SET revenue = revenue + amount
```

**Kappa** (1 implementation):
```python
# stream_processor.py (Flink)
SELECT category, SUM(amount) FROM orders GROUP BY category
```

✅ Same logic, runs on stream only.

### 2. Faster Reprocessing

**Lambda**:
- Reprocess: Run batch job on all S3 data (4 hours)
- Cost: $50 (Glue DPUs)

**Kappa**:
- Reprocess: Replay Kinesis stream (42 minutes for 7 days)
- Cost: $0 (no additional Kinesis read cost)

✅ 5.7x faster, free.

### 3. No Data Synchronization

**Lambda**:
- Batch writes to Redshift
- Speed writes to DynamoDB
- Serving merges (complex logic)

**Kappa**:
- Stream writes to DynamoDB (single source)
- API reads from DynamoDB (simple)

✅ No merge complexity.

---

## Disadvantages of Kappa vs Lambda

### 1. Limited History

**Lambda**: S3 stores all data (years), batch job accesses any time range.

**Kappa**: Kinesis max 365 days retention.

❌ Can't query 2-year-old data without external storage.

**Mitigation**: Archive Kinesis → S3 (backup).

### 2. No Complex Batch Analytics

**Lambda**: Batch layer does complex Spark jobs (ML training, multi-table joins).

**Kappa**: Stream processing limited to stateful aggregations.

❌ Can't train ML model requiring full dataset scan.

**Mitigation**: Hybrid approach (Kappa for metrics, separate batch for ML).

### 3. Stream Reprocessing Bottleneck

**Lambda**: Batch layer scales to 100s of Spark executors (parallel processing).

**Kappa**: Replay limited by Kinesis shard throughput (2 MB/sec/shard).

❌ Replaying 1 year = 365 days × 10M events = 3.65B events → 12-48 hours.

**Mitigation**: Increase shards temporarily during replay.

---

## When to Choose Kappa Over Lambda

### ✅ Choose Kappa When:

1. **Simple Aggregations**: Count, sum, average (no complex batch analytics)
2. **Small Team**: <5 engineers (can't maintain 2 systems)
3. **Frequent Changes**: Adding new metrics often (reprocessing is fast)
4. **Cost-Sensitive**: 50% cheaper than Lambda
5. **Recent Data**: 365-day history sufficient

### ❌ Choose Lambda When:

1. **Complex Batch**: ML training, multi-table joins, historical analysis
2. **Long History**: Need >1 year of data
3. **Interactive Queries**: Ad-hoc SQL (Athena on S3)
4. **Proven Pattern**: Netflix, LinkedIn invested heavily in Lambda

---

## Next Steps

After completing Exercise 02:

1. ✅ **Compare**: Lambda vs Kappa trade-offs (complexity, cost, capabilities)
2. 🔄 **Refactor**: Extract common code (stream reading) into library
3. 📊 **Dashboard**: Build real-time dashboard querying materialized views
4. 🔬 **Experiment**: Benchmark replay time for different data volumes
5. 🚀 **Production**: Deploy Kinesis Analytics Flink application

**Key Takeaway**: Kappa simplifies architecture by unifying batch and speed into single stream processing layer, at cost of limited history and complex analytics capability.

---

## Troubleshooting

### Issue 1: Replay Too Slow

**Symptom**: Replaying 30 days takes >12 hours.

**Solutions**:
1. **Increase shards**: Scale from 2 → 20 shards (10x parallelism)
2. **Batch reads**: Use `GetRecords(Limit=10000)` instead of 100
3. **Parallel replay**: Run multiple replay jobs (each handles subset of time)

### Issue 2: Materialized View Inconsistency

**Symptom**: v2 has different numbers than v1 (for same time period).

**Solutions**:
1. **Check event ordering**: Ensure events processed in order (partition key)
2. **Idempotency**: Deduplicate events (event_id)
3. **Window alignment**: Ensure same window boundaries (tumbling 5 min)

### Issue 3: High DynamoDB Write Cost

**Symptom**: DynamoDB writes cost $500/month.

**Solutions**:
1. **Aggregate more**: 1-minute windows → 5-minute windows (5x fewer writes)
2. **Downsample**: Only write if value changed >1% (skip writes)
3. **Use On-Demand**: Pay per request instead of provisioned capacity

---

## References

**Research Papers**:
- [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (Jay Kreps, 2014)

**AWS Docs**:
- [Kinesis Data Analytics - Flink SQL](https://docs.aws.amazon.com/kinesisanalytics/latest/java/how-it-works.html)
- [Kinesis Extended Retention](https://aws.amazon.com/blogs/aws/amazon-kinesis-update-retain-data-for-up-to-one-year/)

**Case Studies**:
- [LinkedIn's Kappa Architecture](https://engineering.linkedin.com/blog/2016/04/kafka-ecosystem-at-linkedin)

---

**Status**: 🚧 Ready to Implement
**Next Exercise**: Exercise 03 - Data Mesh (decentralized architecture)
