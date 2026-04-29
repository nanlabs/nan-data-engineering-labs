#!/usr/bin/env python3
"""
Generate complete Cloud Data Engineering module structure.

This script creates all 23 modules (18 regular + 3 checkpoints + 2 bonus)
with the appropriate folder structure based on module type.
"""

from pathlib import Path
from typing import Dict

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Module definitions with dependencies
MODULES = [
    # Foundation Tier (No prerequisites)
    {"id": "01", "name": "cloud-fundamentals", "type": "regular", "prerequisites": []},
    {"id": "02", "name": "storage-basics", "type": "regular", "prerequisites": []},
    {"id": "03", "name": "sql-foundations", "type": "regular", "prerequisites": []},
    {"id": "04", "name": "python-for-data", "type": "regular", "prerequisites": []},

    # Core Tier
    {"id": "05", "name": "data-lakehouse-architecture", "type": "regular", "prerequisites": ["02"]},
    {"id": "06", "name": "etl-fundamentals", "type": "regular", "prerequisites": ["02", "04"]},

    # Checkpoint 01 - Serverless Data Lake
    {"id": "checkpoint-01", "name": "serverless-data-lake", "type": "checkpoint", "prerequisites": ["01", "02", "03", "04", "05", "06"]},

    # Core Tier Continued
    {"id": "07", "name": "batch-processing", "type": "regular", "prerequisites": ["02", "04", "05"]},
    {"id": "08", "name": "streaming-basics", "type": "regular", "prerequisites": ["04", "06"]},
    {"id": "09", "name": "data-quality", "type": "regular", "prerequisites": ["04", "06"]},
    {"id": "10", "name": "workflow-orchestration", "type": "regular", "prerequisites": ["06"]},

    # Cloud-Native Tier
    {"id": "11", "name": "infrastructure-as-code", "type": "regular", "prerequisites": ["01", "02"]},
    {"id": "12", "name": "serverless-processing", "type": "regular", "prerequisites": ["06", "11"]},

    # Checkpoint 02 - Real-time Analytics Platform
    {"id": "checkpoint-02", "name": "realtime-analytics-platform", "type": "checkpoint", "prerequisites": ["07", "08", "09", "10", "11", "12"]},

    # Cloud-Native Continued
    {"id": "13", "name": "container-orchestration", "type": "regular", "prerequisites": ["11"]},
    {"id": "14", "name": "data-catalog-governance", "type": "regular", "prerequisites": ["05", "09"]},

    # Advanced Tier (Parallel tracks - no mutual dependencies)
    {"id": "15", "name": "real-time-analytics", "type": "regular", "prerequisites": ["08", "10"], "parallel_track": "A"},
    {"id": "16", "name": "data-security-compliance", "type": "regular", "prerequisites": ["01", "14"], "parallel_track": "B"},
    {"id": "17", "name": "cost-optimization", "type": "regular", "prerequisites": ["11"], "parallel_track": "C"},
    {"id": "18", "name": "advanced-architectures", "type": "regular", "prerequisites": ["05", "07", "08", "14"]},

    # Checkpoint 03 - Enterprise Data Lakehouse
    {"id": "checkpoint-03", "name": "enterprise-data-lakehouse", "type": "checkpoint", "prerequisites": ["13", "14", "15", "16", "17", "18"]},

    # Bonus Modules (Optional)
    {"id": "bonus-01", "name": "databricks-lakehouse", "type": "bonus", "prerequisites": ["05", "07"]},
    {"id": "bonus-02", "name": "snowflake-data-cloud", "type": "bonus", "prerequisites": ["03", "06"]},
]


def create_regular_module_structure(module_path: Path):
    """Create folder structure for a regular learning module."""
    folders = [
        "theory",
        "exercises",
        "infrastructure",
        "data/sample",
        "data/schemas",
        "validation/data-quality",
        "validation/integration",
        "validation/infrastructure",
        "validation/query-results",
        "scripts",
        "assets/diagrams",
    ]

    for folder in folders:
        (module_path / folder).mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to preserve empty folders
        (module_path / folder / ".gitkeep").touch()


