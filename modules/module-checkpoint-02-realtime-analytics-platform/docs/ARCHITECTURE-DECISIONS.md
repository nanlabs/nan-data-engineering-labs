# Architecture Decision Records (ADRs)

## Overview

This document captures key architectural decisions made for the RideShare Real-Time Analytics Platform. Each Architecture Decision Record (ADR) follows the format:

- **Context**: The situation and problem
- **Decision**: The chosen solution
- **Rationale**: Why this decision was made
- **Consequences**: Trade-offs and implications
- **Alternatives Considered**: Other options evaluated

---

## ADR-001: Use Amazon Kinesis Data Streams for Event Ingestion

**Date**: 2024-01-15

**Status**: Accepted

### Context

We need to ingest 100,000+ events per minute from mobile applications with requirements for:
- Low latency (<1 second ingestion)
- Durable storage (24-168 hours)
- Ordered delivery within partition
- Scalability to 1M+ events per minute
- Integration with AWS Lambda and analytics services

### Decision

Use **Amazon Kinesis Data Streams** for all event ingestion.

### Rationale

**Pros**:
1. **AWS-Native Integration**: Seamless integration with Lambda, Kinesis Data Analytics, S3
2. **Managed Service**: No infrastructure to manage (servers, clusters)
3. **Durability**: Data replicated across 3 AZs automatically
4. **Ordering**: Guarantees ordering within shard (partition key)
5. **Scalability**: Can scale from 1 to 1000+ shards
6. **Cost-Effective**: Pay per shard-hour + PUT payload units (cheaper than Kafka for our scale)
7. **Low Latency**: Sub-second to low-second latency
8. **Retention**: Configurable 24 hours to 365 days
9. **Security**: Integrated with IAM, KMS encryption
10. **Replay**: Can replay data from any point in retention period

**Cons**:
1. AWS vendor lock-in
2. Shard limits (1 MB/s write, 2 MB/s read per shard)
3. Manual shard management (provisioned mode) or higher cost (on-demand)

### Consequences

**Positive**:
- Fast time-to-market (no cluster setup)
- Reduced operational overhead
- Built-in high availability
- Easy integration with downstream services

**Negative**:
- Migration to other cloud providers requires significant rework
- Need to monitor and manage shard count
- Costs can increase with high throughput in on-demand mode

### Alternatives Considered

#### Apache Kafka (on Amazon MSK)

**Pros**:
- More powerful (exactly-once semantics, transactions)
- Cloud-agnostic (portable to other clouds)
- Larger ecosystem of tools
- No shard limits (partition management more flexible)

**Cons**:
- Higher operational complexity (cluster management, upgrades)
- Higher cost (~$200-500/month for small cluster)
- Steeper learning curve
- Need to manage Kafka Connect for integrations

**Why Not Chosen**: Operational complexity and cost outweigh benefits for our use case. We don't need advanced Kafka features like transactions.

#### Amazon SQS

**Pros**:
- Simpler (no shard management)
- Cheaper ($0.40 per million requests)
- Auto-scaling

**Cons**:
- No ordering guarantee (except FIFO queues, which have low throughput)
- No replay capability
- Not designed for streaming analytics
- No native integration with analytics tools

**Why Not Chosen**: Lack of ordering and replay makes it unsuitable for streaming analytics.

#### Amazon EventBridge

**Pros**:
- Event routing capabilities
- Schema registry
- Integration with 20+ AWS services

**Cons**:
- Designed for event routing, not high-throughput streaming
- Higher latency
- More expensive for high volume

**Why Not Chosen**: Not designed for high-throughput streaming workloads.

### Implementation Notes

- Use **provisioned mode** for development (predictable, low cost)
- Consider **on-demand mode** for production (auto-scaling, pay for what you use)
- Set **retention to 24 hours** for development, **168 hours for production** (compliance)
- Enable **KMS encryption** for data at rest
- Use **enhanced fan-out** if multiple consumers need high throughput

