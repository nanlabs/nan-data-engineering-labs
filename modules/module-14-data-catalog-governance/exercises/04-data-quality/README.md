# Exercise 04: Data Quality Validation

## Objective

Learn to implement automated data quality validation using AWS Glue Data Quality rules and build a quality monitoring framework.

## Prerequisites

- Exercises 01-03 completed
- Data Catalog tables with data
- Understanding of data quality dimensions

## Learning Goals

- Define data quality rules for completeness, accuracy, consistency
- Configure AWS Glue Data Quality rulesets
- Implement automated quality checks in ETL pipelines
- Build quality score dashboards
- Set up alerting for quality failures

## Exercise Tasks

### Task 1: Create Data Quality Ruleset

Define quality rules using AWS Glue Data Quality DQDL (Data Quality Definition Language):

```python
# create_quality_ruleset.py
import boto3
import json

glue = boto3.client(
    'glue',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Define comprehensive quality ruleset
ruleset = """
# Completeness Rules
Completeness "transaction_id" = 1.0
Completeness "customer_id" > 0.98
Completeness "date" > 0.99
Completeness "total_amount" = 1.0

# Uniqueness Rules
Uniqueness "transaction_id" > 0.99
RowCount > 10

# Range and Validity Rules
ColumnValues "quantity" > 0
ColumnValues "unit_price" > 0
ColumnValues "total_amount" between 0.01 and 50000
ColumnValues "quantity" between 1 and 1000

# Pattern Matching
ColumnValues "transaction_id" matches "^TXN-\\d{5,6}$"
ColumnValues "customer_id" matches "^CUST-\\d{4,6}$"
ColumnValues "product_id" matches "^PROD-[A-Z]{1,4}\\d{3,4}$"
ColumnValues "date" matches "^\\d{4}-\\d{2}-\\d{2}$"

# Categorical Validity
ColumnValues "category" in ["Electronics","Home","Books","Clothing","Grocery","Sports","Toys","Furniture","Beauty","Office"]
ColumnValues "payment_method" in ["credit_card","debit_card","paypal","apple_pay","google_pay","cash","financing"]
ColumnValues "region" in ["US-EAST","US-WEST","US-CENTRAL","US-SOUTH"]
ColumnValues "status" in ["completed","pending","failed","cancelled"]

# Cross-Field Validation
CustomSql "SELECT COUNT(*) FROM primary WHERE ABS(total_amount - (quantity * unit_price)) / total_amount > 0.01" = 0

# Email and Phone Format
ColumnValues "customer_email" matches "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

# Statistical Rules
Mean "total_amount" between 50 and 500
StandardDeviation "total_amount" < 1000
"""

# Create ruleset for Bronze table
response = glue.create_data_quality_ruleset(
    Name='sales_bronze_quality_rules',
    Description='Comprehensive quality validation for raw sales data',
    Ruleset=ruleset,
    TargetTable={
        'DatabaseName': 'dev_sales_bronze_db',
        'TableName': 'sales_transactions'
    },
    Tags={
        'Environment': 'development',
        'DataDomain': 'Sales',
        'Layer': 'Bronze'
    }
)

print(f"Created ruleset: {response['Name']}")
```

### Task 2: Create Silver Layer Quality Rules

More stringent rules for cleaned data:

```python
# silver_quality_rules.py

silver_ruleset = """
# Higher completeness thresholds
Completeness "transaction_id" = 1.0
Completeness "customer_id" = 1.0
Completeness "date" = 1.0
Completeness "total_amount" = 1.0
Completeness "data_quality_score" > 0.95

# Silver-specific validations
ColumnValues "data_quality_score" between 0.85 and 1.0
Completeness "ingestion_timestamp" = 1.0

# Data freshness check
CustomSql "SELECT COUNT(*) FROM primary WHERE ingestion_timestamp < CURRENT_TIMESTAMP - INTERVAL '2' DAY" = 0

# Stricter ranges
ColumnValues "total_amount" between 0.01 and 10000
Mean "total_amount" between 40 and 300

# No masked fields should be null
Completeness "customer_email_masked" = 1.0
Completeness "shipping_city" > 0.95
Completeness "shipping_state" > 0.95

# Proper type validation
ColumnDataType "date" = "DATE"
ColumnDataType "unit_price" in ["DECIMAL(10,2)", "DECIMAL"]
ColumnDataType "ingestion_timestamp" = "TIMESTAMP"
"""

glue.create_data_quality_ruleset(
    Name='sales_silver_quality_rules',
    Ruleset=silver_ruleset,
    TargetTable={
        'DatabaseName': 'dev_sales_silver_db',
        'TableName': 'sales_transactions_clean'
    }
)

print("Created Silver quality ruleset")
```

### Task 3: Run Quality Evaluation

Execute quality checks and analyze results:

