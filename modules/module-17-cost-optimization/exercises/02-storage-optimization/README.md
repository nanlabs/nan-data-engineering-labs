# Exercise 02: S3 Storage Cost Optimization

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐ Intermediate
💰 **Potential Savings:** 40-70% on S3 storage costs

## Learning Objectives

- Analyze S3 storage patterns with S3 Storage Lens
- Implement lifecycle policies for automatic transitions
- Configure S3 Intelligent-Tiering for unknown access patterns
- Optimize data formats (Parquet compression)
- Calculate actual storage cost savings

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   S3 Storage Classes                        │
│                                                             │
│  Upload           Frequent Access      Infrequent Access   │
│    │                    │                    │             │
│    ▼                    ▼                    ▼             │
│  ┌─────────┐      ┌──────────┐        ┌──────────┐        │
│  │ Standard│ ───▶ │ Standard-│  ───▶  │ Glacier  │        │
│  │ $0.023  │ 30d  │    IA    │  90d   │ Instant  │        │
│  │ per GB  │      │ $0.0125  │        │ $0.004   │        │
│  └─────────┘      └──────────┘        └──────────┘        │
│                                              │              │
│                                              │ 180d         │
│                                              ▼              │
│                                        ┌──────────┐         │
│                                        │ Glacier  │         │
│                                        │ Deep     │         │
│                                        │ Archive  │         │
│                                        │ $0.00099 │         │
│                                        └──────────┘         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      S3 Intelligent-Tiering (automatic)             │   │
│  │  Monitors access → Moves between tiers automatically│   │
│  │  $0.023 Frequent + $0.0125 Infrequent + $0.004 Archive│
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Tasks

### Task 1: Analyze Current S3 Storage

**Objective**: Use S3 Storage Lens to understand storage patterns.

**Steps**:

1. **Enable S3 Storage Lens**:

```python
import boto3
import json

s3control = boto3.client('s3control')
account_id = boto3.client('sts').get_caller-identity()['Account']

# Create Storage Lens configuration
config = {
    'Id': 'organization-storage-lens',
    'AccountLevel': {
        'BucketLevel': {
            'ActivityMetrics': {'IsEnabled': True},
            'PrefixLevel': {
                'StorageMetrics': {
                    'IsEnabled': True,
                    'SelectionCriteria': {
                        'MaxDepth': 5,
                        'MinStorageBytesPercentage': 1.0
                    }
                }
            }
        },
        'ActivityMetrics': {'IsEnabled': True}
    },
    'IsEnabled': True,
    'DataExport': {
        'S3BucketDestination': {
            'AccountId': account_id,
            'Arn': f'arn:aws:s3:::storage-lens-reports-{account_id}',
            'Format': 'CSV',
            'OutputSchemaVersion': 'V_1'
        }
    }
}

response = s3control.put_storage_lens_configuration(
    ConfigId='organization-storage-lens',
    AccountId=account_id,
    StorageLensConfiguration=config
)

print("✓ S3 Storage Lens enabled")
print("  Reports available in 24-48 hours")
```

2. **Analyze storage by bucket and prefix**:

```python
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

def analyze_bucket_storage(bucket_name):
    """Get storage metrics for a bucket"""
    # Get storage size from CloudWatch
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/S3',
        MetricName='BucketSizeBytes',
        Dimensions=[
            {'Name': 'BucketName', 'Value': bucket_name},
            {'Name': 'StorageType', 'Value': 'StandardStorage'}
        ],
        StartTime=datetime.now() - timedelta(days=1),
        EndTime=datetime.now(),
        Period=86400,  # 1 day
        Statistics=['Average']
    )

    if response['Datapoints']:
        size_bytes = response['Datapoints'][0]['Average']
        size_gb = size_bytes / (1024**3)

        # Calculate monthly cost (Standard class: $0.023/GB)
        monthly_cost = size_gb * 0.023

        return {
            'bucket': bucket_name,
            'size_gb': size_gb,
            'monthly_cost_standard': monthly_cost
        }
    return None

# Analyze all buckets
buckets = s3.list_buckets()['Buckets']
storage_analysis = []

print("\n📦 S3 Storage Analysis:\n")
for bucket in buckets:
    bucket_name = bucket['Name']
    analysis = analyze_bucket_storage(bucket_name)

    if analysis:
        storage_analysis.append(analysis)
        print(f"  {bucket_name}:")
        print(f"    Size: {analysis['size_gb']:.2f} GB")
        print(f"    Monthly Cost (Standard): ${analysis['monthly_cost_standard']:.2f}")

# Sort by cost
storage_analysis.sort(key=lambda x: x['monthly_cost_standard'], reverse=True)
total_cost = sum(a['monthly_cost_standard'] for a in storage_analysis)
print(f"\n💰 Total S3 Storage Cost: ${total_cost:.2f}/month")
```

