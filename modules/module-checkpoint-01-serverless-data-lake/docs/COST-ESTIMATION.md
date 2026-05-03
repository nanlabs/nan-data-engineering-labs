# 💰 COST ESTIMATION: CloudMart Serverless Data Lake

## Document Control

| Attribute | Value |
|-----------|-------|
| **Project** | CloudMart Serverless Data Lake |
| **Version** | 1.0 |
| **Last Updated** | March 2026 |
| **Budget** | $50/month maximum |
| **Status** | Active |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [AWS Free Tier Coverage](#aws-free-tier-coverage)
3. [Cost Breakdown by Service](#cost-breakdown-by-service)
4. [Monthly Cost Estimate](#monthly-cost-estimate)
5. [Cost Optimization Strategies](#cost-optimization-strategies)
6. [Cost Monitoring Setup](#cost-monitoring-setup)
7. [Cost Comparison vs Alternatives](#cost-comparison-vs-alternatives)
8. [Scaling Cost Projections](#scaling-cost-projections)
9. [Cost Control Checklist](#cost-control-checklist)

---

## Executive Summary

### Budget Overview

| Category | Monthly Estimate | % of Budget |
|----------|-----------------|-------------|
| **Total Budget** | **$50.00** | **100%** |
| **Estimated Cost** | **$32.00** | **64%** |
| **Buffer** | **$18.00** | **36%** |

### Cost by Service

| AWS Service | Monthly Cost | Free Tier Coverage | Notes |
|-------------|-------------|-------------------|--------|
| **Amazon S3** | $8.50 | Partial (5GB free) | Storage for data lake |
| **AWS Lambda** | $2.00 | Full (1M requests free) | Data ingestion |
| **AWS Glue** | $15.00 | None | ETL transformations |
| **Amazon Athena** | $3.50 | None | SQL analytics |
| **CloudWatch** | $2.00 | Partial (5GB logs free) | Monitoring & logs |
| **Data Transfer** | $1.00 | 100GB free | S3/Athena transfers |
| **TOTAL** | **$32.00** | | |

### Key Takeaways

- ✅ **Well within budget:** $32/month vs. $50 limit (36% buffer)
- ✅ **90% cost savings** vs. traditional data warehouse ($400/month)
- ✅ **Free Tier leveraged:** Lambda fully covered, S3 partial
- ✅ **Scalable:** Can grow 2-3x before hitting budget limit
- ⚠️ **Monitor:** Glue is largest expense; optimize job runs

---

## AWS Free Tier Coverage

### Permanent Free Tier (Always Free)

These services remain free forever (not just 12 months):

| Service | Free Tier | Our Usage | Covered? |
|---------|-----------|-----------|----------|
| **Lambda** | 1M requests/month | ~30K requests/month | ✅ 100% |
| **CloudWatch Logs** | 5GB ingestion/month | ~2GB/month | ✅ 100% |
| **CloudWatch Metrics** | 10 custom metrics | ~5 metrics | ✅ 100% |
| **CloudWatch Alarms** | 10 alarms | ~8 alarms | ✅ 100% |
| **SNS** | 1,000 notifications | ~50/month | ✅ 100% |
| **Data Transfer IN** | Always free | ~10GB/month | ✅ 100% |

### 12-Month Free Tier (New AWS Accounts)

If you're within 12 months of AWS account creation:

| Service | Free Tier | Our Usage | Covered? |
|---------|-----------|-----------|----------|
| **S3 Standard** | 5GB storage | 110GB | ⚠️ Partial (5GB free, 105GB paid) |
| **S3 GET** | 20,000 requests | ~5,000/month | ✅ 100% |
| **S3 PUT** | 2,000 requests | ~1,000/month | ✅ 100% |
| **Data Transfer OUT** | 15GB/month | <1GB/month | ✅ 100% |

### Services with NO Free Tier

| Service | Pricing Model | Our Usage |
|---------|--------------|-----------|
| **AWS Glue** | $0.44 per DPU-hour | ~2 DPU-hours/day |
| **Amazon Athena** | $5.00 per TB scanned | ~40GB scanned/month |
| **S3 (over Free Tier)** | $0.023 per GB/month | 105GB |

---

## Cost Breakdown by Service

### 1. Amazon S3 (Object Storage)

**Purpose:** Store all data lake zones (Raw, Processed, Curated)

#### Storage Costs

**Pricing:**
- **S3 Standard:** $0.023 per GB/month (first 50TB)
- **S3 Standard-IA:** $0.0125 per GB/month (infrequent access)
- **S3 Glacier:** $0.004 per GB/month (archive)

**Data Volume (Month 1):**
- Raw (Bronze): 110GB JSON/CSV (gzip compressed)
- Processed (Silver): 35GB Parquet (3:1 compression ratio)
- Curated (Gold): 5GB Parquet (pre-aggregated)
- **Total:** 150GB

**Storage Cost Calculation:**
```
Free Tier: 5GB (first 12 months)
Paid Storage: 145GB

Standard Storage (80%): 116GB × $0.023 = $2.67
Standard-IA (20%): 29GB × $0.0125 = $0.36

Total Storage Cost: $3.03/month
```

#### Request Costs

**Pricing:**
- **PUT/POST:** $0.005 per 1,000 requests
- **GET/SELECT:** $0.0004 per 1,000 requests

**Monthly Requests:**
- PUT (data ingestion): 1,000 files/day × 30 days = 30,000 requests
- GET (Glue/Athena reads): 10,000 requests/month

**Request Cost Calculation:**
```
PUT: (30,000 - 2,000 free) / 1,000 × $0.005 = $0.14
GET: (10,000 - 20,000 free) / 1,000 × $0.0004 = $0.00 (covered by Free Tier)

Total Request Cost: $0.14/month
```

#### Lifecycle Transitions

**Pricing:** $0.01 per 1,000 transition requests

**Transitions:**
- Raw data to Glacier after 90 days: ~30 transitions/month

**Transition Cost:**
```
30 / 1,000 × $0.01 = $0.00 (negligible)
```

#### Data Transfer

**Pricing:**
- Data Transfer IN: Free
- Data Transfer OUT to Internet: $0.09 per GB (after 15GB free)
- Transfer within AWS (S3 → Glue/Lambda): Free

**Monthly Transfers:**
- Internet OUT: <1GB (Athena results download)

**Transfer Cost:** $0.00 (within Free Tier)

#### **S3 Total: $3.20/month**

---

### 2. AWS Lambda (Serverless Compute)

**Purpose:** Data ingestion and validation

#### Compute Costs

**Pricing:**
- **Requests:** $0.20 per 1M requests
- **Duration:** $0.0000166667 per GB-second

**Lambda Configuration:**
- **Memory:** 512MB (0.5GB)
- **Avg Duration:** 2 seconds per invocation
- **Invocations:** 1,000 files/day × 30 days = 30,000/month

**Compute Cost Calculation:**
```
Requests:
  30,000 requests (within 1M free) = $0.00

Duration:
  GB-seconds = 0.5GB × 2 seconds × 30,000 = 30,000 GB-seconds
  Free Tier: 400,000 GB-seconds
  Paid: 0 GB-seconds

Total Compute Cost: $0.00 (fully covered by Free Tier)
```

#### **Lambda Total: $0.00/month (Free Tier)**

---

### 3. AWS Glue (ETL Service)

**Purpose:** Data transformation (Bronze → Silver → Gold)

#### Glue Data Catalog

**Pricing:**
- **First 1M objects stored:** Free
- **First 1M requests:** Free
- **Over 1M:** $1.00 per 100,000 objects

**Our Usage:**
- Objects: ~100 tables/partitions (well within Free Tier)

**Catalog Cost:** $0.00

#### Glue Crawlers

**Pricing:** $0.44 per DPU-hour

**Crawler Configuration:**
- **DPUs:** 2 (default)
- **Runtime:** 5 minutes per crawl
- **Frequency:** 3 times/day (Raw, Processed, Curated crawlers)

**Crawler Cost Calculation:**
```
Daily Runtime: 3 crawls × 5 minutes = 15 minutes = 0.25 hours
Monthly Runtime: 0.25 hours × 30 days = 7.5 DPU-hours

Cost: 7.5 DPU-hours × $0.44 = $3.30/month
```

#### Glue ETL Jobs

**Pricing:** $0.44 per DPU-hour

**Job Configuration:**
- **Bronze → Silver Job:**
  - Workers: 2 (G.1X = 1 DPU each)
  - Runtime: 10 minutes
  - Frequency: Daily

- **Silver → Gold Job:**
  - Workers: 2 (G.1X = 1 DPU each)
  - Runtime: 5 minutes
  - Frequency: Daily

**ETL Cost Calculation:**
```
Bronze → Silver:
  Daily: 2 DPUs × (10/60) hours = 0.33 DPU-hours
  Monthly: 0.33 × 30 = 10 DPU-hours × $0.44 = $4.40

Silver → Gold:
  Daily: 2 DPUs × (5/60) hours = 0.17 DPU-hours
  Monthly: 0.17 × 30 = 5 DPU-hours × $0.44 = $2.20

Total ETL Cost: $6.60/month
```

#### **Glue Total: $9.90/month**

---

### 4. Amazon Athena (Query Engine)

**Purpose:** SQL analytics on data lake

#### Query Costs

**Pricing:** $5.00 per TB of data scanned

**Query Patterns:**
- **Development/Testing:** 50 queries/week scanning 500MB avg = 25GB/month
- **Business Queries:** 100 queries/week scanning 100MB avg = 10GB/month
- **Total Scanned:** 35GB/month = 0.035TB

**Query Cost Calculation:**
```
Data Scanned: 0.035TB × $5.00 = $0.175 ≈ $0.18/month
```

**Note:** Parquet columnar format and partitioning drastically reduce data scanned compared to CSV/JSON.

#### **Athena Total: $0.20/month**

---

### 5. Amazon CloudWatch (Monitoring)

**Purpose:** Logs, metrics, dashboards, and alarms

#### CloudWatch Logs

**Pricing:**
- **Ingestion:** $0.50 per GB
- **Storage:** $0.03 per GB/month
- **Free Tier:** 5GB ingestion/month

**Log Volume:**
- Lambda logs: 1GB/month
- Glue logs: 0.5GB/month
- **Total:** 1.5GB/month (within Free Tier)

**Logs Cost:** $0.00

#### CloudWatch Metrics

**Pricing:**
- **Custom Metrics:** $0.30 per metric/month
- **Free Tier:** 10 custom metrics

**Our Metrics:** 5 custom metrics (within Free Tier)

**Metrics Cost:** $0.00

#### CloudWatch Alarms

**Pricing:** $0.10 per alarm/month (after 10 free)

**Our Alarms:** 8 alarms (within Free Tier)

**Alarms Cost:** $0.00

#### CloudWatch Dashboards

**Pricing:** $3.00 per dashboard/month

**Our Dashboards:** 1 dashboard

**Dashboard Cost:** $3.00/month

#### **CloudWatch Total: $3.00/month**

---

### 6. AWS IAM (Identity and Access Management)

**Pricing:** Free (no charge)

---

### 7. Amazon SNS (Simple Notification Service)

**Purpose:** Alert notifications

**Pricing:**
- **First 1,000 notifications:** Free
- **Email delivery:** $0.00

**Our Usage:** ~50 notifications/month (alerts)

**SNS Cost:** $0.00 (Free Tier)

---

### 8. AWS CloudTrail (Audit Logging)

**Pricing:**
- **First trail:** Free (management events)
- **Additional trails:** $2.00/trail/month

**Our Usage:** 1 trail (default)

**CloudTrail Cost:** $0.00

---

### 9. Data Transfer

**Pricing:**
- **IN:** Free
- **OUT (first 15GB):** Free (12-month Free Tier)
- **OUT (over 15GB):** $0.09/GB
- **Within AWS:** Free

**Our Usage:** <1GB internet OUT (mostly inter-service transfers)

**Transfer Cost:** $0.00 (Free Tier)

---

## Monthly Cost Estimate

### Base Estimate (Month 1)

| Service | Cost | Notes |
|---------|------|-------|
| Amazon S3 | $3.20 | 150GB storage, 30K PUT requests |
| AWS Lambda | $0.00 | Within Free Tier (30K invocations) |
| AWS Glue | $9.90 | Crawlers ($3.30) + ETL Jobs ($6.60) |
| Amazon Athena | $0.20 | 35GB data scanned |
| CloudWatch | $3.00 | 1 dashboard (logs/metrics/alarms free) |
| SNS | $0.00 | Within Free Tier |
| CloudTrail | $0.00 | First trail free |
| Data Transfer | $0.00 | Within Free Tier |
| **TOTAL** | **$16.30** | **Base case** |

### Realistic Estimate (with buffer)

| Scenario | Cost | Notes |
|----------|------|-------|
| **Minimum** | $16.30 | Base usage, perfect optimization |
| **Expected** | $25.00 | Add: experimentation, mistakes, retries |
| **Maximum** | $40.00 | Add: heavy testing, suboptimal queries |
| **Budget** | $50.00 | Hard limit |

**Recommendation:** Plan for **$25-30/month** to account for learning curve and experimentation.

---

## Cost Optimization Strategies

### 1. S3 Storage Optimization

#### Strategy: Leverage Storage Classes

**Implementation:**
```yaml
LifecyclePolicy:
  Rules:
    - Id: TransitionToIA
      Status: Enabled
      Transitions:
        - Days: 30
          StorageClass: STANDARD_IA  # For older data
        - Days: 90
          StorageClass: GLACIER       # For archival
```

**Savings:**
- Standard: $0.023/GB
- Standard-IA: $0.0125/GB (46% savings)
- Glacier: $0.004/GB (83% savings)

**Estimated Monthly Savings:** $1.50

#### Strategy: Enable S3 Intelligent-Tiering

**How:** Automatically moves data between tiers based on access patterns

**Cost:** Small monitoring fee ($0.0025 per 1,000 objects)

**Savings:** 10-30% on storage costs

#### Strategy: Compress Data

**Format:** Use gzip for JSON/CSV, Snappy for Parquet

**Compression Ratios:**
- JSON: 5-10x compression
- CSV: 3-5x compression
- Parquet: 3-5x additional compression

**Estimated Monthly Savings:** Already factored in ($3-5)

---

### 2. Lambda Optimization

#### Strategy: Right-Size Memory Allocation

**Problem:** Over-provisioned memory = wasted cost

**Solution:** Use AWS Lambda Power Tuning tool

**Optimal Configuration:**
- Orders ingestion: 512MB (not 1024MB)
- Clickstream: 256MB (simple validation)

**Savings:** Avoid over-provisioning (already at $0 due to Free Tier)

#### Strategy: Reuse Connections

**Implementation:**
```python
import boto3

# Initialize outside handler (reused across invocations)
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Reuse s3_client (no reconnection overhead)
    s3_client.put_object(...)
```

**Savings:** Reduce execution time = lower GB-seconds

---

### 3. Glue Job Optimization

**Glue is the largest expense ($9.90/month). Optimize here first.**

#### Strategy: Reduce DPUs

**Current:** 2 DPUs (G.1X workers)
**Optimization:** Monitor job metrics, reduce to 1 DPU if possible

**Calculation:**
```
Current: 2 DPUs × 15 min/day × 30 days × $0.44/DPU-hour = $6.60
Optimized: 1 DPU × 30 min/day × 30 days × $0.44/DPU-hour = $6.60 (same total time)
```

**Note:** Fewer workers = longer runtime. Find balance.

#### Strategy: Enable Job Bookmarks

**Benefit:** Process only new data (incremental), not full dataset

**Implementation:**
```python
job.init(args['JOB_NAME'], args)
job.commit()  # Track processed data
```

**Savings:** 50-90% reduction in job runtime (process only delta)

**Estimated Monthly Savings:** $3-5

#### Strategy: Optimize Spark Code

**Tips:**
- Use predicate pushdown (filter early)
- Avoid `collect()` (pulls all data to driver)
- Partition data appropriately
- Use broadcast joins for small tables

**Estimated Monthly Savings:** 20-30% runtime reduction = $2

#### Strategy: Schedule Jobs Efficiently

**Current:** Daily at 3 AM UTC
**Optimization:** Combine jobs if possible

**Example:**
```python
# Instead of 3 separate jobs, create 1 job with 3 scripts
# Saves 2 × 2-minute startup overhead per day
```

---

### 4. Athena Query Optimization

#### Strategy: Use Partitioning

**Problem:** Full table scans are expensive

**Solution:**
```sql
-- Bad (scans 1TB)
SELECT * FROM orders;

-- Good (scans 3 days = 3GB)
SELECT * FROM orders
WHERE year = '2026' AND month = '03'
  AND day IN ('07', '08', '09');
```

**Savings:** 90%+ reduction in data scanned

**Estimated Monthly Savings:** $2-3

#### Strategy: Select Only Needed Columns

**Problem:** `SELECT *` scans all columns

**Solution:**
```sql
-- Bad (scans 100GB)
SELECT * FROM orders;

-- Good (scans 10GB for 2 columns)
SELECT order_id, total_amount FROM orders;
```

**Savings:** 90% in this example

#### Strategy: Use Parquet Format

**Already Implemented:** Parquet is columnar (only selected columns scanned)

**Benefit:** 10-30x less data scanned vs. JSON

#### Strategy: Create Views for Common Queries

**Implementation:**
```sql
CREATE VIEW daily_revenue AS
SELECT
    year, month, day,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY year, month, day;

-- Users query view (pre-aggregated, tiny scan)
SELECT * FROM daily_revenue
WHERE year = '2026' AND month = '03';
```

**Savings:** Users query 1MB instead of 10GB

---

### 5. CloudWatch Cost Control

#### Strategy: Adjust Log Retention

**Current:** 30 days (default)
**Optimization:** Reduce to 7 days for verbose logs

**Implementation:**
```bash
aws logs put-retention-policy \
  --log-group-name /aws/lambda/cloudmart-ingest-orders \
  --retention-in-days 7
```

**Savings:** Reduce storage cost (already at $0 due to Free Tier)

#### Strategy: Disable Verbose Logging in Production

**Development:** `logging.DEBUG`
**Production:** `logging.INFO` or `logging.WARNING`

**Savings:** 50-80% less log volume

#### Strategy: Use Metric Filters Instead of Logs

**Problem:** Storing logs for metrics is expensive

**Solution:** Extract metrics from logs, then delete logs

**Estimated Monthly Savings:** $0.50 (if over Free Tier)

---

### 6. Budget Alerts and Monitoring

#### Strategy: Set Up AWS Budgets

**Implementation:**
```yaml
Budget:
  Name: CloudMart-Monthly-Budget
  Amount: 50
  Currency: USD
  TimeUnit: MONTHLY
  Alerts:
    - Threshold: 80%  # Alert at $40
      NotificationType: EMAIL
      Subscribers:
        - your-email@example.com
```

**Benefit:** Proactive cost awareness

#### Strategy: Daily Cost Tracking

**Tool:** AWS Cost Explorer

**Actions:**
- Review daily costs
- Identify unexpected spikes
- Investigate anomalies immediately

---

## Cost Monitoring Setup

### 1. AWS Cost Explorer

**Enable:**
1. AWS Console → Billing → Cost Explorer
2. Enable Cost Explorer (free)

**Views to Monitor:**
- **Daily Costs:** Identify spikes
- **Service Breakdown:** Which service is expensive?
- **Forecasted Costs:** Project end-of-month total

### 2. AWS Budgets

**Setup:**
```bash
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json:**
```json
{
  "BudgetName": "CloudMart-DataLake-Monthly",
  "BudgetLimit": {
    "Amount": "50",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

**notifications.json:**
```json
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "your-email@example.com"
      }
    ]
  }
]
```

### 3. CloudWatch Billing Alarms

**Setup:**
```yaml
BillingAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: Monthly-Cost-Exceeds-40
    MetricName: EstimatedCharges
    Namespace: AWS/Billing
    Statistic: Maximum
    Period: 21600  # 6 hours
    EvaluationPeriods: 1
    Threshold: 40
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref AlertSNSTopic
    Dimensions:
      - Name: Currency
        Value: USD
```

### 4. Tag-Based Cost Allocation

**Implementation:**
```yaml
Tags:
  - Key: Project
    Value: CloudMart
  - Key: Environment
    Value: dev
  - Key: Owner
    Value: data-engineering
```

**Benefit:** Track costs by project, environment, owner

**Activate:**
1. AWS Console → Billing → Cost Allocation Tags
2. Activate tags (takes 24 hours to appear)

---

## Cost Comparison vs Alternatives

### Serverless Data Lake vs. Traditional Approaches

| Solution | Monthly Cost | Savings |
|----------|-------------|---------|
| **Our Serverless Data Lake** | **$25** | **Baseline** |
| Redshift (dc2.large) | $180 | ❌ $155 more expensive |
| EMR (3 x m5.xlarge) | $500 | ❌ $475 more expensive |
| RDS (db.m5.large) | $150 | ❌ $125 more expensive |
| Snowflake (Standard) | $200+ | ❌ $175+ more expensive |

### Cost Breakdown: Serverless vs. Redshift

| Component | Serverless | Redshift | Savings |
|-----------|-----------|----------|---------|
| **Storage** | S3: $3/month | Redshift: $25/month (200GB) | **$22** |
| **Compute** | Lambda: $0 | Always-on cluster: $180 | **$180** |
| **ETL** | Glue: $10/month | Redshift + EMR: $500 | **$490** |
| **Queries** | Athena: $0.20/month | Included (but cluster cost) | **$0** |
| **Total** | **$25** | **$500+** | **$475 (95% savings)** |

**Conclusion:** Serverless is **20x cheaper** than traditional data warehouse for our scale.

---

## Scaling Cost Projections

### 3-Month Projection

| Service | Month 1 | Month 2 | Month 3 | Notes |
|---------|---------|---------|---------|-------|
| S3 | $3 | $5 | $7 | Cumulative storage growth |
| Lambda | $0 | $0 | $0 | Still in Free Tier |
| Glue | $10 | $12 | $15 | More data = longer jobs |
| Athena | $0.20 | $0.50 | $1.00 | More users querying |
| CloudWatch | $3 | $3 | $3 | Fixed |
| **Total** | **$16** | **$21** | **$26** | Still under budget |

### 6-Month Projection

| Service | Month 6 | Notes |
|---------|---------|-------|
| S3 | $12 | 500GB cumulative storage |
| Lambda | $0.50 | Approaching Free Tier limit |
| Glue | $20 | 2x data volume |
| Athena | $2.00 | More business users |
| CloudWatch | $3 | Fixed |
| **Total** | **$37.50** | Still under $50 budget |

### 12-Month Projection (Post Free Tier)

| Service | Month 12 | Free Tier Impact |
|---------|----------|------------------|
| S3 | $20 | Full 1TB storage ($23 - optimizations) |
| Lambda | $2.00 | No Free Tier (but still cheap) |
| Glue | $25 | 3x data volume |
| Athena | $5.00 | 30 business users |
| CloudWatch | $5 | Logs over Free Tier |
| **Total** | **$57** | Need optimization or budget increase |

**Action:** At Month 12, re-evaluate budget or implement aggressive optimizations.

---

## Cost Control Checklist

### Setup Phase

- [ ] Enable AWS Free Tier notifications
- [ ] Set up AWS Budget ($50/month)
- [ ] Configure billing alerts (80%, 90%, 100%)
- [ ] Enable Cost Allocation Tags
- [ ] Set up CloudWatch billing dashboard
- [ ] Document cost baseline ($25-30/month)

### Development Phase

- [ ] Right-size Lambda memory (use Power Tuning)
- [ ] Enable Glue job bookmarks (incremental processing)
- [ ] Implement S3 lifecycle policies (transition to IA/Glacier)
- [ ] Use Parquet format (3-5x compression)
- [ ] Partition data by date (optimize Athena)
- [ ] Create Athena views for common queries
- [ ] Avoid `SELECT *` in queries
- [ ] Set Glue job timeout limits
- [ ] Configure CloudWatch log retention (7-30 days)

### Operational Phase

- [ ] Review costs daily (first week)
- [ ] Review costs weekly (ongoing)
- [ ] Investigate any $10+ unexpected charges immediately
- [ ] Monitor largest cost drivers (Glue, S3)
- [ ] Optimize slow Glue jobs (reduce DPUs if possible)
- [ ] Educate business users on query costs
- [ ] Archive old data to Glacier after 90 days
- [ ] Delete unnecessary test S3 buckets
- [ ] Stop unused Glue crawlers/jobs
- [ ] Clean up Athena query results periodically

### Monthly Review

- [ ] Month-end cost reconciliation
- [ ] Compare actual vs. estimated costs
- [ ] Identify cost anomalies
- [ ] Update cost projections
- [ ] Document lessons learned
- [ ] Adjust optimization strategies

---

## Tips for Staying Under Budget

### 1. Delete Resources When Not in Use

**Development:**
- Disable crawlers when not needed
- Stop Glue jobs during testing breaks
- Delete test S3 objects regularly

### 2. Avoid Runaway Costs

**Lambda:**
- Set reserved concurrency (max 10 functions)
- Configure dead letter queues (prevent retry loops)
- Set maximum event age (1 hour)

**Glue:**
- Set job timeout (30 minutes max)
- Monitor job failures (stop expensive failures)
- Use job bookmarks (don't reprocess all data)

### 3. Test with Small Datasets First

- Start with 1-day data, not 1-month
- Validate logic before scaling
- Catch expensive mistakes early

### 4. Use AWS Cost Calculator

**Tool:** [AWS Pricing Calculator](https://calculator.aws/)

**Use for:** Estimate costs before deploying new services

### 5. Clean Up After Testing

```bash
# Delete all S3 objects in test buckets
aws s3 rm s3://cloudmart-test-bucket --recursive

# Delete test buckets
aws s3 rb s3://cloudmart-test-bucket

# Delete unused Lambda functions
aws lambda delete-function --function-name test-function
```

---

## Conclusion

### Summary

- ✅ **Estimated Monthly Cost:** $25-30 (well under $50 budget)
- ✅ **Free Tier Coverage:** Lambda, CloudWatch Logs/Metrics, SNS
- ✅ **Largest Expense:** Glue ($10/month) - optimize here
- ✅ **Scalability:** Can handle 2-3x growth before hitting budget limit
- ✅ **Savings vs. Alternatives:** 90-95% cheaper than traditional data warehouse

### Recommendations

1. **Start Conservative:** Use minimum resources, scale up if needed
2. **Monitor Daily:** First week, check costs daily to establish baseline
3. **Enable Alerts:** 80% budget threshold ($40/month)
4. **Optimize Early:** Implement Glue job bookmarks and S3 lifecycle policies from Day 1
5. **Document:** Track what works and what doesn't for cost optimization

### Success Criteria

- [ ] Monthly cost <$50 (hard limit)
- [ ] Costs tracked and explained (no surprises)
- [ ] Optimization strategies documented
- [ ] Budget alerts configured and tested
- [ ] Team educated on cost-conscious practices

---

## Resources

- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/home#/cost-explorer)
- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [AWS Cost Optimization Best Practices](https://aws.amazon.com/pricing/cost-optimization/)
- [S3 Storage Classes](https://aws.amazon.com/s3/storage-classes/)
- [Glue Pricing](https://aws.amazon.com/glue/pricing/)
- [Athena Pricing](https://aws.amazon.com/athena/pricing/)

---

**Document Version:** 1.0
**Last Updated:** March 9, 2026
**Next Review:** Monthly during first 3 months of implementation
