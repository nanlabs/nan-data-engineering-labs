# 🐍 Python Basics - Quick Reference

## 📋 Variables y Tipos de Datos

### Declaration of Variables
```python
# Tipos básicos
nombre = "Juan"                    # str
edad = 30                          # int
altura = 1.75                      # float
activo = True                      # bool
nada = None                        # NoneType

# Verificar tipo
type(nombre)  # <class 'str'>
isinstance(edad, int)  # True
```

### Type Conversion
```python
# String a número
int("42")        # 42
float("3.14")    # 3.14

# Número a string
str(42)          # "42"
str(3.14)        # "3.14"

# Boolean
bool(0)          # False
bool("")         # False
bool([])         # False
bool(1)          # True
```

## 📝 Strings

### Operaciones Comunes
```python
texto = "Python para Datos"

# Mayúsculas/minúsculas
texto.upper()           # "PYTHON PARA DATOS"
texto.lower()           # "python para datos"
texto.title()           # "Python Para Datos"

# Búsqueda
texto.startswith("Py")  # True
texto.endswith("s")     # True
"para" in texto         # True

# Reemplazo
texto.replace("Datos", "ML")  # "Python para ML"

# División
texto.split()           # ["Python", "para", "Datos"]
"a,b,c".split(",")     # ["a", "b", "c"]

# Unión
"-".join(["a", "b"])   # "a-b"

# Limpieza
"  texto  ".strip()    # "texto"
```

### F-Strings (Formateo)
```python
nombre = "Ana"
edad = 25

# Básico
f"Hola, {nombre}"                    # "Hola, Ana"

# Expresiones
f"{nombre} tiene {edad + 1} años"    # "Ana tiene 26 años"

# Formateo numérico
precio = 99.99
f"Precio: ${precio:.2f}"             # "Precio: $99.99"
f"Porcentaje: {0.875:.1%}"           # "Porcentaje: 87.5%"

# Alineación
f"{nombre:>10}"                      # "       Ana"
f"{nombre:<10}"                      # "Ana       "
```

## 📦 Colecciones

### Listas (Ordenadas, Mutables)
```python
# Creación
numeros = [1, 2, 3, 4, 5]
mixta = [1, "dos", 3.0, True]

# Acceso
numeros[0]      # 1 (primer elemento)
numeros[-1]     # 5 (último elemento)
numeros[1:3]    # [2, 3] (slicing)

# Modificación
numeros.append(6)              # Agregar al final
numeros.insert(0, 0)           # Insertar en posición
numeros.remove(3)              # Eliminar valor
numeros.pop()                  # Eliminar y retornar último
numeros.pop(0)                 # Eliminar en posición

# Operaciones
len(numeros)                   # Longitud
sum(numeros)                   # Suma
max(numeros)                   # Máximo
min(numeros)                   # Mínimo
sorted(numeros)                # Ordenar (nueva lista)
numeros.sort()                 # Ordenar in-place
```

### Tuplas (Ordenadas, Inmutables)
```python
# Creación
coordenadas = (10, 20)
punto = 5, 6  # Sin paréntesis

# Desempaquetado
x, y = coordenadas
a, b, c = (1, 2, 3)

# Uso común: retornar múltiples valores
def obtener_datos():
    return "Juan", 30, "México"

nombre, edad, pais = obtener_datos()
```

### Diccionarios (Clave-Valor)
```python
# Creación
persona = {
    "nombre": "Ana",
    "edad": 25,
    "ciudad": "Madrid"
}

# Acceso
persona["nombre"]              # "Ana"
persona.get("edad")            # 25
persona.get("pais", "N/A")     # "N/A" (default)

# Modificación
persona["edad"] = 26           # Actualizar
persona["pais"] = "España"     # Agregar nueva clave
del persona["ciudad"]          # Eliminar

# Operaciones
persona.keys()                 # dict_keys(['nombre', 'edad'])
persona.values()               # dict_values(['Ana', 25])
persona.items()                # dict_items([('nombre', 'Ana'), ...])

# Verificación
"nombre" in persona            # True
```

### Sets (Not ordered, unique)
```python
# Creación
numeros = {1, 2, 3, 4, 5}
letras = set("abracadabra")    # {'a', 'b', 'r', 'c', 'd'}

# Operaciones
numeros.add(6)                 # Agregar
numeros.remove(3)              # Eliminar (error si no existe)
numeros.discard(3)             # Eliminar (sin error)

# Operaciones de conjuntos
a = {1, 2, 3}
b = {3, 4, 5}
a | b                          # {1, 2, 3, 4, 5} unión
a & b                          # {3} intersección
a - b                          # {1, 2} diferencia
```

