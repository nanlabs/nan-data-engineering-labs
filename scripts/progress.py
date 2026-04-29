#!/usr/bin/env python3
"""
Track and display learning progress across all modules.

Scans completed exercises and generates progress report.
"""

from pathlib import Path
from typing import Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent

# Module metadata from generate_structure.py
MODULES_METADATA = {
    "01": {"name": "cloud-fundamentals", "type": "regular", "prereqs": []},
    "02": {"name": "storage-basics", "type": "regular", "prereqs": []},
    "03": {"name": "sql-foundations", "type": "regular", "prereqs": []},
    "04": {"name": "python-for-data", "type": "regular", "prereqs": []},
    "05": {"name": "data-lakehouse-architecture", "type": "regular", "prereqs": ["02"]},
    "06": {"name": "etl-fundamentals", "type": "regular", "prereqs": ["02", "04"]},
    "checkpoint-01": {"name": "serverless-data-lake", "type": "checkpoint", "prereqs": ["01", "02", "03", "04", "05", "06"]},
    "07": {"name": "batch-processing", "type": "regular", "prereqs": ["02", "04", "05"]},
    "08": {"name": "streaming-basics", "type": "regular", "prereqs": ["04", "06"]},
    "09": {"name": "data-quality", "type": "regular", "prereqs": ["04", "06"]},
    "10": {"name": "workflow-orchestration", "type": "regular", "prereqs": ["06"]},
    "11": {"name": "infrastructure-as-code", "type": "regular", "prereqs": ["01", "02"]},
    "12": {"name": "serverless-processing", "type": "regular", "prereqs": ["06", "11"]},
    "checkpoint-02": {"name": "realtime-analytics-platform", "type": "checkpoint", "prereqs": ["07", "08", "09", "10", "11", "12"]},
    "13": {"name": "container-orchestration", "type": "regular", "prereqs": ["11"]},
    "14": {"name": "data-catalog-governance", "type": "regular", "prereqs": ["05", "09"]},
    "15": {"name": "real-time-analytics", "type": "regular", "prereqs": ["08", "10"], "parallel": "A"},
    "16": {"name": "data-security-compliance", "type": "regular", "prereqs": ["01", "14"], "parallel": "B"},
    "17": {"name": "cost-optimization", "type": "regular", "prereqs": ["11"], "parallel": "C"},
    "18": {"name": "advanced-architectures", "type": "regular", "prereqs": ["05", "07", "08", "14"]},
    "checkpoint-03": {"name": "enterprise-data-lakehouse", "type": "checkpoint", "prereqs": ["13", "14", "15", "16", "17", "18"]},
    "bonus-01": {"name": "databricks-lakehouse", "type": "bonus", "prereqs": ["05", "07"]},
    "bonus-02": {"name": "snowflake-data-cloud", "type": "bonus", "prereqs": ["03", "06"]},
}


def count_exercises(module_path: Path) -> Tuple[int, int]:
    """Count total and completed exercises in a module."""
    exercises_dir = module_path / "exercises"
    if not exercises_dir.exists():
        return 0, 0

    total = 0
    completed = 0

    # Count exercise directories
    for item in exercises_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            total += 1

            # Check if my_solution exists and has files
            my_solution = item / "my_solution"
            if my_solution.exists():
                solution_files = list(my_solution.glob('**/*'))
                solution_files = [f for f in solution_files if f.is_file() and f.name != '.gitkeep']
                if solution_files:
                    completed += 1

    return total, completed


def calculate_module_completion(module_path: Path) -> int:
    """Calculate completion percentage for a module."""
    total, completed = count_exercises(module_path)
    if total == 0:
        return 0
    return int((completed / total) * 100)


def check_prerequisites_met(module_id: str, completion_status: Dict[str, int]) -> bool:
    """Check if all prerequisites for a module are met (100% complete)."""
    metadata = MODULES_METADATA.get(module_id, {})
    prereqs = metadata.get("prereqs", [])

    if not prereqs:
        return True

    for prereq in prereqs:
        if completion_status.get(prereq, 0) < 100:
            return False

    return True


