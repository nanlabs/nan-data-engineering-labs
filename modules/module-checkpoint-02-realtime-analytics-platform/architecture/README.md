# Architecture Documentation

This directory contains comprehensive architecture diagrams for the Real-Time Analytics Platform using Mermaid diagram language.

## 📋 Diagram Catalog

### 1. High-Level Architecture (`01-high-level-architecture.mmd`)
**Purpose:** Complete system overview showing all components and their interactions

**Components:**
- Event sources (Mobile Apps, Driver Apps, Payment System, Rating System)
- Ingestion layer (4 Kinesis Data Streams)
- Processing layer (Lambda functions, Kinesis Data Analytics)
- Storage layer (DynamoDB, S3)
- Orchestration (Step Functions, EventBridge)
- Visualization (QuickSight)
- Monitoring (CloudWatch)

**Use Case:** Understanding the complete system design and component relationships

### 2. Streaming Pipeline (`02-streaming-pipeline.mmd`)
**Purpose:** Detailed view of real-time data ingestion and processing pipeline

**Focus Areas:**
- Event producer patterns
- Kinesis stream sharding and partitioning
- Lambda consumers with batching and error handling
- Kinesis Data Analytics transformations
- State management patterns
- Data archival strategies

**Use Case:** Implementing and optimizing streaming data flows

### 3. Lambda Architecture (`03-lambda-architecture.mmd`)
**Purpose:** Implementation of Lambda Architecture pattern for real-time and batch processing

**Layers:**
- **Speed Layer:** Real-time processing with sub-second latency
- **Batch Layer:** Historical data processing with accuracy
- **Serving Layer:** Unified query interface

**Use Case:** Understanding trade-offs between real-time and batch processing

### 4. Data Flow Sequence (`04-data-flow.mmd`)
**Purpose:** Detailed sequence diagram showing event lifecycle and timing

**Flow Steps:**
1. Event creation and validation
2. Ingestion through Kinesis
3. Processing with Lambda
4. State updates in DynamoDB
5. Visualization in QuickSight
6. Error handling and recovery

**Use Case:** Performance optimization and latency analysis

## 🎨 How to View Mermaid Diagrams

### VS Code
1. Install the "Mermaid Preview" extension
2. Open any `.mmd` file
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Type "Mermaid: Preview"

### GitHub
- GitHub automatically renders `.mmd` files when you view them in the repository

### Mermaid Live Editor
1. Visit https://mermaid.live
2. Copy the diagram code
3. Paste into the editor
4. View and export as PNG/SVG

