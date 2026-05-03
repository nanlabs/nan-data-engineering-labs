# 🏛️ ARCHITECTURE DECISIONS

## Document Control

| Attribute | Value |
|-----------|-------|
| **Project** | CloudMart Serverless Data Lake |
| **Version** | 1.0 |
| **Last Updated** | March 2026 |
| **Document Type** | Architecture Decision Records (ADR) |
| **Status** | Active |

---

## Table of Contents

1. [Introduction](#introduction)
2. [ADR-001: Why Serverless Architecture?](#adr-001-why-serverless-architecture)
3. [ADR-002: Why Amazon S3 for Data Lake Storage?](#adr-002-why-amazon-s3-for-data-lake-storage)
4. [ADR-003: Why AWS Glue for ETL?](#adr-003-why-aws-glue-for-etl)
5. [ADR-004: Why Amazon Athena for Analytics?](#adr-004-why-amazon-athena-for-analytics)
6. [ADR-005: Data Partitioning Strategy](#adr-005-data-partitioning-strategy)
7. [ADR-006: File Format Selection (Parquet vs JSON/CSV)](#adr-006-file-format-selection-parquet-vs-jsoncsv)
8. [ADR-007: Lambda vs Step Functions for Orchestration](#adr-007-lambda-vs-step-functions-for-orchestration)
9. [ADR-008: Error Handling and Retry Strategy](#adr-008-error-handling-and-retry-strategy)
10. [ADR-009: Medallion Architecture (Bronze/Silver/Gold)](#adr-009-medallion-architecture-bronzesilvergold)
11. [ADR-010: CloudFormation vs Terraform](#adr-010-cloudformation-vs-terraform)
12. [Summary of Key Decisions](#summary-of-key-decisions)

---

## Introduction

### Purpose of This Document

Architecture Decision Records (ADRs) document important architectural decisions made during the design and implementation of the CloudMart Serverless Data Lake. Each ADR captures:

- **Context:** The situation and problem we're addressing
- **Decision:** The choice we made
- **Rationale:** Why we made this choice
- **Alternatives Considered:** Other options we evaluated
- **Consequences:** Positive and negative implications
- **Trade-offs:** What we gained and what we sacrificed

### Why ADRs Matter

1. **Knowledge Preservation:** Future team members (or your future self) understand why decisions were made
2. **Accountability:** Decisions are transparent and justified
3. **Learning:** Documenting trade-offs helps improve future decision-making
4. **Communication:** Stakeholders understand the technical reasoning
5. **Evolution:** Decisions can be revisited when context changes

### ADR Format

We follow a lightweight ADR template:

```
## ADR-XXX: [Decision Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Date:** [YYYY-MM-DD]
**Decision Makers:** [Who was involved]
**Tags:** [Relevant keywords]

### Context
[What is the situation? What problem are we solving?]

### Decision
[What did we decide?]

### Rationale
[Why this decision?]

### Alternatives Considered
[What other options did we evaluate?]

### Consequences
**Positive:**
- [Benefits]

**Negative:**
- [Costs/Limitations]

### Trade-offs
[What we gained vs. what we sacrificed]

### Related Decisions
[Links to related ADRs]

### Implementation Notes
[Key considerations for implementation]
```

---

## ADR-001: Why Serverless Architecture?

**Status:** Accepted
**Date:** 2026-03-01
**Decision Makers:** Data Engineering Team, CDO, VP Engineering
**Tags:** #architecture #serverless #cost-optimization #scalability

### Context

CloudMart needs a data lake solution that:
- Handles variable workloads (batch processing, ad-hoc queries)
- Minimizes operational overhead (no dedicated data engineering team)
- Scales automatically with business growth
- Keeps costs low for MVP phase (<$50/month)
- Enables rapid development and iteration

**Traditional alternatives:**
- **EC2-based:** Spark cluster on EC2 instances
- **EMR:** Managed Hadoop/Spark cluster
- **Hybrid:** Combination of managed and self-hosted services

### Decision

**We will adopt a serverless-first architecture using AWS Lambda, Glue, Athena, and S3.**

### Rationale

1. **No Infrastructure Management**
   - No servers to provision, patch, or scale
   - Focus on business logic, not operations
   - Perfect for a learning environment and small teams

2. **Cost Efficiency**
   - Pay only for actual compute time
   - No idle resources (EC2 would run 24/7)
   - Free Tier covers significant usage
   - Estimated $30-50/month vs. $500+/month for EC2

3. **Automatic Scaling**
   - Lambda scales automatically to handle load
   - Athena scales query processing dynamically
   - No capacity planning needed

4. **Fast Time-to-Value**
   - No cluster setup or configuration
   - Deploy functions and start processing immediately
   - Iterate quickly without infrastructure changes

5. **Built-in High Availability**
   - AWS manages redundancy and failover
   - 99.9%+ uptime SLA
   - No need to design HA architecture

### Alternatives Considered

#### Alternative 1: Apache Spark on EC2

**Pros:**
- Full control over environment
- Can fine-tune performance
- More flexible for complex transformations

**Cons:**
- Requires 24/7 running instances ($500+/month minimum)
- Complex setup and configuration
- Need expertise in cluster management
- Manual scaling and monitoring
- Higher operational burden

**Cost Comparison:**
- 3 x m5.xlarge instances (modest cluster): $500/month
- Plus: EBS storage, data transfer, ops time
- **Total: $600-800/month minimum**

#### Alternative 2: Amazon EMR

**Pros:**
- Managed Hadoop/Spark
- Good for very large-scale processing
- Familiar Spark API

**Cons:**
- Still requires cluster management
- Minimum cluster size = $300+/month
- Overkill for our data volume (110GB/month)
- Longer startup time for clusters
- More complex than needed

**Cost Comparison:**
- Minimum viable EMR cluster: $300-400/month
- Spot instances can reduce cost, but add complexity
- **Total: $300-500/month**

#### Alternative 3: Hybrid (Lambda + Self-hosted Spark)

**Pros:**
- Use Lambda for simple tasks, Spark for complex
- Optimize costs per workload

**Cons:**
- Complexity of managing two systems
- More code to maintain (different runtimes)
- Harder to debug cross-system issues
- Not beginner-friendly

### Consequences

**Positive:**
- ✅ **Low Cost:** $30-50/month vs. $500+/month
- ✅ **Zero Ops:** No servers to manage
- ✅ **Auto-scaling:** Handles growth automatically
- ✅ **Fast Development:** Deploy and iterate quickly
- ✅ **High Availability:** Built-in redundancy
- ✅ **Learning-Friendly:** Clear service boundaries, easier to understand

**Negative:**
- ❌ **Execution Limits:** Lambda 15-minute timeout, 10GB memory limit
- ❌ **Cold Starts:** Lambda functions may experience latency on first invocation
- ❌ **Vendor Lock-in:** Harder to migrate to another cloud provider
- ❌ **Less Control:** Can't SSH into servers or fine-tune OS
- ❌ **Debugging:** Distributed serverless debugging is harder than single-server

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **Cost savings (90%)** | **Fine-grained performance tuning** |
| **Zero operational overhead** | **Full control over environment** |
| **Automatic scaling** | **Long-running jobs (>15 min Lambda)** |
| **Fast time-to-value** | **Portability to other clouds** |
| **Built-in HA** | **Debugging flexibility** |

### Implementation Notes

1. **Design for Lambda Limits:**
   - Break large jobs into smaller functions
   - Use Glue for jobs >15 minutes
   - Optimize memory allocation to reduce costs

2. **Mitigate Cold Starts:**
   - Use provisioned concurrency for critical functions (adds cost)
   - Keep functions warm with scheduled pings (if needed)
   - Accept 1-2 second cold start for non-critical paths

3. **Handle Vendor Lock-in:**
   - Abstract AWS-specific code into modules
   - Document all AWS service dependencies
   - Use standard formats (Parquet, JSON) for data portability

### Related Decisions

- ADR-003: Why AWS Glue for ETL (complements serverless architecture)
- ADR-007: Lambda vs Step Functions (orchestration within serverless paradigm)

---

## ADR-002: Why Amazon S3 for Data Lake Storage?

**Status:** Accepted
**Date:** 2026-03-01
**Decision Makers:** Data Engineering Team
**Tags:** #storage #s3 #data-lake #cost

### Context

We need a storage solution for our data lake that:
- Stores structured and semi-structured data (CSV, JSON, Parquet)
- Scales from GB to TB and beyond
- Integrates with analytics tools (Athena, Glue)
- Provides durability and availability guarantees
- Keeps storage costs low

**Alternatives:**
- HDFS on EC2
- Amazon EFS
- Amazon RDS with large storage
- DynamoDB

### Decision

**We will use Amazon S3 as the primary storage layer for all data lake zones (Raw, Processed, Curated).**

### Rationale

1. **Cost-Effective Storage**
   - $0.023/GB/month (Standard tier)
   - $0.0125/GB/month (Standard-IA for older data)
   - Much cheaper than EBS ($0.10/GB/month)
   - Intelligent-Tiering auto-optimizes costs

2. **Unlimited Scalability**
   - No capacity planning needed
   - Scales from GB to EB seamlessly
   - No performance degradation with size

3. **Durability and Availability**
   - 99.999999999% (11 nines) durability
   - 99.99% availability SLA
   - Built-in redundancy across multiple AZs
   - Versioning for data protection

4. **Native Integration**
   - Athena queries S3 directly (no data movement)
   - Glue Crawlers understand S3 structure
   - Lambda triggers on S3 events
   - Lifecycle policies for automatic archival

5. **Data Lake Standard**
   - Industry-standard for cloud data lakes
   - Mature ecosystem and tooling
   - Extensive documentation and community support

### Alternatives Considered

#### Alternative 1: HDFS on EC2

**Pros:**
- Traditional big data storage
- Good for Hadoop ecosystem
- Fine-grained control

**Cons:**
- Requires always-on EC2 cluster
- Complex setup and maintenance
- Manual replication for durability
- $500+/month for small cluster
- Not serverless

**Cost:** ~$600/month for 1TB

#### Alternative 2: Amazon EFS

**Pros:**
- Shared file system
- POSIX compliance
- Easy mounting from EC2/Lambda

**Cons:**
- More expensive ($0.30/GB/month)
- Designed for file sharing, not object storage
- No direct Athena integration
- Overkill for our use case

**Cost:** ~$300/month for 1TB

#### Alternative 3: Amazon RDS (PostgreSQL)

**Pros:**
- Structured database
- ACID transactions
- SQL interface

**Cons:**
- Expensive for large data ($115/month for 100GB + instance)
- Not designed for analytics workloads
- Fixed capacity (must provision)
- Performance degrades with data growth
- Difficult to scale to TB-scale

**Cost:** ~$500/month for modest instance + storage

### Consequences

**Positive:**
- ✅ **Lowest Cost:** $23/month for 1TB vs. $300-600/month alternatives
- ✅ **No Limits:** Unlimited scalability
- ✅ **No Ops:** Fully managed, no maintenance
- ✅ **Perfect Athena Integration:** Query in place, no ETL to database
- ✅ **Event-Driven:** Trigger Lambda on object creation
- ✅ **Ecosystem:** Works with all AWS analytics services

**Negative:**
- ❌ **Eventual Consistency:** Cross-region replication has slight delays (not an issue for batch processing)
- ❌ **List Operations:** Listing large prefixes can be slow (mitigated by partitioning)
- ❌ **No Transactions:** Can't do ACID operations (not needed for data lake)

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **90% cost savings** | **ACID transactions** |
| **Infinite scale** | **Low-latency random access** |
| **Zero management** | **POSIX file system semantics** |
| **11-nines durability** | **Strong consistency (cross-region)** |

### Implementation Notes

1. **Bucket Organization:**
   ```
   cloudmart-raw/          # Bronze layer
   cloudmart-processed/    # Silver layer
   cloudmart-curated/      # Gold layer
   cloudmart-scripts/      # ETL scripts
   cloudmart-logs/         # Application logs
   cloudmart-athena-results/ # Athena query results
   ```

2. **Storage Class Strategy:**
   - Standard: Recent data (last 30 days)
   - Standard-IA: Historical data (30-90 days)
   - Glacier: Long-term archive (>90 days)
   - Use Lifecycle policies to automate transitions

3. **Partitioning Best Practices:**
   - Partition by date for time-series data
   - Use Hive-style partitions: `year=2026/month=03/day=09/`
   - Keep partition size 100MB-1GB for optimal query performance

4. **Security:**
   - Enable default encryption (SSE-S3 or SSE-KMS)
   - Use bucket policies to restrict access
   - Enable versioning for critical buckets
   - Enable access logging for auditing

### Related Decisions

- ADR-005: Data Partitioning Strategy (how we organize data in S3)
- ADR-006: File Format Selection (what formats we use on S3)

---

## ADR-003: Why AWS Glue for ETL?

**Status:** Accepted
**Date:** 2026-03-02
**Decision Makers:** Data Engineering Team
**Tags:** #etl #glue #spark #serverless

### Context

We need an ETL solution to transform data through Bronze → Silver → Gold layers. Requirements:
- Support PySpark for complex transformations
- Serverless (no cluster management)
- Integrate with S3 and Data Catalog
- Cost-effective for our workload size
- Easy to develop and debug

**Alternatives:**
- AWS Lambda (for simpler transformations)
- AWS EMR (managed Spark)
- Apache Airflow + Spark on EC2
- AWS Step Functions + Lambda

### Decision

**We will use AWS Glue for all ETL jobs (Bronze→Silver and Silver→Gold transformations).**

### Rationale

1. **Serverless Spark**
   - No cluster to manage
   - Automatic scaling
   - Pay per job execution (~$0.44/DPU-hour)

2. **Native PySpark Support**
   - Full PySpark API
   - Familiar for data engineers
   - Powerful for complex transformations

3. **Glue Data Catalog Integration**
   - Reads metadata automatically
   - No need to define schemas manually
   - Schema evolution handled

4. **Built-in Features**
   - Job bookmarks (incremental processing)
   - DynamicFrame (schema flexibility)
   - Built-in connectors for S3, RDS, etc.

5. **Development Tools**
   - Glue Studio for visual ETL
   - Glue notebooks for interactive development
   - Local testing with Glue Docker image

### Alternatives Considered

#### Alternative 1: AWS Lambda

**Pros:**
- Serverless and low-cost
- Fast startup (no cluster spin-up)
- Simple deployment

**Cons:**
- 15-minute timeout
- 10GB memory limit
- Not designed for large-scale transformations
- No built-in Spark support
- Harder to process >1GB files

**Best for:** Simple transformations, event-driven tasks

**Decision:** Use Lambda for ingestion, Glue for transformations

#### Alternative 2: Amazon EMR

**Pros:**
- Full Hadoop/Spark ecosystem
- More control over cluster configuration
- Can use Spot instances for cost savings

**Cons:**
- Requires cluster management
- Requires cluster management
- Minimum cost $300/month for always-on cluster
- Overkill for our data volume
- Longer development cycle

**Cost Comparison:**
- EMR: $300-500/month minimum
- Glue: ~$20-30/month for our workload

#### Alternative 3: Apache Airflow + Spark on EC2

**Pros:**
- Full control and flexibility
- Open-source (no vendor lock-in)
- Airflow for orchestration

**Cons:**
- Complex setup and maintenance
- Need to manage Spark cluster
- Airflow requires constant monitoring
- High operational overhead
- $500+/month in infrastructure

### Consequences

**Positive:**
- ✅ **No Cluster Management:** Fully serverless
- ✅ **PySpark Power:** Complex transformations easy
- ✅ **Cost-Efficient:** ~$20-30/month for our workload
- ✅ **Data Catalog Integration:** Automatic schema discovery
- ✅ **Job Bookmarks:** Incremental processing without extra code
- ✅ **Auto-scaling:** Handles data volume growth

**Negative:**
- ❌ **Startup Time:** Jobs take 2-3 minutes to start (cold start)
- ❌ **Limited Customization:** Can't install custom OS packages easily
- ❌ **Glue Version Lag:** Spark version may be behind latest
- ❌ **Debugging:** Harder than local Spark cluster

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **Zero ops** | **Fast job startup** |
| **Auto-scaling** | **Full Spark ecosystem** |
| **Cost savings** | **Fine-grained tuning** |
| **Built-in features** | **Latest Spark version** |

### Implementation Notes

1. **Glue Job Configuration:**
   ```python
   --job-language python
   --glue_version 4.0
   --worker-type G.1X  # 1 DPU (4 vCPU, 16GB RAM)
   --number-of-workers 2  # Start small, scale as needed
   --enable-job-insights true
   --enable-continuous-cloudwatch-log true
   --enable-metrics true
   ```

2. **Job Bookmarks:**
   - Enable for incremental processing
   - Tracks processed files in S3
   - Avoids reprocessing data

3. **DynamicFrames vs DataFrames:**
   - Use DynamicFrame for schema flexibility
   - Convert to DataFrame for complex Spark operations
   - Convert back to DynamicFrame for Glue writes

4. **Cost Optimization:**
   - Use appropriate worker type (G.1X for most jobs)
   - Set job timeout to prevent runaway costs
   - Monitor job metrics to right-size workers

### Related Decisions

- ADR-001: Serverless Architecture (Glue fits serverless paradigm)
- ADR-007: Lambda vs Step Functions (Glue handles transformations, not Lambda)

---

## ADR-004: Why Amazon Athena for Analytics?

**Status:** Accepted
**Date:** 2026-03-02
**Decision Makers:** Data Engineering Team, Head of BI
**Tags:** #analytics #athena #sql #query-engine

### Context

Business users need to query data using SQL. Requirements:
- SQL interface (familiar to business analysts)
- Query data without loading into a database
- Support ad-hoc and scheduled queries
- Low cost for MVP phase
- No infrastructure to manage

**Alternatives:**
- Amazon Redshift (data warehouse)
- Amazon RDS (relational database)
- Presto on EMR
- dbt + Snowflake

### Decision

**We will use Amazon Athena as the primary query engine for the data lake.**

### Rationale

1. **Query-in-Place**
   - No need to load data into a database
   - Queries S3 data directly
   - Parquet files enable columnar queries

2. **Pay-Per-Query**
   - $5 per TB scanned
   - No idle costs (unlike Redshift)
   - Typical query: <10GB scanned = $0.05
   - Perfect for variable workloads

3. **Standard SQL**
   - ANSI SQL compatible
   - Business analysts already know SQL
   - Supports JOINs, window functions, CTEs
   - No new language to learn

4. **Serverless**
   - No servers to provision
   - Auto-scales for concurrent queries
   - Zero management overhead

5. **Glue Catalog Integration**
   - Uses Glue Catalog as metastore
   - Schemas already available
   - Partition-aware queries

6. **BI Tool Integration**
   - JDBC/ODBC drivers
   - Works with Tableau, Power BI, Looker
   - QuickSight native integration

### Alternatives Considered

#### Alternative 1: Amazon Redshift

**Pros:**
- Purpose-built for analytics
- Fast for complex queries
- Mature data warehouse
- Many BI tool integrations

**Cons:**
- Requires always-on cluster ($180/month minimum)
- Must load data (ETL into Redshift)
- Adds complexity (another data store)
- Overkill for our data volume (110GB/month)
- Fixed capacity (must provision)

**Cost Comparison:**
- Redshift: $180/month (dc2.large) + storage
- Athena: ~$5-10/month for expected query volume
- **Athena is 95% cheaper**

#### Alternative 2: Amazon RDS (PostgreSQL)

**Pros:**
- Familiar SQL database
- ACID transactions
- Good for operational analytics

**Cons:**
- Not designed for large analytical queries
- Must load data (ETL required)
- Expensive for TB-scale ($500+/month)
- Performance degrades with data size
- Requires optimization (indexes, vacuuming)

#### Alternative 3: Presto on EMR

**Pros:**
- Open-source query engine
- No vendor lock-in
- Fast distributed queries

**Cons:**
- Requires EMR cluster ($300/month minimum)
- Must manage cluster (patching, monitoring)
- Higher operational complexity
- Not cost-effective for our scale

### Consequences

**Positive:**
- ✅ **Lowest Cost:** $5-10/month vs. $180+/month alternatives
- ✅ **No ETL to Database:** Query S3 directly
- ✅ **Zero Ops:** Fully managed
- ✅ **Pure SQL:** No new language
- ✅ **Auto-scaling:** Supports 50+ concurrent users
- ✅ **BI Integration:** Works with all major tools

**Negative:**
- ❌ **Query Performance:** Slower than Redshift for very complex queries
- ❌ **No Indexes:** Must rely on partitioning for performance
- ❌ **Pay Per Scan:** Poorly optimized queries can be expensive
- ❌ **Cold Start:** First query on data may be slower

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **95% cost savings** | **Sub-second query latency** |
| **Query-in-place** | **Indexes and materialized views** |
| **Zero ops** | **Query result caching (limited)** |
| **Pay-per-query** | **Warm query performance** |

### Implementation Notes

1. **Query Optimization:**
   - Partition pruning: Always filter by partition columns
   - Columnar format: Use Parquet for selective column reads
   - Predicate pushdown: Filter early in query
   - Avoid SELECT * (specify columns)

2. **Cost Control:**
   - Set query timeout limits
   - Educate users on query costs
   - Use views to encapsulate best practices
   - Monitor query patterns with CloudWatch

3. **Workgroup Configuration:**
   ```yaml
   Workgroup: cloudmart-analytics
   OutputLocation: s3://cloudmart-athena-results/
   EncryptQueryResults: true
   EnforceWorkgroupConfiguration: true
   BytesScannedCutoffPerQuery: 10 GB  # Alert if query scans >10GB
   ```

4. **Performance Best Practices:**
   - Partition by date (year/month/day)
   - Use Parquet with Snappy compression
   - Pre-aggregate data in Gold layer
   - Create views for common queries

### Related Decisions

- ADR-002: S3 for Storage (Athena queries S3)
- ADR-005: Partitioning Strategy (critical for Athena performance)
- ADR-006: File Formats (Parquet optimizes Athena queries)

---

## ADR-005: Data Partitioning Strategy

**Status:** Accepted
**Date:** 2026-03-03
**Decision Makers:** Data Engineering Team
**Tags:** #partitioning #performance #s3 #athena

### Context

Data partitioning significantly impacts query performance and cost. We need a partitioning strategy that:
- Optimizes Athena query performance (partition pruning)
- Keeps partition sizes reasonable (100MB-1GB)
- Aligns with common query patterns
- Balances granularity with manageability

**Common partition strategies:**
- By date (year/month/day)
- By customer segment
- By product category
- By geographic region
- No partitioning

### Decision

**We will partition data by date (year/month/day) using Hive-style partitioning for all time-series data.**

**Format:** `year=YYYY/month=MM/day=DD/`

### Rationale

1. **Matches Query Patterns**
   - Most queries filter by date range
   - "Last 7 days", "This month", "Last quarter"
   - Partition pruning eliminates 90%+ of data

2. **Hive-Style Compatibility**
   - Standard format: `column=value/`
   - Glue Crawlers recognize automatically
   - Athena understands natively

3. **Balanced Granularity**
   - Daily partitions: manageable count (~365/year)
   - Not too fine (avoid thousands of partitions)
   - Not too coarse (avoid multi-GB partitions)

4. **Incremental Processing**
   - Easy to process "today's data" only
   - Glue job bookmarks work well
   - Clear data boundaries

### Alternatives Considered

#### Alternative 1: No Partitioning

**Pros:**
- Simpler data organization
- No partition maintenance

**Cons:**
- Every query scans all data = high cost
- Poor performance for large datasets
- Not scalable

**Example:**
- Query last 7 days: Scans 2 years of data (100x overhead)
- Cost: $5 per TB scanned (wasteful)

#### Alternative 2: Fine-Grained (Hourly)

**Pros:**
- More precise pruning
- Smaller partition sizes

**Cons:**
- Too many partitions (8,760/year)
- Glue Crawler slowdown
- List operations become expensive
- Diminishing returns for our data volume

#### Alternative 3: Coarse-Grained (Monthly)

**Pros:**
- Fewer partitions (12/year)
- Simple management

**Cons:**
- Partition sizes too large (multi-GB)
- Less effective pruning
- Queries still scan significant data

#### Alternative 4: Multi-Dimensional (Date + Category)

**Format:** `year=2026/month=03/category=electronics/`

**Pros:**
- Very precise pruning
- Optimizes queries with multiple dimensions

**Cons:**
- Explodes partition count (365 * 50 categories = 18K/year)
- Complex to manage
- Most queries don't filter by both dimensions
- Overkill for our data volume

### Consequences

**Positive:**
- ✅ **90%+ Query Cost Reduction:** Partition pruning avoids scanning unnecessary data
- ✅ **10x Query Performance:** Athena processes only relevant partitions
- ✅ **Incremental Processing:** ETL jobs process today's partition only
- ✅ **Easy Maintenance:** Clear data organization
- ✅ **Standard Format:** Works with all AWS tools

**Negative:**
- ❌ **Partition Management:** Need to ensure partitions are registered
- ❌ **Small Files:** Low-volume days create small files (mitigate with compaction)
- ❌ **Not Optimal for All Queries:** Queries without date filter still scan all partitions

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **90% cost reduction** | **Optimal for any query pattern** |
| **10x faster queries** | **Simplicity of flat structure** |
| **Incremental processing** | **Small-file problem** |

### Implementation Notes

1. **Partition Structure:**

   **Orders:**
   ```
   s3://cloudmart-processed/orders/
   └── year=2026/
       └── month=03/
           └── day=09/
               └── orders.parquet
   ```

   **Clickstream:**
   ```
   s3://cloudmart-raw/clickstream/
   └── year=2026/
       └── month=03/
           └── day=09/
               └── hour=14/  # Additional hour partition for high-volume data
                   └── events_14.json.gz
   ```

2. **Partition Registration:**
   - Glue Crawlers auto-discover partitions
   - Or use `MSCK REPAIR TABLE` in Athena
   - Or use `ALTER TABLE ADD PARTITION` manually

3. **Query Example (with partition pruning):**
   ```sql
   SELECT
       order_date,
       SUM(total_amount) AS daily_revenue
   FROM cloudmart_processed.orders
   WHERE year = '2026'
     AND month = '03'
     AND day IN ('07', '08', '09')  -- Last 3 days
   GROUP BY order_date;
   ```
   **Result:** Scans only 3 partitions instead of all data

4. **Avoiding Small Files:**
   - Monitor average file size per partition
   - If <10MB, run periodic compaction job
   - Glue job to merge small files into larger ones

5. **Future Enhancements:**
   - Implement Z-ordering within partitions (Databricks/Delta Lake feature)
   - Add secondary partition (e.g., customer_segment) if query patterns evolve

### Related Decisions

- ADR-002: S3 for Storage (partitioning is S3 directory structure)
- ADR-004: Athena for Analytics (partitioning optimizes Athena)

---

## ADR-006: File Format Selection (Parquet vs JSON/CSV)

**Status:** Accepted
**Date:** 2026-03-03
**Decision Makers:** Data Engineering Team
**Tags:** #file-formats #parquet #performance #cost

### Context

File format choice impacts storage cost, query performance, and compatibility. We need a strategy for:
- Raw (Bronze) zone: Original data format
- Processed (Silver) zone: Optimized for querying
- Curated (Gold) zone: Highly optimized aggregates

**Format options:**
- CSV: Human-readable, widely compatible
- JSON: Flexible schema, nested data
- Parquet: Columnar, compressed, optimized for analytics
- Avro: Row-based, schema evolution
- ORC: Similar to Parquet (mainly for Hive)

### Decision

**Zone-specific format strategy:**

1. **Raw (Bronze) Zone:** Keep original format (JSON, CSV, etc.)
2. **Processed (Silver) Zone:** Convert to Parquet
3. **Curated (Gold) Zone:** Store as Parquet

### Rationale

#### Raw Zone: Original Formats

**Why keep original:**
- Preserve data fidelity (immutable landing zone)
- Support diverse data sources
- No transformation latency at ingestion
- Easy troubleshooting (human-readable)

#### Processed & Curated Zones: Parquet

**Why Parquet:**

1. **Columnar Storage**
   - Query only needed columns (not entire row)
   - Example: `SELECT revenue FROM orders` reads only `revenue` column
   - Athena cost: Pay only for columns scanned

2. **Efficient Compression**
   - 3-5x compression ratio vs. CSV
   - Snappy compression: Fast and effective
   - Storage savings: JSON 100MB → Parquet 25MB

3. **Predicate Pushdown**
   - Filter data at file level (min/max statistics)
   - Skip files that don't match WHERE clause
   - Faster queries, lower costs

4. **Schema Embedded**
   - Schema stored in file metadata
   - No external schema definition needed
   - Self-describing files

5. **Type-Safe**
   - Strong typing (INT, BIGINT, TIMESTAMP, etc.)
   - No parsing errors like CSV
   - Better data integrity

6. **Athena Optimization**
   - Athena is optimized for Parquet
   - 10x faster than JSON for same query
   - Lower costs due to less data scanned

### Alternatives Considered

#### Alternative 1: CSV for All Zones

**Pros:**
- Simple, human-readable
- Easy to inspect and debug
- Universal compatibility

**Cons:**
- No compression (1GB stays 1GB)
- Row-based (must read entire row)
- No predicate pushdown
- Type inference issues
- Expensive to query (scan all data)

**Cost Example:**
- Athena cost to scan 1TB CSV: $5
- Athena cost to scan 1TB Parquet (columnar, only 3 columns): $0.15
- **Parquet is 30x cheaper**

#### Alternative 2: JSON for All Zones

**Pros:**
- Flexible schema
- Nested structures
- Human-readable

**Cons:**
- Inefficient storage (verbose syntax)
- Slow parsing
- No compression benefit
- Not optimized for Athena

**Performance:**
- JSON query: 10 seconds, scans 500MB
- Parquet query: 1 second, scans 50MB
- **Parquet is 10x faster**

#### Alternative 3: Avro

**Pros:**
- Row-based format
- Good for schema evolution
- Efficient serialization

**Cons:**
- Row-based (not columnar)
- Less compression than Parquet
- Fewer tools support (compared to Parquet)
- Not ideal for analytics (better for streaming)

**Use Case:** Better for Kafka/streaming, not analytical queries

#### Alternative 4: ORC (Optimized Row Columnar)

**Pros:**
- Columnar like Parquet
- Optimized for Hive
- Similar compression

**Cons:**
- Less ecosystem support outside Hadoop
- Athena supports but optimized for Parquet
- Smaller community

**Decision:** Parquet is more standard on AWS

### Consequences

**Positive:**
- ✅ **3-5x Storage Savings:** Parquet compression reduces costs
- ✅ **10x Query Performance:** Columnar format + pruning
- ✅ **30x Query Cost Reduction:** Pay only for columns scanned
- ✅ **Schema Evolution:** Parquet handles new columns
- ✅ **Data Integrity:** Strong typing prevents errors

**Negative:**
- ❌ **Not Human-Readable:** Can't inspect with `cat` (use `parquet-tools`)
- ❌ **Conversion Overhead:** Must convert from JSON/CSV to Parquet
- ❌ **Debugging:** Harder to debug Parquet files

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **30x cheaper queries** | **Human readability** |
| **10x faster queries** | **Simplicity** |
| **3x less storage** | **Zero transformation** |
| **Type safety** | **Easy debugging** |

### Implementation Notes

1. **Conversion in Glue ETL:**
   ```python
   # Read JSON from Bronze
   df = spark.read.json("s3://cloudmart-raw/orders/year=2026/month=03/day=09/")

   # Write Parquet to Silver
   df.write.mode("overwrite") \
       .partitionBy("year", "month", "day") \
       .parquet("s3://cloudmart-processed/orders/")
   ```

2. **Parquet Configuration:**
   ```python
   # Compression: Snappy (fast) or GZIP (smaller)
   spark.conf.set("spark.sql.parquet.compression.codec", "snappy")

   # Row group size (default 128MB is good)
   spark.conf.set("parquet.block.size", 134217728)
   ```

3. **Inspect Parquet Files:**
   ```bash
   # Install parquet-tools
   pip install parquet-tools

   # View schema
   parquet-tools schema myfile.parquet

   # View data
   parquet-tools head myfile.parquet
   ```

4. **File Size Best Practices:**
   - Target 100MB-1GB per file
   - Use `coalesce()` or `repartition()` to rightswell files sizes
   - Monitor with CloudWatch metrics

### Related Decisions

- ADR-004: Athena for Analytics (Parquet optimizes Athena)
- ADR-005: Partitioning Strategy (complements columnar format)

---

## ADR-007: Lambda vs Step Functions for Orchestration

**Status:** Accepted
**Date:** 2026-03-04
**Decision Makers:** Data Engineering Team
**Tags:** #orchestration #lambda #step-functions #workflow

### Context

We need orchestration for multi-step workflows, particularly:
- Ingestion: Validate → Transform → Route
- ETL: Bronze → Silver → Gold (sequential)
- Error handling and retries

**Options:**
- AWS Lambda with event-driven triggers
- AWS Step Functions (state machine orchestration)
- Apache Airflow (external orchestrator)
- AWS Glue Workflows

### Decision

**For MVP, use event-driven Lambda functions with S3 triggers. No explicit orchestration layer.**

**Future: Consider Step Functions if workflows become more complex.**

### Rationale

1. **Simplicity**
   - Event-driven: S3 upload triggers Lambda automatically
   - No state machine to define
   - Fewer moving parts = easier to understand

2. **Cost**
   - Lambda: Free Tier + $0.20 per 1M invocations
   - Step Functions: $25 per 1M state transitions
   - For our volume (1,000 files/day), Lambda is cheaper

3. **Fast Development**
   - Lambda functions are independent
   - No workflow DSL to learn (Step Functions JSON)
   - Easy to test individual functions

4. **Event-Driven Pattern**
   - S3 → Lambda (ingestion)
   - Lambda → S3 → Glue (transformation)
   - Glue → S3 → Athena (analytics)
   - Natural data flow

5. **Glue Handles Heavy Lifting**
   - Complex transformations in Glue (not Lambda)
   - Lambda only for lightweight tasks
   - Step Functions less necessary

### Alternatives Considered

#### Alternative 1: AWS Step Functions

**Pros:**
- Visual workflow editor
- Built-in error handling and retries
- Parallel execution
- Workflow history and monitoring

**Cons:**
- More complex to set up
- $25 per 1M transitions (vs. $0.20 Lambda)
- Overkill for simple event-driven flow
- Another service to learn

**When to Use:**
- Complex multi-step workflows
- Long-running orchestrations (>15 minutes)
- Human approval steps
- Dynamic parallel execution

**Decision:** Revisit when workflows become complex

#### Alternative 2: Apache Airflow (MWAA)

**Pros:**
- Powerful DAG-based orchestration
- Rich ecosystem of operators
- Open-source (no lock-in)
- Great for complex dependencies

**Cons:**
- MWAA costs $300/month minimum
- Complex setup and learning curve
- Overkill for our simple pipelines
- Requires maintenance

**Decision:** Not cost-effective for MVP

#### Alternative 3: AWS Glue Workflows

**Pros:**
- Native Glue integration
- DAG-based orchestration
- Visualize dependencies

**Cons:**
- Limited to Glue jobs (not Lambda)
- Less flexible than Step Functions
- Newer service (less mature)

**Decision:** Glue Workflows for future consideration

### Consequences

**Positive:**
- ✅ **Simple Architecture:** Event-driven, no orchestrator
- ✅ **Low Cost:** Lambda is cheapest option
- ✅ **Fast Development:** No workflow DSL to learn
- ✅ **Easy Debugging:** Test each Lambda independently
- ✅ **Scalable:** Lambda auto-scales

**Negative:**
- ❌ **No Visual Workflow:** Must infer flow from code/docs
- ❌ **Limited Retries:** Must implement manually in Lambda
- ❌ **No Central Monitoring:** Must check each Lambda separately
- ❌ **Hard to Change Order:** Tightly coupled to S3 events

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **Simplicity** | **Visual workflow** |
| **Low cost** | **Built-in retries** |
| **Fast development** | **Central monitoring** |
| **Event-driven** | **Workflow flexibility** |

### Implementation Notes

1. **Event-Driven Flow:**
   ```
   Data Source → S3 (Raw)
       ↓ (S3 Event)
   Lambda (Validate & Route)
       ↓
   S3 (Raw/validated)
       ↓ (Scheduled Trigger)
   Glue (Bronze → Silver)
       ↓
   S3 (Processed)
       ↓ (Scheduled Trigger)
   Glue (Silver → Gold)
       ↓
   S3 (Curated)
   ```

2. **Retry Logic in Lambda:**
   ```python
   import boto3
   from botocore.exceptions import ClientError

   def lambda_handler(event, context):
       max_retries = 3
       for attempt in range(max_retries):
           try:
               # Process data
               return {"statusCode": 200}
           except ClientError as e:
               if attempt == max_retries - 1:
                   # Send to DLQ
                   raise
               time.sleep(2 ** attempt)  # Exponential backoff
   ```

3. **Dead Letter Queue (DLQ):**
   - Configure DLQ for failed Lambda invocations
   - Monitor DLQ with CloudWatch alarm
   - Manual inspection and reprocessing

4. **Glue Job Triggers:**
   ```python
   # Trigger Glue job daily at 3 AM
   glue.create_trigger(
       Name='daily-bronze-to-silver',
       Type='SCHEDULED',
       Schedule='cron(0 3 * * ? *)',
       Actions=[
           {'JobName': 'bronze-to-silver'}
       ]
   )
   ```

### When to Migrate to Step Functions

Consider Step Functions when:
- [ ] More than 5 sequential steps
- [ ] Complex conditional logic (if/then/else)
- [ ] Human approval steps
- [ ] Need workflow-level retry logic
- [ ] Parallel fan-out/fan-in patterns
- [ ] Budget increases (can afford $25/1M transitions)

### Related Decisions

- ADR-001: Serverless Architecture (Lambda fits paradigm)
- ADR-008: Error Handling Strategy (Lambda retry logic)

---

## ADR-008: Error Handling and Retry Strategy

**Status:** Accepted
**Date:** 2026-03-04
**Decision Makers:** Data Engineering Team
**Tags:** #error-handling #reliability #monitoring

### Context

Distributed systems fail. We need a strategy to handle:
- Network failures (S3, API calls)
- Data quality issues (invalid schema, missing fields)
- Service throttling (AWS rate limits)
- Code bugs and edge cases

Requirements:
- Automatic retries for transient failures
- Dead letter queue for permanent failures
- Alerting for critical errors
- Data loss prevention

### Decision

**Implement multi-layered error handling:**

1. **Lambda Functions:** Async invocation with DLQ
2. **Glue Jobs:** Job monitoring with CloudWatch alarms
3. **Data Validation:** Quarantine invalid data
4. **Alerts:** SNS notifications for critical failures

### Rationale

1. **Defense in Depth**
   - Multiple layers catch different error types
   - No single point of failure

2. **Graceful Degradation**
   - System continues operating despite partial failures
   - Invalid data quarantined, not blocking pipeline

3. **Observability**
   - CloudWatch Logs for debugging
   - Metrics for monitoring
   - Alarms for alerting

4. **Automatic Recovery**
   - Retries handle transient failures
   - Manual intervention only for true failures

### Error Handling by Layer

#### Layer 1: Lambda Function Level

**Strategy:**
- Async invocation with DLQ
- Exponential backoff for retries
- Structured logging

**Configuration:**
```yaml
Lambda:
  MemorySize: 512
  Timeout: 60
  ReservedConcurrentExecutions: 10  # Prevent runaway costs
  DeadLetterQueue:
    Type: SQS
    TargetArn: !GetAtt DataIngestionDLQ.Arn
  RetryAttempts: 2
  MaximumEventAge: 3600  # 1 hour
```

**Code Pattern:**
```python
import logging
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Process event
        validate_data(event)
        transform_data(event)
        store_data(event)

        return {
            'statusCode': 200,
            'body': 'Success'
        }

    except ValidationError as e:
        # Data quality issue - quarantine
        logger.error(f"Validation failed: {e}")
        send_to_quarantine(event, str(e))
        return {
            'statusCode': 400,
            'body': 'Validation failed'
        }

    except Exception as e:
        # Unexpected error - let Lambda retry
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        raise  # Trigger retry
```

#### Layer 2: Data Validation

**Strategy:**
- Validate schema before processing
- Quarantine invalid records
- Log validation errors

**Quarantine S3 Structure:**
```
s3://cloudmart-quarantine/
└── source=orders/
    └── error_type=schema_mismatch/
        └── year=2026/month=03/day=09/
            ├── invalid_record_1.json
            └── error_metadata_1.json
```

**Validation Code:**
```python
def validate_order(order):
    required_fields = ['order_id', 'customer_id', 'total_amount', 'order_date']

    for field in required_fields:
        if field not in order:
            raise ValidationError(f"Missing required field: {field}")

    if order['total_amount'] <= 0:
        raise ValidationError("Invalid amount: must be positive")

    # ... more validations
```

#### Layer 3: Glue Job Monitoring

**Strategy:**
- Job success/failure alarms
- Data quality checks within job
- Bookmark for incremental processing

**CloudWatch Alarm:**
```yaml
GlueJobFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: glue-bronze-to-silver-failure
    MetricName: glue.driver.aggregate.numFailedTasks
    Namespace: Glue
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref AlertSNSTopic
```

**Data Quality in Glue:**
```python
# Count records before/after transformation
input_count = df_input.count()
output_count = df_output.count()

logger.info(f"Input records: {input_count}")
logger.info(f"Output records: {output_count}")

# Alert if >20% data loss
loss_rate = (input_count - output_count) / input_count
if loss_rate > 0.20:
    raise DataQualityException(f"Excessive data loss: {loss_rate:.2%}")
```

#### Layer 4: Alerting

**Strategy:**
- SNS topic for critical alerts
- Email notifications to team
- CloudWatch dashboard for monitoring

**SNS Topic:**
```yaml
AlertSNSTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: cloudmart-data-pipeline-alerts
    Subscriptions:
      - Endpoint: data-team@cloudmart.com
        Protocol: email
```

**Alert Types:**
1. Lambda DLQ has messages
2. Glue job fails
3. Data quality threshold breached
4. Cost budget exceeded (80% threshold)
5. Athena query failures spike

### Alternatives Considered

#### Alternative 1: Fail Fast (No Retries)

**Pros:**
- Simple
- Immediate alerting

**Cons:**
- Transient failures cause permanent data loss
- More manual intervention required

**Decision:** Retries are essential for reliability

#### Alternative 2: Infinite Retries

**Pros:**
- Eventually consistent
- No data loss from transient failures

**Cons:**
- Poison messages block queue
- Runaway costs
- Delays in error detection

**Decision:** Limited retries (2-3) with DLQ

#### Alternative 3: External Monitoring (Datadog, New Relic)

**Pros:**
- Richer monitoring features
- Better visualization
- Anomaly detection

**Cons:**
- Additional cost ($50-100/month)
- More complexity
- Overkill for MVP

**Decision:** Use CloudWatch for MVP, external later if needed

### Consequences

**Positive:**
- ✅ **Fault Tolerance:** Transient failures auto-recover
- ✅ **Data Protection:** Invalid data quarantined, not lost
- ✅ **Observability:** Logs and metrics for debugging
- ✅ **Proactive Alerts:** Team notified of issues
- ✅ **Cost Control:** Limits prevent runaway costs

**Negative:**
- ❌ **Complexity:** More code to write and test
- ❌ **Noise:** Potential for alert fatigue if not tuned
- ❌ **Latency:** Retries add latency to processing

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **Reliability** | **Simplicity** |
| **Data protection** | **Immediate processing** |
| **Observability** | **Code complexity** |

### Implementation Checklist

- [ ] Lambda DLQ configured for all functions
- [ ] Exponential backoff in retry logic
- [ ] Validation logic with quarantine
- [ ] CloudWatch alarms for Glue jobs
- [ ] SNS topic subscriptions configured
- [ ] CloudWatch dashboard created
- [ ] Runbook for common errors
- [ ] Test failure scenarios

### Related Decisions

- ADR-007: Lambda vs Step Functions (error handling in Lambda)
- ADR-001: Serverless Architecture (distributed system error handling)

---

## ADR-009: Medallion Architecture (Bronze/Silver/Gold)

**Status:** Accepted
**Date:** 2026-03-05
**Decision Makers:** Data Engineering Team, CDO
**Tags:** #architecture #data-quality #lakehouse

### Context

Data lake organization impacts data quality, query performance, and user experience. We need a clear strategy for how data flows through the lake.

**Alternatives:**
- Flat structure (all data in one zone)
- Two-tier (raw + processed)
- Three-tier medallion (bronze/silver/gold)
- Four-tier (+ platinum for ML)

### Decision

**Implement three-tier medallion architecture: Bronze (Raw) → Silver (Processed) → Gold (Curated)**

### Rationale

1. **Clear Data Quality Progression**
   - Bronze: Raw, untouched data (immutable landing zone)
   - Silver: Cleansed, validated, conformed data
   - Gold: Business-ready aggregates and analytics

2. **Separation of Concerns**
   - Bronze: Data engineering (ingestion)
   - Silver: Data engineering (transformation)
   - Gold: Business users (analytics)

3. **Incremental Value**
   - Each layer adds value
   - Users query appropriate layer for their needs
   - Debug data quality issues by tracing through layers

4. **Industry Standard**
   - Databricks lakehouse pattern
   - Well-documented best practices
   - Easy to communicate to stakeholders

### Zone Definitions

#### Bronze Layer (Raw Zone)

**Purpose:** Immutable landing zone for raw data

**Characteristics:**
- **Immutable:** Never modified after ingestion
- **Format:** Original (JSON, CSV)
- **Partitioning:** By ingestion date
- **Retention:** 90 days (then archive to Glacier)
- **Quality:** No validation (accept all)
- **Access:** Data engineering only

**Use Cases:**
- Data auditing and lineage
- Reprocessing (rerun transformations)
- Debugging data quality issues
- Compliance and archival

**S3 Path:**
```
s3://cloudmart-raw/
├── orders/year=2026/month=03/day=09/orders_*.csv.gz
├── clickstream/year=2026/month=03/day=09/hour=14/events_*.json.gz
└── products/year=2026/month=03/day=09/catalog_*.json
```

#### Silver Layer (Processed Zone)

**Purpose:** Cleansed, validated, conformed data

**Characteristics:**
- **Cleansed:** Duplicates removed, nulls handled
- **Validated:** Schema validated, data types correct
- **Conformed:** Standardized formats (dates, decimals)
- **Format:** Parquet (columnar, compressed)
- **Partitioning:** Optimized for queries
- **Retention:** 2 years
- **Quality:** >99% clean data
- **Access:** Data engineering + analysts (read-only)

**Use Cases:**
- Data science model training
- Ad-hoc analysis
- Building Gold layer aggregates

**S3 Path:**
```
s3://cloudmart-processed/
├── orders/year=2026/month=03/day=09/orders.parquet
├── order_items/year=2026/month=03/day=09/order_items.parquet
└── clickstream_events/year=2026/month=03/day=09/events.parquet
```

**Transformations (Bronze → Silver):**
- Deduplicate by business key
- Validate schema and data types
- Handle missing values (fill or filter)
- Standardize formats (timestamp to UTC, decimals to 2 places)
- Add derived columns (year, month, day from timestamp)
- Convert to Parquet

#### Gold Layer (Curated Zone)

**Purpose:** Business-ready aggregated datasets

**Characteristics:**
- **Aggregated:** Pre-computed metrics (daily sales, CLV)
- **Joined:** Cross-source datasets (orders + customers)
- **Business Logic:** Applied (revenue calculations, segmentation)
- **Format:** Parquet (highly optimized)
- **Partitioning:** By business dimensions
- **Retention:** 2 years
- **Quality:** 100% clean, validated
- **Access:** All business users via Athena

**Use Cases:**
- Business intelligence dashboards
- Executive reporting
- Self-service analytics
- Regulatory reporting

**S3 Path:**
```
s3://cloudmart-curated/
├── daily_sales_summary/year=2026/month=03/summary.parquet
├── customer_lifetime_value/snapshot_date=2026-03-09/clv.parquet
└── product_performance/year=2026/month=03/metrics.parquet
```

**Transformations (Silver → Gold):**
- Aggregate (SUM, AVG, COUNT by day/week/month)
- Join across sources (orders + customers + products)
- Apply business logic (revenue = sum(order_items))
- Create cohorts (customer segments)
- Calculate KPIs (CLV, churn rate, conversion rate)

### Alternatives Considered

#### Alternative 1: Flat Structure (One Zone)

**Pros:**
- Simplest
- No ETL between zones

**Cons:**
- No separation of concerns
- Data quality mixed
- Hard to debug
- Users see raw, messy data

**Decision:** Not suitable for business users

#### Alternative 2: Two-Tier (Raw + Processed)

**Pros:**
- Simpler than three-tier
- Clear raw vs. clean separation

**Cons:**
- Processed zone serves both analysts and aggregates
- No clear line between detail and summary data
- Query performance suffers (analysts query huge tables)

**Decision:** Three-tier provides better UX

#### Alternative 3: Four-Tier (+ Platinum)

**Pros:**
- Platinum layer for ML feature store
- Even more specialization

**Cons:**
- Added complexity
- Overkill for MVP
- Harder to explain to stakeholders

**Decision:** Three tiers sufficient; add Platinum later if needed

### Consequences

**Positive:**
- ✅ **Clear Data Quality:** Each layer has defined quality bar
- ✅ **Incremental Value:** Bronze → Silver → Gold adds value at each step
- ✅ **Easy Debugging:** Trace data issues through layers
- ✅ **Performance:** Gold layer pre-aggregated for fast queries
- ✅ **Governance:** Different access controls per layer
- ✅ **Reprocessing:** Immutable Bronze enables easy reprocessing

**Negative:**
- ❌ **Storage Costs:** Data stored in 3 copies (but compressed)
- ❌ **ETL Complexity:** Must maintain transformations between layers
- ❌ **Latency:** Data passes through 3 stages before reaching users

### Trade-offs

| What We Gained | What We Sacrificed |
|---------------|-------------------|
| **Data quality** | **Immediacy** |
| **Query performance** | **Storage efficiency** |
| **Separation of concerns** | **Simplicity** |
| **Debugging** | **ETL complexity** |

### Implementation Notes

1. **Storage Cost Mitigation:**
   - Bronze: Gzip compression, archive to Glacier after 90 days
   - Silver/Gold: Parquet compression (3-5x reduced size)
   - Lifecycle policies automate archival
   - **Total storage: ~30% more than raw, but queries 10x cheaper**

2. **Latency Mitigation:**
   - Run ETL jobs on schedule (daily at 3 AM)
   - Most users OK with T+1 data freshness
   - For real-time needs, query Silver layer directly

3. **Access Control:**
   ```yaml
   Bronze:
     Read: DataEngineers
     Write: IngestionLambda

   Silver:
     Read: DataEngineers, Analysts
     Write: GlueETLJobs

   Gold:
     Read: All_BusinessUsers
     Write: GlueETLJobs
   ```

4. **Documentation:**
   - Data catalog descriptions for each layer
   - README in each S3 prefix
   - Diagram showing data flow

### Success Metrics

- [ ] Bronze layer: 100% of source data ingested
- [ ] Silver layer: >99% data quality (validated)
- [ ] Gold layer: <5 second query performance (90th percentile)
- [ ] Users query Gold >80% of the time (not Silver)

### Related Decisions

- ADR-003: AWS Glue for ETL (transforms data between layers)
- ADR-006: File Formats (Parquet in Silver/Gold)

---

## ADR-010: CloudFormation vs Terraform

**Status:** Accepted
**Date:** 2026-03-06
**Decision Makers:** Data Engineering Team, VP Engineering
**Tags:** #iac #cloudformation #terraform #infrastructure

### Context

Infrastructure as Code (IaC) is essential for:
- Reproducible deployments
- Version control of infrastructure
- Automated provisioning
- Disaster recovery

**Options:**
- AWS CloudFormation (native AWS)
- Terraform (HashiCorp, multi-cloud)
- AWS CDK (code-based)
- Manual AWS Console (not IaC)

### Decision

**Provide both CloudFormation and Terraform templates. Students choose based on preference.**

**Recommended for beginners: CloudFormation**

### Rationale

1. **CloudFormation Advantages:**
   - Native AWS service (no 3rd party)
   - No installation required
   - Stack rollback on failure
   - Free (no cost)
   - Rich AWS service support
   - StackSets for multi-account (future)

2. **Terraform Advantages:**
   - Multi-cloud portability
   - More concise syntax (HCL vs. YAML/JSON)
   - Better state management
   - Larger community
   - More mature modules/libraries

3. **Why Both:**
   - Students learn both technologies
   - Team can use their preferred tool
   - Demonstrates multi-tool proficiency

### CloudFormation Example

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: CloudMart Data Lake - S3 Buckets

Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - prod

Resources:
  RawBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub cloudmart-raw-${EnvironmentName}-${AWS::AccountId}
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: ArchiveOldData
            Status: Enabled
            Transitions:
              - TransitionInDays: 90
                StorageClass: GLACIER
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      Tags:
        - Key: Project
          Value: CloudMart
        - Key: Environment
          Value: !Ref EnvironmentName

Outputs:
  RawBucketName:
    Description: Bronze layer S3 bucket
    Value: !Ref RawBucket
    Export:
      Name: !Sub ${AWS::StackName}-RawBucket
```

**Deploy:**
```bash
aws cloudformation create-stack \
  --stack-name cloudmart-data-lake \
  --template-body file://infrastructure.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=dev \
  --capabilities CAPABILITY_IAM
```

### Terraform Example

```hcl
variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
  default     = "dev"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "raw" {
  bucket = "cloudmart-raw-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project     = "CloudMart"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    id     = "ArchiveOldData"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "raw_bucket_name" {
  description = "Bronze layer S3 bucket"
  value       = aws_s3_bucket.raw.id
}
```

**Deploy:**
```bash
terraform init
terraform plan -var="environment=dev"
terraform apply -var="environment=dev"
```

### Comparison

| Aspect | CloudFormation | Terraform |
|--------|---------------|-----------|
| **Cloud Support** | AWS only | Multi-cloud |
| **Syntax** | YAML/JSON (verbose) | HCL (concise) |
| **State Management** | Managed by AWS | Local or remote backend |
| **Rollback** | Automatic | Manual (destroy + apply) |
| **Cost** | Free | Free (open source) |
| **AWS Support** | Complete, always up-to-date | Good, may lag new services |
| **Learning Curve** | Moderate | Moderate |
| **Community** | Large | Very Large |
| **Modularity** | Nested stacks | Modules |

### Decision for Students

**Choose CloudFormation if:**
- ✅ You're new to IaC
- ✅ You're focusing on AWS only
- ✅ You want native AWS integration
- ✅ You prefer automatic rollback

**Choose Terraform if:**
- ✅ You want multi-cloud skills
- ✅ You prefer HCL syntax
- ✅ You're already familiar with Terraform
- ✅ You want strong modularity

### Consequences

**Positive:**
- ✅ **Flexibility:** Students choose their preferred tool
- ✅ **Learning:** Exposure to both tools
- ✅ **Reproducibility:** Infrastructure as code
- ✅ **Version Control:** Git-friendly

**Negative:**
- ❌ **Maintenance:** Must maintain two templates
- ❌ **Parity:** Risk of divergence between templates
- ❌ **Confusion:** Students must choose

### Implementation Notes

1. **Starter Templates:**
   - `/infrastructure/cloudformation/` (CloudFormation)
   - `/infrastructure/terraform/` (Terraform)
   - Both implement identical infrastructure

2. **Documentation:**
   - Side-by-side comparison guide
   - Deployment instructions for both
   - Troubleshooting tips

3. **Testing:**
   - Validate both templates periodically
   - Ensure parity (same resources deployed)

### Related Decisions

- ADR-001: Serverless Architecture (IaC supports serverless)

---

## Summary of Key Decisions

| ADR | Decision | Primary Rationale |
|-----|----------|------------------|
| **ADR-001** | Serverless Architecture | 90% cost savings, zero ops |
| **ADR-002** | Amazon S3 for Storage | Lowest cost ($0.023/GB), unlimited scale |
| **ADR-003** | AWS Glue for ETL | Serverless Spark, auto-scaling |
| **ADR-004** | Amazon Athena for Analytics | Query-in-place, pay-per-query |
| **ADR-005** | Date-based Partitioning | 90% query cost reduction via pruning |
| **ADR-006** | Parquet Format | 10x faster queries, 3x less storage |
| **ADR-007** | Event-Driven Lambda | Simple, low-cost orchestration |
| **ADR-008** | Multi-Layer Error Handling | Reliability, observability |
| **ADR-009** | Medallion Architecture | Clear data quality progression |
| **ADR-010** | CloudFormation & Terraform | Student choice, both supported |

---

## References

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Databricks Lakehouse Architecture](https://www.databricks.com/glossary/ medallion-architecture)
- [AWS Data Lake Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/building-data-lakes/building-data-lake-aws.html)
- [Architecture Decision Records (ADR)](https://adr.github.io/)

---

**Document Version:** 1.0
**Last Reviewed:** March 9, 2026
**Next Review:** After 10 student submissions
