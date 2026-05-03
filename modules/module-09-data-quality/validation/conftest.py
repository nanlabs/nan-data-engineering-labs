"""
Pytest fixtures for Module 09: Data Quality tests.

Provides reusable test data, configurations, and utilities.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add module root to path
module_root = Path(__file__).parent.parent
sys.path.insert(0, str(module_root))


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def module_root_path():
    """Module root directory path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_path(module_root_path):
    """Data directory path."""
    return module_root_path / "data"


@pytest.fixture(scope="session")
def exercises_path(module_root_path):
    """Exercises directory path."""
    return module_root_path / "exercises"


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_customers():
    """Generate sample customer data."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame({
        'customer_id': range(1, n + 1),
        'email': [f'user{i}@example.com' for i in range(1, n + 1)],
        'phone': [f'555-{i:04d}' for i in range(1, n + 1)],
        'account_status': np.random.choice(['active', 'inactive', 'suspended'], n),
        'registration_date': pd.date_range('2020-01-01', periods=n, freq='D'),
        'date_of_birth': pd.date_range('1950-01-01', periods=n, freq='30D'),
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston'], n),
        'country': 'USA',
        'age': np.random.randint(18, 80, n)
    })


@pytest.fixture
def sample_transactions():
    """Generate sample transaction data."""
    np.random.seed(42)
    n = 200

    df = pd.DataFrame({
        'transaction_id': range(1, n + 1),
        'customer_id': np.random.randint(1, 101, n),
        'product_id': np.random.randint(1, 51, n),
        'amount': np.random.uniform(10, 1000, n),
        'quantity': np.random.randint(1, 10, n),
        'status': np.random.choice(['completed', 'pending', 'failed', 'refunded'], n),
        'payment_method': np.random.choice(['credit_card', 'debit_card', 'paypal'], n),
        'transaction_date': pd.date_range('2024-01-01', periods=n, freq='H')
    })

    # Add calculated field
    df['total'] = df['amount'] * df['quantity']

    return df


@pytest.fixture
def sample_products():
    """Generate sample product data."""
    np.random.seed(42)
    n = 50

    return pd.DataFrame({
        'product_id': range(1, n + 1),
        'product_name': [f'Product {i}' for i in range(1, n + 1)],
        'category': np.random.choice(['Electronics', 'Clothing', 'Home', 'Sports'], n),
        'price': np.random.uniform(10, 500, n),
        'cost': np.random.uniform(5, 250, n),
        'stock': np.random.randint(0, 100, n),
        'is_active': np.random.choice([True, False], n, p=[0.9, 0.1])
    })


@pytest.fixture
def dirty_data():
    """Generate data with quality issues."""
    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        'id': list(range(1, n + 1)) + [5, 10],  # Duplicates
        'email': [f'user{i}@example.com' if i % 10 != 0 else 'invalid-email'
                 for i in range(1, n + 3)],
        'amount': [np.random.uniform(0, 1000) if i % 15 != 0 else -10
                  for i in range(1, n + 3)],
        'status': [np.random.choice(['active', 'inactive']) if i % 20 != 0 else 'unknown'
                  for i in range(1, n + 3)],
        'quantity': [np.random.randint(1, 10) if i % 12 != 0 else None
                    for i in range(1, n + 3)]
    })

    return df


# ============================================================================
# Great Expectations Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def ge_data_context(tmp_path_factory):
    """Create temporary Great Expectations context."""
    import great_expectations as gx

    # Create temporary directory for GE
    temp_dir = tmp_path_factory.mktemp("ge_context")
    context_root_dir = str(temp_dir)

    # Initialize context
    context = gx.get_context(
        project_root_dir=context_root_dir,
        mode="file"
    )

    return context


@pytest.fixture
def ge_validator(ge_data_context, sample_transactions):
    """Create GE validator with sample data."""
    from great_expectations.core.batch import RuntimeBatchRequest

    # Add datasource
    datasource = ge_data_context.sources.add_pandas("test_datasource")

    # Create batch request
    batch_request = RuntimeBatchRequest(
        datasource_name="test_datasource",
        data_asset_name="test_transactions",
        runtime_parameters={"batch_data": sample_transactions},
        batch_identifiers={"default_identifier_name": "default"},
    )

    # Create expectation suite
    suite_name = "test_suite"
    ge_data_context.add_expectation_suite(suite_name)

    # Get validator
    validator = ge_data_context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name
    )

    return validator


# ============================================================================
# Quality Metrics Fixtures
# ============================================================================

@pytest.fixture
def quality_metrics_calculator():
    """DataQualityMetrics instance."""
    class DataQualityMetrics:
        @staticmethod
        def completeness(df: pd.DataFrame, column: str = None) -> float:
            if column:
                return (1 - df[column].isna().sum() / len(df)) * 100
            else:
                total_cells = df.shape[0] * df.shape[1]
                non_null_cells = total_cells - df.isna().sum().sum()
                return (non_null_cells / total_cells) * 100

        @staticmethod
        def uniqueness(df: pd.DataFrame, column: str) -> float:
            return (df[column].nunique() / len(df)) * 100

        @staticmethod
        def validity(df: pd.DataFrame, column: str, validation_func) -> float:
            valid = df[column].apply(validation_func).sum()
            return (valid / len(df)) * 100

    return DataQualityMetrics()


# ============================================================================
# Helper Functions
# ============================================================================

@pytest.fixture
def assert_quality_score():
    """Helper to assert quality scores meet thresholds."""
    def _assert_quality_score(score: float, threshold: float, dimension: str):
        assert score >= threshold, (
            f"{dimension} quality score {score:.2f}% is below threshold {threshold}%"
        )
    return _assert_quality_score


@pytest.fixture
def create_test_csv(tmp_path):
    """Helper to create test CSV files."""
    def _create_csv(df: pd.DataFrame, filename: str) -> Path:
        filepath = tmp_path / filename
        df.to_csv(filepath, index=False)
        return filepath
    return _create_csv


@pytest.fixture
def create_test_parquet(tmp_path):
    """Helper to create test Parquet files."""
    def _create_parquet(df: pd.DataFrame, filename: str) -> Path:
        filepath = tmp_path / filename
        df.to_parquet(filepath, index=False)
        return filepath
    return _create_parquet
