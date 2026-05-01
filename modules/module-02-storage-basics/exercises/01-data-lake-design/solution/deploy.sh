#!/bin/bash
# Deploy GlobalMart Data Lake

set -e

STACK_NAME="globalmart-data-lake"
ENVIRONMENT=${1:-dev}

echo "🚀 Deploying GlobalMart Data Lake (${ENVIRONMENT})"

aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file data-lake-stack.yaml \
  --parameter-overrides Environment=$ENVIRONMENT \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=DataLake Owner=DataEngineering

echo "✅ Deployment complete!"
echo ""
echo "Bucket names:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?contains(OutputKey, `Bucket`)].{Key:OutputKey, Value:OutputValue}' \
  --output table
