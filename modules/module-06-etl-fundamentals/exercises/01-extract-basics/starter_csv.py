#!/usr/bin/env python3
"""
Exercise 01 - Task 1: Extract from CSV

TODO:
1. Read users from CSV file
2. Handle encoding issues
3. Validate data
4. Return DataFrame
"""
import pandas as pd
from pathlib import Path

def extract_users_csv(file_path: str) -> pd.DataFrame:
    """
    Extract user data from CSV file.

    Args:
        file_path: Path to CSV file

    Returns:
        DataFrame with user data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If data is invalid
    """
    # TODO: Implement CSV extraction
    # Hints:
    # - Use pd.read_csv()
    # - Handle encoding parameter
    # - Check for nulls in required columns
    # - Validate email format

    raise NotImplementedError("TODO: Implement extract_users_csv")

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
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
