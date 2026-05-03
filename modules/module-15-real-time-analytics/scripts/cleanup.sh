#!/bin/bash

# Module 15: Real-Time Analytics - Cleanup Script
# Stops all services and removes data

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}======================================"
echo "Module 15: Real-Time Analytics Cleanup"
echo -e "======================================${NC}\n"

echo -e "${YELLOW}This will:"
echo "  - Stop all Docker containers"
echo "  - Remove all volumes and data"
echo "  - Clean up temporary files"
echo -e "${NC}"

read -p "Are you sure you want to cleanup? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo -e "${BLUE}[1/5] Stopping Flink jobs...${NC}"
# Try to cancel any running Flink jobs
FLINK_JOBS=$(curl -s http://localhost:8081/jobs 2>/dev/null | grep -oP '"id":"\K[^"]+' || echo "")
if [ -n "$FLINK_JOBS" ]; then
    for job_id in $FLINK_JOBS; do
        echo "  Cancelling job: $job_id"
        curl -X PATCH "http://localhost:8081/jobs/$job_id?mode=cancel" 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Flink jobs stopped${NC}"
else
    echo -e "${YELLOW}⚠ No running Flink jobs found${NC}"
fi

echo ""
echo -e "${BLUE}[2/5] Stopping Docker containers...${NC}"
cd "$MODULE_DIR/infrastructure"

# Stop containers
docker-compose down -v

echo -e "${GREEN}✓ Docker containers stopped${NC}"

echo ""
echo -e "${BLUE}[3/5] Removing Docker volumes...${NC}"

# Remove named volumes
docker volume rm module15_flink-checkpoints 2>/dev/null || true
docker volume rm module15_flink-savepoints 2>/dev/null || true
docker volume rm module15_postgres-data 2>/dev/null || true
docker volume rm module15_grafana-data 2>/dev/null || true

# Alternative format (if using project name)
docker volume rm infrastructure_flink-checkpoints 2>/dev/null || true
docker volume rm infrastructure_flink-savepoints 2>/dev/null || true
docker volume rm infrastructure_postgres-data 2>/dev/null || true
docker volume rm infrastructure_grafana-data 2>/dev/null || true

echo -e "${GREEN}✓ Docker volumes removed${NC}"

echo ""
echo -e "${BLUE}[4/5] Cleaning up temporary files...${NC}"

# Remove LocalStack data
if [ -d "$MODULE_DIR/infrastructure/localstack-data" ]; then
    rm -rf "$MODULE_DIR/infrastructure/localstack-data"
    echo "  - Removed LocalStack data"
fi

# Remove output files
if [ -d "$MODULE_DIR/data/output" ]; then
    rm -rf "$MODULE_DIR/data/output"/*
    echo "  - Removed output files"
fi

# Remove log files
if [ -d "$MODULE_DIR/logs" ]; then
    rm -rf "$MODULE_DIR/logs"/*
    echo "  - Removed log files"
fi

# Remove validation report
if [ -f "$MODULE_DIR/validation-report.txt" ]; then
    rm "$MODULE_DIR/validation-report.txt"
    echo "  - Removed validation report"
fi

# Remove Python cache
find "$MODULE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$MODULE_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  - Removed Python cache"

echo -e "${GREEN}✓ Temporary files cleaned${NC}"

echo ""
echo -e "${BLUE}[5/5] Verifying cleanup...${NC}"

# Check if containers are stopped
RUNNING_CONTAINERS=$(docker ps -a | grep "module15" | wc -l)
if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    echo -e "${GREEN}✓ All containers stopped${NC}"
else
    echo -e "${YELLOW}⚠ $RUNNING_CONTAINERS containers still exist${NC}"
    echo "  Run: docker ps -a | grep module15"
fi

# Check if volumes are removed
REMAINING_VOLUMES=$(docker volume ls | grep -E "(module15|infrastructure)" | wc -l)
if [ "$REMAINING_VOLUMES" -eq 0 ]; then
    echo -e "${GREEN}✓ All volumes removed${NC}"
else
    echo -e "${YELLOW}⚠ $REMAINING_VOLUMES volumes still exist${NC}"
    echo "  Run: docker volume ls | grep module15"
fi

echo ""
echo -e "${GREEN}======================================"
echo "Cleanup Complete!"
echo -e "======================================${NC}\n"

echo "Environment has been cleaned up."
echo ""
echo "To restart the environment:"
echo "  bash scripts/setup.sh"
echo ""
echo "To remove Docker images (optional):"
echo "  docker rmi localstack/localstack:3.0"
echo "  docker rmi flink:1.18-java11"
echo "  docker rmi postgres:15-alpine"
echo "  docker rmi confluentinc/cp-kafka:7.5.0"
echo "  docker rmi confluentinc/cp-zookeeper:7.5.0"
echo "  docker rmi grafana/grafana:10.2.0"
echo ""
