"""
Tests para Ejercicio 01: Delta Basics

Ejecuta: pytest test_delta_basics.py -v
"""

import pytest
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

@pytest.fixture(scope="session")
def spark():
    """Fixture para SparkSession con Delta Lake"""
    builder = SparkSession.builder \
        .appName("Test Delta Basics") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    yield spark
    spark.stop()

class TestDeltaBasics:
    """Tests para validar el ejercicio Delta Basics"""
    
    delta_path = "s3a://bronze/transactions_delta"
    
    def test_table_exists(self, spark):
        """Verifica que la tabla Delta se creó correctamente"""
        df = spark.read.format("delta").load(self.delta_path)
        assert df is not None, "La tabla Delta no existe"
    
    def test_record_count(self, spark):
        """Verifica que tiene 15,000 registros"""
        df = spark.read.format("delta").load(self.delta_path)
        count = df.count()
        assert count == 15000, f"Esperaba 15,000 registros, encontró {count}"
    
    def test_schema_columns(self, spark):
        """Verifica que las columnas esperadas existen"""
        df = spark.read.format("delta").load(self.delta_path)
        expected_columns = [
            "transaction_id", "user_id", "product_id", "amount",
            "currency", "payment_method", "status", "timestamp",
            "country", "ingestion_date"
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Falta columna: {col}"
    
    def test_partitioning(self, spark):
        """Verifica que la tabla está particionada por country"""
        df = spark.read.format("delta").load(self.delta_path)
        countries = df.select("country").distinct().count()
        assert countries > 0, "No hay particiones por país"
        assert countries >= 5, f"Esperaba al menos 5 países, encontró {countries}"
    
    def test_version_history(self, spark):
        """Verifica que hay múltiples versiones (create, append, overwrite)"""
        delta_table = DeltaTable.forPath(spark, self.delta_path)
        history = delta_table.history()
        versions = history.count()
        
        assert versions >= 3, f"Esperaba al menos 3 versiones, encontró {versions}"
    
    def test_no_pending_in_usa(self, spark):
        """Verifica que no hay status pending en USA (fueron cambiados a expired)"""
        df = spark.read.format("delta").load(self.delta_path)
        pending_usa = df.filter(
            (df.country == "USA") & (df.status == "pending")
        ).count()
        
        assert pending_usa == 0, f"USA todavía tiene {pending_usa} registros pending"
    
    def test_sql_access(self, spark):
        """Verifica que la tabla se puede consultar con SQL"""
        df = spark.read.format("delta").load(self.delta_path)
        df.createOrReplaceTempView("test_table")
        
        result = spark.sql("SELECT COUNT(*) as total FROM test_table").collect()
        assert result[0]["total"] == 15000, "Query SQL falló"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
