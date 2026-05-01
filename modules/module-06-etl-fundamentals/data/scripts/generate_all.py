#!/usr/bin/env python3
"""
Generate all synthetic data for ETL module exercises.
This is a convenience script that generates all datasets at once.
"""
import subprocess
import sys
from pathlib import Path

def run_generator(script_name):
    """Run a data generation script."""
    script_path = Path(__file__).parent / script_name
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"❌ Error running {script_name}")
        sys.exit(1)

    print(f"✓ {script_name} completed successfully")

def main():
    """Generate all datasets."""
    print("🏭 Generating all synthetic data for ETL module...")
    print("This will take a few moments...\n")

    generators = [
        'generate_users.py',
        'generate_products.py',
        'generate_transactions.py'
    ]

    for generator in generators:
        run_generator(generator)

    print(f"\n{'='*60}")
    print("✅ All data generation completed!")
    print(f"{'='*60}")
    print("\nGenerated datasets:")

    output_dir = Path(__file__).parent.parent / 'raw'
    if output_dir.exists():
        files = sorted(output_dir.glob('*'))
        for file in files:
            size = file.stat().st_size / (1024 * 1024)  # MB
            print(f"  • {file.name:30s} ({size:6.2f} MB)")

    print("\n📚 You can now proceed with the ETL exercises!")

if __name__ == '__main__':
    main()
