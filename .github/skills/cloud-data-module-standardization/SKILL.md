---
name: cloud-data-module-standardization
description: Standardize nan-data-engineering-labs modules to the repository contract, enforce module-type structure rules, and validate atomic training readiness.
---

# Cloud Data Module Standardization

Use this skill when the task involves module structure consistency, heading normalization, or contract compliance checks across regular, checkpoint, and bonus modules.

## Inputs

- Target scope:
  - `modules/module-01-*` to `modules/module-18-*`
  - `modules/module-checkpoint-*`
  - `modules/module-bonus-*`
- Reference contract:
  - `docs/MODULE-CONTRACT-MATRIX.md`
- Agent contract:
  - `AGENTS.md`

## Required Workflow

1. Read module README and type-specific folders.
2. Compare current state against `docs/MODULE-CONTRACT-MATRIX.md`.
3. Apply minimal edits to satisfy required files/folders and heading requirements.
4. Keep newly edited instructional content in English.
5. Run validators before finalizing:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --strict-core --strict-headings
$PYTHON scripts/progress.py
```

1. Verify and report outcomes with evidence:

- `git status --short` for changed scope
- validator output summary for targeted modules
- explicit residual issues if any

## Validation Rules

- Regular and checkpoint modules are strict in default mode.
- Bonus modules are validated but can be warning-only in non-strict mode.
- Missing required files in strict mode are failures.
- Missing mandatory README heading groups in strict mode are failures.

## Definition of Done

- Module satisfies required contract for its type.
- Exercise units include required assets.
- Required README heading groups are present.
- Validator returns success for strict mode on targeted scope.
- Status reporting includes verified evidence (not estimates) for the targeted scope.

## Safety

- Do not delete user-authored content unless explicitly requested.
- Preserve existing links when changing headings.
- Avoid formatting-only changes in unrelated files.
