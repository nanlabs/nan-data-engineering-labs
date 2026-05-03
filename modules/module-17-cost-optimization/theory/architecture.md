# Cost-Optimized Cloud Architectures

## Introduction

This document presents reference architectures designed for cost optimization while maintaining performance, reliability, and scalability. Each pattern includes cost breakdowns and optimization techniques.

## Architecture Principles for Cost Optimization

### 1. Serverless-First Design
- Use Lambda, Fargate, Athena for variable workloads
- Eliminate idle capacity costs
- Auto-scale without management overhead

### 2. Multi-Tier Storage Strategy
- Hot data: S3 Standard or EBS gp3
- Warm data: S3 IA or Glacier Instant Retrieval
- Cold data: Glacier Deep Archive
- Automated lifecycle transitions

### 3. Commitment-Based Baseline
- Cover 60-70% of steady load with RIs/Savings Plans
- Use On-Demand for remaining 20-30% variable capacity
- Spot for batch/fault-tolerant (10% of workload)

### 4. Right-Sized from Day 1
- Start with smallest viable instance
- Scale up based on actual metrics
- Avoid "future-proofing" over-provisioning

### 5. Network Optimization
- VPC endpoints to avoid NAT Gateway ($0.045/hour)
- CloudFront for static assets (reduce S3 egress)
- Keep data in same region (avoid cross-region transfer)

