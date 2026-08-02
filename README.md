# WH Frontier Task Suite

WH Frontier Task Suite is a Codex plugin for authoring, independently reviewing, and repairing Frontier-Bench/Harbor benchmark submissions.

It turns a reference task into a disciplined four-stage workflow:

```text
Author three original tasks -> independent review -> evidence-driven repair -> fresh re-review
```

The plugin combines procedural skills with deterministic helper scripts for submission scaffolding, structural validation, evidence snapshots, review reports, and repair ledgers.

## What is included

### `$create-wh-frontier-tasks`

Creates, implements, validates, and packages exactly three original benchmark tasks from one supported reference. The skill covers:

- concept design and originality gates;
- task instructions, metadata, environment, oracle solution, and verifier tests;
- static checks, oracle/nop runs, leakage checks, and shortcut resistance;
- submission layout and reproducible archive generation.

### `$verify-wh-frontier-tasks`

Runs a read-only second review with a fresh AI reviewer and deterministic evidence. It checks:

- originality relative to the selected reference;
- specification-to-test alignment;
- clean-build solvability and nop resistance;
- verifier quality, isolation, leakage, security, and packaging;
- source immutability throughout the review.

The review produces `evidence.json`, `review.json`, and `review.md`, with an overall verdict of `PASS`, `FAIL`, or `PROVISIONAL`.

### `$repair-wh-frontier-tasks`

Consumes an independent review, verifies that it matches the current source fingerprint, reproduces each finding, repairs root causes, runs the full regression gate, and produces an auditable repair ledger. A repaired submission must return to a fresh reviewer before it can be accepted.

## Supported reference tasks

| Domain | Reference task |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

Each reference profile preserves only transferable difficulty mechanisms. New tasks must use original objectives, systems or data, reasoning paths, artifacts, hidden variations, and verifier logic.

## Installation

Install the repository as a Git marketplace, then install the plugin:

```bash
codex plugin marketplace add BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

Start a new Codex task after installation so the three skills are loaded into context.

To update:

```bash
codex plugin marketplace upgrade wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

## Quick start

1. Clone or otherwise provide a local Frontier-Bench checkout.
2. Choose one supported reference task.
3. Open a new Codex task and invoke `$create-wh-frontier-tasks` with the reference path and an output directory.
4. Open a separate Codex task with no authoring context and invoke `$verify-wh-frontier-tasks`.
5. If the verdict is not `PASS`, invoke `$repair-wh-frontier-tasks` in a writable task.
6. Run `$verify-wh-frontier-tasks` again in another fresh task.
7. Package only after the fresh review returns `PASS`. `PROVISIONAL` is not a pass.

Ready-to-copy prompts for all seven reference domains and every workflow stage are available in [docs/prompts.md](docs/prompts.md).

## Repository layout

```text
.
|-- .agents/plugins/marketplace.json
|-- docs/prompts.md
`-- plugins/wh-frontier-task-suite/
    |-- .codex-plugin/plugin.json
    `-- skills/
        |-- create-wh-frontier-tasks/
        |-- verify-wh-frontier-tasks/
        `-- repair-wh-frontier-tasks/
```

## Output contract

The authoring skill creates:

```text
OWNER_submission/
|-- README.md
|-- task-1-short-name/
|-- task-2-short-name/
`-- task-3-short-name/
```

Each task contains `instruction.md`, `task.toml`, `environment/`, `solution/`, and `tests/`. The packaged archive is named `OWNER_Category_Subcategory_YYYYMMDD.zip`.

## Local validation

Run the bundled unit tests:

```bash
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/verify-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/repair-wh-frontier-tasks/scripts -p "test_*.py"
```

During plugin development, validate the plugin with `plugin-creator/scripts/validate_plugin.py` and validate each skill with `skill-creator/scripts/quick_validate.py` from a Codex installation.

## Review integrity

- The independent reviewer receives raw artifacts, not the author's conclusions.
- Commands that may write run against disposable copies.
- Required runtime checks cannot be replaced by source inspection.
- Hidden verifier data and oracle internals stay out of human-facing reports.
- A missing required runtime check yields `PROVISIONAL`, unless observed defects already require `FAIL`.
- A repaired submission always returns to a fresh independent reviewer.
