# Ejercicio 06: Error Handling & Production Code

## Objetivos

✅ Manejo robusto de excepciones  
✅ Logging estructurado  
✅ Retry logic para operaciones fallidas  
✅ Input data validation
✅ Production-ready code

## Conceptos Clave

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Procesando datos")
logger.error("Error al leer archivo", exc_info=True)
```

### Try/Except

```python
try:
    df = pd.read_csv("datos.csv")
except FileNotFoundError:
    logger.error("Archivo no encontrado")
    raise
except Exception as e:
    logger.error(f"Error inesperado: {e}")
    raise
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def funcion_con_retry():
    # código que puede fallar
    pass
```

## Ejercicios

1. **leer_archivo_seguro**(ruta) → DataFrame con manejo de errores
2. **validar_schema**(df, schema) → bool + errores
3. **procesar_con_retry**(func, *args, max_retries=3) → resultado
4. **log_operacion**(func) → decorator que logea
5. **validar_rango**(df, column, min, max) → bool
6. **manejar_nulls_inteligente**(df) → DataFrame limpio
7. **pipeline_con_checkpoint**(steps, checkpoint_dir) → resultado
8. **validar_tipos_datos**(df, schema) → list[errores]
9. **procesar_batch_seguro**(archivos) → dict con resultados
10. **pipeline_production**(config) → pipeline completo con logging

## Execution

```bash
pytest exercises/06-error-handling/tests/ -v
```

✅ **Completaste todos los ejercicios!**
