#!/bin/bash

###############################################################################
# Module 18: Advanced Architectures - Setup Script
#
# This script sets up the local development environment for advanced
# architecture exercises (Lambda, Kappa, Data Mesh, CQRS).
#
# What it does:
# - Checks prerequisites (Python, Docker, AWS CLI, Kafka)
# - Creates Python virtual environment
# - Installs Python dependencies
# - Starts Docker containers (LocalStack, Redis, Kafka, Jupyter)
# - Initializes AWS resources
# - Validates setup
#
# Usage: ./scripts/setup.sh [--env localstack|aws]
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

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Module 18: Advanced Architectures - Setup                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

###############################################################################
# 1. Check Prerequisites
###############################################################################

log_info "Checking prerequisites..."

missing_deps=0

# Python 3.9+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION"
else
    log_error "Python 3.9+ required"
    missing_deps=1
fi

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    log_success "Docker $DOCKER_VERSION"
else
    log_error "Docker required"
    missing_deps=1
fi

# Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    log_success "Docker Compose"
else
    log_error "Docker Compose required"
    missing_deps=1
fi

# AWS CLI
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version | cut -d' ' -f1 | cut -d'/' -f2)
    log_success "AWS CLI $AWS_VERSION"
else
    log_error "AWS CLI required (pip install awscli)"
    missing_deps=1
fi

# jq (for JSON parsing)
if command -v jq &> /dev/null; then
    log_success "jq"
else
    log_warning "jq recommended (brew install jq or apt install jq)"
fi

if [ $missing_deps -ne 0 ]; then
    log_error "Missing required dependencies. Please install and try again."
    exit 1
fi

###############################################################################
# 2. Create Python Virtual Environment
###############################################################################

log_info "Setting up Python environment..."

cd "$MODULE_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Created virtual environment"
else
    log_info "Virtual environment exists"
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
log_success "Upgraded pip"

# Install dependencies
if [ -f "requirements.txt" ]; then
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    log_success "Installed dependencies"
fi

###############################################################################
# 3. Create Directories
###############################################################################

log_info "Creating directory structure..."

mkdir -p data/{raw,processed,curated,batch-views,stream-checkpoints,localstack}
mkdir -p logs
mkdir -p infrastructure/{sql,grafana/{dashboards,datasources}}

log_success "Created directories"

###############################################################################
# 4. Start Docker Containers
###############################################################################

log_info "Starting Docker containers..."

cd "$MODULE_DIR/infrastructure"

# Check if containers are already running
if docker ps | grep -q "advanced-architectures"; then
    log_warning "Containers already running. Stopping..."
    docker-compose down
fi

# Start containers
docker-compose up -d

log_info "Waiting for services to be healthy..."
sleep 10

# Check LocalStack
if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
    log_success "LocalStack ready"
else
    log_warning "LocalStack not responding (may need more time)"
fi

# Check Redis
if docker exec advanced-architectures-redis redis-cli ping > /dev/null 2>&1; then
    log_success "Redis ready"
else
    log_warning "Redis not responding"
fi

# Check PostgreSQL
if docker exec advanced-architectures-postgres pg_isready -U analytics > /dev/null 2>&1; then
    log_success "PostgreSQL ready"
else
    log_warning "PostgreSQL not responding"
fi

# Check Kafka
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    log_success "Kafka UI ready (http://localhost:8080)"
else
    log_warning "Kafka UI not ready yet"
fi

###############################################################################
# 5. Initialize AWS Resources
###############################################################################

log_info "Initializing AWS resources..."

cd "$MODULE_DIR"

if [ -f "infrastructure/init-aws.sh" ]; then
    chmod +x infrastructure/init-aws.sh
    ./infrastructure/init-aws.sh --env "$ENVIRONMENT"
    log_success "AWS resources initialized"
else
    log_warning "init-aws.sh not found"
fi

###############################################################################
# 6. Validate Setup
###############################################################################

log_info "Validating setup..."

# Test AWS connectivity
if [ "$ENVIRONMENT" = "localstack" ]; then
    if aws --endpoint-url=http://localhost:4566 s3 ls > /dev/null 2>&1; then
        log_success "AWS connectivity verified"
    else
        log_error "Cannot connect to LocalStack"
    fi
fi

# Test Redis
if python3 -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping()" 2>/dev/null; then
    log_success "Redis connection verified"
else
    log_warning "Cannot connect to Redis"
fi

# Test PostgreSQL
if python3 -c "import psycopg2; psycopg2.connect('host=localhost dbname=data_lakehouse user=analytics password=analytics')" 2>/dev/null; then
    log_success "PostgreSQL connection verified"
else
    log_warning "Cannot connect to PostgreSQL"
fi

###############################################################################
# Summary
###############################################################################

echo ""
log_success "Setup complete!"
echo ""
log_info "Services running:"
echo "  - LocalStack:    http://localhost:4566"
echo "  - Jupyter:       http://localhost:8888"
echo "  - Kafka UI:      http://localhost:8080"
echo "  - Grafana:       http://localhost:3000 (admin/admin)"
echo "  - Redis:         localhost:6379"
echo "  - PostgreSQL:    localhost:5432"
echo ""
log_info "Next steps:"
echo "  1. Activate environment:  source venv/bin/activate"
echo "  2. Start exercises:       cd exercises/01-lambda-architecture"
echo "  3. Run validation:        ./scripts/validate.sh"
echo ""
log_info "To view logs:"
echo "  docker-compose -f infrastructure/docker-compose.yml logs -f [service]"
echo ""
log_info "To stop services:"
echo "  ./scripts/cleanup.sh"
echo ""
