# 🚀 IMPLEMENTATION GUIDE: CloudMart Serverless Data Lake

## Document Control

| Attribute | Value |
|-----------|-------|
| **Project** | CloudMart Serverless Data Lake |
| **Document** | Implementation Guide |
| **Version** | 1.0 |
| **Last Updated** | March 2026 |
| **Target Audience** | Data Engineers, Cloud Engineers |

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
5. [Phase 2: Data Ingestion](#phase-2-data-ingestion)
6. [Phase 3: Data Cataloging](#phase-3-data-cataloging)
7. [Phase 4: Data Transformation](#phase-4-data-transformation)
8. [Phase 5: Analytics & Querying](#phase-5-analytics--querying)
9. [Testing & Validation](#testing--validation)
10. [Monitoring & Operations](#monitoring--operations)
11. [Optimization](#optimization)
12. [Troubleshooting](#troubleshooting)

---

## 1. Introduction

### 1.1 Purpose

This guide provides step-by-step instructions for implementing the CloudMart Serverless Data Lake on AWS. Follow each phase sequentially to build a production-ready data lake solution.

### 1.2 Implementation Phases

```
Phase 1: Infrastructure Setup (4-5 hours)
├── S3 bucket creation
├── IAM roles and policies
├── CloudFormation templates
└── Networking (VPC endpoints - optional)

Phase 2: Data Ingestion (5-6 hours)
├── Lambda function development
├── S3 event triggers
├── Error handling
└── Monitoring setup

Phase 3: Data Cataloging (3-4 hours)
├── Glue Database creation
├── Glue Crawler configuration
├── Schema management
└── Partitioning strategy

Phase 4: Data Transformation (5-6 hours)
├── Glue ETL job development
├── PySpark transformations
├── Data quality checks
└── Job orchestration

Phase 5: Analytics & Querying (3-4 hours)
├── Athena workgroup setup
├── Query development
├── Performance optimization
└── Visualization integration
```

### 1.3 Expected Outcomes

By the end of this implementation, you will have:

- ✅ Fully functional serverless data lake on AWS
- ✅ Automated data ingestion pipeline
- ✅ Cataloged and query-ready datasets
- ✅ ETL transformations for data quality
- ✅ SQL analytics capability via Athena
- ✅ Monitoring and alerting system
- ✅ Comprehensive documentation

---

## 2. Prerequisites

### 2.1 Technical Requirements

**AWS Account:**
- Active AWS account with admin access (or sufficient permissions)
- AWS CLI installed and configured
- AWS Free Tier eligible (recommended to minimize costs)

**Development Environment:**
- Python 3.9 or later
- AWS CLI v2
- Git
- Code editor (VS Code, PyCharm, etc.)
- Terminal/Shell access

**Knowledge Prerequisites:**
- Modules 01-06 completed
- AWS fundamentals (S3, IAM, Lambda)
- Python programming
- SQL basics
- JSON/CSV data formats

### 2.2 AWS CLI Setup

```bash
# Install AWS CLI (if not already installed)
# On Linux/MacOS:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version

# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1 (or your preferred region)
# - Default output format: json
```

### 2.3 Project Structure Setup

```bash
# Clone or create project directory
mkdir -p ~/cloudmart-data-lake
cd ~/cloudmart-data-lake

# Create directory structure
mkdir -p {infrastructure,ingestion,catalog,transformation,analytics,tests,docs}
mkdir -p data/{sample,raw,processed,curated}
mkdir -p logs
mkdir -p scripts

# Initialize git repository
git init
echo "# CloudMart Serverless Data Lake" > README.md
git add README.md
git commit -m "Initial commit"
```

### 2.4 Environment Variables

Create a `.env` file:

```bash
# .env
export AWS_REGION="us-east-1"
export PROJECT_NAME="cloudmart-datalake"
export ENVIRONMENT="dev"
export S3_BUCKET_PREFIX="cloudmart-dl"
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

Load environment:

```bash
source .env
```

---

## 3. Architecture Overview

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────┬────────────┬────────────┬────────────────────────┤
│ orders.csv  │ customers  │ products   │ clickstream.json       │
│             │ .json      │ .json      │                        │
└──────┬──────┴─────┬──────┴─────┬──────┴────────┬───────────────┘
       │            │            │               │
       │         S3 Upload Event Triggers        │
       │            │            │               │
       └────────────┴────────────┴───────────────┘
                    │
            ┌───────▼───────┐
            │  AWS Lambda   │ ◄─── CloudWatch Logs
            │   Ingestion   │
            │   Function    │
            └───────┬───────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
│   RAW    │  │PROCESSED │  │ CURATED  │
│  Zone    │  │  Zone    │  │  Zone    │
│ (Bronze) │  │ (Silver) │  │  (Gold)  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
     │      ┌───────▼───────┐      │
     │      │  AWS Glue     │      │
     │      │  Crawlers     │      │
     │      └───────┬───────┘      │
     │              │              │
     │      ┌───────▼───────┐      │
     └─────►│  AWS Glue     │◄─────┘
            │  Data Catalog │
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  AWS Glue     │
            │  ETL Jobs     │
            │  (PySpark)    │
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │ Amazon Athena │
            │   (Queries)   │
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  QuickSight   │
            │ Visualization │
            └───────────────┘
```

### 3.2 Data Flow

1. **Ingestion**: Data files uploaded to S3 raw zone
2. **Event Trigger**: S3 event triggers Lambda function
3. **Processing**: Lambda validates and moves data
4. **Cataloging**: Glue Crawlers discover schemas
5. **Transformation**: Glue ETL jobs transform data
6. **Analytics**: Athena queries curated data

### 3.3 AWS Services Used

| Service | Purpose | Cost Impact |
|---------|---------|-------------|
| **S3** | Data storage (all zones) | ~$5/month |
| **Lambda** | Serverless ingestion | ~$1/month |
| **Glue** | Catalog + ETL | ~$10/month |
| **Athena** | SQL queries | ~$5/month |
| **CloudWatch** | Monitoring | ~$3/month |
| **IAM** | Security | Free |
| **CloudFormation** | Infrastructure as Code | Free |
| **Total** | | **~$25-30/month** |

---

## 4. Phase 1: Infrastructure Setup

**Duration:** 4-5 hours
**Goal:** Set up all required AWS infrastructure components

### 4.1 S3 Buckets Creation

#### 4.1.1 Create S3 Buckets

Create three primary buckets for data lake zones:

```bash
# Set variables
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
PROJECT="cloudmart-datalake"

# Create raw data bucket
aws s3 mb s3://${PROJECT}-raw-${ACCOUNT_ID} --region ${REGION}

# Create processed data bucket
aws s3 mb s3://${PROJECT}-processed-${ACCOUNT_ID} --region ${REGION}

# Create curated data bucket
aws s3 mb s3://${PROJECT}-curated-${ACCOUNT_ID} --region ${REGION}

# Create scripts/code bucket
aws s3 mb s3://${PROJECT}-scripts-${ACCOUNT_ID} --region ${REGION}

# Verify buckets
aws s3 ls | grep cloudmart
```

#### 4.1.2 Enable Versioning

```bash
# Enable versioning on all buckets (important for data governance)
aws s3api put-bucket-versioning \
    --bucket ${PROJECT}-raw-${ACCOUNT_ID} \
    --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
    --bucket ${PROJECT}-processed-${ACCOUNT_ID} \
    --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
    --bucket ${PROJECT}-curated-${ACCOUNT_ID} \
    --versioning-configuration Status=Enabled
```

#### 4.1.3 Enable Server-Side Encryption

Create encryption configuration file `encryption-config.json`:

```json
{
  "Rules": [
    {
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }
  ]
}
```

Apply encryption:

```bash
# Apply to all buckets
for bucket in raw processed curated scripts; do
    aws s3api put-bucket-encryption \
        --bucket ${PROJECT}-${bucket}-${ACCOUNT_ID} \
        --server-side-encryption-configuration file://encryption-config.json
done
```

#### 4.1.4 Configure Bucket Lifecycle Policies

Create `lifecycle-raw.json`:

```json
{
  "Rules": [
    {
      "Id": "Move to IA after 30 days",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "Delete old versions after 90 days",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

Apply lifecycle policy:

```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket ${PROJECT}-raw-${ACCOUNT_ID} \
    --lifecycle-configuration file://lifecycle-raw.json
```

#### 4.1.5 Create S3 Folder Structure

```bash
# Raw zone structure
aws s3api put-object --bucket ${PROJECT}-raw-${ACCOUNT_ID} --key orders/
aws s3api put-object --bucket ${PROJECT}-raw-${ACCOUNT_ID} --key customers/
aws s3api put-object --bucket ${PROJECT}-raw-${ACCOUNT_ID} --key products/
aws s3api put-object --bucket ${PROJECT}-raw-${ACCOUNT_ID} --key clickstream/

# Processed zone structure
aws s3api put-object --bucket ${PROJECT}-processed-${ACCOUNT_ID} --key orders/
aws s3api put-object --bucket ${PROJECT}-processed-${ACCOUNT_ID} --key customers/
aws s3api put-object --bucket ${PROJECT}-processed-${ACCOUNT_ID} --key products/
aws s3api put-object --bucket ${PROJECT}-processed-${ACCOUNT_ID} --key clickstream/

# Curated zone structure
aws s3api put-object --bucket ${PROJECT}-curated-${ACCOUNT_ID} --key fact_orders/
aws s3api put-object --bucket ${PROJECT}-curated-${ACCOUNT_ID} --key dim_customers/
aws s3api put-object --bucket ${PROJECT}-curated-${ACCOUNT_ID} --key dim_products/
aws s3api put-object --bucket ${PROJECT}-curated-${ACCOUNT_ID} --key fact_clickstream/
```

### 4.2 IAM Roles and Policies

#### 4.2.1 Lambda Execution Role

Create `lambda-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create `lambda-execution-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-datalake-raw-*/*",
        "arn:aws:s3:::cloudmart-datalake-processed-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-datalake-raw-*",
        "arn:aws:s3:::cloudmart-datalake-processed-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:UpdateTable",
        "glue:CreateTable"
      ],
      "Resource": "*"
    }
  ]
}
```

Create the role:

```bash
# Create Lambda execution role
aws iam create-role \
    --role-name cloudmart-lambda-ingestion-role \
    --assume-role-policy-document file://lambda-trust-policy.json

# Attach custom policy
aws iam put-role-policy \
    --role-name cloudmart-lambda-ingestion-role \
    --policy-name cloudmart-lambda-execution-policy \
    --policy-document file://lambda-execution-policy.json

# Get role ARN (save this!)
LAMBDA_ROLE_ARN=$(aws iam get-role --role-name cloudmart-lambda-ingestion-role --query 'Role.Arn' --output text)
echo "Lambda Role ARN: $LAMBDA_ROLE_ARN"
```

#### 4.2.2 Glue Service Role

Create `glue-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create `glue-service-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-datalake-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-datalake-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:*"
      ],
      "Resource": "*"
    }
  ]
}
```

Create the role:

```bash
# Create Glue service role
aws iam create-role \
    --role-name cloudmart-glue-service-role \
    --assume-role-policy-document file://glue-trust-policy.json

# Attach AWS managed policy
aws iam attach-role-policy \
    --role-name cloudmart-glue-service-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole

# Attach custom policy
aws iam put-role-policy \
    --role-name cloudmart-glue-service-role \
    --policy-name cloudmart-glue-s3-access \
    --policy-document file://glue-service-policy.json

# Get role ARN
GLUE_ROLE_ARN=$(aws iam get-role --role-name cloudmart-glue-service-role --query 'Role.Arn' --output text)
echo "Glue Role ARN: $GLUE_ROLE_ARN"
```

#### 4.2.3 Athena Query Role

Create `athena-user-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-datalake-curated-*",
        "arn:aws:s3:::cloudmart-datalake-curated-*/*",
        "arn:aws:s3:::cloudmart-datalake-athena-results-*",
        "arn:aws:s3:::cloudmart-datalake-athena-results-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::cloudmart-datalake-athena-results-*/*"
      ]
    }
  ]
}
```

### 4.3 CloudFormation Template

Create a comprehensive `cloudmart-infrastructure.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CloudMart Serverless Data Lake Infrastructure'

