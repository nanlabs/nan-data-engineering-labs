#!/usr/bin/env python3
"""Validate module contracts for nan-data-engineering-labs.

Checks module-type structure contracts and README heading groups for
atomic self-training readiness.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / "modules"

REGULAR_REQUIRED = (
    "README.md",
    "STATUS.md",
    "theory",
    "exercises",
    "validation",
    "scripts",
    "data",
    "docs",
)

CHECKPOINT_REQUIRED = (
    "README.md",
    "starter-template",
    "reference-solution",
    "validation",
    "docs",
    "architecture",
    "data",
)

BONUS_REQUIRED = (
    "README.md",
    "theory",
    "exercises",
    "validation",
    "scripts",
    "data",
    "notebooks",
)

EXERCISE_REQUIRED = (
    "README.md",
    "hints.md",
    "starter",
    "solution",
    "my_solution",
)

REGULAR_OPTIONAL = (
    "assets",
    "infrastructure",
    "requirements.txt",
    "pytest.ini",
    "Makefile",
    "GETTING-STARTED.md",
    "QUICK-START.md",
    "STATUS-FINAL.md",
    "PROGRESS.md",
)

CHECKPOINT_OPTIONAL = (
    "scripts",
    "requirements.txt",
    "assets",
    "extensions",
)

BONUS_OPTIONAL = (
    "assets",
    "infrastructure",
    "requirements.txt",
    "COST-ALERT.md",
)

MODULE_SPECIFIC_EXCEPTIONS = {
    "module-10-workflow-orchestration": {"dags"},
}

# Heading groups can be satisfied by at least one candidate each.
README_HEADING_GROUPS = {
    "overview_or_objective": ("overview", "objective"),
    "learning_objectives": ("learning objectives",),
    "prerequisites": ("prerequisites",),
    "practice_or_exercises": ("exercises", "practice"),
    "validation_or_success_criteria": ("validation", "success criteria"),
}


@dataclass
class Finding:
    severity: str  # ERROR or WARNING
    module: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "module": self.module,
            "code": self.code,
            "message": self.message,
        }


def module_type(module_name: str) -> str:
    if module_name.startswith("module-checkpoint-"):
        return "checkpoint"
    if module_name.startswith("module-bonus-"):
        return "bonus"
    if module_name.startswith("module-"):
        return "regular"
    return "unknown"


def required_paths_for(module_kind: str) -> Sequence[str]:
    if module_kind == "regular":
        return REGULAR_REQUIRED
    if module_kind == "checkpoint":
        return CHECKPOINT_REQUIRED
    if module_kind == "bonus":
        return BONUS_REQUIRED
    return ()


def optional_paths_for(module_kind: str) -> Sequence[str]:
    if module_kind == "regular":
        return REGULAR_OPTIONAL
    if module_kind == "checkpoint":
        return CHECKPOINT_OPTIONAL
    if module_kind == "bonus":
        return BONUS_OPTIONAL
    return ()


def is_heading_present(
    readme_text_lower: str,
    candidates: Iterable[str],
) -> bool:
    for candidate in candidates:
        if candidate in readme_text_lower:
            return True
    return False


def find_module_dirs(target_module: str | None) -> List[Path]:
    if target_module:
        path = MODULES_DIR / target_module
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Module path not found: {path}")
        return [path]

    return sorted(
        [
            p
            for p in MODULES_DIR.iterdir()
            if p.is_dir() and p.name.startswith("module-")
        ],
        key=lambda p: p.name,
    )


def check_required_paths(
    module_dir: Path,
    strict_bonus: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    kind = module_type(module_dir.name)
    required_paths = required_paths_for(kind)

    for rel in required_paths:
        if not (module_dir / rel).exists():
            severity = "ERROR"
            if kind == "bonus" and not strict_bonus:
                severity = "WARNING"
            findings.append(
                Finding(
                    severity=severity,
                    module=module_dir.name,
                    code="MISSING_REQUIRED_PATH",
                    message=f"Missing required path: {rel}",
                )
            )

    return findings


def check_unapproved_extras(
    module_dir: Path,
    strict_bonus: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    kind = module_type(module_dir.name)

    approved = set(required_paths_for(kind))
    approved.update(optional_paths_for(kind))
    approved.update(MODULE_SPECIFIC_EXCEPTIONS.get(module_dir.name, set()))

    module_root_entries = {
        p.name for p in module_dir.iterdir() if not p.name.startswith(".")
    }
    extras = sorted(module_root_entries - approved)

    for extra in extras:
        severity = "ERROR"
        if kind == "bonus" and not strict_bonus:
            severity = "WARNING"
        findings.append(
            Finding(
                severity=severity,
                module=module_dir.name,
                code="UNAPPROVED_MODULE_EXTRA",
                message=f"Unapproved module-root path: {extra}",
            )
        )

    return findings


def check_exercise_contract(
    module_dir: Path,
    strict_bonus: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    kind = module_type(module_dir.name)
    exercises_dir = module_dir / "exercises"

    if not exercises_dir.exists() or not exercises_dir.is_dir():
        return findings

    exercise_dirs = [
        d
        for d in exercises_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    if not exercise_dirs:
        severity = "ERROR"
        if kind == "bonus" and not strict_bonus:
            severity = "WARNING"
        findings.append(
            Finding(
                severity=severity,
                module=module_dir.name,
                code="MISSING_EXERCISE_UNITS",
                message="No exercise unit directories found under exercises/",
            )
        )
        return findings

    for exercise_dir in exercise_dirs:
        for rel in EXERCISE_REQUIRED:
            if not (exercise_dir / rel).exists():
                severity = "ERROR"
                if kind == "bonus" and not strict_bonus:
                    severity = "WARNING"
                findings.append(
                    Finding(
                        severity=severity,
                        module=module_dir.name,
                        code="MISSING_EXERCISE_ASSET",
                        message=(
                            f"{exercise_dir.relative_to(module_dir)} "
                            f"is missing {rel}"
                        ),
                    )
                )

    return findings


def check_readme_heading_groups(
    module_dir: Path,
    strict_headings: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    readme_path = module_dir / "README.md"

    if not readme_path.exists():
        return findings

    content = readme_path.read_text(encoding="utf-8", errors="ignore").lower()
    kind = module_type(module_dir.name)

    for group_name, candidates in README_HEADING_GROUPS.items():
        if not is_heading_present(content, candidates):
            severity = "ERROR" if strict_headings else "WARNING"
            if kind == "bonus" and strict_headings:
                severity = "WARNING"
            findings.append(
                Finding(
                    severity=severity,
                    module=module_dir.name,
                    code="MISSING_HEADING_GROUP",
                    message=f"README heading group missing: {group_name}",
                )
            )

    return findings


def validate_modules(
    target_module: str | None,
    strict_bonus: bool,
    strict_headings: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    module_dirs = find_module_dirs(target_module)

    for module_dir in module_dirs:
        kind = module_type(module_dir.name)
        if kind == "unknown":
            findings.append(
                Finding(
                    severity="WARNING",
                    module=module_dir.name,
                    code="UNKNOWN_MODULE_TYPE",
                    message="Module does not match known naming convention",
                )
            )
            continue

        findings.extend(
            check_required_paths(module_dir, strict_bonus=strict_bonus)
        )
        findings.extend(
            check_unapproved_extras(module_dir, strict_bonus=strict_bonus)
        )
        findings.extend(
            check_exercise_contract(module_dir, strict_bonus=strict_bonus)
        )
        findings.extend(
            check_readme_heading_groups(
                module_dir,
                strict_headings=strict_headings,
            )
        )

    return findings


def print_report(findings: Sequence[Finding]) -> None:
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]

    print("=" * 78)
    print("NAN DATA ENGINEERING LABS - MODULE CONTRACT VALIDATION")
    print("=" * 78)
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if not findings:
        print("No findings. Contract validation passed.")
        return

    print("\nFindings:")
    for finding in findings:
        print(
            f"- [{finding.severity}] {finding.module} | "
            f"{finding.code} | {finding.message}"
        )


def write_json_report(path: Path, findings: Sequence[Finding]) -> None:
    data = {
        "errors": len([f for f in findings if f.severity == "ERROR"]),
        "warnings": len([f for f in findings if f.severity == "WARNING"]),
        "findings": [f.as_dict() for f in findings],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate nan-data-engineering-labs module contracts"
    )
    parser.add_argument(
        "--module",
        help=(
            "Validate only one module directory name "
            "(for example module-01-cloud-fundamentals)"
        ),
    )
    parser.add_argument(
        "--strict-core",
        action="store_true",
        help=(
            "Treat regular/checkpoint requirements as hard failures "
            "(default true behavior)."
        ),
    )
    parser.add_argument(
        "--strict-bonus",
        action="store_true",
        help="Treat bonus contract findings as hard failures.",
    )
    parser.add_argument(
        "--strict-headings",
        action="store_true",
        help=(
            "Treat heading group findings as hard failures "
            "(bonus remains warning-only)."
        ),
    )
    parser.add_argument(
        "--report-json",
        help="Write JSON report to this file path.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        findings = validate_modules(
            target_module=args.module,
            strict_bonus=args.strict_bonus,
            strict_headings=args.strict_headings,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

    print_report(findings)

    if args.report_json:
        write_json_report(Path(args.report_json), findings)
        print(f"\nJSON report written to: {args.report_json}")

    has_errors = any(f.severity == "ERROR" for f in findings)

    # strict-core flag exists for explicit workflow compatibility.
    # Core findings are errors by default.
    _ = args.strict_core

    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
