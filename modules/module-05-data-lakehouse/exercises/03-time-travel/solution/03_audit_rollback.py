"""Rollback a versión anterior"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("Rollback").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/time_travel_demo"
delta_table = DeltaTable.forPath(spark, path)

# Ver historial
print("📜 Historial antes del rollback:")
history = delta_table.history()
history.select("version", "operation", "operationMetrics").show(truncate=False)

current_count = spark.read.format("delta").load(path).count()
print(f"\n📊 Registros actuales: {current_count}")

# Rollback a V1
print("\n🔄 Haciendo rollback a V1...")
v1_df = spark.read.format("delta").option("versionAsOf", 1).load(path)
v1_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)

# Verificar
after_rollback = spark.read.format("delta").load(path).count()
print(f"✅ Después del rollback: {after_rollback} registros")

print("\n📜 Nuevo historial:")
delta_table = DeltaTable.forPath(spark, path)
delta_table.history().select("version", "operation").show(5, truncate=False)

spark.stop()