Parameters:
  ProjectName:
    Type: String
    Default: cloudmart-datalake
    Description: Project name prefix for all resources

  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - prod
    Description: Environment name

Resources:
  # S3 Buckets
  RawDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-raw-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: TransitionToIA
            Status: Enabled
            Transitions:
              - TransitionInDays: 30
                StorageClass: STANDARD_IA
              - TransitionInDays: 90
                StorageClass: GLACIER
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
        - Key: Zone
          Value: Raw

  ProcessedDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-processed-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
        - Key: Zone
          Value: Processed

  CuratedDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-curated-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
        - Key: Zone
          Value: Curated

  ScriptsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-scripts-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  AthenaResultsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-athena-results-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldResults
            Status: Enabled
            ExpirationInDays: 30
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # Lambda Execution Role
  LambdaIngestionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-lambda-ingestion-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - s3:DeleteObject
                Resource:
                  - !Sub '${RawDataBucket.Arn}/*'
                  - !Sub '${ProcessedDataBucket.Arn}/*'
              - Effect: Allow
                Action:
                  - s3:ListBucket
                Resource:
                  - !GetAtt RawDataBucket.Arn
                  - !GetAtt ProcessedDataBucket.Arn
      Tags:
        - Key: Project
          Value: !Ref ProjectName

  # Glue Service Role
  GlueServiceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-glue-service-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: glue.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - s3:DeleteObject
                Resource:
                  - !Sub '${RawDataBucket.Arn}/*'
                  - !Sub '${ProcessedDataBucket.Arn}/*'
                  - !Sub '${CuratedDataBucket.Arn}/*'
                  - !Sub '${ScriptsBucket.Arn}/*'
              - Effect: Allow
                Action:
                  - s3:ListBucket
                Resource:
                  - !GetAtt RawDataBucket.Arn
                  - !GetAtt ProcessedDataBucket.Arn
                  - !GetAtt CuratedDataBucket.Arn
                  - !GetAtt ScriptsBucket.Arn
      Tags:
        - Key: Project
          Value: !Ref ProjectName

  # Glue Database
  GlueDatabase:
    Type: AWS::Glue::Database
    Properties:
      CatalogId: !Ref AWS::AccountId
      DatabaseInput:
        Name: !Sub '${ProjectName}_db'
        Description: CloudMart Data Lake Glue Database

  # CloudWatch Log Group for Lambda
  LambdaLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/${ProjectName}-ingestion'
      RetentionInDays: 30

