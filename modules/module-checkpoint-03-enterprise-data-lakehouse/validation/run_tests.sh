#!/bin/bash

################################################################################
# Enterprise Data Lakehouse - Test Execution Script
################################################################################
#
# This script sets up the test environment, runs pytest with coverage,
# and generates comprehensive test reports.
#
# Features:
# ---------
# - Environment validation and setup
# - Dependency installation
# - AWS credentials configuration (LocalStack)
# - Parallel test execution
# - Coverage reporting (terminal, HTML, XML)
# - JUnit XML reports for CI/CD
# - Performance metrics
# - Test result summary
#
# Usage:
# ------
#   ./run_tests.sh                    # Run all tests
#   ./run_tests.sh infrastructure     # Run infrastructure tests only
#   ./run_tests.sh data_quality       # Run data quality tests only
#   ./run_tests.sh governance         # Run governance tests only
#   ./run_tests.sh etl_pipeline       # Run ETL pipeline tests only
#   ./run_tests.sh --fast             # Skip slow tests
#   ./run_tests.sh --verbose          # Verbose output
#   ./run_tests.sh --coverage         # Generate coverage report
#   ./run_tests.sh --html             # Generate HTML report
#
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default configuration
PYTHON_VERSION="3.9"
VENV_DIR="${PROJECT_ROOT}/.venv"
TEST_MODULE=""
VERBOSE=false
FAST_MODE=false
GENERATE_COVERAGE=true
GENERATE_HTML=false
PARALLEL_WORKERS=4
LOCALSTACK_ENDPOINT="http://localhost:4566"

################################################################################
# Helper Functions
################################################################################

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

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

################################################################################
# Environment Validation
################################################################################

validate_environment() {
    print_header "Validating Environment"

    log_info "Checking required commands..."
    check_command python3
    check_command pip3

    log_info "Python version: $(python3 --version)"

    # Check if virtual environment exists
    if [ ! -d "${VENV_DIR}" ]; then
        log_warning "Virtual environment not found. Creating one..."
        python3 -m venv "${VENV_DIR}"
    fi

    log_success "Environment validation complete"
}

################################################################################
# Dependency Installation
################################################################################

install_dependencies() {
    print_header "Installing Dependencies"

    log_info "Activating virtual environment..."
    source "${VENV_DIR}/bin/activate"

    log_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null

    log_info "Installing test dependencies..."
    pip install -q pytest>=7.4.0 \
                   pytest-cov>=4.1.0 \
                   pytest-xdist>=3.3.0 \
                   pytest-html>=3.2.0 \
                   pytest-timeout>=2.1.0 \
                   boto3>=1.28.0 \
                   pandas>=2.0.0 \
                   numpy>=1.24.0 \
                   moto>=4.1.0 \
                   coverage>=7.2.0

    log_success "Dependencies installed"
}

################################################################################
# AWS Configuration (LocalStack)
################################################################################

configure_aws() {
    print_header "Configuring AWS (LocalStack)"

    log_info "Setting AWS credentials for LocalStack..."
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-east-1
    export AWS_ENDPOINT_URL=${LOCALSTACK_ENDPOINT}

    log_info "Checking LocalStack availability..."
    if curl -s "${LOCALSTACK_ENDPOINT}/_localstack/health" > /dev/null 2>&1; then
        log_success "LocalStack is running at ${LOCALSTACK_ENDPOINT}"
    else
        log_warning "LocalStack is not running. Some tests may fail."
        log_info "To start LocalStack: docker-compose up -d localstack"
    fi
}

################################################################################
# Test Execution
################################################################################

run_tests() {
    print_header "Running Tests"

    source "${VENV_DIR}/bin/activate"

    # Build pytest command
    PYTEST_CMD="pytest ${SCRIPT_DIR}"

    # Add test module filter if specified
    if [ -n "${TEST_MODULE}" ]; then
        case "${TEST_MODULE}" in
            infrastructure)
                PYTEST_CMD="${PYTEST_CMD}/test_infrastructure.py"
                ;;
            data_quality)
                PYTEST_CMD="${PYTEST_CMD}/test_data_quality.py"
                ;;
            governance)
                PYTEST_CMD="${PYTEST_CMD}/test_governance.py"
                ;;
            etl_pipeline)
                PYTEST_CMD="${PYTEST_CMD}/test_etl_pipeline.py"
                ;;
            *)
                log_error "Unknown test module: ${TEST_MODULE}"
                exit 1
                ;;
        esac
    fi

    # Add options
    if [ "${VERBOSE}" = true ]; then
        PYTEST_CMD="${PYTEST_CMD} -v"
    fi

    if [ "${FAST_MODE}" = true ]; then
        PYTEST_CMD="${PYTEST_CMD} -m 'not slow'"
    fi

    # Coverage options
    if [ "${GENERATE_COVERAGE}" = true ]; then
        PYTEST_CMD="${PYTEST_CMD} --cov=${SCRIPT_DIR}"
        PYTEST_CMD="${PYTEST_CMD} --cov-report=term-missing"
        PYTEST_CMD="${PYTEST_CMD} --cov-report=xml:${PROJECT_ROOT}/coverage.xml"
    fi

    # HTML report
    if [ "${GENERATE_HTML}" = true ]; then
        PYTEST_CMD="${PYTEST_CMD} --html=${PROJECT_ROOT}/test-report.html --self-contained-html"
        PYTEST_CMD="${PYTEST_CMD} --cov-report=html:${PROJECT_ROOT}/htmlcov"
    fi

    # Parallel execution
    PYTEST_CMD="${PYTEST_CMD} -n ${PARALLEL_WORKERS}"

    # JUnit XML for CI/CD
    PYTEST_CMD="${PYTEST_CMD} --junitxml=${PROJECT_ROOT}/junit.xml"

    # Timeout for slow tests
    PYTEST_CMD="${PYTEST_CMD} --timeout=300"

    log_info "Executing: ${PYTEST_CMD}"

    # Run tests
    if eval "${PYTEST_CMD}"; then
        log_success "All tests passed!"
        return 0
    else
        log_error "Some tests failed!"
        return 1
    fi
}

