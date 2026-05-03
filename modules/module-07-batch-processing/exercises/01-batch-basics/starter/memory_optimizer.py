"""
Memory Optimizer - Starter

Implement dtype optimization to reduce DataFrame memory usage.
"""

import pandas as pd
import numpy as np


class MemoryOptimizer:
    """Optimize DataFrame memory usage by converting dtypes."""

    @staticmethod
    def memory_usage_mb(df: pd.DataFrame) -> float:
        """
        Calculate DataFrame memory usage in MB.

        Args:
            df: DataFrame to measure

        Returns:
            Memory usage in megabytes
        """
        # TODO: Calculate memory usage
        # Hint: Use df.memory_usage(deep=True).sum()
        pass

    @staticmethod
    def optimize_ints(df: pd.DataFrame, column: str) -> str:
        """
        Find optimal integer dtype for column.

        Args:
            df: DataFrame
            column: Column name

        Returns:
            Optimal dtype as string (e.g., 'int8', 'uint16')
        """
        # TODO: Implement int optimization
        # 1. Get min and max values
        # 2. Determine if signed or unsigned
        # 3. Find smallest dtype that fits range
        # 4. Return dtype name
        pass

    @staticmethod
    def optimize_floats(df: pd.DataFrame, column: str) -> str:
        """
        Optimize float columns (float64 -> float32 when possible).

        Args:
            df: DataFrame
            column: Column name

        Returns:
            Optimal dtype
        """
        # TODO: Implement float optimization
        # Most cases: float32 is sufficient
        pass

    @staticmethod
    def optimize_objects(df: pd.DataFrame, column: str) -> str:
        """
        Optimize object columns (convert to category when beneficial).

        Args:
            df: DataFrame
            column: Column name

        Returns:
            Optimal dtype
        """
        # TODO: Implement object optimization
        # If unique values < 50% of total: use 'category'
        # Otherwise: keep as 'object'
        pass

    @staticmethod
    def optimize_dtypes(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
        """
        Optimize all DataFrame dtypes.

        Args:
            df: DataFrame to optimize
            verbose: Print optimization report

        Returns:
            Optimized DataFrame
        """
        # TODO: Implement full optimization
        # 1. Calculate initial memory
        # 2. Optimize each column based on dtype
        # 3. Calculate final memory
        # 4. Print report if verbose
        # 5. Return optimized DataFrame
        pass


def main():
    """Test the MemoryOptimizer."""
    # Create test DataFrame
    df = pd.DataFrame({
        'id': range(1000000),
        'category': ['A', 'B', 'C'] * 333334,
        'amount': np.random.rand(1000000) * 1000,
        'status': ['active'] * 900000 + ['inactive'] * 100000
    })

    print("Testing MemoryOptimizer")
    print("=" * 60)

    # TODO: Test your implementation
    # 1. Show initial memory
    # 2. Optimize dtypes
    # 3. Show final memory and savings
    pass


if __name__ == "__main__":
    main()
