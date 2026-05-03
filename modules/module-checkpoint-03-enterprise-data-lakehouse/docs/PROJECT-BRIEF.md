# Enterprise Data Lakehouse - Project Brief

## 📋 Executive Summary

### Project Vision

**DataCorp Inc.** is embarking on a transformative initiative to consolidate fragmented data systems into a unified, governed, and scalable **Enterprise Data Lakehouse**. This strategic investment addresses critical business imperatives: regulatory compliance, operational efficiency, and data-driven decision-making across the organization's 50+ departments.

### Business Impact

| Dimension | Current State | Target State | Expected Impact |
|-----------|--------------|--------------|-----------------|
| **TCO** | $8M annually | $2.8M annually | **$5.2M savings** (65% reduction) |
| **Query Performance** | 10+ minutes (p95) | <1 minute (p99) | **10x improvement** |
| **Data Silos** | 50+ disconnected systems | 1 unified lakehouse | **Single source of truth** |
| **Compliance Fines** | $2M annual risk | $0 (full compliance) | **Risk elimination** |
| **Time to Insight** | Weeks | Hours | **100x faster** |
| **Data Quality** | 85% accuracy | 99.9% accuracy | **Trust restoration** |

### Strategic Objectives

1. **Regulatory Compliance**: Achieve full GDPR, CCPA, SOX, and HIPAA compliance
2. **Cost Optimization**: Reduce total cost of ownership by 65%
3. **Unified Analytics**: Enable self-service analytics for 5,000+ employees
4. **Real-Time Insights**: Transform from batch (daily) to near real-time (15-minute latency)
5. **Advanced Analytics**: Enable ML/AI on unified datasets (currently impossible)
6. **Operational Excellence**: Establish 99.9% platform availability with automated DR

### Investment Overview

| Category | Development | Production (Year 1) |
|----------|-------------|---------------------|
| **AWS Infrastructure** | $1,800 (12 weeks) | $14,400 |
| **Engineering Resources** | $180,000 (3 FTE x 12 weeks) | - |
| **Training & Enablement** | $50,000 | $75,000 |
| **Third-Party Tools** | $5,000 | $20,000 |
| **Contingency (15%)** | $35,000 | $16,000 |
| **TOTAL** | **$271,800** | **$125,400** |

**ROI**: 191% in Year 1 (savings of $5.2M vs. investment of $271K)

### Success Metrics

**North Star Metric**: 80% of business decisions supported by lakehouse data within 12 months

**Key Results**:
- ✅ 100% compliance audit pass rate (GDPR, CCPA, SOX)
- ✅ <60 seconds query latency (p99) for ad-hoc analytics
- ✅ 99.9% data quality score across all domains
- ✅ $150/month or less development environment costs
- ✅ 50+ concurrent users without performance degradation
- ✅ Zero data breaches or unauthorized access incidents

---

## 🏢 Business Context

### DataCorp Inc. Profile

**Industry**: Multi-Industry Conglomerate
**Headquarters**: San Francisco, CA
**Founded**: 1995
**Revenue**: $2.3B (FY2025)
**Employees**: 12,000 globally
**Locations**: 25 countries, 80+ offices

**Business Units**:
- **Manufacturing** (35% revenue): Industrial equipment, IoT-enabled machinery
- **Retail** (30% revenue): E-commerce platform, 200+ physical stores
- **Financial Services** (20% revenue): B2B payments, invoice financing
- **Healthcare** (15% revenue): Medical devices, telemedicine software

### Current Data Landscape

**Systems Inventory** (as of January 2026):
```
Production Databases (50+ instances):
├── Oracle ERP (6 instances) - Finance, Supply Chain
├── SAP S/4HANA (2 instances) - GL, Procurement
├── Microsoft Dynamics 365 (12 instances) - CRM, HR
├── PostgreSQL (20 instances) - Custom applications
├── MongoDB (8 instances) - IoT data, logs
└── MySQL (5 instances) - E-commerce, analytics

SaaS Applications (30+ platforms):
├── Salesforce (CRM, Sales Cloud)
├── Workday (HCM, Financial Management)
├── ServiceNow (IT Service Management)
├── Shopify Plus (E-commerce)
├── Zendesk (Customer Support)
├── HubSpot (Marketing Automation)
├── Tableau Server (BI, 500+ reports)
└── Looker (Embedded Analytics)

Legacy Systems (20+ systems, end-of-life by 2027):
├── AS/400 mainframes (order management)
├── FoxPro databases (inventory tracking)
├── Access databases (departmental reporting)
└── Excel-based "databases" (budgeting, forecasts)

Data Warehouses (3 separate instances):
├── Snowflake (Sales, Marketing) - $400K/year
├── Redshift (Finance) - $250K/year
└── BigQuery (Operations) - $180K/year
```

**Data Volume**: 10TB production data + 15TB historical archives

**Data Sources Breakdown**:
- Structured (RDBMS): 6TB (60%)
- Semi-structured (JSON/XML): 2.5TB (25%)
- Unstructured (PDFs, images): 1.5TB (15%)

### Pain Points

#### 1. Regulatory Compliance Crisis

**GDPR Violations**:
- €1.2M fine (2024) for data breach affecting 50K EU customers
- 18-day delay in responding to data subject access requests (legal limit: 30 days, internal target: 48 hours)
- No centralized PII inventory
- Inconsistent consent management across 30+ systems

**CCPA Non-Compliance**:
- Unable to fulfill "right to delete" requests within 45 days
- Lack of data lineage prevents identification of all consumer data copies
- No automated opt-out mechanism

**SOX Control Deficiencies**:
- Material weakness reported in Q4 2025 audit: inadequate segregation of duties
- Financial data modified without audit trail in 3 systems
- 7-year data retention requirement not consistently enforced

**HIPAA Risks** (Healthcare BU):
- PHI stored in non-encrypted S3 buckets (2 incidents)
- Unauthorized access to patient records by 12 employees (terminated)

**Cost of Non-Compliance**: $2M annually (fines + audit remediation + legal)

#### 2. Data Silos & Quality Issues

**Cross-Functional Analysis Impossible**:
- Sales team cannot correlate revenue with manufacturing quality issues
- Finance cannot reconcile revenue across 6 different source systems
- HR cannot link employee satisfaction with productivity metrics

