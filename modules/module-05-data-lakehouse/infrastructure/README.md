# Infraestructura - Data Lakehouse

## 📋 Description

This directory contains the complete Docker infrastructure configuration for the Data Lakehouse module. It includes all the services necessary to work with Delta Lake, Apache Iceberg and Apache Spark.

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
- **Puerto API**: 9000
- **Puerto Console**: 9001
- **Credenciales**: minioadmin/minioadmin
- **Buckets**:
  - `lakehouse` - Datos generales
  - `bronze` - Capa Bronze (raw data)
  - `silver` - Capa Silver (cleaned data)
  - `gold` - Capa Gold (aggregated data)
  - `warehouse` - Spark warehouse e Iceberg
  - `checkpoints` - Checkpoints de streaming
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
- **Puerto**: 9083
- **Backend**: PostgreSQL
- **Purpose**: Metadata catalog for Delta Lake and Iceberg

### 4. **PostgreSQL**
- **Puerto**: 5432
- **Database**: metastore
- **Usuario**: hive/hive
- **Purpose**: Backend for Hive Metastore

### 5. **Jupyter Lab**
- **Puerto**: 8888
- **No authentication** (local development)
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
- 10GB espacio en disco

### Paso 1: Descargar JARs necesarios

```bash
cd infrastructure
chmod +x init-scripts/download-jars.sh
./init-scripts/download-jars.sh
```

Este script descarga:
- Delta Lake JARs (core, storage)
- Apache Iceberg JAR
- Hadoop AWS connector
- AWS SDK Bundle

### Paso 2: Iniciar services

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver estado de servicios
docker-compose ps
```

### Step 3: Verify that everything is running

```bash
# Verificar Spark Master
curl http://localhost:8080

# Verificar MinIO
curl http://localhost:9000/minio/health/live

# Verificar Jupyter
curl http://localhost:8888
```

### Paso 4: Acceder a las interfaces

- **Spark Master UI**: http://localhost:8080
- **Spark Worker UI**: http://localhost:8081
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Jupyter Lab**: http://localhost:8888

## 📁 Estructura de Archivos

```
infrastructure/
├── docker-compose.yml           # Definición de servicios
├── .env.example                 # Variables de entorno (template)
├── README.md                    # Este archivo
│
├── spark/                       # Configuración Spark
│   ├── spark-defaults.conf      # Configuración principal Spark
│   ├── log4j.properties         # Logging configuration
│   └── jars/                    # JARs adicionales (Delta, Iceberg)
│
├── minio/                       # Configuración MinIO
│   └── init-buckets.sh          # Script para crear buckets
│
├── jupyter/                     # Configuración Jupyter
│   └── jupyter_notebook_config.py
│
└── init-scripts/                # Scripts de inicialización
    └── download-jars.sh         # Descarga JARs necesarios
```

## 🔧 Settings

### Variables de Entorno

Copia `.env.example` a `.env`and adjust as needed:

```bash
cp .env.example .env
```

Variables principales:
- `MINIO_ROOT_USER/PASSWORD`: Credenciales MinIO
- `SPARK_WORKER_CORES`: Cores per worker
- `SPARK_WORKER_MEMORY`: Memoria por worker
- `SPARK_DRIVER_MEMORY`: Memoria del driver
- `SPARK_EXECUTOR_MEMORY`: Memoria del executor

### scale Workers

```bash
# Escalar a 3 workers
docker-compose up -d --scale spark-worker=3

# Verificar en Spark Master UI (http://localhost:8080)
```

### resources Recomendados

| Componente | CPU | RAM | Disco |
|------------|-----|-----|-------|
| Spark Master | 1 core | 2GB | 1GB |
| Spark Worker (each) | 2 cores | 4GB | 5GB |
| MinIO | 1 core | 512MB | 10GB |
| PostgreSQL | 1 core | 512MB | 1GB |
| Hive Metastore | 1 core | 1GB | 1GB |
| Jupyter Lab | 2 cores | 2GB | 2GB |
| **Total** | **8+ cores** | **12+ GB** | **20+ GB** |

## 📝 Common Use

### PySpark en Jupyter

```python
from pyspark.sql import SparkSession

# Crear SparkSession con Delta Lake
spark = SparkSession.builder \
    .appName("DataLakehouse") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Escribir a Delta Lake
df.write.format("delta").save("s3a://bronze/events")

# Leer desde Delta Lake
df = spark.read.format("delta").load("s3a://bronze/events")
```

### Acceder a MinIO desde Python

```python
import boto3

# Configurar cliente S3 (MinIO)
s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
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

# O usar el script (cuando esté disponible)
../scripts/run_spark.sh
```

## 🧪 Testing

### Verificar Delta Lake

```python
from delta import DeltaTable

# Crear tabla Delta
df.write.format("delta").save("s3a://bronze/test_table")

# Verificar metadata
deltaTable = DeltaTable.forPath(spark, "s3a://bronze/test_table")
print(deltaTable.history().show())
```

### Verificar Iceberg

```python
# Crear tabla Iceberg
spark.sql("""
    CREATE TABLE iceberg.default.test_table (
        id bigint,
        name string
    ) USING iceberg
    LOCATION 's3a://warehouse/iceberg/test_table'
""")

# Insertar datos
spark.sql("INSERT INTO iceberg.default.test_table VALUES (1, 'test')")

# Query
spark.sql("SELECT * FROM iceberg.default.test_table").show()
```

## 🛠️ Mantenimiento

### Ver Logs

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

### Limpiar y Reiniciar

```bash
# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ elimina datos)
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

### Problema: services no inician

```bash
# Verificar recursos disponibles
docker system info

# Verificar logs de error
docker-compose logs

# Liberar recursos
docker system prune -a
```

### Problema: Spark no puede conectar a MinIO

```bash
# Verificar red
docker network inspect lakehouse-network

# Verificar que MinIO está corriendo
docker-compose ps minio

# Test de conectividad
docker-compose exec spark-master curl http://minio:9000/minio/health/live
```

### Problema: JARs no encontrados

```bash
# Re-descargar JARs
cd init-scripts
./download-jars.sh

# Verificar que están en el directorio correcto
ls -la ../spark/jars/
```

### Problema: Puerto en uso

```bash
# Identificar proceso usando puerto
lsof -i :8080
lsof -i :9000

# Cambiar puerto en docker-compose.yml o .env
```

## 📚 Additional Resources

- [Spark Configuration](https://spark.apache.org/docs/latest/configuration.html)
- [Delta Lake Quickstart](https://docs.delta.io/latest/quick-start.html)
- [Iceberg Spark Configuration](https://iceberg.apache.org/docs/latest/spark-configuration/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)

## ⚠️ Notas Importantes

1. **security**: This configuration is for **local development** only
   - Authentication disabled in Jupyter
   - Credenciales por defecto en MinIO
   - Sin SSL/TLS

2. **resources**: Adjust according to your machine
   - Reduce workers si tienes menos de 16GB RAM
   - Reduce memoria de executor/driver si es necesario

3. **Persistencia**: Los datos se almacenan en volumes
   - `minio-data`: Datos de MinIO
   - `postgres-data`: Metadata de Hive
   - `spark-warehouse`: Spark warehouse
   - Usar `docker-compose down -v` elimina TODO

4. **Performance**: Para mejor performance
   - Aumenta `SPARK_WORKER_CORES` y `SPARK_WORKER_MEMORY`
   - Escala workers: `--scale spark-worker=3`
   - Usa SSD para Docker volumes

---

**Last update**: February 2026
**Version**: 1.0.0
