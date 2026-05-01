# Hints - Exercise 05: Infrastructure as Code

## 🟢 NIVEL 1: Conceptual Hints

### Hint 1.1: CloudFormation Structure

Un template tiene 4 secciones principales:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: What this template creates

Parameters:  # Input values
Resources:   # AWS resources (REQUIRED)
Outputs:     # Values to export
```

### Hint 1.2: Parameters vs. Hardcoding

❌ **Bad:**
```yaml
BucketName: quickmart-data-lake-dev
```

✅ **Good:**
```yaml
BucketName: !Sub 'quickmart-data-lake-${Environment}'
```

### Hint 1.3: Cross-Stack References

Stack A exports:
```yaml
Outputs:
  BucketName:
    Export:
      Name: !Sub '${AWS::StackName}-BucketName'
```

Stack B imports:
```yaml
BucketName: !ImportValue data-lake-stack-BucketName
```

---

## 🟡 NIVEL 2: Implementation Hints

### Hint 2.1: S3 Bucket with Lifecycle

```yaml
DataLakeBucket:
  Type: AWS::S3::Bucket
  DeletionPolicy: Retain  # Don't delete on stack deletion
  Properties:
    BucketName: !Sub 'quickmart-data-lake-${Environment}'

    VersioningConfiguration:
      Status: Enabled

    LifecycleConfiguration:
      Rules:
        - Id: TransitionToIA
          Status: Enabled
          Transitions:
            - TransitionInDays: !Ref DataRetentionDays
              StorageClass: STANDARD_IA
            - TransitionInDays: !Ref GlacierTransitionDays
              StorageClass: GLACIER

        - Id: DeleteOldVersions
          Status: Enabled
          NoncurrentVersionExpirationInDays: 90
```

### Hint 2.2: Bucket Policy (Encryption Required)

```yaml
DataLakeBucketPolicy:
  Type: AWS::S3::BucketPolicy
  Properties:
    Bucket: !Ref DataLakeBucket
    PolicyDocument:
      Statement:
        - Sid: DenyUnencryptedObjectUploads
          Effect: Deny
          Principal: '*'
          Action: 's3:PutObject'
          Resource: !Sub '${DataLakeBucket.Arn}/*'
          Condition:
            StringNotEquals:
              s3:x-amz-server-side-encryption: 'AES256'

        - Sid: DenyInsecureTransport
          Effect: Deny
          Principal: '*'
          Action: 's3:*'
          Resource:
            - !GetAtt DataLakeBucket.Arn
            - !Sub '${DataLakeBucket.Arn}/*'
          Condition:
            Bool:
              aws:SecureTransport: false
```

### Hint 2.3: IAM Role with Inline Policy

```yaml
DataEngineerRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: !Sub 'data-engineer-role-${Environment}'

    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service:
              - ec2.amazonaws.com
              - lambda.amazonaws.com
          Action: 'sts:AssumeRole'

    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

    Policies:
      - PolicyName: DataLakeAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - s3:GetObject
                - s3:PutObject
                - s3:DeleteObject
                - s3:ListBucket
              Resource:
                - !GetAtt DataLakeBucket.Arn
                - !Sub '${DataLakeBucket.Arn}/*'
```

### Hint 2.4: Conditional Resources

```yaml
Conditions:
  IsProduction: !Equals [!Ref Environment, prod]
  IsDevelopment: !Equals [!Ref Environment, dev]
  EnableBackup: !Or
    - !Equals [!Ref Environment, prod]
    - !Equals [!Ref Environment, staging]

Resources:
  BackupVault:
    Type: AWS::Backup::BackupVault
    Condition: EnableBackup
    Properties:
      BackupVaultName: !Sub 'data-lake-backup-${Environment}'
```

### Hint 2.5: Deployment Script

```bash
#!/bin/bash
set -e

ENDPOINT_URL="http://localhost:4566"
STACK_NAME="quickmart-data-lake"
ENVIRONMENT="${1:-dev}"

# Validate template
aws --endpoint-url=$ENDPOINT_URL cloudformation validate-template \
  --template-body file://data-lake-stack.yaml

# Deploy stack
aws --endpoint-url=$ENDPOINT_URL cloudformation deploy \
  --stack-name $STACK_NAME-$ENVIRONMENT \
  --template-file data-lake-stack.yaml \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    DataRetentionDays=90 \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for completion
