"""
Batch Reader - Solution

Complete implementation of batch file processing.
"""

import pandas as pd
from pathlib import Path
from typing import Callable, Dict, Any


class BatchReader:
    """Read and process large files in chunks."""

    def __init__(self, filepath: str, chunksize: int = 100000):
        """
        Initialize batch reader.

        Args:
            filepath: Path to CSV file
            chunksize: Number of records per chunk
        """
        self.filepath = Path(filepath)
        self.chunksize = chunksize

        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

    def process_chunks(
        self,
        transform_fn: Callable[[pd.DataFrame], pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Process file in chunks and aggregate results.

        Args:
            transform_fn: Function to apply to each chunk

        Returns:
            Combined DataFrame with all processed chunks
        """
        results = []

        # Read and process chunks
        for chunk in pd.read_csv(self.filepath, chunksize=self.chunksize):
            # Apply transformation
            transformed = transform_fn(chunk)
            results.append(transformed)

        # Combine all chunks
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()

    def aggregate_chunks(
        self,
        agg_fn: Callable[[pd.DataFrame], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process chunks and aggregate to dict (memory efficient).

        Args:
            agg_fn: Function that aggregates chunk to dict

        Returns:
            Combined aggregation results
        """
        # Initialize combined results
        combined = {}
        chunk_count = 0

        # Process each chunk
        for chunk in pd.read_csv(self.filepath, chunksize=self.chunksize):
            chunk_result = agg_fn(chunk)

            # Combine results
            if chunk_count == 0:
                combined = chunk_result.copy()
            else:
                # Merge results (sum numeric values)
                for key, value in chunk_result.items():
                    if isinstance(value, (int, float)):
                        combined[key] = combined.get(key, 0) + value
                    elif isinstance(value, dict):
                        # Merge nested dicts
                        if key not in combined:
                            combined[key] = {}
                        for sub_key, sub_value in value.items():
                            combined[key][sub_key] = combined[key].get(sub_key, 0) + sub_value

            chunk_count += 1

        # Add metadata
        combined['_chunks_processed'] = chunk_count

        return combined


def example_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Example transformation: filter and select columns."""
    df_filtered = df[df['status'] == 'completed']
    return df_filtered[['transaction_id', 'amount', 'category']]


def example_aggregation(df: pd.DataFrame) -> Dict[str, Any]:
    """Example aggregation: compute summary statistics."""
    return {
        'count': len(df),
        'total_amount': float(df['amount'].sum()),
        'avg_amount': float(df['amount'].mean()) if len(df) > 0 else 0,
        'category_counts': df['category'].value_counts().to_dict()
    }


def main():
    """Demonstrate BatchReader usage."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python batch_reader.py <csv_file>")
        print("\nExample:")
        print("  python batch_reader.py ../../data/raw/transactions.csv")
        return

    filepath = sys.argv[1]

    print(f"Processing file: {filepath}")
    print("=" * 60)

    # Create batch reader
    reader = BatchReader(filepath, chunksize=100000)

    # Test 1: Transform and combine
    print("\n1. Transform and combine chunks:")
    result_df = reader.process_chunks(example_transform)
    print(f"   Total records after filtering: {len(result_df):,}")
    print("   First 3 records:")
    print(result_df.head(3))

    # Test 2: Aggregate
    print("\n2. Aggregate across chunks:")
    result_agg = reader.aggregate_chunks(example_aggregation)
    print(f"   Total count: {result_agg['count']:,}")
    print(f"   Total amount: ${result_agg['total_amount']:,.2f}")
    print(f"   Average amount: ${result_agg['avg_amount']:.2f}")
    print(f"   Chunks processed: {result_agg['_chunks_processed']}")
    print("\n   Category counts:")
    for cat, count in sorted(result_agg['category_counts'].items()):
        print(f"     {cat}: {count:,}")


if __name__ == "__main__":
    main()
