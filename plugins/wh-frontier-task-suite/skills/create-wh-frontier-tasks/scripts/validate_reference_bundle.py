#!/usr/bin/env python3
"""Validate the bundled Frontier-Bench authoring snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path


TASKS = (
    "wal-recovery-ordering",
    "ontology-kg-querying",
    "rs-archive-clone",
    "lean-midpoint-proof",
    "ks-solver-cpp",
    "vllm-deepseek-streaming",
    "biped-contact-dynamics",
)

ROOT_FILES = (
    "LICENSE",
    "PROVENANCE.md",
    "CONTRIBUTING.md",
    "docs/task-template.toml",
    "docs/TAXONOMY.md",
    "rubrics/task-proposal.md",
    "rubrics/task-implementation.toml",
)

TASK_ENTRIES = (
    "instruction.md",
    "task.toml",
    "environment",
    "solution",
    "tests",
)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in ROOT_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required bundle file: {relative}")

    checks = root / "checks"
    if not checks.is_dir() or not any(checks.glob("check-*")):
        errors.append("missing Frontier-Bench checks")

    task_root = root / "tasks"
    actual = sorted(path.name for path in task_root.iterdir() if path.is_dir()) if task_root.is_dir() else []
    if actual != sorted(TASKS):
        errors.append(f"task set mismatch: expected {sorted(TASKS)}, found {actual}")

    for task in TASKS:
        path = task_root / task
        for relative in TASK_ENTRIES:
            if not (path / relative).exists():
                errors.append(f"{task}: missing {relative}")

    excluded_wheels = task_root / "ks-solver-cpp" / "tests" / "wheels"
    if excluded_wheels.exists():
        errors.append("excluded ks-solver-cpp wheel directory is present")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Reference bundle validation complete: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