Outputs:
  RawBucketName:
    Description: Raw data bucket name
    Value: !Ref RawDataBucket
    Export:
      Name: !Sub '${ProjectName}-raw-bucket'

  ProcessedBucketName:
    Description: Processed data bucket name
    Value: !Ref ProcessedDataBucket
    Export:
      Name: !Sub '${ProjectName}-processed-bucket'

  CuratedBucketName:
    Description: Curated data bucket name
    Value: !Ref CuratedDataBucket
    Export:
      Name: !Sub '${ProjectName}-curated-bucket'

  ScriptsBucketName:
    Description: Scripts bucket name
    Value: !Ref ScriptsBucket
    Export:
      Name: !Sub '${ProjectName}-scripts-bucket'

  AthenaResultsBucketName:
    Description: Athena results bucket name
    Value: !Ref AthenaResultsBucket
    Export:
      Name: !Sub '${ProjectName}-athena-results-bucket'

  LambdaRoleArn:
    Description: Lambda execution role ARN
    Value: !GetAtt LambdaIngestionRole.Arn
    Export:
      Name: !Sub '${ProjectName}-lambda-role-arn'

  GlueRoleArn:
    Description: Glue service role ARN
    Value: !GetAtt GlueServiceRole.Arn
    Export:
      Name: !Sub '${ProjectName}-glue-role-arn'

  GlueDatabaseName:
    Description: Glue database name
    Value: !Ref GlueDatabase
    Export:
      Name: !Sub '${ProjectName}-glue-db-name'
```

Deploy the CloudFormation stack:

```bash
# Validate template
aws cloudformation validate-template \
    --template-body file://cloudmart-infrastructure.yaml

# Deploy stack
aws cloudformation create-stack \
    --stack-name cloudmart-datalake-infrastructure \
    --template-body file://cloudmart-infrastructure.yaml \
    --parameters ParameterKey=ProjectName,ParameterValue=cloudmart-datalake \
                 ParameterKey=Environment,ParameterValue=dev \
    --capabilities CAPABILITY_NAMED_IAM

# Monitor stack creation
aws cloudformation wait stack-create-complete \
    --stack-name cloudmart-datalake-infrastructure

# Get stack outputs
aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs' \
    --output table
```

### 4.4 Verification

```bash
# Verify S3 buckets
aws s3 ls | grep cloudmart

# Verify IAM roles
aws iam list-roles | grep cloudmart

# Verify CloudFormation stack
aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].StackStatus'
```

**Expected Result:** All resources created successfully, stack status = `CREATE_COMPLETE`

---

## 5. Phase 2: Data Ingestion

**Duration:** 5-6 hours
**Goal:** Implement automated data ingestion pipeline using Lambda

### 5.1 Lambda Function Development

#### 5.1.1 Create Lambda Function Code

Create `lambda_function.py`:

```python
import json
import boto3
import os
import logging
from datetime import datetime
import csv
from io import StringIO

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET')

def lambda_handler(event, context):
    """
    Main Lambda handler for data ingestion
    Processes files uploaded to raw S3 bucket
    """
    try:
        logger.info(f"Event received: {json.dumps(event)}")

        # Parse S3 event
        for record in event['Records']:
            # Get bucket and key from event
            source_bucket = record['s3']['bucket']['name']
            source_key = record['s3']['object']['key']

            logger.info(f"Processing file: s3://{source_bucket}/{source_key}")

            # Determine data type from path
            data_type = source_key.split('/')[0]

            # Process based on file type
            if source_key.endswith('.csv'):
                process_csv_file(source_bucket, source_key, data_type)
            elif source_key.endswith('.json'):
                process_json_file(source_bucket, source_key, data_type)
            else:
                logger.warning(f"Unsupported file type: {source_key}")
                continue

        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed successfully')
        }

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        raise

def process_csv_file(bucket, key, data_type):
    """Process CSV files (orders)"""
    try:
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        # Parse CSV
        csv_reader = csv.DictReader(StringIO(content))
        rows = list(csv_reader)

        logger.info(f"Parsed {len(rows)} rows from CSV")

        # Validate data
        valid_rows = []
        invalid_rows = []

        for row in rows:
            if validate_order_record(row):
                valid_rows.append(row)
            else:
                invalid_rows.append(row)

        logger.info(f"Valid rows: {len(valid_rows)}, Invalid rows: {len(invalid_rows)}")

        # Convert to JSON Lines format for better processing
        jsonl_content = '\n'.join([json.dumps(row) for row in valid_rows])

        # Generate target key with partition
        current_date = datetime.now()
        target_key = f"{data_type}/year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/{os.path.basename(key).replace('.csv', '.jsonl')}"

        # Upload to processed bucket
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=target_key,
            Body=jsonl_content,
            ContentType='application/x-ndjson'
        )

        logger.info(f"File uploaded to: s3://{PROCESSED_BUCKET}/{target_key}")

        # Log invalid rows if any
        if invalid_rows:
            error_key = f"errors/{data_type}/{datetime.now().isoformat()}.json"
            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=error_key,
                Body=json.dumps(invalid_rows, indent=2)
            )
            logger.warning(f"Invalid rows logged to: {error_key}")

        return len(valid_rows)

    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
        raise

def process_json_file(bucket, key, data_type):
    """Process JSON files (customers, products, clickstream)"""
    try:
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        # Parse JSON
        data = json.loads(content)

        # Handle both single object and array
        if not isinstance(data, list):
            data = [data]

        logger.info(f"Parsed {len(data)} records from JSON")

        # Validate data
        valid_records = []
        invalid_records = []

        for record in data:
            if validate_json_record(record, data_type):
                valid_records.append(record)
            else:
                invalid_records.append(record)

        logger.info(f"Valid records: {len(valid_records)}, Invalid records: {len(invalid_records)}")

        # Convert to JSON Lines format
        jsonl_content = '\n'.join([json.dumps(record) for record in valid_records])

        # Generate target key with partition
        current_date = datetime.now()
        target_key = f"{data_type}/year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/{os.path.basename(key).replace('.json', '.jsonl')}"

        # Upload to processed bucket
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=target_key,
            Body=jsonl_content,
            ContentType='application/x-ndjson'
        )

        logger.info(f"File uploaded to: s3://{PROCESSED_BUCKET}/{target_key}")

        # Log invalid records if any
        if invalid_records:
            error_key = f"errors/{data_type}/{datetime.now().isoformat()}.json"
            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=error_key,
                Body=json.dumps(invalid_records, indent=2)
            )
            logger.warning(f"Invalid records logged to: {error_key}")

        return len(valid_records)

    except Exception as e:
        logger.error(f"Error processing JSON file: {str(e)}", exc_info=True)
        raise

