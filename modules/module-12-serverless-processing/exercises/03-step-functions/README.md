# Exercise 03: Step Functions Workflow

## 📋 Información General

- **Level**: Intermedio
- **Duration estimada**: 3-4 hours
- **Prerequisites**:
  - Exercises 01 y 02 completeds
  - Comprensión de state machines
  - Conocimiento de Amazon States Language (ASL)

## 🎯 Objectives de Aprendizaje

Al completar este exercise, serás capaz de:

1. Diseñar workflows complejos con AWS Step Functions
2. Coordinar múltiples funciones Lambda
3. Implementar manejo de errores y retries
4. Usar estados condicionales (Choice)
5. Ejecutar tareas en paralelo
6. Implementar patrones de orquestación

---

## 📚 Context

Construirás un **ETL Pipeline completo** orquestado por Step Functions que:
1. Extrae datos de una API externa
2. Validate la calidad de los datos
3. Transforma datos en paralelo (customers y orders)
4. Carga resultados a Data Warehouse (S3 + Glue)
5. Genera reporte y envía notificación

**Arquitectura**:

```
┌──────────────────────────┐
│  EventBridge Schedule    │
│  (Trigger diario 9 AM)   │
└───────────┬──────────────┘
            │
            ▼
┌─────────────────────────────────────────────┐
│         Step Functions State Machine         │
│                                              │
│  ┌────────────┐                              │
│  │  Extract   │ (Lambda: Fetch API data)     │
│  └──────┬─────┘                              │
│         │                                    │
│         ▼                                    │
│  ┌────────────┐                              │
│  │  Validate  │ (Lambda: Data quality)       │
│  └──────┬─────┘                              │
│         │                                    │
│    ┌────┴────┐ (Choice: Is valid?)          │
│    │ Valid?  │                               │
│    └────┬────┘                               │
│         │                                    │
│    ┌────┴─────────┐                          │
│    │              │                          │
│    ▼              ▼                          │
│ ┌─────┐      ┌────────┐                     │
│ │Trans│      │Quarant.│                     │
│ │form │      │        │                     │
│ │(Para│      └────────┘                     │
│ │llel)│                                     │
│ └──┬──┘                                     │
│    │                                        │
│    ├─ Lambda: Transform Customers          │
│    └─ Lambda: Transform Orders             │
│    │                                        │
│    ▼                                        │
│  ┌────────────┐                             │
│  │   Load     │ (Lambda: Load to S3/Glue)  │
│  └──────┬─────┘                             │
│         │                                   │
│         ▼                                   │
│  ┌────────────┐                             │
│  │  Report    │ (Lambda: Generate report)  │
│  └──────┬─────┘                             │
│         │                                   │
│         ▼                                   │
│  ┌────────────┐                             │
│  │  Notify    │ (SNS: Send email)          │
│  └────────────┘                             │
└─────────────────────────────────────────────┘
```

---

## 🔧 Parte 1: Lambda Functions

### 1.1 Extract (Obtener datos de API)

**`src/extract.py`**:

```python
"""
Lambda: Extract - Obtener datos de API externa
"""
import json
import logging
import requests
from datetime import datetime, timedelta
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Extraer datos de API externa y guardar en S3
    """

    # Parámetros
    api_url = event.get('api_url', 'https://api.example.com/data')
    start_date = event.get('start_date', (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d'))
    end_date = event.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))

    logger.info(f"Extracting data from {start_date} to {end_date}")

    try:
        # Llamar API (simulado con fake API)
        response = requests.get(
            api_url,
            params={
                'start_date': start_date,
                'end_date': end_date
            },
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        # Guardar raw data en S3
        bucket = event.get('bucket', 'data-lake-dev')
        key = f"raw/extraction_date={datetime.utcnow().strftime('%Y%m%d')}/data.json"

        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )

        logger.info(f"Extracted {len(data.get('records', []))} records")

        return {
            'statusCode': 200,
            'extraction_timestamp': datetime.utcnow().isoformat(),
            's3_uri': f's3://{bucket}/{key}',
            'record_count': len(data.get('records', [])),
            'start_date': start_date,
            'end_date': end_date
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise Exception(f"Extraction failed: {e}")
```

### 1.2 Validate (Validar calidad de datos)

**`src/validate.py`**:

