#!/bin/bash
# setup-environment.sh
# Initial environment setup for Cloud Data Engineering learning system

set -e  # Exit on error

echo "🚀 Setting up Cloud Data Engineering Environment"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}✓${NC} Supported OS detected: $OSTYPE"
else
    echo -e "${YELLOW}⚠${NC}  Unsupported OS. This script is tested on Linux and macOS."
fi

# Check Docker
echo ""
echo "📦 Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker installed: $DOCKER_VERSION"

    # Check if Docker is running
    if docker info &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker daemon is running"
    else
        echo -e "${RED}✗${NC} Docker daemon is not running"
        echo "   Please start Docker and run this script again"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Docker not found"
    echo "   Install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
echo ""
echo "📦 Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓${NC} Docker Compose installed: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "${GREEN}✓${NC} Docker Compose (plugin) installed: $COMPOSE_VERSION"
    alias docker-compose='docker compose'
else
    echo -e "${RED}✗${NC} Docker Compose not found"
    echo "   Install from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Python
echo ""
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python installed: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 not found"
    echo "   Install Python 3.9+ from: https://www.python.org/downloads/"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3 is available"
else
    echo -e "${RED}✗${NC} pip3 not found"
    exit 1
fi

# Create virtual environment
echo ""
echo "🔧 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}ℹ${NC}  Virtual environment already exists"
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "   Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓${NC} pip upgraded"

# Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
echo "   This may take a few minutes..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${RED}✗${NC} Failed to install dependencies"
    echo "   Try running: pip install -r requirements.txt"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p shared/data/common-datasets
mkdir -p shared/infrastructure/localstack-init
mkdir -p shared/infrastructure/postgres-init
mkdir -p shared/infrastructure/trino-config
mkdir -p .localstack
echo -e "${GREEN}✓${NC} Directories created"

# Configure AWS CLI for LocalStack
echo ""
echo "⚙️  Configuring AWS CLI for LocalStack..."
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
echo -e "${GREEN}✓${NC} AWS credentials configured for local development"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# AWS Configuration (for LocalStack)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
LOCALSTACK_ENDPOINT=http://localhost:4566

# LocalStack Configuration
LOCALSTACK_VOLUME_DIR=./localstack-volume

# PostgreSQL Configuration
POSTGRES_USER=cloudde
POSTGRES_PASSWORD=cloudde123
POSTGRES_DB=data_warehouse

# Kafka Configuration
KAFKA_BROKER=localhost:29092

# Spark Configuration
SPARK_MASTER=spark://localhost:7077

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=http://localhost:9000

# Trino Configuration
TRINO_COORDINATOR=http://localhost:8080
EOF
    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${YELLOW}ℹ${NC}  .env file already exists"
fi

# Generate sample datasets
echo ""
echo "📊 Generating sample datasets..."
if python shared/utilities/data_generators.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Sample datasets generated"
else
    echo -e "${YELLOW}⚠${NC}  Sample dataset generation skipped (run manually if needed)"
fi

# Pull Docker images
echo ""
echo "🐳 Pulling Docker images..."
echo "   This may take several minutes on first run..."
if docker-compose pull > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker images pulled"
else
    echo -e "${YELLOW}⚠${NC}  Docker pull incomplete. Images will be pulled on first 'docker-compose up'"
fi

# Print next steps
echo ""
echo "================================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start services:"
echo "   make up"
echo "   (or: docker-compose up -d)"
echo ""
echo "2. Check service status:"
echo "   docker-compose ps"
echo ""
echo "3. View the learning path:"
echo "   cat LEARNING-PATH.md"
echo ""
echo "4. Start with Module 01:"
echo "   cd modules/module-01-cloud-fundamentals"
echo "   cat README.md"
echo ""
echo "5. Check your progress anytime:"
echo "   make progress"
echo ""
echo "📚 Resources:"
echo "   - Setup Guide: docs/setup-guide.md"
echo "   - LocalStack Guide: docs/localstack-guide.md"
echo "   - Troubleshooting: docs/troubleshooting.md"
echo ""
echo "💡 Tips:"
echo "   - Services will be available at:"
echo "     • LocalStack: http://localhost:4566"
echo "     • MinIO Console: http://localhost:9001"
echo "     • Kafka: localhost:29092"
echo "     • PostgreSQL: localhost:5432"
echo "     • Trino: http://localhost:8080"
echo "     • Spark UI: http://localhost:8081"
echo ""
echo "   - To stop services: make down"
echo "   - To clean everything: make clean"
echo ""
echo "Happy Learning! 🎓"
