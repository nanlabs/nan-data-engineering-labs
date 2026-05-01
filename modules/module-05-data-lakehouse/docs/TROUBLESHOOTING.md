# Troubleshooting Guide

## 🔧 Problemas Comunes y Soluciones

### 1. Docker Issues

#### ❌ "Docker daemon not running"

**Yesntomas**:
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution**:
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Abre Docker Desktop
```

#### ❌ "Port already in use"

**Yesntomas**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:9000: bind: address already in use
```

**Solution**:
```bash
# Ver qué proceso usa el puerto
lsof -i :9000

# Matar proceso
kill -9 <PID>

# O cambiar puerto en docker-compose.yml
ports:
  - "9001:9000"  # Cambiar 9000 por 9001
```

---

### 2. MinIO Issues

#### ❌ "AccessDenied: Access Denied"

**Yesntomas**:
```python
botocore.exceptions.ClientError: An error occurred (AccessDenied)
```

**Solution**:
```python
# Verificar credenciales en spark session
spark = SparkSession.builder \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "password123") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .getOrCreate()
```

#### ❌ Bucket no existe

**Yesntomas**:
```
NoSuchBucket: The specified bucket does not exist
```

**Solution**:
```bash
# Crear bucket manualmente
docker exec minio mc mb local/bronze
docker exec minio mc mb local/silver
docker exec minio mc mb local/gold
```

---

### 3. Spark Issues

#### ❌ "Py4JJavaError: An error occurred while calling"

**Yesntomas**:
```python
py4j.protocol.Py4JJavaError: An error occurred while calling o123.save
```

**Solution 1** - Check Delta Lake:
```python
# Verificar que delta-spark está instalado
pip show delta-spark

# Reinstalar si necesario
pip install delta-spark==3.0.0
```

**Solution 2** - Add configuration:
```python
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("App") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
```

#### ❌ "OutOfMemoryError: Java heap space"

**Yesntomas**:
```
java.lang.OutOfMemoryError: Java heap space
```

**Solution**:
```python
spark = SparkSession.builder \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()
```

#### ❌ Spark muy lento

**Solution**:
```python
# Aumentar particiones
df.repartition(100).write.format("delta").save(path)

# Habilitar broadcast
from pyspark.sql.functions import broadcast
large_df.join(broadcast(small_df), "id")

# Usar cache para datos pequeños
df.cache()
```

---

### 4. Delta Lake Issues

#### ❌ "ConcurrentModificationException"

**Yesntomas**:
```
delta.exceptions.ConcurrentModificationException: 
A concurrent transaction has written new data
```

**Solution**:
```python
# Retry automático
from delta.tables import DeltaTable
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        delta_table.update(...)
        break
    except ConcurrentModificationException:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

#### ❌ "ProtocolChangedException"

**Yesntomas**:
```
delta.exceptions.ProtocolChangedException: 
The protocol version of the Delta table has been changed
```

**Solution**:
```python
# Re-leer la tabla
delta_table = DeltaTable.forPath(spark, path)

# O usar merge con retries
```

#### ❌ "No transaction log found"

**Yesntomas**:
```
AnalysisException: No transaction log found
```

**Solution**:
```bash
# Verificar que _delta_log/ existe
ls -la /path/to/table/_delta_log/

# Si no existe, la tabla no es Delta
# Convertir Parquet a Delta:
from delta.tables import DeltaTable
DeltaTable.convertToDelta(spark, "parquet.`/path/to/table`")
```

---

### 5. Schema Issues

#### ❌ "AnalysisException: A schema mismatch detected"

**Yesntomas**:
```
AnalysisException: A schema mismatch detected when writing to the Delta table
```

**Solution**:
```python
# Opción 1: Merge schema
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)

# Opción 2: Overwrite schema
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)
```

#### ❌ Type mismatch

**Yesntomas**:
```
Cannot safely cast 'amount': DoubleType to DecimalType(10,2)
```

**Solution**:
```python
from pyspark.sql.functions import col
from pyspark.sql.types import DecimalType

df = df.withColumn("amount", col("amount").cast(DecimalType(10, 2)))
```

---

### 6. Performance Issues

#### ❌ Queries muy lentos

**Diagnosis**:
```python
# Ver execution plan
df.explain(mode="formatted")

# Ver estadísticas
delta_table.detail().select("numFiles", "sizeInBytes").show()

