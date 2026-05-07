# 🐍 Python Basics - Quick Reference

## 📋 Variables y Tipos de Data

### Declaration of Variables

```python
# Tipos basicos
nombre = "Juan"                    # str
edad = 30                          # int
altura = 1.75                      # float
activo = True                      # bool
nada = None                        # NoneType

# Verificar tipo
type(nombre)  # <class 'str'>
isinstance(edad, int)  # True
```text

### Type Conversion

```python
# String a numero
int("42")        # 42
float("3.14")    # 3.14

# Numero a string
str(42)          # "42"
str(3.14)        # "3.14"

# Boolean
bool(0)          # False
bool("")         # False
bool([])         # False
bool(1)          # True
```text

## 📝 Strings

### Operaciones Comunes

```python
texto = "Python para Data"

# Mayusculas/minusculas
texto.upper()           # "PYTHON PARA DATOS"
texto.lower()           # "python para data"
texto.title()           # "Python Para Data"

# Busqueda
texto.startswith("Py")  # True
texto.endswith("s")     # True
"para" in texto         # True

# Reemplazo
texto.replace("Data", "ML")  # "Python para ML"

# Division
texto.split()           # ["Python", "para", "Data"]
"a,b,c".split(",")     # ["a", "b", "c"]

# Union
"-".join(["a", "b"])   # "a-b"

# Cleaning
"  texto  ".strip()    # "texto"
```text

### F-Strings (Formateo)

```python
nombre = "Ana"
edad = 25

# Basico
f"Hola, {nombre}"                    # "Hola, Ana"

# Expresiones
f"{nombre} tiene {edad + 1} anos"    # "Ana tiene 26 anos"

# Formateo numerico
precio = 99.99
f"Precio: ${precio:.2f}"             # "Precio: $99.99"
f"Porcentaje: {0.875:.1%}"           # "Porcentaje: 87.5%"

# Alineacion
f"{nombre:>10}"                      # "       Ana"
f"{nombre:<10}"                      # "Ana       "
```

## 📦 Colecciones

### Listas (Ordenadas, Mutables)

```python
# Creation
numeros = [1, 2, 3, 4, 5]
mixta = [1, "dos", 3.0, True]

# Acceso
numeros[0]      # 1 (primer elemento)
numeros[-1]     # 5 (ultimo elemento)
numeros[1:3]    # [2, 3] (slicing)

# Modification
numeros.append(6)              # Agregar al final
numeros.insert(0, 0)           # Insertar en posicion
numeros.remove(3)              # Eliminar valor
numeros.pop()                  # Eliminar y retornar ultimo
numeros.pop(0)                 # Eliminar en posicion

# Operaciones
len(numeros)                   # Longitud
sum(numeros)                   # Suma
max(numeros)                   # Maximo
min(numeros)                   # Minimo
sorted(numeros)                # Ordenar (nueva lista)
numeros.sort()                 # Ordenar in-place
```text

### Tuplas (Ordenadas, Inmutables)

```python
# Creation
coordenadas = (10, 20)
punto = 5, 6  # Sin parentesis

# Desempaquetado
x, y = coordenadas
a, b, c = (1, 2, 3)

# Uso comun: retornar multiples valores
def obtener_data():
    return "Juan", 30, "Mexico"

nombre, edad, pais = obtener_data()
```text

### Diccionarios (Clave-Valor)

```python
# Creation
persona = {
    "nombre": "Ana",
    "edad": 25,
    "ciudad": "Madrid"
}

# Acceso
persona["nombre"]              # "Ana"
persona.get("edad")            # 25
persona.get("pais", "N/A")     # "N/A" (default)

# Modification
persona["edad"] = 26           # Actualizar
persona["pais"] = "Espana"     # Agregar nueva clave
del persona["ciudad"]          # Eliminar

# Operaciones
persona.keys()                 # dict_keys(['nombre', 'edad'])
persona.values()               # dict_values(['Ana', 25])
persona.items()                # dict_items([('nombre', 'Ana'), ...])

# Verification
"nombre" in persona            # True
```text

### Sets (Not ordered, unique)

```python
# Creation
numeros = {1, 2, 3, 4, 5}
letras = set("abracadabra")    # {'a', 'b', 'r', 'c', 'd'}

# Operaciones
numeros.add(6)                 # Agregar
numeros.remove(3)              # Eliminar (error si no existe)
numeros.discard(3)             # Eliminar (sin error)

# Operaciones de conjuntos
a = {1, 2, 3}
b = {3, 4, 5}
a | b                          # {1, 2, 3, 4, 5} union
a & b                          # {3} interseccion
a - b                          # {1, 2} diferencia
```

## 🔀 Control de Flujo

### Condicionales

```python
# Basic if
if edad >= 18:
    print("Mayor de edad")

# If-else
if edad >= 18:
    print("Mayor de edad")
else:
    print("Menor de edad")

# If-elif-else
if nota >= 90:
    calificacion = "A"
elif nota >= 80:
    calificacion = "B"
elif nota >= 70:
    calificacion = "C"
else:
    calificacion = "F"

# Operador ternario
estado = "activo" if edad >= 18 else "inactivo"
```text

