"""
Configuración global de pytest para el Módulo 04.

Este archivo contiene fixtures compartidas por todos los tests.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
module_root = Path(__file__).parent.parent
sys.path.insert(0, str(module_root))


# =============================================================================
# FIXTURES DE DATASETS
# =============================================================================

@pytest.fixture(scope="session")
def data_dir():
    """Directorio de datos."""
    return module_root / "data" / "raw"


@pytest.fixture(scope="session")
def customers_df(data_dir):
    """DataFrame de customers (10K registros)."""
    return pd.read_csv(data_dir / "customers.csv")


@pytest.fixture(scope="session")
def transactions_df(data_dir):
    """DataFrame de transactions (100K registros)."""
    return pd.read_csv(data_dir / "transactions.csv")


@pytest.fixture(scope="session")
def products_df(data_dir):
    """DataFrame de products (500 registros)."""
    return pd.read_csv(data_dir / "products.csv")


@pytest.fixture(scope="session")
def orders_json(data_dir):
    """Datos de orders en JSON (50K registros)."""
    return pd.read_json(data_dir / "orders.json")


@pytest.fixture(scope="session")
def user_activity_json(data_dir):
    """Datos de user_activity en JSON (20K registros)."""
    return pd.read_json(data_dir / "user_activity.json")


# =============================================================================
# FIXTURES DE UTILIDADES
# =============================================================================

@pytest.fixture
def sample_df():
    """DataFrame pequeño para tests rápidos."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "nombre": ["Ana", "Luis", "María", "Pedro", "Laura"],
        "edad": [25, 30, 28, 35, 22],
        "ciudad": ["Madrid", "Barcelona", "Madrid", "Valencia", "Barcelona"]
    })


@pytest.fixture
def sample_df_with_nulls():
    """DataFrame con valores nulos."""
    return pd.DataFrame({
        "a": [1, 2, None, 4, 5],
        "b": ["x", None, "z", "w", "v"],
        "c": [1.1, 2.2, 3.3, None, 5.5]
    })


@pytest.fixture
def sample_df_with_duplicates():
    """DataFrame con duplicados."""
    return pd.DataFrame({
        "id": [1, 2, 2, 3, 3, 3],
        "valor": [10, 20, 20, 30, 30, 30]
    })


@pytest.fixture
def temp_csv_file(tmp_path):
    """Archivo CSV temporal para tests."""
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def temp_json_file(tmp_path):
    """Archivo JSON temporal para tests."""
    import json
    json_path = tmp_path / "test.json"
    data = {"nombre": "Test", "valor": 123}
    with open(json_path, "w") as f:
        json.dump(data, f)
    return json_path


# =============================================================================
# FIXTURES DE VALIDACIÓN
# =============================================================================

@pytest.fixture
def module_structure():
    """Estructura esperada del módulo."""
    return {
        "exercises": [
            "01-python-basics",
            "02-data-structures",
            "03-file-operations",
            "04-pandas-fundamentals",
            "05-data-transformation",
            "06-error-handling"
        ],
        "data_files": [
            "customers.csv",
            "orders.json",
            "products.csv",
            "transactions.csv",
            "user_activity.json"
        ],
        "schemas": [
            "customers_schema.json",
            "orders_schema.json",
            "products_schema.json",
            "transactions_schema.json",
            "user_activity_schema.json"
        ]
    }


# =============================================================================
# MARKERS PARA CATEGORIZAR TESTS
# =============================================================================

def pytest_configure(config):
    """Registra markers personalizados."""
    config.addinivalue_line("markers", "slow: marca tests lentos")
    config.addinivalue_line("markers", "integration: tests de integración")
    config.addinivalue_line("markers", "data: tests que usan datasets reales")
    config.addinivalue_line("markers", "unit: tests unitarios rápidos")


# =============================================================================
# HOOKS DE PYTEST
# =============================================================================

def pytest_collection_modifyitems(config, items):
    """Modifica items de tests recolectados."""
    for item in items:
        # Agregar marker 'data' automáticamente si usa fixtures de datos
        if any(fixture in item.fixturenames for fixture in 
               ["customers_df", "transactions_df", "products_df", "orders_json", "user_activity_json"]):
            item.add_marker(pytest.mark.data)


# =============================================================================
# REPORTE DE COBERTURA
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_coverage():
    """Configura coverage para el módulo."""
    # Esta fixture se ejecuta automáticamente al inicio de la sesión
    yield
    # Aquí podrías agregar cleanup o reportes adicionales


# =============================================================================
# UTILIDADES DE TESTING
# =============================================================================

@pytest.fixture
def assert_frame_equal():
    """Helper para comparar DataFrames."""
    from pandas.testing import assert_frame_equal as afe
    return afe


@pytest.fixture
def assert_series_equal():
    """Helper para comparar Series."""
    from pandas.testing import assert_series_equal as ase
    return ase
