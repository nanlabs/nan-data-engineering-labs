"""Tests para Ejercicio 01: Delta Basics"""
import pytest
from delta.tables import DeltaTable

def test_create_delta_table(spark, test_data, temp_path):
    """Test: Crear tabla Delta básica"""
    test_data.write.format("delta").mode("overwrite").save(temp_path)
    
    df = spark.read.format("delta").load(temp_path)
    assert df.count() == 3
    assert "transaction_id" in df.columns

def test_append_mode(spark, delta_table_path, test_data):
    """Test: Append sin duplicados"""
    initial_count = spark.read.format("delta").load(delta_table_path).count()
    
    new_data = test_data.limit(1)
    new_data.write.format("delta").mode("append").save(delta_table_path)
    
    final_count = spark.read.format("delta").load(delta_table_path).count()
    assert final_count == initial_count + 1

def test_overwrite_partition(spark, test_data, temp_path):
    """Test: Overwrite con replaceWhere"""
    test_data.write.format("delta").mode("overwrite").partitionBy("country").save(temp_path)
    
    usa_data = test_data.filter("country = 'USA'").limit(1)
    usa_data.write.format("delta").mode("overwrite") \
        .option("replaceWhere", "country = 'USA'") \
        .save(temp_path)
    
    df = spark.read.format("delta").load(temp_path)
    usa_count = df.filter("country = 'USA'").count()
    mex_count = df.filter("country = 'MEX'").count()
    
    assert usa_count == 1  # Reemplazado
    assert mex_count == 1  # Intacto

def test_delta_history(spark, delta_table_path):
    """Test: History tracking"""
    delta_table = DeltaTable.forPath(spark, delta_table_path)
    history = delta_table.history()
    
    assert history.count() > 0
    assert "version" in history.columns
    assert "operation" in history.columns

def test_sql_query(spark, delta_table_path):
    """Test: SQL queries sobre Delta table"""
    df = spark.read.format("delta").load(delta_table_path)
    df.createOrReplaceTempView("transactions")
    
    result = spark.sql("SELECT country, COUNT(*) as cnt FROM transactions GROUP BY country")
    assert result.count() >= 2

def test_partition_pruning(spark, test_data, temp_path):
    """Test: Partitioning funciona correctamente"""
    test_data.write.format("delta").mode("overwrite").partitionBy("country").save(temp_path)
    
    # Verificar estructura de particiones
    df = spark.read.format("delta").load(temp_path)
    assert "country" in df.columns
    
    # Filtrar por partición debe ser eficiente
    usa_data = df.filter("country = 'USA'")
    assert usa_data.count() == 2

def test_metadata_columns(spark, delta_table_path):
    """Test: Metadata disponible"""
    delta_table = DeltaTable.forPath(spark, delta_table_path)
    detail = delta_table.detail()
    
    assert detail.count() == 1
    assert "numFiles" in detail.columns
    assert "sizeInBytes" in detail.columns

def test_transaction_log(spark, delta_table_path):
    """Test: Transaction log existe"""
    import os
    log_path = os.path.join(delta_table_path, "_delta_log")
    assert os.path.exists(log_path)
    assert os.path.isdir(log_path)
