"""Ejercicio 06: Error Handling - Starter"""

import pandas as pd
import logging
from typing import Any, Callable


def leer_archivo_seguro(ruta: str) -> pd.DataFrame:
    """Lee archivo con manejo de errores."""
    # TODO: try/except con FileNotFoundError, pd.errors.EmptyDataError
    pass


def validar_schema(df: pd.DataFrame, schema: dict[str, type]) -> tuple[bool, list[str]]:
    """Valida que DataFrame cumple schema."""
    # TODO: verifica columnas y tipos
    pass


def procesar_con_retry(func: Callable, *args, max_retries: int = 3) -> Any:
    """Ejecuta función con retry logic."""
    # TODO: intenta max_retries veces, espera entre intentos
    pass


def log_operacion(func: Callable) -> Callable:
    """Decorator que logea operaciones."""
    # TODO: logea antes y después de ejecutar función
    pass


def validar_rango(df: pd.DataFrame, columna: str, min_val: float, max_val: float) -> bool:
    """Valida que valores están en rango."""
    # TODO: verifica todos los valores
    pass


def manejar_nulls_inteligente(df: pd.DataFrame) -> pd.DataFrame:
    """Maneja nulls según tipo de columna."""
    # TODO: numéricos -> median, strings -> "Unknown", dates -> forward fill
    pass


def pipeline_con_checkpoint(steps: list[Callable], checkpoint_dir: str) -> Any:
    """Pipeline que guarda checkpoints."""
    # TODO: ejecuta steps, guarda progreso después de cada uno
    pass


def validar_tipos_datos(df: pd.DataFrame, schema: dict[str, str]) -> list[str]:
    """Valida tipos de datos."""
    # TODO: retorna lista de errores
    pass


def procesar_batch_seguro(archivos: list[str]) -> dict[str, Any]:
    """Procesa batch de archivos con error handling."""
    # TODO: procesa cada archivo, registra éxitos y fallos
    pass


def pipeline_production(config: dict[str, Any]) -> None:
    """Pipeline production-ready."""
    # TODO: logging, validation, error handling, checkpoints
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("⚠️  Implementa error handling robusto")