---

## ADR-002: Use Lambda vs Kinesis Data Analytics for Stream Processing

**Date**: 2024-01-16

**Status**: Accepted

### Context

We need to process streaming events with two types of operations:
1. **Simple transformations**: Parse JSON, validate schema, write to DynamoDB
2. **Complex aggregations**: Windowing (1-min, 5-min), joins, Top-N queries

### Decision

Use **both AWS Lambda and Kinesis Data Analytics**:
- **Lambda** for simple, event-driven transformations
- **Kinesis Data Analytics (Flink SQL)** for complex analytics

### Rationale for Lambda

**Pros**:
1. **Low Latency**: Sub-second processing
2. **Cost-Effective**: Pay per invocation and compute time (cheap for simple operations)
3. **Flexible**: Can use any language/library
4. **Easy Debugging**: CloudWatch Logs, X-Ray tracing
5. **Stateless**: No state management needed for simple transforms
6. **Auto-Scaling**: Scales to handle load automatically

**Cons**:
1. **Not Designed for Stateful Processing**: No built-in windowing or aggregations
2. **Cold Starts**: 1-2 second latency on first invocation
3. **Memory Limits**: Max 10 GB memory
4. **Execution Time Limits**: Max 15 minutes

### Rationale for Kinesis Data Analytics

**Pros**:
1. **Built for Streaming Analytics**: Native windowing (tumbling, sliding, session)
2. **SQL Interface**: Easy to write complex queries
3. **Stateful Processing**: Maintains state across windows
4. **Exactly-Once Semantics**: With checkpointing
5. **Joins**: Can join multiple streams or reference data
6. **Auto-Scaling**: Scales KPUs based on load

**Cons**:
1. **Higher Cost**: $0.11 per KPU-hour (1 KPU = 1 vCPU + 4 GB memory)
2. **Higher Latency**: Seconds to minutes depending on window size
3. **Less Flexible**: Limited to Flink SQL (no custom Python/Java unless using Flink API)
4. **Debugging**: More difficult than Lambda

### Consequences

**Positive**:
- Optimal cost/performance for each workload type
- Simple transformations run fast and cheap on Lambda
- Complex analytics leverage Flink's powerful windowing engine
- Can scale each component independently

**Negative**:
- More components to manage and monitor
- Need to learn both Lambda and Flink SQL
- Split architecture (speed layer and analytics layer)

### Decision Matrix

| Operation Type | Service | Reason |
|---------------|---------|--------|
| Parse & validate events | Lambda | Simple, low latency, cheap |
| Enrich with DynamoDB lookup | Lambda | Can use boto3, low latency |
| Write to DynamoDB/S3 | Lambda | Simple I/O operations |
| 1-minute tumbling window aggregations | Kinesis Analytics | Native windowing |
| 5-minute sliding window (surge pricing) | Kinesis Analytics | Sliding windows, stateful |
| Geospatial clustering (hot spots) | Kinesis Analytics | Complex SQL joins |
| Top-N queries | Kinesis Analytics | Built-in Top-N support |

### Alternatives Considered

#### Use Only Lambda

**Why Not**: Would require implementing custom windowing logic, state management, which is complex and error-prone.

#### Use Only Kinesis Data Analytics

**Why Not**: Overkill for simple transformations, higher cost, less flexible.

#### Use Apache Flink on EMR/EKS

**Why Not**: Much higher operational complexity, costs, and expertise required.

---

## ADR-003: Use DynamoDB for Real-Time State Storage

**Date**: 2024-01-17

**Status**: Accepted

### Context

We need a database for:
- Real-time ride state (in-progress rides)
- Driver availability and locations
- Pre-computed aggregated metrics for dashboards

Requirements:
- Single-digit millisecond read/write latency
- Scalable to handle 1000s of writes per second
- Pay-per-use pricing model
- Integration with Lambda and QuickSight