## 🔀 Control de Flujo

### Condicionales
```python
# If básico
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
```

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

# Enumerar (índice + valor)
for i, nombre in enumerate(["Ana", "Luis", "María"]):
    print(f"{i}: {nombre}")

# Control de flujo
for i in range(10):
    if i == 5:
        continue  # Saltar iteración
    if i == 8:
        break     # Salir del loop
    print(i)
```

#### While Loop
```python
# While básico
contador = 0
while contador < 5:
    print(contador)
    contador += 1

# While con break
while True:
    respuesta = input("¿Continuar? (s/n): ")
    if respuesta.lower() == 'n':
        break
```

## 🎯 Funciones

### Basic Definition
```python
# Función simple
def saludar():
    print("¡Hola!")

# Con parámetros
def saludar(nombre):
    print(f"¡Hola, {nombre}!")

# Con retorno
def suma(a, b):
    return a + b

# Múltiples retornos
def dividir(a, b):
    if b == 0:
        return None, "Error: división por cero"
    return a / b, "OK"

resultado, mensaje = dividir(10, 2)
```

### Parameters

```python
# Parámetros por defecto
def saludar(nombre, saludo="Hola"):
    return f"{saludo}, {nombre}!"

# Parámetros nombrados
saludar(nombre="Ana", saludo="Buenos días")

# *args (argumentos variables)
def suma_todos(*numeros):
    return sum(numeros)

suma_todos(1, 2, 3, 4, 5)  # 15

# **kwargs (argumentos con nombre variables)
def crear_persona(**datos):
    return datos

crear_persona(nombre="Ana", edad=25, ciudad="Madrid")
```

### Lambda (Anonymous Functions)
```python
# Sintaxis: lambda argumentos: expresión
suma = lambda a, b: a + b
suma(3, 5)  # 8

# Uso común: como argumento
numeros = [1, 2, 3, 4, 5]
pares = list(filter(lambda x: x % 2 == 0, numeros))  # [2, 4]
cuadrados = list(map(lambda x: x**2, numeros))       # [1, 4, 9, 16, 25]
```

## 🚀 Comprehensions

### List Comprehensions
```python
# Básica
cuadrados = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Con condicional
pares = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# Con transformación
palabras = ["hola", "mundo"]
mayusculas = [p.upper() for p in palabras]
# ["HOLA", "MUNDO"]

# Nested
matriz = [[i*j for j in range(3)] for i in range(3)]
# [[0, 0, 0], [0, 1, 2], [0, 2, 4]]
```

### Dict Comprehensions
```python
# Básica
cuadrados_dict = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# De listas
nombres = ["Ana", "Luis", "María"]
longitudes = {n: len(n) for n in nombres}
# {'Ana': 3, 'Luis': 4, 'María': 5}

# Invertir diccionario
original = {"a": 1, "b": 2}
invertido = {v: k for k, v in original.items()}
# {1: 'a', 2: 'b'}
```

### Set Comprehensions
```python
# Únicos
unicos = {x % 3 for x in range(10)}
# {0, 1, 2}
```

## ⚠️ Errores Comunes

### 1. Inconsistent Indentation
```python
# ❌ Incorrecto
def funcion():
  print("Hola")   # 2 espacios
    print("Mundo")  # 4 espacios

# ✅ Correcto
def funcion():
    print("Hola")   # 4 espacios
    print("Mundo")  # 4 espacios
```

### 2. Mutabilidad de Listas
```python
# ❌ Cuidado
lista1 = [1, 2, 3]
lista2 = lista1        # ¡Misma referencia!
lista2.append(4)
print(lista1)          # [1, 2, 3, 4] ¡Modificada!

# ✅ Correcto
lista2 = lista1.copy()  # o lista1[:]
```

### 3. Default Mutable Arguments
```python
# ❌ Incorrecto
def agregar_item(item, lista=[]):
    lista.append(item)
    return lista

agregar_item(1)  # [1]
agregar_item(2)  # [1, 2] ¡Mantiene estado!

# ✅ Correcto
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

**Siguiente**: Ver [pandas-reference.md](pandas-reference.md) para trabajar con datos