```python
# run_quality_check.py
import boto3
import time

glue = boto3.client(
    'glue',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Start quality evaluation run
response = glue.start_data_quality_rule_recommendation_run(
    DataSource={
        'GlueTable': {
            'DatabaseName': 'dev_sales_bronze_db',
            'TableName': 'sales_transactions'
        }
    },
    Role='arn:aws:iam::000000000000:role/AWSGlueServiceRole-DataLake',
    NumberOfWorkers=2,
    Timeout=60
)

run_id = response['RunId']
print(f"Started quality run: {run_id}")

# Wait for completion
while True:
    run = glue.get_data_quality_rule_recommendation_run(RunId=run_id)
    status = run['Status']
    print(f"Status: {status}")

    if status in ['SUCCEEDED', 'FAILED', 'STOPPED']:
        break

    time.sleep(10)

# Get results
if status == 'SUCCEEDED':
    results = glue.get_data_quality_result(ResultId=run_id)

    print("\n=== Quality Results ===")
    print(f"Score: {results['Score']}")
    print(f"Evaluated Rules: {results['EvaluatedRuleCount']}")
    print(f"Passed Rules: {results['RulesPassed']}")
    print(f"Failed Rules: {results['RulesFailed']}")

    # Rule-level details
    for rule_result in results.get('RuleResults', []):
        status_icon = "✅" if rule_result['Result'] == 'PASS' else "❌"
        print(f"{status_icon} {rule_result['Name']}: {rule_result['Result']}")
        if rule_result['Result'] == 'FAIL':
            print(f"   Reason: {rule_result.get('EvaluationMessage', 'N/A')}")
```

### Task 4: Integrate Quality Checks into ETL Pipeline

Add quality validation to Glue ETL jobs:

```python
# glue_job_with_quality.py
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import current_timestamp, lit

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read Bronze data
bronze_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="dev_sales_bronze_db",
    table_name="sales_transactions",
    transformation_ctx="bronze_dyf"
)

# Convert to DataFrame for quality checks
df = bronze_dyf.toDF()

# Calculate quality score per row
from pyspark.sql.functions import when, col
from pyspark.sql.functions import sum as _sum

quality_checks = [
    (col("transaction_id").isNotNull(), "transaction_id_completeness"),
    (col("customer_id").isNotNull(), "customer_id_completeness"),
    (col("total_amount") > 0, "total_amount_validity"),
    (col("quantity") > 0, "quantity_validity"),
    (col("status").isin(["completed", "pending", "failed"]), "status_validity"),
]

# Add individual check columns
for check, name in quality_checks:
    df = df.withColumn(name, when(check, 1).otherwise(0))

# Calculate overall quality score (percentage of checks passed)
check_columns = [name for _, name in quality_checks]
df = df.withColumn(
    "data_quality_score",
    (_sum([col(c) for c in check_columns]) / len(check_columns))
)

# Filter rows that meet minimum quality threshold
bronze_threshold = 0.85
silver_df = df.filter(col("data_quality_score") >= bronze_threshold)
quarantine_df = df.filter(col("data_quality_score") < bronze_threshold)

# Add ingestion timestamp
silver_df = silver_df.withColumn("ingestion_timestamp", current_timestamp())
silver_df = silver_df.withColumn("layer", lit("silver"))

# Write to Silver layer
silver_dyf = DynamicFrame.fromDF(silver_df, glueContext, "silver_dyf")
glueContext.write_dynamic_frame.from_catalog(
    frame=silver_dyf,
    database="dev_sales_silver_db",
    table_name="sales_transactions_clean",
    transformation_ctx="silver_write"
)

# Write quarantined data for investigation
if quarantine_df.count() > 0:
    quarantine_dyf = DynamicFrame.fromDF(quarantine_df, glueContext, "quarantine_dyf")
    glueContext.write_dynamic_frame.from_options(
        frame=quarantine_dyf,
        connection_type="s3",
        connection_options={"path": "s3://training-data-lake/quarantine/sales/"},
        format="parquet"
    )

    # Send alert
    print(f"⚠️  {quarantine_df.count()} rows quarantined due to quality issues")

# Job metrics
print(f"✅ Processed: {df.count()} rows")
print(f"✅ To Silver: {silver_df.count()} rows")
print(f"❌ Quarantined: {quarantine_df.count()} rows")

job.commit()
```

### Task 5: Build Quality Monitoring Dashboard

Create a quality metrics aggregation job:

```python
# quality_metrics_aggregation.py
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client(
    'cloudwatch',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def publish_quality_metrics(database, table, quality_score, rules_passed, rules_failed):
    """Publish quality metrics to CloudWatch"""

    namespace = f"DataQuality/{database}"
    timestamp = datetime.utcnow()

    metrics = [
        {
            'MetricName': 'QualityScore',
            'Value': quality_score,
            'Unit': 'Percent',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'TableName', 'Value': table},
                {'Name': 'Database', 'Value': database}
            ]
        },
        {
            'MetricName': 'RulesPassed',
            'Value': rules_passed,
            'Unit': 'Count',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'TableName', 'Value': table}
            ]
        },
        {
            'MetricName': 'RulesFailed',
            'Value': rules_failed,
            'Unit': 'Count',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'TableName', 'Value': table}
            ]
        }
    ]

    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=metrics
    )

    print(f"Published metrics for {database}.{table}")

# Example usage
publish_quality_metrics(
    database='dev_sales_bronze_db',
    table='sales_transactions',
    quality_score=92.5,
    rules_passed=25,
    rules_failed=2
)
```