def validate_order_record(record):
    """Validate order record"""
    required_fields = ['order_id', 'customer_id', 'order_date', 'total_amount']

    # Check required fields exist
    for field in required_fields:
        if field not in record or not record[field]:
            return False

    # Validate data types
    try:
        float(record['total_amount'])
    except ValueError:
        return False

    return True

def validate_json_record(record, data_type):
    """Validate JSON records based on data type"""
    if data_type == 'customers':
        required_fields = ['customer_id', 'email', 'first_name', 'last_name']
    elif data_type == 'products':
        required_fields = ['product_id', 'name', 'price']
    elif data_type == 'clickstream':
        required_fields = ['event_id', 'user_id', 'event_type', 'timestamp']
    else:
        return True  # Unknown type, accept it

    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            return False

    return True
```

#### 5.1.2 Create Deployment Package

```bash
# Create deployment directory
mkdir -p lambda_deployment
cd lambda_deployment

# Copy Lambda function
cp ../lambda_function.py .

# Install dependencies (if any were needed, but this function uses only boto3 which is included)
# pip install -r requirements.txt -t .

# Create deployment package
zip -r lambda_deployment.zip .

# Upload to S3
aws s3 cp lambda_deployment.zip s3://cloudmart-datalake-scripts-${ACCOUNT_ID}/lambda/

cd ..
```

#### 5.1.3 Deploy Lambda Function

```bash
# Get role ARN from CloudFormation
LAMBDA_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaRoleArn`].OutputValue' \
    --output text)

# Get processed bucket name
PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucketName`].OutputValue' \
    --output text)

# Create Lambda function
aws lambda create-function \
    --function-name cloudmart-data-ingestion \
    --runtime python3.9 \
    --role ${LAMBDA_ROLE_ARN} \
    --handler lambda_function.lambda_handler \
    --code S3Bucket=cloudmart-datalake-scripts-${ACCOUNT_ID},S3Key=lambda/lambda_deployment.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{PROCESSED_BUCKET=${PROCESSED_BUCKET}}" \
    --description "CloudMart data ingestion Lambda function"

# Wait for function to be active
aws lambda wait function-active \
    --function-name cloudmart-data-ingestion
```

### 5.2 S3 Event Triggers

#### 5.2.1 Add Lambda Permission for S3

```bash
# Get raw bucket name
RAW_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
    --output text)

# Add permission for S3 to invoke Lambda
aws lambda add-permission \
    --function-name cloudmart-data-ingestion \
    --statement-id s3-trigger-permission \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::${RAW_BUCKET}
```

#### 5.2.2 Configure S3 Event Notification

Create `s3-notification-config.json`:

```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "DataIngestionTrigger",
      "LambdaFunctionArn": "arn:aws:lambda:REGION:ACCOUNT_ID:function:cloudmart-data-ingestion",
      "Events": [
        "s3:ObjectCreated:*"
      ],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "orders/"
            },
            {
              "Name": "suffix",
              "Value": ".csv"
            }
          ]
        }
      }
    },
    {
      "Id": "CustomersIngestionTrigger",
      "LambdaFunctionArn": "arn:aws:lambda:REGION:ACCOUNT_ID:function:cloudmart-data-ingestion",
      "Events": [
        "s3:ObjectCreated:*"
      ],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "customers/"
            },
            {
              "Name": "suffix",
              "Value": ".json"
            }
          ]
        }
      }
    },
    {
      "Id": "ProductsIngestionTrigger",
      "LambdaFunctionArn": "arn:aws:lambda:REGION:ACCOUNT_ID:function:cloudmart-data-ingestion",
      "Events": [
        "s3:ObjectCreated:*"
      ],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "products/"
            },
            {
              "Name": "suffix",
              "Value": ".json"
            }
          ]
        }
      }
    },
    {
      "Id": "ClickstreamIngestionTrigger",
      "LambdaFunctionArn": "arn:aws:lambda:REGION:ACCOUNT_ID:function:cloudmart-data-ingestion",
      "Events": [
        "s3:ObjectCreated:*"
      ],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "clickstream/"
            },
            {
              "Name": "suffix",
              "Value": ".json"
            }
          ]
        }
      }
    }
  ]
}
```

Update placeholders and apply:

```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name cloudmart-data-ingestion --query 'Configuration.FunctionArn' --output text)

# Update config file (replace placeholders)
sed -i "s/REGION/${AWS_REGION}/g" s3-notification-config.json
sed -i "s/ACCOUNT_ID/${ACCOUNT_ID}/g" s3-notification-config.json

# Apply notification configuration
aws s3api put-bucket-notification-configuration \
    --bucket ${RAW_BUCKET} \
    --notification-configuration file://s3-notification-config.json
```

### 5.3 Testing Data Ingestion

#### 5.3.1 Create Sample Data Files

Create `sample_orders.csv`:

```csv
order_id,customer_id,order_date,total_amount,status
ORD001,CUST001,2026-03-01,125.50,completed
ORD002,CUST002,2026-03-01,89.99,completed
ORD003,CUST001,2026-03-02,210.00,pending
ORD004,CUST003,2026-03-02,45.75,completed
ORD005,CUST002,2026-03-03,156.20,completed
```

Create `sample_customers.json`:

```json
[
  {
    "customer_id": "CUST001",
    "email": "john.doe@email.com",
    "first_name": "John",
    "last_name": "Doe",
    "signup_date": "2025-01-15",
    "country": "USA"
  },
  {
    "customer_id": "CUST002",
    "email": "jane.smith@email.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "signup_date": "2025-02-20",
    "country": "Canada"
  },
  {
    "customer_id": "CUST003",
    "email": "bob.jones@email.com",
    "first_name": "Bob",
    "last_name": "Jones",
    "signup_date": "2025-03-10",
    "country": "UK"
  }
]
```

Create `sample_products.json`:

```json
[
  {
    "product_id": "PROD001",
    "name": "Wireless Mouse",
    "category": "Electronics",
    "price": 29.99,
    "stock_quantity": 150
  },
  {
    "product_id": "PROD002",
    "name": "USB-C Cable",
    "category": "Accessories",
    "price": 12.99,
    "stock_quantity": 500
  },
  {
    "product_id": "PROD003",
    "name": "Laptop Stand",
    "category": "Accessories",
    "price": 45.00,
    "stock_quantity": 75
  }
]
```

Create `sample_clickstream.json`:

```json
[
  {
    "event_id": "EVT001",
    "user_id": "CUST001",
    "event_type": "page_view",
    "page_url": "/products/wireless-mouse",
    "timestamp": "2026-03-01T10:15:30Z",
    "session_id": "SES12345"
  },
  {
    "event_id": "EVT002",
    "user_id": "CUST001",
    "event_type": "add_to_cart",
    "product_id": "PROD001",
    "timestamp": "2026-03-01T10:16:45Z",
    "session_id": "SES12345"
  },
  {
    "event_id": "EVT003",
    "user_id": "CUST002",
    "event_type": "page_view",
    "page_url": "/products/usb-c-cable",
    "timestamp": "2026-03-01T11:20:15Z",
    "session_id": "SES67890"
  }
]
```

#### 5.3.2 Upload Sample Data

```bash
# Upload files to trigger Lambda
aws s3 cp sample_orders.csv s3://${RAW_BUCKET}/orders/sample_orders.csv
aws s3 cp sample_customers.json s3://${RAW_BUCKET}/customers/sample_customers.json
aws s3 cp sample_products.json s3://${RAW_BUCKET}/products/sample_products.json
aws s3 cp sample_clickstream.json s3://${RAW_BUCKET}/clickstream/sample_clickstream.json
```

#### 5.3.3 Verify Processing

```bash
# Check Lambda logs
aws logs tail /aws/lambda/cloudmart-data-ingestion --follow

