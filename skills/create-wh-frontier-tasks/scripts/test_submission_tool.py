from __future__ import annotations

import argparse
import contextlib
import io
import os
import tempfile
import shutil
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
            slug=["replica", "lease", "index"],
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
            if path.name.startswith("test_") and path.suffix == ".py":
                text += "\n# Seeded variation marker for the completed test fixture.\nimport random\nrng = random.Random(7)\n"
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

    def test_fixed_only_verifier_is_rejected(self) -> None:
        with self.temporary_directory() as directory:
            root = self.make_submission(Path(directory))
            self.complete_placeholders(root)
            test_file = root / "task-1-replica" / "tests" / "test_outputs.py"
            test_file.write_text(
                "def test_one(): assert True\n"
                "def test_two(): assert True\n"
                "def test_three(): assert True\n",
                encoding="utf-8",
            )
            findings = submission_tool.validate(root)
            self.assertTrue(any("fixed-only" in item.message for item in findings))

    def test_unprivileged_ctrf_requires_writable_temp_directory(self) -> None:
        with self.temporary_directory() as directory:
            root = self.make_submission(Path(directory))
            self.complete_placeholders(root)
            wrapper = root / "task-1-replica" / "tests" / "test.sh"
            wrapper.write_text(
                "#!/bin/sh\ntmp=$(mktemp -d)\n"
                "setpriv --reuid nobody pytest --ctrf \"$tmp/ctrf.json\"\n",
                encoding="utf-8",
            )
            findings = submission_tool.validate(root)
            self.assertTrue(any("CTRF output" in item.message for item in findings))



    def test_init_rejects_multi_token_slug(self) -> None:
        with self.temporary_directory() as directory:
            args = argparse.Namespace(
                output_parent=str(directory),
                owner="wh",
                contact="wh",
                category="Software",
                subcategory="Databases",
                reference="wal-recovery-ordering",
                reference_link="local:frontier-bench/tasks/wal-recovery-ordering",
                date="20260802",
                slug=["multi-token-slug", "lease", "index"],
            )
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                submission_tool.cmd_init(args)

    def test_task_directory_token_limit_is_enforced(self) -> None:
        with self.temporary_directory() as directory:
            root = self.make_submission(Path(directory))
            self.complete_placeholders(root)
            src = root / "task-1-replica"
            dst = root / "task-1-replica-extra-token"
            src.rename(dst)
            toml = dst / "task.toml"
            toml.write_text(
                toml.read_text(encoding="utf-8").replace(
                    'name = "z-bench/task-1-replica"',
                    'name = "z-bench/task-1-replica-extra-token"',
                ),
                encoding="utf-8",
            )
            findings = submission_tool.validate(root)
            self.assertTrue(any("more than 3 hyphen-separated tokens" in item.message for item in findings))

    def test_package_excludes_pycache(self) -> None:
        with self.temporary_directory() as directory:
            parent = Path(directory)
            root = self.make_submission(parent)
            self.complete_placeholders(root)
            (root / "task-1-replica" / "solution" / "__pycache__").mkdir(parents=True)
            (root / "task-1-replica" / "solution" / "__pycache__" / "app.cpython-312.pyc").write_text("x")
            archive_path = parent / "result.zip"
            args = argparse.Namespace(
                submission=str(root),
                category="Software",
                subcategory="Databases",
                date="20260802",
                output=str(archive_path),
            )
            shutil.rmtree(root / "task-1-replica" / "solution" / "__pycache__")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(submission_tool.cmd_package(args), 0)
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))
    def test_init_records_seed_and_variant(self) -> None:
        with self.temporary_directory() as directory:
            parent = Path(directory)
            args = argparse.Namespace(
                output_parent=str(parent),
                owner="wh",
                contact="wh",
                category="Software",
                subcategory="Databases",
                reference="wal-recovery-ordering",
                reference_link="local:ref",
                date="20260802",
                slug=["replica", "lease", "index"],
                seed="abc123",
                variant="recovery-index",
            )
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(submission_tool.cmd_init(args), 0)
            readme = (parent / "wh_submission" / "README.md").read_text(encoding="utf-8")
            self.assertIn("Design seed: abc123", readme)
            self.assertIn("Design variant: recovery-index", readme)
            self.assertIn("design_seed=abc123", stdout.getvalue())
            self.assertIn("design_variant=recovery-index", stdout.getvalue())

    def test_init_without_seed_samples_a_pool_variant(self) -> None:
        with self.temporary_directory() as directory:
            parent = Path(directory)
            args = argparse.Namespace(
                output_parent=str(parent),
                owner="wh",
                contact="wh",
                category="Software",
                subcategory="Databases",
                reference="wal-recovery-ordering",
                reference_link="local:ref",
                date="20260802",
                slug=["replica", "lease", "index"],
                seed=None,
                variant=None,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(submission_tool.cmd_init(args), 0)
            readme = (parent / "wh_submission" / "README.md").read_text(encoding="utf-8")
            seed_line = next(line for line in readme.splitlines() if line.startswith("- Design seed: "))
            variant_line = next(line for line in readme.splitlines() if line.startswith("- Design variant: "))
            self.assertGreaterEqual(len(seed_line.split(": ", 1)[1]), 8)
            pool_ids = {entry["id"] for entry in submission_tool.design_pools()["wal-recovery-ordering"]["pool"]}
            self.assertIn(variant_line.split(": ", 1)[1], pool_ids)

    def test_init_warns_on_custom_variant(self) -> None:
        with self.temporary_directory() as directory:
            parent = Path(directory)
            args = argparse.Namespace(
                output_parent=str(parent),
                owner="wh",
                contact="wh",
                category="Software",
                subcategory="Databases",
                reference="wal-recovery-ordering",
                reference_link="local:ref",
                date="20260802",
                slug=["replica", "lease", "index"],
                seed="s",
                variant="my-custom-family",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(submission_tool.cmd_init(args), 0)
            self.assertIn("WARNING", stderr.getvalue())
            readme = (parent / "wh_submission" / "README.md").read_text(encoding="utf-8")
            self.assertIn("Design variant: my-custom-family", readme)


if __name__ == "__main__":
    unittest.main()