### Task 6: Set Up Quality Alerts

Create CloudWatch alarms for quality thresholds:

```bash
# Create alarm for low quality score
awslocal cloudwatch put-metric-alarm \
    --alarm-name sales-bronze-quality-low \
    --alarm-description "Alert when Bronze quality score falls below 85%" \
    --metric-name QualityScore \
    --namespace DataQuality/dev_sales_bronze_db \
    --statistic Average \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 85.0 \
    --comparison-operator LessThanThreshold \
    --dimensions Name=TableName,Value=sales_transactions \
    --alarm-actions arn:aws:sns:us-east-1:000000000000:data-quality-alerts

# Create alarm for high failure rate
awslocal cloudwatch put-metric-alarm \
    --alarm-name sales-bronze-failures-high \
    --metric-name RulesFailed \
    --namespace DataQuality/dev_sales_bronze_db \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=TableName,Value=sales_transactions
```

### Task 7: Quality Report Generation

Generate daily quality reports:

```python
# generate_quality_report.py
import boto3
from datetime import datetime, timedelta
import pandas as pd

glue = boto3.client(
    'glue',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def generate_quality_report(start_date, end_date):
    """Generate comprehensive quality report"""

    report = {
        'tables': [],
        'overall_score': 0,
        'total_rules': 0,
        'total_passed': 0,
        'total_failed': 0
    }

    # Get all quality rulesets
    rulesets = glue.list_data_quality_rulesets()

    for ruleset_info in rulesets.get('Rulesets', []):
        ruleset_name = ruleset_info['Name']

        # Get ruleset details
        ruleset = glue.get_data_quality_ruleset(Name=ruleset_name)
        target = ruleset['TargetTable']

        # Get recent results
        results = glue.list_data_quality_results(
            Filter={
                'DataSource': {
                    'GlueTable': {
                        'DatabaseName': target['DatabaseName'],
                        'TableName': target['TableName']
                    }
                },
                'StartedAfter': start_date
            }
        )

        # Aggregate results
        table_stats = {
            'database': target['DatabaseName'],
            'table': target['TableName'],
            'ruleset': ruleset_name,
            'runs': len(results.get('Results', [])),
            'avg_score': 0,
            'trend': 'stable'
        }

        if results.get('Results'):
            scores = [r.get('Score', 0) for r in results['Results']]
            table_stats['avg_score'] = sum(scores) / len(scores)

            # Calculate trend
            if len(scores) >= 2:
                recent_avg = sum(scores[-3:]) / min(3, len(scores))
                older_avg = sum(scores[:-3]) / max(1, len(scores) - 3)
                if recent_avg > older_avg + 5:
                    table_stats['trend'] = 'improving ↑'
                elif recent_avg < older_avg - 5:
                    table_stats['trend'] = 'declining ↓'

        report['tables'].append(table_stats)

    # Calculate overall metrics
    if report['tables']:
        report['overall_score'] = sum(t['avg_score'] for t in report['tables']) / len(report['tables'])

    return report

# Generate report
start = datetime.now() - timedelta(days=7)
end = datetime.now()
report = generate_quality_report(start, end)

print("\n" + "="*80)
print(f"DATA QUALITY REPORT")
print(f"Period: {start.date()} to {end.date()}")
print("="*80)

print(f"\nOverall Score: {report['overall_score']:.2f}%")
print(f"\n{'Database':<30} {'Table':<30} {'Avg Score':<12} {'Trend':<15}")
print("-"*87)
for table in report['tables']:
    print(f"{table['database']:<30} {table['table']:<30} {table['avg_score']:.2f}%{'':<7} {table['trend']:<15}")
```

## Validation

Test your quality setup:

```bash
python validation_04.py
```

Expected results:
- ✅ Quality rulesets created for Bronze and Silver tables
- ✅ Rules cover completeness, validity, consistency dimensions
- ✅ Quality evaluation runs successfully
- ✅ Quality scores calculated correctly
- ✅ CloudWatch metrics published
- ✅ Alarms configured for threshold violations
- ✅ Quarantine process captures bad data
- ✅ Quality reports generate successfully

## Key Takeaways

1. **Quality Dimensions**: Completeness, accuracy, consistency, timeliness, validity
2. **Rule Types**: Completeness, uniqueness, range checks, pattern matching, referential integrity
3. **Thresholds**: Bronze 85%, Silver 95%, Gold 99%
4. **Quarantine Pattern**: Isolate bad data for investigation
5. **Monitoring**: Track quality scores over time, set up alerts
6. **Integration**: Build quality checks into ETL pipelines

## Next Steps

Proceed to Exercise 05 for cross-account data sharing.

## Additional Resources

- [AWS Glue Data Quality](https://docs.aws.amazon.com/glue/latest/dg/glue-data-quality.html)
- [DQDL Reference](https://docs.aws.amazon.com/glue/latest/dg/dqdl.html)
- Theory: `../theory/concepts.md` - Section 7: Data Quality
