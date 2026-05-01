#!/usr/bin/env python3
"""Exercise 05: Schema Evolution - Starter Template"""
import pyarrow as pa

# TODO: Define schema V1 (transaction_id, amount, timestamp)
schema_v1 = pa.schema([
    # Add fields here
])

def write_v1_data(output_path: str):
    """TODO: Write sample data with V1 schema"""
    pass

def write_v2_data(output_path: str):
    """TODO: Write data with V2 schema (add customer_email)"""
    pass

def test_backward_compatibility():
    """TODO: Test that new readers can read old data"""
    pass

def test_forward_compatibility():
    """TODO: Test that old readers can read new data"""
    pass

if __name__ == '__main__':
    print("Testing schema evolution...")
    write_v1_data('data/v1.parquet')
    write_v2_data('data/v2.parquet')
    test_backward_compatibility()
    test_forward_compatibility()
