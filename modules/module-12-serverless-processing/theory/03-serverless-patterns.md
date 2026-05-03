# Patrones Serverless Avanzados y Producción

## 📋 Tabla de Contenidos

1. [Patrones de Arquitectura](#patrones-de-arquitectura)
2. [API Gateway + Lambda](#api-gateway--lambda)
3. [Seguridad en Serverless](#seguridad-en-serverless)
4. [Observabilidad y Monitoring](#observabilidad-y-monitoring)
5. [CI/CD para Serverless](#cicd-para-serverless)
6. [Cost Optimization](#cost-optimization)

---

## Patrones de Arquitectura

### Pattern 1: API Backend

**Arquitectura clásica**: REST API serverless

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ HTTPS
       ▼
┌──────────────────────────────────┐
│  Amazon API Gateway              │
│  - Rate limiting                 │
│  - Authentication (Cognito)      │
│  - Request validation            │
└────────┬─────────────────────────┘
         │
    ┌────┴─────┬───────┬────────┐
    ▼          ▼       ▼        ▼
┌────────┐ ┌────────┐ ┌──────┐ ┌──────┐
│Lambda  │ │Lambda  │ │Lambda│ │Lambda│
│GET     │ │POST    │ │PUT   │ │DELETE│
└────┬───┘ └────┬───┘ └───┬──┘ └───┬──┘
     │          │         │        │
     └──────────┴─────────┴────────┘
                │
         ┌──────▼──────┐
         │  DynamoDB   │
         └─────────────┘
```

**Implementación**:

```python
# handler.py
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def get_user(event, context):
    """GET /users/{id}"""
    user_id = event['pathParameters']['id']

    response = table.get_item(Key={'user_id': user_id})

    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'User not found'})
        }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response['Item'], default=str)
    }

def create_user(event, context):
    """POST /users"""
    body = json.loads(event['body'])

    # Validation
    if 'email' not in body or 'name' not in body:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required fields'})
        }

    # Crear usuario
    item = {
        'user_id': str(uuid.uuid4()),
        'email': body['email'],
        'name': body['name'],
        'created_at': datetime.utcnow().isoformat()
    }

    table.put_item(Item=item)

    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(item)
    }

def list_users(event, context):
    """GET /users"""
    # Query parameters
    limit = int(event['queryStringParameters'].get('limit', 10))

    response = table.scan(Limit=limit)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'items': response['Items'],
            'count': len(response['Items'])
        }, default=str)
    }
```

### Pattern 2: Data Lake Ingestion

**Arquitectura**: Ingestión automática a Data Lake

```
┌─────────────┐
│ Data Source │ (CSV, JSON, logs)
└──────┬──────┘
       │ Upload
       ▼
┌──────────────────────────────────┐
│  S3 Landing Zone                 │
│  s3://lake/landing/              │
└────────┬─────────────────────────┘
         │ S3 Event
         ▼
┌─────────────────────────────────┐
│  Lambda: Validator               │
│  - Schema validation             │
│  - Quality checks                │
└────────┬────────────────────────┘
         │
    ┌────┴─────┐ (válido)
    ▼          ▼ (inválido)
┌────────┐  ┌─────────────┐
│Lambda  │  │  S3 Quarantine│
│Process │  └─────────────┘
└────┬───┘
     │
     ▼
┌──────────────────────────────────┐
│  S3 Processed Zone               │
│  s3://lake/processed/            │
│  (Parquet, partitioned)          │
└────────┬─────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Glue Crawler                    │
│  (Update Data Catalog)           │
└─────────────────────────────────┘
```

**Implementación: Validator Lambda**

```python
import boto3
import json
import pandas as pd
from io import BytesIO
import jsonschema

s3 = boto3.client('s3')
sns = boto3.client('sns')

# Schema de validation
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150}
    },
    "required": ["user_id", "email"]
}

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    print(f"Validating s3://{bucket}/{key}")

    # Descargar archivo
    obj = s3.get_object(Bucket=bucket, Key=key)

    if key.endswith('.csv'):
        df = pd.read_csv(BytesIO(obj['Body'].read()))
    elif key.endswith('.json'):
        data = json.loads(obj['Body'].read())
        df = pd.DataFrame(data)
    else:
        move_to_quarantine(bucket, key, 'Unsupported format')
        return

    # Validaciones
    validation_errors = []

    # 1. Schema validation
    try:
        for record in df.to_dict('records'):
            jsonschema.validate(record, USER_SCHEMA)
    except jsonschema.ValidationError as e:
        validation_errors.append(f"Schema error: {e.message}")

    # 2. Quality checks
    if df['email'].isna().any():
        validation_errors.append("Null emails found")

    if df.duplicated(subset=['user_id']).any():
        validation_errors.append("Duplicate user IDs found")

    # Resultado
    if validation_errors:
        move_to_quarantine(bucket, key, validation_errors)
    else:
        process_valid_file(bucket, key, df)