**Data Quality Problems**:
| Issue | Affected Systems | Business Impact |
|-------|------------------|-----------------|
| Duplicate customers | Salesforce, Shopify, Dynamics | $5M revenue misattribution |
| Inconsistent product codes | ERP, E-commerce, CRM | Inventory write-downs $800K |
| Missing cost center mappings | SAP, Oracle | Budget variance reports unusable |
| Stale employee data | Workday, AD, 10+ apps | Security risk, access control failures |

**Data Quality Score**: 85% (unacceptable for executive decision-making)

**Root Causes**:
- No master data management (MDM) strategy
- Manual data entry in 40+ systems
- ETL pipelines with no data validation
- Lack of data stewardship ownership

#### 3. Performance & Scalability Bottlenecks

**Query Performance SLA Violations**:
- Executive dashboard refresh: 45 minutes (target: <5 minutes)
- Month-end close reports: 8 hours (target: <1 hour)
- Ad-hoc analytics: Frequently timeout after 30 minutes

**Concurrent User Limitations**:
- Snowflake: Only 10 concurrent analysts (license limit)
- Tableau Server: Crashes with >50 simultaneous users
- Oracle: Batch windows extending into business hours

**Scalability Concerns**:
- 30% YoY data growth
- Q4 holiday season: 5x query volume, frequent outages
- IoT expansion: 100K → 1M sensors by 2027 (10x data volume)

#### 4. Cost Inefficiency

**Current Annual Spend**: $8M

| Category | Annual Cost | Inefficiency |
|----------|-------------|--------------|
| Snowflake | $400K | Over-provisioned warehouses, no auto-suspend |
| Redshift | $250K | 24/7 cluster despite 8-hour daily usage |
| BigQuery | $180K | Unoptimized queries scanning full tables |
| Oracle licenses | $600K | 40% of databases underutilized |
| Data warehouse ETL tools | $300K | Talend, Informatica licenses |
| BI tools | $200K | Tableau, Looker, Power BI duplication |
| Staff augmentation | $2M | Offshore ETL developers maintaining fragile pipelines |
| Data storage | $1.5M | No lifecycle policies, duplicated data |
| On-prem infrastructure | $1.2M | Legacy servers, data center costs |
| Network & data transfer | $370K | Inefficient data movement |

**Cost Optimization Opportunity**: $5.2M (65% reduction)

#### 5. Limited Advanced Analytics

**Current State**:
- Descriptive analytics only (what happened?)
- No predictive models (what will happen?)
- No prescriptive analytics (what should we do?)

**ML/AI Blockers**:
- Data scattered across 50+ systems
- Inconsistent data formats and schemas
- No feature store for ML
- Data scientists spend 80% time on data wrangling, 20% on modeling

**Missed Opportunities**:
- Customer churn prediction (could save $10M annually)
- Dynamic pricing optimization (could increase margin 5%)
- Predictive maintenance (could reduce downtime 30%)
- Fraud detection in real-time (currently 2-week delay)

---

## 🎯 Business Objectives

### 1. Regulatory Compliance (Priority: CRITICAL)

**GDPR Full Compliance**:
- ✅ Centralized PII inventory and data map
- ✅ Automated data subject access request (DSAR) fulfillment <24 hours
- ✅ Right to be forgotten implementation across all systems
- ✅ Consent management with versioning and audit trail
- ✅ Data retention policies enforced automatically
- ✅ Cross-border transfer compliance (EU data residency)
- ✅ Privacy by design in all new data ingestion

**Success Metric**: Zero GDPR violations, pass annual DPA audit

**CCPA Compliance**:
- ✅ California consumer data identification
- ✅ Opt-out of sale mechanism (not applicable, but documented)
- ✅ Data deletion within 45 days
- ✅ Privacy policy disclosures aligned with actual data practices

**Success Metric**: Zero CCPA complaints or enforcement actions

**SOX Compliance**:
- ✅ Segregation of duties enforced via RBAC
- ✅ Immutable audit trail for all financial data
- ✅ 7-year data retention for financial records
- ✅ Change management controls with approval workflows

**Success Metric**: Zero material weaknesses, clean audit opinion

**HIPAA Compliance** (Healthcare BU):
- ✅ PHI encryption at rest and in transit
- ✅ Access controls with MFA for PHI
- ✅ Breach notification procedures <72 hours
- ✅ Business associate agreements (BAAs) with all vendors

**Success Metric**: Zero PHI breaches, OCR compliance

### 2. Cost Optimization (Priority: HIGH)

**Target**: Reduce TCO from $8M to $2.8M (65% savings)

**Cost Reduction Strategies**:

| Initiative | Current Cost | Target Cost | Savings |
|------------|--------------|-------------|---------|
| Consolidate to single lakehouse | $830K (3 DWs) | $150K | $680K |
| Eliminate redundant tools | $500K | $50K | $450K |
| Serverless compute | $1.2M | $500K | $700K |
| S3 Intelligent-Tiering | $1.5M | $800K | $700K |
| Right-size resources | $2M (staff aug) | $500K | $1.5M |
| Shutdown legacy systems | $1.2M (on-prem) | $0 | $1.2M |

**ROI Timeline**:
- Year 1: $5.2M savings - $271K investment = $4.9M net benefit
- Year 2: $5.2M savings - $125K operations = $5M net benefit
- 3-Year NPV: $14.1M (discount rate 10%)

### 3. Performance & Scalability (Priority: HIGH)

**Query Performance Targets**:

| Workload Type | Current | Target | Improvement |
|---------------|---------|--------|-------------|
| Executive dashboards | 45 min | 2 min | 22.5x |
| Ad-hoc analytics (p95) | 10 min | 30 sec | 20x |
| Month-end reports | 8 hours | 30 min | 16x |
| Real-time dashboards | N/A | <5 sec | New capability |

**Concurrency Targets**:
- Support 50+ concurrent analysts
- 500+ daily active users
- 5,000 monthly active users

**Scalability Requirements**:
- Handle 30% YoY data growth (3TB/year)
- Support 10x IoT sensor expansion (100K → 1M devices)
- Maintain performance during Q4 peak (5x query volume)

### 4. Data Quality & Trust (Priority: HIGH)

**Target**: 99.9% data quality score

