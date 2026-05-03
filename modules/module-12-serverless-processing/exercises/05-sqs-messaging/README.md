# Exercise 05: SQS Messaging Patterns

## 📋 Información General

- **Level**: Avanzado
- **Duration estimada**: 2-3 hours
- **Prerequisites**:
  - Exercises 01-04 completeds
  - Comprensión de message queues
  - Conocimiento de retry patterns

## 🎯 Objectives de Aprendizaje

1. Implementar message-driven architectures
2. Usar SQS para decoupling
3. Configurar Dead Letter Queues (DLQ)
4. Batch processing con Lambda
5. FIFO vs Standard queues
6. Message deduplication

---

## 📚 Context

Construirás un **Order Processing System** con:
- SQS como message broker
- Lambda processors (async)
- DLQ para errores
- FIFO queue para procesamiento ordenado

**Arquitectura**:

```
┌──────────────┐
│  API Gateway │
└──────┬───────┘
       │ POST /orders
       ▼
┌──────────────────────┐
│  Lambda: Order API   │
└──────┬───────────────┘
       │ Send message
       ▼
┌────────────────────────────┐
│  SQS: orders-queue.fifo    │
│  (FIFO, deduplication)     │
└──────┬─────────────────────┘
       │ Batch (10 msgs)
       ▼
┌──────────────────────────────────┐
│  Lambda: Order Processor         │
│  1. Validate order               │
│  2. Check inventory              │
│  3. Process payment              │
│  4. Update database              │
└──────┬───────────────────────────┘
       │
  ┌────┴─────┐
  ▼          ▼
┌─────┐  ┌───────────┐
│ DLQ │  │ DynamoDB  │
│     │  │ (orders)  │
└─────┘  └───────────┘
```

---

## 🔧 Parte 1: Order API

**`src/order_api.py`**:

```python
"""
API para recibir órdenes y enviarlas a SQS
"""
import json
import logging
import os
import boto3
import hashlib
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['QUEUE_URL']

def lambda_handler(event, context):
    """
    POST /orders - Create order and send to queue
    """

    try:
        body = json.loads(event['body'])

        # Validar orden
        validate_order(body)

        # Generar deduplication ID (idempotencia)
        dedup_id = generate_dedup_id(body)

        # Enviar mensaje a SQS FIFO
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(body),
            MessageGroupId=body['customer_id'],  # FIFO grouping
            MessageDeduplicationId=dedup_id  # Deduplication
        )

        logger.info(f"Order queued: {response['MessageId']}")

        return {
            'statusCode': 202,  # Accepted
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Order queued for processing',
                'message_id': response['MessageId'],
                'order_id': body['order_id']
            })
        }

    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }


def validate_order(order: dict):
    """Validar campos de orden"""

    required = ['order_id', 'customer_id', 'items', 'total']

    for field in required:
        if field not in order:
            raise ValueError(f"Missing required field: {field}")

    if not order['items']:
        raise ValueError("Order must have at least one item")

    if order['total'] <= 0:
        raise ValueError("Total must be positive")


def generate_dedup_id(order: dict) -> str:
    """
    Generar deduplication ID basado en contenido de la orden
    Permite idempotencia: misma orden = mismo ID
    """
    content = json.dumps(order, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

---

## 🔧 Parte 2: Order Processor

**`src/order_processor.py`**:

```python
"""
Lambda que procesa órdenes desde SQS
"""
import json
import logging
import os
import boto3
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])

def lambda_handler(event, context):
    """
    Procesar batch de órdenes desde SQS
    """

    results = {
        'processed': 0,
        'failed': 0
    }

    batch_item_failures = []

    for record in event['Records']:
        try:
            # Parsear mensaje
            order = json.loads(record['body'])
            message_id = record['messageId']

            logger.info(f"Processing order {order['order_id']}")

            # Procesar orden
            process_order(order)

            results['processed'] += 1

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}")
            results['failed'] += 1

            # Marcar mensaje como fallido para retry
            batch_item_failures.append({
                'itemIdentifier': record['messageId']
            })

    logger.info(f"Batch results: {results}")

    # Retornar mensajes fallidos (Lambda will retry them)
    return {
        'batchItemFailures': batch_item_failures
    }


def process_order(order: dict):
    """
    Procesar una orden
    """

    # 1. Validar inventario (simulado)
    if not check_inventory(order['items']):
        raise Exception("Insufficient inventory")

    # 2. Procesar pago (simulado)
    if not process_payment(order['customer_id'], order['total']):
        raise Exception("Payment failed")

    # 3. Guardar orden en DynamoDB
    order_record = {
        'order_id': order['order_id'],
        'customer_id': order['customer_id'],
        'items': order['items'],
        'total': order['total'],
        'status': 'PROCESSED',
        'processed_at': datetime.utcnow().isoformat()
    }

    orders_table.put_item(Item=order_record)

    logger.info(f"Order {order['order_id']} processed successfully")


def check_inventory(items: List[Dict]) -> bool:
    """Simular validation de inventario"""
    # En producción: consultar servicio de inventario
    return True


def process_payment(customer_id: str, amount: float) -> bool:
    """Simular procesamiento de pago"""
    # En producción: llamar a payment gateway
    if amount > 10000:
        return False  # Simular fallo para órdenes grandes
    return True
