#!/bin/bash

###############################################################################
# Module 18: Advanced Architectures - Validation Script
#
# This script validates the setup and ensures all exercises are working.
#
# What it checks:
# - Docker containers running
# - AWS resources created
# - Python dependencies installed
# - Exercise files present
# - Data can be written/read from each service
#
# Usage: ./scripts/validate.sh [--env localstack|aws]
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
ENVIRONMENT="localstack"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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

# Counters
tests_passed=0
tests_failed=0

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Module 18: Advanced Architectures - Validation             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

###############################################################################
# 1. Docker Containers
###############################################################################

log_info "Checking Docker containers..."

EXPECTED_CONTAINERS=(
    "advanced-architectures-localstack"
    "advanced-architectures-redis"
    "advanced-architectures-postgres"
    "advanced-architectures-jupyter"
    "advanced-architectures-kafka"
)

for container in "${EXPECTED_CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^$container$"; then
        log_success "$container running"
        ((tests_passed++))
    else
        log_error "$container not running"
        ((tests_failed++))
    fi
done

###############################################################################
# 2. AWS Resources (LocalStack)
###############################################################################

if [ "$ENVIRONMENT" = "localstack" ]; then
    log_info "Checking AWS resources..."

    AWS_CMD="aws --endpoint-url=http://localhost:4566 --region=us-east-1"

    # S3 Buckets
    if $AWS_CMD s3 ls | grep -q "advanced-arch-raw"; then
        log_success "S3 buckets exist"
        ((tests_passed++))
    else
        log_error "S3 buckets not found"
        ((tests_failed++))
    fi

    # DynamoDB Tables
    if $AWS_CMD dynamodb list-tables | grep -q "event_store"; then
        log_success "DynamoDB tables exist"
        ((tests_passed++))
    else
        log_error "DynamoDB tables not found"
        ((tests_failed++))
    fi

    # Kinesis Streams
    if $AWS_CMD kinesis list-streams | grep -q "raw-events-stream"; then
        log_success "Kinesis streams exist"
        ((tests_passed++))
    else
        log_error "Kinesis streams not found"
        ((tests_failed++))
    fi

    # Glue Databases
    if $AWS_CMD glue get-databases | grep -q "raw_zone"; then
        log_success "Glue databases exist"
        ((tests_passed++))
    else
        log_error "Glue databases not found"
        ((tests_failed++))
    fi
fi

###############################################################################
# 3. Service Connectivity
###############################################################################

log_info "Testing service connectivity..."

cd "$MODULE_DIR"

# Redis
redis_test=$(python3 << EOF
import redis
try:
    r = redis.Redis(host='localhost', port=6379)
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    r.delete('test_key')
    print("OK" if value == b'test_value' else "FAIL")
except Exception as e:
    print(f"FAIL: {e}")
EOF
)

if [ "$redis_test" = "OK" ]; then
    log_success "Redis read/write"
    ((tests_passed++))
else
    log_error "Redis read/write failed"
    ((tests_failed++))
fi

# PostgreSQL
postgres_test=$(python3 << EOF
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='data_lakehouse',
        user='analytics',
        password='analytics'
    )
    cur = conn.cursor()
    cur.execute('SELECT 1')
    result = cur.fetchone()
    cur.close()
    conn.close()
    print("OK" if result[0] == 1 else "FAIL")
except Exception as e:
    print(f"FAIL: {e}")
EOF
)

if [ "$postgres_test" = "OK" ]; then
    log_success "PostgreSQL query"
    ((tests_passed++))
else
    log_error "PostgreSQL query failed"
    ((tests_failed++))
fi

###############################################################################
# 4. Exercise Files
###############################################################################

log_info "Checking exercise files..."