## Reference Architecture 1: Cost-Optimized Data Lake

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│             Cost-Optimized Data Lake                         │
│                                                              │
│  Ingestion (Serverless)                                      │
│  ┌──────────┐  ┌─────────┐  ┌──────────────────┐           │
│  │ Kinesis  │→ │ Lambda  │→ │ S3 (Parquet)     │           │
│  │ Data     │  │ 256MB   │  │ + Lifecycle      │           │
│  │ Stream   │  │ $50/mo  │  │ Standard→Glacier │           │
│  └──────────┘  └─────────┘  └─────────┬────────┘           │
│  $120/month    Pay-per-use      $500/month                  │
│                                         │                    │
│  Processing (Batch on Spot)            │                    │
│  ┌─────────────────────────────────────▼────────┐           │
│  │ EMR (Spot 80% / On-Demand 20%)               │           │
│  │ 1 Master + 2 Core (On-Demand)                │           │
│  │ 8 Task nodes (Spot)                          │           │
│  │ Run: 4 hours/day                             │           │
│  │ $360/month (vs $1,800 all On-Demand)         │           │
│  └─────────────────────┬────────────────────────┘           │
│                        │                                     │
│  Query (Serverless)    │                                     │
│  ┌────────────────────▼──────────────┐                      │
│  │ Athena                            │                      │
│  │ $5/TB scanned                     │                      │
│  │ With Parquet: 100GB/query         │                      │
│  │ 1000 queries/month = $50          │                      │
│  └───────────────────────────────────┘                      │
│                                                              │
│  Total Monthly Cost: $1,080                                 │
│  vs Traditional (EMR 24/7): $13,000                         │
│  Savings: 92%                                               │
└──────────────────────────────────────────────────────────────┘
```

### Cost Breakdown

| Component | Configuration | Monthly Cost | Optimization |
|-----------|--------------|--------------|--------------|
| **Ingestion** | Kinesis (1 MB/s) | $120 | Could use SQS ($0.40) if not real-time |
| **Streaming ETL** | Lambda (256MB) | $50 | Right-sized memory |
| **Storage** | S3 (10 TB) with lifecycle | $500 | Lifecycle: Standard (1TB) + IA (3TB) + Glacier (6TB) |
| **Batch Processing** | EMR Spot (4h/day) | $360 | 80% Spot = 85% savings vs 24/7 |
| **Querying** | Athena (1000 queries) | $50 | Parquet = 90% less data scanned |
| **Catalog** | Glue Data Catalog | $20 | Fixed cost |
| **Total** | | **$1,100/month** | |

**Traditional Alternative**: EMR 24/7 cluster = $13,000/month
**Savings**: $11,900/month (91.5%)

### Implementation Checklist
- [ ] Use Kinesis Firehose for automatic Parquet conversion
- [ ] Partition S3 by date (year/month/day) for Athena efficiency
- [ ] EMR Auto Scaling (2-10 task nodes based on load)
- [ ] S3 lifecycle: Standard (30d) → IA (90d) → Glacier (180d)
- [ ] Athena workgroups with query limits
- [ ] CloudWatch dashboards for cost tracking

## Reference Architecture 2: Cost-Optimized API Platform

### Architecture Diagram

```
┌────────────────────────────────────────────────────────┐
│          Cost-Optimized API Platform                   │
│                                                        │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────┐   │
│  │   CDN    │  │ API Gateway│  │ Lambda Functions│   │
│  │CloudFront│→ │ REST API   │→ │ 512MB, 200ms   │   │
│  │          │  │            │  │ ARM/Graviton2  │   │
│  │ $80/month│  │ $30/month  │  │ $200/month     │   │
│  └──────────┘  └────────────┘  └────────┬────────┘   │
│  Static assets  1M requests/mo   10M req/mo │         │
│                                             │         │
│  ┌──────────────────────────────────────────▼──────┐  │
│  │ DynamoDB (On-Demand)                           │  │
│  │ Pay per request                                │  │
│  │ $50/month (10M reads, 2M writes)               │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Total: $360/month for 10M API calls                │
│  Unit Cost: $0.000036 per API call                  │
│  vs EC2 + ALB: $150/month (but ops overhead)        │
└────────────────────────────────────────────────────────┘
```

### Cost Comparison

**Serverless Option** (Lambda + API Gateway):
- CloudFront: $80 (10 TB transfer)
- API Gateway: $3.50 per M requests * 10 = $35
- Lambda: $0.20 per M requests + duration = $200
- DynamoDB: On-Demand $50
- **Total**: $365/month

**Traditional Option** (EC2 + ALB):
- ALB: $22.50 base + LCU processing = $45
- EC2 (2x t3.medium 24/7): $60
- RDS (db.t3.medium): $60
- CloudFront: $80
- Ops time (20 hours/month @ $100): $2,000
- **Total**: $2,245/month

**Winner**: Serverless ($1,880/month savings, 84% reduction)

**Break-Even**: At >100M requests/month, EC2 + ALB becomes cheaper on infrastructure alone, but serverless still wins on total cost (including ops).

### When to Use EC2 Instead
- \>50M requests/month with steady traffic
- Long-running connections (WebSockets)
- GPU requirements
- Complex networking (VPN, Direct Connect)

## Reference Architecture 3: Cost-Optimized ETL Pipeline

### Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│           Cost-Optimized ETL Pipeline                      │
│                                                            │
│  Sources        Ingestion       Transform      Serve      │
│  ┌────────┐    ┌──────────┐   ┌──────────┐  ┌─────────┐ │
│  │Databases│ ─→ │ Glue     │─→ │ Athena   │→ │QuickSight│
│  │  APIs   │    │ Crawler  │   │ Queries  │  │Dashboard│ │
│  │  SaaS   │    │ $10/day  │   │ $5/query │  │ $24/mo  │ │
│  └────────┘    └──────────┘   └──────────┘  └─────────┘ │
│                      │                                     │
│                      ▼                                     │
│               ┌─────────────┐                             │
│               │  S3 Curated │                             │
│               │  Parquet +  │                             │
│               │  Snappy     │                             │
│               │  $150/month │                             │
│               └─────────────┘                             │
│                                                            │
│  Daily ETL: Glue (2 hours, 10 DPU) = $264/month          │
│  Storage: 3 TB Parquet = $150/month                       │
│  Queries: 500/month * $0.50 = $250/month                  │
│  Dashboards: QuickSight = $24/month                       │
│                                                            │
│  Total: $688/month                                        │
│  vs EMR 24/7: $5,200/month                                │
│  Savings: 87%                                             │
└────────────────────────────────────────────────────────────┘
```

