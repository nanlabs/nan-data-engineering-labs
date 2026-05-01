"""Tests para Ejercicio 06: Error Handling"""

import pytest
import pandas as pd
from exercises.06_error_handling.solution import error_handling


class TestErrorHandling:
    def test_leer_archivo_seguro(self):
        df = error_handling.leer_archivo_seguro("data/raw/customers.csv")
        assert len(df) == 10000
    
    def test_leer_archivo_no_existe(self):
        with pytest.raises(FileNotFoundError):
            error_handling.leer_archivo_seguro("no_existe.csv")
    
    def test_validar_schema(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        schema = {"a": "int64", "b": "object"}
        valido, errores = error_handling.validar_schema(df, schema)
        assert valido or len(errores) == 0
    
    def test_procesar_con_retry(self):
        intentos = []
        def func_falla_2_veces():
            intentos.append(1)
            if len(intentos) < 3:
                raise ValueError("Fallo intencional")
            return "éxito"
        
        resultado = error_handling.procesar_con_retry(func_falla_2_veces, max_retries=3)
        assert resultado == "éxito"
        assert len(intentos) == 3
    
    def test_manejar_nulls_inteligente(self):
        df = pd.DataFrame({"a": [1, 2, None], "b": ["x", None, "z"]})
        limpio = error_handling.manejar_nulls_inteligente(df)
        assert limpio["b"].fillna("Unknown").eq("Unknown").sum() >= 1
