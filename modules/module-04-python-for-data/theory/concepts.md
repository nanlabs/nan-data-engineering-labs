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
| **Objetivo** | Mover y transformar datos a escala | Extraer insights y models |
| **Focus** | Robust and scalable pipelines | Exploration and experimentation |
| **Herramientas** | Airflow, Spark, Kafka, dbt | Jupyter, scikit-learn, TensorFlow |
| **Priority** | reliability, performance | Model precision |
| **Output** | Datos limpios y estructurados | Modelos y visualizaciones |
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
# Variables (sin declaración de tipo)
nombre = "Pipeline ETL"
num_registros = 1000000
tasa_error = 0.001
activo = True

# Tipos dinámicos
valor = 42        # int
valor = "texto"   # ahora es str
valor = [1, 2, 3] # ahora es list

# Indentación (4 espacios estándar)
if activo:
    print("Pipeline activo")    # 4 espacios
    if num_registros > 0:
        print("Datos disponibles")  # 8 espacios
```

### Convenciones de Nombres (PEP 8)

```python
# Variables y funciones: snake_case
numero_registros = 1000
def procesar_datos():
    pass

# Constantes: UPPER_CASE
MAX_RETRY_ATTEMPTS = 3
DATABASE_URL = "postgresql://..."

# Clases: PascalCase
class DataPipeline:
    pass

# Módulos: lowercase
import data_processor
from utils import helper_functions
```

### Comentarios y Docstrings

```python
# Comentario de una línea

"""
Comentario multi-línea
para documentación extensa
"""

def extraer_datos(fuente: str, fecha: str) -> list:
    """
    Extrae datos de una fuente específica para una fecha dada.
    
    Args:
        fuente: Nombre de la fuente de datos (ej: 'api', 'database', 's3')
        fecha: Fecha en formato YYYY-MM-DD
        
    Returns:
        Lista de diccionarios con los datos extraídos
        
    Raises:
        ValueError: Si el formato de fecha es inválido
        ConnectionError: Si no se puede conectar a la fuente
        
    Example:
        >>> datos = extraer_datos('api', '2026-02-01')
        >>> print(len(datos))
        1523
    """
    pass
```

---

## Tipos de Datos

### Tipos Primitivos

#### Numbers

```python
# Integers (int) - Precisión arbitraria
num_registros = 1_000_000_000  # Underscores para legibilidad
id_usuario = 42
potencia = 2 ** 64  # Python maneja enteros grandes automáticamente

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

# Cuidado con precisión
print(0.1 + 0.2)  # 0.30000000000000004
# Usar Decimal para dinero:
from decimal import Decimal
precio = Decimal('19.99')
```

#### Strings

```python
# Definición
simple = 'hola'
doble = "mundo"
multi = """Texto
multi-línea"""

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

# Métodos útiles
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
completado = False

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
resultado = valor and "nunca"   # None (no evalúa "nunca")
```

#### None

```python
# Representa ausencia de valor
resultado = None

# Verificación
if resultado is None:
    print("Sin resultado")
    
# NO usar == para None
if resultado == None:  # ❌ Funciona pero no es idiomático
    pass
    
if resultado is None:  # ✅ Forma correcta
    pass

# Uso común: valores por defecto
def procesar(datos=None):
    if datos is None:
        datos = []
    return len(datos)
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
    # ... lógica ...
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

## Estructuras de Datos

### Listas (Lists)

**features**:
- Ordenadas
- Mutables
- Permiten duplicados
- Pueden contener tipos mixtos
- Implemented as dynamic arrays

