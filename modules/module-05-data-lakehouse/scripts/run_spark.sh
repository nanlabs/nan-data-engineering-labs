#!/bin/bash
# run_spark.sh - Lanzar PySpark shell con Delta Lake y Apache Iceberg

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  PySpark Shell con Delta Lake${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Debe ejecutar este script desde el directorio module-05-data-lakehouse${NC}"
    exit 1
fi

# Verificar que Docker esté corriendo
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker no está corriendo${NC}"
    echo -e "${YELLOW}   Inicie los servicios con: cd infrastructure && docker-compose up -d${NC}"
    exit 1
fi

# Verificar servicios
echo -e "${YELLOW}🔍 Verificando servicios...${NC}"
if docker-compose -f infrastructure/docker-compose.yml ps | grep -q "spark-master.*Up"; then
    echo -e "${GREEN}✅ Spark Master corriendo${NC}"
else
    echo -e "${RED}❌ Spark Master no está corriendo${NC}"
    echo -e "${YELLOW}   Inicie con: cd infrastructure && docker-compose up -d${NC}"
    exit 1
fi

# Opciones por defecto
SPARK_MASTER=${SPARK_MASTER:-"spark://spark-master:7077"}
EXECUTOR_MEMORY=${EXECUTOR_MEMORY:-"2g"}
DRIVER_MEMORY=${DRIVER_MEMORY:-"2g"}
EXECUTOR_CORES=${EXECUTOR_CORES:-"2"}

echo -e "\n${BLUE}📋 Configuración:${NC}"
echo -e "  Master: ${SPARK_MASTER}"
echo -e "  Driver Memory: ${DRIVER_MEMORY}"
echo -e "  Executor Memory: ${EXECUTOR_MEMORY}"
echo -e "  Executor Cores: ${EXECUTOR_CORES}\n"

echo -e "${YELLOW}🚀 Iniciando PySpark shell...${NC}\n"

# Ejecutar PySpark dentro del contenedor de Spark
docker exec -it spark-master pyspark \
    --master ${SPARK_MASTER} \
    --driver-memory ${DRIVER_MEMORY} \
    --executor-memory ${EXECUTOR_MEMORY} \
    --executor-cores ${EXECUTOR_CORES} \
    --packages io.delta:delta-spark_2.12:3.0.0,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.0 \
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension,org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions" \
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
    --conf "spark.sql.catalog.iceberg_catalog=org.apache.iceberg.spark.SparkCatalog" \
    --conf "spark.sql.catalog.iceberg_catalog.type=hive" \
    --conf "spark.sql.catalog.iceberg_catalog.uri=thrift://hive-metastore:9083" \
    --conf "spark.sql.catalog.iceberg_catalog.warehouse=s3a://warehouse/iceberg" \
    --conf "spark.hadoop.fs.s3a.endpoint=http://minio:9000" \
    --conf "spark.hadoop.fs.s3a.access.key=minioadmin" \
    --conf "spark.hadoop.fs.s3a.secret.key=minioadmin" \
    --conf "spark.hadoop.fs.s3a.path.style.access=true" \
    --conf "spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem"

echo -e "\n${GREEN}✅ PySpark shell finalizado${NC}"
