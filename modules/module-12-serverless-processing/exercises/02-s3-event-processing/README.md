# Exercise 02: S3 Event Processing Avanzado

## 📋 Información General

- **Level**: Intermedio
- **Duration estimada**: 3-4 hours
- **Prerequisites**:
  - Exercise 01 completed
  - Conocimiento de Parquet y particionado de datos
  - Comprensión de SQS queues

## 🎯 Objectives de Aprendizaje

Al completar este exercise, serás capaz de:

1. Transformar CSV a formato Parquet eficientemente
2. Implementar particionado de datos por fecha
3. Usar SQS como buffer entre S3 y Lambda
4. Manejar archivos grandes con procesamiento por chunks
5. Implementar Dead Letter Queue (DLQ) para errores
6. Integrar con AWS Glue Data Catalog

---

## 📚 Context

Construirás un pipeline de ingesta de datos que:
- Recibe archivos CSV de diferentes fuentes
- Los valida y transforma a Parquet
- Los particiona por fecha y categoría
- Actualiza automáticamente el AWS Glue Data Catalog
- Maneja errores con retry automático y DLQ

**Arquitectura**:

```
┌─────────────────┐
│  Source Systems │
└────────┬────────┘
         │ Upload CSV
         ▼
┌─────────────────────────────────┐
│  S3: landing/                   │
│  Raw CSV files                  │
└─────────┬───────────────────────┘
          │ S3 Event
          ▼
┌─────────────────────────────────┐
│  SQS: file-processing-queue     │
│  Buffer (decoupling)            │
└─────────┬───────────────────────┘
          │ Batch (up to 10 msgs)
          ▼
┌──────────────────────────────────────────┐
│  Lambda: csv-to-parquet-processor        │
│  1. Validate schema                      │
│  2. Transform to Parquet                 │
│  3. Partition by date/category           │
│  4. Update Glue Catalog                  │
└─────────┬────────────────────────────────┘
          │
     ┌────┴─────┬─────────────┐
     ▼          ▼             ▼
┌─────────┐ ┌────────┐  ┌──────────────┐
│S3:      │ │S3:     │  │Glue Crawler  │
│processed│ │quarant.│  │(Auto catalog)│
│(Parquet)│ │(errors)│  └──────────────┘
└─────────┘ └────────┘
```

---

## 🔧 Parte 1: Procesamiento CSV → Parquet

### 1.1 Handler Principal

**`src/handler.py`**:

