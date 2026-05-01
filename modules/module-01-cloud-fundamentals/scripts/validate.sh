#!/bin/bash
# Validation script for Module 01: Cloud Fundamentals

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASSED=0
FAILED=0

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Module 01: Cloud Fundamentals - Validation         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

test_exercise() {
    local exercise_name=$1
    local test_command=$2

    echo -e "${BLUE}Testing: ${exercise_name}${NC}"

    if eval "$test_command" &> /dev/null; then
        echo -e "${GREEN}  ✓ Passed${NC}"
        ((PASSED++))
    else
        echo -e "${RED}  ✗ Failed${NC}"
        ((FAILED++))
    fi
}

# Exercise 01: S3 Basics
echo -e "\n${YELLOW}[Exercise 01: S3 Basics]${NC}"
test_exercise "S3 bucket exists" \
    "aws --endpoint-url=http://localhost:4566 s3 ls s3://quickmart-data-lake-raw"
test_exercise "Objects uploaded" \
    "aws --endpoint-url=http://localhost:4566 s3 ls s3://quickmart-data-lake-raw/logs/ | grep -q '.json'"

# Exercise 02: IAM Policies
echo -e "\n${YELLOW}[Exercise 02: IAM Policies]${NC}"
test_exercise "IAM groups created" \
    "aws --endpoint-url=http://localhost:4566 iam list-groups | grep -q 'data-engineers'"
test_exercise "IAM users created" \
    "aws --endpoint-url=http://localhost:4566 iam list-users | grep -q 'alice.engineer'"
test_exercise "Policies attached" \
    "aws --endpoint-url=http://localhost:4566 iam list-attached-group-policies --group-name data-engineers | grep -q 'PolicyArn'"

# Exercise 03: S3 Advanced
echo -e "\n${YELLOW}[Exercise 03: S3 Advanced]${NC}"
test_exercise "Versioning enabled" \
    "aws --endpoint-url=http://localhost:4566 s3api get-bucket-versioning --bucket my-data-lake-raw | grep -q 'Enabled'"
test_exercise "Lifecycle policy exists" \
    "aws --endpoint-url=http://localhost:4566 s3api get-bucket-lifecycle-configuration --bucket my-data-lake-raw"
test_exercise "SQS queue created" \
    "aws --endpoint-url=http://localhost:4566 sqs list-queues | grep -q 's3-events'"

# Exercise 04: Lambda Functions
echo -e "\n${YELLOW}[Exercise 04: Lambda Functions]${NC}"
test_exercise "Lambda function exists" \
    "aws --endpoint-url=http://localhost:4566 lambda list-functions | grep -q 'csv-validator'"
test_exercise "Lambda role exists" \
    "aws --endpoint-url=http://localhost:4566 iam list-roles | grep -q 'lambda-data-processor'"

# Exercise 05: Infrastructure as Code
echo -e "\n${YELLOW}[Exercise 05: Infrastructure as Code]${NC}"
test_exercise "CloudFormation stack exists" \
    "aws --endpoint-url=http://localhost:4566 cloudformation describe-stacks --stack-name quickmart-data-lake"

# Exercise 06: Cost Optimization
echo -e "\n${YELLOW}[Exercise 06: Cost Optimization]${NC}"
test_exercise "CloudWatch metrics published" \
    "aws --endpoint-url=http://localhost:4566 cloudwatch list-metrics --namespace QuickMart/DataLake"

# Summary
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Validation Results                                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

if [ $PERCENTAGE -ge 80 ]; then
    echo -e "${GREEN}✓ Module 01 Completed! (${PERCENTAGE}%)${NC}"
    echo -e "${GREEN}You're ready for Module 02: Storage Basics${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Module 01 Incomplete (${PERCENTAGE}%)${NC}"
    echo -e "${YELLOW}Complete remaining exercises before proceeding.${NC}"
    exit 1
fi
