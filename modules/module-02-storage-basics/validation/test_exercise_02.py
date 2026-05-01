"""
Validation tests for Exercise 02: File Format Conversion
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path for importing solution
sys.path.insert(0, str(Path(__file__).parent.parent / 'exercises' / '02-file-formats' / 'solution'))

try:
    from convert_formats import FormatConverter
except ImportError:
    FormatConverter = None


@pytest.mark.skipif(FormatConverter is None, reason="Solution not available")
class TestExercise02:
    """Test Exercise 02: File Format Conversion."""

    def test_csv_reading(self, sample_transactions, test_data_dir):
        """Test CSV reading functionality."""
        csv_path = test_data_dir / 'test.csv'
        sample_transactions.to_csv(csv_path, index=False)

        converter = FormatConverter(str(csv_path))
        df = converter.read_csv()

        assert len(df) == 100
        assert 'transaction_id' in df.columns
        assert 'amount' in df.columns

    def test_parquet_writing(self, sample_transactions, test_data_dir):
        """Test Parquet writing functionality."""
        csv_path = test_data_dir / 'test.csv'
        sample_transactions.to_csv(csv_path, index=False)

        converter = FormatConverter(str(csv_path))
        df = converter.read_csv()

        parquet_path = test_data_dir / 'test.parquet'
        result = converter.write_parquet(df, str(parquet_path), compression='snappy')

        assert parquet_path.exists()
        assert result['file_size_mb'] > 0
        assert result['write_time_seconds'] >= 0
        assert 'compression_ratio' in result

    def test_json_writing(self, sample_transactions, test_data_dir):
        """Test JSON writing functionality."""
        csv_path = test_data_dir / 'test.csv'
        sample_transactions.to_csv(csv_path, index=False)

        converter = FormatConverter(str(csv_path))
        df = converter.read_csv()

        json_path = test_data_dir / 'test.json'
        result = converter.write_json(df, str(json_path))

        assert json_path.exists()
        assert result['file_size_mb'] > 0
        assert result['write_time_seconds'] >= 0

    def test_avro_writing(self, sample_transactions, test_data_dir):
        """Test Avro writing functionality."""
        csv_path = test_data_dir / 'test.csv'
        sample_transactions.to_csv(csv_path, index=False)

        converter = FormatConverter(str(csv_path))
        df = converter.read_csv()

        avro_path = test_data_dir / 'test.avro'
        result = converter.write_avro(df, str(avro_path))

        assert avro_path.exists()
        assert result['file_size_mb'] > 0
        assert result['write_time_seconds'] >= 0

    def test_compression_effectiveness(self, sample_transactions, test_data_dir):
        """Test that Parquet compression is effective."""
        csv_path = test_data_dir / 'test.csv'
        sample_transactions.to_csv(csv_path, index=False)

        converter = FormatConverter(str(csv_path))
        df = converter.read_csv()

        # Write both Snappy and Gzip
        snappy_path = test_data_dir / 'test_snappy.parquet'
        gzip_path = test_data_dir / 'test_gzip.parquet'

        snappy_result = converter.write_parquet(df, str(snappy_path), 'snappy')
        gzip_result = converter.write_parquet(df, str(gzip_path), 'gzip')

        # Gzip should compress more than Snappy
        assert gzip_result['compression_ratio'] > snappy_result['compression_ratio']

    def test_read_benchmarking(self, sample_transactions, test_data_dir):
        """Test read benchmarking functionality."""
        csv_path = test_data_dir / 'test.csv'
        sample_transactions.to_csv(csv_path, index=False)

        converter = FormatConverter(str(csv_path))

        result = converter.benchmark_read(str(csv_path), 'csv')

        assert 'read_time_seconds' in result
        assert 'memory_usage_mb' in result
        assert result['rows_read'] == 100