### Cost Optimization Techniques

1. **Incremental processing**: Only process new data (partition by date)
2. **Parquet + Snappy**: 80% compression vs CSV
3. **Glue job bookmarks**: Track processed data, avoid reprocessing
4. **Athena partition projection**: Reduce Glue Catalog API calls
5. **QuickSight SPICE**: Cache 10 GB data ($0.25/GB) instead of querying repeatedly

### Alternative: Ultra-Low-Cost ETL

For smaller workloads (<100 GB/day):
- Replace Glue with Lambda ($50/month vs $264/month)
- Replace Athena with DuckDB on Lambda (query Parquet directly, $0 query cost)
- **Total**: <$100/month (86% savings vs Glue)

## Reference Architecture 4: Multi-Account Cost Allocation

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│          AWS Organizations: Cost Allocation                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Management Account (Billing Consolidated)      │ │
│  │  • Cost and Usage Reports                              │ │
│  │  • Organization-wide budgets                           │ │
│  │  • Service Control Policies                            │ │
│  └───────────────────────┬────────────────────────────────┘ │
│                          │                                   │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│  ┌──────▼─────┐   ┌──────▼─────┐   ┌─────▼──────┐         │
│  │ Production │   │Development │   │   Shared   │         │
│  │   Account  │   │  Account   │   │  Services  │         │
│  │            │   │            │   │  Account   │         │
│  │ $30K/mo    │   │ $5K/mo     │   │ $10K/mo    │         │
│  │ Team: Eng  │   │ Team: Eng  │   │ Team: Ops  │         │
│  └────────────┘   └────────────┘   └────────────┘         │
│                                                              │
│  Tagging Strategy:                                          │
│  • CostCenter: CC-12345                                     │
│  • Team: Engineering / Data / ML                            │
│  • Environment: prod / dev / test                           │
│  • Project: project-alpha                                   │
│                                                              │
│  Cost Allocation:                                           │
│  → Production: Chargeback to product P&L                    │
│  → Development: Showback to engineering                     │
│  → Shared: Allocated by usage ratio                         │
└──────────────────────────────────────────────────────────────┘
```

### Multi-Account Benefits

1. **Clear cost boundaries**: Each account = team/project
2. **Budget enforcement**: Account-level limits
3. **Blast radius**: Prevent accidental resource creation in prod
4. **Consolidated billing**: Volume discounts applied across org

### Cost Allocation Rules

```python
# Cost allocation logic for shared services
def allocate_shared_costs(shared_costs, team_usage):
    """
    Allocate shared service costs based on usage

    shared_costs: Monthly cost of shared services
    team_usage: Dict of team usage percentages
    """
    allocations = {}

    for team, usage_pct in team_usage.items():
        allocated = shared_costs * (usage_pct / 100)
        allocations[team] = allocated

    return allocations

# Example
shared_services_cost = 10000  # $10K/month (VPN, monitoring, etc.)
team_usage = {
    'Engineering': 60,  # 60% of requests from eng team
    'Data Science': 30,
    'DevOps': 10
}

allocations = allocate_shared_costs(shared_services_cost, team_usage)

print("\n💰 Shared Cost Allocation:")
for team, cost in allocations.items():
    print(f"  {team}: ${cost:,.2f}")
```

### Tagging Strategy for Multi-Account

```python
MULTI_ACCOUNT_TAGGING = {
    'mandatory': {
        'CostCenter': 'Financial code for chargeback',
        'Team': 'Engineering team responsible',
        'Environment': 'prod, dev, test, staging',
        'Project': 'Product or initiative name',
        'ManagedBy': 'Terraform, CloudFormation, Manual'
    },
    'optional': {
        'Owner': 'Email of resource creator',
        'ExpirationDate': 'Auto-delete after date',
        'BackupRequired': 'true/false',
        'Compliance': 'HIPAA, PCI, SOC2'
    }
}

