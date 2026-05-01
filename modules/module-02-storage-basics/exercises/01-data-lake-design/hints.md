# Exercise 01: Data Lake Design - Progressive Hints

Use these hints if you get stuck. Try to solve on your own first!

---

## Level 1: Conceptual Guidance

### Understanding Medallion Architecture

**Bronze Layer (Raw Zone):**
- Think of it as a "staging area" or "landing zone"
- Store data EXACTLY as it arrives (no transformations)
- Focus on **durability** and **retention**
- Optimize for **write performance** and **cost**

**Key Questions:**
- Where should raw CSV files land?
- How long do we need to keep them?
- What if we need to reprocess?

**Silver Layer (Cleaned Zone):**
- This is your "single source of truth"
- Data is validated, deduplicated, and normalized
- Convert to efficient formats (Parquet)
- Optimize for **query performance**

**Key Questions:**
- What transformations are applied?
- How do we partition for analytics?
- What's the retention policy?

**Gold Layer (Curated Zone):**
- Pre-aggregated, business-ready data
- Optimized for specific use cases
- Heavily cached/accessed
- Think "data marts" or "feature stores"

**Key Questions:**
- What aggregations do business users need?
- How do we optimize for BI tools?
- What's our SLA for freshness?

### S3 Bucket Configuration Checklist

For EACH bucket, consider:
1. ☐ **Versioning:** Protect against accidental deletes?
2. ☐ **Encryption:** Sensitive data? (Hint: Always yes)
3. ☐ **Lifecycle:** Move old data to cheaper tiers?
4. ☐ **Logging:** Track who accesses what?
5. ☐ **Public Access:** Should ALWAYS be blocked
6. ☐ **Tags:** How to track costs?

### CloudFormation Resource Types

You'll need:
- `AWS::S3::Bucket` - For each layer
- `AWS::IAM::Role` - For different user personas
- `AWS::S3::BucketPolicy` - For access control

**Structure:**
```yaml
Resources:
  BronzeBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${CompanyName}-bronze-${Environment}'
      # Add configurations here...
```

---

## Level 2: Configuration Best Practices

### S3 Bucket Properties

**1. Versioning Configuration:**
```yaml
VersioningConfiguration:
  Status: Enabled  # Protects against accidental deletes
```

**Why?** Data engineers sometimes delete files accidentally. Versioning allows recovery.

**2. Encryption Configuration:**
```yaml
BucketEncryption:
  ServerSideEncryptionConfiguration:
    - ServerSideEncryptionByDefault:
        SSEAlgorithm: AES256  # SSE-S3 (managed by AWS)
```

**Alternatives:**
- `aws:kms` - For more control (with KMS key)
- `AES256` - Simpler, cheaper, sufficient for most use cases

**3. Lifecycle Rules (Bronze Example):**
```yaml
LifecycleConfiguration:
  Rules:
    - Id: MoveToIA
      Status: Enabled
      Transitions:
        - TransitionInDays: 30
          StorageClass: STANDARD_IA
        - TransitionInDays: 90
          StorageClass: GLACIER
      ExpirationInDays: 730  # Delete after 2 years
```

**Bronze Strategy:**
- 0-30 days: Standard (recent data, might need reprocessing)
- 31-90 days: Standard-IA (infrequent access)
- 91-730 days: Glacier (archival, compliance)
- 730+ days: Delete

**Silver Strategy:**
```yaml
LifecycleConfiguration:
  Rules:
    - Id: MoveToIA
      Status: Enabled
      Transitions:
        - TransitionInDays: 90
          StorageClass: STANDARD_IA
      ExpirationInDays: 365  # Delete after 1 year
```

**Gold Strategy:**
```yaml
# No lifecycle transitions - keep in Standard
# Data is frequently accessed by BI tools
```

**4. Access Logging:**
```yaml
LoggingConfiguration:
  DestinationBucketName: !Ref LogsBucket
  LogFilePrefix: !Sub '${Layer}-access-logs/'
```

**5. Public Access Block:**
```yaml
PublicAccessBlockConfiguration:
  BlockPublicAcls: true
  BlockPublicPolicy: true
  IgnorePublicAcls: true
  RestrictPublicBuckets: true
```

**Why ALL true?** Data lakes should NEVER be public. All access through IAM.

### IAM Role Configuration

