#!/usr/bin/env python3
"""
Exercise 06: Data Quality - Data Profiler - SOLUTION
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProfiler:
    """Generate data quality profile."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.profile = {}

    def generate_profile(self) -> Dict[str, Any]:
        """Generate comprehensive data profile."""
        logger.info(f"Profiling {len(self.df)} records")

        self.profile = {
            'overview': self._profile_overview(),
            'columns': self._profile_columns(),
            'duplicates': self._profile_duplicates(),
            'missing': self._profile_missing(),
            'numeric_stats': self._profile_numeric()
        }

        return self.profile

    def _profile_overview(self) -> dict:
        """Overall dataset statistics."""
        return {
            'row_count': len(self.df),
            'column_count': len(self.df.columns),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / (1024 ** 2),
            'duplicate_rows': self.df.duplicated().sum()
        }

    def _profile_columns(self) -> dict:
        """Per-column statistics."""
        col_profiles = {}

        for col in self.df.columns:
            col_profiles[col] = {
                'dtype': str(self.df[col].dtype),
                'null_count': int(self.df[col].isnull().sum()),
                'null_percent': round(self.df[col].isnull().sum() / len(self.df) * 100, 2),
                'unique_count': int(self.df[col].nunique()),
                'unique_percent': round(self.df[col].nunique() / len(self.df) * 100, 2)
            }

            # Add sample values
            if self.df[col].nunique() <= 10:
                col_profiles[col]['values'] = self.df[col].value_counts().to_dict()

        return col_profiles

    def _profile_duplicates(self) -> dict:
        """Duplicate analysis."""
        return {
            'total_duplicates': int(self.df.duplicated().sum()),
            'duplicate_percent': round(self.df.duplicated().sum() / len(self.df) * 100, 2)
        }

    def _profile_missing(self) -> dict:
        """Missing value analysis."""
        missing = self.df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)

        return {
            'columns_with_missing': len(missing),
            'total_missing_values': int(missing.sum()),
            'by_column': missing.to_dict()
        }

    def _profile_numeric(self) -> dict:
        """Numeric column statistics."""
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns

        if len(numeric_cols) == 0:
            return {}

        stats = self.df[numeric_cols].describe().to_dict()
        return stats

    def print_report(self):
        """Print formatted profile report."""
        if not self.profile:
            self.generate_profile()

        print("=" * 60)
        print("DATA QUALITY PROFILE")
        print("=" * 60)

        # Overview
        print("\n📊 Overview:")
        for key, value in self.profile['overview'].items():
            print(f"  {key}: {value}")

        # Missing values
        if self.profile['missing']['columns_with_missing'] > 0:
            print("\n⚠️  Missing Values:")
            for col, count in list(self.profile['missing']['by_column'].items())[:5]:
                pct = count / self.profile['overview']['row_count'] * 100
                print(f"  {col}: {count} ({pct:.1f}%)")

        # Duplicates
        print(f"\n🔄 Duplicates: {self.profile['duplicates']['total_duplicates']} "
              f"({self.profile['duplicates']['duplicate_percent']:.1f}%)")

        # Column summary
        print(f"\n📋 Columns ({self.profile['overview']['column_count']}):")
        for col, info in list(self.profile['columns'].items())[:10]:
            print(f"  {col}:")
            print(f"    Type: {info['dtype']}")
            print(f"    Nulls: {info['null_count']} ({info['null_percent']:.1f}%)")
            print(f"    Unique: {info['unique_count']} ({info['unique_percent']:.1f}%)")

def main():
    """Test profiler."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    users_file = data_dir / 'users_clean.csv'

    if not users_file.exists():
        print("⚠️  Data file not found. Run data generation first.")
        return

    print("Loading data...")
    df = pd.read_csv(users_file, nrows=5000)

    print("\nGenerating profile...")
    profiler = DataProfiler(df)
    profile = profiler.generate_profile()

    profiler.print_report()

if __name__ == '__main__':
    main()
