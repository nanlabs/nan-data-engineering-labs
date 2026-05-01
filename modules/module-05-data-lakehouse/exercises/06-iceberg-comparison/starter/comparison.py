"""Delta Lake vs Apache Iceberg Comparison

📝 OBJETIVO:
Comparar Delta Lake y Apache Iceberg en términos de performance, features y uso

✅ TAREAS:
1. Crear tabla Delta Lake y medir performance
2. Crear tabla Apache Iceberg y medir performance
3. Comparar write/read times
4. Analizar diferencias y casos de uso

💡 PISTA: Ambos requieren configuración específica en SparkSession
"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import time

# Configurar Spark con Delta Lake + Iceberg
builder = SparkSession.builder.appName("Comparison") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension,org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.catalog.iceberg_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg_catalog.type", "hive") \
    .config("spark.sql.catalog.iceberg_catalog.uri", "thrift://hive-metastore:9083") \
    .config("spark.sql.catalog.iceberg_catalog.warehouse", "s3a://warehouse/iceberg")

spark = configure_spark_with_delta_pip(builder).getOrCreate()

# TODO: Leer datos de prueba
print("📊 Leyendo datos de prueba...")
# df = spark.read.json("../../../data/raw/transactions.json").limit(10000)


# ========================================
# TODO: 1. DELTA LAKE
# ========================================
print("\n" + "=" * 60)
print("🔷 DELTA LAKE")
print("=" * 60)

delta_path = "s3a://bronze/comparison_delta"

# HINT: Medir tiempo de escritura
# start = time.time()
# df.write.format("delta").mode("overwrite").save(delta_path)
# delta_write_time = time.time() - start

# HINT: Medir tiempo de lectura
# start = time.time()
# delta_df = spark.read.format("delta").load(delta_path)
# delta_count = delta_df.count()
# delta_read_time = time.time() - start

# print(f"✅ Write: {delta_write_time:.2f}s")
# print(f"✅ Read: {delta_read_time:.2f}s")
# print(f"✅ Count: {delta_count}")


# ========================================
# TODO: 2. APACHE ICEBERG
# ========================================
print("\n" + "=" * 60)
print("❄️  APACHE ICEBERG")
print("=" * 60)

# HINT: Iceberg usa .writeTo() y .using("iceberg")
# start = time.time()
# df.writeTo("iceberg_catalog.default.comparison_iceberg").using("iceberg").create()
# iceberg_write_time = time.time() - start

# HINT: Leer tabla Iceberg
# start = time.time()
# iceberg_df = spark.read.format("iceberg").load("iceberg_catalog.default.comparison_iceberg")
# iceberg_count = iceberg_df.count()
# iceberg_read_time = time.time() - start

# print(f"✅ Write: {iceberg_write_time:.2f}s")
# print(f"✅ Read: {iceberg_read_time:.2f}s")
# print(f"✅ Count: {iceberg_count}")


# ========================================
# TODO: 3. COMPARACIÓN
# ========================================
print("\n" + "=" * 60)
print("📊 RESUMEN COMPARATIVO")
print("=" * 60)

# TODO: Imprimir tabla comparativa
# print(f"""
# | Métrica        | Delta Lake     | Apache Iceberg |
# |----------------|----------------|----------------|
# | Write Time     | {delta_write_time:.2f}s          | {iceberg_write_time:.2f}s            |
# | Read Time      | {delta_read_time:.2f}s           | {iceberg_read_time:.2f}s             |
# | Registros      | {delta_count:,}       | {iceberg_count:,}         |
# """)

print("""
💡 KEY DIFFERENCES:

🔷 Delta Lake:
- Optimizado para Spark/Databricks
- Transaction log basado en JSON
- Excelente para Spark workloads
- Menor overhead en metadata

❄️  Apache Iceberg:
- Multi-engine (Spark, Flink, Trino, Presto)
- Metadata basado en Avro
- Hidden partitioning (evolución automática)
- Mejor para entornos heterogéneos

🎯 Cuándo usar cada uno:
- Delta Lake → Ecosistema Spark/Databricks
- Iceberg → Multi-engine o migración de Hive
""")

spark.stop()
