# Exercise 01: Cost Analysis with Cost Explorer & CUR

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐ Intermediate
💰 **AWS Cost:** ~$5 for CUR setup (S3 storage + Athena queries)

## Learning Objectives

- Query AWS Cost Explorer API for granular cost analysis
- Set up Cost and Usage Reports (CUR) with Athena integration
- Create custom cost dashboards and reports
- Implement cost allocation tagging strategy
- Detect cost anomalies programmatically

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS Accounts                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   Prod   │  │ Staging  │  │   Dev    │                 │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘                 │
└────────┼─────────────┼─────────────┼───────────────────────┘
         │             │             │
         └─────────────┴─────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Cost and Usage Reports (CUR)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  S3 Bucket: s3://cur-reports-bucket/                 │  │
│  │  ├── cur-data/                                        │  │
│  │  │   ├── 20240301-20240401/                          │  │
│  │  │   │   └── report.csv.gz (detailed line items)     │  │
│  │  │   └── manifest.json                               │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  AWS Glue Data Catalog                      │
│  Database: cost_usage_db                                    │
│  Table: cur_table (partitioned by year/month)              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Amazon Athena                            │
│  Query CUR data with SQL                                    │
│  - Cost by service                                          │
│  - Cost by tag (team, project, environment)                 │
│  - Daily cost trends                                        │
│  - Top 10 resources by cost                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Cost Dashboards & Alerts                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  QuickSight  │  │   Python     │  │    SNS       │      │
│  │  Dashboard   │  │   Reports    │  │   Alerts     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Tasks

### Task 1: Query Cost Explorer API

**Objective**: Use boto3 to query Cost Explorer for cost and usage data.

**Steps**:

1. **Get monthly costs by service**:

```python
import boto3
from datetime import datetime, timedelta
import pandas as pd

ce = boto3.client('ce', region_name='us-east-1')

# Get last 6 months
end = datetime.now().date()
start = (end - timedelta(days=180)).replace(day=1)

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': start.strftime('%Y-%m-%d'),
        'End': end.strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost', 'UsageQuantity'],
    GroupBy=[
        {'Type': 'DIMENSION', 'Key': 'SERVICE'}
    ]
)

# Parse results
costs = []
for result in response['ResultsByTime']:
    period = result['TimePeriod']['Start']

    for group in result['Groups']:
        service = group['Keys'][0]
        cost = float(group['Metrics']['UnblendedCost']['Amount'])
        usage = float(group['Metrics']['UsageQuantity']['Amount'])

        costs.append({
            'Period': period,
            'Service': service,
            'Cost': cost,
            'Usage': usage
        })

df = pd.DataFrame(costs)

# Top 10 services by cost
top_services = df.groupby('Service')['Cost'].sum().sort_values(ascending=False).head(10)
print("\n🔝 Top 10 Services by Cost (Last 6 Months):")
for service, cost in top_services.items():
    print(f"  {service}: ${cost:,.2f}")
```

2. **Get daily costs to identify trends**:

```python
# Get last 30 days with daily granularity
end = datetime.now().date()
start = end - timedelta(days=30)

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': start.strftime('%Y-%m-%d'),
        'End': end.strftime('%Y-%m-%d')
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost']
)

# Plot daily costs
daily_costs = []
for result in response['ResultsByTime']:
    date = result['TimePeriod']['Start']
    cost = float(result['Total']['UnblendedCost']['Amount'])
    daily_costs.append({'Date': date, 'Cost': cost})

df_daily = pd.DataFrame(daily_costs)
df_daily['Date'] = pd.to_datetime(df_daily['Date'])

# Calculate 7-day moving average
df_daily['MA7'] = df_daily['Cost'].rolling(window=7).mean()

print(f"\n📅 Daily Cost Statistics:")
print(f"  Average: ${df_daily['Cost'].mean():.2f}/day")
print(f"  Min: ${df_daily['Cost'].min():.2f}")
print(f"  Max: ${df_daily['Cost'].max():.2f}")
print(f"  Trend: {'📈 Increasing' if df_daily['Cost'].iloc[-7:].mean() > df_daily['Cost'].iloc[:7].mean() else '📉 Decreasing'}")
```

3. **Cost by tag (team/project allocation)**:

