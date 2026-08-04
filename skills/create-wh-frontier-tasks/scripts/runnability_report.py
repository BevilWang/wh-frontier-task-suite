#!/usr/bin/env python3
"""Report per-reference runnability for the bundled Frontier-Bench snapshot.

For every supported reference this prints (or emits as JSON) a profile with:

- whether every local COPY/ADD source in the reference's Dockerfiles exists;
- network requirements at image build time (beyond the base image pull);
- compute class (cpu vs gpu) and an estimated image size class;
- verifier tooling and timeouts parsed from task.toml;
- a recommended oracle-run count and an estimated validation wall-clock.

This lets the pipeline and users pick a reference they can actually build and
validate on their hardware before authoring, and surfaces known snapshot gaps
(for example the deliberately excluded ks-solver-cpp wheels).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

from validate_reference_bundle import TASK_PATHS, TASKS, bundle_paths, is_short_layout

# References whose verifier or environment needs repeated oracle runs because
# of concurrency, timing, or numerical nondeterminism (see create skill).
ORACLE_RUNS: dict[str, int] = {
    "wal-recovery-ordering": 5,
    "ontology-kg-querying": 5,
    "rs-archive-clone": 3,
    "lean-midpoint-proof": 2,
    "ks-solver-cpp": 5,
    "vllm-deepseek-streaming": 5,
    "biped-contact-dynamics": 3,
}

# Documented snapshot exclusions (see fb/PROVENANCE.md). Each entry explains
# what is missing and how to make the reference runnable again.
KNOWN_GAPS: dict[str, list[str]] = {
    "ks-solver-cpp": [
        "tests/wheels/*.whl excluded from the snapshot; the reference verifier "
        "image cannot build until restored with: python scripts/restore_ks_wheels.py"
    ],
}

SIZE_CLASS_KEYWORDS = {
    "very-large": ("vllm",),
    "large": ("drake", "pytorch", "tensorflow"),
    "medium": ("elan", "lean", "rust", "node:"),
}

IMAGE_FETCH_NOTE = "base image pull (FROM)"

NETWORK_PATTERNS = (
    (re.compile(r"\bapt-get\s+install\b"), "apt-get install"),
    (re.compile(r"\bpip\s+install\b"), "pip install"),
    (re.compile(r"\bpip3\s+install\b"), "pip3 install"),
    (re.compile(r"\bcurl\b"), "curl"),
    (re.compile(r"\bwget\b"), "wget"),
    (re.compile(r"\bgit\s+clone\b"), "git clone"),
    (re.compile(r"\belan\b"), "elan toolchain download"),
    (re.compile(r"\bcargo\s+install\b"), "cargo install"),
)

COPY_RE = re.compile(
    r"^\s*(?:COPY|ADD)"
    r"(?:\s+--[a-z0-9-]+(?:=[^\s]+)?)*"
    r"(?:\s+--from=[^\s]+)*"
    r"\s+(?P<sources>.+?)\s+[^\s]+\s*$",
    re.IGNORECASE,
)
REMOTE_SOURCE = re.compile(r"^(https?://|--from=)", re.IGNORECASE)


@dataclass
class CopySource:
    source: str
    exists: bool
    note: str = ""


@dataclass
class DockerfileProfile:
    path: str
    exists: bool = False
    base_image: str = ""
    copy_sources: list[CopySource] = field(default_factory=list)
    network_reasons: list[str] = field(default_factory=list)


@dataclass
class RunnabilityProfile:
    reference: str
    task: str
    compute: str = "cpu"
    image_size_class: str = "small"
    network_build: bool = True
    network_reasons: list[str] = field(default_factory=list)
    dockerfiles: list[DockerfileProfile] = field(default_factory=list)
    verifier: dict = field(default_factory=dict)
    oracle_runs_recommended: int = 1
    validation_hint_sec: int = 0
    known_gaps: list[str] = field(default_factory=list)


def parse_dockerfile(path: Path, task: Path) -> DockerfileProfile:
    profile = DockerfileProfile(path=path.relative_to(task).as_posix())
    if not path.is_file():
        return profile
    profile.exists = True
    context = path.parent
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for raw in lines:
        line = raw.strip()
        if line.lower().startswith("from "):
            profile.base_image = line.split(None, 2)[1] if len(line.split()) > 1 else ""
            continue
        match = COPY_RE.match(line)
        if not match:
            continue
        sources = match.group("sources").split()
        if not sources:
            continue
        for source in sources:
            if REMOTE_SOURCE.match(source) or source.startswith("/"):
                continue
            resolved = (context / source).resolve()
            # Tolerate globs by checking the parent directory exists.
            probe = resolved
            if "*" in source or "?" in source:
                probe = resolved.parent if resolved.name else resolved
            exists = probe.exists()
            note = ""
            if not exists:
                note = "missing from snapshot build context"
            profile.copy_sources.append(CopySource(source=source, exists=exists, note=note))
    for pattern, label in NETWORK_PATTERNS:
        if pattern.search(text):
            profile.network_reasons.append(label)
    return profile


def _toml_timeout(task: Path, section: str, key: str) -> float | None:
    toml_path = task / "task.toml"
    if not toml_path.is_file():
        return None
    try:
        with toml_path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    value = data.get(section, {}).get(key)
    return float(value) if isinstance(value, (int, float)) else None


def profile_reference(root: Path, reference: str) -> RunnabilityProfile:
    task = bundle_paths(root, reference)["task"]
    profile = RunnabilityProfile(
        reference=reference,
        task=str(task).replace("\\", "/"),
        oracle_runs_recommended=ORACLE_RUNS.get(reference, 1),
    )
    dockerfiles: list[DockerfileProfile] = []
    for name in ("environment/Dockerfile", "tests/Dockerfile"):
        dockerfiles.append(parse_dockerfile(task / name, task))
    profile.dockerfiles = dockerfiles

    all_text = "\n".join(
        (task / dockerfile.path).read_text(encoding="utf-8", errors="replace")
        for dockerfile in dockerfiles
        if dockerfile.exists
    )

    # Compute class and size class.
    if re.search(r"nvidia|\bcuda\b|\bgpu\b", all_text, re.IGNORECASE):
        profile.compute = "gpu"
    profile.image_size_class = "small"
    for size, keywords in SIZE_CLASS_KEYWORDS.items():
        if any(keyword in all_text.lower() for keyword in keywords):
            profile.image_size_class = size
            break

    # Network requirements: every reference pulls a base image; anything else
    # that fetches packages/tools at build time is listed separately.
    reasons = [IMAGE_FETCH_NOTE]
    seen: set[str] = set()
    for dockerfile in dockerfiles:
        for reason in dockerfile.network_reasons:
            if reason not in seen:
                seen.add(reason)
                reasons.append(reason)
    profile.network_reasons = reasons
    profile.network_build = True  # base image pull always requires network unless cached

    # Verifier tooling and timeouts.
    test_sh = task / "tests" / "test.sh"
    tooling = "plain"
    if test_sh.is_file():
        text = test_sh.read_text(encoding="utf-8", errors="replace")
        if "--ctrf" in text and re.search(r"\bpytest\b", text):
            tooling = "pytest-ctrf"
        elif re.search(r"\bpytest\b", text):
            tooling = "pytest"
    profile.verifier = {
        "tooling": tooling,
        "timeout_sec": _toml_timeout(task, "verifier", "timeout_sec"),
        "agent_timeout_sec": _toml_timeout(task, "agent", "timeout_sec"),
        "build_timeout_sec": _toml_timeout(task, "environment", "build_timeout_sec"),
        "environment_mode": _environment_mode(task),
    }

    verifier_timeout = profile.verifier.get("timeout_sec") or 0.0
    profile.validation_hint_sec = int(
        (profile.oracle_runs_recommended + 1) * verifier_timeout
    )
    profile.known_gaps = KNOWN_GAPS.get(reference, [])
    return profile


def _environment_mode(task: Path) -> str | None:
    toml_path = task / "task.toml"
    if not toml_path.is_file():
        return None
    try:
        with toml_path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    value = data.get("verifier", {}).get("environment_mode")
    return value if isinstance(value, str) else None


def format_human(profile: RunnabilityProfile) -> str:
    gaps = "; ".join(profile.known_gaps) if profile.known_gaps else "-"
    verifier = profile.verifier
    def fmt(key: str) -> str:
        value = verifier.get(key)
        return "-" if value is None else f"{value:g}"
    hours = profile.validation_hint_sec / 3600
    return (
        f"{profile.reference}\n"
        f"  compute       : {profile.compute}\n"
        f"  image size    : {profile.image_size_class}\n"
        f"  build network : {', '.join(profile.network_reasons)}\n"
        f"  verifier      : tooling={verifier.get('tooling')} timeout={fmt('timeout_sec')}s "
        f"mode={verifier.get('environment_mode')}\n"
        f"  agent timeout : {fmt('agent_timeout_sec')}s\n"
        f"  validation    : {profile.oracle_runs_recommended}+1 runs ~ {profile.validation_hint_sec}s "
        f"(~{hours:.1f}h) plus image build\n"
        f"  known gaps    : {gaps}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="bundled or canonical Frontier-Bench root")
    parser.add_argument("--reference", choices=TASKS, help="profile a single reference")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a human table")
    args = parser.parse_args()
    root = args.root.resolve()
    if not is_short_layout(root):
        print("runnability profile supports the bundled short layout only", file=sys.stderr)
        return 2
    references = [args.reference] if args.reference else list(TASKS)
    profiles = [profile_reference(root, reference) for reference in references]
    if args.json:
        print(json.dumps([asdict(profile) for profile in profiles], indent=2))
    else:
        for profile in profiles:
            print(format_human(profile))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
