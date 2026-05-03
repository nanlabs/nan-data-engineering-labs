# Enterprise Data Lakehouse - Cost Estimation

## 📊 Executive Summary

This document provides comprehensive cost estimates and optimization strategies for the Enterprise Data Lakehouse project. Cost projections cover both development and production environments across AWS services.

### Quick Summary

| Environment | Monthly Cost | Annual Cost | Key Drivers |
|-------------|--------------|-------------|-------------|
| **Development** | $100-150 | $1,200-1,800 | S3 storage, Glue/EMR compute |
| **Production (Year 1)** | $800-1,200 | $9,600-14,400 | Full-scale data, 500+ users |
| **Production (Steady State)** | $600-900 | $7,200-10,800 | Post-optimization |

### Cost Optimization Impact

| Metric | Before Lakehouse | After Lakehouse | Savings |
|--------|------------------|-----------------|---------|
| **Annual TCO** | $8,000,000 | $2,800,000 | **$5,200,000 (65%)** |
| **Cost per TB** | $800/TB/month | $80/TB/month | **90% reduction** |
| **Cost per Query** | $2.50 | $0.05 | **98% reduction** |

---

## 🏗️ Development Environment Costs

### Baseline Assumptions

- **Data Volume**: 1TB (sample dataset, 10% of production)
- **Users**: 5 data engineers + 10 analysts
- **Workload**: Daily ETL (Bronze/Silver/Gold), ad-hoc queries
- **Retention**: Raw 30 days, Bronze 90 days, Silver/Gold 1 year
- **Region**: us-east-1 (Virginia)

### Detailed Cost Breakdown

#### 1. Amazon S3 Storage

**Components**:
- Raw layer (landing zone)
- Bronze layer (ingested Parquet)
- Silver layer (cleaned Delta Lake)
- Gold layer (aggregates)
- Athena query results
- Logs and metadata

| Layer | Data Volume | Storage Class | Unit Price | Monthly Cost |
|-------|-------------|---------------|------------|--------------|
| **Raw** | 100GB (transient) | Standard | $0.023/GB | $2.30 |
| **Bronze** | 300GB (compressed Parquet) | Standard | $0.023/GB | $6.90 |
| **Silver** | 400GB (Delta Lake) | Standard | $0.023/GB | $9.20 |
| **Gold** | 200GB (aggregates) | Standard | $0.023/GB | $4.60 |
| **Athena Results** | 50GB | Standard | $0.023/GB | $1.15 |
| **Logs** | 50GB | Standard | $0.023/GB | $1.15 |
| **Subtotal** | 1,100GB | | | **$25.30** |

**With S3 Intelligent-Tiering** (automatic cost optimization):
- 30% of data moves to Infrequent Access after 30 days: -$7
- 20% moves to Archive Access after 90 days: -$3
- **Optimized Monthly Cost**: **$15-20**

**Storage Growth**:
- 30% YoY growth = +10GB/month
- Annual storage cost increase: ~$40/year (manageable)

#### 2. AWS Glue

**Components**:
- ETL Jobs (DPU-hours)
- Crawlers (DPU-hours)
- Data Catalog (tables, partitions)
- Data Quality checks

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **ETL Jobs** | 50 DPU-hours/month | $0.44/DPU-hour | $22 |
| **Crawlers** | 10 DPU-hours/month | $0.44/DPU-hour | $4.40 |
| **Data Catalog** | 100 tables, 5K partitions | First 1M objects free | $0 |
| **Data Quality** | Included in ETL | N/A | $0 |
| **Subtotal** | | | **$26.40** |

**ETL Job Breakdown**:
- Daily Bronze ETL: 5 DPU × 1 hour × 30 days = 150 DPU-hours → $66/month
- Daily Silver ETL: 3 DPU × 30 min × 30 days = 45 DPU-hours → $19.80/month
- Daily Gold ETL: 2 DPU × 15 min × 30 days = 15 DPU-hours → $6.60/month

**Optimization**:
- Use Glue's auto-scaling (G.2X workers dynamically allocate)
- Run jobs only when data changes (EventBridge triggers vs. fixed schedule)
- Optimize job code to reduce duration by 30%
- **Optimized Monthly Cost**: **$20-25**

#### 3. Amazon Athena

**Query Volume**:
- 15 analysts × 20 queries/day × 21 workdays = 6,300 queries/month
- Average data scanned: 200MB per query (with partitioning)

