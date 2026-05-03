# Copilot Instructions

## Scope

This file defines repository-specific Copilot guidance for `nan-data-engineering-labs`.

## Routing

- For module structure normalization tasks, use `.github/skills/cloud-data-module-standardization/SKILL.md`.
- For language governance tasks, use `.github/skills/cloud-data-english-standards/SKILL.md`.
- For review requests, prefer the agents under `.github/agents/`.

## Guardrails

- Keep all new governance and instructional content in English.
- Preserve user-authored content unless the task explicitly requests migration.
- Do not widen scope beyond requested modules/files.
- Prefer minimal, auditable changes.

## Execution Norms

- Confirm outcomes before reporting them:
	- Check `git status --short` and `git log --oneline -n 1` before claiming commit/merge completion.
	- Report measured translation deltas only (counts from validator/search output).
- Translation workflow order:
	- Ensure target module content exists before translating.
	- Translate high-impact learning files first: `README.md`, `theory/*.md`, and `exercises/*/{README.md,starter/scenario.md,hints.md}`.
	- If no translation API key is available, continue with local/manual pass and explicitly report remaining markers.
- "Done" criteria for a module translation task:
	- Target module validation command executed.
	- Zero findings for the target module scope, or explicit residual list if not complete.

## Validation

Before finalizing changes, run:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --strict-core --strict-headings
$PYTHON scripts/validate_english_content.py
```