### Task 2: Implement Lifecycle Policies

**Objective**: Automate transition to cheaper storage classes.

**Steps**:

1. **Create lifecycle policy for data lake**:

```python
# Lifecycle policy: Standard → IA → Glacier → Deep Archive
lifecycle_policy = {
    'Rules': [
        {
            'Id': 'RawDataLifecycle',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'raw/'},
            'Transitions': [
                {
                    'Days': 30,
                    'StorageClass': 'STANDARD_IA'  # Save ~45% after 30 days
                },
                {
                    'Days': 90,
                    'StorageClass': 'GLACIER_IR'  # Save ~82% after 90 days
                },
                {
                    'Days': 180,
                    'StorageClass': 'DEEP_ARCHIVE'  # Save ~95% after 180 days
                }
            ],
            'NoncurrentVersionTransitions': [
                {
                    'NoncurrentDays': 7,
                    'StorageClass': 'GLACIER_IR'
                }
            ],
            'Expiration': {
                'Days': 365  # Delete after 1 year
            }
        },
        {
            'Id': 'CuratedDataLifecycle',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'curated/'},
            'Transitions': [
                {
                    'Days': 90,
                    'StorageClass': 'STANDARD_IA'  # Keep accessible longer
                },
                {
                    'Days': 365,
                    'StorageClass': 'GLACIER_IR'
                }
            ]
        },
        {
            'Id': 'LogsLifecycle',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'logs/'},
            'Transitions': [
                {
                    'Days': 7,
                    'StorageClass': 'STANDARD_IA'
                },
                {
                    'Days': 30,
                    'StorageClass': 'GLACIER_IR'
                }
            ],
            'Expiration': {
                'Days': 90  # Delete logs after 90 days
            }
        }
    ]
}

s3.put_bucket_lifecycle_configuration(
    Bucket='data-lake-bucket',
    LifecycleConfiguration=lifecycle_policy
)

print("✓ Lifecycle policies applied")

# Calculate estimated savings
def calculate_lifecycle_savings(size_gb, days_standard, days_ia, days_glacier, days_deep):
    """Calculate monthly savings from lifecycle policy"""
    # Pricing per GB-month
    standard = 0.023
    ia = 0.0125
    glacier_ir = 0.004
    deep_archive = 0.00099

    # Current cost (all in Standard)
    current_cost = size_gb * standard

    # Optimized cost (lifecycle transitions)
    days_total = days_standard + days_ia + days_glacier + days_deep
    optimized_cost = (
        size_gb * standard * (days_standard / days_total) +
        size_gb * ia * (days_ia / days_total) +
        size_gb * glacier_ir * (days_glacier / days_total) +
        size_gb * deep_archive * (days_deep / days_total)
    )

    savings = current_cost - optimized_cost
    savings_pct = (savings / current_cost) * 100

    return current_cost, optimized_cost, savings, savings_pct

# Example: 1000 GB with lifecycle policy
current, optimized, savings, pct = calculate_lifecycle_savings(
    size_gb=1000,
    days_standard=30,
    days_ia=60,
    days_glacier=90,
    days_deep=185
)

print(f"\n💰 Estimated Savings (1000 GB):")
print(f"  Current Cost (all Standard): ${current:.2f}/month")
print(f"  Optimized Cost (lifecycle): ${optimized:.2f}/month")
print(f"  Savings: ${savings:.2f}/month ({pct:.1f}%)")
```

2. **Configure S3 Intelligent-Tiering**:

```python
# Enable Intelligent-Tiering for buckets with unknown access patterns
s3.put_bucket_intelligent_tiering_configuration(
    Bucket='analytics-bucket',
    Id='entire-bucket-tiering',
    IntelligentTieringConfiguration={
        'Id': 'entire-bucket-tiering',
        'Status': 'Enabled',
        'Tierings': [
            {
                'Days': 90,
                'AccessTier': 'ARCHIVE_ACCESS'  # Move to Archive tier after 90 days
            },
            {
                'Days': 180,
                'AccessTier': 'DEEP_ARCHIVE_ACCESS'  # Move to Deep Archive after 180 days
            }
        ]
    }
)

print("✓ Intelligent-Tiering configured")
print("  Automatic transitions: Frequent ↔ Infrequent (30 days)")
print("  Archive Access: After 90 days of no access")
print("  Deep Archive: After 180 days of no access")
```

