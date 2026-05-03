# 🎯 Checkpoint 01: Serverless Data Lake

[![Checkpoint](https://img.shields.io/badge/Type-Integration%20Checkpoint-blue.svg)](https://shields.io/)
[![AWS](https://img.shields.io/badge/Platform-AWS-orange.svg)](https://aws.amazon.com/)
[![Difficulty](https://img.shields.io/badge/Difficulty-Intermediate-yellow.svg)](https://shields.io/)
[![Duration](https://img.shields.io/badge/Duration-20--25%20hours-green.svg)](https://shields.io/)

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Business Scenario](#business-scenario)
- [Learning Objectives](#learning-objectives)
- [Technology Stack](#technology-stack)
- [Architecture Overview](#architecture-overview)
- [Success Criteria](#success-criteria)
- [Getting Started](#getting-started)
- [Project Phases](#project-phases)
- [Project Structure](#project-structure)
- [Deliverables](#deliverables)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)
- [Next Steps](#next-steps)

---

## 🎓 Overview

Welcome to **Checkpoint 01: Serverless Data Lake** - your first major integration project that combines everything you've learned in Modules 01-06. This is a hands-on capstone project where you'll build a complete, production-ready serverless data lake on AWS for a fictional e-commerce company.

**This is NOT a quiz or assessment.** Instead, you'll:
- Build real cloud infrastructure
- Write production-quality code
- Design scalable data pipelines
- Apply AWS best practices
- Create comprehensive documentation

### What You'll Build

A complete **Serverless Data Lake** for **CloudMart**, an e-commerce company that needs to consolidate data from multiple sources and enable data-driven decision making across the organization.

**Key Features:**
- 📦 Multi-zone data lake (Raw → Processed → Curated)
- ⚡ Event-driven data ingestion with AWS Lambda
- 🔍 Automated data cataloging with AWS Glue
- 🔄 ETL pipelines for data transformation
- 📊 SQL analytics with Amazon Athena
- 🔐 Enterprise-grade security with IAM
- 📈 Monitoring and alerting with CloudWatch
- 💰 Cost-optimized architecture (<$50/month)

### Project Characteristics

| Aspect | Details |
|--------|---------|
| **Type** | Integration Checkpoint (Capstone Project) |
| **Duration** | 20-25 hours over 3-5 days |
| **Complexity** | Intermediate |
| **Cloud Provider** | Amazon Web Services (AWS) |
| **Cost** | $30-50/month (mostly Free Tier eligible) |
| **Team Size** | Individual project |
| **Grading** | 100 points (see grading rubric) |

---

## ✅ Prerequisites

### Required Modules (Must be 100% Complete)

Before starting this checkpoint, you must have successfully completed:

- ✅ **Module 01: Cloud Fundamentals**
  - AWS account setup and IAM basics
  - AWS CLI and SDK configuration
  - Core AWS services overview
  - Cloud computing concepts

- ✅ **Module 02: Storage Basics**
  - Amazon S3 fundamentals
  - Bucket policies and lifecycle rules
  - Storage classes and optimization
  - Data organization strategies

- ✅ **Module 03: SQL Foundations**
  - SQL query fundamentals
  - Joins, aggregations, and window functions
  - Query optimization techniques
  - Data modeling concepts

- ✅ **Module 04: Python for Data**
  - Python programming basics
  - Data manipulation with Pandas
  - Boto3 for AWS automation
  - Error handling and logging

- ✅ **Module 05: Data Lakehouse Concepts**
  - Data lake architecture patterns
  - Lakehouse zones (Bronze/Silver/Gold)
  - Data catalog and metadata management
  - File formats (Parquet, JSON, CSV)

- ✅ **Module 06: ETL Fundamentals**
  - Extract-Transform-Load concepts
  - Data quality and validation
  - Scheduling and orchestration basics
  - Monitoring and error handling

### Technical Requirements

- **AWS Account:** Active AWS account with Free Tier access
- **Development Environment:**
  - Python 3.9+ installed
  - AWS CLI configured with credentials
  - Git for version control
  - Code editor (VS Code recommended)
- **Skills:**
  - Comfortable with command-line interface
  - Basic understanding of infrastructure as code
  - Familiarity with JSON and YAML formats
  - SQL query writing proficiency
  - Python scripting experience

### Knowledge Check

Before proceeding, ensure you can answer YES to these questions:

- [ ] Can you create and configure S3 buckets with policies?
- [ ] Can you write and deploy AWS Lambda functions?
- [ ] Can you write SQL queries with joins and aggregations?
- [ ] Can you use Python to process JSON and CSV data?
- [ ] Do you understand data lake architecture concepts?
- [ ] Can you create IAM roles and policies?
- [ ] Have you used CloudFormation or Terraform?
- [ ] Can you use the AWS CLI for automation?

---

## 💼 Business Scenario

### The Company: CloudMart

**CloudMart** is a rapidly growing e-commerce platform with:
- 500K+ monthly active users
- 50K+ daily transactions
- 100K+ products across 50 categories
- Operations in 25 countries

### The Challenge

CloudMart's data is currently siloed across multiple systems:

1. **Transactional Database (RDS):** Orders, customers, products
2. **Application Logs (S3):** User clickstream and behavior data
3. **Marketing Platform:** Campaign and conversion data
4. **Customer Service System:** Support tickets and satisfaction scores

**Pain Points:**
- ❌ No unified view of customer behavior
- ❌ Business analysts can't access operational data
- ❌ Manual data exports taking days
- ❌ Reports are always outdated
- ❌ No ability to correlate user behavior with transactions
- ❌ Limited insights for product recommendations
- ❌ High infrastructure costs for analytics

### Your Mission

As the newly hired **Data Engineer**, you're tasked with:

1. **Design and build** a serverless data lake on AWS
2. **Consolidate** data from multiple sources into a unified platform
3. **Enable self-service analytics** for business users
4. **Implement** automated data quality checks
5. **Optimize costs** while maintaining performance
6. **Document** architecture and operational procedures
7. **Ensure** security and compliance with data regulations

### Business Impact

Your solution will enable:
- 📊 Real-time visibility into business metrics
- 🎯 Data-driven decision making across teams
- 🚀 Faster time-to-insight (days → minutes)
- 💰 90% cost reduction vs. traditional data warehouse
- 🔍 Advanced analytics and machine learning capabilities
- 📈 Better customer experience through personalization

---

## 🎯 Learning Objectives

By completing this checkpoint, you will demonstrate mastery of:

### Technical Skills

1. **Cloud Infrastructure Design**
   - Design multi-tier cloud architectures
   - Apply AWS Well-Architected Framework principles
   - Make informed architecture decisions with trade-off analysis

2. **Serverless Computing**
   - Build event-driven applications with AWS Lambda
   - Configure triggers and event sources
   - Implement error handling and retry logic
   - Optimize Lambda functions for cost and performance

3. **Data Lake Implementation**
   - Structure data lake zones (Raw/Processed/Curated)
   - Implement data partitioning strategies
   - Choose appropriate file formats (Parquet, JSON, CSV)
   - Design data organization for query performance

4. **AWS Storage Services**
   - Configure S3 buckets with proper security
   - Implement bucket policies and lifecycle rules
   - Use S3 event notifications
   - Optimize storage costs with storage classes

5. **Data Cataloging**
   - Configure AWS Glue Data Catalog
   - Set up and run Glue Crawlers
   - Manage schema evolution
   - Create and maintain metadata tables

6. **ETL Pipeline Development**
   - Design data transformation workflows
   - Implement Bronze → Silver → Gold transformations
   - Write Glue ETL jobs in Python
   - Handle incremental data processing

7. **Analytics and Querying**
   - Write optimized SQL queries in Athena
   - Implement partitioning for query performance
   - Create views and materialized datasets
   - Generate business intelligence reports

8. **Security and Access Control**
   - Design IAM roles with least privilege
   - Implement resource-based policies
   - Configure encryption at rest and in transit
   - Manage access to sensitive data

9. **Monitoring and Operations**
   - Set up CloudWatch dashboards
   - Configure alarms and notifications
   - Implement logging strategies
   - Monitor costs and resource usage

10. **Infrastructure as Code**
    - Write CloudFormation or Terraform templates
    - Version control infrastructure definitions
    - Implement automated deployments
    - Follow IaC best practices

### Professional Skills

11. **Documentation**
    - Create architecture decision records (ADRs)
    - Write clear technical documentation
    - Document operational procedures
    - Maintain project runbooks

12. **Problem Solving**
    - Debug distributed systems issues
    - Troubleshoot cloud infrastructure problems
    - Optimize for performance and cost
    - Handle edge cases and errors gracefully

13. **Project Management**
    - Break down complex projects into phases
    - Set milestones and track progress
    - Manage project dependencies
    - Deliver complete solutions on time

14. **Cost Optimization**
    - Estimate cloud infrastructure costs
    - Implement cost-saving strategies
    - Monitor and control spending
    - Balance cost vs. performance trade-offs

15. **Testing and Validation**
    - Write automated tests for data pipelines
    - Validate data quality and accuracy
    - Perform end-to-end system testing
    - Create acceptance criteria

16. **Communication**
    - Present technical solutions to stakeholders
    - Explain architecture decisions
    - Create visual diagrams and documentation
    - Write clear commit messages and code comments

17. **Best Practices**
    - Follow AWS best practices
    - Apply security principles
    - Write maintainable code
    - Design for scalability and reliability

18. **Integration**
    - Connect multiple AWS services
    - Design service interfaces
    - Handle service limits and quotas
    - Implement proper error propagation

---

## 🛠️ Technology Stack

### AWS Services

| Service | Purpose | Usage |
|---------|---------|-------|
| **Amazon S3** | Object storage | Data lake storage (Raw, Processed, Curated zones) |
| **AWS Lambda** | Serverless compute | Event-driven data processing and validation |
| **AWS Glue** | ETL service | Data cataloging, crawling, and transformations |
| **Amazon Athena** | Query service | SQL analytics on S3 data |
| **AWS IAM** | Access management | Roles, policies, and permissions |
| **Amazon CloudWatch** | Monitoring | Logs, metrics, dashboards, and alarms |
| **AWS CloudFormation** | IaC | Infrastructure provisioning and management |
| **AWS KMS** | Key management | Encryption key management |
| **Amazon SNS** | Notifications | Alert notifications |
| **Amazon EventBridge** | Event bus | Event routing and scheduling |

### Programming and Tools

| Tool | Purpose |
|------|---------|
| **Python 3.9+** | Data processing and Lambda functions |
| **Boto3** | AWS SDK for Python |
| **Pandas** | Data manipulation and analysis |
| **PySpark** | Glue ETL transformations |
| **SQL** | Athena queries and analytics |
| **AWS CLI** | Command-line AWS management |
| **Git** | Version control |
| **CloudFormation/Terraform** | Infrastructure as Code |
| **pytest** | Testing framework |
| **JSON/YAML** | Configuration files |

### Data Formats

| Format | Use Case |
|--------|----------|
| **Parquet** | Columnar storage for analytics (Curated zone) |
| **JSON** | Semi-structured data ingestion (Raw zone) |
| **CSV** | Simple tabular data |
| **Avro** | Schema evolution scenarios |

---

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                            │
├─────────────────────────────────────────────────────────────────┤
│  Orders DB  │  Clickstream  │  Products API  │  Customer Data   │
└──────┬──────┴──────┬────────┴────────┬───────┴───────┬──────────┘
       │             │                 │                │
       ▼             ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER (Lambda)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Validator│  │  Parser  │  │ Enricher │  │  Router  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER (S3)                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   RAW ZONE     │  │ PROCESSED ZONE │  │  CURATED ZONE  │   │
│  │   (Landing)    │→│   (Cleansed)   │→│  (Analytics)   │   │
│  │   JSON/CSV     │  │     Parquet    │  │    Parquet     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              CATALOGING LAYER (Glue Data Catalog)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Crawlers │→│  Tables  │→│  Schemas │→│Partitions│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               TRANSFORMATION LAYER (Glue ETL)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Bronze→Silver │→│Silver→Gold   │→│ Aggregations │         │
│  │  Cleansing   │  │  Enrichment  │  │   Analytics  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ANALYTICS LAYER (Athena)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQL Queries  │  Business Reports  │  Ad-Hoc Analysis  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           MONITORING LAYER (CloudWatch + SNS)                   │
│  Metrics  │  Logs  │  Dashboards  │  Alarms  │  Notifications  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion:** Data arrives from multiple sources → Lambda validates and routes to S3 Raw zone
2. **Cataloging:** Glue Crawlers discover schemas → Update Data Catalog
3. **Transformation:** Glue ETL jobs process data → Move through Bronze → Silver → Gold zones
4. **Analytics:** Athena queries S3 data using Glue Catalog → Business insights
5. **Monitoring:** CloudWatch tracks all activities → Alerts on anomalies

### Architecture Principles

- ✅ **Serverless-First:** No servers to manage, automatic scaling
- ✅ **Event-Driven:** Reactive processing triggered by data arrival
- ✅ **Pay-Per-Use:** Pay only for what you consume
- ✅ **Decoupled:** Services communicate through events, not direct calls
- ✅ **Scalable:** Handles growth from GB to PB seamlessly
- ✅ **Secure:** Encryption, IAM, and audit logging throughout
- ✅ **Cost-Optimized:** Leverages Free Tier and efficient storage

---

## ✅ Success Criteria

You will successfully complete this checkpoint when:

### Infrastructure (20 points)

- [ ] All S3 buckets created with proper naming and structure
- [ ] IAM roles and policies configured with least privilege
- [ ] CloudFormation/Terraform templates deploy without errors
- [ ] All resources properly tagged for cost tracking
- [ ] Encryption enabled on all data at rest
- [ ] Bucket versioning and lifecycle policies configured
- [ ] VPC endpoints configured (if required)

### Data Ingestion (15 points)

- [ ] Lambda functions deployed for each data source
- [ ] S3 event notifications configured correctly
- [ ] Data validation logic implemented
- [ ] Error handling and retry logic working
- [ ] Dead letter queue configured for failed messages
- [ ] CloudWatch logs enabled for all Lambda functions

### Data Cataloging (15 points)

- [ ] Glue Data Catalog created with all database schemas
- [ ] Glue Crawlers configured for Raw, Processed, and Curated zones
- [ ] Crawlers run successfully and update catalog
- [ ] Table schemas match expected data structures
- [ ] Partitioning strategy implemented correctly
- [ ] Schema evolution handled appropriately

### ETL Pipelines (20 points)

- [ ] Bronze layer: Raw data ingested without transformation
- [ ] Silver layer: Data cleansed, validated, and deduplicated
- [ ] Gold layer: Business-ready aggregated datasets
- [ ] Glue ETL jobs written in PySpark
- [ ] Data quality checks implemented at each layer
- [ ] Incremental processing working (not full refresh)
- [ ] Error handling and logging implemented

### Analytics (15 points)

- [ ] Athena workgroup configured with query results location
- [ ] All required SQL queries execute successfully
- [ ] Query performance optimized (partitioning, file formats)
- [ ] Views created for common business queries
- [ ] Saved queries documented for business users
- [ ] Query costs estimated and optimized

### Monitoring & Operations (10 points)

- [ ] CloudWatch dashboard created with key metrics
- [ ] Alarms configured for critical failures
- [ ] SNS topic created for alert notifications
- [ ] Cost monitoring alerts configured
- [ ] Lambda function metrics tracked
- [ ] Data pipeline health monitored

### Documentation (10 points)

- [ ] Architecture diagrams created (infrastructure, data flow)
- [ ] README with setup instructions completed
- [ ] Architecture Decision Records (ADRs) documented
- [ ] Operational runbook created
- [ ] Code commented and well-structured
- [ ] Cost estimation documented

### Testing & Validation (5 points)

- [ ] All automated tests pass
- [ ] End-to-end data flow verified
- [ ] Sample data processed successfully
- [ ] Business queries return expected results
- [ ] Performance meets requirements

### Bonus Points (10 points available)

- [ ] CI/CD pipeline implemented (+3 points)
- [ ] Data quality dashboard created (+2 points)
- [ ] Advanced partitioning strategy (+2 points)
- [ ] Multi-region setup (+3 points)

---

## 🚀 Getting Started

### Step 1: Watch Orientation Videos

1. **Project Walkthrough** (15 minutes): Overview of architecture and requirements
2. **Demo: Working Solution** (20 minutes): See the final product in action
3. **Common Pitfalls** (10 minutes): Learn from others' mistakes

### Step 2: Review Documentation

Read these files in order:

1. **`PROJECT-BRIEF.md`** (45 minutes)
   - Business context and requirements
   - Technical specifications
   - Acceptance criteria

2. **`ARCHITECTURE-DECISIONS.md`** (30 minutes)
   - Key design decisions
   - Technology choices
   - Trade-off analysis

3. **`IMPLEMENTATION-GUIDE.md`** (review structure, 15 minutes)
   - Phase-by-phase breakdown
   - Implementation steps
   - Reference back during development

4. **`COST-ESTIMATION.md`** (20 minutes)
   - Budget and cost breakdown
   - Cost optimization strategies
   - Monitoring setup

### Step 3: Set Up Development Environment

```bash
# Clone or navigate to project directory
cd modules/module-checkpoint-01-serverless-data-lake

# Review project structure
ls -la

# Install Python dependencies
pip install -r requirements.txt

# Configure AWS CLI (if not already done)
aws configure

# Verify AWS credentials
aws sts get-caller-identity

# Check AWS region
aws configure get region
```

### Step 4: Review Starter Template

```bash
# Navigate to starter template
cd starter-template

# Review provided scaffolding
tree -L 3

# Key files to examine:
# - infrastructure/cloudformation/main-template.yaml
# - src/lambda/ingestion/requirements.txt
# - src/glue/transformations/bronze_to_silver.py
# - queries/athena/business_queries.sql
```

### Step 5: Plan Your Approach

1. **Time Management:**
   - Block 20-25 hours over 3-5 days
   - Don't try to complete in one sitting
   - Take breaks between phases

2. **Development Strategy:**
   - Follow the 5-phase implementation order
   - Complete one phase before moving to next
   - Test thoroughly at each phase
   - Document as you go

3. **Create Your Project Plan:**
   ```
   Day 1 (5-6 hours): Phase 1 - Infrastructure Setup
   Day 2 (5-6 hours): Phase 2 - Data Ingestion
   Day 3 (5-6 hours): Phase 3 - Cataloging + Phase 4 - ETL (start)
   Day 4 (5-6 hours): Phase 4 - ETL (complete) + Phase 5 - Analytics
   Day 5 (2-3 hours): Testing, Documentation, Final Validation
   ```

### Step 6: Set Up Version Control

```bash
# Initialize git (if not already)
git init

# Create .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# AWS
.aws/
aws-exports.js

# IDE
.vscode/
.idea/

# Terraform
.terraform/
*.tfstate
*.tfstate.*

# Logs
*.log

# OS
.DS_Store
Thumbs.db
EOF

# Make initial commit
git add .
git commit -m "Initial commit: Checkpoint 01 project structure"
```

### Step 7: Begin Phase 1

Open `IMPLEMENTATION-GUIDE.md` and start with **Phase 1: Infrastructure Setup**.

---

## 📅 Project Phases

### Phase 1: Infrastructure Setup (5-6 hours)

**Goal:** Provision all AWS infrastructure using Infrastructure as Code

**Tasks:**
- Create S3 buckets (raw, processed, curated, scripts, logs)
- Configure bucket policies and encryption
- Create IAM roles for Lambda, Glue, and Athena
- Set up CloudWatch log groups
- Deploy CloudFormation/Terraform templates
- Tag all resources

**Deliverables:**
- Infrastructure code (CloudFormation/Terraform)
- S3 bucket structure documented
- IAM policies documented
- Successful deployment screenshot

**Validation:**
```bash
# All buckets exist
aws s3 ls | grep cloudmart

# IAM roles created
aws iam list-roles | grep cloudmart

# CloudFormation stack deployed
aws cloudformation describe-stacks --stack-name cloudmart-data-lake
```

### Phase 2: Data Ingestion (4-5 hours)

**Goal:** Implement Lambda functions to ingest and validate data

**Tasks:**
- Write Lambda function for order data ingestion
- Write Lambda function for clickstream data ingestion
- Write Lambda function for product data ingestion
- Implement data validation logic
- Configure S3 event triggers
- Set up error handling and DLQ
- Write unit tests

**Deliverables:**
- Lambda function code (Python)
- Event trigger configurations
- Unit tests
- Sample data loaded to S3 raw zone

**Validation:**
```bash
# Upload test file
aws s3 cp test-order.json s3://cloudmart-raw/orders/

# Check Lambda execution
aws logs tail /aws/lambda/cloudmart-ingest-orders --follow

# Verify data in raw zone
aws s3 ls s3://cloudmart-raw/orders/year=2024/month=03/
```

### Phase 3: Data Cataloging (3-4 hours)

**Goal:** Set up Glue Data Catalog and Crawlers

**Tasks:**
- Create Glue Database
- Configure Glue Crawler for raw zone
- Run crawler and verify tables
- Configure crawlers for processed and curated zones
- Set up crawler schedules
- Verify schema in Data Catalog

**Deliverables:**
- Glue database and tables
- Crawler configurations
- Schedule definitions
- Data Catalog screenshot

**Validation:**
```bash
# List databases
aws glue get-databases

# List tables in database
aws glue get-tables --database-name cloudmart_raw

# Get table schema
aws glue get-table --database-name cloudmart_raw --name orders
```

### Phase 4: Data Transformation (6-7 hours)

**Goal:** Build ETL pipelines to transform data through lakehouse zones

**Tasks:**
- Implement Bronze → Silver transformation (cleansing)
- Implement Silver → Gold transformation (aggregation)
- Add data quality checks
- Configure Glue job parameters
- Implement incremental processing
- Set up job scheduling
- Test with sample data

**Deliverables:**
- Glue ETL scripts (PySpark)
- Data quality validation logic
- Job configurations
- Transformed data in processed and curated zones
- Test results

**Validation:**
```bash
# Run Glue ETL job
aws glue start-job-run --job-name cloudmart-bronze-to-silver

# Check job status
aws glue get-job-run --job-name cloudmart-bronze-to-silver --run-id <run-id>

# Verify transformed data
aws s3 ls s3://cloudmart-processed/orders/
aws s3 ls s3://cloudmart-curated/orders_daily_summary/
```

### Phase 5: Analytics (3-4 hours)

**Goal:** Enable SQL analytics with Athena

**Tasks:**
- Create Athena workgroup
- Write SQL queries for business insights
- Create views for common queries
- Optimize query performance
- Document query patterns
- Create sample dashboard visualization

**Deliverables:**
- Athena workgroup configuration
- SQL queries (10+ business queries)
- View definitions
- Query optimization notes
- Sample query results

**Validation:**
```bash
# Run Athena query
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM cloudmart_curated.orders_daily_summary" \
  --result-configuration "OutputLocation=s3://cloudmart-athena-results/"

# Get query results
aws athena get-query-results --query-execution-id <execution-id>
```

---

## 📁 Project Structure

```
module-checkpoint-01-serverless-data-lake/
│
├── README.md                          # This file
├── PROJECT-BRIEF.md                   # Detailed project requirements
├── IMPLEMENTATION-GUIDE.md            # Step-by-step implementation guide
├── ARCHITECTURE-DECISIONS.md          # Design decisions documentation
├── COST-ESTIMATION.md                 # Cost breakdown and optimization
│
├── architecture/                      # Architecture diagrams
│   ├── infrastructure-diagram.md      # Infrastructure architecture
│   ├── data-flow-diagram.md           # Data flow visualization
│   └── security-model.md              # Security architecture
│
├── starter-template/                  # Scaffold to get you started
│   ├── infrastructure/
│   │   ├── cloudformation/            # CloudFormation templates
│   │   │   ├── main-template.yaml
│   │   │   ├── s3-buckets.yaml
│   │   │   ├── iam-roles.yaml
│   │   │   └── glue-resources.yaml
│   │   └── terraform/                 # Terraform alternative
│   │       ├── main.tf
│   │       ├── s3.tf
│   │       ├── iam.tf
│   │       └── glue.tf
│   ├── src/
│   │   ├── lambda/                    # Lambda function code
│   │   │   ├── ingestion/
│   │   │   │   ├── orders_ingestion.py
│   │   │   │   ├── clickstream_ingestion.py
│   │   │   │   └── requirements.txt
│   │   │   └── validation/
│   │   │       ├── data_validator.py
│   │   │       └── schema_definitions.py
│   │   ├── glue/                      # Glue ETL scripts
│   │   │   ├── transformations/
│   │   │   │   ├── bronze_to_silver.py
│   │   │   │   ├── silver_to_gold.py
│   │   │   │   └── data_quality.py
│   │   │   └── crawlers/
│   │   │       └── crawler_config.json
│   │   └── utils/                     # Shared utilities
│   │       ├── logging_config.py
│   │       ├── s3_helper.py
│   │       └── constants.py
│   ├── queries/
│   │   └── athena/                    # Athena SQL queries
│   │       ├── business_queries.sql
│   │       ├── views.sql
│   │       └── optimization_queries.sql
│   ├── tests/                         # Test files
│   │   ├── unit/
│   │   │   ├── test_lambda_ingestion.py
│   │   │   └── test_data_validator.py
│   │   └── integration/
│   │       └── test_etl_pipeline.py
│   └── docs/
│       ├── SETUP.md                   # Setup instructions
│       └── RUNBOOK.md                 # Operational runbook
│
├── reference-solution/                # Complete reference implementation
│   ├── infrastructure/
│   ├── src/
│   ├── queries/
│   ├── tests/
│   └── docs/
│       └── SOLUTION-EXPLANATION.md
│
├── data/                              # Sample data files
│   ├── input/                         # Sample input data
│   │   ├── orders.json
│   │   ├── customers.csv
│   │   ├── products.json
│   │   └── clickstream.json
│   └── expected/                      # Expected transformation outputs
│       ├── silver_orders.parquet
│       └── gold_daily_summary.parquet
│
├── validation/                        # Automated acceptance tests
│   ├── test_infrastructure.py         # Validate infrastructure setup
│   ├── test_data_pipeline.py          # Validate data flow
│   ├── test_data_quality.py           # Validate data quality
│   └── test_queries.py                # Validate analytics queries
│
├── extensions/                        # Optional advanced challenges
│   ├── cicd-pipeline/                 # CI/CD automation
│   ├── data-quality-dashboard/        # Advanced monitoring
│   ├── multi-region/                  # Multi-region setup
│   └── ml-integration/                # ML model integration
│
└── requirements.txt                   # Python dependencies
```

---

## 📦 Deliverables

### Required Deliverables

1. **Infrastructure Code**
   - CloudFormation or Terraform templates
   - Parameterized and reusable
   - Well-commented
   - Version controlled

2. **Lambda Functions**
   - Python code for all ingestion functions
   - Unit tests with >80% coverage
   - Requirements.txt with dependencies
   - Deployment packages ready

3. **Glue ETL Scripts**
   - PySpark code for transformations
   - Bronze → Silver → Gold pipelines
   - Data quality checks
   - Error handling

4. **Athena Queries**
   - Minimum 10 business queries
   - Views for common patterns
   - Optimization notes
   - Expected results documented

5. **Documentation**
   - Architecture diagrams (infrastructure + data flow)
   - Setup instructions
   - Operational runbook
   - Architecture Decision Records (ADRs)
   - Code comments

6. **Testing Results**
   - All automated tests passing
   - Test coverage report
   - Manual test scenarios documented
   - Screenshots of working system

7. **Cost Analysis**
   - Monthly cost estimate
   - Cost breakdown by service
   - Optimization recommendations
   - Actual costs incurred

8. **Presentation**
   - 10-minute video demo or write-up
   - Architecture overview
   - Key implementation decisions
   - Challenges and solutions
   - Lessons learned

### Submission Format

```
checkpoint-01-submission/
├── README.md (your project documentation)
├── infrastructure/ (all IaC code)
├── src/ (all application code)
├── queries/ (all SQL queries)
├── tests/ (all test code)
├── docs/
│   ├── architecture-diagrams/
│   ├── RUNBOOK.md
│   └── ADR/
├── screenshots/
│   ├── infrastructure-deployed.png
│   ├── data-flow-working.png
│   ├── athena-queries.png
│   └── cloudwatch-dashboard.png
├── test-results/
│   ├── test-output.txt
│   └── coverage-report.html
└── SUBMISSION.md (summary and reflection)
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Lambda Functions Timing Out

**Symptoms:**
- Lambda execution exceeds 15-second timeout
- Data not appearing in S3

**Solutions:**
```python
# Increase Lambda timeout in CloudFormation
Timeout: 60  # seconds

# Process data in batches
def process_batch(records, batch_size=100):
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        process(batch)

# Use Lambda Layers for dependencies
# Don't bundle large libraries in deployment package
```

#### Issue 2: Glue Crawler Not Finding Data

**Symptoms:**
- Crawler completes but no tables created
- Tables created with empty schemas

**Solutions:**
- Verify S3 path is exactly correct (case-sensitive)
- Ensure data files exist in the S3 path
- Check IAM permissions for Glue to read S3
- Verify file format is recognized (JSON, CSV, Parquet)

```bash
# Check S3 path
aws s3 ls s3://your-bucket/your-prefix/ --recursive

# Verify Glue role permissions
aws iam get-role --role-name AWSGlueServiceRole-CloudMart

# Test crawler with single file first
```

#### Issue 3: Athena Query Fails with "Access Denied"

**Symptoms:**
- Query execution fails immediately
- Error: "Access Denied" or "Insufficient permissions"

**Solutions:**
- Verify Athena has permissions to read S3 buckets
- Check query results S3 location permissions
- Ensure Glue Data Catalog permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-*/*",
        "arn:aws:s3:::cloudmart-*"
      ]
    }
  ]
}
```

#### Issue 4: High AWS Costs

**Symptoms:**
- Costs exceeding $50/month budget
- Unexpected charges

**Solutions:**
- Check S3 storage class (use Standard-IA for infrequent access)
- Verify Glue jobs aren't running continuously
- Review CloudWatch Logs retention period
- Check for orphaned resources

```bash
# Review current costs
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-09 \
  --granularity DAILY \
  --metrics BlendedCost

# List all S3 buckets and sizes
aws s3 ls
aws cloudwatch get-metric-statistics --namespace AWS/S3 \
  --metric-name BucketSizeBytes --dimensions Name=BucketName,Value=YOUR_BUCKET \
  --statistics Average --start-time 2026-03-01T00:00:00Z \
  --end-time 2026-03-09T00:00:00Z --period 86400
```

#### Issue 5: Data Quality Issues

**Symptoms:**
- Duplicate records in Silver layer
- Incorrect aggregations in Gold layer
- Schema mismatches

**Solutions:**
- Implement deduplication logic
- Add data validation checks
- Test with small datasets first

```python
# Deduplication in PySpark
from pyspark.sql import Window
from pyspark.sql.functions import row_number

# Deduplicate by ID, keeping latest timestamp
window = Window.partitionBy("order_id").orderBy(col("timestamp").desc())
deduped_df = df.withColumn("row_num", row_number().over(window)) \
               .filter(col("row_num") == 1) \
               .drop("row_num")
```

### Getting Help

1. **Review Module Materials:** Modules 01-06 contain relevant examples
2. **Check AWS Documentation:** Official AWS docs are comprehensive
3. **Use AWS Support Forums:** Community support available
4. **Office Hours:** Weekly checkpoint office hours (schedule TBD)
5. **Debugging Tips:**
   - Enable verbose logging
   - Test components independently
   - Use AWS CloudWatch Insights for log analysis
   - Check AWS Service Health Dashboard

---

## 📚 Resources

### AWS Documentation

- [Amazon S3 User Guide](https://docs.aws.amazon.com/s3/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/)
- [Amazon Athena User Guide](https://docs.aws.amazon.com/athena/)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)

### Best Practices and Patterns

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Data Lakes and Analytics on AWS](https://aws.amazon.com/big-data/datalakes-and-analytics/)
- [Serverless Data Processing](https://aws.amazon.com/blogs/big-data/)
- [AWS Prescriptive Guidance](https://aws.amazon.com/prescriptive-guidance/)

### Code Examples

- [AWS Samples - Data Lake](https://github.com/aws-samples/aws-data-lake-solution)
- [AWS Glue Samples](https://github.com/aws-samples/aws-glue-samples)
- [AWS Lambda Samples](https://github.com/aws-samples/aws-lambda-sample-applications)

### Tools and Utilities

- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [AWS CDK (TypeScript/Python)](https://docs.aws.amazon.com/cdk/)

### Video Tutorials

- AWS re:Invent Sessions on Data Lakes
- AWS Online Tech Talks
- AWS Workshops (hands-on labs)

### Books and Articles

- "Data Engineering on AWS" by Amazon Press
- "Building Data Lakes on AWS"
- AWS Architecture Blog posts

---

## 🎓 Next Steps

### After Completing This Checkpoint

1. **Self-Assessment**
   - Review your solution against the grading rubric
   - Identify areas for improvement
   - Document lessons learned

2. **Code Review**
   - Review reference solution
   - Compare approaches
   - Note alternative implementations

3. **Clean Up Resources**
   ```bash
   # Delete CloudFormation stack
   aws cloudformation delete-stack --stack-name cloudmart-data-lake

   # Empty and delete S3 buckets
   aws s3 rm s3://cloudmart-raw --recursive
   aws s3 rb s3://cloudmart-raw

   # Verify all resources deleted
   aws s3 ls | grep cloudmart
   aws lambda list-functions | grep cloudmart
   ```

4. **Portfolio Development**
   - Add project to your GitHub portfolio
   - Write a blog post about your experience
   - Create a presentation for your network
   - Update your resume/LinkedIn

### Optional Extensions

If you want to go deeper:

1. **CI/CD Pipeline** (see `extensions/cicd-pipeline/`)
   - Automated testing on commit
   - Infrastructure deployment automation
   - Blue-green deployments

2. **Advanced Monitoring** (see `extensions/data-quality-dashboard/`)
   - Custom CloudWatch dashboard
   - Data quality metrics visualization
   - Anomaly detection alerts

3. **Multi-Region Setup** (see `extensions/multi-region/`)
   - S3 cross-region replication
   - Multi-region Athena queries
   - Disaster recovery strategy

4. **ML Integration** (see `extensions/ml-integration/`)
   - SageMaker model training
   - Real-time inference
   - Batch predictions

### Prepare for Next Checkpoints

- **Checkpoint 02: Real-Time Analytics Platform**
  - Build on this data lake
  - Add streaming with Kinesis
  - Real-time dashboards

- **Checkpoint 03: Enterprise Data Lakehouse**
  - Scale to production
  - Advanced governance
  - Multi-tenant architecture

### Continue Learning

- **Module 07:** Batch Processing (Spark, EMR)
- **Module 08:** Streaming Basics (Kinesis, Kafka)
- **Module 09:** Data Quality (Great Expectations, Deequ)
- **Module 10:** Workflow Orchestration (Step Functions, Airflow)

---

## 🎯 Final Checklist

Before submitting, verify:

- [ ] All phases completed (1-5)
- [ ] All acceptance tests passing
- [ ] Documentation complete
- [ ] Code committed to Git
- [ ] AWS resources deployed
- [ ] Costs within budget ($50/month)
- [ ] Screenshots captured
- [ ] Video demo recorded or write-up completed
- [ ] Reflection on learning (SUBMISSION.md)
- [ ] All deliverables in submission folder
- [ ] Ready for review

---

## 📞 Support

- **Technical Questions:** Office hours (check schedule)
- **AWS Issues:** AWS Support Forums or AWS Support (if you have a plan)
- **Project Clarifications:** GitHub Discussions
- **Emergency Issues:** Contact instructor via email

---

## 🏆 Evaluation

Your checkpoint will be evaluated on:

1. **Completeness** (40%): All requirements implemented
2. **Correctness** (25%): Solution works as specified
3. **Code Quality** (15%): Clean, well-structured, documented code
4. **Best Practices** (10%): Follows AWS and software engineering best practices
5. **Documentation** (10%): Clear and comprehensive documentation

**Passing Score:** 70/100 points

---

## 📝 License

This project is part of the Cloud Data Engineering Training Program.
Materials are for educational use only.

---

**Good luck! You're going to build something amazing! 🚀**

Remember: This is a learning experience. Don't be afraid to experiment, make mistakes, and ask questions. The journey is as important as the destination.

Now, head over to `PROJECT-BRIEF.md` to dive into the detailed requirements!
