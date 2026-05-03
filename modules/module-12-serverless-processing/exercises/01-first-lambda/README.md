# Exercise 01: Primera Función Lambda

## 📋 Información General

- **Level**: Básico
- **Duration estimada**: 2-3 hours
- **Prerequisites**:
  - Module 06 (ETL Fundamentals)
  - Cuenta AWS con permisos para Lambda, S3, CloudWatch
  - Python 3.11+
  - AWS CLI configurado

## 🎯 Objectives de Aprendizaje

Al completar este exercise, serás capaz de:

1. Crear y desplegar tu primera función Lambda
2. Configurar triggers (eventos S3)
3. Trabajar con environment variables
4. Implementar logging estructurado
5. Monitorear ejecuciones con CloudWatch

---

## 📚 Context

Vas a crear una función Lambda que se dispara automáticamente cuando se sube un archivo CSV a un bucket S3. La Lambda procesará el CSV y guardará estadísticas en JSON.

**Arquitectura**:

```
┌─────────────┐
│  Usuario    │
└──────┬──────┘
       │ Upload CSV
       ▼
┌──────────────────────────────┐
│  S3 Bucket: data-landing     │
└──────────┬───────────────────┘
           │ S3 Event Notification
           ▼
┌─────────────────────────────────┐
│  Lambda: csv-processor          │
│  - Leer CSV                     │
│  - Calcular estadísticas        │
│  - Guardar JSON                 │
└──────────┬──────────────────────┘
           │ Put Object
           ▼
┌──────────────────────────────┐
│  S3 Bucket: data-processed   │
└──────────────────────────────┘
```

---

## 🔧 Parte 1: Setup Inicial

### 1.1 Crear Estructura del Proyecto

```bash
cd module-12-serverless-processing/exercises/01-first-lambda

# Crear directorios
mkdir -p src tests infrastructure

# Estructura:
# src/
#   ├── handler.py          # Lambda handler
#   ├── processor.py        # Lógica de procesamiento
#   └── requirements.txt    # Dependencias
# tests/
#   └── test_handler.py
# infrastructure/
#   └── main.tf             # Terraform
```

### 1.2 Crear Función Lambda

**`src/handler.py`**:

```python
"""
Lambda handler para procesar archivos CSV de S3
"""
import json
import logging
import os
from datetime import datetime
import boto3
import pandas as pd
from io import BytesIO

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cliente S3 (fuera del handler para reutilizar)
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler principal

    Args:
        event: Evento S3 con información del archivo subido
        context: Context de Lambda (request_id, etc.)

    Returns:
        dict: Respuesta con statusCode y body
    """

    # Log del evento completo (útil para debugging)
    logger.info(json.dumps({
        'event': 'lambda_invoked',
        'request_id': context.aws_request_id,
        'event_source': event.get('Records', [{}])[0].get('eventSource'),
        'timestamp': datetime.utcnow().isoformat()
    }))

    try:
        # Extraer información del evento S3
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']

        logger.info(json.dumps({
            'event': 'file_detected',
            'bucket': bucket,
            'key': key,
            'size_bytes': size
        }))

        # Validation: Solo procesar archivos CSV
        if not key.endswith('.csv'):
            logger.warning(f"File {key} is not CSV, skipping")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Not a CSV file, skipped'})
            }

        # Procesar archivo
        stats = process_csv_file(bucket, key)

        # Guardar estadísticas
        output_key = key.replace('.csv', '_stats.json').replace('landing/', 'processed/')
        save_stats(bucket, output_key, stats)

        logger.info(json.dumps({
            'event': 'processing_completed',
            'request_id': context.aws_request_id,
            'input_file': f's3://{bucket}/{key}',
            'output_file': f's3://{bucket}/{output_key}',
            'records_processed': stats['row_count'],
            'duration_ms': context.get_remaining_time_in_millis()
        }))

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File processed successfully',
                'input': f's3://{bucket}/{key}',
                'output': f's3://{bucket}/{output_key}',
                'stats': stats
            })
        }

    except Exception as e:
        logger.error(json.dumps({
            'event': 'processing_failed',
            'request_id': context.aws_request_id,
            'error': str(e),
            'error_type': type(e).__name__
        }))

        # Re-raise para que Lambda marque como fallida
        raise e


def process_csv_file(bucket: str, key: str) -> dict:
    """
    Descargar y procesar archivo CSV desde S3

    Args:
        bucket: Nombre del bucket S3
        key: Key del objeto en S3

    Returns:
        dict: Estadísticas del archivo
    """

    # Descargar archivo de S3
    logger.info(f"Downloading s3://{bucket}/{key}")

    response = s3.get_object(Bucket=bucket, Key=key)
    csv_content = response['Body'].read()

    # Leer CSV con pandas
    df = pd.read_csv(BytesIO(csv_content))

    # Calcular estadísticas
    stats = {
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': list(df.columns),
        'memory_usage_bytes': int(df.memory_usage(deep=True).sum()),
        'missing_values': df.isnull().sum().to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict()
    }

    # Estadísticas de columnas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        stats['numeric_stats'] = df[numeric_cols].describe().to_dict()

    return stats


def save_stats(bucket: str, key: str, stats: dict):
    """
    Guardar estadísticas en S3 como JSON

    Args:
        bucket: Nombre del bucket S3
        key: Key del objeto en S3
        stats: Diccionario con estadísticas
    """

    logger.info(f"Saving stats to s3://{bucket}/{key}")

    # Agregar metadata
    stats['processed_at'] = datetime.utcnow().isoformat()
    stats['processor'] = 'lambda-csv-processor'

    # Subir a S3
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(stats, indent=2, default=str),
        ContentType='application/json'
    )
```