**Data Quality Dimensions**:
| Dimension | Current | Target | Implementation |
|-----------|---------|--------|----------------|
| **Completeness** | 88% | 99.5% | Mandatory fields, nullability constraints |
| **Accuracy** | 85% | 99.9% | Source validation, reconciliation |
| **Consistency** | 80% | 99.8% | MDM, golden records |
| **Timeliness** | 78% | 99% | Near real-time ingestion |
| **Validity** | 90% | 99.9% | Business rules, data contracts |
| **Uniqueness** | 82% | 99.9% | Deduplication, primary keys |

**Data Quality Framework**:
- Great Expectations for validation rules
- Automated data profiling and anomaly detection
- Data quality dashboards with SLA tracking
- Data steward alerts for quality degradation

### 5. Enable Advanced Analytics (Priority: MEDIUM)

**Phase 1 (Months 1-6)**: Descriptive analytics
- Historical reporting
- KPI tracking
- Business intelligence dashboards

**Phase 2 (Months 7-12)**: Diagnostic analytics
- Root cause analysis
- Drill-down capabilities
- Variance analysis

**Phase 3 (Months 13-18)**: Predictive analytics
- Customer churn models
- Demand forecasting
- Anomaly detection

**Phase 4 (Months 19-24)**: Prescriptive analytics
- Recommendation engines
- Dynamic pricing
- Resource optimization

**ML/AI Use Cases** (prioritized):
1. Customer lifetime value (CLV) prediction
2. Fraud detection in financial transactions
3. Predictive maintenance for manufacturing equipment
4. Inventory optimization
5. Next-best-action for sales teams

---

## 🏗️ Technical Requirements

### Functional Requirements

#### FR-1: Multi-Source Data Ingestion

**Batch Ingestion**:
- **RDBMS**: CDC from Oracle, PostgreSQL, MySQL via AWS DMS
- **Files**: CSV, JSON, XML, Parquet, Avro from S3/SFTP
- **APIs**: REST/GraphQL with incremental load
- **SaaS**: Salesforce, Workday via native connectors

**Streaming Ingestion**:
- **IoT**: Sensor data via AWS IoT Core → Kinesis
- **Application logs**: CloudWatch Logs → Kinesis Firehose
- **CDC streams**: DynamoDB Streams, RDS binlog

**Ingestion SLAs**:
- Batch: Daily full load (5+ TB), hourly incremental (<100GB)
- Streaming: <5 minute end-to-end latency (source → Bronze layer)

#### FR-2: Data Lake Storage Architecture

**4-Layer Design**:

```
s3://datacorp-lakehouse-dev/
├── raw/ (landing zone, 30-day retention)
│   ├── finance/
│   ├── hr/
│   ├── sales/
│   └── operations/
├── bronze/ (ingested with audit metadata, 90-day retention)
│   ├── finance/
│   ├── hr/
│   ├── sales/
│   └── operations/
├── silver/ (cleaned, conformed, validated, 1-year retention)
│   ├── finance/
│   ├── hr/
│   ├── sales/
│   └── operations/
└── gold/ (business-ready aggregates, 7-year retention for financial)
    ├── finance/
    ├── hr/
    ├── sales/
    └── operations/
```

**Partitioning Strategy**:
- Time-based: `year=YYYY/month=MM/day=DD` for facts
- Categorical: `department={dept}/region={region}` for multi-tenancy

**File Format**:
- Raw: Preserve source format
- Bronze: Parquet (Snappy compression)
- Silver/Gold: Delta Lake (Parquet + transaction log)

#### FR-3: Delta Lake Table Management

**Capabilities Required**:
- ✅ ACID transactions (atomicity, consistency, isolation, durability)
- ✅ Time travel (query historical versions)
- ✅ Schema evolution (add/modify columns)
- ✅ MERGE operations (upserts, CDC)
- ✅ OPTIMIZE (Z-order, file compaction)
- ✅ VACUUM (remove old versions based on retention)

**Table Types**:
- **Dimension Tables**: SCD Type 2 for historical tracking
- **Fact Tables**: Insert-only with partitioning
- **Aggregates**: Materialized views, rebuilt incrementally

#### FR-4: Data Catalog & Metadata Management

**AWS Glue Data Catalog**:
- Centralized metadata for all databases and tables
- Automated schema discovery via Glue crawlers
- Business glossary with data dictionary
- Data lineage tracking (source → target)

**Metadata Enrichment**:
- Technical metadata: schema, data types, partitions
- Business metadata: descriptions, owners, stewards
- Operational metadata: row counts, last updated, SLAs
- Compliance metadata: PII classification, retention period

#### FR-5: Data Governance & Security

**Lake Formation Governance**:
- Database-level permissions by domain (Finance, HR, Sales, Operations)
- Table-level permissions by role (Admin, Engineer, Analyst, User)
- Column-level security for PII (e.g., SSN, salary, email)
- Row-level security for multi-tenancy (filter by department ID)

**Security Controls**:
| Control | Implementation |
|---------|----------------|
| **Authentication** | AWS IAM, federated with corporate SAML SSO |
| **Authorization** | Lake Formation grants, IAM policies |
| **Encryption at rest** | S3 SSE-KMS with customer-managed keys (CMK) |
| **Encryption in transit** | TLS 1.2+ for all API calls |
| **Network isolation** | VPC endpoints (PrivateLink), no internet exposure |
| **Audit logging** | CloudTrail (all API calls), S3 access logs, Lake Formation audit |
| **PII protection** | Masking, tokenization, encryption |
| **Secrets management** | AWS Secrets Manager for DB credentials, API keys |

#### FR-6: ETL / ELT Pipelines

**Orchestration**: AWS Step Functions for complex workflows

**Processing**:
- **AWS Glue**: Serverless Spark for ETL (PySpark scripts)
- **EMR Serverless**: For Spark jobs requiring custom configurations
- **Lambda**: Lightweight transformations, triggering

**Pipeline Patterns**:
1. **Full Load**: Initial historical data migration
2. **Incremental Load**: Timestamp-based (last_modified_date)
3. **CDC**: Change data capture via DMS
4. **Upsert**: MERGE INTO for idempotent loads
5. **Backfill**: Reprocess historical data after bug fixes

**Data Quality Gates**:
- Pre-load validation (schema, nullability, constraints)
- Post-load validation (row counts, reconciliation)
- Quality score publication to dashboard
- Pipeline failure and alert on quality degradation

#### FR-7: Query & Analytics

**Amazon Athena**:
- Serverless SQL queries on S3
- Support for Delta Lake, Parquet, JSON
- Workgroups for resource isolation and cost tracking
- Query result caching (5-minute TTL)

