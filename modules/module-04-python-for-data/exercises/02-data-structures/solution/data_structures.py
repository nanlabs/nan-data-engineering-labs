"""
Ejercicio 02: Data Structures - Solution
Estructuras de Datos en Python

Este archivo contiene las implementaciones completas de todas las funciones.
"""

from typing import Any
from collections import Counter


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
    return [num for num in numeros if num % 2 == 0]


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
    return sum(diccionario.values())


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
    return {valor: clave for clave, valor in diccionario.items()}


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
    contador = Counter(lista)
    return {elemento for elemento, freq in contador.items() if freq > 1}


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
    resultado = {}
    for palabra in palabras:
        longitud = len(palabra)
        if longitud not in resultado:
            resultado[longitud] = []
        resultado[longitud].append(palabra)
    return resultado


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
    return {**dict1, **dict2}


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
    palabras = texto.split()
    return dict(Counter(palabras))


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
    return [elemento for sublista in lista_anidada for elemento in sublista]


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
    return [[valor for _ in range(columnas)] for _ in range(filas)]


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
    return [list(fila) for fila in zip(*matriz)]


# =============================================================================
# Demostración de uso
# =============================================================================

if __name__ == "__main__":
    print("📊 Data Structures - Soluciones\n")
    
    # Listas
    print("1. Filtrar pares:")
    numeros = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"   Original: {numeros}")
    print(f"   Pares: {filtrar_pares(numeros)}\n")
    
    # Diccionarios
    print("2. Sumar valores:")
    ventas = {"enero": 100, "febrero": 200, "marzo": 150}
    print(f"   Ventas: {ventas}")
    print(f"   Total: {sumar_valores(ventas)}\n")
    
    print("3. Invertir diccionario:")
    original = {"a": 1, "b": 2, "c": 3}
    invertido = invertir_diccionario(original)
    print(f"   Original: {original}")
    print(f"   Invertido: {invertido}\n")
    
    # Sets
    print("4. Encontrar duplicados:")
    lista = [1, 2, 2, 3, 3, 3, 4, 5, 5]
    print(f"   Lista: {lista}")
    print(f"   Duplicados: {encontrar_duplicados(lista)}\n")
    
    # Agrupación
    print("5. Agrupar por longitud:")
    palabras = ["hola", "mundo", "a", "python", "es", "genial"]
    print(f"   Palabras: {palabras}")
    print(f"   Agrupadas: {agrupar_por_longitud(palabras)}\n")
    
    # Merge
    print("6. Merge dictionaries:")
    dict1 = {"a": 1, "b": 2}
    dict2 = {"b": 3, "c": 4}
    print(f"   Dict1: {dict1}")
    print(f"   Dict2: {dict2}")
    print(f"   Merged: {merge_dictionaries(dict1, dict2)}\n")
    
    # Frecuencias
    print("7. Contar frecuencias:")
    texto = "hola mundo hola python mundo mundo"
    print(f"   Texto: '{texto}'")
    print(f"   Frecuencias: {contar_frecuencias(texto)}\n")
    
    # Flatten
    print("8. Flatten list:")
    anidada = [[1, 2], [3, 4, 5], [6]]
    print(f"   Anidada: {anidada}")
    print(f"   Aplanada: {flatten_list(anidada)}\n")
    
    # Matrices
    print("9. Crear matriz:")
    matriz = crear_matriz(3, 4, 0)
    print(f"   Matriz 3x4:")
    for fila in matriz:
        print(f"   {fila}")
    print()
    
    print("10. Transponer matriz:")
    original = [[1, 2, 3], [4, 5, 6]]
    transpuesta = transponer_matriz(original)
    print(f"    Original (2x3):")
    for fila in original:
        print(f"    {fila}")
    print(f"    Transpuesta (3x2):")
    for fila in transpuesta:
        print(f"    {fila}")
    
    print("\n✅ Todas las funciones ejecutadas correctamente")