# Auto-tag resources with account-level defaults
def apply_account_default_tags(resource_arn, account_tags):
    """Apply default tags from account/OU to new resources"""
    # This would be triggered by EventBridge on resource creation
    pass
```

## Reference Architecture 5: Cost-Optimized ML Training

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│        Cost-Optimized ML Training Pipeline               │
│                                                          │
│  Data Prep (Serverless)                                  │
│  ┌────────────┐   ┌──────────────┐                      │
│  │  Lambda    │ → │ S3 (Parquet) │                      │
│  │  Clean &   │   │ Training     │                      │
│  │  Feature   │   │ Data         │                      │
│  │  $20/month │   │ $50/month    │                      │
│  └────────────┘   └───────┬──────┘                      │
│                           │                              │
│  Training (Spot)          │                              │
│  ┌────────────────────────▼──────────────┐              │
│  │ SageMaker Training (Spot 70% off)     │              │
│  │ ml.p3.2xlarge (GPU)                   │              │
│  │ On-Demand: $3.06/hour                 │              │
│  │ Spot: $0.92/hour                      │              │
│  │ Train 100 hours/month: $92 (vs $306)  │              │
│  └────────────────────┬───────────────────┘              │
│                       │                                  │
│  Inference (Serverless)                                  │
│  ┌───────────────────▼────────────────┐                 │
│  │ Lambda (512MB) or                  │                 │
│  │ SageMaker Serverless Endpoint      │                 │
│  │ $80/month (100K predictions)       │                 │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Total: $242/month                                      │
│  vs On-Demand training + endpoint: $1,200/month         │
│  Savings: 80%                                           │
└──────────────────────────────────────────────────────────┘
```

### Cost Optimization Strategies

1. **Spot Training**: 70% discount, use managed spot training
2. **Checkpointing**: Save model every epoch to S3 (survive interruptions)
3. **Serverless Inference**: Pay per prediction for <100K requests/day
4. **Model Compression**: Reduce inference compute (quantization)
5. **Batch Transform**: For large batch predictions (cheaper than real-time)

### ML Cost Comparison

| Training Option | 100-hour Training Job | Notes |
|----------------|----------------------|-------|
| On-Demand p3.2xlarge | $306 | Guaranteed, no interruptions |
| Spot p3.2xlarge | $92 | 70% discount, checkpointing required |
| SageMaker Savings Plan | $185 | 40% discount, 1-year commitment |

