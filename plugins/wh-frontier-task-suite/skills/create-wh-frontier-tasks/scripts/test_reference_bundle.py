from __future__ import annotations

import unittest
from pathlib import Path

import validate_reference_bundle


class ReferenceBundleTest(unittest.TestCase):
    def test_bundled_snapshot_is_complete(self) -> None:
        plugin_root = Path(__file__).resolve().parents[3]
        bundle = plugin_root / "assets" / "frontier-bench"
        self.assertEqual(validate_reference_bundle.validate(bundle), [])


if __name__ == "__main__":
    unittest.main()
