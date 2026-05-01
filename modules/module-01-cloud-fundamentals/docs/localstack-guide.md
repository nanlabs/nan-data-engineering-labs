# LocalStack Setup Guide

## 📚 What is LocalStack?

LocalStack is a fully functional local AWS cloud stack that allows you to develop and test AWS applications offline without connecting to a remote cloud provider.

**Benefits:**
- ✅ **Free** - Community edition supports 80+ AWS services
- ✅ **Fast** - No network latency, instant deployments
- ✅ **Safe** - No accidental AWS charges
- ✅ **Offline** - Work without internet connection
- ✅ **Reproducible** - Consistent environment for all developers

## 🚀 Installation

### Option 1: Docker Compose (Recommended)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start LocalStack
cd modules/module-01-cloud-fundamentals
docker-compose up -d

# Verify
docker ps | grep localstack
```

### Option 2: LocalStack CLI

```bash
# Install LocalStack CLI
pip install localstack

# Start LocalStack
localstack start -d

# Check status
localstack status
```

## ⚙️ Configuration

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
      - "4571:4571"
    environment:
      - SERVICES=s3,iam,lambda,sqs,logs,cloudformation
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - ./localstack-data:/tmp/localstack
      - /var/run/docker.sock:/var/run/docker.sock
```

### AWS CLI Configuration

```bash
# Configure AWS CLI for LocalStack
aws configure --profile localstack
# AWS Access Key ID: test
# AWS Secret Access Key: test
# Default region: us-east-1
# Default output format: json

# Or use environment variables
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

### Python Boto3 Configuration

```python
import boto3

# Option 1: Explicit endpoint
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

# Option 2: Environment variable
import os
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
s3 = boto3.client('s3')

# Option 3: Session configuration
session = boto3.Session()
s3 = session.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)
```

## 🎯 Supported Services (Community Edition)

### Storage
- ✅ S3 (buckets, objects, versioning, lifecycle)
- ✅ S3 Select
- ⚠️ Glacier (limited, no retrieval delays)
- ⚠️ EFS (basic support)

### Compute
- ✅ Lambda (Python, Node.js, Java, Go)
- ✅ EC2 (basic support, no actual VMs)
- ✅ ECS (containerized tasks)
- ⚠️ Fargate (limited)

### Database
- ✅ DynamoDB
- ✅ RDS (basic support)
- ✅ Redshift (basic support)
- ⚠️ Aurora (limited)

### Analytics
- ✅ Athena
- ✅ Glue (catalog, crawlers)
- ✅ Kinesis (streams, firehose)
- ⚠️ EMR (limited)

### Integration
- ✅ SQS
- ✅ SNS
- ✅ EventBridge
- ✅ Step Functions

### Management
- ✅ CloudFormation
- ✅ CloudWatch (logs, metrics)
- ✅ Systems Manager (Parameter Store)
- ⚠️ CloudTrail (limited)

### Security
- ✅ IAM (users, groups, roles, policies)
- ✅ Secrets Manager
- ✅ KMS (encryption keys)
- ⚠️ Cognito (limited)

Legend:
- ✅ Full support
- ⚠️ Partial support or limited functionality
- ❌ Not supported in Community Edition

## ⚠️ Limitations

### 1. No Real Resource Constraints

```python
# In real AWS, this would fail with insufficient memory
lambda_function = lambda_client.create_function(
    FunctionName='huge-memory',
    Runtime='python3.9',
    Handler='index.handler',
    Role='arn:aws:iam::000000000000:role/test',
    Code={'ZipFile': b'...'},
    MemorySize=10240  # 10GB - would be expensive in AWS
)
# ✓ Works in LocalStack (no memory validation)
```

**Impact:** Can't test resource limits or quotas

### 2. Simplified IAM

```python
# IAM policies are validated but not fully enforced
s3.put_object(Bucket='protected-bucket', Key='file.txt', Body=b'data')
# ✓ Works even if IAM policy denies access
```

**Impact:** Security testing requires real AWS or mocking

### 3. No Inter-Region Replication Delays

```python
# S3 cross-region replication is instant
s3.put_object(Bucket='source-us-east-1', Key='file.txt', Body=b'data')
# Immediately available in replica bucket (no propagation delay)
```

**Impact:** Can't test eventual consistency scenarios

### 4. Lambda Cold Starts

```python
# No cold start delays
lambda_client.invoke(FunctionName='my-function')
# ✓ Instant response (no initialization time)
```

**Impact:** Performance testing requires real AWS

### 5. Cost Simulation

```python
# All operations are free
s3.put_object(Bucket='my-bucket', Key='huge-file.bin', Body=b'0' * 10**9)
# No storage costs, no request costs
```

**Impact:** Can't test cost optimization strategies with real feedback

### 6. CloudWatch Metrics

```python
# Metrics are stored but not aggregated
cloudwatch.put_metric_data(...)
# ✓ Stored, but no automatic alarms or dashboards
```

**Impact:** Limited monitoring/alerting testing

## 🔧 Troubleshooting

### Issue 1: Connection Refused

```bash
# Symptom
curl http://localhost:4566/_localstack/health
# curl: (7) Failed to connect to localhost port 4566: Connection refused

