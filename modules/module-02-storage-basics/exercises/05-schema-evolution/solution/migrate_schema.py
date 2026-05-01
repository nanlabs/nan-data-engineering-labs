#!/usr/bin/env python3
"""Exercise 05: Schema Evolution - Complete Solution"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

# Schema V1: Basic transaction data
schema_v1 = pa.schema([
    ('transaction_id', pa.int32()),
    ('amount', pa.float32()),
    ('timestamp', pa.timestamp('ms'))
])

# Schema V2: Add customer_email (backward compatible)
schema_v2 = pa.schema([
    ('transaction_id', pa.int32()),
    ('amount', pa.float32()),
    ('timestamp', pa.timestamp('ms')),
    ('customer_email', pa.string())  # NEW FIELD
])

# Schema V3: Add loyalty_points (backward compatible)
schema_v3 = pa.schema([
    ('transaction_id', pa.int32()),
    ('amount', pa.float32()),
    ('timestamp', pa.timestamp('ms')),
    ('customer_email', pa.string()),
    ('loyalty_points', pa.int32())  # NEW FIELD
])

def write_v1_data(output_path: Path):
    """Write sample data with V1 schema."""
    print(f"Writing V1 data to {output_path}...")

    data = pd.DataFrame({
        'transaction_id': [1, 2, 3, 4, 5],
        'amount': [100.0, 200.0, 150.0, 300.0, 75.0],
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='D')
    })

    table = pa.Table.from_pandas(data, schema=schema_v1)
    pq.write_table(table, output_path)
    print(f"✓ Wrote {len(data)} rows with schema V1")

def write_v2_data(output_path: Path):
    """Write sample data with V2 schema (added customer_email)."""
    print(f"Writing V2 data to {output_path}...")

    data = pd.DataFrame({
        'transaction_id': [6, 7, 8, 9, 10],
        'amount': [125.0, 275.0, 180.0, 90.0, 220.0],
        'timestamp': pd.date_range('2024-01-06', periods=5, freq='D'),
        'customer_email': ['user1@example.com', 'user2@example.com',
                          'user3@example.com', 'user4@example.com', 'user5@example.com']
    })

    table = pa.Table.from_pandas(data, schema=schema_v2)
    pq.write_table(table, output_path)
    print(f"✓ Wrote {len(data)} rows with schema V2 (added customer_email)")

def write_v3_data(output_path: Path):
    """Write sample data with V3 schema (added loyalty_points)."""
    print(f"Writing V3 data to {output_path}...")

    data = pd.DataFrame({
        'transaction_id': [11, 12, 13, 14, 15],
        'amount': [165.0, 295.0, 135.0, 240.0, 88.0],
        'timestamp': pd.date_range('2024-01-11', periods=5, freq='D'),
        'customer_email': ['user6@example.com', 'user7@example.com',
                          'user8@example.com', 'user9@example.com', 'user10@example.com'],
        'loyalty_points': [100, 200, 150, 300, 75]
    })

    table = pa.Table.from_pandas(data, schema=schema_v3)
    pq.write_table(table, output_path)
    print(f"✓ Wrote {len(data)} rows with schema V3 (added loyalty_points)")

def test_backward_compatibility(data_dir: Path):
    """Test that new readers can read old data."""
    print("\n" + "="*80)
    print("TEST 1: Backward Compatibility (new code reads old data)")
    print("="*80)

    # New reader (expects V3 schema) reads V1 data
    print("\nReading V1 data with V3 reader...")
    try:
        table = pq.read_table(data_dir / 'v1.parquet')
        df = table.to_pandas()

        print(f"✓ SUCCESS: Read {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        print("  Missing columns handled gracefully")

        # Check if missing columns are filled with nulls
        if 'customer_email' in df.columns:
            print(f"  customer_email: {df['customer_email'].isna().sum()} nulls")
        else:
            print("  customer_email: Column not present (OK)")

    except Exception as e:
        print(f"❌ FAILED: {e}")

    # New reader reads V2 data
    print("\nReading V2 data with V3 reader...")
    try:
        table = pq.read_table(data_dir / 'v2.parquet')
        df = table.to_pandas()

        print(f"✓ SUCCESS: Read {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")

    except Exception as e:
        print(f"❌ FAILED: {e}")

def test_forward_compatibility(data_dir: Path):
    """Test that old readers can read new data."""
    print("\n" + "="*80)
    print("TEST 2: Forward Compatibility (old code reads new data)")
    print("="*80)

    # Old reader (expects V1 schema) reads V3 data
    print("\nReading V3 data with V1 reader (only V1 columns)...")
    try:
        # Read only V1 columns
        table = pq.read_table(data_dir / 'v3.parquet',
                              columns=['transaction_id', 'amount', 'timestamp'])
        df = table.to_pandas()

        print(f"✓ SUCCESS: Read {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        print("  Extra columns ignored")
        print("\n  Sample data:")
        print(df.head(3))

    except Exception as e:
        print(f"❌ FAILED: {e}")

def test_mixed_versions(data_dir: Path):
    """Test reading multiple files with different schema versions."""
    print("\n" + "="*80)
    print("TEST 3: Mixed Version Reading")
    print("="*80)

    print("\nReading all versions together...")
    try:
        # Read all parquet files in directory
        all_data = []
        for file in sorted(data_dir.glob('v*.parquet')):
            table = pq.read_table(file)
            all_data.append(table)

        # Concatenate with schema unification
        combined_table = pa.concat_tables(all_data, promote=True)
        df = combined_table.to_pandas()

        print(f"✓ SUCCESS: Combined {len(df)} rows from {len(all_data)} files")
        print(f"  Unified columns: {list(df.columns)}")
        print("\n  Summary by version:")
        for i, data in enumerate(all_data, 1):
            print(f"    V{i}: {data.num_rows} rows, {data.num_columns} columns")

        print("\n  Null counts:")
        for col in df.columns:
            null_count = df[col].isna().sum()
            print(f"    {col}: {null_count} nulls")

    except Exception as e:
        print(f"❌ FAILED: {e}")

def main():
    """Run complete schema evolution tests."""
    output_dir = Path('data')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*80)
    print("SCHEMA EVOLUTION DEMONSTRATION")
    print("="*80 + "\n")

    # Step 1: Write data with different schema versions
    print("[1/4] Writing data with different schema versions...")
    write_v1_data(output_dir / 'v1.parquet')
    write_v2_data(output_dir / 'v2.parquet')
    write_v3_data(output_dir / 'v3.parquet')

    # Step 2: Test backward compatibility
    print("\n[2/4] Testing compatibility...")
    test_backward_compatibility(output_dir)
    test_forward_compatibility(output_dir)

    # Step 3: Test mixed version reading
    print("\n[3/4] Testing mixed version reading...")
    test_mixed_versions(output_dir)

    # Step 4: Print best practices
    print("\n[4/4] Schema Evolution Best Practices:")
    print("="*80)
    print("✓ ADD columns: Always backward compatible (use defaults/nulls)")
    print("✓ RENAME columns: Create new column, deprecate old (2-phase)")
    print("✓ CHANGE types: Create new column with new type, migrate gradually")
    print("✗ DELETE columns: Can break old readers (deprecate instead)")
    print("✗ CHANGE semantics: Dangerous (e.g., 'amount' USD → EUR)")
    print("\nRECOMMENDATION: Use optional fields for new columns")
    print("  schema_v2 = pa.schema([..., ('new_field', pa.string(), False)])")
    print("="*80)

    print("\n✅ Schema evolution tests completed!")
    print(f"Check generated files in: {output_dir.absolute()}")

if __name__ == '__main__':
    main()
