"""
Tests para Ejercicio 01: Python Basics

Ejecutar:
    pytest exercises/01-python-basics/tests/ -v
    pytest exercises/01-python-basics/tests/ -v --cov
"""

import pytest
from exercises.01_python_basics.solution import basics


class TestSuma:
    """Tests para la función suma()."""
    
    def test_suma_positivos(self):
        """Suma de números positivos."""
        assert basics.suma(2, 3) == 5
        assert basics.suma(10, 20) == 30
    
    def test_suma_negativos(self):
        """Suma de números negativos."""
        assert basics.suma(-1, -1) == -2
        assert basics.suma(-5, -10) == -15
    
    def test_suma_mixtos(self):
        """Suma de números positivos y negativos."""
        assert basics.suma(-1, 1) == 0
        assert basics.suma(-5, 10) == 5
    
    def test_suma_con_cero(self):
        """Suma con cero."""
        assert basics.suma(0, 0) == 0
        assert basics.suma(5, 0) == 5
        assert basics.suma(0, -3) == -3


class TestEsPar:
    """Tests para la función es_par()."""
    
    def test_numeros_pares(self):
        """Números pares."""
        assert basics.es_par(0) is True
        assert basics.es_par(2) is True
        assert basics.es_par(4) is True
        assert basics.es_par(100) is True
    
    def test_numeros_impares(self):
        """Números impares."""
        assert basics.es_par(1) is False
        assert basics.es_par(3) is False
        assert basics.es_par(7) is False
        assert basics.es_par(99) is False
    
    def test_numeros_negativos(self):
        """Números negativos."""
        assert basics.es_par(-2) is True
        assert basics.es_par(-3) is False


class TestMayorDeTres:
    """Tests para la función mayor_de_tres()."""
    
    def test_mayor_al_final(self):
        """Mayor número al final."""
        assert basics.mayor_de_tres(1, 2, 3) == 3
    
    def test_mayor_al_inicio(self):
        """Mayor número al inicio."""
        assert basics.mayor_de_tres(10, 5, 3) == 10
    
    def test_mayor_en_medio(self):
        """Mayor número en medio."""
        assert basics.mayor_de_tres(1, 10, 5) == 10
    
    def test_todos_iguales(self):
        """Todos los números iguales."""
        assert basics.mayor_de_tres(5, 5, 5) == 5
    
    def test_con_negativos(self):
        """Con números negativos."""
        assert basics.mayor_de_tres(-1, -5, -3) == -1
        assert basics.mayor_de_tres(-10, 0, -5) == 0


class TestContarVocales:
    """Tests para la función contar_vocales()."""
    
    def test_texto_con_vocales(self):
        """Texto con vocales."""
        assert basics.contar_vocales("Hola Mundo") == 4
        assert basics.contar_vocales("aeiou") == 5
        assert basics.contar_vocales("AEIOU") == 5
    
    def test_texto_sin_vocales(self):
        """Texto sin vocales."""
        assert basics.contar_vocales("xyz") == 0
        assert basics.contar_vocales("bcdfg") == 0
    
    def test_texto_vacio(self):
        """Texto vacío."""
        assert basics.contar_vocales("") == 0
    
    def test_case_insensitive(self):
        """Case insensitive."""
        assert basics.contar_vocales("Python") == 1
        assert basics.contar_vocales("PYTHON") == 1


class TestRevertirString:
    """Tests para la función revertir_string()."""
    
    def test_string_simple(self):
        """String simple."""
        assert basics.revertir_string("hola") == "aloh"
        assert basics.revertir_string("Python") == "nohtyP"
    
    def test_string_vacio(self):
        """String vacío."""
        assert basics.revertir_string("") == ""
    
    def test_string_un_caracter(self):
        """String de un carácter."""
        assert basics.revertir_string("a") == "a"
    
    def test_palindromo(self):
        """Palíndromo."""
        assert basics.revertir_string("oso") == "oso"


class TestEsPalindromo:
    """Tests para la función es_palindromo()."""
    
    def test_palindromos_simples(self):
        """Palíndromos simples."""
        assert basics.es_palindromo("oso") is True
        assert basics.es_palindromo("radar") is True
        assert basics.es_palindromo("reconocer") is True
    
    def test_palindromos_con_espacios(self):
        """Palíndromos con espacios."""
        assert basics.es_palindromo("anita lava la tina") is True
        assert basics.es_palindromo("a man a plan a canal panama") is True
    
    def test_no_palindromos(self):
        """No palíndromos."""
        assert basics.es_palindromo("hola") is False
        assert basics.es_palindromo("Python") is False
    
    def test_string_vacio(self):
        """String vacío."""
        assert basics.es_palindromo("") is True
    
    def test_case_insensitive(self):
        """Case insensitive."""
        assert basics.es_palindromo("Oso") is True
        assert basics.es_palindromo("RaDaR") is True


