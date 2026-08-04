# Frontier-Bench vendored snapshot

- Upstream repository: https://github.com/harbor-framework/frontier-bench
- Upstream commit: `3d694e919871dbf21ea5ff618782c99a3cb3663f`
- Snapshot date: 2026-08-02
- Upstream license: Apache License 2.0

## Included material

- `CONTRIBUTING.md`
- `docs/`
- `rubrics/`
- `checks/`
- The following task directories:
  - `wal-recovery-ordering`
  - `ontology-kg-querying`
  - `rs-archive-clone`
  - `lean-midpoint-proof`
  - `ks-solver-cpp`
  - `vllm-deepseek-streaming`
  - `biped-contact-dynamics`

## Windows-safe storage layout

The plugin stores this snapshot under `fb/` with short physical directory names: `c/` (checks), `d/` (docs), `r/` (rubrics), and `t/` (tasks). Task directories use `wr`, `kg`, `rs`, `lm`, `ks`, `vs`, and `bd`, in the same order as the full names above. This path-only repackaging keeps Git marketplace checkouts below the traditional Windows `MAX_PATH` limit without requiring `core.longpaths`; users continue to select references by their full upstream names. The validation resolver also accepts the canonical upstream layout on Windows, macOS, and Linux.

## Excluded material

- `tasks/ks-solver-cpp/tests/wheels/**`

The excluded wheel files are large prebuilt dependencies and are not needed to inspect the reference task or author new tasks. File contents remain upstream copies apart from this provenance note; only containing directory names were shortened. This snapshot is intended as an authoring and review reference bundle; executing an upstream task may still require Harbor, Docker, and dependencies documented by that task.

## Restoring excluded wheels (ks-solver-cpp)

`tasks/ks-solver-cpp/tests/wheels/**` is intentionally excluded from this
snapshot (large prebuilt dependencies). The reference's verifier image cannot
build until the directory is recreated from pinned PyPI wheels:

```text
python scripts/restore_ks_wheels.py --check   # status report, no network
python scripts/restore_ks_wheels.py           # download pinned numpy/scipy wheels
```

This is only needed to execute the upstream ks reference for calibration.
Authoring new tasks reads the reference and never requires running it; authored
tasks carry their own self-contained, pinned verifier dependencies.

## Runnability profiles

Each reference's build/run requirements (image size, build-time network,
compute class, verifier tooling, validation wall-clock) are reported by:

```text
python skills/create-wh-frontier-tasks/scripts/runnability_report.py fb [--reference REFERENCE]
```

All seven references validate on CPU with Docker and need network at image build
time. `lean-midpoint-proof` additionally downloads the Lean toolchain via elan,
`biped-contact-dynamics` installs the large drake wheel, and
`vllm-deepseek-streaming` pulls the multi-GB vLLM CPU image (no GPU or model
weights required). See `skills/create-wh-frontier-tasks/references/reference-profiles.md`.
