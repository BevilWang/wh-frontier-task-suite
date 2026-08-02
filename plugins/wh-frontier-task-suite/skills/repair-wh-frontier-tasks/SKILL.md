---
name: repair-wh-frontier-tasks
description: Read an independent second-AI review.json/review.md for a Frontier-Bench/Harbor three-task submission, verify that the report matches the current source fingerprint, reproduce and triage every finding, implement root-cause fixes across instructions, task metadata, environment, oracle solution, verifier tests, and packaging, rerun static/oracle/nop checks, and prepare the corrected submission for a fresh independent re-review. Use when asked to fix, address, resolve, remediate, or iterate on findings produced by verify-wh-frontier-tasks without blindly accepting stale or unsupported reviewer claims.
---

# Repair WH Frontier Tasks

Convert the independent review into verified code and task changes. Treat reviewer claims as hypotheses until reproduced; treat deterministic failures as authoritative evidence.

## Establish inputs and protect user work

Require the submission directory, `review.json`, its matching `evidence.json`, the selected reference task, and the Frontier-Bench checkout. Read [references/repair-playbook.md](references/repair-playbook.md).

Inspect repository status before editing. Preserve unrelated and pre-existing user changes. Never reset, overwrite, or delete them. Use a dedicated branch/worktree or a copied submission when the source contains ambiguous overlapping edits.

Validate report freshness and create the repair ledger:

```text
python scripts/repair_tool.py intake SUBMISSION REVIEW_JSON EVIDENCE_JSON \
  --output REPAIR_DIR/repair-ledger.json
```

Stop if the evidence fingerprint, report fingerprint, and current submission fingerprint differ. A stale report must be re-run with `$verify-wh-frontier-tasks`; do not force findings onto changed files.

## Triage every ledger item

Process blocker, major, minor, then info. Within a severity, fix shared root causes before task-local symptoms.

For each item:

1. Open every cited file and command log.
2. Reproduce the behavior using the smallest safe check.
3. Compare the claim with the live repository rubric and task contract.
4. Choose one decision:
   - `fixed`: the defect was reproduced and corrected;
   - `rejected`: evidence shows the reviewer claim is incorrect or conflicts with the source of truth;
   - `not_applicable`: the finding does not apply to this task shape;
   - `blocked`: a required external dependency, authority, or missing design choice prevents repair.
5. Record rationale, changed files, and validation evidence in the ledger.

Do not weaken the task merely to make tests pass. Do not delete difficult requirements, expose hidden truth, loosen tolerances without calibration, turn outcome checks into source matching, or mark unrun commands as passing.

## Fix by contract layer

Keep the intended real-world outcome stable while repairing the narrowest correct layer:

- If instruction and tests disagree, determine the intended contract from the task concept, oracle, package summary, and Frontier-Bench rules. Update both when ambiguity exists; never hide a test-only requirement.
- If the oracle fails, repair the legitimate solution or environment. Do not change tests to accept the broken oracle unless the verifier itself is demonstrably wrong.
- If nop or a shortcut passes, strengthen independent outcome verification and add a regression case without prescribing an unnecessary implementation method.
- If leakage exists, move truth and tests into the separate verifier and narrow artifacts; then rebuild the agent image and inspect it directly.
- If originality or difficulty fails, redesign the affected task substantially. Treat this as a concept-level repair, not a rename or parameter change.
- If verifier execution is unsafe, drop privileges, protect the reward channel, isolate agent code, clean process groups, keep binary rewards, and emit CTRF.

Apply edits with minimal scope. After each root-cause group, run targeted tests before moving on.

## Run the full regression gate

For every repaired task, run:

```text
for check in checks/check-*.sh; do bash "$check" TASK_PATH; done
harbor check TASK_PATH -r FRONTIER_BENCH/rubrics/task-implementation.toml
harbor run -p TASK_PATH --agent oracle
harbor run -p TASK_PATH --agent nop
```

Require oracle reward `1` and nop reward `0`. Repeat oracle at least five times for concurrent, nondeterministic, numerical, or timing-sensitive tasks. Re-run the creator skill's structural validator and inspect the final agent-visible image for leakage.

Update the package README with truthful post-repair validation status. Do not overwrite the old zip; create a new dated or revision-labeled archive only after all required checks pass.

## Close the ledger

Set `overall_status` to `complete` only when no item is pending or blocked. Validate:

```text
python scripts/repair_tool.py stamp-ledger REPAIR_DIR/repair-ledger.json SUBMISSION
python scripts/repair_tool.py validate-ledger REPAIR_DIR/repair-ledger.json SUBMISSION
```

A `fixed` item must name changed files and passing validation evidence. A `rejected` or `not_applicable` item must contain reproducible counter-evidence. A blocker/major item cannot disappear from the ledger.

Complete the top-level `regression` matrix with static, oracle, and nop commands and evidence for every task. `overall_status = complete` requires every regression entry to be `PASS`.

Write `repair.md` with finding-to-change mappings, commands and outcomes, residual limitations, and the new submission fingerprint. Avoid copying hidden expected values or large oracle excerpts.

## Require fresh independent re-review

When an orchestrator explicitly identifies the current agent as an isolated coordinator-invoked repairer, stop after producing and validating `repair-ledger.json`, `repair.md`, and the corrected fingerprint. Return control to the orchestrator; do not spawn a reviewer or begin another repair cycle.

Otherwise, run `$verify-wh-frontier-tasks` again with a fresh second AI and a new review directory. Do not pass it the old verdict, repair rationale, or expected outcome; give it the corrected raw submission and selected reference.

Mark the repair cycle ready only when the fresh report is `PASS`. If it is `FAIL`, start a new ledger from that new report. If it is `PROVISIONAL`, report exactly which runtime evidence is still missing rather than claiming completion.
