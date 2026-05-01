#!/bin/bash
# Initialization script for LocalStack infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LocalStack Infrastructure Setup    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# Check if docker-compose is running
if docker-compose ps | grep -q localstack-module-01; then
    echo -e "${GREEN}✓${NC} LocalStack is already running"
else
    echo -e "${BLUE}[1/4]${NC} Starting LocalStack..."
    docker-compose up -d

    echo -e "${BLUE}[2/4]${NC} Waiting for LocalStack to be ready..."
    sleep 30

    # Wait for health check
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} LocalStack is ready"
            break
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 1
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "\n${RED}✗${NC} LocalStack failed to start"
        exit 1
    fi
fi

echo -e "${BLUE}[3/4]${NC} Verifying services..."

# Check S3
if aws --endpoint-url=http://localhost:4566 s3 ls > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} S3 service is ready"
else
    echo -e "${YELLOW}⚠${NC} S3 service check failed"
fi

# Check IAM
if aws --endpoint-url=http://localhost:4566 iam list-users > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} IAM service is ready"
else
    echo -e "${YELLOW}⚠${NC} IAM service check failed"
fi

# Check Lambda
if aws --endpoint-url=http://localhost:4566 lambda list-functions > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Lambda service is ready"
else
    echo -e "${YELLOW}⚠${NC} Lambda service check failed"
fi

echo -e "${BLUE}[4/4]${NC} Infrastructure initialization complete"
echo ""

echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Infrastructure Ready!            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs:       docker-compose logs -f"
echo "  Stop services:   docker-compose down"
echo "  Restart:         docker-compose restart"
echo "  Health check:    curl http://localhost:4566/_localstack/health | jq"
echo ""
