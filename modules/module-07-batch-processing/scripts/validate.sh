#!/bin/bash
# Validation script for Module 07: Batch Processing

set -e

echo "=========================================="
echo "Module 07: Batch Processing - Validation"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Check function
check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if eval "$1"; then
        echo -e "${GREEN}✓${NC} $2"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $2"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# 1. Check Python environment
echo "1. Checking Python Environment"
echo "------------------------------"
check "python3 --version | grep -q 'Python 3'" "Python 3.x installed"
check "[ -d venv ] || python3 -c 'import sys; sys.prefix != sys.base_prefix'" "Virtual environment active"
echo ""

# 2. Check dependencies
echo "2. Checking Dependencies"
echo "------------------------"
check "python3 -c 'import pandas'" "pandas installed"
check "python3 -c 'import pyspark'" "pyspark installed"
check "python3 -c 'import pyarrow'" "pyarrow installed"
check "python3 -c 'import pytest'" "pytest installed"
check "python3 -c 'import tqdm'" "tqdm installed"
check "python3 -c 'import pydantic'" "pydantic installed"
echo ""

# 3. Check directory structure
echo "3. Checking Directory Structure"
echo "--------------------------------"
check "[ -d theory ]" "theory/ directory exists"
check "[ -d exercises ]" "exercises/ directory exists"
check "[ -d data ]" "data/ directory exists"
check "[ -d validation ]" "validation/ directory exists"
check "[ -d scripts ]" "scripts/ directory exists"
echo ""

# 4. Check theory files
echo "4. Checking Theory Files"
echo "------------------------"
check "[ -f theory/01-concepts.md ]" "01-concepts.md exists"
check "[ -f theory/02-architecture.md ]" "02-architecture.md exists"
check "[ -f theory/03-resources.md ]" "03-resources.md exists"
echo ""

# 5. Check exercises
echo "5. Checking Exercises"
echo "---------------------"
for i in {01..06}; do
    exercise_dir="exercises/*-*/"
    check "[ -d exercises/*-* ]" "Exercise directories exist"
    break
done
echo ""

# 6. Check data generation scripts
echo "6. Checking Data Scripts"
echo "------------------------"
check "[ -f data/scripts/generate_transactions.py ]" "generate_transactions.py exists"
check "[ -f data/scripts/generate_users.py ]" "generate_users.py exists"
check "[ -f data/scripts/generate_products.py ]" "generate_products.py exists"
check "[ -f data/schemas/transactions.json ]" "transactions schema exists"
check "[ -f data/schemas/users.json ]" "users schema exists"
check "[ -f data/schemas/products.json ]" "products schema exists"
echo ""

# 7. Check data exists (optional)
echo "7. Checking Sample Data (Optional)"
echo "----------------------------------"
if [ -d "data/raw" ]; then
    check "[ -f data/raw/users.parquet ] || [ -d data/raw/transactions ]" "Sample data generated"
else
    echo -e "${YELLOW}⚠${NC} No sample data found (run setup.sh to generate)"
fi
echo ""

# 8. Run unit tests
echo "8. Running Unit Tests"
echo "---------------------"
if check "pytest validation/test_module.py -v --tb=short -x" "All unit tests pass"; then
    echo "  Test results above ↑"
fi
echo ""

# 9. Check PySpark functionality
echo "9. Checking PySpark Functionality"
echo "----------------------------------"
check "python3 -c 'from pyspark.sql import SparkSession; spark = SparkSession.builder.master(\"local[1]\").getOrCreate(); spark.stop()'" "PySpark can create local session"
echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo "Total checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
if [ $FAILED_CHECKS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
fi
echo ""

# Exit code
if [ $FAILED_CHECKS -gt 0 ]; then
    echo -e "${RED}✗ Validation FAILED${NC}"
    echo ""
    echo "Please fix the failed checks and run again."
    exit 1
else
    echo -e "${GREEN}✓ All validations PASSED!${NC}"
    echo ""
    echo "Your module is ready! Start learning:"
    echo "  1. Read theory: theory/01-concepts.md"
    echo "  2. Complete exercises: exercises/01-batch-basics/"
    echo "  3. Run tests: pytest validation/ -v"
    exit 0
fi