**Performance Optimizations**:
- Partition pruning (reduce data scanned)
- Predicate pushdown (filter early)
- Columnar format (Parquet/Delta Lake)
- Compression (Snappy for hot data, Zstd for cold)
- Z-ordering on commonly filtered columns

**Query SLAs**:
| Query Type | Data Scanned | Latency Target (p95) |
|------------|--------------|----------------------|
| Simple aggregates | <1GB | <5 seconds |
| Medium complexity | 1-10GB | <30 seconds |
| Complex joins | 10-100GB | <3 minutes |
| Exploratory (p99) | >100GB | <10 minutes |

#### FR-8: Data Quality Framework

**Great Expectations**:
- Expectation suites for each table
- Automated validation on every pipeline run
- HTML validation reports published to S3
- Slack/email alerts on failures

**Quality Rules**:
```python
# Example expectations
{
  "expect_table_row_count_to_be_between": {
    "min_value": 1000000,
    "max_value": 1100000  # Allow 10% variance
  },
  "expect_column_values_to_not_be_null": {
    "column_list": ["customer_id", "order_date", "amount"]
  },
  "expect_column_values_to_be_unique": {
    "column": "order_id"
  },
  "expect_column_values_to_be_between": {
    "column": "amount",
    "min_value": 0,
    "max_value": 1000000
  },
  "expect_column_values_to_match_regex": {
    "column": "email",
    "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  }
}
```

**Quality Dimensions Tracked**:
- Completeness: % of required fields populated
- Uniqueness: % of records with unique primary keys
- Validity: % of records passing business rules
- Consistency: % of records matching across systems
- Timeliness: Lag from source update to lakehouse availability

#### FR-9: Monitoring & Observability

**CloudWatch Dashboards**:
- **Pipeline Health**: Success/failure rates, duration, throughput
- **Data Quality**: Quality scores by domain, trend over time
- **Query Performance**: Latency (p50/p95/p99), data scanned, cost
- **Cost**: Daily/weekly/monthly spend by service and domain
- **Storage**: S3 bucket sizes, growth rate, lifecycle transitions

**Alerts** (SNS → Email/Slack):
- Pipeline failure or timeout
- Data quality score below 99%
- Query latency exceeding SLA
- Cost anomaly (>20% deviation from baseline)
- Security: unauthorized access attempts

#### FR-10: Disaster Recovery & Business Continuity

**Backup Strategy**:
- **S3 Versioning**: Enabled on all lakehouse buckets
- **Cross-Region Replication**: To us-west-2 (primary: us-east-1)
- **Glue Catalog**: Automated daily backup via AWS Backup
- **Code Repository**: Git with GitHub/CodeCommit

**Recovery Objectives**:
- **RPO (Recovery Point Objective)**: 15 minutes (acceptable data loss)
- **RTO (Recovery Time Objective)**: 1 hour (time to restore service)

**DR Testing**:
- Quarterly failover drills to DR region
- Annual full disaster simulation

---

## 📊 Data Domains Deep Dive

### 1. Finance Domain

#### Data Sources

| Source System | Type | Records | Update Frequency | Integration Method |
|---------------|------|---------|------------------|-------------------|
| Oracle ERP | OLTP | 50M transactions/year | Real-time | CDC via AWS DMS |
| SAP S/4HANA | OLTP | 10M journal entries/year | Daily batch | Full + incremental |
| Stripe API | REST API | 500K payments/month | Hourly | REST API polling |
| QuickBooks | SaaS | 2M invoices (small BUs) | Daily | QuickBooks API |

#### Key Entities

**Dimensions**:
- `dim_accounts`: Chart of accounts (10K rows, SCD Type 2)
- `dim_cost_centers`: Organizational hierarchy (500 rows, SCD Type 2)
- `dim_vendors`: Supplier master data (50K rows, SCD Type 2)
- `dim_customers`: Customer billing info (2M rows, SCD Type 2)

**Facts**:
- `fact_transactions`: General ledger transactions (50M rows/year, daily partitions)
- `fact_invoices`: AR invoices (20M rows/year, monthly partitions)
- `fact_payments`: Cash receipts and disbursements (10M rows/year)
- `fact_budget`: Annual budgets and forecasts (500K rows, static)

#### Business Metrics

**KPIs**:
- Revenue (actual, budget, variance)
- EBITDA and EBITDA margin
- Operating cash flow and free cash flow
- Days sales outstanding (DSO)
- Working capital turnover
- Cost of goods sold (COGS) by product line

**Reports**:
- Consolidated P&L and balance sheet
- Month-end, quarter-end, year-end close reports
- Budget vs. actuals with variance analysis
- Accounts receivable aging
- Vendor spend analysis

#### Compliance Requirements

- **SOX**: 7-year retention, immutable audit trail, segregation of duties
- **Tax**: Country-specific reporting (50+ jurisdictions)
- **Audit**: Support for external auditors (Big 4)

#### Data Quality Rules

```yaml
finance_quality_rules:
  fact_transactions:
    - debit_amount + credit_amount must equal 0 (double-entry accounting)
    - transaction_date must be within fiscal calendar
    - account_id must exist in dim_accounts
    - cost_center_id must be valid for transaction_date
  fact_invoices:
    - invoice_date <= payment_due_date
    - amount > 0
    - customer_id must exist in dim_customers
    - invoice_number must be unique
```

### 2. Human Resources Domain

#### Data Sources

| Source System | Type | Records | Update Frequency | Integration Method |
|---------------|------|---------|------------------|-------------------|
| Workday HCM | SaaS | 50K employees | Real-time | Workday API |
| ADP | SaaS | 50K employees | Weekly | SFTP file drop |
| Greenhouse | SaaS | 500K applications | Hourly | Greenhouse API |
| Culture Amp | SaaS | 45K survey responses | Quarterly | CSV export |

#### Key Entities

**Dimensions**:
- `dim_employees`: Employee master (50K rows, SCD Type 2 for history)
- `dim_positions`: Job titles and levels (500 rows)
- `dim_departments`: Org structure (200 rows, SCD Type 2)
- `dim_locations`: Office locations (80 rows)

**Facts**:
- `fact_payroll`: Bi-weekly payroll runs (5M rows/year)
- `fact_time_tracking`: Hourly time entries (100M rows/year)
- `fact_applications`: Job applications (500K rows/year)
- `fact_performance_reviews`: Annual/quarterly reviews (200K rows)

