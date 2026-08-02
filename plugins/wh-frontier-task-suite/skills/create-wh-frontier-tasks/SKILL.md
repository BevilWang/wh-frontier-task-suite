---
name: create-wh-frontier-tasks
description: Create, implement, validate, and package exactly three original Frontier-Bench/Harbor terminal tasks calibrated from one supported reference. Use when asked to author benchmark tasks from wal-recovery-ordering, ontology-kg-querying, rs-archive-clone, lean-midpoint-proof, ks-solver-cpp, vllm-deepseek-streaming, or biped-contact-dynamics; when producing instruction.md, task.toml, environment, solution, tests, oracle/nop validation, and a dated zip submission; or when checking such a submission against the bundled submission contract and Frontier-Bench quality bar.
---

# Create WH Frontier Tasks

Produce a submission that another agent can solve and a separate verifier can grade. Learn only structure, domain, and difficulty mechanisms from the reference; create new objectives, data, answers, and tests.

## Establish inputs

Require one supported reference name and a local Frontier-Bench checkout. Default the owner to `wh`, the contact to `wanghan.scut@gmail.com`, and the modality to text unless the user provides different values. Obtain a real submission date and output directory before final packaging; never invent other personal details.

Read [references/reference-profiles.md](references/reference-profiles.md) for the selected reference. Then inspect its `instruction.md`, `task.toml`, `README.md`, `environment/`, `solution/`, and `tests/` in that order. Read [references/frontier-standards.md](references/frontier-standards.md) before designing or validating tasks. Do not require or read a claim sheet or assignment PDF.

Treat the checked-out repository as the current source of truth when it conflicts with examples in the references. Do not browse for or copy task-specific solutions.

## Design three original tasks

Before writing files, draft three private concept cards with these fields:

- real-world role and outcome;
- distinct task objective and deliverable;
- environment an agent must explore;
- domain insight and long-horizon difficulty mechanism;
- deterministic oracle approach;
- hidden variation strategy;
- likely shortcuts and how the verifier defeats them;
- expert solution outline and best-case time estimate;
- differences from the reference in objective, system/data, algorithmic work, artifacts, and verifier.

Reject a concept if it is a renamed scenario, constant swap, data reskin, copied test shape, or a composition of routine subtasks. Preserve the reference's difficulty class, not its implementation. Require each concept to differ substantively in at least three of the five comparison dimensions above and to have its own synthetic or independently derived data.

Keep all three tasks in the selected reference's category/subcategory and normally in one modality. Prefer one coherent difficulty mechanism per task over many unrelated requirements. Ensure an expert who knows the solution can implement it in hours, while success still requires professional or research-level judgment.

## Initialize the submission

Run:

```text
python scripts/submission_tool.py init OUTPUT_PARENT \
  --owner wh --contact wanghan.scut@gmail.com --category CATEGORY --subcategory SUBCATEGORY \
  --reference REFERENCE --reference-link REFERENCE_LINK --date YYYYMMDD \
  --slug FIRST_SLUG --slug SECOND_SLUG --slug THIRD_SLUG
```

Use lowercase hyphenated slugs. The command creates `wh_提交/README.md` and exactly three task directories. Replace every `TODO` and tailor every generated file; the skeleton is not a completed task.

## Implement each task

Work in this order:

1. Write `instruction.md` as an outcome contract. State the goal first, use absolute `/app/...` paths, name every graded behavior and artifact, allow solution-method freedom, and end with the required timeout and anti-cheat sentences.
2. Build `environment/` with only agent-visible inputs. Never copy `solution/`, `tests/`, hidden truth, expected outputs, or answer-bearing metadata into it.
3. Implement `solution/solve.sh` and supporting files as a legitimate, reproducible oracle. Do not hard-code verifier fixtures or visible-only outputs.
4. Implement `tests/` in a separate verifier container. Test every instruction requirement and describe every tested behavior in the instruction. Prefer functional outcome checks, hidden deterministic variants, independent recomputation, metamorphic properties, and invariants over source matching.
5. Complete `task.toml` using the current repository template. Keep artifacts narrow, use `environment_mode = "separate"`, set plausible resources/timeouts, and fill difficulty, solution, verification, experience, taxonomy, and expert-time metadata.
6. Add a task `README.md` only when it gives reviewers non-duplicative design or provenance context. It is optional inside each task.

When the verifier executes agent code, drop privileges, protect the reward channel before execution, let root write a binary reward, kill the process group, and emit CTRF for pytest suites. Bake verifier dependencies into `tests/Dockerfile`; install only a submitted pinned manifest at verification time when necessary.

## Validate progressively

Test the smallest units first, then the full task. For each task:

1. Build both containers.
2. Run the oracle and require reward `1`.
3. Run nop and require reward `0`.
4. Run the oracle at least five times when nondeterminism or concurrency exists.
5. Run every repository static check and the implementation rubric.
6. Inspect the final container boundary for answer leakage and artifact bloat.
7. Compare instruction requirements against tests in both directions.

Use the repository commands in [references/frontier-standards.md](references/frontier-standards.md). If Harbor or Docker cannot run, complete all available static/unit checks and record the exact blocker and substitute evidence in the package README; never claim an unrun check passed.

Run the bundled static validator from the skill directory:

```text
python scripts/submission_tool.py validate PATH_TO/wh_提交
```

Fix every `ERROR`. Review each `WARNING` instead of suppressing it.

## Package and report

Update the package `README.md` with owner/contact, reference name and link, one-sentence summaries of all three tasks, modality, and exact validation status. Remove scratch artifacts, caches, generated build outputs, and unused files.

Package only after validation succeeds:

```text
python scripts/submission_tool.py package PATH_TO/wh_提交 \
  --category CATEGORY --subcategory SUBCATEGORY --date YYYYMMDD
```

Expect `wh_Category_Subcategory_YYYYMMDD.zip`. Open the archive listing and confirm it contains one submission root, its README, and exactly three independent task directories.

In the final response, report the skill path, selected reference, three task names, zip path, oracle/nop/static results, and any checks not run. Do not present scaffolding as a finished submission.
