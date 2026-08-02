---
name: verify-wh-frontier-tasks
description: Independently audit a three-task Frontier-Bench/Harbor submission produced by another AI, using a fresh second AI with no creator conclusions plus deterministic evidence, oracle/nop/static results, originality comparison, specification-test alignment, leakage, and verifier-security checks. Use when asked to verify, review, double-check, accept, reject, or quality-gate outputs from create-wh-frontier-tasks or any benchmark submission package without modifying the submitted tasks.
---

# Verify WH Frontier Tasks

Run a read-only, evidence-backed second review. Keep deterministic validation and runtime tests authoritative; use the independent AI for semantic analysis that scripts cannot settle.

## Establish the review boundary

Require:

- the unpacked submission directory containing one README and exactly three tasks;
- the selected reference name or task directory;
- the Frontier-Bench root, defaulting to the bundled snapshot at `../../assets/frontier-bench` relative to this skill;
- a report output directory outside the submission.

When no external root is supplied, resolve the reference as `BUNDLED_FRONTIER_ROOT/tasks/REFERENCE`. Verify that the bundled root contains the selected task, checks, rubrics, taxonomy, and task template before reviewing.

Do not pass creator reasoning, self-evaluation, suspected defects, intended answers, or previous review conclusions to the reviewer. Passing the raw submission, the raw reference, repository standards, and command logs is allowed.

Hash the submission before review:

```text
python scripts/review_tool.py snapshot SUBMISSION \
  --reference REFERENCE_TASK --output REVIEW_DIR/evidence.json
```

Treat `evidence.json` as an index, not as proof that the tasks are correct.

## Launch an independent reviewer

When an orchestrator explicitly identifies the current agent as a fresh, isolated, coordinator-invoked reviewer and provides the raw paths, perform the review directly in the current agent. Do not spawn another reviewer from that mode.

Otherwise, start one fresh subagent or fresh task with no inherited conversation context. Give it only the prompt in [references/reviewer-prompt.md](references/reviewer-prompt.md), replacing the path placeholders. Pass raw artifacts rather than a summary.

If no fresh-agent mechanism is available, stop and return the filled reviewer prompt for the user to run in a new task. Do not silently replace the independent review with self-review.

The reviewer must not edit the submission. Permit writes only under `REVIEW_DIR` and disposable copies used for tests. Keep the source submission hash-stable.

## Gather deterministic evidence

Have the reviewer read [references/review-rubric.md](references/review-rubric.md), then inspect every task in this order:

1. `instruction.md`
2. `task.toml`
3. `tests/`
4. `solution/`
5. `environment/`
6. optional task `README.md`

Run, when locally available:

```text
for check in checks/check-*.sh; do bash "$check" TASK_PATH; done
harbor check TASK_PATH -r FRONTIER_BENCH/rubrics/task-implementation.toml
harbor run -p TASK_PATH --agent oracle
harbor run -p TASK_PATH --agent nop
```

Run oracle at least five times for concurrent, nondeterministic, numerical, or timing-sensitive tasks. Capture exact commands, exit codes, rewards, run counts, and log paths. Never infer a pass from source inspection.

Use a disposable copy for any command that can write into a task. Do not browse for task-specific solutions or send artifacts to external services.

## Perform semantic review

Evaluate all rubric criteria independently for each task and for the package. In particular:

- map every instruction requirement to tests and every test behavior back to instruction text;
- compare objective, data/system, core reasoning, artifacts, oracle, hidden variation, and verifier against the reference;
- inspect the built agent-visible environment for solution, tests, expected values, hidden data, or answer-bearing metadata;
- challenge the verifier with nop, constants, visible-case hard-coding, input mutation, test discovery, reward overwrite, daemon survival, and malformed artifacts where applicable;
- check that difficulty comes from realistic domain work rather than volume, obscurity, missing information, or brittle formatting;
- verify the oracle is legitimate, reproducible, and feasible within declared resources.

Do not expose hidden verifier data or oracle implementation details in the human-facing summary. Cite file paths and line numbers tightly enough that another reviewer can reproduce each finding.

## Produce and validate the report

Initialize the machine-readable report:

```text
python scripts/review_tool.py init-report REVIEW_DIR/evidence.json \
  --output REVIEW_DIR/review.json
```

Replace all `TODO` values. Use only these verdicts:

- `PASS`: every criterion passes, all static checks pass, every oracle passes, every nop fails, and no material limitation remains;
- `FAIL`: at least one blocking/major defect or failed required execution check exists;
- `PROVISIONAL`: no demonstrated blocker, but one or more required runtime checks could not be completed.

Validate the report and confirm source immutability:

```text
python scripts/review_tool.py validate-report REVIEW_DIR/evidence.json REVIEW_DIR/review.json
python scripts/review_tool.py snapshot SUBMISSION \
  --reference REFERENCE_TASK --output REVIEW_DIR/evidence-after.json
python scripts/review_tool.py compare REVIEW_DIR/evidence.json REVIEW_DIR/evidence-after.json
```

Fix the report, not the tasks, if report validation fails. Any source fingerprint change invalidates the independent review.

## Hand off

Return `review.json` plus a concise `review.md` containing:

- overall verdict and confidence;
- per-task verdicts;
- blockers and major findings first;
- commands actually run and their outcomes;
- checks not run and why;
- exact next actions for the creator, without implementing them.

Keep AI-only concerns labeled as concerns. Distinguish observed evidence from inference. Never call a submission fully verified when the required runtime evidence is absent.