| Metric | Value | Unit Price | Monthly Cost |
|--------|-------|------------|--------------|
| **Data Scanned** | 1.26 TB | $5/TB | $6.30 |
| **Query Result Caching** | 50% hit rate | -50% cost | -$3.15 |
| **Subtotal** | | | **$3.15** |

**Without Optimization**:
- Average data scanned: 2GB per query (full table scans)
- Cost: 12.6 TB × $5 = **$63/month**

**Optimization Strategies**:
1. **Partitioning**: Reduce scans by 90% (date partitions)
2. **Query Result Reuse**: 5-minute cache TTL (50% hit rate)
3. **Columnar Format**: Parquet/Delta Lake (scan only needed columns)
4. **CTAS for Common Queries**: Pre-aggregate expensive reports

**Optimized Monthly Cost**: **$3-5**

#### 4. AWS Lake Formation

**Services**:
- Data access management (no direct charge)
- CloudTrail logging for audit (charges apply)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Lake Formation** | Managed service | No additional charge | $0 |
| **CloudTrail Logs** | 5GB/month | $0.50/GB ingestion | $2.50 |
| **Subtotal** | | | **$2.50** |

#### 5. Amazon EMR Serverless

**Usage**:
- 2-3 ad-hoc jobs per week for advanced analytics
- 5 DPU × 2 hours × 12 jobs = 120 DPU-hours/month

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Serverless Spark** | 120 DPU-hours | $0.052/DPU-hour | $6.24 |
| **Pre-initialized Capacity** | Optional (faster start) | $0.014/vCPU-hour | $0 (off for dev) |
| **Subtotal** | | | **$6-8** |

**Alternative: EMR on EC2**:
- 3 × m5.xlarge (24/7): $350/month
- **Savings with Serverless**: 95% ($344/month saved)

#### 6. AWS KMS (Encryption)

**Keys**:
- 1 Customer-Managed Key (CMK) for all lakehouse encryption

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **CMK** | 1 key | $1/month | $1 |
| **API Requests** | 100K requests | $0.03/10K | $0.30 |
| **Subtotal** | | | **$1.30** |

**Multi-Key vs. Single-Key**:
- Alternative: Separate CMK per domain (Finance, HR, Sales, Operations) = $4/month
- **Savings**: $2.70/month (68% reduction)
- **Trade-off**: Less isolation but sufficient for dev environment

#### 7. AWS Secrets Manager

**Secrets**:
- Database credentials: 3 RDS sources
- API keys: 5 third-party integrations
- Service account tokens: 2

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Secrets Storage** | 10 secrets | $0.40/secret | $4 |
| **API Calls** | 10K calls/month | $0.05/10K | $0.05 |
| **Subtotal** | | | **$4-5** |

**Optimization**:
- Use environment variables for non-sensitive config (reduce secrets count)
- Cache secrets in Lambda (reduce API calls)
- **Optimized Monthly Cost**: **$3-4**

#### 8. AWS CloudWatch

**Metrics & Logs**:
- ETL job logs
- CloudTrail logs
- Custom metrics (data quality, pipeline duration)
- Alarms

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Log Ingestion** | 10GB/month | $0.50/GB | $5 |
| **Log Storage** | 50GB | $0.03/GB | $1.50 |
| **Metrics** | 50 custom metrics | $0.30/metric | $15 |
| **Alarms** | 20 alarms | $0.10/alarm | $2 |
| **Dashboards** | 3 dashboards | $3/dashboard | $9 |
| **Subtotal** | | | **$32.50** |

**Optimization**:
- Filter logs to reduce ingestion (exclude DEBUG, INFO levels in production)
- Archive logs to S3 after 30 days ($0.023/GB vs. $0.03/GB)
- Delete low-value metrics (e.g., per-table row counts, aggregate at domain level)
- Use shared alarms (e.g., "Any ETL job failed" vs. per-job alarms)

**Optimized Monthly Cost**: **$10-15**

#### 9. AWS Step Functions

**Workflow Orchestration**:
- Daily ETL workflow: Bronze → Silver → Gold
- Triggered 1x/day

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **State Transitions** | 10 steps × 30 days = 300 | $0.025/1K transitions | $0.01 |
| **Subtotal** | | | **<$1** |

**Alternative: Apache Airflow on MWAA**:
- Minimum: $300/month (overkill for dev)
- **Savings with Step Functions**: 99.7% ($299/month saved)

#### 10. AWS DMS (Optional - CDC)

**Usage**:
- Replicate 3 RDS databases to Raw layer
- 10GB daily change data capture

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Replication Instance** | dms.t3.medium (on-demand) | $0.102/hour | $75 |
| **Data Transfer** | 300GB/month | Free (same region) | $0 |
| **Subtotal** | | | **$75** |

