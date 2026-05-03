#!/bin/bash
# Cleanup script for Module 13
# Destroys all AWS resources created during exercises
# Usage: ./cleanup.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}======================================"
echo "⚠️  CLEANUP SCRIPT"
echo "This will DESTROY all resources!"
echo "======================================${NC}"
echo ""

# Confirm
echo -e "${YELLOW}Are you sure you want to delete all resources? (type 'yes' to confirm)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${GREEN}Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${RED}Starting cleanup...${NC}"
echo ""

# Step 1: Delete EKS workloads
echo -e "${YELLOW}[1/5] Deleting EKS workloads...${NC}"
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
    echo "Deleting all namespaces..."
    kubectl delete namespace data-pipeline spark-jobs monitoring --ignore-not-found=true --wait=false

    # Wait a bit for LoadBalancers to be deleted
    echo "Waiting for LoadBalancers to terminate (30s)..."
    sleep 30

    echo -e "${GREEN}✓ EKS workloads deleted${NC}"
else
    echo -e "${YELLOW}  Skipping (kubectl not configured)${NC}"
fi
echo ""

# Step 2: Delete ECS services and tasks
echo -e "${YELLOW}[2/5] Deleting ECS services and tasks...${NC}"
if command -v aws &> /dev/null; then
    AWS_REGION=${AWS_REGION:-"us-east-1"}

    # List clusters
    CLUSTERS=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[*]' --output text 2>/dev/null || echo "")

    if [ -n "$CLUSTERS" ]; then
        for cluster_arn in $CLUSTERS; do
            cluster_name=$(basename $cluster_arn)
            echo "  Checking cluster: $cluster_name"

            # List and delete services
            SERVICES=$(aws ecs list-services --cluster $cluster_name --region $AWS_REGION --query 'serviceArns[*]' --output text 2>/dev/null || echo "")

            for service_arn in $SERVICES; do
                service_name=$(basename $service_arn)
                echo "    Deleting service: $service_name"
                aws ecs update-service --cluster $cluster_name --service $service_name --desired-count 0 --region $AWS_REGION &> /dev/null || true
                aws ecs delete-service --cluster $cluster_name --service $service_name --force --region $AWS_REGION &> /dev/null || true
            done

            # List and stop tasks
            TASKS=$(aws ecs list-tasks --cluster $cluster_name --region $AWS_REGION --query 'taskArns[*]' --output text 2>/dev/null || echo "")

            for task_arn in $TASKS; do
                echo "    Stopping task: $(basename $task_arn)"
                aws ecs stop-task --cluster $cluster_name --task $task_arn --region $AWS_REGION &> /dev/null || true
            done
        done

        echo -e "${GREEN}✓ ECS services and tasks deleted${NC}"
    else
        echo -e "${YELLOW}  No ECS clusters found${NC}"
    fi
else
    echo -e "${YELLOW}  Skipping (AWS CLI not found)${NC}"
fi
echo ""

# Step 3: Delete Docker images locally
echo -e "${YELLOW}[3/5] Cleaning Docker images...${NC}"
if command -v docker &> /dev/null; then
    echo "Removing dangling images..."
    docker image prune -f &> /dev/null || true

    # Remove module-specific images
    MODULE_IMAGES=$(docker images --filter=reference='*data-*' --filter=reference='*etl-*' -q)
    if [ -n "$MODULE_IMAGES" ]; then
        echo "Removing module images..."
        docker rmi $MODULE_IMAGES -f &> /dev/null || true
    fi

    echo -e "${GREEN}✓ Docker images cleaned${NC}"
else
    echo -e "${YELLOW}  Skipping (Docker not found)${NC}"
fi
echo ""

# Step 4: Destroy Terraform infrastructure
echo -e "${YELLOW}[4/5] Destroying Terraform infrastructure...${NC}"
if [ -d "terraform" ] && command -v terraform &> /dev/null; then
    cd terraform

    # Check if terraform is initialized
    if [ -d ".terraform" ]; then
        echo "Running terraform destroy..."
        terraform destroy -auto-approve

        # Clean terraform files
        rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan 2>/dev/null || true

        echo -e "${GREEN}✓ Terraform resources destroyed${NC}"
    else
        echo -e "${YELLOW}  No terraform state found${NC}"
    fi

    cd ..
else
    echo -e "${YELLOW}  Skipping (no terraform directory)${NC}"
fi
echo ""

# Step 5: Clean local files
echo -e "${YELLOW}[5/5] Cleaning temporary files...${NC}"

# Remove log files
find . -name "*.log" -type f -delete 2>/dev/null || true

# Remove Python cache
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -type f -delete 2>/dev/null || true

# Remove temporary directories
rm -rf tmp/ temp/ .pytest_cache/ 2>/dev/null || true

echo -e "${GREEN}✓ Temporary files cleaned${NC}"
echo ""

# Final verification
echo -e "${GREEN}======================================"
echo "✓ Cleanup Complete!"
echo "======================================${NC}"
echo ""
echo "Remaining manual checks:"
echo "  1. S3 buckets: aws s3 ls (delete manually if needed)"
echo "  2. CloudWatch log groups: aws logs describe-log-groups"
echo "  3. ECR repositories: aws ecr describe-repositories"
echo "  4. AWS Cost Explorer: Verify $0 daily cost"
echo ""
echo "To start fresh:"
echo "  ./scripts/setup.sh"
echo "  ./scripts/deploy-ecs.sh"
echo "  ./scripts/deploy-eks.sh"
echo ""
