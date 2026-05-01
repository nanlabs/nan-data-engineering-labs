"""
Validation tests for complete ETL module.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add exercises to path
exercises_dir = Path(__file__).parent.parent / 'exercises'
sys.path.insert(0, str(exercises_dir / '01-extract-basics'))
sys.path.insert(0, str(exercises_dir / '02-transform-basics'))
sys.path.insert(0, str(exercises_dir / '03-load-basics'))

@pytest.mark.extract
class TestExtraction:
    """Test extraction functions."""

    def test_csv_extraction(self, mock_csv_file):
        """Test CSV extraction."""
        from solution_csv import extract_users_csv

        df = extract_users_csv(str(mock_csv_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'email' in df.columns
        assert df['email'].notnull().all()

    def test_json_extraction(self, mock_json_file):
        """Test JSON extraction."""
        from solution_json import extract_transactions_json

        df = extract_transactions_json(str(mock_json_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert 'transaction_id' in df.columns

    def test_extraction_file_not_found(self):
        """Test file not found handling."""
        from solution_csv import extract_users_csv

        with pytest.raises(FileNotFoundError):
            extract_users_csv('nonexistent.csv')

@pytest.mark.transform
class TestTransformation:
    """Test transformation functions."""

    def test_data_cleaning(self, sample_dirty_data):
        """Test data cleaning."""
        from solution_cleaning import clean_users

        # Add required columns
        sample_dirty_data['first_name'] = 'Test'
        sample_dirty_data['last_name'] = 'User'
        sample_dirty_data['country'] = 'USA'
        sample_dirty_data['created_at'] = '2024-01-01T00:00:00'

        cleaned = clean_users(sample_dirty_data)

        # Should remove invalid records
        assert len(cleaned) < len(sample_dirty_data)
        assert cleaned['email'].notnull().all()
        assert cleaned['age'].between(18, 120).all()

    def test_aggregations(self, sample_transactions_df):
        """Test transaction aggregations."""
        from solution_aggregations import aggregate_transactions

        results = aggregate_transactions(sample_transactions_df)

        assert 'total_transactions' in results
        assert 'total_amount' in results
        assert results['total_transactions'] == 10
        assert results['total_amount'] > 0

    def test_joins(self, sample_users_df, sample_transactions_df):
        """Test join operations."""
        from solution_joins import join_users_transactions

        enriched = join_users_transactions(sample_users_df, sample_transactions_df)

        assert len(enriched) == len(sample_transactions_df)
        assert 'email' in enriched.columns
        assert 'country' in enriched.columns

@pytest.mark.load
class TestLoading:
    """Test load functions."""

    def test_csv_writer(self, temp_dir, sample_users_df):
        """Test writing CSV."""
        from solution_file_writers import FileWriter

        writer = FileWriter(str(temp_dir))
        output_path = writer.write_csv(sample_users_df, 'test.csv')

        assert output_path.exists()

        # Verify content
        df_read = pd.read_csv(output_path)
        assert len(df_read) == len(sample_users_df)

    def test_json_writer(self, temp_dir, sample_users_df):
        """Test writing JSON."""
        from solution_file_writers import FileWriter

        writer = FileWriter(str(temp_dir))
        output_path = writer.write_jsonl(sample_users_df, 'test.jsonl')

        assert output_path.exists()

        # Verify content
        df_read = pd.read_json(output_path, lines=True)
        assert len(df_read) == len(sample_users_df)

    def test_parquet_writer(self, temp_dir, sample_users_df):
        """Test writing Parquet."""
        from solution_file_writers import FileWriter

        writer = FileWriter(str(temp_dir))
        output_path = writer.write_parquet(sample_users_df, 'test.parquet')

        assert output_path.exists()

        # Verify content
        df_read = pd.read_parquet(output_path)
        assert len(df_read) == len(sample_users_df)

@pytest.mark.quality
class TestDataQuality:
    """Test data quality checks."""

    def test_schema_validation(self, sample_users_df):
        """Test schema validation."""
        # Add path for validator
        validator_dir = Path(__file__).parent.parent / 'exercises' / '06-data-quality'
        sys.path.insert(0, str(validator_dir))

        from validator import DataValidator, UserSchema

        validator = DataValidator(UserSchema)
        valid, invalid = validator.validate_dataframe(sample_users_df)

        # All sample records should be valid
        assert len(valid) > 0

    def test_data_profiling(self, sample_users_df):
        """Test data profiling."""
        profiler_dir = Path(__file__).parent.parent / 'exercises' / '06-data-quality'
        sys.path.insert(0, str(profiler_dir))

        from profiler import DataProfiler

        profiler = DataProfiler(sample_users_df)
        profile = profiler.generate_profile()

        assert 'overview' in profile
        assert 'columns' in profile
        assert profile['overview']['row_count'] == len(sample_users_df)

@pytest.mark.integration
class TestFullPipeline:
    """Integration tests for full pipeline."""

    def test_end_to_end_pipeline(self, mock_csv_file, temp_dir):
        """Test complete ETL pipeline."""
        # This would test the full pipeline from exercise 04
        # For now, just verify files exist
        assert mock_csv_file.exists()
        assert temp_dir.exists()

def test_module_structure():
    """Test module structure is correct."""
    module_dir = Path(__file__).parent.parent

    # Check required directories
    assert (module_dir / 'theory').exists()
    assert (module_dir / 'exercises').exists()
    assert (module_dir / 'data').exists()
    assert (module_dir / 'validation').exists()

    # Check theory files
    theory_dir = module_dir / 'theory'
    assert (theory_dir / '01-concepts.md').exists()
    assert (theory_dir / '02-patterns.md').exists()
    assert (theory_dir / '03-resources.md').exists()

def test_requirements_file():
    """Test requirements.txt exists and has dependencies."""
    module_dir = Path(__file__).parent.parent
    req_file = module_dir / 'requirements.txt'

    assert req_file.exists()

    content = req_file.read_text()
    assert 'pandas' in content
    assert 'pytest' in content
