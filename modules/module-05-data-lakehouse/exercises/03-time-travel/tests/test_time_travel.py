"""Tests para Ejercicio 03: Time Travel"""
import pytest
from pyspark.sql import SparkSession
from delta.tables import DeltaTable
import sys
import os

# Añadir el directorio de solución al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../solution'))


class TestTimeTravel:
    """Tests para operaciones de Time Travel"""

    def test_versions_created(self, spark, temp_delta_path):
        """Test que se crean múltiples versiones"""
        # Simular creación de versiones
        path = temp_delta_path
        
        # V0
        df = spark.range(100)
        df.write.format("delta").mode("overwrite").save(path)
        
        # V1
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        
        # Verificar historial
        delta_table = DeltaTable.forPath(spark, path)
        history = delta_table.history().collect()
        assert len(history) >= 2, "Debe haber al menos 2 versiones"
        
    def test_version_as_of(self, spark, temp_delta_path):
        """Test lectura con versionAsOf"""
        path = temp_delta_path
        
        # Crear V0
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        count_v0 = 100
        
        # Crear V1
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        count_v1 = 200
        
        # Leer V0
        v0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
        assert v0.count() == count_v0
        
        # Leer V1 (actual)
        v1 = spark.read.format("delta").load(path)
        assert v1.count() == count_v1
        
    def test_timestamp_as_of(self, spark, temp_delta_path):
        """Test lectura con timestampAsOf"""
        path = temp_delta_path
        
        # Crear versiones
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        
        # Obtener timestamp de V0
        delta_table = DeltaTable.forPath(spark, path)
        history = delta_table.history().collect()
        v0_timestamp = history[-1]['timestamp']
        
        # Leer por timestamp
        v0_by_time = spark.read.format("delta") \
            .option("timestampAsOf", str(v0_timestamp)) \
            .load(path)
        
        assert v0_by_time.count() == 100
        
    def test_rollback(self, spark, temp_delta_path):
        """Test rollback a versión anterior"""
        path = temp_delta_path
        
        # V0: 100 registros
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        
        # V1: 200 registros
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        
        # V2: Delete (150 registros)
        delta_table = DeltaTable.forPath(spark, path)
        delta_table.delete("id > 150")
        
        current = spark.read.format("delta").load(path).count()
        assert current == 151  # 0-150 inclusive
        
        # Rollback a V1
        v1_df = spark.read.format("delta").option("versionAsOf", 1).load(path)
        v1_df.write.format("delta").mode("overwrite") \
            .option("overwriteSchema", "true").save(path)
        
        # Verificar rollback
        after_rollback = spark.read.format("delta").load(path).count()
        assert after_rollback == 200
        
    def test_history_tracking(self, spark, temp_delta_path):
        """Test que history() funciona correctamente"""
        path = temp_delta_path
        
        # Crear múltiples versiones
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        
        delta_table = DeltaTable.forPath(spark, path)
        delta_table.update(condition="id < 50", set={"id": "999"})
        
        # Verificar historial
        history = delta_table.history().collect()
        operations = [h['operation'] for h in history]
        
        assert 'WRITE' in operations or 'CREATE' in operations
        assert 'UPDATE' in operations
        
    def test_sql_time_travel(self, spark, temp_delta_path):
        """Test SQL Time Travel"""
        path = temp_delta_path
        
        # Crear versiones
        df1 = spark.range(100)
        df1.write.format("delta").mode("overwrite").save(path)
        
        df2 = spark.range(100, 200)
        df2.write.format("delta").mode("append").save(path)
        
        # Registrar como tabla temporal
        spark.read.format("delta").load(path).createOrReplaceTempView("test_table")
        
        # Query SQL con VERSION AS OF
        result = spark.sql("SELECT COUNT(*) as cnt FROM test_table VERSION AS OF 0")
        count = result.collect()[0]['cnt']
        
        assert count == 100


@pytest.fixture
def temp_delta_path(tmp_path):
    """Fixture para path temporal de Delta"""
    return str(tmp_path / "delta_table")
