"""Crear múltiples versiones de una tabla Delta

📝 OBJETIVO:
Crear una tabla Delta y realizar múltiples operaciones para generar versiones históricas

✅ TAREAS:
1. Crear tabla inicial (V0) con 10K registros
2. Append más datos (V1) 
3. Update registros con status='pending' → 'expired' (V2)
4. Delete registros inválidos (amount < 0) (V3)
5. Ver historial de versiones

💡 PISTA: Usa DeltaTable.forPath() para operaciones de update/delete
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, current_timestamp
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

# Crear Spark session con Delta Lake
builder = SparkSession.builder.appName("TimeTravel") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/time_travel_demo"

# TODO: V0 - Crear tabla inicial con 10K registros
print("📝 V0: Crear tabla inicial")
# HINT: usa .limit(10000) al leer el JSON
# df = spark.read.json("...").limit(...)
# df.write.format("delta").mode("overwrite").save(path)

# TODO: Verificar cantidad de registros
# v0_count = spark.read.format("delta").load(path).count()
# print(f"✅ V0: {v0_count} registros")


# TODO: V1 - Append datos nuevos
print("\n📝 V1: Append datos")
# HINT: Lee 15K registros y usa .subtract() para obtener los 5K nuevos
# df_new = spark.read.json("...").limit(15000).subtract(df.limit(10000))
# df_new.write.format("delta").mode("append").save(path)


# TODO: V2 - Update status
print("\n📝 V2: Update status")
# HINT: usa DeltaTable.forPath(spark, path) y luego .update()
# delta_table = DeltaTable.forPath(...)
# delta_table.update(condition="...", set={"status": "..."})


# TODO: V3 - Delete registros inválidos
print("\n📝 V3: Delete inválidos")
# HINT: delta_table.delete("amount < 0 OR amount IS NULL")


# TODO: Mostrar historial de versiones
print("\n📜 HISTORIAL DE VERSIONES:")
# HINT: delta_table.history().select("version", "timestamp", "operation", "operationMetrics").show(truncate=False)


spark.stop()