# Check processed bucket
aws s3 ls s3://${PROCESSED_BUCKET}/ --recursive

# Download processed file to verify
aws s3 cp s3://${PROCESSED_BUCKET}/orders/year=2026/month=03/day=09/sample_orders.jsonl ./verify_orders.jsonl
cat verify_orders.jsonl
```

**Expected Result:** Files processed and saved to processed bucket in partitioned format.

---

## 6. Phase 3: Data Cataloging

**Duration:** 3-4 hours
**Goal:** Set up AWS Glue Data Catalog with crawlers

### 6.1 Glue Database Setup

```bash
# Get database name from CloudFormation
GLUE_DB=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`GlueDatabaseName`].OutputValue' \
    --output text)

# Verify database
aws glue get-database --name ${GLUE_DB}
```

### 6.2 Create Glue Crawlers

#### 6.2.1 Crawler for Orders (Processed Zone)

```bash
# Get Glue role ARN
GLUE_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`GlueRoleArn`].OutputValue' \
    --output text)

# Create crawler for orders
aws glue create-crawler \
    --name cloudmart-crawler-orders \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${PROCESSED_BUCKET}/orders/\"}]}" \
    --table-prefix processed_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}" \
    --configuration '{"Version":1.0,"Grouping":{"TableGroupingPolicy":"CombineCompatibleSchemas"}}'
```

#### 6.2.2 Crawler for Customers

```bash
aws glue create-crawler \
    --name cloudmart-crawler-customers \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${PROCESSED_BUCKET}/customers/\"}]}" \
    --table-prefix processed_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}" \
    --configuration '{"Version":1.0,"Grouping":{"TableGroupingPolicy":"CombineCompatibleSchemas"}}'
```

#### 6.2.3 Crawler for Products

```bash
aws glue create-crawler \
    --name cloudmart-crawler-products \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${PROCESSED_BUCKET}/products/\"}]}" \
    --table-prefix processed_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}" \
    --configuration '{"Version":1.0,"Grouping":{"TableGroupingPolicy":"CombineCompatibleSchemas"}}'
```

#### 6.2.4 Crawler for Clickstream

```bash
aws glue create-crawler \
    --name cloudmart-crawler-clickstream \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${PROCESSED_BUCKET}/clickstream/\"}]}" \
    --table-prefix processed_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}" \
    --configuration '{"Version":1.0,"Grouping":{"TableGroupingPolicy":"CombineCompatibleSchemas"}}'
```

### 6.3 Run Crawlers

```bash
# Start all crawlers
aws glue start-crawler --name cloudmart-crawler-orders
aws glue start-crawler --name cloudmart-crawler-customers
aws glue start-crawler --name cloudmart-crawler-products
aws glue start-crawler --name cloudmart-crawler-clickstream

# Monitor crawler status
watch -n 5 'aws glue get-crawler --name cloudmart-crawler-orders --query "Crawler.State"'

# Wait for crawlers to complete (check each)
aws glue get-crawler --name cloudmart-crawler-orders --query 'Crawler.State'
aws glue get-crawler --name cloudmart-crawler-customers --query 'Crawler.State'
aws glue get-crawler --name cloudmart-crawler-products --query 'Crawler.State'
aws glue get-crawler --name cloudmart-crawler-clickstream --query 'Crawler.State'
```

### 6.4 Verify Data Catalog

```bash
# List tables in database
aws glue get-tables --database-name ${GLUE_DB} --query 'TableList[].Name'

# Get table details
aws glue get-table --database-name ${GLUE_DB} --name processed_orders

# View table schema
aws glue get-table \
    --database-name ${GLUE_DB} \
    --name processed_orders \
    --query 'Table.StorageDescriptor.Columns' \
    --output table
```

**Expected Result:** Four tables created: `processed_orders`, `processed_customers`, `processed_products`, `processed_clickstream`

---

## 7. Phase 4: Data Transformation

**Duration:** 5-6 hours
**Goal:** Create Glue ETL jobs to transform data into curated zone

### 7.1 ETL Job for Orders Transformation

#### 7.1.1 Create PySpark Script

Create `glue_etl_orders.py`:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, year, month, dayofmonth, sum as _sum, count

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SOURCE_DATABASE', 'TARGET_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from Glue Catalog
source_orders = glueContext.create_dynamic_frame.from_catalog(
    database=args['SOURCE_DATABASE'],
    table_name="processed_orders"
)

# Convert to Spark DataFrame for easier transformations
df_orders = source_orders.toDF()

# Data transformations
df_transformed = df_orders \
    .withColumn("order_date", to_date(col("order_date"))) \
    .withColumn("year", year(col("order_date"))) \
    .withColumn("month", month(col("order_date"))) \
    .withColumn("day", dayofmonth(col("order_date"))) \
    .withColumn("total_amount", col("total_amount").cast("double"))

# Data quality checks
df_cleaned = df_transformed \
    .filter(col("order_id").isNotNull()) \
    .filter(col("customer_id").isNotNull()) \
    .filter(col("total_amount") > 0) \
    .dropDuplicates(["order_id"])

# Create aggregations for analytics
df_summary = df_cleaned \
    .groupBy("customer_id", "year", "month") \
    .agg(
        _sum("total_amount").alias("total_spent"),
        count("order_id").alias("order_count")
    )

# Write to S3 in Parquet format (partitioned by year/month)
target_path = f"s3://{args['TARGET_BUCKET']}/fact_orders/"

df_cleaned.write \
    .mode("overwrite") \
    .format("parquet") \
    .partitionBy("year", "month") \
    .option("compression", "snappy") \
    .save(target_path)

# Write summary table
summary_path = f"s3://{args['TARGET_BUCKET']}/agg_customer_orders/"

df_summary.write \
    .mode("overwrite") \
    .format("parquet") \
    .partitionBy("year", "month") \
    .option("compression", "snappy") \
    .save(summary_path)

job.commit()
```

#### 7.1.2 Upload Script to S3

```bash
# Upload ETL script
aws s3 cp glue_etl_orders.py s3://cloudmart-datalake-scripts-${ACCOUNT_ID}/glue/
```

#### 7.1.3 Create Glue ETL Job

