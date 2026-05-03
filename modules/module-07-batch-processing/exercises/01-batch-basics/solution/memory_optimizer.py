"""
Memory Optimizer - Solution

Complete implementation of DataFrame memory optimization.
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
        return df.memory_usage(deep=True).sum() / (1024 ** 2)

    @staticmethod
    def optimize_ints(df: pd.DataFrame, column: str) -> str:
        """
        Find optimal integer dtype for column.

        Args:
            df: DataFrame
            column: Column name

        Returns:
            Optimal dtype as string
        """
        col_min = df[column].min()
        col_max = df[column].max()

        # Check if unsigned (all values >= 0)
        if col_min >= 0:
            if col_max < 255:
                return 'uint8'
            elif col_max < 65535:
                return 'uint16'
            elif col_max < 4294967295:
                return 'uint32'
            else:
                return 'uint64'
        else:
            # Signed integers
            if col_min > -128 and col_max < 127:
                return 'int8'
            elif col_min > -32768 and col_max < 32767:
                return 'int16'
            elif col_min > -2147483648 and col_max < 2147483647:
                return 'int32'
            else:
                return 'int64'

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
        # For most practical purposes, float32 is sufficient
        # Only use float64 if precision is critical
        return 'float32'

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
        num_unique = df[column].nunique()
        num_total = len(df[column])

        # If unique values < 50% of total, use category
        # Category dtype is beneficial for repeated strings
        if num_unique / num_total < 0.5:
            return 'category'
        else:
            return 'object'

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
        # Store initial memory
        initial_memory = MemoryOptimizer.memory_usage_mb(df)

        # Copy DataFrame
        df_optimized = df.copy()

        # Track changes
        changes = []

        # Optimize each column
        for col in df_optimized.columns:
            col_type = df_optimized[col].dtype

            # Skip if already optimal or datetime
            if col_type in ['datetime64[ns]', 'bool']:
                continue

            try:
                if np.issubdtype(col_type, np.integer):
                    # Optimize integers
                    new_dtype = MemoryOptimizer.optimize_ints(df_optimized, col)
                    if new_dtype != str(col_type):
                        df_optimized[col] = df_optimized[col].astype(new_dtype)
                        changes.append((col, str(col_type), new_dtype))

                elif np.issubdtype(col_type, np.floating):
                    # Optimize floats
                    new_dtype = MemoryOptimizer.optimize_floats(df_optimized, col)
                    if new_dtype != str(col_type):
                        df_optimized[col] = df_optimized[col].astype(new_dtype)
                        changes.append((col, str(col_type), new_dtype))

                elif col_type == 'object':
                    # Optimize objects/strings
                    new_dtype = MemoryOptimizer.optimize_objects(df_optimized, col)
                    if new_dtype != 'object':
                        df_optimized[col] = df_optimized[col].astype(new_dtype)
                        changes.append((col, str(col_type), new_dtype))

            except Exception as e:
                if verbose:
                    print(f"Warning: Could not optimize column '{col}': {e}")

        # Calculate final memory
        final_memory = MemoryOptimizer.memory_usage_mb(df_optimized)
        reduction = initial_memory - final_memory
        reduction_pct = (reduction / initial_memory) * 100

        # Print report
        if verbose:
            print("Memory Optimization Report")
            print("=" * 60)
            print(f"Initial memory usage: {initial_memory:.2f} MB")
            print(f"Final memory usage:   {final_memory:.2f} MB")
            print(f"Reduction:            {reduction:.2f} MB ({reduction_pct:.1f}%)")
            print()

            if changes:
                print("Dtype changes:")
                for col, old_dtype, new_dtype in changes:
                    print(f"  {col}: {old_dtype} → {new_dtype}")
            else:
                print("No dtype changes made")

        return df_optimized


def main():
    """Demonstrate MemoryOptimizer usage."""
    # Create test DataFrame with suboptimal dtypes
    print("Creating test DataFrame...")
    df = pd.DataFrame({
        'id': range(1000000),  # Will be int64
        'small_id': range(1, 1000001),  # Could be uint32
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 1000000),  # Could be category
        'amount': np.random.rand(1000000) * 1000,  # float64, could be float32
        'status': np.random.choice(['active', 'inactive'], 1000000, p=[0.9, 0.1]),  # Could be category
        'flag': np.random.choice([0, 1], 1000000),  # Could be uint8
        'description': ['Product description ' + str(i % 100) for i in range(1000000)]  # object, many repeats
    })

    print(f"\nDataFrame shape: {df.shape}")
    print("\nInitial dtypes:")
    print(df.dtypes)
    print()

    # Optimize
    print("Optimizing dtypes...")
    print()
    df_optimized = MemoryOptimizer.optimize_dtypes(df, verbose=True)

    print("\n" + "=" * 60)
    print("\nOptimized dtypes:")
    print(df_optimized.dtypes)

    print("\nVerification: Data integrity")
    print(f"  ID sum matches: {df['id'].sum() == df_optimized['id'].sum()}")
    print(f"  Amount sum matches: {abs(df['amount'].sum() - df_optimized['amount'].sum()) < 0.01}")
    print(f"  Category counts match: {df['category'].value_counts().equals(df_optimized['category'].value_counts())}")


if __name__ == "__main__":
    main()
