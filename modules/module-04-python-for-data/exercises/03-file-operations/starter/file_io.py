"""
Ejercicio 03: File Operations - Starter

Instrucciones:
1. Implementa todas las funciones marcadas con TODO
2. Usa context managers (with statement)
3. Maneja errores de I/O adecuadamente
4. Trabaja con los datasets en data/raw/
5. Ejecuta: pytest exercises/03-file-operations/tests/ -v
"""

import json
import os
from pathlib import Path
from typing import Any, Callable
import pandas as pd


def leer_csv(ruta: str) -> pd.DataFrame:
    """Lee un archivo CSV y retorna un DataFrame."""
    # TODO: Implementar lectura de CSV con pandas
    pass


def escribir_csv(df: pd.DataFrame, ruta: str, index: bool = False) -> None:
    """Escribe un DataFrame a CSV."""
    # TODO: Implementar escritura de CSV
    pass


def leer_json(ruta: str) -> Any:
    """Lee un archivo JSON y retorna dict/list."""
    # TODO: Implementar lectura de JSON
    # Usa context manager y json.load()
    pass


def escribir_json(datos: Any, ruta: str, indent: int = 2) -> None:
    """Escribe datos a JSON con formato legible."""
    # TODO: Implementar escritura de JSON
    # Usa indent=2 y ensure_ascii=False
    pass


def csv_a_parquet(csv_path: str, parquet_path: str) -> None:
    """Convierte CSV a Parquet."""
    # TODO: Lee CSV y escribe como Parquet
    # Usa compression="snappy"
    pass


def contar_registros(ruta: str) -> int:
    """Cuenta registros en archivo CSV/JSON."""
    # TODO: Detecta extensión y cuenta registros
    # Para CSV usa pd.read_csv, para JSON usa json.load
    pass


def obtener_columnas_csv(ruta: str) -> list[str]:
    """Obtiene nombres de columnas de un CSV."""
    # TODO: Lee CSV y retorna lista de columnas
    # Tip: df.columns.tolist()
    pass


def filtrar_csv(
    ruta_entrada: str, 
    ruta_salida: str, 
    condicion: Callable[[pd.DataFrame], pd.DataFrame]
) -> None:
    """Filtra CSV según condición y guarda resultado."""
    # TODO: Lee CSV, aplica condición (función), guarda resultado
    pass


def combinar_csvs(rutas: list[str], ruta_salida: str) -> None:
    """Combina múltiples CSVs en uno solo."""
    # TODO: Lee todos los CSVs y concaténalos
    # Tip: pd.concat([df1, df2, ...], ignore_index=True)
    pass


def json_a_csv_plano(json_path: str, csv_path: str) -> None:
    """Convierte JSON anidado a CSV plano (flatten)."""
    # TODO: Lee JSON, aplana estructura, guarda como CSV
    # Tip: pd.json_normalize() para aplanar
    pass


if __name__ == "__main__":
    print("⚠️  Implementa las funciones y ejecuta los tests")
    print("pytest exercises/03-file-operations/tests/ -v")
