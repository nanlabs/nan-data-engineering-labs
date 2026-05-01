# Exercise 05: Infrastructure as Code (CloudFormation)

**Duration:** 75-90 minutos | **Difficulty:** ⭐⭐⭐⭐ Advanced Advanced

## 🎯 Objectives

- Definir infraestructura con CloudFormation templates
- Crear stacks (S3 + IAM + Lambda)
- Usar parámetros y outputs
- Implementar best practices (DeletionPolicy, Tags)

## 📖 Conceptos

**CloudFormation** = Infrastructure as Code para AWS. Define recursos en YAML/JSON.

**Ventajas:**
- **Reproducible:** Mismo template → misma infra
- **Version control:** Git para infraestructura
- **Rollback:** Si falla, revierte automáticamente
- **DRY:** Reutiliza templates con parámetros

## 🎬 Pasos

### Paso 1: Copiar Starter

```bash
cp -r starter/ my_solution/
cd my_solution
```

### Paso 2: Completar Template

```yaml
# data-lake-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'QuickMart Data Lake Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  # TODO: Define S3 bucket with versioning
  RawDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      # ... complete properties

  # TODO: Define IAM role for Lambda
  DataProcessorRole:
    Type: AWS::IAM::Role
    Properties:
      # ... complete properties

  # TODO: Define Lambda function
  CsvValidatorFunction:
    Type: AWS::Lambda::Function
    Properties:
      # ... complete properties

Outputs:
  BucketName:
    Value: !Ref RawDataBucket
    Export:
      Name: !Sub '${AWS::StackName}-BucketName'
```

### Paso 3: Deploy Stack

```bash
aws --endpoint-url=http://localhost:4566 cloudformation create-stack \
  --stack-name quickmart-data-lake \
  --template-body file://data-lake-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_IAM
```

### Paso 4: Verificar Stack

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name quickmart-data-lake

# List resources created
aws cloudformation list-stack-resources --stack-name quickmart-data-lake

# Get outputs
aws cloudformation describe-stacks --stack-name quickmart-data-lake \
  --query 'Stacks[0].Outputs'
```

### Paso 5: Update Stack

```bash
# Modify template (add LifecycleConfiguration)
# Then update:
aws cloudformation update-stack \
  --stack-name quickmart-data-lake \
  --template-body file://data-lake-stack.yaml
```

### Paso 6: Delete Stack

```bash
# Cleanup
aws cloudformation delete-stack --stack-name quickmart-data-lake
```

## 🧪 Validación

```bash
python3 test_cloudformation.py

# Expected:
# ✓ Stack created successfully
# ✓ S3 bucket exists with versioning
# ✓ IAM role created with policies
# ✓ Lambda function deployed
# ✓ Outputs contain bucket name
```

## 📚 Entregables

- ✅ `data-lake-stack.yaml` (complete template)
- ✅ `deploy_stack.sh` (deployment script with parameters)
- ✅ `test_cloudformation.py` (validation tests)
- ✅ Screenshot of stack in AWS Console (LocalStack)

## 💡 Best Practices

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain  # Don't delete on stack deletion
    Properties:
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: ManagedBy
          Value: CloudFormation
```

---

**Hints:** [hints.md](hints.md) | **Siguiente:** [Exercise 06](../06-cost-optimization/README.md)
