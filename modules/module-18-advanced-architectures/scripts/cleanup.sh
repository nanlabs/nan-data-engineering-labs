#!/bin/bash

###############################################################################
# Module 18: Advanced Architectures - Cleanup Script
#
# This script cleans up all resources created during the exercises.
#
# What it does:
# - Stops and removes Docker containers
# - Deletes AWS resources (LocalStack or AWS)
# - Cleans up data directories
# - Removes temporary files
#
# Usage:
#   ./scripts/cleanup.sh [--keep-data] [--env localstack|aws]
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

# Defaults
KEEP_DATA=false
ENVIRONMENT="localstack"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-data)
            KEEP_DATA=true
            shift
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Module 18: Advanced Architectures - Cleanup                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ "$KEEP_DATA" = false ]; then
    log_warning "This will delete ALL data and resources!"
    read -p "Are you sure? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi
fi

###############################################################################
# 1. Stop Docker Containers
###############################################################################

log_info "Stopping Docker containers..."

cd "$MODULE_DIR/infrastructure"

if docker-compose ps | grep -q "Up"; then
    docker-compose down
    log_success "Docker containers stopped"
else
    log_info "No containers running"
fi

# Remove volumes
if [ "$KEEP_DATA" = false ]; then
    docker-compose down -v
    log_success "Docker volumes removed"
fi

###############################################################################
# 2. Clean AWS Resources
###############################################################################

if [ "$ENVIRONMENT" = "localstack" ]; then
    log_info "Cleaning LocalStack resources..."

    AWS_CMD="aws --endpoint-url=http://localhost:4566 --region=us-east-1"

    # Note: When LocalStack container is stopped, resources are automatically cleaned
    log_success "LocalStack resources cleaned (container stopped)"

elif [ "$ENVIRONMENT" = "aws" ]; then
    log_warning "Cleaning AWS resources..."

    read -p "Delete AWS resources? This costs money! (yes/no): " -r
    echo
    if [[ $REPLY =~ ^[Yy]es$ ]]; then

        # Delete S3 buckets
        log_info "Deleting S3 buckets..."
        for bucket in advanced-arch-raw advanced-arch-processed advanced-arch-curated advanced-arch-batch-views advanced-arch-stream-checkpoints; do
            aws s3 rb "s3://$bucket" --force 2>/dev/null && log_success "Deleted bucket: $bucket" || log_info "Bucket not found: $bucket"
        done

        # Delete DynamoDB tables
        log_info "Deleting DynamoDB tables..."
        for table in event_store event_snapshots speed_layer_metrics materialized_views data_product_catalog; do
            aws dynamodb delete-table --table-name "$table" 2>/dev/null && log_success "Deleted table: $table" || log_info "Table not found: $table"
        done

        # Delete Kinesis streams
        log_info "Deleting Kinesis streams..."
        for stream in raw-events-stream processed-events-stream aggregate-metrics-stream; do
            aws kinesis delete-stream --stream-name "$stream" 2>/dev/null && log_success "Deleted stream: $stream" || log_info "Stream not found: $stream"
        done

        # Delete Glue databases
        log_info "Deleting Glue databases..."
        for db in raw_zone processed_zone curated_zone batch_views product_domain sales_domain customer_domain; do
            aws glue delete-database --name "$db" 2>/dev/null && log_success "Deleted database: $db" || log_info "Database not found: $db"
        done

        # Delete EventBridge event bus
        log_info "Deleting EventBridge event bus..."
        aws events delete-event-bus --name data-mesh-events 2>/dev/null && log_success "Deleted event bus" || log_info "Event bus not found"

        log_success "AWS resources cleaned"
    else
        log_info "Skipped AWS cleanup"
    fi
fi

###############################################################################
# 3. Clean Data Directories
###############################################################################

if [ "$KEEP_DATA" = false ]; then
    log_info "Cleaning data directories..."

    cd "$MODULE_DIR"

    rm -rf data/raw/*
    rm -rf data/processed/*
    rm -rf data/curated/*
    rm -rf data/batch-views/*
    rm -rf data/stream-checkpoints/*
    rm -rf data/localstack/*
    rm -rf logs/*

    log_success "Data directories cleaned"
else
    log_info "Keeping data directories (--keep-data flag)"
fi

###############################################################################
# 4. Clean Python Cache
###############################################################################

log_info "Cleaning Python cache..."

cd "$MODULE_DIR"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

log_success "Python cache cleaned"

###############################################################################
# 5. Remove Virtual Environment (Optional)
###############################################################################

if [ -d "$MODULE_DIR/venv" ] && [ "$KEEP_DATA" = false ]; then
    read -p "Remove Python virtual environment? (yes/no): " -r
    echo
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        rm -rf "$MODULE_DIR/venv"
        log_success "Virtual environment removed"
    else
        log_info "Kept virtual environment"
    fi
fi

###############################################################################
# Summary
###############################################################################

echo ""
log_success "Cleanup complete!"
echo ""
log_info "What was cleaned:"
echo "  - Docker containers stopped"
if [ "$KEEP_DATA" = false ]; then
    echo "  - Docker volumes removed"
    echo "  - Data directories cleared"
else
    echo "  - Data directories kept (--keep-data)"
fi
echo "  - Python cache cleaned"
if [ "$ENVIRONMENT" = "aws" ]; then
    echo "  - AWS resources deleted"
fi
echo ""
log_info "To start again:"
echo "  ./scripts/setup.sh"
echo ""
