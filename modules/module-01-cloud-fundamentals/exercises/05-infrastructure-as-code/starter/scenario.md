# Scenario: Declarative Infrastructure at QuickMart

## 📊 Business Context

QuickMart's infrastructure is growing:

- **Manual deployments** → 2-hour setup, error-prone
- **Environment inconsistency** → Dev ≠ Staging ≠ Prod
- **No rollback capability** → Mistakes require manual fixes
- **Poor documentation** → "Ask Sarah how it was set up"
- **Audit requirements** → Need infrastructure change tracking

**CTO's Mandate:** "Everything as code. No more ClickOps."

## 🎯 Your Mission

Create CloudFormation templates for QuickMart's data platform:

### Template 1: Data Lake Stack

**Resources:**
- S3 bucket with versioning
- Lifecycle policies (30d → IA, 90d → Glacier)
- Bucket policy with encryption enforcement
- IAM role for data engineers

**Parameters:**
- `Environment` (dev, staging, prod)
- `DataRetentionDays` (90, 180, 365)

**Outputs:**
- BucketName
- BucketARN
- DataEngineerRoleARN

### Template 2: Processing Stack

**Resources:**
- Lambda function (CSV validator)
- SQS queue for events
- CloudWatch log group
- S3 event notification

**Depends on:** Data Lake Stack (via exported outputs)

### Template 3: Monitoring Stack

**Resources:**
- CloudWatch dashboard
- SNS topic for alerts
- CloudWatch alarms (storage size, Lambda errors)

## 📋 Acceptance Criteria

### Template Requirements
- [x] YAML format (more readable than JSON)
- [x] Parameterized (no hardcoded values)
- [x] Tagged resources (Environment, Project, ManagedBy)
- [x] Outputs for cross-stack references
- [x] DeletionPolicy: Retain for data buckets
- [x] Condition functions for environment-specific logic

### Stack Lifecycle
- [x] Create stack: `aws cloudformation create-stack`
- [x] Update stack: `aws cloudformation update-stack`
- [x] View changes: `aws cloudformation describe-change-set`
- [x] Rollback on failure: automatic
- [x] Delete stack: `aws cloudformation delete-stack`

### Testing
- [x] Deploy to dev environment
- [x] Update with parameter change
- [x] Test rollback (introduce error intentionally)
- [x] Delete and recreate (idempotent)

## 🏗️ Architecture

```
data-lake-stack.yaml
├── S3::Bucket (my-data-lake-${Environment})
├── S3::BucketPolicy (encryption required)
├── IAM::Role (data-engineer-role)
└── Outputs → Export for other stacks

processing-stack.yaml (imports data-lake outputs)
├── Lambda::Function (csv-validator)
├── SQS::Queue (validation-results)
├── Logs::LogGroup (/aws/lambda/csv-validator)
└── Custom::S3Notification (Lambda trigger)

monitoring-stack.yaml
├── CloudWatch::Dashboard (data-platform-overview)
├── SNS::Topic (platform-alerts)
└── CloudWatch::Alarms (storage, errors, costs)
```

## 💡 Implementation Tips

### Parameter Constraints

```yaml
Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - prod
    Description: Deployment environment

  DataRetentionDays:
    Type: Number
    Default: 90
    MinValue: 30
    MaxValue: 365
    Description: Days to retain data before archival
```

### Conditional Resources

```yaml
Conditions:
  IsProduction: !Equals [!Ref Environment, prod]

Resources:
  ProductionAlarm:
    Type: AWS::CloudWatch::Alarm
    Condition: IsProduction
    Properties:
      # Only created in production
```

### Cross-Stack References

```yaml
# In data-lake-stack.yaml
Outputs:
  BucketName:
    Value: !Ref DataLakeBucket
    Export:
      Name: !Sub '${AWS::StackName}-BucketName'

# In processing-stack.yaml
Parameters:
  DataLakeStackName:
    Type: String
    Description: Name of the data lake stack

Resources:
  LambdaFunction:
    Environment:
      Variables:
        BUCKET_NAME: !ImportValue
          Fn::Sub: '${DataLakeStackName}-BucketName'
```

### Tagging Strategy

```yaml
Tags:
  - Key: Environment
    Value: !Ref Environment
  - Key: Project
    Value: QuickMart-DataPlatform
  - Key: ManagedBy
    Value: CloudFormation
  - Key: CostCenter
    Value: Engineering
```

## 🧪 Test Scenarios

### Scenario 1: Multi-Environment Deployment

```bash
# Deploy to dev
aws cloudformation create-stack \
  --stack-name quickmart-data-lake-dev \
  --template-body file://data-lake-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_IAM

# Deploy to prod (different parameters)
aws cloudformation create-stack \
  --stack-name quickmart-data-lake-prod \
  --template-body file://data-lake-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=prod \
    ParameterKey=DataRetentionDays,ParameterValue=365 \
  --capabilities CAPABILITY_IAM
```

### Scenario 2: Update Existing Stack

```bash
# Update lifecycle policy
aws cloudformation update-stack \
  --stack-name quickmart-data-lake-dev \
  --template-body file://data-lake-stack.yaml \
  --parameters ParameterKey=DataRetentionDays,ParameterValue=180
```

### Scenario 3: Test Rollback

```bash
# Introduce intentional error in template (invalid property)
# Then update - CloudFormation will automatically rollback

aws cloudformation update-stack \
  --stack-name quickmart-data-lake-dev \
  --template-body file://data-lake-stack-with-error.yaml

# Watch rollback
aws cloudformation describe-stack-events \
  --stack-name quickmart-data-lake-dev
```

## 📈 Benefits Realized

### Before CloudFormation
```
Setup Time: 2 hours (manual)
Error Rate: 30% (typos, missed steps)
Documentation: Outdated wiki
Rollback: Manual (risky)
Audit Trail: None
```

### After CloudFormation
```
Setup Time: 10 minutes (automated)
Error Rate: <5% (validated templates)
Documentation: Template IS documentation
Rollback: Automatic (safe)
Audit Trail: Git history + CloudFormation events
```

## 🎓 Learning Outcomes

After this exercise:

✅ Write CloudFormation templates in YAML
✅ Use parameters for flexibility
✅ Implement conditions for environment logic
✅ Export/import values between stacks
✅ Tag resources properly
✅ Handle stack updates safely
✅ Implement rollback strategies
✅ Version control infrastructure

---

**Ready?** Head to [README.md](../README.md) for implementation steps!