```python
"""
Lambda para transformar CSV a Parquet con particionado
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
import jsonschema

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
glue = boto3.client('glue')

# Environment variables
TARGET_BUCKET = os.environ['TARGET_BUCKET']
DATABASE_NAME = os.environ.get('GLUE_DATABASE', 'data_lake')
TABLE_NAME = os.environ.get('GLUE_TABLE', 'sales_data')

# Schema esperado
SALES_SCHEMA = {
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "category": {"type": "string"},
        "amount": {"type": "number", "minimum": 0},
        "customer_id": {"type": "string"}
    },
    "required": ["transaction_id", "date", "category", "amount"]
}

def lambda_handler(event, context):
    """
    Procesar batch de mensajes SQS (cada uno con info de archivo S3)
    """

    results = {
        'processed': 0,
        'failed': 0,
        'quarantined': 0
    }

    for record in event['Records']:
        try:
            # Parsear mensaje SQS
            message_body = json.loads(record['body'])

            # Extraer info del evento S3 (dentro del mensaje)
            s3_event = message_body['Records'][0]
            bucket = s3_event['s3']['bucket']['name']
            key = s3_event['s3']['object']['key']

            logger.info(json.dumps({
                'event': 'processing_file',
                'bucket': bucket,
                'key': key,
                'message_id': record['messageId']
            }))

            # Procesar archivo
            process_file(bucket, key)
            results['processed'] += 1

        except ValidationError as e:
            # Error de validation → mover a quarantine
            logger.warning(f"Validation error: {e}")
            move_to_quarantine(bucket, key, str(e))
            results['quarantined'] += 1

        except Exception as e:
            # Error inesperado → raise para retry
            logger.error(f"Processing error: {e}")
            results['failed'] += 1
            raise e

    logger.info(json.dumps({
        'event': 'batch_processed',
        'results': results
    }))

    return results


def process_file(bucket: str, key: str):
    """
    Procesar un archivo CSV
    """

    # 1. Descargar y leer CSV
    logger.info(f"Downloading s3://{bucket}/{key}")
    response = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(BytesIO(response['Body'].read()))

    # 2. Validar schema
    validate_dataframe(df)

    # 3. Transformaciones
    df = transform_data(df)

    # 4. Particionar y guardar como Parquet
    save_partitioned_parquet(df, TARGET_BUCKET)

    # 5. Actualizar Glue Catalog (async)
    trigger_glue_crawler()

    logger.info(f"Successfully processed {len(df)} records from {key}")


def validate_dataframe(df: pd.DataFrame):
    """
    Validar que DataFrame cumple con el schema esperado
    """

    # Verificar columnas requeridas
    required_cols = set(SALES_SCHEMA['required'])
    actual_cols = set(df.columns)

    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        raise ValidationError(f"Missing required columns: {missing}")

    # Validar cada fila contra schema
    errors = []
    for idx, row in df.head(10).iterrows():  # Validar primeras 10 filas
        try:
            jsonschema.validate(row.to_dict(), SALES_SCHEMA)
        except jsonschema.ValidationError as e:
            errors.append(f"Row {idx}: {e.message}")

    if errors:
        raise ValidationError(f"Schema validation failed: {errors[:3]}")

    # Validaciones de calidad
    if df['amount'].isna().any():
        raise ValidationError("Null values found in 'amount' column")

    if df.duplicated(subset=['transaction_id']).any():
        raise ValidationError("Duplicate transaction IDs found")


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplicar transformaciones al DataFrame
    """

    # Convertir date a datetime
    df['date'] = pd.to_datetime(df['date'])

    # Extraer componentes de fecha para particionado
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day

    # Normalizar categorías
    df['category'] = df['category'].str.lower().str.strip()

    # Agregar metadata
    df['ingestion_timestamp'] = pd.Timestamp.utcnow()
    df['file_source'] = 'csv_import'

    return df


def save_partitioned_parquet(df: pd.DataFrame, bucket: str):
    """
    Guardar DataFrame como Parquet particionado por year/month/category
    """

    # Agrupar por particiones
    partition_cols = ['year', 'month', 'category']

    for keys, group in df.groupby(partition_cols):
        year, month, category = keys

        # Path particionado
        partition_path = f"processed/year={year}/month={month:02d}/category={category}/"
        file_name = f"data_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.parquet"
        s3_key = partition_path + file_name

        # Convertir a Parquet
        table = pa.Table.from_pandas(group)
        parquet_buffer = BytesIO()
        pq.write_table(
            table,
            parquet_buffer,
            compression='snappy',
            use_dictionary=True
        )

        # Subir a S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=parquet_buffer.getvalue(),
            ContentType='application/octet-stream'
        )

        logger.info(json.dumps({
            'event': 'partition_saved',
            's3_uri': f's3://{bucket}/{s3_key}',
            'records': len(group),
            'size_bytes': len(parquet_buffer.getvalue())
        }))


def move_to_quarantine(bucket: str, key: str, error_message: str):
    """
    Mover archivo inválido a quarantine con metadata de error
    """

    quarantine_key = key.replace('landing/', 'quarantine/')

    # Copiar archivo
    s3.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': bucket, 'Key': key},
        Key=quarantine_key,
        Metadata={
            'error': error_message,
            'quarantined_at': datetime.utcnow().isoformat()
        },
        MetadataDirective='REPLACE'
    )

    # Eliminar original
    s3.delete_object(Bucket=bucket, Key=key)

    logger.warning(json.dumps({
        'event': 'file_quarantined',
        'original': f's3://{bucket}/{key}',
        'quarantine': f's3://{bucket}/{quarantine_key}',
        'error': error_message
    }))


def trigger_glue_crawler():
    """
    Iniciar Glue Crawler para actualizar Data Catalog
    """
    try:
        glue.start_crawler(Name=f'{DATABASE_NAME}_crawler')
        logger.info("Glue crawler triggered")
    except glue.exceptions.CrawlerRunningException:
        logger.info("Crawler already running")
    except Exception as e:
        logger.warning(f"Could not trigger crawler: {e}")


class ValidationError(Exception):
    """Custom exception para errores de validation"""
    pass
```

