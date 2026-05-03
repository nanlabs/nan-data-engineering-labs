#!/bin/bash

# Module 15: Real-Time Analytics - Validation Script
# Validates that all exercises are completed correctly

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================="
echo "Module 15: Real-Time Analytics Validation"
echo -e "=========================================${NC}\n"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing: $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo -e "${BLUE}[1/6] Checking Infrastructure${NC}"
echo "======================================"

run_test "LocalStack is running" \
    "docker ps | grep -q module15-localstack"

run_test "Flink Job Manager is running" \
    "docker ps | grep -q module15-flink-jobmanager"

run_test "Flink Task Managers are running" \
    "docker ps | grep -q module15-flink-taskmanager"

run_test "PostgreSQL is running" \
    "docker ps | grep -q module15-postgres"

run_test "Kafka is running" \
    "docker ps | grep -q module15-kafka"

run_test "Grafana is running" \
    "docker ps | grep -q module15-grafana"

echo ""
echo -e "${BLUE}[2/6] Checking AWS Services (LocalStack)${NC}"
echo "======================================"

run_test "Kinesis events-stream exists" \
    "awslocal kinesis describe-stream --stream-name events-stream --region us-east-1"

run_test "Kinesis aggregated-stream exists" \
    "awslocal kinesis describe-stream --stream-name aggregated-stream --region us-east-1"

run_test "DynamoDB realtime-aggregates table exists" \
    "awslocal dynamodb describe-table --table-name realtime-aggregates --region us-east-1"

run_test "DynamoDB user-sessions table exists" \
    "awslocal dynamodb describe-table --table-name user-sessions --region us-east-1"

run_test "S3 analytics-checkpoints bucket exists" \
    "awslocal s3 ls s3://analytics-checkpoints"

run_test "SNS fraud-alerts topic exists" \
    "awslocal sns list-topics --region us-east-1 | grep -q fraud-alerts"

echo ""
echo -e "${BLUE}[3/6] Checking Flink Cluster${NC}"
echo "======================================"

run_test "Flink REST API is accessible" \
    "curl -sf http://localhost:8081/overview"

run_test "Flink has task managers registered" \
    "curl -s http://localhost:8081/taskmanagers | grep -q '\"taskmanagers\"'"

run_test "Flink checkpointing is enabled" \
    "curl -s http://localhost:8081/config | grep -q checkpoint"

echo ""
echo -e "${BLUE}[4/6] Running Python Tests${NC}"
echo "======================================"

cd "$MODULE_DIR"

