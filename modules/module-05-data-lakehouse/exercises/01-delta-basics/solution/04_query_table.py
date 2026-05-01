"""
SOLUCIÓN - Tarea 4: Consultar con Spark SQL

Esta solución demuestra cómo ejecutar queries SQL sobre tablas Delta.
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
print("✅ Spark session creado\n")

# 1. Registrar tabla Delta como SQL table temporal
delta_path = "s3a://bronze/transactions_delta"
df = spark.read.format("delta").load(delta_path)
df.createOrReplaceTempView("transactions_delta")

print("✅ Tabla registrada como 'transactions_delta'\n")
print(f"📊 Total de registros: {df.count()}\n")

# ============================================================
# Query 1: Contar registros por país
# ============================================================
print("=" * 60)
print("📊 QUERY 1: Registros por País")
print("=" * 60)

query1 = """
    SELECT 
        country, 
        COUNT(*) as total_transactions
    FROM transactions_delta
    GROUP BY country
    ORDER BY total_transactions DESC
"""

result1 = spark.sql(query1)
result1.show(20, truncate=False)

# ============================================================
# Query 2: Transacciones por status con métricas
# ============================================================
print("\n" + "=" * 60)
print("📊 QUERY 2: Métricas por Status")
print("=" * 60)

query2 = """
    SELECT 
        status,
        COUNT(*) as num_transactions,
        ROUND(AVG(amount), 2) as avg_amount,
        ROUND(SUM(amount), 2) as total_amount,
 MIN(amount) as min_amount,
        MAX(amount) as max_amount
    FROM transactions_delta
    GROUP BY status
    ORDER BY total_amount DESC
"""

result2 = spark.sql(query2)
result2.show(truncate=False)

# ============================================================
# Query 3: Top 10 transacciones más grandes
# ============================================================
print("\n" + "=" * 60)
print("📊 QUERY 3: Top 10 Transacciones Más Grandes")
print("=" * 60)

query3 = """
    SELECT 
        transaction_id,
        user_id,
        amount,
        currency,
        country,
        status,
        timestamp
    FROM transactions_delta
    ORDER BY amount DESC
    LIMIT 10
"""

result3 = spark.sql(query3)
result3.show(truncate=False)

# ============================================================
# Query 4: Transacciones por mes
# ============================================================
print("\n" + "=" * 60)
print("📊 QUERY 4: Transacciones por Mes")
print("=" * 60)

query4 = """
    SELECT 
        DATE_TRUNC('month', timestamp) as month,
        COUNT(*) as num_transactions,
        ROUND(SUM(amount), 2) as total_amount,
        ROUND(AVG(amount), 2) as avg_amount,
        MIN(amount) as min_amount,
        MAX(amount) as max_amount
    FROM transactions_delta
    WHERE timestamp IS NOT NULL
    GROUP BY DATE_TRUNC('month', timestamp)
    ORDER BY month DESC
"""

result4 = spark.sql(query4)
result4.show(truncate=False)

# ============================================================
# BONUS: Análisis Complejo - Geográfico por Moneda
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
# Análisis de Performance - Partitioning
# ============================================================
print("\n" + "=" * 60)
print("⚡ ANÁLISIS DE PERFORMANCE")
print("=" * 60)

# Query CON filtro en columna particionada (country) - RÁPIDO
print("\n🚀 Query aprovechando partitioning (RÁPIDO):")
start = time.time()
result_partitioned = spark.sql("""
    SELECT COUNT(*) as total, 
           ROUND(AVG(amount), 2) as avg_amount,
           ROUND(SUM(amount), 2) as total_amount
    FROM transactions_delta
    WHERE country = 'USA'
""")
result_partitioned.show()
time_partitioned = time.time() - start
print(f"⏱️  Tiempo con partition pruning: {time_partitioned:.3f}s")

# Query SIN usar particiones - MÁS LENTO
print("\n🐢 Query sin aprovechar partitioning (más lento):")
start = time.time()
result_full_scan = spark.sql("""
    SELECT COUNT(*) as total,
           ROUND(AVG(amount), 2) as avg_amount,
           ROUND(SUM(amount), 2) as total_amount
    FROM transactions_delta
    WHERE status = 'completed'
""")
result_full_scan.show()
time_no_partition = time.time() - start
print(f"⏱️  Tiempo con full scan: {time_no_partition:.3f}s")

speedup = time_no_partition / time_partitioned if time_partitioned > 0 else 1
print(f"\n📊 Speedup con partitioning: {speedup:.2f}x más rápido")

# ============================================================
# Window Functions - Análisis Avanzado
# ============================================================
print("\n" + "=" * 60)
print("📊 ANÁLISIS AVANZADO: Window Functions")
print("=" * 60)

window_query = """
    SELECT 
        country,
        transaction_id,
        amount,
        status,
        ROW_NUMBER() OVER (PARTITION BY country ORDER BY amount DESC) as rank_in_country,
        ROUND(AVG(amount) OVER (PARTITION BY country), 2) as country_avg_amount
    FROM transactions_delta
    QUALIFY rank_in_country <= 3
    ORDER BY country, rank_in_country
"""

print("\n🏆 Top 3 transacciones por país:")
try:
    spark.sql(window_query).show(30, truncate=False)
except Exception as e:
    # Si QUALIFY no está disponible, usar alternativa con subquery
    print("⚠️  QUALIFY no disponible, usando alternativa...")
    alt_query = """
        WITH ranked AS (
            SELECT 
                country,
                transaction_id,
                amount,
                status,
                ROW_NUMBER() OVER (PARTITION BY country ORDER BY amount DESC) as rank_in_country,
                ROUND(AVG(amount) OVER (PARTITION BY country), 2) as country_avg_amount
            FROM transactions_delta
        )
        SELECT *
        FROM ranked
        WHERE rank_in_country <= 3
        ORDER BY country, rank_in_country
    """
    spark.sql(alt_query).show(30, truncate=False)

# ============================================================
# Metadata de la tabla
# ============================================================
print("\n" + "=" * 60)
print("📋 METADATA DE LA TABLA")
print("=" * 60)

print("\n🔍 Schema:")
spark.sql("DESCRIBE transactions_delta").show(50, truncate=False)

print("\n🔍 Información detallada:")
spark.sql("DESCRIBE DETAIL transactions_delta").show(vertical=True, truncate=False)

# ============================================================
# Resumen Final
# ============================================================
print("\n" + "=" * 60)
print("✅ RESUMEN DEL EJERCICIO")
print("=" * 60)

print("\n🎓 Has completado exitosamente:")
print("   ✅ Queries de agregación (COUNT, SUM, AVG)")
print("   ✅ Queries con GROUP BY y ORDER BY")
print("   ✅ Window functions (ROW_NUMBER, AVG OVER)")
print("   ✅ Análisis de performance con partitioning")
print("   ✅ Consultas complejas multi-dimensionales")

print("\n💡 Conceptos clave aprendidos:")
print("   - Spark SQL es tan poderoso como PySpark DataFrame API")
print("   - Partitioning mejora SIGNIFICATIVAMENTE el performance")
print("   - Window functions permiten análisis sofisticados")
print("   - Delta Lake integra perfectamente con SQL")

print("\n🚀 Próximos pasos:")
print("   - Experimenta con tus propias queries")
print("   - Prueba EXPLAIN para ver query plans")
print("   - Continúa con Ejercicio 02: Medallion Architecture")

spark.stop()
