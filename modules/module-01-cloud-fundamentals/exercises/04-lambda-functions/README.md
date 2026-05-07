# Exercise 04: AWS Lambda Functions

**Duration:** 75-90 minutes | **Difficulty:** ⭐⭐⭐

## 🎯 Objectives

- Create Lambda functions en Python
- Implement event-driven processing con S3 triggers
- Manejar errores y logging
- Configure timeouts y memory optimization

## 📖 Conceptos

**Lambda** = Compute sin servidores. Ejecutas código sin gestionar infraestructura.

**Event Sources:**

- S3 (ObjectCreated, ObjectRemoved)
- SQS (message polling)
- API Gateway (HTTP requests)
- CloudWatch Events (scheduled)

## 🎬 Steps

### Step 1: Scenario

QuickMart necesita:

- **Validate CSV uploads** (schema, data quality)
- **Transform JSON logs** (parse, enrich, send to CloudWatch)
- **Generate thumbnails** for product images
- **Alert on anomalies** (high transaction values)

### Step 2: Copiar Starter

```bash
cp -r starter/ my_solution/
cd my_solution
```text

### Step 3: Implement Lambda Functions

#### Function 1: CSV Validator

```python
# lambda_csv_validator.py
def lambda_handler(event, context):
    # TODO: Parse S3 event
    # TODO: Download CSV from S3
    # TODO: Validate schema
    # TODO: Return validation report
    pass
```text

#### Function 2: Log Transformer

```python
# lambda_log_transformer.py
def lambda_handler(event, context):
    # TODO: Read JSON logs from S3
    # TODO: Parse and enrich (add timestamp, user_id)
    # TODO: Write to processed/ folder
    pass
```text

### Step 4: Desplegar con CLI

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

### Step 5: Configure S3 Trigger

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
```text

### Step 6: Testing

```bash
# Upload CSV to trigger Lambda
aws s3 cp test.csv s3://my-data-lake/uploads/

# Check Lambda logs
aws --endpoint-url=http://localhost:4566 logs tail /aws/lambda/csv-validator

# Verify processed files
aws s3 ls s3://my-data-lake/processed/
```text

## 🧪 Validation

```python
# Test locally
python3 test_lambda.py

# Expected:
# ✓ Lambda function created
# ✓ S3 trigger configured
# ✓ Upload CSV → Lambda invoked
# ✓ Validation report generated
# ✓ Invalid records logged
```text

## 📚 Deliverables

- ✅ `lambda_csv_validator.py` (validates CSV schema)
- ✅ `lambda_log_transformer.py` (transforms JSON logs)
- ✅ `deploy_lambdas.sh` (deployment script)
- ✅ `test_lambda.py` (integration tests)
- ✅ Screenshot showing Lambda execution logs

---

**Hints:** [hints.md](hints.md) | **Next:** [Exercise 05](../05-infrastructure-as-code/README.md)
