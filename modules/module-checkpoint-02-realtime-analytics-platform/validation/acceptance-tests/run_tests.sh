#!/bin/bash

# ============================================================================
# ACCEPTANCE TESTS RUNNER
# Real-Time Analytics Platform - Checkpoint 02
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default configuration
PROJECT_NAME="${PROJECT_NAME:-rideshare-analytics}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Test markers
TEST_MARKERS="${TEST_MARKERS:-}"

# Report directory
REPORT_DIR="./test-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================

check_dependencies() {
    print_header "Checking Dependencies"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3: $(python3 --version)"

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    print_success "pip3: $(pip3 --version)"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI not found - continuing anyway"
    else
        print_success "AWS CLI: $(aws --version 2>&1)"
    fi

    echo ""
}

# ============================================================================
# INSTALL TEST DEPENDENCIES
# ============================================================================

install_dependencies() {
    print_header "Installing Test Dependencies"

    if [ -f "requirements.txt" ]; then
        print_info "Installing from requirements.txt..."
        pip3 install -q -r requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found - installing minimal dependencies"
        pip3 install -q pytest boto3 faker
        print_success "Minimal dependencies installed"
    fi

    echo ""
}

# ============================================================================
# ENVIRONMENT VALIDATION
# ============================================================================

validate_environment() {
    print_header "Validating Environment"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured properly"
        print_info "Please run: aws configure"
        exit 1
    fi

    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS Account: $ACCOUNT_ID"
    print_success "AWS Region: $AWS_REGION"
    print_success "Project: $PROJECT_NAME"
    print_success "Environment: $ENVIRONMENT"

    # Export for tests
    export PROJECT_NAME
    export ENVIRONMENT
    export AWS_REGION

    echo ""
}

# ============================================================================
# RUN TESTS
# ============================================================================

run_all_tests() {
    print_header "Running All Tests"

    mkdir -p "$REPORT_DIR"

    pytest \
        -v \
        --tb=short \
        --html="$REPORT_DIR/report_${TIMESTAMP}.html" \
        --self-contained-html \
        --junit-xml="$REPORT_DIR/junit_${TIMESTAMP}.xml" \
        --cov=. \
        --cov-report=html:"$REPORT_DIR/coverage_${TIMESTAMP}" \
        --cov-report=term \
        .

    TEST_EXIT_CODE=$?

    echo ""
    return $TEST_EXIT_CODE
}

run_infrastructure_tests() {
    print_header "Running Infrastructure Tests"

    mkdir -p "$REPORT_DIR"

    pytest \
        -v \
        --tb=short \
        -m infrastructure \
        --html="$REPORT_DIR/infrastructure_${TIMESTAMP}.html" \
        --self-contained-html \
        test_infrastructure.py

    TEST_EXIT_CODE=$?

    echo ""
    return $TEST_EXIT_CODE
}

run_streaming_tests() {
    print_header "Running Streaming Pipeline Tests"

    mkdir -p "$REPORT_DIR"

    pytest \
        -v \
        --tb=short \
        --html="$REPORT_DIR/streaming_${TIMESTAMP}.html" \
        --self-contained-html \
        test_streaming_pipeline.py

    TEST_EXIT_CODE=$?

    echo ""
    return $TEST_EXIT_CODE
}

run_quality_tests() {
    print_header "Running Data Quality Tests"

    mkdir -p "$REPORT_DIR"

    pytest \
        -v \
        --tb=short \
        --html="$REPORT_DIR/quality_${TIMESTAMP}.html" \
        --self-contained-html \
        test_data_quality.py

    TEST_EXIT_CODE=$?

    echo ""
    return $TEST_EXIT_CODE
}

run_performance_tests() {
    print_header "Running Performance Tests"

    mkdir -p "$REPORT_DIR"

    pytest \
        -v \
        --tb=short \
        --html="$REPORT_DIR/performance_${TIMESTAMP}.html" \
        --self-contained-html \
        test_performance.py

    TEST_EXIT_CODE=$?

    echo ""
    return $TEST_EXIT_CODE
}

run_orchestration_tests() {
    print_header "Running Orchestration Tests"

    mkdir -p "$REPORT_DIR"

    pytest \
        -v \
        --tb=short \
        --html="$REPORT_DIR/orchestration_${TIMESTAMP}.html" \
        --self-contained-html \
        test_orchestration.py

    TEST_EXIT_CODE=$?

    echo ""
    return $TEST_EXIT_CODE
}

# ============================================================================
# GENERATE SUMMARY
# ============================================================================

generate_summary() {
    print_header "Test Summary"

    if [ -f "$REPORT_DIR/junit_${TIMESTAMP}.xml" ]; then
        python3 << EOF
import xml.etree.ElementTree as ET
import sys

try:
    tree = ET.parse('$REPORT_DIR/junit_${TIMESTAMP}.xml')
    root = tree.getroot()

    tests = int(root.get('tests', 0))
    failures = int(root.get('failures', 0))
    errors = int(root.get('errors', 0))
    skipped = int(root.get('skipped', 0))
    passed = tests - failures - errors - skipped

    print(f"Total Tests:   {tests}")
    print(f"✓ Passed:      {passed}")
    print(f"✗ Failed:      {failures}")
    print(f"✗ Errors:      {errors}")
    print(f"⊘ Skipped:     {skipped}")

    if failures > 0 or errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

except Exception as e:
    print(f"Could not parse results: {e}")
    sys.exit(1)
EOF
        SUMMARY_EXIT=$?
    else
        print_warning "No test results found"
        SUMMARY_EXIT=1
    fi

    echo ""

    print_info "HTML Report: $REPORT_DIR/report_${TIMESTAMP}.html"
    print_info "Coverage Report: $REPORT_DIR/coverage_${TIMESTAMP}/index.html"

    return $SUMMARY_EXIT
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo ""
    print_header "Real-Time Analytics Platform - Acceptance Tests"
    echo ""

    # Check dependencies
    check_dependencies

    # Install dependencies
    install_dependencies

    # Validate environment
    validate_environment

    # Run tests based on argument
    case "${1:-all}" in
        infrastructure)
            run_infrastructure_tests
            TEST_RESULT=$?
            ;;
        streaming)
            run_streaming_tests
            TEST_RESULT=$?
            ;;
        quality)
            run_quality_tests
            TEST_RESULT=$?
            ;;
        performance)
            run_performance_tests
            TEST_RESULT=$?
            ;;
        orchestration)
            run_orchestration_tests
            TEST_RESULT=$?
            ;;
        all)
            run_all_tests
            TEST_RESULT=$?
            ;;
        *)
            print_error "Invalid test suite: $1"
            print_info "Usage: $0 [infrastructure|streaming|quality|performance|orchestration|all]"
            exit 1
            ;;
    esac

    # Generate summary
    generate_summary
    SUMMARY_RESULT=$?

    # Final result
    echo ""
    if [ $TEST_RESULT -eq 0 ] && [ $SUMMARY_RESULT -eq 0 ]; then
        print_success "All tests passed!"
        exit 0
    else
        print_error "Some tests failed. Check the reports for details."
        exit 1
    fi
}

# Run main function
main "$@"
