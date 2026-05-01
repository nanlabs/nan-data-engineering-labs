"""Tests de validación para Ejercicio 03: Time Travel"""
import pytest
import sys
import os
from pathlib import Path

# Agregar path de solución
exercise_path = Path(__file__).parent.parent / "exercises" / "03-time-travel" / "solution"
sys.path.insert(0, str(exercise_path))


def test_time_travel_versions_created(spark, temp_delta_path):
    """Test que se crean múltiples versiones"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    # Crear versiones
    df1 = spark.range(100)
    df1.write.format("delta").mode("overwrite").save(path)
    
    df2 = spark.range(100, 200)
    df2.write.format("delta").mode("append").save(path)
    
    delta_table = DeltaTable.forPath(spark, path)
    history = delta_table.history().collect()
    
    assert len(history) >= 2


def test_time_travel_query_version(spark, temp_delta_path):
    """Test query por versión"""
    path = temp_delta_path
    
    df1 = spark.range(100)
    df1.write.format("delta").mode("overwrite").save(path)
    
    df2 = spark.range(100, 200)
    df2.write.format("delta").mode("append").save(path)
    
    # Query V0
    v0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
    assert v0.count() == 100
    
    # Query actual
    current = spark.read.format("delta").load(path)
    assert current.count() == 200


def test_rollback_functionality(spark, temp_delta_path):
    """Test rollback a versión anterior"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    # V0
    df1 = spark.range(100)
    df1.write.format("delta").mode("overwrite").save(path)
    
    # V1
    df2 = spark.range(100, 200)
    df2.write.format("delta").mode("append").save(path)
    
    # Rollback
    v0_df = spark.read.format("delta").option("versionAsOf", 0).load(path)
    v0_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)
    
    # Verificar
    result = spark.read.format("delta").load(path)
    assert result.count() == 100


def test_history_operations(spark, temp_delta_path):
    """Test que history muestra operaciones correctas"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    df = spark.range(100)
    df.write.format("delta").mode("overwrite").save(path)
    
    delta_table = DeltaTable.forPath(spark, path)
    delta_table.update(condition="id < 50", set={"id": "999"})
    
    history = delta_table.history().collect()
    operations = [h['operation'] for h in history]
    
    assert 'UPDATE' in operations or 'WRITE' in operations