**Optimization**:
- Use DMS only for initial migration, then switch to nightly exports
- **Alternative**: `mysqldump` + S3 upload = $0 (acceptable for dev)

**Optional for Dev**: **$0** (use batch exports instead)

#### 11. Data Transfer & Networking

**Transfers**:
- S3 to Glue/Athena: Free (same region)
- S3 to EMR: Free (same region)
- Internet egress: Minimal (only for API calls)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Internet Egress** | 5GB/month | $0.09/GB | $0.45 |
| **VPC Endpoints** | 2 endpoints (S3, Glue) | $0.01/hour × 730 | $14.60 |
| **Subtotal** | | | **$15** |

**Optimization**:
- Use VPC endpoints to avoid internet egress charges
- **Optimized Monthly Cost**: **$10-15**

---

### Development Environment Summary

| Service | Baseline Cost | Optimized Cost | Optimization % |
|---------|---------------|----------------|----------------|
| **S3 Storage** | $25 | $18 | 28% |
| **Glue** | $26 | $22 | 15% |
| **Athena** | $6 | $4 | 33% |
| **Lake Formation** | $3 | $3 | 0% |
| **EMR Serverless** | $8 | $6 | 25% |
| **KMS** | $2 | $1 | 50% |
| **Secrets Manager** | $5 | $3 | 40% |
| **CloudWatch** | $33 | $12 | 64% |
| **Step Functions** | <$1 | <$1 | 0% |
| **DMS** | $75 (opt) | $0 | 100% |
| **Networking** | $15 | $12 | 20% |
| **TOTAL** | **$198** | **$81** | **59%** |

**With aggressive optimization and excluding DMS**: **$80-100/month** ✅ Meets $100-150 budget

---

## 🏭 Production Environment Costs

### Assumptions

- **Data Volume**: 10TB (full production dataset)
- **Users**: 500 (50 analysts, 400 business users, 50 data scientists)
- **Workload**: Daily batch ETL (2TB processed) + hourly incremental (100GB)
- **Query Volume**: 10,000 queries/day
- **Availability**: 99.9% (Three 9s)
- **Region**: us-east-1 (primary) + us-west-2 (DR)

### Detailed Cost Breakdown

#### 1. Amazon S3 Storage (Production)

| Layer | Data Volume | Storage Class | Unit Price | Monthly Cost |
|-------|-------------|---------------|------------|--------------|
| **Raw** | 500GB (transient) | Standard | $0.023/GB | $11.50 |
| **Bronze** | 3TB (compressed) | Standard → IA (30d) | $0.023 → $0.0125 | $37.50 → $20 |
| **Silver** | 4TB (Delta Lake) | Intelligent-Tiering | $0.023 (avg) | $92 |
| **Gold** | 2TB (aggregates) | Intelligent-Tiering | $0.023 (avg) | $46 |
| **Archive** | 1TB (historical) | Glacier Instant Retrieval | $0.004/GB | $4 |
| **Subtotal** | 10.5TB | | | **$180** |

**With Optimizations**:
- Compression: Snappy (3:1 ratio) → -$60
- Lifecycle policies: Auto-archive after 90 days → -$30
- Delete Raw after 30 days → -$8
- **Optimized Monthly Cost**: **$120-150**

**Cross-Region Replication (DR)**:
- Replicate 50% of data (active tables only)
- Replication cost: $0.02/GB for 5TB = $100/month
- Storage in us-west-2: 5TB × $0.023 = $115/month
- **DR Total**: **$215/month additional**

#### 2. AWS Glue (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Daily Batch ETL** | 200 DPU × 4 hours × 30 = 24K DPU-hours | $0.44/DPU-hour | $10,560 |
| **Hourly Incremental** | 20 DPU × 0.5 hour × 24 × 30 = 7.2K DPU-hours | $0.44/DPU-hour | $3,168 |
| **Crawlers** | 50 DPU-hours/month | $0.44/DPU-hour | $22 |
| **Subtotal** | | | **$13,750** |

**Optimization**:
- Use Glue auto-scaling (provision 200 max DPU, use 80 average) → -$5,280
- Optimize Spark code (30% faster) → -$4,125
- Incremental loads only (skip unchanged data) → -$1,000
- **Optimized Monthly Cost**: **$3,000-4,000**

**Alternative: EMR Serverless**:
- Same workload: 31,200 DPU-hours × $0.052 = **$1,622/month**
- **Decision**: Use EMR Serverless for production → **$1,600-2,000/month**

