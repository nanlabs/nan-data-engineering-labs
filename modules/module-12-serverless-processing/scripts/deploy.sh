#!/bin/bash
# Deployment script for serverless applications

set -e

ENVIRONMENT=${1:-dev}

echo "🚀 Deploying to $ENVIRONMENT environment"

# Package Lambda functions
echo "📦 Packaging Lambda functions..."
./scripts/package-lambdas.sh

# Initialize Terraform
echo "🔧 Initializing Terraform..."
cd infrastructure
terraform init

# Select workspace
echo "🔀 Selecting workspace: $ENVIRONMENT"
terraform workspace select $ENVIRONMENT || terraform workspace new $ENVIRONMENT

# Plan
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Apply
if [ "$ENVIRONMENT" == "prod" ]; then
    echo "⚠️  Production deployment - manual approval required"
    read -p "Deploy to production? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 1
    fi
fi

echo "🚀 Applying Terraform..."
terraform apply tfplan

# Get outputs
echo "📤 Deployment outputs:"
terraform output

echo "✅ Deployment complete!"

# Run smoke tests
if [ -f "../scripts/smoke-tests.sh" ]; then
    echo "🧪 Running smoke tests..."
    cd ..
    ./scripts/smoke-tests.sh
fi
