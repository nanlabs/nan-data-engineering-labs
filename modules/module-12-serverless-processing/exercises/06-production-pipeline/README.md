# Exercise 06: Production-Ready Serverless Pipeline

## 📋 Información General

- **Level**: Avanzado
- **Duration estimada**: 4-5 hours
- **Prerequisites**:
  - Todos los exercises anteriores completeds
  - Comprensión completa de serverless patterns
  - Experiencia con CI/CD

## 🎯 Objectives de Aprendizaje

1. Construir pipeline serverless production-ready
2. Implementar observability completa (X-Ray, CloudWatch)
3. CI/CD automation con GitHub Actions
4. Multi-environment deployment (dev, staging, prod)
5. Security best practices
6. Cost optimization
7. Disaster recovery

---

## 📚 Context

Construirás un **Real-Time Analytics Pipeline** completo y production-ready que:
- Ingesta logs de aplicaciones en tiempo real
- Procesa y agrega métricas
- Almacena en Data Lake particionado
- Genera dashboards en tiempo real
- Alertas automáticas
- CI/CD completo

**Arquitectura**:

```
┌──────────────────────────────────────────────────────────────┐
│                    PRODUCTION PIPELINE                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐                                             │
│  │ API Gateway │ (Logs endpoint)                             │
│  └──────┬──────┘                                             │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                            │
│  │  Kinesis     │ (Stream buffer)                            │
│  │  Data Stream │                                            │
│  └──────┬───────┘                                            │
│         │                                                    │
│    ┌────┴─────────┐                                          │
│    │              │                                          │
│    ▼              ▼                                          │
│ ┌──────┐    ┌──────────┐                                    │
│ │Lambda│    │ Kinesis  │                                    │
│ │Real- │    │ Firehose │                                    │
│ │time  │    │ (S3)     │                                    │
│ │Alert │    └──────────┘                                    │
│ └──────┘                                                    │
│                                                              │
│  ┌────────────────────────────────────────┐                 │
│  │         S3 Data Lake                    │                 │
│  │  /raw/year=/month=/day=/hour=/         │                 │
│  │  (Parquet, compressed, partitioned)    │                 │
│  └──────┬─────────────────────────────────┘                 │
│         │                                                   │
│         ▼                                                   │
│  ┌────────────────┐                                         │
│  │  Glue Crawler  │ → Athena (Ad-hoc queries)              │
│  └────────────────┘                                         │
│                                                              │
│  ┌────────────────────────────────────────┐                 │
│  │  CloudWatch Dashboard                   │                 │
│  │  - Real-time metrics                   │                 │
│  │  - Alarms                              │                 │
│  │  - X-Ray tracing                       │                 │
│  └────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Parte 1: Ingestion API

**`src/ingestion_api.py`**:

```python
"""
API para ingestión de logs con validation y rate limiting
"""
import json
import logging
import os
import boto3
from datetime import datetime
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Instrumentar AWS SDK con X-Ray
patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

kinesis = boto3.client('kinesis')
STREAM_NAME = os.environ['KINESIS_STREAM']

@xray_recorder.capture('lambda_handler')
def lambda_handler(event, context):
    """
    POST /logs - Ingest log events
    """

    try:
        body = json.loads(event['body'])

        # Validar
        validate_log_event(body)

        # Enriquecer con metadata
        enriched_event = enrich_event(body, event)

        # Enviar a Kinesis
        with xray_recorder.in_subsegment('kinesis_put') as subsegment:
            response = kinesis.put_record(
                StreamName=STREAM_NAME,
                Data=json.dumps(enriched_event),
                PartitionKey=enriched_event['app_id']
            )

            subsegment.put_annotation('app_id', enriched_event['app_id'])
            subsegment.put_metadata('event', enriched_event)

        logger.info(json.dumps({
            'event': 'log_ingested',
            'app_id': enriched_event['app_id'],
            'level': enriched_event['level'],
            'shard_id': response['ShardId']
        }))

        return response_ok({'message': 'Log ingested', 'sequence_number': response['SequenceNumber']})

    except ValueError as e:
        return response_error(400, str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return response_error(500, 'Internal error')


def validate_log_event(event: dict):
    """Validar evento de log"""
    required = ['app_id', 'level', 'message', 'timestamp']

    for field in required:
        if field not in event:
            raise ValueError(f"Missing required field: {field}")

    valid_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
    if event['level'] not in valid_levels:
        raise ValueError(f"Invalid level. Must be one of: {valid_levels}")


def enrich_event(event: dict, api_event: dict) -> dict:
    """Enriquecer evento con metadata adicional"""

    return {
        **event,
        'ingestion_timestamp': datetime.utcnow().isoformat(),
        'source_ip': api_event['requestContext']['identity']['sourceIp'],
        'user_agent': api_event['headers'].get('User-Agent', 'unknown'),
        'request_id': api_event['requestContext']['requestId']
    }


def response_ok(body: dict):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }


