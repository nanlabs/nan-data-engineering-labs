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
2. Run language validation script and capture baseline counts.
3. Fix non-English instructional content in scoped files.
4. Re-run validation and compare baseline vs current counts.
5. Confirm zero findings for target scope before claiming completion.

```bash
PYTHON=python
$PYTHON scripts/validate_english_content.py
```

## Rules

- Keep governance and instructional content in English.
- Allow domain terminology and acronyms (for example AWS, IAM, S3, ETL, ELT, SQL, API).
- Avoid introducing bilingual sections in the same file.
- Do not report "fully translated" unless validation confirms zero findings in the declared scope.
- If full zero is not achieved, report residual markers and next remediation slice.

## Definition of Done

- No disallowed non-English markers in scoped files.
- New comments/docstrings/instructions are English-only.
- Validator reports success.
- Report includes: baseline count, final count, and exact validated scope.

## Safety

- Do not rewrite large legacy documents unless requested.
- Prefer scoped remediation to changed or target files.