def move_to_quarantine(bucket, key, errors):
    """Mover archivo inválido a quarantine"""
    quarantine_key = key.replace('landing/', 'quarantine/')

    s3.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': bucket, 'Key': key},
        Key=quarantine_key
    )

    s3.delete_object(Bucket=bucket, Key=key)

    # Notificar error
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123:data-quality-alerts',
        Subject='Data Validation Failed',
        Message=f"File: {key}\nErrors: {errors}"
    )

def process_valid_file(bucket, key, df):
    """Procesar archivo válido"""
    # Transformar a Parquet con particiones
    df['ingestion_date'] = pd.Timestamp.now().date()

    # Partition por fecha
    for date, group in df.groupby('ingestion_date'):
        output_key = f"processed/date={date}/data.parquet"

        parquet_buffer = BytesIO()
        group.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy')

        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=parquet_buffer.getvalue()
        )

    # Eliminar archivo original
    s3.delete_object(Bucket=bucket, Key=key)
```

### Pattern 3: Event Sourcing

**Concepto**: Todos los cambios se almacenan como eventos inmutables.

```
API Request → Lambda → Event Store (DynamoDB/S3)
                           ↓
                    EventBridge Stream
                           ↓
                ┌──────────┴───────────┐
                ▼                      ▼
          [Lambda 1]              [Lambda 2]
        Update Read Model      Generate Report
```

**Implementación**:

```python
import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
events_table = dynamodb.Table('events')
eventbridge = boto3.client('events')

def lambda_handler(event, context):
    """Guardar evento y publicar a EventBridge"""

    # 1. Guardar evento en Event Store (DynamoDB)
    event_record = {
        'event_id': str(uuid.uuid4()),
        'event_type': 'UserCreated',
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'user_id': event['user_id'],
            'email': event['email'],
            'name': event['name']
        },
        'metadata': {
            'source': 'api',
            'version': '1.0'
        }
    }

    events_table.put_item(Item=event_record)

    # 2. Publicar a EventBridge
    eventbridge.put_events(
        Entries=[{
            'Source': 'user.service',
            'DetailType': 'UserCreated',
            'Detail': json.dumps(event_record),
            'EventBusName': 'default'
        }]
    )

    return {'statusCode': 200, 'event_id': event_record['event_id']}

# Lambda consumidor 1: Actualizar read model
def update_read_model(event, context):
    detail = event['detail']

    # Proyección: Tabla de usuarios (denormalizada para lectura rápida)
    users_table = dynamodb.Table('users_read_model')

    users_table.put_item(Item={
        'user_id': detail['data']['user_id'],
        'email': detail['data']['email'],
        'name': detail['data']['name'],
        'created_at': detail['timestamp']
    })

# Lambda consumidor 2: Generar reporte
def generate_report(event, context):
    detail = event['detail']

    # Enviar email de bienvenida
    ses = boto3.client('ses')
    ses.send_email(
        Source='no-reply@example.com',
        Destination={'ToAddresses': [detail['data']['email']]},
        Message={
            'Subject': {'Data': 'Welcome!'},
            'Body': {'Text': {'Data': f"Hello {detail['data']['name']}!"}}
        }
    )
```

---

## API Gateway + Lambda

### REST API

**Tipos de integraciones**:

1. **Lambda Proxy** (recomendado): API Gateway pasa evento completo a Lambda

```python
def lambda_handler(event, context):
    # Acceso a todo el request
    method = event['httpMethod']  # GET, POST, etc.
    path = event['path']  # /users/123
    headers = event['headers']
    body = json.loads(event['body']) if event['body'] else {}
    query = event['queryStringParameters'] or {}

    # Respuesta debe incluir statusCode, headers, body
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # CORS
        },
        'body': json.dumps({'message': 'Success'})
    }
