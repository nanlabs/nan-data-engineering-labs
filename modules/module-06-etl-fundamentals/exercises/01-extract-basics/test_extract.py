"""
Unit tests for Extract Basics exercise.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from solution_csv import extract_users_csv
from solution_json import extract_transactions_json

@pytest.fixture
def data_dir():
    """Get data directory path."""
    return Path(__file__).parents[2] / 'data' / 'raw'

class TestCSVExtraction:
    """Test CSV extraction."""

    def test_extract_users_success(self, data_dir):
        """Test successful user extraction."""
        csv_file = data_dir / 'users_clean.csv'
        if not csv_file.exists():
            pytest.skip("Test data not generated")

        df = extract_users_csv(str(csv_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'id' in df.columns
        assert 'email' in df.columns

    def test_extract_users_file_not_found(self):
        """Test file not found error."""
        with pytest.raises(FileNotFoundError):
            extract_users_csv('nonexistent.csv')

    def test_extract_users_validates_required_columns(self, data_dir, tmp_path):
        """Test validation of required columns."""
        # Create CSV without required column
        invalid_csv = tmp_path / 'invalid.csv'
        pd.DataFrame({'wrong_col': [1, 2, 3]}).to_csv(invalid_csv, index=False)

        with pytest.raises(ValueError, match="Missing required columns"):
            extract_users_csv(str(invalid_csv))

class TestJSONExtraction:
    """Test JSON extraction."""

    def test_extract_transactions_success(self, data_dir):
        """Test successful transaction extraction."""
        json_file = data_dir / 'transactions.json'
        if not json_file.exists():
            pytest.skip("Test data not generated")

        df = extract_transactions_json(str(json_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'transaction_id' in df.columns
        assert 'amount' in df.columns

    def test_extract_transactions_file_not_found(self):
        """Test file not found error."""
        with pytest.raises(FileNotFoundError):
            extract_transactions_json('nonexistent.json')
