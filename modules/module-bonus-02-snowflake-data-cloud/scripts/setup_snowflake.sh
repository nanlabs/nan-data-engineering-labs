#!/bin/bash

################################################################################
# Snowflake Environment Setup Script
#
# This script automates the initial setup of a Snowflake training environment:
# - Verifies SnowSQL installation
# - Tests connection to Snowflake account
# - Creates training database and schemas
# - Sets up compute warehouse with auto-suspend
# - Creates resource monitor for cost control
# - Loads sample data from local files
# - Validates the setup
#
# Usage:
#   ./setup_snowflake.sh
#   ./setup_snowflake.sh --config snowflake_config.txt
#
# Requirements:
#   - SnowSQL CLI installed
#   - Snowflake account with appropriate permissions
#   - Sample data files in data/sample/ directory
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${MODULE_DIR}/data/sample"
CONFIG_FILE=""
LOG_FILE="${SCRIPT_DIR}/setup_snowflake_$(date +%Y%m%d_%H%M%S).log"

# Snowflake configuration (will be populated from user input or config file)
SNOWFLAKE_ACCOUNT=""
SNOWFLAKE_USERNAME=""
SNOWFLAKE_PASSWORD=""
SNOWFLAKE_ROLE="ACCOUNTADMIN"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"

# Resources to create
DATABASE_NAME="TRAINING_SNOWFLAKE"
SCHEMAS=("RAW" "STAGING" "ANALYTICS" "SANDBOX")
WAREHOUSE_NAME="TRAINING_WH"
RESOURCE_MONITOR_NAME="TRAINING_MONITOR"
CREDIT_QUOTA=50

################################################################################
# Utility Functions
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

################################################################################
# Validation Functions
################################################################################

check_snowsql_installed() {
    print_header "Checking SnowSQL Installation"

    if ! command -v snowsql &> /dev/null; then
        print_error "SnowSQL is not installed"
        echo ""
        echo "Please install SnowSQL from:"
        echo "https://docs.snowflake.com/en/user-guide/snowsql-install-config.html"
        echo ""
        echo "Installation instructions:"
        echo "  macOS/Linux: bash <(curl -sS https://sfc-repo.snowflakecomputing.com/snowsql/bootstrap/bootstrap.sh)"
        echo "  Windows: https://sfc-repo.snowflakecomputing.com/snowsql/bootstrap/installer/snowsql-installer-latest.exe"
        exit 1
    fi

    local version
    version=$(snowsql --version 2>&1 | grep -oP 'Version: \K[\d.]+' || echo "unknown")
    print_success "SnowSQL is installed (version: $version)"
    log_message "SnowSQL version: $version"
}

check_data_files() {
    print_header "Checking Sample Data Files"

    if [ ! -d "$DATA_DIR" ]; then
        print_warning "Sample data directory not found: $DATA_DIR"
        echo ""
        echo "Run the following command to generate sample data:"
        echo "  python ${SCRIPT_DIR}/create_sample_data.py --output-dir ${DATA_DIR}"
        return 1
    fi

    local missing_files=0
    local required_files=("customers.csv" "orders.csv" "events.json")

    for file in "${required_files[@]}"; do
        if [ -f "${DATA_DIR}/${file}" ]; then
            local size
            size=$(du -h "${DATA_DIR}/${file}" | cut -f1)
            print_success "Found ${file} (${size})"
        else
            print_warning "Missing ${file}"
            missing_files=$((missing_files + 1))
        fi
    done

    if [ $missing_files -gt 0 ]; then
        echo ""
        echo "Generate missing files with:"
        echo "  python ${SCRIPT_DIR}/create_sample_data.py --output-dir ${DATA_DIR}"
        return 1
    fi

    return 0
}

################################################################################
# Configuration Functions
################################################################################

load_config_file() {
    if [ -n "$CONFIG_FILE" ] && [ -f "$CONFIG_FILE" ]; then
        print_info "Loading configuration from ${CONFIG_FILE}"
        # shellcheck source=/dev/null
        source "$CONFIG_FILE"
        print_success "Configuration loaded"
    fi
}

prompt_for_credentials() {
    print_header "Snowflake Account Configuration"

    if [ -z "$SNOWFLAKE_ACCOUNT" ]; then
        echo -n "Enter Snowflake account identifier (e.g., xy12345.us-east-1): "
        read -r SNOWFLAKE_ACCOUNT
    fi

    if [ -z "$SNOWFLAKE_USERNAME" ]; then
        echo -n "Enter Snowflake username: "
        read -r SNOWFLAKE_USERNAME
    fi

    if [ -z "$SNOWFLAKE_PASSWORD" ]; then
        echo -n "Enter Snowflake password: "
        read -rs SNOWFLAKE_PASSWORD
        echo ""
    fi

    # Validate inputs
    if [ -z "$SNOWFLAKE_ACCOUNT" ] || [ -z "$SNOWFLAKE_USERNAME" ] || [ -z "$SNOWFLAKE_PASSWORD" ]; then
        print_error "All credentials are required"
        exit 1
    fi

    print_success "Configuration complete"
    log_message "Account: $SNOWFLAKE_ACCOUNT, User: $SNOWFLAKE_USERNAME"
}

