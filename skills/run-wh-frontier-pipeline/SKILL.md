---
name: run-wh-frontier-pipeline
description: Orchestrate the complete Frontier-Bench task lifecycle inside one Codex task by spawning isolated author, hardener, reviewer, repair, re-review, and release subagents against the plugin's bundled references. Use when the user wants three original tasks carried through exhaustive independent review, evidence-backed repair, and immutable release; when coordinating create-wh-frontier-tasks, verify-wh-frontier-tasks, and repair-wh-frontier-tasks; or when resuming a saved pipeline run.
---

# Run WH Frontier Pipeline

Coordinate an evidence-gated author-hardening-review-repair-release workflow. Preserve reviewer independence, keep one writer at a time, and treat validated disk artifacts as authoritative.

## Resolve inputs and run root

Require a supported reference, writable workspace root, owner, contact, and real submission date. If the user does not supply a maximum repair-round count, default to a safety cap of **5 repair rounds**. Stop with `BLOCKED` when that cap is reached and tell the user exactly how to resume with a higher cap. When a cap is supplied, keep repairing and independently re-reviewing until a validated `PASS` or a genuine external blocker.
 Resolve the bundled Frontier-Bench root as `../../fb`; validate it with the creator skill's `validate_reference_bundle.py --reference ... --json` and use its returned semantic paths.

Before authoring, run the creator skill's runnability report for the chosen reference and relay the profile to the user:

```text
python skills/create-wh-frontier-tasks/scripts/runnability_report.py BUNDLED_FRONTIER_ROOT --reference REFERENCE
```

Surface image size, build-time network needs, compute class, and the validation wall-clock estimate. Warn when the reference is heavy (`biped-contact-dynamics`, `vllm-deepseek-streaming`) or needs network at build (`lean-midpoint-proof`, `biped-contact-dynamics`, `vllm-deepseek-streaming`). For `ks-solver-cpp`, note that the upstream reference verifier needs restored wheels only if the user wants to execute that reference for calibration; authoring new tasks does not require it. Record the profile in `pipeline-state.json`.

Create `WORKSPACE_ROOT/pipeline-runs/REFERENCE/DATE-TIME/` and use the last directory as `RUN_ID`. Keep author output, hardening evidence, reviews, repairs, release artifacts, and `pipeline-state.json` there. Record every spawned agent, stage transition, fingerprint, verdict, repair count, command outcome, blocker, and release artifact. Never store hidden answers in state.

Read [references/orchestration-protocol.md](references/orchestration-protocol.md) before spawning. Require collaboration tools and use `fork_turns="none"` for every stage agent.

## Preflight runtime

Before authoring and again before every stage that needs execution:

