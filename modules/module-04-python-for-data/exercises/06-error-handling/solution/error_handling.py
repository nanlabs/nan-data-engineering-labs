"""Ejercicio 06: Error Handling - Solution"""

import pandas as pd
import logging
import time
from typing import Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


def leer_archivo_seguro(ruta: str) -> pd.DataFrame:
    try:
        return pd.read_csv(ruta)
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {ruta}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Archivo vacío: {ruta}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise


def validar_schema(df: pd.DataFrame, schema: dict[str, type]) -> tuple[bool, list[str]]:
    errores = []
    for col, tipo in schema.items():
        if col not in df.columns:
            errores.append(f"Columna faltante: {col}")
        elif not pd.api.types.is_dtype_equal(df[col].dtype, tipo):
            errores.append(f"Tipo incorrecto en {col}: esperado {tipo}, obtenido {df[col].dtype}")
    return len(errores) == 0, errores


def procesar_con_retry(func: Callable, *args, max_retries: int = 3) -> Any:
    for intento in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            if intento == max_retries - 1:
                raise
            logger.warning(f"Intento {intento + 1} falló: {e}. Reintentando...")
            time.sleep(1)


def log_operacion(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        logger.info(f"Iniciando {func.__name__}")
        try:
            resultado = func(*args, **kwargs)
            logger.info(f"{func.__name__} completado exitosamente")
            return resultado
        except Exception as e:
            logger.error(f"{func.__name__} falló: {e}")
            raise
    return wrapper


def validar_rango(df: pd.DataFrame, columna: str, min_val: float, max_val: float) -> bool:
    return df[columna].between(min_val, max_val).all()


def manejar_nulls_inteligente(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col].fillna(df[col].median(), inplace=True)
        elif pd.api.types.is_string_dtype(df[col]):
            df[col].fillna("Unknown", inplace=True)
    return df


def pipeline_con_checkpoint(steps: list[Callable], checkpoint_dir: str) -> Any:
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
    resultado = None
    for i, step in enumerate(steps):
        resultado = step(resultado)
        checkpoint_file = f"{checkpoint_dir}/step_{i}.pkl"
        if isinstance(resultado, pd.DataFrame):
            resultado.to_pickle(checkpoint_file)
    return resultado


def validar_tipos_datos(df: pd.DataFrame, schema: dict[str, str]) -> list[str]:
    errores = []
    for col, tipo_esperado in schema.items():
        if col not in df.columns:
            errores.append(f"Columna faltante: {col}")
        elif str(df[col].dtype) != tipo_esperado:
            errores.append(f"Tipo incorrecto en {col}")
    return errores


def procesar_batch_seguro(archivos: list[str]) -> dict[str, Any]:
    resultados = {"exitos": [], "fallos": []}
    for archivo in archivos:
        try:
            df = leer_archivo_seguro(archivo)
            resultados["exitos"].append({"archivo": archivo, "filas": len(df)})
        except Exception as e:
            resultados["fallos"].append({"archivo": archivo, "error": str(e)})
    return resultados


def pipeline_production(config: dict[str, Any]) -> None:
    logger.info("Iniciando pipeline production")
    try:
        df = leer_archivo_seguro(config["input_file"])
        df = manejar_nulls_inteligente(df)
        df.to_csv(config["output_file"], index=False)
        logger.info("Pipeline completado")
    except Exception as e:
        logger.error(f"Pipeline falló: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🛡️ Error Handling - Production-ready code")