### Bucles

#### For Loop

```python
# Iterar lista
for numero in [1, 2, 3, 4, 5]:
    print(numero)

# Iterar rango
for i in range(5):             # 0, 1, 2, 3, 4
    print(i)

for i in range(1, 10, 2):      # 1, 3, 5, 7, 9 (start, stop, step)
    print(i)

# Iterar diccionario
for clave, valor in persona.items():
    print(f"{clave}: {valor}")

# Enumerar (index + valor)
for i, nombre in enumerate(["Ana", "Luis", "Maria"]):
    print(f"{i}: {nombre}")

# Control de flujo
for i in range(10):
    if i == 5:
        continue  # Saltar iteracion
    if i == 8:
        break     # Salir del loop
    print(i)
```text

#### While Loop

```python
# Basic while
contador = 0
while contador < 5:
    print(contador)
    contador += 1

# While con break
while True:
    respuesta = input("¿Continuar? (s/n): ")
    if respuesta.lower() == 'n':
        break
```text

## 🎯 Funciones

### Basic Definition

```python
# Funcion simple
def saludar():
    print("¡Hola!")

# Con parametros
def saludar(nombre):
    print(f"¡Hola, {nombre}!")

# Con retorno
def suma(a, b):
    return a + b

# Multiples retornos
def dividir(a, b):
    if b == 0:
        return None, "Error: division por cero"
    return a / b, "OK"

resultado, mensaje = dividir(10, 2)
```

### Parameters

```python
# Parametros por defecto
def saludar(nombre, saludo="Hola"):
    return f"{saludo}, {nombre}!"

# Parametros nombrados
saludar(nombre="Ana", saludo="Buenos dias")

# *args (argumentos variables)
def suma_todos(*numeros):
    return sum(numeros)

suma_todos(1, 2, 3, 4, 5)  # 15

# **kwargs (argumentos con nombre variables)
def crear_persona(**data):
    return data

crear_persona(nombre="Ana", edad=25, ciudad="Madrid")
```text

### Lambda (Anonymous Functions)

```python
# Sintaxis: lambda argumentos: expresion
suma = lambda a, b: a + b
suma(3, 5)  # 8

# Uso comun: como argumento
numeros = [1, 2, 3, 4, 5]
pares = list(filter(lambda x: x % 2 == 0, numeros))  # [2, 4]
cuadrados = list(map(lambda x: x**2, numeros))       # [1, 4, 9, 16, 25]
```text

## 🚀 Comprehensions

### List Comprehensions

```python
# Basica
cuadrados = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Con condicional
pares = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# Con transformacion
palabras = ["hola", "mundo"]
mayusculas = [p.upper() for p in palabras]
# ["HOLA", "MUNDO"]

# Nested
matriz = [[i*j for j in range(3)] for i in range(3)]
# [[0, 0, 0], [0, 1, 2], [0, 2, 4]]
```text

### Dict Comprehensions

```python
# Basica
cuadrados_dict = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# De listas
nombres = ["Ana", "Luis", "Maria"]
longitudes = {n: len(n) for n in nombres}
# {'Ana': 3, 'Luis': 4, 'Maria': 5}

# Invertir diccionario
original = {"a": 1, "b": 2}
invertido = {v: k for k, v in original.items()}
# {1: 'a', 2: 'b'}
```

### Set Comprehensions

```python
# Unique
unicos = {x % 3 for x in range(10)}
# {0, 1, 2}
```text

## ⚠️ Errores Comunes

### 1. Inconsistent Indentation

```python
# ❌ Incorrect
def funcion():
  print("Hola")   # 2 espacios
    print("Mundo")  # 4 espacios

# ✅ Correct
def funcion():
    print("Hola")   # 4 espacios
    print("Mundo")  # 4 espacios
```text

### 2. Mutabilidad de Listas

```python
# ❌ Cuidado
lista1 = [1, 2, 3]
lista2 = lista1        # ¡Misma referencia!
lista2.append(4)
print(lista1)          # [1, 2, 3, 4] ¡Modificada!

# ✅ Correct
lista2 = lista1.copy()  # o lista1[:]
```text

### 3. Default Mutable Arguments

```python
# ❌ Incorrect
def agregar_item(item, lista=[]):
    lista.append(item)
    return lista

agregar_item(1)  # [1]
agregar_item(2)  # [1, 2] ¡Mantiene estado!

# ✅ Correct
def agregar_item(item, lista=None):
    if lista is None:
        lista = []
    lista.append(item)
    return lista
```

## 💡 Tips and Best Practices

1. **Usa nombres descriptivos**: `edad_usuario` mejor que `e`
2. **PEP 8**: 4 spaces for indentation, snake_case for variables
3. **Docstrings**: Documenta funciones complejas
4. **List comprehensions**: More Pythonic than simple loops
5. **f-strings**: Preferir sobre `.format()` o `%`
6. **Usa `in`**: Para verificar pertenencia en colecciones
7. **Avoid modifying lists during iteration**: Create a copy

---

**Siguiente**: Ver [pandas-reference.md](pandas-reference.md) para trabajar con data
