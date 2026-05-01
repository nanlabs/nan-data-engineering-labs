"""
Ejercicio 03: File Operations - Solution
"""

import json
import os
from pathlib import Path
from typing import Any, Callable
import pandas as pd


def leer_csv(ruta: str) -> pd.DataFrame:
    """Lee un archivo CSV y retorna un DataFrame."""
    return pd.read_csv(ruta)


def escribir_csv(df: pd.DataFrame, ruta: str, index: bool = False) -> None:
    """Escribe un DataFrame a CSV."""
    df.to_csv(ruta, index=index)


def leer_json(ruta: str) -> Any:
    """Lee un archivo JSON y retorna dict/list."""
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def escribir_json(datos: Any, ruta: str, indent: int = 2) -> None:
    """Escribe datos a JSON con formato legible."""
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=indent, ensure_ascii=False)


def csv_a_parquet(csv_path: str, parquet_path: str) -> None:
    """Convierte CSV a Parquet."""
    df = pd.read_csv(csv_path)
    df.to_parquet(parquet_path, compression="snappy")


def contar_registros(ruta: str) -> int:
    """Cuenta registros en archivo CSV/JSON."""
    extension = Path(ruta).suffix.lower()
    
    if extension == ".csv":
        df = pd.read_csv(ruta)
        return len(df)
    elif extension == ".json":
        datos = leer_json(ruta)
        if isinstance(datos, list):
            return len(datos)
        return 1
    else:
        raise ValueError(f"Formato no soportado: {extension}")


def obtener_columnas_csv(ruta: str) -> list[str]:
    """Obtiene nombres de columnas de un CSV."""
    df = pd.read_csv(ruta, nrows=0)
    return df.columns.tolist()


def filtrar_csv(
    ruta_entrada: str, 
    ruta_salida: str, 
    condicion: Callable[[pd.DataFrame], pd.DataFrame]
) -> None:
    """Filtra CSV según condición y guarda resultado."""
    df = pd.read_csv(ruta_entrada)
    df_filtrado = condicion(df)
    df_filtrado.to_csv(ruta_salida, index=False)


def combinar_csvs(rutas: list[str], ruta_salida: str) -> None:
    """Combina múltiples CSVs en uno solo."""
    dfs = [pd.read_csv(ruta) for ruta in rutas]
    df_combinado = pd.concat(dfs, ignore_index=True)
    df_combinado.to_csv(ruta_salida, index=False)


def json_a_csv_plano(json_path: str, csv_path: str) -> None:
    """Convierte JSON anidado a CSV plano (flatten)."""
    df = pd.read_json(json_path)
    df_plano = pd.json_normalize(df.to_dict("records"))
    df_plano.to_csv(csv_path, index=False)


if __name__ == "__main__":
    print("📁 File Operations - Soluciones")
    print("\n✅ Todas las funciones implementadas correctamente")
