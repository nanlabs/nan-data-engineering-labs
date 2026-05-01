# Integration Tests

Este directorio está reservado para tests de integración entre servicios.

## 🔗 Propósito

Validar que múltiples servicios AWS funcionan correctamente en conjunto (S3 → Lambda → SQS, etc.).

## 🎯 Tipos de Tests a Agregar

### Event-Driven Workflows
```python
def test_s3_to_lambda_trigger():
    """Verificar que subir a S3 dispara Lambda"""

def test_lambda_to_sqs_delivery():
    """Verificar que Lambda envía mensajes a SQS"""
```

### End-to-End Scenarios
```python
def test_csv_validation_pipeline():
    """Test completo: S3 upload → Lambda validation → SQS notification"""
```

### Cross-Service Communication
```python
def test_cloudwatch_logs_generated():
    """Verificar que Lambda genera logs en CloudWatch"""

def test_sns_notification_sent():
    """Verificar que SNS envía notificaciones"""
```

## 📝 Ejemplo de Test

```python
import boto3
import time
import pytest

def test_complete_validation_pipeline():
    """Test end-to-end del pipeline de validación CSV"""

    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')

    bucket_name = 'quickmart-data'
    queue_name = 'validation-results'

    # 1. Upload CSV to S3
    csv_data = "transaction_id,amount\nTXN001,100.00\n"
    s3.put_object(
        Bucket=bucket_name,
        Key='uploads/test.csv',
        Body=csv_data.encode('utf-8')
    )

    # 2. Wait for Lambda processing
    time.sleep(5)

    # 3. Check SQS for message
    queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

    # 4. Verify message received
    assert 'Messages' in messages
    assert len(messages['Messages']) > 0

    # 5. Verify validated file exists
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix='validated/')
    assert response['KeyCount'] > 0
```

## 🚀 Ejecutar

```bash
pytest validation/integration/ -v
```

## ⏱️ Consideraciones

- Tests de integración son más lentos (esperan eventos, procesamiento)
- Requieren servicios corriendo (LocalStack)
- Pueden necesitar timeouts más largos
- Útiles para detectar problemas de configuración

## 📚 Herramientas Recomendadas

- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Tests asíncronos
- [pytest-timeout](https://pypi.org/project/pytest-timeout/) - Timeouts para tests
- [tenacity](https://tenacity.readthedocs.io/) - Retry logic
