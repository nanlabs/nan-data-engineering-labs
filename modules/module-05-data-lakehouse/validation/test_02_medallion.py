"""Tests para Ejercicio 02: Medallion Architecture"""
import pytest
from pyspark.sql.functions import col

def test_bronze_layer(spark, test_data, temp_path):
    """Test: Bronze layer preserva datos raw"""
    from pyspark.sql.functions import current_timestamp, lit
    
    bronze_df = test_data.withColumn("ingestion_timestamp", current_timestamp()) \
                         .withColumn("source_file", lit("test.json"))
    
    bronze_path = temp_path + "/bronze"
    bronze_df.write.format("delta").mode("append").save(bronze_path)
    
    df = spark.read.format("delta").load(bronze_path)
    assert df.count() == 3
    assert "ingestion_timestamp" in df.columns
    assert "source_file" in df.columns

def test_silver_deduplication(spark, temp_path):
    """Test: Silver layer deduplica correctamente"""
    from pyspark.sql.functions import row_number
    from pyspark.sql.window import Window
    
    # Crear datos duplicados
    data = [
        ("TX001", "U001", 100.0),
        ("TX001", "U001", 100.0),  # Duplicado
        ("TX002", "U002", 200.0),
    ]
    df = spark.createDataFrame(data, ["transaction_id", "user_id", "amount"])
    
    # Deduplicar
    window = Window.partitionBy("transaction_id").orderBy(col("amount").desc())
    df_deduped = df.withColumn("rn", row_number().over(window)).filter("rn = 1").drop("rn")
    
    assert df_deduped.count() == 2

def test_silver_validation(spark, test_data, temp_path):
    """Test: Silver layer filtra inválidos"""
    # Agregar registro inválido
    invalid_data = [("TX999", "U999", None, None, "completed", "USA", "USD", "2024-01-15")]
    invalid_df = spark.createDataFrame(invalid_data, test_data.columns)
    
    all_data = test_data.union(invalid_df)
    
    # Filtrar inválidos
    silver_df = all_data.filter("amount IS NOT NULL AND amount > 0")
    
    assert silver_df.count() == 3  # Excluye el inválido

def test_gold_aggregation(spark, test_data):
    """Test: Gold layer agrega correctamente"""
    from pyspark.sql.functions import count, sum, avg
    
    gold_df = test_data.groupBy("country").agg(
        count("transaction_id").alias("total_transactions"),
        sum("amount").alias("total_amount"),
        avg("amount").alias("avg_amount")
    )
    
    assert gold_df.count() == 2  # USA y MEX
    usa_row = gold_df.filter("country = 'USA'").first()
    assert usa_row["total_transactions"] == 2

def test_full_pipeline(spark, test_data, temp_path):
    """Test: Pipeline completo Bronze → Silver → Gold"""
    from pyspark.sql.functions import current_timestamp, lit
    
    # Bronze
    bronze_path = temp_path + "/bronze"
    test_data.withColumn("ingestion_timestamp", current_timestamp()).write.format("delta").save(bronze_path)
    
    # Silver
    silver_path = temp_path + "/silver"
    bronze_df = spark.read.format("delta").load(bronze_path)
    silver_df = bronze_df.filter("amount > 0").dropDuplicates(["transaction_id"])
    silver_df.write.format("delta").save(silver_path)
    
    # Gold
    gold_path = temp_path + "/gold"
    silver_df = spark.read.format("delta").load(silver_path)
    gold_df = silver_df.groupBy("country").agg(count("*").alias("cnt"))
    gold_df.write.format("delta").save(gold_path)
    
    # Verificar
    gold_result = spark.read.format("delta").load(gold_path)
    assert gold_result.count() == 2

def test_data_quality_metrics(spark, test_data):
    """Test: Data quality tracking"""
    total = test_data.count()
    valid = test_data.filter("amount > 0 AND timestamp IS NOT NULL").count()
    
    quality_rate = (valid / total) * 100
    assert quality_rate == 100.0  # Test data es 100% válido
