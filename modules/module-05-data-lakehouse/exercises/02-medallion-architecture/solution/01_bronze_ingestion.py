"""SOLUCIÓN - Bronze Ingestion"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit, to_date, col
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("Bronze").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Leer todos los registros
df_raw = spark.read.json("../../../data/raw/transactions.json")
print(f"📊 Total: {df_raw.count()}")

# Agregar metadata
df_bronze = df_raw.withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_file", lit("transactions.json")) \
    .withColumn("ingestion_date", to_date(col("ingestion_timestamp")))

# Guardar en Bronze (append-only)
bronze_path = "s3a://bronze/transactions_medallion"
df_bronze.write.format("delta").mode("append").partitionBy("ingestion_date").save(bronze_path)

print(f"✅ Ingresado a Bronze: {spark.read.format('delta').load(bronze_path).count()} registros")
spark.stop()
