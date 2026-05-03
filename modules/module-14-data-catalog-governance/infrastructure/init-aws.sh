#!/bin/bash

# LocalStack Initialization Script
# This script runs automatically when LocalStack is ready

echo "========================================="
echo "Module 14: LocalStack Initialization"
echo "========================================="

# Wait for services to be fully ready
sleep 5

# Configure AWS CLI to use LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

echo "LocalStack initialization complete!"
echo "Ready to run: bash scripts/setup.sh"
