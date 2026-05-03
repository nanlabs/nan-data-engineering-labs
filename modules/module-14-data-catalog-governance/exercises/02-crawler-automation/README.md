# Exercise 02: Crawler Automation

## Objective

Learn to configure and run AWS Glue Crawlers to automatically discover, classify, and update table schemas in the Data Catalog.

## Prerequisites

- Exercise 01 completed (catalog databases created)
- LocalStack running with Glue service enabled
- Sample data in S3 bucket

## Learning Goals

- Configure crawlers with proper settings
- Understand schema change policies
- Implement crawler scheduling patterns
- Handle partition discovery automatically
- Monitor crawler execution and results

## Exercise Tasks

### Task 1: Create IAM Role for Crawler

First, create an IAM role with permissions for the crawler:

```bash
# Create trust policy for Glue service
cat > /tmp/glue-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
awslocal iam create-role \
    --role-name AWSGlueServiceRole-DataLake \
    --assume-role-policy-document file:///tmp/glue-trust-policy.json

# Attach managed policy for Glue
awslocal iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataLake \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole

# Attach S3 access policy
awslocal iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataLake \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Task 2: Create Bronze Layer Crawler

Configure a crawler to scan raw CSV files:

```bash
# Create crawler for Bronze sales data
awslocal glue create-crawler \
    --name sales-bronze-crawler \
    --role arn:aws:iam::000000000000:role/AWSGlueServiceRole-DataLake \
    --database-name dev_sales_bronze_db \
    --description "Crawls raw sales transaction data from S3" \
    --targets '{
        "S3Targets": [
            {
                "Path": "s3://training-data-lake/bronze/sales/transactions/",
                "Exclusions": [
                    "*.tmp",
                    "_SUCCESS",
                    "_temporary/**",
                    ".spark-staging/**"
                ]
            }
        ]
    }' \
    --schema-change-policy '{
        "UpdateBehavior": "UPDATE_IN_DATABASE",
        "DeleteBehavior": "LOG"
    }' \
    --recrawl-policy '{
        "RecrawlBehavior": "CRAWL_NEW_FOLDERS_ONLY"
    }' \
    --lineage-configuration '{
        "CrawlerLineageSettings": "ENABLE"
    }' \
    --configuration '{
        "Version": 1.0,
        "CrawlerOutput": {
            "Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}
        },
        "Grouping": {
            "TableGroupingPolicy": "CombineCompatibleSchemas"
        }
    }' \
    --tags '{
        "Environment": "development",
        "DataDomain": "Sales",
        "Layer": "Bronze",
        "ManagedBy": "DataEngineering"
    }'

# Verify crawler creation
awslocal glue get-crawler --name sales-bronze-crawler
```

### Task 3: Create Silver Layer Crawler

Configure a crawler for Parquet files with different settings:

```bash
# Create crawler for Silver layer
awslocal glue create-crawler \
    --name sales-silver-crawler \
    --role arn:aws:iam::000000000000:role/AWSGlueServiceRole-DataLake \
    --database-name dev_sales_silver_db \
    --description "Crawls cleaned sales data in Silver layer" \
    --targets '{
        "S3Targets": [
            {
                "Path": "s3://training-data-lake/silver/sales/transactions/",
                "Exclusions": [
                    "_spark_metadata/**",
                    "*.crc",
                    "_committed_*",
                    "_started_*"
                ],
                "SampleSize": 5
            }
        ]
    }' \
    --schema-change-policy '{
        "UpdateBehavior": "UPDATE_IN_DATABASE",
        "DeleteBehavior": "DEPRECATE_IN_DATABASE"
    }' \
    --recrawl-policy '{
        "RecrawlBehavior": "CRAWL_NEW_FOLDERS_ONLY"
    }' \
    --configuration '{
        "Version": 1.0,
        "CrawlerOutput": {
            "Partitions": {"AddOrUpdateBehavior": "InheritFromTable"},
            "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}
        }
    }' \
    --tags '{
        "Environment": "development",
        "DataDomain": "Sales",
        "Layer": "Silver"
    }'
