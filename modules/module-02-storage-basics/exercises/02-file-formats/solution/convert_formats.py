#!/usr/bin/env python3
"""
Exercise 02: File Format Conversion - COMPLETE SOLUTION
Convert data between different formats and benchmark performance.
"""

import pandas as pd
import fastavro
import json
import time
import psutil
import sys
from pathlib import Path
from typing import Dict, Any
from tabulate import tabulate


class FormatConverter:
    """Converts data between different file formats with benchmarking."""

    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.benchmarks = {}
        self.process = psutil.Process()

    def read_csv(self) -> pd.DataFrame:
        """Read CSV file into DataFrame with optimized dtypes."""
        print(f"Reading CSV from {self.input_file}...")
        start_time = time.time()

        df = pd.read_csv(
            self.input_file,
            parse_dates=['timestamp'],
            dtype={
                'transaction_id': 'int32',
                'user_id': 'int32',
                'product_id': 'int16',
                'amount': 'float32',
                'country': 'category',
                'status': 'category'
            }
        )

        read_time = time.time() - start_time
        print(f"✓ Read {len(df):,} rows in {read_time:.2f}s")

        return df

    def write_json(self, df: pd.DataFrame, output_file: str) -> Dict[str, Any]:
        """Write DataFrame to JSONL format and benchmark."""
        output_path = Path(output_file)
        print(f"Writing JSON to {output_path.name}...")

        start_time = time.time()
        df.to_json(output_path, orient='records', lines=True, date_format='iso')
        write_time = time.time() - start_time

        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        return {
            'file_size_mb': round(file_size_mb, 2),
            'write_time_seconds': round(write_time, 2),
            'format': 'JSONL'
        }

    def write_parquet(self, df: pd.DataFrame, output_file: str,
                     compression: str = 'snappy') -> Dict[str, Any]:
        """Write DataFrame to Parquet format with specified compression."""
        output_path = Path(output_file)
        print(f"Writing Parquet ({compression}) to {output_path.name}...")

        start_time = time.time()
        df.to_parquet(
            output_path,
            engine='pyarrow',
            compression=compression,
            index=False
        )
        write_time = time.time() - start_time

        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        original_size_mb = self.input_file.stat().st_size / (1024 * 1024)
        compression_ratio = original_size_mb / file_size_mb

        return {
            'file_size_mb': round(file_size_mb, 2),
            'write_time_seconds': round(write_time, 2),
            'compression_ratio': round(compression_ratio, 2),
            'compression': compression,
            'format': 'Parquet'
        }

    def write_avro(self, df: pd.DataFrame, output_file: str) -> Dict[str, Any]:
        """Write DataFrame to Avro format and benchmark."""
        output_path = Path(output_file)
        print(f"Writing Avro to {output_path.name}...")

        # Define Avro schema
        schema = {
            'type': 'record',
            'name': 'Transaction',
            'namespace': 'com.globalmart.transactions',
            'fields': [
                {'name': 'transaction_id', 'type': 'int'},
                {'name': 'user_id', 'type': 'int'},
                {'name': 'product_id', 'type': 'int'},
                {'name': 'amount', 'type': 'double'},
                {'name': 'timestamp', 'type': 'string'},
                {'name': 'country', 'type': 'string'},
                {'name': 'status', 'type': 'string'}
            ]
        }

        # Convert DataFrame to records
        records = df.to_dict('records')
        for record in records:
            if pd.notna(record['timestamp']):
                record['timestamp'] = str(record['timestamp'])

        start_time = time.time()
        with open(output_path, 'wb') as out:
            fastavro.writer(out, schema, records)
        write_time = time.time() - start_time

        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        return {
            'file_size_mb': round(file_size_mb, 2),
            'write_time_seconds': round(write_time, 2),
            'format': 'Avro'
        }

    def benchmark_read(self, file_path: str, format_type: str) -> Dict[str, Any]:
        """Benchmark reading performance for a file."""
        file_path = Path(file_path)
        print(f"Benchmarking read for {file_path.name} ({format_type})...")

        # Measure initial memory
        mem_before = self.process.memory_info().rss / (1024 * 1024)

        start_time = time.time()

        if format_type == 'csv':
            df = pd.read_csv(file_path, parse_dates=['timestamp'])
        elif format_type == 'json':
            df = pd.read_json(file_path, lines=True)
        elif format_type == 'parquet':
            df = pd.read_parquet(file_path)
        elif format_type == 'avro':
            with open(file_path, 'rb') as f:
                reader = fastavro.reader(f)
                records = list(reader)
                df = pd.DataFrame(records)
        else:
            raise ValueError(f"Unknown format: {format_type}")

        read_time = time.time() - start_time

        # Measure memory after loading
        mem_after = self.process.memory_info().rss / (1024 * 1024)
        memory_used = mem_after - mem_before

        return {
            'read_time_seconds': round(read_time, 3),
            'memory_usage_mb': round(memory_used, 2),
            'rows_read': len(df),
            'format': format_type.upper()
        }

    def run_full_benchmark(self, output_dir: str):
        """Run complete benchmark: read CSV, write all formats, benchmark reads."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("\n" + "="*80)
        print("FILE FORMAT CONVERSION & BENCHMARK")
        print("="*80)

        # Step 1: Read CSV data
        print("\n[1/4] Reading source CSV data...")
        df = self.read_csv()
        original_size_mb = self.input_file.stat().st_size / (1024 * 1024)
        print(f"Original CSV size: {original_size_mb:.2f} MB")

        # Step 2: Write to all formats
        print("\n[2/4] Converting to different formats...")
        write_results = {
            'JSON': self.write_json(df, output_path / 'data.json'),
            'Parquet (Snappy)': self.write_parquet(df, output_path / 'data_snappy.parquet', 'snappy'),
            'Parquet (Gzip)': self.write_parquet(df, output_path / 'data_gzip.parquet', 'gzip'),
            'Parquet (LZ4)': self.write_parquet(df, output_path / 'data_lz4.parquet', 'lz4'),
            'Avro': self.write_avro(df, output_path / 'data.avro')
        }

        # Step 3: Benchmark read performance
        print("\n[3/4] Benchmarking read performance...")
        read_results = {
            'CSV': self.benchmark_read(self.input_file, 'csv'),
            'JSON': self.benchmark_read(output_path / 'data.json', 'json'),
            'Parquet (Snappy)': self.benchmark_read(output_path / 'data_snappy.parquet', 'parquet'),
            'Parquet (Gzip)': self.benchmark_read(output_path / 'data_gzip.parquet', 'parquet'),
            'Avro': self.benchmark_read(output_path / 'data.avro', 'avro')
        }

        # Step 4: Create comparison table
        print("\n[4/4] Generating comparison report...")

        table_data = []
        for format_name in ['CSV', 'JSON', 'Parquet (Snappy)', 'Parquet (Gzip)', 'Parquet (LZ4)', 'Avro']:
            if format_name == 'CSV':
                size = original_size_mb
                write_time = '-'
                compression = '-'
            else:
                write_info = write_results[format_name]
                size = write_info['file_size_mb']
                write_time = write_info['write_time_seconds']
                compression = write_info.get('compression_ratio', '-')

            if format_name in read_results:
                read_info = read_results[format_name]
                read_time = read_info['read_time_seconds']
                memory = read_info['memory_usage_mb']
            else:
                read_time = '-'
                memory = '-'

            table_data.append([
                format_name,
                f"{size:.2f}" if isinstance(size, float) else size,
                write_time if write_time == '-' else f"{write_time:.2f}s",
                read_time if read_time == '-' else f"{read_time:.3f}s",
                memory if memory == '-' else f"{memory:.1f} MB",
                compression if compression == '-' else f"{compression:.2f}x"
            ])

        print("\n" + "="*80)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*80)
        print(tabulate(
            table_data,
            headers=['Format', 'Size (MB)', 'Write Time', 'Read Time', 'Memory', 'Compression'],
            tablefmt='grid'
        ))

        # Print insights
        print("\n" + "="*80)
        print("KEY INSIGHTS")
        print("="*80)

        # Find best compression
        parquet_sizes = {k: v['file_size_mb'] for k, v in write_results.items() if 'Parquet' in k}
        best_compression = min(parquet_sizes.items(), key=lambda x: x[1])
        print(f"✓ Best compression: {best_compression[0]} ({best_compression[1]:.2f} MB)")

        # Find fastest read
        read_times = {k: v['read_time_seconds'] for k, v in read_results.items()}
        fastest_read = min(read_times.items(), key=lambda x: x[1])
        print(f"✓ Fastest read: {fastest_read[0]} ({fastest_read[1]:.3f}s)")

        # Calculate space savings
        parquet_snappy_size = write_results['Parquet (Snappy)']['file_size_mb']
        space_saved = ((original_size_mb - parquet_snappy_size) / original_size_mb) * 100
        print(f"✓ Space saved with Parquet (Snappy): {space_saved:.1f}%")

        # Step 5: Save detailed results to JSON
        results = {
            'metadata': {
                'input_file': str(self.input_file),
                'rows': len(df),
                'original_size_mb': round(original_size_mb, 2)
            },
            'write_benchmarks': write_results,
            'read_benchmarks': read_results
        }

        results_file = output_path / 'benchmark_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n✓ Detailed results saved to: {results_file}")
        print("="*80)


def main():
    """Main function to run the converter."""
    if len(sys.argv) != 3:
        print("Usage: python convert_formats.py <input_csv> <output_dir>")
        print("Example: python convert_formats.py ../../data/transactions.csv output/")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    converter = FormatConverter(input_file)
    converter.run_full_benchmark(output_dir)

    print("\n✅ Format conversion and benchmarking completed successfully!")


if __name__ == '__main__':
    main()
