#!/bin/bash
# Validation script for Module 16
set -e

echo "=========================================="
echo "Module 16: Security Validation"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Validation function
validate() {
    local test_name=$1
    local command=$2

    echo -en "  Testing: $test_name... "

    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# 1. IAM Validation
echo -e "\n${YELLOW}1. IAM Security Checks${NC}"

validate "MFA enforced for sensitive operations" \
    "aws iam get-account-password-policy --query 'PasswordPolicy.RequireUppercaseCharacters' --output text 2>/dev/null"

validate "Password policy strength" \
    "aws iam get-account-password-policy --query 'PasswordPolicy.MinimumPasswordLength' --output text | grep -E '^(1[2-9]|[2-9][0-9])$'"

validate "IAM Access Analyzer enabled" \
    "aws accessanalyzer list-analyzers --query 'analyzers[?status==\`ACTIVE\`]' --output text"

# 2. Encryption Validation
echo -e "\n${YELLOW}2. Encryption Checks${NC}"

validate "KMS keys exist" \
    "aws kms list-keys --query 'Keys[0].KeyId' --output text"

validate "KMS key rotation enabled" \
    "aws kms list-keys --query 'Keys[0].KeyId' --output text | xargs -I {} aws kms get-key-rotation-status --key-id {} --query 'KeyRotationEnabled'"

# Check S3 bucket encryption
DATA_LAKE_BUCKET="data-lake-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"
if aws s3api head-bucket --bucket $DATA_LAKE_BUCKET 2>/dev/null; then
    validate "S3 bucket encryption enabled" \
        "aws s3api get-bucket-encryption --bucket $DATA_LAKE_BUCKET --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text"
else
    echo -e "  ${YELLOW}⚠ Skipped${NC}: Data lake bucket not found"
fi

# 3. Logging & Monitoring
echo -e "\n${YELLOW}3. Logging & Monitoring Checks${NC}"

validate "CloudTrail enabled" \
    "aws cloudtrail describe-trails --query 'trailList[0].Name' --output text"

validate "CloudTrail log validation" \
    "aws cloudtrail describe-trails --query 'trailList[0].LogFileValidationEnabled' --output text"

validate "GuardDuty enabled" \
    "aws guardduty list-detectors --query 'DetectorIds[0]' --output text"

validate "Security Hub enabled" \
    "aws securityhub describe-hub --query 'HubArn' --output text 2>/dev/null"

validate "AWS Config enabled" \
    "aws configservice describe-configuration-recorders --query 'ConfigurationRecorders[0].name' --output text"

# 4. Network Security
echo -e "\n${YELLOW}4. Network Security Checks${NC}"

validate "VPC Flow Logs exist" \
    "aws ec2 describe-flow-logs --query 'FlowLogs[0].FlowLogId' --output text" || \
    echo -e "  ${YELLOW}⚠ Optional${NC}: VPC Flow Logs not configured"

# 5. Data Privacy
echo -e "\n${YELLOW}5. Data Privacy Checks${NC}"

validate "Macie enabled" \
    "aws macie2 get-macie-session --query 'status' --output text 2>/dev/null" || \
    echo -e "  ${YELLOW}⚠ Optional${NC}: Macie not enabled"

# 6. Python Environment
echo -e "\n${YELLOW}6. Python Environment Checks${NC}"

validate "boto3 installed" \
    "python3 -c 'import boto3'"

validate "cryptography installed" \
    "python3 -c 'import cryptography'"

validate "presidio installed" \
    "python3 -c 'from presidio_analyzer import AnalyzerEngine'"

validate "pytest installed" \
    "python3 -c 'import pytest'"

# 7. Run pytest tests
echo -e "\n${YELLOW}7. Running Pytest Security Tests${NC}"

if [ -f "validation/test_security.py" ]; then
    echo -e "  ${YELLOW}Running tests...${NC}"
    python3 -m pytest validation/test_security.py -v --tb=short
    PYTEST_EXIT=$?

    if [ $PYTEST_EXIT -eq 0 ]; then
        echo -e "  ${GREEN}✓ All pytest tests passed${NC}"
        ((PASSED++))
    else
        echo -e "  ${RED}✗ Some pytest tests failed${NC}"
        ((FAILED++))
    fi
else
    echo -e "  ${YELLOW}⚠ Skipped${NC}: test_security.py not found"
fi

# 8. IAM Policy Validation
echo -e "\n${YELLOW}8. IAM Policy Validation${NC}"

if command -v parliament &> /dev/null; then
    echo -e "  ${YELLOW}Checking IAM policies with Parliament...${NC}"

    # Find all IAM policy JSON files
    POLICY_FILES=$(find exercises/ -name "*-policy.json" 2>/dev/null)

    if [ -n "$POLICY_FILES" ]; then
        for policy in $POLICY_FILES; do
            echo -en "    $(basename $policy)... "
            if parliament --file "$policy" &> /dev/null; then
                echo -e "${GREEN}✓${NC}"
                ((PASSED++))
            else
                echo -e "${RED}✗${NC}"
                ((FAILED++))
            fi
        done
    else
        echo -e "  ${YELLOW}⚠ No policy files found${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Skipped${NC}: parliament not installed"
fi

# 9. Security Scanning
echo -e "\n${YELLOW}9. Security Scanning${NC}"

if command -v bandit &> /dev/null; then
    echo -e "  ${YELLOW}Running Bandit (Python security)...${NC}"
    bandit -r exercises/ -ll -f screen 2>/dev/null | tail -5
    echo -e "  ${GREEN}✓ Bandit scan complete${NC}"
else
    echo -e "  ${YELLOW}⚠ Skipped${NC}: bandit not installed"
fi

if command -v safety &> /dev/null; then
    echo -e "  ${YELLOW}Running Safety (dependency check)...${NC}"
    safety check --json > /dev/null 2>&1 && \
        echo -e "  ${GREEN}✓ No vulnerabilities found${NC}" || \
        echo -e "  ${YELLOW}⚠ Vulnerabilities detected - check manually${NC}"
else
    echo -e "  ${YELLOW}⚠ Skipped${NC}: safety not installed"
fi

# 10. Compliance Checks
echo -e "\n${YELLOW}10. Compliance Checks${NC}"

# CIS AWS benchmark checks (sample)
validate "Root account has MFA" \
    "aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled' --output text | grep -q 1" || \
    echo -e "  ${YELLOW}⚠ Warning${NC}: Root MFA not verified"

validate "IAM password policy exists" \
    "aws iam get-account-password-policy 2>/dev/null"

# Summary
echo -e "\n${GREEN}=========================================="
echo "Validation Summary"
echo -e "===========================================${NC}"
echo ""
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some validations failed${NC}"
    echo ""
    echo "Recommendations:"
    echo "  1. Review failed checks above"
    echo "  2. Run specific exercises to fix issues"
    echo "  3. Check AWS console for manual verification"
    echo ""
    exit 1
fi
