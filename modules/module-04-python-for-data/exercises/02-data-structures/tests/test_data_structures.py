"""
Tests para Ejercicio 02: Data Structures

Ejecutar:
    pytest exercises/02-data-structures/tests/ -v
    pytest exercises/02-data-structures/tests/ --cov
"""

import pytest
from exercises.02_data_structures.solution import data_structures


class TestFiltrarPares:
    """Tests para la función filtrar_pares()."""
    
    def test_lista_mixta(self):
        """Lista con números pares e impares."""
        assert data_structures.filtrar_pares([1, 2, 3, 4, 5]) == [2, 4]
        assert data_structures.filtrar_pares([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == [2, 4, 6, 8, 10]
    
    def test_solo_pares(self):
        """Lista solo con pares."""
        assert data_structures.filtrar_pares([2, 4, 6, 8]) == [2, 4, 6, 8]
    
    def test_solo_impares(self):
        """Lista solo con impares."""
        assert data_structures.filtrar_pares([1, 3, 5, 7]) == []
    
    def test_lista_vacia(self):
        """Lista vacía."""
        assert data_structures.filtrar_pares([]) == []
    
    def test_con_negativos(self):
        """Números negativos."""
        assert data_structures.filtrar_pares([-2, -1, 0, 1, 2]) == [-2, 0, 2]


class TestSumarValores:
    """Tests para la función sumar_valores()."""
    
    def test_diccionario_simple(self):
        """Diccionario simple."""
        assert data_structures.sumar_valores({"a": 1, "b": 2, "c": 3}) == 6
    
    def test_diccionario_vacio(self):
        """Diccionario vacío."""
        assert data_structures.sumar_valores({}) == 0
    
    def test_un_elemento(self):
        """Un solo elemento."""
        assert data_structures.sumar_valores({"x": 10}) == 10
    
    def test_con_negativos(self):
        """Con valores negativos."""
        assert data_structures.sumar_valores({"a": -1, "b": 2, "c": -3}) == -2


class TestInvertirDiccionario:
    """Tests para la función invertir_diccionario()."""
    
    def test_invertir_simple(self):
        """Inversión simple."""
        resultado = data_structures.invertir_diccionario({"a": 1, "b": 2})
        assert resultado == {1: "a", 2: "b"}
    
    def test_invertir_vacio(self):
        """Diccionario vacío."""
        assert data_structures.invertir_diccionario({}) == {}
    
    def test_valores_string(self):
        """Valores string."""
        resultado = data_structures.invertir_diccionario({"1": "a", "2": "b"})
        assert resultado == {"a": "1", "b": "2"}


class TestEncontrarDuplicados:
    """Tests para la función encontrar_duplicados()."""
    
    def test_con_duplicados(self):
        """Lista con duplicados."""
        assert data_structures.encontrar_duplicados([1, 2, 2, 3, 3, 3]) == {2, 3}
    
    def test_sin_duplicados(self):
        """Lista sin duplicados."""
        assert data_structures.encontrar_duplicados([1, 2, 3, 4]) == set()
    
    def test_todos_duplicados(self):
        """Todos los elementos duplicados."""
        assert data_structures.encontrar_duplicados([1, 1, 2, 2, 3, 3]) == {1, 2, 3}
    
    def test_lista_vacia(self):
        """Lista vacía."""
        assert data_structures.encontrar_duplicados([]) == set()
    
    def test_strings(self):
        """Con strings."""
        resultado = data_structures.encontrar_duplicados(["a", "b", "b", "c", "c", "c"])
        assert resultado == {"b", "c"}


class TestAgruparPorLongitud:
    """Tests para la función agrupar_por_longitud()."""
    
    def test_agrupar_simple(self):
        """Agrupación simple."""
        resultado = data_structures.agrupar_por_longitud(["hola", "mundo", "a", "python"])
        assert resultado == {1: ["a"], 4: ["hola"], 5: ["mundo"], 6: ["python"]}
    
    def test_mismo_largo(self):
        """Varias palabras del mismo largo."""
        resultado = data_structures.agrupar_por_longitud(["casa", "mesa", "silla", "cama"])
        assert resultado[4] == ["casa", "mesa", "cama"]
        assert resultado[5] == ["silla"]
    
    def test_lista_vacia(self):
        """Lista vacía."""
        assert data_structures.agrupar_por_longitud([]) == {}


class TestMergeDictionaries:
    """Tests para la función merge_dictionaries()."""
    
    def test_merge_simple(self):
        """Merge simple."""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 3, "c": 4}
        resultado = data_structures.merge_dictionaries(d1, d2)
        assert resultado == {"a": 1, "b": 3, "c": 4}
    
    def test_merge_sin_conflictos(self):
        """Merge sin conflictos."""
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3, "d": 4}
        resultado = data_structures.merge_dictionaries(d1, d2)
        assert resultado == {"a": 1, "b": 2, "c": 3, "d": 4}
    
    def test_merge_vacios(self):
        """Merge con diccionarios vacíos."""
        assert data_structures.merge_dictionaries({}, {}) == {}
        assert data_structures.merge_dictionaries({"a": 1}, {}) == {"a": 1}
        assert data_structures.merge_dictionaries({}, {"b": 2}) == {"b": 2}


