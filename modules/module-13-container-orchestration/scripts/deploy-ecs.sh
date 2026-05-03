#!/bin/bash
# Deploy ECS infrastructure for Module 13
# Usage: ./deploy-ecs.sh [cluster-name]

set -e

CLUSTER_NAME=${1:-"data-engineering-cluster"}
AWS_REGION=${AWS_REGION:-"us-east-1"}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================"
echo "ECS Deployment Script"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $AWS_REGION"
echo "======================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform not found${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $AWS_ACCOUNT_ID"
echo ""

# Step 1: Initialize Terraform
echo -e "${GREEN}[1/5] Initializing Terraform...${NC}"
cd terraform
terraform init
echo ""

# Step 2: Plan infrastructure
echo -e "${GREEN}[2/5] Planning infrastructure...${NC}"
terraform plan \
    -var="cluster_name=$CLUSTER_NAME" \
    -var="aws_region=$AWS_REGION" \
    -out=tfplan
echo ""

# Step 3: Apply infrastructure
echo -e "${YELLOW}Ready to create infrastructure. Continue? (yes/no)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 0
fi

echo -e "${GREEN}[3/5] Creating infrastructure...${NC}"
terraform apply tfplan
rm tfplan
echo ""

# Get outputs
ECS_CLUSTER_ARN=$(terraform output -raw cluster_arn)
ECR_URL=$(terraform output -raw ecr_repository_url || echo "")

echo -e "${GREEN}✓ Infrastructure created${NC}"
echo "  ECS Cluster: $ECS_CLUSTER_ARN"
[ -n "$ECR_URL" ] && echo "  ECR Repository: $ECR_URL"
echo ""

# Step 4: Build and push Docker images (if ECR exists)
if [ -n "$ECR_URL" ]; then
    echo -e "${GREEN}[4/5] Building and pushing Docker images...${NC}"

    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

    # Build sample API image (if exists)
    if [ -f "../exercises/01-docker-basics/Dockerfile" ]; then
        echo "Building data-api image..."
        docker build -t data-api:latest ../exercises/01-docker-basics/
        docker tag data-api:latest $ECR_URL:latest
        docker push $ECR_URL:latest
        echo -e "${GREEN}✓ Image pushed to ECR${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}[4/5] Skipping Docker build (no ECR repository)${NC}"
    echo ""
fi

# Step 5: Verify deployment
echo -e "${GREEN}[5/5] Verifying deployment...${NC}"

# Check ECS cluster
CLUSTER_STATUS=$(aws ecs describe-clusters \
    --clusters $CLUSTER_NAME \
    --region $AWS_REGION \
    --query 'clusters[0].status' \
    --output text)

if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
    echo -e "${GREEN}✓ ECS Cluster is ACTIVE${NC}"
else
    echo -e "${RED}✗ ECS Cluster status: $CLUSTER_STATUS${NC}"
fi

# List running services
echo ""
echo "Running ECS services:"
aws ecs list-services \
    --cluster $CLUSTER_NAME \
    --region $AWS_REGION \
    --query 'serviceArns[*]' \
    --output table

echo ""
echo -e "${GREEN}======================================"
echo "✓ ECS Deployment Complete!"
echo "======================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Deploy services: terraform apply -target=module.ecs_service"
echo "  2. Check CloudWatch logs: aws logs tail /ecs/$CLUSTER_NAME --follow"
echo "  3. View in console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo ""
echo "To destroy: cd terraform && terraform destroy"
echo ""
