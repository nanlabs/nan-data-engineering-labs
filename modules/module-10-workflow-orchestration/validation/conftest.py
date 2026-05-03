"""Pytest configuration and fixtures for Airflow DAG testing"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_airflow_context():
    """Mock Airflow context for testing tasks"""
    return {
        'execution_date': datetime(2024, 1, 1),
        'dag': MagicMock(dag_id='test_dag'),
        'task': MagicMock(task_id='test_task'),
        'ti': MagicMock(),
        'dag_run': MagicMock(run_id='test_run'),
        'ds': '2024-01-01',
        'ds_nodash': '20240101',
        'ts': '2024-01-01T00:00:00+00:00',
        'run_id': 'test_run_123',
    }

@pytest.fixture
def mock_postgres_hook(monkeypatch):
    """Mock PostgresHook for testing database operations"""
    mock_hook = MagicMock()
    mock_hook.get_connection.return_value = MagicMock(
        host='localhost',
        schema='test',
        login='test_user',
        password='test_pass'
    )
    return mock_hook

@pytest.fixture
def mock_s3_hook(monkeypatch):
    """Mock S3Hook for testing S3 operations"""
    mock_hook = MagicMock()
    mock_hook.check_for_key.return_value = True
    mock_hook.read_key.return_value = '{"test": "data"}'
    return mock_hook

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create temporary CSV file for testing"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n")
    return str(csv_file)

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv('AIRFLOW_HOME', '/tmp/airflow')
    monkeypatch.setenv('AIRFLOW__CORE__DAGS_FOLDER', '../exercises')
    monkeypatch.setenv('AIRFLOW__CORE__LOAD_EXAMPLES', 'False')
