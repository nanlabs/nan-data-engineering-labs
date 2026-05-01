# GlobalMart Data Lake Design - Detailed Scenario

## Company Background

**GlobalMart** is a fast-growing e-commerce platform with:
- 2M active customers across 15 countries
- 50K products across 20 categories
- $500M annual revenue
- 1M transactions per day
- 10M user events per day (clicks, searches, views)

## Current State (The Problem)

### Existing Architecture
```
s3://globalmart-data/
├── transactions.csv (500GB, mixed dates)
├── users.json (50GB, duplicates)
├── events/ (2TB, unorganized)
├── products/ (10GB, outdated)
└── logs/ (1TB, never accessed)
```

### Pain Points

1. **No Organization:**
   - All data in one bucket
   - No clear structure
   - Can't find specific data
   - 45 minutes average to locate dataset

2. **High Costs:**
   - 3.5TB in S3 Standard: $80/month
   - Storing everything indefinitely
   - No compression (CSV, JSON)
   - 40% of data never accessed after 30 days

3. **Performance Issues:**
   - Athena queries take 15+ minutes
   - Scanning entire bucket for single day
   - No partitioning
   - CSV format (slow to parse)

4. **Compliance Problems:**
   - Customer PII not encrypted
   - No access logging
   - No data retention policy
   - GDPR violations risk

5. **Data Quality:**
   - Duplicates in user data
   - Invalid transactions not filtered
   - No schema validation
   - Mixed data formats

## Desired State (The Solution)

### Medallion Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GLOBALMART DATA LAKE                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🥉 BRONZE (Raw)          🥈 SILVER (Cleaned)    🥇 GOLD (Curated)│
│  ├── transactions/        ├── transactions/      ├── analytics/   │
│  ├── events/              ├── users/             │   ├── daily/   │
│  ├── products/            ├── products/          │   ├── weekly/  │
│  └── logs/                └── events/            │   └── monthly/ │
│                                                   ├── ml_features/ │
│  Format: CSV, JSON        Format: Parquet        ├── reports/     │
│  Retention: 2 years       Retention: 1 year      └── dashboards/  │
│  Lifecycle: Glacier       Lifecycle: IA          Retention: 3 years│
└─────────────────────────────────────────────────────────────┘
```

### Target Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Storage Cost | $80/month | $48/month | 40% reduction |
| Query Time | 15 minutes | 30 seconds | 97% faster |
| Data Discovery | 45 minutes | 2 minutes | 95% faster |
| Storage Size | 3.5TB | 1.2TB | 66% reduction |

## Technical Requirements

### 1. Bronze Layer Specifications

**Bucket:** `globalmart-bronze-{environment}`

**Purpose:** Store raw data exactly as received from sources

**Structure:**
```
s3://globalmart-bronze-dev/
├── transactions/
│   └── year=2024/month=02/day=02/
│       ├── batch_001_20240202_100530.csv
│       ├── batch_002_20240202_103045.csv
│       └── batch_003_20240202_110215.csv
├── events/
│   └── year=2024/month=02/day=02/hour=10/
│       └── events_20240202_10.json.gz
├── products/
│   └── ingestion_date=2024-02-02/
│       └── catalog_snapshot_20240202_120000.json
└── users/
    └── year=2024/month=02/day=02/
        └── users_delta_20240202.csv
```

**Configuration:**
- **Versioning:** Enabled (protect against accidental deletes)
- **Encryption:** SSE-S3 (AES-256)
- **Lifecycle:**
  - 0-30 days: S3 Standard
  - 31-90 days: S3 Standard-IA
  - 91+ days: S3 Glacier
- **Access Logging:** Enabled → `globalmart-logs-{env}`
- **Public Access:** Blocked (all 4 settings)
- **Tags:**
  - Environment: dev/prod
  - Layer: bronze
  - CostCenter: engineering
  - DataClassification: raw

**Partitioning:**
- Date-based (Hive-style): `year=YYYY/month=MM/day=DD/`
- For streaming data: add `hour=HH/`

**Retention:** 2 years (then delete)

### 2. Silver Layer Specifications

**Bucket:** `globalmart-silver-{environment}`

**Purpose:** Store validated, cleaned, deduplicated data

**Structure:**
```
s3://globalmart-silver-dev/
├── transactions/
│   └── year=2024/month=02/day=02/
│       └── transactions.parquet
├── users/
│   └── country=US/state=CA/
│       └── users.parquet
├── products/
│   └── category=electronics/
│       └── products.parquet
└── events/
    └── event_type=purchase/year=2024/month=02/
        └── events.parquet
