# Exercise 03: ECS Data Pipeline con Step Functions

## 📋 Información General

- **Level**: Intermedio-Avanzado
- **Duration estimada**: 3-4 hours
- **Prerequisites**:
  - Exercises 01 y 02 completeds
  - Conocimiento de Step Functions

## 🎯 Objectives de Aprendizaje

1. Orquestar múltiples ECS tasks con Step Functions
2. Implementar ETL pipeline complejo
3. Error handling y retry logic
4. Parallel processing con ECS
5. Integration con S3 y Glue

---

## 📚 Context

Construirás un **ETL Pipeline completo** que:

1. **Extract**: Descarga datos de múltiples fuentes (S3, APIs)
2. **Transform**: Procesa datos en paralelo (3 transformations)
3. **Validate**: Validate calidad de datos
4. **Load**: Carga a Redshift/RDS
5. **Notify**: Envía reporte por SNS

**Arquitectura**:

```text
┌──────────────────────────────────────────────────────────────┐
│             Step Functions ETL Pipeline                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐                                            │
│  │   Extract    │  (ECS Task 1)                              │
│  │  S3 + API    │                                            │
│  └──────┬───────┘                                            │
│         │                                                    │
│         ▼                                                    │
│  ┌────────────────────────────────────────┐                 │
│  │        Parallel Transform              │                 │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  │Transform │  │Transform │  │Transform │  (ECS Tasks)  │
│  │  │   Sales  │  │Customers │  │ Products │              │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│  └───────┼─────────────┼─────────────┼────────┘            │
│          └─────────────┴─────────────┘                      │
│                       │                                      │
│                       ▼                                      │
│            ┌─────────────────┐                              │
│            │    Validate     │  (ECS Task 2)                │
│            │  Data Quality   │                               │
│            └────────┬────────┘                              │
│                     │                                        │
│              ┌──────┴──────┐                                │
│              │ Valid?      │                                │
│              └──┬────────┬──┘                               │
│           Yes   │        │ No                               │
│                 ▼        ▼                                   │
│         ┌───────────┐  ┌──────────┐                        │
│         │   Load    │  │  Quarantine                │        │
│         │ Redshift  │  │  + Alert  │  (ECS Tasks)           │
│         └─────┬─────┘  └──────────┘                        │
│               │                                             │
│               ▼                                             │
│         ┌──────────┐                                        │
│         │  Notify  │  (SNS)                                 │
│         │  Report  │                                         │
│         └──────────┘                                        │
└──────────────────────────────────────────────────────────────┘
```text

---

## 🏗️ Parte 1: Containers ETL

### Step 1.1: Extract Container

Create `containers/extract/extract.py`:

```python
"""
Extract data from S3 and external APIs
"""
import boto3
import json
import os
from datetime import datetime, timedelta

s3 = boto3.client('s3')

def extract_from_s3():
    """Extract CSV files from S3"""
    bucket = os.environ['DATA_BUCKET']
    prefix = 'raw/sales/'

    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    files = [obj['Key'] for obj in response.get('Contents', [])]

    return {
        's3_files': files,
        'total_files': len(files)
    }

def extract_from_api():
    """Extract data from external API (simulated)"""
    # In real scenario: requests.get(API_URL)
    return {
        'api_records': 1500,
        'api_endpoint': 'https://api.example.com/v1/data'
    }

def main():
    print("Starting extraction...")

    # Extract from S3
    s3_data = extract_from_s3()
    print(f"Extracted {s3_data['total_files']} files from S3")

    # Extract from API
    api_data = extract_from_api()
    print(f"Extracted {api_data['api_records']} records from API")

    # Write metadata for next step
    output = {
        'extraction_timestamp': datetime.utcnow().isoformat(),
        's3_files': s3_data['s3_files'],
        'api_records': api_data['api_records'],
        'status': 'success'
    }

    # Write to S3 for Step Functions
    s3.put_object(
        Bucket=os.environ['DATA_BUCKET'],
        Key='metadata/extract_output.json',
        Body=json.dumps(output)
    )

    print("Extraction completed successfully")
    return output

if __name__ == '__main__':
    result = main()
    print(json.dumps(result))
```text

Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY extract.py .

