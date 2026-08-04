#!/usr/bin/env python3
"""Validate and resolve bundled or canonical Frontier-Bench layouts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TASK_PATHS = {
    "wal-recovery-ordering": "wr",
    "ontology-kg-querying": "kg",
    "rs-archive-clone": "rs",
    "lean-midpoint-proof": "lm",
    "ks-solver-cpp": "ks",
    "vllm-deepseek-streaming": "vs",
    "biped-contact-dynamics": "bd",
}
TASKS = tuple(TASK_PATHS)
MAX_BUNDLE_RELATIVE_PATH = 160

COMMON_ROOT_FILES = ("LICENSE", "CONTRIBUTING.md")

TASK_ENTRIES = (
    "instruction.md",
    "task.toml",
    "environment",
    "solution",
    "tests",
)

DOCKERFILES = ("environment/Dockerfile", "tests/Dockerfile")

# Local COPY/ADD sources referenced by a Dockerfile may be missing from the
# snapshot only when documented as an intentional exclusion in fb/PROVENANCE.md.
# Relative to each Dockerfile's build context (its own directory).
ALLOWED_MISSING_CONTEXT = frozenset()

COPY_SOURCE_RE = re.compile(
    r"^\s*(?:COPY|ADD)"
    r"(?:\s+--[a-z0-9-]+(?:=[^\s]+)?)*"
    r"(?:\s+--from=[^\s]+)*"
    r"\s+(?P<sources>.+?)\s+[^\s]+\s*$",
    re.IGNORECASE,
)


def is_short_layout(root: Path) -> bool:
    return (root / "t").is_dir()


def bundle_paths(root: Path, reference: str | None = None) -> dict[str, Path]:
    """Return semantic paths for the Windows-safe bundle or an upstream checkout."""
    short = is_short_layout(root)
    dirs = {"tasks": "t", "checks": "c", "docs": "d", "rubrics": "r"} if short else {
        "tasks": "tasks",
        "checks": "checks",
        "docs": "docs",
        "rubrics": "rubrics",
    }
    paths = {name: root / relative for name, relative in dirs.items()}
    paths["taxonomy"] = paths["docs"] / "TAXONOMY.md"
    paths["template"] = paths["docs"] / "task-template.toml"
    paths["rubric"] = paths["rubrics"] / "task-implementation.toml"
    if reference is not None:
        if reference not in TASK_PATHS:
            raise ValueError(f"unsupported reference: {reference}")
        task_dir = TASK_PATHS[reference] if short else reference
        paths["task"] = paths["tasks"] / task_dir
    return paths


def dockerfile_local_sources(dockerfile: Path) -> list[str]:
    """Return local (non-remote, non-absolute) COPY/ADD sources in a Dockerfile."""
    sources: list[str] = []
    logical = ""
    for raw in dockerfile.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip()
        logical += line
        if line.endswith("\\") or (not logical.strip() and not line.strip()):
            if line.endswith("\\"):
                logical = logical[:-1]
                continue
            logical = ""
            continue
        match = COPY_SOURCE_RE.match(logical)
        logical = ""
        if not match:
            continue
        for source in match.group("sources").split():
            if source.startswith(("http://", "https://", "--from=", "/")):
                continue
            sources.append(source)
    return sources


def dockerfile_integrity_errors(task_dir: Path) -> list[str]:
    """Error when a Dockerfile COPY/ADD source is missing from its context."""
    errors: list[str] = []
    for dockerfile_name in DOCKERFILES:
        dockerfile = task_dir / dockerfile_name
        if not dockerfile.is_file():
            continue
        for source in dockerfile_local_sources(dockerfile):
            context_probe = dockerfile.parent / source
            if any(character in source for character in "*?["):
                context_probe = (
                    context_probe.parent if context_probe.name else context_probe
                )
            key = f"{task_dir.name}:{dockerfile_name}:{source}"
            if not context_probe.exists() and key not in ALLOWED_MISSING_CONTEXT:
                errors.append(
                    f"{task_dir.name}: {dockerfile_name} COPY/ADD source missing "
                    f"from snapshot: {source}"
                )
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    paths = bundle_paths(root)
    required = COMMON_ROOT_FILES + (("PROVENANCE.md",) if is_short_layout(root) else ()) + (
        str(paths["template"].relative_to(root)),
        str(paths["taxonomy"].relative_to(root)),
        str((paths["rubrics"] / "task-proposal.md").relative_to(root)),
        str(paths["rubric"].relative_to(root)),
    )
    for relative in required:
        if not (root / relative).is_file():
            errors.append(f"missing required bundle file: {relative}")

    checks = paths["checks"]
    if not checks.is_dir() or not any(checks.glob("check-*")):
        errors.append("missing Frontier-Bench checks")

    task_root = paths["tasks"]
    actual = sorted(path.name for path in task_root.iterdir() if path.is_dir()) if task_root.is_dir() else []
    expected = sorted(TASK_PATHS.values() if is_short_layout(root) else TASKS)
    if actual != expected:
        errors.append(f"task set mismatch: expected {expected}, found {actual}")

    for task in TASKS:
        path = bundle_paths(root, task)["task"]
        for relative in TASK_ENTRIES:
            if not (path / relative).exists():
                errors.append(f"{task}: missing {relative}")
        errors.extend(dockerfile_integrity_errors(path))

    excluded_wheels = bundle_paths(root, "ks-solver-cpp")["task"] / "tests" / "wheels"
    if excluded_wheels.exists():
        errors.append("excluded ks-solver-cpp wheel directory is present")

    if is_short_layout(root):
        for path in root.rglob("*"):
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                if len(relative) > MAX_BUNDLE_RELATIVE_PATH:
                    errors.append(
                        f"bundle path exceeds {MAX_BUNDLE_RELATIVE_PATH} characters: {relative}"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--reference", choices=TASKS)
    parser.add_argument("--json", action="store_true", help="print resolved semantic paths as JSON")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    if args.json and not errors:
        resolved = bundle_paths(root, args.reference)
        print(json.dumps({key: str(value) for key, value in resolved.items()}, indent=2))
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr if args.json else sys.stdout)
    if not args.json:
        print(f"Reference bundle validation complete: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