**`src/requirements.txt`**:

```txt
pandas==2.1.4
pyarrow==14.0.2
boto3==1.34.0
jsonschema==4.20.0
```

---

## 🔧 Parte 2: Infrastructure

### 2.1 Terraform Configuration

**`infrastructure/main.tf`**:

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

# S3 Buckets
resource "aws_s3_bucket" "source" {
  bucket = "data-source-${var.environment}-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "target" {
  bucket = "data-lake-${var.environment}-${random_id.suffix.hex}"
}

resource "random_id" "suffix" {
  byte_length = 4
}

# SQS Queue
resource "aws_sqs_queue" "processing_queue" {
  name                       = "file-processing-queue-${var.environment}"
  visibility_timeout_seconds = 300  # 5 min (debe ser >= Lambda timeout)
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 10  # Long polling

  # Dead Letter Queue config
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3  # Después de 3 intentos → DLQ
  })
}

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name                      = "file-processing-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days
}

# CloudWatch Alarm para DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_alarm" {
  alarm_name          = "dlq-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when messages appear in DLQ"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# SNS Topic para alertas
resource "aws_sns_topic" "alerts" {
  name = "data-pipeline-alerts-${var.environment}"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "your-email@example.com"  # Cambiar
}

# S3 Event Notification → SQS
resource "aws_s3_bucket_notification" "source_notification" {
  bucket = aws_s3_bucket.source.id

  queue {
    queue_arn     = aws_sqs_queue.processing_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "landing/"
    filter_suffix = ".csv"
  }

  depends_on = [aws_sqs_queue_policy.allow_s3]
}

# SQS Policy: Permitir S3 enviar mensajes
resource "aws_sqs_queue_policy" "allow_s3" {
  queue_url = aws_sqs_queue.processing_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.processing_queue.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_s3_bucket.source.arn
        }
      }
    }]
  })
}

# Lambda Function
resource "aws_lambda_function" "processor" {
  filename      = "lambda.zip"
  function_name = "csv-to-parquet-processor-${var.environment}"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 120
  memory_size   = 1024

  environment {
    variables = {
      TARGET_BUCKET = aws_s3_bucket.target.id
      GLUE_DATABASE = aws_glue_catalog_database.data_lake.name
      GLUE_TABLE    = "sales_data"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_logs
  ]
}

# Lambda Event Source Mapping: SQS → Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.processing_queue.arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 10  # Procesar hasta 10 mensajes por invocación
  enabled          = true

  # Parámetros de retry
  function_response_types = ["ReportBatchItemFailures"]
}

# IAM Role para Lambda
resource "aws_iam_role" "lambda" {
  name = "csv-processor-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Policy: CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy: S3 Access
resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:CopyObject"
        ]
        Resource = [
          "${aws_s3_bucket.source.arn}/*",
          "${aws_s3_bucket.target.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [
          aws_s3_bucket.source.arn,
          aws_s3_bucket.target.arn
        ]
      }
    ]
  })
}

# Policy: SQS Access
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "lambda-sqs-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = aws_sqs_queue.processing_queue.arn
    }]
  })
}

# Policy: Glue Access
resource "aws_iam_role_policy" "lambda_glue" {
  name = "lambda-glue-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "glue:StartCrawler",
        "glue:GetCrawler"
      ]
      Resource = "*"
    }]
  })
}

# Glue Data Catalog
resource "aws_glue_catalog_database" "data_lake" {
  name = "data_lake_${var.environment}"
}

