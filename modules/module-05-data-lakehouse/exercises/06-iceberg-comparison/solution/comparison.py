"""Delta Lake vs Apache Iceberg Comparison"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import time

builder = SparkSession.builder.appName("Comparison") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension,org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.catalog.iceberg_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg_catalog.type", "hive") \
    .config("spark.sql.catalog.iceberg_catalog.uri", "thrift://hive-metastore:9083") \
    .config("spark.sql.catalog.iceberg_catalog.warehouse", "s3a://warehouse/iceberg")

spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Leer datos
df = spark.read.json("../../../data/raw/transactions.json").limit(10000)

# ========================================
# 1. DELTA LAKE
# ========================================
print("=" * 60)
print("🔷 DELTA LAKE")
print("=" * 60)

delta_path = "s3a://bronze/comparison_delta"

start = time.time()
df.write.format("delta").mode("overwrite").save(delta_path)
delta_write_time = time.time() - start

start = time.time()
delta_df = spark.read.format("delta").load(delta_path)
delta_count = delta_df.count()
delta_read_time = time.time() - start

print(f"✅ Write: {delta_write_time:.2f}s")
print(f"✅ Read: {delta_read_time:.2f}s")
print(f"✅ Count: {delta_count}")

# ========================================
# 2. APACHE ICEBERG
# ========================================
print("\n" + "=" * 60)
print("❄️  APACHE ICEBERG")
print("=" * 60)

start = time.time()
df.writeTo("iceberg_catalog.default.comparison_iceberg").using("iceberg").create()
iceberg_write_time = time.time() - start

start = time.time()
iceberg_df = spark.read.format("iceberg").load("iceberg_catalog.default.comparison_iceberg")
iceberg_count = iceberg_df.count()
iceberg_read_time = time.time() - start

print(f"✅ Write: {iceberg_write_time:.2f}s")
print(f"✅ Read: {iceberg_read_time:.2f}s")
print(f"✅ Count: {iceberg_count}")

# ========================================
# 3. COMPARACIÓN
# ========================================
print("\n" + "=" * 60)
print("📊 RESUMEN COMPARATIVO")
print("=" * 60)

print(f"""
| Métrica        | Delta Lake     | Apache Iceberg |
|----------------|----------------|----------------|
| Write Time     | {delta_write_time:.2f}s          | {iceberg_write_time:.2f}s            |
| Read Time      | {delta_read_time:.2f}s           | {iceberg_read_time:.2f}s             |
| Registros      | {delta_count:,}       | {iceberg_count:,}         |

💡 Ambos formatos proveen ACID y Time Travel
💡 Delta Lake: Mejor para Spark/Databricks ecosystem
💡 Iceberg: Mejor Para multi-engine (Trino, Presto, Flink)
""")

spark.stop()
