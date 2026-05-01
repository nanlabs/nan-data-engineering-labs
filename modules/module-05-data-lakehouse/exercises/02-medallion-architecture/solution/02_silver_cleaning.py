"""SOLUCIÓN - Silver Cleaning"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, trim, upper, to_date, lit, when
from pyspark.sql.types import DecimalType
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("Silver").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Leer Bronze
df_bronze = spark.read.format("delta").load("s3a://bronze/transactions_medallion")
bronze_count = df_bronze.count()
print(f"📊 Bronze: {bronze_count}")

# Deduplicar
df_dedup = df_bronze.dropDuplicates(["transaction_id"])
print(f"🗑️  Duplicados: {bronze_count - df_dedup.count()}")

# Filtrar inválidos
df_valid = df_dedup.filter((col("amount").isNotNull()) & (col("amount") > 0) & (col("timestamp").isNotNull()))
print(f"❌ Inválidos: {df_dedup.count() - df_valid.count()}")

# Normalizar y agregar columnas
df_silver = df_valid \
   .withColumn("status", lower(trim(col("status")))) \
    .withColumn("currency", upper(trim(col("currency")))) \
    .withColumn("is_valid", lit(True)) \
    .withColumn("date", to_date(col("timestamp"))) \
    .withColumn("amount", col("amount").cast(DecimalType(10, 2)))

# Guardar en Silver
silver_path = "s3a://silver/transactions_clean"
df_silver.write.format("delta").mode("overwrite").partitionBy("country", "date").save(silver_path)

silver_count = spark.read.format("delta").load(silver_path).count()
print(f"✅ Silver: {silver_count} ({silver_count/bronze_count*100:.1f}% calidad)")
spark.stop()
