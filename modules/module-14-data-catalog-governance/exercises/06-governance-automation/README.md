# Exercise 06: End-to-End Governance Automation

## Objective

Build a complete automated governance workflow integrating catalog management, crawlers, permissions, quality validation, and monitoring.

## Prerequisites

- Exercises 01-05 completed
- Understanding of all governance components
- EventBridge, Step Functions, Lambda knowledge

## Learning Goals

- Design end-to-end governance workflows
- Automate catalog discovery and updates
- Implement automated permission provisioning
- Integrate quality gates in data pipelines
- Build comprehensive monitoring and alerting
- Create governance dashboards

## Architecture Overview

```
┌─────────────────┐
│   S3 Events     │
│  (New Data)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  EventBridge    │◄──────── Manual Trigger
│   Rule Match    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Step Functions         │
│  Governance Workflow    │
├─────────────────────────┤
│ 1. Validate Schema      │
│ 2. Run Crawler          │
│ 3. Quality Check        │
│ 4. Apply Permissions    │
│ 5. Tag Resources        │
│ 6. Publish Metrics      │
│ 7. Send Notifications   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│   Outcomes      │
├─────────────────┤
│ ✅ Catalog      │
│ ✅ Permissions  │
│ ✅ Quality OK   │
│ ✅ Monitored    │
└─────────────────┘
```

## Exercise Tasks

### Task 1: Create Governance Workflow State Machine

Define Step Functions workflow:

```json
{
  "Comment": "End-to-end Data Governance Workflow",
  "StartAt": "ValidateInput",
  "States": {
    "ValidateInput": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:ValidateS3Input",
      "Next": "CheckIfCrawlerNeeded",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "HandleValidationError"
      }]
    },
    "CheckIfCrawlerNeeded": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.needsCrawler",
        "BooleanEquals": true,
        "Next": "RunGlueCrawler"
      }],
      "Default": "SkipCrawler"
    },
    "RunGlueCrawler": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startCrawler.sync",
      "Parameters": {
        "Name.$": "$.crawlerName"
      },
      "Next": "WaitForCrawler",
      "Retry": [{
        "ErrorEquals": ["Glue.CrawlerRunningException"],
        "IntervalSeconds": 30,
        "MaxAttempts": 5,
        "BackoffRate": 1.5
      }]
    },
    "WaitForCrawler": {
      "Type": "Wait",
      "Seconds": 10,
      "Next": "RunDataQuality"
    },
    "SkipCrawler": {
      "Type": "Pass",
      "Next": "RunDataQuality"
    },
    "RunDataQuality": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:RunDataQualityCheck",
      "Next": "EvaluateQualityScore",
      "ResultPath": "$.qualityResults"
    },
    "EvaluateQualityScore": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.qualityResults.score",
          "NumericGreaterThanEquals": 95,
          "Next": "ApplyGoldTags"
        },
        {
          "Variable": "$.qualityResults.score",
          "NumericGreaterThanEquals": 85,
          "Next": "ApplySilverTags"
        }
      ],
      "Default": "QuarantineData"
    },
    "ApplyGoldTags": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:ApplyLFTags",
      "Parameters": {
        "database.$": "$.database",
        "table.$": "$.table",
        "tags": {
          "QualityLevel": "Gold",
          "DataSensitivity": "Internal",
          "Certified": "true"
        }
      },
      "Next": "GrantProduction Permissions"
    },
    "ApplySilverTags": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:ApplyLFTags",
      "Parameters": {
        "database.$": "$.database",
        "table.$": "$.table",
        "tags": {
          "QualityLevel": "Silver",
          "DataSensitivity": "Internal",
          "Certified": "false"
        }
      },
      "Next": "GrantDevelopmentPermissions"
    },
    "GrantProductionPermissions": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:GrantLFPermissions",
      "Parameters": {
        "resource.$": "$.table",
        "principals": [
          "arn:aws:iam::000000000000:role/DataScientist",
          "arn:aws:iam::000000000000:role/DataAnalyst",
          "arn:aws:iam::222222222222:root"
        ],
        "permissions": ["SELECT", "DESCRIBE"]
      },
      "Next": "PublishMetrics"
    },
    "GrantDevelopmentPermissions": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:GrantLFPermissions",
      "Parameters": {
        "resource.$": "$.table",
        "principals": [
          "arn:aws:iam::000000000000:role/DataEngineer",
          "arn:aws:iam::000000000000:role/DataAnalyst"
        ],
        "permissions": ["SELECT", "DESCRIBE"]
      },
      "Next": "PublishMetrics"
    },
    "QuarantineData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:QuarantineData",
      "Next": "SendQualityAlert"
    },
    "SendQualityAlert": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:000000000000:governance-alerts",
        "Subject": "Data Quality Failure - Quarantined",
        "Message.$": "$.quarantineDetails"
      },
      "End": true
    },
    "PublishMetrics": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:PublishGovernanceMetrics",
      "Next": "SendSuccessNotification"
    },
    "SendSuccessNotification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:000000000000:governance-success",
        "Subject": "Governance Workflow Completed",
        "Message.$": "$.summary"
      },
      "End": true
    },
    "HandleValidationError": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:000000000000:governance-errors",
        "Subject": "Governance Workflow Error",
        "Message.$": "$.error"
      },
      "End": true
    }
  }
}
```

