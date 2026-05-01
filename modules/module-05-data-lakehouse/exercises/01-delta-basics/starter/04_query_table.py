"""
Tarea 4: Consultar con Spark SQL

Objetivo:
- Registrar la tabla Delta como SQL table
- Ejecutar queries analíticos con Spark SQL
- Generar reportes de negocio

TODOs:
1. Registrar tabla Delta como SQL table
2. Query 1: Contar registros por país
3. Query 2: Transacciones por status con métricas
4. Query 3: Top 10 transacciones más grandes
5. Query 4: Transacciones por mes
"""

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import time

# Crear SparkSession
builder = SparkSession.builder \
    .appName("Delta Lake - SQL Queries") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
print("✅ Spark session creado")

# TODO 1: Registrar tabla Delta como SQL table temporal
# Esto permite usar SQL directamente
delta_path = "s3a://bronze/transactions_delta"

# COMPLETAR: Leer la tabla Delta y registrarla como "transactions_delta"
df = None  # COMPLETAR: spark.read.format("delta").load(delta_path)
# COMPLETAR: df.createOrReplaceTempView("transactions_delta")

print("✅ Tabla registrada como 'transactions_delta'\n")

# ============================================================
# TODO 2: Query 1 - Contar registros por país
# ============================================================
print("=" * 60)
print("📊 QUERY 1: Registros por País")
print("=" * 60)

query1 = """
    -- COMPLETAR: SELECT country, COUNT(*) ...
"""

# COMPLETAR: Ejecutar query y guardar resultado
result1 = None  # spark.sql(query1)
# result1.show(truncate=False)

# ============================================================
# TODO 3: Query 2 - Transacciones por status con métricas
# ============================================================
print("\n" + "=" * 60)
print("📊 QUERY 2: Métricas por Status")
print("=" * 60)

query2 = """
    -- COMPLETAR: SELECT status, COUNT(*), AVG(amount), SUM(amount) ...
"""

# COMPLETAR: Ejecutar y mostrar
result2 = None  # spark.sql(query2)
# result2.show(truncate=False)

# ============================================================
# TODO 4: Query 3 - Top 10 transacciones más grandes
# ============================================================
print("\n" + "=" * 60)
print("📊 QUERY 3: Top 10 Transacciones Más Grandes")
print("=" * 60)

query3 = """
    -- COMPLETAR: SELECT transaction_id, amount, currency, country
    -- ORDER BY amount DESC
    -- LIMIT 10
"""

# COMPLETAR: Ejecutar y mostrar
result3 = None  # spark.sql(query3)
# result3.show(truncate=False)

# ============================================================
# TODO 5: Query 4 - Transacciones por mes
# ============================================================
print("\n" + "=" * 60)
print("📊 QUERY 4: Transacciones por Mes")
print("=" * 60)

query4 = """
    -- COMPLETAR: Usa DATE_TRUNC('month', timestamp) o MONTH(timestamp)
    -- Agrupa por mes, cuenta transacciones y suma montos
"""

# COMPLETAR: Ejecutar y mostrar
result4 = None  # spark.sql(query4)
# result4.show(truncate=False)

# ============================================================
# BONUS: Query Compleja - Análisis Geográfico por Moneda
# ============================================================
print("\n" + "=" * 60)
print("📊 BONUS QUERY: Análisis Geográfico por Moneda")
print("=" * 60)

bonus_query = """
    SELECT 
        country,
        currency,
        COUNT(*) as num_transactions,
        ROUND(AVG(amount), 2) as avg_amount,
        ROUND(SUM(amount), 2) as total_amount,
        MIN(amount) as min_amount,
        MAX(amount) as max_amount
    FROM transactions_delta
    GROUP BY country, currency
    ORDER BY total_amount DESC
    LIMIT 20
"""

start_time = time.time()
bonus_result = spark.sql(bonus_query)
bonus_result.show(20, truncate=False)
elapsed = time.time() - start_time

print(f"\n⚡ Query ejecutada en {elapsed:.2f} segundos")

# ============================================================
# Verificación de Performance
# ============================================================
print("\n" + "=" * 60)
print("⚡ ANÁLISIS DE PERFORMANCE")
print("=" * 60)

# Query con filtro en columna particionada (country) - RÁPIDO
print("\n🚀 Query con partitioning (RÁPIDO):")
start = time.time()
spark.sql("""
    SELECT COUNT(*), AVG(amount)
    FROM transactions_delta
    WHERE country = 'USA'
""").show()
time_partitioned = time.time() - start
print(f"Tiempo con partitioning: {time_partitioned:.3f}s")

# Query sin usar particiones - MÁS LENTO
print("\n🐢 Query sin aprovechar partitioning (más lento):")
start = time.time()
spark.sql("""
    SELECT COUNT(*), AVG(amount)
    FROM transactions_delta
    WHERE status = 'completed'
""").show()
time_no_partition = time.time() - start
print(f"Tiempo sin partitioning: {time_no_partition:.3f}s")

print(f"\n📊 Speedup con partitioning: {time_no_partition/time_partitioned:.2f}x")

# ============================================================
# Metadata de la tabla
# ============================================================
print("\n" + "=" * 60)
print("📋 METADATA DE LA TABLA")
print("=" * 60)

print("\n🔍 Schema:")
spark.sql("DESCRIBE transactions_delta").show(truncate=False)

print("\n🔍 Información extendida:")
spark.sql("DESCRIBE EXTENDED transactions_delta").show(100, truncate=False)

print("\n✅ ¡Todas las queries completadas exitosamente!")
print("📊 Has aprendido a consultar tablas Delta con Spark SQL")
print("⚡ Has visto el impacto del particionamiento en performance")

spark.stop()
