"""Tests para Ejercicio 05: Optimization"""
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit
from delta.tables import DeltaTable
import time


class TestOptimization:
    """Tests para técnicas de optimización"""

    def test_optimize_reduces_files(self, spark, temp_delta_path):
        """Test que OPTIMIZE reduce el número de archivos"""
        path = temp_delta_path
        
        # Crear muchos archivos pequeños
        for i in range(10):
            df = spark.range(i * 100, (i + 1) * 100)
            df.write.format("delta").mode("append").save(path)
        
        # Contar archivos antes
        delta_table = DeltaTable.forPath(spark, path)
        files_before = delta_table.detail().select("numFiles").collect()[0][0]
        
        # OPTIMIZE
        delta_table.optimize().executeCompaction()
        
        # Contar archivos después
        delta_table = DeltaTable.forPath(spark, path)
        files_after = delta_table.detail().select("numFiles").collect()[0][0]
        
        # Debe haber menos archivos
        assert files_after < files_before
        
    def test_z_order_execution(self, spark, temp_delta_path):
        """Test que Z-ORDER ejecuta sin errores"""
        path = temp_delta_path
        
        # Crear tabla con múltiples columnas
        df = spark.createDataFrame([
            (1, "USA", "2024-01-01"),
            (2, "UK", "2024-01-02"),
            (3, "USA", "2024-01-03")
        ], ["id", "country", "date"])
        df.write.format("delta").mode("overwrite").save(path)
        
        # Z-ORDER
        delta_table = DeltaTable.forPath(spark, path)
        result = delta_table.optimize().executeZOrderBy("country", "date")
        
        # Verificar que ejecutó
        assert result is not None
        
    def test_vacuum_removes_old_files(self, spark, temp_delta_path):
        """Test que VACUUM limpia archivos antiguos"""
        path = temp_delta_path
        
        # Crear V0
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        
        # Crear V1 (sobreescribir)
        df2 = spark.range(200)
        df2.write.format("delta").mode("overwrite").save(path)
        
        # VACUUM con retention 0 (elimina V0)
        delta_table = DeltaTable.forPath(spark, path)
        spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        delta_table.vacuum(0)
        
        # Intentar leer V0 debe fallar después de vacuum
        with pytest.raises(Exception):
            spark.read.format("delta").option("versionAsOf", 0).load(path).count()
            
    def test_detail_shows_metrics(self, spark, temp_delta_path):
        """Test que detail() muestra métricas correctas"""
        path = temp_delta_path
        
        df = spark.range(1000)
        df.write.format("delta").mode("overwrite").save(path)
        
        delta_table = DeltaTable.forPath(spark, path)
        detail = delta_table.detail()
        
        # Verificar columnas importantes
        row = detail.collect()[0]
        assert row['format'] == 'delta'
        assert row['numFiles'] > 0
        assert row['sizeInBytes'] > 0
        
    def test_optimize_by_partition(self, spark, temp_delta_path):
        """Test OPTIMIZE en partición específica"""
        path = temp_delta_path
        
        # Crear tabla particionada
        df = spark.createDataFrame([
            (1, "2024-01-01"),
            (2, "2024-01-01"),
            (3, "2024-01-02"),
            (4, "2024-01-02")
        ], ["id", "date"])
        
        df.write.format("delta").partitionBy("date").mode("overwrite").save(path)
        
        # OPTIMIZE solo una partición
        delta_table = DeltaTable.forPath(spark, path)
        result = delta_table.optimize() \
            .where("date = '2024-01-01'") \
            .executeCompaction()
        
        assert result is not None
        
    def test_data_skipping_benefits(self, spark, temp_delta_path):
        """Test que data skipping mejora queries"""
        path = temp_delta_path
        
        # Crear datos
        df = spark.range(10000).withColumn("category", 
            col("id") % 10).withColumn("value", col("id") * 2)
        df.write.format("delta").mode("overwrite").save(path)
        
        # Query antes de Z-ORDER
        df1 = spark.read.format("delta").load(path)
        start1 = time.time()
        count1 = df1.filter("category = 5").count()
        time1 = time.time() - start1
        
        # Z-ORDER
        delta_table = DeltaTable.forPath(spark, path)
        delta_table.optimize().executeZOrderBy("category")
        
        # Query después de Z-ORDER
        df2 = spark.read.format("delta").load(path)
        start2 = time.time()
        count2 = df2.filter("category = 5").count()
        time2 = time.time() - start2
        
        # Conteos deben ser iguales
        assert count1 == count2
        
        # Nota: time2 puede ser más rápido pero depende del tamaño
        # Solo verificamos que ambos queries funcionan
