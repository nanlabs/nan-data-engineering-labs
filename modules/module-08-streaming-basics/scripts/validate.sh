#!/bin/bash
# Module 08: Streaming Basics - Validation Script
# Validates module setup and runs tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Module 08: Streaming Basics - Validation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

ERRORS=0

# ==================== Check Docker Services ====================

echo -e "${YELLOW}[1/7] Checking Docker services...${NC}"

check_container() {
    local CONTAINER=$1
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo -e "  ${GREEN}✓${NC} $CONTAINER running"
        return 0
    else
        echo -e "  ${RED}✗${NC} $CONTAINER not running"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

check_container "kafka"
check_container "zookeeper"
check_container "schema-registry"

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Docker services not running. Run './scripts/setup.sh' first.${NC}"
    exit 1
fi

echo ""

# ==================== Check Kafka Connectivity ====================

echo -e "${YELLOW}[2/7] Checking Kafka connectivity...${NC}"

if docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Kafka is accessible"
else
    echo -e "  ${RED}✗${NC} Cannot connect to Kafka"
    ERRORS=$((ERRORS+1))
fi

# List topics
TOPIC_COUNT=$(docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list | wc -l)
echo -e "  ${GREEN}✓${NC} Found $TOPIC_COUNT topics"

echo ""

# ==================== Check Schema Registry ====================

echo -e "${YELLOW}[3/7] Checking Schema Registry...${NC}"

if curl -s http://localhost:8081/subjects &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Schema Registry is accessible"

    SUBJECT_COUNT=$(curl -s http://localhost:8081/subjects | jq '. | length')
    echo -e "  ${GREEN}✓${NC} Registered schemas: $SUBJECT_COUNT"
else
    echo -e "  ${RED}✗${NC} Cannot connect to Schema Registry"
    ERRORS=$((ERRORS+1))
fi

echo ""

# ==================== Check Python Dependencies ====================

echo -e "${YELLOW}[4/7] Checking Python dependencies...${NC}"

cd "$MODULE_DIR"

check_package() {
    local PACKAGE=$1
    if python3 -c "import $PACKAGE" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $PACKAGE installed"
        return 0
    else
        echo -e "  ${RED}✗${NC} $PACKAGE not installed"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

check_package "kafka"
check_package "confluent_kafka"
check_package "pyflink"
check_package "boto3"
check_package "pytest"
check_package "fastavro"

echo ""

# ==================== Verify File Structure ====================

echo -e "${YELLOW}[5/7] Verifying file structure...${NC}"

check_file() {
    local FILE=$1
    if [ -f "$MODULE_DIR/$FILE" ]; then
        echo -e "  ${GREEN}✓${NC} $FILE"
        return 0
    else
        echo -e "  ${RED}✗${NC} $FILE missing"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

check_dir() {
    local DIR=$1
    if [ -d "$MODULE_DIR/$DIR" ]; then
        echo -e "  ${GREEN}✓${NC} $DIR/"
        return 0
    else
        echo -e "  ${RED}✗${NC} $DIR/ missing"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

# Check key files
check_file "requirements.txt"
check_file "README.md"
check_file "STATUS.md"
check_file "pytest.ini"

# Check directories
check_dir "theory"
check_dir "exercises"
check_dir "infrastructure"
check_dir "data/schemas"
check_dir "validation"

echo ""

# ==================== Check Theory Content ====================

echo -e "${YELLOW}[6/7] Checking theory content...${NC}"

check_theory() {
    local FILE=$1
    local MIN_SIZE=$2

    if [ -f "$MODULE_DIR/theory/$FILE" ]; then
        local SIZE=$(wc -c < "$MODULE_DIR/theory/$FILE")
        if [ $SIZE -ge $MIN_SIZE ]; then
            echo -e "  ${GREEN}✓${NC} $FILE (${SIZE} bytes)"
            return 0
        else
            echo -e "  ${YELLOW}⚠${NC} $FILE too small (${SIZE} bytes, expected > ${MIN_SIZE})"
            return 1
        fi
    else
        echo -e "  ${RED}✗${NC} $FILE missing"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

check_theory "01-concepts.md" 10000
check_theory "02-architecture.md" 10000
check_theory "03-resources.md" 5000

echo ""

# ==================== Run Tests ====================

echo -e "${YELLOW}[7/7] Running validation tests...${NC}"

cd "$MODULE_DIR"

# Run pytest with specific markers
echo ""
echo "Running unit tests..."
pytest validation/ -v -m "not slow and not aws" --tb=short

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    ERRORS=$((ERRORS+1))
fi

echo ""

# ==================== Summary ====================

echo -e "${GREEN}========================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Validation Complete - All Checks Passed${NC}"
else
    echo -e "${RED}✗ Validation Failed - $ERRORS errors found${NC}"
fi
echo -e "${GREEN}========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "Module Status: ✓ READY"
    echo ""
    echo "Next steps:"
    echo "  1. Review theory: cat theory/01-concepts.md"
    echo "  2. Start Exercise 01: cd exercises/01-kafka-basics"
    echo "  3. Open Kafka UI: http://localhost:8080"
    echo ""
    echo "To run specific test suites:"
    echo "  pytest validation/ -v -m kafka       # Kafka tests only"
    echo "  pytest validation/ -v -m integration # Integration tests"
    echo "  pytest validation/ -v -m slow        # Performance tests"
    echo ""
else
    echo "Please fix the errors above and run validation again."
    echo ""
    exit 1
fi
