#!/bin/bash

################################################################################
# SQL Foundations - Database Reset Script
################################################################################
# Description: Reset database to clean state and reload schema/data
# Usage: ./scripts/reset_db.sh [--keep-container] [--no-data]
# WARNING: This will DELETE all data in the database!
################################################################################

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$MODULE_DIR/infrastructure/docker-compose.yml"
INIT_SQL="$MODULE_DIR/infrastructure/init.sql"
DATA_DIR="$MODULE_DIR/data"

# Default options
KEEP_CONTAINER=false
NO_DATA=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-container)
            KEEP_CONTAINER=true
            shift
            ;;
        --no-data)
            NO_DATA=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --keep-container    Keep container running, only reset database"
            echo "  --no-data           Don't load sample data after reset"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "WARNING: This will DELETE all data in the database!"
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

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
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
# Reset Process
################################################################################

print_header "Database Reset - WARNING"

print_warning "This will DELETE ALL DATA in the database!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Reset cancelled"
    exit 0
fi

print_header "Resetting Database"

cd "$MODULE_DIR/infrastructure"

# Check if container is running
if ! docker ps | grep -q "sql-foundations-db"; then
    print_warning "Database container is not running"

    if [ "$KEEP_CONTAINER" = true ]; then
        print_info "Starting database container..."
        docker-compose up -d
        wait_for_postgres || exit 1
    else
        print_info "Recreating database container..."
        docker-compose down -v
        docker-compose up -d
        wait_for_postgres || exit 1
    fi
else
    if [ "$KEEP_CONTAINER" = false ]; then
        print_info "Recreating database container..."
        docker-compose down -v
        docker-compose up -d
        wait_for_postgres || exit 1
    else
        print_info "Keeping container, resetting database only..."

        # Drop and recreate database
        print_info "Dropping database..."
        docker exec sql-foundations-db psql -U postgres -c "DROP DATABASE IF EXISTS ecommerce;"

        print_info "Creating fresh database..."
        docker exec sql-foundations-db psql -U postgres -c "CREATE DATABASE ecommerce;"

        # Run init script
        print_info "Running initialization script..."
        docker exec -i sql-foundations-db psql -U postgres -d ecommerce < "$INIT_SQL"

        print_success "Database schema recreated"
    fi
fi

# Verify schema
print_info "Verifying schema..."
TABLES_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

if [ "$TABLES_COUNT" -ge 5 ]; then
    print_success "Schema verified ($TABLES_COUNT tables created)"
else
    print_error "Schema incomplete (only $TABLES_COUNT tables found)"
    exit 1
fi

# Load sample data
if [ "$NO_DATA" = false ]; then
    print_header "Loading Sample Data"

    if [ -d "$DATA_DIR" ]; then
        # Load seed data
        if [ -f "$DATA_DIR/seeds/users.csv" ]; then
            print_info "Loading users..."
            docker exec -i sql-foundations-db psql -U postgres -d ecommerce -c "\COPY users(user_id, first_name, last_name, email, country, is_active, loyalty_points, created_at) FROM STDIN WITH (FORMAT csv, HEADER true);" < "$DATA_DIR/seeds/users.csv"
            USER_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
            print_success "Loaded $USER_COUNT users"
        fi

        if [ -f "$DATA_DIR/seeds/products.csv" ]; then
            print_info "Loading products..."
            docker exec -i sql-foundations-db psql -U postgres -d ecommerce -c "\COPY products(product_id, product_name, category, price, is_available, stock_quantity, created_at) FROM STDIN WITH (FORMAT csv, HEADER true);" < "$DATA_DIR/seeds/products.csv"
            PRODUCT_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM products;" | tr -d ' ')
            print_success "Loaded $PRODUCT_COUNT products"
        fi

        # Run migrations
        if ls "$DATA_DIR/migrations"/*.sql 1> /dev/null 2>&1; then
            print_info "Running migrations..."
            for migration in "$DATA_DIR/migrations"/*.sql; do
                print_info "Applying $(basename "$migration")..."
                docker exec -i sql-foundations-db psql -U postgres -d ecommerce < "$migration"
            done
            print_success "Migrations applied"
        fi

        # Show data summary
        print_header "Data Summary"
        docker exec sql-foundations-db psql -U postgres -d ecommerce -c "
            SELECT
                'users' AS table_name,
                COUNT(*) AS row_count
            FROM users
            UNION ALL
            SELECT 'products', COUNT(*) FROM products
            UNION ALL
            SELECT 'orders', COUNT(*) FROM orders
            UNION ALL
            SELECT 'order_items', COUNT(*) FROM order_items
            UNION ALL
            SELECT 'user_activity', COUNT(*) FROM user_activity
            ORDER BY table_name;
        "
    else
        print_warning "Data directory not found, database is empty"
    fi
else
    print_info "Skipping data load (--no-data flag)"
fi

print_header "Reset Complete!"

print_success "Database has been reset successfully"
echo ""
echo "Database details:"
echo "  - Host: localhost"
echo "  - Port: 5432"
echo "  - Database: ecommerce"
echo "  - User: postgres"
echo ""
echo "Connect with:"
echo "  docker exec -it sql-foundations-db psql -U postgres -d ecommerce"
echo ""
echo "Next steps:"
echo "  1. Verify setup: ./scripts/validate.sh --fast"
echo "  2. Start exercises: cd exercises/01-basic-queries"
echo ""

cd "$MODULE_DIR"
