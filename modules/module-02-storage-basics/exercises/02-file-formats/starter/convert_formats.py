#!/usr/bin/env python3
"""
Exercise 02: File Format Conversion
Convert data between different formats and benchmark performance.

TODO: Complete the functions marked with TODO comments.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any


class FormatConverter:
    """Converts data between different file formats."""

    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.benchmarks = {}

    def read_csv(self) -> pd.DataFrame:
        """Read CSV file into DataFrame."""
        # TODO: Implement CSV reading with pandas
        # Hint: Use pd.read_csv() with appropriate parameters
        # Consider: dtype optimization, parse_dates for timestamps
        pass

    def write_json(self, df: pd.DataFrame, output_file: str) -> Dict[str, Any]:
        """
        Write DataFrame to JSON format and benchmark.

        Returns:
            Dictionary with metrics: file_size_mb, write_time_seconds
        """
        # TODO: Implement JSON writing
        # Hint: Use df.to_json() with orient='records', lines=True for JSONL
        # Measure: time.time() before/after, Path.stat().st_size for file size
        pass

    def write_parquet(self, df: pd.DataFrame, output_file: str,
                     compression: str = 'snappy') -> Dict[str, Any]:
        """
        Write DataFrame to Parquet format with specified compression.

        Args:
            df: DataFrame to write
            output_file: Output file path
            compression: Compression algorithm (snappy, gzip, lz4, zstd)

        Returns:
            Dictionary with metrics: file_size_mb, write_time_seconds, compression_ratio
        """
        # TODO: Implement Parquet writing
        # Hint: Use df.to_parquet() or pq.write_table()
        # Set compression parameter
        # Calculate compression ratio = original_size / compressed_size
        pass

    def write_avro(self, df: pd.DataFrame, output_file: str) -> Dict[str, Any]:
        """
        Write DataFrame to Avro format and benchmark.

        Returns:
            Dictionary with metrics: file_size_mb, write_time_seconds
        """
        # TODO: Implement Avro writing
        # Hint: Convert DataFrame to records, define schema, use fastavro.writer
        # Schema example:
        # schema = {
        #     'type': 'record',
        #     'name': 'Transaction',
        #     'fields': [
        #         {'name': 'id', 'type': 'int'},
        #         {'name': 'amount', 'type': 'double'},
        #         ...
        #     ]
        # }
        pass

    def benchmark_read(self, file_path: str, format_type: str) -> Dict[str, Any]:
        """
        Benchmark reading performance for a file.

        Args:
            file_path: Path to file to read
            format_type: Format type (csv, json, parquet, avro)

        Returns:
            Dictionary with metrics: read_time_seconds, memory_usage_mb
        """
        # TODO: Implement read benchmarking
        # Hint: Measure time with time.time()
        # Measure memory with: import psutil; process.memory_info().rss
        # Read based on format_type:
        #   - csv: pd.read_csv()
        #   - json: pd.read_json(lines=True)
        #   - parquet: pd.read_parquet()
        #   - avro: fastavro.reader()
        pass

    def run_full_benchmark(self, output_dir: str):
        """
        Run complete benchmark: read CSV, write all formats, benchmark reads.

        This is the main function students should complete to tie everything together.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # TODO: Step 1 - Read CSV data
        print("Reading CSV data...")
        # df = self.read_csv()

        # TODO: Step 2 - Write to all formats and collect metrics
        print("\nWriting to different formats...")
        # formats = {
        #     'json': self.write_json(df, output_path / 'data.json'),
        #     'parquet_snappy': self.write_parquet(df, output_path / 'data_snappy.parquet', 'snappy'),
        #     'parquet_gzip': self.write_parquet(df, output_path / 'data_gzip.parquet', 'gzip'),
        #     'avro': self.write_avro(df, output_path / 'data.avro')
        # }

        # TODO: Step 3 - Benchmark read performance for each format
        print("\nBenchmarking read performance...")
        # read_benchmarks = {
        #     'csv': self.benchmark_read(self.input_file, 'csv'),
        #     'json': self.benchmark_read(output_path / 'data.json', 'json'),
        #     ...
        # }

        # TODO: Step 4 - Print comparison table
        print("\n" + "="*80)
        print("BENCHMARK RESULTS")
        print("="*80)
        # Print table with: Format | Size (MB) | Write Time (s) | Read Time (s) | Compression Ratio

        # TODO: Step 5 - Save results to JSON
        # results = {'write_benchmarks': formats, 'read_benchmarks': read_benchmarks}
        # with open(output_path / 'benchmark_results.json', 'w') as f:
        #     json.dump(results, f, indent=2)

        pass


def main():
    """Main function to run the converter."""
    # TODO: Parse command line arguments
    # Example: python convert_formats.py input.csv output_dir/

    # TODO: Create converter instance and run benchmark
    # converter = FormatConverter('data/transactions.csv')
    # converter.run_full_benchmark('output/')

    print("Format conversion completed!")


if __name__ == '__main__':
    main()