#### 3. Amazon Athena (Production)

**Query Volume**:
- 500 users × 20 queries/day × 21 workdays = 210,000 queries/month
- Average data scanned: 500MB per query (with partitioning)

| Metric | Value | Unit Price | Monthly Cost |
|--------|-------|------------|--------------|
| **Data Scanned** | 105TB | $5/TB | $525 |
| **Query Result Caching** | 60% hit rate | -60% | -$315 |
| **Net Cost** | 42TB | $5/TB | **$210** |

**Athena Workgroup Pricing** (Alternative for predictable costs):
- Reserved capacity: $0.30/DPU-hour (vs. $0.50/TB effective on-demand)
- For heavy users, provision 100 DPUs → $21,900/month
- **Decision**: Stick with on-demand pricing ($210 < $21,900)

**Optimization**:
- CTAS for top 20 queries (caching pre-aggregates) → -$50
- BI tool query optimization (reduce scans) → -$30
- Enforce partition filters in Tableau data sources → -$40
- **Optimized Monthly Cost**: **$90-150**

#### 4. AWS Lake Formation (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Service** | Managed | No charge | $0 |
| **CloudTrail Logs** | 50GB/month | $0.50/GB | $25 |
| **Subtotal** | | | **$25** |

#### 5. AWS KMS (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **CMK** | 1 shared key | $1/month | $1 |
| **API Requests** | 10M requests | $0.03/10K | $30 |
| **Subtotal** | | | **$31** |

**Optimization**:
- Enable KMS request caching in Glue/EMR (reduce API calls by 80%) → -$24
- **Optimized Monthly Cost**: **$7-10**

#### 6. AWS Secrets Manager (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Secrets** | 20 secrets | $0.40/secret | $8 |
| **API Calls** | 100K/month | $0.05/10K | $0.50 |
| **Subtotal** | | | **$8.50** |

#### 7. AWS CloudWatch (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Log Ingestion** | 100GB/month | $0.50/GB | $50 |
| **Log Storage** | 500GB | $0.03/GB | $15 |
| **Metrics** | 200 custom metrics | $0.30/metric | $60 |
| **Alarms** | 100 alarms | $0.10/alarm | $10 |
| **Dashboards** | 10 dashboards | $3/dashboard | $30 |
| **Subtotal** | | | **$165** |

**Optimization**:
- Archive logs to S3 after 7 days → -$40
- Use metric filters to reduce custom metrics → -$30
- Consolidate alarms (composite alarms) → -$5
- **Optimized Monthly Cost**: **$90-120**

#### 8. AWS Step Functions (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **State Transitions** | 50 steps × 30 daily + 10 steps × 720 hourly = 8,700 | $0.025/1K | $0.22 |
| **Subtotal** | | | **<$1** |

#### 9. AWS DMS (Production - Optional)

**Usage**:
- CDC for 5 RDS databases
- 100GB daily changes

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Replication Instance** | dms.r5.xlarge (on-demand) | $0.405/hour | $296 |
| **Data Transfer** | 3TB/month | Free (same region) | $0 |
| **Subtotal** | | | **$296** |

**Optimization**:
- Use Reserved Instances (1-year upfront) → 40% savings → **$177/month**

**Alternative**:
- Native RDS exports to S3 (free) + incremental timestamp-based loads
- **Savings**: $177/month (100%)

**Decision**: Use native exports for batch, DMS only if real-time CDC required (IoT workloads) → **$0-180/month**

#### 10. Amazon QuickSight (BI Tool)

**Users**:
- 50 Authors (analysts creating dashboards): $18/user = $900/month
- 400 Readers (business users consuming dashboards): $0.30/session, avg 10 sessions/user/month = $1,200/month

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **Authors** | 50 users | $18/user | $900 |
| **Readers** | 400 users, 4K sessions | $0.30/session | $1,200 |
| **SPICE** | 100GB (optional in-memory) | $0.38/GB | $38 |
| **Subtotal** | | | **$2,138** |

**Alternative: Tableau Server**:
- Licensing: $70/user × 450 = $31,500/month (ouch!)
- **Savings with QuickSight**: 93% ($29,362/month)

**Alternative: Open-Source (Apache Superset)**:
- Licensing: Free
- Infrastructure: EC2 t3.large 24/7 = $70/month
- Maintenance: Engineer time = $5,000/month equivalent
- **Decision**: QuickSight is cost-effective at scale

