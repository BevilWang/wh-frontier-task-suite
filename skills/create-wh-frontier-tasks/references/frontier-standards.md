# Frontier-Bench authoring and submission standards

Use the bundled Frontier-Bench snapshot as the default source of truth. Use an external checkout only when the user explicitly supplies it. Relevant files are:

- `CONTRIBUTING.md`
- `docs/task-template.toml`
- `docs/TAXONOMY.md`
- `rubrics/task-proposal.md`
- `rubrics/task-implementation.toml`
- `checks/check-*.sh`

## Bundled package contract

- Produce exactly three original tasks from one selected reference/subcategory.
- Keep the three tasks in one modality where practical.
- Name the archive `OWNER_Category_Subcategory_YYYYMMDD.zip`.
- Put `README.md` and exactly three `task-N-<single-token-slug>/` directories under `OWNER_submission/`. The bundled `check-task-slug.sh` enforces a maximum of three hyphen-separated tokens for the full directory name, so `<slug>` must be a single token.

- Put `instruction.md`, `task.toml`, `environment/`, `solution/`, and `tests/` in every task.
- State owner/contact, reference name/link, three one-line summaries, modality, and local validation status in the package README.
- Remove generated artifacts (`__pycache__`, `*.pyc`, build outputs, scratch files) before packaging; the package command will reject or sanitize them, but do not rely on that.
- Never copy reference data, answers, or tests; never submit a renamed or constant-swapped task.

- Ensure the task and tests describe the same behaviors in both directions.
- Keep ground truth in the verifier, never in the agent environment.
- Explain why the work is hard for an agent but reasonable for a qualified human.

## Task quality gate

Require all six proposal properties:

1. Verifiable: deterministic, efficient, reliable programmatic grading.
2. Well-specified: all graded outcomes appear in the instruction.
3. Solvable: a working oracle passes within resources.
4. Difficult: professional expertise or deep long-horizon reasoning, not bulk work or trivia.
5. Realistic and valuable: recognizable computer work with practical utility.
6. Outcome-verified: grade results, not an arbitrary prescribed process.

## Required implementation properties

- Use absolute agent paths such as `/app/output.json`.
- Include the repository canary in `instruction.md` and `task.toml` when required by the checkout.
- End instructions with an explicit time budget and the repository anti-cheat sentence.
- Make `[task].name` end in the exact task directory name and use the project prefix requested by the submission target.
- Fill category, subcategory, tags, difficulty explanation, solution explanation, verification explanation, relevant experience, and nonzero expert time.
- Use `[verifier] environment_mode = "separate"`.
- Transfer only agent-produced artifacts. Bake fixed inputs into the verifier image or collect a narrow, fail-safe diff for large source trees.
- Keep environment dependencies pinned where the repository requires pinning.
- Do not allow runtime network installation of verifier tooling; bake it into `tests/Dockerfile`.
- Do not copy or mount `solution/` or `tests/` into the agent environment.
- Enforce every concrete "do not modify" or "must preserve" constraint.
- Run agent-produced code unprivileged in the verifier and keep `/logs/verifier` root-only.
- Write exactly `0` or `1` as reward on every reachable scoring path.
- Emit `/logs/verifier/ctrf.json` for pytest or other discrete test suites.
- Keep tests method-agnostic unless a method restriction prevents cheating and is enforced.
- Avoid unused files, build outputs, dependency trees, and duplicated documentation.

## Validation commands

Run from the Frontier-Bench root, adapting the task path:

```bash
for check in checks/check-*.sh; do bash "$check" tasks/your-task; done
harbor run -p tasks/your-task --agent oracle
harbor run -p tasks/your-task --agent nop
```

The official `harbor check` (rubric contract check) is run externally by the Harbor platform after submission; this plugin does not implement it locally (see the plugin README). Local validation uses the bundled static checks plus oracle/nop runs.

For a new submission outside `tasks/`, either copy each task into a disposable checkout location or pass its path if the installed Harbor version supports it. Do not mutate or overwrite an existing benchmark task.

For nondeterministic, concurrent, numerical, or timing-sensitive tasks, repeat oracle runs at least five times. Add deterministic seeds where they do not remove the essential difficulty. Record commands, run counts, exit states, and blockers in the package README.

## Instruction-test parity audit

Create two temporary lists:

1. every observable requirement in `instruction.md`;
2. every behavior asserted by `tests/`.

Map each instruction requirement to at least one meaningful test. Map each test assertion to explicit instruction language. Remove or document incidental implementation checks. Pay special attention to filenames, schemas, tolerances, performance bounds, preservation constraints, invalid inputs, hidden variations, and side effects.

For structured inputs, add a field-totality table that names every required and optional field and covers missing, null, wrong-type, boolean-as-integer, malformed nested, duplicate, ordering, and scale cases where applicable. Follow accepted data through normalization, sorting, serialization, and recovery: validation must guarantee every later indexed field and invariant. This sweep is required even when another blocker is already known.

## Leakage and shortcut audit

- Search the environment image and build context for expected outputs, answer keys, test fixtures, solution code, hidden configs, and revealing filenames.
- Confirm fixed verifier data is not included in artifacts collected from the agent.
- Try nop, trivial constant output, visible-fixture hard-coding, test-file discovery, reward-file overwrite, background-process survival, and protected-input mutation.
- Prefer verifier-owned hidden inputs, independent recomputation, invariants, metamorphic checks, and multiple equivalent cases.
- Do not make the task hard by disabling the open internet, withholding necessary specifications, or relying on obscure facts alone.

## Windows runtime path

Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` for Harbor commands on non-UTF-8 Windows hosts. Before a runtime stage, require `harbor --version` and `docker version` to succeed. For `WinError 206` or long-path failures, copy the disposable task, rubric, and job directory beneath one short workspace-owned directory; optionally map that directory to a temporary drive with `subst`, pass Harbor `--jobs-dir` explicitly, and remove the mapping afterward. Never shorten paths by moving or mutating the reviewed submission.
