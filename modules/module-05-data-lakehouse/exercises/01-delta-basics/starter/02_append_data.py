"""
Tarea 2: Agregar Nuevos Registros (Append)

Objetivo:
- Leer el siguiente lote de transacciones
- Procesarlas igual que en Tarea 1
- Agregarlas a la tabla Delta existente sin duplicar datos

TODOs:
1. Leer transacciones desde la fila 10,000 hasta 15,000
2. Aplicar las mismas transformaciones (timestamp, ingestion_date)
3. Hacer append a la tabla Delta existente
4. Verificar que el total sea 15,000 registros
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, current_date
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

# Crear SparkSession
builder = SparkSession.builder \
    .appName("Delta Lake - Append Data") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado")

# TODO 1: Leer el siguiente lote de transacciones
# Lee desde la fila 10,000 hasta la 15,000 (5,000 registros)
# Hint: Primero lee todo el JSON, luego usa limit() y skip con SQL

df_all = spark.read.json("../../../data/raw/transactions.json")
df_all.createOrReplaceTempView("all_transactions")

# COMPLETAR: Seleccionar filas 10,000 a 15,000
# Hint: Puedes usar ROW_NUMBER() window function o simplemente limit(15000) y luego skip las primeras 10,000
df_new = None  # COMPLETAR

print(f"📊 Nuevas filas a agregar: {df_new.count()}")

# TODO 2: Aplicar transformaciones
# Convierte timestamp y agrega ingestion_date (igual que en Tarea 1)
df_transformed = None  # COMPLETAR: Aplicar to_timestamp() y current_date()

print("\n🔍 Muestra de nuevos datos:")
df_transformed.select("transaction_id", "country", "amount", "timestamp", "ingestion_date") \
    .show(5)

# TODO 3: Hacer append a la tabla Delta existente
# Ruta: s3a://bronze/transactions_delta
# Modo: append
# Particionar por: country (debe coincidir con partición existente)

# COMPLETAR: Escribir en modo append
# df_transformed.write...

print("\n✅ Datos agregados exitosamente!")

# TODO 4: Verificar que el total sea 15,000
print("\n🔍 Verificando resultados...")
delta_df = spark.read.format("delta").load("s3a://bronze/transactions_delta")

total_registros = delta_df.count()
print(f"Total de registros después del append: {total_registros}")

# Debe ser 15,000
assert total_registros == 15000, f"❌ Error: Esperaba 15,000 registros, pero hay {total_registros}"

print("✅ Validación exitosa: 15,000 registros en la tabla")

# Verificar historial de versiones
print("\n📜 Historial de la tabla Delta:")
delta_table = DeltaTable.forPath(spark, "s3a://bronze/transactions_delta")
history = delta_table.history()

print(f"Número de versiones: {history.count()}")
history.select("version", "operation", "operationMetrics").show(truncate=False)

# Debe tener 2 versiones: CREATE (v0) y APPEND (v1)
assert history.count() >= 2, "❌ Error: Debe haber al menos 2 versiones"

print("\n✅ Append completado correctamente!")

spark.stop()
