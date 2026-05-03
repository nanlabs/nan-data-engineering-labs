#!/bin/bash
# Deploy EKS cluster for Module 13
# Usage: ./deploy-eks.sh [cluster-name]

set -e

CLUSTER_NAME=${1:-"data-engineering-cluster"}
AWS_REGION=${AWS_REGION:-"us-east-1"}
K8S_VERSION="1.28"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================"
echo "EKS Deployment Script"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $AWS_REGION"
echo "Kubernetes: $K8S_VERSION"
echo "======================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

for cmd in aws kubectl eksctl terraform; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd not found${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Step 1: Create EKS cluster with Terraform
echo -e "${GREEN}[1/6] Creating EKS cluster with Terraform...${NC}"
cd terraform

terraform init

terraform plan \
    -var="cluster_name=$CLUSTER_NAME" \
    -var="cluster_version=$K8S_VERSION" \
    -var="aws_region=$AWS_REGION" \
    -out=tfplan

echo -e "${YELLOW}Ready to create EKS cluster. Continue? (yes/no)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 0
fi

terraform apply tfplan
rm tfplan
echo ""

# Step 2: Configure kubectl
echo -e "${GREEN}[2/6] Configuring kubectl...${NC}"
aws eks update-kubeconfig \
    --name $CLUSTER_NAME \
    --region $AWS_REGION

kubectl cluster-info
echo ""

# Wait for nodes
echo "Waiting for nodes to be ready..."
kubectl wait --for=condition=ready node --all --timeout=600s
echo -e "${GREEN}✓ Nodes ready${NC}"
echo ""

# Step 3: Install AWS Load Balancer Controller
echo -e "${GREEN}[3/6] Installing AWS Load Balancer Controller...${NC}"

# Install cert-manager (prerequisite)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s

# Download IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

# Create IAM policy
POLICY_ARN=$(aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy-$CLUSTER_NAME \
    --policy-document file://iam_policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    aws iam list-policies --query "Policies[?PolicyName=='AWSLoadBalancerControllerIAMPolicy-$CLUSTER_NAME'].Arn" --output text)

rm iam_policy.json

# Create service account with IRSA
eksctl create iamserviceaccount \
    --cluster=$CLUSTER_NAME \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --attach-policy-arn=$POLICY_ARN \
    --override-existing-serviceaccounts \
    --approve

# Install controller with Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=$CLUSTER_NAME \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller \
    --wait

echo -e "${GREEN}✓ AWS Load Balancer Controller installed${NC}"
echo ""

# Step 4: Install CloudWatch Container Insights
echo -e "${GREEN}[4/6] Installing CloudWatch Container Insights...${NC}"

kubectl create namespace amazon-cloudwatch || true

curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | \
    sed "s/{{cluster_name}}/$CLUSTER_NAME/;s/{{region_name}}/$AWS_REGION/" | \
    kubectl apply -f -

echo -e "${GREEN}✓ CloudWatch Container Insights installed${NC}"
echo ""

# Step 5: Create namespaces
echo -e "${GREEN}[5/6] Creating application namespaces...${NC}"
kubectl create namespace data-pipeline || true
kubectl create namespace spark-jobs || true
kubectl create namespace monitoring || true

echo -e "${GREEN}✓ Namespaces created${NC}"
echo ""

# Step 6: Verify deployment
echo -e "${GREEN}[6/6] Verifying deployment...${NC}"

# Check nodes
echo "Nodes:"
kubectl get nodes

echo ""
echo "Pods in kube-system:"
kubectl get pods -n kube-system

echo ""
echo "Namespaces:"
kubectl get namespaces

echo ""
echo -e "${GREEN}======================================"
echo "✓ EKS Deployment Complete!"
echo "======================================${NC}"
echo ""
echo "Cluster info:"
echo "  Name: $CLUSTER_NAME"
echo "  Region: $AWS_REGION"
echo "  Endpoint: $(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
echo ""
echo "Next steps:"
echo "  1. Deploy workloads: kubectl apply -f k8s/"
echo "  2. View dashboards: kubectl port-forward -n monitoring svc/grafana 3000:80"
echo "  3. Check logs: kubectl logs -f <pod-name> -n data-pipeline"
echo ""
echo "Useful commands:"
echo "  • Get pods: kubectl get pods --all-namespaces"
echo "  • Describe cluster: kubectl cluster-info"
echo "  • View console: https://console.aws.amazon.com/eks/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo ""
echo "To destroy: cd terraform && terraform destroy"
echo ""
