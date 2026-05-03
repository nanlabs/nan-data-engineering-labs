#!/bin/bash

################################################################################
# Acceptance Tests Runner for Serverless Data Lake Checkpoint
#
# This script runs all acceptance tests with proper configuration,
# generates coverage reports, and provides a summary of results.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Serverless Data Lake - Acceptance Test Suite            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if AWS credentials are configured
check_aws_credentials() {
    echo -e "${YELLOW}→ Checking AWS credentials...${NC}"
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}✗ AWS credentials not configured!${NC}"
        echo "  Please configure AWS credentials using:"
        echo "    aws configure"
        echo "  or set environment variables:"
        echo "    AWS_ACCESS_KEY_ID"
        echo "    AWS_SECRET_ACCESS_KEY"
        echo "    AWS_REGION"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS credentials configured${NC}"
}

# Install dependencies
install_dependencies() {
    echo ""
    echo -e "${YELLOW}→ Installing test dependencies...${NC}"

    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "${RED}✗ requirements.txt not found!${NC}"
        exit 1
    fi
}

# Set test environment variables
set_test_environment() {
    echo ""
    echo -e "${YELLOW}→ Setting test environment variables...${NC}"

    # Use environment variables if set, otherwise use defaults
    export AWS_REGION="${AWS_REGION:-us-east-1}"
    export BUCKET_PREFIX="${BUCKET_PREFIX:-data-lake-checkpoint01}"
    export PROJECT_NAME="${PROJECT_NAME:-serverless-data-lake}"
    export ENVIRONMENT="${ENVIRONMENT:-test}"

    echo "  AWS_REGION: $AWS_REGION"
    echo "  BUCKET_PREFIX: $BUCKET_PREFIX"
    echo "  PROJECT_NAME: $PROJECT_NAME"
    echo "  ENVIRONMENT: $ENVIRONMENT"
    echo -e "${GREEN}✓ Environment configured${NC}"
}

# Run tests
run_tests() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Running Tests                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Parse command line arguments
    TEST_MARKERS=""
    VERBOSE=""
    PARALLEL=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                TEST_MARKERS="-m 'not slow and not expensive'"
                echo -e "${YELLOW}Running quick tests only (excluding slow and expensive)${NC}"
                shift
                ;;
            --integration)
                TEST_MARKERS="-m integration"
                echo -e "${YELLOW}Running integration tests only${NC}"
                shift
                ;;
            --verbose)
                VERBOSE="-v"
                echo -e "${YELLOW}Verbose output enabled${NC}"
                shift
                ;;
            --parallel)
                PARALLEL="-n auto"
                echo -e "${YELLOW}Parallel execution enabled${NC}"
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                exit 1
                ;;
        esac
    done

    # Create reports directory
    mkdir -p reports

    # Run pytest with coverage
    pytest $TEST_MARKERS $VERBOSE $PARALLEL \
        --cov=. \
        --cov-report=html:reports/coverage \
        --cov-report=term-missing \
        --html=reports/test-report.html \
        --self-contained-html \
        --tb=short \
        -ra \
        || TEST_EXIT_CODE=$?

    return ${TEST_EXIT_CODE:-0}
}

# Generate summary report
generate_summary() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Test Summary                                             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ -f "reports/test-report.html" ]; then
        echo -e "${GREEN}✓ Test report generated: reports/test-report.html${NC}"
    fi

    if [ -d "reports/coverage" ]; then
        echo -e "${GREEN}✓ Coverage report generated: reports/coverage/index.html${NC}"
    fi

    echo ""
    echo "To view reports:"
    echo "  Test Report:     open reports/test-report.html"
    echo "  Coverage Report: open reports/coverage/index.html"
}

# Main execution
main() {
    # Check prerequisites
    check_aws_credentials

    # Install dependencies
    install_dependencies

    # Set environment
    set_test_environment

    # Run tests
    run_tests
    TEST_RESULT=$?

    # Generate summary
    generate_summary

    echo ""
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✓ ALL TESTS PASSED                                       ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ✗ SOME TESTS FAILED                                      ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Check the test report for details: reports/test-report.html"
        exit 1
    fi
}

# Show usage if --help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick       Run only quick tests (exclude slow and expensive)"
    echo "  --integration Run only integration tests"
    echo "  --verbose     Enable verbose output"
    echo "  --parallel    Run tests in parallel"
    echo "  --help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  AWS_REGION      AWS region (default: us-east-1)"
    echo "  BUCKET_PREFIX   S3 bucket prefix (default: data-lake-checkpoint01)"
    echo "  PROJECT_NAME    Project name (default: serverless-data-lake)"
    echo "  ENVIRONMENT     Environment (default: test)"
    echo ""
    exit 0
fi

# Run main function
main "$@"