### VS Code Native
- Markdown files with Mermaid code blocks (```mermaid) are rendered automatically in preview mode

### Documentation Sites
- Integrated into MkDocs with `pymdown-extensions`
- GitBook with Mermaid plugin
- Docusaurus with `@docusaurus/theme-mermaid`

## 🏗️ Architecture Patterns Used

### 1. Lambda Architecture
**Description:** Hybrid approach combining batch and stream processing

**Benefits:**
- Handles both real-time and historical data
- Fault-tolerant through immutable data
- Balances latency and accuracy

**Trade-offs:**
- Higher complexity (two processing paths)
- Data synchronization challenges
- Increased operational overhead

**Implementation:**
- Speed Layer: Kinesis → Lambda → DynamoDB
- Batch Layer: S3 → Glue → Athena
- Serving Layer: QuickSight

### 2. Event-Driven Architecture
**Description:** Asynchronous communication through events

**Benefits:**
- Loose coupling between services
- Scalability and elasticity
- Resilience through decoupling

**Components:**
- Event producers (Mobile/Driver apps)
- Event bus (Kinesis Data Streams)
- Event processors (Lambda functions)
- Event store (DynamoDB, S3)

### 3. CQRS (Command Query Responsibility Segregation)
**Description:** Separate read and write models

**Implementation:**
- Write model: Kinesis → Lambda → DynamoDB
- Read model: DynamoDB → QuickSight
- Event sourcing: DynamoDB Streams

**Benefits:**
- Optimized read performance
- Scalable writes
- Audit trail through events

### 4. Stream Processing
**Description:** Continuous processing of data streams

**Patterns:**
- Windowing (tumbling, sliding, session)
- Aggregation (count, sum, avg)
- Join (stream-stream, stream-table)
- Pattern detection (CEP)

**Technologies:**
- Kinesis Data Streams (ingestion)
- Kinesis Data Analytics (transformations)
- Lambda (business logic)

### 5. Fan-Out Pattern
**Description:** Multiple consumers process the same event stream

**Implementation:**
- Single Kinesis stream
- Multiple Lambda consumers
- Each consumer handles different use case

**Benefits:**
- Reuse of event data
- Independent scaling per consumer
- Flexibility in processing logic

## 🎯 Key Design Decisions

### Decision 1: Kinesis Data Streams vs. MSK (Managed Streaming for Kafka)
**Choice:** Kinesis Data Streams

**Rationale:**
- Fully managed with zero operational overhead
- Automatic scaling with on-demand mode
- Native AWS integration (Lambda, Analytics, Firehose)
- Lower complexity for team
- Cost-effective for medium-scale workloads

**Trade-offs:**
- Less flexible than Kafka
- Vendor lock-in to AWS
- Higher cost at very large scale

### Decision 2: DynamoDB vs. RDS Aurora
**Choice:** DynamoDB

**Rationale:**
- Single-digit millisecond latency
- Horizontal scaling to any size
- Pay-per-request pricing
- Built-in replication
- DynamoDB Streams for CDC

**Trade-offs:**
- Limited query flexibility
- Higher cost for read-heavy workloads
- Complex access patterns

### Decision 3: Lambda vs. ECS/Fargate for Processing
**Choice:** Lambda

**Rationale:**
- Event-driven architecture fit
- Automatic scaling (0 to thousands)
- Pay per invocation
- Native Kinesis integration
- Simplified operations

**Trade-offs:**
- 15-minute execution limit
- Cold start latency
- Memory limits (10GB max)

### Decision 4: Kinesis Data Analytics vs. Custom Flink on EMR
**Choice:** Kinesis Data Analytics

**Rationale:**
- Fully managed Flink runtime
- Simplified deployment and scaling
- Integrated with Kinesis and S3
- Lower operational complexity

**Trade-offs:**
- Less customization
- Higher cost than self-managed
- Limited Flink version control

### Decision 5: Step Functions vs. Apache Airflow
**Choice:** Step Functions for orchestration

**Rationale:**
- Serverless (no infrastructure)
- Native AWS service integration
- Visual workflow designer
- Pay per state transition

**Trade-offs:**
- Less flexible than Airflow
- Limited scheduling options
- Simpler for AWS-centric workflows

### Decision 6: S3 Partitioning Strategy
**Choice:** Date-based partitioning `year=YYYY/month=MM/day=DD/hour=HH`

**Rationale:**
- Optimizes Athena query performance
- Partition pruning reduces scan costs
- Time-based queries are most common
- Easy to implement retention policies

**Implementation:**
```
s3://bucket/rides/year=2026/month=03/day=09/hour=14/file.parquet
s3://bucket/locations/year=2026/month=03/day=09/hour=14/file.parquet
```

### Decision 7: Hot vs. Cold Storage Strategy
**Choice:** DynamoDB (hot 7 days) + S3 (cold archive)

**Rationale:**
- Recent data needs low latency
- Historical data queried via Athena
- Cost optimization (DynamoDB expensive at scale)
- Compliance and audit requirements

**Lifecycle:**
1. Events → Kinesis → Lambda → DynamoDB
2. DynamoDB TTL expires after 7 days
3. DynamoDB Streams → Lambda → S3
4. S3 lifecycle policy: Standard → Glacier

## 📊 Performance Considerations

### Latency Targets
- End-to-end event processing: < 1 second (p99)
- Lambda processing time: < 500ms (p95)
- DynamoDB write latency: < 10ms (p99)
- QuickSight dashboard refresh: < 5 seconds

### Throughput Targets
- Total events per second: 50,000
- Rides stream: 20,000 events/sec
- Locations stream: 25,000 events/sec
- Payments stream: 3,000 events/sec
- Ratings stream: 2,000 events/sec

### Scalability
- Kinesis shards: Auto-scaling based on throughput
- Lambda concurrency: Reserved concurrency per function
- DynamoDB: On-demand capacity mode
- S3: Unlimited scalability

## 🔐 Security Considerations

### Encryption
- Kinesis: Server-side encryption with KMS
- DynamoDB: Encryption at rest with KMS
- S3: Server-side encryption (SSE-KMS)
- Lambda environment variables: Encrypted

### Access Control
- IAM roles with least privilege
- Service-to-service authentication
- VPC endpoints for private connectivity
- Resource-based policies

### Monitoring
- CloudWatch Logs for audit trails
- CloudTrail for API calls
- GuardDuty for threat detection
- Security Hub for compliance

## 📚 References

### AWS Documentation
- [Kinesis Data Streams Developer Guide](https://docs.aws.amazon.com/streams/)
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [Kinesis Data Analytics Developer Guide](https://docs.aws.amazon.com/kinesisanalytics/)

### Best Practices
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Streaming Data Solutions on AWS](https://aws.amazon.com/streaming-data/)
- [Lambda Architecture Pattern](http://lambda-architecture.net/)

### Tools
- [Mermaid Documentation](https://mermaid-js.github.io/mermaid/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
