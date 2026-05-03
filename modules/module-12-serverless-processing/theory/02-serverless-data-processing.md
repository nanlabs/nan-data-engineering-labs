# Procesamiento de Datos con Serverless

## 📋 Tabla de Contenidos

1. [Arquitecturas Serverless para Datos](#arquitecturas-serverless-para-datos)
2. [Lambda + S3: File Processing](#lambda--s3-file-processing)
3. [AWS Step Functions](#aws-step-functions)
4. [Event-Driven Data Pipelines](#event-driven-data-pipelines)
5. [Serverless ETL Patterns](#serverless-etl-patterns)
6. [Integración con AWS Glue](#integración-con-aws-glue)

---

## Arquitecturas Serverless para Datos

### Patrón 1: Event-Driven ETL

```
S3 Upload → Lambda (Transform) → S3 (Processed)
                ↓
           DynamoDB (Metadata)
```

**Caso de uso**: Transformar archivos CSV a Parquet al subirlos a S3.

```python
import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Evento S3
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Descargar CSV
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(BytesIO(obj['Body'].read()))

    # Transformar
    df['processed_at'] = pd.Timestamp.now()
    df['source_file'] = key

    # Guardar como Parquet
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy')

    output_key = key.replace('.csv', '.parquet').replace('raw/', 'processed/')
    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=parquet_buffer.getvalue()
    )

    return {'output': f's3://{bucket}/{output_key}'}
```

### Patrón 2: Fan-Out Processing

```
S3 Upload → SNS Topic
              ├→ Lambda 1 (Validation)
              ├→ Lambda 2 (Transform)
              └→ Lambda 3 (Metadata extraction)
```

**Caso de uso**: Procesar un archivo en paralelo (validation, transformación, metadata).

```python
# Lambda Publisher (disparada por S3)
def lambda_handler(event, context):
    sns = boto3.client('sns')

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Publicar mensaje a SNS
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789012:FileProcessing',
        Subject='New file uploaded',
        Message=json.dumps({
            'bucket': bucket,
            'key': key,
            'timestamp': datetime.utcnow().isoformat()
        })
    )

# Lambda Subscriber 1: Validation
def validate_file(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    # Validar archivo...

# Lambda Subscriber 2: Transform
def transform_file(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    # Transformar archivo...

# Lambda Subscriber 3: Metadata
def extract_metadata(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    # Extraer metadata...
```

### Patrón 3: Stream Processing

```
Kinesis Stream → Lambda (Process) → S3/DynamoDB
                     ↓
           CloudWatch Metrics
```

**Caso de uso**: Procesar logs en tiempo real.

```python
import base64

def lambda_handler(event, context):
    for record in event['Records']:
        # Decodificar data de Kinesis
        payload = base64.b64decode(record['kinesis']['data'])
        log_entry = json.loads(payload)

        # Procesar log
        if log_entry['level'] == 'ERROR':
            send_alert(log_entry)

        # Agregar métricas
        update_metrics(log_entry)
```

---

## Lambda + S3: File Processing

### Batch Processing con Pandas

**Problema**: Archivos grandes (>500 MB) no caben en memoria Lambda.

**Solution**: Procesamiento en chunks.

```python
import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']

    # Obtener tamaño del archivo
    head = s3.head_object(Bucket=bucket, Key=key)
    file_size = head['ContentLength']

    chunk_size = 50 * 1024 * 1024  # 50 MB chunks
    num_chunks = (file_size // chunk_size) + 1

    results = []

    for i in range(num_chunks):
        # Descargar chunk con Range request
        start_byte = i * chunk_size
        end_byte = min(start_byte + chunk_size - 1, file_size - 1)

        response = s3.get_object(
            Bucket=bucket,
            Key=key,
            Range=f'bytes={start_byte}-{end_byte}'
        )

        # Procesar chunk
        chunk_data = response['Body'].read()
        df_chunk = pd.read_csv(BytesIO(chunk_data))

        # Agregación
        result = df_chunk.groupby('category')['amount'].sum()
        results.append(result)

    # Combinar resultados
    final_result = pd.concat(results).groupby(level=0).sum()

    return {'status': 'success', 'results': final_result.to_dict()}
```

### S3 Select: SQL en Archivos

**AWS S3 Select** permite query directo en S3 sin descargar todo el archivo.

```python
def lambda_handler(event, context):
    s3 = boto3.client('s3')

    # Query SQL en CSV
    response = s3.select_object_content(
        Bucket='my-bucket',
        Key='data.csv',
        ExpressionType='SQL',
        Expression="""
            SELECT customer_id, amount
            FROM s3object s
            WHERE amount > 1000
        """,
        InputSerialization={
            'CSV': {'FileHeaderInfo': 'USE'},
            'CompressionType': 'NONE'
        },
        OutputSerialization={'CSV': {}}
    )

    # Procesar stream
    results = []
    for event in response['Payload']:
        if 'Records' in event:
            data = event['Records']['Payload'].decode('utf-8')
            results.append(data)

    return ''.join(results)
```

**Ventajas S3 Select**:
- ✅ 80% menos datos transferidos
- ✅ 400% más rápido que descargar archivo completo
- ✅ Soporta CSV, JSON, Parquet

### Presigned URLs

Generar URLs temporales para upload/download sin credenciales AWS.

```python
def lambda_handler(event, context):
    s3 = boto3.client('s3')

    # Presigned URL para UPLOAD (usuario puede subir archivo)
    upload_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': 'my-bucket',
            'Key': 'uploads/file.csv',
            'ContentType': 'text/csv'
        },
        ExpiresIn=3600  # Válido por 1 hora
    )

    # Presigned URL para DOWNLOAD
    download_url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'my-bucket',
            'Key': 'reports/report.pdf'
        },
        ExpiresIn=300  # Válido por 5 minutes
    )

    return {
        'upload_url': upload_url,
        'download_url': download_url
    }
```

---

## AWS Step Functions

### ¿Qué es Step Functions?

**AWS Step Functions** es un servicio de orquestación serverless para coordinar múltiples Lambdas y servicios AWS.

**Analogía**: Es el "director de orquesta" que coordina cuándo cada Lambda debe ejecutarse.

### State Machine

Definido en **Amazon States Language (ASL)** - JSON que describe el workflow.

```json
{
  "Comment": "ETL Pipeline",
  "StartAt": "ExtractData",
  "States": {
    "ExtractData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:extract",
      "Next": "TransformData"
    },
    "TransformData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:transform",
      "Next": "LoadData"
    },
    "LoadData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:load",
      "End": true
    }
  }
}
```

### Tipos de States

#### 1. Task (Ejecutar Lambda)

```json
{
  "ValidateData": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:us-east-1:123:function:validate",
    "ResultPath": "$.validation",
    "Next": "CheckValidation"
  }
}
```

#### 2. Choice (Condicional)

```json
{
  "CheckValidation": {
    "Type": "Choice",
    "Choices": [
      {
        "Variable": "$.validation.is_valid",
        "BooleanEquals": true,
        "Next": "ProcessData"
      },
      {
        "Variable": "$.validation.is_valid",
        "BooleanEquals": false,
        "Next": "SendAlert"
      }
    ]
  }
}
```

#### 3. Parallel (Ejecutar en paralelo)

```json
{
  "ParallelProcessing": {
    "Type": "Parallel",
    "Branches": [
      {
        "StartAt": "Process1",
        "States": {
          "Process1": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123:function:process1",
            "End": true
          }
        }
      },
      {
        "StartAt": "Process2",
        "States": {
          "Process2": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123:function:process2",
            "End": true
          }
        }
      }
    ],
    "Next": "Aggregate"
  }
}
```

#### 4. Map (Iterar sobre array)

```json
{
  "ProcessFiles": {
    "Type": "Map",
    "ItemsPath": "$.files",
    "MaxConcurrency": 10,
    "Iterator": {
      "StartAt": "ProcessFile",
      "States": {
        "ProcessFile": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:us-east-1:123:function:process-file",
          "End": true
        }
      }
    },
    "End": true
  }
}
```

#### 5. Wait (Esperar)

```json
{
  "Wait10Seconds": {
    "Type": "Wait",
    "Seconds": 10,
    "Next": "RetryTask"
  }
}
```

### ETL Pipeline Completo con Step Functions

```json
{
  "Comment": "Complete ETL Pipeline",
  "StartAt": "ExtractFromSource",
  "States": {
    "ExtractFromSource": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:extract",
      "ResultPath": "$.extract_result",
      "Retry": [{
        "ErrorEquals": ["States.ALL"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2
      }],
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "ExtractFailed"
      }],
      "Next": "ValidateData"
    },

    "ValidateData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:validate",
      "ResultPath": "$.validation",
      "Next": "IsDataValid"
    },

    "IsDataValid": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.validation.is_valid",
        "BooleanEquals": true,
        "Next": "ParallelTransform"
      }],
      "Default": "ValidationFailed"
    },

    "ParallelTransform": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "TransformCustomers",
          "States": {
            "TransformCustomers": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:us-east-1:123:function:transform-customers",
              "End": true
            }
          }
        },
        {
          "StartAt": "TransformOrders",
          "States": {
            "TransformOrders": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:us-east-1:123:function:transform-orders",
              "End": true
            }
          }
        }
      ],
      "ResultPath": "$.transform_results",
      "Next": "LoadToWarehouse"
    },

    "LoadToWarehouse": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:load",
      "Next": "GenerateReport"
    },

    "GenerateReport": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:generate-report",
      "End": true
    },

    "ExtractFailed": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:send-alert",
      "End": true
    },

    "ValidationFailed": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:handle-invalid-data",
      "End": true
    }
  }
}
```

### Integración con Lambda

**Lambda para iniciar Step Function**:

```python
import boto3
import json

sfn = boto3.client('stepfunctions')

def lambda_handler(event, context):
    # Input para la state machine
    input_data = {
        'source': 's3://my-bucket/data.csv',
        'destination': 's3://my-warehouse/processed/',
        'timestamp': datetime.utcnow().isoformat()
    }

    # Iniciar ejecución
    response = sfn.start_execution(
        stateMachineArn='arn:aws:states:us-east-1:123:stateMachine:MyETL',
        name=f'execution-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
        input=json.dumps(input_data)
    )

    return {
        'executionArn': response['executionArn'],
        'startDate': response['startDate'].isoformat()
    }
```

**Lambda dentro de Step Function**:

```python
def lambda_handler(event, context):
    # event contiene el output del state anterior
    source = event['source']
    validation = event.get('validation', {})

    # Procesar
    result = transform_data(source)

    # Return será el input del siguiente state
    return {
        'transformed_data': result,
        'record_count': len(result),
        'status': 'success'
    }
```

---

## Event-Driven Data Pipelines

### EventBridge + Lambda

**EventBridge** es un event bus serverless para conectar aplicaciones.

```python
# Lambda que publica custom event
def lambda_handler(event, context):
    eventbridge = boto3.client('events')

    eventbridge.put_events(
        Entries=[{
            'Source': 'my.data.pipeline',
            'DetailType': 'Data Processing Completed',
            'Detail': json.dumps({
                'file': 's3://bucket/file.csv',
                'records_processed': 1000,
                'status': 'success'
            }),
            'EventBusName': 'default'
        }]
    )
```

**EventBridge Rule** (Terraform):

```hcl
resource "aws_cloudwatch_event_rule" "data_processed" {
  name        = "data-processing-completed"
  description = "Triggers when data processing completes"

  event_pattern = jsonencode({
    source      = ["my.data.pipeline"]
    detail-type = ["Data Processing Completed"]
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.data_processed.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.notifier.arn
}
```

### SQS + Lambda: Reliable Processing

**Pattern**: SQS como buffer entre eventos y procesamiento.

```
S3 Upload → SQS Queue → Lambda (Batch processing)
                ↓
          DLQ (errores)
```

**Ventajas**:
- ✅ **Decoupling**: Si Lambda falla, mensaje no se pierde
- ✅ **Throttling control**: Lambda procesa a su propio ritmo
- ✅ **Retry automático**: Mensajes fallidos vuelven a la cola
- ✅ **DLQ**: Mensajes que fallan repetidamente van a Dead Letter Queue

```python
# Lambda que procesa mensajes SQS
def lambda_handler(event, context):
    # event contiene hasta 10 mensajes (batch)
    for record in event['Records']:
        message_id = record['messageId']
        body = json.loads(record['body'])

        try:
            process_message(body)
            print(f"Mensaje {message_id} procesado exitosamente")
        except Exception as e:
            # Si raise exception, mensaje vuelve a la cola
            print(f"Error procesando {message_id}: {e}")
            raise e

    # Si return exitoso, mensajes se eliminan de la cola
    return {'statusCode': 200}
```

**Terraform configuration**:

```hcl
resource "aws_sqs_queue" "processing_queue" {
  name                       = "data-processing-queue"
  visibility_timeout_seconds = 300  # 5 min (debe ser >= lambda timeout)
  message_retention_seconds  = 1209600  # 14 days

  # Dead Letter Queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3  # Después de 3 fallos → DLQ
  })
}

resource "aws_sqs_queue" "dlq" {
  name                       = "data-processing-dlq"
  message_retention_seconds  = 1209600  # 14 days
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.processing_queue.arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 10
  enabled          = true
}
```

---

## Serverless ETL Patterns

### Pattern 1: Micro-Batch ETL

**Caso de uso**: Procesar archivos pequeños frecuentemente (cada 5 minutes).

```
EventBridge (rate: 5 min)
   ↓
Lambda (List S3 new files)
   ↓
SQS (1 mensaje por archivo)
   ↓
Lambda (Process file)
   ↓
S3 (Processed)
```

**Lambda 1: Detector de archivos nuevos**

```python
def lambda_handler(event, context):
    s3 = boto3.client('s3')
    sqs = boto3.client('sqs')
    dynamodb = boto3.resource('dynamodb')

    # Tabla para tracking de archivos procesados
    table = dynamodb.Table('processed-files')

    # Listar archivos en S3
    response = s3.list_objects_v2(
        Bucket='my-bucket',
        Prefix='landing/'
    )

    for obj in response.get('Contents', []):
        key = obj['Key']

        # Check si ya fue procesado
        item = table.get_item(Key={'file_key': key})
        if 'Item' in item:
            continue  # Ya procesado

        # Enviar a SQS para procesamiento
        sqs.send_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/123/processing-queue',
            MessageBody=json.dumps({
                'bucket': 'my-bucket',
                'key': key,
                'size': obj['Size']
            })
        )
```

### Pattern 2: Large File Processing

**Problema**: Archivo de 5 GB no cabe en Lambda (max 10 GB temp storage).

**Solution**: Dividir en chunks y procesar en paralelo.

```
S3 (large file)
   ↓
Lambda (Splitter) → Invoca múltiples...
   ↓
[Lambda 1, Lambda 2, ..., Lambda N] (Procesadores)
   ↓
S3 (chunks procesados)
   ↓
Lambda (Aggregator)
   ↓
S3 (resultado final)
```

```python
# Lambda Splitter
def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']

    s3 = boto3.client('s3')
    lambda_client = boto3.client('lambda')

    # Obtener tamaño
    head = s3.head_object(Bucket=bucket, Key=key)
    file_size = head['ContentLength']

    chunk_size = 100 * 1024 * 1024  # 100 MB
    num_chunks = (file_size // chunk_size) + 1

    # Invocar Lambda por cada chunk (async)
    for i in range(num_chunks):
        start_byte = i * chunk_size
        end_byte = min(start_byte + chunk_size - 1, file_size - 1)

        lambda_client.invoke(
            FunctionName='chunk-processor',
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'bucket': bucket,
                'key': key,
                'start_byte': start_byte,
                'end_byte': end_byte,
                'chunk_id': i
            })
        )

    return {'chunks_created': num_chunks}
```

```python
# Lambda Processor (procesa un chunk)
def lambda_handler(event, context):
    s3 = boto3.client('s3')

    # Descargar chunk con Range
    response = s3.get_object(
        Bucket=event['bucket'],
        Key=event['key'],
        Range=f"bytes={event['start_byte']}-{event['end_byte']}"
    )

    chunk_data = response['Body'].read()

    # Procesar chunk
    processed_data = process_chunk(chunk_data)

    # Guardar chunk procesado
    output_key = f"processed/chunk_{event['chunk_id']}.parquet"
    s3.put_object(
        Bucket=event['bucket'],
        Key=output_key,
        Body=processed_data
    )

    return {'chunk_id': event['chunk_id'], 'output': output_key}
```

### Pattern 3: Real-Time Aggregation

**Caso de uso**: Agregar métricas en tiempo real (ej: conteo de eventos por minuto).

```
EventBridge → Lambda → DynamoDB (atomic counters)
```

```python
def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('metrics')

    # Timestamp truncado a minuto
    now = datetime.utcnow()
    minute_key = now.strftime('%Y-%m-%d %H:%M:00')

    # Incrementar counter atómicamente
    table.update_item(
        Key={'timestamp': minute_key, 'metric': 'events'},
        UpdateExpression='ADD count :inc',
        ExpressionAttributeValues={':inc': 1}
    )
```

---

## Integración con AWS Glue

### Glue Crawler + Lambda

**Caso de uso**: Después de procesar datos, actualizar Glue Data Catalog.

```python
def lambda_handler(event, context):
    glue = boto3.client('glue')

    # Después de guardar datos en S3, iniciar crawler
    glue.start_crawler(Name='my-data-crawler')

    return {'status': 'Crawler started'}
```

### Lambda + Glue Job

**Caso de uso**: Lambda para jobs pequeños, Glue para transformaciones complejas.

```python
def lambda_handler(event, context):
    glue = boto3.client('glue')

    # Si archivo es pequeño (<100 MB), procesar con Lambda
    file_size = event['file_size']

    if file_size < 100 * 1024 * 1024:  # 100 MB
        process_with_lambda(event)
    else:
        # Archivo grande → usar Glue Job
        glue.start_job_run(
            JobName='large-file-processor',
            Arguments={
                '--S3_INPUT': event['s3_path'],
                '--S3_OUTPUT': event['output_path']
            }
        )
```

### Athen + Lambda

**Lambda que ejecuta query en Athena**:

```python
def lambda_handler(event, context):
    athena = boto3.client('athena')

    query = """
        SELECT category, SUM(amount) as total
        FROM sales
        WHERE date = CURRENT_DATE
        GROUP BY category
    """

    # Iniciar query
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': 'my_database'},
        ResultConfiguration={
            'OutputLocation': 's3://my-bucket/athena-results/'
        }
    )

    query_execution_id = response['QueryExecutionId']

    # Esperar resultado (polling)
    while True:
        status = athena.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        state = status['QueryExecution']['Status']['State']

        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break

        time.sleep(1)

    if state == 'SUCCEEDED':
        # Obtener resultados
        results = athena.get_query_results(
            QueryExecutionId=query_execution_id
        )
        return {'results': results['ResultSet']['Rows']}
    else:
        raise Exception(f"Query failed: {state}")
```

---

## Monitoring y Observabilidad

### CloudWatch Logs Insights

Query logs de Lambda:

```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

### Custom Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    # Tu lógica...
    records_processed = 1000

    # Publicar custom metric
    cloudwatch.put_metric_data(
        Namespace='MyDataPipeline',
        MetricData=[{
            'MetricName': 'RecordsProcessed',
            'Value': records_processed,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        }]
    )
```

### X-Ray Tracing

**Habilitar tracing en Lambda**:

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()  # Instrumenta boto3, requests, etc.

def lambda_handler(event, context):
    # Subsegment custom
    with xray_recorder.in_subsegment('ProcessData') as subsegment:
        result = process_data(event)
        subsegment.put_annotation('record_count', len(result))

    return result
```

---

## Best Practices

### 1. Idempotencia

Asegúrate que execute la misma Lambda múltiples veces con el mismo input produce el mismo resultado.

```python
# ✅ Idempotente
def lambda_handler(event, context):
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('processed-files')

    file_key = event['key']

    # Check si ya fue procesado
    response = table.get_item(Key={'file_key': file_key})
    if 'Item' in response:
        return {'status': 'already_processed'}

    # Procesar
    result = process_file(file_key)

    # Marcar como procesado
    table.put_item(Item={
        'file_key': file_key,
        'processed_at': datetime.utcnow().isoformat(),
        'result': result
    })

    return {'status': 'processed', 'result': result}
```

### 2. Error Handling

```python
def lambda_handler(event, context):
    try:
        result = process_data(event)
        return {'statusCode': 200, 'body': json.dumps(result)}

    except ClientError as e:
        # Error de AWS (permisos, recurso no encontrado)
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            return {'statusCode': 404, 'body': 'File not found'}
        raise

    except ValueError as e:
        # Error de validation (no reintentar)
        return {'statusCode': 400, 'body': f'Invalid data: {e}'}

    except Exception as e:
        # Error inesperado (raise para retry)
        print(f"Unexpected error: {e}")
        raise
```

### 3. Secrets Management

```python
import boto3
import json

secrets_client = boto3.client('secretsmanager')

# ❌ NO HACER: Hardcodear credenciales
DB_PASSWORD = "mysecretpassword123"

# ✅ Usar Secrets Manager
def get_secret(secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def lambda_handler(event, context):
    # Obtener credenciales
    db_creds = get_secret('prod/database/credentials')

    # Usar credenciales
    conn = connect_to_db(
        host=db_creds['host'],
        user=db_creds['username'],
        password=db_creds['password']
    )
```

### 4. Testing

```python
# test_lambda.py
import pytest
from unittest.mock import patch, MagicMock
from handler import lambda_handler

@patch('handler.boto3.client')
def test_lambda_handler_success(mock_boto3):
    # Mock S3 client
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3

    event = {
        'Records': [{
            's3': {
                'bucket': {'name': 'test-bucket'},
                'object': {'key': 'test.csv'}
            }
        }]
    }

    result = lambda_handler(event, {})

    assert result['statusCode'] == 200
    mock_s3.get_object.assert_called_once()
```

---

## Resumen

- **Lambda + S3**: Pattern fundamental para file processing
- **Step Functions**: Orquestación de workflows complejos
- **EventBridge**: Event bus para arquitecturas event-driven
- **SQS**: Buffer confiable para procesamiento asíncrono
- **Glue integration**: Combinar serverless con big data processing
- **Best practices**: Idempotencia, error handling, monitoring

**Próximo**: [03-serverless-patterns.md](03-serverless-patterns.md) - Patrones avanzados y producción
