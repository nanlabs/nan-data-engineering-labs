"""
SOLUCIÓN - Tarea 3: Sobrescribir Partición Específica

Esta solución demuestra cómo usar replaceWhere para sobrescribir 
solo una partición sin afectar las demás.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

# Crear SparkSession
builder = SparkSession.builder \
    .appName("Delta Lake - Overwrite Partition") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado\n")

# País a modificar
TARGET_COUNTRY = "USA"
delta_path = "s3a://bronze/transactions_delta"

print(f"🎯 Objetivo: Sobrescribir partición de {TARGET_COUNTRY}\n")

# 1. Leer datos actuales de la tabla Delta
df_original = spark.read.format("delta").load(delta_path)

total_before = df_original.count()
print(f"📊 Total de registros antes: {total_before}")

# Contar registros del país objetivo ANTES
count_target_before = df_original.filter(col("country") == TARGET_COUNTRY).count()
print(f"📊 Registros de {TARGET_COUNTRY} antes: {count_target_before}")

# Contar registros con status="pending" en USA
pending_usa_before = df_original \
    .filter((col("country") == TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()
print(f"📊 Transacciones 'pending' en {TARGET_COUNTRY}: {pending_usa_before}")

# Guardar conteo de pending en otros países para verificar después
pending_others_before = df_original \
    .filter((col("country") != TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()
print(f"📊 Transacciones 'pending' en otros países: {pending_others_before}\n")

# 2. Filtrar datos del país objetivo y modificar
df_usa = df_original.filter(col("country") == TARGET_COUNTRY)

# Modificar el status: "pending" -> "expired"
df_usa_modified = df_usa.withColumn(
    "status",
    when(col("status") == "pending", "expired")
    .otherwise(col("status"))
)

print("🔍 Muestra de datos modificados (primeras 10 filas):")
df_usa_modified.select("transaction_id", "country", "status", "amount") \
    .show(10, truncate=False)

# Contar cuántos cambios hicimos
expired_count = df_usa_modified.filter(col("status") == "expired").count()
print(f"\n📊 Transacciones marcadas como 'expired': {expired_count}")

# 3. Sobrescribir SOLO la partición de USA
print(f"\n💾 Sobrescribiendo partición de {TARGET_COUNTRY}...")

df_usa_modified.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", f"country = '{TARGET_COUNTRY}'") \
    .save(delta_path)

print(f"✅ Partición de {TARGET_COUNTRY} sobrescrita\n")

# 4. Verificar que solo USA cambió
print("🔍 Verificando resultados...")

df_after = spark.read.format("delta").load(delta_path)

# El total de registros debe ser el mismo
total_after = df_after.count()
print(f"📊 Total de registros después: {total_after}")
assert total_after == total_before, f"❌ Error: Total cambió de {total_before} a {total_after}"
print("✅ Total de registros sin cambios")

# Registros de USA deben ser los mismos
count_target_after = df_after.filter(col("country") == TARGET_COUNTRY).count()
print(f"📊 Registros de {TARGET_COUNTRY} después: {count_target_after}")
assert count_target_after == count_target_before, f"❌ Error: Registros de USA cambiaron"
print(f"✅ Número de registros de {TARGET_COUNTRY} sin cambios")

# Ya no debe haber registros "pending" en USA
pending_usa_after = df_after \
    .filter((col("country") == TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()
print(f"📊 Transacciones 'pending' en {TARGET_COUNTRY} después: {pending_usa_after}")
assert pending_usa_after == 0, f"❌ Error: Todavía hay {pending_usa_after} pending en USA"
print(f"✅ Todos los 'pending' de {TARGET_COUNTRY} fueron cambiados a 'expired'")

# Verificar que otros países no cambiaron
pending_others_after = df_after \
    .filter((col("country") != TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()
print(f"📊 Transacciones 'pending' en otros países después: {pending_others_after}")
assert pending_others_after == pending_others_before, "❌ Error: Otros países fueron afectados"
print("✅ Otros países permanecen intactos")

# Verificar distribución de status en USA
print(f"\n📊 Distribución de status en {TARGET_COUNTRY} después:")
df_after.filter(col("country") == TARGET_COUNTRY) \
    .groupBy("status") \
    .count() \
    .orderBy(col("count").desc()) \
    .show()

# Verificar historial
print("\n📜 Historial de versiones:")
delta_table = DeltaTable.forPath(spark, delta_path)
history = delta_table.history()

print(f"📊 Total de versiones: {history.count()}")
history.select(
    "version",
    "timestamp", 
    "operation",
    "operationMetrics.numFiles",
    "operationMetrics.numOutputRows",
    "operationParameters.predicate"
).show(10, truncate=False)

print("\n✅ ÉXITO: Sobrescritura de partición completada correctamente!")
print(f"✅ Solo {TARGET_COUNTRY} fue modificada")
print("✅ Otras particiones permanecen intactas")
print("✅ Transaction log actualizado con nueva versión")

print("\n💡 Puntos clave aprendidos:")
print("   - replaceWhere permite sobrescribir particiones específicas")
print("   - Mucho más eficiente que sobrescribir toda la tabla")
print("   - Operación ACID - todo o nada")
print("   - Otras particiones nunca son tocadas")

spark.stop()
