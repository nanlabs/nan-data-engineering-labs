#!/bin/bash

################################################################################
# SQL Foundations - Load Sample Data Script
################################################################################
# Description: Load seed data and run migrations
# Usage: ./scripts/load_sample_data.sh [--clear-first]
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
DATA_DIR="$MODULE_DIR/data"

# Default options
CLEAR_FIRST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clear-first)
            CLEAR_FIRST=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clear-first    Clear existing data before loading"
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

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

################################################################################
# Data Loading
################################################################################

print_header "Loading Sample Data"

# Check if database is running
if ! docker ps | grep -q "sql-foundations-db"; then
    print_error "Database container is not running"
    print_info "Run: ./scripts/setup.sh"
    exit 1
fi

# Check if database is accessible
if ! docker exec sql-foundations-db psql -U postgres -d ecommerce -c "SELECT 1;" &> /dev/null; then
    print_error "Cannot connect to database"
    exit 1
fi

print_success "Database connection verified"

# Clear existing data if requested
if [ "$CLEAR_FIRST" = true ]; then
    print_warning "Clearing existing data..."

    docker exec sql-foundations-db psql -U postgres -d ecommerce << 'EOF'
        TRUNCATE TABLE user_activity CASCADE;
        TRUNCATE TABLE order_items CASCADE;
        TRUNCATE TABLE orders CASCADE;
        TRUNCATE TABLE products CASCADE;
        TRUNCATE TABLE users CASCADE;
EOF

    print_success "Existing data cleared"
fi

# Check data directory
if [ ! -d "$DATA_DIR" ]; then
    print_error "Data directory not found: $DATA_DIR"
    exit 1
fi

# Load seed data
print_header "Step 1: Loading Seed Data"

if [ -f "$DATA_DIR/seeds/users.csv" ]; then
    print_info "Loading users from CSV..."

    docker exec -i sql-foundations-db psql -U postgres -d ecommerce -c "\COPY users(user_id, first_name, last_name, email, country, is_active, loyalty_points, created_at) FROM STDIN WITH (FORMAT csv, HEADER true);" < "$DATA_DIR/seeds/users.csv"

    USER_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
    print_success "Loaded $USER_COUNT users"
else
    print_warning "users.csv not found, skipping"
fi

if [ -f "$DATA_DIR/seeds/products.csv" ]; then
    print_info "Loading products from CSV..."

    docker exec -i sql-foundations-db psql -U postgres -d ecommerce -c "\COPY products(product_id, product_name, category, price, is_available, stock_quantity, created_at) FROM STDIN WITH (FORMAT csv, HEADER true);" < "$DATA_DIR/seeds/products.csv"

    PRODUCT_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM products;" | tr -d ' ')
    print_success "Loaded $PRODUCT_COUNT products"
else
    print_warning "products.csv not found, skipping"
fi

# Run migrations
print_header "Step 2: Running Migrations"

