#!/bin/bash

################################################################################
# Test Runner Script for Real-Time Analytics Platform
#
# This script orchestrates the execution of all test suites including:
# - Environment validation
# - Unit tests
# - Integration tests
# - Performance tests
# - Orchestration tests
#
# Usage:
#   ./run_tests.sh [OPTIONS]
#
# Options:
#   --all           Run all test suites (default)
#   --unit          Run only unit tests
#   --integration   Run only integration tests
#   --performance   Run only performance tests
#   --orchestration Run only orchestration tests
#   --coverage      Generate coverage report
#   --html          Generate HTML test report
#   --verbose       Verbose output
#   --help          Show this help message
#
# Environment Variables:
#   AWS_REGION      AWS region (default: us-east-1)
#   PROJECT_NAME    Project name (default: rideshare-analytics)
#   ENVIRONMENT     Environment name (default: dev)
#   SKIP_SETUP      Skip environment checks (default: false)
#
################################################################################

set -e  # Exit on error

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-rideshare-analytics}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
RESOURCE_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

# Test configuration
RUN_ALL=true
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_PERFORMANCE=false
RUN_ORCHESTRATION=false
GENERATE_COVERAGE=false
GENERATE_HTML=false
VERBOSE=false
SKIP_SETUP="${SKIP_SETUP:-false}"

# Output directories
TEST_OUTPUT_DIR="${SCRIPT_DIR}/test-results"
COVERAGE_DIR="${TEST_OUTPUT_DIR}/coverage"
HTML_REPORT_DIR="${TEST_OUTPUT_DIR}/html-report"

# ==============================================================================
# COLOR OUTPUT
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "========================================================================"
    echo "$1"
    echo "========================================================================"
    echo ""
}

show_help() {
    head -n 30 "$0" | grep "^#" | sed 's/^# \?//'
    exit 0
}

# ==============================================================================
# PARSE COMMAND LINE ARGUMENTS
# ==============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                RUN_ALL=true
                shift
                ;;
            --unit)
                RUN_ALL=false
                RUN_UNIT=true
                shift
                ;;
            --integration)
                RUN_ALL=false
                RUN_INTEGRATION=true
                shift
                ;;
            --performance)
                RUN_ALL=false
                RUN_PERFORMANCE=true
                shift
                ;;
            --orchestration)
                RUN_ALL=false
                RUN_ORCHESTRATION=true
                shift
                ;;
            --coverage)
                GENERATE_COVERAGE=true
                shift
                ;;
            --html)
                GENERATE_HTML=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================

check_aws_credentials() {
    print_header "Checking AWS Credentials"

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        return 1
    fi

    log_info "AWS CLI version: $(aws --version)"

    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        log_info "Run: aws configure"
        return 1
    fi

    CALLER_IDENTITY=$(aws sts get-caller-identity)
    ACCOUNT_ID=$(echo "$CALLER_IDENTITY" | grep -oP '"Account":\s*"\K[^"]+')
    USER_ARN=$(echo "$CALLER_IDENTITY" | grep -oP '"Arn":\s*"\K[^"]+')

    log_success "AWS credentials validated"
    log_info "Account ID: $ACCOUNT_ID"
    log_info "User ARN: $USER_ARN"
    log_info "Region: $AWS_REGION"

    return 0
}

check_python_environment() {
    print_header "Checking Python Environment"

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install it first."
        return 1
    fi

    PYTHON_VERSION=$(python3 --version)
    log_info "Python version: $PYTHON_VERSION"

    # Check for pytest
    if ! python3 -m pytest --version &> /dev/null; then
        log_warning "pytest not found. Installing dependencies..."
        pip install -r "${PROJECT_ROOT}/requirements.txt"
    fi

    log_success "Python environment validated"

    return 0
}

