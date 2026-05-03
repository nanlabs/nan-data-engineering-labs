#!/bin/bash

###############################################################################
# Module 17: Cost Optimization - Cleanup Script
#
# Cleans up all resources created during the cost optimization exercises.
# Use this to avoid unnecessary costs after completing the module.
#
# What it cleans:
# - Test EC2 instances (tagged with training)
# - Test S3 buckets (keeps CUR bucket)
# - Test RDS databases
# - Lambda functions created during exercises
# - AWS Budgets (demo budgets)
# - Docker containers and volumes
# - Local data and reports
#
# Usage: ./scripts/cleanup.sh [--keep-data] [--keep-aws]
#
# Options:
#   --keep-data: Don't delete local data and reports
#   --keep-aws: Don't delete AWS resources (only Docker/local)
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

KEEP_DATA=false
KEEP_AWS=false

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Parse arguments
for arg in "$@"; do
    case $arg in
        --keep-data)
            KEEP_DATA=true
            ;;
        --keep-aws)
            KEEP_AWS=true
            ;;
    esac
done

# Cleanup AWS resources
cleanup_aws() {
    log_info "Cleaning up AWS resources..."

    if [ "$KEEP_AWS" = true ]; then
        log_warning "Skipping AWS cleanup (--keep-aws flag)"
        return
    fi

    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

    if [ -z "$ACCOUNT_ID" ]; then
        log_warning "AWS credentials not configured, skipping AWS cleanup"
        return
    fi

    # Delete test EC2 instances
    log_info "Deleting test EC2 instances..."
    TEST_INSTANCES=$(aws ec2 describe-instances \
        --filters "Name=tag:Project,Values=cost-optimization-training" \
        --query "Reservations[].Instances[?State.Name=='running'].InstanceId" \
        --output text 2>/dev/null)

    if [ -n "$TEST_INSTANCES" ]; then
        aws ec2 terminate-instances --instance-ids $TEST_INSTANCES &>/dev/null
        log_success "Terminated ${#TEST_INSTANCES[@]} test instances"
    else
        log_info "No test EC2 instances found"
    fi

    # Delete test S3 buckets (keep CUR bucket)
    log_info "Deleting test S3 buckets..."
    TEST_BUCKET="cost-optimization-demo-${ACCOUNT_ID}"

    if aws s3api head-bucket --bucket "$TEST_BUCKET" 2>/dev/null; then
        # Empty bucket first
        aws s3 rm "s3://${TEST_BUCKET}" --recursive &>/dev/null
        # Delete bucket
        aws s3api delete-bucket --bucket "$TEST_BUCKET" &>/dev/null
        log_success "Deleted test bucket: $TEST_BUCKET"
    else
        log_info "Test bucket not found"
    fi

    # Delete test RDS instances
    log_info "Deleting test RDS instances..."
    TEST_RDS=$(aws rds describe-db-instances \
        --query "DBInstances[?contains(DBInstanceIdentifier, 'cost-opt-test')].DBInstanceIdentifier" \
        --output text 2>/dev/null)

    if [ -n "$TEST_RDS" ]; then
        for db in $TEST_RDS; do
            aws rds delete-db-instance \
                --db-instance-identifier "$db" \
                --skip-final-snapshot &>/dev/null
        done
        log_success "Deleted test RDS instances"
    else
        log_info "No test RDS instances found"
    fi

    # Delete test Lambda functions
    log_info "Deleting test Lambda functions..."
    TEST_LAMBDAS=$(aws lambda list-functions \
        --query "Functions[?contains(FunctionName, 'cost-optimization-')].FunctionName" \
        --output text 2>/dev/null)

    if [ -n "$TEST_LAMBDAS" ]; then
        for func in $TEST_LAMBDAS; do
            aws lambda delete-function --function-name "$func" &>/dev/null
        done
        log_success "Deleted test Lambda functions"
    else
        log_info "No test Lambda functions found"
    fi

    # Delete demo budgets (keep production budgets)
    log_info "Deleting demo budgets..."
    DEMO_BUDGETS=$(aws budgets describe-budgets \
        --account-id "$ACCOUNT_ID" \
        --region us-east-1 \
        --query "Budgets[?contains(BudgetName, 'demo') || contains(BudgetName, 'test')].BudgetName" \
        --output text 2>/dev/null)

    if [ -n "$DEMO_BUDGETS" ]; then
        for budget in $DEMO_BUDGETS; do
            aws budgets delete-budget \
                --account-id "$ACCOUNT_ID" \
                --budget-name "$budget" \
                --region us-east-1 &>/dev/null
        done
        log_success "Deleted demo budgets"
    else
        log_info "No demo budgets found"
    fi

    # Don't delete CUR or anomaly detection (production-useful)
    log_info "Keeping: CUR, Cost Anomaly Detection, Cost Explorer (production services)"

    echo ""
}