**Optimization**:
- Limit Reader sessions (10 → 5 per user/month) → -$600
- Use dashboard emails instead of live sessions → -$300
- **Optimized Monthly Cost**: **$1,200-1,500**

#### 11. Amazon RDS (Source Databases - Optional)

If DataCorp sources are external, no cost here. If internal:

| Instance | Type | Unit Price | Monthly Cost |
|----------|------|------------|--------------|
| **Finance DB** | db.r5.xlarge (on-demand) | $0.360/hour | $263 |
| **HR DB** | db.m5.large (on-demand) | $0.192/hour | $140 |
| **Sales DB** | db.r5.2xlarge (on-demand) | $0.720/hour | $526 |
| **Subtotal** | | | **$929** |

**With Reserved Instances** (1-year, all upfront):
- Savings: 40% → **$557/month**

**Out of Scope**: Assuming source databases are owned by application teams. Not included in lakehouse budget.

#### 12. Data Transfer & Networking (Production)

| Component | Usage | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| **S3 to Glue/Athena** | 100TB/month | Free (same region) | $0 |
| **Cross-Region Replication** | 5TB/month | $0.02/GB | $100 |
| **Internet Egress** | 50GB/month | $0.09/GB | $4.50 |
| **VPC Endpoints** | 5 endpoints × 730 hours | $0.01/hour | $36.50 |
| **Subtotal** | | | **$141** |

---

### Production Environment Summary (Year 1)

| Service | Monthly Cost | Annual Cost | Notes |
|---------|--------------|-------------|-------|
| **S3 Storage** | $180 | $2,160 | Base storage |
| **S3 (DR Replication)** | $215 | $2,580 | Cross-region replication |
| **EMR Serverless** | $2,000 | $24,000 | ETL compute |
| **Athena** | $210 | $2,520 | Query engine |
| **Lake Formation** | $25 | $300 | Governance |
| **KMS** | $31 | $372 | Encryption |
| **Secrets Manager** | $9 | $108 | Credentials |
| **CloudWatch** | $165 | $1,980 | Monitoring |
| **Step Functions** | <$1 | $10 | Orchestration |
| **DMS (optional)** | $180 | $2,160 | CDC (if needed) |
| **QuickSight** | $2,138 | $25,656 | BI tool |
| **Networking** | $141 | $1,692 | Data transfer |
| **TOTAL** | **$5,294** | **$63,538** | Year 1 baseline |

**With Optimizations**:

| Service | Optimized Monthly | Annual | Savings |
|---------|------------------|--------|---------|
| **S3 Storage** | $120 | $1,440 | $720 |
| **S3 (DR Replication)** | $215 | $2,580 | $0 (required) |
| **EMR Serverless** | $1,600 | $19,200 | $4,800 |
| **Athena** | $120 | $1,440 | $1,080 |
| **Lake Formation** | $25 | $300 | $0 |
| **KMS** | $8 | $96 | $276 |
| **Secrets Manager** | $8 | $96 | $12 |
| **CloudWatch** | $100 | $1,200 | $780 |
| **Step Functions** | <$1 | $10 | $0 |
| **DMS (skipped)** | $0 | $0 | $2,160 |
| **QuickSight** | $1,300 | $15,600 | $10,056 |
| **Networking** | $120 | $1,440 | $252 |
| **TOTAL** | **$3,616** | **$43,392** | **$20,136 (32%)** |

---

## 💰 Cost Optimization Strategies

### 1. S3 Storage Optimization

#### Strategy 1.1: Intelligent-Tiering (Automatic)

**Implementation**:
```bash
# Enable Intelligent-Tiering on lakehouse bucket
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket datacorp-lakehouse-prod \
  --id EntireBucket \
  --intelligent-tiering-configuration '{
    "Id": "EntireBucket",
    "Status": "Enabled",
    "Tiering": {
      "Days": 90,
      "AccessTier": "ARCHIVE_ACCESS"
    }
  }'
```

**Savings**: 40% on infrequently accessed data (automatic transitions)

#### Strategy 1.2: Lifecycle Policies

```bash
# Lifecycle policy: Raw → Delete after 30 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket datacorp-lakehouse-prod \
  --lifecycle-configuration '{
    "Rules": [
      {
        "Id": "DeleteRawAfter30Days",
        "Status": "Enabled",
        "Filter": {"Prefix": "raw/"},
        "Expiration": {"Days": 30}
      },
      {
        "Id": "ArchiveBronzeAfter90Days",
        "Status": "Enabled",
        "Filter": {"Prefix": "bronze/"},
        "Transitions": [
          {"Days": 90, "StorageClass": "GLACIER_IR"}
        ]
      }
    ]
  }'
```

