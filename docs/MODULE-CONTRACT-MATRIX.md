# Module Contract Matrix

This document defines the required and optional structure for each module type in `nan-data-engineering-labs`.

## Goals

- Keep module design atomic by concept.
- Keep progression explicit and verifiable.
- Keep quality checks objective and automatable.

## Contract by Module Type

| Module Type | Required Files and Folders | Optional Files and Folders |
| --- | --- | --- |
| Regular | `README.md`, `STATUS.md`, `theory/`, `exercises/`, `validation/`, `scripts/`, `data/` | `assets/`, `infrastructure/`, `requirements.txt` |
| Checkpoint | `README.md`, `starter-template/`, `reference-solution/`, `validation/`, `docs/`, `architecture/`, `data/` | `scripts/`, `requirements.txt`, `assets/` |
| Bonus | `README.md`, `theory/`, `exercises/`, `validation/`, `scripts/`, `data/`, `notebooks/` | `assets/`, `infrastructure/`, `requirements.txt` |

## Exercise Unit Contract

Every exercise directory under `exercises/` must include:

- `README.md`
- `hints.md`
- `starter/`
- `solution/`
- `my_solution/`

## Required README Headings

Core module README headings must include at least:

1. `Overview` or `Objective`
2. `Learning Objectives`
3. `Prerequisites`
4. `Exercises` or `Practice`
5. `Validation` or `Success Criteria`

## Atomic Training Criteria

A module is considered atomically trainable when all conditions hold:

1. It defines explicit concept boundaries and prerequisites.
2. It exposes at least one progressive practice path.
3. It exposes at least one verification entrypoint.
4. It can be validated with repository scripts.

## Validation Tooling

- `scripts/validate_learning_labs.py` validates structure and heading contracts.
- `scripts/validate_english_content.py` validates English-only governance in scoped files.
- `scripts/progress.py` reports progression and dependency unlock status.