```python
# Creación
registros = [1, 2, 3, 4, 5]
mixto = [1, "texto", True, None, [1, 2]]
vacia = []
range_list = list(range(10))  # [0, 1, 2, ..., 9]

# Acceso
primer_elemento = registros[0]   # 1
ultimo = registros[-1]           # 5
slice = registros[1:4]           # [2, 3, 4]
reversa = registros[::-1]        # [5, 4, 3, 2, 1]

# Modificación
registros.append(6)              # [1, 2, 3, 4, 5, 6]
registros.extend([7, 8])         # [1, 2, 3, 4, 5, 6, 7, 8]
registros.insert(0, 0)           # [0, 1, 2, 3, 4, 5, 6, 7, 8]
registros.remove(3)              # Remueve primera ocurrencia de 3
elemento = registros.pop()       # Remueve y retorna último
elemento = registros.pop(0)      # Remueve y retorna primero

# Operaciones
len(registros)                   # Tamaño
3 in registros                   # True/False
registros.count(2)               # Cuenta ocurrencias
registros.index(4)               # Índice de primera ocurrencia
registros.sort()                 # Ordena in-place
ordenada = sorted(registros)     # Retorna nueva lista ordenada
registros.reverse()              # Revierte in-place

# List Comprehensions (muy importante!)
cuadrados = [x**2 for x in range(10)]
pares = [x for x in range(20) if x % 2 == 0]
procesados = [procesar(x) for x in datos if validar(x)]
```

### Tuplas (Tuples)

**features**:
- Ordenadas
- Inmutables
- Permiten duplicados
- More efficient than lists for fixed data
- Pueden usarse como keys en diccionarios

```python
# Creación
coordenadas = (10.5, 20.3)
resultado = (True, "Éxito", 1234)
singleton = (42,)  # Nota la coma
vacia = ()

# Unpacking
x, y = coordenadas
estado, mensaje, codigo = resultado

# Inmutabilidad
# coordenadas[0] = 15  # ❌ Error
nueva = (15,) + coordenadas[1:]  # ✅ Crear nueva

# Named Tuples (más legibles)
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
# Creación
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

# Modificación
usuario["edad"] = 30                     # Agregar/actualizar
usuario.update({"ciudad": "Santiago", "edad": 31})
del usuario["edad"]                      # Eliminar
edad = usuario.pop("edad", None)         # Eliminar y retornar

# Iteración
for key in usuario:
    print(key)

for key, value in usuario.items():
    print(f"{key}: {value}")
    
for value in usuario.values():
    print(value)

# Operaciones
len(usuario)                             # Número de keys
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
# Creación
numeros = {1, 2, 3, 4, 5}
letras = set("abracadabra")  # {'a', 'b', 'r', 'c', 'd'}
vacio = set()  # Nota: {} crea dict vacío!

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

# Uso común: deduplicación
datos_con_duplicados = [1, 2, 2, 3, 3, 3, 4]
unicos = list(set(datos_con_duplicados))
```

---

## Control de Flujo

### Condicionales

```python
# If básico
if temperatura > 30:
    print("Calor")

# If-elif-else
if temperatura > 30:
    print("Calor")
elif temperatura > 20:
    print("Templado")
else:
    print("Frío")

# Expresión ternaria
estado = "activo" if usuario.get("activo") else "inactivo"

# Múltiples condiciones
if edad >= 18 and licencia_valida:
    print("Puede conducir")

if usuario is None or not usuario.get("activo"):
    print("Usuario inválido")
```

### Loops

#### For Loops

```python
# Iterar sobre lista
for item in lista:
    print(item)

# Con índice
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
# While básico
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

# Con múltiples for
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
# Función básica
def saludar(nombre):
    return f"Hola, {nombre}"

# Argumentos por defecto
def conectar_db(host="localhost", port=5432):
    return f"Conectando a {host}:{port}"

# Type hints
def procesar_datos(datos: List[Dict], filtro: str = "") -> List[Dict]:
    """Procesa y filtra datos"""
    if filtro:
        datos = [d for d in datos if d.get('tipo') == filtro]
    return datos

# Args y kwargs
def log_mensaje(*args, **kwargs):
    """Acepta cualquier número de argumentos"""
    print("Args:", args)
    print("Kwargs:", kwargs)

log_mensaje(1, 2, 3, nivel="INFO", timestamp="2026-02-02")
# Args: (1, 2, 3)
# Kwargs: {'nivel': 'INFO', 'timestamp': '2026-02-02'}
```

### Lambda Functions

```python
# Sintaxis
cuadrado = lambda x: x**2
suma = lambda a, b: a + b

# Uso común: con map, filter, sorted
numeros = [1, 2, 3, 4, 5]
cuadrados = list(map(lambda x: x**2, numeros))
pares = list(filter(lambda x: x % 2 == 0, numeros))

# Sorting con key
usuarios = [
    {"nombre": "Ana", "edad": 25},
    {"nombre": "Juan", "edad": 30},
    {"nombre": "María", "edad": 22}
]
ordenados = sorted(usuarios, key=lambda u: u["edad"])
```