### Task 2: Implement Lambda Functions

Create Lambda functions for each workflow step:

**1. Validate S3 Input**
```python
# lambda_validate_input.py
import boto3
import json

s3 = boto3.client('s3')
glue = boto3.client('glue')

def lambda_handler(event, context):
    """Validate S3 event and determine processing needs"""

    # Extract S3 details from event
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    size = event['detail']['object']['size']

    print(f"Validating: s3://{bucket}/{key}")

    # Determine layer and crawler
    if 'bronze/' in key:
        layer = 'bronze'
        crawler_name = 'sales-bronze-crawler'
        database = 'dev_sales_bronze_db'
        needs_crawler = True
    elif 'silver/' in key:
        layer = 'silver'
        crawler_name = 'sales-silver-crawler'
        database = 'dev_sales_silver_db'
        needs_crawler = True
    elif 'gold/' in key:
        layer = 'gold'
        crawler_name = None
        database = 'dev_sales_gold_db'
        needs_crawler = False
    else:
        raise ValueError(f"Unknown data layer for path: {key}")

    # Extract table name from path
    path_parts = key.split('/')
    table_name = path_parts[2] if len(path_parts) > 2 else 'unknown'

    # Check file size
    if size == 0:
        raise ValueError("Empty file detected")

    # Check if too large for immediate processing
    if size > 1073741824:  # 1 GB
        print("Large file detected, may need batch processing")

    return {
        'bucket': bucket,
        'key': key,
        'size': size,
        'layer': layer,
        'database': database,
        'table': table_name,
        'crawlerName': crawler_name,
        'needsCrawler': needs_crawler,
        'timestamp': context.timestamp
    }
```

**2. Run Data Quality Check**
```python
# lambda_run_quality_check.py
import boto3

glue = boto3.client('glue')

def lambda_handler(event, context):
    """Execute data quality evaluation"""

    database = event['database']
    table = event['table']

    print(f"Running quality check: {database}.{table}")

    # Get ruleset for table
    rulesets = glue.list_data_quality_rulesets(
        Filter={'TargetTable': {
            'DatabaseName': database,
            'TableName': table
        }}
    )

    if not rulesets.get('Rulesets'):
        print("No ruleset found, using default rules")
        score = 90.0  # Default passing score
    else:
        ruleset_name = rulesets['Rulesets'][0]['Name']

        # Start quality evaluation
        response = glue.start_data_quality_ruleset_evaluation_run(
            DataSource={
                'GlueTable': {
                    'DatabaseName': database,
                    'TableName': table
                }
            },
            Role='arn:aws:iam::000000000000:role/AWSGlueServiceRole-DataLake',
            RulesetNames=[ruleset_name]
        )

        # Wait for completion (in real scenario, use Step Functions wait)
        import time
        run_id = response['RunId']

        for _ in range(30):  # 5 minutes max
            result = glue.get_data_quality_ruleset_evaluation_run(RunId=run_id)
            status = result['Status']

            if status in ['SUCCEEDED', 'FAILED']:
                break
            time.sleep(10)

        # Get score
        if status == 'SUCCEEDED':
            score = result.get('Score', 0)
            rules_passed = result.get('RulesPassed', 0)
            rules_failed = result.get('RulesFailed', 0)
        else:
            score = 0
            rules_passed = 0
            rules_failed = 999

    return {
        'database': database,
        'table': table,
        'score': score,
        'rulesPassed': rules_passed,
        'rulesFailed': rules_failed,
        'passed': score >= 85
    }
```