check_aws_resources() {
    print_header "Checking AWS Resources"

    # Check Kinesis stream
    log_info "Checking Kinesis stream: ${RESOURCE_PREFIX}-rides-stream"
    if aws kinesis describe-stream \
        --stream-name "${RESOURCE_PREFIX}-rides-stream" \
        --region "$AWS_REGION" &> /dev/null; then
        log_success "Kinesis stream found"
    else
        log_warning "Kinesis stream not found (some tests may be skipped)"
    fi

    # Check DynamoDB table
    log_info "Checking DynamoDB table: ${RESOURCE_PREFIX}-rides"
    if aws dynamodb describe-table \
        --table-name "${RESOURCE_PREFIX}-rides" \
        --region "$AWS_REGION" &> /dev/null; then
        log_success "DynamoDB table found"
    else
        log_warning "DynamoDB table not found (some tests may be skipped)"
    fi

    # Check Step Functions
    log_info "Checking Step Functions state machines"
    STATE_MACHINES=$(aws stepfunctions list-state-machines \
        --region "$AWS_REGION" \
        --query "stateMachines[?contains(name, '${RESOURCE_PREFIX}')].name" \
        --output text)

    if [ -n "$STATE_MACHINES" ]; then
        log_success "Found state machines: $STATE_MACHINES"
    else
        log_warning "No state machines found (orchestration tests may be skipped)"
    fi

    return 0
}

# ==============================================================================
# SETUP
# ==============================================================================

setup_test_environment() {
    print_header "Setting Up Test Environment"

    # Create output directories
    mkdir -p "$TEST_OUTPUT_DIR"
    mkdir -p "$COVERAGE_DIR"
    mkdir -p "$HTML_REPORT_DIR"

    log_success "Test directories created"

    # Export environment variables for tests
    export AWS_REGION="$AWS_REGION"
    export PROJECT_NAME="$PROJECT_NAME"
    export ENVIRONMENT="$ENVIRONMENT"
    export RESOURCE_PREFIX="$RESOURCE_PREFIX"

    log_info "Environment variables exported:"
    log_info "  AWS_REGION=$AWS_REGION"
    log_info "  PROJECT_NAME=$PROJECT_NAME"
    log_info "  ENVIRONMENT=$ENVIRONMENT"
    log_info "  RESOURCE_PREFIX=$RESOURCE_PREFIX"

    return 0
}

# ==============================================================================
# TEST EXECUTION
# ==============================================================================

run_unit_tests() {
    print_header "Running Unit Tests"

    PYTEST_ARGS="-v"
    [ "$VERBOSE" = true ] && PYTEST_ARGS="$PYTEST_ARGS -s"
    [ "$GENERATE_COVERAGE" = true ] && PYTEST_ARGS="$PYTEST_ARGS --cov --cov-report=html:${COVERAGE_DIR}"

    if [ -d "${SCRIPT_DIR}/acceptance-tests" ]; then
        python3 -m pytest "${SCRIPT_DIR}/acceptance-tests" \
            $PYTEST_ARGS \
            --junitxml="${TEST_OUTPUT_DIR}/unit-tests-${TIMESTAMP}.xml" \
            -m "not performance and not integration"

        log_success "Unit tests completed"
        return 0
    else
        log_warning "No unit tests directory found"
        return 0
    fi
}

run_integration_tests() {
    print_header "Running Integration Tests"

    PYTEST_ARGS="-v"
    [ "$VERBOSE" = true ] && PYTEST_ARGS="$PYTEST_ARGS -s"

    if [ -d "${SCRIPT_DIR}/acceptance-tests" ]; then
        python3 -m pytest "${SCRIPT_DIR}/acceptance-tests" \
            $PYTEST_ARGS \
            --junitxml="${TEST_OUTPUT_DIR}/integration-tests-${TIMESTAMP}.xml" \
            -m "integration"

        log_success "Integration tests completed"
        return 0
    fi
}

run_performance_tests() {
    print_header "Running Performance Tests"

    PYTEST_ARGS="-v"
    [ "$VERBOSE" = true ] && PYTEST_ARGS="$PYTEST_ARGS -s"

    if [ -f "${SCRIPT_DIR}/test_performance.py" ]; then
        python3 -m pytest "${SCRIPT_DIR}/test_performance.py" \
            $PYTEST_ARGS \
            --junitxml="${TEST_OUTPUT_DIR}/performance-tests-${TIMESTAMP}.xml"

        log_success "Performance tests completed"
        return 0
    else
        log_warning "Performance test file not found"
        return 0
    fi
}

run_orchestration_tests() {
    print_header "Running Orchestration Tests"

    PYTEST_ARGS="-v"
    [ "$VERBOSE" = true ] && PYTEST_ARGS="$PYTEST_ARGS -s"

    if [ -f "${SCRIPT_DIR}/test_orchestration.py" ]; then
        python3 -m pytest "${SCRIPT_DIR}/test_orchestration.py" \
            $PYTEST_ARGS \
            --junitxml="${TEST_OUTPUT_DIR}/orchestration-tests-${TIMESTAMP}.xml"

        log_success "Orchestration tests completed"
        return 0
    else
        log_warning "Orchestration test file not found"
        return 0
    fi
}

