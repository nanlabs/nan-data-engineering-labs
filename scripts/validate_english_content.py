#!/usr/bin/env python3
"""Validate English-only governance content for nan-data-engineering-labs.

Default scope is governance and automation assets. Use --full-scan to inspect
all documentation and module content.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCOPE = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    ".github",
    "docs/MODULE-CONTRACT-MATRIX.md",
    "scripts/validate_learning_labs.py",
)

FULL_SCAN_SCOPE = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    ".github",
    "docs",
    "modules",
    "scripts",
    "shared",
    "README.md",
)

ALLOWED_SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml", ".txt"}

SPANISH_MARKERS = [
    "modulo",
    "modulos",
    "modulo",
    "descripcion",
    "objetivo",
    "objetivos",
    "aprendizaje",
    "ejercicio",
    "ejercicios",
    "prerrequisito",
    "prerrequisitos",
    "resumen",
    "conclusion",
    "siguiente",
    "paso",
    "pasos",
    "configuracion",
    "entorno",
    "guia",
    "inicio",
    "validacion",
    "progreso",
    "bloqueante",
    "nivel",
    "modulo",
    "que",
    "vas a",
    "aprender",
    "ruta",
]

ACCENTED_SPANISH = re.compile(
    r"[\u00E1\u00E9\u00ED\u00F3\u00FA\u00F1"
    r"\u00C1\u00C9\u00CD\u00D3\u00DA\u00D1]"
)

MARKER_PATTERNS = [
    re.compile(rf"\b{re.escape(marker)}\b", re.IGNORECASE)
    for marker in SPANISH_MARKERS
]


@dataclass
class Finding:
    path: Path
    line_number: int
    marker: str
    line: str


def iter_candidate_files(scope_entries: Sequence[str]) -> Iterable[Path]:
    for entry in scope_entries:
        path = ROOT / entry
        if not path.exists():
            continue

        if path.is_file() and path.suffix in ALLOWED_SUFFIXES:
            yield path
            continue

        if path.is_dir():
            for file_path in path.rglob("*"):
                if not file_path.is_file():
                    continue
                if ".git" in file_path.parts:
                    continue
                if file_path.suffix in ALLOWED_SUFFIXES:
                    yield file_path


def detect_marker(line_lower: str) -> str | None:
    for pattern in MARKER_PATTERNS:
        match = pattern.search(line_lower)
        if match:
            return match.group(0)
    return None


def scan_file(file_path: Path) -> List[Finding]:
    findings: List[Finding] = []

    try:
        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()
    except OSError:
        return findings

    for idx, line in enumerate(content, start=1):
        line_lower = line.lower()

        marker = detect_marker(line_lower)
        if marker:
            findings.append(Finding(file_path, idx, marker, line.strip()))
            continue

        if ACCENTED_SPANISH.search(line):
            findings.append(
                Finding(file_path, idx, "accented_spanish", line.strip())
            )

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate English-only content in scoped files"
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help=(
            "Scan full repository instructional scope, "
            "including modules and docs."
        ),
    )
    return parser


def print_report(findings: Sequence[Finding], full_scan: bool) -> None:
    scan_mode = "FULL" if full_scan else "GOVERNANCE"

    print("=" * 78)
    print(f"NAN DATA ENGINEERING LABS - ENGLISH CONTENT VALIDATION ({scan_mode})")
    print("=" * 78)
    print(f"Findings: {len(findings)}")

    if not findings:
        print("No language findings detected in scanned scope.")
        return

    for finding in findings:
        rel_path = finding.path.relative_to(ROOT)
        print(
            f"- {rel_path}:{finding.line_number} | marker={finding.marker} | "
            f"line={finding.line}"
        )


def main() -> int:
    args = build_parser().parse_args()
    scope = FULL_SCAN_SCOPE if args.full_scan else DEFAULT_SCOPE

    all_findings: List[Finding] = []
    seen = set()

    for file_path in iter_candidate_files(scope):
        # Avoid duplicate scans if overlapping scope entries are provided.
        resolved = str(file_path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        all_findings.extend(scan_file(file_path))

    print_report(all_findings, full_scan=args.full_scan)
    return 1 if all_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
