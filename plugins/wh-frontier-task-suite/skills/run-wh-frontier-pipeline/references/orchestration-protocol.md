# Multi-agent orchestration protocol

## Goals

1. Complete the full task lifecycle from one user-facing Codex task.
2. Keep review judgment independent from authoring and repair context.
3. Use deterministic files and validators as the stage interface.
4. Prevent concurrent writes to the same submission.
5. Stop safely on missing authority, invalid evidence, or exhausted repair rounds.

## Context boundaries

- Spawn every stage agent with `fork_turns="none"`.
- Give stage agents raw paths and role instructions, not coordinator conclusions.
- Never send author reasoning, intended answers, suspected defects, or desired verdicts to a reviewer.
- A reviewer may read a previous review and repair ledger only after completing and recording a from-scratch assessment of the corrected submission.
- Treat agent final messages as notifications. Treat validated artifacts on disk as authoritative.

## Filesystem boundaries

- Author, repair, and release agents are writers and must run sequentially.
- Review agents treat the submission and reference as read-only.
- Commands that may write during review run against disposable copies.
- Each stage writes to a unique directory under the run root.
- Never allow two agents to edit the submission concurrently.

## Stage artifact contract

| Stage | Required artifacts |
| --- | --- |
| Author | `OWNER_submission/` with package README and exactly three tasks |
| Review | `evidence.json`, `review.json`, `review.md`, post-review fingerprint; repaired cycles use `from-scratch/` and `closure/` subdirectories |
| Repair | `repair-ledger.json`, `repair.md`, corrected source fingerprint |
| Release | final zip, checksum, archive inventory, extracted smoke-test evidence |

## State machine

```text
AUTHORING
  -> REVIEWING
  -> PASS -> RELEASING -> COMPLETE
  -> FAIL -> REPAIRING -> REVIEWING
  -> PROVISIONAL -> RETRY_MISSING_CHECKS or BLOCKED
  -> INVALID_REPORT -> ONE_REVIEWER_RETRY or BLOCKED
  -> REPAIR_LIMIT_EXHAUSTED -> BLOCKED
```

## Agent lifecycle

1. Use run-scoped stage names such as `frontier_author_RUN_ID`, `frontier_review_RUN_ID_r1`, `frontier_repair_RUN_ID_r1`, and `frontier_release_RUN_ID` so repeated runs in one Codex task do not collide.
2. Before spawning, use `list_agents`. If the run-scoped agent already exists, wait when it is running or use `followup_task` when it is idle; never create a duplicate stage agent for the same run.
3. Wait for each dependency-producing agent before spawning the next stage.
4. Use `followup_task` only to complete missing stage artifacts, correct an invalid stage report, or perform the defined closure phase; do not coach a reviewer toward a verdict.
5. Interrupt an agent only when it writes outside its boundary, mutates read-only inputs, or continues after a terminal failure.
6. Keep user updates concise during long stages.

## Failure rules

- Missing collaboration tools: stop; independent review cannot be simulated.
- Author output missing or structurally invalid after one follow-up: stop.
- Reviewer report invalid after one follow-up: stop.
- Submission fingerprint changed during review: invalidate that review and stop unless the change is proven to be disposable-copy output.
- Release snapshot or extracted archive fingerprint differs from the passing review: stop release and return to repair plus fresh review.
- `PROVISIONAL` caused by missing infrastructure: stop unless the missing check can be run within existing authority.
- Repair ledger stale or invalid: stop and require a new review or corrected ledger.
- Repair-round limit reached without `PASS`: stop and report the latest evidence.

## Approval boundary

Multi-agent orchestration removes manual task switching, not permission boundaries. If a stage requires new credentials, external publication, destructive changes, or expanded authority, route the approval request to the user through the coordinator and resume only after approval.
