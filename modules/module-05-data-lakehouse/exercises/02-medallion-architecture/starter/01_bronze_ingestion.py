"""
Tarea 1: Bronze Layer - Ingestión Cruda

TODOs:
1. Leer TODOS los registros de transactions.json
2. Agregar metadata: ingestion_timestamp, source_file, ingestion_date
3. Guardar en Bronze SIN aplicar limpieza
4. Particionar por ingestion_date
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit, to_date
from delta import configure_spark_with_delta_pip

# Crear SparkSession
builder = SparkSession.builder \
    .appName("Medallion - Bronze Ingestion") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado\n")

# TODO 1: Leer TODOS los registros del JSON
data_path = "../../../data/raw/transactions.json"
df_raw = None  # COMPLETAR: spark.read.json(data_path)

print(f"📊 Total de registros a ingestar: {df_raw.count()}")

# TODO 2: Agregar metadata de ingestión
# - ingestion_timestamp: current_timestamp()
# - source_file: lit("transactions.json")
# - ingestion_date: to_date(ingestion_timestamp)

df_bronze = df_raw  # COMPLETAR: Agregar las 3 columnas de metadata

print("\n📋 Schema Bronze:")
df_bronze.printSchema()

# TODO 3: Guardar en Bronze como Delta
# Ruta: s3a://bronze/transactions_medallion
# Modo: append (Bronze es append-only)
# Partición: ingestion_date

bronze_path = "s3a://bronze/transactions_medallion"

# COMPLETAR: Escribir a Bronze
# df_bronze.write...

print(f"\n✅ Datos ingastados a Bronze: {bronze_path}")

# Verificación
bronze_df = spark.read.format("delta").load(bronze_path)
print(f"📊 Total en Bronze: {bronze_df.count()}")
print(f"📅 Fechas de ingestión: {bronze_df.select('ingestion_date').distinct().count()}")

print("\n🥉 BRONZE LAYER CARACTERÍSTICAS:")
print("   ✅ Append-only (nunca sobrescribir)")
print("   ✅ Datos crudos preservados")
print("   ✅ Metadata de ingestión agregada")
print("   ✅ Incluye duplicados y errores")

spark.stop()