```

**Transformations Applied:**
- ✅ Schema validation
- ✅ Deduplication
- ✅ Data type enforcement
- ✅ Null handling
- ✅ Format conversion (CSV/JSON → Parquet)
- ✅ Compression (Snappy)

**Configuration:**
- **Versioning:** Enabled
- **Encryption:** SSE-S3
- **Lifecycle:**
  - 0-90 days: S3 Standard
  - 91+ days: S3 Standard-IA
- **Access Logging:** Enabled
- **Public Access:** Blocked
- **Tags:**
  - Environment: dev/prod
  - Layer: silver
  - CostCenter: engineering
  - DataClassification: cleaned

**Format:** Parquet with Snappy compression

**Partitioning:**
- Transactions: `year/month/day`
- Users: `country/state` (for GDPR)
- Products: `category`
- Events: `event_type/year/month`

**Retention:** 1 year

### 3. Gold Layer Specifications

**Bucket:** `globalmart-gold-{environment}`

**Purpose:** Pre-aggregated, business-ready datasets

**Structure:**
```
s3://globalmart-gold-dev/
├── analytics/
│   ├── daily_sales_summary/
│   │   └── date=2024-02-02/
│   │       └── summary.parquet
│   ├── customer_360/
│   │   └── snapshot_date=2024-02-02/
│   │       └── customer_360.parquet
│   └── product_performance/
│       └── month=2024-02/
│           └── performance.parquet
├── ml_features/
│   ├── churn_features/
│   ├── recommendation_features/
│   └── fraud_detection_features/
└── reports/
    ├── executive_dashboard/
    └── operational_metrics/
```

**Business Logic Applied:**
- Daily/weekly/monthly aggregations
- Customer 360 views
- Product performance metrics
- Feature engineering for ML
- Denormalization for BI tools

**Configuration:**
- **Versioning:** Enabled
- **Encryption:** SSE-S3
- **Lifecycle:**
  - All data: S3 Standard (frequently accessed)
- **Access Logging:** Enabled
- **Public Access:** Blocked
- **Tags:**
  - Environment: dev/prod
  - Layer: gold
  - CostCenter: business-intelligence
  - DataClassification: aggregated

**Format:** Parquet with Snappy compression

**Optimization:**
- Small file sizes (compacted)
- Pre-aggregated
- Z-ordering on filter columns (bonus)

**Retention:** 3 years

### 4. Access Control Requirements

**Data Engineers:**
```yaml
Permissions:
  - Read/Write: Bronze (all)
  - Read/Write: Silver (all)
  - Read only: Gold
Actions:
  - s3:PutObject
  - s3:GetObject
  - s3:ListBucket
  - s3:DeleteObject (Bronze only)
```

**Data Scientists:**
```yaml
Permissions:
  - Read only: Silver, Gold
  - No access: Bronze
Actions:
  - s3:GetObject
  - s3:ListBucket
```

**BI Analysts:**
```yaml
Permissions:
  - Read only: Gold
Actions:
  - s3:GetObject
  - s3:ListBucket
  - athena:StartQueryExecution
```

### 5. Cost Optimization

**Storage Classes:**
```
Bronze:
  0-30 days:  S3 Standard ($0.023/GB)
  31-90 days: S3 Standard-IA ($0.0125/GB)
  91+ days:   S3 Glacier ($0.004/GB)

