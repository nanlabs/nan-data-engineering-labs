#!/bin/bash

# Module 15: Real-Time Analytics - Environment Setup Script
# Sets up the complete real-time analytics environment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$MODULE_DIR")")"

echo -e "${BLUE}====================================="
echo "Module 15: Real-Time Analytics Setup"
echo -e "=====================================${NC}\n"

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose is installed"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_warning "AWS CLI is not installed. Installing via pip..."
    pip install awscli-local
fi
print_success "AWS CLI is available"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+."
    exit 1
fi
print_success "Python 3 is installed"

# Step 1: Install Python dependencies
print_status "Installing Python dependencies..."
cd "$MODULE_DIR"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    print_success "Python dependencies installed"
else
    print_warning "No requirements.txt found, skipping Python dependencies"
fi

# Step 2: Create necessary directories
print_status "Creating directories..."
mkdir -p "$MODULE_DIR/infrastructure/localstack-data"
mkdir -p "$MODULE_DIR/infrastructure/flink-jobs"
mkdir -p "$MODULE_DIR/infrastructure/grafana/dashboards"
mkdir -p "$MODULE_DIR/infrastructure/grafana/datasources"
mkdir -p "$MODULE_DIR/data/output"
mkdir -p "$MODULE_DIR/logs"
print_success "Directories created"

# Step 3: Make scripts executable
print_status "Making scripts executable..."
chmod +x "$MODULE_DIR/infrastructure/init-aws.sh"
chmod +x "$SCRIPT_DIR"/*.sh
print_success "Scripts are executable"

# Step 4: Start Docker containers
print_status "Starting Docker containers..."
cd "$MODULE_DIR/infrastructure"

# Stop any existing containers
docker-compose down -v 2>/dev/null || true

# Start containers
docker-compose up -d

print_success "Docker containers started"

# Step 5: Wait for services to be ready
print_status "Waiting for services to be ready (this may take 30-60 seconds)..."

# Wait for LocalStack
echo -n "  - LocalStack: "
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:4566/_localstack/health | grep -q '"kinesis": "available"'; then
        print_success "Ready"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    print_error "LocalStack failed to start"
    exit 1
fi

# Wait for Flink Job Manager
echo -n "  - Flink Job Manager: "
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8081/overview > /dev/null 2>&1; then
        print_success "Ready"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    print_warning "Flink Job Manager may not be ready, but continuing..."
fi

# Wait for PostgreSQL
echo -n "  - PostgreSQL: "
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec module15-postgres pg_isready -U flink > /dev/null 2>&1; then
        print_success "Ready"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

# Wait for Kafka
echo -n "  - Kafka: "
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec module15-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        print_success "Ready"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

# Step 6: AWS services are initialized automatically via init-aws.sh
print_status "AWS services initialized by LocalStack init script"

# Step 7: Verify setup
print_status "Verifying setup..."

# Check Kinesis streams
STREAMS=$(awslocal kinesis list-streams --region us-east-1 2>/dev/null | grep -c "events-stream" || echo "0")
if [ "$STREAMS" -gt 0 ]; then
    print_success "Kinesis streams created"
else
    print_warning "Kinesis streams not found (may still be initializing)"
fi

# Check DynamoDB tables
TABLES=$(awslocal dynamodb list-tables --region us-east-1 2>/dev/null | grep -c "realtime-aggregates" || echo "0")
if [ "$TABLES" -gt 0 ]; then
    print_success "DynamoDB tables created"
else
    print_warning "DynamoDB tables not found (may still be initializing)"
fi

# Step 8: Load sample data
print_status "Loading sample data (if available)..."
if [ -f "$MODULE_DIR/data/sample/streaming-events.json" ]; then
    python3 "$SCRIPT_DIR/load-sample-data.py" 2>/dev/null || print_warning "Could not load sample data"
else
    print_warning "No sample data file found, skipping data load"
fi

# Step 9: Create test Kafka topics
print_status "Creating Kafka topics for testing..."
docker exec module15-kafka kafka-topics --create --if-not-exists \
    --topic events --partitions 4 --replication-factor 1 \
    --bootstrap-server localhost:9092 > /dev/null 2>&1 || true

docker exec module15-kafka kafka-topics --create --if-not-exists \
    --topic aggregates --partitions 2 --replication-factor 1 \
    --bootstrap-server localhost:9092 > /dev/null 2>&1 || true

print_success "Kafka topics created"

echo ""
echo -e "${GREEN}====================================="
echo "Setup Complete!"
echo -e "=====================================${NC}\n"

echo "Available Services:"
echo "  - LocalStack (AWS):      http://localhost:4566"
echo "  - Flink Web UI:          http://localhost:8081"
echo "  - Grafana:               http://localhost:3000 (admin/admin123)"
echo "  - PostgreSQL:            localhost:5432 (flink/flink123)"
echo "  - Kafka:                 localhost:9092"
echo ""
echo "AWS Resources (LocalStack):"
echo "  - Kinesis Streams:       events-stream, aggregated-stream, fraud-alerts-stream, dlq-stream"
echo "  - DynamoDB Tables:       realtime-aggregates, user-sessions, fraud-detections"
echo "  - S3 Buckets:            analytics-checkpoints, analytics-savepoints, analytics-data-lake"
echo ""
echo "Useful Commands:"
echo "  List Kinesis streams:    awslocal kinesis list-streams"
echo "  List DynamoDB tables:    awslocal dynamodb list-tables"
echo "  View Flink jobs:         curl http://localhost:8081/jobs"
echo "  Stop environment:        docker-compose down"
echo ""
echo "Next Steps:"
echo "  1. Read theory/concepts.md for fundamentals"
echo "  2. Start with exercises/01-kinesis-analytics-sql/"
echo "  3. Access Flink UI to monitor jobs: http://localhost:8081"
echo ""
