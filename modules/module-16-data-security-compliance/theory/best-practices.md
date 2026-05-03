# Security Best Practices for Data Engineering

## Table of Contents
- [IAM Best Practices](#iam-best-practices)
- [Data Protection](#data-protection)
- [Network Security](#network-security)
- [Monitoring and Logging](#monitoring-and-logging)
- [Incident Response](#incident-response)
- [Compliance](#compliance)
- [DevSecOps](#devsecops)

---

## IAM Best Practices

### **1. Use IAM Roles Instead of Users**
❌ **Bad**:
```python
# Hardcoded credentials in code
aws_access_key = 'AKIAIOSFODNN7EXAMPLE'
aws_secret_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

s3 = boto3.client('s3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)
```

✅ **Good**:
```python
# Use IAM role attached to EC2/Lambda/ECS
s3 = boto3.client('s3')  # Automatically uses instance role
```

### **2. Enable MFA for Sensitive Operations**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "Action": [
      "s3:DeleteObject",
      "s3:DeleteBucket",
      "dynamodb:DeleteTable"
    ],
    "Resource": "*",
    "Condition": {
      "BoolIfExists": {"aws:MultiFactorAuthPresent": false}
    }
  }]
}
```

### **3. Use Permission Boundaries**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*",
    "Condition": {
      "StringEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}
    }
  }, {
    "Effect": "Deny",
    "Action": [
      "iam:CreateUser",
      "iam:DeleteUser",
      "iam:CreateAccessKey"
    ],
    "Resource": "*"
  }]
}
```

### **4. Implement Least Privilege**
❌ **Bad** (overly permissive):
```json
{
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "*"
}
```

✅ **Good** (specific permissions):
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::my-bucket/data/*"
}
```

### **5. Rotate Access Keys Regularly**
```bash
# Automated key rotation script
aws iam create-access-key --user-name data-engineer
aws iam update-access-key --access-key-id OLD_KEY --status Inactive
# Wait 48 hours to ensure no usage
aws iam delete-access-key --access-key-id OLD_KEY
```

### **6. Use IAM Access Analyzer**
```python
import boto3

analyzer = boto3.client('accessanalyzer')

# Create analyzer
response = analyzer.create_analyzer(
    analyzerName='organization-analyzer',
    type='ORGANIZATION'
)

# List findings
findings = analyzer.list_findings(analyzerArn=response['arn'])

for finding in findings['findings']:
    if finding['status'] == 'ACTIVE':
        print(f"⚠️  {finding['resourceType']}: {finding['resource']}")
        print(f"   External access from: {finding['principal']}")
```

---

## Data Protection

### **1. Encrypt Data at Rest**

**S3 Buckets**:
```python
import boto3

s3 = boto3.client('s3')

# Default encryption (SSE-KMS)
s3.put_bucket_encryption(
    Bucket='data-lake-bucket',
    ServerSideEncryptionConfiguration={
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {
                'SSEAlgorithm': 'aws:kms',
                'KMSMasterKeyID': 'arn:aws:kms:us-east-1:123456789012:key/12345'
            },
            'BucketKeyEnabled': True  # Reduces KMS costs
        }]
    }
)

# Enforce encryption with bucket policy
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Deny",
        "Principal": "*",
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::data-lake-bucket/*",
        "Condition": {
            "StringNotEquals": {
                "s3:x-amz-server-side-encryption": "aws:kms"
            }
        }
    }]
}

s3.put_bucket_policy(Bucket='data-lake-bucket', Policy=json.dumps(bucket_policy))
```

**RDS Databases**:
```python
rds = boto3.client('rds')

# Create encrypted DB instance
rds.create_db_instance(
    DBInstanceIdentifier='analytics-db',
    DBInstanceClass='db.r5.xlarge',
    Engine='postgres',
    MasterUsername='admin',
    MasterUserPassword='SecurePass123!',
    StorageEncrypted=True,
    KmsKeyId='arn:aws:kms:us-east-1:123456789012:key/12345',
    BackupRetentionPeriod=30,  # Encrypted backups
    EnableCloudwatchLogsExports=['postgresql']
)
```

### **2. Encrypt Data in Transit**

**ALB with TLS 1.2+**:
```python
elbv2 = boto3.client('elbv2')

# Create HTTPS listener
elbv2.create_listener(
    LoadBalancerArn='arn:aws:elasticloadbalancing:...',
    Protocol='HTTPS',
    Port=443,
    Certificates=[{
        'CertificateArn': 'arn:aws:acm:us-east-1:123456789012:certificate/...'
    }],
    DefaultActions=[{
        'Type': 'forward',
        'TargetGroupArn': 'arn:aws:elasticloadbalancing:...'
    }],
    SslPolicy='ELBSecurityPolicy-TLS-1-2-2017-01'  # Enforce TLS 1.2+
)
```

### **3. Implement Data Classification**

```python
# Tag resources by classification
s3.put_object_tagging(
    Bucket='data-lake',
    Key='customer-data.csv',
    Tagging={
        'TagSet': [
            {'Key': 'DataClassification', 'Value': 'Confidential'},
            {'Key': 'PIIData', 'Value': 'true'},
            {'Key': 'Compliance', 'Value': 'GDPR'}
        ]
    }
)

# Use tags in IAM policies
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Deny",
        "Action": "s3:GetObject",
        "Resource": "*",
        "Condition": {
            "StringEquals": {
                "s3:ExistingObjectTag/DataClassification": "Confidential"
            },
            "StringNotEquals": {
                "aws:PrincipalTag/SecurityClearance": "High"
            }
        }
    }]
}
```

### **4. Enable Versioning and MFA Delete**

```python
# Enable versioning
s3.put_bucket_versioning(
    Bucket='critical-data',
    VersioningConfiguration={'Status': 'Enabled'}
)

# Enable MFA delete (CLI only)
# aws s3api put-bucket-versioning --bucket critical-data \
#   --versioning-configuration Status=Enabled,MFADelete=Enabled \
#   --mfa "arn:aws:iam::123456789012:mfa/user 123456"
```

### **5. Use S3 Object Lock (WORM)**

```python
# Enable Object Lock on bucket creation
s3.create_bucket(
    Bucket='compliance-archive',
    ObjectLockEnabledForBucket=True
)

# Set default retention
s3.put_object_lock_configuration(
    Bucket='compliance-archive',
    ObjectLockConfiguration={
        'ObjectLockEnabled': 'Enabled',
        'Rule': {
            'DefaultRetention': {
                'Mode': 'COMPLIANCE',  # Cannot be deleted by anyone
                'Years': 7
            }
        }
    }
)
```

---

## Network Security

### **1. Use Security Groups as Stateful Firewalls**

```python
ec2 = boto3.client('ec2')

# Create restrictive security group
sg = ec2.create_security_group(
    GroupName='data-engineers-sg',
    Description='Data engineers access',
    VpcId='vpc-12345'
)

# Allow SSH only from corporate VPN
ec2.authorize_security_group_ingress(
    GroupId=sg['GroupId'],
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [{'CidrIp': '10.0.0.0/8', 'Description': 'Corporate VPN'}]
    }]
)
```

### **2. Use VPC Endpoints**

```python
# S3 Gateway Endpoint (no charges)
ec2.create_vpc_endpoint(
    VpcId='vpc-12345',
    ServiceName='com.amazonaws.us-east-1.s3',
    RouteTableIds=['rtb-12345']
)

# KMS Interface Endpoint (charged)
ec2.create_vpc_endpoint(
    VpcId='vpc-12345',
    VpcEndpointType='Interface',
    ServiceName='com.amazonaws.us-east-1.kms',
    SubnetIds=['subnet-12345']
)
```

### **3. Enable VPC Flow Logs**

```python
ec2.create_flow_logs(
    ResourceType='VPC',
    ResourceIds=['vpc-12345'],
    TrafficType='ALL',  # ACCEPT, REJECT, or ALL
    LogDestinationType='cloud-watch-logs',
    LogGroupName='/aws/vpc/flowlogs',
    DeliverLogsPermissionArn='arn:aws:iam::123456789012:role/flowlogsRole'
)
```

---

## Monitoring and Logging

### **1. Enable CloudTrail Organization Trail**

```python
cloudtrail = boto3.client('cloudtrail')

cloudtrail.create_trail(
    Name='organization-trail',
    S3BucketName='cloudtrail-logs-bucket',
    IsOrganizationTrail=True,
    IsMultiRegionTrail=True,
    IncludeGlobalServiceEvents=True,
    EnableLogFileValidation=True,  # Integrity checking
    EventSelectors=[{
        'ReadWriteType': 'All',
        'IncludeManagementEvents': True,
        'DataResources': [{
            'Type': 'AWS::S3::Object',
            'Values': ['arn:aws:s3:::data-lake/*']
        }]
    }]
)
```

### **2. Set Up CloudWatch Alarms**

```python
cloudwatch = boto3.client('cloudwatch')

# Alarm for root account usage
cloudwatch.put_metric_alarm(
    AlarmName='root-account-usage',
    MetricName='RootAccountUsage',
    Namespace='CloudTrailMetrics',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=1,
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:security-alerts']
)
```

### **3. Enable GuardDuty**

```python
guardduty = boto3.client('guardduty')

# Enable GuardDuty
detector = guardduty.create_detector(Enable=True)

# Enable all data sources
guardduty.update_detector(
    DetectorId=detector['DetectorId'],
    Enable=True,
    DataSources={
        'S3Logs': {'Enable': True},
        'Kubernetes': {'AuditLogs': {'Enable': True}},
        'MalwareProtection': {'ScanEc2InstanceWithFindings': {'EbsVolumes': {'Enable': True}}}
    }
)
```

---

## Incident Response

### **1. Create IR Playbooks**

**Example: Compromised IAM Credentials**
```python
def respond_to_compromised_credentials(access_key_id):
    """Automated response to compromised credentials"""
    iam = boto3.client('iam')

    # 1. Disable access key
    iam.update_access_key(
        AccessKeyId=access_key_id,
        Status='Inactive'
    )
    print(f"✓ Disabled access key: {access_key_id}")

    # 2. Attach deny-all policy
    user = iam.get_access_key_last_used(AccessKeyId=access_key_id)['UserName']
    iam.put_user_policy(
        UserName=user,
        PolicyName='DenyAll-IncidentResponse',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]
        })
    )
    print(f"✓ Applied deny-all policy to user: {user}")

    # 3. Notify security team
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789012:security-incidents',
        Subject='🚨 Compromised Credentials Detected',
        Message=f'Access key {access_key_id} for user {user} has been disabled.'
    )
    print("✓ Security team notified")
```

### **2. Use AWS Systems Manager for Remediation**

```python
ssm = boto3.client('ssm')

# Create automation document
ssm.create_document(
    Content=json.dumps({
        "schemaVersion": "0.3",
        "description": "Isolate compromised EC2 instance",
        "mainSteps": [{
            "name": "isolateInstance",
            "action": "aws:executeAwsApi",
            "inputs": {
                "Service": "ec2",
                "Api": "ModifyInstanceAttribute",
                "InstanceId": "{{ InstanceId }}",
                "Groups": ["{{ ForensicsSecurityGroup }}"]
            }
        }]
    }),
    Name='IsolateCompromisedInstance',
    DocumentType='Automation'
)
```

---

## Compliance

### **CIS AWS Foundations Benchmark**

```python
# Example: Check 1.3 - Credentials unused for 90 days
import datetime

iam = boto3.client('iam')

users = iam.list_users()['Users']

for user in users:
    keys = iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']

    for key in keys:
        last_used = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])

        if 'LastUsedDate' in last_used['AccessKeyLastUsed']:
            days = (datetime.datetime.now(datetime.timezone.utc) -
                    last_used['AccessKeyLastUsed']['LastUsedDate']).days

            if days > 90:
                print(f"⚠️  {user['UserName']}: Access key {key['AccessKeyId']} unused for {days} days")
```

---

## DevSecOps

### **1. Scan Infrastructure as Code**

```bash
# Terraform security scanning
tfsec .

# CloudFormation validation
cfn-lint template.yaml

# Python code security
bandit -r src/
```

### **2. Dependency Vulnerability Scanning**

```bash
# Python dependencies
safety check

# Node.js dependencies
npm audit

# Container images
trivy image my-app:latest
```

### **3. Pre-commit Hooks**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/awslabs/git-secrets
    rev: master
    hooks:
      - id: git-secrets
  - repo: https://github.com/zricethezav/gitleaks
    rev: v8.16.0
    hooks:
      - id: gitleaks
```

---

## Key Takeaways

✅ **IAM**: Use roles, enable MFA, rotate keys, least privilege
✅ **Data Protection**: Encrypt at rest/transit, versioning, Object Lock
✅ **Network**: Security groups, VPC endpoints, Flow Logs
✅ **Monitoring**: CloudTrail, GuardDuty, CloudWatch alarms
✅ **Incident Response**: Automated playbooks, isolation, notification
✅ **Compliance**: CIS Benchmark, automated checks
✅ **DevSecOps**: Scan IaC, dependencies, pre-commit hooks
