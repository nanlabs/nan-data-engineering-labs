# Scenario: Real-Time Data Processing at QuickMart

## 📊 Business Context

QuickMart's data platform needs **serverless event-driven processing** for:

- **CSV Validation:** Daily transaction uploads need schema validation (10k+ rows/day)
- **Log Transformation:** JSON application logs need parsing and enrichment (100k+ events/day)
- **Image Processing:** Product images need thumbnail generation (1k+ uploads/day)
- **Anomaly Detection:** Flag suspicious transactions in real-time

**Current Problem:** Manual processing, 2-hour delay, prone to errors

**Goal:** Automate with AWS Lambda → <5 minute latency, zero manual intervention

## 🏗️ Architecture

```
S3 Upload → Event Notification → Lambda Function → Processed Output
   │                                    │
   └────────────────────────────────────┴─→ CloudWatch Logs
```

## 🎯 Your Mission

Create 3 Lambda functions:

### 1. CSV Validator Function

**Input:** `s3://quickmart-data/uploads/transactions-2024-01-15.csv`

**Validation Rules:**
- Required columns: `transaction_id`, `user_id`, `product_id`, `amount`, `timestamp`
- `amount` must be > 0 and < 10000
- `timestamp` must be valid ISO 8601
- No duplicate `transaction_id`

**Output:**
- Valid records → `s3://quickmart-data/validated/transactions-2024-01-15.csv`
- Invalid records → `s3://quickmart-data/rejected/transactions-2024-01-15-errors.csv`
- Summary to CloudWatch Logs

### 2. Log Transformer Function

**Input:** `s3://quickmart-data/logs/app-2024-01-15.jsonl` (JSON Lines)

**Transformations:**
- Parse JSON
- Add `processed_at` timestamp
- Enrich with user metadata (lookup from DynamoDB if time permits)
- Convert to structured format

**Output:**
- Transformed logs → `s3://quickmart-data/processed/app-2024-01-15.jsonl`

### 3. Anomaly Detector Function

**Input:** Transaction events from CSV validator

**Detection Logic:**
- Amount > $5000 (flag as high-value)
- Multiple transactions from same IP in < 1 minute (flag as suspicious)
- Foreign country transactions for domestic accounts (flag as unusual)

**Output:**
- Alerts to SNS topic
- Flagged transactions to `s3://quickmart-data/alerts/`

## 📋 Acceptance Criteria

### Lambda Function Requirements
- [x] Python 3.9+ runtime
- [x] Memory: 256 MB (adjust if needed)
- [x] Timeout: 30 seconds
- [x] Environment variables for S3 bucket names
- [x] Proper error handling (try/except)
- [x] Structured logging (JSON format)

### S3 Trigger Configuration
- [x] Trigger on `s3:ObjectCreated:*` event
- [x] Filter by prefix (`uploads/transactions/` for CSV validator)
- [x] Filter by suffix (`.csv` for CSV validator, `.jsonl` for log transformer)

### Testing
- [x] Unit tests for validation logic
- [x] Integration test: Upload file → verify processed output
- [x] Error handling test: Upload invalid file → verify rejection

## 🧪 Test Data

### Valid Transaction CSV
```csv
transaction_id,user_id,product_id,amount,timestamp,country
TXN001,USER1234,PROD5678,29.99,2024-01-15T10:30:00Z,US
TXN002,USER5678,PROD1234,149.50,2024-01-15T10:31:00Z,US
```

### Invalid Transaction CSV (for testing error handling)
```csv
transaction_id,user_id,product_id,amount,timestamp,country
TXN003,USER9999,PROD0001,-50.00,2024-01-15T10:32:00Z,US
TXN004,DUPLICATE_ID,PROD0002,99.99,INVALID_DATE,US
```

### Log JSON Lines
```json
{"timestamp":"2024-01-15T10:30:00Z","level":"INFO","user_id":"USER1234","event":"page_view","page":"/products"}
{"timestamp":"2024-01-15T10:30:05Z","level":"INFO","user_id":"USER1234","event":"add_to_cart","product_id":"PROD5678"}
```

## 💡 Implementation Tips

### Lambda Function Template

```python
import json
import boto3
import csv
from io import StringIO
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler for S3 event

    Event structure:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "bucket-name"},
                "object": {"key": "path/to/file.csv"}
            }
        }]
    }
    """

    try:
        # Extract S3 info from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        print(f"Processing {bucket}/{key}")

        # Download file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        # Process content
        results = process_csv(content)

        # Upload results
        upload_results(bucket, key, results)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': len(results['valid']),
                'rejected': len(results['invalid'])
            })
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise


def process_csv(content):
    """Process CSV content and validate"""
    reader = csv.DictReader(StringIO(content))

    valid = []
    invalid = []

    for row in reader:
        if validate_row(row):
            valid.append(row)
        else:
            invalid.append(row)

    return {'valid': valid, 'invalid': invalid}


def validate_row(row):
    """Validate a single row"""
    # TODO: Implement validation logic
    pass
```

### Deployment Package

```bash
# Create deployment package with dependencies
pip install -t package pandas  # If using pandas
cd package
zip -r ../lambda-function.zip .
cd ..
zip -g lambda-function.zip lambda_function.py

# Deploy
aws lambda create-function \
  --function-name csv-validator \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --timeout 30 \
  --memory-size 256
```

## 📈 Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| Cold start | < 3s | TBD |
| Warm execution | < 500ms | TBD |
| Memory usage | < 200 MB | TBD |
| Cost per 1M invocations | < $5 | TBD |

## 🎓 Learning Outcomes

After completing this exercise:

✅ Understand Lambda execution model
✅ Configure S3 event triggers
✅ Handle errors gracefully
✅ Optimize Lambda performance
✅ Monitor with CloudWatch
✅ Calculate serverless costs

---

**Ready?** Head to [README.md](../README.md) for step-by-step instructions!