```bash
# Get curated bucket name
CURATED_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`CuratedBucketName`].OutputValue' \
    --output text)

# Create Glue job
aws glue create-job \
    --name cloudmart-etl-orders \
    --role ${GLUE_ROLE_ARN} \
    --command '{
        "Name": "glueetl",
        "ScriptLocation": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/glue/glue_etl_orders.py",
        "PythonVersion": "3"
    }' \
    --default-arguments '{
        "--job-language": "python",
        "--SOURCE_DATABASE": "'${GLUE_DB}'",
        "--TARGET_BUCKET": "'${CURATED_BUCKET}'",
        "--enable-metrics": "",
        "--enable-spark-ui": "true",
        "--spark-event-logs-path": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/sparkui/",
        "--enable-job-insights": "true",
        "--enable-glue-datacatalog": "",
        "--job-bookmark-option": "job-bookmark-enable",
        "--TempDir": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/temp/"
    }' \
    --max-retries 1 \
    --timeout 60 \
    --glue-version "4.0" \
    --number-of-workers 2 \
    --worker-type "G.1X"
```

### 7.2 ETL Job for Customers Dimension

Create `glue_etl_customers.py`:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, datediff, current_date, when

# Initialize
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SOURCE_DATABASE', 'TARGET_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read customers data
source_customers = glueContext.create_dynamic_frame.from_catalog(
    database=args['SOURCE_DATABASE'],
    table_name="processed_customers"
)

df_customers = source_customers.toDF()

# Transformations
df_transformed = df_customers \
    .withColumn("signup_date", to_date(col("signup_date"))) \
    .withColumn("days_since_signup", datediff(current_date(), col("signup_date"))) \
    .withColumn("customer_segment",
        when(datediff(current_date(), col("signup_date")) < 30, "New")
        .when(datediff(current_date(), col("signup_date")) < 180, "Regular")
        .otherwise("Loyal")
    )

# Data quality checks
df_cleaned = df_transformed \
    .filter(col("customer_id").isNotNull()) \
    .filter(col("email").isNotNull()) \
    .dropDuplicates(["customer_id"])

# Write to curated zone
target_path = f"s3://{args['TARGET_BUCKET']}/dim_customers/"

df_cleaned.write \
    .mode("overwrite") \
    .format("parquet") \
    .option("compression", "snappy") \
    .save(target_path)

job.commit()
```

```bash
# Upload and create job
aws s3 cp glue_etl_customers.py s3://cloudmart-datalake-scripts-${ACCOUNT_ID}/glue/

aws glue create-job \
    --name cloudmart-etl-customers \
    --role ${GLUE_ROLE_ARN} \
    --command '{
        "Name": "glueetl",
        "ScriptLocation": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/glue/glue_etl_customers.py",
        "PythonVersion": "3"
    }' \
    --default-arguments '{
        "--job-language": "python",
        "--SOURCE_DATABASE": "'${GLUE_DB}'",
        "--TARGET_BUCKET": "'${CURATED_BUCKET}'",
        "--enable-metrics": "",
        "--enable-glue-datacatalog": "",
        "--job-bookmark-option": "job-bookmark-enable",
        "--TempDir": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/temp/"
    }' \
    --max-retries 1 \
    --timeout 60 \
    --glue-version "4.0" \
    --number-of-workers 2 \
    --worker-type "G.1X"
```

### 7.3 ETL Job for Products Dimension

Create `glue_etl_products.py`:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when

# Initialize
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SOURCE_DATABASE', 'TARGET_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read products data
source_products = glueContext.create_dynamic_frame.from_catalog(
    database=args['SOURCE_DATABASE'],
    table_name="processed_products"
)

df_products = source_products.toDF()

# Transformations
df_transformed = df_products \
    .withColumn("price", col("price").cast("double")) \
    .withColumn("stock_quantity", col("stock_quantity").cast("int")) \
    .withColumn("price_category",
        when(col("price") < 20, "Low")
        .when(col("price") < 50, "Medium")
        .otherwise("High")
    ) \
    .withColumn("stock_status",
        when(col("stock_quantity") == 0, "Out of Stock")
        .when(col("stock_quantity") < 50, "Low Stock")
        .otherwise("In Stock")
    )

# Data quality checks
df_cleaned = df_transformed \
    .filter(col("product_id").isNotNull()) \
    .filter(col("price") > 0) \
    .dropDuplicates(["product_id"])

# Write to curated zone
target_path = f"s3://{args['TARGET_BUCKET']}/dim_products/"

df_cleaned.write \
    .mode("overwrite") \
    .format("parquet") \
    .option("compression", "snappy") \
    .save(target_path)

job.commit()
```

```bash
# Upload and create job
aws s3 cp glue_etl_products.py s3://cloudmart-datalake-scripts-${ACCOUNT_ID}/glue/

aws glue create-job \
    --name cloudmart-etl-products \
    --role ${GLUE_ROLE_ARN} \
    --command '{
        "Name": "glueetl",
        "ScriptLocation": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/glue/glue_etl_products.py",
        "PythonVersion": "3"
    }' \
    --default-arguments '{
        "--job-language": "python",
        "--SOURCE_DATABASE": "'${GLUE_DB}'",
        "--TARGET_BUCKET": "'${CURATED_BUCKET}'",
        "--enable-metrics": "",
        "--enable-glue-datacatalog": "",
        "--job-bookmark-option": "job-bookmark-enable",
        "--TempDir": "s3://cloudmart-datalake-scripts-'${ACCOUNT_ID}'/temp/"
    }' \
    --max-retries 1 \
    --timeout 60 \
    --glue-version "4.0" \
    --number-of-workers 2 \
    --worker-type "G.1X"
```

### 7.4 Run ETL Jobs

```bash
# Start all ETL jobs
aws glue start-job-run --job-name cloudmart-etl-orders
aws glue start-job-run --job-name cloudmart-etl-customers
aws glue start-job-run --job-name cloudmart-etl-products

# Monitor job status
watch -n 10 'aws glue get-job-runs --job-name cloudmart-etl-orders --max-results 1 --query "JobRuns[0].JobRunState"'

# Get job run details
aws glue get-job-runs --job-name cloudmart-etl-orders --max-results 1
```

### 7.5 Create Crawlers for Curated Zone

```bash
# Crawler for fact_orders
aws glue create-crawler \
    --name cloudmart-crawler-curated-orders \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${CURATED_BUCKET}/fact_orders/\"}]}" \
    --table-prefix curated_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}"

# Crawler for dim_customers
aws glue create-crawler \
    --name cloudmart-crawler-curated-customers \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${CURATED_BUCKET}/dim_customers/\"}]}" \
    --table-prefix curated_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}"

# Crawler for dim_products
aws glue create-crawler \
    --name cloudmart-crawler-curated-products \
    --role ${GLUE_ROLE_ARN} \
    --database-name ${GLUE_DB} \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://${CURATED_BUCKET}/dim_products/\"}]}" \
    --table-prefix curated_ \
    --schema-change-policy "{\"UpdateBehavior\": \"UPDATE_IN_DATABASE\", \"DeleteBehavior\": \"LOG\"}"

# Run crawlers
aws glue start-crawler --name cloudmart-crawler-curated-orders
aws glue start-crawler --name cloudmart-crawler-curated-customers
aws glue start-crawler --name cloudmart-crawler-curated-products
```

---

