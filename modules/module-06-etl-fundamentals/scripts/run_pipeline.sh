#!/bin/bash
# Run a complete ETL pipeline demonstration

echo "🚀 Running ETL Pipeline Demo"
echo "========================================"

MODULE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$MODULE_DIR"

# Check if data exists
if [ ! -f "data/raw/users_clean.csv" ]; then
    echo "⚠️  Test data not found. Generating..."
    cd data/scripts
    python generate_all.py
    cd "$MODULE_DIR"
fi

echo ""
echo "📊 Step 1: Extract"
echo "-------------------"
python exercises/01-extract-basics/solution_csv.py

echo ""
echo "🔄 Step 2: Transform"
echo "-------------------"
python exercises/02-transform-basics/solution_cleaning.py

echo ""
echo "💾 Step 3: Load"
echo "-------------------"
python exercises/03-load-basics/solution_file_writers.py

echo ""
echo "🎯 Step 4: Full Pipeline"
echo "------------------------"
cd exercises/04-full-pipeline
python pipeline.py
cd "$MODULE_DIR"

echo ""
echo "========================================"
echo "✅ Pipeline demo complete!"
echo ""
echo "📁 Output files created in:"
echo "  - data/processed/"
echo "  - data/output/"
