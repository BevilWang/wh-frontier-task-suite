from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import validate_plugin_release


class PluginReleaseValidationTest(unittest.TestCase):
    def create_release(self, root: Path) -> None:
        plugin = root / "plugins" / validate_plugin_release.PLUGIN_NAME
        (plugin / ".codex-plugin").mkdir(parents=True)
        for name in (
            "create-wh-frontier-tasks",
            "repair-wh-frontier-tasks",
            "run-wh-frontier-pipeline",
            "verify-wh-frontier-tasks",
        ):
            skill = plugin / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8")
        manifest = {
            "name": validate_plugin_release.PLUGIN_NAME,
            "version": "0.7.0+codex.test",
            "description": "test",
            "author": {"name": "BevilWang", "email": "wanghan.scut@gmail.com"},
            "repository": validate_plugin_release.REPOSITORY,
            "interface": {
                "displayName": "Test",
                "shortDescription": "Test",
                "longDescription": "Test",
                "developerName": "BevilWang",
                "category": "Developer Tools",
                "defaultPrompt": ["Run the workflow."],
            },
        }
        (plugin / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        marketplace_dir = root / ".agents" / "plugins"
        marketplace_dir.mkdir(parents=True)
        marketplace = {
            "name": validate_plugin_release.PLUGIN_NAME,
            "plugins": [{
                "name": validate_plugin_release.PLUGIN_NAME,
                "source": {
                    "source": "git-subdir",
                    "url": f"{validate_plugin_release.REPOSITORY}.git",
                    "path": f"./plugins/{validate_plugin_release.PLUGIN_NAME}",
                    "ref": "main",
                },
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }],
        }
        (marketplace_dir / "marketplace.json").write_text(json.dumps(marketplace), encoding="utf-8")
        (root / "README.md").write_text("Codex 应用 Plugins", encoding="utf-8")

    def test_accepts_app_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.create_release(root)
            self.assertEqual(validate_plugin_release.validate_release(root), [])

    def test_rejects_local_source_and_cli_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.create_release(root)
            marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            marketplace["plugins"][0]["source"] = {
                "source": "local",
                "path": "./plugins/wh-frontier-task-suite",
            }
            marketplace_path.write_text(json.dumps(marketplace), encoding="utf-8")
            (root / "README.md").write_text("Codex 应用 Plugins\ncodex plugin add x", encoding="utf-8")
            errors = validate_plugin_release.validate_release(root)
            self.assertTrue(any("git-subdir" in error for error in errors))
            self.assertTrue(any("not CLI" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