EXERCISES=(
    "01-lambda-architecture/README.md"
    "01-lambda-architecture/batch_layer.py"
    "01-lambda-architecture/speed_layer.py"
    "01-lambda-architecture/serving_layer.py"
    "02-kappa-architecture/README.md"
    "02-kappa-architecture/stream_processor.py"
    "02-kappa-architecture/materialized_views.py"
    "02-kappa-architecture/replay_handler.py"
    "03-data-mesh/README.md"
    "03-data-mesh/domain_api.py"
    "03-data-mesh/schema_registry.py"
    "03-data-mesh/catalog_federation.py"
    "04-event-driven-cqrs/README.md"
    "04-event-driven-cqrs/event_store.py"
    "04-event-driven-cqrs/command_handler.py"
    "04-event-driven-cqrs/query_projections.py"
)

for exercise in "${EXERCISES[@]}"; do
    if [ -f "$MODULE_DIR/exercises/$exercise" ]; then
        ((tests_passed++))
    else
        log_error "Missing: exercises/$exercise"
        ((tests_failed++))
    fi
done

if [ $tests_failed -eq 0 ]; then
    log_success "All exercise files present (${#EXERCISES[@]} files)"
else
    log_warning "Some exercise files missing"
fi

###############################################################################
# 5. Python Imports
###############################################################################

log_info "Checking Python dependencies..."

python_test=$(python3 << EOF
import sys
missing = []

try:
    import boto3
except ImportError:
    missing.append('boto3')

try:
    import pandas
except ImportError:
    missing.append('pandas')

try:
    import redis
except ImportError:
    missing.append('redis')

try:
    import psycopg2
except ImportError:
    missing.append('psycopg2')

try:
    import fastapi
except ImportError:
    missing.append('fastapi')

try:
    from kafka import KafkaProducer
except ImportError:
    missing.append('kafka-python')

if missing:
    print(f"MISSING: {', '.join(missing)}")
else:
    print("OK")
EOF
)

if [ "$python_test" = "OK" ]; then
    log_success "Python dependencies installed"
    ((tests_passed++))
else
    log_error "Python dependencies: $python_test"
    ((tests_failed++))
fi

###############################################################################
# 6. Quick Exercise Tests
###############################################################################

log_info "Running quick exercise tests..."

# Test Lambda Architecture - Batch Layer
if python3 "$MODULE_DIR/exercises/01-lambda-architecture/batch_layer.py" --mode setup --env localstack > /dev/null 2>&1; then
    log_success "Lambda Architecture - Batch Layer"
    ((tests_passed++))
else
    log_warning "Lambda Architecture - Batch Layer setup failed"
    ((tests_failed++))
fi

# Test CQRS - Event Store
if python3 "$MODULE_DIR/exercises/04-event-driven-cqrs/event_store.py" --mode setup --env localstack > /dev/null 2>&1; then
    log_success "Event-Driven CQRS - Event Store"
    ((tests_passed++))
else
    log_warning "CQRS - Event Store setup failed"
    ((tests_failed++))
fi

###############################################################################
# Summary
###############################################################################

echo ""
log_info "Validation Summary:"
echo "  Tests Passed: $tests_passed"
echo "  Tests Failed: $tests_failed"
echo ""

if [ $tests_failed -eq 0 ]; then
    log_success "All validation tests passed! ✨"
    echo ""
    log_info "Ready to start exercises:"
    echo "  1. Exercise 01: cd exercises/01-lambda-architecture && python batch_layer.py"
    echo "  2. Exercise 02: cd exercises/02-kappa-architecture && python stream_processor.py"
    echo "  3. Exercise 03: cd exercises/03-data-mesh && python domain_api.py"
    echo "  4. Exercise 04: cd exercises/04-event-driven-cqrs && python event_store.py"
    echo ""
    exit 0
else
    log_warning "Some tests failed. Review errors above."
    echo ""
    log_info "Troubleshooting:"
    echo "  1. Check containers: docker ps"
    echo "  2. View logs: docker-compose -f infrastructure/docker-compose.yml logs [service]"
    echo "  3. Restart services: ./scripts/cleanup.sh && ./scripts/setup.sh"
    echo ""
    exit 1
fi