### Task 3: Optimize Data Formats

**Objective**: Reduce storage costs with compression and columnar formats.

**Steps**:

1. **Convert CSV to Parquet with compression**:

```python
import pandas as pd

# Read CSV
df = pd.read_csv('s3://data-lake/raw/sales-data.csv')

print(f"Original CSV size: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Write Parquet with Snappy compression
df.to_parquet(
    's3://data-lake/curated/sales-data.parquet',
    compression='snappy',
    index=False
)

# Compare sizes
csv_size = s3.head_object(Bucket='data-lake', Key='raw/sales-data.csv')['ContentLength']
parquet_size = s3.head_object(Bucket='data-lake', Key='curated/sales-data.parquet')['ContentLength']

compression_ratio = (1 - parquet_size / csv_size) * 100

print(f"\n📊 Compression Results:")
print(f"  CSV: {csv_size / 1024**2:.2f} MB")
print(f"  Parquet (Snappy): {parquet_size / 1024**2:.2f} MB")
print(f"  Compression: {compression_ratio:.1f}% reduction")
print(f"  Storage Savings: ${(csv_size - parquet_size) / 1024**3 * 0.023:.2f}/month")
```

2. **Benchmark query performance and cost**:

```python
import time

athena = boto3.client('athena')

def query_athena(query, database='default'):
    """Execute Athena query and return execution stats"""
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': 's3://athena-results/'}
    )

    query_id = response['QueryExecutionId']

    # Wait for completion
    while True:
        execution = athena.get_query_execution(QueryExecutionId=query_id)
        state = execution['QueryExecution']['Status']['State']

        if state == 'SUCCEEDED':
            stats = execution['QueryExecution']['Statistics']
            return {
                'execution_time_ms': stats.get('EngineExecutionTimeInMillis', 0),
                'data_scanned_bytes': stats.get('DataScannedInBytes', 0),
                'cost': stats.get('DataScannedInBytes', 0) / (1024**4) * 5.0  # $5 per TB
            }
        elif state in ['FAILED', 'CANCELLED']:
            raise Exception(f"Query failed: {execution['QueryExecution']['Status'].get('StateChangeReason', '')}")

        time.sleep(1)

# Compare CSV vs Parquet query costs
query = "SELECT COUNT(*), AVG(sales_amount) FROM sales_data WHERE year=2024"

print("\n⚡ Query Performance Comparison:\n")

# Query CSV
csv_stats = query_athena(f"SELECT COUNT(*), AVG(sales_amount) FROM sales_data_csv WHERE year=2024")
print(f"CSV Format:")
print(f"  Data Scanned: {csv_stats['data_scanned_bytes'] / 1024**3:.2f} GB")
print(f"  Query Cost: ${csv_stats['cost']:.4f}")
print(f"  Execution Time: {csv_stats['execution_time_ms']/1000:.2f}s")

# Query Parquet
parquet_stats = query_athena(f"SELECT COUNT(*), AVG(sales_amount) FROM sales_data_parquet WHERE year=2024")
print(f"\nParquet Format:")
print(f"  Data Scanned: {parquet_stats['data_scanned_bytes'] / 1024**3:.2f} GB")
print(f"  Query Cost: ${parquet_stats['cost']:.4f}")
print(f"  Execution Time: {parquet_stats['execution_time_ms']/1000:.2f}s")

# Calculate savings
scan_reduction = (1 - parquet_stats['data_scanned_bytes'] / csv_stats['data_scanned_bytes']) * 100
cost_reduction = (1 - parquet_stats['cost'] / csv_stats['cost']) * 100

print(f"\n💰 Savings:")
print(f"  Data Scanned: {scan_reduction:.1f}% reduction")
print(f"  Query Cost: {cost_reduction:.1f}% reduction")
print(f"  If 1000 queries/month: ${(csv_stats['cost'] - parquet_stats['cost']) * 1000:.2f}/month saved")
```

### Task 2: Implement Cost-Optimized Lifecycle Policy

