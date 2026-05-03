# Advanced Data Architecture Concepts

## Table of Contents

1. [Introduction to Data Architecture Patterns](#introduction)
2. [Lambda Architecture](#lambda-architecture)
3. [Kappa Architecture](#kappa-architecture)
4. [Data Mesh](#data-mesh)
5. [Event-Driven Architecture](#event-driven-architecture)
6. [Event Sourcing & CQRS](#event-sourcing--cqrs)
7. [Multi-Region Architectures](#multi-region-architectures)
8. [Polyglot Persistence](#polyglot-persistence)
9. [CAP Theorem & Consistency Models](#cap-theorem--consistency-models)
10. [Architectural Trade-offs](#architectural-trade-offs)

---

## Introduction

Modern data platforms require sophisticated architectural patterns to handle:

- **Scale**: Petabytes of data, millions of events per second
- **Latency**: Sub-second query response for real-time insights
- **Consistency**: Trade-offs between strong and eventual consistency
- **Availability**: 99.99% uptime for mission-critical applications
- **Cost**: Optimize infrastructure spending while maintaining performance
- **Complexity**: Balance simplicity with capabilities

**Evolution of Data Architectures**:

1. **2000s**: Monolithic data warehouses (Oracle, Teradata)
2. **2010s**: Big Data (Hadoop, MapReduce) + Data Lake (S3)
3. **2015+**: Lambda Architecture (batch + streaming)
4. **2017+**: Kappa Architecture (streaming-first)
5. **2019+**: Data Mesh (decentralized domains)
6. **2020+**: Lakehouse (unified batch + streaming + ACID)

---

## Lambda Architecture

### Overview

Proposed by Nathan Marz (2011), Lambda Architecture addresses the challenge: *"How do we get both accuracy and speed?"*

**Core Principle**: Separate batch and real-time processing, merge results at query time.

### Three Layers

#### 1. **Batch Layer** (Accuracy)

```
Raw Data (S3) → Spark Job (EMR) → Batch Views (Parquet/Delta Lake)
```

- **Purpose**: Process ALL data for complete, accurate results
- **Technology**: Apache Spark, AWS Glue, EMR
- **Latency**: Hours (e.g., daily ETL)
- **Consistency**: Strong (recomputes from scratch)
- **Storage**: Immutable data lake (S3)

**Example**: Calculate lifetime customer value from all historical transactions.

#### 2. **Speed Layer** (Low Latency)

```
Live Events → Kinesis → Lambda → Real-time Views (DynamoDB)
```

- **Purpose**: Process recent data for immediate insights
- **Technology**: Kinesis, AWS Lambda, Flink
- **Latency**: Sub-second
- **Consistency**: Approximate (sampling, windowing)
- **Storage**: In-memory or hot storage

**Example**: Calculate current session activity (last 5 minutes).

#### 3. **Serving Layer** (Query)

```
Query → Merge Batch Views + Real-time Views → Combined Result
```

- **Purpose**: Provide unified interface to consume data
- **Technology**: Redshift, Athena, DynamoDB
- **Complexity**: Merge logic must handle overlaps
- **Query Pattern**: `SELECT batch_data + realtime_data WHERE timestamp > batch_cutoff`

### Diagram

```
                    Raw Data (S3)
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
  Batch Layer                        Speed Layer
  (Spark/EMR)                    (Kinesis/Lambda)
        ↓                                   ↓
  Batch Views                       Real-time Views
  (Parquet/Delta)                   (DynamoDB)
        └─────────────────┬─────────────────┘
                          ↓
                   Serving Layer
                   (Merged Query)
                          ↓
                     User Query
```

### Advantages

✅ **Accuracy**: Batch layer corrects errors in speed layer
✅ **Fault Tolerance**: Immutable data allows reprocessing
✅ **Scalability**: Separate scaling for batch and streaming
✅ **Flexibility**: Different technologies optimized for each layer

### Disadvantages

❌ **Complexity**: Two processing paradigms (batch + streaming)
❌ **Operational Overhead**: Maintain two separate code bases
❌ **Storage Costs**: Duplicate data in batch and speed layers
❌ **Merge Logic**: Complex query logic to combine layers

### When to Use

**Use Lambda When**:
- Need guaranteed accuracy (banking, healthcare)
- Complex batch analytics (ML training, aggregations)
- Reprocessing is frequent (fix bugs, add features)
- Team has expertise in both batch and streaming

**Example Use Cases**:
- **E-commerce**: Product recommendations (batch collaborative filtering + real-time session)
- **Banking**: Fraud detection (batch risk models + real-time transaction scoring)
- **IoT**: Predictive maintenance (batch trend analysis + real-time alerts)

---

## Kappa Architecture

### Overview

Proposed by Jay Kreps (2014, LinkedIn), Kappa simplifies Lambda by asking: *"What if everything is a stream?"*

**Core Principle**: Process all data as streams, reprocess by replaying from event log.

### Single Processing Layer

```
Event Log (Kafka/Kinesis) → Stream Processor → Materialized Views
                ↓
         Retention: 7-365 days
         Replay: Reprocess from timestamp
```

### Key Concepts

#### 1. **Event Log as Source of Truth**

- **Immutable**: Events never deleted (until retention expires)
- **Ordered**: Partition-level ordering guarantees
- **Replayable**: Reprocess any time range on demand
- **Retention**: Days to months (Kinesis: 7 days default, Kafka: configurable)

**Example**: Kinesis Data Stream with 365-day retention.

```python
# Replay last 30 days
stream.get_records(
    ShardIterator=get_shard_iterator(
        timestamp=now() - timedelta(days=30)
    )
)
```

#### 2. **Reprocessing Strategy**

Instead of batch jobs, reprocess by:
1. Create new version of stream processor
2. Replay events from offset/timestamp
3. Output to new materialized view (v2)
4. Switch reads from v1 → v2 (blue-green deployment)
5. Delete v1 after validation

**Benefits**:
- No separate batch layer
- Single code base (one processing logic)
- Testing = replay with sample data

#### 3. **Materialized Views**

Precomputed aggregations stored in databases:

```
Stream → Window (1 min) → Aggregate → DynamoDB (count by user_id)
Stream → Window (1 hour) → Aggregate → Redshift (daily totals)
```

**View Types**:
- **Real-time**: Updated every second (DynamoDB, ElastiCache)
- **Near-real-time**: Updated every minute (RDS, OpenSearch)
- **Batch**: Updated daily (Redshift, S3)

### Diagram

```
                Event Producers
                       ↓
              ┌────────────────┐
              │ Event Log      │
              │ (Kafka/Kinesis)│
              │ Retention: 30d │
              └────────┬───────┘
                       ↓
              Stream Processor v1
              (Flink/Kinesis Analytics)
                       ↓
              ┌────────┴────────┐
              ↓                 ↓
         Materialized      Materialized
         View A            View B
         (DynamoDB)        (OpenSearch)
```

**Reprocessing**:

```
Event Log → Stream Processor v2 → Materialized View v2
                ↓
          (Blue-Green Deploy)
```

### Advantages

✅ **Simplicity**: Single processing paradigm (streaming only)
✅ **Consistency**: One code base for all data
✅ **Replayability**: Easy reprocessing from event log
✅ **Real-time by Default**: All data available immediately

### Disadvantages

❌ **Retention Limits**: Event log storage costs (Kafka: $$, Kinesis: $$$)
❌ **Complex Analytics**: Streaming harder than batch for complex joins
❌ **Reprocessing Performance**: Slower than batch for full historical reprocessing
❌ **Stream Expertise**: Team needs strong streaming knowledge

### When to Use

**Use Kappa When**:
- Data naturally arrives as streams (clickstreams, logs, IoT)
- Reprocessing windows are short (<30 days)
- Team strong in stream processing
- Operational simplicity > performance

**Example Use Cases**:
- **Real-time Monitoring**: System metrics, application logs
- **Fraud Detection**: Credit card transactions (process once, near-real-time)
- **IoT Platforms**: Sensor data aggregation and alerting
- **Ad Tech**: Real-time bidding, impression counting

---

## Data Mesh

### Overview

Proposed by Zhamak Dehghani (2019, ThoughtWorks), Data Mesh addresses: *"How do we scale data platforms in large organizations?"*

**Core Principle**: Decentralize data ownership to domain teams, federate governance.

### Four Principles

#### 1. **Domain-Oriented Ownership**

Each business domain owns their data:

```
Product Domain → Product Data (sales, inventory, catalog)
Customer Domain → Customer Data (profiles, preferences, interactions)
Marketing Domain → Marketing Data (campaigns, attribution)
```

**Ownership Includes**:
- Data pipelines (ETL/ELT)
- Data quality
- Schema evolution
- SLAs/uptime

**Anti-pattern**: Central data team becomes bottleneck for 100+ domain requests.

#### 2. **Data as a Product**

Treat data like an API product with:

- **Discoverability**: Data catalog with descriptions
- **Addressability**: APIs/SQL endpoints
- **Trustworthiness**: SLAs, data quality metrics
- **Self-service**: Documentation, examples, access control
- **Interoperability**: Standard formats (Parquet, Avro)

**Example Data Product**:

```
Product Domain Data Product:
- Name: "Product Catalog"
- Owner: Product Engineering Team
- Format: Parquet (Delta Lake)
- Schema: Glue Schema Registry
- Access: Lake Formation (column-level)
- SLA: 99.9% uptime, <5min freshness
- Quality: 99.5% completeness, 0 duplicates
- Docs: API reference, examples, changelog
```

#### 3. **Self-Serve Data Platform**

Central platform team provides:

- **Infrastructure**: S3, Glue, Redshift, Kinesis
- **Developer Tools**: SDKs, CI/CD pipelines
- **Monitoring**: CloudWatch, Grafana
- **Governance**: Schema registry, data catalog
- **Cost Management**: Budgets, tagging

**Domain teams use** these tools to build their data products independently.

#### 4. **Federated Computational Governance**

Global policies enforced across all domains:

- **Schema Standards**: Naming conventions, data types
- **Data Quality**: Validation rules, SLAs
- **Security**: Encryption, access control (least privilege)
- **Privacy**: PII handling, GDPR compliance
- **Interoperability**: Standard formats (Parquet, Avro, JSON)

**Governance Tools**:
- Glue Data Catalog (central metadata)
- Lake Formation (access control)
- Schema Registry (compatibility rules)
- CloudTrail (audit logs)

### Diagram

```
                 ┌───────────────────────┐
                 │ Central Platform Team │
                 │ (Infrastructure)      │
                 └───────────┬───────────┘
                             ↓
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
  Product Domain        Sales Domain      Customer Domain
  (Team A)             (Team B)           (Team C)
        ↓                    ↓                    ↓
  Data Product A        Data Product B     Data Product C
  (S3 + Glue)          (DynamoDB)         (Redshift)
        ↓                    ↓                    ↓
  API + Catalog         API + Catalog      API + Catalog
        └────────────────────┼────────────────────┘
                             ↓
                 ┌───────────────────────┐
                 │ Federated Governance  │
                 │ (Schema, Security)    │
                 └───────────────────────┘
```

### Advantages

✅ **Scalability**: Teams work independently (parallelization)
✅ **Domain Expertise**: Teams closest to data understand it best
✅ **Autonomy**: Faster feature development (no central bottleneck)
✅ **Clear Ownership**: Accountability for data quality

### Disadvantages

❌ **Coordination Cost**: Need strong governance to prevent silos
❌ **Duplication**: Domains may reimplement common pipelines
❌ **Discovery**: Harder to find data across domains
❌ **Skill Requirements**: All teams need data engineering skills

### When to Use

**Use Data Mesh When**:
- Organization >50 data engineers
- Clear domain boundaries (Product, Sales, Customer)
- Domains have specialized knowledge
- Central data team is bottleneck

**Example Organizations**:
- **Uber**: 1000+ data engineers, 20+ domains (Rides, Eats, Freight)
- **Netflix**: 200+ engineers, domains by content type
- **Airbnb**: Domains by business unit (Homes, Experiences, Trust & Safety)

---

## Event-Driven Architecture

### Overview

**Principle**: Components communicate via events, not direct calls.

### Key Concepts

#### 1. **Events vs Commands**

**Event** (past tense, immutable):
```json
{
  "eventType": "OrderPlaced",
  "orderId": "order_123",
  "timestamp": "2026-03-09T10:30:00Z",
  "userId": "user_456",
  "amount": 99.99
}
```

**Command** (imperative, mutable):
```json
{
  "commandType": "PlaceOrder",
  "userId": "user_456",
  "items": ["item_1", "item_2"]
}
```

**Difference**:
- Events: "Something happened" (notification)
- Commands: "Do something" (instruction)

#### 2. **Event Backbone**

Central event bus routes events to consumers:

```
Producer → EventBridge → Rules → Targets (Lambda, SQS, Kinesis)
```

**AWS EventBridge Example**:

```python
# Producer: Order Service
eventbridge.put_events(
    Entries=[{
        'Source': 'order.service',
        'DetailType': 'OrderPlaced',
        'Detail': json.dumps(order_event)
    }]
)

# Consumer 1: Inventory Service (decrements stock)
# Consumer 2: Analytics Service (updates metrics)
# Consumer 3: Notification Service (sends email)
```

#### 3. **Event Choreography vs Orchestration**

**Choreography** (decentralized):
```
OrderPlaced → InventoryService (listens) → InventoryUpdated
           → PaymentService (listens) → PaymentProcessed
           → NotificationService (listens) → EmailSent
```

**Orchestration** (centralized with Step Functions):
```
Workflow:
1. Validate Order
2. Process Payment
3. Update Inventory
4. Send Notification
```

**Trade-offs**:
- Choreography: Loose coupling, harder to debug
- Orchestration: Centralized control, single point of failure

### Advantages

✅ **Decoupling**: Services don't know about each other
✅ **Scalability**: Add consumers without modifying producers
✅ **Resilience**: Services can fail independently
✅ **Audit Trail**: All events logged

### Disadvantages

❌ **Debugging**: Distributed tracing required (X-Ray)
❌ **Eventual Consistency**: No immediate guarantees
❌ **Complexity**: Many moving parts
❌ **Testing**: Need to mock event flows

---

## Event Sourcing & CQRS

### Event Sourcing

**Principle**: Store state changes as immutable events, reconstruct current state by replaying.

#### Example: Banking Account

**Traditional (CRUD)**:
```
Account Table: { id: 123, balance: $1,500 }
```

**Event Sourcing**:
```
Event Log:
1. AccountOpened { accountId: 123, initialBalance: $1,000 }
2. MoneyDeposited { accountId: 123, amount: $500 }
3. MoneyWithdrawn { accountId: 123, amount: $200 }
... (300 more events)

Current State: Replay all 303 events → Balance = $1,500
```

#### Benefits

✅ **Complete Audit Trail**: Every change recorded
✅ **Temporal Queries**: "What was balance on March 1?"
✅ **Replay**: Fix bugs by reprocessing events
✅ **Event-Driven**: Events trigger downstream systems

#### Implementation with DynamoDB

```python
# Event Store Schema
{
    "PK": "ACCOUNT#123",
    "SK": "EVENT#2026-03-09T10:30:00Z#uuid",
    "eventType": "MoneyDeposited",
    "amount": 500,
    "timestamp": "2026-03-09T10:30:00Z"
}

# Query all events for account
events = dynamodb.query(
    KeyConditionExpression="PK = :pk",
    ExpressionAttributeValues={":pk": "ACCOUNT#123"}
)

# Replay to get current balance
balance = 0
for event in events['Items']:
    if event['eventType'] == 'MoneyDeposited':
        balance += event['amount']
    elif event['eventType'] == 'MoneyWithdrawn':
        balance -= event['amount']
```

### CQRS (Command Query Responsibility Segregation)

**Principle**: Separate write model (commands) from read model (queries).

#### Architecture

```
Write Side:                         Read Side:
Commands → Event Store         Events → Projections → Read Models
(Normalize, Validate)          (Denormalize, Optimize)
       ↓                                    ↓
DynamoDB (events)                    ElastiCache (views)
                                     Redshift (analytics)
                                     OpenSearch (search)
```

#### Example: E-commerce Order

**Command Model** (Write):
```python
def place_order(order):
    # Validate inventory, payment
    event = create_event("OrderPlaced", order)
    event_store.append(event)  # Write to DynamoDB
    event_bus.publish(event)   # Trigger projections
```

**Query Model** (Read):
```python
def get_order_summary(user_id):
    # Read from optimized view (ElastiCache)
    return cache.get(f"order_summary:{user_id}")
```

**Projections** (Event Handlers):
```python
# Update read model when event received
def on_order_placed(event):
    summary = {
        "user_id": event["userId"],
        "order_count": get_order_count(event["userId"]) + 1,
        "total_spent": get_total_spent(event["userId"]) + event["amount"]
    }
    cache.set(f"order_summary:{event['userId']}", summary)
```

### Advantages

✅ **Optimized Reads**: Read models tuned for specific queries
✅ **Scalability**: Read/write scale independently
✅ **Flexibility**: Multiple read models from same events
✅ **Performance**: Precomputed views (no joins at query time)

### Disadvantages

❌ **Eventual Consistency**: Writes not immediately visible in reads
❌ **Complexity**: More infrastructure (event store + read models)
❌ **Storage**: Duplicate data in multiple read models
❌ **Synchronization**: Projections must stay up-to-date

### When to Use

**Use Event Sourcing + CQRS When**:
- Audit requirements (financial, healthcare)
- Complex business logic with many state changes
- Need temporal queries ("show me state 3 months ago")
- High read:write ratio (10:1 or higher)

**Example Use Cases**:
- **Banking**: Every transaction must be auditable
- **Order Management**: Track order lifecycle (placed → paid → shipped → delivered)
- **Collaboration Tools**: Version history (Google Docs-like change tracking)

---

## Multi-Region Architectures

### Overview

Deploy data platform across multiple AWS regions for:

- **Low Latency**: Users query nearest region (<100ms)
- **High Availability**: Survive regional outages (99.99%+)
- **Compliance**: Data residency requirements (GDPR)
- **Disaster Recovery**: Automatic failover in minutes

### Patterns

#### 1. **Active-Passive** (Backup Region)

```
Primary (us-east-1) → Writes + Reads
          ↓
Replication (async)
          ↓
Secondary (us-west-2) → Read-only
```

**Failover**: Manual switch to secondary (minutes to hours)
**Cost**: 50% extra (storage only, minimal compute)
**Use Case**: Disaster recovery, not performance

#### 2. **Active-Active** (Multi-Master)

```
US Region (us-east-1) ← → EU Region (eu-west-1)
     ↓                          ↓
  US Users                   EU Users
  (Write + Read)            (Write + Read)
```

**Replication**: Bidirectional, near-real-time (<1 second)
**Conflicts**: Possible when same item written in both regions
**Cost**: 100%+ extra (full infrastructure × regions)
**Use Case**: Global applications with local writes

#### 3. **Active-Active-Active** (Multi-Region)

Global deployment across 3+ regions:

```
US (us-east-1) ←→ EU (eu-west-1) ←→ APAC (ap-southeast-1)
```

### AWS Technologies

#### **DynamoDB Global Tables**

Fully managed multi-region replication:

```python
# Create global table
dynamodb.create_global_table(
    GlobalTableName='orders',
    ReplicationGroup=[
        {'RegionName': 'us-east-1'},
        {'RegionName': 'eu-west-1'},
        {'RegionName': 'ap-southeast-1'}
    ]
)

# Write to us-east-1
dynamodb_us.put_item(TableName='orders', Item=order)

# Automatically replicated to eu-west-1 and ap-southeast-1 (<1 sec)
```

**Consistency**: Strong consistency within region, eventual across regions
**Conflict Resolution**: Last-Write-Wins (LWW) by timestamp

#### **Aurora Global Database**

Cross-region MySQL/PostgreSQL:

```python
# Create global cluster
rds.create_global_cluster(
    GlobalClusterIdentifier='ecommerce-global',
    Engine='aurora-postgresql',
    EngineVersion='15.4'
)

# Add regions
rds.create_db_cluster(
    DBClusterIdentifier='ecommerce-us',
    GlobalClusterIdentifier='ecommerce-global',
    ...
)
```

**Replication**: <1 second lag
**Reads**: Local reads from each region (low latency)
**Writes**: Sent to primary region (single-master)
**Failover**: Promote secondary to primary (<1 minute)

#### **S3 Cross-Region Replication**

Replicate data lake across regions:

```python
# Enable CRR
s3.put_bucket_replication(
    Bucket='data-lake-us',
    ReplicationConfiguration={
        'Role': replication_role_arn,
        'Rules': [{
            'Prefix': 'raw/',
            'Status': 'Enabled',
            'Destination': {
                'Bucket': 'arn:aws:s3:::data-lake-eu',
                'ReplicationTime': {
                    'Status': 'Enabled',
                    'Time': {'Minutes': 15}  # SLA
                }
            }
        }]
    }
)
```

### Conflict Resolution

When same item written in multiple regions:

#### **Last-Write-Wins (LWW)**

```python
# Two writes to same item
# US: { id: 1, name: "John", timestamp: 10:30:00 }
# EU: { id: 1, name: "Jane", timestamp: 10:30:05 }

# Result: EU wins (later timestamp)
# Final: { id: 1, name: "Jane", timestamp: 10:30:05 }
```

**Simple but**: Lost data (John) not recoverable.

#### **Multi-Value**

```python
# DynamoDB returns both versions
item = dynamodb.get_item(TableName='users', Key={'id': 1})
# Result: [
#   { name: "John", timestamp: 10:30:00, region: "us" },
#   { name: "Jane", timestamp: 10:30:05, region: "eu" }
# ]

# Application must resolve
resolved_name = resolve_conflict(item)
```

#### **Custom Resolution**

```python
# Business logic determines winner
def resolve_conflict(versions):
    # Priority: EU > US > APAC
    for region in ['eu-west-1', 'us-east-1', 'ap-southeast-1']:
        version = find_version(versions, region)
        if version:
            return version
    return versions[0]  # Fallback to first
```

### When to Use

**Use Multi-Region When**:
- Global user base (users in US, EU, APAC)
- Latency SLA <100ms (single region insufficient)
- High availability required (99.99%+)
- Compliance (data residency in EU)

**Cost-Benefit Analysis**:
- Single Region: $10K/month, 150ms latency (EU users)
- Multi-Region (2): $25K/month, <50ms latency (all users)
- **Break-even**: If >40% users are EU and latency matters, worth it

---

## Polyglot Persistence

### Overview

**Principle**: Use specialized databases for each use case, not one-size-fits-all.

### Database Selection Guide

| Use Case | Database | Why |
|----------|----------|-----|
| **Transactions** | Aurora PostgreSQL | ACID, relational |
| **Key-Value** | DynamoDB | Scalability, single-digit ms |
| **Caching** | ElastiCache (Redis) | In-memory, sub-ms |
| **Analytics** | Redshift | OLAP, columnar, fast aggregations |
| **Search** | OpenSearch | Full-text, fuzzy matching |
| **Graph** | Neptune | Relationships (fraud, social) |
| **Time-Series** | Timestream | IoT, metrics, optimized storage |
| **Document** | DocumentDB | Flexible schema, JSON |

### Anti-Pattern: One Database for Everything

**Problem**: Using PostgreSQL for all workloads

```
PostgreSQL:
- Transactions (orders) → ✅ Good (ACID)
- Analytics (aggregations) → ❌ Slow (row-based)
- Caching (product details) → ❌ Wasteful (disk I/O)
- Search (product catalog) → ❌ Poor (no full-text ranking)
- Graphs (recommendations) → ❌ Complex (recursive joins)
```

**Result**: Poor performance, high costs, frustrated users.

### Polyglot Example: E-commerce

```
┌─────────────────────────────────────────┐
│            Application Layer            │
└─────────────────┬───────────────────────┘
                  ↓
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
Aurora       DynamoDB      ElastiCache
(Orders)     (Cart)        (Product Cache)
ACID          Low latency   Sub-ms reads
    ↓             ↓             ↓
Redshift     OpenSearch    Neptune
(Analytics)  (Search)      (Recommendations)
Aggregations Full-text     Graph queries
```

**Data Flow**:

1. **Write**: Order placed → Aurora (transactional)
2. **Cache**: Product details → ElastiCache (read-heavy)
3. **Search**: Product catalog → OpenSearch (full-text)
4. **Analytics**: Order data → Redshift (via CDC)
5. **Recommendations**: User→Product graph → Neptune

### Change Data Capture (CDC)

Sync data from operational (OLTP) to analytical (OLAP) databases:

```
Aurora PostgreSQL → DMS (CDC) → S3 → Glue → Redshift
(Source: Transactions)                  (Target: Analytics)
```

**CDC Tools**:
- **AWS DMS**: Database Migration Service (real-time replication)
- **Debezium**: Open-source CDC (Kafka-based)
- **DynamoDB Streams**: Native change streams

**Example**:

```python
# DynamoDB Stream Handler
def handle_stream_record(record):
    if record['eventName'] == 'INSERT':
        new_item = record['dynamodb']['NewImage']
        # Sync to Redshift
        redshift.insert(table='orders', data=new_item)
```

### Advantages

✅ **Performance**: Each database optimized for use case
✅ **Cost**: Cheaper specialized databases (vs one expensive RDBMS)
✅ **Scalability**: Scale independently per workload
✅ **Resilience**: Failure in one database doesn't affect others

### Disadvantages

❌ **Complexity**: Multiple databases to manage
❌ **Consistency**: Eventual consistency across databases
❌ **Data Synchronization**: CDC pipelines add latency
❌ **Operational Burden**: More monitoring, backups, upgrades

---

## CAP Theorem & Consistency Models

### CAP Theorem

Proven by Eric Brewer (2000): Distributed systems can provide AT MOST 2 of 3:

- **C** (Consistency): All nodes see same data at same time
- **A** (Availability): Every request gets response (success/failure)
- **P** (Partition Tolerance): System continues despite network splits

**Reality**: Partition tolerance is mandatory (networks DO fail), so choose:

- **CP**: Consistency + Partition Tolerance (sacrifice availability)
- **AP**: Availability + Partition Tolerance (sacrifice consistency)

### Consistency Models

#### 1. **Strong Consistency** (CP)

Read always returns latest write:

```
Write(x=1) → Success
Read(x) → 1 (guaranteed)
```

**AWS Examples**:
- DynamoDB: `ConsistentRead=True`
- Aurora: Within single region
- S3: After PUT succeeds

**Trade-off**: Higher latency (wait for replication), may fail during partitions.

#### 2. **Eventual Consistency** (AP)

Read may return stale data, but eventually consistent:

```
Write(x=1) → Success
Read(x) → 0 (stale, immediately after write)
Read(x) → 1 (after propagation, ~100ms)
```

**AWS Examples**:
- DynamoDB: Default (`ConsistentRead=False`)
- DynamoDB Global Tables
- S3 (eventually consistent for overwrite PUT)

**Trade-off**: Stale reads possible, but always available.

#### 3. **Causal Consistency**

Reads respect causality:

```
Write(x=1) → Write(y=2, depends on x)
Read(y=2) → Must also see x=1 (causally related)
```

**Use Case**: Chat applications (see replies after message).

#### 4. **Timeline Consistency** (LinkedIn's Espresso)

Guarantee order of events per entity:

```
User 123: Update Name → Update Email → Update Phone
Any read sees updates in order (never phone before name)
```

**Implementation**: Version vector per entity.

### Consistency Spectrum

```
Strong                  Causal              Eventual
  │                       │                    │
  ↓                       ↓                    ↓
Slow, Available     Balance               Fast, May-Be-Stale
(Aurora, RDS)      (Custom)               (DynamoDB, Global)
```

---

## Architectural Trade-offs

### Lambda vs Kappa

| Criterion | Lambda | Kappa | Winner |
|-----------|--------|-------|--------|
| **Simplicity** | ❌ Complex (2 systems) | ✅ Simple (1 system) | Kappa |
| **Accuracy** | ✅ Batch reprocessing | ⚠️ Stream reprocessing | Lambda |
| **Latency** | ✅ Real-time speed layer | ✅ Real-time processing | Tie |
| **Cost** | ❌ 2x storage | ✅ 1x storage | Kappa |
| **Complex SQL** | ✅ Spark SQL easy | ❌ Streaming SQL hard | Lambda |
| **Reprocessing** | ✅ Fast batch | ⚠️ Slower stream replay | Lambda |

**Decision**:
- **Lambda**: Banking, healthcare, complex analytics (accuracy critical)
- **Kappa**: IoT, monitoring, fraud detection (simplicity + speed)

### Centralized vs Data Mesh

| Criterion | Centralized | Data Mesh | Winner |
|-----------|-------------|-----------|--------|
| **Team Size** | ✅ <50 engineers | ✅ >50 engineers | Context |
| **Speed** | ❌ Bottleneck | ✅ Parallel work | Mesh |
| **Consistency** | ✅ Single standard | ❌ Risk of silos | Central |
| **Domain Expertise** | ❌ Data team generic | ✅ Domain teams expert | Mesh |
| **Governance** | ✅ Easy enforcement | ❌ Federated complexity | Central |

**Decision**:
- **Centralized**: Startups, <50 engineers, simple domains
- **Data Mesh**: Enterprises, >50 engineers, clear domain boundaries (Uber, Netflix)

### CRUD vs Event Sourcing

| Criterion | CRUD | Event Sourcing | Winner |
|-----------|------|----------------|--------|
| **Simplicity** | ✅ Simple DB ops | ❌ Complex replay | CRUD |
| **Audit** | ❌ No history | ✅ Complete trail | Event |
| **Performance** | ✅ Direct reads | ❌ Replay overhead | CRUD |
| **Temporal Queries** | ❌ Not possible | ✅ Time travel | Event |
| **Storage** | ✅ Current state only | ❌ All events | CRUD |
| **Debugging** | ❌ Lost history | ✅ Full trace | Event |

**Decision**:
- **CRUD**: Most applications (e.g., blog, social media)
- **Event Sourcing**: High compliance (banking, healthcare), need audit trail

### Single-Region vs Multi-Region

| Criterion | Single Region | Multi-Region | Winner |
|-----------|---------------|--------------|--------|
| **Latency** | ❌ 150ms (global) | ✅ <50ms (local) | Multi |
| **Cost** | ✅ $10K/month | ❌ $30K/month | Single |
| **Availability** | ⚠️ 99.9% | ✅ 99.99% | Multi |
| **Complexity** | ✅ Simple | ❌ Conflict resolution | Single |
| **Compliance** | ❌ May violate GDPR | ✅ Data residency | Multi |

**Break-Even Analysis**:

```python
# Calculate if multi-region is worth it
single_region_cost = 10000  # per month
multi_region_cost = 30000   # per month
extra_cost = 20000          # per month

# Revenue impact of latency
users_affected = 0.4  # 40% users are EU/APAC
conversion_lift = 0.15  # 15% more conversions with <50ms
monthly_revenue = 500000  # $500K revenue/month

revenue_gain = monthly_revenue * users_affected * conversion_lift
# = $500K × 0.4 × 0.15 = $30K/month

# Net benefit = $30K (revenue) - $20K (extra cost) = +$10K/month
# Decision: Multi-region is worth it
```

---

## Key Architectural Principles

### 1. **Loose Coupling**

Components interact via well-defined interfaces:

```
Service A → Event Bus → Service B
(No direct dependency)
```

**Benefits**: Change Service B without modifying Service A.

### 2. **High Cohesion**

Related functionality grouped together:

```
Order Service:
- place_order()
- cancel_order()
- get_order_status()

NOT:
- place_order() in Service A
- cancel_order() in Service B (low cohesion)
```

### 3. **Immutability**

Data written once, never modified:

```
❌ UPDATE orders SET status='shipped' WHERE id=123
✅ INSERT INTO order_events (event_type, order_id, timestamp)
   VALUES ('OrderShipped', 123, NOW())
```

**Benefits**: Audit trail, time travel queries, easy replication.

### 4. **Idempotency**

Same operation executed multiple times = same result:

```python
# Idempotent (safe to retry)
def create_order(order_id, data):
    if exists(order_id):
        return get_order(order_id)  # Already created
    else:
        return insert_order(order_id, data)

# Not idempotent (duplicate orders on retry)
def create_order(data):
    order_id = generate_id()  # Different each time!
    return insert_order(order_id, data)
```

**Critical For**: Retries, exactly-once processing, disaster recovery.

### 5. **Circuit Breaker**

Stop calling failing service (fail fast):

```python
class CircuitBreaker:
    def call(self, func):
        if self.failure_rate > 0.5:  # 50% failures
            raise CircuitOpenError("Service unavailable")

        try:
            return func()
        except Exception:
            self.failures += 1
            raise
```

**Prevents**: Cascading failures (don't bring down entire system).

---

## Summary

### Pattern Selection Matrix

| Use Case | Pattern | Complexity | Cost | Latency |
|----------|---------|------------|------|---------|
| **Real-time + Historical** | Lambda | High | $$$ | ms + hours |
| **Stream-First** | Kappa | Medium | $$ | ms |
| **Large Org** | Data Mesh | High | $$$ | Varies |
| **Audit Trail** | Event Sourcing | High | $$ | ms |
| **Global Users** | Multi-Region | Medium | $$$ | <50ms |
| **Mixed Workloads** | Polyglot | Medium | $$ | Optimized |

### Key Takeaways

1. **No Silver Bullet**: Every architecture has trade-offs
2. **Start Simple**: Begin with centralized/single-paradigm, evolve as needed
3. **Measure First**: Quantify latency/cost/complexity before decision
4. **Team Skills**: Architecture must match team capabilities
5. **Business Value**: Justify complexity with revenue/cost savings

### Recommended Reading

- **Designing Data-Intensive Applications** (Martin Kleppmann) - Chapter 11: Stream Processing
- **Building Microservices** (Sam Newman) - Chapters on events and orchestration
- **Big Data** (Nathan Marz) - Lambda Architecture explained by creator
- **Data Mesh** (Zhamak Dehghani) - Principles and implementation

---

**Next**: Read [architecture.md](architecture.md) for AWS reference architectures with diagrams.
