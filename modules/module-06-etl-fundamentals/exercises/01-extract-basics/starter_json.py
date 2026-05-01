#!/usr/bin/env python3
"""
Exercise 01 - Task 2: Extract from JSON
"""
import pandas as pd
from pathlib import Path

def extract_transactions_json(file_path: str) -> pd.DataFrame:
    """
    Extract transaction data from JSON Lines file.

    Args:
        file_path: Path to JSON file

    Returns:
        DataFrame with transaction data
    """
    # TODO: Implement JSON extraction
    # Hints:
    # - Use pd.read_json() with lines=True for JSON Lines format
    # - Parse timestamp column
    # - Handle nested JSON structures

    raise NotImplementedError("TODO: Implement extract_transactions_json")

def main():
    """Test the extractor."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    json_file = data_dir / 'transactions.json'

    print("Extracting transactions from JSON...")
    try:
        df = extract_transactions_json(str(json_file))
        print(f"✓ Extracted {len(df)} transactions")
        print("\nFirst 5 transactions:")
        print(df.head())
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
