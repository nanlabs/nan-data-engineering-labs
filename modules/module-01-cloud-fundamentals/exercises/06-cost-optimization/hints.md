# Hints - Exercise 06: Cost Optimization

## 🟢 NIVEL 1: Conceptual Hints

### Hint 1.1: Storage Cost Breakdown

```
S3 Storage Classes (per GB/month):
- STANDARD:      $0.023   (immediate access)
- STANDARD_IA:   $0.0125  (infrequent, retrieval fee)
- GLACIER:       $0.004   (archive, hours to restore)
- DEEP_ARCHIVE:  $0.00099 (long-term, 12+ hours restore)
```

**Rule of thumb:** Data not accessed in 30 days → move to IA

### Hint 1.2: Lambda Cost Formula

```python
cost_per_invocation = (memory_gb * duration_seconds * $0.0000166667)
monthly_cost = invocations_per_month * cost_per_invocation

Example:
- 1M invocations
- 512MB memory
- 1000ms duration
→ 1,000,000 × (0.5 × 1 × 0.0000166667) = $8.33/month
```

**Optimization:** Use minimum memory that doesn't timeout

### Hint 1.3: CloudWatch Logs Costs

```
- Ingestion: $0.50/GB (one-time)
- Storage: $0.03/GB/month (recurring)
- Retention: 7/30/90/180/365/never

Optimization Strategy:
1. Reduce retention: 180d → 7d (saves 96%)
2. Export to S3: $0.03/GB → $0.004/GB (saves 87%)
```

---

## 🟡 NIVEL 2: Implementation Hints

### Hint 2.1: S3 Storage Analysis

```python
import boto3
from datetime import datetime, timezone

s3 = boto3.client('s3')

def analyze_bucket(bucket_name):
    age_buckets = {
        'hot': 0, 'warm': 0, 'cold': 0, 'archive': 0
    }

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            last_modified = obj['LastModified']
            age_days = (datetime.now(timezone.utc) - last_modified).days
            size = obj['Size']

            if age_days <= 30:
                age_buckets['hot'] += size
            elif age_days <= 90:
                age_buckets['warm'] += size
            elif age_days <= 365:
                age_buckets['cold'] += size
            else:
                age_buckets['archive'] += size

    # Convert to GB
    for key in age_buckets:
        age_buckets[key] = age_buckets[key] / (1024**3)

    return age_buckets
```

### Hint 2.2: Cost Calculation

```python
def calculate_costs(age_buckets):
    pricing = {
        'STANDARD': 0.023,
        'STANDARD_IA': 0.0125,
        'GLACIER': 0.004,
        'DEEP_ARCHIVE': 0.00099
    }

    # Current: all STANDARD
    current_cost = sum(age_buckets.values()) * pricing['STANDARD']

    # Optimized: tiered
    optimized_cost = (
        age_buckets['hot'] * pricing['STANDARD'] +
        age_buckets['warm'] * pricing['STANDARD_IA'] +
        age_buckets['cold'] * pricing['GLACIER'] +
        age_buckets['archive'] * pricing['DEEP_ARCHIVE']
    )

    savings = current_cost - optimized_cost
    savings_percent = (savings / current_cost) * 100 if current_cost > 0 else 0

    return {
        'current': current_cost,
        'optimized': optimized_cost,
        'savings': savings,
        'savings_percent': savings_percent
    }
```

### Hint 2.3: Lifecycle Policy Generator

```python
def generate_lifecycle_policy(bucket_name):
    policy = {
        'Rules': [
            {
                'Id': 'intelligent-tiering',
                'Status': 'Enabled',
                'Filter': {'Prefix': ''},
                'Transitions': [
                    {
                        'Days': 30,
                        'StorageClass': 'STANDARD_IA'
                    },
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    },
                    {
                        'Days': 365,
                        'StorageClass': 'DEEP_ARCHIVE'
                    }
                ]
            },
            {
                'Id': 'delete-old-versions',
                'Status': 'Enabled',
                'NoncurrentVersionExpiration': {
                    'NoncurrentDays': 90
                }
            }
        ]
    }

    # Apply policy
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration=policy
    )
```

### Hint 2.4: Lambda Performance Analysis

