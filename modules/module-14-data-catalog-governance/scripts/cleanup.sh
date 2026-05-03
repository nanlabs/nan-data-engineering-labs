#!/bin/bash

# Module 14: Data Catalog & Governance - Cleanup Script
# This script removes all resources created during module exercises

set -e

LOCALSTACK_ENDPOINT="http://localhost:4566"
BUCKET_NAME="training-data-lake"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo "Module 14: Cleanup Script"
echo "========================================="
echo ""
echo -e "${YELLOW}WARNING: This will delete all resources created in Module 14${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting cleanup...${NC}"
echo ""

# Delete Glue tables
echo "[1/7] Deleting Glue tables..."
for db in dev_sales_bronze_db dev_sales_silver_db dev_sales_gold_db shared_sales_db; do
    tables=$(awslocal glue get-tables --database-name $db --query 'TableList[*].Name' --output text 2>/dev/null || echo "")
    for table in $tables; do
        echo "  Deleting table: $db.$table"
        awslocal glue delete-table --database-name $db --name $table 2>/dev/null || true
    done
done
echo -e "${GREEN}✓ Tables deleted${NC}"
echo ""

# Delete Glue databases
echo "[2/7] Deleting Glue databases..."
for db in dev_sales_bronze_db dev_sales_silver_db dev_sales_gold_db shared_sales_db; do
    echo "  Deleting database: $db"
    awslocal glue delete-database --name $db 2>/dev/null || true
done
echo -e "${GREEN}✓ Databases deleted${NC}"
echo ""

# Delete Glue crawlers
echo "[3/7] Deleting Glue crawlers..."
for crawler in sales-bronze-crawler sales-silver-crawler sales-gold-crawler; do
    echo "  Deleting crawler: $crawler"
    awslocal glue delete-crawler --name $crawler 2>/dev/null || true
done
echo -e "${GREEN}✓ Crawlers deleted${NC}"
echo ""

# Delete S3 bucket contents and bucket
echo "[4/7] Deleting S3 bucket contents..."
awslocal s3 rm s3://${BUCKET_NAME} --recursive 2>/dev/null || true
awslocal s3 rb s3://${BUCKET_NAME} 2>/dev/null || true
echo -e "${GREEN}✓ S3 bucket deleted${NC}"
echo ""

# Delete IAM roles
echo "[5/7] Deleting IAM roles..."
for role in AWSGlueServiceRole-DataLake DataEngineer DataAnalyst DataScientist ExternalPartner ConsumerAnalyst; do
    echo "  Deleting role: $role"

    # Detach policies first
    policies=$(awslocal iam list-attached-role-policies --role-name $role --query 'AttachedPolicies[*].PolicyArn' --output text 2>/dev/null || echo "")
    for policy in $policies; do
        awslocal iam detach-role-policy --role-name $role --policy-arn $policy 2>/dev/null || true
    done

    # Delete role
    awslocal iam delete-role --role-name $role 2>/dev/null || true
done
echo -e "${GREEN}✓ IAM roles deleted${NC}"
echo ""

# Delete SNS topics
echo "[6/7] Deleting SNS topics..."
for topic in governance-alerts data-quality-alerts governance-success governance-errors; do
    echo "  Deleting topic: $topic"
    awslocal sns delete-topic --topic-arn arn:aws:sns:us-east-1:000000000000:$topic 2>/dev/null || true
done
echo -e "${GREEN}✓ SNS topics deleted${NC}"
echo ""

# Delete CloudWatch alarms
echo "[7/7] Deleting CloudWatch alarms..."
alarms=$(awslocal cloudwatch describe-alarms --query 'MetricAlarms[?starts_with(AlarmName, `sales-`)].AlarmName' --output text 2>/dev/null || echo "")
for alarm in $alarms; do
    echo "  Deleting alarm: $alarm"
    awslocal cloudwatch delete-alarms --alarm-names $alarm 2>/dev/null || true
done
echo -e "${GREEN}✓ CloudWatch alarms deleted${NC}"
echo ""

echo -e "${GREEN}========================================="
echo "Cleanup Complete!"
echo "=========================================${NC}"
echo ""
echo "All Module 14 resources have been removed."
echo "You can re-run 'bash scripts/setup.sh' to start fresh."