CMD ["python", "extract.py"]
```

### Step 1.2: Transform Containers (3 paralelas)

Create `containers/transform/transform_sales.py`:

```python
"""
Transform sales data
"""
import boto3
import pandas as pd
import os
from io import StringIO

s3 = boto3.client('s3')

def main():
    bucket = os.environ['DATA_BUCKET']

    # Read raw sales data
    obj = s3.get_object(Bucket=bucket, Key='raw/sales.csv')
    df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

    print(f"Transforming {len(df)} sales records")

    # Transformations
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['revenue'] = df['quantity'] * df['price']
    df['year'] = df['order_date'].dt.year
    df['month'] = df['order_date'].dt.month

    # Aggregate
    monthly_sales = df.groupby(['year', 'month']).agg({
        'revenue': 'sum',
        'order_id': 'count'
    }).reset_index()

    monthly_sales.columns = ['year', 'month', 'total_revenue', 'total_orders']

    # Write to S3
    csv_buffer = StringIO()
    monthly_sales.to_csv(csv_buffer, index=False)

    s3.put_object(
        Bucket=bucket,
        Key='processed/sales/monthly_sales.csv',
        Body=csv_buffer.getvalue()
    )

    print(f"Transformed and wrote {len(monthly_sales)} monthly summaries")

    return {
        'status': 'success',
        'records_processed': len(df),
        'output_file': 'processed/sales/monthly_sales.csv'
    }

if __name__ == '__main__':
    import json
    result = main()
    print(json.dumps(result))
```text

Similar files: `transform_customers.py`, `transform_products.py`

### Step 1.3: Validate Container

Create `containers/validate/validate.py`:

```python
"""
Data quality validation
"""
import boto3
import pandas as pd
from io import StringIO
import json

s3 = boto3.client('s3')

def validate_sales(bucket, key):
    """Validate sales data"""
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

    issues = []

    # Check for nulls
    null_counts = df.isnull().sum()
    if null_counts.any():
        issues.append({
            'type': 'null_values',
            'columns': null_counts[null_counts > 0].to_dict()
        })

    # Check for negative revenue
    if (df['total_revenue'] < 0).any():
        issues.append({
            'type': 'negative_revenue',
            'count': (df['total_revenue'] < 0).sum()
        })

    # Check date range
    if df['year'].min() < 2020 or df['year'].max() > 2025:
        issues.append({
            'type': 'invalid_date_range',
            'min_year': int(df['year'].min()),
            'max_year': int(df['year'].max())
        })

    return {
        'file': key,
        'valid': len(issues) == 0,
        'row_count': len(df),
        'issues': issues
    }

def main():
    bucket = os.environ['DATA_BUCKET']

    # Validate all processed files
    files_to_validate = [
        'processed/sales/monthly_sales.csv',
        'processed/customers/customer_summary.csv',
        'processed/products/product_metrics.csv'
    ]

    results = []
    for file in files_to_validate:
        print(f"Validating {file}")
        validation_result = validate_sales(bucket, file)
        results.append(validation_result)

    # Overall validation
    all_valid = all(r['valid'] for r in results)

    output = {
        'overall_valid': all_valid,
        'files_validated': len(results),
        'validation_details': results,
        'timestamp': datetime.utcnow().isoformat()
    }

    # Write validation report
    s3.put_object(
        Bucket=bucket,
        Key='metadata/validation_report.json',
        Body=json.dumps(output, indent=2)
    )

    print(f"Validation complete. Overall valid: {all_valid}")

    return output

if __name__ == '__main__':
    from datetime import datetime
    result = main()
    print(json.dumps(result))
```text

### Step 1.4: Load Container

Create `containers/load/load.py`:

```python
"""
Load validated data to Redshift
"""
import boto3
import psycopg2
import pandas as pd
from io import StringIO
import os
import json

s3 = boto3.client('s3')

def get_db_connection():
    """Connect to Redshift"""
    return psycopg2.connect(
        host=os.environ['REDSHIFT_HOST'],
        port=os.environ['REDSHIFT_PORT'],
        database=os.environ['REDSHIFT_DB'],
        user=os.environ['REDSHIFT_USER'],
        password=os.environ['REDSHIFT_PASSWORD']
    )