if [ -d "$DATA_DIR/migrations" ]; then
    MIGRATION_COUNT=0

    for migration in "$DATA_DIR/migrations"/*.sql; do
        if [ -f "$migration" ]; then
            MIGRATION_NAME=$(basename "$migration")
            print_info "Applying $MIGRATION_NAME..."

            docker exec -i sql-foundations-db psql -U postgres -d ecommerce < "$migration"

            MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
            print_success "$MIGRATION_NAME applied"
        fi
    done

    if [ $MIGRATION_COUNT -eq 0 ]; then
        print_warning "No migration files found"
    else
        print_success "Applied $MIGRATION_COUNT migration(s)"
    fi
else
    print_warning "Migrations directory not found"
fi

# Generate additional data using SQL
print_header "Step 3: Generating Additional Data"

print_info "Generating sample orders..."

docker exec sql-foundations-db psql -U postgres -d ecommerce << 'EOF'
-- Generate random orders
INSERT INTO orders (user_id, status, total_amount, order_date)
SELECT
    (ARRAY(SELECT user_id FROM users WHERE is_active = TRUE))[floor(random() * (SELECT COUNT(*) FROM users WHERE is_active = TRUE) + 1)],
    (ARRAY['pending', 'processing', 'shipped', 'delivered', 'cancelled'])[floor(random() * 5 + 1)],
    (random() * 1000 + 50)::DECIMAL(10,2),
    CURRENT_DATE - (random() * 365)::INTEGER
FROM generate_series(1, 200);
EOF

ORDER_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM orders;" | tr -d ' ')
print_success "Generated $ORDER_COUNT orders"

print_info "Generating order items..."

docker exec sql-foundations-db psql -U postgres -d ecommerce << 'EOF'
-- Generate order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
SELECT
    o.order_id,
    (ARRAY(SELECT product_id FROM products WHERE is_available = TRUE))[floor(random() * (SELECT COUNT(*) FROM products WHERE is_available = TRUE) + 1)],
    floor(random() * 5 + 1)::INTEGER,
    p.price,
    floor(random() * 5 + 1)::INTEGER * p.price
FROM orders o
CROSS JOIN LATERAL (
    SELECT price FROM products WHERE is_available = TRUE ORDER BY random() LIMIT 1
) p
WHERE NOT EXISTS (SELECT 1 FROM order_items WHERE order_id = o.order_id LIMIT 3);
EOF

ITEM_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM order_items;" | tr -d ' ')
print_success "Generated $ITEM_COUNT order items"

print_info "Generating user activity..."

docker exec sql-foundations-db psql -U postgres -d ecommerce << 'EOF'
-- Generate user activity
INSERT INTO user_activity (user_id, activity_type, activity_timestamp, page_url, session_duration)
SELECT
    (ARRAY(SELECT user_id FROM users))[floor(random() * (SELECT COUNT(*) FROM users) + 1)],
    (ARRAY['page_view', 'product_view', 'add_to_cart', 'purchase', 'search'])[floor(random() * 5 + 1)],
    CURRENT_TIMESTAMP - (random() * INTERVAL '90 days'),
    '/product/' || floor(random() * 1000),
    floor(random() * 600)::INTEGER
FROM generate_series(1, 1000);
EOF

ACTIVITY_COUNT=$(docker exec sql-foundations-db psql -U postgres -d ecommerce -t -c "SELECT COUNT(*) FROM user_activity;" | tr -d ' ')
print_success "Generated $ACTIVITY_COUNT activity records"

# Verify data
print_header "Data Summary"

docker exec sql-foundations-db psql -U postgres -d ecommerce -c "
    SELECT
        table_name,
        row_count,
        pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) AS size
    FROM (
        SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
        UNION ALL
        SELECT 'products', COUNT(*) FROM products
        UNION ALL
        SELECT 'orders', COUNT(*) FROM orders
        UNION ALL
        SELECT 'order_items', COUNT(*) FROM order_items
        UNION ALL
        SELECT 'user_activity', COUNT(*) FROM user_activity
    ) t
    ORDER BY table_name;
"

print_header "Sample Data Queries"

print_info "Top 5 customers by order count:"
docker exec sql-foundations-db psql -U postgres -d ecommerce -c "
    SELECT
        u.user_id,
        u.first_name || ' ' || u.last_name AS name,
        COUNT(o.order_id) AS order_count,
        COALESCE(SUM(o.total_amount), 0)::DECIMAL(10,2) AS total_spent
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.user_id, u.first_name, u.last_name
    ORDER BY order_count DESC, total_spent DESC
    LIMIT 5;
"

print_info "Product sales summary:"
docker exec sql-foundations-db psql -U postgres -d ecommerce -c "
    SELECT
        category,
        COUNT(DISTINCT product_id) AS products,
        SUM(CASE WHEN is_available THEN 1 ELSE 0 END) AS available,
        ROUND(AVG(price), 2) AS avg_price
    FROM products
    GROUP BY category
    ORDER BY category;
"

print_header "Load Complete!"

print_success "Sample data loaded successfully"
echo ""
echo "Data statistics:"
echo "  - Users: $USER_COUNT"
echo "  - Products: $PRODUCT_COUNT"
echo "  - Orders: $ORDER_COUNT"
echo "  - Order Items: $ITEM_COUNT"
echo "  - User Activity: $ACTIVITY_COUNT"
echo ""
echo "Next steps:"
echo "  1. Explore data: docker exec -it sql-foundations-db psql -U postgres -d ecommerce"
echo "  2. Run validation: ./scripts/validate.sh"
echo "  3. Start exercises: cd exercises/01-basic-queries"
echo ""