**Objective**: Create comprehensive lifecycle policy based on access patterns.

**Steps**:

1. **Analyze object access patterns**:

```python
from collections import defaultdict
from dateutil import parser

def analyze_access_patterns(bucket_name):
    """Analyze S3 access logs to determine object access frequency"""
    s3 = boto3.client('s3')

    # Enable S3 access logging first
    s3.put_bucket_logging(
        Bucket=bucket_name,
        BucketLoggingStatus={
            'LoggingEnabled': {
                'TargetBucket': f'{bucket_name}-logs',
                'TargetPrefix': 'access-logs/'
            }
        }
    )

    # Analyze access patterns (simplified - would parse actual logs)
    access_counts = defaultdict(int)
    last_access = {}

    # Example: Simulate access pattern analysis
    objects = s3.list_objects_v2(Bucket=bucket_name)

    for obj in objects.get('Contents', []):
        key = obj['Key']
        last_modified = obj['LastModified']
        days_since_modified = (datetime.now(timezone.utc) - last_modified).days

        # Categorize by age
        if days_since_modified < 30:
            category = 'Hot Data (< 30 days)'
        elif days_since_modified < 90:
            category = 'Warm Data (30-90 days)'
        elif days_since_modified < 180:
            category = 'Cool Data (90-180 days)'
        else:
            category = 'Cold Data (> 180 days)'

        access_counts[category] += 1

    return access_counts

# Analyze
patterns = analyze_access_patterns('data-lake-bucket')

print("\n📊 Access Pattern Analysis:")
total = sum(patterns.values())
for category, count in sorted(patterns.items()):
    pct = (count / total) * 100
    print(f"  {category}: {count} objects ({pct:.1f}%)")

# Recommend lifecycle policy based on patterns
print("\n💡 Recommended Lifecycle Policy:")
if patterns.get('Cold Data (> 180 days)', 0) > total * 0.3:
    print("  ✓ High percentage of cold data → Aggressive Glacier transitions")
else:
    print("  ✓ Frequent access → Use Intelligent-Tiering")
```

2. **Implement optimized lifecycle policy**:

```python
# Advanced lifecycle policy with multiple rules
lifecycle_config = {
    'Rules': [
        {
            'Id': 'data-lake-raw-aggressive',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'raw/'},
            'Transitions': [
                {'Days': 30, 'StorageClass': 'INTELLIGENT_TIERING'},
            ],
            'NoncurrentVersionExpiration': {'NoncurrentDays': 30},
            'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 7}
        },
        {
            'Id': 'data-lake-curated-standard',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'curated/'},
            'Transitions': [
                {'Days': 90, 'StorageClass': 'STANDARD_IA'},
                {'Days': 365, 'StorageClass': 'GLACIER_IR'}
            ]
        },
        {
            'Id': 'temp-data-cleanup',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'temp/'},
            'Expiration': {'Days': 7}  # Auto-delete temp data
        },
        {
            'Id': 'incomplete-multipart-cleanup',
            'Status': 'Enabled',
            'Filter': {},
            'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 1}
        }
    ]
}

s3.put_bucket_lifecycle_configuration(
    Bucket='data-lake-bucket',
    LifecycleConfiguration=lifecycle_config
)

print("✓ Lifecycle policies applied")

# Calculate projected savings
def project_lifecycle_savings(current_storage_gb, rules):
    """Project savings from lifecycle policy"""
    # Assume distribution based on analysis
    hot_pct = 0.2   # 20% accessed in last 30 days
    warm_pct = 0.3  # 30% accessed 30-90 days ago
    cool_pct = 0.3  # 30% accessed 90-180 days ago
    cold_pct = 0.2  # 20% accessed > 180 days ago

    # Standard: $0.023/GB
    # IA: $0.0125/GB
    # Glacier IR: $0.004/GB
    # Deep Archive: $0.00099/GB

    current_cost = current_storage_gb * 0.023

    optimized_cost = (
        current_storage_gb * hot_pct * 0.023 +      # Hot stays in Standard
        current_storage_gb * warm_pct * 0.0125 +    # Warm → IA
        current_storage_gb * cool_pct * 0.004 +     # Cool → Glacier IR
        current_storage_gb * cold_pct * 0.00099     # Cold → Deep Archive
    )

    savings = current_cost - optimized_cost
    savings_pct = (savings / current_cost) * 100

    return current_cost, optimized_cost, savings, savings_pct

# Project savings for your data lake
total_storage = sum(a['size_gb'] for a in storage_analysis)
current, optimized, savings, pct = project_lifecycle_savings(total_storage, lifecycle_config['Rules'])

print(f"\n💰 Projected Monthly Savings:")
print(f"  Current Cost (all Standard): ${current:.2f}")
print(f"  Optimized Cost (lifecycle): ${optimized:.2f}")
print(f"  Monthly Savings: ${savings:.2f} ({pct:.1f}%)")
print(f"  Annual Savings: ${savings * 12:.2f}")
```

