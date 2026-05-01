"""Schema Evolution Examples

📝 OBJETIVO:
Aprender a evolucionar el esquema de una tabla Delta sin romper pipelines

✅ TAREAS:
1. Crear tabla inicial con schema base
2. Agregar nueva columna (customer_segment) usando mergeSchema
3. Cambiar tipo de columna (amount a Decimal)
4. Verificar schema final
5. Ver historial de cambios

💡 PISTA: Usa .option("mergeSchema", "true") para agregar columnas
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when
from pyspark.sql.types import DecimalType
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("SchemaEvolution") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/schema_evolution_demo"

# TODO: 1. Crear tabla inicial
print("📝 1. Crear tabla inicial")
# df = spark.read.json("../../../data/raw/transactions.json").limit(1000)
# df.write.format("delta").mode("overwrite").save(path)
# print("✅ Tabla inicial creada")
# spark.read.format("delta").load(path).printSchema()


# TODO: 2. Agregar columna con mergeSchema
print("\n📝 2. Agregar columna 'customer_segment'")
# HINT: usa .withColumn() para agregar la nueva columna
# df_new = df.withColumn("customer_segment", 
#     when(col("amount") > 1000, "VIP").otherwise("Regular"))
# HINT: usa .option("mergeSchema", "true") al escribir
# df_new.write.format("delta").mode("append").option("mergeSchema", "true").save(path)


# TODO: 3. Cambiar tipo de columna (amount → Decimal)
print("\n📝 3. Cambiar tipo de 'amount' a Decimal")
# HINT: Lee la tabla, aplica .cast() y sobreescribe con overwriteSchema
# df_retyped = spark.read.format("delta").load(path) \
#     .withColumn("amount", col("amount").cast(DecimalType(10, 2)))
# df_retyped.write.format("delta").mode("overwrite") \
#     .option("overwriteSchema", "true").save(path)


# TODO: 4. Verificar schema final
print("\n📋 Schema final:")
# spark.read.format("delta").load(path).printSchema()


# TODO: 5. Ver historial de cambios
print("\n📜 Historial de cambios de schema:")
# DeltaTable.forPath(spark, path).history() \
#     .select("version", "operation", "operationParameters.mergeSchema") \
#     .show(truncate=False)


spark.stop()
