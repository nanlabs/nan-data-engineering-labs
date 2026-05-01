#!/usr/bin/env python3
"""
Exercise 03 - File Writers - SOLUTION
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileWriter:
    """Handle writing data to various file formats."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Write DataFrame to CSV."""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Wrote {len(df)} records to CSV: {output_path}")
        return output_path

    def write_json(self, df: pd.DataFrame, filename: str, orient='records') -> Path:
        """Write DataFrame to JSON."""
        output_path = self.output_dir / filename
        df.to_json(output_path, orient=orient, indent=2, date_format='iso')
        logger.info(f"Wrote {len(df)} records to JSON: {output_path}")
        return output_path

    def write_jsonl(self, df: pd.DataFrame, filename: str) -> Path:
        """Write DataFrame to JSON Lines."""
        output_path = self.output_dir / filename
        df.to_json(output_path, orient='records', lines=True, date_format='iso')
        logger.info(f"Wrote {len(df)} records to JSONL: {output_path}")
        return output_path

    def write_parquet(self, df: pd.DataFrame, filename: str) -> Path:
        """Write DataFrame to Parquet."""
        output_path = self.output_dir / filename
        df.to_parquet(output_path, index=False, compression='snappy')
        logger.info(f"Wrote {len(df)} records to Parquet: {output_path}")
        return output_path

def main():
    """Test file writers."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    users_file = data_dir / 'users_clean.csv'

    if not users_file.exists():
        print("⚠️  Data file not found. Run data generation first.")
        return

    # Load sample data
    df = pd.read_csv(users_file, nrows=100)
    print(f"Loaded {len(df)} sample records")

    # Write to various formats
    output_dir = Path(__file__).parents[2] / 'data' / 'output'
    writer = FileWriter(str(output_dir))

    print("\nWriting to different formats...")
    writer.write_csv(df, 'users_export.csv')
    writer.write_json(df, 'users_export.json')
    writer.write_jsonl(df, 'users_export.jsonl')
    writer.write_parquet(df, 'users_export.parquet')

    print(f"\n✓ All files written to {output_dir}")

    # Compare file sizes
    print("\n📊 File sizes:")
    for file in output_dir.glob('users_export.*'):
        size_kb = file.stat().st_size / 1024
        print(f"  {file.name:25s} {size_kb:8.2f} KB")

if __name__ == '__main__':
    main()