1. On Windows set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` for Harbor commands.
2. Require `harbor --version` and `docker version` to succeed. If Docker is installed but stopped, request only the approval needed to start Docker Desktop, then retry. Do not spend a review or repair round on an infrastructure-only failure that can be corrected first.
3. Record available Bash/static-check support. On Windows long-path failures, use a disposable short root containing short task aliases, a copied rubric, and an explicit short `--jobs-dir`; optionally map that root with `subst`. Keep the reviewed submission immutable and remove only the disposable mapping afterward.
4. If required infrastructure remains unavailable, record `PROVISIONAL` evidence and stop unless the user supplies the missing authority or service.

Respect the host sandbox. Never disable it, request blanket bypasses, or redirect output into the plugin cache.

## 1. Author without packaging

Derive a fresh design seed for this run (e.g., from `RUN_ID` or a random value,
unless the user supplied one) and record it in `pipeline-state.json`. Before
spawning the author, sample the design direction family with the creator
skill's `select_variant.py`; check prior runs of this reference under
`WORKSPACE_ROOT/pipeline-runs/REFERENCE/` and avoid reusing a family from a
recent run. Record the chosen seed and variant in `pipeline-state.json` and
pass both through to the author.

Spawn `frontier_author_RUN_ID` with raw input paths and:

```text
Use $create-wh-frontier-tasks to create and validate the complete unpacked three-task submission. Design seed: <SEED>. Design variant: <VARIANT>. Write only under <AUTHOR_OUTPUT> and permitted disposable build locations. Complete all four author hardening sweeps and record exact evidence. Do not create a zip; packaging belongs only to the release stage.
```

Wait for completion. Run the creator validator, require zero errors, and resolve every warning or record concrete counter-evidence. Confirm the submission has exactly three tasks named `task-N-<single-token-slug>`. An author-created zip is stale-by-design and must never be treated as a release artifact.


## 2. Fresh pre-review hardening

Before the counted independent review, spawn a new writer `frontier_hardener_RUN_ID`. Pass the raw submission, raw reference, standards, the selected profile's reference-specific hardening checklist, and a hardening output directory, but no author reasoning. Instruct it to use `$create-wh-frontier-tasks` for a full adversarial author gate: contract-test matrices, input/domain totality and accepted-state tracing, generated/hidden verifier depth, exact unprivileged CTRF/reward execution, oracle/nop, leakage, and shortcut probes. It may fix defects and must leave evidence under the hardening directory; it must not package.

Wait, rerun the structural validator **and every bundled static check that can execute on the host**, fingerprint the hardened submission, and update state. If the hardener cannot produce a structurally valid submission, do not consume a review round; return to author or stop. This stage is not an independent verdict and does not consume a repair round. Its purpose is to remove preventable author defects before reviewer budget begins.


## 3. Exhaustive independent review

Spawn `frontier_review_RUN_ID_r1` as a coordinator-invoked isolated reviewer. Pass only the raw hardened submission, raw reference, resolved Frontier-Bench root, evidence path, and review output. Require `$verify-wh-frontier-tasks` schema-2 output and explicitly require the reviewer to continue after the first blocker and finish all four source sweeps for all three tasks.

Wait for `evidence.json`, `review.json`, `review.md`, and the post-review fingerprint. Validate the report and source immutability with the verifier scripts. Read the verdict from the validated JSON, never from prose.

## 4. Decide

- `PASS`: proceed to release.
- `FAIL`: repair if the repair budget remains.
- `PROVISIONAL`: retry only missing checks after re-running runtime preflight. If infrastructure or authority remains unavailable, stop precisely; never convert it to `PASS`.
- Invalid/missing report: follow up once with the same reviewer. Stop if it remains invalid.

## 5. Repair with full hardening halo

For repair round `N`, spawn `frontier_repair_RUN_ID_rN` with the submission, validated authoritative review, matching evidence, reference paths, and repair directory. Identify it as a coordinator-invoked isolated repairer. Require `$repair-wh-frontier-tasks` schema-2 output, root-cause fixes, and all four hardening sweeps for every task, including tasks not named in the finding.

Wait for a valid `repair-ledger.json`, `repair.md`, and new fingerprint. Validate the ledger. Do not accept prose or a targeted regression alone; the ledger must preserve imported items and record contract matrix, input/domain totality, adversarial verifier, repair halo, static, oracle, and nop evidence, including the selected profile's reference-specific risks.

## 6. Fresh re-review and closure

Spawn `frontier_review_RUN_ID_rN+1` with only the corrected raw submission, raw reference, root, and new `from-scratch/` directory. Do not disclose previous verdicts, findings, ledger, rationale, or desired outcome. Require a complete schema-2 from-scratch report and validate it before revealing prior-cycle artifacts.

Then use `followup_task` on the same reviewer with the previous review and validated repair ledger. Require closure/regression verification without erasing the recorded from-scratch assessment; write the authoritative report under `closure/`. Validate the closure report and immutability. Use only the closure verdict.

Loop through repair and re-review until `PASS` or until the repair cap is reached. Track the fingerprint of open blocker/major findings; if the same blocker recurs in two consecutive repair rounds without new evidence of progress, stop with `BLOCKED` to prevent endless oscillation. Stop only for a genuine external blocker, repeated invalid stage artifacts after the defined retry, an explicit user-supplied repair cap being exhausted, or repeated finding fingerprints. If an explicit cap is exhausted, mark `BLOCKED`, preserve the latest narrow findings, and state exactly how to resume after raising or removing that cap. Never release a stale author zip.


## 7. Immutable release

After a validated fresh `PASS`, require the live fingerprint to equal the passing review fingerprint. Create an immutable snapshot or disposable bit-identical copy. All content changes must precede the passing review.

Spawn `frontier_release_RUN_ID` with only the reviewed snapshot, passing review, Frontier-Bench root, and release directory. Instruct it to use `$create-wh-frontier-tasks` only for read-only final validation, bit-for-bit packaging, checksum, clean extraction, fingerprint comparison, and smoke testing. It must not edit, clean, rename, or update reviewed content.

Require the archive, extracted submission, and passing review fingerprints to match. If release discovers a required content change, return to repair plus fresh review. Update `pipeline-state.json` after every terminal stage and include every agent actually spawned.

## Report

Return the reference and run root; runtime preflight; every agent/stage; every verdict and repair round; commands and observed evidence; final archive/checksum/fingerprint when released; and unresolved blockers or resume instructions. Claim completion only after fresh `PASS` and successful immutable release.
