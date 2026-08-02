from __future__ import annotations

import unittest

import validate_windows_paths


class WindowsPathValidationTest(unittest.TestCase):
    def test_accepts_cross_platform_posix_paths(self) -> None:
        paths = ["plugins/example/fb/t/rs/tests/fixtures/data.bin", "README.md"]
        self.assertEqual(validate_windows_paths.validate_paths(paths), [])

    def test_rejects_over_budget_paths(self) -> None:
        path = "plugins/example/" + "x" * 40
        errors = validate_windows_paths.validate_paths([path], max_relative=30)
        self.assertTrue(any("exceeds 30" in error for error in errors))

    def test_rejects_case_collisions_and_reserved_names(self) -> None:
        errors = validate_windows_paths.validate_paths(["docs/Readme.md", "docs/README.md", "aux.txt"])
        self.assertTrue(any("collision" in error for error in errors))
        self.assertTrue(any("reserved Windows name" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