**Data Engineer Role (Full Access to Bronze/Silver):**
```yaml
DataEngineerRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service:
              - ec2.amazonaws.com
              - glue.amazonaws.com
          Action: 'sts:AssumeRole'
    Policies:
      - PolicyName: DataEngineerPolicy
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - 's3:GetObject'
                - 's3:PutObject'
                - 's3:DeleteObject'
                - 's3:ListBucket'
              Resource:
                - !GetAtt BronzeBucket.Arn
                - !Sub '${BronzeBucket.Arn}/*'
                - !GetAtt SilverBucket.Arn
                - !Sub '${SilverBucket.Arn}/*'
            - Effect: Allow
              Action:
                - 's3:GetObject'
                - 's3:ListBucket'
              Resource:
                - !GetAtt GoldBucket.Arn
                - !Sub '${GoldBucket.Arn}/*'
```

**Data Scientist Role (Read-Only Silver/Gold):**
```yaml
Policies:
  - PolicyName: DataScientistPolicy
    PolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Action:
            - 's3:GetObject'
            - 's3:ListBucket'
          Resource:
            - !GetAtt SilverBucket.Arn
            - !Sub '${SilverBucket.Arn}/*'
            - !GetAtt GoldBucket.Arn
            - !Sub '${GoldBucket.Arn}/*'
```

### Bucket Policy Examples

**Force Encrypted Uploads:**
```yaml
BronzeBucketPolicy:
  Type: AWS::S3::BucketPolicy
  Properties:
    Bucket: !Ref BronzeBucket
    PolicyDocument:
      Statement:
        - Sid: DenyUnencryptedObjectUploads
          Effect: Deny
          Principal: '*'
          Action: 's3:PutObject'
          Resource: !Sub '${BronzeBucket.Arn}/*'
          Condition:
            StringNotEquals:
              's3:x-amz-server-side-encryption': 'AES256'

        - Sid: DenyInsecureTransport
          Effect: Deny
          Principal: '*'
          Action: 's3:*'
          Resource:
            - !GetAtt BronzeBucket.Arn
            - !Sub '${BronzeBucket.Arn}/*'
          Condition:
            Bool:
              'aws:SecureTransport': false
```

---

## Level 3: Complete Solution Components

### Complete Bronze Bucket

```yaml
BronzeBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub '${CompanyName}-bronze-${Environment}'

    VersioningConfiguration:
      Status: Enabled

    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256

    LifecycleConfiguration:
      Rules:
        - Id: TransitionOldData
          Status: Enabled
          Transitions:
            - TransitionInDays: 30
              StorageClass: STANDARD_IA
            - TransitionInDays: 90
              StorageClass: GLACIER
          ExpirationInDays: 730

    LoggingConfiguration:
      DestinationBucketName: !Ref LogsBucket
      LogFilePrefix: bronze-access-logs/

    PublicAccessBlockConfiguration:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true

    Tags:
      - Key: Environment
        Value: !Ref Environment
      - Key: Layer
        Value: bronze
      - Key: CostCenter
        Value: !Ref CostCenter
      - Key: DataClassification
        Value: raw
```

### Complete Silver Bucket

```yaml
SilverBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub '${CompanyName}-silver-${Environment}'

    VersioningConfiguration:
      Status: Enabled

    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256

    LifecycleConfiguration:
      Rules:
        - Id: TransitionToIA
          Status: Enabled
          Transitions:
            - TransitionInDays: 90
              StorageClass: STANDARD_IA
          ExpirationInDays: 365

    LoggingConfiguration:
      DestinationBucketName: !Ref LogsBucket
      LogFilePrefix: silver-access-logs/

    PublicAccessBlockConfiguration:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true

    Tags:
      - Key: Environment
        Value: !Ref Environment
      - Key: Layer
        Value: silver
      - Key: CostCenter
        Value: !Ref CostCenter
      - Key: DataClassification
        Value: cleaned
```

### Complete Gold Bucket

```yaml
GoldBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub '${CompanyName}-gold-${Environment}'

    VersioningConfiguration:
      Status: Enabled

    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256

    # No lifecycle transitions - keep in Standard
    # Data is frequently accessed

    LoggingConfiguration:
      DestinationBucketName: !Ref LogsBucket
      LogFilePrefix: gold-access-logs/

    PublicAccessBlockConfiguration:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true

    Tags:
      - Key: Environment
        Value: !Ref Environment
      - Key: Layer
        Value: gold
      - Key: CostCenter
        Value: business-intelligence
      - Key: DataClassification
        Value: aggregated
```

