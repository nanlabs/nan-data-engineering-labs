"""
Pytest fixtures for ETL module tests.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

@pytest.fixture(scope='session')
def data_dir():
    """Get data directory path."""
    return Path(__file__).parent.parent / 'data'

@pytest.fixture(scope='session')
def raw_data_dir(data_dir):
    """Get raw data directory."""
    return data_dir / 'raw'

@pytest.fixture(scope='session')
def processed_data_dir(data_dir):
    """Get processed data directory."""
    return data_dir / 'processed'

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)

@pytest.fixture
def sample_users_df():
    """Create sample users DataFrame."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'email': ['user1@test.com', 'user2@test.com', 'user3@test.com',
                  'user4@test.com', 'user5@test.com'],
        'first_name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
        'last_name': ['Doe', 'Smith', 'Johnson', 'Brown', 'Wilson'],
        'age': [25, 30, 35, 28, 42],
        'country': ['USA', 'UK', 'USA', 'Canada', 'USA'],
        'status': ['active', 'active', 'inactive', 'pending', 'active'],
        'created_at': pd.date_range('2024-01-01', periods=5),
        'last_login': pd.date_range('2024-03-01', periods=5)
    })

@pytest.fixture
def sample_transactions_df():
    """Create sample transactions DataFrame."""
    return pd.DataFrame({
        'transaction_id': [f'TXN-{i:08d}' for i in range(1, 11)],
        'user_id': [1, 2, 1, 3, 2, 1, 4, 3, 5, 2],
        'product_id': [101, 102, 103, 101, 104, 102, 105, 103, 101, 104],
        'amount': [25.99, 49.99, 15.50, 99.99, 29.99, 35.00, 199.99, 12.50, 45.00, 89.99],
        'quantity': [1, 2, 1, 1, 3, 1, 1, 2, 1, 1],
        'payment_method': ['credit_card'] * 10,
        'status': ['completed'] * 10,
        'timestamp': pd.date_range('2024-03-01', periods=10, freq='H')
    })

@pytest.fixture
def sample_dirty_data():
    """Create sample data with quality issues."""
    return pd.DataFrame({
        'id': [1, 2, 3, 3, None],  # Duplicate and null
        'email': ['user1@test.com', 'invalid', None, 'user3@test.com', 'user4@test.com'],
        'age': [25, 200, -5, 30, 28],  # Invalid ages
        'status': ['active', 'active', 'invalid', 'active', None]
    })

@pytest.fixture(scope='function')
def mock_csv_file(temp_dir, sample_users_df):
    """Create temporary CSV file."""
    csv_path = temp_dir / 'test_users.csv'
    sample_users_df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture(scope='function')
def mock_json_file(temp_dir, sample_transactions_df):
    """Create temporary JSON file."""
    json_path = temp_dir / 'test_transactions.json'
    sample_transactions_df.to_json(json_path, orient='records', lines=True)
    return json_path

@pytest.fixture
def skip_if_no_data(raw_data_dir):
    """Skip test if test data is not generated."""
    if not (raw_data_dir / 'users_clean.csv').exists():
        pytest.skip("Test data not generated. Run data generation scripts first.")
