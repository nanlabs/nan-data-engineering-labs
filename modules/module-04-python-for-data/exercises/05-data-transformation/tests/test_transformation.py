"""Tests para Ejercicio 05: Data Transformation"""

import pytest
import pandas as pd
from exercises.05_data_transformation.solution import transformation


class TestTransformation:
    def test_extraer_datos(self):
        rutas = {"customers": "data/raw/customers.csv"}
        dfs = transformation.extraer_datos(rutas)
        assert "customers" in dfs
        assert len(dfs["customers"]) == 10000
    
    def test_limpiar_customers(self):
        df = pd.read_csv("data/raw/customers.csv")
        limpio = transformation.limpiar_customers(df)
        assert limpio['customer_id'].nunique() == len(limpio)
    
    def test_generar_reporte_calidad(self):
        df = pd.DataFrame({"a": [1, 2, None], "b": [1, 2, 3]})
        reporte = transformation.generar_reporte_calidad(df)
        assert "completitud" in reporte
        assert reporte["filas"] == 3