```python
# Get costs grouped by cost allocation tags
response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': (datetime.now().date().replace(day=1)).strftime('%Y-%m-%d'),
        'End': datetime.now().date().strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost'],
    GroupBy=[
        {'Type': 'TAG', 'Key': 'Team'},
        {'Type': 'TAG', 'Key': 'Project'}
    ]
)

# Parse and display
print("\n🏷️  Cost by Team and Project (Current Month):")
for result in response['ResultsByTime']:
    for group in result['Groups']:
        team = group['Keys'][0].split('$')[1] if '$' in group['Keys'][0] else 'No Tag'
        project = group['Keys'][1].split('$')[1] if '$' in group['Keys'][1] else 'No Tag'
        cost = float(group['Metrics']['UnblendedCost']['Amount'])

        print(f"  Team: {team}, Project: {project} → ${cost:.2f}")
```

### Task 2: Set Up Cost and Usage Reports (CUR)

**Objective**: Configure CUR for detailed cost analysis with Athena.

**Steps**:

1. **Create S3 bucket for CUR**:

```python
import boto3
import json

s3 = boto3.client('s3')
cur = boto3.client('cur', region_name='us-east-1')  # CUR API only in us-east-1
account_id = boto3.client('sts').get_caller_identity()['Account']

# Create bucket
bucket_name = f'cur-reports-{account_id}'
s3.create_bucket(Bucket=bucket_name)

# Bucket policy for CUR
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "billingreports.amazonaws.com"},
            "Action": ["s3:GetBucketAcl", "s3:GetBucketPolicy"],
            "Resource": f"arn:aws:s3:::{bucket_name}"
        },
        {
            "Effect": "Allow",
            "Principal": {"Service": "billingreports.amazonaws.com"},
            "Action": "s3:PutObject",
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }
    ]
}

s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
print(f"✓ CUR bucket created: {bucket_name}")
```

2. **Create CUR report definition**:

```python
# Create CUR report
cur.put_report_definition(
    ReportDefinition={
        'ReportName': 'hourly-cost-usage-report',
        'TimeUnit': 'HOURLY',
        'Format': 'Parquet',  # Use Parquet for better Athena performance
        'Compression': 'Parquet',
        'AdditionalSchemaElements': ['RESOURCES'],  # Include resource IDs
        'S3Bucket': bucket_name,
        'S3Prefix': 'cur-data',
        'S3Region': 'us-east-1',
        'AdditionalArtifacts': ['ATHENA'],  # Generate Athena integration
        'RefreshClosedReports': True,
        'ReportVersioning': 'OVERWRITE_REPORT'
    }
)

print("✓ CUR report definition created")
print("  Report Name: hourly-cost-usage-report")
print("  Format: Parque (optimized for Athena)")
print("  Frequency: Hourly updates")
print("  Note: First report available in 24 hours")
```

3. **Wait 24 hours for first report, then query with Athena**:

```python
import time

athena = boto3.client('athena')

# Database and table are auto-created by CUR
database = 'athenacurcfn_hourly_cost_usage_report'
output_location = f's3://{bucket_name}/athena-results/'

def execute_athena_query(query):
    """Execute Athena query and wait for results"""
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': output_location}
    )

    query_id = response['QueryExecutionId']

    # Wait for completion
    while True:
        status = athena.get_query_execution(QueryExecutionId=query_id)
        state = status['QueryExecution']['Status']['State']

        if state == 'SUCCEEDED':
            break
        elif state in ['FAILED', 'CANCELLED']:
            raise Exception(f"Query {state}: {status['QueryExecution']['Status'].get('StateChangeReason', '')}")

        time.sleep(2)

    # Get results
    results = athena.get_query_results(QueryExecutionId=query_id)
    return results

# Query 1: Total cost by service (current month)
query_service_costs = """
SELECT
    line_item_product_code AS service,
    ROUND(SUM(line_item_unblended_cost), 2) AS total_cost
FROM hourly_cost_usage_report
WHERE year='2024' AND month='03'
GROUP BY line_item_product_code
ORDER BY total_cost DESC
LIMIT 10;
"""

print("\n💰 Top 10 Services by Cost (Current Month):")
results = execute_athena_query(query_service_costs)

for row in results['ResultSet']['Rows'][1:]:  # Skip header
    service = row['Data'][0].get('VarCharValue', 'N/A')
    cost = row['Data'][1].get('VarCharValue', '0')
    print(f"  {service}: ${cost}")
```

### Task 3: Create Cost Allocation Tags

**Objective**: Implement tagging strategy for cost visibility and chargeback.

**Steps**:

1. **Define tagging strategy**:

