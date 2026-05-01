#!/bin/bash
# Setup script for Module 01: Cloud Fundamentals

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Module 01: Cloud Fundamentals - Setup Script       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
echo -e "${BLUE}[1/5]${NC} Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
echo -e "${BLUE}[2/5]${NC} Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check AWS CLI
echo -e "${BLUE}[3/5]${NC} Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found. Installing...${NC}"
    pip3 install awscli-local --user
fi
echo -e "${GREEN}✓ AWS CLI installed${NC}"

# Check Python
echo -e "${BLUE}[4/5]${NC} Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found. Please install Python 3.9+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} installed${NC}"

# Start LocalStack
echo -e "${BLUE}[5/5]${NC} Starting LocalStack..."
cd ../../../docker
if docker-compose ps | grep -q localstack; then
    echo -e "${GREEN}✓ LocalStack already running${NC}"
else
    echo "Starting LocalStack container..."
    docker-compose up -d localstack
    echo "Waiting for LocalStack to be ready..."
    sleep 10
    echo -e "${GREEN}✓ LocalStack started${NC}"
fi

# Test LocalStack connection
echo ""
echo -e "${BLUE}Testing LocalStack connection...${NC}"
if aws --endpoint-url=http://localhost:4566 s3 ls &> /dev/null; then
    echo -e "${GREEN}✓ LocalStack is responding${NC}"
else
    echo -e "${RED}✗ LocalStack not responding. Check docker logs.${NC}"
    exit 1
fi

# Install Python dependencies
echo ""
echo -e "${BLUE}Installing Python dependencies...${NC}"
cd ../modules/module-01-cloud-fundamentals
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Setup Complete!                                     ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Read theory: ${BLUE}theory/concepts.md${NC}"
echo "2. Start Exercise 01: ${BLUE}cd exercises/01-s3-basics${NC}"
echo "3. Follow README.md in each exercise"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  aws --endpoint-url=http://localhost:4566 s3 ls"
echo "  aws --endpoint-url=http://localhost:4566 iam list-users"
echo "  docker-compose logs -f localstack"
echo ""
echo -e "${BLUE}Documentation:${NC} ../../../docs/localstack-guide.md"
echo ""
