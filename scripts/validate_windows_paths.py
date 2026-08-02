#!/usr/bin/env python3
"""Reject repository paths that are unsafe for default Windows Git checkouts."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path, PureWindowsPath


DEFAULT_MAX_RELATIVE = 180
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
WINDOWS_ILLEGAL = set('<>:"\\|?*')


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def validate_paths(paths: list[str], max_relative: int = DEFAULT_MAX_RELATIVE) -> list[str]:
    errors: list[str] = []
    folded: dict[str, str] = {}
    for raw in paths:
        normalized = raw.replace("\\", "/")
        if len(normalized) > max_relative:
            errors.append(f"path exceeds {max_relative} characters ({len(normalized)}): {normalized}")

        windows = PureWindowsPath(normalized)
        for component in windows.parts:
            if len(component) > 255:
                errors.append(f"component exceeds 255 characters: {normalized}")
            stem = component.rstrip(" .").split(".", 1)[0].upper()
            if stem in WINDOWS_RESERVED:
                errors.append(f"reserved Windows name '{component}': {normalized}")
            if component.endswith((" ", ".")):
                errors.append(f"component has a trailing space or dot: {normalized}")
            if any(char in WINDOWS_ILLEGAL for char in component):
                errors.append(f"component contains a Windows-illegal character: {normalized}")

        key = normalized.casefold()
        previous = folded.get(key)
        if previous is not None and previous != normalized:
            errors.append(f"case-insensitive collision: {previous} <> {normalized}")
        folded[key] = normalized
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-relative", type=int, default=DEFAULT_MAX_RELATIVE)
    args = parser.parse_args()

    root = args.root.resolve()
    paths = tracked_paths(root)
    errors = validate_paths(paths, args.max_relative)
    for error in errors:
        print(f"ERROR: {error}")
    longest = max((len(path.replace('\\', '/')) for path in paths), default=0)
    print(
        f"Windows path validation complete: {len(errors)} error(s), "
        f"{len(paths)} tracked path(s), longest relative path {longest}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
