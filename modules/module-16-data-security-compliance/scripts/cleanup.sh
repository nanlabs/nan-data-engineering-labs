#!/bin/bash
# Cleanup script for Module 16
set -e

echo "=========================================="
echo "Module 16: Cleanup AWS Resources"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Confirmation
echo -e "${RED}⚠️  WARNING: This will delete all AWS resources created in Module 16${NC}"
echo -e "   This includes KMS keys, S3 buckets, CloudTrail, Config, GuardDuty, etc."
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo ""
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

# 1. Disable and delete GuardDuty
echo -e "${YELLOW}1. Cleaning up GuardDuty...${NC}"
DETECTOR_IDS=$(aws guardduty list-detectors --query 'DetectorIds' --output text)

if [ -n "$DETECTOR_IDS" ]; then
    for detector in $DETECTOR_IDS; do
        echo "  Deleting detector: $detector"
        aws guardduty delete-detector --detector-id $detector || true
    done
    echo -e "  ${GREEN}✓ GuardDuty detectors deleted${NC}"
else
    echo -e "  ${YELLOW}⚠ No GuardDuty detectors found${NC}"
fi

# 2. Disable Security Hub
echo -e "\n${YELLOW}2. Disabling Security Hub...${NC}"
aws securityhub disable-security-hub 2>/dev/null && \
    echo -e "  ${GREEN}✓ Security Hub disabled${NC}" || \
    echo -e "  ${YELLOW}⚠ Security Hub not enabled${NC}"

# 3. Disable Macie
echo -e "\n${YELLOW}3. Disabling Macie...${NC}"
aws macie2 disable-macie 2>/dev/null && \
    echo -e "  ${GREEN}✓ Macie disabled${NC}" || \
    echo -e "  ${YELLOW}⚠ Macie not enabled${NC}"

# 4. Stop and delete CloudTrail trails
echo -e "\n${YELLOW}4. Cleaning up CloudTrail...${NC}"
TRAILS=$(aws cloudtrail list-trails --query 'Trails[*].Name' --output text)

if [ -n "$TRAILS" ]; then
    for trail in $TRAILS; do
        echo "  Stopping trail: $trail"
        aws cloudtrail stop-logging --name $trail || true
        echo "  Deleting trail: $trail"
        aws cloudtrail delete-trail --name $trail || true
    done
    echo -e "  ${GREEN}✓ CloudTrail trails deleted${NC}"
else
    echo -e "  ${YELLOW}⚠ No CloudTrail trails found${NC}"
fi

# 5. Stop AWS Config
echo -e "\n${YELLOW}5. Stopping AWS Config...${NC}"
RECORDERS=$(aws configservice describe-configuration-recorders --query 'ConfigurationRecorders[*].name' --output text)

if [ -n "$RECORDERS" ]; then
    for recorder in $RECORDERS; do
        echo "  Stopping recorder: $recorder"
        aws configservice stop-configuration-recorder --configuration-recorder-name $recorder || true
        echo "  Deleting recorder: $recorder"
        aws configservice delete-configuration-recorder --configuration-recorder-name $recorder || true
    done
    echo -e "  ${GREEN}✓ Config recorders deleted${NC}"
else
    echo -e "  ${YELLOW}⚠ No Config recorders found${NC}"
fi

# Delete delivery channels
CHANNELS=$(aws configservice describe-delivery-channels --query 'DeliveryChannels[*].name' --output text)
if [ -n "$CHANNELS" ]; then
    for channel in $CHANNELS; do
        echo "  Deleting delivery channel: $channel"
        aws configservice delete-delivery-channel --delivery-channel-name $channel || true
    done
fi

# 6. Delete S3 buckets
echo -e "\n${YELLOW}6. Deleting S3 buckets...${NC}"

# List of bucket prefixes to delete
BUCKET_PREFIXES="cloudtrail-logs- aws-config- data-lake-"

for prefix in $BUCKET_PREFIXES; do
    BUCKETS=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$prefix')].Name" --output text)

    for bucket in $BUCKETS; do
        echo "  Deleting bucket: $bucket"

        # Remove all objects (including versions)
        aws s3 rm s3://$bucket --recursive 2>/dev/null || true

        # Delete all versions
        aws s3api list-object-versions --bucket $bucket --output json | \
            jq -r '.Versions[] | "\(.Key) \(.VersionId)"' | \
            while read key version; do
                aws s3api delete-object --bucket $bucket --key "$key" --version-id "$version" 2>/dev/null || true
            done

        # Delete bucket
        aws s3 rb s3://$bucket --force 2>/dev/null || true
    done
