# WH Frontier Task Suite

WH Frontier Task Suite is a Codex plugin for authoring, independently reviewing, and repairing Frontier-Bench/Harbor benchmark submissions.

It turns a reference task into a coordinated multi-agent workflow inside one Codex task:

```text
Author three original tasks -> independent review -> evidence-driven repair -> fresh re-review
```

The coordinator spawns isolated author, reviewer, repair, re-review, and release subagents. Stages exchange validated filesystem artifacts instead of conversation summaries, preserving reviewer independence without requiring the user to open separate tasks.

The plugin combines procedural skills with deterministic helper scripts for submission scaffolding, structural validation, evidence snapshots, review reports, and repair ledgers.

## What is included

### `$run-wh-frontier-pipeline`

Runs the complete lifecycle from one user-facing task. It:

- starts every stage agent with an empty inherited conversation context;
- prevents concurrent writers from editing the same submission;
- passes raw artifact paths rather than author conclusions;
- validates review reports, source fingerprints, and repair ledgers between stages;
- loops through repair and fresh re-review up to a configured limit;
- releases only after a validated independent `PASS`.

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

Start a new Codex task after installation so all four skills are loaded into context. The coordinator requires a Codex surface with subagent collaboration tools.

To update:

```bash
codex plugin marketplace upgrade wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

## One-task quick start

1. Clone or otherwise provide a local Frontier-Bench checkout.
2. Choose one supported reference task.
3. Open one Codex task and invoke `$run-wh-frontier-pipeline` with the reference path, workspace, owner, contact, and date.
4. Let the coordinator spawn and supervise the isolated stage agents.
5. Respond only if Codex requests authority that the agents do not already have.

Example:

```text
Use $run-wh-frontier-pipeline to create and release a complete submission.

Reference task: /path/to/frontier-bench/tasks/wal-recovery-ordering
Frontier-Bench checkout: /path/to/frontier-bench
Workspace root: /path/to/workspace
Owner: example-owner
Contact: owner@example.com
Submission date: 20260802
Maximum repair rounds: 2
```

The three specialist skills remain available for manual or partial workflows, but normal use should start with the coordinator.

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
        |-- run-wh-frontier-pipeline/
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