```

2. **Lambda Custom**: API Gateway transforma request/response

### HTTP API vs REST API

| Característica | HTTP API | REST API |
|----------------|----------|----------|
| **Costo** | ~70% más barato | Más caro |
| **Performance** | Mejor latencia | Latencia OK |
| **Features** | Básicas | Avanzadas (caching, throttling) |
| **Use case** | APIs simples | APIs complejas enterprise |

### Authentication

#### 1. API Key (básico)

```python
# API Gateway valida x-api-key header
# Lambda recibe request solo si API key es válida
def lambda_handler(event, context):
    # No necesitas validar, API Gateway ya lo hizo
    return {'statusCode': 200, 'body': 'Authenticated'}
```

#### 2. IAM (AWS credentials)

```python
import boto3
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth

# Cliente necesita firmar request con AWS credentials
auth = AWSRequestsAuth(
    aws_access_key='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET',
    aws_host='api123.execute-api.us-east-1.amazonaws.com',
    aws_region='us-east-1',
    aws_service='execute-api'
)

response = requests.get(
    'https://api123.execute-api.us-east-1.amazonaws.com/prod/users',
    auth=auth
)
```

#### 3. Cognito (OAuth 2.0 / JWT)

```python
# API Gateway valida JWT token de Cognito
def lambda_handler(event, context):
    # Usuario identificado en event['requestContext']['authorizer']['claims']
    claims = event['requestContext']['authorizer']['claims']
    user_id = claims['sub']
    email = claims['email']

    print(f"User {email} ({user_id}) made request")

    return {'statusCode': 200, 'body': f'Hello {email}'}
```

#### 4. Lambda Authorizer (custom)

```python
# Lambda Authorizer
def authorizer_handler(event, context):
    token = event['authorizationToken']  # "Bearer abc123"

    # Validar token (ej: JWT, consultar DB, etc.)
    if validate_token(token):
        principal_id = 'user123'

        # Generar IAM policy
        return {
            'principalId': principal_id,
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow',
                    'Resource': event['methodArn']
                }]
            },
            'context': {
                'user_id': principal_id,
                'role': 'admin'
            }
        }
    else:
        raise Exception('Unauthorized')

# Lambda backend
def handler(event, context):
    # Acceder a context del authorizer
    user_id = event['requestContext']['authorizer']['user_id']
    role = event['requestContext']['authorizer']['role']

    return {'statusCode': 200, 'body': f'Hello {user_id} ({role})'}
```

### Request Validation

**API Gateway puede validar request antes de invocar Lambda**:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "CreateUserRequest",
  "type": "object",
  "properties": {
    "email": {
      "type": "string",
      "format": "email"
    },
    "age": {
      "type": "integer",
      "minimum": 0,
      "maximum": 150
    }
  },
  "required": ["email"]
}
```

Si request no cumple schema, API Gateway retorna 400 sin invocar Lambda (ahorro de costos).

### Rate Limiting

```hcl
# Terraform: API Gateway usage plan
resource "aws_api_gateway_usage_plan" "main" {
  name = "basic-plan"

  throttle_settings {
    burst_limit = 100   # Máximo burst
    rate_limit  = 50    # Requests por segundo
  }

  quota_settings {
    limit  = 10000      # Requests por periodo
    period = "DAY"
  }
}
```

---

## Seguridad en Serverless

### Principio de Least Privilege

**❌ BAD**: Lambda con permisos amplios

```json
{
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "*"
}
```

**✅ GOOD**: Lambda con permisos mínimos

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": [
    "arn:aws:s3:::my-bucket/processed/*"
  ]
}
```

### Secrets Management

**❌ BAD**: Credenciales en environment variables

```python
os.environ['DB_PASSWORD'] = 'mypassword123'  # ⚠️ Visible en console
```

**✅ GOOD**: AWS Secrets Manager

```python
import boto3
import json
from functools import lru_cache

@lru_cache(maxsize=1)  # Cache secret (no obtener en cada invocación)
def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def lambda_handler(event, context):
    db_creds = get_secret('prod/db/credentials')

    conn = psycopg2.connect(
        host=db_creds['host'],
        user=db_creds['username'],
        password=db_creds['password']
    )
```

**Terraform**:

```hcl
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "prod/db/credentials"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    host     = aws_db_instance.main.address
    username = "admin"
    password = random_password.db_password.result
  })
}