#### Business Metrics

**KPIs**:
- Headcount by department, location, level
- Attrition rate (voluntary vs. involuntary)
- Time-to-fill open positions
- Offer acceptance rate
- Employee satisfaction score (eNPS)
- Diversity metrics (gender, ethnicity, age)

**Reports**:
- Workforce planning and forecasting
- Recruitment funnel analysis
- Compensation benchmarking
- Performance distribution (rating curve)

#### Compliance Requirements

- **GDPR**: Right to erasure (employee data after termination + 2 years)
- **CCPA**: California employee privacy rights
- **EEO-1**: US diversity reporting
- **GDPR Article 9**: Special category data (health, union membership)

#### Sensitive Data

| Data Element | Classification | Protection Method |
|--------------|----------------|-------------------|
| SSN / National ID | Restricted | Encrypted, tokenized |
| Salary | Confidential | Column-level security |
| Medical info | PHI (HIPAA) | Encrypted, audit all access |
| Performance ratings | Confidential | RBAC, managers only |
| Home address | PII | Masked for analytics |

#### Data Quality Rules

```yaml
hr_quality_rules:
  dim_employees:
    - employee_id must be unique
    - hire_date <= termination_date (if terminated)
    - department_id must exist in dim_departments
    - email must be valid format and unique
  fact_payroll:
    - gross_pay = base_pay + overtime + bonuses - deductions
    - pay_period_end_date = pay_period_start_date + 13 days (bi-weekly)
    - employee_id must exist in dim_employees
```

### 3. Sales Domain

#### Data Sources

| Source System | Type | Records | Update Frequency | Integration Method |
|---------------|------|---------|------------------|-------------------|
| Salesforce | SaaS CRM | 10M opportunities | Real-time | Salesforce Bulk API |
| HubSpot | Marketing | 50M leads | Hourly | HubSpot API |
| Shopify Plus | E-commerce | 80M orders | Real-time webhook | Shopify API + S3 |
| Zendesk | Support | 20M tickets | Hourly | Zendesk API |

#### Key Entities

**Dimensions**:
- `dim_customers`: Customer master (2M rows, SCD Type 2)
- `dim_products`: Product catalog (100K SKUs, SCD Type 2)
- `dim_sales_reps`: Sales team (5K reps, SCD Type 2)
- `dim_campaigns`: Marketing campaigns (10K campaigns)

**Facts**:
- `fact_opportunities`: Sales pipeline (10M rows)
- `fact_orders`: Customer orders (80M rows/year, daily partitions)
- `fact_order_lines`: Line items (300M rows/year)
- `fact_support_tickets`: Customer support (20M rows/year)

#### Business Metrics

**KPIs**:
- Revenue (actual, forecast, quota attainment)
- Sales pipeline coverage (pipeline value / quota)
- Win rate (closed-won / total opportunities)
- Average deal size
- Sales cycle duration (days from lead to close)
- Customer acquisition cost (CAC)
- Customer lifetime value (CLV)
- Monthly recurring revenue (MRR), annual recurring revenue (ARR)
- Churn rate (logo churn, revenue churn)

**Reports**:
- Sales forecast by rep, region, product
- Pipeline health (stage distribution)
- Top customers by revenue
- Product performance analysis
- Customer cohort analysis

#### Compliance Requirements

- **GDPR**: Marketing consent management, opt-out tracking
- **CCPA**: Do not sell my personal information
- **CAN-SPAM**: Email marketing compliance
- **TCPA**: Telemarketing consent (US)

#### Data Quality Rules

```yaml
sales_quality_rules:
  fact_opportunities:
    - close_date >= created_date
    - amount > 0 for won opportunities
    - stage must progress forward (no skipping stages)
    - probability must be 0-100
  fact_orders:
    - order_date <= ship_date
    - total_amount = sum(order_lines.amount)
    - customer_id must exist in dim_customers
```

### 4. Operations Domain

#### Data Sources

| Source System | Type | Records | Update Frequency | Integration Method |
|---------------|------|---------|------------------|-------------------|
| IoT sensors | Streaming | 100K sensors, 10 events/sec | Real-time | AWS IoT Core → Kinesis |
| ERP inventory | OLTP | 500K inventory items | Hourly | CDC via DMS |
| Logistics APIs | REST | 30M shipments/year | Real-time | API polling |
| Quality control | RDBMS | 10M inspections/year | Daily batch | PostgreSQL dump |

#### Key Entities

**Dimensions**:
- `dim_locations`: Warehouses, factories (1K rows)
- `dim_equipment`: Manufacturing machines (10K rows, SCD Type 2)
- `dim_carriers`: Shipping companies (50 rows)
- `dim_inventory_items`: SKUs and raw materials (500K rows)

**Facts**:
- `fact_sensor_readings`: Time-series IoT data (500M rows/year, hourly partitions)
- `fact_shipments`: Outbound shipments (30M rows/year)
- `fact_inventory_transactions`: Stock movements (100M rows/year)
- `fact_quality_inspections`: QC results (10M rows/year)

#### Business Metrics

**KPIs**:
- Equipment utilization (uptime %)
- Overall equipment effectiveness (OEE)
- Mean time between failures (MTBF)
- Mean time to repair (MTTR)
- Inventory turnover ratio
- Order fill rate
- On-time delivery rate
- Defect rate (parts per million)

**Reports**:
- Equipment performance dashboards
- Predictive maintenance alerts
- Inventory aging analysis
- Shipment tracking
- Quality trends by supplier

#### Compliance Requirements

- **ISO 9001**: Quality management system
- **ISO 14001**: Environmental management (emissions tracking)
- **FDA 21 CFR Part 11**: Medical device manufacturing (Healthcare BU)

#### Data Quality Rules

```yaml
operations_quality_rules:
  fact_sensor_readings:
    - timestamp must be within last 1 hour (for real-time)
    - sensor_id must exist in dim_equipment
    - reading_value must be within sensor's min/max range
  fact_shipments:
    - ship_date <= delivery_date
    - tracking_number must be unique
    - carrier_id must exist in dim_carriers
```

---

## 🔒 Security Requirements

### 1. Identity & Access Management

#### Authentication

**Human Users**:
- Corporate SSO via SAML 2.0 (Okta/Azure AD)
- Multi-factor authentication (MFA) required for production access
- Session timeout: 8 hours (inactivity: 1 hour)

