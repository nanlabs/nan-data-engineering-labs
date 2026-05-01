#!/usr/bin/env python3
"""Exercise 04: Compression Optimization - Starter Template"""
from pathlib import Path

class CompressionTester:
    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.df = None

    def load_data(self):
        """TODO: Load CSV data into DataFrame"""
        pass

    def test_compression(self, output_path: str, compression: str):
        """
        TODO: Write Parquet with specified compression and measure:
        - Write time
        - File size
        - Compression ratio
        - Read time
        """
        pass

    def run_comparison(self, output_dir: str):
        """TODO: Test snappy, gzip, lz4, zstd and compare results"""
        pass

if __name__ == '__main__':
    tester = CompressionTester('../../data/transactions.csv')
    tester.run_comparison('output/')
