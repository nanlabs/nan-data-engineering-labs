# AGENTS

## Scope

This file defines agent behavior for this repository.

## Source of Truth

1. Follow this file first.
1. Follow `docs/MODULE-CONTRACT-MATRIX.md` for module structure contracts.
1. Follow `.github/skills/cloud-data-module-standardization/SKILL.md` for normalization workflow.
1. Follow `.github/skills/cloud-data-english-standards/SKILL.md` for language governance.
1. If instructions conflict, prefer this file for agent behavior and SKILL files for content rules.

## Repository Conventions

- Canonical module taxonomy:
  - Regular modules: `modules/module-01-*` to `modules/module-18-*`
  - Checkpoints: `modules/module-checkpoint-01-*` to `modules/module-checkpoint-03-*`
  - Bonus modules: `modules/module-bonus-01-*` to `modules/module-bonus-02-*`
- Language policy:
  - All governance and newly edited instructional content must be English.
  - Existing legacy non-English content should be migrated incrementally.
- Atomic training policy:
  - Every module must expose clear prerequisites, concept objectives, practice path, and validation entrypoints.
  - Module requirements are validated by `scripts/validate_learning_labs.py`.

## Validation Commands

Use project venv explicitly:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --strict-core --strict-headings
$PYTHON scripts/validate_english_content.py
$PYTHON scripts/progress.py
```

## Execution and Reporting Norms

- Verify before claiming completion:
  - For commits/merges: confirm with `git log --oneline -n 1` and `git status --short`.
  - For translation progress: report measured counts (for example with `rg`/validator output), not estimates.
  - For validations: include the exact command run and whether scope was full repo or target module.
- Scope-first translation flow:
  - Populate missing module content before claiming translation progress.
  - Translate target module files first (`README.md`, `theory/`, `exercises/*/{README.md,starter/scenario.md,hints.md}`), then expand scope.
  - If API credentials are missing, use local/manual translation and explicitly mark residual Spanish markers.
- Commit discipline:
  - Keep commits atomic by module or wave.
  - Do not claim "fully translated" unless target-scope validation passes with zero findings.

## Safety

- Do not run destructive git commands (`reset --hard`, `checkout --`) unless explicitly requested.
- Do not revert unrelated user changes.
- Keep changes minimal and scoped to the requested task.
