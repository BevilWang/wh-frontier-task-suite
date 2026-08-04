#!/usr/bin/env python3
"""Tests for the ks wheels restore helper (offline modes only)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import restore_ks_wheels


class RestoreKsWheelsTest(unittest.TestCase):
    def test_check_reports_missing_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            messages, present = restore_ks_wheels.check_restore(root)
            self.assertFalse(present)
            self.assertTrue(any("missing" in message for message in messages))

    def test_check_reports_present_wheels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheels = restore_ks_wheels.wheels_dir(root)
            wheels.mkdir(parents=True)
            (wheels / "numpy-2.3.5-cp312-cp312-manylinux_2_17_x86_64.whl").write_bytes(b"x")
            messages, present = restore_ks_wheels.check_restore(root)
            self.assertTrue(present)
            self.assertTrue(any("present" in message for message in messages))

    def test_wheels_dir_points_at_ks_reference(self) -> None:
        self.assertEqual(
            restore_ks_wheels.wheels_dir(Path("ROOT")),
            Path("ROOT") / "fb" / "t" / "ks" / "tests" / "wheels",
        )


if __name__ == "__main__":
    unittest.main()
