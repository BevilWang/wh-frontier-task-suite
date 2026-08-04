# Multi-agent orchestration protocol

## Goals

1. Complete the full task lifecycle from one user-facing Codex task.
2. Keep review judgment independent from authoring and repair context.
3. Use deterministic files and validators as the stage interface.
4. Prevent concurrent writes to the same submission.
5. Remove preventable author defects before the counted independent-review loop.
6. Default to repair-until-PASS; stop safely only on missing authority, persistent invalid evidence, or an explicit user safety cap.

## Context boundaries

- Spawn every stage agent with `fork_turns="none"`.
- Give stage agents raw paths and role instructions, not coordinator conclusions.
- Never send author reasoning, intended answers, suspected defects, or desired verdicts to a reviewer.
- A reviewer may read a previous review and repair ledger only after completing and recording a from-scratch assessment of the corrected submission.
- Treat agent final messages as notifications. Treat validated artifacts on disk as authoritative.

## Filesystem boundaries

- Author, hardener, repair, and release agents are writers and must run sequentially.
- Review agents treat the submission and reference as read-only.
- Commands that may write during review run against disposable copies.
- Each stage writes to a unique directory under the run root.
- Never allow two agents to edit the submission concurrently.

## Stage artifact contract

| Stage | Required artifacts |
| --- | --- |
| Author | `OWNER_submission/` with package README and exactly three tasks |
| Hardener | source-sweep evidence, runtime evidence, corrected fingerprint; no zip |
| Review | `evidence.json`, schema-2 `review.json`, `review.md`, post-review fingerprint; repaired cycles use `from-scratch/` and `closure/` subdirectories |
| Repair | schema-2 `repair-ledger.json`, `repair.md`, hardening matrix, corrected source fingerprint |
| Release | final zip, checksum, archive inventory, extracted smoke-test evidence |

## State machine

Persist `repair_policy` in `pipeline-state.json`. The default is `{"mode":"until_pass","maximum_rounds":5}`. If the user explicitly supplies a cap, store `mode` as `capped` and the positive integer in `maximum_rounds`; never silently invent or lower a cap during resume.

```text
AUTHORING
  -> HARDENING
  -> REVIEWING
  -> PASS -> RELEASING -> COMPLETE
  -> FAIL -> REPAIRING -> REVIEWING
  -> PROVISIONAL -> RETRY_MISSING_CHECKS or BLOCKED
  -> INVALID_REPORT -> ONE_REVIEWER_RETRY or BLOCKED
  -> EXPLICIT_REPAIR_CAP_EXHAUSTED -> BLOCKED
```

## Agent lifecycle

1. Use run-scoped stage names such as `frontier_author_RUN_ID`, `frontier_hardener_RUN_ID`, `frontier_review_RUN_ID_r1`, `frontier_repair_RUN_ID_r1`, and `frontier_release_RUN_ID` so repeated runs in one Codex task do not collide.
2. Before spawning, use `list_agents`. If the run-scoped agent already exists, wait when it is running or use `followup_task` when it is idle; never create a duplicate stage agent for the same run.
3. Wait for each dependency-producing agent before spawning the next stage.
4. Use `followup_task` only to complete missing stage artifacts, correct an invalid stage report, or perform the defined closure phase; do not coach a reviewer toward a verdict.
5. Interrupt an agent only when it writes outside its boundary, mutates read-only inputs, or continues after a terminal failure.
6. Keep user updates concise during long stages.
7. Append every spawned agent and its terminal status to `pipeline-state.json`; never leave later reviewers or repairers out of the agent history.

## Runtime lifecycle

- Run Harbor/Docker preflight before every runtime-producing stage, not only once at pipeline start.
- On Windows, set Python UTF-8 variables and use a short disposable task/rubric/jobs root for long-path failures. Keep the source fingerprint stable.
- Correct a stopped Docker daemon or transient runtime prerequisite before spawning a reviewer when existing authority permits; do not consume a review round on a preventable infrastructure-only failure.
- Distinguish upstream/static evidence from a direct isolated verifier substitute. Record substitutes honestly; they do not silently become a Harbor static pass.

## Failure rules

- Missing collaboration tools: stop; independent review cannot be simulated.
- Author output missing or structurally invalid after one follow-up: stop.
- Hardener output missing, structurally invalid, or lacking complete source sweeps after one follow-up: stop before the counted review.
- Reviewer report invalid after one follow-up: stop.
- Submission fingerprint changed during review: invalidate that review and stop unless the change is proven to be disposable-copy output.
- Release snapshot or extracted archive fingerprint differs from the passing review: stop release and return to repair plus fresh review.
- `PROVISIONAL` caused by missing infrastructure: stop unless the missing check can be run within existing authority.
- Repeated identical blocker/major finding fingerprint across two consecutive repair rounds: stop with `BLOCKED`; the repairer is not converging.

- Repair ledger stale or invalid: stop and require a new review or corrected ledger.
- Explicit user-supplied repair cap reached without `PASS`: stop and report the latest evidence. With no explicit cap, continue the evidence-backed repair/re-review loop until `PASS` or a genuine blocker.
- An archive created before the passing review is stale and must not be published or described as a release artifact.

## Approval boundary

Multi-agent orchestration removes manual task switching, not permission boundaries. If a stage requires new credentials, external publication, destructive changes, or expanded authority, route the approval request to the user through the coordinator and resume only after approval.
