# Hints - Exercise 03: S3 Advanced Features

## 🟢 NIVEL 1: Conceptual Hints

### Hint 1.1: Lifecycle Configuration Structure

```python
lifecycle_config = {
    'Rules': [
        {
            'Id': 'RuleName',
            'Status': 'Enabled',
            'Filter': {'Prefix': ''},  # Apply to all objects
            'Transitions': [
                {'Days': 30, 'StorageClass': 'STANDARD_IA'},
                {'Days': 90, 'StorageClass': 'GLACIER'}
            ],
            'Expiration': {'Days': 365}
        }
    ]
}
```

### Hint 1.2: Replication Requirements

**3 Requirements for Replication:**
1. Versioning enabled on BOTH source and destination buckets
2. IAM role with `s3:ReplicateObject` permission
3. Replication configuration with destination bucket ARN

### Hint 1.3: Event Notification Flow

```
S3 Upload → Event Generated → SQS Queue → Lambda/App Processes
```

**Key:** SQS queue policy must allow S3 to send messages!

---

## 🟡 NIVEL 2: Implementation Hints

### Hint 2.1: Enable Versioning

```python
def enable_versioning(bucket_name: str) -> bool:
    try:
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print_success(f"Versioning enabled on {bucket_name}")
        return True
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        return False
```

### Hint 2.2: Create Lifecycle Policy

```python
def create_lifecycle_policy(bucket_name: str) -> bool:
    lifecycle_config = {
        'Rules': [{
            'Id': 'CostOptimization',
            'Status': 'Enabled',
            'Filter': {'Prefix': ''},
            'Transitions': [
                {'Days': 30, 'StorageClass': 'STANDARD_IA'},
                {'Days': 90, 'StorageClass': 'GLACIER'}
            ],
            'Expiration': {'Days': 365}
        }]
    }

    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        return True
    except Exception as e:
        print_error(str(e))
        return False
```

### Hint 2.3: Create SQS Queue

```python
def create_sqs_queue(queue_name: str) -> tuple:
    try:
        # Create queue
        response = sqs.create_queue(QueueName=queue_name)
        queue_url = response['QueueUrl']

        # Get ARN
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = attrs['Attributes']['QueueArn']

        return (queue_url, queue_arn)
    except Exception as e:
        return (None, None)
```

### Hint 2.4: Configure Queue Policy

```python
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "s3.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": queue_arn,
        "Condition": {
            "ArnEquals": {
                "aws:SourceArn": f"arn:aws:s3:::{bucket_name}"
            }
        }
    }]
}

sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={'Policy': json.dumps(policy)}
)
```

---

## 🔴 NIVEL 3: Complete Solutions

### Hint 3.1: Complete Replication Setup

```python
def create_replication_role() -> str:
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    replication_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetReplicationConfiguration",
                    "s3:ListBucket"
                ],
                "Resource": "arn:aws:s3:::my-data-lake-raw"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObjectVersionForReplication",
                    "s3:GetObjectVersionAcl"
                ],
                "Resource": "arn:aws:s3:::my-data-lake-raw/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ReplicateObject",
                    "s3:ReplicateDelete"
                ],
                "Resource": "arn:aws:s3:::my-data-lake-backup/*"
            }
        ]
    }

    try:
        role_response = iam.create_role(
            RoleName='s3-replication-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )

        iam.put_role_policy(
            RoleName='s3-replication-role',
            PolicyName='S3ReplicationPolicy',
            PolicyDocument=json.dumps(replication_policy)
        )

        return role_response['Role']['Arn']
    except:
        return "arn:aws:iam::000000000000:role/s3-replication-role"
```

### Hint 3.2: Complete Bucket Notification

```python
def configure_bucket_notification(bucket_name: str, queue_arn: str) -> bool:
    notification_config = {
        'QueueConfigurations': [{
            'QueueArn': queue_arn,
            'Events': ['s3:ObjectCreated:*'],
            'Filter': {
                'Key': {
                    'FilterRules': [
                        {'Name': 'prefix', 'Value': 'uploads/'}
                    ]
                }
            }
        }]
    }

    try:
        s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=notification_config
        )
        return True
    except Exception as e:
        print_error(str(e))
        return False
```

### Hint 3.3: Test Notifications

```python
def test_notifications(bucket_name: str, queue_url: str) -> bool:
    import time

    test_key = 'uploads/test-notification.txt'

    # Upload file
    s3.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=b'Testing event notifications'
    )

    # Wait for event
    time.sleep(5)

    # Check SQS
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )

    if 'Messages' in response:
        message = json.loads(response['Messages'][0]['Body'])
        if 'Records' in message:
            event = message['Records'][0]
            if event['eventName'].startswith('ObjectCreated'):
                print_success("Event notification received!")
                return True

    return False
```

---

## 🐛 Troubleshooting

### Error: "Versioning must be enabled"

```bash
# Enable on both buckets
aws --endpoint-url=http://localhost:4566 s3api put-bucket-versioning \
  --bucket SOURCE_BUCKET \
  --versioning-configuration Status=Enabled

aws --endpoint-url=http://localhost:4566 s3api put-bucket-versioning \
  --bucket DESTINATION_BUCKET \
  --versioning-configuration Status=Enabled
```

### Error: "Access Denied" on SQS

The queue policy is missing or incorrect. Make sure:
- Principal is `s3.amazonaws.com`
- Action is `sqs:SendMessage`
- Condition includes source bucket ARN

### LocalStack Limitations

**Replication:** LocalStack Community simulates replication but doesn't actually copy objects automatically. You can manually copy to test:

```python
# Manual replication for testing
s3.copy_object(
    CopySource={'Bucket': source_bucket, 'Key': key},
    Bucket=dest_bucket,
    Key=key
)
```

---

## 📚 Additional Resources

- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [S3 Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)
