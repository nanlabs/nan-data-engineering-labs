"""Crear múltiples versiones de una tabla Delta"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, current_timestamp
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("TimeTravel").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/time_travel_demo"

# V0: Create
print("📝 V0: Crear tabla inicial")
df = spark.read.json("../../../data/raw/transactions.json").limit(10000)
df.write.format("delta").mode("overwrite").save(path)
print(f"✅ V0: {spark.read.format('delta').load(path).count()} registros")

# V1: Append
print("\n📝 V1: Append datos")
df_new = spark.read.json("../../../data/raw/transactions.json").limit(15000).subtract(df.limit(10000))
df_new.write.format("delta").mode("append").save(path)
print(f"✅ V1: {spark.read.format('delta').load(path).count()} registros")

# V2: Update
print("\n📝 V2: Update status")
delta_table = DeltaTable.forPath(spark, path)
delta_table.update(condition="status = 'pending'", set={"status": "'expired'"})
expired_count = spark.read.format("delta").load(path).filter("status='expired'").count()
print(f"✅ V2: {expired_count} marcados como expired")

# V3: Delete
print("\n📝 V3: Delete inválidos")
delta_table.delete("amount < 0 OR amount IS NULL")
final_count = spark.read.format("delta").load(path).count()
print(f"✅ V3: {final_count} registros finales")

# Historial
print("\n📜 HISTORIAL DE VERSIONES:")
delta_table.history().select("version", "timestamp", "operation", "operationMetrics").show(truncate=False)

spark.stop()
