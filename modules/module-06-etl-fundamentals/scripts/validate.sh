#!/bin/bash
# Validate module completion

set -e

echo "🔍 Validating Module 06: ETL Fundamentals"
echo "=========================================="

MODULE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$MODULE_DIR"

# Check structure
echo ""
echo "📁 Checking module structure..."
required_dirs=("theory" "exercises" "data" "validation" "scripts" "assets")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ❌ $dir/ missing"
        exit 1
    fi
done

# Check theory files
echo ""
echo "📚 Checking theory files..."
theory_files=("01-concepts.md" "02-patterns.md" "03-resources.md")
for file in "${theory_files[@]}"; do
    if [ -f "theory/$file" ]; then
        echo "  ✓ theory/$file"
    else
        echo "  ❌ theory/$file missing"
        exit 1
    fi
done

# Check exercises
echo ""
echo "🏋️  Checking exercises..."
exercises=("01-extract-basics" "02-transform-basics" "03-load-basics"
           "04-full-pipeline" "05-error-handling" "06-data-quality")
for ex in "${exercises[@]}"; do
    if [ -d "exercises/$ex" ]; then
        echo "  ✓ exercises/$ex/"
    else
        echo "  ❌ exercises/$ex/ missing"
        exit 1
    fi
done

# Check data generation
echo ""
echo "🏭 Checking test data..."
if [ -f "data/raw/users_clean.csv" ] && [ -f "data/raw/transactions_clean.csv" ]; then
    echo "  ✓ Test data exists"
else
    echo "  ⚠️  Test data not generated. Run: cd data/scripts && python generate_all.py"
fi

# Run tests
echo ""
echo "🧪 Running validation tests..."
if pytest validation/ -v --tb=short; then
    echo "  ✓ All tests passed"
else
    echo "  ❌ Some tests failed"
    exit 1
fi

# Check file counts
echo ""
echo "📊 Module Statistics:"
echo "  Theory files: $(find theory -name '*.md' | wc -l)"
echo "  Exercise READMEs: $(find exercises -name 'README.md' | wc -l)"
echo "  Python files: $(find exercises -name '*.py' | wc -l)"
echo "  Test files: $(find . -name 'test_*.py' | wc -l)"
echo "  Data schemas: $(find data/schemas -name '*.json' 2>/dev/null | wc -l || echo 0)"

echo ""
echo "=========================================="
echo "✅ Module validation complete!"
echo ""
echo "🎓 You can now proceed to the next module"
