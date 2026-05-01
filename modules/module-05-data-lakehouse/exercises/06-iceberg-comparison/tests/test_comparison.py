"""Tests para Ejercicio 06: Delta Lake vs Iceberg Comparison"""
import pytest
from pyspark.sql import SparkSession
from delta.tables import DeltaTable


class TestComparison:
    """Tests para comparación Delta Lake vs Iceberg"""

    def test_delta_write_read(self, spark, temp_delta_path):
        """Test escritura y lectura básica en Delta Lake"""
        path = temp_delta_path
        
        # Crear datos
        df = spark.range(1000)
        
        # Escribir
        df.write.format("delta").mode("overwrite").save(path)
        
        # Leer
        result = spark.read.format("delta").load(path)
        
        assert result.count() == 1000
        
    def test_delta_time_travel(self, spark, temp_delta_path):
        """Test Time Travel en Delta Lake"""
        path = temp_delta_path
        
        # V0
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        
        # V1
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        
        # Leer V0
        v0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
        assert v0.count() == 100
        
        # Leer V1 (actual)
        v1 = spark.read.format("delta").load(path)
        assert v1.count() == 200
        
    def test_delta_update(self, spark, temp_delta_path):
        """Test UPDATE en Delta Lake"""
        path = temp_delta_path
        
        # Crear tabla
        df = spark.createDataFrame([(1, "A"), (2, "B")], ["id", "status"])
        df.write.format("delta").mode("overwrite").save(path)
        
        # Update
        delta_table = DeltaTable.forPath(spark, path)
        delta_table.update(
            condition="status = 'A'",
            set={"status": "'UPDATED'"}
        )
        
        # Verificar
        result = spark.read.format("delta").load(path)
        updated_count = result.filter("status = 'UPDATED'").count()
        assert updated_count == 1
        
    def test_delta_schema_evolution(self, spark, temp_delta_path):
        """Test Schema Evolution en Delta Lake"""
        path = temp_delta_path
        
        # Tabla inicial
        df1 = spark.createDataFrame([(1, "A")], ["id", "name"])
        df1.write.format("delta").mode("overwrite").save(path)
        
        # Agregar columna
        from pyspark.sql.functions import lit
        df2 = spark.createDataFrame([(2, "B")], ["id", "name"]) \
            .withColumn("new_col", lit(100))
        
        df2.write.format("delta").mode("append") \
            .option("mergeSchema", "true").save(path)
        
        # Verificar
        result = spark.read.format("delta").load(path)
        assert "new_col" in result.columns
        assert result.count() == 2
        
    # Nota: Tests de Iceberg requieren configuración más compleja
    # y pueden fallar si Iceberg no está disponible
    @pytest.mark.skip(reason="Iceberg requiere configuración adicional")
    def test_iceberg_basic(self, spark_with_iceberg):
        """Test básico de Iceberg (requiere configuración especial)"""
        # Este test está disabled por defecto
        # porque requiere Hive Metastore y configuración Iceberg
        pass
        
    def test_performance_comparison_concept(self, spark, temp_delta_path):
        """Test concepto de comparación de performance"""
        import time
        path = temp_delta_path
        
        df = spark.range(10000)
        
        # Medir write
        start = time.time()
        df.write.format("delta").mode("overwrite").save(path)
        write_time = time.time() - start
        
        # Medir read
        start = time.time()
        result = spark.read.format("delta").load(path)
        count = result.count()
        read_time = time.time() - start
        
        # Verificar que las métricas existen
        assert write_time > 0
        assert read_time > 0
        assert count == 10000
        
    def test_delta_optimize(self, spark, temp_delta_path):
        """Test OPTIMIZE en Delta Lake"""
        path = temp_delta_path
        
        # Crear archivos pequeños
        for i in range(5):
            df = spark.range(i * 100, (i + 1) * 100)
            df.write.format("delta").mode("append").save(path)
        
        # OPTIMIZE
        delta_table = DeltaTable.forPath(spark, path)
        delta_table.optimize().executeCompaction()
        
        # Verificar que se completó
        result = spark.read.format("delta").load(path)
        assert result.count() == 500