run_all_tests() {
    print_header "Running All Test Suites"

    PYTEST_ARGS="-v"
    [ "$VERBOSE" = true ] && PYTEST_ARGS="$PYTEST_ARGS -s"
    [ "$GENERATE_COVERAGE" = true ] && PYTEST_ARGS="$PYTEST_ARGS --cov --cov-report=html:${COVERAGE_DIR}"

    python3 -m pytest "${SCRIPT_DIR}" \
        $PYTEST_ARGS \
        --junitxml="${TEST_OUTPUT_DIR}/all-tests-${TIMESTAMP}.xml"

    log_success "All tests completed"
    return 0
}

# ==============================================================================
# REPORTING
# ==============================================================================

generate_html_report() {
    print_header "Generating HTML Report"

    if [ "$GENERATE_HTML" = true ]; then
        log_info "HTML report generation requested"

        # Generate pytest-html report if installed
        if python3 -c "import pytest_html" &> /dev/null; then
            log_info "Using pytest-html for report generation"
            # Report will be generated during test execution
        else
            log_warning "pytest-html not installed. Install with: pip install pytest-html"
        fi

        # Copy coverage report if exists
        if [ -d "$COVERAGE_DIR" ]; then
            log_success "Coverage report available at: ${COVERAGE_DIR}/index.html"
        fi
    fi
}

generate_summary() {
    print_header "Test Execution Summary"

    log_info "Test results saved to: $TEST_OUTPUT_DIR"

    # Count test results from XML files
    if command -v xmllint &> /dev/null; then
        for xml_file in "${TEST_OUTPUT_DIR}"/*.xml; do
            if [ -f "$xml_file" ]; then
                TESTS=$(xmllint --xpath "string(//testsuites/@tests)" "$xml_file" 2>/dev/null || echo "N/A")
                FAILURES=$(xmllint --xpath "string(//testsuites/@failures)" "$xml_file" 2>/dev/null || echo "N/A")
                ERRORS=$(xmllint --xpath "string(//testsuites/@errors)" "$xml_file" 2>/dev/null || echo "N/A")

                log_info "$(basename "$xml_file"): Tests=$TESTS, Failures=$FAILURES, Errors=$ERRORS"
            fi
        done
    fi

    if [ "$GENERATE_COVERAGE" = true ] && [ -d "$COVERAGE_DIR" ]; then
        log_success "Coverage report: file://${COVERAGE_DIR}/index.html"
    fi
}

# ==============================================================================
# CLEANUP
# ==============================================================================

cleanup() {
    print_header "Cleanup"

    # Remove temporary files if any
    log_info "Cleaning up temporary files..."

    # Keep test results
    log_success "Test results preserved in: $TEST_OUTPUT_DIR"
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    print_header "Real-Time Analytics Platform - Test Runner"
    log_info "Starting test execution at $(date)"

    # Parse command line arguments
    parse_arguments "$@"

    # Environment validation
    if [ "$SKIP_SETUP" != "true" ]; then
        check_aws_credentials || exit 1
        check_python_environment || exit 1
        check_aws_resources || true  # Don't fail on missing resources
    fi

    # Setup
    setup_test_environment || exit 1

    # Run tests based on flags
    TEST_FAILED=false

    if [ "$RUN_ALL" = true ]; then
        run_all_tests || TEST_FAILED=true
    else
        [ "$RUN_UNIT" = true ] && (run_unit_tests || TEST_FAILED=true)
        [ "$RUN_INTEGRATION" = true ] && (run_integration_tests || TEST_FAILED=true)
        [ "$RUN_PERFORMANCE" = true ] && (run_performance_tests || TEST_FAILED=true)
        [ "$RUN_ORCHESTRATION" = true ] && (run_orchestration_tests || TEST_FAILED=true)
    fi

    # Generate reports
    generate_html_report
    generate_summary

    # Cleanup
    cleanup

    # Exit status
    print_header "Test Execution Complete"
    if [ "$TEST_FAILED" = true ]; then
        log_error "Some tests failed. Check the output above for details."
        exit 1
    else
        log_success "All tests passed!"
        exit 0
    fi
}

# Run main function
main "$@"
