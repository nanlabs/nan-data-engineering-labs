#!/bin/bash
# Setup script for Module 13 - Container Orchestration
# Installs Docker, AWS CLI, kubectl, eksctl, Terraform, Helm

set -e

echo "======================================"
echo "Module 13: Container Orchestration"
echo "Environment Setup Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${YELLOW}Warning: This script is optimized for Linux${NC}"
fi

# Update system
echo -e "${GREEN}[1/7] Updating system packages...${NC}"
sudo apt-get update -y

# Install Docker
echo -e "${GREEN}[2/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${YELLOW}✓ Docker already installed ($(docker --version))${NC}"
fi

# Install Docker Compose
echo -e "${GREEN}[3/7] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${YELLOW}✓ Docker Compose already installed ($(docker-compose --version))${NC}"
fi

# Install AWS CLI
echo -e "${GREEN}[4/7] Installing AWS CLI v2...${NC}"
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    echo -e "${GREEN}✓ AWS CLI installed${NC}"
else
    echo -e "${YELLOW}✓ AWS CLI already installed ($(aws --version))${NC}"
fi

# Install kubectl
echo -e "${GREEN}[5/7] Installing kubectl...${NC}"
if ! command -v kubectl &> /dev/null; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
    echo -e "${GREEN}✓ kubectl installed${NC}"
else
    echo -e "${YELLOW}✓ kubectl already installed ($(kubectl version --client --short 2>/dev/null || echo 'installed'))${NC}"
fi

# Install eksctl
echo -e "${GREEN}[6/7] Installing eksctl...${NC}"
if ! command -v eksctl &> /dev/null; then
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
    sudo mv /tmp/eksctl /usr/local/bin
    echo -e "${GREEN}✓ eksctl installed${NC}"
else
    echo -e "${YELLOW}✓ eksctl already installed ($(eksctl version))${NC}"
fi

# Install Terraform
echo -e "${GREEN}[7/7] Installing Terraform...${NC}"
if ! command -v terraform &> /dev/null; then
    wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt-get update && sudo apt-get install terraform -y
    echo -e "${GREEN}✓ Terraform installed${NC}"
else
    echo -e "${YELLOW}✓ Terraform already installed ($(terraform version | head -n1))${NC}"
fi

# Install Helm
echo -e "${GREEN}[Bonus] Installing Helm...${NC}"
if ! command -v helm &> /dev/null; then
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    echo -e "${GREEN}✓ Helm installed${NC}"
else
    echo -e "${YELLOW}✓ Helm already installed ($(helm version --short))${NC}"
fi

# Verify installations
echo ""
echo -e "${GREEN}======================================"
echo "✓ Setup Complete!"
echo "======================================${NC}"
echo ""
echo "Installed tools:"
echo "  • Docker: $(docker --version)"
echo "  • Docker Compose: $(docker-compose --version)"
echo "  • AWS CLI: $(aws --version)"
echo "  • kubectl: $(kubectl version --client --short 2>/dev/null || echo 'installed')"
echo "  • eksctl: $(eksctl version)"
echo "  • Terraform: $(terraform version | head -n1)"
echo "  • Helm: $(helm version --short)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Configure AWS credentials: aws configure"
echo "  2. Logout and login again for Docker group changes"
echo "  3. Start with Exercise 01: Docker Basics"
echo ""
