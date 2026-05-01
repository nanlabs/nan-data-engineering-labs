"""Tests para Ejercicio 02: Medallion Architecture"""
import pytest
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

@pytest.fixture(scope="session")
def spark():
    builder = SparkSession.builder.appName("Test").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    yield spark
    spark.stop()

class TestMedallion:
    def test_bronze_exists(self, spark):
        df = spark.read.format("delta").load("s3a://bronze/transactions_medallion")
        assert df.count() > 0
    
    def test_bronze_has_metadata(self, spark):
        df = spark.read.format("delta").load("s3a://bronze/transactions_medallion")
        assert "ingestion_timestamp" in df.columns
        assert "source_file" in df.columns
    
    def test_silver_no_duplicates(self, spark):
        df = spark.read.format("delta").load("s3a://silver/transactions_clean")
        total = df.count()
        unique = df.select("transaction_id").distinct().count()
        assert total == unique
    
    def test_silver_no_invalid_amounts(self, spark):
        df = spark.read.format("delta").load("s3a://silver/transactions_clean")
        invalid = df.filter((df.amount.isNull()) | (df.amount <= 0)).count()
        assert invalid == 0
    
    def test_gold_has_metrics(self, spark):
        df = spark.read.format("delta").load("s3a://gold/transactions_metrics")
        expected_cols = ["date", "country", "total_transactions", "total_amount"]
        for col in expected_cols:
            assert col in df.columns
    
    def test_data_quality_rate(self, spark):
        bronze = spark.read.format("delta").load("s3a://bronze/transactions_medallion").count()
        silver = spark.read.format("delta").load("s3a://silver/transactions_clean").count()
        quality_rate = (silver / bronze) * 100
        assert quality_rate >= 80, f"Quality rate too low: {quality_rate:.1f}%"