# Solution
docker ps -a | grep localstack
docker logs localstack-main
docker-compose restart
```

### Issue 2: DNS Resolution

```bash
# Symptom
Error: Could not resolve host: my-bucket.s3.localhost.localstack.cloud

# Solution - Use path-style URLs
aws s3 ls s3://my-bucket --endpoint-url=http://localhost:4566

# Or configure boto3
s3 = boto3.client('s3',
    endpoint_url='http://localhost:4566',
    config=boto3.session.Config(s3={'addressing_style': 'path'})
)
```

### Issue 3: Lambda Deployment Fails

```bash
# Symptom
An error occurred (InvalidParameterValueException):
The role defined for the function cannot be assumed by Lambda.

# Solution - Create role first
aws iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document file://trust-policy.json \
  --endpoint-url=http://localhost:4566
```

### Issue 4: Slow Performance

```bash
# Symptom
Operations take 10+ seconds

# Solution - Allocate more memory
docker update --memory=4g localstack-main
docker-compose restart

# Or in docker-compose.yml
services:
  localstack:
    mem_limit: 4g
```

### Issue 5: Data Persistence

```bash
# Symptom
Data lost after restart

# Solution - Mount volume
volumes:
  - ./localstack-data:/tmp/localstack

# Verify
ls -la ./localstack-data/
```

## 🧪 Testing LocalStack

```bash
# Health check
curl http://localhost:4566/_localstack/health | jq

# Expected output:
# {
#   "services": {
#     "s3": "running",
#     "lambda": "running",
#     "iam": "running"
#   }
# }

# Test S3
aws --endpoint-url=http://localhost:4566 s3 mb s3://test-bucket
aws --endpoint-url=http://localhost:4566 s3 ls

# Test Lambda
aws --endpoint-url=http://localhost:4566 lambda list-functions

# Test IAM
aws --endpoint-url=http://localhost:4566 iam list-users
```

## 🌟 Best Practices

### 1. Use Environment Variables

```bash
# .env file
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1

# Load in scripts
export $(cat .env | xargs)
```

### 2. Wrapper Functions

```python
# utils/aws.py
import os
import boto3

def get_s3_client():
    endpoint = os.getenv('AWS_ENDPOINT_URL')
    return boto3.client('s3', endpoint_url=endpoint)

# Use everywhere
from utils.aws import get_s3_client
s3 = get_s3_client()
```

### 3. Separate Test Data

```bash
# Use different bucket names
BUCKET_NAME="my-bucket-${ENV:-local}"

# local: my-bucket-local
# dev: my-bucket-dev
# prod: my-bucket-prod
```

### 4. Reset Between Tests

```bash
# Reset script
docker-compose down -v
docker-compose up -d
sleep 10  # Wait for startup
```

## 📚 Resources

- [LocalStack Docs](https://docs.localstack.cloud/)
- [LocalStack GitHub](https://github.com/localstack/localstack)
- [LocalStack Coverage](https://docs.localstack.cloud/user-guide/aws/feature-coverage/)
- [LocalStack Pro](https://localstack.cloud/pricing/) (for advanced features)
- [Community Support](https://discuss.localstack.cloud/)

## 🎓 When to Use Real AWS

Consider using real AWS (free tier) for:

1. **IAM Policy Testing** - Verify access controls work correctly
2. **Performance Benchmarking** - Measure real latency and throughput
3. **Cost Optimization** - Test billing impact of changes
4. **Regional Features** - Test multi-region deployments
5. **Production Validation** - Final testing before deployment
6. **Compliance Requirements** - Certain certifications require real AWS

**Tip:** Use LocalStack for 90% of development, real AWS for final validation.
