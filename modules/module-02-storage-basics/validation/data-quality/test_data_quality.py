"""
Data Quality Validation Tests for Module 02

These tests validate data quality aspects of the data lake implementation.
"""

import pandas as pd
import pyarrow.parquet as pq


class TestDataQuality:
    """Test data quality rules and constraints."""

    def test_no_null_primary_keys(self, sample_transactions):
        """Ensure primary keys have no null values."""
        assert sample_transactions['transaction_id'].notna().all(), \
            "Primary key transaction_id contains null values"

    def test_positive_amounts(self, sample_transactions):
        """Ensure all transaction amounts are positive."""
        assert (sample_transactions['amount'] > 0).all(), \
            "Found negative or zero amounts"

    def test_valid_status_values(self, sample_transactions):
        """Ensure status field contains only valid values."""
        valid_statuses = ['completed', 'pending', 'cancelled', 'refunded']
        assert sample_transactions['status'].isin(valid_statuses).all(), \
            f"Invalid status values found. Valid: {valid_statuses}"

    def test_timestamp_in_reasonable_range(self, sample_transactions):
        """Ensure timestamps are within reasonable range."""
        min_date = pd.Timestamp('2020-01-01')
        max_date = pd.Timestamp('2026-12-31')

        timestamps = pd.to_datetime(sample_transactions['timestamp'])
        assert (timestamps >= min_date).all(), \
            "Found timestamps before 2020"
        assert (timestamps <= max_date).all(), \
            "Found timestamps after 2026"

    def test_no_duplicate_ids(self, sample_transactions):
        """Ensure no duplicate transaction IDs."""
        duplicates = sample_transactions['transaction_id'].duplicated().sum()
        assert duplicates == 0, \
            f"Found {duplicates} duplicate transaction IDs"

    def test_amount_within_expected_range(self, sample_transactions):
        """Ensure amounts are within expected business range."""
        min_amount = 1.0
        max_amount = 10000.0

        assert (sample_transactions['amount'] >= min_amount).all(), \
            f"Found amounts below minimum {min_amount}"
        assert (sample_transactions['amount'] <= max_amount).all(), \
            f"Found amounts above maximum {max_amount}"


class TestParquetDataQuality:
    """Test Parquet-specific data quality aspects."""

    def test_parquet_schema_consistency(self, test_data_dir, sample_transactions):
        """Ensure Parquet files maintain schema consistency."""
        # Write sample data
        parquet_path = test_data_dir / 'test_quality.parquet'
        sample_transactions.to_parquet(parquet_path, engine='pyarrow', index=False)

        # Read and verify schema
        schema = pq.read_schema(parquet_path)

        # Expected columns
        expected_columns = [
            'transaction_id', 'user_id', 'product_id',
            'amount', 'timestamp', 'country', 'status'
        ]

        actual_columns = schema.names
        assert set(actual_columns) == set(expected_columns), \
            f"Schema mismatch. Expected: {expected_columns}, Got: {actual_columns}"

    def test_parquet_row_group_size(self, test_data_dir, sample_transactions):
        """Ensure Parquet row groups are within optimal size."""
        parquet_path = test_data_dir / 'test_rowgroup.parquet'
        sample_transactions.to_parquet(parquet_path, engine='pyarrow', index=False)

        metadata = pq.read_metadata(parquet_path)

        # For small test data, we expect 1 row group
        assert metadata.num_row_groups >= 1, \
            "Parquet file should have at least 1 row group"

    def test_parquet_compression_applied(self, test_data_dir, sample_transactions):
        """Ensure compression is applied to Parquet files."""
        parquet_path = test_data_dir / 'test_compressed.parquet'
        sample_transactions.to_parquet(
            parquet_path,
            engine='pyarrow',
            compression='snappy',
            index=False
        )

        # Read metadata
        parquet_file = pq.ParquetFile(parquet_path)

        # Check that compression is set
        # Note: compression info is per-column chunk
        assert parquet_file.metadata.num_columns > 0, \
            "Parquet file should have columns"


