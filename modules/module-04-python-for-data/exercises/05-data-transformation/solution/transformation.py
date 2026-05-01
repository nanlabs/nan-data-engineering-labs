"""Ejercicio 05: Data Transformation - Solution"""

import pandas as pd
from typing import Any
from pathlib import Path


def extraer_datos(rutas: dict[str, str]) -> dict[str, pd.DataFrame]:
    dfs = {}
    for nombre, ruta in rutas.items():
        if ruta.endswith('.csv'):
            dfs[nombre] = pd.read_csv(ruta)
        elif ruta.endswith('.json'):
            dfs[nombre] = pd.read_json(ruta)
    return dfs


def limpiar_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=['customer_id'])
    df = df.drop_duplicates(subset=['customer_id'])
    if 'first_name' in df.columns:
        df['first_name'] = df['first_name'].str.title()
    if 'last_name' in df.columns:
        df['last_name'] = df['last_name'].str.title()
    return df


def flatten_orders(df: pd.DataFrame) -> pd.DataFrame:
    if 'items' in df.columns:
        return pd.json_normalize(df.to_dict('records'), sep='_')
    return df


def calcular_metricas_orden(df: pd.DataFrame) -> pd.DataFrame:
    if 'total_amount' not in df.columns and 'price' in df.columns:
        df['total_amount'] = df['price'] * df.get('quantity', 1)
    return df


def join_customers_orders(customers: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(customers, orders, on='customer_id', how='inner')


def agregar_ventas_por_cliente(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby('customer_id')['total_amount'].agg(['sum', 'count', 'mean']).reset_index()


def detectar_problemas_calidad(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "nulls": df.isnull().sum().to_dict(),
        "duplicados": int(df.duplicated().sum()),
        "tipos": df.dtypes.to_dict()
    }


def normalizar_fechas(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    for col in columnas:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


def pipeline_etl_completo(source_dir: str, dest_dir: str) -> None:
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(f"{source_dir}/customers.csv")
    df = limpiar_customers(df)
    df.to_parquet(f"{dest_dir}/customers_clean.parquet")


def generar_reporte_calidad(df: pd.DataFrame) -> dict[str, Any]:
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    return {
        "completitud": (1 - null_cells / total_cells) * 100,
        "filas": df.shape[0],
        "columnas": df.shape[1],
        "nulls": int(null_cells),
        "duplicados": int(df.duplicated().sum())
    }


if __name__ == "__main__":
    print("🔄 Data Transformation - Pipeline ETL completo")