### Funciones de Orden Superior

```python
# Map: aplica función a cada elemento
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
# Decorator básico
def log_execution(func):
    def wrapper(*args, **kwargs):
        print(f"Ejecutando {func.__name__}")
        resultado = func(*args, **kwargs)
        print(f"{func.__name__} completado")
        return resultado
    return wrapper

@log_execution
def procesar_datos(datos):
    return len(datos)

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
                    print(f"Intento {attempt + 1} falló: {e}")
        return wrapper
    return decorator

@retry(max_attempts=5)
def llamar_api():
    # código que puede fallar
    pass
```

---

## Manejo de Archivos

### Context Managers

```python
# Forma correcta: with statement (cierra automáticamente)
with open('datos.txt', 'r') as f:
    contenido = f.read()
# Archivo se cierra automáticamente al salir del bloque

# Múltiples archivos
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
# 'x' - Creación exclusiva (falla si existe)

# Lectura
with open('datos.txt', 'r', encoding='utf-8') as f:
    # Leer todo
    contenido = f.read()
    
    # Leer líneas
    lineas = f.readlines()  # Lista de líneas
    
    # Iterar línea por línea (memory-efficient)
    for linea in f:
        procesar(linea)

# Escritura
with open('output.txt', 'w') as f:
    f.write("Primera línea\n")
    f.writelines(["Línea 2\n", "Línea 3\n"])
```

### Formatos de Datos

#### CSV

```python
import csv

# Lectura
with open('datos.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['nombre'], row['edad'])

# Escritura
datos = [
    {'nombre': 'Ana', 'edad': 25},
    {'nombre': 'Juan', 'edad': 30}
]

with open('output.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['nombre', 'edad'])
    writer.writeheader()
    writer.writerows(datos)
```

#### JSON

```python
import json

# Lectura
with open('config.json', 'r') as f:
    config = json.load(f)

# Escritura
datos = {"usuarios": [{"id": 1, "nombre": "Ana"}]}
with open('datos.json', 'w') as f:
    json.dump(datos, f, indent=2, ensure_ascii=False)

# String ↔ JSON
json_str = json.dumps(datos)
datos = json.loads(json_str)
```

#### Parquet

```python
import pyarrow.parquet as pq
import pandas as pd

# Lectura con pandas
df = pd.read_parquet('datos.parquet')

# Escritura
df.to_parquet('output.parquet', compression='snappy')

# Lectura con PyArrow (más control)
table = pq.read_table('datos.parquet')
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

# Operaciones vectorizadas (muy rápidas)
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

# Creación
df = pd.DataFrame({
    'nombre': ['Ana', 'Juan', 'María'],
    'edad': [25, 30, 22],
    'ciudad': ['Santiago', 'Lima', 'Bogotá']
})

# Desde CSV
df = pd.read_csv('datos.csv')

# Exploración
df.head()            # Primeras 5 filas
df.tail()            # Últimas 5 filas
df.info()            # Información del DataFrame
df.describe()        # Estadísticas descriptivas
df.shape             # (filas, columnas)
df.columns           # Lista de columnas
df.dtypes            # Tipos de datos

# Selección
df['nombre']         # Una columna (Series)
df[['nombre', 'edad']]  # Múltiples columnas
df.loc[0]            # Fila por índice label
df.iloc[0]           # Fila por posición
df.loc[0, 'nombre']  # Celda específica

# Filtrado
df[df['edad'] > 25]
df[(df['edad'] > 20) & (df['ciudad'] == 'Santiago')]
df.query('edad > 25 and ciudad == "Santiago"')

# Agregaciones
df['edad'].mean()
df.groupby('ciudad')['edad'].mean()
df.groupby(['ciudad', 'género']).agg({
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

# Validación
try:
    validated_df = schema.validate(df)
except pa.errors.SchemaError as e:
    print(f"Validation error: {e}")
```

---

## Error Handling y Logging

### Excepciones

