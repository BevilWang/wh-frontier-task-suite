#!/usr/bin/env python3
"""Validate the Codex app plugin manifest and Git-backed marketplace release."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLUGIN_NAME = "wh-frontier-task-suite"
REPOSITORY = "https://github.com/BevilWang/wh-frontier-task-suite"
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_release(root: Path) -> list[str]:
    errors: list[str] = []
    plugin_root = root / "plugins" / PLUGIN_NAME
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"

    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read plugin manifest: {exc}"]
    try:
        marketplace = load_json(marketplace_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read marketplace: {exc}"]

    if manifest.get("name") != PLUGIN_NAME:
        errors.append("manifest name must match the plugin directory")
    version = manifest.get("version", "")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append("manifest version must be strict semver")

    author = manifest.get("author", {})
    if author.get("email") != "wanghan.scut@gmail.com":
        errors.append("manifest author email must be wanghan.scut@gmail.com")
    if manifest.get("repository") != REPOSITORY:
        errors.append("manifest repository must point at the canonical GitHub repository")

    interface = manifest.get("interface", {})
    required_interface = (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
    )
    for field in required_interface:
        if not interface.get(field):
            errors.append(f"manifest interface.{field} is required")
    prompts = interface.get("defaultPrompt", [])
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("manifest must provide one to three default prompts")
    elif any(not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts):
        errors.append("every default prompt must be a string of at most 128 characters")

    entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == PLUGIN_NAME]
    if len(entries) != 1:
        errors.append("marketplace must contain exactly one plugin entry")
    else:
        entry = entries[0]
        source = entry.get("source", {})
        expected_source = {
            "source": "git-subdir",
            "url": f"{REPOSITORY}.git",
            "path": f"./plugins/{PLUGIN_NAME}",
            "ref": "main",
        }
        if source != expected_source:
            errors.append("marketplace must use the canonical GitHub git-subdir source")
        policy = entry.get("policy", {})
        if policy.get("installation") != "AVAILABLE":
            errors.append("marketplace installation policy must be AVAILABLE")
        if policy.get("authentication") != "ON_INSTALL":
            errors.append("marketplace authentication policy must be ON_INSTALL")
        if not entry.get("category"):
            errors.append("marketplace category is required")

    skill_roots = sorted((plugin_root / "skills").glob("*/SKILL.md"))
    expected_skills = {
        "create-wh-frontier-tasks",
        "repair-wh-frontier-tasks",
        "run-wh-frontier-pipeline",
        "verify-wh-frontier-tasks",
    }
    discovered = {path.parent.name for path in skill_roots}
    if discovered != expected_skills:
        errors.append(f"unexpected skill set: {sorted(discovered)}")
    for skill_path in skill_roots:
        text = skill_path.read_text(encoding="utf-8")
        match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text)
        if match is None or match.group(1) != skill_path.parent.name:
            errors.append(f"skill name does not match directory: {skill_path}")
        if re.search(r"git\s+config[^\n]*core\.longpaths", text, re.IGNORECASE):
            errors.append(f"skill must not require Git long-path configuration: {skill_path}")

    readme = (root / "README.md").read_text(encoding="utf-8")
    if "codex plugin marketplace add" in readme or "codex plugin add" in readme:
        errors.append("README installation must use the Codex app, not CLI commands")
    if "Codex 应用" not in readme or "Plugins" not in readme:
        errors.append("README must document Codex app installation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_release(args.root.resolve())
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Codex app release validation complete: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