**Service Accounts**:
- IAM roles with temporary security credentials
- No long-lived access keys in production
- Secrets Manager for third-party API keys

#### Authorization Model

**Role Hierarchy**:
```
Roles:
├── Data Admin
│   ├── Full access to all databases and tables
│   ├── Lake Formation admin permissions
│   ├── Infrastructure deployment (Terraform)
│   └── Users: Data Platform team (5 members)
│
├── Data Engineer
│   ├── Read/write access to dev and staging
│   ├── Read-only access to production
│   ├── Deploy ETL pipelines
│   └── Users: Data Engineering team (15 members)
│
├── Data Analyst
│   ├── Read-only access to Gold layer (all domains)
│   ├── Query via Athena workgroups
│   ├── No PII columns without approval
│   └── Users: Analytics team (50 members)
│
├── Finance Analyst
│   ├── Read-only access to Finance Gold layer
│   ├── Limited Silver layer for troubleshooting
│   └── Users: Finance team (30 members)
│
├── HR Analyst (restricted)
│   ├── Read-only access to HR Gold layer
│   ├── Column-level security: masked PII
│   ├── Row-level security: own department only
│   └── Users: HR team (20 members)
│
└── Business User
    ├── Read-only access to curated datasets
    ├── Pre-built dashboards only
    └── Users: Executives, managers (5,000 members)
```

### 2. Data Encryption

#### Encryption at Rest

| Data Store | Encryption Method | Key Management |
|------------|-------------------|----------------|
| **S3 buckets** | SSE-KMS | Customer-managed CMK |
| **Glue Data Catalog** | AWS-managed encryption | AWS-managed key |
| **RDS (source DBs)** | Encrypted snapshots | AWS-managed key |
| **EBS volumes (EMR)** | Encrypted volumes | Customer-managed CMK |
| **CloudWatch Logs** | KMS encryption | Customer-managed CMK |

**KMS Key Rotation**: Automated annual rotation

#### Encryption in Transit

- **TLS 1.2+** for all AWS API calls
- **VPC endpoints** for AWS services (no internet egress)
- **HTTPS-only** bucket policies on S3
- **Signed URLs** for temporary data access (expiration: 1 hour)

### 3. Network Security

**VPC Architecture**:
```
VPC: datacorp-lakehouse-vpc (10.0.0.0/16)
├── Private Subnets (no internet route)
│   ├── Data processing (Glue, EMR)
│   ├── Database connectivity (DMS endpoints)
│   └── VPC endpoints (S3, Glue, STS, KMS)
├── Public Subnets (internet gateway for egress only)
│   └── NAT Gateway (for outbound API calls)
└── Security Groups
    ├── SG-Glue: Allow HTTPS to S3 VPC endpoint
    ├── SG-EMR: Allow Spark communication within cluster
    └── SG-RDS: Allow inbound from DMS replication instance
```

**No Direct Internet Access**:
- S3 accessed via VPC endpoint (PrivateLink)
- No S3 buckets with public read/write

### 4. PII Protection Strategy

#### PII Discovery

**Automated Classification**:
- AWS Glue Data Quality with regex patterns
- Custom classifiers for domain-specific PII
- Quarterly full scan of all lakehouse data

**PII Categories**:
| Category | Examples | Sensitivity |
|----------|----------|-------------|
| **Identifiers** | SSN, passport, driver's license | Critical |
| **Financial** | Credit card, bank account | Critical |
| **Contact** | Email, phone, address | High |
| **Biometric** | Fingerprint, facial image | Critical |
| **Health** | Medical records, prescriptions | Critical (PHI) |
| **Demographic** | Race, religion, sexual orientation | High (GDPR Article 9) |

#### PII Protection Methods

**Masking** (for analytics):
```python
# Email masking
john.doe@company.com → j***@company.com

# Phone masking
+1-555-555-1234 → +1-XXX-XXX-1234

# SSN masking
123-45-6789 → ***-**-6789
```

**Tokenization** (for reversibility):
```python
# Replace PII with random token, store mapping in Secrets Manager
john.doe@company.com → TOKEN_A7F8B9C3D2E1
```

**Encryption** (for highly sensitive):
```python
# Encrypt with KMS, store ciphertext
SSN: 123-45-6789 → [ENCRYPTED_BLOB_BASE64]
```

**Anonymization** (irreversible):
```python
# For ML models, remove PII entirely or aggregate
IP 192.168.1.100 → [ANONYMIZED] or 192.168.X.X
```

#### PII Access Controls

**Column-Level Security** (Lake Formation):
```sql
-- HR Analysts see masked salary
GRANT SELECT ON hr.dim_employees
(employee_id, name, department, masked_salary)
TO ROLE hr_analyst;

-- Finance Admins see actual salary
GRANT SELECT ON hr.dim_employees
(employee_id, name, department, salary)
TO ROLE finance_admin;
```

**Row-Level Security** (Lake Formation data filters):
```sql
-- HR Analysts only see own department
CREATE DATA FILTER hr_rls_filter
FOR TABLE hr.dim_employees
ROW FILTER department_id = current_user_department();
```

### 5. Audit & Logging

#### Logging Requirements

| Log Type | Retention | Purpose |
|----------|-----------|---------|
| **CloudTrail** | 365 days (S3) | All AWS API calls |
| **S3 Server Access Logs** | 90 days | Object-level access |
| **Lake Formation Audit** | 365 days | Query-level access to tables |
| **Glue Job Logs** | 30 days (CloudWatch) | ETL pipeline execution |
| **Athena Query History** | 45 days | Query performance, cost tracking |
| **Application Logs** | 30 days | Custom ETL scripts |

#### Audit Trail Requirements

**SOX Compliance**:
- Who accessed financial data (user, role, IP)
- What data was accessed (database, table, columns)
- When access occurred (timestamp)
- What action was performed (SELECT, UPDATE, DELETE)

**GDPR Compliance**:
- Log all PII access for data subject access requests
- Track consent changes with versioning
- Audit data deletion requests and fulfillment

#### Security Monitoring

**CloudWatch Alarms**:
- Unauthorized API calls (denied by IAM/Lake Formation)
- Root account usage (should be zero)
- MFA disabled on user accounts
- S3 bucket policy changes
- KMS key deletion attempts

**GuardDuty** (optional, +$50/month):
- Anomalous API behavior
- Compromised credentials
- Unusual data access patterns

---

## ✅ Acceptance Criteria

