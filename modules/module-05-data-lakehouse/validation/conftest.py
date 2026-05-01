"""Pytest Fixtures para Spark y Delta Lake"""
import pytest
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import shutil
import os

@pytest.fixture(scope="session")
def spark():
    """SparkSession con Delta Lake configurado"""
    builder = SparkSession.builder \
        .appName("TestSuite") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
    
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    
    yield spark
    
    spark.stop()

@pytest.fixture(scope="function")
def test_data(spark):
    """Datos de prueba"""
    data = [
        ("TX001", "U001", "P001", 100.0, "completed", "USA", "USD", "2024-01-15 10:00:00"),
        ("TX002", "U002", "P002", 200.0, "pending", "MEX", "MXN", "2024-01-15 11:00:00"),
        ("TX003", "U003", "P003", 300.0, "failed", "USA", "USD", "2024-01-15 12:00:00"),
    ]
    columns = ["transaction_id", "user_id", "product_id", "amount", "status", "country", "currency", "timestamp"]
    return spark.createDataFrame(data, columns)

@pytest.fixture(scope="function")
def temp_path(tmp_path):
    """Path temporal para tests"""
    path = str(tmp_path / "delta_test")
    yield path
    # Cleanup
    if os.path.exists(path):
        shutil.rmtree(path)

@pytest.fixture(scope="function")
def delta_table_path(spark, test_data, temp_path):
    """Delta table pre-creada para tests"""
    test_data.write.format("delta").mode("overwrite").save(temp_path)
    yield temp_path
