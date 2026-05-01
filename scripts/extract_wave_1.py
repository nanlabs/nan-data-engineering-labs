#!/usr/bin/env python3
"""
Wave 1 Content Extraction and Inventory

Extracts all content from training-cloud-data Wave 1 modules (01-06)
into nan-data-engineering-labs modules/, and generates inventory report.

Usage:
    python scripts/extract_wave_1.py

Output:
    - Copies all files from training-cloud-data/modules/module-0{1..6}-* 
      to nan-data-engineering-labs/modules/module-0{1..6}-*
    - Generates wave_1_inventory.txt with file counts and structure
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime


def extract_wave_1():
    """Extract Wave 1 modules from source to target."""
    labs_root = Path(__file__).parent.parent
    source_root = labs_root.parent / "training-cloud-data" / "modules"
    target_root = labs_root / "modules"

    # Wave 1 modules
    wave_1_modules = [
        "module-01-cloud-fundamentals",
        "module-02-storage-basics",
        "module-03-sql-foundations",
        "module-04-python-for-data",
        "module-05-data-lakehouse",
        "module-06-etl-fundamentals",
    ]

    print("=== Wave 1 Content Extraction ===\n")

    total_files = 0
    total_size = 0
    module_stats = {}

    for module_prefix in wave_1_modules:
        # Find matching module directory
        module_dirs = list(source_root.glob(f"{module_prefix}*"))
        if not module_dirs:
            print(f"⚠️  {module_prefix}: NOT FOUND in source")
            continue

        source_module = module_dirs[0]
        target_module = target_root / source_module.name

        print(f"Extracting: {source_module.name}")

        # Count files in source
        source_files = list(source_module.rglob("*"))
        source_file_count = len([f for f in source_files if f.is_file()])

        # Copy module
        if target_module.exists():
            print(f"  ⚠️  Target exists, removing and re-copying...")
            shutil.rmtree(target_module)

        shutil.copytree(source_module, target_module)

        # Count files in target
        target_files = list(target_module.rglob("*"))
        target_file_count = len([f for f in target_files if f.is_file()])
        target_size = sum(f.stat().st_size for f in target_files if f.is_file())

        module_stats[source_module.name] = {
            "file_count": target_file_count,
            "size_bytes": target_size,
            "source_path": str(source_module),
            "target_path": str(target_module),
        }

        print(f"  ✅ Copied {target_file_count} files ({target_size / 1024:.1f} KB)")

        total_files += target_file_count
        total_size += target_size

    print(f"\n=== Wave 1 Summary ===")
    print(f"Total Modules: {len(module_stats)}")
    print(f"Total Files: {total_files}")
    print(f"Total Size: {total_size / 1024:.1f} KB ({total_size / 1024 / 1024:.2f} MB)")

    # Save inventory
    inventory = {
        "timestamp": datetime.now().isoformat(),
        "wave": 1,
        "modules": module_stats,
        "summary": {
            "total_modules": len(module_stats),
            "total_files": total_files,
            "total_size_bytes": total_size,
        },
    }

    inventory_path = labs_root / "wave_1_inventory.json"
    with open(inventory_path, "w") as f:
        json.dump(inventory, f, indent=2)

    print(f"\n📋 Inventory saved to: {inventory_path}")

    # Generate human-readable report
    report_path = labs_root / "wave_1_extraction_report.txt"
    with open(report_path, "w") as f:
        f.write("WAVE 1 EXTRACTION REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Source: {source_root}\n")
        f.write(f"Target: {target_root}\n\n")

        f.write("MODULE DETAILS\n")
        f.write("-" * 50 + "\n")
        for module_name, stats in module_stats.items():
            f.write(f"\n{module_name}:\n")
            f.write(f"  Files: {stats['file_count']}\n")
            f.write(f"  Size: {stats['size_bytes'] / 1024:.1f} KB\n")
            f.write(f"  Target: {stats['target_path']}\n")

        f.write("\n\nSUMMARY\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total Modules: {len(module_stats)}\n")
        f.write(f"Total Files: {total_files}\n")
        f.write(f"Total Size: {total_size / 1024:.1f} KB\n\n")

        f.write("NEXT STEPS\n")
        f.write("-" * 50 + "\n")
        f.write("1. Run batch translation:\n")
        f.write(
            "   python scripts/batch_translate.py --wave 1 --report wave_1_translation_report.txt\n"
        )
        f.write("\n2. Validate translated content:\n")
        f.write(
            "   python scripts/validate_english_content.py --path modules/module-0{1..6}-* --full\n"
        )
        f.write("\n3. Review translations using QA checklist:\n")
        f.write("   docs/TRANSLATION-QA-CHECKLIST.md\n")

    print(f"📄 Report saved to: {report_path}\n")

    return inventory


if __name__ == "__main__":
    try:
        extract_wave_1()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
