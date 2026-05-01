"""Ejercicio 05: Data Transformation - Starter"""

import pandas as pd
from typing import Any


def extraer_datos(rutas: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Extrae múltiples datasets."""
    # TODO: lee todos los archivos y retorna dict con DataFrames
    pass


def limpiar_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia dataset de customers."""
    # TODO: remove nulls, duplicados, normaliza nombres
    pass


def flatten_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Aplana estructura anidada de orders."""
    # TODO: usa pd.json_normalize si es necesario
    pass


def calcular_metricas_orden(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula total_amount por orden."""
    # TODO: suma items, aplica descuento
    pass


def join_customers_orders(customers: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Join entre customers y orders."""
    # TODO: pd.merge on customer_id
    pass


def agregar_ventas_por_cliente(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega ventas por cliente."""
    # TODO: groupby customer_id, suma totales
    pass


def detectar_problemas_calidad(df: pd.DataFrame) -> dict[str, Any]:
    """Detecta problemas de calidad."""
    # TODO: nulls, duplicados, outliers, tipos incorrectos
    pass


def normalizar_fechas(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Normaliza columnas de fecha."""
    # TODO: pd.to_datetime para cada columna
    pass


def pipeline_etl_completo(source_dir: str, dest_dir: str) -> None:
    """Pipeline ETL completo."""
    # TODO: Extract -> Transform -> Load
    pass


def generar_reporte_calidad(df: pd.DataFrame) -> dict[str, Any]:
    """Genera reporte de calidad."""
    # TODO: métricas de completitud, consistencia, validez
    pass


if __name__ == "__main__":
    print("⚠️  Implementa el pipeline ETL")
