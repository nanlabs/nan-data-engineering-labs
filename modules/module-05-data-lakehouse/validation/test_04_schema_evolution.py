"""Tests de validación para Ejercicio 04: Schema Evolution"""
import pytest
import sys
import os
from pathlib import Path
from pyspark.sql.functions import col, lit
from pyspark.sql.types import DecimalType

# Agregar path de solución
exercise_path = Path(__file__).parent.parent / "exercises" / "04-schema-evolution" / "solution"
sys.path.insert(0, str(exercise_path))


def test_add_column_with_merge_schema(spark, temp_delta_path):
    """Test agregar columna con mergeSchema"""
    path = temp_delta_path
    
    # Tabla inicial
    df1 = spark.createDataFrame([(1, "A"), (2, "B")], ["id", "name"])
    df1.write.format("delta").mode("overwrite").save(path)
    
    # Agregar columna
    df2 = spark.createDataFrame([(3, "C", 100)], ["id", "name", "value"])
    df2.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
    
    result = spark.read.format("delta").load(path)
    assert "value" in result.columns
    assert result.count() == 3


def test_change_column_type(spark, temp_delta_path):
    """Test cambiar tipo de columna"""
    path = temp_delta_path
    
    # Crear con int
    df1 = spark.createDataFrame([(1, 100), (2, 200)], ["id", "amount"])
    df1.write.format("delta").mode("overwrite").save(path)
    
    # Cambiar a Decimal
    df_retyped = spark.read.format("delta").load(path) \
        .withColumn("amount", col("amount").cast(DecimalType(10, 2)))
    
    df_retyped.write.format("delta").mode("overwrite") \
        .option("overwriteSchema", "true").save(path)
    
    # Verificar tipo
    schema = spark.read.format("delta").load(path).schema
    amount_field = [f for f in schema.fields if f.name == "amount"][0]
    assert isinstance(amount_field.dataType, DecimalType)


def test_schema_history_tracking(spark, temp_delta_path):
    """Test que el historial muestra cambios de schema"""
    from delta.tables import DeltaTable
    path = temp_delta_path
    
    # V0
    df1 = spark.createDataFrame([(1, "A")], ["id", "name"])
    df1.write.format("delta").mode("overwrite").save(path)
    
    # V1 con nueva columna
    df2 = spark.createDataFrame([(2, "B", 100)], ["id", "name", "value"])
    df2.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
    
    delta_table = DeltaTable.forPath(spark, path)
    history = delta_table.history().collect()
    
    assert len(history) >= 2
