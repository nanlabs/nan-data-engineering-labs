"""
Ejercicio 01: Python Basics - Starter
Fundamentos de Python para Ingeniería de Datos

Instrucciones:
1. Implementa todas las funciones marcadas con TODO
2. Agrega type hints a todas las funciones
3. Escribe docstrings en formato Google
4. Maneja casos edge (None, vacío, negativos)
5. Ejecuta: pytest exercises/01-python-basics/tests/ -v
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
    # TODO: Implementar suma
    pass


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
    # TODO: Implementar verificación de paridad
    pass


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
    # TODO: Implementar búsqueda del mayor
    pass


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
    # TODO: Implementar conteo de vocales
    # Tip: Convierte a minúsculas y verifica si cada char está en "aeiou"
    pass


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
    # TODO: Implementar reversión
    # Tip: Usa slicing [::-1]
    pass


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
    # TODO: Implementar verificación de palíndromo
    # Tip: Limpia espacios, convierte a minúsculas, compara con versión revertida
    pass


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
    # TODO: Implementar factorial
    # Casos especiales: factorial(0) = 1, factorial(1) = 1
    # Validar que n no sea negativo
    pass


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
    # TODO: Implementar generación de Fibonacci
    # Casos especiales: n=0 -> [], n=1 -> [0], n=2 -> [0, 1]
    pass


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
    # TODO: Implementar validación de email
    # Validar que no sea None
    # Validar que contenga exactamente un @
    # Validar que después del @ haya al menos un punto
    pass


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
    # TODO: Implementar cálculo de promedio
    # Validar que la lista no esté vacía
    pass


# =============================================================================
# Función auxiliar para testing (NO MODIFICAR)
# =============================================================================

def test_all_functions():
    """
    Función de prueba rápida. Ejecuta algunos casos de prueba básicos.
    NO reemplaza los tests unitarios completos.
    """
    print("🧪 Probando funciones básicas...")
    
    try:
        assert suma(2, 3) == 5, "suma() falló"
        print("✅ suma() OK")
    except (AssertionError, Exception) as e:
        print(f"❌ suma() falló: {e}")
    
    try:
        assert es_par(4) == True, "es_par() falló"
        print("✅ es_par() OK")
    except (AssertionError, Exception) as e:
        print(f"❌ es_par() falló: {e}")
    
    try:
        assert mayor_de_tres(1, 2, 3) == 3, "mayor_de_tres() falló"
        print("✅ mayor_de_tres() OK")
    except (AssertionError, Exception) as e:
        print(f"❌ mayor_de_tres() falló: {e}")
    
    print("\n⚠️  Para tests completos ejecuta: pytest exercises/01-python-basics/tests/ -v")


if __name__ == "__main__":
    test_all_functions()