# Ver history
delta_table.history().show()
```

**Soluciones**:

1. **OPTIMIZE** para small files:
```python
delta_table.optimize().executeCompaction()
```

2. **Z-ORDER** para data skipping:
```python
delta_table.optimize().executeZOrderBy("country", "date")
```

3. **Partition pruning**:
```python
# ✅ Bueno
df.filter("date = '2024-01-15'")

# ❌ Malo
df.filter(col("date") == lit("2024-01-15"))
```

4. **Cache small tables**:
```python
small_df.cache()
```

#### ❌ Writes muy lentos

**Solution**:
```python
# Repartition antes de escribir
df.repartition(100).write.format("delta").save(path)

# Ajustar tamaño de archivo
spark.conf.set("spark.sql.files.maxRecordsPerFile", 100000)
```

---

### 7. Path Issues

#### ❌ "Path does not exist"

**Yesntomas**:
```
AnalysisException: Path does not exist: s3a://bronze/table
```

**Solution**:
```bash
# Verificar bucket existe
docker exec minio mc ls local/

# Crear si no existe
docker exec minio mc mb local/bronze

# Verificar desde Python
import boto3
s3 = boto3.client('s3', 
    endpoint_url='http://localhost:9000',
    aws_access_key_id='admin',
    aws_secret_access_key='password123'
)
print(s3.list_buckets())
```

#### ❌ "URI scheme not recognized"

**Yesntomas**:
```
IllegalArgumentException: URI scheme is not 's3a'
```

**Solution**:
```python
# Usar s3a:// (no s3://)
path = "s3a://bronze/table"  # ✅ Correcto
# path = "s3://bronze/table"  # ❌ Incorrecto
```

---

### 8. Testing Issues

#### ❌ "pytest: command not found"

**Solution**:
```bash
pip install pytest pytest-cov
```

#### ❌ Tests fail con "No module named 'delta'"

**Solution**:
```bash
pip install delta-spark==3.0.0 pyspark==3.5.0
```

#### ❌ Tests timeout

**Solution**:
```bash
# Aumentar timeout
pytest --timeout=300 validation/
```

---

### 9. Cleanup Issues

#### ❌ "Unable to VACUUM due to retention"

**Yesntomas**:
```
IllegalArgumentException: requirement failed: 
Retention period must be at least 7 days
```

**Solution**:
```python
# Deshabilitar check (solo en desarrollo)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

# Ejecutar VACUUM
delta_table.vacuum(0)  # Borra TODO

# ⚠️ ADVERTENCIA: Esto elimina Time Travel
```

---

### 10. Data Quality Issues

#### ❌ Duplicados en Silver

**Diagnosis**:
```python
# Verificar duplicados
df.groupBy("transaction_id").count().filter("count > 1").show()
```

**Solution**:
```python
# Deduplicar por clave primaria
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window = Window.partitionBy("transaction_id").orderBy(col("timestamp").desc())
df_deduped = df.withColumn("rn", row_number().over(window)) \
    .filter("rn = 1") \
    .drop("rn")
```

#### ❌ Valores null inesperados

**Diagnosis**:
```python
# Contar nulls por columna
from pyspark.sql.functions import col, sum, when
df.select([
    sum(when(col(c).isNull(), 1).otherwise(0)).alias(c) 
    for c in df.columns
]).show()
```

**Solution**:
```python
# Filtrar nulls críticos
df = df.filter("amount IS NOT NULL AND timestamp IS NOT NULL")

# O rellenar con defaults
from pyspark.sql.functions import coalesce, lit
df = df.withColumn("status", coalesce(col("status"), lit("unknown")))
```

---

## 🆘 Getting Help

If neither solution works:

1. **Ver logs detallados**:
```bash
# Spark logs
docker logs spark-master

# MinIO logs
docker logs minio

# Todos los servicios
docker-compose logs -f
```

2. **Reset completo**:
```bash
# Parar todo
docker-compose down -v

# Limpiar datos
rm -rf data/*

# Re-setup
./scripts/setup.sh
```

3. **Verificar versiones**:
```bash
python --version  # Should be 3.9+
pip show pyspark  # Should be 3.5.0
pip show delta-spark  # Should be 3.0.0
docker --version  # Should be 20.10+
```

4. **Abrir issue en GitHub** con:
   - Problem description
   - Logs relevantes
   - Versiones de software
   - Comandos ejecutados
