# Real-Time Analytics: AWS Architecture Patterns

## Table of Contents

1. [AWS Kinesis Data Analytics Architecture](#aws-kinesis-data-analytics-architecture)
2. [Managed Apache Flink on AWS](#managed-apache-flink-on-aws)
3. [Real-Time Dashboard Architectures](#real-time-dashboard-architectures)
4. [Lambda vs Kappa Architecture](#lambda-vs-kappa-architecture)
5. [Event Sourcing & CQRS](#event-sourcing--cqrs)
6. [Multi-Region Real-Time Analytics](#multi-region-real-time-analytics)
7. [Cost-Optimized Architectures](#cost-optimized-architectures)
8. [Security & Compliance](#security--compliance)

---

## AWS Kinesis Data Analytics Architecture

### Basic Real-Time Pipeline

```
┌──────────────┐    ┌───────────────────┐    ┌─────────────────┐
│              │    │   Kinesis Data    │    │    Kinesis      │
│  Producers   │───▶│     Streams       │───▶│  Data Analytics │
│ (Web/Mobile) │    │  (Buffering)      │    │  (SQL/Flink)    │
│              │    └───────────────────┘    └─────────────────┘
└──────────────┘                                      │
                                                      │
                                                      ▼
                               ┌─────────────────────────────────┐
                               │      Destinations               │
                               ├────────────────┬────────────────┤
                               │ Kinesis Stream │ S3 (Parquet)   │
                               │ Lambda         │ OpenSearch     │
                               │ Firehose       │ Redshift       │
                               └────────────────┴────────────────┘
```

### Components

**1. Amazon Kinesis Data Streams**
- **Purpose**: Durable buffer for streaming data
- **Capacity**: Shards (1 MB/sec writes, 2 MB/sec reads per shard)
-Auto-scaling**: On-demand or provisioned mode
- **Retention**: 24 hours to 365 days

**2. Kinesis Data Analytics for Apache Flink**
- **Purpose**: Process and analyze streams with SQL or Flink
- **Compute**: Kinesis Processing Units (KPUs) - 1 vCPU + 4 GB memory
- **Scaling**: Auto-scaling based on CPU utilization
- **Checkpointing**: Automatic snapshots to S3

**3. Amazon Kinesis Data Firehose**
- **Purpose**: Load streams to data lakes/warehouses
- **Transformations**: Lambda for data transformation
- **Buffering**: Time (60s-900s) or size (1-128 MB)
- **Destinations**: S3, Redshift, OpenSearch, HTTP endpoints

### Reference Architecture

```
                          ┌─────────────────────────────────────────┐
                          │                                         │
                          │      Real-Time Analytics Platform       │
                          │                                         │
┌─────────────┐           │  ┌─────────────────────────────────┐  │
│             │           │  │  Kinesis Data Analytics         │  │
│ Web Apps    │───────────┼─▶│  (Managed Flink)                │  │
│             │           │  │                                  │  │
└─────────────┘           │  │  - Tumbling windows (1 min)     │  │
                          │  │  - Aggregations (COUNT, AVG)    │  │
┌─────────────┐           │  │  - Filtering                    │  │
│             │           │  │  - Joins                        │  │
│ Mobile Apps │───────────┼─▶│                                  │  │
│             │           │  └─────────────────┬────────────────┘  │
└─────────────┘           │                    │                   │
                          │                    │                   │
┌─────────────┐           │                    ▼                   │
│             │           │  ┌─────────────────────────────────┐  │
│ IoT Devices │───────────┼─▶│      Kinesis Data Streams       │  │
│             │           │  │      (4 shards, 4 MB/sec)       │  │
└─────────────┘           │  └─────────────────┬────────────────┘  │
                          │                    │                   │
                          └────────────────────┼───────────────────┘
                                               │
                                               ▼
                          ┌────────────────────────────────────────┐
                          │           Destinations                  │
                          │                                         │
                          │  ┌──────────┐  ┌──────────┐  ┌───────┐│
                          │  │QuickSight│  │ DynamoDB │  │   S3  ││
                          │  │Dashboard │  │(Metrics) │  │(Lake) ││
                          │  └──────────┘  └──────────┘  └───────┘│
                          └────────────────────────────────────────┘
```

---

## Managed Apache Flink on AWS

### Flink Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              Kinesis Data Analytics for Apache Flink            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                     Flink Job Manager                       │ │
│  │            (Coordinates execution, checkpointing)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                │                                 │
│                                │                                 │
│         ┌──────────────────────┼──────────────────────┐          │
│         │                      │                      │          │
│  ┌──────▼──────┐        ┌──────▼──────┐       ┌──────▼──────┐  │
│  │   Task      │        │   Task      │       │   Task      │  │
│  │  Manager 1  │        │  Manager 2  │       │  Manager 3  │  │
│  │  (1 KPU)    │        │  (1 KPU)    │       │  (1 KPU)    │  │
│  └─────────────┘        └─────────────┘       └─────────────┘  │
│                                                                  │
│  Auto-scaling: 1-32 KPUs based on CPU utilization              │
│  Checkpointing: Every 60 seconds to S3                         │
│  Snapshots: Manual or automated for deployments                │
└─────────────────────────────────────────────────────────────────┘
```

### Flink SQL Application

**Table Definitions**:
```sql
-- Source: Kinesis Data Stream
CREATE TABLE user_events (
    user_id INT,
    event_type STRING,
    event_time TIMESTAMP(3),
    page STRING,
    session_id STRING,
    WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'user-events-stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);

-- Sink: Another Kinesis Stream
CREATE TABLE page_views_per_minute (
    page STRING,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    view_count BIGINT,
    unique_users BIGINT,
    avg_session_duration DOUBLE,
    PRIMARY KEY (page, window_start) NOT ENFORCED
) WITH (
    'connector' = 'kinesis',
    'stream' = 'page-views-aggregated',
    'aws.region' = 'us-east-1',
    'format' = 'json'
);

-- Analytics Query
INSERT INTO page_views_per_minute
SELECT
    page,
    TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end,
    COUNT(*) AS view_count,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(UNIX_TIMESTAMP(MAX(event_time)) - UNIX_TIMESTAMP(MIN(event_time))) AS avg_session_duration
FROM user_events
WHERE event_type = 'page_view'
GROUP BY
    page,
    TUMBLE(event_time, INTERVAL '1' MINUTE);
```

### Deployment Patterns

**1. Blue/Green Deployment**
```
1. Current application running on snapshot v1
2. Deploy new code as snapshot v2
3. Test v2 with subset of traffic
4. Switch traffic to v2
5. Rollback to v1 if issues detected
```

**2. Canary Deployment**
```
1. Deploy new version alongside current
2. Route 10% traffic to new version
3. Monitor metrics (latency, errors)
4. Gradually increase to 50%, then 100%
5. Decommission old version
```

---

## Real-Time Dashboard Architectures

### Amazon QuickSight with Streaming Data

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│                  Real-Time Dashboard Pipeline                   │
│                                                                 │
│  Kinesis          Flink           DynamoDB/       QuickSight   │
│  Data Streams  →  Analytics    →  Redshift/    →  Dashboard    │
│                   (Aggregation)   Athena         (Refresh 1s)  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Architecture Options**:

**Option 1: DynamoDB Backend** (sub-second latency)
- Flink writes aggregates to DynamoDB
- QuickSight SPICE refresh every 1 second
- Best for: Key metrics, gauges, counters
- Cost: ~$200/month for 10K writes/sec

**Option 2: Athena + S3** (minute latency)
- Flink writes Parquet to S3 (every minute)
- Glue crawler updates catalog
- QuickSight queries via Athena
- Best for: Historical trends, detailed analytics
- Cost: ~$50/month for 1 GB data scanned/day

**Option 3: Redshift** (5-10 second latency)
- Kinesis Firehose loads to Redshift
- QuickSight queries Redshift
- Best for: Complex joins, large datasets
- Cost: ~$180/month for dc2.large node

### CloudWatch Dashboards

```
┌──────────────────────────────────────────────────────────────┐
│           CloudWatch Dashboard (Free, 3-second refresh)       │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Line Chart     │  │  Number Widget  │  │ Log Insights │ │
│  │  Events/second  │  │  Total today    │  │ Error logs   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Stacked Area Chart - Events by Type                    │ │
│  │  [Page View] [Button Click] [Form Submit] [Error]      │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Publishing Metrics from Flink**:
```python
from pyflink.datastream.functions import ProcessFunction
import boto3

class MetricsPublisher(ProcessFunction):
    def open(self, runtime_context):
        self.cloudwatch = boto3.client('cloudwatch')

    def process_element(self, value, ctx):
        # Publish to CloudWatch
        self.cloudwatch.put_metric_data(
            Namespace='RealTimeAnalytics',
            MetricData=[{
                'MetricName': 'EventsProcessed',
                'Value': value['count'],
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'EventType', 'Value': value['event_type']}
                ]
            }]
        )

        yield value
```

### Managed Grafana on AWS

```
┌────────────────────────────────────────────────────────────────┐
│                 Amazon Managed Grafana                          │
│                                                                 │
│  Data Sources:                                                  │
│  - CloudWatch (metrics, logs)                                   │
│  - Prometheus (custom metrics)                                  │
│  - Athena (historical queries)                                  │
│  - Redshift (aggregated data)                                   │
│                                                                 │
│  Features:                                                      │
│  - Real-time charts (1-second updates)                          │
│  - Alerting rules                                               │
│  - Dashboard variables                                          │
│  - SSO integration                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## Lambda vs Kappa Architecture

### Lambda Architecture

```
                        ┌──────────────────────────────────────┐
                        │         Data Sources                  │
                        └───────────────┬──────────────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         │                             │
                         ▼                             ▼
              ┌─────────────────────┐       ┌──────────────────┐
              │   Batch Layer       │       │  Speed Layer     │
              │   (Comprehensive)   │       │  (Real-time)     │
              │                     │       │                  │
              │  - S3 + Glue ETL   │       │  - Kinesis       │
              │  - Athena/Spark    │       │  - Flink         │
              │  - Accurate        │       │  - Approximate   │
              │  - 1-24 hour lag   │       │  - <1 sec lag    │
              └──────────┬──────────┘       └────────┬─────────┘
                         │                           │
                         └──────────────┬────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │    Serving Layer         │
                         │  (Merge batch + speed)   │
                         │                          │
                         │  - Query merges results  │
                         │  - Batch overwrites      │
                         └──────────────────────────┘
```

**Pros**:
- ✅ Accurate batch results
- ✅ Fault tolerance (reprocess batch)
- ✅ Handles late data well

**Cons**:
- ❌ Maintain two codebases (batch + speed)
- ❌ Complex serving layer (merge logic)
- ❌ Higher operational cost

### Kappa Architecture

```
                        ┌──────────────────────────────────────┐
                        │         Data Sources                  │
                        └───────────────┬──────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │    Stream Processing     │
                         │    (Only One Layer)      │
                         │                          │
                         │  - Kinesis + Flink       │
                         │  - Process once          │
                         │  - Write to S3 + DB      │
                         │  - Reprocess by replay   │
                         └──────────┬───────────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     │              │              │
                     ▼              ▼              ▼
              ┌───────────┐  ┌───────────┐  ┌───────────┐
              │  DynamoDB │  │    S3     │  │ OpenSearch│
              │  (Cur)    │  │  (Hist)   │  │  (Search) │
              └───────────┘  └───────────┘  └───────────┘
```

**Pros**:
- ✅ Single codebase (simpler)
- ✅ True real-time processing
- ✅ Lower operational cost
- ✅ Reprocessing by replaying stream

**Cons**:
- ❌ Stream replay can be slow
- ❌ Requires long retention (costly)
- ❌ More complex error handling

**When to Use**:
- **Lambda**: When batch accuracy is critical (finance, compliance)
- **Kappa**: When real-time is paramount, data patterns stable

---

## Event Sourcing & CQRS

### Event Sourcing

**Concept**: Store all changes as immutable events, derive current state by replaying events.

```
Traditional:
┌─────────────────┐
│   Account       │
│   balance: $100 │  ← Only current state
└─────────────────┘

Event Sourcing:
┌──────────────────────────────────────────┐
│  Event Store (Immutable Log)             │
├──────────────────────────────────────────┤
│  1. AccountCreated(id=123, amount=0)     │
│  2. Deposited(id=123, amount=50)         │
│  3. Deposited(id=123, amount=75)         │
│  4. Withdrawn(id=123, amount=25)         │
└──────────────────────────────────────────┘
          │
          │ Replay events
          ▼
┌─────────────────┐
│   Account       │
│   balance: $100 │  ← Derived from events
└─────────────────┘
```

**Implementation with Kinesis**:
```
┌──────────────┐       ┌─────────────────┐       ┌──────────────┐
│   Commands   │  ───▶ │ Kinesis Streams │  ───▶ │   Flink      │
│ (API calls)  │       │  (Event Store)  │       │ (Projection) │
└──────────────┘       └─────────────────┘       └──────┬───────┘
                                                         │
                                                         ▼
                                              ┌────────────────────┐
                                              │  DynamoDB          │
                                              │  (Current State)   │
                                              └────────────────────┘
```

### CQRS (Command Query Responsibility Segregation)

**Separate read and write models**:

```
┌──────────────┐                              ┌──────────────────┐
│              │                              │                  │
│   Commands   │─────────▶ Write Model ───────▶│  Event Stream    │
│  (Writes)    │           (Normalized)       │  (Kinesis)       │
│              │                              │                  │
└──────────────┘                              └────────┬─────────┘
                                                       │
                                                       │
                                                       ▼
                                            ┌──────────────────────┐
                                            │   Flink Processors   │
                                            │  (Build Read Models) │
                                            └──────────┬───────────┘
                                                       │
                        ┌──────────────────────────────┼────────────────────────────┐
                        │                              │                            │
                        ▼                              ▼                            ▼
        ┌─────────────────────────┐    ┌─────────────────────────┐  ┌──────────────────────────┐
        │  Read Model 1           │    │  Read Model 2           │  │  Read Model 3            │
        │  (DynamoDB)             │    │  (OpenSearch)           │  │  (S3 + Athena)           │
        │                         │    │                         │  │                          │
        │  - Dashboard queries    │    │  - Full-text search     │  │  - Historical reports    │
        │  - Fast lookups         │    │  - Aggregations         │  │  - Batch analytics       │
        └─────────────────────────┘    └─────────────────────────┘  └──────────────────────────┘
```

**Benefits**:
- ✅ Optimized read models (denormalized for queries)
- ✅ Independent scaling of reads and writes
- ✅ Multiple read models for different use cases
- ✅ Event history for audit, replay, debugging

---

## Multi-Region Real-Time Analytics

### Active-Active Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Global Real-Time Analytics                      │
└─────────────────────────────────────────────────────────────────────────┘

Region 1 (us-east-1)                         Region 2 (eu-west-1)
┌──────────────────────────┐                 ┌──────────────────────────┐
│                          │                 │                          │
│  Producers (US users)    │                 │  Producers (EU users)    │
│          │               │                 │          │               │
│          ▼               │                 │          ▼               │
│  ┌─────────────────┐    │   Cross-Region  │  ┌─────────────────┐    │
│  │ Kinesis Stream  │◀───┼─────Replication─┼──│ Kinesis Stream  │    │
│  │  (4 shards)     │────┼────────────────▶│  │  (4 shards)     │    │
│  └────────┬────────┘    │                 │  └────────┬────────┘    │
│           │             │                 │           │             │
│           ▼             │                 │           ▼             │
│  ┌─────────────────┐    │                 │  ┌─────────────────┐    │
│  │ Flink Analytics │    │                 │  │ Flink Analytics │    │
│  └────────┬────────┘    │                 │  └────────┬────────┘    │
│           │             │                 │           │             │
│           ▼             │                 │           ▼             │
│  ┌─────────────────┐    │   DynamoDB      │  ┌─────────────────┐    │
│  │   DynamoDB      │◀───┼─────Global──────┼──│   DynamoDB      │    │
│  │   (US Table)    │────┼─────Tables──────┼─▶│   (EU Replica)  │    │
│  └─────────────────┘    │                 │  └─────────────────┘    │
│                          │                 │                          │
└──────────────────────────┘                 └──────────────────────────┘
```

**Key Features**:
- **Cross-Region Replication**: Kinesis streams replicate to secondary region
- **DynamoDB Global Tables**: Multi-region, multi-master replication
- **Route 53**: Route users to nearest region
- **S3 Cross-Region Replication**: Backup and historical data

**Latency**:
- Same-region reads: <10 ms
- Cross-region replication: 500-1000 ms

---

## Cost-Optimized Architectures

### Tiered Storage Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                     Data Lifecycle                              │
│                                                                 │
│  Hot (Real-time)   →  Warm (Recent)  →  Cold (Archive)        │
│  0-7 days             7-90 days          90+ days              │
│  Kinesis+Flink        S3 Standard        S3 Glacier            │
│  $$$                  $$                 $                      │
└────────────────────────────────────────────────────────────────┘
```

**Cost Breakdown**:
```
Service                  | Cost/Month | Use Case
─────────────────────────┼────────────┼──────────────────────
Kinesis Data Streams     | $100       | 4 shards, 1 MB/sec
Kinesis Data Analytics   | $400       | 2 KPUs (24/7)
DynamoDB (On-Demand)     | $50        | 10M reads, 1M writes
S3 Standard              | $23        | 1 TB storage
Glue Crawler             | $10        | 1 run/hour
Athena                   | $5         | 100 GB scanned/month
──────────────────────────────────────────────────────────────
Total                    | $588/month
```

**Optimization Strategies**:
1. **On-Demand Kinesis**: Save 70% for variable workloads
2. **Reserved Capacity**: Save 50% for DynamoDB predictable workloads
3. **Lifecycle Policies**: Move S3 data to IA/Glacier after 30/90 days
4. **Query Optimization**: Partition Athena tables to reduce scanned data
5. **Snapshot Management**: Delete old Flink snapshots after 7 days

---

## Security & Compliance

### Encryption at Rest and In Transit

```
┌────────────────────────────────────────────────────────────────┐
│                    Encrypted Data Pipeline                      │
│                                                                 │
│  Producers                    Processing                        │
│  (HTTPS/TLS 1.2)             (KMS Encryption)      Storage      │
│                                                   (S3/KMS)      │
│  ┌────────┐   TLS 1.2   ┌──────────┐   KMS    ┌────────────┐  │
│  │ Client │───────────▶ │ Kinesis  │─────────▶│     S3     │  │
│  └────────┘             │ (SSE-KMS)│          │ (SSE-KMS)  │  │
│                         └──────────┘          └────────────┘  │
│                                                                 │
│  All data encrypted:                                            │
│  - In transit (TLS 1.2)                                         │
│  - At rest (AWS KMS CMK)                                        │
│  - Application-level (optional)                                 │
└────────────────────────────────────────────────────────────────┘
```

### IAM Roles and Permissions

**Flink Application Role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
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
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:us-east-1:123456789012:stream/output-stream"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::flink-checkpoints/*"
    }
  ]
}
```

### Compliance (GDPR, HIPAA)

**GDPR Considerations**:
- **Right to be Forgotten**: Implement event tombstones or data deletion jobs
- **Data Minimization**: Only collect necessary fields
- **Consent Management**: Track consent in events
- **Data Retention**: Automate deletion after retention period

**HIPAA Compliance**:
- **BAA with AWS**: Sign Business Associate Agreement
- **Encryption**: Enable KMS encryption for all services
- **Access Logging**: CloudTrail for all API calls
- **Audit Trail**: Maintain event logs for 6 years

---

## Summary

### Key Takeaways

**Architecture Patterns**:
- **Lambda**: Batch + speed layers (accuracy priority)
- **Kappa**: Pure streaming (real-time priority)
- **Event Sourcing**: Immutable event log, replay for state
- **CQRS**: Separate read/write models for optimization

**AWS Services**:
- **Kinesis Data Streams**: Durable, scalable streaming buffer
- **Kinesis Data Analytics**: Managed Flink for SQL/Java/Python
- **QuickSight**: Real-time dashboards
- **CloudWatch**: Metrics and alerting

**Best Practices**:
- Auto-scaling for cost optimization
- Multi-region for global users
- Encryption everywhere (TLS + KMS)
- Lifecycle policies for data tiering

### Next Steps

- Read `best-practices.md` for production patterns
- Review `resources.md` for learning materials
- Complete exercises to build hands-on experience

---

**Previous**: [concepts.md](./concepts.md) - Core Concepts
**Next**: [best-practices.md](./best-practices.md) - Production Best Practices
