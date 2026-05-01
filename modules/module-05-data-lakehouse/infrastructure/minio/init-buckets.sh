#!/bin/bash
# ============================================================================
# MinIO Bucket Initialization Script
# ============================================================================
# This script creates required S3 buckets in MinIO for the lakehouse
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MinIO Bucket Initialization${NC}"
echo -e "${BLUE}========================================${NC}"

# Wait for MinIO to be ready
echo -e "${YELLOW}⏳ Waiting for MinIO to be ready...${NC}"
sleep 10

# Configure MinIO client
echo -e "${YELLOW}🔧 Configuring MinIO client...${NC}"
mc config host add minio http://minio:9000 minioadmin minioadmin

# Create buckets
echo -e "${YELLOW}📦 Creating buckets...${NC}"

buckets=(
    "lakehouse:General lakehouse data"
    "bronze:Bronze layer - raw data"
    "silver:Silver layer - cleaned data"
    "gold:Gold layer - aggregated data"
    "warehouse:Spark warehouse and Iceberg data"
    "checkpoints:Streaming checkpoints"
    "events:Event logs"
)

for bucket_info in "${buckets[@]}"; do
    IFS=':' read -r bucket description <<< "$bucket_info"
    
    if mc mb minio/$bucket --ignore-existing; then
        echo -e "${GREEN}✓ Created bucket: $bucket - $description${NC}"
    else
        echo -e "${RED}✗ Failed to create bucket: $bucket${NC}"
    fi
done

# Set anonymous download policy for lakehouse bucket (for easier access)
echo -e "${YELLOW}🔓 Setting public read policy on lakehouse bucket...${NC}"
mc anonymous set download minio/lakehouse

# List all buckets
echo -e "${YELLOW}📋 Current buckets:${NC}"
mc ls minio/

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ MinIO initialization complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Access MinIO Console at: ${BLUE}http://localhost:9001${NC}"
echo -e "Username: ${YELLOW}minioadmin${NC}"
echo -e "Password: ${YELLOW}minioadmin${NC}"
echo ""
