"""
Tarea 1: Crear Tabla Delta Inicial

Objetivo:
- Leer transacciones desde JSON
- Transformar datos y agregar metadata
- Guardar como tabla Delta particionada por país

TODOs:
1. Configurar SparkSession con Delta Lake
2. Leer datos desde data/raw/transactions.json (primeras 10K filas)
3. Convertir campo timestamp a timestamp type
4. Agregar columna ingestion_date con fecha actual
5. Guardar como tabla Delta en s3a://bronze/transactions_delta
6. Particionar por 'country'
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, current_date
from delta import configure_spark_with_delta_pip

# TODO 1: Crear SparkSession con configuración Delta Lake
# Hint: Usa configure_spark_with_delta_pip() para configurar Delta
spark = None  # COMPLETAR: Inicializar Spark con Delta

print("✅ Spark session creado con Delta Lake")

# TODO 2: Leer datos de transacciones (primeras 10,000 filas)
# Archivo: ../../../data/raw/transactions.json
df_raw = None  # COMPLETAR: Leer JSON limitando a 10,000 filas

print(f"📊 Filas leídas: {df_raw.count()}")
print("\n📋 Schema original:")
df_raw.printSchema()

# TODO 3: Convertir timestamp string a timestamp type
# El campo 'timestamp' viene como string, conviértelo a TimestampType
df_transformed = df_raw  # COMPLETAR: Usar to_timestamp() en la columna 'timestamp'

# TODO 4: Agregar columna ingestion_date con la fecha actual
# Hint: Usa current_date() function
df_transformed = df_transformed  # COMPLETAR: Agregar columna ingestion_date

print("\n📋 Schema transformado:")
df_transformed.printSchema()

# Mostrar algunos registros
print("\n🔍 Muestra de datos:")
df_transformed.select("transaction_id", "country", "amount", "timestamp", "ingestion_date") \
    .show(10, truncate=False)

# TODO 5: Guardar como tabla Delta particionada por país
# Ruta: s3a://bronze/transactions_delta
# Formato: delta
# Modo: overwrite (primera vez)
# Partición: country

# COMPLETAR: Guardar DataFrame como Delta
# df_transformed.write...

print("\n✅ Tabla Delta creada exitosamente!")

# Verificación: Leer la tabla recién creada
print("\n🔍 Verificando tabla creada...")
delta_df = spark.read.format("delta").load("s3a://bronze/transactions_delta")

print(f"Total de registros en tabla Delta: {delta_df.count()}")
print(f"Particiones (países): {delta_df.select('country').distinct().count()}")

# Mostrar distribución por país
print("\n📊 Distribución por país:")
delta_df.groupBy("country").count().orderBy(col("count").desc()).show(10)

# Verificar estructura de directorios
print("\n📁 Estructura de la tabla Delta:")
print("Deberías ver carpetas como: country=USA/, country=GBR/, etc.")
print("Además de _delta_log/ con el transaction log")

spark.stop()