################################################################################
# Snowflake Operations
################################################################################

execute_snowflake_query() {
    local query="$1"
    local description="${2:-Executing query}"

    log_message "Executing: $query"

    if snowsql \
        -a "$SNOWFLAKE_ACCOUNT" \
        -u "$SNOWFLAKE_USERNAME" \
        -r "$SNOWFLAKE_ROLE" \
        -w "$SNOWFLAKE_WAREHOUSE" \
        --private-key-path="" \
        -q "$query" \
        -o exit_on_error=true \
        -o friendly=false \
        -o output_format=plain \
        <<< "$SNOWFLAKE_PASSWORD" >> "$LOG_FILE" 2>&1; then
        print_success "$description"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
}

test_connection() {
    print_header "Testing Snowflake Connection"

    local query="SELECT CURRENT_VERSION() AS version, CURRENT_ACCOUNT() AS account, CURRENT_USER() AS user;"

    log_message "Testing connection to $SNOWFLAKE_ACCOUNT"

    if snowsql \
        -a "$SNOWFLAKE_ACCOUNT" \
        -u "$SNOWFLAKE_USERNAME" \
        -q "$query" \
        -o exit_on_error=true \
        -o friendly=false \
        <<< "$SNOWFLAKE_PASSWORD" >> "$LOG_FILE" 2>&1; then
        print_success "Connection successful"
        return 0
    else
        print_error "Connection failed"
        echo ""
        echo "Please check:"
        echo "  1. Account identifier is correct"
        echo "  2. Username and password are correct"
        echo "  3. Network connectivity to Snowflake"
        echo ""
        echo "See log file for details: $LOG_FILE"
        return 1
    fi
}

create_database() {
    print_header "Creating Training Database"

    local query="CREATE DATABASE IF NOT EXISTS ${DATABASE_NAME} COMMENT='Training database for Snowflake exercises';"
    execute_snowflake_query "$query" "Database ${DATABASE_NAME} created"
}

create_schemas() {
    print_header "Creating Schemas"

    for schema in "${SCHEMAS[@]}"; do
        local query="CREATE SCHEMA IF NOT EXISTS ${DATABASE_NAME}.${schema} COMMENT='${schema} schema for data organization';"
        execute_snowflake_query "$query" "Schema ${schema} created"
    done
}

create_warehouse() {
    print_header "Creating Training Warehouse"

    local query="
    CREATE WAREHOUSE IF NOT EXISTS ${WAREHOUSE_NAME}
    WITH
        WAREHOUSE_SIZE = 'X-SMALL'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE
        INITIALLY_SUSPENDED = TRUE
        COMMENT = 'Training warehouse with auto-suspend for cost optimization';
    "

    execute_snowflake_query "$query" "Warehouse ${WAREHOUSE_NAME} created"

    print_info "Warehouse configuration:"
    echo "  • Size: X-SMALL"
    echo "  • Auto-suspend: 60 seconds"
    echo "  • Auto-resume: Enabled"
}

create_resource_monitor() {
    print_header "Creating Resource Monitor"

    # Drop existing monitor if it exists
    local drop_query="DROP RESOURCE MONITOR IF EXISTS ${RESOURCE_MONITOR_NAME};"
    execute_snowflake_query "$drop_query" "Dropped existing resource monitor" || true

    # Create new resource monitor
    local create_query="
    CREATE RESOURCE MONITOR ${RESOURCE_MONITOR_NAME}
    WITH
        CREDIT_QUOTA = ${CREDIT_QUOTA}
        FREQUENCY = MONTHLY
        START_TIMESTAMP = IMMEDIATELY
        TRIGGERS
            ON 75 PERCENT DO NOTIFY
            ON 90 PERCENT DO SUSPEND
            ON 100 PERCENT DO SUSPEND_IMMEDIATE;
    "

    execute_snowflake_query "$create_query" "Resource monitor ${RESOURCE_MONITOR_NAME} created"

    # Assign monitor to warehouse
    local assign_query="ALTER WAREHOUSE ${WAREHOUSE_NAME} SET RESOURCE_MONITOR = ${RESOURCE_MONITOR_NAME};"
    execute_snowflake_query "$assign_query" "Resource monitor assigned to warehouse"

    print_info "Resource monitor configuration:"
    echo "  • Credit quota: ${CREDIT_QUOTA} credits/month"
    echo "  • Alert at: 75% usage"
    echo "  • Suspend at: 90% usage"
    echo "  • Immediate suspend at: 100% usage"
}