**Savings**: $30-50/month by deleting transient data and archiving cold data

#### Strategy 1.3: Compression

**Parquet Compression Benchmarks**:
| Codec | Compression Ratio | Read Performance | Write Performance |
|-------|------------------|------------------|-------------------|
| **Snappy** | 3:1 | Fastest (baseline) | Fastest (baseline) |
| **Gzip** | 5:1 | 30% slower | 50% slower |
| **Zstd** | 4:1 | 10% slower | 20% slower |
| **LZ4** | 2.5:1 | 10% faster | 5% faster |

**Recommendation**:
- **Hot data** (last 30 days): Snappy (balance compression + speed)
- **Warm data** (30-90 days): Zstd (better compression, acceptable speed)
- **Cold data** (90+ days): Gzip (max compression, rarely accessed)

**Implementation**:
```python
# PySpark example
df.write.mode("overwrite") \
  .option("compression", "snappy") \
  .parquet("s3://lakehouse/bronze/finance/")
```

**Savings**: 66% storage reduction (1TB → 330GB) → **$15/month saved per TB**

### 2. Compute Optimization

#### Strategy 2.1: Right-Size Glue/EMR Jobs

**Before Optimization**:
- Job uses 200 DPUs but only needs 80 DPUs
- Over-provisioned by 150%
- Cost: $0.44 × 200 DPUs × 4 hours = $352

**After Optimization**:
- Profile job with Spark UI (identify bottlenecks)
- Reduce parallelism, tune memory settings
- Use 80 DPUs
- Cost: $0.44 × 80 DPUs × 4 hours = **$140** → **$212 saved**

**Tools**:
- AWS Glue Metrics (CloudWatch)
- Spark UI (execution time per stage)
- AWS Glue Job Insights (auto-generated recommendations)

#### Strategy 2.2: Spot Instances for EMR

**Implementation**:
```bash
# Create EMR Serverless app with spot instance policy
aws emr-serverless create-application \
  --name lakehouse-emr-spot \
  --type SPARK \
  --release-label emr-6.9.0 \
  --initial-capacity '{
    "DRIVER": {
      "workerCount": 1,
      "resourceConfiguration": {
        "cpu": "4vCPU",
        "memory": "16GB"
      }
    },
    "EXECUTOR": {
      "workerCount": 10,
      "resourceConfiguration": {
        "cpu": "4vCPU",
        "memory": "16GB"
      }
    }
  }' \
  --maximum-capacity '{
    "cpu": "400vCPU",
    "memory": "1600GB"
  }'
  # Note: EMR Serverless uses on-demand pricing by default
  # For spot, use EMR on EC2 with instance fleets
```

**Spot Pricing for EMR on EC2**:
- **m5.4xlarge** on-demand: $0.768/hour
- **m5.4xlarge** spot (average): $0.230/hour (70% savings)
- **Risk**: Spot interruptions (mitigate with checkpointing)

**When to Use Spot**:
- ✅ Non-critical batch jobs (can retry)
- ✅ Jobs with checkpointing (Spark savepoints)
- ❌ Real-time / SLA-critical workloads

**Savings**: 70% on compute → **$480/month saved** (EMR on EC2 cluster)

#### Strategy 2.3: Batch Jobs Only When Data Changes

**Before**:
- Daily ETL runs regardless of data changes
- 30 runs/month, 10 runs process 0 new records → wasted $132

**After**:
- Use S3 EventBridge trigger on new file arrival
- Run ETL only when raw data lands
- 20-25 runs/month → **$44-88 saved**

**Implementation**:
```python
# Lambda function to check if new data exists
import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = 'datacorp-lakehouse-prod'

    # Check if new files in raw/ folder
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix='raw/finance/',
        StartAfter=f'raw/finance/{last_processed_date}'
    )

    if response['KeyCount'] > 0:
        # Trigger Glue job
        glue = boto3.client('glue')
        glue.start_job_run(JobName='bronze-finance-etl')
    else:
        print("No new data, skipping ETL")
```

### 3. Query Optimization (Athena)

#### Strategy 3.1: Partition Pruning

**Bad Query** (scans entire table):
```sql
SELECT * FROM fact_transactions
WHERE transaction_date = '2026-03-01';
-- Scans all 100 partitions (100GB)
-- Cost: 0.1 TB × $5 = $0.50
```

