# Checkpoint 01: Serverless Data Lake

## Overview

This checkpoint integrates the concepts from modules 01 to 06 in a single project.
You will build an end-to-end serverless data lake using a layered architecture.

## Learning Objectives

By completing this checkpoint, you will:

- Implement infrastructure as code for a serverless data platform.
- Build ingestion and transformation pipelines.
- Apply data quality validations and acceptance checks.
- Deliver an analytics-ready output for business reporting.

## Prerequisites

You must complete modules 01, 02, 03, 04, 05, and 06 before starting.

## Practice

Use the starter template and complete implementation incrementally:

1. Read `starter-template/README.md`.
2. Follow `starter-template/CHECKLIST.md`.
3. Implement all pending TODO blocks in starter files.
4. Compare only after attempting with `reference-solution/`.

## Validation

Run the checkpoint acceptance tests from this module:

```bash
bash validation/run-tests.sh
```

Also validate module contracts from repository root:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --module module-checkpoint-01-serverless-data-lake --strict-core --strict-headings
```