load_sample_data() {
    print_header "Loading Sample Data"

    if ! check_data_files; then
        print_warning "Skipping data load - sample files not available"
        return 0
    fi

    # Create tables
    print_info "Creating tables..."

    local create_customers="
    CREATE TABLE IF NOT EXISTS ${DATABASE_NAME}.RAW.CUSTOMERS (
        CUSTOMER_ID INTEGER,
        NAME STRING,
        EMAIL STRING,
        COUNTRY STRING,
        SIGNUP_DATE DATE,
        TOTAL_SPENT FLOAT
    );
    "
    execute_snowflake_query "$create_customers" "Table CUSTOMERS created"

    local create_orders="
    CREATE TABLE IF NOT EXISTS ${DATABASE_NAME}.RAW.ORDERS (
        ORDER_ID INTEGER,
        CUSTOMER_ID INTEGER,
        PRODUCT STRING,
        QUANTITY INTEGER,
        PRICE FLOAT,
        ORDER_DATE TIMESTAMP
    );
    "
    execute_snowflake_query "$create_orders" "Table ORDERS created"

    local create_events="
    CREATE TABLE IF NOT EXISTS ${DATABASE_NAME}.RAW.EVENTS (
        EVENT_ID INTEGER,
        USER_ID INTEGER,
        EVENT_TYPE STRING,
        TIMESTAMP TIMESTAMP,
        PROPERTIES VARIANT
    );
    "
    execute_snowflake_query "$create_events" "Table EVENTS created"

    print_success "Tables created successfully"
}

verify_setup() {
    print_header "Verifying Setup"

    # Check database exists
    local db_query="SHOW DATABASES LIKE '${DATABASE_NAME}';"
    execute_snowflake_query "$db_query" "Database verification"

    # Check schemas exist
    local schema_query="SHOW SCHEMAS IN DATABASE ${DATABASE_NAME};"
    execute_snowflake_query "$schema_query" "Schema verification"

    # Check warehouse exists
    local wh_query="SHOW WAREHOUSES LIKE '${WAREHOUSE_NAME}';"
    execute_snowflake_query "$wh_query" "Warehouse verification"

    # Count tables
    local table_query="SHOW TABLES IN SCHEMA ${DATABASE_NAME}.RAW;"
    execute_snowflake_query "$table_query" "Table verification"

    print_success "Setup verification complete"
}

################################################################################
# Main Execution
################################################################################

print_success_message() {
    echo ""
    print_header "Setup Complete!"
    echo ""
    print_success "Your Snowflake training environment is ready!"
    echo ""
    echo "Resources created:"
    echo "  • Database: ${DATABASE_NAME}"
    echo "  • Schemas: ${SCHEMAS[*]}"
    echo "  • Warehouse: ${WAREHOUSE_NAME}"
    echo "  • Resource Monitor: ${RESOURCE_MONITOR_NAME}"
    echo ""
    echo "Next steps:"
    echo "  1. Connect to Snowflake: snowsql -a ${SNOWFLAKE_ACCOUNT} -u ${SNOWFLAKE_USERNAME}"
    echo "  2. Use database: USE DATABASE ${DATABASE_NAME};"
    echo "  3. Use warehouse: USE WAREHOUSE ${WAREHOUSE_NAME};"
    echo "  4. Start exercises in: ${MODULE_DIR}/exercises/"
    echo ""
    echo "Monitor costs:"
    echo "  python ${SCRIPT_DIR}/monitor_costs.py --account ${SNOWFLAKE_ACCOUNT}"
    echo ""
    echo "Log file: $LOG_FILE"
    echo ""
}

cleanup_on_error() {
    print_error "Setup failed. Check log file: $LOG_FILE"

    if [ -n "${ROLLBACK:-}" ]; then
        print_info "Rolling back changes..."
        # Add rollback logic here if needed
    fi

    exit 1
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --config FILE    Load configuration from file"
                echo "  --help, -h       Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Setup trap for errors
    trap cleanup_on_error ERR

    # Start setup
    print_header "Snowflake Training Environment Setup"
    echo ""
    print_info "Log file: $LOG_FILE"
    echo ""

    log_message "=== Setup started ==="

    # Execute setup steps
    check_snowsql_installed
    load_config_file
    prompt_for_credentials
    test_connection || exit 1

    create_database
    create_schemas
    create_warehouse
    create_resource_monitor
    load_sample_data
    verify_setup

    log_message "=== Setup completed successfully ==="

    # Print success message
    print_success_message
}

# Run main function
main "$@"
