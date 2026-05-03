"""
Batch Reader - Starter

Implement a class that reads and processes large CSV files in chunks.
"""

import pandas as pd
from typing import Callable


class BatchReader:
    """Read and process large files in chunks."""

    def __init__(self, filepath: str, chunksize: int = 100000):
        """
        Initialize batch reader.

        Args:
            filepath: Path to CSV file
            chunksize: Number of records per chunk
        """
        # TODO: Initialize attributes
        pass

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
        # TODO: Implement chunked processing
        # 1. Read file in chunks
        # 2. Apply transform_fn to each chunk
        # 3. Collect results
        # 4. Return combined DataFrame
        pass

    def aggregate_chunks(
        self,
        agg_fn: Callable[[pd.DataFrame], dict]
    ) -> dict:
        """
        Process chunks and aggregate to dict (for memory efficiency).

        Args:
            agg_fn: Function that aggregates chunk to dict

        Returns:
            Combined aggregation results
        """
        # TODO: Implement aggregation
        # This is more memory efficient than storing full DataFrames
        pass


def example_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Example transformation function."""
    # Filter completed transactions
    df_filtered = df[df['status'] == 'completed']

    # Select relevant columns
    return df_filtered[['transaction_id', 'amount', 'category']]


def example_aggregation(df: pd.DataFrame) -> dict:
    """Example aggregation function."""
    return {
        'count': len(df),
        'total_amount': df['amount'].sum(),
        'avg_amount': df['amount'].mean()
    }


def main():
    """Test the BatchReader."""
    # TODO: Test your implementation
    # 1. Create BatchReader instance
    # 2. Process with transform
    # 3. Print results
    # 4. Test aggregation
    pass


if __name__ == "__main__":
    main()
