#!/usr/bin/env python3
"""
Exercise 01 - Task 1: Extract from CSV - SOLUTION
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_users_csv(file_path: str) -> pd.DataFrame:
    """Extract user data from CSV file."""
    logger.info(f"Extracting from {file_path}")

    # Check file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read CSV with error handling
    try:
        df = pd.read_csv(
            file_path,
            encoding='utf-8',
            parse_dates=['created_at', 'last_login']
        )
    except UnicodeDecodeError:
        # Retry with different encoding
        df = pd.read_csv(
            file_path,
            encoding='latin-1',
            parse_dates=['created_at', 'last_login']
        )

    # Validate required columns
    required_cols = ['id', 'email', 'created_at']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Validate data
    if df.empty:
        raise ValueError("Empty dataframe")

    if df['id'].isnull().any():
        raise ValueError("Null values in id column")

    logger.info(f"Successfully extracted {len(df)} records")
    return df

def main():
    """Test the extractor."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    csv_file = data_dir / 'users_clean.csv'

    print("Extracting users from CSV...")
    try:
        df = extract_users_csv(str(csv_file))
        print(f"✓ Extracted {len(df)} users")
        print("\nFirst 5 users:")
        print(df.head())
        print("\nData types:")
        print(df.dtypes)
        print("\nNull counts:")
        print(df.isnull().sum())
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    main()
