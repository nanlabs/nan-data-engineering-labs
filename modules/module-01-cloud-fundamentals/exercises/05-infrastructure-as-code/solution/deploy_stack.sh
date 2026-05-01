#!/bin/bash
# Deploy CloudFormation stack - Complete Solution

set -e

ENDPOINT_URL="http://localhost:4566"
STACK_NAME="quickmart-data-lake"
TEMPLATE_FILE="data-lake-stack.yaml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CloudFormation Stack Deployment     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Parse arguments
ENVIRONMENT="${1:-dev}"
RETENTION_DAYS="${2:-90}"
GLACIER_DAYS="${3:-180}"

echo -e "${BLUE}Configuration:${NC}"
echo "  Stack Name: $STACK_NAME-$ENVIRONMENT"
echo "  Environment: $ENVIRONMENT"
echo "  Retention (IA): $RETENTION_DAYS days"
echo "  Retention (Glacier): $GLACIER_DAYS days"
echo ""

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}✗ Template file not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

# Validate template
echo -e "${BLUE}[1/4]${NC} Validating template..."
if aws --endpoint-url=$ENDPOINT_URL cloudformation validate-template \
  --template-body file://$TEMPLATE_FILE > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Template is valid"
else
    echo -e "${RED}✗ Template validation failed${NC}"
    exit 1
fi

# Check if stack exists
echo -e "${BLUE}[2/4]${NC} Checking stack status..."
STACK_EXISTS=0
aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stacks \
  --stack-name $STACK_NAME-$ENVIRONMENT &> /dev/null && STACK_EXISTS=1

if [ $STACK_EXISTS -eq 1 ]; then
    echo -e "${YELLOW}⚠${NC} Stack exists, will update"
    ACTION="update"
else
    echo -e "${GREEN}✓${NC} New stack, will create"
    ACTION="create"
fi

# Deploy stack
echo -e "${BLUE}[3/4]${NC} Deploying stack..."

if [ "$ACTION" == "update" ]; then
    # Use change set for updates
    CHANGE_SET_NAME="update-$(date +%Y%m%d-%H%M%S)"

    aws --endpoint-url=$ENDPOINT_URL cloudformation create-change-set \
      --stack-name $STACK_NAME-$ENVIRONMENT \
      --change-set-name $CHANGE_SET_NAME \
      --template-body file://$TEMPLATE_FILE \
      --parameters \
        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        ParameterKey=DataRetentionDays,ParameterValue=$RETENTION_DAYS \
        ParameterKey=GlacierTransitionDays,ParameterValue=$GLACIER_DAYS \
      --capabilities CAPABILITY_NAMED_IAM

    echo "Waiting for change set..."
    aws --endpoint-url=$ENDPOINT_URL cloudformation wait change-set-create-complete \
      --stack-name $STACK_NAME-$ENVIRONMENT \
      --change-set-name $CHANGE_SET_NAME 2>/dev/null || true

    # Show changes
    echo -e "\n${BLUE}Proposed Changes:${NC}"
    aws --endpoint-url=$ENDPOINT_URL cloudformation describe-change-set \
      --stack-name $STACK_NAME-$ENVIRONMENT \
      --change-set-name $CHANGE_SET_NAME \
      --query 'Changes[].{Action:ResourceChange.Action,Resource:ResourceChange.LogicalResourceId,Type:ResourceChange.ResourceType}' \
      --output table || echo "No changes detected"

    # Execute change set
    echo ""
    read -p "Execute update? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        aws --endpoint-url=$ENDPOINT_URL cloudformation execute-change-set \
          --stack-name $STACK_NAME-$ENVIRONMENT \
          --change-set-name $CHANGE_SET_NAME

        WAIT_TYPE="stack-update-complete"
    else
        echo -e "${YELLOW}⚠ Update cancelled${NC}"
        exit 0
    fi
else
    # Create new stack
    aws --endpoint-url=$ENDPOINT_URL cloudformation create-stack \
      --stack-name $STACK_NAME-$ENVIRONMENT \
      --template-body file://$TEMPLATE_FILE \
      --parameters \
        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        ParameterKey=DataRetentionDays,ParameterValue=$RETENTION_DAYS \
        ParameterKey=GlacierTransitionDays,ParameterValue=$GLACIER_DAYS \
      --capabilities CAPABILITY_NAMED_IAM \
      --tags \
        Key=Environment,Value=$ENVIRONMENT \
        Key=Project,Value=QuickMart \
        Key=ManagedBy,Value=CloudFormation

    WAIT_TYPE="stack-create-complete"
fi

# Wait for completion
echo -e "${BLUE}[4/4]${NC} Waiting for stack operation..."
if aws --endpoint-url=$ENDPOINT_URL cloudformation wait $WAIT_TYPE \
  --stack-name $STACK_NAME-$ENVIRONMENT 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Stack operation complete"
else
    echo -e "${RED}✗ Stack operation failed${NC}"
    echo "Check events:"
    aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stack-events \
      --stack-name $STACK_NAME-$ENVIRONMENT \
      --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]' \
      --output table
    exit 1
fi

# Display outputs
echo ""
echo -e "${BLUE}Stack Outputs:${NC}"
aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stacks \
  --stack-name $STACK_NAME-$ENVIRONMENT \
  --query 'Stacks[0].Outputs' \
  --output table

# Display resources
echo ""
echo -e "${BLUE}Created Resources:${NC}"
aws --endpoint-url=$ENDPOINT_URL cloudformation list-stack-resources \
  --stack-name $STACK_NAME-$ENVIRONMENT \
  --query 'StackResourceSummaries[].{Type:ResourceType,LogicalId:LogicalResourceId,Status:ResourceStatus}' \
  --output table

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Deployment Complete!             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Verification commands
echo -e "${BLUE}Verification Commands:${NC}"
echo ""
echo "View stack details:"
echo "  aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stacks --stack-name $STACK_NAME-$ENVIRONMENT"
echo ""
echo "View stack resources:"
echo "  aws --endpoint-url=$ENDPOINT_URL cloudformation list-stack-resources --stack-name $STACK_NAME-$ENVIRONMENT"
echo ""
echo "View S3 bucket:"
echo "  aws --endpoint-url=$ENDPOINT_URL s3 ls s3://quickmart-data-lake-$ENVIRONMENT-000000000000/"
echo ""
echo "Delete stack (when done):"
echo "  aws --endpoint-url=$ENDPOINT_URL cloudformation delete-stack --stack-name $STACK_NAME-$ENVIRONMENT"
echo ""