```python
"""
Lambda: Validate - Validar calidad de datos
"""
import json
import logging
import boto3
from io import BytesIO
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Validar calidad de datos extraídos
    """

    # Obtener S3 URI de datos
    extraction_result = event
    s3_uri = extraction_result['s3_uri']
    bucket, key = parse_s3_uri(s3_uri)

    logger.info(f"Validating data from {s3_uri}")

    # Descargar datos
    response = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(response['Body'].read())

    # Ejecutar validaciones
    validation_results = {
        'is_valid': True,
        'checks': [],
        'errors': [],
        'warnings': []
    }

    records = data.get('records', [])

    # 1. Check: Mínimo de registros
    if len(records) < 1:
        validation_results['is_valid'] = False
        validation_results['errors'].append('No records found')
    else:
        validation_results['checks'].append(f'✓ Record count: {len(records)}')

    # 2. Check: Campos requeridos
    required_fields = ['id', 'customer_id', 'amount', 'date']
    for idx, record in enumerate(records[:10]):  # Validar primeros 10
        missing = [f for f in required_fields if f not in record]
        if missing:
            validation_results['is_valid'] = False
            validation_results['errors'].append(
                f'Record {idx}: Missing fields {missing}'
            )

    if len(validation_results['errors']) == 0:
        validation_results['checks'].append('✓ All required fields present')

    # 3. Check: Valores nulos
    df = pd.DataFrame(records)
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        validation_results['warnings'].append(
            f'Null values found: {null_counts[null_counts > 0].to_dict()}'
        )
    else:
        validation_results['checks'].append('✓ No null values')

    # 4. Check: Duplicados
    if df.duplicated(subset=['id']).any():
        validation_results['is_valid'] = False
        validation_results['errors'].append('Duplicate IDs found')
    else:
        validation_results['checks'].append('✓ No duplicates')

    # 5. Check: Valores negativos en amount
    if (df['amount'] < 0).any():
        validation_results['is_valid'] = False
        validation_results['errors'].append('Negative amounts found')
    else:
        validation_results['checks'].append('✓ All amounts positive')

    logger.info(json.dumps(validation_results))

    # Agregar resultado al evento
    return {
        **extraction_result,
        'validation': validation_results
    }


def parse_s3_uri(uri: str) -> tuple:
    """Parse s3://bucket/key to (bucket, key)"""
    parts = uri.replace('s3://', '').split('/', 1)
    return parts[0], parts[1]
```

### 1.3 Transform (Transformar datos)

**` src/transform_customers.py`**:

```python
"""
Lambda: Transform Customers - Transformar datos de clientes
"""
import json
import logging
import boto3
import pandas as pd
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Transformar datos de clientes
    """

    s3_uri = event['s3_uri']
    bucket, key = parse_s3_uri(s3_uri)

    logger.info(f"Transforming customers from {s3_uri}")

    # Cargar datos
    response = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(response['Body'].read())
    df = pd.DataFrame(data['records'])

    # Transformaciones
    customers = df.groupby('customer_id').agg({
        'amount': ['sum', 'mean', 'count'],
        'date': ['min', 'max']
    }).reset_index()

    customers.columns = ['customer_id', 'total_amount', 'avg_amount',
                         'transaction_count', 'first_purchase', 'last_purchase']

    # Guardar resultado
    output_key = key.replace('raw/', 'transformed/customers/')

    parquet_buffer = BytesIO()
    customers.to_parquet(parquet_buffer, engine='pyarrow')

    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=parquet_buffer.getvalue()
    )

    logger.info(f"Transformed {len(customers)} customers")

    return {
        's3_uri': f's3://{bucket}/{output_key}',
        'record_count': len(customers)
    }


def parse_s3_uri(uri: str) -> tuple:
    parts = uri.replace('s3://', '').split('/', 1)
    return parts[0], parts[1]
```

**`src/transform_orders.py`** (similar structure):

```python
"""
Lambda: Transform Orders - Transformar datos de órdenes
"""
import json
import logging
import boto3
import pandas as pd
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Transformar datos de órdenes
    """

    s3_uri = event['s3_uri']
    bucket, key = parse_s3_uri(s3_uri)

    logger.info(f"Transforming orders from {s3_uri}")

    # Cargar datos
    response = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(response['Body'].read())
    df = pd.DataFrame(data['records'])

    # Transformaciones
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day

    # Guardar resultado particionado por fecha
    output_key = key.replace('raw/', 'transformed/orders/')

    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, engine='pyarrow')

    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=parquet_buffer.getvalue()
    )

    logger.info(f"Transformed {len(df)} orders")

    return {
        's3_uri': f's3://{bucket}/{output_key}',
        'record_count': len(df)
    }


def parse_s3_uri(uri: str) -> tuple:
    parts = uri.replace('s3://', '').split('/', 1)
    return parts[0], parts[1]
```

