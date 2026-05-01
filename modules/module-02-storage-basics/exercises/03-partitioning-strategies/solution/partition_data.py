#!/usr/bin/env python3
"""
Exercise 03: Partitioning Strategies - COMPLETE SOLUTION
Implement and compare different partitioning strategies for data lakes.
"""

import pandas as pd
import pyarrow.dataset as ds
from pathlib import Path
from typing import Dict, Any
import time
import sys
from tabulate import tabulate


class DataPartitioner:
    """Implements different partitioning strategies for Parquet files."""

    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """Load data from CSV or Parquet with date parsing."""
        print(f"Loading data from {self.data_path}...")

        if self.data_path.suffix == '.csv':
            df = pd.read_csv(self.data_path, parse_dates=['timestamp'])
        else:
            df = pd.read_parquet(self.data_path)

        print(f"✓ Loaded {len(df):,} rows")
        return df

    def write_unpartitioned(self, output_dir: str) -> Dict[str, Any]:
        """Write data without partitioning (single file)."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("Writing unpartitioned data...")
        start_time = time.time()

        self.df.to_parquet(
            output_path / 'data.parquet',
            engine='pyarrow',
            compression='snappy',
            index=False
        )

        write_time = time.time() - start_time

        files = list(output_path.rglob('*.parquet'))
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)

        return {
            'file_count': len(files),
            'total_size_mb': round(total_size, 2),
            'write_time_seconds': round(write_time, 2)
        }

    def write_date_partitioned(self, output_dir: str) -> Dict[str, Any]:
        """Write data partitioned by date (year/month/day)."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("Writing date-partitioned data...")

        # Extract date components
        df = self.df.copy()
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day

        start_time = time.time()

        df.to_parquet(
            output_path,
            engine='pyarrow',
            compression='snappy',
            index=False,
            partition_cols=['year', 'month', 'day']
        )

        write_time = time.time() - start_time

        files = list(output_path.rglob('*.parquet'))
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)

        return {
            'file_count': len(files),
            'total_size_mb': round(total_size, 2),
            'write_time_seconds': round(write_time, 2)
        }

    def write_country_partitioned(self, output_dir: str) -> Dict[str, Any]:
        """Write data partitioned by country."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("Writing country-partitioned data...")
        start_time = time.time()

        self.df.to_parquet(
            output_path,
            engine='pyarrow',
            compression='snappy',
            index=False,
            partition_cols=['country']
        )

        write_time = time.time() - start_time

        files = list(output_path.rglob('*.parquet'))
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)

        return {
            'file_count': len(files),
            'total_size_mb': round(total_size, 2),
            'write_time_seconds': round(write_time, 2)
        }

    def write_hybrid_partitioned(self, output_dir: str) -> Dict[str, Any]:
        """Write data with hybrid partitioning (year/month/country)."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("Writing hybrid-partitioned data...")

        df = self.df.copy()
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month

        start_time = time.time()

        df.to_parquet(
            output_path,
            engine='pyarrow',
            compression='snappy',
            index=False,
            partition_cols=['year', 'month', 'country']
        )

        write_time = time.time() - start_time

        files = list(output_path.rglob('*.parquet'))
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)

        return {
            'file_count': len(files),
            'total_size_mb': round(total_size, 2),
            'write_time_seconds': round(write_time, 2)
        }

    def benchmark_query(self, data_dir: str, query_type: str) -> Dict[str, Any]:
        """Benchmark query on partitioned data."""
        print(f"  Benchmarking {query_type} query...")

        dataset = ds.dataset(data_dir, format='parquet', partitioning='hive')

        # Define filters based on query type
        if query_type == 'all':
            filter_expr = None
        elif query_type == 'date_filter':
            filter_expr = (ds.field('year') == 2024) & (ds.field('month') == 1)
        elif query_type == 'country_filter':
            filter_expr = ds.field('country') == 'USA'
        elif query_type == 'hybrid_filter':
            filter_expr = (ds.field('year') == 2024) & \
                         (ds.field('month') == 1) & \
                         (ds.field('country') == 'USA')
        else:
            filter_expr = None

        start_time = time.time()
        table = dataset.to_table(filter=filter_expr)
        query_time = time.time() - start_time

        # Count fragments (files) accessed
        fragments = list(dataset.get_fragments(filter=filter_expr))
        data_scanned = sum(f.metadata.total_byte_size for f in fragments) / (1024 * 1024)

        return {
            'query_time_seconds': round(query_time, 3),
            'rows_read': len(table),
            'data_scanned_mb': round(data_scanned, 2),
            'files_scanned': len(fragments)
        }

    def run_comparison(self, output_base_dir: str):
        """Run complete comparison of all partitioning strategies."""
        base_path = Path(output_base_dir)
        base_path.mkdir(parents=True, exist_ok=True)

        print("\n" + "="*80)
        print("PARTITIONING STRATEGY COMPARISON")
        print("="*80)

        # Step 1: Load data
        print("\n[1/3] Loading data...")
        self.df = self.load_data()

        # Step 2: Write with different strategies
        print("\n[2/3] Writing with different partitioning strategies...")
        write_results = {
            'Unpartitioned': self.write_unpartitioned(f"{output_base_dir}/unpartitioned"),
            'Date (Y/M/D)': self.write_date_partitioned(f"{output_base_dir}/date_partitioned"),
            'Country': self.write_country_partitioned(f"{output_base_dir}/country_partitioned"),
            'Hybrid (Y/M/Country)': self.write_hybrid_partitioned(f"{output_base_dir}/hybrid_partitioned")
        }

        # Step 3: Benchmark queries
        print("\n[3/3] Benchmarking queries...")

        query_results = {}
        for strategy_name, dir_name in [
            ('Unpartitioned', 'unpartitioned'),
            ('Date (Y/M/D)', 'date_partitioned'),
            ('Country', 'country_partitioned'),
            ('Hybrid (Y/M/Country)', 'hybrid_partitioned')
        ]:
            print(f"\n{strategy_name}:")
            query_results[strategy_name] = {
                'date_filter': self.benchmark_query(f"{output_base_dir}/{dir_name}", 'date_filter')
            }

        # Print write comparison
        print("\n" + "="*80)
        print("WRITE PERFORMANCE")
        print("="*80)

        write_table = []
        for strategy, metrics in write_results.items():
            write_table.append([
                strategy,
                metrics['file_count'],
                f"{metrics['total_size_mb']:.2f} MB",
                f"{metrics['write_time_seconds']:.2f}s"
            ])

        print(tabulate(
            write_table,
            headers=['Strategy', 'Files', 'Total Size', 'Write Time'],
            tablefmt='grid'
        ))

        # Print query comparison
        print("\n" + "="*80)
        print("QUERY PERFORMANCE (Date Filter: year=2024, month=1)")
        print("="*80)

        query_table = []
        for strategy in ['Unpartitioned', 'Date (Y/M/D)', 'Country', 'Hybrid (Y/M/Country)']:
            metrics = query_results[strategy]['date_filter']
            query_table.append([
                strategy,
                f"{metrics['query_time_seconds']:.3f}s",
                f"{metrics['rows_read']:,}",
                f"{metrics['data_scanned_mb']:.2f} MB",
                metrics['files_scanned']
            ])

        print(tabulate(
            query_table,
            headers=['Strategy', 'Query Time', 'Rows', 'Data Scanned', 'Files'],
            tablefmt='grid'
        ))

        # Calculate improvements
        print("\n" + "="*80)
        print("KEY INSIGHTS")
        print("="*80)

        unprt_time = query_results['Unpartitioned']['date_filter']['query_time_seconds']
        date_time = query_results['Date (Y/M/D)']['date_filter']['query_time_seconds']
        hybrid_time = query_results['Hybrid (Y/M/Country)']['date_filter']['query_time_seconds']

        speedup_date = (unprt_time / date_time) if date_time > 0 else 0
        speedup_hybrid = (unprt_time / hybrid_time) if hybrid_time > 0 else 0

        print(f"✓ Date partitioning: {speedup_date:.1f}x faster than unpartitioned")
        print(f"✓ Hybrid partitioning: {speedup_hybrid:.1f}x faster than unpartitioned")

        unprt_scan = query_results['Unpartitioned']['date_filter']['data_scanned_mb']
        date_scan = query_results['Date (Y/M/D)']['date_filter']['data_scanned_mb']
        scan_reduction = ((unprt_scan - date_scan) / unprt_scan * 100) if unprt_scan > 0 else 0

        print(f"✓ Date partitioning reduces data scanned by {scan_reduction:.1f}%")

        print("\n📋 RECOMMENDATIONS:")
        print("• Use Date partitioning for time-series queries")
        print("• Use Hybrid partitioning for multi-dimensional queries")
        print("• Avoid over-partitioning (keep partitions >100MB)")
        print("• Use year/month/day for Hive compatibility")
        print("="*80)


def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python partition_data.py <input_file> <output_dir>")
        print("Example: python partition_data.py ../../data/transactions.csv output/")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    partitioner = DataPartitioner(input_file)
    partitioner.run_comparison(output_dir)

    print("\n✅ Partitioning comparison completed successfully!")


if __name__ == '__main__':
    main()