aws --endpoint-url=$ENDPOINT_URL cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME-$ENVIRONMENT
```

---

## 🔴 NIVEL 3: Complete Solution

### Hint 3.1: Complete Data Lake Stack

See [solution/data-lake-stack.yaml](solution/data-lake-stack.yaml) for:
- Parameterized bucket with lifecycle rules
- Encryption-enforced bucket policy
- IAM role with inline policies
- Conditional DeletionPolicy
- Tagged resources
- Exported outputs

### Hint 3.2: Processing Stack (Nested)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'QuickMart Processing Infrastructure'

Parameters:
  DataLakeStackName:
    Type: String
    Description: Name of the data lake stack

  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]

Resources:
  ValidationQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'validation-results-${Environment}'
      VisibilityTimeout: 300
      MessageRetentionPeriod: 1209600  # 14 days

  ValidatorFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub 'csv-validator-${Environment}'
      Runtime: python3.9
      Handler: lambda_csv_validator.lambda_handler
      Timeout: 30
      MemorySize: 256

      Role: !ImportValue
        Fn::Sub: '${DataLakeStackName}-DataEngineerRoleArn'

      Environment:
        Variables:
          BUCKET_NAME: !ImportValue
            Fn::Sub: '${DataLakeStackName}-BucketName'
          QUEUE_URL: !Ref ValidationQueue

      Code:
        ZipFile: |
          import json
          def lambda_handler(event, context):
              return {'statusCode': 200}

  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/csv-validator-${Environment}'
      RetentionInDays: 7

Outputs:
  QueueUrl:
    Value: !Ref ValidationQueue
    Export:
      Name: !Sub '${AWS::StackName}-QueueUrl'

  FunctionArn:
    Value: !GetAtt ValidatorFunction.Arn
    Export:
      Name: !Sub '${AWS::StackName}-FunctionArn'
```

### Hint 3.3: Stack Update Script

```bash
#!/bin/bash

ENDPOINT_URL="http://localhost:4566"
STACK_NAME="quickmart-data-lake-dev"

# Create change set
CHANGE_SET_NAME="update-$(date +%Y%m%d-%H%M%S)"

aws --endpoint-url=$ENDPOINT_URL cloudformation create-change-set \
  --stack-name $STACK_NAME \
  --change-set-name $CHANGE_SET_NAME \
  --template-body file://data-lake-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=DataRetentionDays,ParameterValue=180

# Wait for change set
aws --endpoint-url=$ENDPOINT_URL cloudformation wait change-set-create-complete \
  --stack-name $STACK_NAME \
  --change-set-name $CHANGE_SET_NAME

# Review changes
echo "Proposed changes:"
aws --endpoint-url=$ENDPOINT_URL cloudformation describe-change-set \
  --stack-name $STACK_NAME \
  --change-set-name $CHANGE_SET_NAME \
  --query 'Changes[].{Action:ResourceChange.Action,Resource:ResourceChange.LogicalResourceId,Type:ResourceChange.ResourceType}' \
  --output table

# Prompt for confirmation
read -p "Execute change set? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    aws --endpoint-url=$ENDPOINT_URL cloudformation execute-change-set \
      --stack-name $STACK_NAME \
      --change-set-name $CHANGE_SET_NAME

    echo "Waiting for update to complete..."
    aws --endpoint-url=$ENDPOINT_URL cloudformation wait stack-update-complete \
      --stack-name $STACK_NAME

    echo "✓ Update complete"
fi
```

---

## 🧪 Testing Tips

### Test 1: Validate Syntax

```bash
# YAML linting
yamllint data-lake-stack.yaml

# CloudFormation validation
aws cloudformation validate-template \
  --template-body file://data-lake-stack.yaml
```

### Test 2: Multi-Environment

```bash
# Deploy to all environments
for env in dev staging prod; do
    ./deploy_stack.sh $env
done

# Verify stacks
aws cloudformation list-stacks \
  --query 'StackSummaries[?StackStatus==`CREATE_COMPLETE`].StackName'
```

### Test 3: Rollback Testing

```bash
# Introduce intentional error
cat > error-template.yaml << EOF
Resources:
  InvalidBucket:
    Type: AWS::S3::Bucket
    Properties:
      InvalidProperty: ThisWillFail
EOF

# Try to update (will rollback)
aws cloudformation update-stack \
  --stack-name quickmart-data-lake-dev \
  --template-body file://error-template.yaml

# Monitor rollback
aws cloudformation describe-stack-events \
  --stack-name quickmart-data-lake-dev \
  --query 'StackEvents[?ResourceStatus==`ROLLBACK_IN_PROGRESS`]'
```

### Test 4: Drift Detection

```bash
# Make manual change
aws s3api put-bucket-tagging \
  --bucket quickmart-data-lake-dev \
  --tagging 'TagSet=[{Key=Manual,Value=Change}]'

# Detect drift
aws cloudformation detect-stack-drift \
  --stack-name quickmart-data-lake-dev

# View drift
aws cloudformation describe-stack-resource-drifts \
  --stack-name quickmart-data-lake-dev \
  --stack-resource-drift-status-filters MODIFIED
```

---

## 🐛 Common Issues

### Error: "Template format error: YAML not well-formed"

**Fix:** Check indentation (2 spaces, not tabs)

```bash
# Convert tabs to spaces
expand -t 2 template.yaml > template-fixed.yaml
```

### Error: "No updates are to be performed"

**Cause:** No changes detected

**Fix:** Modify a property or parameter

### Error: "Unresolved resource dependencies"

**Cause:** Circular dependency or missing resource

**Fix:** Check `!Ref` and `!GetAtt` references

### Error: "Stack cannot be deleted (DeletionPolicy: Retain)"

**Expected:** Data buckets are retained for safety

**Fix:** Manually delete bucket if needed:
```bash
aws s3 rb s3://quickmart-data-lake-dev --force
```

---

## 📚 Additional Resources

- [CloudFormation Template Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-reference.html)
- [Intrinsic Functions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html)
- [Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) - Template validator
