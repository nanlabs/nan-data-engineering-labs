#!/bin/bash

###############################################################################
# Module 17: Cost Optimization - Setup Script
#
# This script sets up the local development environment for the cost
# optimization module exercises.
#
# What it does:
# - Checks prerequisites (Python, AWS CLI, Docker, jq)
# - Creates Python virtual environment
# - Installs Python dependencies
# - Verifies AWS credentials and permissions
# - Starts Docker containers (LocalStack, Jupyter, PostgreSQL)
# - Initializes sample data
# - Validates setup
#
# Usage: ./scripts/setup.sh
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

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing=0

    # Python 3.9+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION"
    else
        log_error "Python 3.9+ required"
        missing=1
    fi

    # AWS CLI
    if command -v aws &> /dev/null; then
        AWS_VERSION=$(aws --version | cut -d' ' -f1 | cut -d'/' -f2)
        log_success "AWS CLI $AWS_VERSION"
    else
        log_error "AWS CLI required: https://aws.amazon.com/cli/"
        missing=1
    fi

    # Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_success "Docker $DOCKER_VERSION"
    else
        log_error "Docker required: https://docs.docker.com/get-docker/"
        missing=1
    fi

    # Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        log_success "Docker Compose available"
    else
        log_warning "Docker Compose not found (may need docker compose instead)"
    fi

    # jq (optional but recommended)
    if command -v jq &> /dev/null; then
        log_success "jq available"
    else
        log_warning "jq not found (install for better JSON parsing)"
    fi

    # bc (for calculations)
    if command -v bc &> /dev/null; then
        log_success "bc available"
    else
        log_warning "bc not found (install: apt-get install bc / brew install bc)"
    fi

    if [ $missing -eq 1 ]; then
        log_error "Please install missing prerequisites"
        exit 1
    fi

    echo ""
}

# Check AWS credentials
check_aws_credentials() {
    log_info "Checking AWS credentials..."

    if aws sts get-caller-identity &>/dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
        log_success "AWS credentials configured"
        echo "   Account: $ACCOUNT_ID"
        echo "   Identity: $AWS_USER"
    else
        log_error "AWS credentials not configured"
        log_info "Run: aws configure"
        exit 1
    fi

    # Check Cost Explorer permissions
    log_info "Checking Cost Explorer permissions..."
    if aws ce get-cost-and-usage \
        --time-period Start=2024-01-01,End=2024-01-02 \
        --granularity MONTHLY \
        --metrics UnblendedCost \
        --region us-east-1 &>/dev/null; then
        log_success "Cost Explorer access verified"
    else
        log_warning "Cost Explorer may not be enabled or you lack permissions"
        log_info "Enable at: https://console.aws.amazon.com/cost-management/home#/cost-explorer"
    fi

    echo ""
}

# Create Python virtual environment
setup_python_env() {
    log_info "Setting up Python environment..."

    cd "$MODULE_DIR"

    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Created virtual environment"
    else
        log_success "Virtual environment exists"
    fi

    # Activate venv
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip setuptools wheel &>/dev/null
    log_success "Upgraded pip"

    # Install dependencies
    log_info "Installing Python dependencies (this may take 2-3 minutes)..."
    pip install -r requirements.txt &>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Installed Python packages"
    else
        log_error "Failed to install dependencies"
        exit 1
    fi

    echo ""
}

# Start Docker containers
start_docker() {
    log_info "Starting Docker containers..."

    cd "$MODULE_DIR/infrastructure"

    # Check if containers are already running
    if docker ps | grep -q cost-optimization-localstack; then
        log_success "Docker containers already running"
        return
    fi

    # Start containers
    docker-compose up -d

    if [ $? -eq 0 ]; then
        log_success "Docker containers started"

        # Wait for health checks
        log_info "Waiting for services to be healthy (30 seconds)..."
        sleep 30

        # Check LocalStack
        if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then
            log_success "LocalStack is healthy"
        else
            log_warning "LocalStack may not be fully ready yet"
        fi

        # Check PostgreSQL
        if docker exec cost-optimization-postgres pg_isready -U cost_optimizer &>/dev/null; then
            log_success "PostgreSQL is healthy"
        else
            log_warning "PostgreSQL may not be fully ready yet"
        fi

        # Check Jupyter
        if curl -s http://localhost:8888 &>/dev/null; then
            log_success "Jupyter is healthy"
            echo "   Access: http://localhost:8888 (no token required)"
        else
            log_warning "Jupyter may not be fully ready yet"
        fi
    else
        log_error "Failed to start Docker containers"
        exit 1
    fi

    echo ""
}

