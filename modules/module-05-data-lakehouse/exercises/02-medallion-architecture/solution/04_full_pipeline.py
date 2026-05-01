"""SOLUCIÓN - Full Pipeline"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import DecimalType
from delta import configure_spark_with_delta_pip
import time

print("🚀 MEDALLION PIPELINE")
builder = SparkSession.builder.appName("Pipeline").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

start = time.time()

# BRONZE
print("\n🥉 BRONZE...")
df_raw = spark.read.json("../../../data/raw/transactions.json")
df_bronze = df_raw.withColumn("ingestion_timestamp", current_timestamp()).withColumn("source_file", lit("transactions.json")).withColumn("ingestion_date", to_date(col("ingestion_timestamp")))
df_bronze.write.format("delta").mode("append").partitionBy("ingestion_date").save("s3a://bronze/transactions_medallion")
bronze_count = spark.read.format("delta").load("s3a://bronze/transactions_medallion").count()
print(f"✅ Bronze: {bronze_count}")

# SILVER
print("\n🥈 SILVER...")
df_dedup = df_bronze.dropDuplicates(["transaction_id"])
dupes = bronze_count - df_dedup.count()
df_valid = df_dedup.filter((col("amount").isNotNull()) & (col("amount") > 0) & (col("timestamp").isNotNull()))
invalids = df_dedup.count() - df_valid.count()
df_silver = df_valid.withColumn("status", lower(trim(col("status")))).withColumn("currency", upper(trim(col("currency")))).withColumn("is_valid", lit(True)).withColumn("date", to_date(col("timestamp"))).withColumn("amount", col("amount").cast(DecimalType(10, 2)))
df_silver.write.format("delta").mode("overwrite").partitionBy("country", "date").save("s3a://silver/transactions_clean")
silver_count = spark.read.format("delta").load("s3a://silver/transactions_clean").count()
quality = silver_count/bronze_count*100
print(f"✅ Silver: {silver_count} ({quality:.1f}% calidad)")

# GOLD
print("\n🥇 GOLD...")
df_gold = df_silver.groupBy("date", "country").agg(count("*").alias("total_transactions"), round(sum("amount"), 2).alias("total_amount"), round(avg("amount"), 2).alias("avg_amount"), countDistinct("user_id").alias("unique_users"), count(when(col("status") == "completed", 1)).alias("num_completed"), expr("percentile_approx(amount, 0.5)").alias("p50_amount"))
df_gold.write.format("delta").mode("overwrite").partitionBy("country").save("s3a://gold/transactions_metrics")
gold_count = spark.read.format("delta").load("s3a://gold/transactions_metrics").count()
print(f"✅ Gold: {gold_count} métricas")

total_time = time.time() - start
print(f"\n📊 RESUMEN:\n   Bronze: {bronze_count:,}\n   Silver: {silver_count:,} (dupes: {dupes}, invalids: {invalids})\n   Gold: {gold_count}\n   Tiempo: {total_time:.1f}s\n✅ SUCCESS")
spark.stop()