resource "aws_glue_crawler" "sales_data" {
  name          = "${aws_glue_catalog_database.data_lake.name}_crawler"
  role          = aws_iam_role.glue_crawler.arn
  database_name = aws_glue_catalog_database.data_lake.name

  s3_target {
    path = "s3://${aws_s3_bucket.target.id}/processed/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })
}

# IAM Role para Glue Crawler
resource "aws_iam_role" "glue_crawler" {
  name = "glue-crawler-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3" {
  name = "glue-s3-access"
  role = aws_iam_role.glue_crawler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject"
      ]
      Resource = "${aws_s3_bucket.target.arn}/*"
    }]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.processor.function_name}"
  retention_in_days = 7
}

# Outputs
output "source_bucket" {
  value = aws_s3_bucket.source.id
}

output "target_bucket" {
  value = aws_s3_bucket.target.id
}

output "queue_url" {
  value = aws_sqs_queue.processing_queue.url
}

output "glue_database" {
  value = aws_glue_catalog_database.data_lake.name
}
```

---

## 🧪 Parte 3: Testing

### 3.1 Generar Datos de Test

**`scripts/generate_test_data.py`**:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generar datos sintéticos
np.random.seed(42)

dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
categories = ['electronics', 'clothing', 'food', 'books', 'toys']

data = []
for i in range(10000):
    data.append({
        'transaction_id': f'TXN{i:06d}',
        'date': np.random.choice(dates).strftime('%Y-%m-%d'),
        'category': np.random.choice(categories),
        'amount': round(np.random.uniform(10, 500), 2),
        'customer_id': f'CUST{np.random.randint(1, 1000):04d}'
    })

df = pd.DataFrame(data)

# Guardar como CSV
df.to_csv('test_sales_data.csv', index=False)
print(f"Generated {len(df)} records")
```

### 3.2 Test End-to-End

```bash
# 1. Deploy infrastructure
cd infrastructure/
terraform apply

# 2. Generar datos de test
cd ../scripts/
python generate_test_data.py

# 3. Upload a S3
SOURCE_BUCKET=$(cd ../infrastructure && terraform output -raw source_bucket)
aws s3 cp test_sales_data.csv s3://$SOURCE_BUCKET/landing/

# 4. Monitorear logs
aws logs tail /aws/lambda/csv-to-parquet-processor-dev --follow

# 5. Verificar SQS (debe estar vacía después de procesarse)
aws sqs get-queue-attributes \
  --queue-url $(cd ../infrastructure && terraform output -raw queue_url) \
  --attribute-names ApproximateNumberOfMessages

# 6. Verificar Parquet files creados
TARGET_BUCKET=$(cd ../infrastructure && terraform output -raw target_bucket)
aws s3 ls s3://$TARGET_BUCKET/processed/ --recursive

# 7. Query con Athena
aws athena start-query-execution \
  --query-string "SELECT category, COUNT(*), SUM(amount) FROM sales_data GROUP BY category" \
  --result-configuration "OutputLocation=s3://$TARGET_BUCKET/athena-results/" \
  --query-execution-context "Database=data_lake_dev"
```

---

## 📊 Parte 4: Monitoring y Alertas

### 4.1 CloudWatch Dashboard

```hcl
resource "aws_cloudwatch_dashboard" "pipeline" {
  dashboard_name = "data-pipeline-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", {FunctionName = aws_lambda_function.processor.function_name}],
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
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", {QueueName = aws_sqs_queue.processing_queue.name}],
            [".", "NumberOfMessagesSent", {"."}],
            [".", "NumberOfMessagesDeleted", {"."}]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "SQS Queue Metrics"
        }
      }
    ]
  })
}
```

---

## ✅ Checklist

- [ ] SQS queue configurada como buffer
- [ ] Lambda procesa batches de hasta 10 mensajes
- [ ] Dead Letter Queue funcional
- [ ] Archivos transformados a Parquet
- [ ] Particionado por year/month/category
- [ ] Glue Catalog actualizado automáticamente
- [ ] Queries Athena funcionando
- [ ] Alertas CloudWatch configuradas
- [ ] Archivos inválidos en quarantine

**Siguiente**: [Exercise 03 - API Gateway + Lambda](../03-api-gateway/)
