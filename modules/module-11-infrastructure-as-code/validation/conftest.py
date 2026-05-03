# Configuración pytest para módulo de Infrastructure as Code

import pytest
import os


@pytest.fixture(scope="session")
def module_root():
    """Retorna el path raíz del módulo"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def exercises_dir(module_root):
    """Retorna el directorio de ejercicios"""
    return os.path.join(module_root, "exercises")


@pytest.fixture(scope="session")
def infrastructure_dir(module_root):
    """Retorna el directorio de infraestructura"""
    return os.path.join(module_root, "infrastructure")


@pytest.fixture(scope="session")
def theory_dir(module_root):
    """Retorna el directorio de teoría"""
    return os.path.join(module_root, "theory")


@pytest.fixture
def terraform_module(tmp_path):
    """
    Fixture para crear un módulo temporal de Terraform para testing
    """
    module_dir = tmp_path / "terraform-test"
    module_dir.mkdir()
    return module_dir


def pytest_configure(config):
    """Configuración inicial de pytest"""
    config.addinivalue_line(
        "markers", "terraform: mark test as requiring terraform"
    )
    config.addinivalue_line(
        "markers", "aws: mark test as requiring AWS credentials"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
