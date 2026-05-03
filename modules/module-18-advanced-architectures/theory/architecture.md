# Reference Architectures for Advanced Data Platforms

## Table of Contents

1. [Lambda Architecture on AWS](#lambda-architecture-on-aws)
2. [Kappa Architecture on AWS](#kappa-architecture-on-aws)
3. [Data Mesh on AWS](#data-mesh-on-aws)
4. [Event-Driven Architecture on AWS](#event-driven-architecture-on-aws)
5. [Multi-Region Active-Active](#multi-region-active-active)
6. [Polyglot Persistence Architecture](#polyglot-persistence-architecture)
7. [Hybrid Architectures](#hybrid-architectures)

---

## Lambda Architecture on AWS

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources                                │
│  (Applications, IoT, Logs, APIs, Databases)                     │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
    ┌─────────────┴─────────────┐
    ↓                           ↓
┌───────────────┐       ┌──────────────────┐
│ Batch Layer   │       │ Speed Layer      │
│               │       │                  │
│ S3 (Raw)      │       │ Kinesis Streams  │
│   ↓           │       │   ↓              │
│ Glue ETL      │       │ Lambda/Flink     │
│   ↓           │       │   ↓              │
│ S3 (Curated)  │       │ DynamoDB (1hr)   │
│   ↓           │       │                  │
│ Redshift      │       │                  │
│ (Batch Views) │       │ (Real-time Views)│
└───────┬───────┘       └────────┬─────────┘
        └─────────────┬───────────┘
                      ↓
            ┌──────────────────┐
            │  Serving Layer   │
            │  (Athena/Redshift│
            │   + DynamoDB)    │
            │                  │
            │  Query Merge:    │
            │  batch + realtime│
            └────────┬─────────┘
                     ↓
            ┌────────────────┐
            │ QuickSight/BI  │
            │   (Dashboards) │
            └────────────────┘
```

### AWS Service Mapping

#### Batch Layer

```yaml
Raw Storage:
  - S3 (Standard tier): Unlimited scale, $0.023/GB-month
  - Format: Parquet with Snappy compression (5x smaller than JSON)

Processing:
  - AWS Glue: Serverless Spark ($0.44/DPU-hour)
  - EMR: Managed Hadoop/Spark (from $0.096/hour for m5.xlarge)

Serving:
  - Redshift: Data warehouse (from $0.25/hour for dc2.large)
  - S3 + Athena: Query in place ($5/TB scanned)
```

#### Speed Layer

```yaml
Ingestion:
  - Kinesis Data Streams: $0.015/shard-hour + $0.014/GB ingested
  - MSK (Kafka): From $0.21/broker-hour

Processing:
  - Lambda: Serverless functions ($0.20/1M requests)
  - Kinesis Data Analytics (Flink): $0.11/KPU-hour

Storage:
  - DynamoDB: $0.25/GB-month + $0.25/WCU per hour
  - ElastiCache: From $0.017/hour (cache.t3.micro)
```

### Example: E-commerce Analytics

**Batch Layer** (Accuracy):
```
Daily ETL (03:00 AM):
1. Read all orders from yesterday (S3)
2. Join with customers, products (10+ tables)
3. Calculate:
   - Lifetime value per customer
   - Product affinity matrix (collaborative filtering)
   - Cohort analysis (retention curves)
4. Export to Redshift

Query: "What is customer lifetime value?"
Result: Accurate up to yesterday (03:00 AM cutoff)
```

**Speed Layer** (Freshness):
```
Real-time (sub-second):
1. Order placed → Kinesis Stream
2. Lambda function:
   - Increment order count (DynamoDB)
   - Update current session value
   - Calculate cart abandonment
3. Results in DynamoDB

Query: "What is current cart value?"
Result: Real-time (last 5 seconds)
```

**Serving Layer** (Unified Query):
```sql
-- Merge batch + real-time
SELECT
    c.customer_id,
    c.lifetime_value_batch,  -- From Redshift (accurate, yesterday)
    r.revenue_today           -- From DynamoDB (real-time, today)
FROM
    redshift.customers c
    LEFT JOIN dynamodb.realtime_revenue r ON c.customer_id = r.customer_id
```

### Performance Characteristics

| Metric | Batch Layer | Speed Layer | Combined |
|--------|-------------|-------------|----------|
| **Latency** | 1-24 hours | <1 second | Best of both |
| **Throughput** | 1M records/min | 100K records/sec | High |
| **Accuracy** | 100% | 95-99% | Converges to 100% |
| **Cost** | $8K/month | $4K/month | $12K/month |

### Scaling Example

**Scenario**: 10M events/day → 100M events/day (10x growth)

**Batch Layer Scaling**:
```
Glue: 10 DPUs → 50 DPUs (+40 DPUs)
Cost: $44/day → $220/day (+$176/day)
Time: 2 hours → 2 hours (parallel scaling)
```

**Speed Layer Scaling**:
```
Kinesis: 5 shards → 50 shards (+45 shards)
Lambda: Auto-scales (no changes needed)
Cost: $200/month → $2,000/month (+$1,800/month)
```

**Total Scaling Cost**: +$2,000/month for 10x traffic (reasonable).

---

## Kappa Architecture on AWS

### Architecture Diagram

```
┌──────────────────────────────────────────┐
│          Data Sources                    │
│  (Applications, IoT, Logs)               │
└───────────────┬──────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│       Event Log (Source of Truth)         │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │   Kinesis Data Streams              │ │
│  │   Retention: 365 days               │ │
│  │   Shards: Auto-scaling              │ │
│  │                                     │ │
│  │   Partition Key: user_id            │ │
│  │   Ordering: Per partition           │ │
│  └─────────────────────────────────────┘ │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│     Stream Processor (v1)                 │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │ Kinesis Data Analytics (Flink)      │ │
│  │                                     │ │
│  │ - Windowing (tumbling, sliding)    │ │
│  │ - Aggregations (count, sum, avg)   │ │
│  │ - Joins (stream-stream, stream-table)│ │
│  └─────────────────────────────────────┘ │
└───────────┬───────────┬───────────────────┘
            ↓           ↓
  ┌─────────────────┐ ┌──────────────────┐
  │ Materialized    │ │ Materialized     │
  │ View A          │ │ View B           │
  │                 │ │                  │
  │ DynamoDB        │ │ OpenSearch       │
  │ (Aggregates)    │ │ (Search Index)   │
  └─────────────────┘ └──────────────────┘
```

### Reprocessing Flow

```
Event Log (Kinesis)
    ↓
Replay from timestamp (30 days ago)
    ↓
Stream Processor v2 (new logic)
    ↓
Materialized View v2 (new table)
    ↓
Test/Validate
    ↓
Switch traffic: v1 → v2 (blue-green)
    ↓
Delete v1 after 7 days
```

### AWS Service Mapping

```yaml
Event Log:
  Primary: Kinesis Data Streams
    - Retention: 1-365 days
    - Throughput: 1 MB/sec per shard
    - Ordering: Per partition key
  Alternative: MSK (Kafka)
    - Retention: Unlimited (until storage full)
    - Throughput: Higher (10+ MB/sec per partition)
    - Cost: More expensive

Stream Processing:
  Serverless: Kinesis Data Analytics (Apache Flink)
  Self-Managed: Flink on EKS/ECS
  Simple: Lambda (stateless transformations)

Materialized Views:
  Real-time: DynamoDB, ElastiCache
  Near-real-time: RDS, OpenSearch
  Analytical: Redshift, S3 (Athena)
```

### Example: IoT Monitoring

**Use Case**: Monitor 100K IoT devices, alert on anomalies.

**Stream Flow**:

```python
# Devices → Kinesis
{
  "device_id": "device_001",
  "temperature": 85.3,
  "pressure": 120.5,
  "timestamp": "2026-03-09T10:30:00Z"
}

# Flink SQL (Kinesis Analytics)
CREATE VIEW device_metrics AS
SELECT
    device_id,
    AVG(temperature) as avg_temp,
    MAX(temperature) as max_temp,
    COUNT(*) as reading_count,
    TUMBLE_START(event_time, INTERVAL '1' MINUTE) as window_start
FROM devices_stream
GROUP BY
    device_id,
    TUMBLE(event_time, INTERVAL '1' MINUTE);

# Alert on anomalies
INSERT INTO alerts_stream
SELECT device_id, avg_temp, max_temp
FROM device_metrics
WHERE avg_temp > 90 OR max_temp > 100;

# Output to DynamoDB
{
  "device_id": "device_001",
  "avg_temp": 92.5,
  "max_temp": 105.2,
  "window": "2026-03-09T10:30:00Z",
  "alert": true
}
```

### Reprocessing Scenario

**Problem**: Bug in aggregation logic (used SUM instead of AVG).

**Solution** (No Batch Reprocessing!):

```python
# 1. Deploy Stream Processor v2 with fix
flink_app_v2 = deploy_application(
    application_name="iot-processor-v2",
    sql_code=fixed_sql  # Changed SUM → AVG
)

# 2. Replay last 30 days
kinesis_analytics.start_application(
    ApplicationName="iot-processor-v2",
    InputStartingPositionConfiguration={
        'InputStartingPosition': 'TRIM_HORIZON'  # From beginning
        # Or: 'AT_TIMESTAMP': 30 days ago
    }
)

# 3. Output to new table
DynamoDB table: device_metrics_v2

# 4. Verify results
assert device_metrics_v2.avg_temp == expected_values

# 5. Switch reads: v1 → v2
update_application_config(read_table='device_metrics_v2')

# 6. Delete v1 after 7 days
```

**Time**: 2-4 hours (vs 24 hours for batch reprocessing)

---

## Data Mesh on AWS

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                 Central Platform Team                             │
│  (Provides Infrastructure, Not Data)                             │
│                                                                   │
│  AWS Services: S3, Glue, Redshift, Kinesis, Lake Formation       │
│  Tools: CI/CD, Monitoring, Cost Management, Schema Registry      │
└──────────────────────┬───────────────────────────────────────────┘
                       ↓ (Self-service)
        ┌──────────────┼──────────────┬──────────────┐
        ↓              ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Product Domain│ │ Sales Domain │ │Customer Domain│ │Marketing Dom.│
│  (Team A)    │ │  (Team B)    │ │  (Team C)     │ │  (Team D)    │
│              │ │              │ │               │ │              │
│ Owns:        │ │ Owns:        │ │ Owns:         │ │ Owns:        │
│ - Catalog    │ │ - Orders     │ │ - Profiles    │ │ - Campaigns  │
│ - Inventory  │ │ - Revenue    │ │ - Preferences │ │ - Attribution│
│ - Pricing    │ │ - Discounts  │ │ - Behavior    │ │ - Spend      │
└──────┬───────┘ └──────┬───────┘ └──────┬────────┘ └──────┬───────┘
       ↓                ↓                 ↓                 ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Data Product A│ │Data Product B│ │Data Product C│ │Data Product D│
│              │ │              │ │              │ │              │
│ S3 Bucket    │ │ DynamoDB     │ │ Redshift     │ │ S3 + Athena  │
│ + Glue Table │ │ + Streams    │ │ + DataAPI    │ │ + Lake Form. │
│              │ │              │ │              │ │              │
│ API: Athena  │ │ API: REST    │ │ API: SQL     │ │ API: GraphQL │
│ Format:Parquet│ │ Format: JSON │ │ Format: CSV  │ │ Format: Avro │
│              │ │              │ │              │ │              │
│ SLA: 99.9%   │ │ SLA: 99.5%   │ │ SLA: 99.9%   │ │ SLA: 99.0%   │
│ Fresh: <1hr  │ │ Fresh: <1min │ │ Fresh: <5min │ │ Fresh: Daily │
└──────┬───────┘ └──────┬───────┘ └──────┬────────┘ └──────┬───────┘
       └────────────────┴────────────────┴──────────────────┘
                                ↓
                    ┌────────────────────────┐
                    │ Federated Governance   │
                    │                        │
                    │ - Glue Data Catalog    │
                    │ - Schema Registry      │
                    │ - Lake Formation (IAM) │
                    │ - CloudTrail (Audit)   │
                    └────────────────────────┘
```

### Data Product Structure

Each domain publishes data products with:

#### 1. **Data Product Metadata** (Glue Catalog)

```json
{
  "name": "product-catalog",
  "domain": "Product",
  "owner": "product-team@company.com",
  "description": "Complete product catalog with pricing",
  "sla": {
    "uptime": "99.9%",
    "freshness": "<1 hour",
    "quality": "99.5% completeness"
  },
  "schema": {
    "registry": "glue-schema-registry",
    "version": "2.1.0",
    "compatibility": "BACKWARD"
  },
  "access": {
    "public": ["product_id", "name", "price"],
    "restricted": ["cost", "margin"],
    "pii": []
  }
}
```

#### 2. **Data Product API**

```python
# Athena Query API
def query_product_catalog(filters):
    query = f"""
    SELECT * FROM product_catalog
    WHERE category IN ({filters['categories']})
      AND price BETWEEN {filters['min_price']} AND {filters['max_price']}
    """
    return athena.execute_query(query)

# Usage by other domains
data_api.query(
    domain="Product",
    product="product-catalog",
    filters={"categories": ["Electronics"], "min_price": 50}
)
```

#### 3. **Self-Service Documentation**

```markdown
# Product Catalog Data Product

## Quick Start
```python
from data_mesh import get_data_product
catalog = get_data_product("product-catalog")
df = catalog.query(category="Electronics")
```

## Schema
- product_id (string): Unique identifier
- name (string): Product name
- price (decimal): USD, 2 decimals
- updated_at (timestamp): Last modification

## Quality Metrics
- Completeness: 99.7% (last 7 days)
- Duplicates: 0
- Freshness: 45 min average

## Change Log
- v2.1.0 (2026-03-01): Added `margin` field
- v2.0.0 (2026-01-15): Breaking: Renamed `cost` → `unit_cost`
```

### Governance Model

**Global Policies** (Enforced by Platform Team):

```yaml
Data Standards:
  naming_convention: snake_case
  required_fields: [created_at, updated_at, domain, version]
  timestamp_format: ISO 8601 (UTC)

Schema Evolution:
  compatibility: BACKWARD  # Old readers work with new schema
  breaking_changes: Require major version bump

Security:
  encryption: AES-256 (rest + transit)
  access_control: Lake Formation (column-level)
  pii_handling: Tokenization mandatory

Quality:
  completeness: >95%
  freshness: Domain-specific SLA
  testing: Great Expectations rules
```

**Domain Autonomy** (Decided by Domain Team):

```yaml
Technology Choice:
  storage: S3, DynamoDB, Redshift (any)
  processing: Glue, EMR, Lambda (any)
  format: Parquet, Avro, JSON (must document)

Update Frequency:
  batch: Daily, hourly (domain decides)
  streaming: Real-time, near-real-time

Query Interface:
  api_type: REST, GraphQL, SQL (domain decides)
```

### Example: Uber's Data Mesh

**20+ Domains**:

- **Rides Domain**: Trip data (pickups, dropoffs, routes)
- **Eats Domain**: Restaurant orders, delivery tracking
- **Freight Domain**: Logistics, shipping
- **Marketplace Domain**: Driver supply, rider demand
- **Payments Domain**: Transactions, billing

**Cross-Domain Query**:

```sql
-- Analytics team queries multiple domains
SELECT
    r.trip_id,
    r.fare_amount,        -- From Rides domain
    p.payment_method,     -- From Payments domain
    u.user_tier           -- From Customer domain
FROM rides.trips r
JOIN payments.transactions p ON r.trip_id = p.trip_id
JOIN customer.profiles u ON r.rider_id = u.user_id
WHERE r.date = '2026-03-09'
```

**Enabled By**: Federated Glue Catalog (domains register their tables).

---

## Event-Driven Architecture on AWS

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Event Producers                           │
│  (Order Service, Payment Service, Inventory Service)        │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │  Amazon EventBridge   │
         │  (Event Bus)          │
         │                       │
         │  Rules:               │
         │  - order.placed → [targets] │
         │  - payment.failed → [SNS]   │
         └───────────┬───────────┘
                     ↓
    ┌────────────────┼────────────────┬─────────────┐
    ↓                ↓                ↓             ↓
┌─────────┐  ┌──────────────┐  ┌─────────┐  ┌──────────┐
│Lambda 1 │  │ Step Function│  │Kinesis  │  │SQS Queue │
│(Fast)   │  │(Orchestration)│  │(Stream) │  │(Async)   │
│         │  │              │  │         │  │          │
│Inventory│  │Order Workflow│  │Analytics│  │Email     │
│Decrement│  │1.Validate    │  │Pipeline │  │Service   │
│         │  │2.Pay         │  │         │  │          │
│         │  │3.Ship        │  │         │  │          │
└─────────┘  └──────────────┘  └─────────┘  └──────────┘
```

### Event Schema (CloudEvents Standard)

```json
{
  "specversion": "1.0",
  "type": "com.company.order.placed",
  "source": "order-service",
  "id": "evt_123456789",
  "time": "2026-03-09T10:30:00.123Z",
  "datacontenttype": "application/json",
  "data": {
    "orderId": "order_789",
    "userId": "user_456",
    "items": [
      {"productId": "prod_123", "quantity": 2, "price": 29.99}
    ],
    "totalAmount": 59.98,
    "currency": "USD"
  }
}
```

### EventBridge Rules

```python
# Rule 1: Send high-value orders to fraud detection
eventbridge.put_rule(
    Name='high-value-orders',
    EventPattern=json.dumps({
        'source': ['order-service'],
        'detail-type': ['OrderPlaced'],
        'detail': {
            'totalAmount': [{'numeric': ['>', 1000]}]
        }
    }),
    State='ENABLED'
)

eventbridge.put_targets(
    Rule='high-value-orders',
    Targets=[{
        'Id': '1',
        'Arn': fraud_detection_lambda_arn
    }]
)

# Rule 2: Archive all events to S3 (compliance)
eventbridge.put_targets(
    Rule='archive-all-events',
    Targets=[{
        'Id': '1',
        'Arn': kinesis_firehose_arn  # → S3
    }]
)
```

### Saga Pattern (Distributed Transactions)

**Problem**: Place order requires:
1. Reserve inventory
2. Process payment
3. Create shipment

If payment fails after inventory reserved, need to rollback.

**Solution**: Saga with compensating transactions

```python
# Step Functions Workflow (saga)
{
  "StartAt": "ReserveInventory",
  "States": {
    "ReserveInventory": {
      "Type": "Task",
      "Resource": inventory_lambda_arn,
      "Next": "ProcessPayment",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "InventoryReservationFailed"
      }]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": payment_lambda_arn,
      "Next": "CreateShipment",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "ReleaseInventory"  # Compensate
      }]
    },
    "CreateShipment": {
      "Type": "Task",
      "Resource": shipment_lambda_arn,
      "End": true
    },
    "ReleaseInventory": {
      "Type": "Task",
      "Resource": release_inventory_lambda_arn,
      "Next": "NotifyPaymentFailed"
    }
  }
}
```

---

## Multi-Region Active-Active

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Global Load Balancer                        │
│         (Route 53 with Latency-Based Routing)                   │
└───────────────┬──────────────────────┬──────────────────────────┘
                ↓                      ↓
┌───────────────────────────┐ ┌───────────────────────────┐
│    US Region (us-east-1)  │ │   EU Region (eu-west-1)   │
│                           │ │                           │
│ ┌───────────────────────┐ │ │ ┌───────────────────────┐ │
│ │ Application Servers   │ │ │ │ Application Servers   │ │
│ │ (ECS/EKS)             │ │ │ │ (ECS/EKS)             │ │
│ └───────┬───────────────┘ │ │ └───────┬───────────────┘ │
│         ↓                 │ │         ↓                 │
│ ┌───────────────────────┐ │ │ ┌───────────────────────┐ │
│ │ DynamoDB Global Table │←┼─┼→│ DynamoDB Global Table │ │
│ │ "orders"              │ │ │ │ "orders"              │ │
│ │ Read + Write          │ │ │ │ Read + Write          │ │
│ │                       │ │ │ │                       │ │
│ │ Replication: <1 sec   │ │ │ │ Replication: <1 sec   │ │
│ └───────────────────────┘ │ │ └───────────────────────┘ │
│                           │ │                           │
│ ┌───────────────────────┐ │ │ ┌───────────────────────┐ │
│ │ Aurora Global Database│←┼─┼→│ Aurora Global Database│ │
│ │ Primary (Write)       │ │ │ │ Secondary (Read)      │ │
│ │ Replication: <1 sec   │ │ │ │ Can promote to primary│ │
│ └───────────────────────┘ │ │ └───────────────────────┘ │
│                           │ │                           │
│ ┌───────────────────────┐ │ │ ┌───────────────────────┐ │
│ │ S3 Bucket             │←┼─┼→│ S3 Bucket             │ │
│ │ Cross-Region Replication │ │ Cross-Region Replication │
│ │ SLA: <15 minutes      │ │ │ │ SLA: <15 minutes      │ │
│ └───────────────────────┘ │ │ └───────────────────────┘ │
└───────────────────────────┘ └───────────────────────────┘
```

### Routing Strategy

```python
# Route 53 Latency-Based Routing
route53.change_resource_record_sets(
    HostedZoneId='Z123456789',
    ChangeBatch={
        'Changes': [{
            'Action': 'CREATE',
            'ResourceRecordSet': {
                'Name': 'api.example.com',
                'Type': 'A',
                'SetIdentifier': 'US-East',
                'Region': 'us-east-1',
                'AliasTarget': {
                    'HostedZoneId': alb_us_zone_id,
                    'DNSName': alb_us_dns
                }
            }
        }, {
            'Action': 'CREATE',
            'ResourceRecordSet': {
                'Name': 'api.example.com',
                'Type': 'A',
                'SetIdentifier': 'EU-West',
                'Region': 'eu-west-1',
                'AliasTarget': {
                    'HostedZoneId': alb_eu_zone_id,
                    'DNSName': alb_eu_dns
                }
            }
        }]
    }
)

# User from US → Routed to us-east-1 (20ms)
# User from EU → Routed to eu-west-1 (15ms)
```

### Conflict Resolution Example

**Scenario**: User edits profile simultaneously in US and EU.

```python
# US Region (10:30:00.000)
dynamodb_us.update_item(
    TableName='users',
    Key={'user_id': 'user_123'},
    UpdateExpression='SET email = :email',
    ExpressionAttributeValues={':email': 'john@us.com'}
)

# EU Region (10:30:00.050) - 50ms later
dynamodb_eu.update_item(
    TableName='users',
    Key={'user_id': 'user_123'},
    UpdateExpression='SET email = :email',
    ExpressionAttributeValues={':email': 'john@eu.com'}
)

# Conflict! Both regions think they have latest value.
```

**Resolution Strategies**:

#### **Last-Write-Wins (LWW)** - Default
```
US: email = "john@us.com" (timestamp: 10:30:00.000)
EU: email = "john@eu.com" (timestamp: 10:30:00.050)

Winner: EU (later timestamp)
Final: email = "john@eu.com"

⚠️ Lost Data: "john@us.com" (no trace it existed)
```

#### **Version Vectors** - Track Causality
```python
# US write
{
  "email": "john@us.com",
  "version": {"us": 5, "eu": 3}  # US ahead
}

# EU write
{
  "email": "john@eu.com",
  "version": {"us": 4, "eu": 4}  # EU concurrent
}

# Conflict detected: US=5 vs EU=4 (diverged)
# Store both versions, app resolves
```

#### **Custom Resolver** - Business Logic
```python
def resolve_email_conflict(us_value, eu_value):
    # Business rule: EU GDPR takes precedence
    if is_gdpr_country(us_value['country']):
        return eu_value
    else:
        return us_value  # Use US version
```

### Failover Automation

```python
# Monitor primary region health
def check_region_health(region):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='HealthyHostCount',
            Dimensions=[{'Name': 'LoadBalancer', 'Value': alb_name}],
            StartTime=datetime.now() - timedelta(minutes=5),
            EndTime=datetime.now(),
            Period=60,
            Statistics=['Average']
        )
        return response['Datapoints'][0]['Average'] > 0
    except:
        return False

# Automatic failover
if not check_region_health('us-east-1'):
    # Promote Aurora secondary to primary
    rds.failover_global_cluster(
        GlobalClusterIdentifier='global-db',
        TargetDbClusterIdentifier='eu-cluster'
    )

    # Update Route 53 (remove us-east-1)
    route53.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            'Changes': [{
                'Action': 'DELETE',
                'ResourceRecordSet': us_record
            }]
        }
    )

    # Alert team
    sns.publish(
        TopicArn=alert_topic,
        Subject='🚨 Failover: US → EU',
        Message='Primary region failed, traffic routed to EU'
    )
```

---

## Polyglot Persistence Architecture

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│          (Microservices with Database-per-Service)              │
└───────────────────────┬──────────────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┬───────────────┐
        ↓               ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Aurora Postgre│ │  DynamoDB    │ │ ElastiCache  │ │ OpenSearch   │
│(Transactional)│ │(Session Data)│ │  (Cache)     │ │(Full-Text)   │
│              │ │              │ │              │ │              │
│Orders        │ │Shopping cart │ │Product cache │ │Product search│
│Users         │ │User sessions │ │API responses │ │Fuzzy match   │
│Inventory     │ │Preferences   │ │              │ │Aggregations  │
│              │ │              │ │              │ │              │
│ACID          │ │Single-digit│ │Sub-millisecond│ │Relevance rank│
│Consistent    │ │ms latency    │ │Volatile      │ │Analyzers     │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                        ↓
         ┌──────────────────────────────┐
         │   Change Data Capture (CDC)  │
         │   (DMS + DynamoDB Streams)   │
         └──────────────┬───────────────┘
                        ↓
                ┌────────────────┐
                │   Redshift     │
                │  (Analytics)   │
                │                │
                │All data unified│
                │for BI queries  │
                └────────────────┘
```

### Database Selection Criteria

#### **Aurora PostgreSQL** (Transactional)

**Use When**:
- ACID transactions required
- Complex joins (10+ tables)
- Relational data (foreign keys)
- Moderate write rate (<10K/sec)

**Example**: Order management system

```sql
-- Complex query with ACID guarantees
BEGIN;
  -- Atomic: Both succeed or both fail
  UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 123;
  INSERT INTO orders (user_id, product_id, amount) VALUES (456, 123, 29.99);
COMMIT;
```

#### **DynamoDB** (Key-Value)

**Use When**:
- Simple access patterns (get/put by key)
- High write rate (>10K/sec)
- Unpredictable traffic (auto-scaling)
- Global reach (global tables)

**Example**: Shopping cart

```python
# Simple key-value access
cart = dynamodb.get_item(
    TableName='carts',
    Key={'user_id': 'user_456'}
)

# Fast writes
dynamodb.put_item(
    TableName='carts',
    Item={'user_id': 'user_456', 'items': []}
)
```

#### **ElastiCache (Redis)** (Caching)

**Use When**:
- Read-heavy (read:write = 100:1)
- Expensive to compute (complex queries)
- Sub-millisecond latency required
- Data can be regenerated (cache miss OK)

**Example**: Product details cache

```python
# Check cache first
product = redis.get(f"product:{product_id}")
if product:
    return json.loads(product)  # Cache hit (1ms)

# Cache miss: Query database
product = aurora.query("SELECT * FROM products WHERE id = %s", product_id)
redis.setex(f"product:{product_id}", 3600, json.dumps(product))  # TTL = 1 hour
return product
```

#### **Redshift** (Analytics)

**Use When**:
- Complex analytics (aggregations, window functions)
- Historical queries (TB to PB scale)
- Batch reporting (daily/weekly)
- Columnar benefits (scan only needed columns)

**Example**: Sales reporting

```sql
-- Efficient columnar scan (only reads 3 columns)
SELECT
    DATE_TRUNC('month', order_date) as month,
    SUM(amount) as total_revenue,
    COUNT(DISTINCT customer_id) as unique_customers
FROM orders
WHERE order_date >= '2025-01-01'
GROUP BY month
ORDER BY month;
```

#### **OpenSearch** (Search)

**Use When**:
- Full-text search ("iPhone 15 Pro Max cases")
- Fuzzy matching (handle typos)
- Faceted search (filters: category, price, brand)
- Log analytics (Kibana dashboards)

**Example**: Product search

```python
# Full-text query with filters
opensearch.search(
    index='products',
    body={
        'query': {
            'bool': {
                'must': [
                    {'match': {'name': 'wireless headphones'}},  # Full-text
                ],
                'filter': [
                    {'range': {'price': {'gte': 50, 'lte': 200}}},
                    {'term': {'brand': 'Sony'}}
                ]
            }
        },
        'sort': ['_score']  # Relevance ranking
    }
)
```

### CDC Implementation

Sync Aurora → Redshift for analytics:

```
Aurora (Orders Table)
   ↓
DMS CDC (continuous replication)
   ↓
S3 (Parquet files every 5 min)
   ↓
Glue Crawler (update schema)
   ↓
Redshift COPY (load data)
   ↓
Redshift (Analytics-ready)
```

**Configuration**:

```python
# Create DMS task
dms.create_replication_task(
    ReplicationTaskIdentifier='aurora-to-s3',
    SourceEndpointArn=aurora_endpoint_arn,
    TargetEndpointArn=s3_endpoint_arn,
    ReplicationInstanceArn=replication_instance_arn,
    MigrationType='cdc',  # Only capture changes
    TableMappings=json.dumps({
        'rules': [{
            'rule-type': 'selection',
            'rule-id': '1',
            'rule-name': 'orders-table',
            'object-locator': {
                'schema-name': 'public',
                'table-name': 'orders'
            },
            'rule-action': 'include'
        }]
    })
)

# Redshift COPY from S3 (scheduled every 5 min)
redshift.execute("""
COPY orders_staging
FROM 's3://cdc-bucket/orders/'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftCopyRole'
FORMAT AS PARQUET;
""")
```

**Latency**: 5-10 minutes (Aurora write → Redshift available)

---

## Hybrid Architectures (Combining Patterns)

###Lambda + Data Mesh

**Use Case**: Large organization with both batch and streaming needs.

```
┌───────────────────────────────────────────┐
│         Data Mesh (3 Domains)             │
│                                           │
│ Product Domain → Lambda Architecture      │
│  - Batch: Spark (daily)                   │
│  - Speed: Kinesis (real-time)             │
│                                           │
│ Sales Domain → Kappa Architecture         │
│  - Stream-only: Flink                     │
│                                           │
│ Customer Domain → Batch-Only              │
│  - Daily ETL: Glue                        │
└───────────────────────────────────────────┘
```

**Benefit**: Domains choose architecture independently.

### Multi-Region + Polyglot

**Use Case**: Global e-commerce with specialized databases.

```
US Region:
- Aurora (orders) → EU Region: Aurora (read replica)
- DynamoDB (cart) → Global Table → EU Region
- ElastiCache (cache) → Separate cache per region
- OpenSearch (search) → Cross-region replication

Result: <50ms latency worldwide, specialized databases
```

### Event-Driven + CQRS

**Use Case**: Command validation + multiple read models.

```
Command → EventBridge → Event Store (DynamoDB)
                ↓
        ┌───────┼───────┬───────┐
        ↓       ↓       ↓       ↓
    Lambda  Lambda  Lambda  Lambda
    (Proj1) (Proj2) (Proj3) (Proj4)
        ↓       ↓       ↓       ↓
  DynamoDB  Redshift OpenSearch S3
  (Current) (History)(Search) (Archive)
```

**Benefit**: Single event stream, 4 specialized read models.

---

## Real-World Implementation: Netflix

### Architecture

**Lambda Architecture + Microservices + Multi-Region**

```
┌──────────────────────────────────────────────────────────────┐
│                 Content Delivery Network (CloudFront)        │
└─────────────────────┬────────────────────────────────────────┘
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
┌──────────────────┐       ┌──────────────────┐
│ US Region        │       │ EU Region        │
│                  │       │                  │
│ Zuul (Gateway)   │       │ Zuul (Gateway)   │
│      ↓           │       │      ↓           │
│ Microservices:   │       │ Microservices:   │
│ - User Service   │       │ - User Service   │
│ - Viewing Service│       │ - Viewing Service│
│ - Recommendation │       │ - Recommendation │
│      ↓           │       │      ↓           │
│ Cassandra (Multi│←──────→│ Cassandra (Multi│
│  -region)        │       │  -region)        │
└──────┬───────────┘       └──────┬───────────┘
       ↓                           ↓
┌──────────────────────────────────────────┐
│         Data Platform (Lambda)           │
│                                          │
│ Batch Layer:                             │
│ - Spark on Titus (container platform)   │
│ - Daily ETL: 1 trillion events           │
│ - Output: S3 Parquet (100 PB)            │
│                                          │
│ Speed Layer:                             │
│ - Kafka (streaming backbone)             │
│ - Flink: Real-time aggregations          │
│ - Druid: OLAP queries (<1 sec)           │
│                                          │
│ Serving Layer:                           │
│ - Presto/Athena: SQL over S3             │
│ - Druid: Real-time dashboards            │
└──────────────────────────────────────────┘
```

### Scale Numbers

- **Users**: 200M+ subscribers
- **Events**: 1 trillion per day (12M events/second peak)
- **Storage**: 100+ PB in S3
- **Regions**: 3 (US, EU, South America)
- **Availability**: 99.99% (4-nines)
- **Personalization Latency**: <100ms

### Technology Choices

| Layer | Technology | Why |
|-------|------------|-----|
| **API Gateway** | Zuul | Custom routing, resilience |
| **Microservices** | Spring Boot | Java ecosystem |
| **Database** | Cassandra | Multi-region, high writes |
| **Streaming** | Kafka | Backbone for all events |
| **Batch** | Spark on Titus | Large-scale ETL |
| **Real-time OLAP** | Druid | Sub-second queries |
| **SQL Analytics** | Presto | SQL over S3 |

---

## Real-World Implementation: Uber

### Architecture

**Data Mesh + Multi-Region + Polyglot**

```
┌──────────────────────────────────────────────────────────────┐
│                 Central Platform (Unified Data Platform)     │
│   Technologies: HDFS, Hive, Presto, Spark, Kafka, Flink     │
└─────────────────────┬────────────────────────────────────────┘
                      ↓
        ┌─────────────┼─────────────┬───────────────┐
        ↓             ↓             ↓               ↓
┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│Rides Domain  │ │Eats Domain  │ │Driver Domain │ │Payments Dom. │
│              │ │             │ │              │ │              │
│Data Products:│ │Data Products│ │Data Products:│ │Data Products:│
│- Trips       │ │- Orders     │ │- Profiles    │ │- Transactions│
│- Routes      │ │- Restaurants│ │- Ratings     │ │- Payouts     │
│- Fares       │ │- Deliveries │ │- Earnings    │ │- Disputes    │
│              │ │             │ │              │ │              │
│Storage:      │ │Storage:     │ │Storage:      │ │Storage:      │
│- HDFS (batch)│ │- Cassandra  │ │- MySQL       │ │- Postgres    │
│- Kafka (stream)│ │- Kafka      │ │- Kafka       │ │- Kafka       │
└──────┬───────┘ └─────┬───────┘ └──────┬───────┘ └──────┬───────┘
       └───────────────┴────────────────┴────────────────┘
                       ↓
         ┌─────────────────────────────┐
         │   Unified Analytics Layer   │
         │   (Presto - SQL over all)   │
         └─────────────────────────────┘
```

### Scale Numbers

- **Data Engineers**: 1,000+
- **Data Pipelines**: 10,000+
- **Daily Events**: 100+ billion
- **Storage**: Multi-PB across domains
- **Queries**: 100K+ Presto queries/day

### Technology Choices

| Component | Technology | Why |
|-----------|------------|-----|
| **Batch Storage** | HDFS | Hadoop ecosystem integration |
| **Streaming** | Kafka | High throughput, replay |
| **Stream Processing** | Flink | Stateful processing |
| **SQL Engine** | Presto | Federated queries |
| **Orchestration** | Airflow | 10K+ DAGs |
| **Metadata** | Hive Metastore | Central catalog |

---

## Summary: Architecture Selection Flowchart

```
Start: What are your requirements?
│
├─ Need real-time + historical accuracy?
│  ├─ Yes → Lambda Architecture
│  └─ No → Continue
│
├─ Everything is a stream?
│  ├─ Yes → Kappa Architecture
│  └─ No → Continue
│
├─ Large organization (>50 engineers)?
│  ├─ Yes → Data Mesh
│  └─ No → Continue
│
├─ Need complete audit trail?
│  ├─ Yes → Event Sourcing + CQRS
│  └─ No → Continue
│
├─ Global users requiring <100ms latency?
│  ├─ Yes → Multi-Region Active-Active
│  └─ No → Continue
│
├─ Mixed workloads (OLTP + OLAP + Search)?
│  ├─ Yes → Polyglot Persistence
│  └─ No → Simple Architecture (CRUD + single database)
```

### Cost Comparison (10TB data/month)

| Architecture | Monthly Cost | Rationale |
|--------------|--------------|-----------|
| **Simple CRUD** | $2K | Single RDS instance |
| **Lambda** | $12K | Batch ($8K) + Speed ($4K) |
| **Kappa** | $7K | Streaming only |
| **Data Mesh** | $20K | 5 domains × $4K |
| **Multi-Region** | $25K | 2x infrastructure + replication |
| **Polyglot** | $10K | Specialized databases |

---

**Next**: Read [best-practices.md](best-practices.md) for design principles and anti-patterns.
