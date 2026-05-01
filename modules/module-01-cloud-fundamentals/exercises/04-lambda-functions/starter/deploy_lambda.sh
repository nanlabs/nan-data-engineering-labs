#!/bin/bash
# Deploy Lambda functions to LocalStack

set -e

ENDPOINT_URL="http://localhost:4566"
ROLE_ARN="arn:aws:iam::000000000000:role/lambda-execution-role"

echo "╔═══════════════════════════════════════╗"
echo "║  Lambda Functions Deployment Script  ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Create IAM role for Lambda
echo -e "${BLUE}[1/4]${NC} Creating Lambda execution role..."

aws --endpoint-url=$ENDPOINT_URL iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || echo "Role already exists"

aws --endpoint-url=$ENDPOINT_URL iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AWSLambdaExecute 2>/dev/null || true

echo -e "${GREEN}✓${NC} Lambda role ready"

# Step 2: Package Lambda function
echo -e "${BLUE}[2/4]${NC} Packaging Lambda function..."

cd "$(dirname "$0")"

# Create zip with just the Lambda function (no dependencies for now)
zip -q lambda-csv-validator.zip lambda_csv_validator.py

echo -e "${GREEN}✓${NC} Function packaged"

# Step 3: Deploy Lambda function
echo -e "${BLUE}[3/4]${NC} Deploying Lambda function..."

aws --endpoint-url=$ENDPOINT_URL lambda create-function \
  --function-name csv-validator \
  --runtime python3.9 \
  --role $ROLE_ARN \
  --handler lambda_csv_validator.lambda_handler \
  --zip-file fileb://lambda-csv-validator.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{BUCKET_NAME=quickmart-data}" \
  2>/dev/null && echo -e "${GREEN}✓${NC} Function created" || {
    echo "Function exists, updating code..."
    aws --endpoint-url=$ENDPOINT_URL lambda update-function-code \
      --function-name csv-validator \
      --zip-file fileb://lambda-csv-validator.zip > /dev/null
    echo -e "${GREEN}✓${NC} Function updated"
  }

# Step 4: Configure S3 trigger
echo -e "${BLUE}[4/4]${NC} Configuring S3 trigger..."

# Get Lambda ARN
LAMBDA_ARN=$(aws --endpoint-url=$ENDPOINT_URL lambda get-function \
  --function-name csv-validator \
  --query 'Configuration.FunctionArn' \
  --output text)

# Add permission for S3 to invoke Lambda
aws --endpoint-url=$ENDPOINT_URL lambda add-permission \
  --function-name csv-validator \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::quickmart-data 2>/dev/null || true

# Configure bucket notification
aws --endpoint-url=$ENDPOINT_URL s3api put-bucket-notification-configuration \
  --bucket quickmart-data \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "Id": "csv-validator-trigger",
      "LambdaFunctionArn": "'"$LAMBDA_ARN"'",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "uploads/transactions/"},
            {"Name": "suffix", "Value": ".csv"}
          ]
        }
      }
    }]
  }' 2>/dev/null || echo "Notification configuration updated"

echo -e "${GREEN}✓${NC} S3 trigger configured"

# Cleanup
rm -f lambda-csv-validator.zip

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║   ✓ Deployment Complete!             ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "Test with:"
echo "  aws --endpoint-url=$ENDPOINT_URL s3 cp test-transactions.csv s3://quickmart-data/uploads/transactions/"
echo ""
echo "Check logs:"
echo "  aws --endpoint-url=$ENDPOINT_URL logs tail /aws/lambda/csv-validator --follow"
echo ""
