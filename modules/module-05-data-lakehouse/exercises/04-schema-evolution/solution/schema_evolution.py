"""Schema Evolution Examples"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when
from pyspark.sql.types import DecimalType
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("SchemaEvolution").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

path = "s3a://bronze/schema_evolution_demo"

# 1. Crear tabla inicial
df = spark.read.json("../../../data/raw/transactions.json").limit(1000)
df.write.format("delta").mode("overwrite").save(path)
print("✅ Tabla inicial creada")
spark.read.format("delta").load(path).printSchema()

# 2. Add column con mergeSchema
df_new = df.withColumn("customer_segment", when(col("amount") > 1000, "VIP").otherwise("Regular"))
df_new.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
print("\n✅ Columna 'customer_segment' agregada")

# 3. Change column type (requiere reescritura)
print("\n🔄 Cambiando tipo de 'amount' a Decimal...")
df_retyped = spark.read.format("delta").load(path).withColumn("amount", col("amount").cast(DecimalType(10, 2)))
df_retyped.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)
print("✅ Tipo cambiado a Decimal(10,2)")

# 4. Verificar schema final
print("\n📋 Schema final:")
spark.read.format("delta").load(path).printSchema()

# Historial de cambios
DeltaTable.forPath(spark, path).history().select("version", "operation", "operationParameters.mergeSchema").show(truncate=False)

spark.stop()
