#!/bin/bash

# Module 10: Workflow Orchestration - Setup Script
# Sets up Apache Airflow environment with Docker Compose

set -e

echo "==============================================="
echo "  Module 10: Workflow Orchestration Setup"
echo "==============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "${YELLOW}[1/7] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo "${GREEN}✓ Prerequisites satisfied${NC}"
echo ""

# Setup directory structure
echo "${YELLOW}[2/7] Setting up directory structure...${NC}"

mkdir -p dags logs plugins config data
mkdir -p infrastructure

echo "${GREEN}✓ Directories created${NC}"
echo ""

# Create environment file
echo "${YELLOW}[3/7] Creating environment file...${NC}"

if [ ! -f infrastructure/.env ]; then
    cp infrastructure/.env.example infrastructure/.env
    echo "${GREEN}✓ Created .env file from template${NC}"
    echo "${YELLOW}⚠ Please edit infrastructure/.env with your configuration${NC}"
else
    echo "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Set Airflow UID
echo "${YELLOW}[4/7] Setting Airflow UID...${NC}"

echo -e "AIRFLOW_UID=$(id -u)" >> infrastructure/.env

echo "${GREEN}✓ Airflow UID set to $(id -u)${NC}"
echo ""

# Initialize Airflow database
echo "${YELLOW}[5/7] Initializing Airflow...${NC}"

cd infrastructure

docker-compose up airflow-init

echo "${GREEN}✓ Airflow initialized${NC}"
echo ""

# Start services
echo "${YELLOW}[6/7] Starting Airflow services...${NC}"

docker-compose up -d

echo "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be healthy
echo "${YELLOW}[7/7] Waiting for services to be healthy...${NC}"

max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "${GREEN}✓ Services are healthy${NC}"
        break
    fi

    echo "Waiting for services... ($((attempt+1))/$max_attempts)"
    sleep 10
    attempt=$((attempt+1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "${YELLOW}⚠ Services may not be fully healthy yet${NC}"
fi

cd ..

echo ""
echo "${GREEN}===============================================${NC}"
echo "${GREEN}  Setup Complete!${NC}"
echo "${GREEN}===============================================${NC}"
echo ""
echo "Airflow UI: http://localhost:8080"
echo "Username: airflow"
echo "Password: airflow"
echo ""
echo "Flower (Celery monitoring): http://localhost:5555"
echo ""
echo "To stop services:"
echo "  cd infrastructure && docker-compose down"
echo ""
echo "To view logs:"
echo "  cd infrastructure && docker-compose logs -f"
echo ""
