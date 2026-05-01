#!/usr/bin/env python3
"""
Master script to generate all datasets for Module 05 - Data Lakehouse.

This script orchestrates the generation of all three datasets:
1. E-commerce transactions (300K records)
2. User events/clickstream (200K records)
3. Application logs (100K records)

Total: 500K+ records with intentional quality issues for practice.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_script(script_name: str) -> bool:
    """Run a generation script and return success status."""
    script_path = Path(__file__).parent / script_name
    
    print(f"\n{'=' * 70}")
    print(f"Running: {script_name}")
    print('=' * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main execution."""
    print("=" * 70)
    print("🚀 DATA LAKEHOUSE - MASTER DATA GENERATOR")
    print("=" * 70)
    print("\nThis script will generate all datasets for Module 05:")
    print("  1. E-commerce Transactions (300K records)")
    print("  2. User Events/Clickstream (200K records)")
    print("  3. Application Logs (100K records)")
    print("\nTotal: 500K+ records with quality issues")
    print("\nEstimated time: 2-3 minutes")
    print("=" * 70)
    
    input("\nPress Enter to start generation... ")
    
    start_time = time.time()
    
    # Scripts to run
    scripts = [
        "generate_transactions.py",
        "generate_events.py",
        "generate_logs.py"
    ]
    
    results = {}
    
    # Run each script
    for script in scripts:
        success = run_script(script)
        results[script] = success
        
        if not success:
            print(f"\n⚠️  Warning: {script} failed. Continuing with next script...")
    
    # Final summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("📊 GENERATION SUMMARY")
    print("=" * 70)
    
    for script, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {script:30s} {status}")
    
    print(f"\nTotal time: {elapsed_time:.1f} seconds")
    
    # Check output files
    raw_dir = Path(__file__).parent.parent / "raw"
    expected_files = ["transactions.json", "events.json", "logs.jsonl"]
    
    print("\n📁 Generated Files:")
    total_size = 0
    for filename in expected_files:
        filepath = raw_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"  ✅ {filename:25s} {size_mb:8.2f} MB")
        else:
            print(f"  ❌ {filename:25s} NOT FOUND")
    
    print(f"\n  Total dataset size: {total_size:.2f} MB")
    
    # Success check
    all_success = all(results.values())
    
    if all_success:
        print("\n" + "=" * 70)
        print("✅ ALL DATASETS GENERATED SUCCESSFULLY!")
        print("=" * 70)
        print("\n💡 Next Steps:")
        print("   1. Review data quality issues in each dataset")
        print("   2. Start Docker infrastructure: cd ../infrastructure && docker-compose up -d")
        print("   3. Load data into Bronze layer with PySpark")
        print("   4. Clean and validate for Silver layer")
        print("   5. Aggregate for Gold layer metrics")
        print("\n📚 Documentation:")
        print("   - Dataset details: data/README.md")
        print("   - Schemas: data/schemas/*.json")
        print("   - Theory: theory/*.md")
        print("\n🎯 Ready to start exercises!")
    else:
        print("\n" + "=" * 70)
        print("⚠️  GENERATION COMPLETED WITH WARNINGS")
        print("=" * 70)
        print("\nSome datasets failed to generate. Check errors above.")
        print("You can re-run individual scripts if needed.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