### Decision

Use **Amazon DynamoDB** with on-demand billing mode.

### Rationale

**Pros**:
1. **Low Latency**: <10ms reads, <20ms writes (P99)
2. **Serverless**: No servers to manage, auto-scaling
3. **Cost-Effective**: Pay only for what you use (on-demand mode)
4. **Highly Available**: Multi-AZ replication, 99.99% SLA
5. **Flexible Schema**: NoSQL, can evolve schema over time
6. **Streams**: DynamoDB Streams for CDC (change data capture)
7. **TTL**: Automatic expiration of old records
8. **Global Secondary Indexes**: Flexible query patterns
9. **Integration**: Native integration with Lambda, Kinesis

**Cons**:
1. **Query Limitations**: No complex joins, limited filtering (not a full RDBMS)
2. **Cost at Scale**: Can be expensive at very high throughput (but on-demand helps)
3. **Capacity Planning**: Need to understand RCU/WCU (on-demand abstracts this)

### Consequences

**Positive**:
- Fast development (no schema migrations needed)
- Predictable performance at scale
- No database administration overhead
- Cost scales with usage

**Negative**:
- Need to denormalize data (no joins)
- Query patterns must be designed upfront (GSIs)
- Cost can be higher than RDS for analytical queries at scale

### Data Model Design

**Table: rides_state**
- **Partition Key**: `ride_id`
- **Attributes**: `customer_id`, `driver_id`, `status`, `pickup_location`, `dropoff_location`, `timestamps`, etc.
- **GSI**: `StatusIndex` (status, request_timestamp) for querying active rides

**Table: driver_availability**
- **Partition Key**: `driver_id`
- **Attributes**: `location` (lat, lon), `available`, `current_ride_id`, `last_update`, `city`
- **GSI**: `CityAvailableIndex` (city, available) for finding available drivers in a city

**Table: aggregated_metrics**
- **Partition Key**: `metric_name` (e.g., "active_rides_nyc")
- **Sort Key**: `timestamp` (minute-level granularity)
- **Attributes**: `value`, `dimensions`
- **TTL**: 30 days

### Alternatives Considered

#### Amazon RDS (PostgreSQL)

**Pros**:
- Relational model (joins, transactions)
- Familiar SQL
- Complex queries

**Cons**:
- Higher latency (10-50ms typical)
- Need to provision instances (r5.large, etc.)
- Vertical scaling limits
- More expensive for OLTP workloads

**Why Not Chosen**: Higher latency and operational overhead. Don't need relational features for real-time state.

#### Amazon Aurora Serverless

**Pros**:
- Auto-scaling
- SQL queries
- Good for read-heavy workloads

**Cons**:
- Higher latency than DynamoDB (20-100ms)
- Cold start issues (if scaled to 0)
- More expensive than DynamoDB for write-heavy workloads

**Why Not Chosen**: Latency requirements favor DynamoDB.

#### Redis (Amazon ElastiCache)

**Pros**:
- Extremely fast (<1ms latency)
- Rich data structures
- Pub/Sub capabilities

**Cons**:
- In-memory only (need persistence configuration)
- Need to manage cluster sizing
- Higher cost (pay for capacity, not usage)
- No native integration with QuickSight

**Why Not Chosen**: Operational complexity and cost. DynamoDB meets latency requirements.

---

## ADR-004: Use Step Functions for Workflow Orchestration

**Date**: 2024-01-18

**Status**: Accepted

### Context

We need to orchestrate:
- Daily batch aggregations (parallel processing of rides, drivers, payments)
- Weekly reporting (fan-out to cities, fan-in for summary)
- Error handling and retries
- Notifications on success/failure

Requirements:
- Visual workflow design
- Parallel and sequential processing
- Error handling with retries
- Integration with Lambda, Glue, SNS
- Cost-effective (<$50/month)

### Decision

