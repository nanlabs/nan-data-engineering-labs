"""Tests para Ejercicio 04: Pandas Fundamentals"""

import pytest
import pandas as pd
from exercises.04_pandas_fundamentals.solution import pandas_basics


class TestPandasBasics:
    def test_cargar_y_explorar(self):
        info = pandas_basics.cargar_y_explorar("data/raw/customers.csv")
        assert info["filas"] == 10000
        assert "customer_id" in info["columnas_nombres"]
    
    def test_filtrar_por_pais(self):
        df = pd.read_csv("data/raw/customers.csv")
        df_usa = pandas_basics.filtrar_por_pais(df, "USA")
        assert all(df_usa["country"] == "USA")
    
    def test_limpiar_datos(self):
        df = pd.DataFrame({"a": [1, 2, 2, None], "b": [1, 2, 2, 4]})
        limpio = pandas_basics.limpiar_datos(df)
        assert len(limpio) == 2
        assert limpio.isnull().sum().sum() == 0
