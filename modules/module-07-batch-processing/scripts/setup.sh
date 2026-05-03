#!/bin/bash
# Setup script for Module 07: Batch Processing

set -e  # Exit on error

echo "=========================================="
echo "Module 07: Batch Processing - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    echo "ERROR: Python 3.8+ is required"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null
echo "✓ pip upgraded"

# Install requirements
echo ""
echo "Installing dependencies..."
echo "(This may take a few minutes)"
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"

# Verify PySpark installation
echo ""
echo "Verifying PySpark installation..."
if python3 -c 'import pyspark' 2>/dev/null; then
    pyspark_version=$(python3 -c 'import pyspark; print(pyspark.__version__)')
    echo "✓ PySpark $pyspark_version installed"
else
    echo "ERROR: PySpark installation failed"
    exit 1
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/temp
mkdir -p logs
echo "✓ Directories created"

# Generate sample data
echo ""
echo "Do you want to generate sample data? (y/n)"
read -r generate_data

if [ "$generate_data" = "y" ]; then
    echo ""
    echo "Generating sample data..."
    echo "(This may take 5-10 minutes)"

    # Generate users (fast)
    echo "  → Generating users (1M records)..."
    python3 data/scripts/generate_users.py \
        --num-users 1000000 \
        --output-path data/raw/users.parquet

    # Generate products (fast)
    echo "  → Generating products (100K records)..."
    python3 data/scripts/generate_products.py \
        --num-products 100000 \
        --output-path data/raw/products.parquet

    # Generate transactions (slower)
    echo "  → Generating transactions (10M records, partitioned)..."
    python3 data/scripts/generate_transactions.py \
        --total-records 10000000 \
        --days 90 \
        --partition-by date \
        --output-dir data/raw/transactions

    echo "✓ Sample data generated"

    # Show data summary
    echo ""
    echo "Data Summary:"
    echo "-------------"
    du -sh data/raw/* 2>/dev/null | awk '{print "  " $2 ": " $1}'
else
    echo "Skipping data generation"
    echo "You can generate data later with:"
    echo "  python3 data/scripts/generate_transactions.py"
    echo "  python3 data/scripts/generate_users.py"
    echo "  python3 data/scripts/generate_products.py"
fi

# Run validation tests
echo ""
echo "Do you want to run validation tests? (y/n)"
read -r run_tests

if [ "$run_tests" = "y" ]; then
    echo ""
    echo "Running validation tests..."
    pytest validation/ -v --tb=short
fi

echo ""
echo "=========================================="
echo "Setup Complete! ✨"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start with theory: cd theory && cat 01-concepts.md"
echo "  3. Complete exercises: cd exercises/01-batch-basics"
echo "  4. Run tests: pytest validation/ -v"
echo ""
echo "Happy learning! 🚀"
