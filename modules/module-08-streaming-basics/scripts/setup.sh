#!/bin/bash
# Module 08: Streaming Basics - Setup Script
# Initializes the streaming environment with Docker and sample data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$MODULE_DIR/infrastructure"
DATA_DIR="$MODULE_DIR/data"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Module 08: Streaming Basics - Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ==================== Check Prerequisites ====================

echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8+.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION installed${NC}"

echo ""

# ==================== Install Python Dependencies ====================

echo -e "${YELLOW}[2/6] Installing Python dependencies...${NC}"

cd "$MODULE_DIR"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

echo ""

# ==================== Start Docker Services ====================

echo -e "${YELLOW}[3/6] Starting Docker services...${NC}"

cd "$INFRA_DIR"

# Stop existing containers
docker-compose down 2>/dev/null || true

# Start services
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check Kafka
echo -n "Waiting for Kafka..."
MAX_RETRIES=30
RETRY=0
until docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; do
    RETRY=$((RETRY+1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo -e "\n${RED}✗ Kafka failed to start${NC}"
        docker-compose logs kafka
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓${NC}"

# Check Schema Registry
echo -n "Waiting for Schema Registry..."
RETRY=0
until curl -s http://localhost:8081/subjects &> /dev/null; do
    RETRY=$((RETRY+1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo -e "\n${RED}✗ Schema Registry failed to start${NC}"
        docker-compose logs schema-registry
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓${NC}"

echo -e "${GREEN}✓ All services running${NC}"

echo ""

# ==================== Create Kafka Topics ====================

echo -e "${YELLOW}[4/6] Creating Kafka topics...${NC}"

# Function to create topic
create_topic() {
    local TOPIC_NAME=$1
    local PARTITIONS=$2

    docker exec kafka kafka-topics \
        --create \
        --bootstrap-server localhost:9092 \
        --topic "$TOPIC_NAME" \
        --partitions "$PARTITIONS" \
        --replication-factor 1 \
        --if-not-exists &> /dev/null

    echo -e "  ${GREEN}✓${NC} Created topic: $TOPIC_NAME (partitions: $PARTITIONS)"
}

# Create topics
create_topic "user-events" 3
create_topic "sensor-readings" 6
create_topic "transactions" 4
create_topic "high-value-transactions" 2
create_topic "processed-events" 3
create_topic "failed-events-dlq" 1

echo ""

# ==================== Generate Sample Data ====================

echo -e "${YELLOW}[5/6] Generating sample data...${NC}"

cd "$DATA_DIR/scripts"

# Generate sample events (batch mode)
python3 stream_generator.py \
    --type user \
    --mode batch \
    --count 100 \
    --output ../samples/user_events_sample.json

echo -e "  ${GREEN}✓${NC} Generated 100 user events"

python3 stream_generator.py \
    --type sensor \
    --mode batch \
    --count 100 \
    --output ../samples/sensor_readings_sample.json

echo -e "  ${GREEN}✓${NC} Generated 100 sensor readings"

python3 stream_generator.py \
    --type transaction \
    --mode batch \
    --count 100 \
    --output ../samples/transactions_sample.json

echo -e "  ${GREEN}✓${NC} Generated 100 transactions"

echo ""

# ==================== Verify Setup ====================

echo -e "${YELLOW}[6/6] Verifying setup...${NC}"

# List topics
TOPIC_COUNT=$(docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list | wc -l)
echo -e "  ${GREEN}✓${NC} Topics created: $TOPIC_COUNT"

# Check Kafka UI
if curl -s http://localhost:8080 &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Kafka UI accessible at http://localhost:8080"
else
    echo -e "  ${YELLOW}⚠${NC} Kafka UI not accessible (may still be starting)"
fi

# Check Schema Registry
SUBJECT_COUNT=$(curl -s http://localhost:8081/subjects | jq '. | length')
echo -e "  ${GREEN}✓${NC} Schema Registry accessible (subjects: $SUBJECT_COUNT)"

echo ""

# ==================== Summary ====================

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services:"
echo "  • Kafka: localhost:9092"
echo "  • Schema Registry: http://localhost:8081"
echo "  • Kafka UI: http://localhost:8080"
echo ""
echo "Sample data available in:"
echo "  • $DATA_DIR/samples/"
echo ""
echo "Next steps:"
echo "  1. Open Kafka UI: http://localhost:8080"
echo "  2. Explore exercises: cd exercises/01-kafka-basics"
echo "  3. Run validation: cd .. && ./scripts/validate.sh"
echo ""
echo "To stream events continuously:"
echo "  cd data/scripts"
echo "  python3 stream_generator.py --type user --mode stream --rate 10"
echo ""
