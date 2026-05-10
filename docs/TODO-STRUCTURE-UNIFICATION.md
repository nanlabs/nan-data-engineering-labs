# TODO: Module Structure Unification

## Execution Tracker (Current)

Current step: **Post-contract stabilization**, preparing next quality wave.

### Completed

- [x] Add missing `starter/` and `solution/` exercise assets in Module 07.
- [x] Add missing `solution/` asset for
  `module-02-storage-basics/exercises/04-compression-optimization`.
- [x] Add missing `starter/` and `solution/` exercise assets in Module 06.
- [x] Add missing `starter/` and `solution/` exercise assets in
  Modules 08-18 and bonus modules.
- [x] Pass strict contract validation with:
  - `python scripts/validate_learning_labs.py --strict-core --strict-headings`

### In Progress

- [ ] Consolidate follow-up quality tasks now that structure contract is green.

### Next Steps

- [ ] Run and record full governance checks:
  - `python scripts/validate_english_content.py`
  - `python scripts/progress.py`
- [ ] Replace placeholder starter/solution notes with exercise-specific
  implementation guidance where needed.
- [ ] Define the next wave (content quality, test depth, and consistency
  hardening) and execute in atomic commits.

Goal: keep module structure predictable so learners can transfer navigation habits across all modules.

## Current Drift Detected

- Regular modules are not fully uniform:
  - `module-01` to `module-05` contain `docs/` while most regular modules do not.
  - `module-10` contains `dags/` while other regular modules do not.
  - `module-05` contains `venv/` (should not be a module subfolder).
- Checkpoint modules include `extensions/` which is not listed in required or optional matrix.
- Some modules may still include legacy placeholder content;
  verify current state before cleanup.

## Decisions Required

- [ ] Decide regular-module baseline for `docs/`:
  - Option A: required for all regular modules.
  - Option B: remove from modules 01-05.
- [ ] Decide policy for `dags/` in module 10:
  - Option A: allow only module-specific extension (documented exception).
  - Option B: standardize in all orchestration-related modules.
- [ ] Remove `venv/` from `module-05-data-lakehouse`.
- [ ] Decide policy for checkpoint `extensions/`:
  - Option A: add as optional in contract matrix.
  - Option B: remove from checkpoints.

## Contract and Automation

- [ ] Update `docs/MODULE-CONTRACT-MATRIX.md` with approved optional
  folders by module type.
- [ ] Update `scripts/validate_learning_labs.py` to fail on unapproved extras.
- [ ] Add exception list support (if needed) for module-specific justified folders.
- [ ] Run `python scripts/validate_learning_labs.py --strict-core
  --strict-headings` and verify expected output is clean
  after content migration.

## Skills and Agent Alignment

- [ ] Use `nanlabs-assistant` for workflow guardrails.
- [ ] Use `planner` for wave planning and dependency sequencing.
- [ ] Use `code-reviewer` after each migration wave.
- [ ] Use `security-reviewer` for scripts and CI changes.
- [ ] Use `build-error-resolver` if validator or CI checks fail.
- [ ] Confirm `nan-skills check` passes once `clickup` and `glab` are installed.
