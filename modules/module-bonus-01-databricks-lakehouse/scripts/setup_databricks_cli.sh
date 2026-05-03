#!/bin/bash
# Setup script for Databricks CLI
# This script installs and configures the Databricks CLI for automation

set -e  # Exit on error

echo "=============================================="
echo "Databricks CLI Setup"
echo "=============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ ERROR: pip3 is not installed"
    echo "Install with: sudo apt install python3-pip (Ubuntu/Debian)"
    exit 1
fi

echo "✅ pip found: $(pip3 --version)"
echo ""

# Install Databricks CLI
echo "📦 Installing Databricks CLI..."
pip3 install --upgrade databricks-cli

# Verify installation
if ! command -v databricks &> /dev/null; then
    echo "❌ ERROR: Databricks CLI installation failed"
    exit 1
fi

echo "✅ Databricks CLI installed: $(databricks --version)"
echo ""

# Configure CLI
echo "=============================================="
echo "Databricks CLI Configuration"
echo "=============================================="
echo ""
echo "You need:"
echo "  1. Databricks workspace URL"
echo "  2. Personal access token"
echo ""
echo "To generate a token:"
echo "  1. Go to your Databricks workspace"
echo "  2. Click User Settings (top-right)"
echo "  3. Click 'Access Tokens' tab"
echo "  4. Click 'Generate New Token'"
echo "  5. Copy the token (you'll only see it once!)"
echo ""
read -p "Press Enter to continue with configuration..."
echo ""

# Run configuration
databricks configure --token

# Test connection
echo ""
echo "=============================================="
echo "Testing Connection"
echo "=============================================="
echo ""

if databricks workspace ls / &> /dev/null; then
    echo "✅ Successfully connected to Databricks!"
    echo ""
    echo "Common commands:"
    echo "  databricks workspace ls /                    # List workspace files"
    echo "  databricks clusters list                     # List clusters"
    echo "  databricks fs ls dbfs:/                      # List DBFS files"
    echo "  databricks jobs list                         # List jobs"
    echo ""
    echo "Documentation: https://docs.databricks.com/dev-tools/cli/"
else
    echo "❌ ERROR: Failed to connect to Databricks"
    echo "Please check your configuration and try again"
    echo ""
    echo "Reconfigure with: databricks configure --token"
    exit 1
fi

echo "✅ Setup complete!"
