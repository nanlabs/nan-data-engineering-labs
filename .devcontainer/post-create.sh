#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing Python dependencies"
python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt

echo "==> Installing pre-commit hooks"
pre-commit install || true

echo "==> Done. Run: make up"
