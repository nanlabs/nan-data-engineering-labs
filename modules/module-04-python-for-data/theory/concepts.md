# Fundamental Concepts: Python for Data Engineering

## Table of Contents

1. [Introduction](#introduction)
2. [Python for Data Engineering](#python-for-data-engineering)
3. [Syntax and Fundamentals](#syntax-and-fundamentals)
4. [Data Types](#data-types)
5. [Data Structures](#data-structures)
6. [Flow Control](#flow-control)
7. [Functions and Functional Programming](#functions-and-functional-programming)
8. [File Handling](#file-handling)
9. [Pandas and NumPy Fundamentals](#pandas-and-numpy-fundamentals)
10. [Data Quality and Validation](#data-quality-and-validation)
11. [Error Handling and Logging](#error-handling-and-logging)
12. [Best Practices](#best-practices)

---

## Introduction

Python has become the dominant language for data engineering thanks to its clear syntax, extensive library ecosystem, and ability to integrate multiple systems. This document covers the fundamental concepts needed to effectively work with data in Python.

### Why Python for Data Engineering?

**Key Advantages**:
- **Clear Syntax**: Readable code that resembles pseudocode
- **Ecosistema Rico**: pandas, NumPy, PyArrow, SQLAlchemy, PySpark
- **Universal Integration**: REST APIs, databases, cloud providers
- **Community Support**: Extensive documentation and active community
- **Performance**: With NumPy and Cython, approaching C speeds
- **Versatilidad**: Desde scripts simples hasta pipelines distribuidos

**Casos de Uso en Data Engineering**:
- ETL/ELT pipelines
- Data transformation y cleaning
- API integration y web scraping
- Data quality checks
- Orchestration (Airflow, Prefect)
- Data warehouse loading
- Stream processing (con Apache Kafka)
- Data lakehouse operations

---

## Python para Data Engineering

### Diferencias con Data Science

| Aspecto | Data Engineering | Data Science |
|---------|------------------|--------------|
| **Objective** | Mover y transformar data a escala | Extraer insights y models |
| **Focus** | Robust and scalable pipelines | Exploration and experimentation |
| **Herramientas** | Airflow, Spark, Kafka, dbt | Jupyter, scikit-learn, TensorFlow |
| **Priority** | reliability, performance | Model precision |
| **Output** | Data limpios y estructurados | Modelos y visualizaciones |
| **Testing** | Unit tests, integration tests | Model validation |

### Principios Core

1. **Idempotence**: Running the same pipeline multiple times produces the same result
2. **scalability**: Code that works with 1MB must work with 1TB (with adjustments)
3. **Observabilidad**: Logging extensivo para debugging y monitoring
4. **Error Handling**: Graceful degradation y retry logic
5. **Data Quality**: Validation at each step of the pipeline
6. **Reproducibilidad**: Mismos inputs → mismos outputs siempre

---

## Sintaxis y Fundamentos

### features del Lenguaje

**Python es**:
- **Interpreted**: Does not require explicit compilation
- **Dynamically Typed**: Variables do not require type declaration
- **Orientado a Objetos**: Todo es un objeto
- **Indented**: Blocks are defined by indentation, not by braces
- **Multi-paradigma**: Soporta OOP, funcional, procedural

### Basic Syntax

```python
# Variables (without type declaration)
nombre = "Pipeline ETL"
num_registros = 1000000
tasa_error = 0.001
activo = True

# Dynamic types
valor = 42        # int
valor = "texto"   # ahora es str
valor = [1, 2, 3] # ahora es list

# Indentation (standard 4 spaces)
if activo:
    print("Pipeline activo")    # 4 espacios
    if num_registros > 0:
        print("Data disponibles")  # 8 espacios
```

### Convenciones de Nombres (PEP 8)

```python
# Variables y funciones: snake_case
numero_registros = 1000
def procesar_data():
    pass

# Constantes: UPPER_CASE
MAX_RETRY_ATTEMPTS = 3
DATABASE_URL = "postgresql://..."

# Clases: PascalCase
class DataPipeline:
    pass

# Modules: lowercase
import data_processor
from utils import helper_functions
```

### Comentarios y Docstrings

```python
# Single-line comment

"""
Multi-line comment
para documentation extensa
"""

def extract_data(fuente: str, fecha: str) -> list:
    """
    Extracts data from a specific source for a given date.
    
    Args:
        fuente: Nombre de la fuente de data (ej: 'api', 'database', 's3')
        fecha: Fecha en formato YYYY-MM-DD
        
    Returns:
        List of dictionaries with extracted data
        
    Raises:
        ValueError: If the date format is invalid
        ConnectionError: Si no se puede conectar a la fuente
        
    Example:
        >>> data = extract_data('api', '2026-02-01')
        >>> print(len(data))
        1523
    """
    pass
```

---

## Tipos de Data

### Tipos Primitivos

#### Numbers

```python
# Integers (int) - Arbitrary precision
num_registros = 1_000_000_000  # Underscores para legibilidad
id_usuario = 42
potencia = 2 ** 64  # Python handles large integers automatically

# Operaciones
suma = 10 + 5        # 15
resta = 10 - 5       # 5
multiplicacion = 10 * 5  # 50
division = 10 / 3    # 3.3333... (siempre float)
division_entera = 10 // 3  # 3 (trunca decimales)
modulo = 10 % 3      # 1
potencia = 2 ** 3    # 8

# Floats (float) - IEEE 754 double precision
tasa_conversion = 0.045
precio = 19.99
cientifico = 1.23e-4  # 0.000123

# Be careful with precision
print(0.1 + 0.2)  # 0.30000000000000004
# Usar Decimal para dinero:
from decimal import Decimal
precio = Decimal('19.99')
```

#### Strings

```python
# Definition
simple = 'hola'
doble = "mundo"
multi = """Texto
multi-line"""

# Inmutables
texto = "Python"
# texto[0] = "J"  # ❌ Error: strings son inmutables
nuevo = "J" + texto[1:]  # ✅ Crear nuevo string

# F-strings (Python 3.6+) - Preferred
nombre = "Pipeline"
version = 2
mensaje = f"Ejecutando {nombre} v{version}"

# Format especial
valor = 1234.5678
print(f"{valor:,.2f}")  # "1,234.57"
print(f"{valor:>10.2f}")  # "   1234.57" (right-align)

# Useful methods
texto = "  Data Engineering  "
texto.strip()           # "Data Engineering"
texto.lower()           # "  data engineering  "
texto.upper()           # "  DATA ENGINEERING  "
texto.replace("Data", "Cloud")  # "  Cloud Engineering  "
texto.split()           # ["Data", "Engineering"]

# Verificaciones
"Data" in texto         # True
texto.startswith("  D") # True
texto.endswith("ing  ") # True
texto.isdigit()         # False
```

#### Booleanos

```python
# Valores
activo = True
completed = False

# Operadores
resultado = True and False  # False
resultado = True or False   # True
resultado = not True        # False

# Comparaciones
10 > 5                # True
10 <= 10              # True
"a" == "a"            # True
5 != 10               # True

# Truthy y Falsy values
bool(0)               # False
bool(1)               # True
bool("")              # False
bool("texto")         # True
bool([])              # False
bool([1, 2])          # True
bool(None)            # False

# Short-circuit evaluation
valor = None
resultado = valor or "default"  # "default"
resultado = valor and "never"   # None (no evalua "never")
```

#### None

```python
# Representa ausencia de valor
resultado = None

# Verification
if resultado is None:
    print("Sin resultado")
    
# NO usar == para None
if resultado == None:  # ❌ Works but is not idiomatic
    pass
    
if resultado is None:  # ✅ Forma correcta
    pass

# Common use: default values
def procesar(data=None):
    if data is None:
        data = []
    return len(data)
```

### Type Hints (Python 3.5+)

```python
from typing import List, Dict, Optional, Union, Tuple, Any

# Funciones con tipos
def procesar_registros(
    registros: List[Dict[str, Any]],
    filtro: Optional[str] = None
) -> Tuple[int, int]:
    """Procesa registros y retorna (procesados, fallidos)"""
    procesados = 0
    fallidos = 0
    # ... logica ...
    return procesados, fallidos

# Variables con tipos
usuarios: List[str] = []
config: Dict[str, Union[str, int]] = {
    "host": "localhost",
    "port": 5432
}

# Optional es equivalente a Union[T, None]
resultado: Optional[str] = None
# es lo mismo que:
resultado: Union[str, None] = None
```

---

## Structures de Data

### Listas (Lists)

**features**:
- Ordenadas
- Mutables
- Permiten duplicados
- Pueden contener tipos mixtos
- Implemented as dynamic arrays

```python
# Creation
registros = [1, 2, 3, 4, 5]
mixto = [1, "texto", True, None, [1, 2]]
vacia = []
range_list = list(range(10))  # [0, 1, 2, ..., 9]

# Acceso
primer_elemento = registros[0]   # 1
ultimo = registros[-1]           # 5
slice = registros[1:4]           # [2, 3, 4]
reversa = registros[::-1]        # [5, 4, 3, 2, 1]

# Modification
registros.append(6)              # [1, 2, 3, 4, 5, 6]
registros.extend([7, 8])         # [1, 2, 3, 4, 5, 6, 7, 8]
registros.insert(0, 0)           # [0, 1, 2, 3, 4, 5, 6, 7, 8]
registros.remove(3)              # Remueve primera ocurrencia de 3
elemento = registros.pop()       # Removes and returns last
elemento = registros.pop(0)      # Remueve y retorna primero

# Operaciones
len(registros)                   # Size
3 in registros                   # True/False
registros.count(2)               # Cuenta ocurrencias
registros.index(4)               # First occurrence index
registros.sort()                 # Ordena in-place
ordenada = sorted(registros)     # Retorna nueva lista ordenada
registros.reverse()              # Revierte in-place

# List Comprehensions (muy importante!)
cuadrados = [x**2 for x in range(10)]
pares = [x for x in range(20) if x % 2 == 0]
procesados = [procesar(x) for x in data if validate(x)]
```

### Tuplas (Tuples)

**features**:
- Ordenadas
- Inmutables
- Permiten duplicados
- More efficient than lists for fixed data
- Pueden usarse como keys en diccionarios

```python
# Creation
coordenadas = (10.5, 20.3)
resultado = (True, "Success", 1234)
singleton = (42,)  # Nota la coma
vacia = ()

# Unpacking
x, y = coordenadas
estado, mensaje, codigo = resultado

# Inmutabilidad
# coordenadas[0] = 15  # ❌ Error
nueva = (15,) + coordenadas[1:]  # ✅ Crear nueva

# Named Tuples (more readable)
from collections import namedtuple

Registro = namedtuple('Registro', ['id', 'nombre', 'valor'])
reg = Registro(1, "Cliente A", 1000)
print(reg.id)       # 1
print(reg.nombre)   # "Cliente A"
```

### Diccionarios (Dicts)

**features**:
- Unsorted (sorted by insertion since Python 3.7+)
- Mutables
- Unique keys
- Keys deben ser inmutables (str, int, tuple)
- Implementados como hash tables (O(1) lookup)

```python
# Creation
usuario = {
    "id": 123,
    "nombre": "Juan",
    "email": "juan@example.com",
    "activo": True
}

config = dict(host="localhost", port=5432)
vacio = {}

# Acceso
nombre = usuario["nombre"]               # Puede lanzar KeyError
email = usuario.get("email")             # None si no existe
telefono = usuario.get("telefono", "")   # Default value

# Modification
usuario["edad"] = 30                     # Agregar/actualizar
usuario.update({"ciudad": "Santiago", "edad": 31})
del usuario["edad"]                      # Eliminar
edad = usuario.pop("edad", None)         # Eliminar y retornar

# Iteration
for key in usuario:
    print(key)

for key, value in usuario.items():
    print(f"{key}: {value}")
    
for value in usuario.values():
    print(value)

# Operaciones
len(usuario)                             # Number of keys
"email" in usuario                       # True
keys = list(usuario.keys())
values = list(usuario.values())

# Dict Comprehensions
cuadrados = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

filtrado = {k: v for k, v in usuario.items() if v is not None}
```

### Sets

**features**:
- No ordenados
- Mutables
- Sin duplicados
- Elementos deben ser inmutables
- Fast set operations

```python
# Creation
numeros = {1, 2, 3, 4, 5}
letras = set("abracadabra")  # {'a', 'b', 'r', 'c', 'd'}
vacio = set()  # Note: {} creates empty dict!

# Operaciones
numeros.add(6)
numeros.remove(3)      # KeyError si no existe
numeros.discard(3)     # No error si no existe
elemento = numeros.pop()  # Remueve arbitrario

# Operaciones de conjunto
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

union = a | b          # {1, 2, 3, 4, 5, 6}
interseccion = a & b   # {3, 4}
diferencia = a - b     # {1, 2}
diff_simetrica = a ^ b # {1, 2, 5, 6}

# Verificaciones
3 in a                 # True
a.issubset(b)          # False
a.issuperset({1, 2})   # True
a.isdisjoint(b)        # False

# Common use: deduplication
data_con_duplicados = [1, 2, 2, 3, 3, 3, 4]
unicos = list(set(data_con_duplicados))
```

---

## Control de Flujo

### Condicionales

```python
# Basic if
if temperatura > 30:
    print("Calor")

# If-elif-else
if temperatura > 30:
    print("Calor")
elif temperatura > 20:
    print("Templado")
else:
    print("Cold")

# Ternary expression
estado = "activo" if usuario.get("activo") else "inactivo"

# Multiple conditions
if edad >= 18 and licencia_valida:
    print("Puede conducir")

if usuario is None or not usuario.get("activo"):
    print("Invalid user")
```

### Loops

#### For Loops

```python
# Iterar sobre lista
for item in lista:
    print(item)

# Con index
for i, item in enumerate(lista):
    print(f"{i}: {item}")

# Iterar sobre dict
for key, value in diccionario.items():
    print(f"{key} = {value}")

# Range
for i in range(10):        # 0 a 9
    print(i)

for i in range(5, 10):     # 5 a 9
    print(i)

for i in range(0, 10, 2):  # 0, 2, 4, 6, 8
    print(i)

# Nested loops
for x in range(3):
    for y in range(3):
        print(f"({x}, {y})")
```

#### While Loops

```python
# Basic while
contador = 0
while contador < 5:
    print(contador)
    contador += 1

# Infinite loop con break
while True:
    dato = obtener_dato()
    if dato is None:
        break
    procesar(dato)

# Continue
for numero in range(10):
    if numero % 2 == 0:
        continue  # Salta pares
    print(numero)
```

### Comprehensions (Avanzado)

```python
# List comprehension
cuadrados = [x**2 for x in range(10)]
pares = [x for x in range(20) if x % 2 == 0]

# With multiple for loops
pares = [(x, y) for x in range(3) for y in range(3)]
# [(0,0), (0,1), (0,2), (1,0), ...]

# Dict comprehension
usuarios_dict = {u['id']: u for u in usuarios_lista}
nombres = {id: nombre.upper() for id, nombre in usuarios.items()}

# Set comprehension
unicos = {x % 10 for x in range(100)}

# Generator expression (lazy evaluation)
suma = sum(x**2 for x in range(1000000))  # No crea lista en memoria
```

---

## Functions and Functional Programming

### Definition of Functions

```python
# Basic function
def saludar(nombre):
    return f"Hola, {nombre}"

# Argumentos por defecto
def conectar_db(host="localhost", port=5432):
    return f"Conectando a {host}:{port}"

# Type hints
def procesar_data(data: List[Dict], filtro: str = "") -> List[Dict]:
    """Procesa y filtra data"""
    if filtro:
        data = [d for d in data if d.get('tipo') == filtro]
    return data

# Args y kwargs
def log_mensaje(*args, **kwargs):
    """Accepts any number of arguments"""
    print("Args:", args)
    print("Kwargs:", kwargs)

log_mensaje(1, 2, 3, level="INFO", timestamp="2026-02-02")
# Args: (1, 2, 3)
# Kwargs: {'level': 'INFO', 'timestamp': '2026-02-02'}
```

### Lambda Functions

```python
# Sintaxis
cuadrado = lambda x: x**2
suma = lambda a, b: a + b

# Common use: with map, filter, sorted
numeros = [1, 2, 3, 4, 5]
cuadrados = list(map(lambda x: x**2, numeros))
pares = list(filter(lambda x: x % 2 == 0, numeros))

# Sorting con key
usuarios = [
    {"nombre": "Ana", "edad": 25},
    {"nombre": "Juan", "edad": 30},
    {"nombre": "Maria", "edad": 22}
]
ordenados = sorted(usuarios, key=lambda u: u["edad"])
```

### Funciones de Orden Superior

```python
# Map: aplica funcion a cada elemento
def duplicar(x):
    return x * 2

numeros = [1, 2, 3, 4]
duplicados = list(map(duplicar, numeros))  # [2, 4, 6, 8]

# Filter: filtra elementos
def es_par(x):
    return x % 2 == 0

pares = list(filter(es_par, numeros))  # [2, 4]

# Reduce: reduce a un solo valor
from functools import reduce

suma = reduce(lambda a, b: a + b, numeros)  # 10
```

### Decoradores

```python
# Basic decorator
def log_execution(func):
    def wrapper(*args, **kwargs):
        print(f"Ejecutando {func.__name__}")
        resultado = func(*args, **kwargs)
        print(f"{func.__name__} completed")
        return resultado
    return wrapper

@log_execution
def procesar_data(data):
    return len(data)

# Decorator con argumentos
def retry(max_attempts=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}")
        return wrapper
    return decorator

@retry(max_attempts=5)
def llamar_api():
    # code that may fail
    pass
```

---

## Manejo de Files

### Context Managers

```python
# Correct way: with statement (closes automatically)
with open('data.txt', 'r') as f:
    contenido = f.read()
# File closes automatically when leaving the block

# Multiple files
with open('input.txt') as f_in, open('output.txt', 'w') as f_out:
    for linea in f_in:
        f_out.write(linea.upper())
```

### Modos de Apertura

```python
# 'r' - Lectura (default)
# 'w' - Escritura (sobrescribe)
# 'a' - Append
# 'r+' - Lectura y escritura
# 'b' - Modo binario
# 'x' - Creation exclusiva (falla si existe)

# Lectura
with open('data.txt', 'r', encoding='utf-8') as f:
    # Leer todo
    contenido = f.read()
    
    # Read lines
    lineas = f.readlines()  # List of lines
    
    # Iterate line by line (memory-efficient)
    for linea in f:
        procesar(linea)

# Escritura
with open('output.txt', 'w') as f:
    f.write("First line\n")
    f.writelines(["Line 2\n", "Line 3\n"])
```

### Formatos de Data

#### CSV

```python
import csv

# Lectura
with open('data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['nombre'], row['edad'])

# Escritura
data = [
    {'nombre': 'Ana', 'edad': 25},
    {'nombre': 'Juan', 'edad': 30}
]

with open('output.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['nombre', 'edad'])
    writer.writeheader()
    writer.writerows(data)
```

#### JSON

```python
import json

# Lectura
with open('config.json', 'r') as f:
    config = json.load(f)

# Escritura
data = {"usuarios": [{"id": 1, "nombre": "Ana"}]}
with open('data.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# String ↔ JSON
json_str = json.dumps(data)
data = json.loads(json_str)
```

#### Parquet

```python
import pyarrow.parquet as pq
import pandas as pd

# Lectura con pandas
df = pd.read_parquet('data.parquet')

# Escritura
df.to_parquet('output.parquet', compression='snappy')

# Reading with PyArrow (more control)
table = pq.read_table('data.parquet')
df = table.to_pandas()
```

---

## Pandas y NumPy Fundamentals

### NumPy Basics

```python
import numpy as np

# Arrays
arr = np.array([1, 2, 3, 4, 5])
matriz = np.array([[1, 2], [3, 4], [5, 6]])

# Operaciones vectorizadas (muy quicks)
arr * 2              # [2, 4, 6, 8, 10]
arr + arr            # [2, 4, 6, 8, 10]
arr ** 2             # [1, 4, 9, 16, 25]

# Agregaciones
arr.sum()            # 15
arr.mean()           # 3.0
arr.std()            # 1.4142...
arr.max()            # 5

# Broadcasting
matriz + 10          # Suma 10 a cada elemento
```

### Pandas DataFrames

```python
import pandas as pd

# Creation
df = pd.DataFrame({
    'nombre': ['Ana', 'Juan', 'Maria'],
    'edad': [25, 30, 22],
    'ciudad': ['Santiago', 'Lima', 'Bogota']
})

# Desde CSV
df = pd.read_csv('data.csv')

# Exploration
df.head()            # Primeras 5 filas
df.tail()            # Last 5 rows
df.info()            # DataFrame information
df.describe()        # Descriptive statistics
df.shape             # (filas, columnas)
df.columns           # Lista de columnas
df.dtypes            # Tipos de data

# Selection
df['nombre']         # Una columna (Series)
df[['nombre', 'edad']]  # Multiple columns
df.loc[0]            # Fila por index label
df.iloc[0]           # Row by position
df.loc[0, 'nombre']  # Specific cell

# Filtrado
df[df['edad'] > 25]
df[(df['edad'] > 20) & (df['ciudad'] == 'Santiago')]
df.query('edad > 25 and ciudad == "Santiago"')

# Agregaciones
df['edad'].mean()
df.groupby('ciudad')['edad'].mean()
df.groupby(['ciudad', 'gender']).agg({
    'edad': ['mean', 'max'],
    'ingreso': 'sum'
})
```

---

## Data Quality and Validation

### Missing Data

```python
# Detectar
df.isnull()          # DataFrame de booleanos
df.isnull().sum()    # Conteo por columna
df.isna()            # Alias de isnull()

# Eliminar
df.dropna()          # Elimina filas con cualquier null
df.dropna(subset=['columna'])  # Solo si columna es null
df.dropna(thresh=2)  # Mantiene si tiene al menos 2 no-null

# Rellenar
df.fillna(0)         # Reemplaza todos con 0
df.fillna({'edad': 0, 'nombre': 'Desconocido'})
df.fillna(method='ffill')  # Forward fill
df.fillna(method='bfill')  # Backward fill
```

### Duplicados

```python
# Detectar
df.duplicated()      # Series booleana
df.duplicated(subset=['email'])  # Solo considerando email

# Eliminar
df.drop_duplicates()
df.drop_duplicates(subset=['email'], keep='first')
```

### Validation with Pandera

```python
import pandera as pa

# Schema definition
schema = pa.DataFrameSchema({
    "user_id": pa.Column(int, pa.Check.ge(0)),
    "email": pa.Column(str, pa.Check.str_matches(r".+@.+\..+")),
    "age": pa.Column(int, pa.Check.in_range(0, 120)),
    "signup_date": pa.Column(pd.Timestamp)
})

# Validation
try:
    validated_df = schema.validate(df)
except pa.errors.SchemaError as e:
    print(f"Validation error: {e}")
```

---

## Error Handling y Logging

### Excepciones

```python
# Basic try-except
try:
    resultado = 10 / 0
except ZeroDivisionError:
    print("No se puede dividir por cero")

# Multiple exceptions
try:
    # code that may fail
    pass
except ValueError as e:
    print(f"Error de valor: {e}")
except TypeError as e:
    print(f"Error de tipo: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")

# Finally (siempre se ejecuta)
try:
    file = open('data.txt')
    # procesar
except FileNotFoundError:
    print("File no encontrado")
finally:
    file.close()  # Siempre se ejecuta

# Else (runs if no exception)
try:
    resultado = procesar_data()
except Exception as e:
    print(f"Error: {e}")
else:
    print("Success!")
    guardar(resultado)
```

### Excepciones Personalizadas

```python
class DataValidationError(Exception):
    """Error cuando los data no cumplen validaciones"""
    pass

class PipelineError(Exception):
    """Generic pipeline error"""
    def __init__(self, mensaje, codigo_error=None):
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        super().__init__(self.mensaje)

# Uso
def validate_data(df):
    if df.empty:
        raise DataValidationError("Empty DataFrame")
    if df.isnull().sum().sum() > 0:
        raise DataValidationError("Data contienen nulls")
```

### Logging

```python
import logging

# Basic configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed info for debugging")
logger.info("General flow information")
logger.warning("Advertencia: algo inesperado")
logger.error("Error that does not stop execution")
logger.critical("Critical error")

# Logging con contexto
try:
    procesar_data(df)
except Exception as e:
    logger.error(f"Error procesando data: {e}", exc_info=True)
```

---

## Best Practices

### Code Style (PEP 8)

```python
# ✅ Bueno
def procesar_data(data: List[Dict]) -> pd.DataFrame:
    """Procesa lista de diccionarios y retorna DataFrame"""
    df = pd.DataFrame(data)
    df_limpio = df.dropna()
    return df_limpio

# ❌ Malo
def ProcesarData(d):
    df=pd.DataFrame(d)
    df=df.dropna()
    return df
```

### Docstrings

```python
def extraer_transformar_cargar(
    fuente: str,
    destino: str,
    transformaciones: List[callable]
) -> Dict[str, int]:
    """
    Pipeline ETL completo de fuente a destino.
    
    Args:
        fuente: Path o URL de origen de data
        destino: Path o URL de destino
        transformations: List of transformation functions
        
    Returns:
        Dict with metrics: {'processed_records': int, 'errors': int}
        
    Raises:
        ConnectionError: Si no puede conectar a fuente/destino
        DataValidationError: If data fails validation
        
    Example:
        >>> metrics = extraer_transformar_cargar(
        ...     fuente='s3://bucket/data.csv',
        ...     destino='postgresql://db/tabla',
        ...     transformaciones=[limpiar, normalizar]
        ... )
        >>> print(metrics['registros_procesados'])
        15000
    """
    pass
```

### DRY (Don't Repeat Yourself)

```python
# ❌ Bad: repeated code
registros_validos = []
for registro in registros:
    if registro.get('edad') and registro.get('email'):
        registros_validos.append(registro)

usuarios_validos = []
for usuario in usuarios:
    if usuario.get('edad') and usuario.get('email'):
        usuarios_validos.append(usuario)

# ✅ Good: reusable function
def filtrar_validos(items: List[Dict], campos_requeridos: List[str]) -> List[Dict]:
    """Filtra items que tienen todos los campos requeridos"""
    return [
        item for item in items
        if all(item.get(campo) for campo in campos_requeridos)
    ]

registros_validos = filtrar_validos(registros, ['edad', 'email'])
usuarios_validos = filtrar_validos(usuarios, ['edad', 'email'])
```

### Pythonic Code

```python
# ❌ No Pythonic
i = 0
while i < len(lista):
    elemento = lista[i]
    print(elemento)
    i += 1

# ✅ Pythonic
for elemento in lista:
    print(elemento)

# ❌ No Pythonic
nueva_lista = []
for x in lista:
    if x > 0:
        nueva_lista.append(x * 2)

# ✅ Pythonic
nueva_lista = [x * 2 for x in lista if x > 0]

# ❌ No Pythonic
if len(lista) == 0:
    print("Empty")

# ✅ Pythonic
if not lista:
    print("Empty")
```

### Performance Tips

```python
# 1. Usar comprensiones en vez de loops
# ❌ Slow
resultado = []
for x in range(1000000):
    resultado.append(x * 2)

# ✅ Fast
resultado = [x * 2 for x in range(1000000)]

# 2. Usar generators para grandes datasets
# ❌ Crea lista completa en memoria
suma = sum([x**2 for x in range(1000000)])

# ✅ Genera on-the-fly
suma = sum(x**2 for x in range(1000000))

# 3. Usar set para membership testing
# ❌ O(n) lookup en lista
lista_grande = list(range(10000))
if 9999 in lista_grande:  # Slow
    pass

# ✅ O(1) lookup en set
set_grande = set(range(10000))
if 9999 in set_grande:  # Fast
    pass

# 4. Usar dict comprehension para lookups
# ❌ O(n) lookup
usuarios_lista = [{"id": 1, "nombre": "Ana"}, ...]
usuario = next(u for u in usuarios_lista if u["id"] == 1)

# ✅ O(1) lookup
usuarios_dict = {u["id"]: u for u in usuarios_lista}
usuario = usuarios_dict[1]
```

---

## Resumen

This document covered the fundamental concepts of Python for data engineering:

1. **Syntax and Fundamentals**: Dynamic typing, indentation, conventions
2. **Data Types**: Numbers, strings, booleans, None, type hints
3. **Structures**: Listas, tuplas, dicts, sets y sus operaciones
4. **Control de Flujo**: Condicionales, loops, comprehensions
5. **Functions**: Definition, lambdas, decorators, functional programming
6. **Files**: Context managers, CSV, JSON, Parquet
7. **Pandas/NumPy**: DataFrames, Series, operaciones vectorizadas
8. **Data Quality**: Missing data, duplicates, validation
9. **Error Handling**: Excepciones, logging, debugging
10. **Best Practices**: PEP 8, docstrings, pythonic code

Estos conceptos forman la base para construir pipelines de data robustos y scalables.

---

**Next step**: Read [architecture.md](./architecture.md) to understand data engineering patterns and architectures with Python.