```

### Task 4: Add Crawler Schedule

Configure automatic execution schedules:

```bash
# Update Bronze crawler with daily schedule (2 AM UTC)
awslocal glue update-crawler \
    --name sales-bronze-crawler \
    --schedule "cron(0 2 * * ? *)"

# Update Silver crawler to run after Bronze (4 AM UTC)
awslocal glue update-crawler \
    --name sales-silver-crawler \
    --schedule "cron(0 4 * * ? *)"

# Verify schedules
awslocal glue get-crawler --name sales-bronze-crawler | grep Schedule
awslocal glue get-crawler --name sales-silver-crawler | grep Schedule
```

### Task 5: Run Crawler Manually

Execute crawlers and monitor their progress:

```bash
# Start Bronze crawler
awslocal glue start-crawler --name sales-bronze-crawler

# Check crawler status
awslocal glue get-crawler --name sales-bronze-crawler | grep State

# Wait for completion (poll every 10 seconds)
while true; do
    STATE=$(awslocal glue get-crawler --name sales-bronze-crawler --query 'Crawler.State' --output text)
    echo "Crawler state: $STATE"
    if [ "$STATE" == "READY" ]; then
        break
    fi
    sleep 10
done

# Get crawler metrics
awslocal glue get-crawler-metrics --crawler-name-list sales-bronze-crawler
```

### Task 6: Analyze Crawler Results

Check what the crawler discovered:

```bash
# Get tables created/updated by crawler
awslocal glue get-tables \
    --database-name dev_sales_bronze_db \
    --query 'TableList[?Parameters.UPDATED_BY_CRAWLER==`sales-bronze-crawler`]'

# Get partitions discovered
awslocal glue get-partitions \
    --database-name dev_sales_bronze_db \
    --table-name sales_transactions \
    --query 'Partitions[*].{Values:Values,Location:StorageDescriptor.Location,Records:Parameters.recordCount}'

# Check crawler statistics
awslocal glue get-crawler --name sales-bronze-crawler \
    --query 'Crawler.LastCrawl.{Status:Status,TablesCreated:TablesCreated,TablesUpdated:TablesUpdated,TablesDeleted:TablesDeleted}'
```

### Task 7: Handle Schema Changes

Simulate schema evolution and see how crawler handles it:

```python
# schema_evolution_test.py
import boto3
import pandas as pd
import io

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

glue = boto3.client(
    'glue',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

print("=== Original Schema ===")
table_v1 = glue.get_table(
    DatabaseName='dev_sales_bronze_db',
    Name='sales_transactions'
)
for col in table_v1['Table']['StorageDescriptor']['Columns']:
    print(f"- {col['Name']}: {col['Type']}")

# Upload new data with additional column
print("\n=== Uploading data with new column 'discount_amount' ===")
new_data = """date,transaction_id,customer_id,product_id,quantity,total_amount,discount_amount
2024-03-09,TXN-20051,CUST-4501,PROD-E101,1,899.99,50.00
2024-03-09,TXN-20052,CUST-4502,PROD-H205,2,91.00,10.00
"""
s3.put_object(
    Bucket='training-data-lake',
    Key='bronze/sales/transactions/year=2024/month=03/day=09/sales.csv',
    Body=new_data
)

# Run crawler to detect schema change
print("\n=== Running crawler to detect schema change ===")
glue.start_crawler(Name='sales-bronze-crawler')

# Wait for crawler (in real scenario, use waiter or async)
import time
time.sleep(30)

# Check updated schema
print("\n=== Updated Schema ===")
table_v2 = glue.get_table(
    DatabaseName='dev_sales_bronze_db',
    Name='sales_transactions'
)
for col in table_v2['Table']['StorageDescriptor']['Columns']:
    print(f"- {col['Name']}: {col['Type']}")

# Check version history
versions = glue.get_table_versions(
    DatabaseName='dev_sales_bronze_db',
    TableName='sales_transactions'
)
print(f"\n=== Table has {len(versions['TableVersions'])} versions ===")
for i, version in enumerate(versions['TableVersions'][:3]):
    print(f"Version {version['VersionId']}: {len(version['Table']['StorageDescriptor']['Columns'])} columns")
```

Run the schema evolution test:
```bash
python schema_evolution_test.py
```

### Task 8: Configure Custom Classifiers

Create a custom classifier for special file formats:

```bash
# Create custom CSV classifier with specific delimiter
awslocal glue create-classifier \
    --csv-classifier '{
        "Name": "custom-sales-csv",
        "Delimiter": ",",
        "QuoteSymbol": "\"",
        "ContainsHeader": "PRESENT",
        "Header": ["date","transaction_id","customer_id","product_id","category","quantity","unit_price","total_amount","payment_method","store_location","region","customer_email","customer_phone","shipping_address","status"],
        "DisableValueTrimming": false,
        "AllowSingleColumn": false
    }'

