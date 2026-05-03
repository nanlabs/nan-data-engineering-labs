#!/bin/bash
# Setup script for Module 16: Data Security & Compliance
set -e

echo "=========================================="
echo "Module 16: Data Security & Compliance"
echo "Environment Setup"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}1. Checking prerequisites...${NC}"

# Python 3.11+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "  ${RED}✗${NC} Python 3.11+ required"
    exit 1
fi

# AWS CLI
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version | cut -d' ' -f1 | cut -d'/' -f2)
    echo -e "  ${GREEN}✓${NC} AWS CLI $AWS_VERSION"
else
    echo -e "  ${RED}✗${NC} AWS CLI required"
    exit 1
fi

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "  ${GREEN}✓${NC} Docker $DOCKER_VERSION"
else
    echo -e "  ${RED}✗${NC} Docker required"
    exit 1
fi

# Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
    echo -e "  ${GREEN}✓${NC} Docker Compose $COMPOSE_VERSION"
else
    echo -e "  ${RED}✗${NC} Docker Compose required"
    exit 1
fi

# 2. Create virtual environment
echo -e "\n${YELLOW}2. Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "  ${GREEN}✓${NC} Virtual environment created"
else
    echo -e "  ${GREEN}✓${NC} Virtual environment already exists"
fi

# 3. Activate and install dependencies
echo -e "\n${YELLOW}3. Installing dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "  ${GREEN}✓${NC} Dependencies installed"

# 4. Check AWS credentials
echo -e "\n${YELLOW}4. Checking AWS credentials...${NC}"
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region || echo "us-east-1")
    echo -e "  ${GREEN}✓${NC} AWS Account: $ACCOUNT_ID"
    echo -e "  ${GREEN}✓${NC} AWS Region: $AWS_REGION"
else
    echo -e "  ${YELLOW}⚠${NC}  AWS credentials not configured"
    echo -e "     Run: aws configure"
fi

# 5. Start Docker containers
echo -e "\n${YELLOW}5. Starting Docker containers...${NC}"
cd infrastructure
docker-compose up -d
cd ..

# Wait for services
echo -e "  ${YELLOW}⏳${NC} Waiting for services to start..."
sleep 10

# Check LocalStack
if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then
    echo -e "  ${GREEN}✓${NC} LocalStack running"
else
    echo -e "  ${RED}✗${NC} LocalStack failed to start"
fi

# Check PostgreSQL
if docker exec module16-postgres pg_isready -U admin &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL running"
else
    echo -e "  ${RED}✗${NC} PostgreSQL failed to start"
fi

# Check Elasticsearch
if curl -s http://localhost:9200 | grep -q "elasticsearch"; then
    echo -e "  ${GREEN}✓${NC} Elasticsearch running"
else
    echo -e "  ${RED}✗${NC} Elasticsearch failed to start"
fi

# 6. Configure LocalStack
echo -e "\n${YELLOW}6. Configuring LocalStack...${NC}"

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Create S3 buckets
aws --endpoint-url=http://localhost:4566 s3 mb s3://data-lake-test &> /dev/null
aws --endpoint-url=http://localhost:4566 s3 mb s3://cloudtrail-logs-test &> /dev/null
echo -e "  ${GREEN}✓${NC} S3 buckets created"

# Create KMS key
KMS_KEY=$(aws --endpoint-url=http://localhost:4566 kms create-key \
    --description "Test encryption key" \
    --query 'KeyMetadata.KeyId' --output text)
aws --endpoint-url=http://localhost:4566 kms create-alias \
    --alias-name alias/test-key \
    --target-key-id $KMS_KEY &> /dev/null
echo -e "  ${GREEN}✓${NC} KMS key created"

# Create DynamoDB table for tokenization
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name TokenStore \
    --attribute-definitions AttributeName=token_id,AttributeType=S \
    --key-schema AttributeName=token_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST &> /dev/null
echo -e "  ${GREEN}✓${NC} DynamoDB table created"

# 7. Create directories
echo -e "\n${YELLOW}7. Creating directories...${NC}"
mkdir -p data/sample
mkdir -p data/encrypted
mkdir -p logs
mkdir -p reports
echo -e "  ${GREEN}✓${NC} Directories created"

# 8. Initialize git-secrets (if available)
echo -e "\n${YELLOW}8. Configuring git-secrets...${NC}"
if command -v git-secrets &> /dev/null; then
    git secrets --install --force &> /dev/null || true
    git secrets --register-aws &> /dev/null || true
    echo -e "  ${GREEN}✓${NC} git-secrets configured"
else
    echo -e "  ${YELLOW}⚠${NC}  git-secrets not installed (optional)"
    echo -e "     Install: brew install git-secrets (macOS) or see docs"
fi

# 9. Run validation checks
echo -e "\n${YELLOW}9. Running validation checks...${NC}"
python3 -c "import boto3; print('  ✓ boto3')"
python3 -c "import cryptography; print('  ✓ cryptography')"
python3 -c "from presidio_analyzer import AnalyzerEngine; print('  ✓ presidio')"
python3 -c "import pytest; print('  ✓ pytest')"

# 10. Summary
echo -e "\n${GREEN}=========================================="
echo "Setup Complete!"
echo -e "===========================================${NC}"
echo ""
echo "Environment:"
echo "  - Python virtual environment: venv/"
echo "  - LocalStack: http://localhost:4566"
echo "  - Kibana: http://localhost:5601"
echo "  - Vault: http://localhost:8200 (token: root-token)"
echo ""
echo "Next steps:"
echo "  1. Initialize AWS infrastructure:"
echo "     ./infrastructure/init-aws.sh"
echo ""
echo "  2. Run exercises:"
echo "     make ex01  # IAM & Access Control"
echo "     make ex02  # Data Encryption"
echo "     make ex03  # Data Masking"
echo "     make ex04  # Audit & Compliance"
echo "     make ex05  # Data Governance"
echo "     make ex06  # Security Monitoring"
echo ""
echo "  3. Run tests:"
echo "     make test"
echo ""
echo "  4. View documentation:"
echo "     cat README.md"
echo ""