### Complete Logs Bucket

```yaml
LogsBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub '${CompanyName}-logs-${Environment}'

    VersioningConfiguration:
      Status: Enabled

    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256

    LifecycleConfiguration:
      Rules:
        - Id: DeleteOldLogs
          Status: Enabled
          ExpirationInDays: 90  # Logs only kept 90 days

    PublicAccessBlockConfiguration:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true

    Tags:
      - Key: Environment
        Value: !Ref Environment
      - Key: Purpose
        Value: access-logs
```

### Complete IAM Role with Full Permissions

```yaml
DataEngineerRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: !Sub 'GlobalMart-DataEngineer-${Environment}'
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service:
              - ec2.amazonaws.com
              - glue.amazonaws.com
              - lambda.amazonaws.com
          Action: 'sts:AssumeRole'
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
    Policies:
      - PolicyName: DataLakeAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            # Full access to Bronze and Silver
            - Effect: Allow
              Action:
                - 's3:GetObject'
                - 's3:PutObject'
                - 's3:DeleteObject'
                - 's3:ListBucket'
                - 's3:GetBucketLocation'
              Resource:
                - !GetAtt BronzeBucket.Arn
                - !Sub '${BronzeBucket.Arn}/*'
                - !GetAtt SilverBucket.Arn
                - !Sub '${SilverBucket.Arn}/*'

            # Read-only access to Gold
            - Effect: Allow
              Action:
                - 's3:GetObject'
                - 's3:ListBucket'
                - 's3:GetBucketLocation'
              Resource:
                - !GetAtt GoldBucket.Arn
                - !Sub '${GoldBucket.Arn}/*'

            # Glue permissions
            - Effect: Allow
              Action:
                - 'glue:*'
              Resource: '*'

    Tags:
      - Key: Environment
        Value: !Ref Environment
      - Key: Role
        Value: data-engineer
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

STACK_NAME="globalmart-data-lake"
TEMPLATE_FILE="data-lake-stack.yaml"
ENVIRONMENT=${1:-dev}

echo "🚀 Deploying GlobalMart Data Lake..."
echo "Environment: $ENVIRONMENT"
echo "Stack: $STACK_NAME"

# Validate template
echo "Validating CloudFormation template..."
aws cloudformation validate-template \
  --template-body file://$TEMPLATE_FILE

# Deploy stack
echo "Deploying stack..."
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://$TEMPLATE_FILE \
  --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags \
    Key=Project,Value=DataLake \
    Key=Owner,Value=DataEngineering

# Wait for completion
echo "Waiting for stack creation..."
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME

# Get outputs
echo "✅ Stack deployed successfully!"
echo ""
echo "Outputs:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

---

## Common Issues & Solutions

### Issue 1: "Bucket name already exists"
**Solution:** Bucket names are globally unique. Change `CompanyName` parameter or add random suffix.

### Issue 2: "AccessDenied creating bucket"
**Solution:** Check your AWS credentials and IAM permissions.

### Issue 3: "LoggingConfiguration error"
**Solution:** Logs bucket must exist BEFORE other buckets reference it. Use `DependsOn`:
```yaml
BronzeBucket:
  Type: AWS::S3::Bucket
  DependsOn: LogsBucket
  Properties:
    LoggingConfiguration:
      DestinationBucketName: !Ref LogsBucket
```

### Issue 4: "Lifecycle rule validation error"
**Solution:** Ensure `TransitionInDays` values increase:
- 30 days → STANDARD_IA
- 90 days → GLACIER (must be > 30)

---

## Verification Checklist

After deployment, verify:
- [ ] `aws s3 ls` shows all 4 buckets
- [ ] `aws s3api get-bucket-versioning` shows Enabled
- [ ] `aws s3api get-bucket-encryption` shows AES256
- [ ] `aws s3api get-bucket-lifecycle-configuration` shows rules
- [ ] `aws iam list-roles` shows created roles
- [ ] Can upload file: `aws s3 cp test.csv s3://globalmart-bronze-dev/test/`
- [ ] Pytest tests pass: `pytest test_exercise_01.py -v`

---

**Still stuck?** Check the complete solution in `solution/data-lake-stack.yaml`
