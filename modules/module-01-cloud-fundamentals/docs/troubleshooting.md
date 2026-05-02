# Troubleshooting Guide - Module 01

## 🔧 Common Issues and Solutions

### AWS CLI Issues

#### Error: "Unable to locate credentials"

**Symptom:**

```bash
aws s3 ls
# Unable to locate credentials. You can configure credentials by running "aws configure".
```

**Solution:**

```bash
# Configure AWS CLI for LocalStack
aws configure --profile localstack
# Enter: test / test / us-east-1 / json

# Use profile
aws s3 ls --endpoint-url=http://localhost:4566 --profile localstack

# Or set environment variables
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

---

#### Error: "Could not connect to the endpoint URL"

**Symptom:**
```bash
aws s3 ls
# Could not connect to the endpoint URL: "https://s3.us-east-1.amazonaws.com/"
```

**Solution:**
```bash
# Always specify LocalStack endpoint
aws s3 ls --endpoint-url=http://localhost:4566

# Or set environment variable
export AWS_ENDPOINT_URL=http://localhost:4566
aws s3 ls
```

---

### LocalStack Issues

#### Error: "Connection refused to localhost:4566"

**Symptom:**
```bash
curl http://localhost:4566/_localstack/health
# curl: (7) Failed to connect to localhost port 4566: Connection refused
```

**Solutions:**

1. **Check if LocalStack is running:**
```bash
docker ps | grep localstack
# No output = not running

# Start LocalStack
docker-compose up -d
```

2. **Check logs:**
```bash
docker logs localstack-main
# Look for errors or "Ready" message
```

3. **Restart LocalStack:**
```bash
docker-compose restart
sleep 10  # Wait for startup
curl http://localhost:4566/_localstack/health
```

4. **Check port conflicts:**
```bash
# See what's using port 4566
sudo lsof -i :4566
sudo netstat -tulpn | grep 4566

# Kill conflicting process
sudo kill -9 <PID>
```

---

#### Error: "LocalStack is slow or unresponsive"

**Symptom:**
- Commands take 30+ seconds
- Docker CPU usage at 100%
- Out of memory errors

**Solutions:**

1. **Increase Docker resources:**
```bash
# For Docker Desktop: Settings → Resources → Memory (4GB+)

# For docker-compose:
services:
  localstack:
    mem_limit: 4g
    cpus: 2
```

2. **Limit enabled services:**
```yaml
# docker-compose.yml
environment:
  - SERVICES=s3,iam,lambda,sqs  # Only what you need