```python
# Tagging schema
REQUIRED_TAGS = {
    'Environment': ['prod', 'staging', 'dev'],
    'Team': ['data-engineering', 'data-science', 'analytics'],
    'Project': ['customer-360', 'fraud-detection', 'recommendation-engine'],
    'CostCenter': ['engineering', 'marketing', 'sales'],
    'Owner': []  # Email address
}

def validate_tags(resource_tags):
    """Validate resource has required tags"""
    missing = []
    invalid = []

    for tag_key in REQUIRED_TAGS:
        if tag_key not in resource_tags:
            missing.append(tag_key)
        elif REQUIRED_TAGS[tag_key] and resource_tags[tag_key] not in REQUIRED_TAGS[tag_key]:
            invalid.append(f"{tag_key}={resource_tags[tag_key]}")

    return missing, invalid

# Example usage
resource_tags = {
    'Environment': 'prod',
    'Team': 'data-engineering',
    'Project': 'customer-360'
}

missing, invalid = validate_tags(resource_tags)
if missing:
    print(f"⚠️  Missing required tags: {', '.join(missing)}")
if invalid:
    print(f"⚠️  Invalid tag values: {', '.join(invalid)}")
```

2. **Activate cost allocation tags**:

```python
billing = boto3.client('ce')

# Activate tags for cost allocation
tags_to_activate = ['Team', 'Project', 'Environment', 'CostCenter', 'Owner']

# Note: Tag activation takes up to 24 hours
print("Activating cost allocation tags...")
for tag in tags_to_activate:
    print(f"  - {tag}")

print("\n✓ Tags will be active in 24 hours")
print("  After activation, tags appear in Cost Explorer and CUR")
```

3. **Tag existing resources**:

```python
def tag_all_s3_buckets():
    """Apply cost allocation tags to all S3 buckets"""
    s3 = boto3.client('s3')

    buckets = s3.list_buckets()['Buckets']

    for bucket in buckets:
        bucket_name = bucket['Name']

        # Determine tags based on bucket name patterns
        tags = {'Owner': 'data-team@example.com'}

        if 'prod' in bucket_name:
            tags['Environment'] = 'prod'
        elif 'staging' in bucket_name or 'stg' in bucket_name:
            tags['Environment'] = 'staging'
        else:
            tags['Environment'] = 'dev'

        # Apply tags
        try:
            s3.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={
                    'TagSet': [{'Key': k, 'Value': v} for k, v in tags.items()]
                }
            )
            print(f"✓ Tagged: {bucket_name}")
        except Exception as e:
            print(f"✗ Failed to tag {bucket_name}: {e}")

tag_all_s3_buckets()
```

### Task 4: Build Cost Dashboard

**Objective**: Create Python dashboard for cost visualization.

**Steps**:

1. **Cost trend visualization**:

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Assume df_daily from previous query
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 1. Daily cost trend
axes[0, 0].plot(df_daily['Date'], df_daily['Cost'], label='Daily Cost', alpha=0.6)
axes[0, 0].plot(df_daily['Date'], df_daily['MA7'], label='7-day MA', linewidth=2)
axes[0, 0].set_title('Daily Cost Trend')
axes[0, 0].set_xlabel('Date')
axes[0, 0].set_ylabel('Cost ($)')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# 2. Cost by service (pie chart)
top_services.plot(kind='pie', ax=axes[0, 1], autopct='%1.1f%%')
axes[0, 1].set_title('Cost Distribution by Service')
axes[0, 1].set_ylabel('')

# 3. Month-over-month growth
# Assume df from Task 1 with monthly data
monthly = df.pivot_table(index='Period', columns='Service', values='Cost', aggfunc='sum')
monthly.sum(axis=1).plot(kind='bar', ax=axes[1, 0])
axes[1, 0].set_title('Monthly Total Cost')
axes[1, 0].set_xlabel('Month')
axes[1, 0].set_ylabel('Cost ($)')

# 4. Cost by team (if tags available)
# Placeholder - would query CUR for tag-based costs
axes[1, 1].text(0.5, 0.5, 'Cost by Team\n(Requires cost allocation tags)',
                ha='center', va='center', fontsize=12)
axes[1, 1].set_title('Cost by Team')

plt.tight_layout()
plt.savefig('cost-dashboard.png', dpi=300, bbox_inches='tight')
print("✓ Dashboard saved: cost-dashboard.png")
```

### Task 5: Detect Cost Anomalies

**Objective**: Identify unusual spending patterns programmatically.

**Steps**:

1. **Statistical anomaly detection**:

```python
import numpy as np

