# 🏗️ Architecture Documentation

## Overview

This directory contains comprehensive architecture diagrams for the **CloudMart Serverless Data Lake** project using Mermaid diagram syntax. These diagrams provide visual representations of the system architecture, data flows, security, and operational aspects of the solution.

---

## 📊 Diagram Collection

This architecture documentation includes **6 detailed Mermaid diagrams** covering all aspects of the serverless data lake implementation:

| Diagram | File | Lines | Description |
|---------|------|-------|-------------|
| **High-Level Architecture** | `01-high-level-architecture.mmd` | ~400 | Complete end-to-end system architecture showing all AWS services, data sources, and data lake zones |
| **Data Ingestion Flow** | `02-data-ingestion-flow.mmd` | ~350 | Detailed ingestion pipeline with S3 events, Lambda processing, and error handling |
| **ETL Pipeline** | `03-etl-pipeline.mmd` | ~400 | Glue ETL jobs orchestration, Bronze→Silver→Gold transformations, and data quality |
| **Data Catalog** | `04-data-catalog.mmd` | ~300 | Glue Data Catalog structure, crawlers, schemas, and Athena integration |
| **Security Architecture** | `05-security-architecture.mmd` | ~350 | IAM roles, encryption, bucket policies, VPC endpoints, and audit logging |
| **Cost Optimization** | `06-cost-optimization.mmd` | ~250 | Lifecycle policies, resource optimization, and cost monitoring strategies |

**Total Documentation:** ~2,050 lines of detailed Mermaid diagrams

---

## 🎨 How to Render Mermaid Diagrams

### Option 1: GitHub (Recommended)

GitHub natively supports Mermaid diagrams in Markdown files. Simply view these `.mmd` files on GitHub and they will render automatically.

**Steps:**
1. Push this repository to GitHub
2. Navigate to the `architecture/` folder
3. Click on any `.mmd` file
4. GitHub will automatically render the Mermaid diagram

### Option 2: VS Code

Use the **Mermaid Preview** extension for VS Code:

```bash
# Install the extension
code --install-extension bierner.markdown-mermaid
```

**Steps:**
1. Open any `.mmd` file in VS Code
2. Press `Ctrl+Shift+V` (or `Cmd+Shift+V` on Mac)
3. The preview pane will render the Mermaid diagram

### Option 3: Mermaid Live Editor