class TestFactorial:
    """Tests para la función factorial()."""
    
    def test_factoriales_basicos(self):
        """Factoriales básicos."""
        assert basics.factorial(0) == 1
        assert basics.factorial(1) == 1
        assert basics.factorial(2) == 2
        assert basics.factorial(3) == 6
        assert basics.factorial(4) == 24
        assert basics.factorial(5) == 120
    
    def test_factorial_10(self):
        """Factorial de 10."""
        assert basics.factorial(10) == 3628800
    
    def test_factorial_negativo(self):
        """Factorial de número negativo debe lanzar error."""
        with pytest.raises(ValueError):
            basics.factorial(-1)


class TestFibonacci:
    """Tests para la función fibonacci()."""
    
    def test_fibonacci_cero(self):
        """Fibonacci de 0."""
        assert basics.fibonacci(0) == []
    
    def test_fibonacci_uno(self):
        """Fibonacci de 1."""
        assert basics.fibonacci(1) == [0]
    
    def test_fibonacci_pequenos(self):
        """Fibonacci de números pequeños."""
        assert basics.fibonacci(2) == [0, 1]
        assert basics.fibonacci(3) == [0, 1, 1]
        assert basics.fibonacci(5) == [0, 1, 1, 2, 3]
    
    def test_fibonacci_diez(self):
        """Fibonacci de 10."""
        assert basics.fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    
    def test_fibonacci_ultimo_numero(self):
        """Verifica el último número de la secuencia."""
        resultado = basics.fibonacci(15)
        assert resultado[-1] == 377


class TestValidarEmail:
    """Tests para la función validar_email()."""
    
    def test_emails_validos(self):
        """Emails válidos."""
        assert basics.validar_email("user@example.com") is True
        assert basics.validar_email("test@test.org") is True
        assert basics.validar_email("admin@company.co.uk") is True
    
    def test_emails_invalidos(self):
        """Emails inválidos."""
        assert basics.validar_email("invalid.email") is False
        assert basics.validar_email("no@domain") is False
        assert basics.validar_email("@example.com") is False
        assert basics.validar_email("user@") is False
    
    def test_email_none(self):
        """Email None."""
        assert basics.validar_email(None) is False
    
    def test_multiples_arrobas(self):
        """Múltiples arrobas."""
        assert basics.validar_email("user@@example.com") is False
        assert basics.validar_email("us@er@example.com") is False


class TestCalcularPromedio:
    """Tests para la función calcular_promedio()."""
    
    def test_promedio_simple(self):
        """Promedio simple."""
        assert basics.calcular_promedio([1, 2, 3, 4, 5]) == 3.0
        assert basics.calcular_promedio([10, 20, 30]) == 20.0
    
    def test_promedio_un_elemento(self):
        """Promedio de un elemento."""
        assert basics.calcular_promedio([10]) == 10.0
    
    def test_promedio_con_negativos(self):
        """Promedio con negativos."""
        assert basics.calcular_promedio([-1, 1]) == 0.0
        assert basics.calcular_promedio([-10, -20, -30]) == -20.0
    
    def test_promedio_con_decimales(self):
        """Promedio con decimales."""
        resultado = basics.calcular_promedio([1.5, 2.5, 3.0])
        assert abs(resultado - 2.333333) < 0.001
    
    def test_lista_vacia(self):
        """Lista vacía debe lanzar error."""
        with pytest.raises(ValueError):
            basics.calcular_promedio([])


# =============================================================================
# Test de integración
# =============================================================================

def test_integracion_todas_funciones():
    """
    Test de integración que verifica que todas las funciones
    están implementadas y funcionan juntas.
    """
    # Operaciones básicas
    assert basics.suma(2, 3) == 5
    assert basics.es_par(4) is True
    assert basics.mayor_de_tres(1, 2, 3) == 3
    
    # Strings
    assert basics.contar_vocales("Hola") == 2
    assert basics.revertir_string("abc") == "cba"
    assert basics.es_palindromo("oso") is True
    
    # Matemáticas
    assert basics.factorial(5) == 120
    assert len(basics.fibonacci(10)) == 10
    
    # Validaciones
    assert basics.validar_email("test@test.com") is True
    assert basics.calcular_promedio([1, 2, 3]) == 2.0
