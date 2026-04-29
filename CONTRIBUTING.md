# Contributing

## Branches

- Work from `main` using short-lived feature branches.
- Keep one logical change per branch.

## Commits

- Use English commit messages.
- Keep commits focused and small.
- Avoid mixing infrastructure and content changes in the same commit when possible.

## Validation Before Commit

Run from repository root:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --strict-core --strict-headings
$PYTHON scripts/validate_english_content.py
$PYTHON scripts/progress.py
```

## Pull Requests

- Use the PR template.
- Include scope, validation evidence, and risks.
- Do not include unrelated changes.

## Module Authoring Contract

- Before creating or editing modules, read `docs/MODULE-CONTRACT-MATRIX.md`.
- Use `.github/skills/cloud-data-module-standardization/SKILL.md` when normalizing module structure.
- Use `.github/skills/cloud-data-english-standards/SKILL.md` when enforcing language governance.
