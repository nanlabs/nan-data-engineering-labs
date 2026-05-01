# Ejercicio 01: Python Basics

## Objetivos de Aprendizaje

After completing this exercise, you will be able to:

1. ✅ Escribir funciones con **type hints** y **docstrings**
2. ✅ Use operators and basic flow control
3. ✅ Manejar **valores None** y casos edge
4. ✅ Trabajar con **strings** y formateo
5. ✅ Aplicar best practices de Python (PEP 8)

---

## Conceptos Clave

### Type Hints (Python 3.5+)

```python
def suma(a: int, b: int) -> int:
    """Suma dos números enteros."""
    return a + b

def procesar_nombre(nombre: str) -> str:
    """Convierte nombre a mayúsculas."""
    return nombre.upper()

# Con tipos opcionales
from typing import Optional

def buscar_usuario(id: int) -> Optional[dict]:
    """Busca un usuario. Retorna None si no existe."""
    # ...
    return None  # o dict
```

**Why they are important**:
- Improve code readability
- Allow error detection with mypy
- Facilitan autocompletado en IDEs
- Documentan contratos de funciones

### Docstrings (Google Style)

```python
def calcular_promedio(numeros: list[float]) -> float:
    """
    Calcula el promedio de una lista de números.
    
    Args:
        numeros: Lista de números flotantes.
        
    Returns:
        El promedio como float.
        
    Raises:
        ValueError: Si la lista está vacía.
        
    Example:
        >>> calcular_promedio([1.0, 2.0, 3.0])
        2.0
    """
    if not numeros:
        raise ValueError("La lista no puede estar vacía")
    return sum(numeros) / len(numeros)
```

### Control de Flujo

```python
# If/elif/else
edad = 25
if edad >= 18:
    print("Mayor de edad")
elif edad >= 13:
    print("Adolescente")
else:
    print("Niño")

# Ternario (inline if)
estado = "activo" if edad >= 18 else "inactivo"

# For loop
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# While loop
contador = 0
while contador < 5:
    print(contador)
    contador += 1
```

### Manejo de None

```python
# Mal ❌
nombre = obtener_nombre()
if nombre != None:  # Usar 'is' no '!='
    print(nombre.upper())

# Bien ✅
nombre = obtener_nombre()
if nombre is not None:
    print(nombre.upper())

# Aún mejor ✅
nombre = obtener_nombre()
if nombre:  # Truthy check
    print(nombre.upper())
```

---

## Ejercicios

Implementa las siguientes funciones en `starter/basics.py`.

### 1. suma(a, b) ⭐

Add two numbers.

```python
assert suma(2, 3) == 5
assert suma(-1, 1) == 0
assert suma(0, 0) == 0
```

### 2. es_par(numero) ⭐

Determine if a number is even.

```python
assert es_par(4) == True
assert es_par(7) == False
assert es_par(0) == True
```

### 3. mayor_de_tres(a, b, c) ⭐

Returns the largest of three numbers.

```python
assert mayor_de_tres(1, 2, 3) == 3
assert mayor_de_tres(5, 5, 5) == 5
assert mayor_de_tres(-1, -5, -3) == -1
```

### 4. contar_vocales(texto) ⭐⭐

Cuenta las vocales en un texto (case-insensitive).

```python
assert contar_vocales("Hola Mundo") == 4
assert contar_vocales("aeiou") == 5
assert contar_vocales("xyz") == 0
assert contar_vocales("") == 0
```

### 5. revertir_string(texto) ⭐⭐

Revierte un string.

```python
assert revertir_string("hola") == "aloh"
assert revertir_string("Python") == "nohtyP"
assert revertir_string("") == ""
```

### 6. es_palindromo(texto) ⭐⭐

Checks if a text is palindrome (ignores spaces and capital letters).

```python
assert es_palindromo("oso") == True
assert es_palindromo("anita lava la tina") == True
assert es_palindromo("hola") == False
assert es_palindromo("") == True
```

### 7. factorial(n) ⭐⭐

Calcula el factorial de n.

```python
assert factorial(0) == 1
assert factorial(1) == 1
assert factorial(5) == 120
```

### 8. fibonacci(n) ⭐⭐⭐

Returns the first n Fibonacci numbers.

```python
assert fibonacci(0) == []
assert fibonacci(1) == [0]
assert fibonacci(5) == [0, 1, 1, 2, 3]
assert fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### 9. validar_email(email) ⭐⭐⭐

Validates basic email format (contains @ and .).

```python
assert validar_email("user@example.com") == True
assert validar_email("invalid.email") == False
assert validar_email("no@domain") == False
assert validar_email(None) == False
```

### 10. calcular_promedio(numeros) ⭐⭐

Calculates the average of a list of numbers.

```python
assert calcular_promedio([1, 2, 3, 4, 5]) == 3.0
assert calcular_promedio([10]) == 10.0
# Debe manejar lista vacía
```

---

## Execution

```bash
# Ejecutar tests
pytest exercises/01-python-basics/tests/ -v

# Con coverage
pytest exercises/01-python-basics/tests/ --cov=exercises.01-python-basics.starter

# Ejecutar un test específico
pytest exercises/01-python-basics/tests/test_basics.py::test_suma -v
```

---

## Tips

1. **Type hints**: Add them to all functions
2. **Docstrings**: Usa formato Google
3. **Edge cases**: Handles empty, None, negative values
4. **PEP 8**: Usa nombres descriptivos en snake_case
5. **Tests primero**: Lee los tests antes de implementar

---

## resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [PEP 8 Style Guide](https://pep8.org/)
- [Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)

---

## Siguiente Paso

Una vez completado: ➡️ **Ejercicio 02: Data Structures**