def response_error(status_code: int, message: str):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }
```

---

## 🔧 Parte 2: Real-Time Processor

**`src/realtime_processor.py`**:

```python
"""
Lambda que procesa streams de Kinesis en tiempo real
- Detecta anomalías
- Genera alertas
- Calcula métricas agregadas
"""
import json
import logging
import os
import base64
import boto3
from datetime import datetime
from collections import defaultdict
from aws_xray_sdk.core import xray_recorder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

ALERT_TOPIC = os.environ['ALERT_TOPIC_ARN']
ERROR_THRESHOLD = int(os.environ.get('ERROR_THRESHOLD', '10'))

@xray_recorder.capture('lambda_handler')
def lambda_handler(event, context):
    """
    Procesar batch de records de Kinesis
    """

    metrics = defaultdict(int)
    errors = []

    for record in event['Records']:
        # Decodificar data de Kinesis
        payload = base64.b64decode(record['kinesis']['data'])
        log_event = json.loads(payload)

        # Contadores
        metrics[f"{log_event['app_id']}_{log_event['level']}"] += 1

        # Detectar errores
        if log_event['level'] in ['ERROR', 'FATAL']:
            errors.append(log_event)

    # Publicar métricas a CloudWatch
    publish_metrics(metrics)

    # Alertar si hay muchos errores
    if len(errors) >= ERROR_THRESHOLD:
        send_alert(errors)

    logger.info(json.dumps({
        'event': 'batch_processed',
        'records': len(event['Records']),
        'errors': len(errors)
    }))

    return {'processed': len(event['Records'])}


def publish_metrics(metrics: dict):
    """Publicar custom metrics a CloudWatch"""

    metric_data = []

    for metric_name, value in metrics.items():
        app_id, level = metric_name.rsplit('_', 1)

        metric_data.append({
            'MetricName': 'LogEvents',
            'Value': value,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'AppId', 'Value': app_id},
                {'Name': 'Level', 'Value': level}
            ]
        })

    if metric_data:
        cloudwatch.put_metric_data(
            Namespace='LogAnalytics',
            MetricData=metric_data
        )


def send_alert(errors: list):
    """Enviar alerta por SNS"""

    message = {
        'alert_type': 'HIGH_ERROR_RATE',
        'timestamp': datetime.utcnow().isoformat(),
        'error_count': len(errors),
        'threshold': ERROR_THRESHOLD,
        'sample_errors': errors[:5]  # Primeros 5 errores
    }

    sns.publish(
        TopicArn=ALERT_TOPIC,
        Subject='🚨 High Error Rate Detected',
        Message=json.dumps(message, indent=2)
    )

    logger.warning(f"Alert sent: {len(errors)} errors detected")
```

---

## 🔧 Parte 3: Infrastructure (Production-Ready)

**`infrastructure/main.tf`** (multi-environment):

```hcl
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Configurar backend S3 para Terraform state
    # terraform init -backend-config="bucket=my-terraform-state"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "RealTimeAnalytics"
      ManagedBy   = "Terraform"
    }
  }
}

# Workspaces para multi-environment
locals {
  environment = terraform.workspace

  # Configuration por environment
  config = {
    dev = {
      kinesis_shards     = 1
      lambda_memory      = 512
      retention_days     = 7
      alarm_threshold    = 20
    }
    staging = {
      kinesis_shards     = 2
      lambda_memory      = 1024
      retention_days     = 14
      alarm_threshold    = 15
    }
    prod = {
      kinesis_shards     = 4
      lambda_memory      = 2048
      retention_days     = 30
      alarm_threshold    = 10
    }
  }

  env_config = local.config[local.environment]
}

# Kinesis Data Stream
resource "aws_kinesis_stream" "logs" {
  name             = "log-stream-${local.environment}"
  shard_count      = local.env_config.kinesis_shards
  retention_period = 24  # hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

# Kinesis Firehose → S3 (Data Lake)
resource "aws_kinesis_firehose_delivery_stream" "s3" {
  name        = "logs-to-s3-${local.environment}"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.logs.arn
    role_arn           = aws_iam_role.firehose.arn
  }

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = aws_s3_bucket.data_lake.arn
    prefix     = "raw/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"

    # Buffer settings
    buffering_size     = 5   # MB
    buffering_interval = 60  # seconds

    # Compression
    compression_format = "GZIP"

    # Cloudwatch Logging
    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose.name
      log_stream_name = "S3Delivery"
    }

    # Data transformation con Lambda (opcional)
    processing_configuration {
      enabled = true

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${aws_lambda_function.transform.arn}:$LATEST"
        }
      }
    }
  }
}

# S3 Data Lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "data-lake-${local.environment}-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# Lambda: Ingestion API
resource "aws_lambda_function" "ingestion_api" {
  filename      = "ingestion_api.zip"
  function_name = "log-ingestion-api-${local.environment}"
  role          = aws_iam_role.ingestion_api.arn
  handler       = "ingestion_api.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = local.env_config.lambda_memory

  environment {
    variables = {
      KINESIS_STREAM = aws_kinesis_stream.logs.name
      ENVIRONMENT    = local.environment
    }
  }

  # X-Ray Tracing
  tracing_config {
    mode = "Active"
  }

  # Reserved Concurrency (prod only)
  reserved_concurrent_executions = local.environment == "prod" ? 100 : null
}

