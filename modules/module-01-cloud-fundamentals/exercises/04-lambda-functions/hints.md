# Hints - Exercise 04: Lambda Functions

## 🟢 NIVEL 1: Conceptual Hints

### Hint 1.1: Lambda Event Structure

Cuando S3 invoca tu Lambda, el evento tiene esta estructura:

```python
event = {
    "Records": [{
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "my-bucket"},
            "object": {"key": "uploads/file.csv", "size": 1024}
        }
    }]
}
```

Extrae bucket y key del primer Record.

### Hint 1.2: CSV Validation Logic

Para cada fila, valida:
- `transaction_id`: no vacío
- `user_id`: matches pattern `USER####`
- `amount`: debe ser número > 0 y < 10000
- `timestamp`: debe parsear con `datetime.fromisoformat()`

### Hint 1.3: Uploading Results

```python
# Upload to S3
s3.put_object(
    Bucket=bucket,
    Key='validated/file.csv',
    Body=csv_content.encode('utf-8')
)
```

---

## 🟡 NIVEL 2: Implementation Hints

### Hint 2.1: Parse S3 Event

```python
def lambda_handler(event, context):
    # Extract S3 info
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    print(f"Processing s3://{bucket}/{key}")
```

### Hint 2.2: Download and Parse CSV

```python
import csv
from io import StringIO

# Download file
response = s3.get_object(Bucket=bucket, Key=key)
content = response['Body'].read().decode('utf-8')

# Parse CSV
reader = csv.DictReader(StringIO(content))
rows = list(reader)
```

### Hint 2.3: Validation Function

```python
import re
from datetime import datetime

def validate_row(row):
    errors = []

    # Check transaction_id
    if not row.get('transaction_id'):
        errors.append("transaction_id is required")

    # Check user_id format
    if not re.match(r'^USER\d{4}$', row.get('user_id', '')):
        errors.append("user_id must match USER####")

    # Check amount
    try:
        amount = float(row.get('amount', 0))
        if amount <= 0 or amount >= 10000:
            errors.append("amount must be between 0 and 10000")
    except ValueError:
        errors.append("amount must be a number")

    # Check timestamp
    try:
        datetime.fromisoformat(row.get('timestamp', '').replace('Z', '+00:00'))
    except:
        errors.append("timestamp must be valid ISO 8601")

    return (len(errors) == 0, ", ".join(errors))
```

### Hint 2.4: Convert to CSV String

```python
def format_csv(records):
    if not records:
        return ""

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

    return output.getvalue()
```

---

## 🔴 NIVEL 3: Complete Implementation

### Hint 3.1: Complete Lambda Handler

```python
def lambda_handler(event, context):
    try:
        # Parse event
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        print(f"Processing s3://{bucket}/{key}")

        # Download file
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        # Validate CSV
        result = validate_csv(content)

        print(f"Validation complete: {len(result['valid'])} valid, {len(result['invalid'])} invalid")

        # Upload results
        filename = key.split('/')[-1]
        upload_results(bucket, filename, result['valid'], result['invalid'])

        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': len(result['valid']),
                'rejected': len(result['invalid'])
            })
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Hint 3.2: Complete Validation Logic

```python
def validate_csv(content):
    reader = csv.DictReader(StringIO(content))
    valid = []
    invalid = []

    for row in reader:
        is_valid, error_msg = validate_row(row)

        if is_valid:
            valid.append(row)
        else:
            row['error'] = error_msg
            invalid.append(row)

    return {'valid': valid, 'invalid': invalid}
```

### Hint 3.3: Complete Upload Function

```python
def upload_results(bucket, filename, valid_records, invalid_records):
    # Upload valid records
    if valid_records:
        valid_csv = format_csv(valid_records)
        s3.put_object(
            Bucket=bucket,
            Key=f'validated/{filename}',
            Body=valid_csv.encode('utf-8')
        )
        print(f"Uploaded {len(valid_records)} valid records to validated/{filename}")

    # Upload invalid records
    if invalid_records:
        # Add error column if not present
        if invalid_records and 'error' not in invalid_records[0]:
            for record in invalid_records:
                record['error'] = 'validation_failed'

        invalid_csv = format_csv(invalid_records)
        error_filename = filename.replace('.csv', '-errors.csv')
        s3.put_object(
            Bucket=bucket,
            Key=f'rejected/{error_filename}',
            Body=invalid_csv.encode('utf-8')
        )
        print(f"Uploaded {len(invalid_records)} invalid records to rejected/{error_filename}")
```

---

## 🧪 Testing Tips

### Local Testing

```python
# test_lambda_local.py
import json
from lambda_csv_validator import lambda_handler

# Create test event
event = {
    "Records": [{
        "s3": {
            "bucket": {"name": "quickmart-data"},
            "object": {"key": "uploads/transactions/test.csv"}
        }
    }]
}

# Run locally
result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

### Testing with LocalStack

```bash
# Upload test file
aws --endpoint-url=http://localhost:4566 s3 cp test.csv \
  s3://quickmart-data/uploads/transactions/

# Check Lambda logs
aws --endpoint-url=http://localhost:4566 logs tail \
  /aws/lambda/csv-validator --follow

# Verify results
aws --endpoint-url=http://localhost:4566 s3 ls \
  s3://quickmart-data/validated/

aws --endpoint-url=http://localhost:4566 s3 ls \
  s3://quickmart-data/rejected/
```

### Create Test Data

```bash
# Valid transactions
cat > test-valid.csv << EOF
transaction_id,user_id,product_id,amount,timestamp,country
TXN001,USER1234,PROD5678,29.99,2024-01-15T10:30:00Z,US
TXN002,USER5678,PROD1234,149.50,2024-01-15T10:31:00Z,US
EOF

# Invalid transactions
cat > test-invalid.csv << EOF
transaction_id,user_id,product_id,amount,timestamp,country
TXN003,INVALID_USER,PROD0001,-50.00,2024-01-15T10:32:00Z,US
TXN004,USER9999,PROD0002,99.99,INVALID_DATE,US
TXN005,,PROD0003,15000.00,2024-01-15T10:33:00Z,US
EOF
```

---

## 🐛 Common Issues

### Error: "Unable to import module"

**Cause:** Lambda can't find your handler function.

**Fix:** Ensure handler is set to `lambda_csv_validator.lambda_handler`

### Error: "Task timed out after 3.00 seconds"

**Cause:** Lambda timeout too short.

**Fix:** Increase timeout to 30 seconds:
```bash
aws lambda update-function-configuration \
  --function-name csv-validator \
  --timeout 30
```

### Error: "KeyError: 'Records'"

**Cause:** Event structure unexpected.

**Fix:** Add defensive checks:
```python
if 'Records' not in event or len(event['Records']) == 0:
    return {'statusCode': 400, 'body': 'No records in event'}
```

### Error: "Access Denied" writing to S3

**Cause:** Lambda role doesn't have S3 permissions.

**Fix:** Attach policy:
```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::quickmart-data/*"
}
```

---

## 📚 Additional Resources

- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [S3 Event Notification](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