# Create JSON classifier for nested data
awslocal glue create-classifier \
    --json-classifier '{
        "Name": "custom-sales-json",
        "JsonPath": "$.transactions[*]"
    }'

# List classifiers
awslocal glue get-classifiers

# Update crawler to use custom classifier
awslocal glue update-crawler \
    --name sales-bronze-crawler \
    --classifiers "custom-sales-csv"
```

### Task 9: Event-Driven Crawler Execution

Configure crawler to run when new data arrives (Lambda + EventBridge pattern):

```python
# lambda_trigger_crawler.py
import boto3
import json

def lambda_handler(event, context):
    """
    Triggered by S3 ObjectCreated event via EventBridge.
    Starts the appropriate crawler based on S3 path.
    """
    glue = boto3.client('glue')

    # Extract S3 bucket and key from event
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']

    print(f"New file: s3://{bucket}/{key}")

    # Determine which crawler to run based on path
    crawler_name = None
    if 'bronze/sales' in key:
        crawler_name = 'sales-bronze-crawler'
    elif 'silver/sales' in key:
        crawler_name = 'sales-silver-crawler'

    if crawler_name:
        try:
            # Check if crawler is already running
            response = glue.get_crawler(Name=crawler_name)
            state = response['Crawler']['State']

            if state == 'READY':
                # Start crawler
                glue.start_crawler(Name=crawler_name)
                print(f"Started crawler: {crawler_name}")
                return {
                    'statusCode': 200,
                    'body': json.dumps(f'Crawler {crawler_name} started')
                }
            else:
                print(f"Crawler {crawler_name} is {state}, skipping")
                return {
                    'statusCode': 200,
                    'body': json.dumps(f'Crawler {crawler_name} already running')
                }
        except Exception as e:
            print(f"Error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Error: {str(e)}')
            }

    return {
        'statusCode': 200,
        'body': json.dumps('No crawler matched for this path')
    }
```

EventBridge rule configuration:
```json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["training-data-lake"]
    },
    "object": {
      "key": [{"prefix": "bronze/sales/"}, {"prefix": "silver/sales/"}]
    }
  }
}
```

### Task 10: Monitor and Optimize Crawler Performance

Create a monitoring script:

```python
# crawler_monitor.py
import boto3
from datetime import datetime, timedelta
import json