Use **AWS Step Functions** (Standard Workflows).

### Rationale

**Pros**:
1. **Serverless**: No servers to manage
2. **Visual Designer**: Easy to design and debug workflows
3. **Built-in Error Handling**: Retry, catch, fallback
4. **Parallel Processing**: Parallel states for concurrent execution
5. **Integration**: Native integration with 200+ AWS services
6. **State Management**: Maintains state across steps
7. **Audit Trail**: CloudWatch Logs for all executions
8. **Cost-Effective**: $0.025 per 1,000 state transitions (cheap for our use case)

**Cons**:
1. **Execution Time Limit**: Max 1 year (not an issue for us)
2. **Payload Size Limit**: 256 KB (need to use S3 for large data)
3. **Learning Curve**: JSON-based state machine definition

### Consequences

**Positive**:
- Simplified orchestration logic (no custom code for retries, parallelism)
- Visual representation of workflows
- Easy to add new steps or modify existing workflows
- Low operational overhead

**Negative**:
- JSON definition can become verbose
- Debugging can be tricky for complex workflows
- Cost increases with number of transitions (but still cheap for our scale)

### Example Workflow Definition

```json
{
  "Comment": "Daily aggregation workflow",
  "StartAt": "Parallel",
  "States": {
    "Parallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "AggregateRides",
          "States": {
            "AggregateRides": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:function:aggregate-rides",
              "Retry": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 3,
                  "BackoffRate": 2
                }
              ],
              "End": true
            }
          }
        },
        {
          "StartAt": "AggregateDrivers",
          "States": {
            "AggregateDrivers": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:function:aggregate-drivers",
              "Retry": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 3,
                  "BackoffRate": 2
                }
              ],
              "End": true
            }
          }
        }
      ],
      "Next": "NotifySuccess"
    },
    "NotifySuccess": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:...:daily-aggregation-success",
        "Message": "Daily aggregation completed successfully"
      },
      "End": true
    }
  }
}
```

### Alternatives Considered

#### Apache Airflow (Amazon MWAA)

**Pros**:
- Powerful scheduling (complex DAGs)
- Python-based (familiar to data engineers)
- Rich ecosystem of operators
- Open-source (portable)

**Cons**:
- Higher cost ($300-500/month for small environment)
- Need to manage Airflow cluster (even though MWAA is managed)
- Overkill for simple workflows
- Higher learning curve

**Why Not Chosen**: Overkill for our use case, higher cost, operational complexity.

#### AWS Glue Workflows

**Pros**:
- Integrated with Glue ETL
- Visual designer
- Triggers for scheduling

**Cons**:
- Limited to Glue jobs
- Less powerful than Step Functions for general orchestration
- No Lambda integration

**Why Not Chosen**: Limited functionality compared to Step Functions.

#### Prefect/Dagster (self-hosted or cloud)

**Pros**:
- Modern workflow engines
- Python-based
- Good developer experience

**Cons**:
- Need to self-host or pay for cloud ($100-500/month)
- Additional infrastructure to manage
- Not AWS-native (integration requires custom code)

**Why Not Chosen**: Additional infrastructure and cost.

---

## ADR-005: Use QuickSight for Dashboards

**Date**: 2024-01-19

**Status**: Accepted

### Context

We need real-time dashboards for:
- **Operations Team**: Active rides, available drivers, revenue, alerts
- **Executives**: Daily trends, city comparisons, top performers

Requirements:
- Auto-refresh (10 seconds for operational, 1 hour for executive)
- Connect to DynamoDB (real-time) and Athena (historical)
- Role-based access control
- Mobile-responsive
- Cost-effective (<$100/month for 10 users)

### Decision

Use **Amazon QuickSight** (Enterprise Edition).

### Rationale

