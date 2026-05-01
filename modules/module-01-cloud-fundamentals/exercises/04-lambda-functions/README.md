# Exercise 04: AWS Lambda Functions

**Duration:** 75-90 minutos | **Difficulty:** ⭐⭐⭐

## 🎯 Objectives

- Crear Lambda functions en Python
- Implementar event-driven processing con S3 triggers
- Manejar errores y logging
- Configurar timeouts y memory optimization

## 📖 Conceptos

**Lambda** = Compute sin servidores. Ejecutas código sin gestionar infraestructura.

**Event Sources:**
- S3 (ObjectCreated, ObjectRemoved)
- SQS (message polling)
- API Gateway (HTTP requests)
- CloudWatch Events (scheduled)

## 🎬 Pasos

### Paso 1: Escenario

QuickMart necesita:
- **Validar CSV uploads** (schema, data quality)
- **Transform JSON logs** (parse, enrich, send to CloudWatch)
- **Generate thumbnails** for product images
- **Alert on anomalies** (high transaction values)

### Paso 2: Copiar Starter

```bash
cp -r starter/ my_solution/
cd my_solution
```

### Paso 3: Implementar Lambda Functions

#### Function 1: CSV Validator

```python
# lambda_csv_validator.py
def lambda_handler(event, context):
    # TODO: Parse S3 event
    # TODO: Download CSV from S3
    # TODO: Validate schema
    # TODO: Return validation report
    pass
```

#### Function 2: Log Transformer

```python
# lambda_log_transformer.py
def lambda_handler(event, context):
    # TODO: Read JSON logs from S3
    # TODO: Parse and enrich (add timestamp, user_id)
    # TODO: Write to processed/ folder
    pass
```

### Paso 4: Desplegar con CLI

```bash
# Create deployment package
zip function.zip lambda_csv_validator.py

# Create Lambda function
aws --endpoint-url=http://localhost:4566 lambda create-function \
  --function-name csv-validator \
  --runtime python3.9 \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --handler lambda_csv_validator.lambda_handler \
  --zip-file fileb://function.zip
```

### Paso 5: Configurar S3 Trigger

```python
# Add S3 trigger programmatically
s3.put_bucket_notification_configuration(
    Bucket='my-data-lake',
    NotificationConfiguration={
        'LambdaFunctionConfigurations': [{
            'LambdaFunctionArn': 'arn:aws:lambda:us-east-1:000000000000:function:csv-validator',
            'Events': ['s3:ObjectCreated:*'],
            'Filter': {'Key': {'FilterRules': [{'Name': 'suffix', 'Value': '.csv'}]}}
        }]
    }
)
```

### Paso 6: Testing

```bash
# Upload CSV to trigger Lambda
aws s3 cp test.csv s3://my-data-lake/uploads/

# Check Lambda logs
aws --endpoint-url=http://localhost:4566 logs tail /aws/lambda/csv-validator

# Verify processed files
aws s3 ls s3://my-data-lake/processed/
```

## 🧪 Validación

```python
# Test locally
python3 test_lambda.py

# Expected:
# ✓ Lambda function created
# ✓ S3 trigger configured
# ✓ Upload CSV → Lambda invoked
# ✓ Validation report generated
# ✓ Invalid records logged
```

## 📚 Entregables

- ✅ `lambda_csv_validator.py` (validates CSV schema)
- ✅ `lambda_log_transformer.py` (transforms JSON logs)
- ✅ `deploy_lambdas.sh` (deployment script)
- ✅ `test_lambda.py` (integration tests)
- ✅ Screenshot showing Lambda execution logs

---

**Hints:** [hints.md](hints.md) | **Siguiente:** [Exercise 05](../05-infrastructure-as-code/README.md)
