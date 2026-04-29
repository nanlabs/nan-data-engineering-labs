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

## Validation

Before finalizing changes, run:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --strict-core --strict-headings
$PYTHON scripts/validate_english_content.py
```
