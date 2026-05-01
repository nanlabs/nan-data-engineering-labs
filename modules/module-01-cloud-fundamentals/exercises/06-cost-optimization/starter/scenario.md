# Scenario: Cost Optimization at QuickMart

## 📊 Business Context

QuickMart's AWS bill is growing faster than revenue:

**Current State (Month 1):**
- **S3 Storage:** $450/month (2TB of data, all STANDARD class)
- **CloudWatch Logs:** $180/month (500GB retained for 6 months)
- **Lambda Executions:** $85/month (25M invocations, 512MB memory)
- **Data Transfer:** $120/month (outbound to internet)
- **Idle Resources:** $200/month (stopped EC2, orphaned EBS volumes)
- **Total:** $1,035/month

**Growth Trajectory:** +30% monthly

**CFO's Challenge:** "Reduce costs by 40% without impacting performance."

## 🎯 Your Mission

Implement cost optimization strategies across the data platform:

### Optimization 1: S3 Storage Tiering

Analyze data access patterns and implement lifecycle policies:

**Current:**
```
2TB data → 100% STANDARD ($0.023/GB) = $47/GB = $450/month
```

**Optimized:**
```
- Hot data (30 days): 200GB STANDARD = $4.60
- Warm data (90 days): 500GB STANDARD_IA ($0.0125/GB) = $6.25
- Cold data (1 year): 800GB GLACIER ($0.004/GB) = $3.20
- Archive (2+ years): 500GB DEEP_ARCHIVE ($0.00099/GB) = $0.50
Total: $14.55/month (97% reduction)
```

### Optimization 2: CloudWatch Logs Management

Reduce retention and export to S3:

**Current:**
```
500GB logs × 6 months retention × $0.03/GB = $180/month
```

**Optimized:**
```
- 7 days retention: 60GB × $0.03/GB = $1.80
- Archive to S3 GLACIER: 440GB × $0.004/GB = $1.76
Total: $3.56/month (98% reduction)
```

### Optimization 3: Lambda Right-Sizing

Analyze execution time and adjust memory:

**Current:**
```
25M invocations × 512MB × 1000ms avg × $0.0000166667 = $85/month
```

**Optimized:**
```
- Memory: 512MB → 256MB (sufficient for workload)
- Duration: 1000ms → 800ms (code optimization)
25M × 256MB × 800ms × $0.0000166667 = $34/month (60% reduction)
```

### Optimization 4: Resource Cleanup

Identify and remove unused resources:

**Targets:**
- Stopped EC2 instances (pay for EBS)
- Unattached EBS volumes
- Old EBS snapshots
- Unused Elastic IPs
- Orphaned ENIs
- Old CloudWatch log groups

**Estimated Savings:** $200/month

## 📋 Acceptance Criteria

### Analysis Scripts
- [x] Python script to analyze S3 storage by age
- [x] Generate lifecycle policy recommendations
- [x] CloudWatch Logs analyzer (size, retention)
- [x] Lambda performance analyzer (memory vs. duration)
- [x] Resource scanner (unused/orphaned)

### Cost Budgets
- [x] Create AWS Budget with $800/month limit
- [x] Configure SNS alerts at 80%, 90%, 100%
- [x] Email notifications to engineering team

### CloudWatch Dashboards
- [x] S3 storage by class (chart)
- [x] Lambda duration percentiles (p50, p95, p99)
- [x] CloudWatch Logs ingestion rate
- [x] Monthly cost projection

### Reporting
- [x] Weekly cost report (by service)
- [x] Monthly optimization recommendations
- [x] Savings achieved vs. target

## 🏗️ Architecture

```
Cost Optimization Platform
├── Analysis Layer
│   ├── s3_storage_analyzer.py → CSV report
│   ├── logs_analyzer.py → Retention recommendations
│   └── lambda_profiler.py → Right-sizing suggestions
│
├── Automation Layer
│   ├── lifecycle_applier.py → Apply S3 policies
│   ├── log_exporter.py → Export to S3, reduce retention
│   └── resource_cleaner.py → Delete unused resources
│
├── Monitoring Layer
│   ├── CloudWatch Dashboard → Real-time metrics
│   ├── AWS Budgets → Spending alerts
│   └── Cost Anomaly Detection → ML-based alerts
│
└── Reporting Layer
    ├── weekly_report.py → Email summary
    └── savings_calculator.py → ROI calculation
```

## 💡 Implementation Tips

### S3 Storage Analysis