### 1. Functional Acceptance

#### Data Ingestion
- ✅ All 20+ data sources successfully ingested
- ✅ Batch ingestion completes within 4-hour window (2 AM - 6 AM EST)
- ✅ Streaming data appears in Bronze layer within 5 minutes
- ✅ Failed ingestions automatically quarantined with alerts
- ✅ Ingestion metadata captured (source, timestamp, row count)

#### Data Transformation
- ✅ Bronze → Silver transformation completes within 2 hours
- ✅ Silver → Gold aggregation completes within 1 hour
- ✅ Data quality score >99% at each layer
- ✅ Idempotent pipelines (can re-run without duplicates)
- ✅ Error handling with retry logic (3 attempts)

#### Query Performance
- ✅ Simple queries (1 table, <1GB): <5 seconds (p95)
- ✅ Complex queries (3+ tables, 10GB): <30 seconds (p95)
- ✅ Executive dashboards refresh in <2 minutes
- ✅ 50 concurrent queries without degradation

#### Data Governance
- ✅ Lake Formation permissions enforced for all users
- ✅ PII columns masked/encrypted for non-privileged users
- ✅ Row-level security filters by department
- ✅ Audit logs complete and queryable

### 2. Non-Functional Acceptance

#### Reliability
- ✅ 99.9% pipeline success rate (max 7 failures/month)
- ✅ RPO: 15 minutes (tested via DR drill)
- ✅ RTO: 1 hour (tested via DR drill)
- ✅ Zero data loss incidents

#### Security
- ✅ Penetration testing passed (no critical/high vulnerabilities)
- ✅ All S3 buckets encrypted with KMS
- ✅ No public access to any lakehouse components
- ✅ MFA enforced for all production access
- ✅ Secrets rotation automated (90 days)

#### Compliance
- ✅ GDPR checklist 100% complete
- ✅ CCPA compliance validated
- ✅ SOX controls documented and tested
- ✅ HIPAA BAA signed with AWS

#### Cost
- ✅ Development environment: ≤$150/month
- ✅ Production environment (projected): ≤$1,200/month
- ✅ Cost tracking by domain and workload
- ✅ Cost anomaly alerts configured

### 3. Test Scenarios

#### Test Scenario 1: End-to-End Pipeline

**Objective**: Validate data flows from source to Gold layer

**Steps**:
1. Insert 1,000 new records into source PostgreSQL (Finance)
2. Trigger CDC replication via DMS
3. Verify records appear in Raw layer within 5 minutes
4. Trigger Bronze pipeline, verify records in Bronze layer
5. Trigger Silver pipeline, verify data quality checks pass
6. Trigger Gold pipeline, verify aggregates updated
7. Query Athena, verify new data visible

**Expected Result**: All steps complete successfully, data available in <15 minutes

#### Test Scenario 2: Schema Evolution

**Objective**: Validate backward-compatible schema changes

**Steps**:
1. Add new column `discount_percent` to source table
2. Run Glue crawler to detect schema change
3. Append data with new column to Bronze Delta table (mergeSchema=true)
4. Update Silver transformation to include new column
5. Verify old records have NULL for new column, new records populated

**Expected Result**: No pipeline failures, new column available

#### Test Scenario 3: GDPR Data Deletion

**Objective**: Validate right to be forgotten

**Steps**:
1. Identify all records for customer_id=12345 (DSAR)
2. Execute deletion across all layers (Raw, Bronze, Silver, Gold)
3. Verify records deleted via Athena queries
4. Verify deletion logged in audit trail

**Expected Result**: All customer data deleted within 24 hours, audit trail complete

#### Test Scenario 4: Access Control

**Objective**: Validate Lake Formation permissions

**Steps**:
1. Attempt to query HR salary as Finance Analyst (should fail)
2. Attempt to query Finance data as HR Analyst (should fail)
3. Attempt to query own domain (should succeed)
4. Verify denials logged in Lake Formation audit log

**Expected Result**: Cross-domain access denied, audit logs complete

#### Test Scenario 5: Disaster Recovery

**Objective**: Validate DR procedures

**Steps**:
1. Simulate us-east-1 region failure (disable all resources)
2. Fail over to us-west-2 DR region
3. Verify S3 data replicated (CRR)
4. Restore Glue Data Catalog from backup
5. Execute test query via Athena in DR region
6. Measure time to restore service (RTO)

**Expected Result**: Service restored within 1 hour, data loss <15 minutes

#### Test Scenario 6: Performance Under Load

**Objective**: Validate concurrent query performance

**Steps**:
1. Simulate 50 concurrent Athena queries (Apache JMeter)
2. Mix of simple (1-table) and complex (multi-join) queries
3. Measure latency (p50, p95, p99)
4. Monitor CloudWatch for throttling or errors

**Expected Result**: All queries complete successfully, p95 latency within SLA

---

## 📈 Success Metrics & KPIs

### 1. Platform Adoption

| Metric | Baseline | Month 3 | Month 6 | Month 12 |
|--------|----------|---------|---------|----------|
| **Active Users** | 0 | 50 | 200 | 500 |
| **Daily Queries** | 0 | 500 | 2,000 | 10,000 |
| **Dashboards Created** | 0 | 20 | 100 | 300 |
| **Data Domains Onboarded** | 0 | 2 (Finance, HR) | 4 (all) | 4 + 10 sub-domains |
| **ML Models in Production** | 0 | 0 | 2 | 5 |

### 2. Data Quality

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Completeness** | 99.5% | % of required fields populated |
| **Accuracy** | 99.9% | % matching source reconciliation |
| **Timeliness** | 95% | % of pipelines completing within SLA |
| **Consistency** | 99.8% | % of cross-domain joins succeeding |
| **Uniqueness** | 99.9% | % of dimension records with unique PK |

### 3. Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Query Latency (p50)** | <10 sec | Athena CloudWatch metrics |
| **Query Latency (p95)** | <30 sec | Athena CloudWatch metrics |
| **Query Latency (p99)** | <60 sec | Athena CloudWatch metrics |
| **Pipeline Duration** | <4 hours | Glue job execution time |
| **Data Freshness** | <15 min | Time from source update to Gold layer |

### 4. Cost

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Monthly Dev Cost** | <$150 | AWS Cost Explorer |
| **Monthly Prod Cost** | <$1,200 | AWS Cost Explorer |
| **Cost per Query** | <$0.05 | Athena cost / query count |
| **Cost per GB Stored** | <$0.03 | S3 cost / data volume |
| **TCO Reduction** | 65% | Year-over-year comparison |

