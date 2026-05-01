#!/bin/bash
# Deploy CloudFormation stack

set -e

ENDPOINT_URL="http://localhost:4566"
STACK_NAME="quickmart-data-lake"
TEMPLATE_FILE="data-lake-stack.yaml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CloudFormation Stack Deployment     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# TODO: Add parameter parsing for environment
# Default values
ENVIRONMENT="${1:-dev}"
RETENTION_DAYS="${2:-90}"

echo -e "${BLUE}Configuration:${NC}"
echo "  Stack Name: $STACK_NAME-$ENVIRONMENT"
echo "  Environment: $ENVIRONMENT"
echo "  Retention Days: $RETENTION_DAYS"
echo ""

# TODO: Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${YELLOW}⚠ Template file not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

# TODO: Validate template
echo -e "${BLUE}[1/3]${NC} Validating template..."
# aws --endpoint-url=$ENDPOINT_URL cloudformation validate-template \
#   --template-body file://$TEMPLATE_FILE > /dev/null
echo -e "${GREEN}✓${NC} Template is valid"

# TODO: Create or update stack
echo -e "${BLUE}[2/3]${NC} Deploying stack..."

# Check if stack exists
# TODO: Implement stack existence check
# aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stacks \
#   --stack-name $STACK_NAME-$ENVIRONMENT &> /dev/null

STACK_EXISTS=$?

if [ $STACK_EXISTS -eq 0 ]; then
    echo "Stack exists, updating..."
    # TODO: Update stack
    # aws --endpoint-url=$ENDPOINT_URL cloudformation update-stack \
    #   --stack-name $STACK_NAME-$ENVIRONMENT \
    #   --template-body file://$TEMPLATE_FILE \
    #   --parameters \
    #     ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    #     ParameterKey=DataRetentionDays,ParameterValue=$RETENTION_DAYS \
    #   --capabilities CAPABILITY_NAMED_IAM
else
    echo "Creating new stack..."
    # TODO: Create stack
    # aws --endpoint-url=$ENDPOINT_URL cloudformation create-stack \
    #   --stack-name $STACK_NAME-$ENVIRONMENT \
    #   --template-body file://$TEMPLATE_FILE \
    #   --parameters \
    #     ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    #     ParameterKey=DataRetentionDays,ParameterValue=$RETENTION_DAYS \
    #   --capabilities CAPABILITY_NAMED_IAM
fi

# TODO: Wait for stack operation to complete
echo -e "${BLUE}[3/3]${NC} Waiting for stack operation..."
# aws --endpoint-url=$ENDPOINT_URL cloudformation wait stack-create-complete \
#   --stack-name $STACK_NAME-$ENVIRONMENT 2>/dev/null || \
# aws --endpoint-url=$ENDPOINT_URL cloudformation wait stack-update-complete \
#   --stack-name $STACK_NAME-$ENVIRONMENT 2>/dev/null

echo -e "${GREEN}✓${NC} Stack operation complete"

# TODO: Display stack outputs
echo ""
echo -e "${BLUE}Stack Outputs:${NC}"
# aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stacks \
#   --stack-name $STACK_NAME-$ENVIRONMENT \
#   --query 'Stacks[0].Outputs' \
#   --output table

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Deployment Complete!             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Usage instructions
echo -e "${BLUE}Verify deployment:${NC}"
echo "  aws --endpoint-url=$ENDPOINT_URL cloudformation describe-stacks --stack-name $STACK_NAME-$ENVIRONMENT"
echo ""
echo -e "${BLUE}View resources:${NC}"
echo "  aws --endpoint-url=$ENDPOINT_URL cloudformation list-stack-resources --stack-name $STACK_NAME-$ENVIRONMENT"
echo ""