# Lambda con permisos para leer secret
resource "aws_iam_role_policy" "lambda_secrets" {
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = aws_secretsmanager_secret.db_credentials.arn
    }]
  })
}
```

### Encryption

**At Rest**:
- S3: Server-Side Encryption (SSE-S3, SSE-KMS)
- DynamoDB: Encryption at rest con KMS
- Lambda env vars: Cifradas con KMS

**In Transit**:
- API Gateway: HTTPS obligatorio
- Lambda → AWS services: TLS por defecto

```python
# Cifrar datos antes de guardar en S3
import boto3
from cryptography.fernet import Fernet

kms = boto3.client('kms')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Obtener data key de KMS
    response = kms.generate_data_key(
        KeyId='arn:aws:kms:us-east-1:123:key/abc-123',
        KeySpec='AES_256'
    )

    plaintext_key = response['Plaintext']
    encrypted_key = response['CiphertextBlob']

    # Cifrar data con data key
    cipher = Fernet(plaintext_key)
    encrypted_data = cipher.encrypt(b'sensitive data')

    # Guardar encrypted_data + encrypted_key
    s3.put_object(
        Bucket='my-bucket',
        Key='encrypted/data.bin',
        Body=encrypted_data,
        Metadata={'encrypted-key': encrypted_key.hex()}
    )
```

### VPC Security

**Lambda en VPC privada** (acceso a RDS, ElastiCache):

```hcl
resource "aws_lambda_function" "processor" {
  function_name = "data-processor"

  # VPC Configuration
  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }
}

resource "aws_security_group" "lambda" {
  vpc_id = aws_vpc.main.id

  # Permitir salida a RDS
  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.rds.id]
  }
}

resource "aws_security_group" "rds" {
  vpc_id = aws_vpc.main.id

  # Permitir entrada desde Lambda
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}
```

---

## Observabilidad y Monitoring

### CloudWatch Logs

**Structured Logging** (JSON):

```python
import json
import logging

# Configurar logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Log estructurado
    logger.info(json.dumps({
        'event': 'processing_started',
        'request_id': context.aws_request_id,
        'file_key': event['key'],
        'timestamp': datetime.utcnow().isoformat()
    }))

    try:
        result = process_file(event['key'])

        logger.info(json.dumps({
            'event': 'processing_completed',
            'request_id': context.aws_request_id,
            'records_processed': len(result),
            'duration_ms': context.get_remaining_time_in_millis()
        }))

    except Exception as e:
        logger.error(json.dumps({
            'event': 'processing_failed',
            'request_id': context.aws_request_id,
            'error': str(e),
            'traceback': traceback.format_exc()
        }))
        raise
```

**CloudWatch Logs Insights** (query logs):

```sql
-- Encontrar errores en las últimas 24 hours
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50

-- Calcular P50, P90, P99 de duration
fields duration_ms
| stats percentile(duration_ms, 50) as p50,
        percentile(duration_ms, 90) as p90,
        percentile(duration_ms, 99) as p99

-- Top 10 archivos más procesados
fields file_key
| stats count() as count by file_key
| sort count desc
| limit 10
```

### CloudWatch Metrics

**Custom Metrics**:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    records_processed = process_data(event)

    # Publicar métrica
    cloudwatch.put_metric_data(
        Namespace='DataPipeline',
        MetricData=[
            {
                'MetricName': 'RecordsProcessed',
                'Value': records_processed,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': 'production'},
                    {'Name': 'Pipeline', 'Value': 'user-data'}
                ]
            },
            {
                'MetricName': 'ProcessingDuration',
                'Value': get_duration(),
                'Unit': 'Milliseconds'
            }
        ]
    )
```

**Alarmas**:

```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "lambda-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 10

  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "lambda-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5

  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### X-Ray Tracing

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Instrumentar bibliotecas (boto3, requests, etc.)
patch_all()

def lambda_handler(event, context):
    # Subsegmento para S3 download
    with xray_recorder.in_subsegment('download_from_s3') as subsegment:
        data = s3.get_object(Bucket=bucket, Key=key)
        subsegment.put_annotation('bucket', bucket)
        subsegment.put_annotation('key', key)

    # Subsegmento para processing
    with xray_recorder.in_subsegment('process_data') as subsegment:
        result = process(data)
        subsegment.put_metadata('record_count', len(result))

    return result
```

**Terraform: Habilitar X-Ray**:

