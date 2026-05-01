#!/bin/bash
# Setup script for Module 02

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up Module 02: Storage Basics${NC}"

# Check Python
python3 --version || { echo "Python 3 required"; exit 1; }

# Install dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Generate sample data
echo -e "${BLUE}Generating sample data files...${NC}"
cd data/sample
bash generate_users.sh
cd ../..

# Start infrastructure
echo -e "${BLUE}Starting LocalStack infrastructure...${NC}"
cd infrastructure
./init.sh
cd ..

echo -e "${GREEN}✅ Module 02 setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Read theory/concepts.md"
echo "  2. Start with exercises/01-data-lake-design/"
echo "  3. Run tests: pytest validation/ -v"
