#!/bin/bash

# Module 14: Data Catalog & Governance - Setup Script
# This script initializes the local environment for learning exercises

set -e

echo "========================================="
echo "Module 14: Data Catalog & Governance"
echo "Setup Script"
echo "========================================="
echo ""

# Configuration
LOCALSTACK_ENDPOINT="http://localhost:4566"
AWS_REGION="us-east-1"
BUCKET_NAME="training-data-lake"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if LocalStack is running
echo -e "${YELLOW}[1/8]${NC} Checking LocalStack..."
if ! curl -s ${LOCALSTACK_ENDPOINT}/_localstack/health > /dev/null; then
    echo -e "${RED}ERROR: LocalStack is not running${NC}"
    echo "Please start LocalStack with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ LocalStack is running${NC}"
echo ""

# Create S3 bucket
echo -e "${YELLOW}[2/8]${NC} Creating S3 bucket..."
awslocal s3 mb s3://${BUCKET_NAME} 2>/dev/null || echo "Bucket already exists"
echo -e "${GREEN}✓ S3 bucket ready: s3://${BUCKET_NAME}${NC}"
echo ""

# Create directory structure in S3
echo -e "${YELLOW}[3/8]${NC} Creating S3 directory structure..."
awslocal s3api put-object --bucket ${BUCKET_NAME} --key bronze/sales/transactions/ --content-length 0
awslocal s3api put-object --bucket ${BUCKET_NAME} --key silver/sales/transactions/ --content-length 0
awslocal s3api put-object --bucket ${BUCKET_NAME} --key gold/sales/daily_summary/ --content-length 0
awslocal s3api put-object --bucket ${BUCKET_NAME} --key quarantine/sales/ --content-length 0
echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# Create IAM roles
echo -e "${YELLOW}[4/8]${NC} Creating IAM roles..."

# Trust policy for Glue service
cat > /tmp/glue-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "glue.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create Glue service role
awslocal iam create-role \
    --role-name AWSGlueServiceRole-DataLake \
    --assume-role-policy-document file:///tmp/glue-trust-policy.json \
    2>/dev/null || echo "Role already exists"

# Attach policies
awslocal iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataLake \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole \
    2>/dev/null || true

awslocal iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataLake \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    2>/dev/null || true

# Create user roles
for role in DataEngineer DataAnalyst DataScientist ExternalPartner; do
    awslocal iam create-role \
        --role-name ${role} \
        --assume-role-policy-document file:///tmp/glue-trust-policy.json \
        2>/dev/null || echo "${role} role already exists"
done

echo -e "${GREEN}✓ IAM roles created${NC}"
echo ""

# Create Glue databases
echo -e "${YELLOW}[5/8]${NC} Creating Glue Data Catalog databases..."

awslocal glue create-database \
    --database-input "{
        \"Name\": \"dev_sales_bronze_db\",
        \"Description\": \"Bronze layer - Raw sales data\",
        \"LocationUri\": \"s3://${BUCKET_NAME}/bronze/sales/\",
        \"Parameters\": {
            \"data_owner\": \"sales_team@company.com\",
            \"environment\": \"development\"
        }
    }" 2>/dev/null || echo "Bronze DB already exists"

awslocal glue create-database \
    --database-input "{
        \"Name\": \"dev_sales_silver_db\",
        \"Description\": \"Silver layer - Cleaned sales data\",
        \"LocationUri\": \"s3://${BUCKET_NAME}/silver/sales/\",
        \"Parameters\": {
            \"data_owner\": \"data_engineering@company.com\",
            \"data_quality_level\": \"95\"
        }
    }" 2>/dev/null || echo "Silver DB already exists"

awslocal glue create-database \
    --database-input "{
        \"Name\": \"dev_sales_gold_db\",
        \"Description\": \"Gold layer - Business-ready analytics\",
        \"LocationUri\": \"s3://${BUCKET_NAME}/gold/sales/\",
        \"Parameters\": {
            \"data_owner\": \"analytics_team@company.com\",
            \"data_quality_level\": \"99\"
        }
    }" 2>/dev/null || echo "Gold DB already exists"

echo -e "${GREEN}✓ Glue databases created${NC}"
echo ""

# Upload sample data
echo -e "${YELLOW}[6/8]${NC} Uploading sample data..."
if [ -f "./data/sample/sales-transactions.csv" ]; then
    awslocal s3 cp ./data/sample/sales-transactions.csv \
        s3://${BUCKET_NAME}/bronze/sales/transactions/year=2024/month=03/day=08/
    echo -e "${GREEN}✓ Sample data uploaded${NC}"
else
    echo -e "${YELLOW}⚠ Sample data file not found, skipping${NC}"
fi
echo ""

# Create SNS topics for notifications
echo -e "${YELLOW}[7/8]${NC} Creating SNS topics for alerts..."
awslocal sns create-topic --name governance-alerts 2>/dev/null || echo "Topic already exists"
awslocal sns create-topic --name data-quality-alerts 2>/dev/null || echo "Topic already exists"
awslocal sns create-topic --name governance-success 2>/dev/null || echo "Topic already exists"
echo -e "${GREEN}✓ SNS topics created${NC}"
echo ""

# Verify setup
echo -e "${YELLOW}[8/8]${NC} Verifying setup..."
echo "S3 Buckets:"
awslocal s3 ls | grep ${BUCKET_NAME}

echo ""
echo "Glue Databases:"
awslocal glue get-databases --query 'DatabaseList[*].Name' --output text

echo ""
echo "IAM Roles:"
awslocal iam list-roles --query 'Roles[?contains(RoleName, `Data`) || contains(RoleName, `Glue`)].RoleName' --output text

echo ""
echo -e "${GREEN}========================================="
echo "Setup Complete!"
echo "=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Review theory documentation: theory/concepts.md"
echo "2. Start with Exercise 01: exercises/01-setup-catalog/"
echo "3. Run validation after completing exercises: bash scripts/validate.sh"
echo ""
echo "Happy learning! 🚀"
