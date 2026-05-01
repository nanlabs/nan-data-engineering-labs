#!/bin/bash

################################################################################
# SQL Foundations - Complete Environment Setup Script
################################################################################
# Description: Automated setup for Module 03 - SQL Foundations
# Usage: ./scripts/setup.sh [--skip-docker] [--skip-python] [--skip-data]
# Requirements: Docker, Python 3.8+, pip
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$MODULE_DIR/infrastructure/docker-compose.yml"
ENV_FILE="$MODULE_DIR/infrastructure/.env"
INIT_SQL="$MODULE_DIR/infrastructure/init.sql"
REQUIREMENTS_FILE="$MODULE_DIR/requirements.txt"

# Parse arguments
SKIP_DOCKER=false
SKIP_PYTHON=false
SKIP_DATA=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --skip-data)
            SKIP_DATA=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-docker    Skip Docker setup"
            echo "  --skip-python    Skip Python environment setup"
            echo "  --skip-data      Skip loading sample data"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

wait_for_postgres() {
    local max_attempts=30
    local attempt=0

    print_info "Waiting for PostgreSQL to be ready..."

    while [ $attempt -lt $max_attempts ]; do
        if docker exec sql-foundations-db pg_isready -U postgres -d ecommerce &> /dev/null; then
            print_success "PostgreSQL is ready!"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done

    print_error "PostgreSQL did not become ready in time"
    return 1
}

################################################################################
# Setup Steps
################################################################################

print_header "Module 03: SQL Foundations - Environment Setup"

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"

if ! $SKIP_DOCKER; then
    check_command "docker" || exit 1
    check_command "docker-compose" || check_command "docker compose" || exit 1
fi

if ! $SKIP_PYTHON; then
    check_command "python3" || check_command "python" || exit 1
    check_command "pip3" || check_command "pip" || exit 1
fi

# Step 2: Set up environment file
print_header "Step 2: Setting Up Environment"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$MODULE_DIR/infrastructure/.env.example" ]; then
        print_info "Creating .env file from .env.example..."
        cp "$MODULE_DIR/infrastructure/.env.example" "$ENV_FILE"
        print_success ".env file created"
    else
        print_warning ".env.example not found, creating default .env..."
        cat > "$ENV_FILE" << 'EOF'
# PostgreSQL Configuration
POSTGRES_DB=ecommerce
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

# PgAdmin Configuration (optional)
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin123
PGADMIN_PORT=5050
EOF
        print_success "Default .env file created"
    fi
else
    print_success ".env file already exists"
fi

# Step 3: Set up Docker containers
if ! $SKIP_DOCKER; then
    print_header "Step 3: Setting Up Docker Containers"

    cd "$MODULE_DIR/infrastructure"

    # Check if containers are already running
    if docker ps | grep -q "sql-foundations-db"; then
        print_warning "Database container is already running"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Stopping and removing existing containers..."
            docker-compose down -v
        else
            print_info "Using existing container"
        fi
    fi

    if ! docker ps | grep -q "sql-foundations-db"; then
        print_info "Starting Docker containers..."
        docker-compose up -d

        # Wait for PostgreSQL to be ready
        if wait_for_postgres; then
            print_success "Database is up and running"
        else
            print_error "Failed to start database"
            exit 1
        fi
    fi

    # Verify database initialization
    print_info "Verifying database schema..."
    TABLES_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

    if [ "$TABLES_COUNT" -ge 5 ]; then
        print_success "Database schema initialized ($TABLES_COUNT tables created)"
    else
        print_error "Database schema incomplete (only $TABLES_COUNT tables found)"
        exit 1
    fi

    cd "$MODULE_DIR"
else
    print_info "Skipping Docker setup"
fi

