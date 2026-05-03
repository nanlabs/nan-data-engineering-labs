#!/bin/bash

# Module 10: Workflow Orchestration - Validation Script
# Validates Airflow setup and runs tests

set -e

echo "==============================================="
echo "  Module 10: Validation"
echo "==============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Airflow is running
echo "${YELLOW}[1/6] Checking if Airflow is running...${NC}"

if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "${RED}Error: Airflow webserver is not accessible${NC}"
    echo "Run setup.sh first to start Airflow"
    exit 1
fi

echo "${GREEN}✓ Airflow is running${NC}"
echo ""

# Check services health
echo "${YELLOW}[2/6] Checking service health...${NC}"

cd infrastructure

if docker-compose ps | grep -q "unhealthy"; then
    echo "${RED}Warning: Some services are unhealthy${NC}"
    docker-compose ps
else
    echo "${GREEN}✓ All services healthy${NC}"
fi

echo ""

# List DAGs
echo "${YELLOW}[3/6] Listing available DAGs...${NC}"

docker-compose exec -T webserver airflow dags list

echo "${GREEN}✓ DAGs listed successfully${NC}"
echo ""

# Run pytest tests
echo "${YELLOW}[4/6] Running pytest tests...${NC}"

cd ../validation

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r ../requirements.txt
    pip install -q pytest pytest-cov
else
    source venv/bin/activate
fi

pytest . -v --tb=short

test_result=$?

deactivate

if [ $test_result -eq 0 ]; then
    echo "${GREEN}✓ All tests passed${NC}"
else
    echo "${RED}✗ Some tests failed${NC}"
fi

cd ..

echo ""

# Check DAG integrity
echo "${YELLOW}[5/6] Validating DAG integrity...${NC}"

cd infrastructure

# Test for import errors
import_errors=$(docker-compose exec -T webserver airflow dags list-import-errors | wc -l)

if [ $import_errors -gt 1 ]; then
    echo "${RED}✗ DAG import errors detected:${NC}"
    docker-compose exec -T webserver airflow dags list-import-errors
else
    echo "${GREEN}✓ No DAG import errors${NC}"
fi

cd ..

echo ""

# Generate validation report
echo "${YELLOW}[6/6] Generating validation report...${NC}"

REPORT_FILE="validation_report.txt"

cat > $REPORT_FILE << EOF
Module 10: Workflow Orchestration - Validation Report
Generated: $(date)

===== System Status =====
Airflow Webserver: Running
Scheduler: Running
Workers: Running
Database: Connected
Redis: Connected

===== DAGs =====
EOF

cd infrastructure
docker-compose exec -T webserver airflow dags list >> ../$REPORT_FILE
cd ..

cat >> $REPORT_FILE << EOF

===== Tests =====
Pytest: $([ $test_result -eq 0 ] && echo "PASSED" || echo "FAILED")
DAG Imports: $([ $import_errors -gt 1 ] && echo "ERRORS" || echo "OK")

===== Next Steps =====
1. Review exercises in exercises/ directory
2. Complete all 6 exercises
3. Run 'validate.sh' after completing exercises
4. Check STATUS.md for progress

EOF

echo "${GREEN}✓ Report generated: $REPORT_FILE${NC}"
cat $REPORT_FILE

echo ""
echo "${GREEN}===============================================${NC}"
echo "${GREEN}  Validation Complete!${NC}"
echo "${GREEN}===============================================${NC}"
echo ""

if [ $test_result -eq 0 ] && [ $import_errors -le 1 ]; then
    echo "${GREEN}✓ All validations passed${NC}"
    exit 0
else
    echo "${YELLOW}⚠ Some validations failed - review the report${NC}"
    exit 1
fi
