"""
Tarea 3: Sobrescribir Partición Específica

Objetivo:
- Modificar datos de un país específico (ej: USA)
- Sobrescribir SOLO esa partición
- Verificar que otras particiones no se afectaron

TODOs:
1. Leer datos actuales del país "USA"
2. Modificar el campo 'status' de "pending" a "expired"
3. Sobrescribir solo la partición de USA usando replaceWhere
4. Verificar que otras particiones permanecen intactas
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
print("✅ Spark session creado")

# País a modificar
TARGET_COUNTRY = "USA"

print(f"\n🎯 Objetivo: Sobrescribir partición de {TARGET_COUNTRY}")

# TODO 1: Leer datos actuales de la tabla Delta
delta_path = "s3a://bronze/transactions_delta"
df_original = spark.read.format("delta").load(delta_path)

print(f"📊 Total de registros antes: {df_original.count()}")

# Contar registros del país objetivo ANTES de la modificación
count_target_before = df_original.filter(col("country") == TARGET_COUNTRY).count()
print(f"📊 Registros de {TARGET_COUNTRY} antes: {count_target_before}")

# Contar registros con status="pending" en USA
pending_usa_before = df_original \
    .filter((col("country") == TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()
print(f"📊 Transacciones 'pending' en {TARGET_COUNTRY}: {pending_usa_before}")

# TODO 2: Filtrar datos del país objetivo y modificar
# Lee solo datos de USA
df_usa = df_original.filter(col("country") == TARGET_COUNTRY)

# Modifica el status: "pending" -> "expired"
# COMPLETAR: Usa when() para cambiar pending a expired
df_usa_modified = None  # COMPLETAR: Cambiar status de pending a expired

print("\n🔍 Muestra de datos modificados:")
df_usa_modified.select("transaction_id", "country", "status", "amount") \
    .show(10)

# TODO 3: Sobrescribir SOLO la partición de USA
# Usa .mode("overwrite") con .option("replaceWhere", "country = 'USA'")
# Esto sobrescribe solo USA sin tocar otras particiones

print(f"\n💾 Sobrescribiendo partición de {TARGET_COUNTRY}...")

# COMPLETAR: Escribir con replaceWhere
# df_usa_modified.write...

print(f"✅ Partición de {TARGET_COUNTRY} sobrescrita")

# TODO 4: Verificar que solo USA cambió
print("\n🔍 Verificando resultados...")

df_after = spark.read.format("delta").load(delta_path)

# El total de registros debe ser el mismo
total_after = df_after.count()
print(f"📊 Total de registros después: {total_after}")
assert total_after == df_original.count(), "❌ Error: Total de registros cambió"

# Registros de USA deben ser los mismos
count_target_after = df_after.filter(col("country") == TARGET_COUNTRY).count()
print(f"📊 Registros de {TARGET_COUNTRY} después: {count_target_after}")
assert count_target_after == count_target_before, "❌ Error: Número de registros de USA cambió"

# Ya no debe haber registros "pending" en USA
pending_usa_after = df_after \
    .filter((col("country") == TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()
print(f"📊 Transacciones 'pending' en {TARGET_COUNTRY} después: {pending_usa_after}")
assert pending_usa_after == 0, "❌ Error: Todavía hay registros pending en USA"

# Verificar que otros países no cambiaron
print("\n🔍 Verificando que otros países permanecen intactos...")
other_countries = df_after.filter(col("country") != TARGET_COUNTRY)
pending_others_after = other_countries.filter(col("status") == "pending").count()

pending_others_before = df_original \
    .filter((col("country") != TARGET_COUNTRY) & (col("status") == "pending")) \
    .count()

print(f"📊 Transacciones 'pending' en otros países: {pending_others_after} (antes: {pending_others_before})")
assert pending_others_after == pending_others_before, "❌ Error: Otros países fueron afectados"

# Verificar historial
print("\n📜 Historial de versiones:")
delta_table = DeltaTable.forPath(spark, delta_path)
history = delta_table.history()
history.select("version", "operation", "operationMetrics.numFiles", "operationMetrics.numOutputRows") \
    .show(10, truncate=False)

# Debe haber al menos 3 versiones ahora
assert history.count() >= 3, "❌ Error: Debe haber al menos 3 versiones (create, append, overwrite)"

print("\n✅ Sobrescritura de partición exitosa!")
print(f"✅ Solo {TARGET_COUNTRY} fue modificada")
print("✅ Otras particiones permanecen intactas")

spark.stop()