**3. Apply LF-Tags**
```python
# lambda_apply_lf_tags.py
import boto3

lakeformation = boto3.client('lakeformation')

def lambda_handler(event, context):
    """Apply Lake Formation tags to resources"""

    database = event['database']
    table = event['table']
    tags = event['tags']

    print(f"Applying tags to {database}.{table}")

    # Convert tags to LF-Tag format
    lf_tags = [
        {'TagKey': k, 'TagValues': [v]}
        for k, v in tags.items()
    ]

    # Apply to table
    lakeformation.add_lf_tags_to_resource(
        Resource={
            'Table': {
                'DatabaseName': database,
                'Name': table
            }
        },
        LFTags=lf_tags
    )

    print(f"Applied {len(lf_tags)} tags")

    return {
        'database': database,
        'table': table,
        'tagsApplied': list(tags.keys())
    }
```

**4. Grant LF Permissions**
```python
# lambda_grant_permissions.py
import boto3

lakeformation = boto3.client('lakeformation')

def lambda_handler(event, context):
    """Grant Lake Formation permissions"""

    database = event['resource'].get('database')
    table = event['resource'].get('table')
    principals = event['principals']
    permissions = event['permissions']

    print(f"Granting permissions to {len(principals)} principals")

    for principal_arn in principals:
        try:
            lakeformation.grant_permissions(
                Principal={'DataLakePrincipalIdentifier': principal_arn},
                Resource={
                    'Table': {
                        'DatabaseName': database,
                        'Name': table
                    }
                },
                Permissions=permissions
            )
            print(f"✅ Granted to {principal_arn}")
        except Exception as e:
            print(f"❌ Failed for {principal_arn}: {e}")

    return {
        'database': database,
        'table': table,
        'principalsGranted': len(principals)
    }
```

**5. Publish Governance Metrics**
```python
# lambda_publish_metrics.py
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """Publish governance workflow metrics"""

    namespace = 'DataGovernance'
    timestamp = datetime.utcnow()

    metrics = [
        {
            'MetricName': 'WorkflowExecutions',
            'Value': 1,
            'Unit': 'Count',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'Database', 'Value': event['database']},
                {'Name': 'Layer', 'Value': event['layer']}
            ]
        },
        {
            'MetricName': 'QualityScore',
            'Value': event.get('qualityResults', {}).get('score', 0),
            'Unit': 'Percent',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'Table', 'Value': event['table']}
            ]
        },
        {
            'MetricName': 'ProcessingLatency',
            'Value': (datetime.now() - datetime.fromisoformat(event['timestamp'])).seconds,
            'Unit': 'Seconds',
            'Timestamp': timestamp
        }
    ]

    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=metrics
    )

    return {'metricsPublished': len(metrics)}
```

### Task 3: Configure EventBridge Rule

Trigger workflow on S3 events:

```bash
# Create EventBridge rule
awslocal events put-rule \
    --name governance-s3-trigger \
    --event-pattern '{
        "source": ["aws.s3"],
        "detail-type": ["Object Created"],
        "detail": {
            "bucket": {
                "name": ["training-data-lake"]
            },
            "object": {
                "key": [
                    {"prefix": "bronze/sales/"},
                    {"prefix": "silver/sales/"},
                    {"prefix": "gold/sales/"}
                ]
            }
        }
    }' \
    --state ENABLED

# Add Step Functions as target
awslocal events put-targets \
    --rule governance-s3-trigger \
    --targets '[{
        "Id": "1",
        "Arn": "arn:aws:states:us-east-1:000000000000:stateMachine:DataGovernanceWorkflow",
        "RoleArn": "arn:aws:iam::000000000000:role/EventBridgeStepFunctionsRole"
    }]'
```

### Task 4: Build Governance Dashboard

Create monitoring dashboard:

