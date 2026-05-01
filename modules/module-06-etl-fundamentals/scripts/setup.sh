#!/bin/bash
# Setup script for module-06-etl-fundamentals

set -e  # Exit on error

echo "🚀 Setting up Module 06: ETL Fundamentals"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODULE_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$MODULE_DIR"

echo ""
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✓ Dependencies installed"
else
    echo "⚠️  requirements.txt not found"
fi

echo ""
echo "🏭 Generating test data..."
if [ -d "data/scripts" ]; then
    cd data/scripts
    python generate_all.py
    cd "$MODULE_DIR"
    echo "✓ Test data generated"
else
    echo "⚠️  Data generation scripts not found"
fi

echo ""
echo "🧪 Running validation tests..."
pytest validation/ -v --tb=short || echo "⚠️  Some tests failed"

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Read theory: theory/01-concepts.md"
echo "  2. Start exercises: exercises/01-extract-basics/"
echo "  3. Run tests: pytest validation/ -v"
echo ""
echo "📖 See README.md for full documentation"
