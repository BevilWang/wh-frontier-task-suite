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

## Excluded material

- `tasks/ks-solver-cpp/tests/wheels/**`

The excluded wheel files are large prebuilt dependencies and are not needed to inspect the reference task or author new tasks. Other included upstream files are copied without modification. This snapshot is intended as an authoring and review reference bundle; executing an upstream task may still require Harbor, Docker, and dependencies documented by that task.