### 5. Reliability

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Pipeline Success Rate** | >99.5% | Successful runs / total runs |
| **Platform Uptime** | 99.9% | CloudWatch synthetic monitoring |
| **Data Loss Incidents** | 0 | Manual tracking |
| **Mean Time to Recovery** | <1 hour | Incident duration tracking |

### 6. Security & Compliance

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Unauthorized Access Attempts** | 0 successful | GuardDuty, CloudTrail analysis |
| **Compliance Audit Findings** | 0 critical | External audit results |
| **PII Exposure Incidents** | 0 | Macie/manual scans |
| **Patch Compliance** | 100% | AWS Systems Manager |

---

## 🗓️ Project Timeline

### Phase 0: Initiation (Week 1)
- Kickoff meeting with stakeholders
- AWS account setup and budgets
- Team onboarding and training
- Development environment provisioning

### Phase 1: Foundation (Weeks 2-4)
- Infrastructure as Code (Terraform)
- S3 bucket structure and lifecycle policies
- Glue Data Catalog databases
- Lake Formation initial setup
- VPC and networking
- IAM roles and policies

### Phase 2: Data Ingestion (Weeks 5-7)
- Finance domain: Oracle → Raw/Bronze (Week 5)
- HR domain: Workday → Raw/Bronze (Week 6)
- Sales domain: Salesforce → Raw/Bronze (Week 7)
- Operations domain: IoT → Raw/Bronze (Week 7)

### Phase 3: Data Transformation (Weeks 8-10)
- Delta Lake setup on Glue/EMR
- Finance Silver/Gold layers (Week 8)
- HR Silver/Gold layers (Week 9)
- Sales Silver/Gold layers (Week 10)
- Operations Silver/Gold layers (Week 10)

### Phase 4: Governance (Week 11)
- PII classification and tagging
- Lake Formation permissions (RBAC)
- Row/column-level security
- Data retention policies

### Phase 5: Monitoring & Quality (Week 12)
- CloudWatch dashboards
- Data quality framework (Great Expectations)
- Cost tracking and alerting
- Pipeline monitoring

### Phase 6: UAT & Hardening (Weeks 13-14)
- User acceptance testing
- Performance tuning
- Security hardening
- Documentation finalization

### Phase 7: Production Launch (Week 15)
- Stakeholder demo
- Production deployment
- Knowledge transfer
- Hypercare support (2 weeks)

**Total Duration**: 15 weeks (3.5 months)

---

## 🎓 Training & Enablement

### Data Engineering Team

**Curriculum**:
- AWS Glue and EMR Serverless (2 days)
- Delta Lake and lakehouse architecture (2 days)
- Lake Formation security (1 day)
- Great Expectations data quality (1 day)
- Terraform IaC (1 day)

### Data Analyst Team

**Curriculum**:
- Athena SQL best practices (1 day)
- Data catalog navigation (0.5 days)
- Dashboard creation (Tableau/QuickSight) (1 day)
- Data governance and RBAC (0.5 days)

### Business Users

**Curriculum**:
- Self-service analytics overview (2 hours)
- Pre-built dashboard training (1 hour)
- Data request process (1 hour)

---

## 📞 Stakeholder Communication Plan

### Executive Steering Committee

**Members**: CFO, CIO, Chief Data Officer, VP Finance, VP HR, VP Sales
**Frequency**: Monthly
**Format**: Executive dashboard (KPIs), project status, risks/issues

### Working Group

**Members**: Data platform lead, domain data engineers, BI leads
**Frequency**: Weekly
**Format**: Sprint review, demo, technical discussions

### End Users

**Members**: Analysts, data scientists, business users
**Frequency**: Bi-weekly
**Format**: Office hours, Q&A, feature announcements

---

## 🚨 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Cost overrun** | Medium | High | Daily cost monitoring, alerts at $100/$150 |
| **Data quality issues** | High | Critical | Robust validation, reconciliation with sources |
| **Performance degradation** | Medium | High | Load testing, query optimization, caching |
| **Security breach** | Low | Critical | Penetration testing, least-privilege IAM |
| **Scope creep** | High | Medium | Strict change control, prioritization |
| **Stakeholder resistance** | Medium | High | Early engagement, training, quick wins |
| **Vendor dependency** | Low | Medium | Use open standards (Delta Lake), avoid lock-in |

---

## 📚 Appendices

### Appendix A: Glossary

- **ACID**: Atomicity, Consistency, Isolation, Durability
- **CDC**: Change Data Capture
- **CMK**: Customer-Managed Key (KMS)
- **DSAR**: Data Subject Access Request (GDPR)
- **ELT**: Extract, Load, Transform
- **ETL**: Extract, Transform, Load
- **KMS**: AWS Key Management Service
- **PHI**: Protected Health Information (HIPAA)
- **PII**: Personally Identifiable Information
- **RBAC**: Role-Based Access Control
- **RPO**: Recovery Point Objective
- **RTO**: Recovery Time Objective
- **SCD**: Slowly Changing Dimension
- **TCO**: Total Cost of Ownership

### Appendix B: AWS Services Used

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| S3 | Lakehouse storage | $40-60/month |
| Glue | Serverless ETL, Data Catalog | $20-35/month |
| Athena | Serverless SQL queries | $10-20/month |
| Lake Formation | Governance and security | $5-10/month |
| EMR Serverless | Spark processing | $20-30/month (if used) |
| Step Functions | Workflow orchestration | $5/month |
| CloudWatch | Monitoring and logs | $10-15/month |
| KMS | Encryption key management | $5/month |
| Secrets Manager | Secrets storage | $2/month |
| DMS | Database replication | $15-20/month (if CDC) |
| VPC | Network isolation | $0 (VPC free, endpoints $7/month) |

### Appendix C: Reference Architectures

- AWS Analytics Reference Architecture: https://aws.amazon.com/architecture/analytics-big-data/
- AWS Lake Formation Workshop: https://github.com/aws-samples/aws-lake-formation-workshop
- Databricks Lakehouse Platform: https://www.databricks.com/product/data-lakehouse
- Netflix Data Platform: https://netflixtechblog.com/

---

**This project brief is a living document. Last updated: March 10, 2026.**

For questions or feedback, contact the Data Platform team: data-platform@datacorp.com
