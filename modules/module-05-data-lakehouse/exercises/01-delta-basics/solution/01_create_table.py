"""
SOLUCIÓN - Tarea 1: Crear Tabla Delta Inicial

Esta es la solución completa para crear tu primera tabla Delta Lake.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, current_date
from delta import configure_spark_with_delta_pip

# 1. Crear SparkSession con Delta Lake
builder = SparkSession.builder \
    .appName("Delta Lake - Create Table") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado con Delta Lake\n")

# 2. Leer datos de transacciones (primeras 10,000 filas)
data_path = "../../../data/raw/transactions.json"
df_raw = spark.read.json(data_path).limit(10000)

print(f"📊 Filas leídas: {df_raw.count()}")
print("\n📋 Schema original:")
df_raw.printSchema()

# 3. Convertir timestamp string a timestamp type
df_transformed = df_raw.withColumn(
    "timestamp",
    to_timestamp(col("timestamp"))
)

# 4. Agregar columna ingestion_date con la fecha actual
df_transformed = df_transformed.withColumn(
    "ingestion_date",
    current_date()
)

print("\n📋 Schema transformado:")
df_transformed.printSchema()

# Mostrar algunos registros
print("\n🔍 Muestra de datos:")
df_transformed.select(
    "transaction_id", 
    "country", 
    "amount", 
    "currency",
    "timestamp", 
    "ingestion_date"
).show(10, truncate=False)

# 5. Guardar como tabla Delta particionada por país
delta_path = "s3a://bronze/transactions_delta"

print(f"\n💾 Guardando tabla Delta en: {delta_path}")

df_transformed.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("country") \
    .save(delta_path)

print("✅ Tabla Delta creada exitosamente!")

# Verificación: Leer la tabla recién creada
print("\n🔍 Verificando tabla creada...")
delta_df = spark.read.format("delta").load(delta_path)

total_records = delta_df.count()
num_countries = delta_df.select('country').distinct().count()

print(f"📊 Total de registros en tabla Delta: {total_records}")
print(f"📊 Particiones (países): {num_countries}")

# Mostrar distribución por país
print("\n📊 Distribución por país:")
delta_df.groupBy("country") \
    .count() \
    .orderBy(col("count").desc()) \
    .show(10)

# Verificar estructura del transaction log
print("\n📁 Verificación completa:")
print("✅ Tabla Delta creada con éxito")
print("✅ Particionamiento por país aplicado")
print("✅ Transaction log inicializado")
print("\n💡 La tabla ahora tiene:")
print("   - Directorio _delta_log/ con el transaction log")
print("   - Subdirectorios country=XXX/ para cada país")
print("   - Archivos Parquet con los datos")

spark.stop()
