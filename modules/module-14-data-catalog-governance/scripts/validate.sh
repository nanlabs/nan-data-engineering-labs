#!/bin/bash

# Module 14: Data Catalog & Governance - Validation Script
# This script validates that all exercises were completed correctly

set -e

LOCALSTACK_ENDPOINT="http://localhost:4566"
AWS_REGION="us-east-1"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Module 14: Validation Script"
echo "========================================="
echo ""

PASSED=0
FAILED=0

# Test function
test_check() {
    local description=$1
    local command=$2

    echo -n "Testing: $description... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
}

echo "=== Exercise 01: Data Catalog Setup ==="
test_check "Bronze database exists" "awslocal glue get-database --name dev_sales_bronze_db"
test_check "Silver database exists" "awslocal glue get-database --name dev_sales_silver_db"
test_check "Gold database exists" "awslocal glue get-database --name dev_sales_gold_db"
test_check "Bronze table exists" "awslocal glue get-table --database-name dev_sales_bronze_db --name sales_transactions"
echo ""

echo "=== Exercise 02: Crawler Automation ==="
test_check "Bronze crawler exists" "awslocal glue get-crawler --name sales-bronze-crawler"
test_check "Silver crawler exists" "awslocal glue get-crawler --name sales-silver-crawler"
test_check "Crawler IAM role exists" "awslocal iam get-role --role-name AWSGlueServiceRole-DataLake"
echo ""

echo "=== Exercise 03: Lake Formation Permissions ==="
test_check "DataEngineer role exists" "awslocal iam get-role --role-name DataEngineer"
test_check "DataAnalyst role exists" "awslocal iam get-role --role-name DataAnalyst"
test_check "DataScientist role exists" "awslocal iam get-role --role-name DataScientist"
test_check "ExternalPartner role exists" "awslocal iam get-role --role-name ExternalPartner"

# Check Lake Formation permissions (LocalStack may have limited support)
echo "Note: Lake Formation permission checks may be limited in LocalStack"
echo ""

echo "=== Exercise 04: Data Quality ==="
# Quality ruleset checks would go here
# Note: AWS Glue Data Quality may not be fully supported in LocalStack
echo "Note: Data Quality validation may be limited in LocalStack"
echo ""

echo "=== Exercise 05: Cross-Account Sharing ==="
# Resource link checks
echo "Note: Cross-account sharing validation may be limited in LocalStack"
echo ""

echo "=== Exercise 06: Governance Automation ==="
test_check "SNS alert topic exists" "awslocal sns get-topic-attributes --topic-arn arn:aws:sns:us-east-1:000000000000:governance-alerts"
# Step Functions checks would go here
echo ""

echo "=== Summary ==="
echo -e "Tests passed: ${GREEN}${PASSED}${NC}"
echo -e "Tests failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================="
    echo "All validations passed! 🎉"
    echo "=========================================${NC}"
    echo ""
    echo "You have successfully completed Module 14!"
    echo "You are ready to proceed to Module 15: Real-Time Analytics"
    exit 0
else
    echo -e "${RED}========================================="
    echo "Some validations failed"
    echo "=========================================${NC}"
    echo ""
    echo "Please review the failed tests and complete missing exercises."
    echo "Refer to exercise READMEs for detailed instructions."
    exit 1
fi
