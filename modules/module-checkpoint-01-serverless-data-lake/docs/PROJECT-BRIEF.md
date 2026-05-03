# 📋 PROJECT BRIEF: CloudMart Serverless Data Lake

## Document Control

| Attribute | Value |
|-----------|-------|
| **Project Name** | CloudMart Serverless Data Lake |
| **Project Code** | CHECKPOINT-01-SDL |
| **Version** | 1.0 |
| **Last Updated** | March 2026 |
| **Document Owner** | Cloud Data Engineering Training |
| **Status** | Active |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Context](#business-context)
3. [Current State Analysis](#current-state-analysis)
4. [Project Objectives](#project-objectives)
5. [Technical Requirements](#technical-requirements)
6. [Data Sources](#data-sources)
7. [Data Lake Architecture](#data-lake-architecture)
8. [Deliverables](#deliverables)
9. [Acceptance Criteria](#acceptance-criteria)
10. [Non-Functional Requirements](#non-functional-requirements)
11. [Security and Compliance](#security-and-compliance)
12. [Timeline and Milestones](#timeline-and-milestones)
13. [Grading Rubric](#grading-rubric)
14. [Assumptions and Constraints](#assumptions-and-constraints)

---

## 1. Executive Summary

### 1.1 Project Overview

**CloudMart**, a rapidly growing e-commerce platform, requires a modern, serverless data lake solution to consolidate data from multiple operational systems and enable advanced analytics capabilities. The current data infrastructure is fragmented, making it difficult for business teams to access data and derive insights efficiently.

This project will design and implement a **serverless data lake on AWS**, leveraging services including S3, Lambda, Glue, Athena, and CloudWatch. The solution will follow a medallion architecture (Bronze, Silver, Gold layers) to ensure data quality and enable progressive data refinement.

### 1.2 Business Value

**Expected Benefits:**
- **90% reduction** in analytics infrastructure costs (from traditional data warehouse)
- **From days to minutes:** Time-to-insight improvement
- **Self-service analytics:** Enable 50+ business users to query data independently
- **Data democratization:** Unified view of customer journey and business metrics
- **Scalability:** Handle 10x data growth without infrastructure changes
- **Foundation for ML:** Enable predictive analytics and recommendation engines

**ROI Projection:**
- Infrastructure cost savings: $300K annually
- Analyst productivity improvement: 40 hours/week reclaimed
- Faster decision-making: Estimated $500K in revenue opportunities

### 1.3 Project Scope

**In Scope:**
- ✅ Serverless data lake infrastructure on AWS
- ✅ Data ingestion from 4 primary data sources
- ✅ Automated data cataloging and schema management
- ✅ ETL pipelines for data transformation (Bronze → Silver → Gold)
- ✅ SQL analytics interface via Amazon Athena
- ✅ Monitoring, logging, and alerting
- ✅ Cost optimization and budget controls
- ✅ Documentation and operational runbooks

**Out of Scope:**
- ❌ Real-time streaming pipelines (future phase - Checkpoint 02)
- ❌ Machine learning model deployment (future phase)
- ❌ Business intelligence dashboards (integration only)
- ❌ Migration of historical data (>2 years old)
- ❌ Data governance tooling (future phase - Checkpoint 03)
- ❌ Multi-region deployment (optional extension)

---

## 2. Business Context

### 2.1 Company Background

**CloudMart** is a global e-commerce marketplace founded in 2018, enabling consumers to purchase products from thousands of merchants worldwide.

**Key Statistics (2025):**
- **Monthly Active Users:** 500,000+
- **Daily Transactions:** 50,000+
- **Product Catalog:** 100,000+ SKUs
- **Merchant Partners:** 2,000+
- **Geographic Presence:** 25 countries
- **Annual Revenue:** $150M (projected 2026)
- **Year-over-Year Growth:** 45%
- **Employee Count:** 250

**Business Model:**
- Direct sales (75% of revenue)
- Marketplace commissions (20% of revenue)
- Subscription services (5% of revenue)

### 2.2 Organizational Structure

**Key Stakeholders:**

1. **Sarah Chen - Chief Data Officer (CDO)**
   - Project sponsor and executive champion
   - Budget approval authority
   - Strategic alignment oversight

2. **Michael Rodriguez - VP of Engineering**
   - Technical leadership and architecture approval
   - DevOps and infrastructure decision-making
   - Quality and security standards enforcement

3. **Priya Sharma - Head of Business Intelligence**
   - Primary end-user representative
   - Business requirements definition
   - Analytics use case validation

4. **David Kim - Director of Data Engineering**
   - Your direct manager
   - Day-to-day project oversight
   - Technical mentorship and reviews

5. **Lisa Thompson - VP of Finance**
   - Budget monitoring and cost control
   - Financial reporting requirements
   - Compliance and audit liaison

**Business Users (50+ people):**
- Product managers
- Marketing analysts
- Finance analysts
- Operations managers
- Customer success teams

### 2.3 Strategic Drivers

**Why Now?**

1. **Business Growth:** 45% YoY growth is straining existing systems
2. **Competitive Pressure:** Competitors have advanced analytics capabilities
3. **Customer Expectations:** Users expect personalized experiences
4. **Regulatory Requirements:** Increasing data governance requirements
5. **Cost Pressures:** Current analytics infrastructure costs $400K/year
6. **Technical Debt:** Legacy systems built 4 years ago need modernization

**Strategic Initiatives Enabled:**
- Personalized product recommendations
- Dynamic pricing optimization
- Customer churn prediction
- Inventory optimization
- Marketing campaign effectiveness
- Fraud detection
- Supply chain analytics

---

## 3. Current State Analysis

### 3.1 Existing Data Infrastructure

**Current Architecture Problems:**

1. **Transactional Database (Amazon RDS PostgreSQL)**
   - **Purpose:** Orders, customers, products, inventory
   - **Size:** 500GB
   - **Issues:**
     - Analytics queries compete with operational workload
     - Read replicas are expensive and lag behind
     - No historical data retention (only 90 days)
     - Complex joins slow down applications

2. **Application Logs (Amazon S3)**
   - **Purpose:** User clickstream, application events
   - **Size:** 2TB
   - **Issues:**
     - Unstructured JSON logs
     - No cataloging or querying capability
     - Manual downloads required for analysis
     - Inconsistent schemas across application versions

3. **Marketing Platform (Salesforce)**
   - **Purpose:** Campaign data, lead tracking
   - **Size:** 50GB
   - **Issues:**
     - Isolated system with no data integration
     - Manual CSV exports weekly
     - No correlation with transaction data
     - Limited API access for automation

4. **Customer Service System (Zendesk)**
   - **Purpose:** Support tickets, CSAT scores
   - **Size:** 100GB
   - **Issues:**
     - No linkage to customer purchase history
     - Unable to analyze service impact on retention
     - Reporting capabilities are limited
     - Data export is cumbersome

### 3.2 Current Analytics Process

**Today's Workflow (Painful):**

1. Business analyst requests data (via Jira ticket)
2. Data engineer manually extracts data from multiple systems (4-8 hours)
3. Data loaded into Excel or local database (2-4 hours)
4. Data cleaning and joining (4-8 hours)
5. Analysis performed (variable time)
6. Results delivered (3-5 days total time)

**Problems:**
- ⏱️ Slow turnaround time (3-5 days average)
- 🔄 No refresh capability (outdated immediately)
- 🤷 No self-service (bottleneck on data engineers)
- 💰 High labor cost (40% of engineering time)
- 🔍 Limited data access (only engineers can extract)
- 📊 No standardization (different analysts get different results)
- 🔐 Security gaps (data emailed, stored locally)

### 3.3 Pain Points Summary

**Top 10 Pain Points (ranked by business impact):**

1. **Slow time-to-insight** (days instead of minutes)
2. **Inability to correlate data** across systems
3. **No historical trend analysis** (90-day retention limit)
4. **Manual, error-prone processes** for data extraction
5. **Bottleneck on data engineering team** (backlog of 30+ requests)
6. **Inconsistent data definitions** across departments
7. **No data quality monitoring** (trust issues)
8. **High infrastructure costs** ($400K/year for analytics)
9. **Limited scalability** (can't handle data growth)
10. **Security and compliance risks** (uncontrolled data exports)

---

## 4. Project Objectives

### 4.1 Primary Objectives

1. **Consolidate Data Sources**
   - Ingest data from 4 primary systems into unified data lake
   - Automated, scheduled ingestion with minimal manual intervention
   - Preserve data lineage and metadata

2. **Enable Self-Service Analytics**
   - Business users can write SQL queries via Athena
   - Curated, business-ready datasets in Gold layer
   - Query response time <5 seconds for 90% of queries
   - Documentation and training for business users

3. **Reduce Costs**
   - Achieve <$50/month operational cost for MVP
   - Demonstrate 90% cost reduction vs. current state
   - Optimize storage and compute resources

4. **Improve Data Quality**
   - Automated data validation at ingestion
   - Data quality checks in transformation pipelines
   - Monitoring and alerting on data quality issues
   - Documented data quality metrics

5. **Establish Foundation for Advanced Analytics**
   - Scalable architecture supporting future ML workloads
   - Historical data retention (2+ years)
   - Support for both batch and future streaming (Checkpoint 02)
   - API access for external tools (BI dashboards, notebooks)

### 4.2 Key Performance Indicators (KPIs)

**Success Metrics:**

| KPI | Baseline (Current) | Target (After Project) | Measurement Method |
|-----|-------------------|------------------------|-------------------|
| Time-to-Insight | 3-5 days | <1 hour | Survey business users |
| Analytics Cost | $400K/year | <$50K/year | AWS Cost Explorer |
| Data Refresh Frequency | Weekly (manual) | Daily (automated) | Pipeline monitoring |
| Data Engineers' Time on Analytics | 40% (16 hrs/week) | <5% (2 hrs/week) | Time tracking |
| Business User Self-Service | 0% (all requests go through engineering) | 80% of queries | Query logs analysis |
| Query Performance | N/A (no self-service) | <5s for 90% | Athena query logs |
| Data Freshness | 1-7 days old | <24 hours | Data catalog timestamps |
| Data Quality Issues | Unknown (no monitoring) | <1% error rate | Data quality tests |

### 4.3 Business Outcomes

**Expected Outcomes (6 months post-launch):**

1. **Operational Efficiency**
   - 50+ business users query data independently
   - Data engineering team focuses on new features, not requests
   - Automated daily data refreshes eliminate manual work
   - 40 hours/week of analyst time reclaimed

2. **Business Insights**
   - Daily revenue and conversion reports
   - Customer cohort analysis and retention metrics
   - Product performance and inventory insights
   - Marketing campaign effectiveness measurement
   - Cross-selling and upselling opportunities identified

3. **Cost Savings**
   - $350K annual infrastructure cost reduction
   - 80% reduction in data engineering request backlog
   - Elimination of manual data extraction labor

4. **Strategic Capabilities**
   - Foundation for machine learning initiatives
   - Ability to make data-driven decisions in real-time
   - Competitive advantage through advanced analytics

---

## 5. Technical Requirements

### 5.1 Functional Requirements

#### FR-001: Data Ingestion

**Description:** System must automatically ingest data from multiple sources into the Raw (Bronze) zone.

**Requirements:**
- **FR-001.1:** Support ingestion of JSON, CSV, and Parquet formats
- **FR-001.2:** Validate data schema before accepting into data lake
- **FR-001.3:** Reject invalid records to a quarantine/DLQ location
- **FR-001.4:** Partition data by ingestion date (year/month/day)
- **FR-001.5:** Generate metadata for each ingestion batch (timestamp, record count, source)
- **FR-001.6:** Support both event-driven (S3 upload) and scheduled ingestion
- **FR-001.7:** Handle files up to 1GB in size
- **FR-001.8:** Ensure exactly-once semantics (no duplicates)

**Acceptance Test:**
```bash
# Upload test file to S3
aws s3 cp test-orders.json s3://cloudmart-raw/orders/

# Verify ingestion within 1 minute
# Verify data appears in correct partition
# Verify metadata logged to CloudWatch
```

#### FR-002: Data Cataloging

**Description:** System must automatically catalog data and maintain searchable metadata.

**Requirements:**
- **FR-002.1:** Automatically discover schemas from Raw, Processed, and Curated zones
- **FR-002.2:** Run crawlers on schedule (daily for Raw, after ETL for others)
- **FR-002.3:** Maintain table and column-level metadata
- **FR-002.4:** Support schema evolution (new columns, type changes)
- **FR-002.5:** Partition discovery and registration
- **FR-002.6:** Data type inference with >95% accuracy

**Acceptance Test:**
```bash
# Upload new data with additional column
# Run crawler
# Verify new column appears in Data Catalog
# Verify backward compatibility with old queries
```

#### FR-003: Data Transformation (Bronze → Silver)

**Description:** Cleanse and standardize raw data into the Processed (Silver) zone.

**Requirements:**
- **FR-003.1:** Remove duplicate records based on business keys
- **FR-003.2:** Standardize data types (dates, numeric fields)
- **FR-003.3:** Handle null and missing values appropriately
- **FR-003.4:** Validate referential integrity (e.g., orders reference valid customers)
- **FR-003.5:** Add derived columns (e.g., year, month from timestamp)
- **FR-003.6:** Filter out test/invalid data
- **FR-003.7:** Convert to Parquet format for efficiency
- **FR-003.8:** Maintain data lineage (source file references)

**Acceptance Test:**
```bash
# Load raw data with known duplicates and issues
# Run Bronze → Silver ETL
# Verify duplicates removed
# Verify data types corrected
# Verify Parquet files created
```

#### FR-004: Data Transformation (Silver → Gold)

**Description:** Create business-ready aggregated datasets in the Curated (Gold) zone.

**Requirements:**
- **FR-004.1:** Daily order summary (revenue, order count, average order value)
- **FR-004.2:** Customer lifetime value and purchase history
- **FR-004.3:** Product performance metrics (views, sales, conversion rate)
- **FR-004.4:** Geographic sales analysis
- **FR-004.5:** Time-series aggregations (daily, weekly, monthly)
- **FR-004.6:** Incremental updates (not full refresh)
- **FR-004.7:** Business logic validation (e.g., revenue = sum(order_items))

**Acceptance Test:**
```bash
# Run Silver → Gold ETL
# Query daily summary in Athena
# Verify aggregations match source data
# Verify incremental processing (only new dates)
```

#### FR-005: SQL Analytics

**Description:** Enable business users to query data using SQL via Amazon Athena.

**Requirements:**
- **FR-005.1:** All Gold tables queryable via Athena
- **FR-005.2:** Query response time <5 seconds for 90% of business queries
- **FR-005.3:** Support for common SQL operations (joins, aggregations, window functions)
- **FR-005.4:** Saved queries for common business reports
- **FR-005.5:** Views for simplified data access
- **FR-005.6:** Query result caching for repeated queries
- **FR-005.7:** Cost estimation before query execution

**Acceptance Test:**
```sql
-- Execute 10 standard business queries
-- Measure query execution time
-- Verify results accuracy
-- Confirm cost within budget (<$5 per TB scanned)
```

#### FR-006: Monitoring and Alerting

**Description:** Monitor data pipeline health and alert on failures or anomalies.

**Requirements:**
- **FR-006.1:** CloudWatch dashboard showing pipeline status
- **FR-006.2:** Alarms for Lambda function failures
- **FR-006.3:** Alarms for Glue job failures
- **FR-006.4:** Data quality alerts (e.g., record count drop >20%)
- **FR-006.5:** Cost alerts if spending exceeds budget
- **FR-006.6:** Email notifications via SNS for critical issues
- **FR-006.7:** Daily health check summary

**Acceptance Test:**
```bash
# Simulate Lambda failure
# Verify CloudWatch alarm triggers
# Verify SNS notification sent
# Verify visible in dashboard
```

### 5.2 Non-Functional Requirements

#### NFR-001: Performance

- **Data Ingestion Latency:** <1 minute from file upload to availability in Raw zone
- **ETL Processing Time:** Bronze → Silver in <10 minutes for daily batch
- **Query Response Time:** <5 seconds for 90% of Athena queries on Gold tables
- **Data Freshness:** Data available for querying within 24 hours of generation
- **Concurrent Users:** Support 50+ simultaneous Athena users

#### NFR-002: Scalability

- **Data Volume Growth:** Handle 10x data growth (2TB → 20TB) without architecture changes
- **User Growth:** Support 100+ concurrent Athena users
- **Throughput:** Process 1M records/day with room to grow to 10M
- **File Size:** Handle files up to 5GB (current max: 500MB)

#### NFR-003: Availability

- **Uptime:** 99.9% availability for query access (downtime <43 minutes/month)
- **Data Durability:** 99.999999999% (11 nines) via S3
- **Recovery Time Objective (RTO):** <1 hour to recover from failure
- **Recovery Point Objective (RPO):** <24 hours of data loss acceptable

#### NFR-004: Security

- **Encryption at Rest:** All S3 buckets encrypted using AWS KMS
- **Encryption in Transit:** TLS 1.2+ for all API calls
- **Access Control:** Role-based access (RBAC) via IAM
- **Least Privilege:** All service roles follow principle of least privilege
- **Audit Logging:** CloudTrail enabled for all API calls
- **Data Isolation:** Development and production environments separated

#### NFR-005: Cost

- **Monthly Budget:** <$50/month for MVP phase
- **Cost Per Query:** <$0.01 per typical analytic query
- **Storage Cost:** <$30/month for 2TB of data
- **Compute Cost:** <$20/month for Lambda and Glue execution
- **Cost Monitoring:** Automated budget alerts at 80% threshold

#### NFR-006: Maintainability

- **Infrastructure as Code:** 100% of infrastructure defined in code (CloudFormation/Terraform)
- **Code Documentation:** All functions and scripts documented
- **Operational Runbook:** Step-by-step procedures for common operations
- **Versioning:** All code in Git with semantic versioning
- **Testability:** Unit tests for Lambda functions (>80% coverage)

#### NFR-007: Usability

- **Self-Service:** Business users can query without engineering help
- **Documentation:** User guide for common analytics tasks
- **Query Templates:** 10+ saved queries for common use cases
- **Error Messages:** Clear, actionable error messages
- **Training:** Training materials and workshops for business users

---

## 6. Data Sources

### 6.1 Source System Inventory

#### Source 1: Orders Database (RDS PostgreSQL)

**Description:** Production transactional database containing orders, customers, and products

**Owner:** Engineering Team
**Update Frequency:** Real-time
**Export Frequency:** Daily at 2:00 AM UTC
**Export Method:** Automated SQL export to S3

**Schema:**

**Orders Table:**
```sql
CREATE TABLE orders (
    order_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,
    order_date TIMESTAMP NOT NULL,
    order_status VARCHAR(20),  -- pending, confirmed, shipped, delivered, cancelled
    total_amount DECIMAL(10,2),
    currency VARCHAR(3),
    payment_method VARCHAR(20),
    shipping_address_id VARCHAR(36),
    billing_address_id VARCHAR(36),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Order Items Table:**
```sql
CREATE TABLE order_items (
    order_item_id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) REFERENCES orders(order_id),
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    tax_amount DECIMAL(10,2),
    subtotal DECIMAL(10,2)
);
```

**Customers Table:**
```sql
CREATE TABLE customers (
    customer_id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    registration_date DATE,
    customer_segment VARCHAR(20),  -- new, regular, vip, inactive
    country VARCHAR(2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Products Table:**
```sql
CREATE TABLE products (
    product_id VARCHAR(36) PRIMARY KEY,
    product_name VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    inventory_quantity INTEGER,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Characteristics:**
- Volume: ~10K orders/day, ~25K order items/day
- File Format: CSV (gzip compressed)
- Estimated Daily Size: 50MB compressed
- Retention: Export last 7 days of changes

#### Source 2: Clickstream Event Logs (S3)

**Description:** Application logs capturing user interactions and page views

**Owner:** Application Team
**Update Frequency:** Real-time (log buffering every 5 minutes)
**Storage Location:** s3://cloudmart-app-logs/clickstream/
**File Format:** Newline-delimited JSON (NDJSON)

**Event Schema:**
```json
{
  "event_id": "uuid",
  "user_id": "uuid or null (anonymous)",
  "session_id": "uuid",
  "event_type": "page_view | product_view | add_to_cart | remove_from_cart | checkout_start | purchase",
  "event_timestamp": "ISO 8601 timestamp",
  "page_url": "string",
  "referrer_url": "string",
  "product_id": "uuid (nullable)",
  "product_category": "string (nullable)",
  "user_agent": "string",
  "ip_address": "string (anonymized, last octet masked)",
  "device_type": "desktop | mobile | tablet",
  "browser": "string",
  "country": "ISO 2-letter code",
  "ab_test_variant": "string (nullable)",
  "metadata": {
    "search_query": "string (if applicable)",
    "filter_applied": "array (if applicable)",
    "cart_value": "numeric (nullable)"
  }
}
```

**Characteristics:**
- Volume: ~2M events/day
- File Format: NDJSON (gzip compressed)
- File Size: ~10MB per file, 300+ files/day
- Estimated Daily Size: 3GB compressed

#### Source 3: Product Catalog API

**Description:** Real-time product information from inventory management system

**Owner:** Operations Team
**Update Frequency:** Hourly
**Export Method:** REST API → Lambda → S3
**File Format:** JSON

**API Response Schema:**
```json
{
  "catalog_snapshot_timestamp": "ISO 8601 timestamp",
  "products": [
    {
      "product_id": "uuid",
      "sku": "string",
      "product_name": "string",
      "description": "string",
      "category": "string",
      "subcategory": "string",
      "brand": "string",
      "price": "decimal",
      "cost": "decimal",
      "currency": "string",
      "inventory_quantity": "integer",
      "warehouse_location": "string",
      "supplier_id": "string",
      "is_active": "boolean",
      "images": ["array of URLs"],
      "attributes": {
        "color": "string",
        "size": "string",
        "weight_kg": "decimal"
      },
      "updated_at": "ISO 8601 timestamp"
    }
  ]
}
```

**Characteristics:**
- Volume: 100K products
- File Format: JSON
- Estimated Hourly Size: 25MB

#### Source 4: Marketing Campaign Data

**Description:** Campaign performance metrics and customer engagement data

**Owner:** Marketing Team
**Update Frequency:** Daily at 6:00 AM UTC
**Export Method:** Manual CSV export to S3 (to be automated)
**File Format:** CSV

**Schema:**
```csv
campaign_id,campaign_name,start_date,end_date,channel,budget,impressions,clicks,conversions,revenue,customer_id
```

**Characteristics:**
- Volume: ~50 campaigns, ~10K records/day
- File Format: CSV
- Estimated Daily Size: 5MB

### 6.2 Data Volume Projections

**Current State (Month 1):**
- Orders: 10K/day = 300K/month = 50MB/day = 1.5GB/month
- Clickstream: 2M events/day = 60M/month = 3GB/day = 90GB/month
- Products: 100K products x 24 snapshots/day = 25MB x 24 = 600MB/day = 18GB/month
- Marketing: 10K records/day = 5MB/day = 150MB/month

**Total: ~110GB/month raw data**

**6-Month Projection:**
- Orders: 15K/day = 2.25GB/month
- Clickstream: 3M events/day = 135GB/month
- Products: 150K products = 27GB/month
- Marketing: 15K records/day = 225MB/month

**Total: ~165GB/month raw data**

**Storage Estimates:**
- Raw (Bronze): Full data in JSON/CSV = 165GB/month
- Processed (Silver): Parquet = 50GB/month (3:1 compression)
- Curated (Gold): Aggregated = 5GB/month

**Total Storage Month 6: ~220GB cumulative (accounting for 6 months retention)**

---

## 7. Data Lake Architecture

### 7.1 Lakehouse Zones (Medallion Architecture)

#### Zone 1: Raw (Bronze Layer)

**Purpose:** Landing zone for all ingested data in original format

**Characteristics:**
- Immutable: Data never modified after ingestion
- File Format: Original (JSON, CSV, Parquet)
- Partitioning: /source/year/month/day/
- Retention: 90 days (then archived to Glacier)
- Access: Restricted to data engineering team

**Directory Structure:**
```
s3://cloudmart-raw/
├── orders/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               ├── orders_20260309_020000.csv.gz
│               ├── order_items_20260309_020000.csv.gz
│               └── _metadata.json
├── clickstream/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── hour=14/
│                   ├── events_146.json.gz
│                   ├── events_147.json.gz
│                   └── _metadata.json
├── products/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── hour=14/
│                   ├── catalog_20260309_140000.json
│                   └── _metadata.json
└── marketing/
    └── year=2026/
        └── month=03/
            └── day=09/
                ├── campaigns_20260309.csv
                └── _metadata.json
```

**Data Quality:** None (accept all data as-is, validation happens in Silver layer)

#### Zone 2: Processed (Silver Layer)

**Purpose:** Cleansed, validated, and standardized data ready for analysis

**Characteristics:**
- Cleansed: Duplicates removed, nulls handled, types standardized
- File Format: Parquet (columnar, compressed)
- Partitioning: Optimized for query patterns (date-based)
- Retention: 2 years
- Access: Data engineering + business analysts

**Directory Structure:**
```
s3://cloudmart-processed/
├── orders/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── orders.parquet
├── order_items/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── order_items.parquet
├── customers/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── customers.parquet
├── products/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── products.parquet
└── clickstream_events/
    └── year=2026/
        └── month=03/
            └── day=09/
                └── events.parquet
```

**Data Quality Checks:**
- Schema validation
- Duplicate detection and removal
- Referential integrity checks
- Data type validation
- Range/boundary checks
- Null value handling

#### Zone 3: Curated (Gold Layer)

**Purpose:** Business-ready aggregated datasets optimized for analytics

**Characteristics:**
- Aggregated: Pre-computed metrics and summaries
- File Format: Parquet (highly optimized partitions)
- Partitioning: By date and other business dimensions
- Retention: 2 years
- Access: All business users via Athena

**Directory Structure:**
```
s3://cloudmart-curated/
├── daily_sales_summary/
│   └── year=2026/
│       └── month=03/
│           └── daily_sales_summary.parquet
├── customer_lifetime_value/
│   └── snapshot_date=2026-03-09/
│       └── customer_ltv.parquet
├── product_performance/
│   └── year=2026/
│       └── month=03/
│           └── product_metrics.parquet
├── funnel_analysis/
│   └── year=2026/
│       └── month=03/
│           └── day=09/
│               └── conversion_funnel.parquet
└── geographic_sales/
    └── year=2026/
        └── month=03/
            └── geo_summary.parquet
```

**Datasets:**
1. **daily_sales_summary:** Revenue, order count, AOV by day
2. **customer_lifetime_value:** CLV, purchase frequency, recency
3. **product_performance:** Views, sales, conversion rate, inventory
4. **funnel_analysis:** Page views → Add to cart → Purchase conversion
5. **geographic_sales:** Sales breakdown by country and region

### 7.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                │
└───────────────────┬─────────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │         INGESTION (Lambda Functions)          │
    │  ┌────────────┐  ┌────────────┐              │
    │  │  Validate  │  │  Transform │              │
    │  │  Schema    │→│    Route    │              │
    │  └────────────┘  └────────────┘              │
    └───────────────────┬───────────────────────────┘
                        │
                        ▼ JSON/CSV
    ┌───────────────────────────────────────────────┐
    │           RAW ZONE (Bronze - S3)              │
    │  • Original format (JSON/CSV)                 │
    │  • Immutable                                  │
    │  • Partitioned by date                        │
    │  • 90-day retention                           │
    └───────────────────┬───────────────────────────┘
                        │
                        │ (Scheduled)
                        ▼
    ┌───────────────────────────────────────────────┐
    │        GLUE CRAWLER (Raw Zone)                │
    │  • Discover schemas                           │
    │  • Update Data Catalog                        │
    │  • Run daily at 3 AM                          │
    └───────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
    ┌───────────────────────────────────────────────┐
    │      GLUE ETL: Bronze → Silver                │
    │  • Deduplicate records                        │
    │  • Validate data types                        │
    │  • Handle nulls                               │
    │  • Convert to Parquet                         │
    │  • Data quality checks                        │
    └───────────────────┬───────────────────────────┘
                        │
                        ▼ Parquet
    ┌───────────────────────────────────────────────┐
    │       PROCESSED ZONE (Silver - S3)            │
    │  • Cleansed data                              │
    │  • Parquet format                             │
    │  • Optimized partitions                       │
    │  • 2-year retention                           │
    └───────────────────┬───────────────────────────┘
                        │
                        │ (Scheduled)
                        ▼
    ┌───────────────────────────────────────────────┐
    │       GLUE CRAWLER (Processed Zone)           │
    │  • Update schemas                             │
    │  • Maintain partitions                        │
    └───────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
    ┌───────────────────────────────────────────────┐
    │      GLUE ETL: Silver → Gold                  │
    │  • Aggregate metrics                          │
    │  • Join across sources                        │
    │  • Business logic                             │
    │  • Create analytical datasets                 │
    └───────────────────┬───────────────────────────┘
                        │
                        ▼ Parquet
    ┌───────────────────────────────────────────────┐
    │        CURATED ZONE (Gold - S3)               │
    │  • Business-ready datasets                    │
    │  • Pre-aggregated metrics                     │
    │  • Optimized for queries                      │
    │  • 2-year retention                           │
    └───────────────────┬───────────────────────────┘
                        │
                        │ (On-demand)
                        ▼
    ┌───────────────────────────────────────────────┐
    │            ATHENA (Query Engine)              │
    │  • SQL interface                              │
    │  • Uses Glue Data Catalog                     │
    │  • Pay-per-query                              │
    │  • Results to S3                              │
    └───────────────────┬───────────────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────────────┐
    │          BUSINESS USERS / BI TOOLS            │
    │  • Self-service analytics                     │
    │  • Dashboards                                 │
    │  • Ad-hoc queries                             │
    └───────────────────────────────────────────────┘
```

---

## 8. Deliverables

### 8.1 Technical Deliverables

#### D-001: Infrastructure Code

**Description:** Complete infrastructure as code for all AWS resources

**Contents:**
- CloudFormation or Terraform templates
- S3 bucket definitions with policies
- IAM role and policy definitions
- Glue database and job definitions
- Lambda function configurations
- CloudWatch log groups and alarms
- SNS topic for notifications

**Acceptance Criteria:**
- [ ] All resources can be deployed via single command
- [ ] Infrastructure is parameterized (dev/prod environments)
- [ ] All resources properly tagged
- [ ] Infrastructure validates before deployment
- [ ] Deployment completes in <10 minutes

**File Location:** `/infrastructure/`

#### D-002: Lambda Functions

**Description:** Python Lambda functions for data ingestion

**Contents:**
- `orders_ingestion.py`: Ingest order data from RDS export
- `clickstream_ingestion.py`: Ingest clickstream events
- `products_ingestion.py`: Ingest product catalog
- `marketing_ingestion.py`: Ingest marketing data
- `data_validator.py`: Shared validation logic
- `requirements.txt`: Python dependencies
- Unit tests for all functions

**Acceptance Criteria:**
- [ ] Functions handle errors gracefully
- [ ] Logging to CloudWatch implemented
- [ ] Dead letter queue configured
- [ ] Unit test coverage >80%
- [ ] Functions complete within timeout limits

**File Location:** `/src/lambda/`

#### D-003: Glue ETL Scripts

**Description:** PySpark scripts for data transformations

**Contents:**
- `bronze_to_silver_orders.py`: Cleanse orders data
- `bronze_to_silver_clickstream.py`: Cleanse clickstream data
- `silver_to_gold_daily_sales.py`: Create daily sales summary
- `silver_to_gold_customer_ltv.py`: Calculate customer lifetime value
- `silver_to_gold_product_performance.py`: Product performance metrics
- `data_quality.py`: Shared data quality checks

**Acceptance Criteria:**
- [ ] Scripts handle incremental processing
- [ ] Data quality checks implemented
- [ ] Error handling and logging
- [ ] Performance optimized (partition pruning)
- [ ] Successfully transform sample data

**File Location:** `/src/glue/`

#### D-004: Athena SQL Queries

**Description:** SQL queries for business analytics

**Contents:**
- Minimum 10 business queries covering:
  - Daily/weekly/monthly revenue trends
  - Customer segmentation and CLV
  - Product sales ranking
  - Conversion funnel analysis
  - Geographic sales distribution
  - Customer retention cohorts
  - Average order value trends
  - Inventory levels and turnover
  - Marketing campaign ROI
  - Top customers by revenue

**Acceptance Criteria:**
- [ ] All queries execute successfully
- [ ] Queries optimized for performance (<5s)
- [ ] Queries documented with business context
- [ ] Expected results validated
- [ ] Saved queries created in Athena

**File Location:** `/queries/athena/`

#### D-005: Documentation

**Description:** Comprehensive project documentation

**Contents:**
- Architecture diagrams (infrastructure, data flow, security)
- Setup and deployment instructions
- Operational runbook (start/stop, troubleshooting)
- Architecture Decision Records (ADRs)
- User guide for business analysts
- API/code documentation
- Cost analysis and optimization guide

**Acceptance Criteria:**
- [ ] Documentation is clear and comprehensive
- [ ] Diagrams are professional and accurate
- [ ] Instructions can be followed by non-expert
- [ ] All code is commented
- [ ] ADRs document key decisions

**File Location:** `/docs/`

#### D-006: Tests and Validation

**Description:** Automated tests and validation scripts

**Contents:**
- Unit tests for Lambda functions
- Integration tests for end-to-end pipeline
- Data quality validation scripts
- Query accuracy validation
- Performance test scripts

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80% for Lambda functions
- [ ] End-to-end pipeline test successful
- [ ] Data quality tests pass
- [ ] Performance meets requirements

**File Location:** `/tests/`

### 8.2 Project Artifacts

- **Architecture Diagrams** (Lucidchart, draw.io, or Mermaid)
- **Deployment Guide** (Step-by-step instructions)
- **Operational Runbook** (Day-2 operations)
- **Cost Analysis Report** (Estimated vs. actual costs)
- **Test Results Report** (All test outcomes)
- **Demo Video or Presentation** (10-minute walkthrough)
- **Reflection Document** (Lessons learned, challenges, solutions)

---

## 9. Acceptance Criteria

### 9.1 Infrastructure Acceptance

**Criteria:**
- [ ] **AC-INF-001:** All S3 buckets created with correct naming convention
- [ ] **AC-INF-002:** Bucket policies enforce least privilege access
- [ ] **AC-INF-003:** Server-side encryption enabled (SSE-KMS)
- [ ] **AC-INF-004:** Bucket versioning enabled for critical buckets
- [ ] **AC-INF-005:** Lifecycle policies configured (90-day retention for raw)
- [ ] **AC-INF-006:** IAM roles created with least privilege
- [ ] **AC-INF-007:** All resources tagged (Project, Environment, Owner)
- [ ] **AC-INF-008:** CloudWatch log groups created
- [ ] **AC-INF-009:** SNS topic for alerts configured
- [ ] **AC-INF-010:** Infrastructure deploys successfully via IaC

**Validation Method:** Run infrastructure validation script

### 9.2 Data Ingestion Acceptance

**Criteria:**
- [ ] **AC-ING-001:** Lambda functions deploy successfully
- [ ] **AC-ING-002:** S3 event triggers configured correctly
- [ ] **AC-ING-003:** Sample data ingests within 1 minute
- [ ] **AC-ING-004:** Data partitioned correctly (year/month/day)
- [ ] **AC-ING-005:** Invalid data rejected to DLQ
- [ ] **AC-ING-006:** Metadata logged to CloudWatch
- [ ] **AC-ING-007:** Duplicate detection prevents re-ingestion
- [ ] **AC-ING-008:** Error handling logs failures
- [ ] **AC-ING-009:** Lambda execution time <30 seconds
- [ ] **AC-ING-010:** Unit tests pass with >80% coverage

**Validation Method:** Upload test files and verify ingestion

### 9.3 Data Cataloging Acceptance

**Criteria:**
- [ ] **AC-CAT-001:** Glue Database created
- [ ] **AC-CAT-002:** Crawlers configured for all zones
- [ ] **AC-CAT-003:** Crawlers discover schemas correctly
- [ ] **AC-CAT-004:** Tables visible in Data Catalog
- [ ] **AC-CAT-005:** Partitions registered automatically
- [ ] **AC-CAT-006:** Schema evolution handled (new columns)
- [ ] **AC-CAT-007:** Data types inferred correctly (>95% accuracy)
- [ ] **AC-CAT-008:** Crawler schedules configured
- [ ] **AC-CAT-009:** Crawler execution completes successfully
- [ ] **AC-CAT-010:** Table statistics updated

**Validation Method:** Run crawlers and query Data Catalog

### 9.4 ETL Pipeline Acceptance

**Criteria:**
- [ ] **AC-ETL-001:** Bronze → Silver ETL job executes successfully
- [ ] **AC-ETL-002:** Duplicates removed (verified with test data)
- [ ] **AC-ETL-003:** Data types standardized
- [ ] **AC-ETL-004:** Null values handled appropriately
- [ ] **AC-ETL-005:** Parquet files created in Silver zone
- [ ] **AC-ETL-006:** Data quality checks pass (>99% clean data)
- [ ] **AC-ETL-007:** Silver → Gold ETL job executes successfully
- [ ] **AC-ETL-008:** Aggregations match source data (validated)
- [ ] **AC-ETL-009:** Incremental processing works (not full refresh)
- [ ] **AC-ETL-010:** ETL job completes in <10 minutes

**Validation Method:** Run ETL jobs with test data and verify outputs

### 9.5 Analytics Acceptance

**Criteria:**
- [ ] **AC-ANL-001:** Athena workgroup configured
- [ ] **AC-ANL-002:** All Gold tables queryable
- [ ] **AC-ANL-003:** 10+ business queries execute successfully
- [ ] **AC-ANL-004:** Query performance <5 seconds (90th percentile)
- [ ] **AC-ANL-005:** Query results accurate (validated against source)
- [ ] **AC-ANL-006:** Views created for common queries
- [ ] **AC-ANL-007:** Saved queries documented
- [ ] **AC-ANL-008:** Query cost <$0.01 per query (average)
- [ ] **AC-ANL-009:** Partition pruning working (verified in query plans)
- [ ] **AC-ANL-010:** Multiple concurrent users supported (tested)

**Validation Method:** Execute business queries and measure performance

### 9.6 Monitoring Acceptance

**Criteria:**
- [ ] **AC-MON-001:** CloudWatch dashboard created
- [ ] **AC-MON-002:** Dashboard shows key metrics (ingestion, ETL status, costs)
- [ ] **AC-MON-003:** Alarms configured for Lambda failures
- [ ] **AC-MON-004:** Alarms configured for Glue job failures
- [ ] **AC-MON-005:** Alarms configured for cost overruns
- [ ] **AC-MON-006:** SNS notifications sent for critical alerts
- [ ] **AC-MON-007:** Email notifications received and tested
- [ ] **AC-MON-008:** Log retention set appropriately (30 days)
- [ ] **AC-MON-009:** Metrics tracked (invocations, duration, errors)
- [ ] **AC-MON-010:** Dashboard accessible to stakeholders

**Validation Method:** Simulate failures and verify alerting

### 9.7 Documentation Acceptance

**Criteria:**
- [ ] **AC-DOC-001:** Architecture diagrams created (infrastructure, data flow)
- [ ] **AC-DOC-002:** README with project overview complete
- [ ] **AC-DOC-003:** Setup instructions documented (step-by-step)
- [ ] **AC-DOC-004:** Operational runbook created
- [ ] **AC-DOC-005:** ADRs document key design decisions (minimum 5)
- [ ] **AC-DOC-006:** Code comments on all functions
- [ ] **AC-DOC-007:** SQL queries documented with business context
- [ ] **AC-DOC-008:** Cost analysis documented
- [ ] **AC-DOC-009:** Troubleshooting guide included
- [ ] **AC-DOC-010:** User guide for business analysts

**Validation Method:** Documentation review by third party

### 9.8 Cost Acceptance

**Criteria:**
- [ ] **AC-CST-001:** Monthly cost <$50 (verified)
- [ ] **AC-CST-002:** Cost breakdown documented by service
- [ ] **AC-CST-003:** Cost optimization implemented (S3 lifecycle, Glue DPU tuning)
- [ ] **AC-CST-004:** Budget alerts configured at 80% threshold
- [ ] **AC-CST-005:** Cost monitoring dashboard created
- [ ] **AC-CST-006:** No unexpected charges (all services budgeted)
- [ ] **AC-CST-007:** Free Tier utilization maximized
- [ ] **AC-CST-008:** Cost per query <$0.01 (average)
- [ ] **AC-CST-009:** Storage costs optimized (compression, formats)
- [ ] **AC-CST-010:** Compute costs optimized (Lambda memory, Glue workers)

**Validation Method:** Review AWS Cost Explorer

---

## 10. Non-Functional Requirements

### 10.1 Performance Requirements

| Requirement | Target | Measurement Method |
|------------|--------|-------------------|
| **Data Ingestion Latency** | <1 minute from S3 upload to availability | CloudWatch metrics |
| **Bronze → Silver ETL** | <10 minutes for daily batch (10K orders) | Glue job metrics |
| **Silver → Gold ETL** | <15 minutes for daily aggregations | Glue job metrics |
| **Athena Query Response (Simple)** | <3 seconds (COUNT, SUM on single table) | Query execution time |
| **Athena Query Response (Complex)** | <10 seconds (multi-table JOIN) | Query execution time |
| **Athena Query Response (90th percentile)** | <5 seconds for business queries | Query logs analysis |
| **Data Freshness** | Data available within 24 hours | Pipeline monitoring |
| **Concurrent Athena Users** | 50+ simultaneous queries | Load test |

### 10.2 Scalability Requirements

| Aspect | Current | 6-Month Projection | 1-Year Projection |
|--------|---------|-------------------|------------------|
| **Daily Order Volume** | 10K | 15K | 25K |
| **Daily Clickstream Events** | 2M | 3M | 5M |
| **Data Storage** | 110GB/month | 220GB cumulative | 1.5TB cumulative |
| **Athena Users** | 10 | 30 | 60 |
| **Business Queries** | 100/day | 500/day | 1,000/day |

**Scalability Tests:**
- [ ] Test with 2x current data volume
- [ ] Test with 5x current query load
- [ ] Test with 10x file count

### 10.3 Availability and Reliability

| Metric | Target | Notes |
|--------|--------|-------|
| **Query Availability** | 99.9% (Athena SLA) | AWS responsibility |
| **Data Durability** | 99.999999999% (S3 SLA) | AWS responsibility |
| **Pipeline Success Rate** | >99% | Measured over 30 days |
| **Data Quality** | >99% clean records | Validated by DQ checks |
| **Recovery Time (RTO)** | <1 hour | Time to restore service |
| **Recovery Point (RPO)** | <24 hours | Acceptable data loss |

### 10.4 Security Requirements

**Authentication and Authorization:**
- IAM for all AWS service access
- MFA required for production access
- Role-based access control (RBAC)

**\Encryption:**
- S3 encryption: SSE-KMS (AWS KMS)
- Athena query results: Encrypted
- Data in transit: TLS 1.2+

**Audit and Compliance:**
- CloudTrail enabled for all API calls
- CloudWatch Logs retention: 30 days
- Access logs for S3 buckets
- Regular access reviews (quarterly)

**Network Security:**
- VPC endpoints for private access (optional)
- No public exposure of sensitive data
- IP whitelisting for production access (optional)

**Data Privacy:**
- PII data identified and protected
- Data masking for non-production environments (future)
- GDPR compliance considerations (right to forget)

---

## 11. Security and Compliance

### 11.1 Data Classification

**Public Data:**
- Product catalog (non-pricing)
- Marketing campaign names

**Internal Data:**
- Aggregated analytics
- Business metrics and KPIs

**Confidential Data:**
- Customer PII (name, email, phone)
- Order details
- Pricing and cost information

**Highly Confidential:**
- Payment information (not stored in data lake)
- Authentication credentials

### 11.2 Security Controls

**Access Control:**
- Principle of least privilege for all IAM roles
- Separate roles for Lambda, Glue, Athena
- Read-only access for business users
- Separate dev/prod environments

**Encryption:**
- S3 buckets: SSE-KMS with customer-managed keys
- Glue Data Catalog: Encrypted at rest
- Athena results: Encrypted
- CloudWatch Logs: Encrypted

**Monitoring:**
- CloudTrail for API call auditing
- CloudWatch for operational monitoring
- Anomaly detection for unusual access patterns
- Budget alerts for cost anomalies

**Data Retention:**
- Raw data: 90 days (then Glacier or delete)
- Processed data: 2 years
- Curated data: 2 years
- CloudWatch Logs: 30 days
- CloudTrail: 90 days

### 11.3 Compliance Requirements

**GDPR Considerations:**
- Right to access: Ability to query customer data
- Right to erasure: Ability to delete customer records
- Data minimization: Only store necessary data
- Data lineage: Track data sources

**SOC 2 (future):**
- Access controls and monitoring
- Encryption of sensitive data
- Regular security reviews
- Incident response procedures

**PCI DSS:**
- Payment data NOT stored in data lake
- Only transaction IDs and amounts (no card details)

---

## 12. Timeline and Milestones

### 12.1 Project Phases

**Duration: 20-25 hours over 3-5 days**

#### Phase 1: Infrastructure Setup (Day 1 - 5-6 hours)

**Objective:** Provision all AWS infrastructure

**Tasks:**
1. Create S3 buckets (raw, processed, curated, scripts, logs)
2. Configure bucket policies and encryption
3. Create IAM roles (Lambda, Glue, Athena)
4. Set up CloudWatch log groups
5. Deploy SNS topic for alerts
6. Write and deploy CloudFormation/Terraform templates
7. Validate deployment

**Deliverables:**
- Infrastructure as Code templates
- Deployed AWS resources
- Deployment validation report

**Milestone:** ✅ Infrastructure deployed and validated

#### Phase 2: Data Ingestion (Day 2 - 4-5 hours)

**Objective:** Implement Lambda-based data ingestion

**Tasks:**
1. Write Lambda function for orders data
2. Write Lambda function for clickstream data
3. Write Lambda function for products data
4. Write Lambda function for marketing data
5. Implement data validation logic
6. Configure S3 event triggers
7. Set up DLQ for error handling
8. Write unit tests
9. Deploy and test with sample data

**Deliverables:**
- Lambda function code
- Unit tests
- Test data in Raw zone
- Deployment package

**Milestone:** ✅ Data ingestion pipeline functional

#### Phase 3: Data Cataloging (Day 2-3 - 3-4 hours)

**Objective:** Set up Glue Data Catalog

**Tasks:**
1. Create Glue Database
2. Configure Glue Crawler for Raw zone
3. Run crawler and validate tables
4. Configure crawlers for Processed and Curated zones
5. Set up crawler schedules
6. Validate schema discovery

**Deliverables:**
- Glue database and tables
- Crawler configurations
- Validated schemas

**Milestone:** ✅ Data cataloging operational

#### Phase 4: Data Transformation (Day 3-4 - 6-7 hours)

**Objective:** Build ETL pipelines

**Tasks:**
1. Write Bronze → Silver transformation for orders
2. Write Bronze → Silver transformation for clickstream
3. Implement data quality checks
4. Write Silver → Gold aggregations (daily sales, CLV, product metrics)
5. Configure Glue job parameters
6. Implement incremental processing
7. Set up job schedules
8. Test with sample data

**Deliverables:**
- Glue ETL scripts
- Data quality checks
- Transformed data in Processed and Curated zones
- Test validation report

**Milestone:** ✅ ETL pipelines operational

#### Phase 5: Analytics and Finalization (Day 4-5 - 5-6 hours)

**Objective:** Enable SQL analytics and finalize project

**Tasks:**
1. Create Athena workgroup
2. Write business SQL queries (10+)
3. Create views for common queries
4. Optimize query performance
5. Generate sample query results
6. Create CloudWatch dashboard
7. Configure monitoring alarms
8. Write documentation (README, Runbook, ADRs)
9. Final testing and validation
10. Record demo video

**Deliverables:**
- Athena queries and views
- CloudWatch dashboard
- Monitoring alarms
- Complete documentation
- Demo video

**Milestone:** ✅ Project complete and ready for submission

### 12.2 Milestones Summary

| Milestone | Target Date | Completion Criteria |
|-----------|------------|---------------------|
| **M1: Infrastructure Ready** | Day 1 | All AWS resources deployed via IaC |
| **M2: Ingestion Functional** | Day 2 | Sample data flowing to Raw zone |
| **M3: Catalog Operational** | Day 3 | Schemas discovered and queryable |
| **M4: Transformations Working** | Day 4 | Data flowing through Bronze→Silver→Gold |
| **M5: Analytics Enabled** | Day 5 | Business queries returning results |
| **M6: Project Complete** | Day 5 | All acceptance criteria met, docs complete |

---

## 13. Grading Rubric

**Total Points: 100**

### Category 1: Infrastructure (20 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| IaC Templates | 5 | CloudFormation or Terraform, parameterized, well-documented |
| S3 Buckets | 4 | Correct structure, policies, encryption, lifecycle rules |
| IAM Roles | 4 | Least privilege, proper trust relationships |
| Resource Tagging | 2 | All resources tagged (Project, Environment, Owner) |
| Deployment Success | 3 | Stack deploys without errors |
| Security Configuration | 2 | Encryption, CloudTrail, proper access controls |

### Category 2: Data Ingestion (15 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| Lambda Functions | 5 | All 4 ingestion functions implemented correctly |
| Data Validation | 3 | Schema validation, error handling |
| Event Configuration | 2 | S3 triggers configured properly |
| Error Handling | 2 | DLQ, logging, graceful failures |
| Unit Tests | 2 | >80% coverage, tests pass |
| Performance | 1 | Ingestion <1 minute |

### Category 3: Data Cataloging (15 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| Glue Database | 3 | Properly configured with descriptions |
| Crawlers | 5 | All zones covered, schedules configured |
| Schema Discovery | 4 | Accurate schemas, partitions discovered |
| Metadata Quality | 2 | Table descriptions, column comments |
| Catalog Maintenance | 1 | Schema evolution handled |

### Category 4: ETL Pipelines (20 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| Bronze → Silver | 8 | Cleansing, deduplication, validation working |
| Silver → Gold | 8 | Aggregations correct, business logic sound |
| Data Quality | 3 | DQ checks implemented and passing |
| Incremental Processing | 1 | Not full refresh, handles new data only |

### Category 5: Analytics (15 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| Query Functionality | 5 | 10+ queries execute successfully |
| Query Performance | 3 | 90% of queries <5 seconds |
| Query Accuracy | 4 | Results validated against source data |
| Views and Optimization | 2 | Views created, partitioning utilized |
| Documentation | 1 | Queries documented with business context |

### Category 6: Monitoring (10 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| CloudWatch Dashboard | 4 | Key metrics visible, clean layout |
| Alarms | 3 | Critical failures trigger alarms |
| Notifications | 2 | SNS configured, tested |
| Log Management | 1 | Appropriate retention, structured logging |

### Category 7: Documentation (10 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| Architecture Diagrams | 3 | Clear, professional, accurate |
| README | 2 | Project overview, setup instructions |
| ADRs | 2 | Minimum 5 ADRs, well-reasoned |
| Code Comments | 1 | All functions and complex logic documented |
| Runbook | 2 | Operational procedures documented |

### Category 8: Testing (5 points)

| Criteria | Points | Requirements |
|----------|--------|-------------|
| Unit Tests | 2 | >80% coverage, pass |
| Integration Tests | 2 | End-to-end pipeline tested |
| Test Documentation | 1 | Test results documented |

### Bonus Points (10 additional points available)

| Bonus | Points | Requirements |
|-------|--------|-------------|
| CI/CD Pipeline | +3 | Automated testing and deployment |
| Data Quality Dashboard | +2 | Custom dashboard for DQ metrics |
| Advanced Partitioning | +2 | Complex partitioning strategy (e.g., by customer segment) |
| Multi-Region | +3 | Multi-region deployment with replication |

### Grading Scale

| Score | Grade | Outcome |
|-------|-------|---------|
| 90-100+ | Excellent | Exceeds all expectations |
| 80-89 | Very Good | Meets all requirements with quality |
| 70-79 | Good (Pass) | Meets minimum requirements |
| 60-69 | Needs Improvement | Some requirements missing |
| <60 | Does Not Pass | Significant gaps |

**Passing Score: 70/100**

---

## 14. Assumptions and Constraints

### 14.1 Assumptions

1. **AWS Account:** Student has active AWS account with Free Tier
2. **Permissions:** Full admin access to AWS account (learning environment)
3. **Region:** Single AWS region (us-east-1 recommended)
4. **Sample Data:** Provided sample datasets represent actual data patterns
5. **No Real Production:** This is a learning project, not production system
6. **Budget:** Student can afford ~$30-50/month for 1-2 months
7. **Time:** Student has 20-25 hours available over 3-5 days
8. **Prerequisites:** Modules 01-06 completed successfully
9. **Tools:** Student has Python, AWS CLI, and code editor installed
10. **Internet:** Reliable internet access for AWS console and CLI

### 14.2 Constraints

**Technical Constraints:**
1. **Budget:** Maximum $50/month for all AWS services
2. **Services:** Limited to AWS services covered in Modules 01-06
3. **Region:** Single-region deployment (multi-region optional)
4. **Data Volume:** Limited to sample datasets provided
5. **Real-Time:** No real-time streaming (future checkpoint)
6. **BI Tools:** Integration only, not building dashboards
7. **Authentication:** IAM only (no SSO or federated identity)

**Time Constraints:**
1. **Duration:** Must complete within 5 days maximum
2. **Support:** Office hours once per week (async otherwise)
3. **Review:** Submission review within 1 week

**Scope Constraints:**
1. **Historical Data:** Not migrating historical data (>2 years)
2. **ML Models:** Not deploying machine learning models
3. **Streaming:** Batch processing only (no Kinesis/Kafka)
4. **Governance:** Basic IAM only (no Lake Formation)

### 14.3 Risks and Mitigations

**Risk 1: Budget Overrun**
- **Likelihood:** Medium
- **Impact:** High (student cost)
- **Mitigation:** Budget alerts at 80%, cost monitoring dashboard, cleanup scripts

**Risk 2: Incomplete Prerequisites**
- **Likelihood:** Low
- **Impact:** High (project failure)
- **Mitigation:** Prerequisites validation quiz, module completion tracking

**Risk 3: AWS Service Limits**
- **Likelihood:** Low
- **Impact:** Medium (project delays)
- **Mitigation:** Request limit increases proactively, document limits

**Risk 4: Data Quality Issues**
- **Likelihood:** Medium
- **Impact:** Medium (incorrect results)
- **Mitigation:** Comprehensive DQ checks, validation scripts, test data

**Risk 5: Time Management**
- **Likelihood:** High
- **Impact:** Medium (incomplete project)
- **Mitigation:** Phased approach, milestones, time tracking, MVP focus

---

## 15. Success Metrics

### 15.1 Project Success Indicators

**Technical Success:**
- ✅ All acceptance criteria met (100%)
- ✅ All automated tests passing
- ✅ Performance targets achieved
- ✅ Budget maintained (<$50/month)
- ✅ Zero critical security vulnerabilities

**Learning Success:**
- ✅ Student demonstrates understanding of all concepts
- ✅ Student can explain architecture decisions
- ✅ Student can troubleshoot issues independently
- ✅ Student can optimize costs and performance

**Business Success (Simulation):**
- ✅ Business users can self-serve analytics
- ✅ Time-to-insight reduced from days to minutes
- ✅ Data quality >99%
- ✅ Cost reduction >90% vs. traditional approach

### 15.2 Post-Project Assessment

**Self-Reflection Questions:**
1. What was the most challenging aspect of the project?
2. Which AWS service did you find most interesting?
3. What would you do differently if starting over?
4. How would you scale this to production?
5. What additional features would you add?

**Instructor Evaluation:**
- Code quality and organization
- Architecture appropriateness
- Problem-solving approach
- Documentation quality
- Communication and presentation

---

## 16. Resources and Support

### 16.1 Documentation

- AWS S3 Documentation
- AWS Lambda Developer Guide
- AWS Glue Developer Guide
- Amazon Athena User Guide
- CloudFormation/Terraform Guides
- PySpark API Reference

### 16.2 Sample Data

Sample datasets will be provided in `/data/input/`:
- `orders_sample.csv`: 1,000 sample orders
- `order_items_sample.csv`: 2,500 sample order items
- `customers_sample.csv`: 500 sample customers
- `products_sample.json`: 100 sample products
- `clickstream_sample.ndjson`: 10,000 sample events
- `campaigns_sample.csv`: 50 sample campaigns

### 16.3 Support Channels

- **Office Hours:** Weekly (check schedule)
- **Discussion Forum:** GitHub Discussions
- **Email:** For urgent issues only
- **AWS Support:** Use AWS Support Forums (free)

### 16.4 Additional Learning

- **AWS Architecture Blog:** Latest patterns and practices
- **AWS Samples GitHub:** Code examples
- **YouTube:** AWS re:Invent sessions on data lakes
- **Books:** "Data Engineering on AWS"

---

## 17. Conclusion

This project represents the culmination of Modules 01-06 and your first major cloud data engineering deliverable. Successfully completing this checkpoint demonstrates your ability to design, build,and operate a production-grade serverless data lake on AWS.

**Remember:**
- Start early; don't leave it all for the last day
- Test incrementally; don't wait until the end
- Document as you go; it's easier in the moment
- Ask questions; that's what learning is about
- Have fun; you're building something real!

**Good luck! We can't wait to see what you build! 🚀**

---

**Document Version:** 1.0
**Last Updated:** March 9, 2026
**Next Review:** After 10 student submissions
