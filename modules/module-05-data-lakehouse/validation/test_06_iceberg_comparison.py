"""Tests de validación para Ejercicio 06: Delta vs Iceberg Comparison"""
import pytest
import sys
import os
from pathlib import Path

# Agregar path de solución
exercise_path = Path(__file__).parent.parent / "exercises" / "06-iceberg-comparison" / "solution"
sys.path.insert(0, str(exercise_path))


def test_delta_basic_operations(spark, temp_delta_path):
    """Test operaciones básicas de Delta Lake"""
    path = temp_delta_path
    
    df = spark.range(1000)
    df.write.format("delta").mode("overwrite").save(path)
    
    result = spark.read.format("delta").load(path)
    assert result.count() == 1000


def test_delta_time_travel_works(spark, temp_delta_path):
    """Test Time Travel en Delta Lake"""
    path = temp_delta_path
    
    # V0
    df1 = spark.range(100)
    df1.write.format("delta").mode("overwrite").save(path)
    
    # V1
    df2 = spark.range(100, 200)
    df2.write.format("delta").mode("append").save(path)
    
    # Query V0
    v0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
    assert v0.count() == 100
    
    # Query actual
    current = spark.read.format("delta").load(path)
    assert current.count() == 200


# Nota: Tests de Iceberg están marcados como skip porque requieren
# configuración adicional (Hive Metastore, JARs de Iceberg, etc.)
@pytest.mark.skip(reason="Iceberg requiere configuración adicional")
def test_iceberg_basic_operations():
    """Test básico de Iceberg (requiere configuración especial)"""
    # Este test requiere:
    # 1. Hive Metastore corriendo
    # 2. Iceberg JARs en classpath
    # 3. Configuración de catalog Iceberg
    pass


@pytest.mark.skip(reason="Iceberg requiere configuración adicional")  
def test_iceberg_time_travel():
    """Test Time Travel en Iceberg (requiere configuración especial)"""
    pass