# Stop and remove Docker containers
cleanup_docker() {
    log_info "Stopping Docker containers..."

    cd "$MODULE_DIR/infrastructure"

    if docker-compose ps &>/dev/null; then
        docker-compose down
        log_success "Stopped Docker containers"
    else
        log_info "No Docker containers running"
    fi

    # Remove volumes (optional)
    read -p "Delete Docker volumes (PostgreSQL data)? [y/N]: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        log_success "Removed Docker volumes"
    else
        log_info "Keeping Docker volumes"
    fi

    echo ""
}

# Clean local data
cleanup_local_data() {
    if [ "$KEEP_DATA" = true ]; then
        log_warning "Skipping local data cleanup (--keep-data flag)"
        return
    fi

    log_info "Cleaning local data..."

    cd "$MODULE_DIR"

    # Archive reports before deleting
    if [ -d "data/reports" ] && [ "$(ls -A data/reports)" ]; then
        ARCHIVE_NAME="reports-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "data/archive/$ARCHIVE_NAME" data/reports/ &>/dev/null
        log_success "Archived reports to: data/archive/$ARCHIVE_NAME"

        # Delete reports
        rm -rf data/reports/*
        log_success "Deleted local reports"
    else
        log_info "No reports to clean"
    fi

    # Clean LocalStack data
    if [ -d "data/localstack" ]; then
        rm -rf data/localstack/*
        log_success "Cleaned LocalStack data"
    fi

    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    log_success "Cleaned Python cache"

    echo ""
}

# Remove virtual environment
cleanup_venv() {
    read -p "Delete Python virtual environment? [y/N]: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$MODULE_DIR"
        rm -rf venv
        log_success "Deleted virtual environment"
    else
        log_info "Keeping virtual environment"
    fi

    echo ""
}

# Calculate savings from cleanup
estimate_savings() {
    log_info "Estimating monthly cost savings..."

    # This is a rough estimate based on typical test resources
    ESTIMATED_SAVINGS=0

    # EC2 instances
    if [ -n "$TEST_INSTANCES" ]; then
        EC2_SAVINGS=$(echo "${#TEST_INSTANCES[@]} * 0.096 * 730" | bc)
        ESTIMATED_SAVINGS=$(echo "$ESTIMATED_SAVINGS + $EC2_SAVINGS" | bc)
        echo "   EC2 instances: \$${EC2_SAVINGS}"
    fi

    # S3 storage (assume 10 GB)
    S3_SAVINGS=$(echo "10 * 0.023" | bc)
    ESTIMATED_SAVINGS=$(echo "$ESTIMATED_SAVINGS + $S3_SAVINGS" | bc)
    echo "   S3 storage: \$${S3_SAVINGS}"

    # RDS instances
    if [ -n "$TEST_RDS" ]; then
        RDS_SAVINGS=$(echo "${#TEST_RDS[@]} * 140" | bc)
        ESTIMATED_SAVINGS=$(echo "$ESTIMATED_SAVINGS + $RDS_SAVINGS" | bc)
        echo "   RDS instances: \$${RDS_SAVINGS}"
    fi

    echo ""
    echo "   Estimated monthly savings: \$${ESTIMATED_SAVINGS}"
    echo ""
}

# Print summary
print_summary() {
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Cleanup Complete                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$KEEP_AWS" = false ]; then
        echo "🗑️  AWS Resources Cleaned:"
        echo "   ✓ Test EC2 instances terminated"
        echo "   ✓ Test S3 buckets deleted"
        echo "   ✓ Test RDS instances deleted"
        echo "   ✓ Test Lambda functions deleted"
        echo "   ✓ Demo budgets removed"
        echo ""
        echo "📌 Kept (production-useful):"
        echo "   • Cost and Usage Report (CUR)"
        echo "   • Cost Explorer"
        echo "   • Cost Anomaly Detection"
        echo "   • Production budgets"
        echo ""
    fi

    echo "🐳 Docker:"
    echo "   ✓ Containers stopped"

    if [ "$KEEP_DATA" = false ]; then
        echo ""
        echo "📁 Local Data:"
        echo "   ✓ Reports archived"
        echo "   ✓ Temporary files deleted"
    fi

    echo ""
    echo "⚠️  To completely remove AWS cost services:"
    echo "   • Disable Cost Explorer: AWS Console only"
    echo "   • Delete CUR: aws cur delete-report-definition"
    echo "   • Delete CUR bucket: aws s3 rb s3://cost-usage-report-$ACCOUNT_ID --force"
    echo ""
    echo "📝 To resume exercises:"
    echo "   ./scripts/setup.sh"
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   Module 17: Cost Optimization - Cleanup              ${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""

    echo "This will clean up test resources and containers."
    echo ""
    echo "Options:"
    echo "  --keep-data: Keep local reports and data"
    echo "  --keep-aws: Only clean Docker/local (keep AWS resources)"
    echo ""

    read -p "Continue with cleanup? [y/N]: " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi

    echo ""

    cleanup_aws
    cleanup_docker
    cleanup_local_data
    cleanup_venv
    estimate_savings
    print_summary
}

main "$@"
