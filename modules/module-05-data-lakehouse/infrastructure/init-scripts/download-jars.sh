#!/bin/bash
# ============================================================================
# Download Required JAR Files for Delta Lake and Iceberg
# ============================================================================
# This script downloads necessary JAR files for Spark to work with
# Delta Lake and Apache Iceberg
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Downloading Spark JARs${NC}"
echo -e "${BLUE}========================================${NC}"

# Create jars directory if it doesn't exist
JARS_DIR="$(dirname "$0")/../spark/jars"
mkdir -p "$JARS_DIR"

# Maven Central base URL
MAVEN_URL="https://repo1.maven.org/maven2"

# JAR versions
SCALA_VERSION="2.12"
SPARK_VERSION="3.5"
DELTA_VERSION="3.0.0"
ICEBERG_VERSION="1.4.3"
HADOOP_VERSION="3.3.4"
AWS_SDK_VERSION="1.12.262"

# Define JARs to download
declare -A JARS=(
    # Delta Lake
    ["delta-core"]="io/delta/delta-core_${SCALA_VERSION}/${DELTA_VERSION}/delta-core_${SCALA_VERSION}-${DELTA_VERSION}.jar"
    ["delta-storage"]="io/delta/delta-storage/${DELTA_VERSION}/delta-storage-${DELTA_VERSION}.jar"
    
    # Apache Iceberg
    ["iceberg-spark-runtime"]="org/apache/iceberg/iceberg-spark-runtime-${SPARK_VERSION}_${SCALA_VERSION}/${ICEBERG_VERSION}/iceberg-spark-runtime-${SPARK_VERSION}_${SCALA_VERSION}-${ICEBERG_VERSION}.jar"
    
    # Hadoop AWS (for S3 support)
    ["hadoop-aws"]="org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar"
    
    # AWS SDK Bundle
    ["aws-java-sdk-bundle"]="com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar"
)

# Download function
download_jar() {
    local name=$1
    local path=$2
    local url="${MAVEN_URL}/${path}"
    local filename=$(basename "$path")
    local dest="${JARS_DIR}/${filename}"
    
    if [ -f "$dest" ]; then
        echo -e "${YELLOW}⏭️  Skipping $name (already exists)${NC}"
        return 0
    fi
    
    echo -e "${BLUE}📥 Downloading $name...${NC}"
    
    if curl -L -o "$dest" "$url" --fail --silent --show-error; then
        echo -e "${GREEN}✓ Downloaded: $filename${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to download: $name${NC}"
        rm -f "$dest"
        return 1
    fi
}

# Download all JARs
echo -e "\n${YELLOW}Starting downloads...${NC}\n"

success=0
failed=0

for name in "${!JARS[@]}"; do
    if download_jar "$name" "${JARS[@]/$name]}"; then
        ((success++))
    else
        ((failed++))
    fi
done

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Download Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Success: $success${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed:  $failed${NC}"
fi
echo -e "\n${YELLOW}JARs location: $JARS_DIR${NC}\n"

# List downloaded files
echo -e "${YELLOW}Downloaded files:${NC}"
ls -lh "$JARS_DIR"

if [ $failed -gt 0 ]; then
    echo -e "\n${RED}⚠️  Some downloads failed. Please check your internet connection and try again.${NC}"
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All JARs downloaded successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
