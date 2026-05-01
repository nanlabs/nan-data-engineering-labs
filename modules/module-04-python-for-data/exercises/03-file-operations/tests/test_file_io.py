"""
Tests para Ejercicio 03: File Operations
"""

import pytest
import pandas as pd
import json
import os
from pathlib import Path
from exercises.03_file_operations.solution import file_io


@pytest.fixture
def temp_dir(tmp_path):
    """Directorio temporal para tests."""
    return tmp_path


@pytest.fixture
def sample_df():
    """DataFrame de ejemplo."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "nombre": ["Ana", "Luis", "María"],
        "edad": [25, 30, 28]
    })


class TestLeerCSV:
    """Tests para leer_csv()."""
    
    def test_leer_csv_real(self):
        """Lee CSV real de customers."""
        df = file_io.leer_csv("data/raw/customers.csv")
        assert len(df) == 10000
        assert "customer_id" in df.columns
    
    def test_leer_csv_simple(self, temp_dir, sample_df):
        """Lee CSV simple."""
        csv_path = temp_dir / "test.csv"
        sample_df.to_csv(csv_path, index=False)
        
        df = file_io.leer_csv(str(csv_path))
        assert len(df) == 3
        assert list(df.columns) == ["id", "nombre", "edad"]


class TestEscribirCSV:
    """Tests para escribir_csv()."""
    
    def test_escribir_csv(self, temp_dir, sample_df):
        """Escribe CSV."""
        csv_path = temp_dir / "output.csv"
        file_io.escribir_csv(sample_df, str(csv_path))
        
        assert csv_path.exists()
        df_leido = pd.read_csv(csv_path)
        assert len(df_leido) == 3


class TestLeerJSON:
    """Tests para leer_json()."""
    
    def test_leer_json_real(self):
        """Lee JSON real de orders."""
        datos = file_io.leer_json("data/raw/orders.json")
        assert isinstance(datos, list)
        assert len(datos) == 50000
    
    def test_leer_json_dict(self, temp_dir):
        """Lee JSON dict."""
        json_path = temp_dir / "test.json"
        datos = {"nombre": "Ana", "edad": 25}
        
        with open(json_path, "w") as f:
            json.dump(datos, f)
        
        resultado = file_io.leer_json(str(json_path))
        assert resultado == datos


class TestEscribirJSON:
    """Tests para escribir_json()."""
    
    def test_escribir_json(self, temp_dir):
        """Escribe JSON."""
        json_path = temp_dir / "output.json"
        datos = {"nombre": "Ana", "edad": 25}
        
        file_io.escribir_json(datos, str(json_path))
        
        assert json_path.exists()
        with open(json_path, "r") as f:
            leido = json.load(f)
        assert leido == datos


class TestCSVAParquet:
    """Tests para csv_a_parquet()."""
    
    def test_conversion(self, temp_dir, sample_df):
        """Convierte CSV a Parquet."""
        csv_path = temp_dir / "test.csv"
        parquet_path = temp_dir / "test.parquet"
        
        sample_df.to_csv(csv_path, index=False)
        file_io.csv_a_parquet(str(csv_path), str(parquet_path))
        
        assert parquet_path.exists()
        df = pd.read_parquet(parquet_path)
        assert len(df) == 3


class TestContarRegistros:
    """Tests para contar_registros()."""
    
    def test_contar_csv(self):
        """Cuenta registros en CSV."""
        count = file_io.contar_registros("data/raw/customers.csv")
        assert count == 10000
    
    def test_contar_json(self):
        """Cuenta registros en JSON."""
        count = file_io.contar_registros("data/raw/orders.json")
        assert count == 50000


class TestObtenerColumnasCSV:
    """Tests para obtener_columnas_csv()."""
    
    def test_obtener_columnas(self):
        """Obtiene columnas de CSV."""
        columnas = file_io.obtener_columnas_csv("data/raw/customers.csv")
        assert "customer_id" in columnas
        assert "first_name" in columnas


class TestFiltrarCSV:
    """Tests para filtrar_csv()."""
    
    def test_filtrar(self, temp_dir, sample_df):
        """Filtra CSV."""
        entrada = temp_dir / "entrada.csv"
        salida = temp_dir / "salida.csv"
        
        sample_df.to_csv(entrada, index=False)
        
        # Filtrar edad >= 28
        file_io.filtrar_csv(
            str(entrada),
            str(salida),
            lambda df: df[df["edad"] >= 28]
        )
        
        df_filtrado = pd.read_csv(salida)
        assert len(df_filtrado) == 2
        assert all(df_filtrado["edad"] >= 28)


class TestCombinarCSVs:
    """Tests para combinar_csvs()."""
    
    def test_combinar(self, temp_dir):
        """Combina múltiples CSVs."""
        df1 = pd.DataFrame({"id": [1, 2], "valor": [10, 20]})
        df2 = pd.DataFrame({"id": [3, 4], "valor": [30, 40]})
        
        csv1 = temp_dir / "parte1.csv"
        csv2 = temp_dir / "parte2.csv"
        salida = temp_dir / "completo.csv"
        
        df1.to_csv(csv1, index=False)
        df2.to_csv(csv2, index=False)
        
        file_io.combinar_csvs([str(csv1), str(csv2)], str(salida))
        
        df_combinado = pd.read_csv(salida)
        assert len(df_combinado) == 4
        assert list(df_combinado["id"]) == [1, 2, 3, 4]


class TestJSONaCSVPlano:
    """Tests para json_a_csv_plano()."""
    
    def test_aplanar(self, temp_dir):
        """Aplana JSON anidado."""
        json_path = temp_dir / "anidado.json"
        csv_path = temp_dir / "plano.csv"
        
        datos = [
            {"id": 1, "user": {"name": "Ana", "age": 25}},
            {"id": 2, "user": {"name": "Luis", "age": 30}}
        ]
        
        with open(json_path, "w") as f:
            json.dump(datos, f)
        
        file_io.json_a_csv_plano(str(json_path), str(csv_path))
        
        df = pd.read_csv(csv_path)
        assert "user.name" in df.columns or "user_name" in str(df.columns)
        assert len(df) == 2