# Step 4: Set up Python environment
if ! $SKIP_PYTHON; then
    print_header "Step 4: Setting Up Python Environment"

    # Check if virtual environment exists
    if [ ! -d "$MODULE_DIR/venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv "$MODULE_DIR/venv"
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi

    # Activate virtual environment
    print_info "Activating virtual environment..."
    source "$MODULE_DIR/venv/bin/activate"

    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        print_info "Installing Python dependencies..."
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r "$REQUIREMENTS_FILE" > /dev/null 2>&1
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
else
    print_info "Skipping Python setup"
fi

# Step 5: Load sample data
if ! $SKIP_DATA && ! $SKIP_DOCKER; then
    print_header "Step 5: Loading Sample Data"

    DATA_DIR="$MODULE_DIR/data"

    if [ -d "$DATA_DIR" ]; then
        print_info "Checking for seed data files..."

        # Load seed data if available
        if [ -f "$DATA_DIR/seeds/users.csv" ]; then
            print_info "Loading users seed data..."
            docker exec -i sql-foundations-db psql -U postgres -d ecommerce -c "\COPY users(user_id, first_name, last_name, email, country, is_active, loyalty_points, created_at) FROM STDIN WITH (FORMAT csv, HEADER true);" < "$DATA_DIR/seeds/users.csv"
            print_success "Users data loaded"
        fi

        if [ -f "$DATA_DIR/seeds/products.csv" ]; then
            print_info "Loading products seed data..."
            docker exec -i sql-foundations-db psql -U postgres -d ecommerce -c "\COPY products(product_id, product_name, category, price, is_available, stock_quantity, created_at) FROM STDIN WITH (FORMAT csv, HEADER true);" < "$DATA_DIR/seeds/products.csv"
            print_success "Products data loaded"
        fi

        # Run migrations if available
        if ls "$DATA_DIR/migrations"/*.sql 1> /dev/null 2>&1; then
            print_info "Running migrations..."
            for migration in "$DATA_DIR/migrations"/*.sql; do
                print_info "Applying $(basename "$migration")..."
                docker exec -i sql-foundations-db psql -U postgres -d ecommerce < "$migration"
            done
            print_success "Migrations applied"
        fi

        # Verify data
        print_info "Verifying data..."
        USER_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
        PRODUCT_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM products;" | tr -d ' ')

        print_success "Data loaded: $USER_COUNT users, $PRODUCT_COUNT products"
    else
        print_warning "Data directory not found, skipping sample data load"
    fi
else
    print_info "Skipping data load"
fi

# Step 6: Verify installation
print_header "Step 6: Verifying Installation"

if ! $SKIP_DOCKER; then
    # Check database connection
    if docker exec sql-foundations-db psql -U postgres -d ecommerce -c "SELECT 1;" &> /dev/null; then
        print_success "Database connection successful"
    else
        print_error "Database connection failed"
        exit 1
    fi

    # List available tables
    print_info "Available tables:"
    docker exec sql-foundations-db psql -U postgres -d ecommerce -c "\dt" | grep "public" | awk '{print "  - " $3}'
fi

if ! $SKIP_PYTHON && [ -d "$MODULE_DIR/venv" ]; then
    print_info "Python packages installed:"
    pip list | grep -E "(psycopg2|pytest|pandas|sqlalchemy)" | awk '{print "  - " $1 " (" $2 ")"}'
fi

# Final summary
print_header "Setup Complete!"

echo -e "${GREEN}✓ Environment is ready for SQL Foundations module${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run tests: pytest validation/"
echo "  3. Start exercises: cd exercises/01-basic-queries"
echo ""
echo "Useful commands:"
echo "  - Connect to database: docker exec -it sql-foundations-db psql -U postgres -d ecommerce"
echo "  - View logs: docker-compose -f infrastructure/docker-compose.yml logs -f"
echo "  - Stop containers: docker-compose -f infrastructure/docker-compose.yml down"
echo "  - Reset database: ./scripts/reset_db.sh"
echo ""
echo "Access points:"
if ! $SKIP_DOCKER; then
    echo "  - PostgreSQL: localhost:5432 (user: postgres, db: ecommerce)"
    if docker ps | grep -q "pgadmin"; then
        echo "  - PgAdmin: http://localhost:5050"
    fi
fi
echo ""
print_success "Happy learning! 🚀"