```python
def analyze_lambda(function_name):
    # Get function config
    function = lambda_client.get_function(FunctionName=function_name)
    current_memory = function['Configuration']['MemorySize']

    # Query CloudWatch Logs Insights
    query = """
    fields @memorySize / 1000000 as memoryUsedMB, @duration
    | stats
        avg(@duration) as avg_duration,
        max(@duration) as max_duration,
        avg(memoryUsedMB) as avg_memory,
        max(memoryUsedMB) as max_memory,
        count() as invocations
    """

    log_group = f'/aws/lambda/{function_name}'

    response = logs.start_query(
        logGroupName=log_group,
        startTime=int((datetime.now() - timedelta(days=7)).timestamp()),
        endTime=int(datetime.now().timestamp()),
        queryString=query
    )

    # Wait and get results
    query_id = response['queryId']
    result = logs.get_query_results(queryId=query_id)

    # Parse results
    stats = {}
    for field in result['results'][0]:
        stats[field['field']] = float(field['value'])

    # Recommend memory (avg + 20% buffer, rounded to 64MB)
    recommended_memory = int((stats['avg_memory'] * 1.2) / 64) * 64
    recommended_memory = max(128, min(10240, recommended_memory))

    return {
        'current_memory': current_memory,
        'recommended_memory': recommended_memory,
        'avg_duration': stats['avg_duration'],
        'invocations': stats['invocations']
    }
```

### Hint 2.5: AWS Budget Creation

```python
import boto3

budgets = boto3.client('budgets')

def create_budget(account_id, amount, email):
    response = budgets.create_budget(
        AccountId=account_id,
        Budget={
            'BudgetName': 'monthly-cost-budget',
            'BudgetLimit': {
                'Amount': str(amount),
                'Unit': 'USD'
            },
            'TimeUnit': 'MONTHLY',
            'BudgetType': 'COST'
        },
        NotificationsWithSubscribers=[
            {
                'Notification': {
                    'NotificationType': 'ACTUAL',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': 80,
                    'ThresholdType': 'PERCENTAGE'
                },
                'Subscribers': [
                    {
                        'SubscriptionType': 'EMAIL',
                        'Address': email
                    }
                ]
            },
            {
                'Notification': {
                    'NotificationType': 'FORECASTED',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': 100,
                    'ThresholdType': 'PERCENTAGE'
                },
                'Subscribers': [
                    {
                        'SubscriptionType': 'EMAIL',
                        'Address': email
                    }
                ]
            }
        ]
    )
```

---

## 🔴 NIVEL 3: Complete Solutions

See solution files for:
- [s3_storage_analyzer.py](solution/s3_storage_analyzer.py) - Full analysis with CSV export
- [logs_analyzer.py](solution/logs_analyzer.py) - CloudWatch Logs cost analysis
- [lambda_profiler.py](solution/lambda_profiler.py) - Right-sizing recommendations
- [resource_scanner.py](solution/resource_scanner.py) - Find unused resources
- [cost_report.py](solution/cost_report.py) - Generate monthly report

---

## 🧪 Testing Tips

### Test 1: S3 Analysis

```bash
# Generate test data with different ages
python3 ../data/sample/generate_sample_data.py

# Upload to S3
aws s3 cp transactions-sample.csv s3://bucket/data/

# Modify object dates (for testing)
aws s3api copy-object \
  --copy-source bucket/data/old-file.csv \
  --bucket bucket \
  --key data/old-file.csv \
  --metadata-directive REPLACE

# Run analyzer
python3 s3_storage_analyzer.py --bucket quickmart-data-lake-dev
```

### Test 2: Lambda Profiling

```bash
# Invoke Lambda multiple times
for i in {1..100}; do
    aws lambda invoke \
      --function-name csv-validator \
      --payload '{"test": true}' \
      output.json
done

# Wait for logs (5 minutes)
sleep 300

# Run profiler
python3 lambda_profiler.py
```

### Test 3: Budget Creation

```bash
# Create budget (requires account ID)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

python3 -c "
from create_budget import create_budget
create_budget('$ACCOUNT_ID', 800, 'your-email@example.com')
"

# Verify
aws budgets describe-budgets --account-id $ACCOUNT_ID
```

---

## 🐛 Common Issues

### Error: "Access Denied" for CloudWatch Logs Insights

**Fix:** Add IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "logs:StartQuery",
    "logs:GetQueryResults"
  ],
  "Resource": "*"
}
```

### Error: "Rate exceeded" when listing S3 objects

**Fix:** Add throttling:
```python
import time

for page in paginator.paginate(Bucket=bucket_name):
    process_page(page)
    time.sleep(0.1)  # 100ms delay
```

### Error: Budget creation requires confirmation

**Cause:** Email subscription not confirmed

**Fix:** Check email and click confirmation link

---

## 📚 Additional Resources

- [AWS Cost Optimization](https://aws.amazon.com/pricing/cost-optimization/)
- [S3 Storage Classes](https://aws.amazon.com/s3/storage-classes/)
- [Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning)
- [AWS Trusted Advisor](https://aws.amazon.com/premiumsupport/technology/trusted-advisor/)
