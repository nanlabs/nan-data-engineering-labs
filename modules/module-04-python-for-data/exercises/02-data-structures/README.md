# Ejercicio 02: Data Structures

## Objetivos de Aprendizaje

After completing this exercise, you will be able to:

1. ✅ Trabajar con **listas**, **tuplas**, **diccionarios** y **sets**
2. ✅ Usar **list/dict/set comprehensions** de forma efectiva
3. ✅ Manipular estructuras de datos anidadas
4. ✅ Aplicar operaciones avanzadas (filter, map, reduce)
5. ✅ Optimize code using appropriate structures

---

## Conceptos Clave

### Listas (list)

```python
# Creación
numeros = [1, 2, 3, 4, 5]
vacia = []

# Operaciones
numeros.append(6)           # Agregar al final
numeros.insert(0, 0)        # Insertar en posición
numeros.remove(3)           # Remover primer 3
ultimo = numeros.pop()      # Remover y retornar último
numeros.extend([7, 8])      # Extender lista

# Slicing
primeros_3 = numeros[:3]    # [0, 1, 2]
ultimos_2 = numeros[-2:]    # [7, 8]
invertida = numeros[::-1]   # Lista invertida

# List comprehension
cuadrados = [x**2 for x in range(10)]
pares = [x for x in range(20) if x % 2 == 0]
```

### Diccionarios (dict)

```python
# Creación
usuario = {"nombre": "Ana", "edad": 25}
vacio = {}

# Acceso
nombre = usuario["nombre"]          # KeyError si no existe
nombre = usuario.get("nombre")      # None si no existe
nombre = usuario.get("nombre", "N/A")  # Valor por defecto

# Operaciones
usuario["email"] = "ana@example.com"  # Agregar/actualizar
del usuario["edad"]                   # Eliminar
edad = usuario.pop("edad", None)      # Eliminar y retornar

# Iteración
for clave, valor in usuario.items():
    print(f"{clave}: {valor}")

# Dict comprehension
cuadrados = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

### Sets (set)

```python
# Creación
numeros = {1, 2, 3, 4, 5}
vacio = set()  # No {} (eso es dict)

# Operaciones
numeros.add(6)              # Agregar
numeros.remove(3)           # Remover (KeyError si no existe)
numeros.discard(3)          # Remover (sin error si no existe)

# Operaciones de conjuntos
a = {1, 2, 3}
b = {3, 4, 5}
union = a | b               # {1, 2, 3, 4, 5}
interseccion = a & b        # {3}
diferencia = a - b          # {1, 2}

# Set comprehension
pares = {x for x in range(20) if x % 2 == 0}
```

### Tuplas (tuple)

```python
# Creación (inmutables)
coordenadas = (10, 20)
singleton = (1,)  # Nota la coma

# Unpacking
x, y = coordenadas
a, b, *resto = [1, 2, 3, 4, 5]  # resto = [3, 4, 5]

# Named tuples
from collections import namedtuple
Punto = namedtuple('Punto', ['x', 'y'])
p = Punto(10, 20)
print(p.x, p.y)
```

---

## Ejercicios

### 1. filtrar_pares(numeros) ⭐

Filters even numbers from a list.

```python
assert filtrar_pares([1, 2, 3, 4, 5]) == [2, 4]
assert filtrar_pares([]) == []
```

### 2. sumar_valores(diccionario) ⭐

Add all numeric values ​​in a dictionary.

```python
assert sumar_valores({"a": 1, "b": 2, "c": 3}) == 6
assert sumar_valores({}) == 0
```

### 3. invertir_diccionario(diccionario) ⭐⭐

Invierte claves y valores de un diccionario.

```python
assert invertir_diccionario({"a": 1, "b": 2}) == {1: "a", 2: "b"}
```

### 4. encontrar_duplicados(lista) ⭐⭐

Encuentra elementos duplicados en una lista.

```python
assert encontrar_duplicados([1, 2, 2, 3, 3, 3]) == {2, 3}
assert encontrar_duplicados([1, 2, 3]) == set()
```

### 5. agrupar_por_longitud(palabras) ⭐⭐

Agrupa palabras por su longitud.

```python
resultado = agrupar_por_longitud(["hola", "mundo", "a", "python"])
assert resultado == {1: ["a"], 4: ["hola"], 5: ["mundo"], 6: ["python"]}
```

### 6. merge_dictionaries(dict1, dict2) ⭐⭐

Fusiona dos diccionarios (dict2 sobrescribe dict1).

```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 3, "c": 4}
assert merge_dictionaries(d1, d2) == {"a": 1, "b": 3, "c": 4}
```

### 7. contar_frecuencias(texto) ⭐⭐⭐

Cuenta la frecuencia de cada palabra en un texto.

```python
resultado = contar_frecuencias("hola mundo hola")
assert resultado == {"hola": 2, "mundo": 1}
```

### 8. flatten_list(lista_anidada) ⭐⭐⭐

Aplana una lista anidada.

```python
assert flatten_list([[1, 2], [3, 4], [5]]) == [1, 2, 3, 4, 5]
assert flatten_list([[1], [[2, 3]], [4]]) == [1, [2, 3], 4]  # Solo un nivel
```

### 9. crear_matriz(rows, columns, valor) ⭐⭐

Crea una matriz de rows × columns con un valor inicial.

```python
matriz = crear_matriz(2, 3, 0)
assert matriz == [[0, 0, 0], [0, 0, 0]]
```

### 10. transponer_matriz(matriz) ⭐⭐⭐

Transpone una matriz (rows ↔ columns).

```python
matriz = [[1, 2, 3], [4, 5, 6]]
resultado = transponer_matriz(matriz)
assert resultado == [[1, 4], [2, 5], [3, 6]]
```

---

## Execution

```bash
# Ejecutar tests
pytest exercises/02-data-structures/tests/ -v

# Con coverage
pytest exercises/02-data-structures/tests/ --cov

# Test específico
pytest exercises/02-data-structures/tests/test_data_structures.py::test_filtrar_pares -v
```

---

## Tips

1. **Comprehensions**: Use them instead of loops when possible
2. **Sets**: For quick searches and removing duplicates
3. **get()**: Usa `.get()` en dicts para evitar KeyError
4. **Unpacking**: Useful for returning multiple values
5. **Inmutabilidad**: Tuplas para datos que no deben cambiar

---

## resources

- [Python Data Structures](https://docs.python.org/3/tutorial/datastructures.html)
- [List Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)
- [Collections Module](https://docs.python.org/3/library/collections.html)

---

## Siguiente Paso

Una vez completado: ➡️ **Ejercicio 03: File Operations**
