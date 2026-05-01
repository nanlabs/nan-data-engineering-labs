"""Time Travel Queries"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("TimeTravel").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/time_travel_demo"

# Leer versiones específicas
print("📊 V0 (original):")
v0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
print(f"Total: {v0.count()}")

print("\n📊 V3 (actual):")
v3 = spark.read.format("delta").load(path)
print(f"Total: {v3.count()}")

# Comparar
print(f"\n📊 Registros borrados entre V0 y V3: {v0.count() - v3.count()}")

# Query por timestamp
from delta.tables import DeltaTable
delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history().collect()
if len(history) > 1:
    v1_timestamp = history[-2]['timestamp']
    df_v1 = spark.read.format("delta").option("timestampAsOf", str(v1_timestamp)).load(path)
    print(f"\n📊 V1 (por timestamp): {df_v1.count()} registros")

# SQL Time Travel
spark.read.format("delta").load(path).createOrReplaceTempView("demo")
spark.sql("SELECT COUNT(*) FROM demo VERSION AS OF 0").show()

spark.stop()