## Reference Architecture 6: Cost-Optimized Streaming Analytics

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│       Cost-Optimized Streaming Analytics                 │
│                                                          │
│  ┌───────────┐   ┌──────────────┐   ┌────────────────┐ │
│  │ IoT / API │ → │ Kinesis Data │ → │ Kinesis Data   │ │
│  │ Sources   │   │ Streams      │   │ Firehose       │ │
│  │           │   │ 2 shards     │   │ S3 batching    │ │
│  │           │   │ $50/month    │   │ $180/month     │ │
│  └───────────┘   └──────────────┘   └───────┬────────┘ │
│                                              │          │
│  ┌───────────────────────────────────────────▼────────┐ │
│  │ S3 (Parquet, Partitioned by hour)                 │ │
│  │ 1 TB/month ingested                                │ │
│  │ Lifecycle: Standard (30d) → IA (90d)               │ │
│  │ $23/month                                          │ │
│  └───────────────────────┬────────────────────────────┘ │
│                          │                              │
│  Real-Time              │  Historical                   │
│  ┌────────────┐         │  ┌──────────────┐            │
│  │  Lambda    │         └→ │   Athena     │            │
│  │  Process   │            │   Queries    │            │
│  │  $40/month │            │   $25/month  │            │
│  └────────────┘            └──────────────┘            │
│                                                          │
│  Total: $318/month                                      │
│  vs Kafka on EC2: $1,500/month                          │
│  Savings: 79%                                           │
└──────────────────────────────────────────────────────────┘
```

### Cost Optimization Decisions

**Kinesis vs Kafka (self-managed)**:
- Kinesis: $50/month (2 shards, 2 MB/s) - Managed
- Kafka on EC2: $500/month (3x m5.large 24/7) - Self-managed
- **Winner**: Kinesis for <10 MB/s (saves ops time)

**Kinesis Data Analytics vs Lambda**:
- Analytics: $0.11 per KPU-hour (Kinesis Processing Unit)
- Lambda: $0.20 per 1M requests + duration
- **Winner**: Lambda for simple transforms (<1 sec processing)
- **Winner**: Analytics for complex SQL (>5 sec processing)

## Reference Architecture 7: Hybrid Commitment Strategy

### Portfolio Approach

```
┌────────────────────────────────────────────────────────┐
│         Hybrid Commitment Portfolio                    │
│                                                        │
│  Total Monthly Compute: $10,000                        │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Reserved/Savings Plans: $6,000 (60%)             │ │
│  │ • 3-Year Compute Savings Plan: $4,000            │ │
│  │ • 1-Year EC2 RIs: $2,000                         │ │
│  │ Discount: 60% average                            │ │
│  │ Actual Cost: $2,400/month                        │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ On-Demand: $3,000 (30%)                          │ │
│  │ • Variable workload peaks                        │ │
│  │ • Development instances                          │ │
│  │ Discount: 0%                                     │ │
│  │ Actual Cost: $3,000/month                        │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Spot: $1,000 (10%)                               │ │
│  │ • Batch processing                               │ │
│  │ • CI/CD pipelines                                │ │
│  │ Discount: 75%                                    │ │
│  │ Actual Cost: $250/month                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Total Actual Cost: $5,650/month                       │
│  vs All On-Demand: $10,000/month                       │
│  Savings: $4,350/month (43.5%)                         │
└────────────────────────────────────────────────────────┘
```

### Portfolio Optimization

**Goal**: Maximize savings while maintaining flexibility

**60-30-10 Rule**:
- 60% commitments (RIs/SPs) - Steady baseline
- 30% On-Demand - Variable capacity
- 10% Spot - Batch workloads

**Quarterly Review**:
- Are commitments >85% utilized?
- Is On-Demand coverage >70%?
- Adjust ratios based on growth

## Architecture Pattern: Auto-Scaling for Cost

### Time-Based Scaling

```python
# Schedule-based scaling for predictable patterns
SCALING_SCHEDULE = {
    'business_hours': {
        'time': '08:00-18:00 Mon-Fri',
        'desired_capacity': 10,
        'cost_per_hour': 10 * 0.096,  # 10x m5.large
        'monthly_cost': 10 * 0.096 * 220  # 220 business hours
    },
    'off_hours': {
        'time': '18:00-08:00 Mon-Fri + weekends',
        'desired_capacity': 2,  # Minimum for availability
        'cost_per_hour': 2 * 0.096,
        'monthly_cost': 2 * 0.096 * 510  # 510 off-hours
    }
}

business_cost = SCALING_SCHEDULE['business_hours']['monthly_cost']
off_cost = SCALING_SCHEDULE['off_hours']['monthly_cost']
total_cost = business_cost + off_cost

# Compare to 24/7
always_on_cost = 10 * 0.096 * 730

savings = always_on_cost - total_cost
savings_pct = (savings / always_on_cost) * 100