glue = boto3.client(
    'glue',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def analyze_crawler_performance(crawler_name):
    """Analyze crawler execution metrics"""

    # Get crawler details
    crawler = glue.get_crawler(Name=crawler_name)['Crawler']

    print(f"\n=== Crawler: {crawler_name} ===")
    print(f"State: {crawler['State']}")
    print(f"Schedule: {crawler.get('Schedule', 'On-demand only')}")

    # Last crawl statistics
    if 'LastCrawl' in crawler:
        last_crawl = crawler['LastCrawl']
        print(f"\n=== Last Crawl ===")
        print(f"Status: {last_crawl.get('Status')}")
        print(f"Start Time: {last_crawl.get('StartTime')}")
        print(f"Duration: {last_crawl.get('Duration', 0)} seconds")
        print(f"Tables Created: {last_crawl.get('TablesCreated', 0)}")
        print(f"Tables Updated: {last_crawl.get('TablesUpdated', 0)}")
        print(f"Tables Deleted: {last_crawl.get('TablesDeleted', 0)}")

    # Get crawler metrics
    metrics = glue.get_crawler_metrics(
        CrawlerNameList=[crawler_name]
    )

    if metrics['CrawlerMetricsList']:
        metric = metrics['CrawlerMetricsList'][0]
        print(f"\n=== Historical Metrics ===")
        print(f"Times Run: {metric.get('StillEstimating', 0)}")
        print(f"Median Runtime: {metric.get('MedianRuntimeSeconds', 0)} seconds")
        print(f"Tables Created: {metric.get('TablesCreated', 0)}")
        print(f"Tables Updated: {metric.get('TablesUpdated', 0)}")
        print(f"Tables Deleted: {metric.get('TablesDeleted', 0)}")

    # Cost estimation (simplified)
    dpu_hours = last_crawl.get('Duration', 0) / 3600  # Duration in hours
    dpu_count = 2  # Default DPU allocation
    cost_per_dpu_hour = 0.44  # AWS pricing
    estimated_cost = dpu_hours * dpu_count * cost_per_dpu_hour
    print(f"\n=== Cost Estimate ===")
    print(f"DPU-hours: {dpu_hours:.4f}")
    print(f"Estimated cost: ${estimated_cost:.4f}")

# Analyze all crawlers
for crawler_name in ['sales-bronze-crawler', 'sales-silver-crawler']:
    try:
        analyze_crawler_performance(crawler_name)
    except Exception as e:
        print(f"Error analyzing {crawler_name}: {e}")

# Optimization recommendations
print("\n=== Optimization Recommendations ===")
print("1. Use exclusion patterns to skip unnecessary files (_SUCCESS, .crc)")
print("2. Set SampleSize to 5-10% for large datasets")
print("3. Use CRAWL_NEW_FOLDERS_ONLY for incremental crawls")
print("4. Schedule crawlers during off-peak hours")
print("5. Use custom classifiers for faster detection")
print("6. Enable lineage tracking for data governance")
```

Run monitoring:
```bash
python crawler_monitor.py
```

## Validation

Test your crawler configuration:

```bash
# Run validation script
python validation_02.py
```

Expected results:
- ✅ 2 crawlers created (bronze, silver)
- ✅ Crawlers have proper IAM role configured
- ✅ Schema change policy is UPDATE_IN_DATABASE
- ✅ Exclusion patterns configured
- ✅ Lineage tracking enabled
- ✅ Schedules configured for daily execution
- ✅ Crawlers successfully discovered tables
- ✅ Partitions automatically added to catalog

## Key Takeaways

1. **Schema Change Policies**:
   - UPDATE_IN_DATABASE: Add new columns, modify types
   - LOG/DEPRECATE: Track deletions without breaking queries

2. **Recrawl Behavior**:
   - CRAWL_NEW_FOLDERS_ONLY: Efficient for partitioned data
   - CRAWL_EVERYTHING: Full scan, use sparingly

3. **Optimization**:
   - Use exclusion patterns to skip metadata files
   - Set sampling for large datasets (5-10%)
   - Schedule during off-peak hours
   - Use custom classifiers for special formats

4. **Cost Management**:
   - Monitor DPU-hours usage
   - Use event-driven execution instead of frequent schedules
   - Optimize crawler targets to scan only necessary paths

5. **Lineage Tracking**:
   - Enable for data governance
   - Track upstream/downstream dependencies

## Next Steps

Proceed to Exercise 03 to implement fine-grained access control with Lake Formation.

## Additional Resources

- [AWS Glue Crawler Documentation](https://docs.aws.amazon.com/glue/latest/dg/add-crawler.html)
- [Schema Change Policies](https://docs.aws.amazon.com/glue/latest/dg/crawler-schema-changes.html)
- Theory: `../theory/best-practices.md` - Section 2: Crawler Configuration
