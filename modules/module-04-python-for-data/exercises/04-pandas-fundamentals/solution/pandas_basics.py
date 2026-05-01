"""
Ejercicio 04: Pandas Fundamentals - Solution
"""

import pandas as pd
from typing import Any


def cargar_y_explorar(ruta: str) -> dict[str, Any]:
    df = pd.read_csv(ruta)
    return {
        "filas": len(df),
        "columnas": len(df.columns),
        "columnas_nombres": list(df.columns),
        "tipos": df.dtypes.to_dict(),
        "nulls": df.isnull().sum().to_dict()
    }


def filtrar_por_pais(df: pd.DataFrame, pais: str) -> pd.DataFrame:
    return df[df['country'] == pais].copy()


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna().drop_duplicates()


def calcular_estadisticas(df: pd.DataFrame, columna: str) -> dict[str, float]:
    return {
        "mean": float(df[columna].mean()),
        "median": float(df[columna].median()),
        "std": float(df[columna].std())
    }


def agrupar_por_columna(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    return df.groupby(columna).size().reset_index(name='count')


def top_n_registros(df: pd.DataFrame, columna: str, n: int = 10) -> pd.DataFrame:
    return df.nlargest(n, columna)


def detectar_outliers(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    Q1 = df[columna].quantile(0.25)
    Q3 = df[columna].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[columna] < lower) | (df[columna] > upper)]


def merge_datasets(df1: pd.DataFrame, df2: pd.DataFrame, on: str) -> pd.DataFrame:
    return pd.merge(df1, df2, on=on, how='inner')


def crear_columna_calculada(df: pd.DataFrame, formula: str) -> pd.DataFrame:
    return df.eval(formula, inplace=False)


def resumen_completo(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "shape": df.shape,
        "columnas": list(df.columns),
        "tipos": df.dtypes.to_dict(),
        "nulls_total": int(df.isnull().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
        "memoria_mb": df.memory_usage(deep=True).sum() / 1024**2,
        "describe": df.describe().to_dict()
    }


if __name__ == "__main__":
    print("📊 Pandas Fundamentals - Soluciones completas")
