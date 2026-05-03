#!/bin/bash
# Setup script for Module 12

set -e

echo "🚀 Setting up Module 12: Serverless Processing"

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed"
        exit 1
    else
        echo "✅ $1 is installed"
    fi
}

echo "Checking prerequisites..."
check_command python3
check_command terraform
check_command aws

# Install AWS CLI if needed
if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install dev dependencies
echo "Installing dev dependencies..."
pip install pytest pytest-cov moto boto3 aws-xray-sdk

# Configure AWS (if not configured)
if [ ! -f ~/.aws/credentials ]; then
    echo "Configuring AWS CLI..."
    aws configure
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Run tests to verify setup
echo "Running tests..."
pytest validation/ -v

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review exercises in exercises/"
echo "2. Start with exercises/01-first-lambda/"
echo "3. Deploy infrastructure: cd infrastructure && terraform init"