################################################################################
# Coverage Report
################################################################################

generate_coverage_report() {
    if [ "${GENERATE_COVERAGE}" = false ]; then
        return 0
    fi

    print_header "Coverage Report"

    source "${VENV_DIR}/bin/activate"

    log_info "Generating coverage report..."

    # Terminal report
    coverage report

    # HTML report
    if [ "${GENERATE_HTML}" = true ]; then
        log_info "Generating HTML coverage report..."
        coverage html
        log_success "HTML coverage report: ${PROJECT_ROOT}/htmlcov/index.html"
    fi
}

################################################################################
# Test Summary
################################################################################

generate_summary() {
    print_header "Test Summary"

    if [ -f "${PROJECT_ROOT}/junit.xml" ]; then
        log_info "Parsing JUnit XML results..."

        # Extract test statistics (requires xmllint)
        if command -v xmllint &> /dev/null; then
            TOTAL_TESTS=$(xmllint --xpath "string(//testsuite/@tests)" "${PROJECT_ROOT}/junit.xml")
            FAILURES=$(xmllint --xpath "string(//testsuite/@failures)" "${PROJECT_ROOT}/junit.xml")
            ERRORS=$(xmllint --xpath "string(//testsuite/@errors)" "${PROJECT_ROOT}/junit.xml")
            SKIPPED=$(xmllint --xpath "string(//testsuite/@skipped)" "${PROJECT_ROOT}/junit.xml")

            echo "Total Tests:  ${TOTAL_TESTS}"
            echo "Passed:       $((TOTAL_TESTS - FAILURES - ERRORS - SKIPPED))"
            echo "Failed:       ${FAILURES}"
            echo "Errors:       ${ERRORS}"
            echo "Skipped:      ${SKIPPED}"
        fi
    fi

    # Coverage summary
    if [ -f "${PROJECT_ROOT}/coverage.xml" ]; then
        log_info "Coverage summary available in coverage.xml"
    fi

    # Reports
    echo ""
    log_info "Generated Reports:"
    [ -f "${PROJECT_ROOT}/junit.xml" ] && echo "  - JUnit XML:      ${PROJECT_ROOT}/junit.xml"
    [ -f "${PROJECT_ROOT}/coverage.xml" ] && echo "  - Coverage XML:   ${PROJECT_ROOT}/coverage.xml"
    [ -f "${PROJECT_ROOT}/test-report.html" ] && echo "  - HTML Report:    ${PROJECT_ROOT}/test-report.html"
    [ -d "${PROJECT_ROOT}/htmlcov" ] && echo "  - Coverage HTML:  ${PROJECT_ROOT}/htmlcov/index.html"
}

################################################################################
# Cleanup
################################################################################

cleanup() {
    log_info "Cleaning up temporary files..."

    # Remove pytest cache
    find "${SCRIPT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${SCRIPT_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

    # Remove coverage files
    rm -f "${SCRIPT_DIR}/.coverage" 2>/dev/null || true

    log_success "Cleanup complete"
}

################################################################################
# Main Script
################################################################################

main() {
    local start_time=$(date +%s)

    print_header "Enterprise Data Lakehouse - Test Suite"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            infrastructure|data_quality|governance|etl_pipeline)
                TEST_MODULE=$1
                shift
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
                GENERATE_COVERAGE=true
                shift
                ;;
            --html)
                GENERATE_HTML=true
                shift
                ;;
            --no-coverage)
                GENERATE_COVERAGE=false
                shift
                ;;
            --workers)
                PARALLEL_WORKERS=$2
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [TEST_MODULE] [OPTIONS]"
                echo ""
                echo "Test Modules:"
                echo "  infrastructure    Run infrastructure tests"
                echo "  data_quality      Run data quality tests"
                echo "  governance        Run governance tests"
                echo "  etl_pipeline      Run ETL pipeline tests"
                echo ""
                echo "Options:"
                echo "  --fast            Skip slow tests"
                echo "  --verbose, -v     Verbose output"
                echo "  --coverage        Generate coverage report (default)"
                echo "  --no-coverage     Skip coverage report"
                echo "  --html            Generate HTML reports"
                echo "  --workers N       Number of parallel workers (default: 4)"
                echo "  --help, -h        Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown argument: $1"
                exit 1
                ;;
        esac
    done

    # Execute test workflow
    validate_environment
    install_dependencies
    configure_aws

    # Run tests
    if run_tests; then
        TEST_STATUS=0
    else
        TEST_STATUS=1
    fi

    # Generate reports
    generate_coverage_report
    generate_summary

    # Cleanup
    cleanup

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    print_header "Test Execution Complete"
    log_info "Total duration: ${duration} seconds"

    if [ ${TEST_STATUS} -eq 0 ]; then
        log_success "All tests passed! ✓"
        exit 0
    else
        log_error "Some tests failed! ✗"
        exit 1
    fi
}

# Run main function
main "$@"
