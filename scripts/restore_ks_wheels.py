#!/usr/bin/env python3
"""Restore the wheels excluded from the ks-solver-cpp reference snapshot.

The bundled Frontier-Bench snapshot intentionally excludes
`tasks/ks-solver-cpp/tests/wheels/` (large prebuilt dependencies; see
fb/PROVENANCE.md). The reference's verifier image cannot build until that
directory is recreated.

Authoring new tasks does NOT require this: the create skill reads the
reference for structure and difficulty, and authored tasks carry their own
self-contained, pinned verifier dependencies. Restoring the wheels is only
needed to execute the upstream ks reference for calibration.

Usage (requires network for the download mode):

    python scripts/restore_ks_wheels.py --check     # offline status report
    python scripts/restore_ks_wheels.py             # download pinned wheels
    python scripts/restore_ks_wheels.py --arch aarch64

Pinned versions match the snapshot era (numpy 2.x / scipy 1.17.x); override
with --numpy/--scipy if a different pairing is needed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WHEELS_REL = Path("fb") / "t" / "ks" / "tests" / "wheels"

DEFAULT_PINS = {"numpy": "2.3.5", "scipy": "1.17.1"}


def wheels_dir(root: Path | None = None) -> Path:
    return (root or REPO_ROOT) / WHEELS_REL


def check_restore(root: Path) -> tuple[list[str], bool]:
    """Return (messages, present). Never touches the network."""
    wheels = wheels_dir(root)
    present = sorted(wheels.glob("*.whl")) if wheels.is_dir() else []
    if present:
        return (
            [f"ks-solver-cpp wheels present ({len(present)}): {present[0].name} ..."],
            True,
        )
    return (
        [
            "ks-solver-cpp wheels are missing (excluded from the snapshot).",
            "Run: python scripts/restore_ks_wheels.py   (requires network)",
        ],
        False,
    )


def download(root: Path, pins: dict[str, str], arch: str, python_abi: str) -> int:
    wheels = wheels_dir(root)
    wheels.mkdir(parents=True, exist_ok=True)
    platform = f"manylinux2014_{arch}"
    packages = [f"{name}=={version}" for name, version in pins.items()]
    command = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        str(wheels),
        "--no-deps",
        "--only-binary=:all:",
        "--platform",
        platform,
        "--implementation",
        "cp",
        "--python-version",
        python_abi,
        "--abi",
        python_abi,
        *packages,
    ]
    print("Running:", " ".join(command))
    result = subprocess.run(command)
    if result.returncode != 0:
        print(
            "Download failed. The wheels are consumed inside a Linux verifier "
            "image, so --platform/--python-version target Linux CPython; adjust "
            "with --arch/--python-abi if needed.",
            file=sys.stderr,
        )
        return result.returncode
    ok, _ = check_restore(root)
    print("\n".join(ok))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report status without network")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--arch", default="x86_64", choices=("x86_64", "aarch64"))
    parser.add_argument("--python-abi", default="312", help="CPython version tag, e.g. 312")
    parser.add_argument("--numpy", default=DEFAULT_PINS["numpy"])
    parser.add_argument("--scipy", default=DEFAULT_PINS["scipy"])
    args = parser.parse_args()

    root = args.root.resolve()
    messages, present = check_restore(root)
    print("\n".join(messages))
    if args.check or present:
        return 0 if present else 1
    pins = {"numpy": args.numpy, "scipy": args.scipy}
    return download(root, pins, args.arch, args.python_abi)


if __name__ == "__main__":
    raise SystemExit(main())