def create_checkpoint_structure(module_path: Path):
    """Create folder structure for a checkpoint project."""
    folders = [
        "architecture",
        "starter-template/infrastructure",
        "starter-template/pipelines",
        "starter-template/sql",
        "starter-template/config",
        "reference-solution/infrastructure",
        "reference-solution/pipelines",
        "reference-solution/sql",
        "reference-solution/config",
        "data/input",
        "data/expected-output",
        "data/generators",
        "validation/acceptance-tests",
        "extensions",
    ]

    for folder in folders:
        (module_path / folder).mkdir(parents=True, exist_ok=True)
        (module_path / folder / ".gitkeep").touch()


def create_bonus_module_structure(module_path: Path):
    """Create folder structure for bonus modules (cloud-managed platforms)."""
    folders = [
        "theory",
        "notebooks",
        "exercises",
        "data/sample",
        "validation",
        "scripts",
        "assets",
    ]

    for folder in folders:
        (module_path / folder).mkdir(parents=True, exist_ok=True)
        (module_path / folder / ".gitkeep").touch()


def create_module_readme(module_path: Path, module: Dict):
    """Create README.md for a module."""
    module_id = module["id"]
    module_name = module["name"].replace("-", " ").title()
    module_type = module["type"]

    if module_type == "regular":
        content = f"""# Module {module_id}: {module_name}

⏱️ **Estimated Time:** TBD hours

## Prerequisites

"""
        if module.get("prerequisites"):
            for prereq in module["prerequisites"]:
                content += f"- ✅ Module {prereq} must be completed (100%)\n"
        else:
            content += "- None - This is a foundation module\n"

        if module.get("parallel_track"):
            content += f"\n**Note:** This module is part of parallel track {module['parallel_track']} and can be completed alongside other parallel modules.\n"

        content += """

## Module Overview

[Brief description of what you'll learn in this module]

## Learning Objectives

By the end of this module, you will be able to:

- [ ] Objective 1
- [ ] Objective 2
- [ ] Objective 3

## Structure

- **theory/**: Core concepts and architecture documentation
- **exercises/**: Hands-on practice exercises (6 exercises)
- **infrastructure/**: LocalStack/Docker setup for this module
- **data/**: Sample datasets and schemas
- **validation/**: Automated tests to validate your learning
- **scripts/**: Helper scripts

## Getting Started

1. Ensure prerequisites are completed
2. Read `theory/concepts.md` for foundational understanding
3. Review `theory/architecture.md` for AWS architecture patterns
4. Set up infrastructure: `bash scripts/setup.sh`
5. Complete exercises in order (01 through 06)
6. Validate your learning: `bash scripts/validate.sh`

## Exercises

1. **Exercise 01**: [Title] - Basic concepts
2. **Exercise 02**: [Title] - Intermediate application
3. **Exercise 03**: [Title] - Advanced usage
4. **Exercise 04**: [Title] - Integration patterns
5. **Exercise 05**: [Title] - Performance optimization
6. **Exercise 06**: [Title] - Production best practices

## Resources

See `theory/resources.md` for:
- Official AWS documentation
- Video tutorials and workshops
- Community resources
- Certification mapping

## Validation

Run all validations:
```bash
bash scripts/validate.sh
```

Or use the global validation:
```bash
make validate MODULE=module-{module_id}-{module["name"]}
```

## Progress Checklist

- [ ] Read all theory documentation
- [ ] Completed Exercise 01
- [ ] Completed Exercise 02
- [ ] Completed Exercise 03
- [ ] Completed Exercise 04
- [ ] Completed Exercise 05
- [ ] Completed Exercise 06
- [ ] All validations passing
- [ ] Ready for next module

## Next Steps

After completing this module, you'll be ready for:
[List of modules that depend on this one]
"""

    elif module_type == "checkpoint":
        content = f"""# Checkpoint {module_id}: {module_name}

🎯 **Project Type:** Integration Checkpoint
⏱️ **Estimated Time:** TBD hours

## Prerequisites

**Required Modules (Must be 100% complete):**
"""
        for prereq in module.get("prerequisites", []):
            content += f"- ✅ Module {prereq}\n"

        content += """

## Project Overview

[Description of the business scenario and technical challenge]

## Success Criteria

You will complete this checkpoint when:

- [ ] All acceptance tests pass
- [ ] Infrastructure deploys successfully
- [ ] Data pipeline produces expected outputs
- [ ] Data quality validations pass
- [ ] Architecture matches requirements
- [ ] Self-assessment rubric is completed

## Architecture

See `architecture/` folder for:
- Target architecture diagrams (Mermaid)
- Data flow diagrams
- Design decisions documentation

## Project Structure

- **starter-template/**: Scaffold to get you started
- **reference-solution/**: Complete reference implementation
- **data/**: Input data and expected outputs
- **validation/**: Automated acceptance tests
- **extensions/**: Optional advanced challenges

## Getting Started

1. Review project brief: `PROJECT-BRIEF.md`
2. Study target architecture: `architecture/`
3. Read implementation guide: `IMPLEMENTATION-GUIDE.md`
4. Copy starter template to your workspace
5. Implement solution incrementally
6. Run acceptance tests frequently
7. Complete self-assessment rubric

## Implementation Approach

See `IMPLEMENTATION-GUIDE.md` for step-by-step guidance on:
- Setting up infrastructure
- Building data pipelines
- Implementing transformations
- Adding data quality checks
- Testing and validation

## Validation

Run acceptance tests:
```bash
bash validation/run-tests.sh
```

## Certification Bonus

See `validation/certification-practice-questions.md` for exam-style questions related to this project.

## Self-Assessment

Complete `validation/rubric.md` to evaluate your solution against industry standards.
"""

    else:  # bonus
        content = f"""# Bonus Module {module_id}: {module_name}

🎁 **Type:** Optional Bonus Module
☁️ **Platform:** Cloud-Managed Service
⏱️ **Estimated Time:** TBD hours

## Prerequisites

"""
        if module.get("prerequisites"):
            for prereq in module["prerequisites"]:
                content += f"- Module {prereq}\n"

        content += """

## ⚠️ Important Notes

- This module uses a **cloud-managed platform** with trial limitations
- Review `COST-ALERT.md` for pricing and free tier details
- Not required for core learning path
- Complements AWS knowledge with alternative platform

## Module Overview

[Description of the platform and what you'll learn]

## Getting Started

1. Review cost considerations: `COST-ALERT.md`
2. Set up account (see `theory/setup-guide.md`)
3. Complete notebooks/exercises
4. Explore platform features

## Structure

- **theory/**: Platform concepts and setup
- **notebooks/**: Interactive tutorials
- **exercises/**: Practice problems
- **validation/**: Self-assessment

## Resources

See `theory/resources.md` for platform-specific documentation and tutorials.
"""

    (module_path / "README.md").write_text(content)


