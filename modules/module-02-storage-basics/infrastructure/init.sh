#!/bin/bash
# Initialize LocalStack infrastructure for Module 02

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Initializing Module 02 Storage Infrastructure${NC}"

# Check if LocalStack is running
if docker ps | grep -q localstack-module-02; then
    echo -e "${GREEN}✓ LocalStack already running${NC}"
else
    echo -e "${YELLOW}Starting LocalStack...${NC}"
    cd "$(dirname "$0")"
    docker-compose up -d

    echo -e "${YELLOW}Waiting for LocalStack to be ready...${NC}"
    sleep 30

    # Health check
    for i in {1..30}; do
        if curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "running"'; then
            echo -e "${GREEN}✓ LocalStack ready${NC}"
            break
        fi
        sleep 1
    done
fi

# Verify services
echo -e "${BLUE}Verifying services...${NC}"

aws --endpoint-url=http://localhost:4566 s3 ls > /dev/null 2>&1 && \
    echo -e "${GREEN}✓ S3 available${NC}" || \
    echo -e "${RED}✗ S3 not available${NC}"

aws --endpoint-url=http://localhost:4566 glue get-databases > /dev/null 2>&1 && \
    echo -e "${GREEN}✓ Glue available${NC}" || \
    echo -e "${RED}✗ Glue not available${NC}"

# Create sample buckets
echo -e "${BLUE}Creating sample buckets...${NC}"
for bucket in globalmart-bronze-dev globalmart-silver-dev globalmart-gold-dev; do
    aws --endpoint-url=http://localhost:4566 s3 mb s3://$bucket 2>/dev/null && \
        echo -e "${GREEN}✓ Created $bucket${NC}" || \
        echo -e "${YELLOW}  $bucket already exists${NC}"
done

echo -e "${GREEN}✅ Infrastructure ready!${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  docker-compose logs -f       # View logs"
echo "  docker-compose down          # Stop services"
echo "  aws --endpoint-url=http://localhost:4566 s3 ls  # List buckets"