### 1.4 Load y Report

**`src/load.py`**:

```python
"""
Lambda: Load - Cargar datos transformados
"""
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client('glue')

def lambda_handler(event, context):
    """
    Trigger Glue Crawler para actualizar Catalog
    """

    customers_result = event[0]  # Resultado parallel branch 1
    orders_result = event[1]     # Resultado parallel branch 2

    logger.info("Loading transformed data to Data Catalog")

    # Trigger Glue Crawler
    try:
        glue.start_crawler(Name='data-lake-crawler')
        logger.info("Glue crawler started successfully")
    except glue.exceptions.CrawlerRunningException:
        logger.info("Crawler already running")

    return {
        'statusCode': 200,
        'customers': customers_result,
        'orders': orders_result,
        'catalog_updated': True
    }
```

**`src/report.py`**:

```python
"""
Lambda: Report - Generar reporte de ejecución
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Generar reporte final del pipeline
    """

    report = {
        'pipeline': 'daily-etl',
        'execution_time': datetime.utcnow().isoformat(),
        'status': 'SUCCESS',
        'summary': {
            'records_extracted': event['record_count'],
            'customers_transformed': event['customers']['record_count'],
            'orders_transformed': event['orders']['record_count'],
            'validation_passed': event['validation']['is_valid']
        }
    }

    logger.info(json.dumps(report, indent=2))

    return report
```

---

## 🔧 Parte 2: Step Functions State Machine

### 2.1 State Machine Definition

**`infrastructure/state_machine.json`**:

```json
{
  "Comment": "Daily ETL Pipeline with Step Functions",
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "${ExtractLambdaArn}",
      "ResultPath": "$.extraction",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 60,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "ExtractFailed"
        }
      ],
      "Next": "Validate"
    },

    "Validate": {
      "Type": "Task",
      "Resource": "${ValidateLambdaArn}",
      "ResultPath": "$",
      "Next": "CheckValidation"
    },

    "CheckValidation": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.validation.is_valid",
          "BooleanEquals": true,
          "Next": "ParallelTransform"
        }
      ],
      "Default": "ValidationFailed"
    },

    "ParallelTransform": {
      "Type": "Parallel",
      "ResultPath": "$.transform_results",
      "Branches": [
        {
          "StartAt": "TransformCustomers",
          "States": {
            "TransformCustomers": {
              "Type": "Task",
              "Resource": "${TransformCustomersArn}",
              "End": true
            }
          }
        },
        {
          "StartAt": "TransformOrders",
          "States": {
            "TransformOrders": {
              "Type": "Task",
              "Resource": "${TransformOrdersArn}",
              "End": true
            }
          }
        }
      ],
      "Next": "Load"
    },

    "Load": {
      "Type": "Task",
      "Resource": "${LoadLambdaArn}",
      "InputPath": "$.transform_results",
      "ResultPath": "$.load_result",
      "Next": "GenerateReport"
    },

    "GenerateReport": {
      "Type": "Task",
      "Resource": "${ReportLambdaArn}",
      "ResultPath": "$.report",
      "Next": "NotifySuccess"
    },

    "NotifySuccess": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${SNSTopicArn}",
        "Subject": "ETL Pipeline Success",
        "Message.$": "$.report"
      },
      "End": true
    },

    "ValidationFailed": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${SNSTopicArn}",
        "Subject": "ETL Pipeline - Validation Failed",
        "Message": {
          "Status": "FAILED",
          "Reason": "Data validation failed",
          "Errors.$": "$.validation.errors"
        }
      },
      "Next": "FailState"
    },

    "ExtractFailed": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${SNSTopicArn}",
        "Subject": "ETL Pipeline - Extract Failed",
        "Message.$": "$.error"
      },
      "Next": "FailState"
    },

    "FailState": {
      "Type": "Fail",
      "Error": "PipelineExecutionFailed",
      "Cause": "Pipeline failed, check notifications"
    }
  }
}
```