**`src/requirements.txt`**:

```txt
pandas==2.1.4
boto3==1.34.0
```

---

## 🔧 Parte 2: Infrastructure as Code (Terraform)

### 2.1 Crear Infraestructura

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

# Variables
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# S3 Bucket para datos
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket-${var.environment}-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Carpetas en S3 (usando objetos vacíos)
resource "aws_s3_object" "landing_folder" {
  bucket = aws_s3_bucket.data.id
  key    = "landing/"
}

resource "aws_s3_object" "processed_folder" {
  bucket = aws_s3_bucket.data.id
  key    = "processed/"
}

# IAM Role para Lambda
resource "aws_iam_role" "lambda" {
  name = "csv-processor-lambda-role-${var.environment}"

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

# Policy: S3 access
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
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.data.arn
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "csv_processor" {
  filename      = "lambda.zip"
  function_name = "csv-processor-${var.environment}"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  # Dependencias
  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_iam_role_policy.lambda_s3
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.csv_processor.function_name}"
  retention_in_days = 7
}

# S3 Event Notification → Lambda
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.csv_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "landing/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

# Permission para S3 invocar Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.csv_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data.arn
}

# Outputs
output "bucket_name" {
  value       = aws_s3_bucket.data.id
  description = "S3 bucket name"
}

output "lambda_function_name" {
  value       = aws_lambda_function.csv_processor.function_name
  description = "Lambda function name"
}

output "lambda_arn" {
  value       = aws_lambda_function.csv_processor.arn
  description = "Lambda ARN"
}
```

---

## 🔧 Parte 3: Testing

### 3.1 Unit Tests

**`tests/test_handler.py`**:

```python
"""
Unit tests para Lambda handler
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from src.handler import lambda_handler, process_csv_file
import pandas as pd

@pytest.fixture
def s3_event():
    """Evento S3 de prueba"""
    return {
        'Records': [{
            'eventSource': 'aws:s3',
            'eventName': 'ObjectCreated:Put',
            's3': {
                'bucket': {'name': 'test-bucket'},
                'object': {
                    'key': 'landing/test.csv',
                    'size': 1024
                }
            }
        }]
    }

@pytest.fixture
def lambda_context():
    """Mock de Lambda context"""
    context = MagicMock()
    context.aws_request_id = 'test-request-123'
    context.get_remaining_time_in_millis.return_value = 30000
    return context

@pytest.fixture
def sample_csv():
    """CSV de prueba"""
    return b"""user_id,name,age,city
