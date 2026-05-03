# Cost Estimation: Real-Time Analytics Platform

## Executive Summary

This document provides a detailed cost breakdown for the RideShare Real-Time Analytics Platform across development and production environments.

### Quick Summary

| Environment | Monthly Cost | Annual Cost | Notes |
|------------|--------------|-------------|-------|
| **Development** | $50-80 | $600-960 | Leverages AWS Free Tier |
| **Production (Current Scale)** | $2,000-5,000 | $24K-60K | 10M rides/month |
| **Production (Future Scale)** | $5,000-10,000 | $60K-120K | 100M rides/month (10x growth) |

---

## Table of Contents

- [Cost Breakdown by Service](#cost-breakdown-by-service)
- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Cost Optimization Strategies](#cost-optimization-strategies)
- [Cost Monitoring and Alerting](#cost-monitoring-and-alerting)
- [Free Tier Usage](#free-tier-usage)
- [Cost Projections](#cost-projections)
- [Cost Allocation and Chargebacks](#cost-allocation-and-chargebacks)

---

## Cost Breakdown by Service

### Amazon Kinesis Data Streams

**Pricing Model**:
- **Shard Hour**: $0.015 per shard-hour
- **PUT Payload Units**: $0.014 per million PUT payload units (25 KB per unit)
- **Enhanced Fan-Out**: $0.015 per shard-hour + $0.013 per GB data retrieved

**Development Environment** (10M events/day = ~115 events/second):

| Stream | Shards | Shard-Hours/Month | PUT Units/Month | Monthly Cost |
|--------|--------|-------------------|-----------------|--------------|
| ride-events | 1 | 730 | 10M events × 0.5 KB × (1/25KB) = 0.2M units | $10.95 + $2.80 = $13.75 |
| driver-locations | 1 | 730 | 60M events × 0.25 KB × (1/25KB) = 0.6M units | $10.95 + $8.40 = $19.35 |
| payment-events | 1 | 730 | 10M events × 0.3 KB × (1/25KB) = 0.12M units | $10.95 + $1.68 = $12.63 |
| rating-events | 1 | 730 | 8M events × 0.4 KB × (1/25KB) = 0.128M units | $10.95 + $1.79 = $12.74 |
| **Total** | **4** | **2,920** | **1.028M units** | **$58.47** |

**Production Environment** (100M events/day = ~1,157 events/second):

| Stream | Shards | Shard-Hours/Month | PUT Units/Month | Monthly Cost |
|--------|--------|-------------------|-----------------|--------------|
| ride-events | 4 | 2,920 | 100M × 0.5 KB × (1/25KB) = 2M units | $43.80 + $28.00 = $71.80 |
| driver-locations | 10 | 7,300 | 600M × 0.25 KB × (1/25KB) = 6M units | $109.50 + $84.00 = $193.50 |
| payment-events | 2 | 1,460 | 100M × 0.3 KB × (1/25KB) = 1.2M units | $21.90 + $16.80 = $38.70 |
| rating-events | 1 | 730 | 80M × 0.4 KB × (1/25KB) = 1.28M units | $10.95 + $17.92 = $28.87 |
| **Total** | **17** | **12,410** | **10.48M units** | **$332.87** |

**Cost Optimization**:
- Use **On-Demand mode** for unpredictable workloads (auto-scales, $0.04 per GB data ingested + $0.04 per GB data retrieved)
- For production at 10M events/day = ~3 GB/day = 90 GB/month:
  - On-Demand cost: 90 GB × $0.04 = $3.60 ingestion + variable consumption cost
  - Provisioned is cheaper for steady workloads

### AWS Lambda

**Pricing Model**:
- **Free Tier**: 1M requests/month + 400,000 GB-seconds compute
- **Requests**: $0.20 per 1M requests
- **Compute**: $0.0000166667 per GB-second

**Development Environment**:

| Function | Invocations/Month | Memory | Duration | GB-Seconds/Month | Cost |
|----------|------------------|--------|----------|------------------|------|
| ride_processor | 10M | 512 MB | 100ms | 10M × 0.5 GB × 0.1s = 500K | Free Tier + $0 |
| driver_location_processor | 60M | 512 MB | 50ms | 60M × 0.5 GB × 0.05s = 1.5M | $1.80 req + $25 compute = $26.80 |
| payment_processor | 10M | 512 MB | 200ms | 10M × 0.5 GB × 0.2s = 1M | $1.80 req + $16.67 compute = $18.47 |
| rating_processor | 8M | 512 MB | 100ms | 8M × 0.5 GB × 0.1s = 400K | $1.40 req + $0 (Free Tier) = $1.40 |
| aggregation_processor | 30 | 1024 MB | 5 min | 30 × 1 GB × 300s = 9K | $0 (Free Tier) |
| data_quality_checker | 1M | 512 MB | 50ms | 1M × 0.5 GB × 0.05s = 25K | $0 (Free Tier) |
| **Total** | **89M** | - | - | **3.434M GB-s** | **$46.67** |

**Production Environment** (10x scale):

| Function | Invocations/Month | Memory | Duration | GB-Seconds/Month | Cost |
|----------|------------------|--------|----------|------------------|------|
| ride_processor | 100M | 512 MB | 100ms | 100M × 0.5 GB × 0.1s = 5M | $19.80 req + $83.33 compute = $103.13 |
| driver_location_processor | 600M | 512 MB | 50ms | 600M × 0.5 GB × 0.05s = 15M | $119.80 req + $250 compute = $369.80 |
| payment_processor | 100M | 512 MB | 200ms | 100M × 0.5 GB × 0.2s = 10M | $19.80 req + $166.67 compute = $186.47 |
| rating_processor | 80M | 512 MB | 100ms | 80M × 0.5 GB × 0.1s = 4M | $15.80 req + $66.67 compute = $82.47 |
| aggregation_processor | 30 | 1024 MB | 5 min | 30 × 1 GB × 300s = 9K | $0 |
| data_quality_checker | 10M | 512 MB | 50ms | 10M × 0.5 GB × 0.05s = 250K | $1.80 req + $4.17 compute = $5.97 |
| **Total** | **890M** | - | - | **34.259M GB-s** | **$747.84** |

**Cost Optimization**:
- Right-size memory (test 256 MB, 512 MB, 1024 MB to find optimal)
- Use **Graviton2 processors** (20% cheaper, 34% better price-performance)
- Optimize code to reduce duration
- Use **Provisioned Concurrency** for critical functions (eliminates cold starts, $0.0041 per GB-hour)

### Amazon DynamoDB

**Pricing Model**:
- **On-Demand Mode**:
  - Write: $1.25 per million write request units (1 WRU = 1 KB)
  - Read: $0.25 per million read request units (1 RRU = 4 KB)
- **Provisioned Mode**:
  - Write: $0.00065 per WCU-hour (1 WCU = 1KB/sec)
  - Read: $0.00013 per RCU-hour (1 RCU = 4KB/sec eventually consistent)
- **Storage**: $0.25 per GB-month

**Development Environment (On-Demand)**:

| Table | Writes/Month | Item Size | WRUs | Reads/Month | RRUs | Storage | Cost |
|-------|-------------|-----------|------|-------------|------|---------|------|
| rides_state | 10M | 1 KB | 10M | 1M | 0.25M | 5 GB | $12.50 + $0.06 + $1.25 = $13.81 |
| driver_availability | 60M | 0.5 KB | 30M | 5M | 1.25M | 2 GB | $37.50 + $0.31 + $0.50 = $38.31 |
| aggregated_metrics | 100K | 0.5 KB | 50K | 1M | 0.25M | 1 GB | $0.06 + $0.06 + $0.25 = $0.37 |
| **Total** | **70.1M** | - | **40.05M WRUs** | **7M** | **1.75M RRUs** | **8 GB** | **$52.49** |

**Production Environment (On-Demand, 10x scale)**:

| Table | Writes/Month | WRUs | Reads/Month | RRUs | Storage | Cost |
|-------|-------------|------|-------------|------|---------|------|
| rides_state | 100M | 100M | 10M | 2.5M | 50 GB | $125 + $0.63 + $12.50 = $138.13 |
| driver_availability | 600M | 300M | 50M | 12.5M | 20 GB | $375 + $3.13 + $5.00 = $383.13 |
| aggregated_metrics | 1M | 500K | 10M | 2.5M | 10 GB | $0.63 + $0.63 + $2.50 = $3.76 |
| **Total** | **701M** | **400.5M WRUs** | **70M** | **17.5M RRUs** | **80 GB** | **$525.02** |

**Cost Optimization**:
- Consider **Provisioned Mode** for steady workloads (50% cheaper)
- Use **Reserved Capacity** (1-year or 3-year commitment, up to 75% discount)
- Enable **Auto-Scaling** for provisioned capacity
- Use **DynamoDB Accelerator (DAX)** for read-heavy workloads (in-memory cache, $0.04/node-hour)

### Amazon S3

**Pricing Model**:
- **Storage**:
  - Standard: $0.023 per GB-month (first 50 TB)
  - Standard-IA: $0.0125 per GB-month
  - Glacier: $0.004 per GB-month
- **Requests**:
  - PUT/POST: $0.005 per 1,000 requests
  - GET: $0.0004 per 1,000 requests

**Development Environment**:

| Bucket | Storage/Month | Storage Class | Requests | Cost |
|--------|---------------|---------------|----------|------|
| event-archive | 50 GB | Standard (30d) + IA (60d) + Glacier (rest) | 10M PUT, 100K GET | $1.15 (Std) + $0.13 (IA) + $0.08 (Glacier) + $50 PUT + $0.04 GET = $51.40 |
| lambda-artifacts | 5 GB | Standard | 1K PUT, 10K GET | $0.12 + $0.01 = $0.13 |
| **Total** | **55 GB** | Mixed | - | **$51.53** |

**Production Environment (10x scale)**:

| Bucket | Storage/Month | Storage Class | Requests | Cost |
|--------|---------------|---------------|----------|------|
| event-archive | 500 GB | Standard (30d) + IA (60d) + Glacier (rest) | 100M PUT, 1M GET | $11.50 + $1.25 + $0.80 + $500 PUT + $0.40 GET = $514.95 |
| lambda-artifacts | 5 GB | Standard | 1K PUT, 10K GET | $0.12 + $0.01 = $0.13 |
| **Total** | **505 GB** | Mixed | - | **$515.08** |

**Cost Optimization**:
- Use **S3 Intelligent-Tiering** (auto-moves objects between tiers, $0.0025/1000 objects monitoring fee)
- **Compress data** before uploading (gzip, Parquet columnar format)
- **Lifecycle policies**: Transition to IA after 30 days, Glacier after 90 days
- **Delete incomplete multipart uploads** after 7 days
- Use **S3 Select** to retrieve only necessary data (reduce data transfer)

### Amazon Kinesis Data Analytics

**Pricing Model**:
- **KPU (Kinesis Processing Unit)**: $0.11 per KPU-hour
- 1 KPU = 1 vCPU + 4 GB memory

**Development Environment**:

| Application | KPUs | Hours/Month | Cost |
|-------------|------|-------------|------|
| surge_pricing_calculator | 1 | 730 | $80.30 |
| real_time_metrics | 1 | 730 | $80.30 |
| hot_spots_detector | 1 | 730 | $80.30 |
| **Total** | **3** | **2,190** | **$240.90** |

**Production Environment**:

| Application | KPUs | Hours/Month | Cost |
|-------------|------|-------------|------|
| surge_pricing_calculator | 2 | 730 | $160.60 |
| real_time_metrics | 2 | 730 | $160.60 |
| hot_spots_detector | 2 | 730 | $160.60 |
| **Total** | **6** | **4,380** | **$481.80** |

**Cost Optimization**:
- Optimize SQL queries to use fewer KPUs
- Consider **Apache Flink on EMR** for very high throughput (can be cheaper at large scale)
- Use **Flink Savepoints** to pause/resume applications (stop during low-traffic hours)
- Monitor KPU utilization, scale down if <50% utilized

### AWS Step Functions

**Pricing Model**:
- **Standard Workflows**: $0.025 per 1,000 state transitions
- **Express Workflows**: $1.00 per 1M requests + $0.00001667 per GB-second

**Development Environment**:

| Workflow | Executions/Month | States per Execution | Transitions/Month | Cost |
|----------|------------------|---------------------|-------------------|------|
| daily_aggregation | 30 | 10 | 300 | $0.01 |
| weekly_reporting | 4 | 20 | 80 | $0.002 |
| **Total** | **34** | - | **380** | **$0.012** |

**Production Environment** (same):
- **Total**: $0.012

**Cost Optimization**:
- Minimize state transitions (combine steps where possible)
- Use **Express Workflows** for high-volume, short-duration workflows

### Amazon EventBridge

**Pricing Model**:
- **Custom Events**: $1.00 per million events
- **Scheduled Rules**: Free

**Development Environment**:
- **Scheduled Rules Only**: $0 (cron jobs for daily/weekly workflows)

**Production Environment**:
- **Scheduled Rules**: $0
- **Custom Events** (data quality alerts): 1,000/month = $0.001

### Amazon CloudWatch

**Pricing Model**:
- **Logs**:
  - Ingestion: $0.50 per GB
  - Storage: $0.03 per GB-month
- **Metrics**:
  - Custom metrics: $0.30 per metric/month
  - API requests: $0.01 per 1,000 requests
- **Dashboards**: $3 per dashboard/month
- **Alarms**: $0.10 per alarm/month

**Development Environment**:

| Component | Usage | Cost |
|-----------|-------|------|
| Logs (Lambda) | 10 GB ingested, 5 GB stored | $5.00 + $0.15 = $5.15 |
| Custom Metrics | 50 metrics | $15.00 |
| Dashboards | 2 dashboards | $6.00 |
| Alarms | 20 alarms | $2.00 |
| **Total** | - | **$28.15** |

**Production Environment** (10x scale):

| Component | Usage | Cost |
|-----------|-------|------|
| Logs (Lambda) | 100 GB ingested, 50 GB stored | $50.00 + $1.50 = $51.50 |
| Custom Metrics | 100 metrics | $30.00 |
| Dashboards | 2 dashboards | $6.00 |
| Alarms | 30 alarms | $3.00 |
| **Total** | - | **$90.50** |

**Cost Optimization**:
- **Filter logs**: Only log important events (not every invocation)
- **Aggregate metrics**: Use CloudWatch Embedded Metric Format
- **Set retention**: 7 days for debug logs, 30 days for important logs
- Use **CloudWatch Logs Insights** for ad-hoc queries (cheaper than storing all logs)

### Amazon SNS

**Pricing Model**:
- **Email Notifications**: $2.00 per 100,000 notifications
- **SMS**: $0.00645 per message (US)

**Development Environment**:
- **Email**: 100 notifications/month = $0.002

**Production Environment**:
- **Email**: 1,000 notifications/month = $0.02
- **SMS** (optional): 100 SMS/month = $0.65

**Total**: $0.67

### Amazon QuickSight

**Pricing Model**:
- **Standard Edition**: $9 per user/month (pay-per-session available)
- **Enterprise Edition**: $18 per user/month
- **SPICE Capacity**: Included up to 10 GB per user, then $0.25 per GB

**Development Environment**:
- **2 Users** (dev, analyst): 2 × $18 = $36/month

**Production Environment**:
- **10 Users** (operations team, executives): 10 × $18 = $180/month
- **SPICE**: 20 GB = 10 GB included per user (100 GB total < 10 users × 10 GB) = $0

**Total**: $180/month

**Cost Optimization**:
- Use **Pay-Per-Session** for users who access infrequently ($0.30/session, max $5/month)
- Use **Direct Query** to DynamoDB/Athena instead of SPICE (slower but no storage cost)

### AWS X-Ray

**Pricing Model**:
- **Traces**: $5.00 per 1M traces recorded, $0.50 per 1M traces retrieved
- **Scanned traces**: $0.50 per 1M scanned

**Development Environment**:
- **Traces**: 1M/month recorded, 100K retrieved = $5.00 + $0.05 = $5.05

**Production Environment**:
- **Traces**: 10M/month recorded, 1M retrieved = $50.00 + $0.50 = $50.50

**Cost Optimization**:
- **Sampling**: Trace 1% of requests (100K traces/month = $0.50)
- Use X-Ray only for debugging (disable in production once stable)

---

## Development Environment

**Total Monthly Cost**: $539.91

| Service | Cost |
|---------|------|
| Kinesis Data Streams | $58.47 |
| Lambda | $46.67 |
| DynamoDB | $52.49 |
| S3 | $51.53 |
| Kinesis Data Analytics | $240.90 |
| Step Functions | $0.012 |
| EventBridge | $0 |
| CloudWatch | $28.15 |
| SNS | $0.002 |
| QuickSight | $36.00 |
| X-Ray | $5.05 |
| **AWS Support (Developer)** | $29 |
| **Total** | **$548.33** |

**With Free Tier Credits**: ~$480/month (Lambda Free Tier saves ~$68)

**Recommended Budget**: $50-80/month (by minimizing usage, running only during testing)

---

## Production Environment

**Total Monthly Cost (Current Scale - 10M rides/month)**: $3,132.15

| Service | Cost |
|---------|------|
| Kinesis Data Streams | $332.87 |
| Lambda | $747.84 |
| DynamoDB | $525.02 |
| S3 | $515.08 |
| Kinesis Data Analytics | $481.80 |
| Step Functions | $0.012 |
| EventBridge | $0.001 |
| CloudWatch | $90.50 |
| SNS | $0.67 |
| QuickSight | $180.00 |
| X-Ray | $50.50 |
| **AWS Support (Business)** | $100 (minimum) |
| **Reserved Capacity Discount** | -$500 (estimated 16% discount) |
| **Total** | **$2,524.41** |

**With Optimizations**: ~$2,000-2,500/month

**Future Scale (100M rides/month, 10x growth)**: $5,000-$10,000/month

---

## Cost Optimization Strategies

### 1. Right-Size Lambda Functions

**Strategy**: Test different memory configurations (128 MB, 256 MB, 512 MB, 1024 MB) and measure execution time vs cost.

**Example**:
- **Current**: 512 MB, 100ms duration = $0.000000833 per invocation
- **Optimized**: 256 MB, 120ms duration = $0.000000500 per invocation (40% cheaper)

**Savings**: $18/month per function (for 10M invocations)

**Action**:
```bash
# Test different memory sizes
aws lambda update-function-configuration \
  --function-name ride-processor \
  --memory-size 256

# Run load test, measure duration
python scripts/load_test.py --rate 1000 --duration 60

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=ride-processor \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

### 2. Optimize Kinesis Shard Count

**Strategy**: Monitor `IncomingRecords` and `WriteProvisionedThroughputExceeded` metrics. Reduce shards if under-utilized.

**Example**:
- **Current**: 4 shards for ride-events = $44/month
- **Optimized**: 2 shards (if throughput allows) = $22/month

**Savings**: $22/month per stream

**Action**:
```bash
# Check current throughput
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis \
  --metric-name IncomingRecords \
  --dimensions Name=StreamName,Value=rideshare-ride-events-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# If average < 100 records/sec per shard, consider reducing shards
aws kinesis update-shard-count \
  --stream-name rideshare-ride-events-dev \
  --target-shard-count 2 \
  --scaling-type UNIFORM_SCALING
```

### 3. Use DynamoDB Provisioned Capacity with Auto-Scaling

**Strategy**: Switch from on-demand to provisioned capacity for predictable workloads.

**Example**:
- **Current (On-Demand)**: $525/month for 400M WRUs
- **Optimized (Provisioned)**: $285/month (55 WCUs × 730 hours × $0.00065)

**Savings**: $240/month (45% reduction)

**Trade-off**: Need to manage capacity, set up auto-scaling

**Action**:
```bash
# Update table billing mode
aws dynamodb update-table \
  --table-name rideshare-rides-state-prod \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=55

# Enable auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/rideshare-rides-state-prod \
  --scalable-dimension dynamodb:table:WriteCapacityUnits \
  --min-capacity 10 \
  --max-capacity 100

aws application-autoscaling put-scaling-policy \
  --service-namespace dynamodb \
  --resource-id table/rideshare-rides-state-prod \
  --scalable-dimension dynamodb:table:WriteCapacityUnits \
  --policy-name Write-AutoScaling-Policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
      file://scaling-policy.json
```

### 4. Compress and Optimize S3 Storage

**Strategy**: Use Parquet columnar format, gzip compression, and S3 Intelligent-Tiering.

**Example**:
- **Current (JSON)**: 500 GB/month = $11.50
- **Optimized (Parquet + gzip)**: 100 GB/month = $2.30 (5x compression)

**Savings**: $9.20/month (80% reduction)

**Action**:
```python
# Use Parquet instead of JSON
import pandas as pd
import pyarrow.parquet as pq

# Convert events to Parquet
df = pd.DataFrame(events)
df.to_parquet('s3://rideshare-event-archive-prod/raw/rides/2024/01/15/rides.parquet',
              compression='gzip')
```

### 5. Reduce Kinesis Data Analytics Usage

**Strategy**: Optimize SQL queries to use fewer KPUs, or move some analytics to Lambda.

**Example**:
- **Current**: 3 apps × 1 KPU × 730 hours = $240/month
- **Optimized**: Run only during business hours (12 hours/day) = 3 × 1 × 360 hours = $119/month

**Savings**: $121/month (50% reduction)

**Trade-off**: No analytics during off-hours

### 6. Use Reserved Capacity for Predictable Workloads

**Strategy**: Purchase 1-year or 3-year reserved capacity for DynamoDB, Kinesis.

**Example** (DynamoDB):
- **Current**: 100 WCUs on-demand = $5,475/year
- **Optimized**: 100 WCUs reserved (1-year, no upfront) = $2,737/year

**Savings**: $2,738/year (50% reduction)

### 7. Optimize CloudWatch Logs Retention

**Strategy**: Set retention period based on log importance.

| Log Type | Retention | Reason |
|----------|-----------|--------|
| Lambda debug logs | 7 days | Only for debugging recent issues |
| Lambda error logs | 30 days | Need history for troubleshooting |
| Audit logs | 1 year | Compliance requirement |

**Savings**: $20/month (40% reduction in storage)

### 8. Use CloudWatch Embedded Metric Format

**Strategy**: Instead of calling `put_metric_data` API, embed metrics in log output.

**Example**:
```python
import json

def lambda_handler(event, context):
    # Process event
    processed_count = len(event['Records'])

    # Embed metric in log (free)
    print(json.dumps({
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [{
                "Namespace": "RideShare",
                "Dimensions": [["FunctionName"]],
                "Metrics": [{"Name": "ProcessedRecords", "Unit": "Count"}]
            }]
        },
        "FunctionName": context.function_name,
        "ProcessedRecords": processed_count
    }))
```

**Savings**: $5/month (no API calls for metrics)

### 9. Use S3 Select for Athena Queries

**Strategy**: Use S3 Select to retrieve only necessary columns from Parquet files.

**Example**:
- **Current**: Query 10 GB Parquet file, scan all columns = $0.05
- **Optimized**: Query 10 GB, scan 2 columns = $0.01

**Savings**: $0.04 per query (80% reduction)

### 10. Stop/Start Resources During Non-Business Hours

**Strategy**: For development environment, stop Kinesis Data Analytics applications during nights/weekends.

**Example**:
- **Current**: 3 apps × 24/7 = $240/month
- **Optimized**: 3 apps × 12 hours/day × 5 days/week = $60/month

**Savings**: $180/month (75% reduction)

**Implementation**:
```bash
# Stop application (save to S3 snapshot)
aws kinesisanalyticsv2 stop-application \
  --application-name surge-pricing-calculator

# Start application
aws kinesisanalyticsv2 start-application \
  --application-name surge-pricing-calculator \
  --run-configuration file://run-config.json

# Automate with Lambda + EventBridge (cron)
# Stop at 6pm: cron(0 18 * * ? *)
# Start at 8am: cron(0 8 * * ? *)
```

---

## Cost Monitoring and Alerting

### Set Up AWS Budgets

```bash
# Create budget for $80/month (dev) or $3,000/month (prod)
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json**:
```json
{
  "BudgetName": "RideShare-Dev-Monthly-Budget",
  "BudgetLimit": {
    "Amount": "80",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "TagKeyValue": ["user:Project$RideShare"]
  }
}
```

**notifications.json**:
```json
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "engineering@rideshare.com"
      }
    ]
  },
  {
    "Notification": {
      "NotificationType": "FORECASTED",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "engineering@rideshare.com"
      }
    ]
  }
]
```

### Cost Anomaly Detection

```bash
# Enable AWS Cost Anomaly Detection
aws ce create-anomaly-monitor \
  --anomaly-monitor file://anomaly-monitor.json

aws ce create-anomaly-subscription \
  --anomaly-subscription file://anomaly-subscription.json
```

### Daily Cost Reports

```python
# scripts/cost_report.py
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')

start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

response = ce.get_cost_and_usage(
    TimePeriod={'Start': start_date, 'End': end_date},
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    GroupBy=[{'Type': 'SERVICE', 'Key': 'SERVICE'}]
)

print(f"Cost for {start_date}:")
for result in response['ResultsByTime'][0]['Groups']:
    service = result['Keys'][0]
    cost = result['Metrics']['UnblendedCost']['Amount']
    print(f"  {service}: ${float(cost):.2f}")
```

---

## Free Tier Usage

### AWS Free Tier (12 Months)

| Service | Free Tier Limit | Benefit for RideShare |
|---------|----------------|----------------------|
| Lambda | 1M requests + 400K GB-s per month | Covers ~10M invocations/month at 128 MB |
| DynamoDB | 25 GB storage + 25 WCU + 25 RCU | Covers small dev environment |
| Kinesis | 1M PUT units/month | Covers ~25M events/month at 1 KB |
| S3 | 5 GB storage + 20K GET + 2K PUT | Covers small logging |
| CloudWatch | 10 custom metrics + 10 alarms | Covers basic monitoring |

**Estimated Free Tier Savings for Development**: $68/month

### Always Free Tier

| Service | Free Tier Limit | Benefit |
|---------|----------------|---------|
| Lambda | 1M requests/month | Always covered |
| CloudWatch | 5 GB logs ingestion | Covers basic logging |
| EventBridge | Scheduled rules | All cron jobs free |

---

## Cost Projections

### 3-Year TCO (Total Cost of Ownership)

| Year | Rides/Month | Monthly Cost | Annual Cost | Cumulative |
|------|------------|--------------|-------------|------------|
| **Year 1** | 10M | $2,500 | $30,000 | $30,000 |
| **Year 2** | 30M (3x growth) | $5,000 | $60,000 | $90,000 |
| **Year 3** | 60M (2x growth) | $8,000 | $96,000 | $186,000 |

**3-Year TCO**: $186,000

**With Reserved Capacity (20% discount)**: $148,800

**Savings**: $37,200 over 3 years

---

## Cost Allocation and Chargebacks

### Tag Resources for Cost Attribution

```bash
# Terraform tagging (in terraform/main.tf)
resource "aws_kinesis_stream" "ride_events" {
  # ...
  tags = {
    Project     = "RideShare"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CostCenter  = "Engineering"
    Application = "RealTimeAnalytics"
    Owner       = "DataEngineering"
  }
}
```

### Cost Allocation Report

```bash
# Query costs by tag
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=TAG,Key=CostCenter
```

### Chargeback to Business Units

| Cost Center | Monthly Cost | Justification |
|------------|--------------|---------------|
| Engineering (platform) | $1,500 | Infrastructure, Lambda, Kinesis |
| Operations (dashboards) | $200 | QuickSight licenses |
| Finance (reporting) | $300 | Step Functions, analytics |

---

## Summary

| Metric | Development | Production (Current) | Production (Future) |
|--------|------------|---------------------|---------------------|
| **Monthly Cost** | $50-80 | $2,000-3,000 | $5,000-10,000 |
| **Annual Cost** | $600-960 | $24K-36K | $60K-120K |
| **Cost per Ride** | - | $0.0002-0.0003 | $0.00005-0.0001 |
| **Optimization Potential** | -30% | -40% | -40% |

**Key Takeaways**:
1. Development environment can be kept under $80/month by leveraging Free Tier
2. Production costs scale linearly with ride volume (cost per ride decreases)
3. 40% cost savings possible with optimization strategies
4. Reserved capacity provides 20-50% discount for predictable workloads

---

**Last Updated**: March 2026

**Next Review**: Quarterly or when ride volume increases 2x
