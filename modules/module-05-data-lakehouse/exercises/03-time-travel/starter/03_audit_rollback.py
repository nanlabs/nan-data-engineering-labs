"""Audit y Rollback

📝 OBJETIVO:
Ver historial completo y hacer rollback a una versión anterior

✅ TAREAS:
1. Ver historial de todas las operaciones
2. Contar registros actuales
3. Hacer rollback a V1
4. Verificar el rollback
5. Ver nuevo historial

💡 PISTA: El rollback se hace leyendo la versión antigua y escribiendo con mode="overwrite"
"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("Rollback") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/time_travel_demo"

# TODO: Ver historial completo
print("📜 Historial antes del rollback:")
# delta_table = DeltaTable.forPath(spark, path)
# history = delta_table.history()
# history.select("version", "operation", "operationMetrics").show(truncate=False)


# TODO: Contar registros actuales
# current_count = spark.read.format("delta").load(path).count()
# print(f"\n📊 Registros actuales: {current_count}")


# TODO: Hacer rollback a V1
print("\n🔄 Haciendo rollback a V1...")
# HINT: Lee V1 y sobreescribe la tabla
# v1_df = spark.read.format("delta").option("versionAsOf", 1).load(path)
# v1_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)


# TODO: Verificar el rollback
# after_rollback = spark.read.format("delta").load(path).count()
# print(f"✅ Después del rollback: {after_rollback} registros")


# TODO: Ver nuevo historial
print("\n📜 Nuevo historial:")
# delta_table = DeltaTable.forPath(spark, path)
# delta_table.history().select("version", "operation").show(5, truncate=False)


spark.stop()
