"""
Pytest configuration and fixtures for Module 07: Batch Processing
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from pyspark.sql import SparkSession
from datetime import datetime, timedelta


@pytest.fixture(scope="session")
def spark_session():
    """Create Spark session for tests."""
    spark = SparkSession.builder \
        .appName("BatchProcessingTests") \
        .master("local[2]") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.default.parallelism", "4") \
        .getOrCreate()

    yield spark

    spark.stop()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_transactions_df():
    """Create sample transactions DataFrame."""
    np.random.seed(42)

    n = 10000
    start_date = datetime(2024, 1, 1)

    data = {
        'transaction_id': [f'TXN{i:010d}' for i in range(1, n + 1)],
        'user_id': [f'USER{i:06d}' for i in np.random.randint(1, 1000, n)],
        'product_id': [f'PROD{i:05d}' for i in np.random.randint(1, 100, n)],
        'amount': np.random.rand(n) * 1000,
        'quantity': np.random.randint(1, 10, n),
        'timestamp': [
            start_date + timedelta(
                days=np.random.randint(0, 90),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            for _ in range(n)
        ],
        'status': np.random.choice(
            ['completed', 'pending', 'failed', 'refunded'],
            n,
            p=[0.85, 0.10, 0.04, 0.01]
        ),
        'payment_method': np.random.choice(
            ['credit_card', 'debit_card', 'paypal'],
            n,
            p=[0.5, 0.3, 0.2]
        ),
        'country': np.random.choice(['US', 'UK', 'CA', 'DE', 'FR'], n),
        'category': np.random.choice(
            ['electronics', 'clothing', 'books', 'home'],
            n
        )
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_users_df():
    """Create sample users DataFrame."""
    np.random.seed(43)

    n = 1000

    data = {
        'user_id': [f'USER{i:06d}' for i in range(1, n + 1)],
        'email': [f'user{i}@example.com' for i in range(1, n + 1)],
        'name': [f'User {i}' for i in range(1, n + 1)],
        'age': np.random.randint(18, 80, n),
        'country': np.random.choice(['US', 'UK', 'CA', 'DE', 'FR'], n),
        'created_at': [
            datetime(2024, 1, 1) - timedelta(days=np.random.randint(0, 1095))
            for _ in range(n)
        ],
        'tier': np.random.choice(
            ['bronze', 'silver', 'gold', 'platinum'],
            n,
            p=[0.6, 0.25, 0.12, 0.03]
        ),
        'total_spent': np.random.rand(n) * 5000,
        'is_active': np.random.choice([True, False], n, p=[0.95, 0.05])
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_products_df():
    """Create sample products DataFrame."""
    np.random.seed(44)

    n = 100

    data = {
        'product_id': [f'PROD{i:05d}' for i in range(1, n + 1)],
        'name': [f'Product {i}' for i in range(1, n + 1)],
        'category': np.random.choice(
            ['electronics', 'clothing', 'books', 'home'],
            n
        ),
        'price': np.random.rand(n) * 500 + 10,
        'stock': np.random.randint(0, 1000, n),
        'brand': np.random.choice(['Brand A', 'Brand B', 'Brand C'], n),
        'rating': np.random.rand(n) * 2 + 3,  # 3-5 stars
        'reviews_count': np.random.randint(0, 1000, n),
        'is_available': np.random.choice([True, False], n, p=[0.95, 0.05])
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_csv_file(sample_transactions_df, temp_dir):
    """Create sample CSV file for testing."""
    csv_path = temp_dir / "transactions.csv"
    sample_transactions_df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_parquet_file(sample_transactions_df, temp_dir):
    """Create sample Parquet file for testing."""
    parquet_path = temp_dir / "transactions.parquet"
    sample_transactions_df.to_parquet(parquet_path, index=False)
    return parquet_path


@pytest.fixture
def partitioned_data(sample_transactions_df, temp_dir):
    """Create date-partitioned dataset."""
    df = sample_transactions_df.copy()
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.month
    df['day'] = df['timestamp'].dt.day

    # Write partitioned
    output_dir = temp_dir / "partitioned"

    for (year, month, day), group in df.groupby(['year', 'month', 'day']):
        partition_dir = output_dir / f"year={year}" / f"month={month:02d}" / f"day={day:02d}"
        partition_dir.mkdir(parents=True, exist_ok=True)

        group.to_parquet(
            partition_dir / "data.parquet",
            index=False
        )

    return output_dir


@pytest.fixture
def spark_df_transactions(spark_session, sample_transactions_df):
    """Create Spark DataFrame from pandas transactions."""
    return spark_session.createDataFrame(sample_transactions_df)


@pytest.fixture
def spark_df_users(spark_session, sample_users_df):
    """Create Spark DataFrame from pandas users."""
    return spark_session.createDataFrame(sample_users_df)


@pytest.fixture
def spark_df_products(spark_session, sample_products_df):
    """Create Spark DataFrame from pandas products."""
    return spark_session.createDataFrame(sample_products_df)


# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with -m 'not slow')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "spark: marks tests that require Spark"
    )
    config.addinivalue_line(
        "markers", "performance: marks performance benchmark tests"
    )