```

---

## 🔧 Parte 3: Infrastructure

**`infrastructure/main.tf`**:

```hcl
# SQS Queue (FIFO)
resource "aws_sqs_queue" "orders_fifo" {
  name                       = "orders-queue-${var.environment}.fifo"
  fifo_queue                 = true
  content_based_deduplication = false  # Usaremos MessageDeduplicationId
  deduplication_scope        = "messageGroup"
  fifo_throughput_limit      = "perMessageGroupId"

  visibility_timeout_seconds = 300  # 5 min
  message_retention_seconds  = 1209600  # 14 días

  # Dead Letter Queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

# Dead Letter Queue (FIFO)
resource "aws_sqs_queue" "dlq" {
  name                      = "orders-dlq-${var.environment}.fifo"
  fifo_queue                = true
  message_retention_seconds = 1209600  # 14 días
}

# CloudWatch Alarm para DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_alarm" {
  alarm_name          = "orders-dlq-alarm-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# Lambda: Order API
resource "aws_lambda_function" "order_api" {
  filename      = "order_api.zip"
  function_name = "order-api-${var.environment}"
  role          = aws_iam_role.order_api.arn
  handler       = "order_api.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.orders_fifo.url
    }
  }
}

# Lambda: Order Processor
resource "aws_lambda_function" "order_processor" {
  filename      = "order_processor.zip"
  function_name = "order-processor-${var.environment}"
  role          = aws_iam_role.order_processor.arn
  handler       = "order_processor.lambda_handler"
  runtime       = "python3.11"
  timeout       = 120
  memory_size   = 1024

  environment {
    variables = {
      ORDERS_TABLE = aws_dynamodb_table.orders.name
    }
  }
}

# Event Source Mapping: SQS → Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.orders_fifo.arn
  function_name    = aws_lambda_function.order_processor.arn
  batch_size       = 10
  enabled          = true

  # Configuration de retry
  function_response_types = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = 5  # Max 5 Lambda instances
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "orders" {
  name         = "orders-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }

  attribute {
    name = "customer_id"
    type = "S"
  }

  global_secondary_index {
    name            = "customer-index"
    hash_key        = "customer_id"
    projection_type = "ALL"
  }
}

# IAM Roles
resource "aws_iam_role" "order_api" {
  name = "order-api-role-${var.environment}"

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

resource "aws_iam_role_policy" "order_api_sqs" {
  name = "sqs-send"
  role = aws_iam_role.order_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:GetQueueUrl"
      ]
      Resource = aws_sqs_queue.orders_fifo.arn
    }]
  })
}

# Outputs
output "api_endpoint" {
  value = aws_api_gateway_stage.orders_api.invoke_url
}

output "queue_url" {
  value = aws_sqs_queue.orders_fifo.url
}
```

---

## 🧪 Parte 4: Testing

### 4.1 Test Order Creation

```bash
# Get API URL
API_URL=$(cd infrastructure && terraform output -raw api_endpoint)

# Crear orden
curl -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD001",
    "customer_id": "CUST123",
    "items": [
      {"product_id": "PROD1", "quantity": 2, "price": 50.00},
      {"product_id": "PROD2", "quantity": 1, "price": 100.00}
    ],
    "total": 200.00
  }'

# Verificar que el mensaje fue procesado
aws dynamodb get-item \
  --table-name orders-dev \
  --key '{"order_id": {"S": "ORD001"}}'
```

### 4.2 Test Deduplication (Idempotencia)

```bash
# Enviar la MISMA orden dos veces
for i in {1..2}; do
  curl -X POST "$API_URL/orders" \
    -H "Content-Type: application/json" \
    -d '{
      "order_id": "ORD002",
      "customer_id": "CUST123",
      "items": [{"product_id": "PROD1", "quantity": 1, "price": 50.00}],
      "total": 50.00
    }'
done

# Solo debe procesarse UNA vez (deduplication ID idéntico)
```

### 4.3 Test DLQ (Simular fallo)

```bash
# Enviar orden > $10,000 (simulará fallo de pago)
curl -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD003",
    "customer_id": "CUST123",
    "items": [{"product_id": "PROD1", "quantity": 100, "price": 200.00}],
    "total": 20000.00
  }'

# Después de 3 reintentos, debería ir a DLQ
aws sqs receive-message \
  --queue-url $(cd infrastructure && terraform output -raw dlq_url)
```

---

## 📊 Monitoring

### CloudWatch Logs Insights

```sql
-- Ver órdenes procesadas
fields @timestamp, order_id, status
| filter @message like /processed successfully/
| sort @timestamp desc

-- Ver errores
fields @timestamp, error
| filter @message like /Failed to process/
| stats count() by error
```

---

## ✅ Checklist

- [ ] FIFO queue configurada
- [ ] Deduplication funcionando
- [ ] DLQ configurada
- [ ] Lambda procesa batchs
- [ ] Retry logic funcional
- [ ] Alarmas CloudWatch
- [ ] Órdenes en DynamoDB
- [ ] Idempotencia verificada

**Siguiente**: [Exercise 06 - Production Pipeline](../06-production-pipeline/)
