#!/usr/bin/env python3
"""Tests for the bundled Frontier-Bench reference validator."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import validate_reference_bundle


class ReferenceBundleTest(unittest.TestCase):
    def test_bundled_snapshot_is_complete(self) -> None:
        plugin_root = Path(__file__).resolve().parents[3]
        bundle = plugin_root / "fb"
        self.assertEqual(validate_reference_bundle.validate(bundle), [])

    def test_short_layout_resolves_public_name(self) -> None:
        plugin_root = Path(__file__).resolve().parents[3]
        bundle = plugin_root / "fb"
        paths = validate_reference_bundle.bundle_paths(bundle, "rs-archive-clone")
        self.assertEqual(paths["task"], bundle / "t" / "rs")
        self.assertEqual(paths["checks"], bundle / "c")
        self.assertEqual(paths["rubric"], bundle / "r" / "task-implementation.toml")

    def test_short_bundle_paths_keep_windows_headroom(self) -> None:
        plugin_root = Path(__file__).resolve().parents[3]
        bundle = plugin_root / "fb"
        longest = max(
            len(path.relative_to(bundle).as_posix())
            for path in bundle.rglob("*")
            if path.is_file()
        )
        self.assertLessEqual(longest, validate_reference_bundle.MAX_BUNDLE_RELATIVE_PATH)

    def test_canonical_external_layout_stays_supported(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tasks").mkdir()
            paths = validate_reference_bundle.bundle_paths(root, "wal-recovery-ordering")
            self.assertEqual(paths["task"], root / "tasks" / "wal-recovery-ordering")
            self.assertEqual(paths["checks"], root / "checks")
            self.assertEqual(paths["rubric"], root / "rubrics" / "task-implementation.toml")

    def test_dockerfile_missing_copy_source_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            task = Path(directory)
            env = task / "environment"
            env.mkdir()
            (env / "Dockerfile").write_text(
                "FROM ubuntu:24.04\nCOPY missing.txt /app/missing.txt\n",
                encoding="utf-8",
            )
            errors = validate_reference_bundle.dockerfile_integrity_errors(task)
            self.assertTrue(
                any("COPY/ADD source missing" in error and "missing.txt" in error for error in errors)
            )

    def test_dockerfile_remote_and_multiline_sources_pass(self) -> None:
        with TemporaryDirectory() as directory:
            task = Path(directory)
            env = task / "environment"
            env.mkdir()
            (env / "present.txt").write_text("x", encoding="utf-8")
            backslash = chr(92)
            dockerfile_text = "\n".join(
                [
                    "FROM ubuntu:24.04",
                    "ADD https://example.com/f.bin /tmp/f.bin",
                    "COPY --chown=root:root " + backslash,
                    "    present.txt " + backslash,
                    "    /app/",
                ]
            ) + "\n"
            (env / "Dockerfile").write_text(dockerfile_text, encoding="utf-8")
            self.assertEqual(validate_reference_bundle.dockerfile_integrity_errors(task), [])


if __name__ == "__main__":
    unittest.main()
