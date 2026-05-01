"""
Ejercicio 01: Python Basics - Solution
Fundamentos de Python para Ingeniería de Datos

Este archivo contiene las implementaciones completas de todas las funciones.
"""

from typing import Optional


def suma(a: int, b: int) -> int:
    """
    Suma dos números enteros.
    
    Args:
        a: Primer número entero.
        b: Segundo número entero.
        
    Returns:
        La suma de a y b.
        
    Example:
        >>> suma(2, 3)
        5
    """
    return a + b


def es_par(numero: int) -> bool:
    """
    Determina si un número es par.
    
    Args:
        numero: Número entero a verificar.
        
    Returns:
        True si el número es par, False en caso contrario.
        
    Example:
        >>> es_par(4)
        True
        >>> es_par(7)
        False
    """
    return numero % 2 == 0


def mayor_de_tres(a: int, b: int, c: int) -> int:
    """
    Retorna el mayor de tres números.
    
    Args:
        a: Primer número.
        b: Segundo número.
        c: Tercer número.
        
    Returns:
        El número mayor.
        
    Example:
        >>> mayor_de_tres(1, 2, 3)
        3
    """
    return max(a, b, c)


def contar_vocales(texto: str) -> int:
    """
    Cuenta las vocales en un texto (case-insensitive).
    
    Args:
        texto: Texto a analizar.
        
    Returns:
        Cantidad de vocales encontradas.
        
    Example:
        >>> contar_vocales("Hola Mundo")
        4
    """
    vocales = "aeiouAEIOU"
    return sum(1 for char in texto if char in vocales)


def revertir_string(texto: str) -> str:
    """
    Revierte un string.
    
    Args:
        texto: String a revertir.
        
    Returns:
        String revertido.
        
    Example:
        >>> revertir_string("hola")
        'aloh'
    """
    return texto[::-1]


def es_palindromo(texto: str) -> bool:
    """
    Verifica si un texto es palíndromo (ignora espacios y mayúsculas).
    
    Args:
        texto: Texto a verificar.
        
    Returns:
        True si es palíndromo, False en caso contrario.
        
    Example:
        >>> es_palindromo("oso")
        True
        >>> es_palindromo("anita lava la tina")
        True
    """
    # Limpiar texto: remover espacios y convertir a minúsculas
    texto_limpio = texto.replace(" ", "").lower()
    return texto_limpio == texto_limpio[::-1]


def factorial(n: int) -> int:
    """
    Calcula el factorial de n.
    
    Args:
        n: Número entero no negativo.
        
    Returns:
        El factorial de n.
        
    Raises:
        ValueError: Si n es negativo.
        
    Example:
        >>> factorial(5)
        120
        >>> factorial(0)
        1
    """
    if n < 0:
        raise ValueError("El factorial no está definido para números negativos")
    
    if n == 0 or n == 1:
        return 1
    
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado


def fibonacci(n: int) -> list[int]:
    """
    Retorna los primeros n números de Fibonacci.
    
    La secuencia de Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13, ...
    
    Args:
        n: Cantidad de números a generar.
        
    Returns:
        Lista con los primeros n números de Fibonacci.
        
    Example:
        >>> fibonacci(5)
        [0, 1, 1, 2, 3]
        >>> fibonacci(0)
        []
    """
    if n <= 0:
        return []
    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i - 1] + fib[i - 2])
    return fib


def validar_email(email: Optional[str]) -> bool:
    """
    Valida formato básico de email (contiene @ y punto después del @).
    
    Args:
        email: String con el email a validar, o None.
        
    Returns:
        True si el email tiene formato válido, False en caso contrario.
        
    Example:
        >>> validar_email("user@example.com")
        True
        >>> validar_email("invalid.email")
        False
        >>> validar_email(None)
        False
    """
    if email is None:
        return False
    
    # Verificar que contenga exactamente un @
    if email.count("@") != 1:
        return False
    
    # Separar local y dominio
    local, dominio = email.split("@")
    
    # Validar que ambas partes tengan contenido
    if not local or not dominio:
        return False
    
    # Validar que el dominio contenga al menos un punto
    if "." not in dominio:
        return False
    
    return True


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
        >>> calcular_promedio([1, 2, 3, 4, 5])
        3.0
    """
    if not numeros:
        raise ValueError("La lista no puede estar vacía")
    
    return sum(numeros) / len(numeros)


# =============================================================================
# Demostración de uso
# =============================================================================

if __name__ == "__main__":
    print("🐍 Python Basics - Soluciones\n")
    
    # Operaciones básicas
    print("1. Suma:")
    print(f"   suma(2, 3) = {suma(2, 3)}")
    print(f"   suma(-5, 10) = {suma(-5, 10)}\n")
    
    # Verificaciones
    print("2. Es par:")
    print(f"   es_par(4) = {es_par(4)}")
    print(f"   es_par(7) = {es_par(7)}\n")
    
    # Comparaciones
    print("3. Mayor de tres:")
    print(f"   mayor_de_tres(1, 2, 3) = {mayor_de_tres(1, 2, 3)}")
    print(f"   mayor_de_tres(10, 5, 8) = {mayor_de_tres(10, 5, 8)}\n")
    
    # Strings
    print("4. Contar vocales:")
    print(f"   contar_vocales('Hola Mundo') = {contar_vocales('Hola Mundo')}")
    print(f"   contar_vocales('Python') = {contar_vocales('Python')}\n")
    
    print("5. Revertir string:")
    print(f"   revertir_string('hola') = {revertir_string('hola')}")
    print(f"   revertir_string('Python') = {revertir_string('Python')}\n")
    
    print("6. Palíndromo:")
    print(f"   es_palindromo('oso') = {es_palindromo('oso')}")
    print(f"   es_palindromo('anita lava la tina') = {es_palindromo('anita lava la tina')}")
    print(f"   es_palindromo('hola') = {es_palindromo('hola')}\n")
    
    # Matemáticas
    print("7. Factorial:")
    print(f"   factorial(5) = {factorial(5)}")
    print(f"   factorial(0) = {factorial(0)}\n")
    
    print("8. Fibonacci:")
    print(f"   fibonacci(10) = {fibonacci(10)}\n")
    
    # Validaciones
    print("9. Validar email:")
    print(f"   validar_email('user@example.com') = {validar_email('user@example.com')}")
    print(f"   validar_email('invalid.email') = {validar_email('invalid.email')}")
    print(f"   validar_email(None) = {validar_email(None)}\n")
    
    # Estadísticas
    print("10. Promedio:")
    print(f"    calcular_promedio([1, 2, 3, 4, 5]) = {calcular_promedio([1, 2, 3, 4, 5])}")
    print(f"    calcular_promedio([10, 20, 30]) = {calcular_promedio([10, 20, 30])}\n")
    
    print("✅ Todas las funciones ejecutadas correctamente")