Silver:
  0-90 days:  S3 Standard
  91+ days:   S3 Standard-IA

Gold:
  All data:   S3 Standard (frequent access)
```

**Expected Cost Breakdown:**

| Layer | Raw Size | Compressed | Monthly Cost |
|-------|----------|------------|--------------|
| Bronze | 1.5TB | 400GB | $15 (mixed tiers) |
| Silver | 1.0TB | 200GB | $5 (mostly IA) |
| Gold | 1.0TB | 600GB | $28 (Standard) |
| **Total** | **3.5TB** | **1.2TB** | **$48/month** |

**Savings:** $32/month (40% reduction)

### 6. Naming Conventions

**Buckets:**
```
{company}-{layer}-{environment}
Examples:
  - globalmart-bronze-dev
  - globalmart-silver-prod
  - globalmart-gold-dev
```

**Objects (Files):**
```
Bronze: {entity}_{date}_{time}_{batch}.{format}
  Example: transactions_20240202_100530_001.csv

Silver: {entity}.parquet
  Example: transactions.parquet

Gold: {metric}_{aggregation}.parquet
  Example: daily_sales_summary_2024-02-02.parquet
```

**Partitions:**
```
Hive-style: key=value/
  year=2024/month=02/day=02/
  country=US/state=CA/
  event_type=purchase/
```

## Deliverables

Your CloudFormation template should create:

1. ✅ 3 S3 Buckets (Bronze, Silver, Gold)
2. ✅ Lifecycle policies on each bucket
3. ✅ Versioning enabled
4. ✅ Encryption (SSE-S3)
5. ✅ Access logging
6. ✅ Block public access
7. ✅ Tags for cost allocation
8. ✅ IAM roles (DataEngineer, DataScientist, Analyst)
9. ✅ Bucket policies for access control
10. ✅ S3 Access Points (bonus)

## Acceptance Criteria

- [ ] All 3 buckets created successfully
- [ ] Lifecycle rules configured correctly
- [ ] Versioning enabled on all buckets
- [ ] Encryption at rest configured
- [ ] Access logging enabled
- [ ] Public access blocked
- [ ] Proper tags applied
- [ ] IAM roles created with correct permissions
- [ ] Can upload file to Bronze
- [ ] Can query Silver with Athena
- [ ] Total estimated cost < $50/month
- [ ] All validation tests pass

## Testing Your Solution

1. **Deploy the stack:**
   ```bash
   aws cloudformation create-stack \
     --stack-name globalmart-data-lake \
     --template-body file://solution/data-lake-stack.yaml \
     --parameters ParameterKey=Environment,ParameterValue=dev \
     --capabilities CAPABILITY_IAM
   ```

2. **Upload test data:**
   ```bash
   aws s3 cp test-data.csv s3://globalmart-bronze-dev/transactions/year=2024/month=02/day=02/
   ```

3. **Verify structure:**
   ```bash
   aws s3 ls s3://globalmart-bronze-dev/ --recursive
   aws s3 ls s3://globalmart-silver-dev/ --recursive
   aws s3 ls s3://globalmart-gold-dev/ --recursive
   ```

4. **Check configuration:**
   ```bash
   aws s3api get-bucket-versioning --bucket globalmart-bronze-dev
   aws s3api get-bucket-encryption --bucket globalmart-bronze-dev
   aws s3api get-bucket-lifecycle-configuration --bucket globalmart-bronze-dev
   ```

5. **Run validation tests:**
   ```bash
   cd ../../validation
   pytest test_exercise_01.py -v
   ```

## Success Metrics

After implementation:
- ✅ 66% storage reduction (3.5TB → 1.2TB)
- ✅ 40% cost reduction ($80 → $48/month)
- ✅ 97% faster queries (15min → 30sec)
- ✅ 95% faster data discovery (45min → 2min)
- ✅ GDPR compliant (encryption + retention)
- ✅ Clear data lineage (Bronze → Silver → Gold)

Good luck! 🚀