class TestContarFrecuencias:
    """Tests para la función contar_frecuencias()."""
    
    def test_frecuencias_simples(self):
        """Frecuencias simples."""
        resultado = data_structures.contar_frecuencias("hola mundo hola")
        assert resultado == {"hola": 2, "mundo": 1}
    
    def test_una_palabra(self):
        """Una sola palabra."""
        resultado = data_structures.contar_frecuencias("hola")
        assert resultado == {"hola": 1}
    
    def test_texto_vacio(self):
        """Texto vacío."""
        resultado = data_structures.contar_frecuencias("")
        assert resultado == {"": 1}
    
    def test_frecuencias_multiples(self):
        """Múltiples palabras repetidas."""
        resultado = data_structures.contar_frecuencias("python es genial python es python")
        assert resultado == {"python": 3, "es": 2, "genial": 1}


class TestFlattenList:
    """Tests para la función flatten_list()."""
    
    def test_flatten_simple(self):
        """Aplanar lista simple."""
        assert data_structures.flatten_list([[1, 2], [3, 4], [5]]) == [1, 2, 3, 4, 5]
    
    def test_sublistas_vacias(self):
        """Con sublistas vacías."""
        assert data_structures.flatten_list([[], [1, 2], [], [3]]) == [1, 2, 3]
    
    def test_lista_vacia(self):
        """Lista vacía."""
        assert data_structures.flatten_list([]) == []
    
    def test_un_nivel(self):
        """Solo aplana un nivel."""
        resultado = data_structures.flatten_list([[1], [[2, 3]], [4]])
        assert resultado == [1, [2, 3], 4]


class TestCrearMatriz:
    """Tests para la función crear_matriz()."""
    
    def test_matriz_simple(self):
        """Matriz simple."""
        matriz = data_structures.crear_matriz(2, 3, 0)
        assert matriz == [[0, 0, 0], [0, 0, 0]]
        assert len(matriz) == 2
        assert len(matriz[0]) == 3
    
    def test_matriz_identidad_prep(self):
        """Preparación para matriz identidad."""
        matriz = data_structures.crear_matriz(3, 3, 0)
        assert matriz == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    
    def test_valores_personalizados(self):
        """Con valores personalizados."""
        matriz = data_structures.crear_matriz(2, 2, 5)
        assert matriz == [[5, 5], [5, 5]]
    
    def test_independencia_filas(self):
        """Verificar que las filas son independientes."""
        matriz = data_structures.crear_matriz(2, 2, 0)
        matriz[0][0] = 1
        assert matriz[0][0] == 1
        assert matriz[1][0] == 0  # No debe cambiar


class TestTransponerMatriz:
    """Tests para la función transponer_matriz()."""
    
    def test_transponer_rectangular(self):
        """Matriz rectangular."""
        matriz = [[1, 2, 3], [4, 5, 6]]
        resultado = data_structures.transponer_matriz(matriz)
        assert resultado == [[1, 4], [2, 5], [3, 6]]
    
    def test_transponer_cuadrada(self):
        """Matriz cuadrada."""
        matriz = [[1, 2], [3, 4]]
        resultado = data_structures.transponer_matriz(matriz)
        assert resultado == [[1, 3], [2, 4]]
    
    def test_transponer_una_fila(self):
        """Matriz de una fila."""
        matriz = [[1, 2, 3]]
        resultado = data_structures.transponer_matriz(matriz)
        assert resultado == [[1], [2], [3]]
    
    def test_transponer_una_columna(self):
        """Matriz de una columna."""
        matriz = [[1], [2], [3]]
        resultado = data_structures.transponer_matriz(matriz)
        assert resultado == [[1, 2, 3]]


# =============================================================================
# Test de integración
# =============================================================================

def test_integracion_pipeline_datos():
    """
    Test de integración: pipeline de procesamiento de datos.
    """
    # 1. Datos de entrada
    numeros = [1, 2, 2, 3, 3, 3, 4, 5, 5]
    
    # 2. Filtrar pares
    pares = data_structures.filtrar_pares(numeros)
    assert pares == [2, 2, 4]
    
    # 3. Encontrar duplicados en pares
    duplicados = data_structures.encontrar_duplicados(pares)
    assert duplicados == {2}
    
    # 4. Crear diccionario de frecuencias
    texto = "python es genial python es"
    frecuencias = data_structures.contar_frecuencias(texto)
    assert frecuencias["python"] == 2
    
    # 5. Sumar frecuencias
    total = data_structures.sumar_valores(frecuencias)
    assert total == 5