Use the official online editor at [https://mermaid.live](https://mermaid.live):

**Steps:**
1. Go to [https://mermaid.live](https://mermaid.live)
2. Copy the content of any `.mmd` file
3. Paste into the editor
4. The diagram will render in real-time
5. Export as PNG, SVG, or PDF

### Option 4: Documentation Tools

**MkDocs with Mermaid Plugin:**
```bash
pip install mkdocs-mermaid2-plugin
```

**Docusaurus:**
```bash
npm install @docusaurus/theme-mermaid
```

**Confluence:**
Use the "Mermaid Charts & Diagrams" plugin

---

## 📐 Diagram Details

### 1. High-Level Architecture (`01-high-level-architecture.mmd`)

**Purpose:** Provides a complete bird's-eye view of the entire serverless data lake architecture.

**Key Components:**
- **Data Sources (4):**
  - E-commerce transactions (CSV)
  - Customer profiles (JSON)
  - Product catalog (Parquet)
  - Web analytics (JSON/CSV)

- **AWS Services:**
  - Amazon S3 (3 zones: Raw/Bronze, Processed/Silver, Curated/Gold)
  - AWS Lambda (ingestion functions)
  - AWS Glue (ETL jobs, crawlers, data catalog)
  - Amazon Athena (SQL analytics)
  - Amazon CloudWatch (monitoring)
  - AWS IAM (security)
  - AWS KMS (encryption)

- **Data Lake Zones:**
  - **Bronze/Raw:** Original data as-is
  - **Silver/Processed:** Cleaned and validated data
  - **Gold/Curated:** Business-ready aggregated data

**Use Cases:**
- Executive presentations
- Solution architecture reviews
- Documentation for stakeholders
- Onboarding new team members

---

### 2. Data Ingestion Flow (`02-data-ingestion-flow.mmd`)

**Purpose:** Detailed breakdown of how data flows from source systems into the data lake.

**Key Processes:**
1. **File Upload:** Data arrives in S3 landing buckets
2. **Event Trigger:** S3 event notification triggers Lambda
3. **Validation:** Lambda validates file format, schema, size
4. **Processing:** File metadata extraction and enrichment
5. **Partitioning:** Data organized by date (year/month/day)
6. **Error Handling:** Failed files moved to error bucket
7. **Logging:** All activities logged to CloudWatch

**Decision Points:**
- File format validation (CSV, JSON, Parquet)
- Schema validation (required fields)
- Size validation (min/max thresholds)
- Duplicate detection

**Error Scenarios:**
- Invalid file format → move to error bucket
- Schema mismatch → log and alert
- Parsing failure → retry with exponential backoff

**Monitoring:**
- Lambda execution metrics
- S3 PUT/GET operations
- Error rates and types
- Processing latency

---

### 3. ETL Pipeline (`03-etl-pipeline.mmd`)

**Purpose:** Comprehensive view of Glue ETL jobs transforming data across data lake zones.

**Pipeline Stages:**

**Stage 1: Bronze to Silver (Cleaning & Validation)**
- Remove duplicates
- Handle null values
- Standardize data types
- Fix formatting issues
- Validate business rules
- Add audit columns (ingestion_timestamp, source_system)

**Stage 2: Silver to Gold (Aggregation & Enrichment)**
- Join related datasets
- Calculate derived metrics
- Aggregate by business dimensions
- Create star schema tables
- Apply business logic

**ETL Job Types:**
1. **Transactions ETL:** Process sales transactions
2. **Customers ETL:** Clean and deduplicate customer data
3. **Products ETL:** Maintain product master data
4. **Analytics ETL:** Process web analytics events

**Data Quality Checks:**
- Row count validation
- Column completeness checks
- Data type validation
- Range and constraint checks
- Referential integrity
- Business rule validation

**Job Dependencies:**
- Bronze→Silver jobs run after ingestion
- Silver→Gold jobs wait for Silver completion
- Analytics jobs depend on all Gold tables

**Orchestration:**
- AWS Glue Workflows
- CloudWatch Events for scheduling
- Step Functions for complex workflows

---

### 4. Data Catalog (`04-data-catalog.mmd`)

**Purpose:** Structure of the Glue Data Catalog and how Athena queries the catalog.

**Catalog Hierarchy:**

```
cloudmart_datalake (Catalog)
├── Bronze Database
│   ├── raw_transactions (Table)
│   ├── raw_customers (Table)
│   ├── raw_products (Table)
│   └── raw_web_events (Table)
├── Silver Database
│   ├── clean_transactions (Table)
│   ├── clean_customers (Table)
│   ├── clean_products (Table)
│   └── clean_web_events (Table)
└── Gold Database
    ├── fact_sales (Table)
    ├── dim_customers (Table)
    ├── dim_products (Table)
    ├── dim_date (Table)
    └── agg_daily_sales (Table)
```

**Crawler Strategy:**
- **Bronze Crawlers:** Run after ingestion (event-driven)
- **Silver Crawlers:** Run after Bronze→Silver ETL
- **Gold Crawlers:** Run after Silver→Gold ETL
- **Schedule:** Daily for incremental updates

**Partition Management:**
- Date-based partitioning (year/month/day)
- Automatic partition discovery by crawlers
- Manual partition addition via MSCK REPAIR
- Partition pruning for query optimization

**Schema Evolution:**
- Schema versioning in catalog
- Backward-compatible changes
- Schema validation in ETL jobs

**Athena Integration:**
- Query execution via catalog metadata
- Table statistics for query optimization
- Partition projection for performance
- Workgroup isolation

---

### 5. Security Architecture (`05-security-architecture.mmd`)

**Purpose:** Comprehensive security controls protecting data at rest, in transit, and during processing.

**Security Layers:**

**1. Identity & Access Management (IAM)**
- **Lambda Execution Role:**
  - Read/write S3
  - Write CloudWatch Logs
  - KMS decrypt permissions
- **Glue Service Role:**
  - Read S3 (Bronze, Silver)
  - Write S3 (Silver, Gold)
  - Data Catalog access
  - KMS encrypt/decrypt
- **Athena User Role:**
  - Read S3 (Silver, Gold)
  - Query execution permissions
  - Results bucket access
- **Principle of Least Privilege:** Each service has only necessary permissions

**2. Data Encryption**
- **At Rest:**
  - S3 bucket encryption (SSE-KMS)
  - Customer-managed KMS keys
  - Key rotation enabled (annual)
- **In Transit:**
  - TLS 1.2+ for all API calls
  - HTTPS for S3 access
  - VPC endpoints (private network)

**3. S3 Bucket Security**
- **Bucket Policies:**
  - Deny unencrypted uploads
  - Enforce MFA delete
  - Block public access
- **Versioning:** Enabled on all buckets
- **Access Logging:** S3 access logs to audit bucket
- **Cross-Region Replication:** DR strategy

**4. Network Security**
- **VPC Endpoints (Optional):**
  - S3 Gateway Endpoint
  - Glue Interface Endpoint
  - Athena Interface Endpoint
  - No internet gateway required
- **Security Groups:** Control service-to-service communication

**5. Audit & Compliance**
- **CloudTrail:**
  - All API calls logged
  - Log file integrity validation
  - Multi-region trail
- **CloudWatch Logs:**
  - Lambda execution logs
  - Glue job logs
  - Athena query logs
- **AWS Config:**
  - Resource compliance monitoring
  - Configuration change tracking

**6. Data Governance**
- **Lake Formation (Future):**
  - Fine-grained access control
  - Column-level security
  - Tag-based policies
- **AWS Macie (Optional):**
  - PII detection
  - Sensitive data discovery

---

### 6. Cost Optimization (`06-cost-optimization.mmd`)

**Purpose:** Strategies and implementations to minimize operational costs while maintaining performance.

**Optimization Strategies:**

**1. S3 Storage Optimization**
- **Lifecycle Policies:**
  - Bronze (Raw): 30 days → Glacier, 90 days → Deep Archive
  - Silver (Processed): 60 days → IA, 180 days → Glacier
  - Gold (Curated): Keep in Standard (most accessed)
  - Logs: 7 days → IA, 30 days → Glacier
- **Compression:**
  - Store data in compressed formats (Gzip, Snappy)
  - Parquet with Snappy compression (best balance)
- **Partitioning:**
  - Efficient partition strategy reduces scanned data
  - Partition by date (year/month/day)

**2. Lambda Optimization**
- **Memory Allocation:**
  - Right-size memory (1024MB typical)
  - Monitor duration/memory usage
- **Concurrency:**
  - Reserved concurrency to prevent cost spikes
  - Use SQS for rate limiting
- **Cold Starts:**
  - Keep functions warm with CloudWatch Events
  - Use provisioned concurrency for critical paths

**3. Glue ETL Optimization**
- **DPU (Data Processing Unit) Tuning:**
  - Start with 2 DPUs, scale based on data volume
  - Monitor job metrics to right-size
- **Job Bookmarks:**
  - Process only new data (incremental)
  - Reduce reprocessing costs
- **Pushdown Predicates:**
  - Filter early in ETL pipeline
  - Reduce data movement
- **Columnar Formats:**
  - Use Parquet for optimal performance
  - Better compression, faster queries

**4. Athena Query Optimization**
- **Partition Pruning:**
  - Always filter on partition keys
  - Reduces data scanned (primary cost driver)
- **Columnar Storage:**
  - Query only needed columns
  - Parquet enables column pruning
- **Compression:**
  - Compressed data = less data scanned
- **CTAS (Create Table As Select):**
  - Transform data into optimized format
- **Query Result Reuse:**
  - Enable result caching (24 hours)

**5. Cost Monitoring & Alerts**
- **Cost Allocation Tags:**
  - Tag all resources: project, environment, team
  - Track costs by dimension
- **AWS Budgets:**
  - Set monthly budget thresholds
  - Alerts at 50%, 75%, 90%, 100%
- **Cost Explorer:**
  - Analyze spending patterns
  - Identify cost optimization opportunities
- **CloudWatch Dashboards:**
  - Real-time cost metrics
  - Resource utilization tracking

**6. Reserved Capacity (Future)**
- **Savings Plans:** For predictable workloads
- **Reserved Concurrency:** For Lambda
- **Glue Data Processing Units:** Long-term discount

**Cost Targets:**
- **Development:** < $50/month
- **Production (Small):** < $200/month
- **Production (Medium):** < $500/month

---

## 🎯 Key Design Decisions

### 1. Serverless-First Approach
**Decision:** Use AWS serverless services (Lambda, Glue, Athena) exclusively
**Rationale:**
- No infrastructure management
- Pay-per-use pricing model
- Automatic scaling
- Lower operational overhead

**Trade-offs:**
- Cold start latency (Lambda)
- Service limits (Lambda 15min timeout)
- Less control over infrastructure

### 2. Three-Zone Data Lake (Bronze/Silver/Gold)
**Decision:** Implement medallion architecture with three zones
**Rationale:**
- Clear separation of concerns
- Progressive data quality improvement
- Enables data lineage tracking
- Supports different access patterns

**Trade-offs:**
- Increased storage costs (data duplication)
- More ETL jobs to maintain
- Higher complexity

### 3. Event-Driven Ingestion
**Decision:** Use S3 events to trigger Lambda for ingestion
**Rationale:**
- Real-time processing
- No polling overhead
- Scalable by design
- Loose coupling

**Trade-offs:**
- Eventual consistency
- Requires careful error handling
- Potential duplicate events

### 4. Glue Data Catalog as Metadata Store
**Decision:** Use Glue Data Catalog instead of external metastore (Hive, etc.)
**Rationale:**
- Native AWS integration
- No additional infrastructure
- Shared by Glue and Athena
- Serverless

**Trade-offs:**
- AWS vendor lock-in
- Limited to AWS ecosystem

### 5. Parquet as Standard Format
**Decision:** Standardize on Parquet for Silver and Gold zones
**Rationale:**
- Columnar storage (query performance)
- Excellent compression
- Schema evolution support
- Industry standard

**Trade-offs:**
- Not human-readable
- Write overhead vs. row formats

### 6. Date-Based Partitioning
**Decision:** Partition all tables by year/month/day
**Rationale:**
- Most queries filter by date
- Efficient partition pruning
- Standard pattern easy to understand

**Trade-offs:**
- Too many partitions for small datasets
- Metadata overhead

---

## 📂 Navigation Guide

### For Solution Architects
Start with: `01-high-level-architecture.mmd` → `05-security-architecture.mmd` → `06-cost-optimization.mmd`

### For Data Engineers
Start with: `02-data-ingestion-flow.mmd` → `03-etl-pipeline.mmd` → `04-data-catalog.mmd`

### For DevOps Engineers
Start with: `05-security-architecture.mmd` → `06-cost-optimization.mmd` → `01-high-level-architecture.mmd`

### For Business Stakeholders
Start with: `01-high-level-architecture.mmd` → `06-cost-optimization.mmd`

---

## 🔄 Diagram Maintenance

### When to Update Diagrams

1. **Architecture Changes:**
   - New AWS service added
   - Service version upgrade
   - Major component changes

2. **Security Updates:**
   - New IAM policies
   - Encryption changes
   - Compliance requirements

3. **Cost Optimizations:**
   - New lifecycle policies
   - Resource size changes
   - New cost-saving measures

4. **Data Flow Changes:**
   - New data source
   - ETL logic changes
   - Partition strategy updates

### Version Control
- All diagrams are version-controlled in Git
- Use conventional commit messages
- Tag releases with version numbers

---

## 📚 Additional Resources

### Mermaid Documentation
- [Official Mermaid Docs](https://mermaid-js.github.io/mermaid/)
- [Flowchart Syntax](https://mermaid-js.github.io/mermaid/#/flowchart)
- [Sequence Diagrams](https://mermaid-js.github.io/mermaid/#/sequenceDiagram)
- [C4 Diagrams](https://mermaid-js.github.io/mermaid/#/c4c)

### AWS Architecture
- [AWS Architecture Center](https://aws.amazon.com/architecture/)
- [Data Lake Best Practices](https://aws.amazon.com/big-data/datalakes-and-analytics/)
- [Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

### Related Documentation
- [../IMPLEMENTATION-GUIDE.md](../IMPLEMENTATION-GUIDE.md) - Step-by-step implementation
- [../ARCHITECTURE-DECISIONS.md](../ARCHITECTURE-DECISIONS.md) - ADR records
- [../COST-ESTIMATION.md](../COST-ESTIMATION.md) - Detailed cost breakdown

---

## 💡 Tips for Reading Diagrams

1. **Start Top-to-Bottom, Left-to-Right:** Most diagrams flow in this direction
2. **Follow the Arrows:** Arrows show data flow and dependencies
3. **Color Coding:** Different colors typically represent different types of components
4. **Legend:** Check for legends explaining symbols and colors
5. **Zoom In:** Use Mermaid Live Editor to zoom for detailed views

---

## 🤝 Contributing

To add or modify diagrams:

1. Follow Mermaid syntax guidelines
2. Test rendering in Mermaid Live Editor
3. Add description to this README
4. Update the diagram table
5. Submit PR with clear commit message

---

**Last Updated:** March 2026
**Maintained By:** CloudMart Data Engineering Team
**Contact:** data-engineering@cloudmart.example.com