```

3. **Clear data and restart:**
```bash
docker-compose down -v
rm -rf ./localstack-data/*
docker-compose up -d
```

---

### S3 Issues

#### Error: "NoSuchBucket"

**Symptom:**
```bash
aws s3 ls s3://my-bucket --endpoint-url=http://localhost:4566
# An error occurred (NoSuchBucket) when calling the ListObjectsV2 operation: The specified bucket does not exist
```

**Solutions:**

1. **Create bucket first:**
```bash
aws s3 mb s3://my-bucket --endpoint-url=http://localhost:4566
```

2. **Check bucket name:**
```bash
# List all buckets
aws s3 ls --endpoint-url=http://localhost:4566

# Bucket names must be lowercase, no underscores
# Bad: my_bucket, My-Bucket
# Good: my-bucket, mybucket
```

3. **Check LocalStack is running:**
```bash
docker ps | grep localstack
```

---

#### Error: "Access Denied" when uploading to S3

**Symptom:**
```bash
aws s3 cp file.txt s3://my-bucket/ --endpoint-url=http://localhost:4566
# upload failed: An error occurred (AccessDenied) when calling the PutObject operation: Access Denied
```

**Solutions:**

1. **Check bucket policy:**
```bash
aws s3api get-bucket-policy \
  --bucket my-bucket \
  --endpoint-url=http://localhost:4566
```

2. **Use runct IAM role/user:**
```python
# In Python
import boto3

s3 = boto3.client('s3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)
```

3. **LocalStack limitation:** IAM is not fully enforced. If it fails, check bucket existence and network.

---

#### Error: "SignatureDoesNotMatch"

**Symptom:**
```
The request signature we calculated does not match the signature you provided.
```

**Solution:**
```bash
# Use simple credentials for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

# Avoid special characters in credentials
```

---

### Lambda Issues

#### Error: "The role defined for the function cannot be assumed by Lambda"

**Symptom:**
```bash
aws lambda create-function ... --role arn:aws:iam::000000000000:role/lambda-role
# InvalidParameterValueException: The role defined for the function cannot be assumed by Lambda.
```

**Solution:**

1. **Create IAM role first:**
```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document file://trust-policy.json \
  --endpoint-url=http://localhost:4566
```

2. **Use LocalStack account ID:**
```bash
# LocalStack uses 000000000000 as account ID
ARN="arn:aws:iam::000000000000:role/lambda-role"
```

---

#### Error: "Lambda function not found" after creation

**Symptom:**
```bash
aws lambda invoke --function-name my-function output.json
# ResourceNotFoundException: Function not found
```

**Solutions:**

1. **Wait a few seconds:** LocalStack needs time to initialize
```bash
sleep 5
aws lambda get-function --function-name my-function
```

2. **Check function name:**
```bash
# List all functions
aws lambda list-functions --endpoint-url=http://localhost:4566
```

3. **Verify deployment package:**
```bash
# Check zip file is valid
unzip -l function.zip
```

---

#### Error: Lambda timeout after 3 seconds

**Symptom:**
```
Task timed out after 3.00 seconds
```

**Solution:**
```bash
# Increase timeout (max: 900 seconds)
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 30 \
  --endpoint-url=http://localhost:4566
```

---

### IAM Issues

#### Error: "User already exists"

**Symptom:**
```bash
aws iam create-user --user-name alice
# EntityAlreadyExistsException: User alice already exists
```

**Solutions:**

1. **Delete and recreate:**
```bash
aws iam delete-user --user-name alice --endpoint-url=http://localhost:4566
aws iam create-user --user-name alice --endpoint-url=http://localhost:4566
```

2. **Update instead of create:**
```bash
# Check if exists first
aws iam get-user --user-name alice || aws iam create-user --user-name alice
```

---

#### Error: "MalformedPolicyDocument"

**Symptom:**
```
MalformedPolicyDocument: The policy failed syntax validation
```

**Solution:**
```bash
# Validate JSON
cat policy.json | python -m json.tool

# Common issues:
# - Missing comma
# - Trailing comma
# - Wrong quotes ("" vs '')
# - Invalid Action/Resource format
```

**Valid policy structure:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::bucket-name/*"
    }
  ]
}
```

---

### Python/Boto3 Issues

#### Error: "ModuleNotFoundError: No module named 'boto3'"

**Solution:**
```bash
# Install boto3
pip install boto3

# Or use requirements.txt
pip install -r requirements.txt

# For virtual environment
python -m venv venv
source venv/bin/activate
pip install boto3
```

---

#### Error: "EndpointConnectionError: Could not connect to the endpoint URL"

**Symptom:**
```python
s3 = boto3.client('s3')
s3.list_buckets()
# EndpointConnectionError: Could not connect to the endpoint URL
```

**Solution:**
```python
# Specify LocalStack endpoint
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

# Or use environment variable
import os
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
s3 = boto3.client('s3')
```

---

#### Error: "botocore.exceptions.ClientError: An error occurred (404)"

**Symptom:**
```python
s3.get_object(Bucket='my-bucket', Key='file.txt')
# ClientError: An error occurred (404) when calling the GetObject operation: Not Found
```

**Solutions:**

1. **Check object exists:**
```python
# List objects
response = s3.list_objects_v2(Bucket='my-bucket')
for obj in response.get('Contents', []):
    print(obj['Key'])
```

2. **Check key is runct:**
```python
# Keys are case-sensitive and include folders
# Bad: 'File.txt', '/data/file.txt'
# Good: 'file.txt', 'data/file.txt'
```

3. **Upload file first:**
```python
s3.put_object(Bucket='my-bucket', Key='file.txt', Body=b'content')
```

---

### CloudFormation Issues

#### Error: "Template format error: YAML not well-formed"

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('template.yaml'))"

# Common issues:
# - Indentation (use 2 spaces, not tabs)
# - Missing colon after key
# - Inrunct list formatting
```

**Fix indentation:**
```bash
# Convert tabs to spaces
expand -t 2 template.yaml > fixed.yaml
```

---

#### Error: "Unresolved resource dependencies"

**Symptom:**
```
CREATE_FAILED: Unresolved resource dependencies [LambdaFunction] in the Resources block
```

**Solution:**
```yaml
# Ensure dependencies exist
Resources:
  # Create role first
  LambdaRole:
    Type: AWS::IAM::Role
    Properties: ...

  # Then reference it
  LambdaFunction:
    Type: AWS::Lambda::Function
    DependsOn: LambdaRole  # Explicit dependency
    Properties:
      Role: !GetAtt LambdaRole.Arn  # Reference
```

---

### Pytest Issues

#### Error: "ImportError: attempted relative import with no known parent package"

**Solution:**
```bash
# Run from project root
cd /path/to/training-cloud-data/modules/module-01-cloud-fundamentals
pytest validation/

# Not from validation/ directory
```

---

#### Error: "fixture 'wait_for_localstack' not found"

**Solution:**
```bash
# Ensure conftest.py exists
ls validation/conftest.py

# Run pytest with verbose
pytest -v validation/test_exercise_01.py
```

---

#### Error: All tests fail immediately

**Symptom:**
```
====== FAILED validation/test_exercise_01.py::test_bucket_exists ======
```

**Solutions:**

1. **Check LocalStack is running:**
```bash
docker ps | grep localstack
```

2. **Increase wait time in conftest.py:**
```python
# conftest.py
@pytest.fixture(scope='session', autouse=True)
def wait_for_localstack():
    max_attempts = 60  # Increase from 30
    # ...
```

3. **Run setup script first:**
```bash
./scripts/setup.sh
pytest validation/
```

---

## 🐛 Debugging Tips

### Enable Debug Logging

```bash
# LocalStack
docker-compose up  # Without -d to see logs in realtime

# AWS CLI
aws s3 ls --endpoint-url=http://localhost:4566 --debug

# Python boto3
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Service Health

```bash
# LocalStack health endpoint
curl http://localhost:4566/_localstack/health | jq

# Specific service
curl http://localhost:4566/_localstack/health | jq '.services.s3'
```

### Inspect Docker

```bash
# Container logs
docker logs localstack-main --tail 100

# Container shell
docker exec -it localstack-main bash

# Inside container
awslocal s3 ls  # AWS CLI with LocalStack endpoint pre-configured
```

### Network Diagnostics

```bash
# Test connectivity
curl -v http://localhost:4566

# Check DNS
nslookup localhost
ping localhost

# Check firewall
sudo ufw status
sudo iptables -L
```

---

## 📞 Getting Help

### Community Resources

- [LocalStack Discussions](https://discuss.localstack.cloud/)
- [AWS Community Forums](https://repost.aws/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/localstack)

### Reporting Issues

When reporting issues, include:

1. **Environment:**
```bash
docker --version
docker-compose --version
python --version
aws --version
cat /etc/os-release
```

2. **LocalStack logs:**
```bash
docker logs localstack-main > localstack.log
```

3. **Minimal reproduction:**
```bash
# Commands to reproduce
aws s3 mb s3://test-bucket --endpoint-url=http://localhost:4566
aws s3 cp file.txt s3://test-bucket/ --endpoint-url=http://localhost:4566
# Error occurs here
```

4. **Expected vs actual behavior**

---

## ✅ Verification Checklist

Before asking for help, verify:

- [ ] LocalStack is running (`docker ps`)
- [ ] Health endpoint responds (`curl http://localhost:4566/_localstack/health`)
- [ ] AWS CLI configured (`aws configure list`)
- [ ] Endpoint URL specified (`--endpoint-url=http://localhost:4566`)
- [ ] Credentials set (test/test for LocalStack)
- [ ] Python boto3 installed (`pip list | grep boto3`)
- [ ] Scripts are executable (`chmod +x script.sh`)
- [ ] You're in runct directory (`pwd`)
- [ ] No typos in bucket/function names (case-sensitive)
- [ ] Waited for LocalStack startup (10-30 seconds)

---

**Pro Tip:** 90% of issues are solved by restarting LocalStack and checking endpoints. When in doubt, `docker-compose restart` and wait 30 seconds.