1,Alice,25,NYC
2,Bob,30,SF
3,Charlie,35,LA"""

@patch('src.handler.s3')
def test_lambda_handler_success(mock_s3, s3_event, lambda_context, sample_csv):
    """Test procesamiento exitoso"""

    # Mock S3 get_object
    mock_s3.get_object.return_value = {
        'Body': MagicMock(read=MagicMock(return_value=sample_csv))
    }

    # Ejecutar Lambda
    response = lambda_handler(s3_event, lambda_context)

    # Assertions
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'File processed successfully'
    assert body['stats']['row_count'] == 3
    assert body['stats']['column_count'] == 4

    # Verificar que se guardó el resultado
    mock_s3.put_object.assert_called_once()
    call_args = mock_s3.put_object.call_args
    assert call_args[1]['Bucket'] == 'test-bucket'
    assert 'processed/' in call_args[1]['Key']

@patch('src.handler.s3')
def test_lambda_handler_non_csv(mock_s3, lambda_context):
    """Test archivo no CSV (debe skipear)"""

    event = {
        'Records': [{
            'eventSource': 'aws:s3',
            's3': {
                'bucket': {'name': 'test-bucket'},
                'object': {'key': 'landing/test.txt', 'size': 100}
            }
        }]
    }

    response = lambda_handler(event, lambda_context)

    assert response['statusCode'] == 200
    assert 'skipped' in json.loads(response['body'])['message'].lower()

    # No debe llamar a S3
    mock_s3.get_object.assert_not_called()

@patch('src.handler.s3')
def test_process_csv_file(mock_s3, sample_csv):
    """Test procesamiento de CSV"""

    mock_s3.get_object.return_value = {
        'Body': MagicMock(read=MagicMock(return_value=sample_csv))
    }

    stats = process_csv_file('test-bucket', 'test.csv')

    assert stats['row_count'] == 3
    assert stats['column_count'] == 4
    assert 'user_id' in stats['columns']
    assert 'age' in stats['numeric_stats']
```

### 3.2 Ejecutar Tests

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov moto

# Ejecutar tests
pytest tests/ -v --cov=src

# Ver cobertura HTML
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🚀 Parte 4: Deployment

### 4.1 Empaquetar Lambda

```bash
# Script para crear deployment package
cd src/

# Instalar dependencias en directorio local
pip install -r requirements.txt -t package/

# Copiar código
cp handler.py package/
cp processor.py package/

# Crear ZIP
cd package/
zip -r ../lambda.zip .
cd ..

# Mover ZIP a infrastructure/
mv lambda.zip ../infrastructure/
```

**`infrastructure/deploy.sh`** (automatizar):

```bash
#!/bin/bash
set -e

echo "🔧 Building Lambda deployment package..."

cd ../src

# Limpiar build anterior
rm -rf package/
mkdir package/

# Instalar dependencias
pip install -r requirements.txt -t package/ --platform manylinux2014_x86_64 --only-binary=:all:

# Copiar código
cp *.py package/

# Crear ZIP
cd package/
zip -r ../../infrastructure/lambda.zip .
cd ..

echo "✅ Lambda package created: infrastructure/lambda.zip"

cd ../infrastructure

echo "🚀 Deploying infrastructure..."

# Terraform
terraform init
terraform plan
terraform apply -auto-approve

echo "✅ Deployment completed!"
```

### 4.2 Deploy con Terraform

```bash
cd infrastructure/

# Inicializar
terraform init

# Plan
terraform plan

# Apply
terraform apply

# Obtener outputs
terraform output bucket_name
terraform output lambda_function_name
```

---

## 🧪 Parte 5: Testing en AWS

### 5.1 Crear CSV de Prueba

```bash
# Obtener nombre del bucket
BUCKET=$(terraform output -raw bucket_name)

# Crear CSV de prueba
cat > test_data.csv << EOF
user_id,name,age,city,signup_date
1,Alice Johnson,28,New York,2024-01-15
2,Bob Smith,35,San Francisco,2024-01-16
3,Charlie Brown,42,Los Angeles,2024-01-17
4,Diana Prince,31,Chicago,2024-01-18
5,Eve Adams,29,Boston,2024-01-19
EOF

# Upload a S3
aws s3 cp test_data.csv s3://$BUCKET/landing/

# Verificar Lambda fue invocada
aws logs tail /aws/lambda/csv-processor-dev --follow
```

### 5.2 Verificar Resultado

```bash
# Listar archivos procesados
aws s3 ls s3://$BUCKET/processed/

# Descargar estadísticas
aws s3 cp s3://$BUCKET/processed/test_data_stats.json .

# Ver contenido
cat test_data_stats.json | jq .
```

**Expected output**:

```json
{
  "row_count": 5,
  "column_count": 5,
  "columns": ["user_id", "name", "age", "city", "signup_date"],
  "memory_usage_bytes": 450,
  "missing_values": {
    "user_id": 0,
    "name": 0,
    "age": 0,
    "city": 0,
    "signup_date": 0
  },
  "dtypes": {
    "user_id": "int64",
    "name": "object",
    "age": "int64",
    "city": "object",
    "signup_date": "object"
  },
  "numeric_stats": {
    "user_id": {
      "mean": 3.0,
      "std": 1.58,
      "min": 1.0,
      "max": 5.0
    },
    "age": {
      "mean": 33.0,
      "std": 5.89,
      "min": 28.0,
      "max": 42.0
    }
  },
  "processed_at": "2024-03-07T10:30:00.123456",
  "processor": "lambda-csv-processor"
}
```

---

## 📊 Parte 6: Monitoring

### 6.1 CloudWatch Logs Insights

Query para analizar logs:

```sql
-- Ver todos los eventos
fields @timestamp, @message
| sort @timestamp desc
| limit 20

-- Calcular duración promedio
fields duration_ms
| stats avg(duration_ms) as avg_duration,
        max(duration_ms) as max_duration,
        count() as invocations

-- Encontrar errores
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
```

### 6.2 CloudWatch Metrics

Ver métricas de Lambda:

```bash
# Invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=csv-processor-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=csv-processor-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

---

## 🎓 Desafíos Adicionales

### Level 1: Básico

1. **Agregar validation de schema**: Validar que CSV tenga columnas requeridas
2. **Manejo de errores mejorado**: Mover archivos inválidos a carpeta `quarantine/`
3. **Custom metrics**: Publicar métricas custom a CloudWatch

### Level 2: Intermedio

4. **Procesamiento por chunks**: Manejar archivos grandes (>100 MB)
5. **Dead Letter Queue**: Configurar DLQ para invocaciones fallidas
6. **Lambda Layers**: Crear Layer con pandas para reutilizar en otras Lambdas

### Level 3: Avanzado

7. **X-Ray tracing**: Habilitar tracing y agregar subsegments
8. **VPC integration**: Mover Lambda a VPC privada
9. **Reserved concurrency**: Configurar concurrency limits

---

## 🧹 Cleanup

```bash
# Eliminar infraestructura
cd infrastructure/
terraform destroy -auto-approve

# Limpiar archivos locales
cd ..
rm -rf src/package/
rm infrastructure/lambda.zip
```

---

## ✅ Checklist de Completación

- [ ] Lambda function creada y desplegada
- [ ] S3 bucket configurado con event notifications
- [ ] IAM roles con permisos mínimos
- [ ] Unit tests pasando (>80% coverage)
- [ ] CSV de prueba procesado exitosamente
- [ ] Logs estructurados en CloudWatch
- [ ] Métricas visibles en CloudWatch
- [ ] Infraestructura como código (Terraform)
- [ ] Documentation completa

---

## 📚 Recursos

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

**Siguiente**: [Exercise 02 - S3 Event Processing](../02-s3-event-processing/) - Procesamiento avanzado de eventos S3