# Initialize sample data
init_sample_data() {
    log_info "Initializing sample data..."

    cd "$MODULE_DIR"

    # Create directories
    mkdir -p data/sample
    mkdir -p data/reports
    mkdir -p data/localstack

    # Check if sample data exists
    if [ -f "data/sample/cost-usage-report.csv" ]; then
        log_success "Sample data already exists"
    else
        log_info "Sample data will be created in next step"
    fi

    echo ""
}

# Run AWS initialization (if credentials available)
run_aws_init() {
    log_info "Running AWS infrastructure initialization..."

    cd "$MODULE_DIR"

    if [ -f "infrastructure/init-aws.sh" ]; then
        chmod +x infrastructure/init-aws.sh

        read -p "Initialize AWS services? (Cost Explorer, Budgets, etc.) [y/N]: " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash infrastructure/init-aws.sh
        else
            log_info "Skipping AWS initialization (you can run it later)"
        fi
    else
        log_warning "init-aws.sh not found"
    fi

    echo ""
}

# Create useful aliases
create_aliases() {
    log_info "Creating command aliases..."

    cd "$MODULE_DIR"

    cat > venv/bin/cost-aliases.sh <<'EOF'
# Cost Optimization Aliases
alias cost-report='make cost-report'
alias cost-by-service='make cost-by-service'
alias cost-by-team='make cost-by-team'
alias savings='make savings-recommendations'
alias waste='make waste-report'
alias anomalies='make anomalies'

# Exercise shortcuts
alias ex01='make ex01'
alias ex02='make ex02'
alias ex03='make ex03'
alias ex04='make ex04'
alias ex05='make ex05'
alias ex06='make ex06'

echo "💰 Cost optimization aliases loaded"
echo "   cost-report, cost-by-service, savings, waste, anomalies"
echo "   ex01-ex06 for exercises"
EOF

    log_success "Created command aliases"
    log_info "Activate with: source venv/bin/cost-aliases.sh"

    echo ""
}

# Print next steps
print_next_steps() {
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            Setup Complete!                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "📦 Environment Ready:"
    echo "   ✓ Python venv with dependencies"
    echo "   ✓ Docker containers running (LocalStack, PostgreSQL, Jupyter)"
    echo "   ✓ AWS services configured"
    echo ""
    echo "🚀 Quick Start:"
    echo "   1. Activate environment:"
    echo "      source venv/bin/activate"
    echo ""
    echo "   2. Load aliases (optional):"
    echo "      source venv/bin/cost-aliases.sh"
    echo ""
    echo "   3. Validate setup:"
    echo "      make validate"
    echo ""
    echo "   4. Start with Exercise 01:"
    echo "      cd exercises/01-cost-analysis"
    echo "      jupyter notebook  # or follow README.md"
    echo ""
    echo "🔗 Access Points:"
    echo "   • Jupyter: http://localhost:8888"
    echo "   • LocalStack: http://localhost:4566"
    echo "   • PostgreSQL: localhost:5432 (user: cost_optimizer, pass: cost_optimizer)"
    echo "   • Grafana (optional): http://localhost:3000 (admin/admin)"
    echo ""
    echo "📚 Available Commands (with aliases):"
    echo "   • make cost-report        # Generate monthly cost report"
    echo "   • make cost-by-service    # Cost breakdown by service"
    echo "   • make savings            # Get RI/SP recommendations"
    echo "   • make waste              # Find idle resources"
    echo "   • make anomalies          # Cost anomaly detection"
    echo "   • make dashboard          # Generate cost dashboard"
    echo "   • make ex01...ex06        # Run exercises"
    echo ""
    echo "⚠️  Remember:"
    echo "   • Cost Explorer needs 24 hours to populate data"
    echo "   • First CUR report available in 24 hours"
    echo "   • Cost allocation tags visible after 24 hours"
    echo ""
    echo "📖 Documentation:"
    echo "   • Module README: README.md"
    echo "   • Theory: theory/concepts.md"
    echo "   • Exercises: exercises/*/README.md"
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   Module 17: Cloud Cost Optimization - Setup          ${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""

    check_prerequisites
    check_aws_credentials
    setup_python_env
    start_docker
    init_sample_data
    create_aliases
    run_aws_init
    print_next_steps
}

main "$@"
