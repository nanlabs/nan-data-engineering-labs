#!/bin/bash
# Validation script for Module 02

set -e

echo "🧪 Running Module 02 validations..."

# Run pytest
pytest validation/ -v --tb=short

echo "✅ All validations passed!"
