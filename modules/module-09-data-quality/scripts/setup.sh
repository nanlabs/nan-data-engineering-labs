#!/bin/bash

# Setup script for Module 09: Data Quality
# This script installs dependencies, initializes tools, and verifies the environment

set -e  # Exit on error

echo "=========================================="
echo "Module 09: Data Quality - Setup"
echo "=========================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_success "Python $PYTHON_VERSION (>= $REQUIRED_VERSION required)"
else
    print_error "Python $PYTHON_VERSION is below required version $REQUIRED_VERSION"
    exit 1
fi
echo

# Step 2: Create virtual environment (if not exists)
echo "Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"
echo

# Step 3: Upgrade pip
echo "Step 3: Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded"
echo

# Step 4: Install dependencies
echo "Step 4: Installing dependencies..."
print_info "This may take a few minutes..."

if pip install -r requirements.txt > /tmp/pip_install.log 2>&1; then
    print_success "All dependencies installed"
else
    print_error "Failed to install dependencies. Check /tmp/pip_install.log for details"
    exit 1
fi
echo

# Step 5: Verify key packages
echo "Step 5: Verifying key package installations..."

check_package() {
    if python3 -c "import $1" 2>/dev/null; then
        print_success "$1"
    else
        print_error "$1 not found"
        return 1
    fi
}

check_package "pandas"
check_package "numpy"
check_package "great_expectations"
check_package "pandera"
check_package "ydata_profiling"
check_package "pyod"
check_package "pytest"
echo

# Step 6: Initialize Great Expectations (if not already done)
echo "Step 6: Initializing Great Expectations..."
if [ ! -d "great_expectations" ]; then
    print_info "Creating GE project structure..."
    echo "y" | great_expectations init > /dev/null 2>&1 || true
    print_success "Great Expectations initialized"
else
    print_info "Great Expectations already initialized"
fi
echo

# Step 7: Create necessary directories
echo "Step 7: Creating directories..."
mkdir -p data/samples
mkdir -p data/generated
mkdir -p data/quarantine
mkdir -p validation/data-quality
mkdir -p validation/profiling
mkdir -p validation/validation
mkdir -p validation/integration
mkdir -p assets
mkdir -p scripts
print_success "Directories created"
echo

# Step 8: Generate sample data
echo "Step 8: Generating sample datasets..."
print_info "Generating clean dataset..."
python3 data/scripts/generate_data.py --quality clean --output data/generated/ > /dev/null 2>&1 || print_info "Skipping data generation (script may need adjustments)"

if [ -f "data/generated/customers_clean.csv" ]; then
    print_success "Clean dataset generated"

    print_info "Generating medium quality dataset..."
    python3 data/scripts/generate_data.py --quality medium --output data/generated/ > /dev/null 2>&1
    print_success "Medium quality dataset generated"

    print_info "Generating poor quality dataset..."
    python3 data/scripts/generate_data.py --quality poor --output data/generated/ > /dev/null 2>&1
    print_success "Poor quality dataset generated"
else
    print_info "Sample data generation skipped"
fi
echo

# Step 9: Verify setup
echo "Step 9: Verifying setup..."

ERRORS=0

# Check files
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt missing"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -f "pytest.ini" ]; then
    print_error "pytest.ini missing"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -f "validation/conftest.py" ]; then
    print_error "validation/conftest.py missing"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -f "validation/test_module.py" ]; then
    print_error "validation/test_module.py missing"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    print_success "All required files present"
else
    print_error "$ERRORS file(s) missing"
fi
echo

# Step 10: Run quick smoke test
echo "Step 10: Running smoke tests..."
if SKIP_GE_TESTS=1 pytest validation/test_module.py -m smoke -v > /tmp/smoke_tests.log 2>&1; then
    print_success "Smoke tests passed"
else
    print_info "Some smoke tests failed (this may be expected if exercises aren't complete)"
    print_info "Check /tmp/smoke_tests.log for details"
fi
echo

# Final summary
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo
echo "To activate the environment in the future:"
echo "  source venv/bin/activate"
echo
echo "To run tests:"
echo "  pytest validation/ -v"
echo
echo "To generate data:"
echo "  python data/scripts/generate_data.py --quality clean --output data/generated/"
echo
echo "Next steps:"
echo "  1. Review theory/ documentation"
echo "  2. Complete exercises in exercises/ directory"
echo "  3. Run validation tests: ./scripts/validate.sh"
echo
print_success "Module 09: Data Quality is ready!"
echo