# Check if pytest is available
if command -v pytest &> /dev/null; then
    # Run validation tests if they exist
    if [ -d "validation" ] && [ "$(find validation -name 'test_*.py' | wc -l)" -gt 0 ]; then
        echo "Running pytest validation tests..."
        if pytest validation/ -v --tb=short 2>&1 | tail -20; then
            echo -e "${GREEN}✓ Python tests passed${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${YELLOW}⚠ Some Python tests failed${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        echo -e "${YELLOW}⚠ No Python test files found, skipping${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pytest not installed, skipping Python tests${NC}"
fi

echo ""
echo -e "${BLUE}[5/6] Checking Data Quality${NC}"
echo "======================================"

# Check if there's data in Kinesis streams
SHARD_COUNT=$(awslocal kinesis describe-stream \
    --stream-name events-stream \
    --region us-east-1 2>/dev/null \
    | grep -c "ShardId" || echo "0")

if [ "$SHARD_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ events-stream has $SHARD_COUNT shards${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Could not verify shard count${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check DynamoDB table item count
ITEM_COUNT=$(awslocal dynamodb scan \
    --table-name realtime-aggregates \
    --select COUNT \
    --region us-east-1 2>/dev/null \
    | grep -oP '"Count":\s*\K\d+' || echo "0")

echo "  - DynamoDB realtime-aggregates has $ITEM_COUNT items"

echo ""
echo -e "${BLUE}[6/6] Checking Exercise Completion${NC}"
echo "======================================"

# Exercise 01: Kinesis Analytics SQL
if [ -f "$MODULE_DIR/exercises/01-kinesis-analytics-sql/solution.sql" ]; then
    echo -e "${GREEN}✓ Exercise 01 solution exists${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Exercise 01 solution not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Exercise 02: Flink Table API
if [ -f "$MODULE_DIR/exercises/02-flink-table-api/flink_app.py" ]; then
    echo -e "${GREEN}✓ Exercise 02 Flink app exists${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Exercise 02 Flink app not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Exercise 03: Real-Time Dashboards
if [ -f "$MODULE_DIR/exercises/03-real-time-dashboards/dashboard-config.json" ]; then
    echo -e "${GREEN}✓ Exercise 03 dashboard config exists${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Exercise 03 dashboard config not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Exercise 04: CEP Fraud Detection
if [ -f "$MODULE_DIR/exercises/04-cep-fraud-detection/cep_patterns.py" ]; then
    echo -e "${GREEN}✓ Exercise 04 CEP patterns exist${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Exercise 04 CEP patterns not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Exercise 05: ML Scoring
if [ -f "$MODULE_DIR/exercises/05-ml-scoring/ml_scorer.py" ]; then
    echo -e "${GREEN}✓ Exercise 05 ML scorer exists${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Exercise 05 ML scorer not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Exercise 06: Production Deployment
if [ -f "$MODULE_DIR/exercises/06-production-deployment/deploy.sh" ]; then
    echo -e "${GREEN}✓ Exercise 06 deployment script exists${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Exercise 06 deployment script not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Summary
echo ""
echo -e "${BLUE}========================================="
echo "Validation Summary"
echo -e "=========================================${NC}"
echo ""
echo -e "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
echo ""

PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
echo -e "Pass Rate:    ${PASS_RATE}%"
echo ""

# Generate validation report
REPORT_FILE="$MODULE_DIR/validation-report.txt"
cat > "$REPORT_FILE" << EOF
Module 15: Real-Time Analytics - Validation Report
Generated: $(date)

Summary:
  Total Tests: $TOTAL_TESTS
  Passed: $PASSED_TESTS
  Failed: $FAILED_TESTS
  Pass Rate: ${PASS_RATE}%

Infrastructure Status:
  - LocalStack: $(docker ps | grep -q module15-localstack && echo "Running" || echo "Stopped")
  - Flink: $(docker ps | grep -q module15-flink-jobmanager && echo "Running" || echo "Stopped")
  - PostgreSQL: $(docker ps | grep -q module15-postgres && echo "Running" || echo "Stopped")
  - Kafka: $(docker ps | grep -q module15-kafka && echo "Running" || echo "Stopped")

AWS Services:
  - Kinesis Streams: $(awslocal kinesis list-streams --region us-east-1 2>/dev/null | grep -c StreamName || echo "0") streams
  - DynamoDB Tables: $(awslocal dynamodb list-tables --region us-east-1 2>/dev/null | grep -c TableName || echo "0") tables
  - S3 Buckets: $(awslocal s3 ls 2>/dev/null | wc -l || echo "0") buckets

Exercise Completion:
  Exercise 01: $([ -f "$MODULE_DIR/exercises/01-kinesis-analytics-sql/solution.sql" ] && echo "Complete" || echo "Incomplete")
  Exercise 02: $([ -f "$MODULE_DIR/exercises/02-flink-table-api/flink_app.py" ] && echo "Complete" || echo "Incomplete")
  Exercise 03: $([ -f "$MODULE_DIR/exercises/03-real-time-dashboards/dashboard-config.json" ] && echo "Complete" || echo "Incomplete")
  Exercise 04: $([ -f "$MODULE_DIR/exercises/04-cep-fraud-detection/cep_patterns.py" ] && echo "Complete" || echo "Incomplete")
  Exercise 05: $([ -f "$MODULE_DIR/exercises/05-ml-scoring/ml_scorer.py" ] && echo "Complete" || echo "Incomplete")
  Exercise 06: $([ -f "$MODULE_DIR/exercises/06-production-deployment/deploy.sh" ] && echo "Complete" || echo "Incomplete")

Recommendations:
EOF

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo "  ✓ All tests passed! Module is complete." >> "$REPORT_FILE"
    echo -e "${GREEN}✓ All tests passed! Ready to move to next module.${NC}"
elif [ "$FAILED_TESTS" -lt 5 ]; then
    echo "  ⚠ Minor issues found. Review failed tests and complete remaining exercises." >> "$REPORT_FILE"
    echo -e "${YELLOW}⚠ Minor issues found. Review failed tests above.${NC}"
else
    echo "  ✗ Multiple failures detected. Review setup and exercise implementations." >> "$REPORT_FILE"
    echo -e "${RED}✗ Multiple failures. Review setup steps.${NC}"
fi

echo ""
echo "Detailed report saved to: $REPORT_FILE"
echo ""

# Exit with appropriate code
if [ "$FAILED_TESTS" -eq 0 ]; then
    exit 0
else
    exit 1
fi
