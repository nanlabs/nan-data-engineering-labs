"""
Ejercicio 04: Pandas Fundamentals - Starter

TODO: Implementa las 10 funciones usando pandas
"""

import pandas as pd
from typing import Any


def cargar_y_explorar(ruta: str) -> dict[str, Any]:
    """Carga CSV y retorna info básica."""
    # TODO: shape, columnas, tipos, nulls
    pass


def filtrar_por_pais(df: pd.DataFrame, pais: str) -> pd.DataFrame:
    """Filtra DataFrame por país."""
    # TODO: df[df['country'] == pais]
    pass


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia nulls y duplicados."""
    # TODO: dropna() y drop_duplicates()
    pass


def calcular_estadisticas(df: pd.DataFrame, columna: str) -> dict[str, float]:
    """Calcula mean, median, std de una columna."""
    # TODO: usa df[columna].mean(), median(), std()
    pass


def agrupar_por_columna(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Agrupa y cuenta por columna."""
    # TODO: df.groupby(columna).size()
    pass


def top_n_registros(df: pd.DataFrame, columna: str, n: int = 10) -> pd.DataFrame:
    """Retorna top N valores."""
    # TODO: df.nlargest(n, columna)
    pass


def detectar_outliers(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Detecta outliers usando IQR."""
    # TODO: Q1, Q3, IQR = Q3 - Q1, outliers fuera de [Q1-1.5*IQR, Q3+1.5*IQR]
    pass


def merge_datasets(df1: pd.DataFrame, df2: pd.DataFrame, on: str) -> pd.DataFrame:
    """Hace merge de dos DataFrames."""
    # TODO: pd.merge(df1, df2, on=on)
    pass


def crear_columna_calculada(df: pd.DataFrame, formula: str) -> pd.DataFrame:
    """Crea columna usando eval."""
    # TODO: df.eval(formula, inplace=False)
    pass


def resumen_completo(df: pd.DataFrame) -> dict[str, Any]:
    """Genera resumen completo del DataFrame."""
    # TODO: shape, dtypes, nulls, duplicados, describe
    pass


if __name__ == "__main__":
    print("⚠️  Implementa las funciones y ejecuta tests")