### Task 3: Configure Intelligent-Tiering

**Objective**: Enable automatic cost optimization for unpredictable access.

**Steps**:

```python
# Enable Intelligent-Tiering for new uploads
s3.put_bucket_intelligent_tiering_configuration(
    Bucket='analytics-workspace',
    Id='workspace-tiering',
    IntelligentTieringConfiguration={
        'Id': 'workspace-tiering',
        'Status': 'Enabled',
        'Filter': {'Prefix': 'workspace/'},
        'Tierings': [
            {'Days': 90, 'AccessTier': 'ARCHIVE_ACCESS'},
            {'Days': 180, 'AccessTier': 'DEEP_ARCHIVE_ACCESS'}
        ]
    }
)

# Set default storage class for new uploads
print("✓ Intelligent-Tiering configured")
print("\n  How it works:")
print("  1. Objects start in Frequent Access tier ($0.023/GB)")
print("  2. Not accessed for 30 days → Infrequent Access ($0.0125/GB)")
print("  3. Not accessed for 90 days → Archive Access ($0.004/GB)")
print("  4. Not accessed for 180 days → Deep Archive ($0.00099/GB)")
print("  5. Accessed → Automatically moves back to Frequent tier")
print("\n  Monitoring fee: $0.0025 per 1000 objects (small price for auto-optimization)")
```

## Validation Checklist

- [ ] Enabled S3 Storage Lens for organization-wide visibility
- [ ] Analyzed storage by bucket and calculated current costs
- [ ] Created lifecycle policies for at least 3 buckets
- [ ] Configured Intelligent-Tiering for unpredictable workloads
- [ ] Converted CSV to Parquet and measured compression ratio
- [ ] Benchmarked Athena query costs (CSV vs Parquet)
- [ ] Calculated projected savings from optimizations
- [ ] Documented tagging strategy for cost allocation

## Troubleshooting

**Issue**: Lifecycle policy not transitioning objects
- **Solution**: Check object size (min 128 KB for IA, Glacier)
- Verify policy status is 'Enabled'
- Wait 24-48 hours for first transition

**Issue**: Intelligent-Tiering shows no savings
- **Solution**: Ensure monitoring is enabled
- Check object sizes (min 128 KB)
- Wait 30+ days for first transitions

**Issue**: Parquet files larger than CSV
- **Solution**: Use appropriate compression (Snappy for balance, Gzip for max compression)
- Ensure data types are optimized (int32 vs int64)
- Remove unnecessary columns before writing

## Key Learnings

✅ **Storage Classes**: 95% cost reduction possible (Standard → Deep Archive)
✅ **Lifecycle Policies**: Automate transitions, eliminate manual management
✅ **Intelligent-Tiering**: Best for unknown patterns, automatic optimization
✅ **Parquet + Compression**: 80-90% reduction vs CSV, faster queries
✅ **Cost Allocation**: Tagging enables showback/chargeback

## Real-World Impact

**Case Study**: E-commerce data lake (10 TB storage)
- **Before**: 10 TB Standard ($230/month)
- **After**: Lifecycle + Parquet (5 TB effective)
  - 1 TB Standard ($23)
  - 2 TB IA ($25)
  - 1 TB Glacier IR ($4)
  - 1 TB Deep Archive ($1)
- **Total Optimized**: $53/month
- **Savings**: $177/month (77% reduction, $2,124/year)

## Next Steps

- **Exercise 03**: Compute purchasing options (RI, Savings Plans, Spot)
- **Exercise 04**: Right-sizing over-provisioned resources

## Additional Resources

- [S3 Storage Classes](https://aws.amazon.com/s3/storage-classes/)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [S3 Intelligent-Tiering](https://aws.amazon.com/s3/storage-classes/intelligent-tiering/)
- [Parquet Format Specification](https://parquet.apache.org/docs/)
