"""Optimization Techniques"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
import time

builder = SparkSession.builder.appName("Optimization").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://silver/transactions_clean"
delta_table = DeltaTable.forPath(spark, path)

# 1. Ver estado actual
print("📊 ANTES DE OPTIMIZAR:")
detail = delta_table.detail()
detail.select("numFiles", "sizeInBytes").show()

# 2. OPTIMIZE para compactar archivos
print("\n🔧 Ejecutando OPTIMIZE...")
delta_table.optimize().executeCompaction()
print("✅ Compactación completa")

# 3. Z-ORDER por columnas frecuentes
print("\n🔧 Ejecutando Z-ORDER por country y date...")
delta_table.optimize().executeZOrderBy("country", "date")
print("✅ Z-Ordering aplicado")

# 4. Ver mejora
print("\n📊 DESPUÉS DE OPTIMIZAR:")
delta_table.detail().select("numFiles", "sizeInBytes").show()

# 5. Test de performance
print("\n⚡ TEST DE PERFORMANCE:")
df = spark.read.format("delta").load(path)

start = time.time()
df.filter("country = 'USA' AND date = '2024-01-15'").count()
optimized_time = time.time() - start
print(f"Query optimizada: {optimized_time:.3f}s")

# 6. VACUUM (cuidado: borra historial)
print("\n🧹 Limpiando archivos antiguos...")
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
delta_table.vacuum(0)  # Borra TODO (solo para demo)
print("✅ Vacuum completado")

spark.stop()
