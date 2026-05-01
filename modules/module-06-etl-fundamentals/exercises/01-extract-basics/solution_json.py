#!/usr/bin/env python3
"""
Exercise 01 - Task 2: Extract from JSON - SOLUTION
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_transactions_json(file_path: str) -> pd.DataFrame:
    """Extract transaction data from JSON Lines file."""
    logger.info(f"Extracting from {file_path}")

    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read JSON Lines format
    df = pd.read_json(
        file_path,
        lines=True,
        convert_dates=['timestamp']
    )

    # Validate
    if df.empty:
        raise ValueError("Empty dataframe")

    required_cols = ['transaction_id', 'user_id', 'amount', 'timestamp']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.info(f"Successfully extracted {len(df)} records")
    return df

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
        print("\nData types:")
        print(df.dtypes)
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    main()
