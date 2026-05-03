#!/bin/bash

###############################################################################
# Module 17: Cost Optimization - Validation Script
#
# Validates that the cost optimization environment is correctly set up
# and all AWS services are accessible.
#
# Checks:
# - AWS credentials and permissions
# - Cost Explorer access
# - CUR bucket and data
# - Cost allocation tags
# - AWS Budgets
# - Compute Optimizer
# - Docker containers
# - Python environment
# - Sample data
#
# Usage: ./scripts/validate.sh
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

PASSED=0
FAILED=0
WARNINGS=0

log_test() { echo -e "${BLUE}[TEST]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASSED=$((PASSED + 1)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILED=$((FAILED + 1)); }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARNINGS=$((WARNINGS + 1)); }

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Module 17: Cost Optimization - Validation           ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Test 1: AWS Credentials
log_test "AWS credentials configured"
if ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null); then
    log_pass "AWS Account: $ACCOUNT_ID"
else
    log_fail "AWS credentials not configured"
fi

# Test 2: Cost Explorer access
log_test "Cost Explorer API access"
if aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-02 \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --region us-east-1 &>/dev/null; then
    log_pass "Cost Explorer accessible"
else
    log_fail "Cost Explorer not accessible (enable or wait 24 hours)"
fi

# Test 3: CUR bucket exists
log_test "Cost and Usage Report bucket"
CUR_BUCKET="cost-usage-report-${ACCOUNT_ID}"
if aws s3api head-bucket --bucket "$CUR_BUCKET" 2>/dev/null; then
    log_pass "CUR bucket exists: s3://$CUR_BUCKET"

    # Check if CUR data exists
    OBJECT_COUNT=$(aws s3 ls "s3://${CUR_BUCKET}/reports/" --recursive 2>/dev/null | wc -l)
    if [ "$OBJECT_COUNT" -gt 0 ]; then
        log_pass "CUR data available ($OBJECT_COUNT files)"
    else
        log_warn "CUR bucket empty (first report available in 24 hours)"
    fi
else
    log_warn "CUR bucket not found (run infrastructure/init-aws.sh)"
fi

# Test 4: Cost allocation tags
log_test "Cost allocation tags"
TAG_STATUS=$(aws ce list-cost-allocation-tags \
    --region us-east-1 \
    --status Active \
    --query 'length(CostAllocationTags)' \
    --output text 2>/dev/null)

if [ -n "$TAG_STATUS" ] && [ "$TAG_STATUS" -gt 0 ]; then
    log_pass "Cost allocation tags active: $TAG_STATUS tags"
else
    log_warn "No active cost allocation tags (activate with init-aws.sh)"
fi

# Test 5: AWS Budgets
log_test "AWS Budgets configured"
BUDGET_COUNT=$(aws budgets describe-budgets \
    --account-id "$ACCOUNT_ID" \
    --region us-east-1 \
    --query 'length(Budgets)' \
    --output text 2>/dev/null)

if [ -n "$BUDGET_COUNT" ] && [ "$BUDGET_COUNT" -gt 0 ]; then
    log_pass "Budgets configured: $BUDGET_COUNT budgets"
else
    log_warn "No budgets configured (create with init-aws.sh)"
fi

# Test 6: Compute Optimizer
log_test "AWS Compute Optimizer"
if aws compute-optimizer get-enrollment-status \
    --region us-east-1 \
    --query 'status' \
    --output text 2>/dev/null | grep -q "Active"; then
    log_pass "Compute Optimizer enrolled"
else
    log_warn "Compute Optimizer not enrolled (may need 30 hours of usage)"
fi

# Test 7: Docker containers
log_test "Docker containers running"

if docker ps | grep -q cost-optimization-localstack; then
    log_pass "LocalStack container running"
else
    log_fail "LocalStack not running (run: docker-compose up -d)"
fi

if docker ps | grep -q cost-optimization-postgres; then
    log_pass "PostgreSQL container running"
else
    log_fail "PostgreSQL not running"
fi

if docker ps | grep -q cost-optimization-jupyter; then
    log_pass "Jupyter container running"
else
    log_fail "Jupyter not running"
fi

# Test 8: LocalStack health
log_test "LocalStack services"
if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then
    log_pass "LocalStack services healthy"
else
    log_warn "LocalStack may not be fully ready"
fi

# Test 9: PostgreSQL connection
log_test "PostgreSQL database"
if docker exec cost-optimization-postgres pg_isready -U cost_optimizer &>/dev/null; then
    log_pass "PostgreSQL ready"
else
    log_fail "PostgreSQL not accessible"
fi

# Test 10: Python environment
log_test "Python virtual environment"
if [ -d "$MODULE_DIR/venv" ]; then
    log_pass "Virtual environment exists"

    # Check key packages
    if "$MODULE_DIR/venv/bin/python" -c "import boto3, pandas, matplotlib" 2>/dev/null; then
        log_pass "Key Python packages installed"
    else
        log_fail "Python packages missing (run: pip install -r requirements.txt)"
    fi
else
    log_fail "Virtual environment not found (run setup.sh)"
fi

# Test 11: Sample data
log_test "Sample data files"
if [ -f "$MODULE_DIR/data/sample/cost-usage-report.csv" ]; then
    log_pass "Sample CUR data exists"
else
    log_warn "Sample CUR data not found"
fi

if [ -f "$MODULE_DIR/data/sample/cost-allocation-tags.json" ]; then
    log_pass "Sample tag data exists"
else
    log_warn "Sample tag data not found"
fi

# Test 12: Athena setup (if CUR is configured)
log_test "Athena for CUR analysis"
if aws athena list-databases \
    --catalog-name AwsDataCatalog \
    --region "$AWS_REGION" \
    --query 'DatabaseList[?Name==`cur_analysis`]' \
    --output text 2>/dev/null | grep -q "cur_analysis"; then
    log_pass "Athena database configured"
else
    log_warn "Athena database not found (run init-aws.sh)"
fi

# Test 13: Run pytest suite
log_test "Running pytest validation suite"
cd "$MODULE_DIR"

if [ -f "validation/test_cost_optimization.py" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate

        # Run tests
        pytest validation/test_cost_optimization.py -v --tb=short &>/tmp/pytest-output.txt

        if [ $? -eq 0 ]; then
            TEST_COUNT=$(grep -c "PASSED" /tmp/pytest-output.txt || echo "0")
            log_pass "All pytest tests passed ($TEST_COUNT tests)"
        else
            FAILED_COUNT=$(grep -c "FAILED" /tmp/pytest-output.txt || echo "0")
            log_warn "Some pytest tests failed ($FAILED_COUNT failures)"
            log_warn "Run 'pytest validation/test_cost_optimization.py -v' for details"
        fi
    else
        log_warn "Virtual environment not activated"
    fi
else
    log_warn "Test suite not found (not yet created)"
fi

# Summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Validation Summary                                   ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Environment validation successful!${NC}"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Activate Python environment: source venv/bin/activate"
    echo "   2. Start with Exercise 01: cd exercises/01-cost-analysis"
    echo "   3. Generate a cost report: make cost-report"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Validation failed. Please fix the errors above.${NC}"
    echo ""
    echo "🔧 Common Fixes:"
    echo "   • AWS credentials: aws configure"
    echo "   • Cost Explorer: Enable in AWS Console"
    echo "   • Docker: Run 'docker-compose up -d' in infrastructure/"
    echo "   • Python deps: pip install -r requirements.txt"
    echo ""
    exit 1
fi