```hcl
resource "aws_lambda_function" "processor" {
  function_name = "processor"

  tracing_config {
    mode = "Active"  # Enable X-Ray
  }
}

resource "aws_iam_role_policy_attachment" "xray" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
```

---

## CI/CD para Serverless

### Pattern: Infrastructure as Code + CI/CD

```
Git Push → GitHub Actions → Tests → Deploy Lambda + API Gateway
```

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-serverless.yml
name: Deploy Serverless

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov moto

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src

      - name: Run integration tests
        run: pytest tests/integration/ -v

  deploy-staging:
    needs: test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to Staging
        run: |
          cd infrastructure
          terraform init
          terraform workspace select staging
          terraform apply -auto-approve

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to Production
        run: |
          cd infrastructure
          terraform init
          terraform workspace select production
          terraform apply -auto-approve

      - name: Run smoke tests
        run: |
          python scripts/smoke-tests.py
```

### AWS SAM (Serverless Application Model)

**template.yaml**:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.11
    Timeout: 30
    MemorySize: 512
    Environment:
      Variables:
        TABLE_NAME: !Ref UsersTable

Resources:
  # Lambda Function
  GetUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: handlers.get_user
      Events:
        GetUser:
          Type: Api
          Properties:
            Path: /users/{id}
            Method: get
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref UsersTable

  CreateUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: handlers.create_user
      Events:
        CreateUser:
          Type: Api
          Properties:
            Path: /users
            Method: post
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable

  # DynamoDB Table
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: users
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: user_id
          AttributeType: S
      KeySchema:
        - AttributeName: user_id
          KeyType: HASH

Outputs:
  ApiUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

**Deploy**:

```bash
# Build
sam build

# Deploy to staging
sam deploy --stack-name my-app-staging --parameter-overrides Environment=staging

# Deploy to production
sam deploy --stack-name my-app-prod --parameter-overrides Environment=production
```

---

## Cost Optimization

### 1. Right-sizing Memory

**Lambda pricing**: Pago por GB-segundo. Más RAM = más CPU = más rápido.

```python
# Test con diferentes configuraciones
# 512 MB: 1000ms = 512 MB-s = $0.000008333
# 1024 MB: 600ms = 614 MB-s = $0.00001023 (MÁS RÁPIDO Y MÁS BARATO!)
```

**Tool**: AWS Lambda Power Tuning - encuentra configuration óptima.

### 2. Reserved Concurrency

**Problema**: Límite de 1000 concurrent executions compartido entre todas las Lambdas.

**Solution**: Reserved concurrency para funciones críticas.

```hcl
resource "aws_lambda_function" "critical" {
  function_name = "critical-function"

  # Reservar 100 concurrent executions
  reserved_concurrent_executions = 100
}
```

### 3. Provisioned Concurrency (eliminar cold starts)

**Problema**: Cold start de 1-5 segundos inaceptable.

**Solution**: Mantener X instancias "warm" ($$$ más caro).

```hcl
resource "aws_lambda_provisioned_concurrency_config" "warm" {
  function_name = aws_lambda_function.api.function_name

  # Mantener 5 instancias siempre warm
  provisioned_concurrent_executions = 5
}
```

**Costo**: ~$0.015 por GB-hora (vs $0.0000166667 por GB-segundo on-demand).

### 4. S3 Intelligent-Tiering

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    transition {
      days          = 0
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "archive-old-data"
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
```

### 5. DynamoDB On-Demand vs Provisioned

**On-Demand**: Paga por request (bueno para tráfico impredecible)
**Provisioned**: Paga por capacidad reservada (más barato si tráfico constante)

```hcl
resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"  # On-demand

  # O provisioned:
  # billing_mode   = "PROVISIONED"
  # read_capacity  = 5
  # write_capacity = 5
}
```

---

## Resumen

- **Patrones**: API Backend, Data Lake Ingestion, Event Sourcing
- **API Gateway**: REST API serverless con authentication y rate limiting
- **Seguridad**: Least privilege, Secrets Manager, encryption
- **Observabilidad**: CloudWatch Logs/Metrics, X-Ray tracing
- **CI/CD**: GitHub Actions + Terraform/SAM
- **Cost Optimization**: Right-sizing, reserved concurrency, intelligent tiering

**Próximo**: [Exercises prácticos](../exercises/) - Implementar patrones serverless
