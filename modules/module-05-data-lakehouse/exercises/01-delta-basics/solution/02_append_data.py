"""
SOLUCIÓN - Tarea 2: Agregar Nuevos Registros (Append)

Esta solución muestra cómo hacer append de datos a una tabla Delta existente.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, current_date, row_number
from pyspark.sql.window import Window
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

# Crear SparkSession
builder = SparkSession.builder \
    .appName("Delta Lake - Append Data") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado\n")

# 1. Leer el siguiente lote de transacciones (filas 10,000 a 15,000)
data_path = "../../../data/raw/transactions.json"
df_all = spark.read.json(data_path)

# Opción 1: Usando window function (más robusto)
window = Window.orderBy("transaction_id")
df_numbered = df_all.withColumn("row_num", row_number().over(window))
df_new = df_numbered \
    .filter((col("row_num") > 10000) & (col("row_num") <= 15000)) \
    .drop("row_num")

print(f"📊 Nuevas filas a agregar: {df_new.count()}")

# 2. Aplicar las mismas transformaciones
df_transformed = df_new.withColumn(
    "timestamp",
    to_timestamp(col("timestamp"))
).withColumn(
    "ingestion_date",
    current_date()
)

print("\n🔍 Muestra de nuevos datos:")
df_transformed.select(
    "transaction_id", 
    "country", 
    "amount", 
    "timestamp", 
    "ingestion_date"
).show(5, truncate=False)

# 3. Hacer append a la tabla Delta existente
delta_path = "s3a://bronze/transactions_delta"

print(f"\n💾 Haciendo append a: {delta_path}")

df_transformed.write \
    .format("delta") \
    .mode("append") \
    .save(delta_path)

print("✅ Datos agregados exitosamente!")

# 4. Verificar que el total sea 15,000
print("\n🔍 Verificando resultados...")
delta_df = spark.read.format("delta").load(delta_path)

total_registros = delta_df.count()
print(f"📊 Total de registros después del append: {total_registros}")

if total_registros == 15000:
    print("✅ Validación exitosa: 15,000 registros en la tabla")
else:
    print(f"⚠️  Advertencia: Esperaba 15,000 registros, pero hay {total_registros}")

# Verificar historial de versiones
print("\n📜 Historial de la tabla Delta:")
delta_table = DeltaTable.forPath(spark, delta_path)
history = delta_table.history()

print(f"📊 Número de versiones: {history.count()}")
history.select(
    "version", 
    "timestamp",
    "operation", 
    "operationMetrics.numFiles",
    "operationMetrics.numOutputRows"
).show(truncate=False)

# Verificar distribución por país después del append
print("\n📊 Distribución por país después del append:")
delta_df.groupBy("country") \
    .count() \
    .orderBy(col("count").desc()) \
    .show(10)

print("\n✅ Append completado correctamente!")
print("💡 La tabla ahora tiene:")
print(f"   - {history.count()} versiones en el transaction log")
print(f"   - {total_registros} registros totales")
print("   - Manteniendo el mismo esquema y particionamiento")

spark.stop()
