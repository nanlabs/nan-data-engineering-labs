#!/bin/bash
# Initialize AWS infrastructure for Module 16
set -e

echo "======================================"
echo "Module 16: AWS Security Infrastructure"
echo "======================================"

# Configuration
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "AWS Account ID: $ACCOUNT_ID"
echo "AWS Region: $REGION"

# 1. Create KMS Keys
echo ""
echo "Creating KMS keys..."

echo "  - Data Lake Key"
DATA_LAKE_KEY=$(aws kms create-key \
  --description "Data Lake encryption key" \
  --key-policy "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Sid\": \"Enable IAM policies\",
      \"Effect\": \"Allow\",
      \"Principal\": {\"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\"},
      \"Action\": \"kms:*\",
      \"Resource\": \"*\"
    }]
  }" \
  --query 'KeyMetadata.KeyId' --output text)

aws kms create-alias --alias-name alias/data-lake --target-key-id $DATA_LAKE_KEY
aws kms enable-key-rotation --key-id $DATA_LAKE_KEY
echo "    ✓ Data Lake Key: $DATA_LAKE_KEY"

echo "  - Database Key"
DB_KEY=$(aws kms create-key \
  --description "Database encryption key" \
  --query 'KeyMetadata.KeyId' --output text)

aws kms create-alias --alias-name alias/database --target-key-id $DB_KEY
aws kms enable-key-rotation --key-id $DB_KEY
echo "    ✓ Database Key: $DB_KEY"

echo "  - Application Key"
APP_KEY=$(aws kms create-key \
  --description "Application secrets encryption key" \
  --query 'KeyMetadata.KeyId' --output text)

aws kms create-alias --alias-name alias/application --target-key-id $APP_KEY
aws kms enable-key-rotation --key-id $APP_KEY
echo "    ✓ Application Key: $APP_KEY"

# 2. Create S3 bucket for CloudTrail
echo ""
echo "Creating CloudTrail S3 bucket..."
TRAIL_BUCKET="cloudtrail-logs-${ACCOUNT_ID}-${REGION}"

aws s3 mb s3://$TRAIL_BUCKET --region $REGION

# Apply bucket policy for CloudTrail
cat > /tmp/trail-bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck",
      "Effect": "Allow",
      "Principal": {"Service": "cloudtrail.amazonaws.com"},
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::$TRAIL_BUCKET"
    },
    {
      "Sid": "AWSCloudTrailWrite",
      "Effect": "Allow",
      "Principal": {"Service": "cloudtrail.amazonaws.com"},
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::$TRAIL_BUCKET/AWSLogs/${ACCOUNT_ID}/*",
      "Condition": {
        "StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}
      }
    }
  ]
}
EOF

aws s3api put-bucket-policy --bucket $TRAIL_BUCKET --policy file:///tmp/trail-bucket-policy.json
aws s3api put-bucket-encryption --bucket $TRAIL_BUCKET \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "'$DATA_LAKE_KEY'"
      },
      "BucketKeyEnabled": true
    }]
  }'

echo "  ✓ CloudTrail bucket: $TRAIL_BUCKET"

# 3. Create CloudTrail trail
echo ""
echo "Creating CloudTrail trail..."

aws cloudtrail create-trail \
  --name security-trail \
  --s3-bucket-name $TRAIL_BUCKET \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id $DATA_LAKE_KEY

aws cloudtrail start-logging --name security-trail

echo "  ✓ CloudTrail trail: security-trail"

# 4. Enable AWS Config
echo ""
echo "Enabling AWS Config..."

# Create S3 bucket for Config
CONFIG_BUCKET="aws-config-${ACCOUNT_ID}-${REGION}"
aws s3 mb s3://$CONFIG_BUCKET --region $REGION

# Create IAM role for Config
cat > /tmp/config-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "config.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name AWSConfigRole \
  --assume-role-policy-document file:///tmp/config-trust-policy.json || true

aws iam attach-role-policy \
  --role-name AWSConfigRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/ConfigRole

# Create configuration recorder
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::${ACCOUNT_ID}:role/AWSConfigRole \
  --recording-group allSupported=true,includeGlobalResourceTypes=true

# Create delivery channel
aws configservice put-delivery-channel \
  --delivery-channel name=default,s3BucketName=$CONFIG_BUCKET

# Start recorder
aws configservice start-configuration-recorder --configuration-recorder-name default

echo "  ✓ AWS Config enabled"

# 5. Enable GuardDuty
echo ""
echo "Enabling GuardDuty..."

DETECTOR_ID=$(aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES \
  --query 'DetectorId' --output text)

echo "  ✓ GuardDuty detector: $DETECTOR_ID"

# 6. Enable Security Hub
echo ""
echo "Enabling Security Hub..."

aws securityhub enable-security-hub \
  --enable-default-standards || true

echo "  ✓ Security Hub enabled"

# 7. Enable Macie
echo ""
echo "Enabling Amazon Macie..."

aws macie2 enable-macie || true

echo "  ✓ Macie enabled"

# 8. Create Lake Formation data lake
echo ""
echo "Configuring Lake Formation..."

# Register S3 location
DATA_LAKE_BUCKET="data-lake-${ACCOUNT_ID}"
aws s3 mb s3://$DATA_LAKE_BUCKET --region $REGION || true

aws lakeformation register-resource \
  --resource-arn arn:aws:s3:::$DATA_LAKE_BUCKET \
  --use-service-linked-role || true

echo "  ✓ Lake Formation configured"

# 9. Create SNS topic for alerts
echo ""
echo "Creating SNS alert topic..."

TOPIC_ARN=$(aws sns create-topic \
  --name security-alerts \
  --query 'TopicArn' --output text)

echo "  ✓ SNS topic: $TOPIC_ARN"

# Export configuration
echo ""
echo "======================================"
echo "Infrastructure Setup Complete!"
echo "======================================"
echo ""
echo "Configuration:"
echo "  KMS Data Lake Key: $DATA_LAKE_KEY"
echo "  KMS Database Key: $DB_KEY"
echo "  KMS Application Key: $APP_KEY"
echo "  CloudTrail Bucket: $TRAIL_BUCKET"
echo "  Config Bucket: $CONFIG_BUCKET"
echo "  Data Lake Bucket: $DATA_LAKE_BUCKET"
echo "  GuardDuty Detector: $DETECTOR_ID"
echo "  SNS Topic: $TOPIC_ARN"
echo ""

# Save to file
cat > infrastructure-config.json <<EOF
{
  "region": "$REGION",
  "accountId": "$ACCOUNT_ID",
  "kmsKeys": {
    "dataLake": "$DATA_LAKE_KEY",
    "database": "$DB_KEY",
    "application": "$APP_KEY"
  },
  "buckets": {
    "cloudtrail": "$TRAIL_BUCKET",
    "config": "$CONFIG_BUCKET",
    "dataLake": "$DATA_LAKE_BUCKET"
  },
  "security": {
    "guarddutyDetector": "$DETECTOR_ID",
    "snsAlerts": "$TOPIC_ARN"
  }
}
EOF

echo "Configuration saved to: infrastructure-config.json"
echo ""
echo "Next steps:"
echo "  1. Subscribe to SNS topic for alerts"
echo "  2. Review Security Hub findings"
echo "  3. Run exercises in order"