def generate_progress_report():
    """Generate and display progress report."""
    modules_dir = PROJECT_ROOT / "modules"

    if not modules_dir.exists():
        print("❌ Modules directory not found")
        return

    print("\n" + "="*70)
    print("📊 CLOUD DATA ENGINEERING - LEARNING PROGRESS")
    print("="*70 + "\n")

    completion_status = {}

    # Regular modules
    print("🎯 FOUNDATION & CORE MODULES")
    print("-" * 70)

    for module_id in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]:
        metadata = MODULES_METADATA[module_id]
        module_folder = f"module-{module_id}-{metadata['name']}"
        module_path = modules_dir / module_folder

        if module_path.exists():
            completion = calculate_module_completion(module_path)
            completion_status[module_id] = completion
            prereqs_met = check_prerequisites_met(module_id, completion_status)

            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
            ready_icon = "🔓" if prereqs_met else "🔒"

            parallel_info = f" [Track {metadata.get('parallel', '')}]" if 'parallel' in metadata else ""
            print(f"{status_icon} {ready_icon} Module {module_id}: {metadata['name'].replace('-', ' ').title():40} {completion:3}%{parallel_info}")

    # Checkpoint 1
    print("\n🏁 CHECKPOINT 1")
    print("-" * 70)
    checkpoint_id = "checkpoint-01"
    metadata = MODULES_METADATA[checkpoint_id]
    module_folder = f"module-{checkpoint_id}-{metadata['name']}"
    module_path = modules_dir / module_folder

    if module_path.exists():
        completion = calculate_module_completion(module_path)
        completion_status[checkpoint_id] = completion
        prereqs_met = check_prerequisites_met(checkpoint_id, completion_status)

        status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
        ready_icon = "🔓" if prereqs_met else "🔒"

        print(f"{status_icon} {ready_icon} Checkpoint 01: {metadata['name'].replace('-', ' ').title():38} {completion:3}%")
        if not prereqs_met:
            print(f"   ⚠️  Requires modules: {', '.join(metadata['prereqs'])}")

    # Cloud-Native modules
    print("\n☁️  CLOUD-NATIVE MODULES")
    print("-" * 70)

    for module_id in ["11", "12", "13", "14"]:
        metadata = MODULES_METADATA[module_id]
        module_folder = f"module-{module_id}-{metadata['name']}"
        module_path = modules_dir / module_folder

        if module_path.exists():
            completion = calculate_module_completion(module_path)
            completion_status[module_id] = completion
            prereqs_met = check_prerequisites_met(module_id, completion_status)

            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
            ready_icon = "🔓" if prereqs_met else "🔒"

            print(f"{status_icon} {ready_icon} Module {module_id}: {metadata['name'].replace('-', ' ').title():40} {completion:3}%")

    # Checkpoint 2
    print("\n🏁 CHECKPOINT 2")
    print("-" * 70)
    checkpoint_id = "checkpoint-02"
    metadata = MODULES_METADATA[checkpoint_id]
    module_folder = f"module-{checkpoint_id}-{metadata['name']}"
    module_path = modules_dir / module_folder

    if module_path.exists():
        completion = calculate_module_completion(module_path)
        completion_status[checkpoint_id] = completion
        prereqs_met = check_prerequisites_met(checkpoint_id, completion_status)

        status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
        ready_icon = "🔓" if prereqs_met else "🔒"

        print(f"{status_icon} {ready_icon} Checkpoint 02: {metadata['name'].replace('-', ' ').title():38} {completion:3}%")
        if not prereqs_met:
            print(f"   ⚠️  Requires modules: {', '.join(metadata['prereqs'])}")

    # Advanced modules
    print("\n🚀 ADVANCED MODULES")
    print("-" * 70)

    for module_id in ["15", "16", "17", "18"]:
        metadata = MODULES_METADATA[module_id]
        module_folder = f"module-{module_id}-{metadata['name']}"
        module_path = modules_dir / module_folder

        if module_path.exists():
            completion = calculate_module_completion(module_path)
            completion_status[module_id] = completion
            prereqs_met = check_prerequisites_met(module_id, completion_status)

            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
            ready_icon = "🔓" if prereqs_met else "🔒"

            parallel_info = f" [Parallel Track {metadata.get('parallel', '')}]" if 'parallel' in metadata else ""
            print(f"{status_icon} {ready_icon} Module {module_id}: {metadata['name'].replace('-', ' ').title():40} {completion:3}%{parallel_info}")

    # Checkpoint 3
    print("\n🏁 CHECKPOINT 3 (FINAL)")
    print("-" * 70)
    checkpoint_id = "checkpoint-03"
    metadata = MODULES_METADATA[checkpoint_id]
    module_folder = f"module-{checkpoint_id}-{metadata['name']}"
    module_path = modules_dir / module_folder

    if module_path.exists():
        completion = calculate_module_completion(module_path)
        completion_status[checkpoint_id] = completion
        prereqs_met = check_prerequisites_met(checkpoint_id, completion_status)

        status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
        ready_icon = "🔓" if prereqs_met else "🔒"

        print(f"{status_icon} {ready_icon} Checkpoint 03: {metadata['name'].replace('-', ' ').title():38} {completion:3}%")
        if not prereqs_met:
            print(f"   ⚠️  Requires modules: {', '.join(metadata['prereqs'])}")

    # Bonus modules
    print("\n🎁 BONUS MODULES (Optional)")
    print("-" * 70)

    for module_id in ["bonus-01", "bonus-02"]:
        metadata = MODULES_METADATA[module_id]
        module_folder = f"module-{module_id}-{metadata['name']}"
        module_path = modules_dir / module_folder

        if module_path.exists():
            completion = calculate_module_completion(module_path)
            completion_status[module_id] = completion
            prereqs_met = check_prerequisites_met(module_id, completion_status)

            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "⬜"
            ready_icon = "🔓" if prereqs_met else "🔒"

            print(f"{status_icon} {ready_icon} Bonus {module_id}: {metadata['name'].replace('-', ' ').title():38} {completion:3}%")

    # Overall statistics
    print("\n" + "="*70)
    print("📈 OVERALL STATISTICS")
    print("="*70)

    total_modules = len([m for m in MODULES_METADATA.values() if m['type'] == 'regular'])
    completed_modules = len([m for m, c in completion_status.items() if MODULES_METADATA[m]['type'] == 'regular' and c == 100])

    total_checkpoints = len([m for m in MODULES_METADATA.values() if m['type'] == 'checkpoint'])
    completed_checkpoints = len([m for m, c in completion_status.items() if MODULES_METADATA[m]['type'] == 'checkpoint' and c == 100])

    print(f"\n   Regular Modules:  {completed_modules}/{total_modules} completed")
    print(f"   Checkpoints:      {completed_checkpoints}/{total_checkpoints} completed")

    overall_completion = int((completed_modules / total_modules) * 100) if total_modules > 0 else 0
    print(f"\n   Overall Progress: {overall_completion}%")

    # Progress bar
    bar_length = 50
    filled = int(bar_length * overall_completion / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"   [{bar}] {overall_completion}%")

    print("\n" + "="*70)
    print("\n💡 Legend:")
    print("   ✅ = Completed (100%)    🔄 = In Progress    ⬜ = Not Started")
    print("   🔓 = Ready to Start      🔒 = Prerequisites Required")
    print("\n")

    # Next recommended module
    for module_id in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18"]:
        completion = completion_status.get(module_id, 0)
        if completion < 100 and check_prerequisites_met(module_id, completion_status):
            metadata = MODULES_METADATA[module_id]
            module_folder = f"module-{module_id}-{metadata['name']}"
            print(f"🎯 Next Recommended: Module {module_id} - {metadata['name'].replace('-', ' ').title()}")
            print(f"   cd modules/{module_folder}")
            break


if __name__ == "__main__":
    generate_progress_report()
