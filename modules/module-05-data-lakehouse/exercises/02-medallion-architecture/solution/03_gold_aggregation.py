"""SOLUCIÓN - Gold Aggregation"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, avg, min, max, countDistinct, round as spark_round, when, expr
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("Gold").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

df_silver = spark.read.format("delta").load("s3a://silver/transactions_clean")
print(f"📊 Silver: {df_silver.count()}")

# Agregar métricas
df_gold = df_silver.groupBy("date", "country").agg(
    count("*").alias("total_transactions"),
    spark_round(sum("amount"), 2).alias("total_amount"),
    spark_round(avg("amount"), 2).alias("avg_amount"),
    spark_round(min("amount"), 2).alias("min_amount"),
    spark_round(max("amount"), 2).alias("max_amount"),
    countDistinct("user_id").alias("unique_users"),
    countDistinct("product_id").alias("unique_products"),
    count(when(col("status") == "completed", 1)).alias("num_completed"),
    count(when(col("status") == "failed", 1)).alias("num_failed"),
    count(when(col("status") == "pending", 1)).alias("num_pending"),
    expr("percentile_approx(amount, 0.5)").alias("p50_amount"),
    expr("percentile_approx(amount, 0.9)").alias("p90_amount"),
    expr("percentile_approx(amount, 0.99)").alias("p99_amount")
).withColumn("completion_rate", spark_round((col("num_completed") / col("total_transactions")) * 100, 2))

# Guardar en Gold
gold_path = "s3a://gold/transactions_metrics"
df_gold.write.format("delta").mode("overwrite").partitionBy("country").save(gold_path)

gold_count = spark.read.format("delta").load(gold_path).count()
print(f"✅ Gold: {gold_count} métricas generadas")
df_gold.orderBy(col("total_amount").desc()).show(5, truncate=False)
spark.stop()
