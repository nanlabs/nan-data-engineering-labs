#!/bin/bash
# validate-module.sh
# Validate a specific module's exercises and solutions

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if module parameter is provided
if [ -z "$1" ]; then
    echo -e "${RED}✗${NC} Module name required"
    echo "Usage: $0 <module-name>"
    echo "Example: $0 module-01-cloud-fundamentals"
    exit 1
fi

MODULE_NAME=$1
MODULE_PATH="modules/$MODULE_NAME"

# Check if module exists
if [ ! -d "$MODULE_PATH" ]; then
    echo -e "${RED}✗${NC} Module not found: $MODULE_PATH"
    echo "Available modules:"
    ls -1 modules/ | grep "^module-"
    exit 1
fi

echo ""
echo "🔍 Validating Module: $MODULE_NAME"
echo "================================================"
echo ""

# Check if validation directory exists
if [ ! -d "$MODULE_PATH/validation" ]; then
    echo -e "${YELLOW}⚠${NC}  No validation directory found"
    echo "   Module may not have validation tests yet"
    exit 0
fi

cd "$MODULE_PATH"

# Activate virtual environment if it exists
if [ -f "../../venv/bin/activate" ]; then
    source ../../venv/bin/activate
fi

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Run data quality tests
if [ -d "validation/data-quality" ]; then
    echo -e "${BLUE}📊 Running Data Quality Tests...${NC}"
    if find validation/data-quality -name "test_*.py" -o -name "*_test.py" | grep -q .; then
        if pytest validation/data-quality -v --tb=short 2>&1 | tee /tmp/validation_output.txt; then
            TESTS_RUN=$(grep -c "PASSED" /tmp/validation_output.txt || echo 0)
            TOTAL_TESTS=$((TOTAL_TESTS + TESTS_RUN))
            PASSED_TESTS=$((PASSED_TESTS + TESTS_RUN))
            echo -e "${GREEN}✓${NC} Data quality tests passed"
        else
            TESTS_FAILED=$(grep -c "FAILED" /tmp/validation_output.txt || echo 0)
            TOTAL_TESTS=$((TOTAL_TESTS + TESTS_FAILED))
            FAILED_TESTS=$((FAILED_TESTS + TESTS_FAILED))
            echo -e "${RED}✗${NC} Data quality tests failed"
        fi
    else
        echo -e "${YELLOW}ℹ${NC}  No data quality test files found"
    fi
    echo ""
fi

# Run integration tests
if [ -d "validation/integration" ]; then
    echo -e "${BLUE}🔗 Running Integration Tests...${NC}"
    if find validation/integration -name "test_*.py" -o -name "*_test.py" | grep -q .; then
        if pytest validation/integration -v --tb=short 2>&1 | tee /tmp/validation_output.txt; then
            TESTS_RUN=$(grep -c "PASSED" /tmp/validation_output.txt || echo 0)
            TOTAL_TESTS=$((TOTAL_TESTS + TESTS_RUN))
            PASSED_TESTS=$((PASSED_TESTS + TESTS_RUN))
            echo -e "${GREEN}✓${NC} Integration tests passed"
        else
            TESTS_FAILED=$(grep -c "FAILED" /tmp/validation_output.txt || echo 0)
            TOTAL_TESTS=$((TOTAL_TESTS + TESTS_FAILED))
            FAILED_TESTS=$((FAILED_TESTS + TESTS_FAILED))
            echo -e "${RED}✗${NC} Integration tests failed"
        fi
    else
        echo -e "${YELLOW}ℹ${NC}  No integration test files found"
    fi
    echo ""
fi

# Run infrastructure validation
if [ -d "validation/infrastructure" ]; then
    echo -e "${BLUE}🏗️  Running Infrastructure Validation...${NC}"

    # Check for Terraform files
    if find validation/infrastructure -name "*.tf" | grep -q .; then
        echo "   Validating Terraform configurations..."
        if terraform -chdir=validation/infrastructure validate > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Terraform validation passed"
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗${NC} Terraform validation failed"
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi

    # Check for YAML files
    if find validation/infrastructure -name "*.yaml" -o -name "*.yml" | grep -q .; then
        echo "   Validating YAML configurations..."
        YAML_VALID=true
        for yaml_file in validation/infrastructure/*.yaml validation/infrastructure/*.yml 2>/dev/null; do
            if [ -f "$yaml_file" ]; then
                if python -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
                    echo -e "     ${GREEN}✓${NC} $(basename $yaml_file)"
                else
                    echo -e "     ${RED}✗${NC} $(basename $yaml_file)"
                    YAML_VALID=false
                fi
            fi
        done

        if $YAML_VALID; then
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    echo ""
fi

# Run query result validation
if [ -d "validation/query-results" ]; then
    echo -e "${BLUE}📝 Running Query Result Validation...${NC}"
    if find validation/query-results -name "test_*.py" -o -name "*_test.py" | grep -q .; then
        if pytest validation/query-results -v --tb=short 2>&1 | tee /tmp/validation_output.txt; then
            TESTS_RUN=$(grep -c "PASSED" /tmp/validation_output.txt || echo 0)
            TOTAL_TESTS=$((TOTAL_TESTS + TESTS_RUN))
            PASSED_TESTS=$((PASSED_TESTS + TESTS_RUN))
            echo -e "${GREEN}✓${NC} Query result tests passed"
        else
            TESTS_FAILED=$(grep -c "FAILED" /tmp/validation_output.txt || echo 0)
            TOTAL_TESTS=$((TOTAL_TESTS + TESTS_FAILED))
            FAILED_TESTS=$((FAILED_TESTS + TESTS_FAILED))
            echo -e "${RED}✗${NC} Query result tests failed"
        fi
    else
        echo -e "${YELLOW}ℹ${NC}  No query result test files found"
    fi
    echo ""
fi

# Print summary
echo "================================================"
echo "📊 Validation Summary"
echo "================================================"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $TOTAL_TESTS -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC}  No tests found to run"
    echo "   This module may not have validation tests implemented yet"
    exit 0
elif [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All validations passed!${NC}"
    echo ""
    echo "✅ You've successfully completed this module."
    echo "   Check LEARNING-PATH.md for next modules."
    exit 0
else
    echo -e "${RED}❌ Some validations failed${NC}"
    echo ""
    echo "Please review the errors above and:"
    echo "1. Check your solution implementation"
    echo "2. Review the exercise README for requirements"
    echo "3. Compare with hints if stuck"
    echo "4. Run validation again after fixes"
    exit 1
fi