---

## 🔧 Parte 3: Infrastructure (Terraform)

**`infrastructure/main.tf`** (excerpts):

```hcl
# Step Functions State Machine
resource "aws_sfn_state_machine" "etl_pipeline" {
  name     = "daily-etl-pipeline-${var.environment}"
  role_arn = aws_iam_role.step_functions.arn

  definition = templatefile("${path.module}/state_machine.json", {
    ExtractLambdaArn       = aws_lambda_function.extract.arn
    ValidateLambdaArn      = aws_lambda_function.validate.arn
    TransformCustomersArn  = aws_lambda_function.transform_customers.arn
    TransformOrdersArn     = aws_lambda_function.transform_orders.arn
    LoadLambdaArn          = aws_lambda_function.load.arn
    ReportLambdaArn        = aws_lambda_function.report.arn
    SNSTopicArn            = aws_sns_topic.pipeline_notifications.arn
  })
}

# IAM Role para Step Functions
resource "aws_iam_role" "step_functions" {
  name = "etl-step-functions-role-${var.environment}"

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

# Policy: Invocar Lambdas
resource "aws_iam_role_policy" "step_functions_lambda" {
  name = "invoke-lambdas"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "lambda:InvokeFunction"
      ]
      Resource = [
        aws_lambda_function.extract.arn,
        aws_lambda_function.validate.arn,
        aws_lambda_function.transform_customers.arn,
        aws_lambda_function.transform_orders.arn,
        aws_lambda_function.load.arn,
        aws_lambda_function.report.arn
      ]
    }]
  })
}

# Policy: Publicar a SNS
resource "aws_iam_role_policy" "step_functions_sns" {
  name = "publish-sns"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sns:Publish"
      ]
      Resource = aws_sns_topic.pipeline_notifications.arn
    }]
  })
}

# EventBridge Rule: Trigger diario
resource "aws_cloudwatch_event_rule" "daily_etl" {
  name                = "daily-etl-trigger-${var.environment}"
  description         = "Trigger ETL pipeline daily at 9 AM UTC"
  schedule_expression = "cron(0 9 * * ? *)"
}

resource "aws_cloudwatch_event_target" "step_functions" {
  rule      = aws_cloudwatch_event_rule.daily_etl.name
  target_id = "TriggerStepFunctions"
  arn       = aws_sfn_state_machine.etl_pipeline.arn
  role_arn  = aws_iam_role.eventbridge.arn

  input = jsonencode({
    api_url = "https://api.example.com/data"
    bucket  = aws_s3_bucket.data_lake.id
  })
}

# IAM Role para EventBridge
resource "aws_iam_role" "eventbridge" {
  name = "eventbridge-step-functions-${var.environment}"

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

resource "aws_iam_role_policy" "eventbridge_step_functions" {
  name = "start-execution"
  role = aws_iam_role.eventbridge.id

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

# Outputs
output "state_machine_arn" {
  value = aws_sfn_state_machine.etl_pipeline.arn
}
```

---

## 🧪 Parte 4: Testing

### 4.1 Test Manual

```bash
# Deploy infrastructure
cd infrastructure/
terraform apply

# Start execution manually
STATE_MACHINE_ARN=$(terraform output -raw state_machine_arn)

aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{
    "api_url": "https://jsonplaceholder.typicode.com/posts",
    "bucket": "data-lake-dev-abc123"
  }'

# Ver ejecución en consola
echo "https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines/view/$STATE_MACHINE_ARN"
```

### 4.2 Monitor Execution

```bash
# Listar ejecuciones
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 10

# Ver detalle de ejecución
EXECUTION_ARN="<execution-arn-from-previous-command>"

aws stepfunctions describe-execution \
  --execution-arn $EXECUTION_ARN

# Ver history
aws stepfunctions get-execution-history \
  --execution-arn $EXECUTION_ARN
```

---

## ✅ Checklist

- [ ] 6 Lambda functions creadas
- [ ] State Machine desplegada
- [ ] EventBridge trigger configurado (cron)
- [ ] Parallel execution funciona
- [ ] Retry logic implementado
- [ ] Choice states funcionan
- [ ] SNS notifications recibidas
- [ ] Logs en CloudWatch
- [ ] Ejecución manual exitosa

**Siguiente**: [Exercise 04 - EventBridge Patterns](../04-eventbridge-patterns/)
