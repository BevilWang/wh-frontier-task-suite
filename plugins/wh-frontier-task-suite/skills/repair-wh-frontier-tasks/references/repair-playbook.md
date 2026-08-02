# Report-driven repair playbook

Use the live Frontier-Bench checkout as the source of truth. Keep the original review immutable and record all decisions in `repair-ledger.json`.

## Evidence hierarchy

Prefer evidence in this order:

1. Reproducible oracle/nop/static execution result.
2. Current repository checks, rubric, templates, and Harbor behavior.
3. Direct inspection of built agent and verifier environments.
4. Bidirectional instruction-test mapping and independent calculations.
5. Reviewer interpretation.

An AI concern without reproduction can justify investigation, but not a destructive redesign by itself.

## Structure and packaging

Repair missing files, names, metadata, canary, absolute paths, README fields, and archive layout. Remove only confirmed caches, build products, and unrelated artifacts. Preserve licensed or runtime-referenced data.

## Originality and difficulty

Concept-level failures require concept-level changes. Rewrite the objective, data/system, core reasoning, artifact, hidden variation, or verifier, not just names or constants. Recheck all three tasks for accidental convergence after redesign. Ensure an expert solution remains achievable in hours.

## Specification-test alignment

Create two lists: instruction requirements and test behaviors. Map both directions. For a hidden test requirement, either disclose the outcome contract or remove the accidental assertion. For an untested promise, add a meaningful test. Prefer functional invariants and hidden variants over source-string checks.

## Oracle and solvability

Reproduce from a clean build. Fix dependencies, paths, resource declarations, algorithms, determinism, or data generation at their source. Never let the oracle read verifier-only truth. Calibrate numerical tolerances from justified error bounds and repeated runs.

## Nop and reward hacking

Add regressions for the actual shortcut: empty/constant output, copied input, visible fixture lookup, malformed artifacts, input mutation, test discovery, reward overwrite, daemon survival, or agent-controlled expected values. Keep the verifier method-agnostic when possible.

## Verifier quality and isolation

Use a separate verifier, narrow artifacts, verifier-owned hidden inputs, unprivileged execution, a root-only reward directory, process-group cleanup, binary reward writes, CTRF for discrete suites, pinned/baked verifier tooling, and loud dependency failures.

## Decision standards

- `fixed`: reproduced, changed at root cause, targeted regression passes, and no existing check regresses.
- `rejected`: current source-of-truth evidence directly disproves the finding; document commands/lines.
- `not_applicable`: the criterion genuinely does not apply; explain the task shape.
- `blocked`: completion requires unavailable infrastructure, user authority, external data, or a material product decision.

Do not use `rejected` merely because a fix is difficult. Do not use `fixed` when validation is `NOT_RUN`.

## Closure standard

Require all blocker/major items to be fixed, rejected with strong counter-evidence, or explicitly blocked. A blocked material item prevents completion. Require full static, oracle, and nop evidence before packaging and fresh independent re-review before declaring readiness.
