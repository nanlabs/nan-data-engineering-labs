"""Tests para Ejercicio 04: Schema Evolution"""
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit
from pyspark.sql.types import DecimalType, StringType, IntegerType
from delta.tables import DeltaTable


class TestSchemaEvolution:
    """Tests para Schema Evolution en Delta Lake"""

    def test_add_column_merge_schema(self, spark, temp_delta_path):
        """Test agregar columna con mergeSchema"""
        path = temp_delta_path
        
        # Crear tabla inicial
        df1 = spark.createDataFrame([(1, "A"), (2, "B")], ["id", "name"])
        df1.write.format("delta").mode("overwrite").save(path)
        
        # Agregar columna
        df2 = spark.createDataFrame([(3, "C", 100)], ["id", "name", "value"])
        df2.write.format("delta").mode("append") \
            .option("mergeSchema", "true").save(path)
        
        # Verificar
        result = spark.read.format("delta").load(path)
        assert "value" in result.columns
        assert result.count() == 3
        
    def test_change_column_type(self, spark, temp_delta_path):
        """Test cambiar tipo de columna"""
        path = temp_delta_path
        
        # Crear tabla con int
        df1 = spark.createDataFrame([(1, 100), (2, 200)], ["id", "amount"])
        df1.write.format("delta").mode("overwrite").save(path)
        
        # Cambiar a Decimal
        df_retyped = spark.read.format("delta").load(path) \
            .withColumn("amount", col("amount").cast(DecimalType(10, 2)))
        
        df_retyped.write.format("delta").mode("overwrite") \
            .option("overwriteSchema", "true").save(path)
        
        # Verificar tipo
        result_schema = spark.read.format("delta").load(path).schema
        amount_type = [f.dataType for f in result_schema.fields if f.name == "amount"][0]
        assert isinstance(amount_type, DecimalType)
        
    def test_without_merge_schema_fails(self, spark, temp_delta_path):
        """Test que sin mergeSchema falla al agregar columna"""
        path = temp_delta_path
        
        # Crear tabla inicial
        df1 = spark.createDataFrame([(1, "A")], ["id", "name"])
        df1.write.format("delta").mode("overwrite").save(path)
        
        # Intentar agregar columna sin mergeSchema
        df2 = spark.createDataFrame([(2, "B", 100)], ["id", "name", "value"])
        
        with pytest.raises(Exception):  # AnalysisException
            df2.write.format("delta").mode("append").save(path)
            
    def test_schema_history(self, spark, temp_delta_path):
        """Test que el historial muestra cambios de schema"""
        path = temp_delta_path
        
        # V0: Tabla inicial
        df1 = spark.createDataFrame([(1, "A")], ["id", "name"])
        df1.write.format("delta").mode("overwrite").save(path)
        
        # V1: Agregar columna
        df2 = spark.createDataFrame([(2, "B", 100)], ["id", "name", "value"])
        df2.write.format("delta").mode("append") \
            .option("mergeSchema", "true").save(path)
        
        # Verificar historial
        delta_table = DeltaTable.forPath(spark, path)
        history = delta_table.history().collect()
        
        # Debe tener al menos 2 versiones
        assert len(history) >= 2
        
        # V1 debe tener mergeSchema=true en operationParameters
        v1_params = history[0]['operationParameters']
        if v1_params and 'mergeSchema' in v1_params:
            assert v1_params['mergeSchema'] == 'true'
            
    def test_backward_compatible_read(self, spark, temp_delta_path):
        """Test lectura backward compatible con columnas faltantes"""
        path = temp_delta_path
        
        # V0: Tabla con 2 columnas
        df1 = spark.createDataFrame([(1, "A")], ["id", "name"])
        df1.write.format("delta").mode("overwrite").save(path)
        
        # V1: Agregar columna
        df2 = spark.createDataFrame([(2, "B", 100)], ["id", "name", "value"])
        df2.write.format("delta").mode("append") \
            .option("mergeSchema", "true").save(path)
        
        # Leer solo columnas originales (backward compatible)
        df_old_schema = spark.read.format("delta").load(path).select("id", "name")
        assert df_old_schema.count() == 2
        assert "value" not in df_old_schema.columns
        
    def test_remove_column_projection(self, spark, temp_delta_path):
        """Test 'eliminar' columna mediante proyección"""
        path = temp_delta_path
        
        # Crear tabla con 3 columnas
        df = spark.createDataFrame([(1, "A", 100)], ["id", "name", "to_remove"])
        df.write.format("delta").mode("overwrite").save(path)
        
        # 'Eliminar' columna to_remove
        df_filtered = spark.read.format("delta").load(path).select("id", "name")
        df_filtered.write.format("delta").mode("overwrite") \
            .option("overwriteSchema", "true").save(path)
        
        # Verificar
        result = spark.read.format("delta").load(path)
        assert "to_remove" not in result.columns
        assert set(result.columns) == {"id", "name"}
