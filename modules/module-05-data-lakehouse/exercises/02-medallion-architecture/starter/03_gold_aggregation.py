"""
Tarea 3: Gold Layer - Agregaciones de Negocio

TODOs:
1. Leer tabla Silver
2. Agregar métricas diarias por país
3. Calcular KPIs de negocio
4. Calcular percentiles
5. Guardar en Gold
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum, avg, min, max,
    countDistinct, round as spark_round,
    when, expr
)
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder \
    .appName("Medallion - Gold Aggregation") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado\n")

# TODO 1: Leer tabla Silver
silver_path = "s3a://silver/transactions_clean"
df_silver = None  # COMPLETAR

print(f"📊 Registros en Silver: {df_silver.count()}")

# TODO 2: Agregar métricas diarias por país
# GroupBy: date, country
# Métricas:
#   - total_transactions: count(*)
#   - total_amount: sum(amount)
#   - avg_amount: avg(amount)
#   - min_amount: min(amount)
#   - max_amount: max(amount)
#   - unique_users: countDistinct(user_id)
#   - unique_products: countDistinct(product_id)

# COMPLETAR: Crear agregación base

# TODO 3: Calcular métricas por status
# Contar cuántas transacciones hay de cada status
#   - num_completed: count where status='completed'
#   - num_failed: count where status='failed'
#   - num_pending: count where status='pending'
#   - completion_rate: (num_completed / total_transactions) * 100

# Hint: Usa when() dentro de count()
# Ejemplo: count(when(col("status") == "completed", 1))

# COMPLETAR: Agregar métricas de status

# TODO 4: Calcular percentiles
# Usa approx_percentile o percentile_approx
#   - p50_amount (mediana)
#   - p90_amount
#   - p99_amount

# COMPLETAR: Agregar percentiles
# Hint: expr("percentile_approx(amount, 0.5)").alias("p50_amount")

# TODO 5: Redondear valores numéricos
# Usa round() en las métricas de amount

df_gold = None  # COMPLETAR: Resultado final con todos los campos

print("\n📋 Schema Gold:")
df_gold.printSchema()

print("\n🔍 Muestra de métricas Gold:")
df_gold.orderBy(col("total_amount").desc()).show(10, truncate=False)

# TODO 6: Guardar en Gold
# Ruta: s3a://gold/transactions_metrics
# Modo: overwrite
# Partición: country

gold_path = "s3a://gold/transactions_metrics"

# COMPLETAR: Escribir a Gold

print(f"\n✅ Métricas agregadas guardadas en Gold: {gold_path}")

# Verificación
gold_df = spark.read.format("delta").load(gold_path)
print(f"📊 Total de filas en Gold: {gold_df.count()}")
print(f"📅 Días únicos: {gold_df.select('date').distinct().count()}")
print(f"🌍 Países únicos: {gold_df.select('country').distinct().count()}")

print("\n🥇 GOLD LAYER CARACTERÍSTICAS:")
print("   ✅ Business-friendly metrics")
print("   ✅ Pre-aggregated (consultas instantáneas)")
print("   ✅ Denormalized (todo en una tabla)")
print("   ✅ BI-ready (Tableau, PowerBI, Looker)")

# Métricas globales
print("\n📊 MÉTRICAS GLOBALES:")
gold_df.agg(
    sum("total_transactions").alias("global_transactions"),
    spark_round(sum("total_amount"), 2).alias("global_revenue"),
    spark_round(avg("avg_amount"), 2).alias("global_avg_amount")
).show(truncate=False)

spark.stop()