# Lambda: Real-time Processor
resource "aws_lambda_function" "realtime_processor" {
  filename      = "realtime_processor.zip"
  function_name = "realtime-processor-${local.environment}"
  role          = aws_iam_role.realtime_processor.arn
  handler       = "realtime_processor.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = local.env_config.lambda_memory

  environment {
    variables = {
      ALERT_TOPIC_ARN  = aws_sns_topic.alerts.arn
      ERROR_THRESHOLD  = local.env_config.alarm_threshold
    }
  }

  tracing_config {
    mode = "Active"
  }
}

# Event Source Mapping: Kinesis → Lambda
resource "aws_lambda_event_source_mapping" "kinesis_processor" {
  event_source_arn  = aws_kinesis_stream.logs.arn
  function_name     = aws_lambda_function.realtime_processor.arn
  starting_position = "LATEST"
  batch_size        = 100

  maximum_batching_window_in_seconds = 10
  parallelization_factor             = 2
}

# SNS Topic para Alertas
resource "aws_sns_topic" "alerts" {
  name = "log-alerts-${local.environment}"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "LogAnalytics-${local.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", {stat = "Sum", period = 300}],
            [".", "IncomingBytes", {stat = "Sum", period = 300}]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "Kinesis Ingestion"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", {FunctionName = aws_lambda_function.ingestion_api.function_name}],
            [".", "Errors", {"."}],
            [".", "Duration", {stat = "Average"}]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "Lambda Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["LogAnalytics", "LogEvents", {Level = "ERROR"}],
            [".", ".", {Level = "FATAL"}]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "Error Events"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "high-error-rate-${local.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = local.env_config.alarm_threshold

  dimensions = {
    FunctionName = aws_lambda_function.ingestion_api.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# Outputs
output "ingestion_api_url" {
  value = aws_api_gateway_stage.api.invoke_url
}

output "kinesis_stream_name" {
  value = aws_kinesis_stream.logs.name
}

output "data_lake_bucket" {
  value = aws_s3_bucket.data_lake.id
}
```

---

## 🔧 Parte 4: CI/CD Pipeline

**`.github/workflows/deploy.yml`**:

```yaml
name: Deploy Serverless Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  PYTHON_VERSION: '3.11'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov moto

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-dev:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Package Lambda functions
        run: ./scripts/package-lambdas.sh

      - name: Deploy with Terraform
        run: |
          cd infrastructure
          terraform init
          terraform workspace select dev || terraform workspace new dev
          terraform apply -auto-approve

  deploy-prod:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_PROD_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_PROD_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Package Lambda functions
        run: ./scripts/package-lambdas.sh

      - name: Deploy with Terraform
        run: |
          cd infrastructure
          terraform init
          terraform workspace select prod || terraform workspace new prod
          terraform apply -auto-approve

      - name: Run smoke tests
        run: ./scripts/smoke-tests.sh
```

---

## ✅ Checklist de Producción

### Security
- [ ] IAM roles con least privilege
- [ ] Secrets en AWS Secrets Manager
- [ ] VPC endpoints configurados
- [ ] Encryption at rest y in transit
- [ ] API Gateway con authentication
- [ ] WAF rules configuradas

### Observability
- [ ] X-Ray tracing habilitado
- [ ] Structured logging (JSON)
- [ ] CloudWatch Dashboard
- [ ] Custom metrics publicadas
- [ ] Alarmas configuradas
- [ ] SNS notifications

### Reliability
- [ ] Multi-AZ deployment
- [ ] Dead Letter Queues
- [ ] Retry logic con exponential backoff
- [ ] Circuit breakers
- [ ] Idempotencia garantizada

### Performance
- [ ] Lambda memory tuning
- [ ] Reserved concurrency configurado
- [ ] Kinesis shards adecuados
- [ ] S3 lifecycle policies
- [ ] Compression habilitada

### Cost Optimization
- [ ] S3 Intelligent Tiering
- [ ] DynamoDB on-demand billing
- [ ] Lambda timeout optimizado
- [ ] CloudWatch Logs retention policies
- [ ] Resource tagging completo

### CI/CD
- [ ] Automated tests (>80% coverage)
- [ ] Multi-environment deployment
- [ ] Smoke tests post-deployment
- [ ] Rollback mechanism
- [ ] Change approval workflow

---

## 🎓 Conclusión

¡Felicitaciones! Has completed el **Module 12: Serverless Processing**.

Has aprendido a:
✅ Construir aplicaciones serverless escalables
✅ Orquestar workflows complejos con Step Functions
✅ Implementar APIs REST production-ready
✅ Procesar streams en tiempo real
✅ Desplegar con CI/CD automation
✅ Aplicar observability y security best practices

**Próximo module**: [Module 13 - Container Orchestration](../../module-13-container-orchestration/)