**Good Query** (partition filter):
```sql
SELECT * FROM fact_transactions
WHERE year = 2026 AND month = 3 AND day = 1;
-- Scans 1 partition (1GB)
-- Cost: 0.001 TB × $5 = $0.005 → 99% savings
```

**Savings**: $0.495 per query × 1,000 queries/month = **$495/month**

#### Strategy 3.2: Columnar Projection

**Bad Query** (SELECT *):
```sql
SELECT * FROM dim_customers;
-- Scans all 50 columns (10GB)
-- Cost: 0.01 TB × $5 = $0.05
```

**Good Query** (only needed columns):
```sql
SELECT customer_id, name, region FROM dim_customers;
-- Scans 3 columns (600MB)
-- Cost: 0.0006 TB × $5 = $0.003 → 94% savings
```

**Savings**: $0.047 per query × 5,000 queries/month = **$235/month**

#### Strategy 3.3: Query Result Caching

**Athena Workgroup Settings**:
```bash
aws athena update-work-group \
  --work-group primary \
  --configuration-updates '{
    "ResultConfigurationUpdates": {
      "OutputLocation": "s3://lakehouse/athena-results/",
      "EncryptionConfiguration": {
        "EncryptionOption": "SSE_S3"
      }
    },
    "EnforceWorkGroupConfiguration": true,
    "ResultConfigurationUpdates": {
      "ResultReuseByAgeConfiguration": {
        "Enabled": true,
        "MaxAgeInMinutes": 5
      }
    }
  }'
```

**Impact**:
- Dashboard refresh queries: 80% hit rate (TTL = 5 minutes)
- Savings: 80% × $150/month = **$120/month**

#### Strategy 3.4: CTAS (Create Table As Select) for Expensive Queries

**Scenario**: Executive dashboard runs 100x/day, each query scans 50GB

**Before**:
- 100 queries × 0.05 TB × $5 = **$25/day** = **$750/month**

**After** (CTAS pre-aggregation):
```sql
-- Run once per day
CREATE TABLE executive_summary_cache
WITH (
  format = 'PARQUET',
  external_location = 's3://lakehouse/gold/executive-summary-cache/'
) AS
SELECT
  year, month, region,
  SUM(revenue) as total_revenue,
  COUNT(DISTINCT customer_id) as unique_customers
FROM fact_transactions
GROUP BY year, month, region;

-- Dashboard queries now scan <1GB
SELECT * FROM executive_summary_cache WHERE year = 2026;
```

**New Cost**:
- CTAS: 1x × 0.05 TB × $5 = **$0.25/day**
- Dashboard queries: 100x × 0.001 TB × $5 = **$0.50/day**
- **Total**: **$0.75/day** = **$22.50/month** → **$727.50 saved**

### 4. Monitoring & Alerting Optimization

#### Strategy 4.1: Log Filtering

**Before**:
- Ingest all Glue job logs (DEBUG, INFO, WARN, ERROR)
- 100GB/month × $0.50 = $50

**After**:
- Filter to ERROR and WARN only in production
- 10GB/month × $0.50 = **$5** → **$45 saved**

**Implementation** (in Glue job):
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.WARN)  # Only WARN and ERROR
```

#### Strategy 4.2: Metric Consolidation

**Before**:
- 200 custom metrics (per-table row counts)
- 200 × $0.30 = **$60/month**

**After**:
- Aggregate to domain-level metrics (4 domains)
- 20 metrics × $0.30 = **$6/month** → **$54 saved**

### 5. Reserved Capacity & Savings Plans

#### AWS Savings Plans

**Compute Savings Plan** (1-year, no upfront):
- Commit to $100/month spend on Glue/EMR/Lambda/Fargate
- Savings: 17% → **$17/month saved**
- **Recommendation**: Only if spend is predictable (prod environment)

**EC2 Instance Savings Plan** (if using EMR on EC2):
- Commit to m5.4xlarge instance family
- Savings: 40% (1-year upfront) → **$200/month saved** on $500 baseline

#### S3 Intelligent-Tiering (Automatic)

- No upfront commitment
- Automatic cost optimization (30-40% savings)
- **Recommendation**: Enable on all buckets

---

## 📊 Cost Tracking & Governance

### 1. AWS Cost Explorer

**Enable Cost Allocation Tags**:
```bash
# Tag all resources
aws resourcegroupstaggingapi tag-resources \
  --resource-arn-list arn:aws:s3:::datacorp-lakehouse-prod \
  --tags Project=Lakehouse,Environment=Production,CostCenter=IT-Analytics
