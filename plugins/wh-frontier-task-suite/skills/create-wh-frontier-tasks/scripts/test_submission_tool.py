from __future__ import annotations

import argparse
import contextlib
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

import submission_tool


class SubmissionToolTest(unittest.TestCase):
    @contextlib.contextmanager
    def temporary_directory(self):
        test_root = os.environ.get("SUBMISSION_TOOL_TEST_ROOT")
        if test_root:
            parent = Path(test_root).resolve() / self._testMethodName
            if not parent.is_dir():
                raise RuntimeError(f"pre-create writable test directory: {parent}")
            yield str(parent)
            return
        with tempfile.TemporaryDirectory() as directory:
            yield directory

    def make_submission(self, parent: Path) -> Path:
        args = argparse.Namespace(
            output_parent=str(parent),
            owner="wh",
            contact="wh",
            category="Software",
            subcategory="Databases",
            reference="wal-recovery-ordering",
            reference_link="local:frontier-bench/tasks/wal-recovery-ordering",
            date="20260802",
            slug=["replica-repair", "lease-reconcile", "index-snapshot"],
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(submission_tool.cmd_init(args), 0)
        return parent / "wh_submission"

    def complete_placeholders(self, root: Path) -> None:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            text = text.replace("TODO", "completed")
            if path.name == "task.toml":
                text = text.replace("expert_time_estimate_hours = 0", "expert_time_estimate_hours = 4")
            path.write_text(text, encoding="utf-8", newline="\n")

    def test_scaffold_fails_until_completed(self) -> None:
        with self.temporary_directory() as directory:
            root = self.make_submission(Path(directory))
            findings = submission_tool.validate(root)
            self.assertTrue(any(item.level == "ERROR" for item in findings))

    def test_completed_submission_validates_and_packages(self) -> None:
        with self.temporary_directory() as directory:
            parent = Path(directory)
            root = self.make_submission(parent)
            self.complete_placeholders(root)
            self.assertFalse(any(item.level == "ERROR" for item in submission_tool.validate(root)))

            archive_path = parent / "result.zip"
            args = argparse.Namespace(
                submission=str(root),
                category="Software",
                subcategory="Databases",
                date="20260802",
                output=str(archive_path),
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(submission_tool.cmd_package(args), 0)
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
            self.assertIn("wh_submission/README.md", names)
            self.assertEqual(sum(name.endswith("/task.toml") for name in names), 3)


if __name__ == "__main__":
    unittest.main()
