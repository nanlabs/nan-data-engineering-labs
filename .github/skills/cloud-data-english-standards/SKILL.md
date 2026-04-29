---
name: cloud-data-english-standards
description: Enforce English-only governance for nan-data-engineering-labs instructional and governance assets, and report non-compliant lines with clear remediation guidance.
---

# Cloud Data English Standards

Use this skill when reviewing or normalizing language compliance in governance docs, module docs, and instructional code comments.

## Inputs

- Target scope: repository files under `AGENTS.md`, `.github/`, `docs/`, `modules/`, `scripts/`, and `shared/`.
- Validation script: `scripts/validate_english_content.py`.
- Contract source: `AGENTS.md`.

## Required Workflow

1. Identify modified or target files.
2. Run language validation script.
3. Fix non-English instructional content in scoped files.
4. Re-run validation and confirm zero findings.

```bash
PYTHON=python
$PYTHON scripts/validate_english_content.py
```

## Rules

- Keep governance and instructional content in English.
- Allow domain terminology and acronyms (for example AWS, IAM, S3, ETL, ELT, SQL, API).
- Avoid introducing bilingual sections in the same file.

## Definition of Done

- No disallowed non-English markers in scoped files.
- New comments/docstrings/instructions are English-only.
- Validator reports success.

## Safety

- Do not rewrite large legacy documents unless requested.
- Prefer scoped remediation to changed or target files.
