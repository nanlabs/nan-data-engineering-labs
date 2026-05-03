# Infrastructure - data Lakehouse

## 📋 DescrIPtion

This directory contains the complete Docker infrastructure configuration for the data Lakehouse module. It includes all the services necessary to work with Delta Lake, Apache Iceberg and Apache Spark.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                 LAKEHOUSE INFRASTRUCTURE                     │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │   Jupyter    │────▶│ Spark Master │────▶│   MinIO    │ │
│  │     Lab      │     │   & Worker   │     │    (S3)    │ │
│  └──────────────┘     └──────────────┘     └────────────┘ │
│         │                     │                     │       │
│         └─────────────────────┼─────────────────────┘       │
│                               │                             │
│                     ┌─────────▼─────────┐                   │
│                     │ Hive Metastore    │                   │
│                     │  (PostgreSQL)     │                   │
│                     └───────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 🐳 services

### 1. **MinIO** (S3-Compatible Storage)
- **Port API**: 9000
- **Port Console**: 9001
- **Cnetworkenciales**: minioadmin/minioadmin
- **Buckets**:
  - `lakehouse` - Datas generales
  - `bronze` - Capa Bronze (raw data)
  - `silver` - Capa Silver (cleaned data)
  - `gold` - Capa Gold (aggregated data)
  - `warehouse` - Spark warehouse e Iceberg
  - `checkpoints` - Checkpoints of streaming
  - `events` - Event logs

### 2. **Apache Spark**
- **Master UI**: 8080
- **Worker UI**: 8081
- **Master URL**: spark://spark-master:7077
- **Configuration**:
  - Spark 3.5.0
  - Delta Lake 3.0.0
  - Apache Iceberg 1.4.3
  - Integration with S3/MinIO
  - Hive Metastore

### 3. **Hive Metastore**
- **Port**: 9083
- **Backend**: PostgreSQL
- **Purpose**: Metadata catalog for Delta Lake and Iceberg

### 4. **PostgreSQL**
- **Port**: 5432
- **Database**: metastore
- **User**: hive/hive
- **Purpose**: Backend for Hive Metastore

### 5. **Jupyter Lab**
- **Port**: 8888
- **not authentication** (local development)
- **Pre-instalado**:
  - PySpark
  - Delta Lake
  - PyIceberg
  - Great Expectations

## 🚀 Quick Start

### Prerequisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 10GB espacio in disk

### Paso 1: Descargar JARs necesarios

```bash
cd infrastructure
chmod +x init-scrIPts/download-jars.sh
./init-scrIPts/download-jars.sh
```

this scrIPt descarga:
- Delta Lake JARs (core, storage)
- Apache Iceberg JAR
- Hadoop AWS connector
- AWS SDK Bundle

### Paso 2: Iniciar services

```bash
# Iniciar todos los servicios
docker-compose up -d

# to see logs
docker-compose logs -f

# to see estado of servicios
docker-compose ps
```

### Step 3: Verify that everything is running

```bash
# Verificar Spark Master
curl HTTP://localhost:8080

# Verificar MinIO
curl HTTP://localhost:9000/minio/health/live

# Verificar Jupyter
curl HTTP://localhost:8888
```

### Paso 4: Acceder to las interfaces

- **Spark Master UI**: HTTP://localhost:8080
- **Spark Worker UI**: HTTP://localhost:8081
- **MinIO Console**: HTTP://localhost:9001 (minioadmin/minioadmin)
- **Jupyter Lab**: HTTP://localhost:8888

## 📁 Structure of Archivos

```
infrastructure/
├── docker-compose.yml           # Definición of servicios
├── .env.example                 # Variables of entorno (template)
├── README.md                    # this archivo
│
├── spark/                       # Configuration Spark
│   ├── spark-defaults.conf      # Configuration princIPal Spark
│   ├── log4j.properties         # Logging configuration
│   └── jars/                    # JARs adicionales (Delta, Iceberg)
│
├── minio/                       # Configuration MinIO
│   └── init-buckets.sh          # ScrIPt for crear buckets
│
├── jupyter/                     # Configuration Jupyter
│   └── jupyter_notebook_config.py
│
└── init-scrIPts/                # ScrIPts of inicialización
    └── download-jars.sh         # Descarga JARs necesarios
```

## 🔧 Settings

### Variables of Entorno

Copia `.env.example` to `.env`and adjust as needed:

```bash
cp .env.example .env
```

Variables princIPales:
- `MINIO_ROOT_USER/PASSWORD`: Cnetworkenciales MinIO
- `SPARK_WORKER_CORES`: Cores per worker
- `SPARK_WORKER_MEMORY`: Memory by worker
- `SPARK_DRIVER_MEMORY`: Memory of the driver
- `SPARK_EXECUTOR_MEMORY`: Memory of the executor

### scale Workers

```bash
# Escalar to 3 workers
docker-compose up -d --scale spark-worker=3

# Verificar in Spark Master UI (HTTP://localhost:8080)
```

### resources Recomendados

