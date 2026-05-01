"""
Tarea 2: Silver Layer - Limpieza y Validación

TODOs:
1. Leer tabla Bronze
2. Remover duplicados por transaction_id
3. Filtrar registros inválidos (amount NULL/negativo, timestamp NULL)
4. Normalizar status y currency
5. Agregar columnas de validación
6. Convertir tipos correctos
7. Guardar en Silver particionado por country y date
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lower, trim, upper, to_date, 
    when, array, lit, concat_ws
)
from pyspark.sql.types import DecimalType, TimestampType
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder \
    .appName("Medallion - Silver Cleaning") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado\n")

# TODO 1: Leer tabla Bronze
bronze_path = "s3a://bronze/transactions_medallion"
df_bronze = None  # COMPLETAR: Leer desde Bronze

print(f"📊 Registros en Bronze: {df_bronze.count()}")

# TODO 2: Remover duplicados basados en transaction_id
# Hint: Usa dropDuplicates(["transaction_id"])
df_dedup = df_bronze  # COMPLETAR

duplicates_removed = df_bronze.count() - df_dedup.count()
print(f"🗑️  Duplicados removidos: {duplicates_removed}")

# TODO 3: Filtrar registros inválidos
# Condiciones:
# - amount no debe ser NULL ni negativo
# - timestamp no debe ser NULL

df_valid = df_dedup  # COMPLETAR: Filtrar registros válidos

invalid_removed = df_dedup.count() - df_valid.count()
print(f"❌ Registros inválidos removidos: {invalid_removed}")

# TODO 4: Normalizar campos
# - status: lowercase y trimmed
# - currency: uppercase

df_normalized = df_valid  # COMPLETAR: Normalizar status y currency

# TODO 5: Agregar columnas de validación
# - is_valid: true (todos los que llegaron aquí son válidos)
# - date: to_date(timestamp) para particionamiento

df_silver = df_normalized  # COMPLETAR: Agregar is_valid y date

# TODO 6: Convertir tipos correctos
# - amount: cast a DecimalType(10, 2)
# - timestamp: cast a TimestampType (si no lo está ya)

# COMPLETAR: Cast de tipos

print("\n📋 Schema Silver:")
df_silver.printSchema()

# TODO 7: Guardar en Silver
# Ruta: s3a://silver/transactions_clean
# Modo: overwrite (para este ejercicio, en producción sería merge)
# Partición: country, date

silver_path = "s3a://silver/transactions_clean"

# COMPLETAR: Escribir a Silver

print(f"\n✅ Datos limpiados y guardados en Silver: {silver_path}")

# Verificación
silver_df = spark.read.format("delta").load(silver_path)
total_silver = silver_df.count()
print(f"📊 Total en Silver: {total_silver}")

# Calidad de datos
quality_rate = (total_silver / df_bronze.count()) * 100
print(f"📈 Tasa de calidad: {quality_rate:.1f}%")

print("\n🥈 SILVER LAYER CARACTERÍSTICAS:")
print("   ✅ Deduplicated")
print("   ✅ Validated")
print("   ✅ Strongly typed")
print("   ✅ Normalized")
print("   ✅ Ready for analytics")

spark.stop()