def generate_all_modules():
    """Generate all module structures."""
    modules_dir = PROJECT_ROOT / "modules"
    modules_dir.mkdir(exist_ok=True)

    print("🚀 Generating Cloud Data Engineering module structure...\n")

    for module in MODULES:
        module_folder = f"module-{module['id']}-{module['name']}"
        module_path = modules_dir / module_folder

        print(f"📁 Creating {module_folder}...")
        module_path.mkdir(exist_ok=True)

        # Create appropriate structure based on type
        if module["type"] == "regular":
            create_regular_module_structure(module_path)
        elif module["type"] == "checkpoint":
            create_checkpoint_structure(module_path)
        else:  # bonus
            create_bonus_module_structure(module_path)

        # Create README
        create_module_readme(module_path, module)

        print(f"   ✓ {module['type'].capitalize()} module structure created")

    print(f"\n✅ Successfully generated {len(MODULES)} modules!")
    print(f"   - Regular modules: {sum(1 for m in MODULES if m['type'] == 'regular')}")
    print(f"   - Checkpoints: {sum(1 for m in MODULES if m['type'] == 'checkpoint')}")
    print(f"   - Bonus modules: {sum(1 for m in MODULES if m['type'] == 'bonus')}")
    print(f"\n📂 Location: {modules_dir}")


if __name__ == "__main__":
    generate_all_modules()