| Componente | CPU | RAM | Disk |
|------------|-----|-----|-------|
| Spark Master | 1 core | 2GB | 1GB |
| Spark Worker (each) | 2 cores | 4GB | 5GB |
| MinIO | 1 core | 512MB | 10GB |
| PostgreSQL | 1 core | 512MB | 1GB |
| Hive Metastore | 1 core | 1GB | 1GB |
| Jupyter Lab | 2 cores | 2GB | 2GB |
| **Total** | **8+ cores** | **12+ GB** | **20+ GB** |

## 📝 Common Use

### PySpark in Jupyter

```python
from pyspark.sql import SparkSession

# Crear SparkSession with Delta Lake
spark = SparkSession.builder \
    .appName("DataLakehouse") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Escribir to Delta Lake
df.write.format("delta").save("s3a://bronze/events")

# Leer desde Delta Lake
df = spark.read.format("delta").load("s3a://bronze/events")
```

### Acceder to MinIO desde Python

```python
import boto3

# Configurar client S3 (MinIO)
s3 = boto3.client(
    's3',
    endpoint_url='HTTP://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

# Listar buckets
buckets = s3.list_buckets()
print(buckets)
```

### PySpark Shell

```bash
# Ejecutar desde host
docker-compose exec spark-master pyspark

# or usar el scrIPt (when am disponible)
../scrIPts/run_spark.sh
```

## 🧪 Testing

### Verificar Delta Lake

```python
from delta import DeltaTable

# Crear table Delta
df.write.format("delta").save("s3a://bronze/test_table")

# Verificar metadata
deltaTable = DeltaTable.forPath(spark, "s3a://bronze/test_table")
print(deltaTable.history().show())
```

### Verificar Iceberg

```python
# Crear table Iceberg
spark.sql("""
    CREATE TABLE iceberg.default.test_table (
        id bigint,
        name string
    ) USING iceberg
    LOCATION 's3a://warehouse/iceberg/test_table'
""")

# Insertar datas
spark.sql("INSERT INTO iceberg.default.test_table VALUES (1, 'test')")

# Query
spark.sql("SELECT * FROM iceberg.default.test_table").show()
```

## 🛠️ Mantenimiento

### to see Logs

```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f spark-master
docker-compose logs -f minio
docker-compose logs -f jupyter
```

### Reiniciar services

```bash
# Reiniciar servicio específico
docker-compose restart spark-master

# Reiniciar todos
docker-compose restart
```

### Limpiar and Reiniciar

```bash
# Detener servicios
docker-compose down

# Detener and eliminar volúmenes (⚠️ elimina datas)
docker-compose down -v

# Reiniciar desde cero
docker-compose up -d
```

### Update Images

```bash
# Descargar últimas versiones
docker-compose pull

# Recrear contenedores
docker-compose up -d --force-recreate
```

## 🐛 Troubleshooting

### Problem: services not inician

```bash
# Verificar resources disponibles
docker system info

# Verificar logs of error
docker-compose logs

# Liberar resources
docker system prune -to
```

### Problem: Spark not he/she can conectar to MinIO

```bash
# Verificar network
docker network inspect lakehouse-network

# Verificar que MinIO is corriendo
docker-compose ps minio

# Test of conectividad
docker-compose exec spark-master curl HTTP://minio:9000/minio/health/live
```

### Problem: JARs not encontrados

```bash
# Re-descargar JARs
cd init-scrIPts
./download-jars.sh

# Verificar que are in the directory correcto
ls -la ../spark/jars/
```

### Problem: Port in uso

```bash
# Identificar process usando port
lsof -i :8080
lsof -i :9000

# Cambiar port in docker-compose.yml or .env
```

## 📚 Additional Resources

- [Spark Configuration](HTTPs://spark.apache.org/docs/latest/configuration.html)
- [Delta Lake Quickstart](HTTPs://docs.delta.io/latest/quick-start.html)
- [Iceberg Spark Configuration](HTTPs://iceberg.apache.org/docs/latest/spark-configuration/)
- [MinIO Documentation](HTTPs://min.io/docs/minio/linux/index.html)

## ⚠️ Notes Importantes

1. **security**: This configuration is for **local development** only
   - Authentication disabled in Jupyter
   - Cnetworkenciales by defecto in MinIO
   - without SSL/TLS

2. **resources**: Adjust according to your machine
   - Networkuce workers if you have less of 16GB RAM
   - Networkuce memory of executor/driver if is necesario

3. **Persistencia**: Los datas se almacenan in volumes
   - `minio-data`: Datas of MinIO
   - `postgres-data`: Metadata of Hive
   - `spark-warehouse`: Spark warehouse
   - Usar `docker-compose down -v` elimina everything

4. **Performance**: for mejor performance
   - Aumenta `SPARK_WORKER_CORES` and `SPARK_WORKER_MEMORY`
   - Escala workers: `--scale spark-worker=3`
   - Usa SSD for Docker volumes

---

**Last update**: February 2026
**Version**: 1.0.0
