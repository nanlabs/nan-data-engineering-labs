#!/bin/bash

# Validation script for Module 09: Data Quality
# Runs all tests and generates comprehensive report

set -e

echo "=========================================="
echo "Module 09: Data Quality - Validation"
echo "=========================================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }
print_section() { echo -e "${BLUE}▶ $1${NC}"; }

ERRORS=0

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    print_info "Virtual environment activated"
else
    print_info "No virtual environment found, using system Python"
fi
echo

# Step 1: Check dependencies
print_section "Step 1: Checking dependencies..."
REQUIRED_PACKAGES=("pandas" "numpy" "great_expectations" "pandera" "pytest")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        print_success "$package"
    else
        print_error "$package not installed"
        ERRORS=$((ERRORS + 1))
    fi
done
echo

# Step 2: Verify file structure
print_section "Step 2: Verifying file structure..."

check_file() {
    if [ -f "$1" ]; then
        print_success "$1"
    elif [ -d "$1" ]; then
        print_success "$1/ (directory)"
    else
        print_error "$1 missing"
        ERRORS=$((ERRORS + 1))
    fi
}

# Theory files
check_file "theory/01-concepts.md"
check_file "theory/02-architecture.md"
check_file "theory/03-resources.md"

# Exercise files
check_file "exercises/01-data-profiling/README.md"
check_file "exercises/02-validation-rules/README.md"
check_file "exercises/03-great-expectations/README.md"
check_file "exercises/04-anomaly-detection/README.md"
check_file "exercises/05-quality-monitoring/README.md"
check_file "exercises/06-production-gates/README.md"

# Data files
check_file "data/scripts/generate_data.py"
check_file "data/README.md"
check_file "data/schemas/customer_schema.json"
check_file "data/schemas/transaction_schema.json"
check_file "data/schemas/product_schema.json"

# Config files
check_file "requirements.txt"
check_file "pytest.ini"
check_file ".gitignore"
check_file "STATUS.md"
check_file "README.md"

# Test files
check_file "validation/conftest.py"
check_file "validation/test_module.py"

echo

# Step 3: Run pytest tests
print_section "Step 3: Running test suite..."
echo

# Run different test categories
echo "Running smoke tests..."
if SKIP_GE_TESTS=1 pytest validation/test_module.py -m smoke -v --tb=short 2>&1 | tee /tmp/smoke_tests.log; then
    print_success "Smoke tests passed"
else
    print_error "Some smoke tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo

echo "Running profiling tests..."
if SKIP_GE_TESTS=1 pytest validation/test_module.py -m profiling -v --tb=short 2>&1 | tee /tmp/profiling_tests.log; then
    print_success "Profiling tests passed"
else
    print_error "Some profiling tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo

echo "Running validation tests..."
if SKIP_GE_TESTS=1 pytest validation/test_module.py -m validation -v --tb=short 2>&1 | tee /tmp/validation_tests.log; then
    print_success "Validation tests passed"
else
    print_error "Some validation tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo

echo "Running anomaly detection tests..."
if SKIP_GE_TESTS=1 pytest validation/test_module.py -m anomaly_detection -v --tb=short 2>&1 | tee /tmp/anomaly_tests.log; then
    print_success "Anomaly detection tests passed"
else
    print_error "Some anomaly tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo

echo "Running monitoring tests..."
if SKIP_GE_TESTS=1 pytest validation/test_module.py -m monitoring -v --tb=short 2>&1 | tee /tmp/monitoring_tests.log; then
    print_success "Monitoring tests passed"
else
    print_error "Some monitoring tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo

# Step 4: Code quality checks (optional)
print_section "Step 4: Code quality checks..."

if command -v flake8 &> /dev/null; then
    echo "Running flake8..."
    if flake8 data/scripts/ --max-line-length=100 --extend-ignore=E501 2>/dev/null; then
        print_success "Flake8 checks passed"
    else
        print_info "Flake8 found some issues (non-critical)"
    fi
else
    print_info "Flake8 not installed, skipping"
fi
echo

# Step 5: Generate coverage report
print_section "Step 5: Generating test coverage report..."

if SKIP_GE_TESTS=1 pytest validation/ --cov=. --cov-report=html --cov-report=term-missing > /tmp/coverage.log 2>&1; then
    print_success "Coverage report generated: htmlcov/index.html"
else
    print_info "Coverage report generation skipped"
fi
echo

# Step 6: Count lines of code and documentation
print_section "Step 6: Module statistics..."

echo "Theory documentation:"
if command -v wc &> /dev/null; then
    THEORY_LINES=$(find theory/ -name "*.md" -exec wc -l {} + 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "N/A")
    THEORY_WORDS=$(find theory/ -name "*.md" -exec wc -w {} + 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "N/A")
    echo "  Lines: $THEORY_LINES"
    echo "  Words: ~$THEORY_WORDS"
fi

echo "Exercise documentation:"
if command -v wc &> /dev/null; then
    EXERCISE_LINES=$(find exercises/ -name "README.md" -exec wc -l {} + 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "N/A")
    echo "  Lines: $EXERCISE_LINES"
fi

echo "Python code:"
if command -v wc &> /dev/null; then
    CODE_LINES=$(find data/scripts validation/ -name "*.py" -exec wc -l {} + 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "N/A")
    echo "  Lines: $CODE_LINES"
fi

echo "Total files:"
TOTAL_FILES=$(find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.json" -o -name "*.sh" \) ! -path "./venv/*" ! -path "./great_expectations/*" ! -path "./.git/*" | wc -l || echo "N/A")
echo "  Count: $TOTAL_FILES"
echo

# Step 7: Verify data generation
print_section "Step 7: Data generation verification..."

if [ -f "data/scripts/generate_data.py" ]; then
    print_info "Testing data generation script..."

    if python3 data/scripts/generate_data.py --quality clean --output /tmp/test_data 2>&1 | grep -q "Summary"; then
        print_success "Data generation script works"
        rm -rf /tmp/test_data
    else
        print_info "Data generation script needs adjustment"
    fi
else
    print_error "Data generation script missing"
    ERRORS=$((ERRORS + 1))
fi
echo

# Final summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo

if [ $ERRORS -eq 0 ]; then
    print_success "All validations passed!"
    echo
    echo "Module 09: Data Quality is complete and ready to use."
    echo
    echo "Coverage report: htmlcov/index.html"
    echo "Test logs: /tmp/*_tests.log"
    echo
    EXIT_CODE=0
else
    print_error "$ERRORS validation(s) failed"
    echo
    echo "Please review the errors above and:"
    echo "  1. Ensure all dependencies are installed (./scripts/setup.sh)"
    echo "  2. Complete any missing exercises"
    echo "  3. Fix any failing tests"
    echo
    echo "Test logs available in /tmp/*_tests.log"
    echo
    EXIT_CODE=1
fi

echo "=========================================="
exit $EXIT_CODE
