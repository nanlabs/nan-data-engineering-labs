# Fundamentos de Serverless Computing

## 📋 Tabla de Contenidos

1. [¿Qué es Serverless?](#qué-es-serverless)
2. [AWS Lambda Fundamentals](#aws-lambda-fundamentals)
3. [Event-Driven Architecture](#event-driven-architecture)
4. [AWS Lambda en Detalle](#aws-lambda-en-detalle)
5. [Event Sources](#event-sources)
6. [Pricing y Límites](#pricing-y-límites)

---

## ¿Qué es Serverless?

### Definición

**Serverless computing** es un modelo de computación en la nube donde el proveedor gestiona automáticamente la infraestructura servers. El desarrollador solo se enfoca en el código.

**⚠️ "Serverless" NO significa "sin servidores"**
- Los servidores existen, pero NO los gestionas tú
- El proveedor cloud se encarga de provisioning, scaling, patching
- Pagas solo por el tiempo de ejecución real

### Características Clave

1. **No Server Management** 🖥️
   - Sin provisioning de VMs
   - Sin instalación de OS
   - Sin patches o actualizaciones

2. **Auto-scaling** 📈
   - Escala automáticamente de 0 a miles de instancias
   - Sin configuration de capacity planning

3. **Pay-per-use** 💰
   - Solo pagas por tiempo de ejecución
   - Granularidad de milisegundos
   - $0 cuando no hay invocaciones

4. **Event-driven** ⚡
   - Reacciona a eventos (file upload, HTTP request, schedule)
   - Integración nativa con otros servicios

5. **Stateless** 🔄
   - Cada invocación es independiente
   - Estado se almacena externamente (DynamoDB, S3, etc.)

### Serverless vs Traditional

| Aspecto | Traditional (EC2) | Serverless (Lambda) |
|---------|-------------------|---------------------|
| **Provisioning** | Manual (minutes/hours) | Automático (instantáneo) |
| **Scaling** | Manual o auto-scaling groups | Automático ilimitado |
| **Costo mínimo** | Instancia corriendo 24/7 | $0 sin invocaciones |
| **Billing** | Por hora | Por milisegundo |
| **Capacity planning** | Requerido | No necesario |
| **Idle capacity** | Pagas por ello | No existe |
| **Maintenance** | Patches, updates | Proveedor se encarga |
| **Cold starts** | No existen | Latencia inicial |

### Casos de Uso Ideales

✅ **Perfecto para**:
- APIs REST/GraphQL
- Procesamiento de eventos (file uploads, DynamoDB streams)
- ETL y data transformation jobs
- Scheduled tasks (cron jobs)
- Webhooks
- Image/video processing
- Backends móviles
- Chatbots y Alexa skills
- IoT backends

❌ **No ideal para**:
- Aplicaciones con tráfico constante 24/7 (más caro que EC2)
- Procesos de larga duración (>15 minutes)
- Aplicaciones con cold start crítico (<100ms latency requerido)
- Workloads con requerimientos de GPU intensivo

---

## AWS Lambda Fundamentals

### ¿Qué es AWS Lambda?

AWS Lambda es el servicio de **Function as a Service (FaaS)** de AWS. Ejecuta código en respuesta a eventos sin provisionar servidores.

**Analogía**: Lambda es como un "chef on-demand". Solo llamas al chef cuando necesitas cocinar (evento), el chef prepara el plato (ejecuta tu código), y solo pagas por el tiempo que estuvo cocinando.

### Conceptos Core

#### 1. Function (Función)

Es el código que ejecutas:

```python
# handler.py
def lambda_handler(event, context):
    """
    event: Datos del evento que disparó la Lambda
    context: Metadata sobre la invocación y el runtime
    """
    print(f"Evento recibido: {event}")

    # Tu lógica de negocio
    result = process_data(event)

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

#### 2. Event (Evento)

JSON que contiene datos del trigger:

```json
{
  "Records": [{
    "s3": {
      "bucket": {"name": "my-bucket"},
      "object": {"key": "data.csv"}
    }
  }]
}
```

#### 3. Context

Información sobre la ejecución:

```python
def lambda_handler(event, context):
    print(f"Request ID: {context.aws_request_id}")
    print(f"Function name: {context.function_name}")
    print(f"Memory: {context.memory_limit_in_mb} MB")
    print(f"Time remaining: {context.get_remaining_time_in_millis()} ms")
```

### Runtimes Soportados

AWS Lambda soporta múltiples lenguajes:

| Runtime | Versiones | Caso de Uso |
|---------|-----------|-------------|
| **Python** | 3.8, 3.9, 3.10, 3.11, 3.12 | Data processing, ML, ETL |
| **Node.js** | 16.x, 18.x, 20.x | APIs, real-time apps |
| **Java** | 8, 11, 17, 21 | Enterprise apps |
| **Go** | 1.x | High performance, compiled |
| **.NET** | 6, 8 | Microsoft stack |
| **Ruby** | 3.2 | Web frameworks |
| **Custom** | Container images | Cualquier runtime |

**Para Data Engineering**: Python es el runtime más popular por sus librerías (pandas, boto3, etc.)

### Ejemplo Completo: Lambda para Procesar CSV

```python
import json
import boto3
import pandas as pd
from io import StringIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda que se dispara cuando se sube un CSV a S3,
    lo procesa con pandas, y guarda el resultado.
    """

    # 1. Obtener información del evento
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    print(f"Procesando archivo: s3://{bucket}/{key}")

    try:
        # 2. Descargar archivo de S3
        response = s3.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')

        # 3. Procesar con pandas
        df = pd.read_csv(StringIO(csv_content))

        # Transformación: calcular estadísticas
        stats = {
            'row_count': len(df),
            'columns': list(df.columns),
            'numeric_stats': df.describe().to_dict()
        }

        # 4. Guardar resultado
        output_key = key.replace('.csv', '_stats.json')
        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=json.dumps(stats, indent=2),
            ContentType='application/json'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Procesamiento exitoso',
                'input': f's3://{bucket}/{key}',
                'output': f's3://{bucket}/{output_key}',
                'stats': stats
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise e
```

### Lambda Lifecycle

```
┌─────────────────────────────────────────────┐
│  1. COLD START (Primera invocación)         │
│     ├─ Descargar código                     │
│     ├─ Iniciar runtime                      │
│     ├─ Ejecutar código de inicialización    │
│     └─ Ejecutar handler                     │
│        Tiempo: 1-5 segundos                 │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  2. WARM EXECUTION (Invocaciones siguientes)│
│     └─ Ejecutar handler directamente        │
│        Tiempo: milisegundos                 │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  3. IDLE (Sin invocaciones)                 │
│     └─ Container se mantiene 5-15 min       │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  4. TERMINATED                              │
│     └─ Container destruido                  │
│        Próxima invocación = COLD START      │
└─────────────────────────────────────────────┘
```

### Optimizar Cold Starts

```python
# ❌ MAL: Importar dentro del handler
def lambda_handler(event, context):
    import pandas as pd  # Se importa en CADA invocación
    import boto3

    s3 = boto3.client('s3')  # Se crea cliente en CADA invocación
    # ...

# ✅ BIEN: Importar fuera del handler
import pandas as pd  # Se importa UNA VEZ (cold start)
import boto3

s3 = boto3.client('s3')  # Cliente reutilizado entre invocaciones

def lambda_handler(event, context):
    # Solo lógica de negocio aquí
    # ...
```

---

## Event-Driven Architecture

### Concepto

En arquitectura event-driven, los componentes reaccionan a **eventos** en lugar de llamarse directamente.

**Ejemplo tradicional (synchronous)**:
```
API Request → Lambda 1 → Lambda 2 → Lambda 3 → Response
(Cada uno espera al siguiente)
```

**Event-driven (asynchronous)**:
```
API Request → SQS Queue
                 │
                 ├→ Lambda 1 (procesa async)
                 ├→ Lambda 2 (procesa async)
                 └→ Lambda 3 (procesa async)
Response inmediato
```

### Patrones de Invocación Lambda

#### 1. Synchronous (Request/Response)

Llamador espera la respuesta:

```python
import boto3

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='RequestResponse',  # Synchronous
    Payload=json.dumps({'key': 'value'})
)

result = json.loads(response['Payload'].read())
print(result)
```

**Casos de uso**:
- API Gateway
- Cognito triggers
- SDK invocations

#### 2. Asynchronous (Fire and Forget)

Llamador NO espera respuesta:

```python
response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='Event',  # Asynchronous
    Payload=json.dumps({'key': 'value'})
)
# Retorna inmediatamente, Lambda se ejecuta después
```

**Casos de uso**:
- S3 events
- SNS messages
- EventBridge events

**Retry automático**: Si falla, Lambda reintenta 2 veces.

#### 3. Polling (Pull-based)

Lambda hace polling de una cola/stream:

```
SQS Queue → [Lambda polls every second] → Lambda procesa batch
```

**Casos de uso**:
- SQS queues
- Kinesis streams
- DynamoDB streams

### Event Sources Comunes

| Source | Type | Caso de Uso |
|--------|------|-------------|
| **API Gateway** | Sync | REST APIs |
| **S3** | Async | File processing |
| **DynamoDB Streams** | Poll | Data changes reaction |
| **SQS** | Poll | Queue processing |
| **SNS** | Async | Pub/sub notifications |
| **EventBridge** | Async | Scheduled/custom events |
| **Kinesis** | Poll | Real-time streams |
| **CloudWatch Logs** | Async | Log processing |

---

## AWS Lambda en Detalle

### Configuration

#### Memory

- **Rango**: 128 MB a 10,240 MB (10 GB)
- **CPU proporcional**: Más memoria = más CPU
- **Recomendación**: Empezar con 512 MB, ajustar según profiling

```python
# Lambda configurada con 1024 MB
# Obtiene ~0.58 vCPU
```

#### Timeout

- **Rango**: 1 segundo a 15 minutes (900 segundos)
- **Default**: 3 segundos
- **Recomendación**: Configurar según el proceso más largo esperado + margen

```python
# Si tu proceso toma 2 minutes, configurar timeout de 2.5 minutes
```

#### Environment Variables

```python
import os

def lambda_handler(event, context):
    # Variables de entorno
    db_host = os.environ['DB_HOST']
    api_key = os.environ['API_KEY']  # ⚠️ Cifrar con KMS
    environment = os.environ['ENVIRONMENT']  # dev, staging, prod

    print(f"Conectando a {db_host} en entorno {environment}")
```

### Networking

#### Sin VPC (default)

```
Lambda → Internet → AWS Services (S3, DynamoDB, etc.)
```

**Ventajas**:
- ✅ No cold start adicional
- ✅ Internet access por defecto
- ✅ Acceso a servicios AWS públicos

**Desventajas**:
- ❌ No puede acceder a recursos en VPC (RDS, ElastiCache)

#### Con VPC

```
Lambda → VPC → Private Subnet → RDS/ElastiCache
```

**Ventajas**:
- ✅ Acceso a recursos privados (RDS, ElastiCache, EC2)
- ✅ Mayor seguridad

**Desventajas**:
- ❌ Cold start más lento (~10 segundos adicionales antes)
- ❌ Requiere NAT Gateway para internet ($$$)

**⚠️ Desde 2019**: AWS mejoró VPC cold starts con Hyperplane ENIs.

### IAM Permissions

#### Execution Role

Lambda necesita permisos para acceder a AWS services:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/MyTable"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**Principio de least privilege**: Solo dar permisos mínimos necesarios.

### Layers

**Lambda Layers** permiten compartir código/dependencias entre funciones:

```
┌─────────────────────────────────┐
│     Lambda Function Code        │
│        (handler.py)             │
├─────────────────────────────────┤
│   Layer 3: Custom Utils         │
│   Layer 2: pandas, numpy        │
│   Layer 1: requests             │
└─────────────────────────────────┘
```

**Ventajas**:
- ✅ Reutilizar dependencias (pandas, numpy)
- ✅ Reducir tamaño del deployment package
- ✅ Separar código de negocio de dependencias

**Crear Layer**:

```bash
# Estructura
python/lib/python3.11/site-packages/
└── pandas/
└── numpy/

# Empaquetar
zip -r pandas-layer.zip python/

# Subir a Lambda Layer
aws lambda publish-layer-version \
    --layer-name pandas-numpy \
    --zip-file fileb://pandas-layer.zip \
    --compatible-runtimes python3.11
```

### Concurrency

**Concurrent executions**: Número de invocaciones ejecutándose simultáneamente.

```
Request 1 → Lambda Instance 1  ┐
Request 2 → Lambda Instance 2  ├─ 3 concurrent executions
Request 3 → Lambda Instance 3  ┘
```

**Límites**:
- Default concurrency: 1000 por región
- Puede solicitar aumento
- Reserved concurrency: Garantizar X instancias para función crítica

**Throttling**: Si llegas al límite, nuevas invocaciones son rechazadas (429 error).

---

## Event Sources

### S3 Events

**Caso de uso**: Procesar archivos cuando se suben a S3.

```python
def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        event_name = record['eventName']  # ObjectCreated:Put

        print(f"Evento: {event_name} en s3://{bucket}/{key}")

        if key.endswith('.csv'):
            process_csv(bucket, key)
        elif key.endswith('.json'):
            process_json(bucket, key)
```

**Configuration**: S3 Bucket → Properties → Event notifications → Lambda function

**Event Structure**:

```json
{
  "Records": [{
    "eventVersion": "2.1",
    "eventSource": "aws:s3",
    "awsRegion": "us-east-1",
    "eventTime": "2024-03-07T10:30:00.000Z",
    "eventName": "ObjectCreated:Put",
    "s3": {
      "bucket": {"name": "my-bucket"},
      "object": {
        "key": "data/file.csv",
        "size": 1024,
        "eTag": "abc123"
      }
    }
  }]
}
```

### SQS (Queue)

**Caso de uso**: Procesamiento asíncrono con retries automáticos.

```python
def lambda_handler(event, context):
    for record in event['Records']:
        message_id = record['messageId']
        body = json.loads(record['body'])

        print(f"Procesando mensaje {message_id}: {body}")

        try:
            process_message(body)
        except Exception as e:
            # Si falla, mensaje vuelve a la cola
            print(f"Error: {e}")
            raise e
```

**Ventajas**:
- ✅ Retry automático
- ✅ Dead Letter Queue (DLQ) para mensajes fallidos
- ✅ Batch processing (hasta 10 mensajes por invocación)

### EventBridge (antes CloudWatch Events)

**Caso de uso**: Eventos programados o custom events.

```python
# Scheduled event (cron job)
def lambda_handler(event, context):
    # Se ejecuta cada día a las 9 AM
    print("Ejecutando tarea programada")
    generate_daily_report()
```

**Cron expression**:
```
rate(5 minutes)           # Cada 5 minutes
rate(1 hour)              # Cada hora
rate(1 day)               # Cada día
cron(0 9 * * ? *)         # Todos los días a las 9 AM UTC
cron(0 18 ? * MON-FRI *)  # Lunes a viernes a las 6 PM
```

### DynamoDB Streams

**Caso de uso**: Reaccionar a cambios en tabla DynamoDB.

```python
def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_item = record['dynamodb']['NewImage']
            print(f"Nuevo item: {new_item}")

        elif record['eventName'] == 'MODIFY':
            old_item = record['dynamodb']['OldImage']
            new_item = record['dynamodb']['NewImage']
            print(f"Modificado: {old_item} → {new_item}")

        elif record['eventName'] == 'REMOVE':
            old_item = record['dynamodb']['OldImage']
            print(f"Eliminado: {old_item}")
```

---

## Pricing y Límites

### Pricing

**Componentes**:

1. **Requests**: $0.20 por 1 millón de requests
2. **Duration**: $0.0000166667 por GB-segundo

**Cálculo ejemplo**:

```
Lambda: 1024 MB memory, 500ms execution time
Invocations: 1 millón por mes

Requests: 1M × $0.20 = $0.20
Duration: 1M × 0.5s × (1024/1024 GB) = 500,000 GB-s
          500,000 × $0.0000166667 = $8.33

Total: $8.53/mes
```

**Free Tier (permanente)**:
- 1 millón de requests gratis/mes
- 400,000 GB-segundos gratis/mes

### Límites (Soft)

| Recurso | Límite | Ajustable |
|---------|--------|-----------|
| Concurrent executions | 1000 | ✅ Sí |
| Function timeout | 15 minutes | ❌ No |
| Memory | 128 MB - 10 GB | ❌ No |
| Deployment package | 50 MB (zipped), 250 MB (unzipped) | ❌ No |
| /tmp storage | 512 MB - 10 GB | ✅ Sí |
| Environment variables | 4 KB | ❌ No |
| Layers | 5 layers por función | ❌ No |

### Best Practices

✅ **DO**:
- Usar environment variables para configuration
- Implementar idempotencia (misma entrada = mismo resultado)
- Usar DLQ (Dead Letter Queue) para errores
- Separar funciones por responsabilidad
- Usar Layers para dependencias compartidas
- Implement structured logging (JSON)
- Usar async cuando sea posible

❌ **DON'T**:
- No procesar más de 15 minutes (usar Step Functions)
- No mantener estado en el código (usar DynamoDB/S3)
- No hardcodear credenciales
- No usar Lambda para workloads constantes 24/7

---

## Resumen

- **Serverless = No server management**, auto-scaling, pay-per-use
- **AWS Lambda** ejecuta código en respuesta a eventos
- **Cold start** es real pero optimizable
- **Event-driven architecture** desacopla componentes
- **Múltiples event sources**: S3, SQS, API Gateway, EventBridge, etc.
- **Pricing**: Muy económico para cargas variables
- **Límites**: 15 minutes max, 10 GB memory max

**Próximo**: [02-serverless-data-processing.md](02-serverless-data-processing.md) - Procesamiento de datos con Lambda
