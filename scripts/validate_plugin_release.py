#!/usr/bin/env python3
"""Validate the Codex plugin manifest, marketplace entry, skills, and repo hygiene.

This supersedes the pre-refactor release validator: the plugin now lives at the
repository root instead of under plugins/frontier-task-suite/, so all paths
and expectations were rewritten for the current layout.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PLUGIN_NAME = "frontier-task-suite"
REPOSITORY = "https://github.com/BevilWang/Frontier-Task-Suite"
AUTHOR_EMAIL = "wanghan.scut@gmail.com"
EXPECTED_LICENSE = "MIT"
EXPECTED_SKILLS = {
    "create-wh-frontier-tasks",
    "repair-wh-frontier-tasks",
    "run-wh-frontier-pipeline",
    "verify-wh-frontier-tasks",
}
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
TEXT_EXTENSIONS = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".sh", ".txt"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)


def find_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
    return sorted(files)


def check_utf8_no_bom(root: Path) -> list[str]:
    errors: list[str] = []
    for path in find_text_files(root):
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"UTF-8 BOM found in {path.relative_to(root)}")
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"non-UTF-8 file {path.relative_to(root)}: {exc}")
    return errors


def validate_release(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / ".codex-plugin" / "plugin.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"

    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read plugin manifest: {exc}")
        return errors
    try:
        marketplace = load_json(marketplace_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read marketplace: {exc}")
        return errors

    # --- plugin manifest ---
    if manifest.get("name") != PLUGIN_NAME:
        errors.append("manifest name must match the plugin identifier")
    version = manifest.get("version", "")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append("manifest version must be strict semver")
    author = manifest.get("author", {})
    if author.get("email") != AUTHOR_EMAIL:
        errors.append("manifest author email is missing or wrong")
    if manifest.get("repository") != REPOSITORY:
        errors.append("manifest repository must point at the canonical GitHub repository")
    if manifest.get("license") != EXPECTED_LICENSE:
        errors.append(f"manifest license must be {EXPECTED_LICENSE}")
    if manifest.get("skills") != "./skills/":
        errors.append("manifest skills must point at ./skills/")

    interface = manifest.get("interface", {})
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        if not interface.get(field):
            errors.append(f"manifest interface.{field} is required")
    prompts = interface.get("defaultPrompt", [])
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("manifest must provide one to three default prompts")
    elif any(not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts):
        errors.append("every default prompt must be a string of at most 128 characters")

    # --- marketplace ---
    if marketplace.get("name") != PLUGIN_NAME:
        errors.append("marketplace name must match the plugin identifier")
    entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == PLUGIN_NAME]
    if len(entries) != 1:
        errors.append("marketplace must contain exactly one plugin entry")
    else:
        entry = entries[0]
        source = entry.get("source", {})
        if source.get("source") == "local":
            if source.get("path") != ".":
                errors.append("local marketplace source path must be '.'")
        elif source.get("source") == "git":
            if not source.get("url") or not source.get("path"):
                errors.append("git marketplace source requires url and path")
        else:
            errors.append("marketplace source must be local or git")
        policy = entry.get("policy", {})
        if policy.get("installation") != "AVAILABLE":
            errors.append("marketplace installation policy must be AVAILABLE")
        if policy.get("authentication") != "ON_INSTALL":
            errors.append("marketplace authentication policy must be ON_INSTALL")
        if not entry.get("category"):
            errors.append("marketplace category is required")

    # --- skills ---
    skill_roots = sorted((root / "skills").glob("*/SKILL.md"))
    discovered = {path.parent.name for path in skill_roots}
    if discovered != EXPECTED_SKILLS:
        errors.append(f"unexpected skill set: {sorted(discovered)}")
    for skill_path in skill_roots:
        try:
            text = skill_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"skill file is not UTF-8: {skill_path}: {exc}")
            continue
        match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text)
        if match is None or match.group(1) != skill_path.parent.name:
            errors.append(f"skill name does not match directory: {skill_path}")
        if re.search(r"git\s+config[^\n]*core\.longpaths", text, re.IGNORECASE):
            errors.append(f"skill must not require Git long-path configuration: {skill_path}")

    # --- rs fixture integrity ---
    vectors_path = root / "fb" / "t" / "rs" / "tests" / "fixtures" / "vectors.json"
    try:
        vectors = load_json(vectors_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read rs fixture vectors: {exc}")
    else:
        for relative in sorted({item for item in iter_strings(vectors) if item.startswith("files/")}):
            if not (vectors_path.parent / relative).is_file():
                errors.append(f"rs fixture vector points at a missing file: {relative}")

    # --- repo hygiene ---
    errors.extend(check_utf8_no_bom(root))

    readme = root / "README.md"
    if not readme.is_file():
        errors.append("README.md is required")
    else:
        text = readme.read_text(encoding="utf-8")
        if "Codex app" not in text or "Codex CLI" not in text:
            errors.append("README must document both Codex app and Codex CLI installation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_release(args.root.resolve())
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Plugin release validation complete: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