**Pros**:
1. **AWS-Native**: Direct connection to DynamoDB, Athena, S3
2. **Auto-Refresh**: Enterprise edition supports scheduled refresh
3. **Cost-Effective**: $9/user/month (vs $70+/user for Tableau)
4. **Serverless**: No infrastructure to manage
5. **Mobile**: Responsive design, mobile apps (iOS, Android)
6. **SPICE**: In-memory engine for fast queries
7. **Embedded Analytics**: Can embed in custom apps (future)
8. **Row-Level Security**: For multi-tenant scenarios

**Cons**:
1. **Limited Customization**: Not as flexible as Tableau/Looker
2. **Learning Curve**: UI is different from traditional BI tools
3. **SPICE Limits**: 250 GB per user (can be extended)
4. **Refresh API**: Not as robust as competitors

### Consequences

**Positive**:
- Low cost ($90/month for 10 users)
- Fast time-to-value (no server setup)
- Native AWS integration (no connectors needed)
- Scales with usage

**Negative**:
- Limited customization for complex visualizations
- Refresh scheduling less flexible than some competitors

### Dashboard Design

**Operational Dashboard**:
- KPI Cards: Active Rides, Available Drivers, Current Revenue, Avg Wait Time
- Line Chart: Rides over time (last 4 hours)
- Bar Chart: Rides by city (top 10)
- Heatmap: Geographic density of rides
- Table: Recent alerts

**Executive Dashboard**:
- KPI Cards: Daily metrics vs yesterday, MTD vs last month
- Line Charts: Daily rides, revenue, CSAT (last 30 days)
- Pie Chart: Revenue by city
- Bar Chart: Top 10 drivers by rating and ride count

### Alternatives Considered

#### Tableau

**Pros**:
- Most powerful BI tool
- Incredible customization
- Large community

**Cons**:
- Very expensive ($70/user/month)
- Need Tableau Server ($1000s/month)
- Overkill for our use case

**Why Not Chosen**: Cost.

#### Grafana (on Amazon Managed Grafana)

**Pros**:
- Great for system metrics
- Real-time dashboards
- Open-source (portable)

**Cons**:
- Not designed for business analytics
- No connection to DynamoDB (need to use Athena or API)
- Higher learning curve for non-technical users

**Why Not Chosen**: Better for system monitoring than business analytics.

#### Apache Superset (self-hosted)

**Pros**:
- Open-source (free)
- Powerful and customizable

**Cons**:
- Need to self-host (infrastructure, maintenance)
- No native DynamoDB connector
- Smaller community than commercial tools

**Why Not Chosen**: Operational overhead.

#### CloudWatch Dashboards

**Pros**:
- Free (included with AWS)
- Native integration with CloudWatch metrics
- Good for system monitoring

**Cons**:
- Not designed for business metrics
- Limited visualization types
- No connection to DynamoDB/Athena

**Why Not Chosen**: Better for system monitoring, not business dashboards.

---

## ADR-006: Use Terraform for Infrastructure as Code

**Date**: 2024-01-20

**Status**: Accepted

### Context

We need to provision 50+ AWS resources (Kinesis, Lambda, DynamoDB, IAM, etc.) with requirements for:
- Version-controlled infrastructure
- Reproducible deployments
- Multi-environment support (dev, prod)
- State management
- Drift detection

### Decision

Use **Terraform** for all infrastructure provisioning.

### Rationale

**Pros**:
1. **Cloud-Agnostic**: Can manage multiple clouds (AWS, Azure, GCP)
2. **Mature Ecosystem**: 3000+ providers, large community
3. **State Management**: Tracks infrastructure state (S3 backend)
4. **Declarative**: Describe desired state, Terraform handles how to get there
5. **Plan Before Apply**: See changes before applying
6. **Modular**: Reusable modules
7. **HCL Language**: Easy to read and write
8. **Import Existing Resources**: Can manage existing infrastructure

**Cons**:
1. **State File**: Need to manage state (S3 + DynamoDB locking)
2. **Learning Curve**: HCL syntax, Terraform concepts
3. **Drift**: Manual changes outside Terraform cause drift

