# Getting Started -- Cloud Data Engineering Labs

## What this program is

A self-guided, progressive learning system that teaches you **Cloud Data Engineering** with AWS through hands-on exercises. 23 modules covering data lakehouses, ETL pipelines, streaming analytics, and cloud-native architectures. Everything runs locally via Docker and LocalStack at zero cost.

## Prerequisites

- `git` installed
- **Docker and Docker Compose** (for LocalStack, Kafka, Spark, etc.)
- **Python 3.9+** (for scripts and data processing)
- One of:
  - **DevContainer-capable IDE** (VS Code, Cursor, GitHub Codespaces) -- recommended
  - Local Python environment with `pip`/`venv`
- **10 GB disk space** for Docker images and datasets
- **8 GB RAM** minimum for running services

## Setup

### Option A -- DevContainer (recommended)

```bash
git clone git@github.com:nanlabs/nan-data-engineering-labs.git
cd nan-data-engineering-labs
code .
# Command Palette -> "Dev Containers: Reopen in Container"
```

The DevContainer pre-installs Python, dependencies, pre-commit hooks, and Docker-in-Docker support.

### Option B -- Local

```bash
git clone git@github.com:nanlabs/nan-data-engineering-labs.git
cd nan-data-engineering-labs

python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate            # Windows

pip install -r requirements.txt
pre-commit install
```

## First run

```bash
# Start local services (LocalStack, Kafka, Spark, PostgreSQL, Trino, MinIO)
make up

# Check learning progress
make progress

# Validate module structure
python scripts/validate_learning_labs.py --strict-core --strict-headings
```

You should see all 23 modules listed and the service stack running.

## How to study a module

```text
1. Read   modules/module-NN-topic/README.md
2. Read   theory/concepts.md and theory/architecture.md
3. Inspect sample data in data/
4. Solve  exercises sequentially (01, 02, ...)
5. Use    hints.md (3 progressive levels) when stuck
6. Compare with solution/ after completing
7. Run    validation (scripts/validate.sh or make validate MODULE=...)
```

## Validation

Each module includes automated validation. Run from root:

```bash
# Validate a specific module
make validate MODULE=module-01-cloud-fundamentals

# Validate all modules
python scripts/validate_learning_labs.py --strict-core --strict-headings
```

## Learning path

See [LEARNING-PATH.md](LEARNING-PATH.md) for the full dependency-based progression from foundation to advanced topics.

## Help

- Read [`AGENTS.md`](AGENTS.md) before asking AI to modify the repo.
- Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a PR.
- Check [docs/troubleshooting.md](docs/troubleshooting.md) for common issues.
- File issues for content gaps; PRs welcome for improvements.
