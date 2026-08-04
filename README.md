# WH Frontier Task Suite

A Codex plugin for authoring, hardening, independently reviewing, repairing, and releasing three original Frontier-Bench/Harbor tasks from one bundled reference.

## What it does

The plugin turns a single reference task into a complete three-task submission:

- **Author** an original objective, agent environment, oracle solution, verifier, and metadata for each task.
- **Harden** the submission with contract, input-domain, adversarial, and runtime sweeps before review.
- **Review** with a fresh independent AI plus deterministic oracle, nop, and static checks.
- **Repair** from validated findings and re-review until the submission passes.
- **Release** an immutable archive whose fingerprint matches the passing review.

The plugin bundles the reference tasks, validation scripts, and review tooling, so no separate Frontier-Bench checkout is required.

## Supported references

| Category | Reference |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

## Installation

### Codex app

1. Open this repository in the Codex app.
2. Restart Codex so it loads `.agents/plugins/marketplace.json`.
3. Go to **Plugins**, find **WH Frontier Task Suite**, and install it.

### Codex CLI

Add the repository as a marketplace and install the plugin:

```bash
codex plugin marketplace add .
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

Or install from the remote URL after pushing:

```bash
codex plugin marketplace add https://github.com/BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

Run `codex plugin marketplace list` to confirm the marketplace name if it differs.

See [docs/app-install.md](docs/app-install.md) for the full guide and a post-install verification checklist.

## Skills

After installation, start a new Codex task and invoke any of the four skills:

| Skill | Use when you want to ... |
| --- | --- |
| `$run-wh-frontier-pipeline` | Run the complete lifecycle from authoring through release. |
| `$create-wh-frontier-tasks` | Create or validate a three-task submission on its own. |
| `$verify-wh-frontier-tasks` | Audit an existing three-task submission independently. |
| `$repair-wh-frontier-tasks` | Fix findings from an independent review and prepare for re-review. |

## Quick start

```text
Use $run-wh-frontier-pipeline.

Reference: wal-recovery-ordering
Workspace root: E:\path\to\writable-workspace
Owner: Your Name
Contact: name@example.com
Submission date: 20260805
```

By default the pipeline repairs and re-reviews up to 5 rounds. Add `Maximum repair rounds: N` to cap it.

## Requirements

- Codex app or Codex CLI
- Python 3.12+
- Docker Desktop with the daemon running
- Harbor CLI (`python -m uv tool install harbor`)
- A writable workspace directory

On Windows, set UTF-8 variables and restart Codex:

```powershell
setx PYTHONUTF8 1
setx PYTHONIOENCODING utf-8
```

## Development

The repository is fully self-testing with only the Python standard library:

```powershell
python scripts/run_all_tests.py                                # all unit tests
python scripts/validate_plugin_release.py                      # manifest + marketplace + repo hygiene
python scripts/validate_windows_paths.py                       # Windows-safe path budget
python skills/create-wh-frontier-tasks/scripts/validate_reference_bundle.py fb  # bundled references
```

GitHub Actions runs all four on every push and pull request (Windows and Ubuntu).

## Repository layout

```text
.
├── .codex-plugin/plugin.json   # plugin manifest
├── .agents/plugins/marketplace.json  # Codex app marketplace entry
├── .github/workflows/ci.yml    # Windows + Ubuntu CI matrix
├── .gitattributes              # LF line endings for scripts and config
├── skills/                     # four Codex skills
├── fb/                         # bundled Frontier-Bench snapshot
├── docs/                       # installation and usage docs
├── scripts/                    # repository validation helpers
├── LICENSE                     # MIT license for this project
├── README.md                   # this file
└── THIRD_PARTY_NOTICES.md      # third-party attribution
```

## License and provenance

This project (plugin code, skills, and tooling) is licensed under the [MIT License](LICENSE).

The built-in reference materials come from [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench) and are distributed under the Apache License 2.0. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [fb/PROVENANCE.md](fb/PROVENANCE.md) for details.