def load_to_redshift(bucket, file_key, table_name):
    """Load CSV from S3 to Redshift using COPY command"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # COPY command (más eficiente que INSERT row-by-row)
    copy_query = f"""
        COPY {table_name}
        FROM 's3://{bucket}/{file_key}'
        IAM_ROLE '{os.environ['REDSHIFT_IAM_ROLE']}'
        FORMAT AS CSV
        IGNOREHEADER 1
        REGION 'us-east-1'
    """

    cursor.execute(copy_query)
    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count

def main():
    bucket = os.environ['DATA_BUCKET']

    loads = [
        ('processed/sales/monthly_sales.csv', 'fact_sales'),
        ('processed/customers/customer_summary.csv', 'dim_customers'),
        ('processed/products/product_metrics.csv', 'dim_products')
    ]

    results = []
    for file_key, table_name in loads:
        print(f"Loading {file_key} to {table_name}")
        row_count = load_to_redshift(bucket, file_key, table_name)
        results.append({
            'file': file_key,
            'table': table_name,
            'rows_loaded': row_count
        })
        print(f"Loaded {row_count} rows to {table_name}")

    output = {
        'status': 'success',
        'tables_loaded': len(results),
        'load_details': results,
        'timestamp': datetime.utcnow().isoformat()
    }

    # Write load report
    s3.put_object(
        Bucket=bucket,
        Key='metadata/load_report.json',
        Body=json.dumps(output, indent=2)
    )

    return output

if __name__ == '__main__':
    from datetime import datetime
    result = main()
    print(json.dumps(result))
```text

---

## 🔄 Parte 2: Step Functions State Machine

### Step 2.1: State Machine Definition

Create `stepfunctions/etl_pipeline.asl.json`:

```json
{
  "Comment": "Complete ETL Pipeline with ECS Tasks",
  "StartAt": "Extract Data",
  "States": {
    "Extract Data": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask.sync",
      "Parameters": {
        "Cluster": "${ECS_CLUSTER_ARN}",
        "TaskDefinition": "${EXTRACT_TASK_DEFINITION}",
        "LaunchType": "FARGATE",
        "NetworkConfiguration": {
          "AwsvpcConfiguration": {
            "Subnets": ["${SUBNET_1}", "${SUBNET_2}"],
            "SecurityGroups": ["${SECURITY_GROUP}"],
            "AssignPublicIp": "DISABLED"
          }
        }
      },
      "ResultPath": "$.extractResult",
      "Next": "Parallel Transform",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 30,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "Extraction Failed",
          "ResultPath": "$.error"
        }
      ]
    },

    "Parallel Transform": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "Transform Sales",
          "States": {
            "Transform Sales": {
              "Type": "Task",
              "Resource": "arn:aws:states:::ecs:runTask.sync",
              "Parameters": {
                "Cluster": "${ECS_CLUSTER_ARN}",
                "TaskDefinition": "${TRANSFORM_SALES_TASK_DEF}",
                "LaunchType": "FARGATE",
                "NetworkConfiguration": {
                  "AwsvpcConfiguration": {
                    "Subnets": ["${SUBNET_1}", "${SUBNET_2}"],
                    "SecurityGroups": ["${SECURITY_GROUP}"]
                  }
                }
              },
              "End": true
            }
          }
        },
        {
          "StartAt": "Transform Customers",
          "States": {
            "Transform Customers": {
              "Type": "Task",
              "Resource": "arn:aws:states:::ecs:runTask.sync",
              "Parameters": {
                "Cluster": "${ECS_CLUSTER_ARN}",
                "TaskDefinition": "${TRANSFORM_CUSTOMERS_TASK_DEF}",
                "LaunchType": "FARGATE",
                "NetworkConfiguration": {
                  "AwsvpcConfiguration": {
                    "Subnets": ["${SUBNET_1}", "${SUBNET_2}"],
                    "SecurityGroups": ["${SECURITY_GROUP}"]
                  }
                }
              },
              "End": true
            }
          }
        },
        {
          "StartAt": "Transform Products",
          "States": {
            "Transform Products": {
              "Type": "Task",
              "Resource": "arn:aws:states:::ecs:runTask.sync",
              "Parameters": {
                "Cluster": "${ECS_CLUSTER_ARN}",
                "TaskDefinition": "${TRANSFORM_PRODUCTS_TASK_DEF}",
                "LaunchType": "FARGATE",
                "NetworkConfiguration": {
                  "AwsvpcConfiguration": {
                    "Subnets": ["${SUBNET_1}", "${SUBNET_2}"],
                    "SecurityGroups": ["${SECURITY_GROUP}"]
                  }
                }
              },
              "End": true
            }
          }
        }
      ],
      "ResultPath": "$.transformResults",
      "Next": "Validate Data"
    },

    "Validate Data": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask.sync",
      "Parameters": {
        "Cluster": "${ECS_CLUSTER_ARN}",
        "TaskDefinition": "${VALIDATE_TASK_DEFINITION}",
        "LaunchType": "FARGATE",
        "NetworkConfiguration": {
          "AwsvpcConfiguration": {
            "Subnets": ["${SUBNET_1}", "${SUBNET_2}"],
            "SecurityGroups": ["${SECURITY_GROUP}"]
          }
        }
      },
      "ResultPath": "$.validationResult",
      "Next": "Check Validation"
    },

    "Check Validation": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.validationResult.overall_valid",
          "BooleanEquals": true,
          "Next": "Load to Redshift"
        }
      ],
      "Default": "Move to Quarantine"
    },

    "Load to Redshift": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask.sync",
      "Parameters": {
        "Cluster": "${ECS_CLUSTER_ARN}",
        "TaskDefinition": "${LOAD_TASK_DEFINITION}",
        "LaunchType": "FARGATE",
        "NetworkConfiguration": {
          "AwsvpcConfiguration": {
            "Subnets": ["${SUBNET_1}", "${SUBNET_2}"],
            "SecurityGroups": ["${SECURITY_GROUP}"]
          }
        }
      },
      "ResultPath": "$.loadResult",
      "Next": "Send Success Notification"
    },

    "Move to Quarantine": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${QUARANTINE_LAMBDA}",
        "Payload": {
          "validation_report.$": "$.validationResult"
        }
      },
      "Next": "Send Failure Notification"
    },

    "Send Success Notification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${SNS_TOPIC_ARN}",
        "Subject": "✅ ETL Pipeline Completed Successfully",
        "Message.$": "States.Format('ETL Pipeline completed at {}. Loaded {} tables to Redshift.', $.loadResult.timestamp, $.loadResult.tables_loaded)"
      },
      "End": true
    },

    "Send Failure Notification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${SNS_TOPIC_ARN}",
        "Subject": "❌ ETL Pipeline Failed - Data Quality Issues",
        "Message.$": "States.Format('Data validation failed with {} issues. Files moved to quarantine.', States.ArrayLength($.validationResult.issues))"
      },
      "End": true
    },

    "Extraction Failed": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${SNS_TOPIC_ARN}",
        "Subject": "❌ ETL Pipeline Failed - Extraction Error",
        "Message.$": "$.error.Cause"
      },
      "End": true
    }
  }
}
```

### Step 2.2: Terraform for Step Functions

Create `terraform/stepfunctions.tf`:

```hcl
# Step Functions State Machine
resource "aws_sfn_state_machine" "etl_pipeline" {
  name     = "etl-data-pipeline"
  role_arn = aws_iam_role.stepfunctions.arn

  definition = templatefile("${path.module}/../stepfunctions/etl_pipeline.asl.json", {
    ECS_CLUSTER_ARN              = aws_ecs_cluster.main.arn
    EXTRACT_TASK_DEFINITION      = aws_ecs_task_definition.extract.arn
    TRANSFORM_SALES_TASK_DEF     = aws_ecs_task_definition.transform_sales.arn
    TRANSFORM_CUSTOMERS_TASK_DEF = aws_ecs_task_definition.transform_customers.arn
    TRANSFORM_PRODUCTS_TASK_DEF  = aws_ecs_task_definition.transform_products.arn
    VALIDATE_TASK_DEFINITION     = aws_ecs_task_definition.validate.arn
    LOAD_TASK_DEFINITION         = aws_ecs_task_definition.load.arn
    QUARANTINE_LAMBDA            = aws_lambda_function.quarantine.function_name
    SNS_TOPIC_ARN                = aws_sns_topic.etl_notifications.arn
    SUBNET_1                     = aws_subnet.private[0].id
    SUBNET_2                     = aws_subnet.private[1].id
    SECURITY_GROUP               = aws_security_group.ecs_tasks.id
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.stepfunctions.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }
}

# IAM Role for Step Functions
resource "aws_iam_role" "stepfunctions" {
  name = "stepfunctions-etl-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "stepfunctions" {
  name = "stepfunctions-etl-policy"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:DescribeTasks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.ecs_task.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "events:PutTargets",
          "events:PutRule",
          "events:DescribeRule"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.etl_notifications.arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.quarantine.arn
      }
    ]
  })
}

# SNS Topic for notifications
resource "aws_sns_topic" "etl_notifications" {
  name = "etl-pipeline-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.etl_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "stepfunctions" {
  name              = "/aws/vendedlogs/states/etl-pipeline"
  retention_in_days = 7
}

# EventBridge trigger (daily at 3 AM)
resource "aws_cloudwatch_event_rule" "daily_etl" {
  name                = "daily-etl"
  schedule_expression = "cron(0 3 * * ? *)"
}

resource "aws_cloudwatch_event_target" "stepfunctions" {
  rule      = aws_cloudwatch_event_rule.daily_etl.name
  target_id = "step-functions-etl"
  arn       = aws_sfn_state_machine.etl_pipeline.arn
  role_arn  = aws_iam_role.eventbridge_stepfunctions.arn
}

# IAM for EventBridge → Step Functions
resource "aws_iam_role" "eventbridge_stepfunctions" {
  name = "eventbridge-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_stepfunctions" {
  name = "eventbridge-stepfunctions-policy"
  role = aws_iam_role.eventbridge_stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "states:StartExecution"
      ]
      Resource = aws_sfn_state_machine.etl_pipeline.arn
    }]
  })
}
```text

---

## 🚀 Parte 3: Deploy y Test

### Step 3.1: Build & Push Containers

```bash
# Build all containers
for dir in extract transform_sales transform_customers transform_products validate load; do
  docker build -t etl-$dir:latest containers/$dir/
  docker tag etl-$dir:latest $(terraform output -raw ecr_url)/etl-$dir:latest
  docker push $(terraform output -raw ecr_url)/etl-$dir:latest
done
```text

### Step 3.2: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply
```text

### Step 3.3: Manual Trigger

```bash
# Start execution
aws stepfunctions start-execution \
  --state-machine-arn $(terraform output -raw state_machine_arn) \
  --name manual-execution-$(date +%s)

# Get execution ARN
EXECUTION_ARN=$(aws stepfunctions list-executions \
  --state-machine-arn $(terraform output -raw state_machine_arn) \
  --max-results 1 \
  --query 'executions[0].executionArn' \
  --output text)

# Monitor execution
aws stepfunctions describe-execution \
  --execution-arn $EXECUTION_ARN

# View execution history
aws stepfunctions get-execution-history \
  --execution-arn $EXECUTION_ARN
```

### Step 3.4: View in Console

```bash
# Get console URL
echo "https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines/view/$(terraform output -raw state_machine_arn)"
```text

---

## ✅ Validation

### 1. Step Functions Execution Success

```bash
aws stepfunctions describe-execution \
  --execution-arn $EXECUTION_ARN \
  | jq '.status'
# Should return "SUCCEEDED"
```text

### 2. All ECS Tasks Complete

```bash
# Check CloudWatch Logs for each task
aws logs tail /ecs/data-pipeline --follow --filter-pattern "completed successfully"
```text

### 3. Data Loaded to Redshift

```bash
psql -h $REDSHIFT_HOST -U dataeng -d analytics -c "SELECT COUNT(*) FROM fact_sales;"
```

### 4. SNS Notification Received

Check email for success notification.

---

## 🎓 Conclusión

Has aprendido a:
✅ Orquestar múltiples ECS tasks con Step Functions
✅ Parallel execution para performance
✅ Error handling robusto con retry y catch
✅ Choice states para branching logic
✅ Integration con SNS para notifications
✅ Complex ETL pipelines production-ready

**Próximo**: [Exercise 04 - Kubernetes Basics](../04-kubernetes-basics/) - Introducción a EKS.