## 8. Phase 5: Analytics & Querying

**Duration:** 3-4 hours
**Goal:** Set up Athena for SQL analytics

### 8.1 Athena Workgroup Setup

```bash
# Get Athena results bucket
ATHENA_RESULTS_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cloudmart-datalake-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`AthenaResultsBucketName`].OutputValue' \
    --output text)

# Create Athena workgroup
aws athena create-work-group \
    --name cloudmart-analytics \
    --configuration "ResultConfigurationUpdates={OutputLocation=s3://${ATHENA_RESULTS_BUCKET}/}" \
    --description "CloudMart Analytics Workgroup"
```

### 8.2 Sample Athena Queries

#### 8.2.1 Query Orders

```sql
-- Total revenue by month
SELECT
    year,
    month,
    COUNT(DISTINCT order_id) as total_orders,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM curated_fact_orders
GROUP BY year, month
ORDER BY year DESC, month DESC;
```

Execute via CLI:

```bash
# Run query
QUERY_ID=$(aws athena start-query-execution \
    --query-string "SELECT year, month, COUNT(DISTINCT order_id) as total_orders, SUM(total_amount) as total_revenue FROM curated_fact_orders GROUP BY year, month ORDER BY year DESC, month DESC LIMIT 10;" \
    --query-execution-context "Database=${GLUE_DB}" \
    --result-configuration "OutputLocation=s3://${ATHENA_RESULTS_BUCKET}/" \
    --work-group cloudmart-analytics \
    --query 'QueryExecutionId' \
    --output text)

# Wait for query to complete
aws athena wait query-execution-complete --query-execution-id ${QUERY_ID}

# Get results
aws athena get-query-results --query-execution-id ${QUERY_ID} --output table
```

#### 8.2.2 Customer Analytics Query

```sql
-- Customer segmentation analysis
SELECT
    customer_segment,
    COUNT(DISTINCT customer_id) as customer_count,
    AVG(days_since_signup) as avg_days_active
FROM curated_dim_customers
GROUP BY customer_segment
ORDER BY customer_count DESC;
```

#### 8.2.3 Product Performance Query

```sql
-- Top selling products (requires join with orders)
SELECT
    p.product_id,
    p.name,
    p.category,
    p.price,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as total_revenue
FROM curated_dim_products p
LEFT JOIN curated_fact_orders o ON p.product_id = o.product_id
GROUP BY p.product_id, p.name, p.category, p.price
ORDER BY total_revenue DESC
LIMIT 10;
```

### 8.3 Create Saved Queries

Create `athena_saved_queries.sh`:

```bash
#!/bin/bash

# Revenue by Month
aws athena create-named-query \
    --name "Revenue by Month" \
    --database ${GLUE_DB} \
    --query-string "SELECT year, month, COUNT(DISTINCT order_id) as total_orders, SUM(total_amount) as total_revenue, AVG(total_amount) as avg_order_value FROM curated_fact_orders GROUP BY year, month ORDER BY year DESC, month DESC;" \
    --description "Monthly revenue analysis"

# Customer Segmentation
aws athena create-named-query \
    --name "Customer Segmentation" \
    --database ${GLUE_DB} \
    --query-string "SELECT customer_segment, COUNT(DISTINCT customer_id) as customer_count, AVG(days_since_signup) as avg_days_active FROM curated_dim_customers GROUP BY customer_segment;" \
    --description "Customer segmentation analysis"

# Product Inventory Status
aws athena create-named-query \
    --name "Product Inventory Status" \
    --database ${GLUE_DB} \
    --query-string "SELECT stock_status, COUNT(*) as product_count, AVG(price) as avg_price FROM curated_dim_products GROUP BY stock_status;" \
    --description "Product inventory status overview"
```

```bash
chmod +x athena_saved_queries.sh
./athena_saved_queries.sh
```

### 8.4 Query Performance Optimization

#### 8.4.1 Partition Projection

For better query performance on partitioned data, enable partition projection:

```sql
-- Enable partition projection on fact_orders table
ALTER TABLE curated_fact_orders
SET TBLPROPERTIES (
  'projection.enabled' = 'true',
  'projection.year.type' = 'integer',
  'projection.year.range' = '2020,2030',
  'projection.month.type' = 'integer',
  'projection.month.range' = '1,12',
  'projection.month.digits' = '2',
  'storage.location.template' = 's3://CURATED_BUCKET/fact_orders/year=${year}/month=${month}'
);
```

---

## 9. Testing & Validation

### 9.1 End-to-End Testing

Create `test_pipeline.sh`:

```bash
#!/bin/bash

set -e

echo "=== CloudMart Data Lake End-to-End Test ==="

# Test 1: Upload test data
echo "Test 1: Uploading test data..."
aws s3 cp test_orders.csv s3://${RAW_BUCKET}/orders/test_orders_$(date +%s).csv

# Test 2: Verify Lambda execution
echo "Test 2: Checking Lambda execution..."
sleep 10
aws logs tail /aws/lambda/cloudmart-data-ingestion --since 1m

# Test 3: Verify processed data
echo "Test 3: Verifying processed data..."
aws s3 ls s3://${PROCESSED_BUCKET}/orders/ --recursive | tail -5

# Test 4: Run crawler
echo "Test 4: Running Glue crawler..."
aws glue start-crawler --name cloudmart-crawler-orders
aws glue wait crawler-ready --name cloudmart-crawler-orders

# Test 5: Run ETL job
echo "Test 5: Running ETL job..."
JOB_RUN_ID=$(aws glue start-job-run --job-name cloudmart-etl-orders --query 'JobRunId' --output text)
echo "Job Run ID: $JOB_RUN_ID"

# Test 6: Query with Athena
echo "Test 6: Running Athena query..."
QUERY_ID=$(aws athena start-query-execution \
    --query-string "SELECT COUNT(*) as record_count FROM curated_fact_orders;" \
    --query-execution-context "Database=${GLUE_DB}" \
    --result-configuration "OutputLocation=s3://${ATHENA_RESULTS_BUCKET}/" \
    --query 'QueryExecutionId' \
    --output text)

aws athena wait query-execution-complete --query-execution-id ${QUERY_ID}
aws athena get-query-results --query-execution-id ${QUERY_ID}

echo "=== All tests completed successfully! ==="
```

### 9.2 Data Quality Checks

Create `validate_data_quality.py`:

