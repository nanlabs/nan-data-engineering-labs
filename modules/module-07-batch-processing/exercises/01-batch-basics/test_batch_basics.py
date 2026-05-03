"""
Tests for Exercise 01: Batch Processing Basics
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add solution directory to path
sys.path.insert(0, str(Path(__file__).parent / 'solution'))

from batch_reader import BatchReader, example_transform, example_aggregation
from memory_optimizer import MemoryOptimizer


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    data = {
        'transaction_id': [f'TXN{i:010d}' for i in range(1, 10001)],
        'user_id': np.random.randint(1, 1000, 10000),
        'amount': np.random.rand(10000) * 1000,
        'category': np.random.choice(['electronics', 'books', 'clothing'], 10000),
        'status': np.random.choice(['completed', 'pending', 'failed'], 10000, p=[0.8, 0.15, 0.05])
    }
    df = pd.DataFrame(data)

    csv_path = tmp_path / "test_transactions.csv"
    df.to_csv(csv_path, index=False)

    return csv_path, df


class TestBatchReader:
    """Test BatchReader class."""

    def test_init(self, sample_csv):
        """Test BatchReader initialization."""
        csv_path, _ = sample_csv
        reader = BatchReader(csv_path, chunksize=1000)

        assert reader.filepath == Path(csv_path)
        assert reader.chunksize == 1000

    def test_init_file_not_found(self):
        """Test error handling when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            BatchReader("nonexistent_file.csv")

    def test_process_chunks(self, sample_csv):
        """Test chunk processing and combining."""
        csv_path, original_df = sample_csv
        reader = BatchReader(csv_path, chunksize=2000)

        # Apply transformation
        result = reader.process_chunks(example_transform)

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'transaction_id' in result.columns
        assert 'amount' in result.columns

        # All should be completed
        expected_count = len(original_df[original_df['status'] == 'completed'])
        assert len(result) == expected_count

    def test_aggregate_chunks(self, sample_csv):
        """Test chunked aggregation."""
        csv_path, original_df = sample_csv
        reader = BatchReader(csv_path, chunksize=2000)

        # Aggregate
        result = reader.aggregate_chunks(example_aggregation)

        # Verify
        assert isinstance(result, dict)
        assert 'count' in result
        assert 'total_amount' in result
        assert 'avg_amount' in result
        assert '_chunks_processed' in result

        # Check values match original
        assert result['count'] == len(original_df)
        assert abs(result['total_amount'] - original_df['amount'].sum()) < 0.01
        assert result['_chunks_processed'] == 5  # 10000 / 2000


class TestMemoryOptimizer:
    """Test MemoryOptimizer class."""

    def test_memory_usage_mb(self):
        """Test memory usage calculation."""
        df = pd.DataFrame({
            'a': range(1000),
            'b': ['test'] * 1000
        })

        memory = MemoryOptimizer.memory_usage_mb(df)
        assert isinstance(memory, float)
        assert memory > 0

    def test_optimize_ints_unsigned(self):
        """Test integer optimization for unsigned values."""
        df = pd.DataFrame({'col': range(200)})

        optimal_dtype = MemoryOptimizer.optimize_ints(df, 'col')
        assert optimal_dtype == 'uint8'

    def test_optimize_ints_signed(self):
        """Test integer optimization for signed values."""
        df = pd.DataFrame({'col': range(-100, 100)})

        optimal_dtype = MemoryOptimizer.optimize_ints(df, 'col')
        assert optimal_dtype == 'int8'

    def test_optimize_ints_large(self):
        """Test integer optimization for large values."""
        df = pd.DataFrame({'col': [1000000]})

        optimal_dtype = MemoryOptimizer.optimize_ints(df, 'col')
        assert optimal_dtype in ['uint32', 'int32']

    def test_optimize_floats(self):
        """Test float optimization."""
        df = pd.DataFrame({'col': [1.5, 2.5, 3.5]})

        optimal_dtype = MemoryOptimizer.optimize_floats(df, 'col')
        assert optimal_dtype == 'float32'

    def test_optimize_objects_to_category(self):
        """Test object to category conversion when beneficial."""
        df = pd.DataFrame({'col': ['A', 'B', 'C'] * 100})

        optimal_dtype = MemoryOptimizer.optimize_objects(df, 'col')
        assert optimal_dtype == 'category'

    def test_optimize_objects_keep_object(self):
        """Test keeping object dtype when not beneficial."""
        df = pd.DataFrame({'col': [f'unique_{i}' for i in range(100)]})

        optimal_dtype = MemoryOptimizer.optimize_objects(df, 'col')
        assert optimal_dtype == 'object'

    def test_optimize_dtypes_full(self):
        """Test full DataFrame optimization."""
        df = pd.DataFrame({
            'id': range(1000),
            'category': ['A', 'B', 'C'] * 334,
            'amount': np.random.rand(1000) * 100,
            'status': ['active'] * 900 + ['inactive'] * 100
        })

        initial_memory = MemoryOptimizer.memory_usage_mb(df)
        df_optimized = MemoryOptimizer.optimize_dtypes(df, verbose=False)
        final_memory = MemoryOptimizer.memory_usage_mb(df_optimized)

        # Should reduce memory
        assert final_memory < initial_memory

        # Should preserve data
        assert len(df) == len(df_optimized)
        assert df['id'].sum() == df_optimized['id'].sum()

    def test_optimize_dtypes_preserves_data(self):
        """Test that optimization preserves data integrity."""
        df = pd.DataFrame({
            'int_col': range(100),
            'float_col': np.random.rand(100),
            'cat_col': ['A', 'B', 'C'] * 34,
            'obj_col': [f'item_{i}' for i in range(100)]
        })

        df_optimized = MemoryOptimizer.optimize_dtypes(df, verbose=False)

        # Verify data integrity
        assert df['int_col'].sum() == df_optimized['int_col'].sum()
        assert abs(df['float_col'].sum() - df_optimized['float_col'].sum()) < 0.01
        pd.testing.assert_series_equal(
            df['cat_col'].value_counts().sort_index(),
            df_optimized['cat_col'].value_counts().sort_index()
        )


@pytest.mark.integration
class TestIntegration:
    """Integration tests combining batch processing and memory optimization."""

    def test_batch_processing_with_optimization(self, sample_csv):
        """Test processing batches with memory optimization."""
        csv_path, _ = sample_csv
        reader = BatchReader(csv_path, chunksize=2000)

        def transform_and_optimize(chunk):
            transformed = example_transform(chunk)
            return MemoryOptimizer.optimize_dtypes(transformed, verbose=False)

        result = reader.process_chunks(transform_and_optimize)

        # Verify optimized dtypes were applied
        assert result['amount'].dtype == np.float32
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
