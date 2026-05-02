# Exercise 06: Cost Optimization & Monitoring

**Duration:** 60-75 minutes | **Difficulty:** ⭐⭐⭐

## 🎯 Objectives

- Implement AWS Budgets para alertas de costos
- Configure CloudWatch Metrics y Alarms
- Analizar Cost Explorer patterns
- Optimizar costos con lifecycle y reserved capacity

## 📖 Conceptos

### AWS Cost Management

**4 Pilares:**
1. **Measure:** CloudWatch Metrics, Cost Explorer
2. **Monitor:** Budgets, Alarms
3. **Optimize:** Right-sizing, lifecycle policies
4. **Govern:** Tagging, quotas, IAM policies

### CloudWatch Metrics

```python
# Publish custom metric
cloudwatch.put_metric_data(
    Namespace='QuickMart/DataLake',
    MetricData=[{
        'MetricName': 'ProcessedFiles',
        'Value': 150,
        'Unit': 'Count',
        'Timestamp': datetime.utcnow()
    }]
)
```

### Cost Optimization Strategies

| Strategy | Savings | Effort |
|----------|---------|--------|
| Lifecycle policies | 60-80% | Low |
| Reserved capacity | 30-50% | Medium |
| Spot instances (EMR) | 70-90% | High |
| Right-sizing | 20-40% | Medium |
| Data compression | 50-70% | Low |

## 🎬 Steps

### Step 1: Configure CloudWatch Metrics

```python
# my_solution/cloudwatch_metrics.py
def publish_data_quality_metrics(bucket_name: str):
    # TODO: Count objects in bucket
    # TODO: Calculate total storage size
    # TODO: Publish metrics to CloudWatch
    pass

def create_storage_alarm(metric_name: str, threshold: int):
    # TODO: Create alarm when storage > threshold
    # TODO: Send SNS notification
    pass
```

### Step 2: Implement Cost Budgets

```python
# my_solution/cost_budgets.py
def create_monthly_budget(amount: float):
    # TODO: Create budget with $amount limit
    # TODO: Set alerts at 80%, 100%, 120%
    # TODO: Send email notifications
    pass
```

### Step 3: Analizar Storage Patterns

```python
# my_solution/analyze_costs.py
def analyze_storage_by_prefix():
    # TODO: List all objects with storage class
    # TODO: Calculate cost per prefix
    # TODO: Recommend lifecycle transitions
    pass

def recommend_optimizations():
    # TODO: Identify objects in wrong storage class
    # TODO: Calculate potential savings
    pass
```

### Step 4: Implement Optimizaciones

```bash
# Apply lifecycle policies
python3 apply_lifecycle.py

# Expected output:
# Analyzing 10,000 objects...
# ✓ 7,000 objects older than 30 days → STANDARD_IA (save $87/month)
# ✓ 2,000 objects older than 90 days → GLACIER (save $46/month)
# Total potential savings: $133/month (58%)
```

### Step 5: Configure Dashboards

```python
# Create CloudWatch Dashboard
dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/S3", "BucketSizeBytes", {"stat": "Average"}],
                    ["AWS/S3", "NumberOfObjects", {"stat": "Average"}]
                ],
                "period": 86400,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Data Lake Storage"
            }
        }
    ]
}
```

## 🧪 Validation

```python
# Run tests
python3 test_cost_optimization.py

# Expected:
# ✓ CloudWatch metrics published
# ✓ Storage alarm created (threshold: 1 TB)
# ✓ Budget created ($500/month with 80% alert)
# ✓ Lifecycle policy applied (estimated savings: 58%)
# ✓ Dashboard created with 4 widgets
```

## 📊 Cost Analysis Report

```
Current Monthly Costs:
  S3 Storage (STANDARD): $230
  Data Transfer: $15
  Lambda Invocations: $5
  Total: $250/month

After Optimization:
  S3 Storage (mixed classes): $97
  Data Transfer: $15 (no change)
  Lambda (reserved): $3
  Total: $115/month

💰 Savings: $135/month (54% reduction)
```

## 📚 Deliverables

- ✅ `cloudwatch_metrics.py` (custom metrics)
- ✅ `cost_budgets.py` (budget configuration)
- ✅ `analyze_costs.py` (cost analysis script)
- ✅ `optimization_report.md` (savings analysis)
- ✅ Screenshot of CloudWatch Dashboard

## 💡 Real-World Tips

**Tagging Strategy:**
```python
tags = [
    {'Key': 'Project', 'Value': 'DataLake'},
    {'Key': 'Environment', 'Value': 'Production'},
    {'Key': 'CostCenter', 'Value': 'Engineering'},
    {'Key': 'Owner', 'Value': 'data-team@quickmart.com'}
]
```

**Compression Savings:**
```bash
# Before: 10 GB raw JSON
# After: 2 GB Parquet with Snappy
# Savings: 80% storage + 80% scan costs (Athena)
```

---

**Hints:** [hints.md](hints.md) | **Next:** [Module 02: Storage Basics](../../module-02-storage-basics/README.md)