```python
import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client('s3')
athena = boto3.client('athena')

def run_athena_query(query, database):
    """Execute Athena query and return results"""
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': f's3://{ATHENA_RESULTS_BUCKET}/'}
    )

    query_id = response['QueryExecutionId']

    # Wait for query to complete
    waiter = athena.get_waiter('query_succeeded')
    waiter.wait(QueryExecutionId=query_id)

    # Get results
    results = athena.get_query_results(QueryExecutionId=query_id)
    return results

# Data quality checks
quality_checks = [
    {
        'name': 'Null Check - Orders',
        'query': 'SELECT COUNT(*) as null_count FROM curated_fact_orders WHERE order_id IS NULL'
    },
    {
        'name': 'Duplicate Check - Orders',
        'query': 'SELECT order_id, COUNT(*) as count FROM curated_fact_orders GROUP BY order_id HAVING COUNT(*) > 1'
    },
    {
        'name': 'Value Range Check - Orders',
        'query': 'SELECT COUNT(*) as invalid_count FROM curated_fact_orders WHERE total_amount <= 0'
    },
    {
        'name': 'Referential Integrity - Orders x Customers',
        'query': '''
            SELECT COUNT(*) as orphan_count
            FROM curated_fact_orders o
            LEFT JOIN curated_dim_customers c ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        '''
    }
]

# Run checks
print("Running Data Quality Checks...\n")
for check in quality_checks:
    print(f"Running: {check['name']}")
    try:
        results = run_athena_query(check['query'], GLUE_DB)
        print(f"Result: {results['ResultSet']['Rows']}\n")
    except Exception as e:
        print(f"Error: {str(e)}\n")
```

---

## 10. Monitoring & Operations

### 10.1 CloudWatch Dashboards

Create CloudWatch dashboard:

```bash
aws cloudwatch put-dashboard \
    --dashboard-name CloudMart-DataLake \
    --dashboard-body file://dashboard-config.json
```

`dashboard-config.json`:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Lambda Invocations"}],
          [".", "Errors", {"stat": "Sum", "label": "Lambda Errors"}],
          [".", "Duration", {"stat": "Average", "label": "Avg Duration"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Metrics",
        "yAxis": {
          "left": {"min": 0}
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/S3", "NumberOfObjects", {"stat": "Average"}],
          [".", "BucketSizeBytes", {"stat": "Average"}]
        ],
        "period": 86400,
        "stat": "Average",
        "region": "us-east-1",
        "title": "S3 Storage Metrics"
      }
    }
  ]
}
```

### 10.2 CloudWatch Alarms

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
    --alarm-name cloudmart-lambda-errors \
    --alarm-description "Alert on Lambda function errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=cloudmart-data-ingestion

# Create alarm for Glue job failures
aws cloudwatch put-metric-alarm \
    --alarm-name cloudmart-glue-job-failures \
    --alarm-description "Alert on Glue job failures" \
    --metric-name glue.driver.ExecutorAllocationManager.executors.numberMaxNeeded \
    --namespace Glue \
    --statistic Average \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 0 \
    --comparison-operator LessThanOrEqualToThreshold
```

---

## 11. Optimization

### 11.1 S3 Storage Optimization

```bash
# Enable S3 Intelligent-Tiering
aws s3api put-bucket-intelligent-tiering-configuration \
    --bucket ${CURATED_BUCKET} \
    --id EntirePrefix \
    --intelligent-tiering-configuration file://intelligent-tiering.json
```

### 11.2 Athena Query Optimization

Best practices:
- Use partitioning
- Use columnar formats (Parquet)
- Compress data (Snappy)
- Limit column selection
- Use approximate functions when possible

### 11.3 Cost Optimization

```bash
# Review S3 storage costs
aws s3api list-buckets --query 'Buckets[?starts_with(Name, `cloudmart`)].Name' | \
while read bucket; do
    echo "Bucket: $bucket"
    aws s3 ls s3://$bucket --recursive --summarize | grep "Total Size"
done

# Review Glue job costs
aws glue get-jobs --query 'Jobs[?starts_with(Name, `cloudmart`)].{Name:Name, MaxCapacity:MaxCapacity}'
```

---

## 12. Troubleshooting

### 12.1 Common Issues

#### Issue: Lambda function timing out

**Solution:**
```bash
# Increase timeout
aws lambda update-function-configuration \
    --function-name cloudmart-data-ingestion \
    --timeout 900
```

#### Issue: Glue crawler not finding partitions

**Solution:**
```bash
# Manually add partition
aws glue create-partition \
    --database-name ${GLUE_DB} \
    --table-name processed_orders \
    --partition-input '{
        "Values": ["2026", "03"],
        "StorageDescriptor": {
            "Location": "s3://'${PROCESSED_BUCKET}'/orders/year=2026/month=03/"
        }
    }'
```

#### Issue: Athena query fails

**Solution:**
```bash
# Check query execution details
aws athena get-query-execution --query-execution-id ${QUERY_ID}

# Repair table partitions
athena_query="MSCK REPAIR TABLE curated_fact_orders;"
aws athena start-query-execution \
    --query-string "$athena_query" \
    --query-execution-context "Database=${GLUE_DB}" \
    --result-configuration "OutputLocation=s3://${ATHENA_RESULTS_BUCKET}/"
```

### 12.2 Debugging Commands

```bash
# Check Lambda logs
aws logs tail /aws/lambda/cloudmart-data-ingestion --follow --since 30m

# Check Glue job logs
aws logs tail /aws-glue/jobs/output --follow --filter-pattern "cloudmart-etl-orders"

# List recent S3 uploads
aws s3 ls s3://${RAW_BUCKET}/ --recursive | tail -20

# Check crawler status
aws glue get-crawler --name cloudmart-crawler-orders --query 'Crawler.{State:State,LastCrawl:LastCrawl}'

# Check table schemas
aws glue get-table --database-name ${GLUE_DB} --name curated_fact_orders --query 'Table.StorageDescriptor.Columns'
```

---

## 13. Documentation Deliverables

### 13.1 Architecture Diagram

Create using draw.io or similar tool showing:
- Data sources
- S3 buckets (zones)
- Lambda functions
- Glue components
- Athena
- Data flow

### 13.2 Technical Documentation

Include:
- Infrastructure setup details
- IAM policies and roles
- Lambda function code
- Glue ETL scripts
- Athena queries
- Troubleshooting guide

### 13.3 Operations Runbook

Document:
- Daily operations procedures
- Monitoring checkpoints
- Incident response procedures
- Backup and recovery
- Cost management

---

## 14. Next Steps

After completing this implementation:

1. **Extend functionality:**
   - Add more data sources
   - Implement incremental loads
   - Add data quality framework
   - Integrate with QuickSight

2. **Enhance security:**
   - Implement fine-grained access control
   - Add data encryption at rest
   - Enable AWS CloudTrail
   - Implement VPC endpoints

3. **Optimize performance:**
   - Tune Glue job parameters
   - Optimize Athena queries
   - Implement caching strategies

4. **Automate operations:**
   - Create CI/CD pipeline
   - Implement automated testing
   - Set up automated alerts
   - Create backup automation

---

## 15. Conclusion

Congratulations! You've successfully implemented a production-ready serverless data lake on AWS. This implementation demonstrates:

✅ Infrastructure as Code with CloudFormation
✅ Event-driven architecture with Lambda
✅ Data cataloging and governance with Glue
✅ ETL processing with PySpark
✅ SQL analytics with Athena
✅ Monitoring and alerting with CloudWatch
✅ Security best practices with IAM
✅ Cost optimization strategies

**Total Implementation Cost:** ~$25-30/month (with sample data)

**Skills Demonstrated:**
- AWS serverless architecture
- Python development
- PySpark/ETL development
- SQL analytics
- Infrastructure as Code
- DevOps practices
- Data governance

---

**Document Version:** 1.0
**Last Updated:** March 2026
**Total Lines:** ~1,550
