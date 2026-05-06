# Checkpoint 02: Real-Time Analytics Platform

## Overview

This checkpoint integrates modules 07 to 12 by implementing a complete
real-time analytics platform with ingestion, processing, orchestration,
and observability.

## Learning Objectives

By completing this checkpoint, you will:

- Build a streaming ingestion path with managed cloud services.
- Implement event processing and stateful analytics components.
- Integrate orchestration and monitoring for operational readiness.
- Validate end-to-end outputs against acceptance criteria.

## Prerequisites

You must complete modules 07, 08, 09, 10, 11, and 12 before starting.

## Practice

Use the starter template as your implementation workspace:

1. Read `starter-template/README.md`.
2. Follow `starter-template/CHECKLIST.md`.
3. Implement required components in phases.
4. Use `reference-solution/` only after your own attempt.

## Validation

Run acceptance tests from this module:

```bash
bash validation/run-tests.sh
```

Also validate module contracts from repository root:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --module module-checkpoint-02-realtime-analytics-platform --strict-core --strict-headings
```