```python
# Try-except básico
try:
    resultado = 10 / 0
except ZeroDivisionError:
    print("No se puede dividir por cero")

# Múltiples excepciones
try:
    # código que puede fallar
    pass
except ValueError as e:
    print(f"Error de valor: {e}")
except TypeError as e:
    print(f"Error de tipo: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")

# Finally (siempre se ejecuta)
try:
    archivo = open('datos.txt')
    # procesar
except FileNotFoundError:
    print("Archivo no encontrado")
finally:
    archivo.close()  # Siempre se ejecuta

# Else (se ejecuta si no hay excepción)
try:
    resultado = procesar_datos()
except Exception as e:
    print(f"Error: {e}")
else:
    print("Éxito!")
    guardar(resultado)
```

### Excepciones Personalizadas

```python
class DataValidationError(Exception):
    """Error cuando los datos no cumplen validaciones"""
    pass

class PipelineError(Exception):
    """Error genérico de pipeline"""
    def __init__(self, mensaje, codigo_error=None):
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        super().__init__(self.mensaje)

# Uso
def validar_datos(df):
    if df.empty:
        raise DataValidationError("DataFrame vacío")
    if df.isnull().sum().sum() > 0:
        raise DataValidationError("Datos contienen nulls")
```

### Logging

```python
import logging

# Configuración básica
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Niveles de log
logger.debug("Información detallada para debugging")
logger.info("Información general del flujo")
logger.warning("Advertencia: algo inesperado")
logger.error("Error que no detiene la ejecución")
logger.critical("Error crítico")

# Logging con contexto
try:
    procesar_datos(df)
except Exception as e:
    logger.error(f"Error procesando datos: {e}", exc_info=True)
```

---

## Best Practices

### Code Style (PEP 8)

```python
# ✅ Bueno
def procesar_datos(datos: List[Dict]) -> pd.DataFrame:
    """Procesa lista de diccionarios y retorna DataFrame"""
    df = pd.DataFrame(datos)
    df_limpio = df.dropna()
    return df_limpio

# ❌ Malo
def ProcesarDatos(d):
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
        fuente: Path o URL de origen de datos
        destino: Path o URL de destino
        transformaciones: Lista de funciones de transformación
        
    Returns:
        Dict con métricas: {'registros_procesados': int, 'errores': int}
        
    Raises:
        ConnectionError: Si no puede conectar a fuente/destino
        DataValidationError: Si datos no pasan validación
        
    Example:
        >>> metrics = extraer_transformar_cargar(
        ...     fuente='s3://bucket/datos.csv',
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
# ❌ Malo: código repetido
registros_validos = []
for registro in registros:
    if registro.get('edad') and registro.get('email'):
        registros_validos.append(registro)

usuarios_validos = []
for usuario in usuarios:
    if usuario.get('edad') and usuario.get('email'):
        usuarios_validos.append(usuario)

# ✅ Bueno: función reutilizable
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
    print("Vacía")

# ✅ Pythonic
if not lista:
    print("Vacía")
```

### Performance Tips

```python
# 1. Usar comprensiones en vez de loops
# ❌ Lento
resultado = []
for x in range(1000000):
    resultado.append(x * 2)

# ✅ Rápido
resultado = [x * 2 for x in range(1000000)]

# 2. Usar generators para grandes datasets
# ❌ Crea lista completa en memoria
suma = sum([x**2 for x in range(1000000)])

# ✅ Genera on-the-fly
suma = sum(x**2 for x in range(1000000))

# 3. Usar set para membership testing
# ❌ O(n) lookup en lista
lista_grande = list(range(10000))
if 9999 in lista_grande:  # Lento
    pass

# ✅ O(1) lookup en set
set_grande = set(range(10000))
if 9999 in set_grande:  # Rápido
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
3. **Estructuras**: Listas, tuplas, dicts, sets y sus operaciones
4. **Control de Flujo**: Condicionales, loops, comprehensions
5. **Functions**: Definition, lambdas, decorators, functional programming
6. **Archivos**: Context managers, CSV, JSON, Parquet
7. **Pandas/NumPy**: DataFrames, Series, operaciones vectorizadas
8. **Data Quality**: Missing data, duplicates, validation
9. **Error Handling**: Excepciones, logging, debugging
10. **Best Practices**: PEP 8, docstrings, pythonic code

Estos conceptos forman la base para construir pipelines de datos robustos y scalables.

---

**Next step**: Read [architecture.md](./architecture.md) to understand data engineering patterns and architectures with Python.
