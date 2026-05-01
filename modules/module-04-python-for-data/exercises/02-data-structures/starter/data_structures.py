"""
Ejercicio 02: Data Structures - Starter
Estructuras de Datos en Python

Instrucciones:
1. Implementa todas las funciones marcadas con TODO
2. Usa comprehensions donde sea apropiado
3. Agrega type hints y docstrings
4. Maneja casos edge (vacío, None)
5. Ejecuta: pytest exercises/02-data-structures/tests/ -v
"""

from typing import Any


def filtrar_pares(numeros: list[int]) -> list[int]:
    """
    Filtra números pares de una lista.
    
    Args:
        numeros: Lista de números enteros.
        
    Returns:
        Lista con solo los números pares.
        
    Example:
        >>> filtrar_pares([1, 2, 3, 4, 5])
        [2, 4]
    """
    # TODO: Implementar filtrado de pares
    # Tip: Usa list comprehension con condición
    pass


def sumar_valores(diccionario: dict[str, int]) -> int:
    """
    Suma todos los valores numéricos de un diccionario.
    
    Args:
        diccionario: Diccionario con valores enteros.
        
    Returns:
        La suma de todos los valores.
        
    Example:
        >>> sumar_valores({"a": 1, "b": 2, "c": 3})
        6
    """
    # TODO: Implementar suma de valores
    # Tip: Usa sum() con dict.values()
    pass


def invertir_diccionario(diccionario: dict[str, Any]) -> dict[Any, str]:
    """
    Invierte claves y valores de un diccionario.
    
    Args:
        diccionario: Diccionario a invertir.
        
    Returns:
        Nuevo diccionario con claves y valores invertidos.
        
    Example:
        >>> invertir_diccionario({"a": 1, "b": 2})
        {1: 'a', 2: 'b'}
    """
    # TODO: Implementar inversión de diccionario
    # Tip: Usa dict comprehension
    pass


def encontrar_duplicados(lista: list[Any]) -> set[Any]:
    """
    Encuentra elementos duplicados en una lista.
    
    Args:
        lista: Lista de elementos.
        
    Returns:
        Set con los elementos que aparecen más de una vez.
        
    Example:
        >>> encontrar_duplicados([1, 2, 2, 3, 3, 3])
        {2, 3}
    """
    # TODO: Implementar detección de duplicados
    # Tip: Cuenta frecuencias y filtra los que aparecen > 1
    pass


def agrupar_por_longitud(palabras: list[str]) -> dict[int, list[str]]:
    """
    Agrupa palabras por su longitud.
    
    Args:
        palabras: Lista de palabras.
        
    Returns:
        Diccionario donde las claves son longitudes y los valores son listas de palabras.
        
    Example:
        >>> agrupar_por_longitud(["hola", "mundo", "a"])
        {1: ['a'], 4: ['hola'], 5: ['mundo']}
    """
    # TODO: Implementar agrupación por longitud
    # Tip: Itera sobre palabras y agrégalas al grupo correspondiente
    pass


def merge_dictionaries(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """
    Fusiona dos diccionarios (dict2 sobrescribe valores de dict1).
    
    Args:
        dict1: Primer diccionario.
        dict2: Segundo diccionario (prioridad en conflictos).
        
    Returns:
        Nuevo diccionario fusionado.
        
    Example:
        >>> merge_dictionaries({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 3, 'c': 4}
    """
    # TODO: Implementar merge de diccionarios
    # Tip: Usa {**dict1, **dict2} o dict.update()
    pass


def contar_frecuencias(texto: str) -> dict[str, int]:
    """
    Cuenta la frecuencia de cada palabra en un texto.
    
    Args:
        texto: Texto a analizar.
        
    Returns:
        Diccionario con palabras como claves y frecuencias como valores.
        
    Example:
        >>> contar_frecuencias("hola mundo hola")
        {'hola': 2, 'mundo': 1}
    """
    # TODO: Implementar conteo de frecuencias
    # Tip: Split por espacios, itera y cuenta
    pass


def flatten_list(lista_anidada: list[list[Any]]) -> list[Any]:
    """
    Aplana una lista anidada (solo un nivel).
    
    Args:
        lista_anidada: Lista que contiene sublistas.
        
    Returns:
        Lista aplanada.
        
    Example:
        >>> flatten_list([[1, 2], [3, 4], [5]])
        [1, 2, 3, 4, 5]
    """
    # TODO: Implementar aplanado de lista
    # Tip: Usa list comprehension con doble for
    pass


def crear_matriz(filas: int, columnas: int, valor: Any = 0) -> list[list[Any]]:
    """
    Crea una matriz de filas × columnas con un valor inicial.
    
    Args:
        filas: Número de filas.
        columnas: Número de columnas.
        valor: Valor inicial para cada celda (default: 0).
        
    Returns:
        Matriz (lista de listas).
        
    Example:
        >>> crear_matriz(2, 3, 0)
        [[0, 0, 0], [0, 0, 0]]
    """
    # TODO: Implementar creación de matriz
    # IMPORTANTE: No uses [[valor] * columnas] * filas (referencias compartidas)
    # Usa list comprehension anidada
    pass


def transponer_matriz(matriz: list[list[Any]]) -> list[list[Any]]:
    """
    Transpone una matriz (intercambia filas y columnas).
    
    Args:
        matriz: Matriz a transponer.
        
    Returns:
        Matriz transpuesta.
        
    Example:
        >>> transponer_matriz([[1, 2, 3], [4, 5, 6]])
        [[1, 4], [2, 5], [3, 6]]
    """
    # TODO: Implementar transposición
    # Tip: Usa zip(*matriz) y convierte a lista de listas
    pass


# =============================================================================
# Función auxiliar para testing (NO MODIFICAR)
# =============================================================================

def test_all_functions():
    """
    Función de prueba rápida. Ejecuta algunos casos de prueba básicos.
    NO reemplaza los tests unitarios completos.
    """
    print("🧪 Probando estructuras de datos...")
    
    try:
        assert filtrar_pares([1, 2, 3, 4, 5]) == [2, 4], "filtrar_pares() falló"
        print("✅ filtrar_pares() OK")
    except (AssertionError, Exception) as e:
        print(f"❌ filtrar_pares() falló: {e}")
    
    try:
        assert sumar_valores({"a": 1, "b": 2, "c": 3}) == 6, "sumar_valores() falló"
        print("✅ sumar_valores() OK")
    except (AssertionError, Exception) as e:
        print(f"❌ sumar_valores() falló: {e}")
    
    try:
        resultado = invertir_diccionario({"a": 1, "b": 2})
        assert resultado == {1: "a", 2: "b"}, "invertir_diccionario() falló"
        print("✅ invertir_diccionario() OK")
    except (AssertionError, Exception) as e:
        print(f"❌ invertir_diccionario() falló: {e}")
    
    print("\n⚠️  Para tests completos ejecuta: pytest exercises/02-data-structures/tests/ -v")


if __name__ == "__main__":
    test_all_functions()