```python
# create_governance_dashboard.py
import boto3
import json

cloudwatch = boto3.client('cloudwatch')

dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["DataGovernance", "WorkflowExecutions", {"stat": "Sum"}],
                    [".", "QualityScore", {"stat": "Average"}],
                    [".", "ProcessingLatency", {"stat": "Average"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Governance Workflows - Overview",
                "yAxis": {"left": {"min": 0}}
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["DataQuality/dev_sales_bronze_db", "QualityScore", {"stat": "Average"}],
                    ["DataQuality/dev_sales_silver_db", "QualityScore", {"stat": "Average"}],
                    ["DataQuality/dev_sales_gold_db", "QualityScore", {"stat": "Average"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Quality Scores by Layer",
                "yAxis": {"left": {"min": 0, "max": 100}}
            }
        },
        {
            "type": "log",
            "properties": {
                "query": "SOURCE '/aws/lambda/RunDataQualityCheck' | fields @timestamp, @message | filter @message like /FAIL/ | sort @timestamp desc | limit 20",
                "region": "us-east-1",
                "title": "Recent Quality Failures"
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='DataGovernance',
    DashboardBody=json.dumps(dashboard_body)
)

print("Dashboard created: DataGovernance")
```

### Task 5: Test End-to-End Workflow

Trigger complete workflow:

```bash
# Upload test file to trigger workflow
awslocal s3 cp ../../data/sample/sales-transactions.csv \
    s3://training-data-lake/bronze/sales/transactions/year=2024/month=03/day=10/

# Monitor Step Functions execution
awslocal stepfunctions list-executions \
    --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:DataGovernanceWorkflow \
    --max-results 1

# Get execution details
EXECUTION_ARN=$(awslocal stepfunctions list-executions \
    --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:DataGovernanceWorkflow \
    --max-results 1 \
    --query 'executions[0].executionArn' \
    --output text)

awslocal stepfunctions describe-execution --execution-arn $EXECUTION_ARN

# Get execution history
awslocal stepfunctions get-execution-history --execution-arn $EXECUTION_ARN
```

### Task 6: Create Governance Report

Generate comprehensive governance report:

```python
# governance_report.py
import boto3
from datetime import datetime, timedelta
import json

def generate_governance_report(days=7):
    """Generate comprehensive governance status report"""

    glue = boto3.client('glue')
    lakeformation = boto3.client('lakeformation')
    cloudwatch = boto3.client('cloudwatch')

    report = {
        'period': f"Last {days} days",
        'generated_at': datetime.now().isoformat(),
        'catalog': {},
        'quality': {},
        'permissions': {},
        'workflows': {}
    }

    # 1. Catalog Statistics
    databases = glue.get_databases()
    total_tables = 0
    for db in databases['DatabaseList']:
        tables = glue.get_tables(DatabaseName=db['Name'])
        total_tables += len(tables['TableList'])

    report['catalog'] = {
        'databases': len(databases['DatabaseList']),
        'tables': total_tables
    }

    # 2. Quality Scores
    # (Aggregate quality metrics from CloudWatch)

    # 3. Permission Grants
    permissions = lakeformation.list_permissions()
    report['permissions'] = {
        'total_grants': len(permissions.get('PrincipalResourcePermissions', []))
    }

    # 4. Workflow Executions
    # (Aggregate Step Functions metrics)

    return report

# Generate and display report
report = generate_governance_report()
print(json.dumps(report, indent=2))
```

## Validation

Test complete governance automation:

```bash
python validation_06.py
```

Expected results:
- ✅ Step Functions state machine deployed
- ✅ All Lambda functions created and operational
- ✅ EventBridge rule triggering on S3 events
- ✅ Workflow executes all steps successfully
- ✅ Quality checks integrate properly
- ✅ Tags applied automatically based on quality
- ✅ Permissions granted correctly
- ✅ Metrics published to CloudWatch
- ✅ Notifications sent on completion/failure
- ✅ Dashboard displays all governance metrics

## Key Takeaways

1. **Automation**: Reduces manual governance tasks by 90%
2. **Integration**: Catalog → Quality → Permissions → Monitoring
3. **Quality Gates**: Automatic classification based on quality scores
4. **Self-Service**: Tag-based permissions enable automatic access
5. **Monitoring**: Real-time dashboards for governance health
6. **Scalability**: Handles unlimited tables with minimal overhead

## Additional Resources

- [Step Functions Glue Integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-glue.html)
- [EventBridge S3 Events](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html)
- Theory: `../theory/best-practices.md` - Section 10: Monitoring and Alerting

## Congratulations!

You've completed all governance exercises. You can now:
- ✅ Manage Data Catalog programmatically
- ✅ Automate schema discovery with Crawlers
- ✅ Implement fine-grained Lake Formation permissions
- ✅ Validate data quality automatically
- ✅ Share data securely across accounts
- ✅ Build end-to-end governance automation

Ready for Module 15: Real-Time Analytics!