```

**Create Cost Dashboard**:
- Group by: Service, Tag (Domain, Environment)
- Granularity: Daily
- Filters: Project=Lakehouse

### 2. AWS Budgets

**Set Budget Alerts**:
```bash
# $150/month budget for dev
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "Lakehouse-Dev-Monthly",
    "BudgetLimit": {
      "Amount": "150",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80
      },
      "Subscribers": [
        {
          "SubscriptionType": "EMAIL",
          "Address": "data-platform@datacorp.com"
        }
      ]
    }
  ]'
```

### 3. Cost Anomaly Detection

**Enable AWS Cost Anomaly Detection**:
- Automatic ML-based anomaly detection
- Alert when spend deviates >20% from baseline
- Example: Athena cost spikes from $10 to $150 (unoptimized query)

---

## 📈 ROI Calculation

### Total Cost of Ownership (TCO) Comparison

| Component | Before Lakehouse | After Lakehouse | Annual Savings |
|-----------|------------------|-----------------|----------------|
| **Data Warehouses** | $830K (Snowflake, Redshift, BigQuery) | $50K (S3, Athena) | $780K |
| **ETL Tools** | $300K (Talend, Informatica licenses) | $25K (Glue/EMR) | $275K |
| **BI Tools** | $200K (Tableau Server, Looker) | $26K (QuickSight) | $174K |
| **On-Prem Infrastructure** | $1.2M (servers, data center) | $0 (cloud-native) | $1.2M |
| **Staff Augmentation** | $2M (offshore ETL developers) | $500K (1-2 engineers) | $1.5M |
| **Storage** | $1.5M (enterprise SAN, NAS) | $2K (S3) | $1.498M |
| **Network & Transfer** | $370K (MPLS, VPN) | $20K (AWS data transfer) | $350K |
| **TOTAL** | **$8M/year** | **$2.8M/year** | **$5.2M (65%)** |

### Investment Payback Period

- **Initial Investment**: $271,800 (dev + migration)
- **Annual Savings**: $5,200,000
- **Payback Period**: 271,800 / 5,200,000 = **0.05 years (19 days)** ✅

### 3-Year NPV (Net Present Value)

Assumptions:
- Discount rate: 10%
- Annual savings: $5.2M
- Annual operational cost: $125K

| Year | Savings | Operational Cost | Net Benefit | PV (10% discount) |
|------|---------|------------------|-------------|-------------------|
| 0 | $0 | $271,800 | -$271,800 | -$271,800 |
| 1 | $5.2M | $125K | $5.075M | $4.614M |
| 2 | $5.2M | $125K | $5.075M | $4.195M |
| 3 | $5.2M | $125K | $5.075M | $3.813M |
| **NPV** | | | | **$12.35M** ✅

---

## 🎯 Cost Optimization Roadmap

### Phase 1: Quick Wins (Month 1)
- ✅ Enable S3 Intelligent-Tiering
- ✅ Implement lifecycle policies (delete Raw after 30 days)
- ✅ Configure Athena query result caching
- ✅ Filter CloudWatch logs to WARN+ only
- **Expected Savings**: $50-80/month

### Phase 2: Medium Effort (Months 2-3)
- ✅ Optimize Glue job DPU allocation (profiling)
- ✅ Partition pruning enforcement (query validation)
- ✅ CTAS for top 20 expensive Athena queries
- ✅ Metric consolidation (200 → 20 custom metrics)
- **Expected Savings**: $150-250/month

### Phase 3: Long-Term (Months 4-6)
- ✅ Reserved Instances for DMS (40% savings)
- ✅ EMR Spot Instances for non-critical jobs
- ✅ Compute Savings Plan (17% on Glue/EMR)
- ✅ Cross-region replication optimization (selective replication)
- **Expected Savings**: $300-500/month

### Phase 4: Continuous Optimization (Ongoing)
- ✅ Weekly cost review meetings
- ✅ Automated cost anomaly alerts
- ✅ Quarterly vendor negotiations (QuickSight, tooling)
- ✅ FinOps culture: developers own cost decisions
- **Expected Savings**: 5-10% YoY improvement

---

## 📞 Cost Support & Resources

- **AWS Cost Optimization Hub**: https://aws.amazon.com/aws-cost-management/
- **AWS Well-Architected Cost Optimization Pillar**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/
- **FinOps Foundation**: https://www.finops.org/

---

**Last Updated**: March 10, 2026
**Maintainer**: FinOps Team + Data Platform Team

**Next Review**: Quarterly (June 2026, September 2026, December 2026)
