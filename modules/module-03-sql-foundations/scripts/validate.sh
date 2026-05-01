#!/bin/bash

################################################################################
# SQL Foundations - Validation Script
################################################################################
# Description: Run all validation checks for the module
# Usage: ./scripts/validate.sh [OPTIONS]
# Options: --exercise N, --fast, --verbose, --coverage
################################################################################

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
VALIDATION_DIR="$MODULE_DIR/validation"

# Default options
EXERCISE=""
FAST_MODE=false
VERBOSE=false
COVERAGE=false
PARALLEL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --exercise)
            EXERCISE="$2"
            shift 2
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --parallel|-n)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --exercise N      Run tests for specific exercise (01-06)"
            echo "  --fast            Skip slow tests"
            echo "  --verbose, -v     Verbose output"
            echo "  --coverage        Generate coverage report"
            echo "  --parallel, -n    Run tests in parallel"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Run all tests"
            echo "  $0 --exercise 01        # Run tests for exercise 01"
            echo "  $0 --fast --parallel    # Quick validation with parallel execution"
            echo "  $0 --coverage           # Run with coverage report"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

################################################################################
# Validation Steps
################################################################################

print_header "SQL Foundations - Validation Suite"

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

# Check if database is running
if ! docker ps | grep -q "sql-foundations-db"; then
    print_error "Database container is not running"
    print_info "Run: ./scripts/setup.sh"
    exit 1
fi

# Check if database is accessible
if ! docker exec sql-foundations-db psql -U postgres -d ecommerce -c "SELECT 1;" &> /dev/null; then
    print_error "Cannot connect to database"
    exit 1
fi

print_success "Prerequisites check passed"

# Step 2: Verify database schema
print_info "Verifying database schema..."

TABLES=(users products orders order_items user_activity)
MISSING_TABLES=()

for table in "${TABLES[@]}"; do
    if ! docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT to_regclass('public.$table');" | grep -q "$table"; then
        MISSING_TABLES+=("$table")
    fi
done

if [ ${#MISSING_TABLES[@]} -ne 0 ]; then
    print_error "Missing tables: ${MISSING_TABLES[*]}"
    print_info "Run: ./scripts/reset_db.sh"
    exit 1
fi

print_success "Database schema verified (${#TABLES[@]} tables)"

# Step 3: Check Python environment
print_info "Checking Python environment..."

if [ ! -d "$MODULE_DIR/venv" ]; then
    print_warning "Virtual environment not found"
    print_info "Run: ./scripts/setup.sh"
else
    source "$MODULE_DIR/venv/bin/activate"
    print_success "Virtual environment activated"
fi

# Check pytest installation
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed"
    print_info "Run: pip install -r requirements.txt"
    exit 1
fi

print_success "Python environment ready"

# Step 4: Run pytest
print_header "Running Tests"

cd "$MODULE_DIR"

# Build pytest command
PYTEST_CMD="pytest $VALIDATION_DIR"

# Add exercise-specific marker
if [ -n "$EXERCISE" ]; then
    PYTEST_CMD="$PYTEST_CMD -m exercise$EXERCISE"
    print_info "Running tests for exercise $EXERCISE..."
fi

# Add fast mode
if [ "$FAST_MODE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
    print_info "Fast mode: skipping slow tests"
fi

# Add verbose mode
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    if pip show pytest-xdist &> /dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
        print_info "Running tests in parallel"
    else
        print_warning "pytest-xdist not installed, running sequentially"
    fi
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    if pip show pytest-cov &> /dev/null; then
        PYTEST_CMD="$PYTEST_CMD --cov=validation --cov-report=html --cov-report=term"
        print_info "Coverage report will be generated"
    else
        print_warning "pytest-cov not installed, skipping coverage"
    fi
fi

# Add default options
PYTEST_CMD="$PYTEST_CMD --tb=short"

# Run tests
echo ""
print_info "Executing: $PYTEST_CMD"
echo ""

if eval "$PYTEST_CMD"; then
    TESTS_PASSED=true
else
    TESTS_PASSED=false
fi

# Step 5: Generate summary
print_header "Validation Summary"

if [ "$TESTS_PASSED" = true ]; then
    print_success "All tests passed!"

    # Show coverage summary if enabled
    if [ "$COVERAGE" = true ] && [ -f "$MODULE_DIR/htmlcov/index.html" ]; then
        print_info "Coverage report generated: htmlcov/index.html"
    fi

    # Show test statistics
    if [ -f "$MODULE_DIR/.pytest_cache/v/cache/lastfailed" ]; then
        FAILED_COUNT=$(jq '. | length' "$MODULE_DIR/.pytest_cache/v/cache/lastfailed" 2>/dev/null || echo "0")
        if [ "$FAILED_COUNT" -gt 0 ]; then
            print_warning "$FAILED_COUNT test(s) failed in previous run"
        fi
    fi

    echo ""
    echo "Validation complete! ✓"
    echo ""
    echo "Next steps:"
    echo "  - Review failed tests (if any)"
    echo "  - Check coverage report: open htmlcov/index.html"
    echo "  - Run specific exercise: ./scripts/validate.sh --exercise 01"
    echo ""

    exit 0
else
    print_error "Some tests failed"

    echo ""
    echo "Troubleshooting:"
    echo "  1. Check test output above for details"
    echo "  2. Verify database has data: docker exec sql-foundations-db psql -U postgres -d ecommerce -c 'SELECT COUNT(*) FROM users;'"
    echo "  3. Reset database: ./scripts/reset_db.sh"
    echo "  4. Run with verbose: ./scripts/validate.sh --verbose"
    echo "  5. See docs/troubleshooting.md for more help"
    echo ""

    exit 1
fi