```python
import boto3
from datetime import datetime, timedelta

s3 = boto3.client('s3')

def analyze_bucket(bucket_name):
    """Analyze object age distribution"""

    age_buckets = {
        'hot': 0,      # 0-30 days
        'warm': 0,     # 31-90 days
        'cold': 0,     # 91-365 days
        'archive': 0   # 365+ days
    }

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            age = (datetime.now(obj['LastModified'].tzinfo) - obj['LastModified']).days
            size = obj['Size']

            if age <= 30:
                age_buckets['hot'] += size
            elif age <= 90:
                age_buckets['warm'] += size
            elif age <= 365:
                age_buckets['cold'] += size
            else:
                age_buckets['archive'] += size

    return age_buckets
```

### Lambda Right-Sizing

```python
import boto3

logs = boto3.client('logs')

def analyze_lambda(function_name):
    """Get memory usage and duration stats"""

    log_group = f'/aws/lambda/{function_name}'

    # Query CloudWatch Logs Insights
    query = """
    fields @memorySize / 1000000 as memoryUsedMB, @duration, @billedDuration
    | stats
        avg(@duration) as avg_duration,
        max(@duration) as max_duration,
        avg(memoryUsedMB) as avg_memory,
        max(memoryUsedMB) as max_memory,
        count() as invocations
    """

    response = logs.start_query(
        logGroupName=log_group,
        startTime=int((datetime.now() - timedelta(days=7)).timestamp()),
        endTime=int(datetime.now().timestamp()),
        queryString=query
    )

    # Get results...
    return {
        'current_memory': 512,
        'recommended_memory': 256,  # Based on avg_memory + 20% buffer
        'estimated_savings': 0.50  # 50% reduction
    }
```

### Cost Budgets (CloudFormation)

```yaml
Resources:
  MonthlyCostBudget:
    Type: AWS::Budgets::Budget
    Properties:
      Budget:
        BudgetName: quickmart-monthly-budget
        BudgetLimit:
          Amount: 800
          Unit: USD
        TimeUnit: MONTHLY
        BudgetType: COST

      NotificationsWithSubscribers:
        - Notification:
            NotificationType: ACTUAL
            ComparisonOperator: GREATER_THAN
            Threshold: 80
          Subscribers:
            - SubscriptionType: EMAIL
              Address: engineering@quickmart.com

        - Notification:
            NotificationType: FORECASTED
            ComparisonOperator: GREATER_THAN
            Threshold: 100
          Subscribers:
            - SubscriptionType: EMAIL
              Address: cfo@quickmart.com
```

## 🧪 Test Scenarios

### Scenario 1: S3 Storage Analysis

```bash
# Run analyzer
python3 s3_storage_analyzer.py --bucket quickmart-data-lake-prod

# Expected output:
# Hot (0-30d):     200GB → STANDARD
# Warm (31-90d):   500GB → STANDARD_IA (save $5.75/month)
# Cold (91-365d):  800GB → GLACIER (save $15.20/month)
# Archive (365+d): 500GB → DEEP_ARCHIVE (save $11.00/month)
# Total Savings: $31.95/month (70%)
```

### Scenario 2: Resource Cleanup

```bash
# Scan for unused resources
python3 resource_scanner.py --region us-east-1

# Expected findings:
# - 5 stopped EC2 instances (save $50/month on EBS)
# - 12 unattached EBS volumes (save $120/month)
# - 200 old snapshots (save $20/month)
# - 3 unused Elastic IPs (save $10.80/month)
```

### Scenario 3: Budget Alerts

```bash
# Simulate overspending
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://monthly-budget.json

# Trigger alert by exceeding threshold
# (In real scenario, this happens automatically)
```

## 📈 Expected Results

### Cost Reduction Breakdown

| Category | Before | After | Savings | % |
|----------|--------|-------|---------|---|
| S3 Storage | $450 | $140 | $310 | 69% |
| CloudWatch Logs | $180 | $36 | $144 | 80% |
| Lambda | $85 | $34 | $51 | 60% |
| Data Transfer | $120 | $80 | $40 | 33% |
| Unused Resources | $200 | $0 | $200 | 100% |
| **Total** | **$1,035** | **$290** | **$745** | **72%** |

**Target:** 40% reduction ($414 savings)
**Achieved:** 72% reduction ($745 savings)
**Over-delivered:** +32 percentage points 🎯

## 🎓 Learning Outcomes

After this exercise:

✅ Analyze S3 storage patterns
✅ Create intelligent lifecycle policies
✅ Right-size Lambda functions
✅ Set up AWS Budgets and alerts
✅ Build cost monitoring dashboards
✅ Identify and clean unused resources
✅ Calculate ROI of optimizations
✅ Create cost reports

---

**Ready?** Head to [README.md](../README.md) for implementation steps!