def detect_anomalies(costs, threshold=2.5):
    """
    Detect anomalies using Z-score method
    threshold: Number of standard deviations
    """
    mean = np.mean(costs)
    std = np.std(costs)

    anomalies = []
    for i, cost in enumerate(costs):
        z_score = abs((cost - mean) / std)
        if z_score > threshold:
            anomalies.append({
                'index': i,
                'cost': cost,
                'z_score': z_score,
                'deviation': cost - mean
            })

    return anomalies, mean, std

# Apply to daily costs
costs = df_daily['Cost'].values
anomalies, mean, std = detect_anomalies(costs)

if anomalies:
    print(f"\n⚠️  Cost Anomalies Detected:")
    print(f"  Baseline: ${mean:.2f} ± ${std:.2f}")
    for anomaly in anomalies:
        date = df_daily.iloc[anomaly['index']]['Date'].strftime('%Y-%m-%d')
        print(f"  {date}: ${anomaly['cost']:.2f} (Z-score: {anomaly['z_score']:.2f}, +${anomaly['deviation']:.2f})")
else:
    print("✓ No significant cost anomalies detected")
```

2. **Use AWS Cost Anomaly Detection** service:

```python
# Create cost anomaly monitor
ce = boto3.client('ce')

monitor_arn = ce.create_anomaly_monitor(
    AnomalyMonitor={
        'MonitorName': 'DataPlatformCostMonitor',
        'MonitorType': 'DIMENSIONAL',
        'MonitorDimension': 'SERVICE'
    }
)['AnomalyMonitorArn']

print(f"✓ Anomaly monitor created: {monitor_arn}")

# Create subscription for alert
subscription_arn = ce.create_anomaly_subscription(
    AnomalySubscription={
        'SubscriptionName': 'DataPlatformCostAlerts',
        'Threshold': 100.0,  # Alert if anomaly > $100
        'Frequency': 'DAILY',
        'MonitorArnList': [monitor_arn],
        'Subscribers': [{
            'Type': 'EMAIL',
            'Address': 'data-team@example.com'
        }]
    }
)['SubscriptionArn']

print(f"✓ Anomaly subscription created: {subscription_arn}")
print("  Email alerts will be sent for anomalies > $100")
```

## Validation Checklist

- [ ] Successfully queried Cost Explorer API for monthly costs
- [ ] Retrieved daily cost trends and calculated moving averages
- [ ] Created CUR report definition
- [ ] CUR data visible in S3 bucket (after 24 hours)
- [ ] Queried CUR data with Athena
- [ ] Defined and documented cost allocation tagging strategy
- [ ] Tagged at least 10 existing resources
- [ ] Created cost dashboard visualization
- [ ] Implemented anomaly detection algorithm
- [ ] Set up AWS Cost Anomaly Detection service

## Troubleshooting

**Issue**: `AccessDeniedException` when calling Cost Explorer
- **Solution**: Ensure IAM user/role has `ce:GetCostAndUsage` permission
- Add policy: `arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess`

**Issue**: CUR report not generating
- **Solution**: Wait 24 hours for first report delivery
- Check S3 bucket policy allows billingreports.amazonaws.com
- Verify bucket is in us-east-1 region

**Issue**: Athena query fails on CUR table
- **Solution**: Run `MSCK REPAIR TABLE` to update partitions
- Ensure Glue Data Catalog has correct table schema
- Check S3 permissions for Athena role

**Issue**: Cost allocation tags not showing in Cost Explorer
- **Solution**: Activate tags in Billing Console
- Wait 24 hours after activation
- Ensure resources are tagged correctly

## Key Learnings

✅ **Cost Explorer API**: Programmatic cost queries with filters and grouping
✅ **CUR**: Most detailed billing data, queryable with Athena (Parquet for performance)
✅ **Cost Allocation Tags**: Foundation for showback/chargeback, team accountability
✅ **Anomaly Detection**: Statistical methods + AWS managed service
✅ **Dashboards**: Visualize trends, identify optimization opportunities

## Cost Optimization Insights

After analyzing your costs, common findings:
- **Top 5 services typically account for 80% of costs**
- **Dev/staging can be 20-40% of total** (optimization opportunity!)
- **Untagged resources**: 10-30% of costs (improve visibility)
- **Daily variations**: Weekends often 30-50% lower (stop dev resources!)

## Next Steps

- **Exercise 02**: S3 storage optimization (reduce storage costs 40-60%)
- **Exercise 03**: Reserved Instances and Savings Plans (save 30-70%)
- **Exercise 04**: Right-sizing (reduce over-provisioned resources)

## Additional Resources

- [Cost Explorer API Reference](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ce-api.html)
- [Cost and Usage Report Guide](https://docs.aws.amazon.com/cur/latest/userguide/)
- [AWS Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
