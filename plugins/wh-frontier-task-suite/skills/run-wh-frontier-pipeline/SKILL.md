---
name: run-wh-frontier-pipeline
description: Orchestrate the complete Frontier-Bench task lifecycle inside one Codex task by spawning isolated author, reviewer, repair, re-review, and release subagents. Use when the user wants to create three original tasks from a supported reference and complete independent review and repair without manually opening separate Codex tasks; when coordinating create-wh-frontier-tasks, verify-wh-frontier-tasks, and repair-wh-frontier-tasks; or when resuming a saved pipeline run from its artifact directories.
---

# Run WH Frontier Pipeline

Run the author-review-repair-release workflow as a coordinator. Keep stage decisions evidence-based and preserve reviewer independence through isolated subagent contexts and file-based handoffs.

## Require inputs

Obtain:

- a supported reference task path;
- a local Frontier-Bench checkout;
- a writable workspace root;
- owner, contact, and real submission date;
- an optional maximum repair-round count, defaulting to `2`.

Derive one run root under `WORKSPACE_ROOT/pipeline-runs/REFERENCE/DATE-TIME/` and use the final directory name as `RUN_ID`. Keep author output, reviews, repairs, release artifacts, and `pipeline-state.json` under that root. Record inputs, current state, agent names, artifact paths, verdicts, repair rounds, blockers, and final release metadata without storing hidden answers.

Read [references/orchestration-protocol.md](references/orchestration-protocol.md) before spawning any agent.

## Confirm orchestration support

Require the Codex collaboration tools for spawning and waiting on subagents. Use `spawn_agent` with `fork_turns="none"` for every stage agent. Do not use user-owned tasks or ask the user to open another task.

If subagent tools are unavailable, stop and state that this skill requires a Codex surface with multi-agent support. Do not simulate independent review in the coordinator context.

## Coordinate stages

### 1. Author

Spawn one isolated author agent named `frontier_author_RUN_ID`. Give it only the raw input paths, owner/contact/date, output path, and this instruction:

```text
Use $create-wh-frontier-tasks to create, validate, and prepare the complete three-task submission. Write only under <AUTHOR_OUTPUT> and permitted disposable build locations. Record exact validation evidence in the submission README. Return a concise status, but treat files on disk as authoritative.
```

Wait for completion. Inspect the produced submission and run the creator structural validator before continuing. Do not pass the author's reasoning or self-assessment to reviewers.

### 2. Independent review

Spawn a new isolated agent named `frontier_review_RUN_ID_r1`. Pass only the raw submission path, reference path, Frontier-Bench root, and review output path. Explicitly mark it as a coordinator-invoked isolated reviewer so `$verify-wh-frontier-tasks` performs the review directly instead of spawning another reviewer.

Wait for `review.json`, `review.md`, and evidence snapshots. Validate the report and source immutability with the verifier skill's scripts. Read the machine-readable verdict from disk; do not infer it from the agent's final message.

### 3. Decide

- On `PASS`, proceed to release.
- On `FAIL`, proceed to repair if the repair-round limit is not exhausted.
- On `PROVISIONAL`, retry only the missing checks that are feasible within existing authority. If the missing evidence requires unavailable infrastructure, credentials, or user authority, stop with a precise blocker. Do not turn `PROVISIONAL` into `PASS`.
- On an invalid or missing report, send one follow-up to the same reviewer to complete or correct the report. If it still fails validation, stop the run as blocked.

### 4. Repair

Spawn a new isolated agent named `frontier_repair_RUN_ID_rN`. Give it the submission, reference, validated review, evidence snapshot, repair output, and Frontier-Bench paths. Explicitly identify it as a coordinator-invoked isolated repairer so `$repair-wh-frontier-tasks` returns control after the validated ledger instead of spawning a reviewer. Instruct it to preserve the original review and update only the submission and repair directory.

Wait for a valid `repair-ledger.json` and corrected submission fingerprint. Run the repair ledger validator. Do not accept a repair status based only on prose.

### 5. Fresh re-review

Spawn a new isolated agent named `frontier_review_RUN_ID_rN+1`. Pass the corrected raw submission, reference, Frontier-Bench root, and a new `from-scratch/` review directory. Do not pass the old verdict, old review path, repair ledger path, author summary, repair rationale, or expected outcome in the initial prompt.

Instruct the reviewer to perform a direct review and write a complete, validated assessment under `from-scratch/`. Validate that report and source immutability before revealing prior-cycle artifacts.

Then use `followup_task` on the same reviewer. Provide the previous review and validated `repair-ledger.json`; instruct it to verify closure and regressions without erasing its recorded independent assessment, and to write the authoritative report under `closure/`. Validate the closure report and source immutability. Use only the closure report as the stage verdict.

Loop through repair and fresh re-review until a review returns `PASS` or the repair-round limit is exhausted.

### 6. Release

After a validated fresh `PASS`, confirm the live submission fingerprint still equals the passing review fingerprint. Create an immutable release snapshot or a disposable copy whose fingerprint matches that review. All metadata, cleanup, and content changes must have occurred before the passing review.

Spawn one isolated release agent named `frontier_release_RUN_ID`. Give it only the immutable reviewed snapshot, passing review, Frontier-Bench root, and release directory. Instruct it to use `$create-wh-frontier-tasks` only for read-only final validation, bit-for-bit packaging, checksum generation, clean extraction, and smoke testing. It must not redesign, edit, clean, rename, or update the reviewed submission.

Fingerprint the extracted archive submission and require it to equal the passing review fingerprint. If release validation discovers a required content change, stop release, return the submission to a new repair round, and require another fresh review. Verify the final archive exists and record its hash, inventory, fingerprint comparison, and smoke-test evidence. Update `pipeline-state.json` after every terminal stage transition so an interrupted run can be audited or resumed without relying on conversation history.

## Report to the user

Return:

- the selected reference and run root;
- each spawned agent and stage status;
- every review verdict and repair round;
- the final archive and checksum when released;
- commands and checks actually run;
- unresolved blockers or residual risks.

Do not claim completion unless the final independent review is `PASS` and release validation succeeds.