print(f"\n💰 Schedule-Based Auto Scaling:")
print(f"  24/7 (10 instances): ${always_on_cost:.2f}/month")
print(f"  Scheduled (10 → 2): ${total_cost:.2f}/month")
print(f"  Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
```

### Metric-Based Scaling

```python
# Predictive scaling based on CloudWatch metrics
SCALING_POLICY = {
    'metric': 'ASGAverageCPUUtilization',
    'target_value': 60,  # Target 60% CPU
    'scale_out_cooldown': 60,   # seconds
    'scale_in_cooldown': 300,   # seconds (conservative)

    'estimated_scenarios': {
        'low_traffic': {'instances': 2, 'hours': 400},
        'medium_traffic': {'instances': 5, 'hours': 250},
        'high_traffic': {'instances': 10, 'hours': 80}
    }
}

# Calculate cost with auto-scaling
dynamic_cost = sum(
    scenario['instances'] * scenario['hours'] * 0.096
    for scenario in SCALING_POLICY['estimated_scenarios'].values()
)

# vs fixed 10 instances 24/7
fixed_cost = 10 * 0.096 * 730

print(f"\n💰 Metric-Based Auto Scaling:")
print(f"  Fixed (10 instances): ${fixed_cost:.2f}/month")
print(f"  Dynamic (2-10 based on CPU): ${dynamic_cost:.2f}/month")
print(f"  Savings: ${fixed_cost - dynamic_cost:.2f}/month")
```

## Architecture Pattern: Data Lake Tiering

### Hot-Warm-Cold Storage Strategy

```
┌──────────────────────────────────────────────────────────┐
│              Data Lake Storage Tiers                     │
│                                                          │
│  Hot Tier (Last 30 days)         Cost: $0.023/GB-month  │
│  ┌────────────────────────────────────────────────────┐ │
│  │ S3 Standard                                        │ │
│  │ • Frequent access (queries, dashboards)            │ │
│  │ • Example: 1 TB * $0.023 = $23/month              │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│                          ▼ (30 days)                     │
│  Warm Tier (30-90 days)          Cost: $0.0125/GB-month │
│  ┌────────────────────────────────────────────────────┐ │
│  │ S3 Standard-IA                                     │ │
│  │ • Weekly access (reports, analysis)                │ │
│  │ • Example: 3 TB * $0.0125 = $37.5/month           │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│                          ▼ (90 days)                     │
│  Cool Tier (90-180 days)         Cost: $0.004/GB-month  │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Glacier Instant Retrieval                          │ │
│  │ • Monthly access (compliance, audits)              │ │
│  │ • Example: 5 TB * $0.004 = $20/month              │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│                          ▼ (180 days)                    │
│  Cold Tier (>180 days)           Cost: $0.00099/GB-month│
│  ┌────────────────────────────────────────────────────┐ │
│  │ Glacier Deep Archive                               │ │
│  │ • Rare access (legal hold, archives)               │ │
│  │ • 12-hour retrieval time                           │ │
│  │ • Example: 20 TB * $0.00099 = $19.8/month         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Total Storage: 29 TB                                   │
│  Total Cost: $100.3/month                               │
│  vs All Standard: 29 TB * $0.023 = $667/month          │
│  Savings: $566.7/month (85%)                            │
└──────────────────────────────────────────────────────────┘
```

### Implementation

```python
# Lifecycle policy for 4-tier strategy
lifecycle_policy = {
    'Rules': [
        {
            'Id': 'hot-to-warm-30d',
            'Status': 'Enabled',
            'Transitions': [
                {'Days': 30, 'StorageClass': 'STANDARD_IA'}
            ]
        },
        {
            'Id': 'warm-to-cool-90d',
            'Status': 'Enabled',
            'Transitions': [
                {'Days': 90, 'StorageClass': 'GLACIER_IR'}
            ]
        },
        {
            'Id': 'cool-to-cold-180d',
            'Status': 'Enabled',
            'Transitions': [
                {'Days': 180, 'StorageClass': 'DEEP_ARCHIVE'}
            ]
        },
        {
            'Id': 'delete-after-7-years',
            'Status': 'Enabled',
            'Expiration': {'Days': 2555}  # 7 years for compliance
        }
    ]
}
```

## Architecture Pattern: Reserved Capacity Planning

### Capacity Planning Framework

```python
def calculate_optimal_ri_coverage(usage_data):
    """
    Calculate optimal RI coverage based on usage patterns

    Principle: Cover baseline, leave peaks for On-Demand
    """
    # Analyze 90 days of hourly usage
    hourly_usage = usage_data['hourly_instance_counts']

    # Calculate percentiles
    p50_usage = np.percentile(hourly_usage, 50)  # Median
    p75_usage = np.percentile(hourly_usage, 75)
    p95_usage = np.percentile(hourly_usage, 95)
    max_usage = np.max(hourly_usage)

    # Strategy: RI coverage at P50-P75 percentile
    recommended_ri_count = int(np.ceil(p50_usage))

    # Calculate savings
    on_demand_cost = np.mean(hourly_usage) * 730 * 0.192  # m5.xlarge
    ri_cost = recommended_ri_count * 730 * 0.125  # RI hourly
    remaining_on_demand = (np.mean(hourly_usage) - recommended_ri_count) * 730 * 0.192

    total_hybrid_cost = ri_cost + remaining_on_demand
    savings = on_demand_cost - total_hybrid_cost
    savings_pct = (savings / on_demand_cost) * 100

    return {
        'recommended_ri_count': recommended_ri_count,
        'coverage_pct': (recommended_ri_count / max_usage) * 100,
        'monthly_savings': savings,
        'savings_pct': savings_pct
    }

# Example usage data
usage_data = {
    'hourly_instance_counts': np.random.randint(5, 15, size=2160)  # 90 days
}

recommendation = calculate_optimal_ri_coverage(usage_data)

print(f"\n💡 RI Coverage Recommendation:")
print(f"  Purchase {recommendation['recommended_ri_count']} RIs")
print(f"  Coverage: {recommendation['coverage_pct']:.1f}% of peak")
print(f"  Monthly Savings: ${recommendation['monthly_savings']:.2f} ({recommendation['savings_pct']:.1f}%)")
```

## Cost-Aware Application Design

### Design Pattern 1: Lazy Loading
- Don't load all data upfront (reduces Lambda memory/duration)
- Load from S3 only when needed
- Cache frequently accessed data in Lambda /tmp (512 MB available)

### Design Pattern 2: Bulk Processing
- Batch API calls (reduce per-request overhead)
- Process S3 files in chunks (reduce Lambda invocations)
- Use SQS batching (10 messages per receive = 90% reduction)

### Design Pattern 3: Caching Strategy
- CloudFront for static assets (90% cache hit = 90% cost reduction)
- ElastiCache/DynamoDB DAX for database queries
- Lambda response caching in API Gateway

### Design Pattern 4: Async Processing
- Use SQS instead of synchronous Lambda (cheaper, more reliable)
- Decouple components (reduce idle waiting time)
- Step Functions Express for high-volume workflows

## Cost Optimization Decision Trees

### Storage Decision
```
Data access pattern?
    ├─ Frequent (daily) → S3 Standard
    ├─ Occasional (weekly) → S3 Standard-IA
    ├─ Rare (monthly) → Glacier Instant Retrieval
    ├─ Archive (yearly) → Glacier Deep Archive
    └─ Unknown → S3 Intelligent-Tiering (auto-optimize)

Data format?
    ├─ Analytics → Parquet + Snappy (best balance)
    ├─ Archival → Parquet + Gzip (max compression)
    ├─ Transient → No optimization needed
```

### Compute Decision
```
Usage pattern?
    ├─ 24/7 predictable → Reserved Instances (60% savings)
    ├─ Variable compute → Compute Savings Plan (60% savings)
    ├─ Sporadic → Lambda (pay per execution)
    ├─ Batch → Spot Instances (75% savings)
    └─ Microservices → Fargate (no management)

Fault tolerance?
    ├─ Tolerant → Spot (70-90% savings)
    └─ Critical → On-Demand + RIs
```

## Summary

This architecture guide covered:
- 7 cost-optimized reference architectures
- Real-world cost breakdowns with alternatives
- Multi-account cost allocation strategies
- Hybrid commitment portfolio (60-30-10 rule)
- Data lake storage tiering (hot-warm-cold)
- Cost-aware application design patterns

**Key Principle**: Architect for cost from day 1, not as an afterthought.

**Next**: Explore best practices for implementing these architectures.
