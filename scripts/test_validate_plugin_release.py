#!/usr/bin/env python3
"""Tests for the plugin release validator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import validate_plugin_release


def make_repo(tmp: Path) -> None:
    """Build a minimal passing repository skeleton."""
    (tmp / ".codex-plugin").mkdir(parents=True)
    (tmp / ".agents" / "plugins").mkdir(parents=True)
    (tmp / "skills").mkdir()
    (tmp / "fb" / "t" / "rs" / "tests" / "fixtures" / "files").mkdir(parents=True)
    manifest = {
        "name": "wh-frontier-task-suite",
        "version": "0.8.2+codex.20260805000000",
        "description": "test",
        "author": {"name": "BevilWang", "email": "wanghan.scut@gmail.com", "url": "https://github.com/BevilWang"},
        "homepage": "https://github.com/BevilWang/wh-frontier-task-suite#readme",
        "repository": "https://github.com/BevilWang/wh-frontier-task-suite",
        "license": "MIT",
        "keywords": [],
        "skills": "./skills/",
        "interface": {
            "displayName": "WH Frontier Task Suite",
            "shortDescription": "s",
            "longDescription": "l",
            "developerName": "BevilWang",
            "category": "Developer Tools",
            "defaultPrompt": ["Run the pipeline."],
        },
    }
    (tmp / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    marketplace = {
        "name": "wh-frontier-task-suite",
        "interface": {"displayName": "WH Frontier Task Suite"},
        "plugins": [
            {
                "name": "wh-frontier-task-suite",
                "source": {"source": "local", "path": "."},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ],
    }
    (tmp / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps(marketplace), encoding="utf-8")
    for skill in validate_plugin_release.EXPECTED_SKILLS:
        directory = tmp / "skills" / skill
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text(f"---\nname: {skill}\n---\n# {skill}\n", encoding="utf-8")
    vectors = {"files": ["files/a.bin"]}
    (tmp / "fb" / "t" / "rs" / "tests" / "fixtures" / "vectors.json").write_text(
        json.dumps(vectors), encoding="utf-8"
    )
    (tmp / "fb" / "t" / "rs" / "tests" / "fixtures" / "files" / "a.bin").write_bytes(b"\x00\x01")
    (tmp / "README.md").write_text("# Test\n\nCodex app\nCodex CLI\n", encoding="utf-8")


class ReleaseValidatorTest(unittest.TestCase):
    def test_passing_repository_has_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            make_repo(repo)
            self.assertEqual(validate_plugin_release.validate_release(repo), [])

    def test_rejects_wrong_license(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            make_repo(repo)
            manifest_path = repo / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["license"] = "Apache-2.0"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validate_plugin_release.validate_release(repo)
            self.assertTrue(any("license must be MIT" in error for error in errors))

    def test_rejects_bad_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            make_repo(repo)
            manifest_path = repo / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "not-semver"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validate_plugin_release.validate_release(repo)
            self.assertTrue(any("strict semver" in error for error in errors))

    def test_rejects_missing_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            make_repo(repo)
            (repo / "skills" / "verify-wh-frontier-tasks").rename(
                repo / "skills" / "other-wh-frontier-tasks"
            )
            errors = validate_plugin_release.validate_release(repo)
            self.assertTrue(any("unexpected skill set" in error for error in errors))

    def test_rejects_utf16_skill_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            make_repo(repo)
            target = repo / "skills" / "verify-wh-frontier-tasks" / "SKILL.md"
            target.write_bytes("---\nname: verify-wh-frontier-tasks\n---\n".encode("utf-16"))
            errors = validate_plugin_release.validate_release(repo)
            self.assertTrue(any("non-UTF-8 file" in error for error in errors))

    def test_rejects_bad_marketplace_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            make_repo(repo)
            marketplace_path = repo / ".agents" / "plugins" / "marketplace.json"
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            marketplace["plugins"][0]["source"] = {"source": "http", "url": "x"}
            marketplace_path.write_text(json.dumps(marketplace), encoding="utf-8")
            errors = validate_plugin_release.validate_release(repo)
            self.assertTrue(any("must be local or git" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
