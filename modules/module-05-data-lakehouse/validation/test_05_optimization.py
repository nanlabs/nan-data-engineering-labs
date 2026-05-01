"""Tests de validación para Ejercicio 05: Optimization"""
import pytest
import sys
import os
from pathlib import Path

# Agregar path de solución
exercise_path = Path(__file__).parent.parent / "exercises" / "05-optimization" / "solution"
sys.path.insert(0, str(exercise_path))


def test_optimize_reduces_files(spark, temp_delta_path):
    """Test que OPTIMIZE reduce archivos"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    # Crear muchos archivos pequeños
    for i in range(10):
        df = spark.range(i * 100, (i + 1) * 100)
        df.write.format("delta").mode("append").save(path)
    
    delta_table = DeltaTable.forPath(spark, path)
    files_before = delta_table.detail().select("numFiles").collect()[0][0]
    
    # OPTIMIZE
    delta_table.optimize().executeCompaction()
    
    delta_table = DeltaTable.forPath(spark, path)
    files_after = delta_table.detail().select("numFiles").collect()[0][0]
    
    assert files_after < files_before


def test_z_order_executes(spark, temp_delta_path):
    """Test que Z-ORDER ejecuta correctamente"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    df = spark.createDataFrame([
        (1, "USA", "2024-01-01"),
        (2, "UK", "2024-01-02")
    ], ["id", "country", "date"])
    df.write.format("delta").mode("overwrite").save(path)
    
    delta_table = DeltaTable.forPath(spark, path)
    result = delta_table.optimize().executeZOrderBy("country", "date")
    
    assert result is not None


def test_vacuum_cleanup(spark, temp_delta_path):
    """Test que VACUUM limpia archivos"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    # V0
    df1 = spark.range(100)
    df1.write.format("delta").mode("overwrite").save(path)
    
    # V1
    df2 = spark.range(200)
    df2.write.format("delta").mode("overwrite").save(path)
    
    # VACUUM
    delta_table = DeltaTable.forPath(spark, path)
    spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
    delta_table.vacuum(0)
    
    # V0 no debe ser accesible después de vacuum
    with pytest.raises(Exception):
        spark.read.format("delta").option("versionAsOf", 0).load(path).count()