### Consequences

**Positive**:
- All infrastructure is version-controlled (Git)
- Easy to reproduce environments
- Changes are reviewed (PRs)
- Drift can be detected (`terraform plan`)
- Can tear down and rebuild entire environment

**Negative**:
- Need to learn Terraform
- State management adds complexity
- Manual console changes not reflected in code

### Best Practices

1. **Remote State**: Store state in S3 with DynamoDB locking
2. **Workspaces**: Use workspaces for dev/staging/prod
3. **Modules**: Create reusable modules for common patterns
4. **Variables**: Parameterize for different environments
5. **Outputs**: Export values for other tools/scripts
6. **Secrets**: Never commit secrets to Git (use AWS Secrets Manager)
7. **Plan Review**: Always review plan before apply
8. **State Backup**: Enable S3 versioning for state bucket

### Project Structure

```
terraform/
├── main.tf                 # Main configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── backend.tf              # State backend configuration
├── kinesis.tf              # Kinesis resources
├── lambda.tf               # Lambda resources
├── dynamodb.tf             # DynamoDB resources
├── s3.tf                   # S3 resources
├── iam.tf                  # IAM roles and policies
├── step-functions.tf       # Step Functions workflows
├── eventbridge.tf          # EventBridge rules
├── cloudwatch.tf           # CloudWatch dashboards and alarms
├── sns.tf                  # SNS topics
└── modules/                # Reusable modules
    ├── lambda-function/
    ├── kinesis-stream/
    └── dynamodb-table/
```

### Alternatives Considered

#### AWS CloudFormation

**Pros**:
- AWS-native (no third-party dependency)
- Deep AWS integration
- Drift detection

**Cons**:
- AWS-only (vendor lock-in)
- YAML/JSON verbose
- Slower to adopt new AWS features
- Less mature than Terraform

**Why Not Chosen**: Terraform is more flexible and has better community support.

#### AWS CDK (Cloud Development Kit)

**Pros**:
- Write IaC in Python/TypeScript/Java
- Type checking
- Reusable constructs

**Cons**:
- Compiles to CloudFormation (inherits CF limitations)
- Smaller community than Terraform
- Less mature

**Why Not Chosen**: Terraform is more established and cloud-agnostic.

#### Pulumi

**Pros**:
- Write IaC in Python/TypeScript/Go
- Type checking
- State management similar to Terraform

**Cons**:
- Smaller community
- Less mature
- Commercial offering (free tier available)

**Why Not Chosen**: Terraform has larger community and ecosystem.

---

## Summary of Key Decisions

| Decision Area | Choice | Primary Reason |
|--------------|--------|----------------|
| **Event Ingestion** | Kinesis Data Streams | AWS-native, managed, cost-effective |
| **Stream Processing** | Lambda + Kinesis Analytics | Right tool for each job type |
| **State Storage** | DynamoDB | Low latency, serverless, scalable |
| **Workflow Orchestration** | Step Functions | Serverless, visual, AWS-native |
| **Dashboards** | QuickSight | Cost-effective, AWS-native |
| **Infrastructure as Code** | Terraform | Cloud-agnostic, mature, community |

---

## Decision Process

For future architectural decisions, follow this process:

1. **Define Context**: What problem are we solving?
2. **List Requirements**: Functional and non-functional requirements
3. **Research Options**: Evaluate 3-5 alternatives
4. **Create Decision Matrix**: Compare options across key criteria
5. **Prototype** (if uncertain): Build small POC
6. **Document Decision**: Create ADR with rationale
7. **Review**: Get team feedback
8. **Implement**: Build according to decision
9. **Evaluate**: Monitor metrics, revisit if needed

---

**Last Updated**: March 2026

**Contributors**: Data Engineering Team

**Review Cycle**: Quarterly (or when significant changes occur)