done

echo -e "  ${GREEN}✓ S3 buckets deleted${NC}"

# 7. Delete IAM roles created by exercises
echo -e "\n${YELLOW}7. Cleaning up IAM roles...${NC}"

IAM_ROLES="DataEngineerRole DataScientistRole DataAnalystRole AWSConfigRole"

for role in $IAM_ROLES; do
    if aws iam get-role --role-name $role &>/dev/null; then
        echo "  Deleting role: $role"

        # Detach policies
        ATTACHED=$(aws iam list-attached-role-policies --role-name $role --query 'AttachedPolicies[*].PolicyArn' --output text)
        for policy in $ATTACHED; do
            aws iam detach-role-policy --role-name $role --policy-arn $policy || true
        done

        # Delete inline policies
        INLINE=$(aws iam list-role-policies --role-name $role --query 'PolicyNames' --output text)
        for policy in $INLINE; do
            aws iam delete-role-policy --role-name $role --policy-name $policy || true
        done

        # Delete role
        aws iam delete-role --role-name $role || true
    fi
done

echo -e "  ${GREEN}✓ IAM roles deleted${NC}"

# 8. Schedule KMS key deletion
echo -e "\n${YELLOW}8. Scheduling KMS key deletion...${NC}"

KMS_ALIASES="alias/data-lake alias/database alias/application"

for alias in $KMS_ALIASES; do
    KEY_ID=$(aws kms describe-key --key-id $alias --query 'KeyMetadata.KeyId' --output text 2>/dev/null || true)

    if [ -n "$KEY_ID" ]; then
        echo "  Scheduling deletion for key: $KEY_ID ($alias)"

        # Delete alias
        aws kms delete-alias --alias-name $alias 2>/dev/null || true

        # Schedule key deletion (minimum 7 days)
        aws kms schedule-key-deletion --key-id $KEY_ID --pending-window-in-days 7 2>/dev/null || true
    fi
done

echo -e "  ${GREEN}✓ KMS keys scheduled for deletion (7 days)${NC}"

# 9. Delete SNS topics
echo -e "\n${YELLOW}9. Deleting SNS topics...${NC}"

TOPICS=$(aws sns list-topics --query "Topics[?contains(TopicArn, 'security-alerts')].TopicArn" --output text)

for topic in $TOPICS; do
    echo "  Deleting topic: $topic"
    aws sns delete-topic --topic-arn $topic || true
done

echo -e "  ${GREEN}✓ SNS topics deleted${NC}"

# 10. Delete Lake Formation resources
echo -e "\n${YELLOW}10. Cleaning up Lake Formation...${NC}"

# Deregister S3 locations
LOCATIONS=$(aws lakeformation list-resources --query 'ResourceInfoList[*].ResourceArn' --output text 2>/dev/null || true)

for location in $LOCATIONS; do
    echo "  Deregistering: $location"
    aws lakeformation deregister-resource --resource-arn $location 2>/dev/null || true
done

echo -e "  ${GREEN}✓ Lake Formation cleaned up${NC}"

# 11. Stop Docker containers
echo -e "\n${YELLOW}11. Stopping Docker containers...${NC}"

cd infrastructure 2>/dev/null || true
docker-compose down -v 2>/dev/null && \
    echo -e "  ${GREEN}✓ Docker containers stopped${NC}" || \
    echo -e "  ${YELLOW}⚠ Docker containers not running${NC}"
cd ..

# 12. Clean local files
echo -e "\n${YELLOW}12. Cleaning local files...${NC}"

rm -rf data/encrypted/* 2>/dev/null || true
rm -rf logs/* 2>/dev/null || true
rm -rf reports/* 2>/dev/null || true
rm -f infrastructure-config.json 2>/dev/null || true

echo -e "  ${GREEN}✓ Local files cleaned${NC}"

# Summary
echo -e "\n${GREEN}=========================================="
echo "Cleanup Complete!"
echo -e "===========================================${NC}"
echo ""
echo "Cleaned up:"
echo "  - GuardDuty detectors"
echo "  - Security Hub"
echo "  - Macie"
echo "  - CloudTrail trails"
echo "  - AWS Config"
echo "  - S3 buckets"
echo "  - IAM roles"
echo "  - KMS keys (scheduled for deletion in 7 days)"
echo "  - SNS topics"
echo "  - Lake Formation resources"
echo "  - Docker containers"
echo "  - Local files"
echo ""
echo -e "${YELLOW}Note:${NC} KMS keys are scheduled for deletion but can be cancelled within 7 days"
echo ""
