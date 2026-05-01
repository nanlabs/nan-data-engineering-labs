"""Optimization Techniques

📝 OBJETIVO:
Aprender técnicas de optimización para mejorar performance de queries en Delta Lake

✅ TAREAS:
1. Ver estado actual de la tabla (numFiles, size)
2. OPTIMIZE para compactar archivos pequeños
3. Z-ORDER por columnas de filtrado frecuente
4. Verificar mejoras
5. Test de performance
6. VACUUM para limpiar archivos antiguos

💡 PISTA: usa delta_table.optimize().executeCompaction() y executeZOrderBy()
"""
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
import time

builder = SparkSession.builder.appName("Optimization") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://silver/transactions_clean"

# TODO: 1. Ver estado actual
print("📊 ANTES DE OPTIMIZAR:")
# HINT: usa DeltaTable.forPath(spark, path)
# delta_table = DeltaTable.forPath(spark, path)
# detail = delta_table.detail()
# detail.select("numFiles", "sizeInBytes").show()


# TODO: 2. OPTIMIZE - Compactar archivos
print("\n🔧 Ejecutando OPTIMIZE (compactación)...")
# HINT: delta_table.optimize().executeCompaction()


# TODO: 3. Z-ORDER - Optimizar queries por columnas específicas
print("\n🔧 Ejecutando Z-ORDER por country y date...")
# HINT: delta_table.optimize().executeZOrderBy("col1", "col2", ...)
# NOTA: Usar columnas que frecuentemente aparezcan en WHERE


# TODO: 4. Ver mejora después de optimización
print("\n📊 DESPUÉS DE OPTIMIZAR:")
# detail = delta_table.detail()
# detail.select("numFiles", "sizeInBytes").show()


# TODO: 5. Test de performance
print("\n⚡ TEST DE PERFORMANCE:")
# df = spark.read.format("delta").load(path)
# start = time.time()
# result = df.filter("country = 'USA' AND date = '2024-01-15'").count()
# elapsed = time.time() - start
# print(f"Query time: {elapsed:.3f}s, rows: {result}")


# TODO: 6. VACUUM - Limpiar archivos antiguos (PRECAUCIÓN)
print("\n🧹 VACUUM - Limpiando archivos antiguos...")
# HINT: Necesitas deshabilitar el check de retention primero
# spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
# delta_table.vacuum(0)  # 0 = borra todo (solo para testing)
# ⚠️ En producción usa vacuum(168) para retener 7 días


spark.stop()