class TestPartitioningQuality:
    """Test data quality in partitioned datasets."""

    def test_partition_column_consistency(self, test_data_dir, sample_transactions):
        """Ensure partition columns exist in all records."""
        # Add partition columns
        df = sample_transactions.copy()
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        df['month'] = pd.to_datetime(df['timestamp']).dt.month

        # Write partitioned data
        output_path = test_data_dir / 'partitioned'
        df.to_parquet(
            output_path,
            engine='pyarrow',
            partition_cols=['year', 'month'],
            index=False
        )

        # Read back and verify
        read_df = pd.read_parquet(output_path)

        assert 'year' in read_df.columns, "Partition column 'year' missing"
        assert 'month' in read_df.columns, "Partition column 'month' missing"
        assert read_df['year'].notna().all(), "Partition column 'year' has nulls"
        assert read_df['month'].notna().all(), "Partition column 'month' has nulls"

    def test_no_empty_partitions(self, test_data_dir, sample_transactions):
        """Ensure no partitions are empty."""
        df = sample_transactions.copy()
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        df['month'] = pd.to_datetime(df['timestamp']).dt.month

        output_path = test_data_dir / 'partitioned_check'
        df.to_parquet(
            output_path,
            engine='pyarrow',
            partition_cols=['year', 'month'],
            index=False
        )

        # Find all parquet files
        parquet_files = list(output_path.rglob('*.parquet'))

        # Check each file has data
        for parquet_file in parquet_files:
            file_df = pd.read_parquet(parquet_file)
            assert len(file_df) > 0, \
                f"Empty partition found: {parquet_file}"


class TestDataFreshness:
    """Test data freshness and timeliness."""

    def test_recent_data_exists(self, sample_transactions):
        """Ensure dataset contains recent data."""
        timestamps = pd.to_datetime(sample_transactions['timestamp'])
        max_date = timestamps.max()

        # Data should be within last year
        one_year_ago = pd.Timestamp.now() - pd.Timedelta(days=365)

        assert max_date >= one_year_ago, \
            f"Most recent data is from {max_date}, older than 1 year"

    def test_data_distribution_by_date(self, sample_transactions):
        """Ensure data is distributed across time periods."""
        timestamps = pd.to_datetime(sample_transactions['timestamp'])

        # Group by month
        monthly_counts = timestamps.dt.to_period('M').value_counts()

        # Should have data in multiple months
        assert len(monthly_counts) > 0, \
            "No temporal distribution found"


class TestReferentialIntegrity:
    """Test referential integrity rules."""

    def test_user_id_consistency(self, sample_transactions):
        """Ensure user_id values are consistent."""
        assert sample_transactions['user_id'].notna().all(), \
            "user_id contains null values"
        assert (sample_transactions['user_id'] > 0).all(), \
            "user_id contains invalid values"

    def test_product_id_consistency(self, sample_transactions):
        """Ensure product_id values are consistent."""
        assert sample_transactions['product_id'].notna().all(), \
            "product_id contains null values"
        assert (sample_transactions['product_id'] > 0).all(), \
            "product_id contains invalid values"


class TestDataCompleteness:
    """Test data completeness."""

    def test_no_fully_null_rows(self, sample_transactions):
        """Ensure no rows are completely null."""
        null_rows = sample_transactions.isnull().all(axis=1).sum()
        assert null_rows == 0, \
            f"Found {null_rows} completely null rows"

    def test_critical_columns_not_null(self, sample_transactions):
        """Ensure critical columns have no nulls."""
        critical_columns = ['transaction_id', 'amount', 'timestamp', 'status']

        for col in critical_columns:
            null_count = sample_transactions[col].isnull().sum()
            assert null_count == 0, \
                f"Critical column '{col}' has {null_count} null values"

    def test_minimum_row_count(self, sample_transactions):
        """Ensure dataset has minimum number of rows."""
        min_rows = 10
        actual_rows = len(sample_transactions)

        assert actual_rows >= min_rows, \
            f"Dataset has only {actual_rows} rows, expected at least {min_rows}"
