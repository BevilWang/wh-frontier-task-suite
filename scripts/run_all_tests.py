#!/usr/bin/env python3
"""Run every unit-test suite in the repository with the standard library.

Discovers and runs the unittest suites bundled with the plugin skills plus the
repository-level scripts. Exits non-zero if any suite fails.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SUITES = [
    REPO_ROOT / "scripts",
    REPO_ROOT / "skills" / "create-wh-frontier-tasks" / "scripts",
    REPO_ROOT / "skills" / "verify-wh-frontier-tasks" / "scripts",
    REPO_ROOT / "skills" / "repair-wh-frontier-tasks" / "scripts",
]


def load_test_files(directory: Path) -> unittest.TestSuite:
    """Load test_*.py modules by file path so non-package directories work."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # Make sibling helper modules (e.g. submission_tool, review_tool) importable.
    sys.path.insert(0, str(directory))
    try:
        for test_file in sorted(directory.glob("test_*.py")):
            module_name = f"{directory.parent.name}_{test_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"cannot load {test_file}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            suite.addTests(loader.loadTestsFromModule(module))
    finally:
        sys.path.pop(0)
    return suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    suite = unittest.TestSuite()
    missing: list[str] = []
    for directory in SUITES:
        if not directory.is_dir():
            missing.append(str(directory))
            continue
        suite.addTests(load_test_files(directory))

    if missing:
        print(f"ERROR: missing test directories: {missing}")
        return 1

    verbosity = 2 if args.verbose else 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
