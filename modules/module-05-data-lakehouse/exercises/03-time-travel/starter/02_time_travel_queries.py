"""Time Travel Queries

📝 OBJETIVO:
Consultar versiones históricas de una tabla Delta usando versionAsOf y timestampAsOf

✅ TAREAS:
1. Leer V0 (versión original)
2. Leer V3 (versión actual)
3. Comparar diferencias
4. Query por timestamp
5. Usar SQL Time Travel

💡 PISTA: .option("versionAsOf", N) o .option("timestampAsOf", "timestamp")
"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("TimeTravel") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/time_travel_demo"

# TODO: Leer V0 (versión original)
print("📊 V0 (original):")
# HINT: .option("versionAsOf", 0)
# v0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
# print(f"Total: {v0.count()}")


# TODO: Leer V3 (versión actual)
print("\n📊 V3 (actual):")
# v3 = spark.read.format("delta").load(path)
# print(f"Total: {v3.count()}")


# TODO: Comparar diferencias
print(f"\n📊 Diferencia V0 vs V3:")
# print(f"Registros eliminados: {v0.count() - v3.count()}")


# TODO: Query por timestamp
print("\n📊 Query por timestamp:")
# HINT: Obtén el timestamp de V1 del history()
# delta_table = DeltaTable.forPath(spark, path)
# history = delta_table.history().collect()
# v1_timestamp = history[-2]['timestamp']
# df_v1 = spark.read.format("delta").option("timestampAsOf", str(v1_timestamp)).load(path)


# TODO: SQL Time Travel
print("\n📊 SQL Time Travel:")
# HINT: CREATE OR REPLACE TEMP VIEW y luego usa VERSION AS OF en SQL
# spark.read.format("delta").load(path).createOrReplaceTempView("demo")
# spark.sql("SELECT COUNT(*) FROM demo VERSION AS OF 0").show()


spark.stop()
