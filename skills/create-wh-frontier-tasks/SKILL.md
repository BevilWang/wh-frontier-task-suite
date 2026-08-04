---
name: create-wh-frontier-tasks
description: Create, implement, validate, and package exactly three original Frontier-Bench/Harbor terminal tasks calibrated from one of seven bundled reference tasks. Use when asked to author benchmark tasks from wal-recovery-ordering, ontology-kg-querying, rs-archive-clone, lean-midpoint-proof, ks-solver-cpp, vllm-deepseek-streaming, or biped-contact-dynamics; when producing instruction.md, task.toml, environment, solution, tests, oracle/nop validation, and a dated zip submission; or when checking such a submission against the bundled submission contract and Frontier-Bench quality bar without requiring a separate Frontier-Bench checkout.
---

# Create WH Frontier Tasks

Produce a submission that another agent can solve and a separate verifier can grade. Learn only structure, domain, and difficulty mechanisms from the reference; create new objectives, data, answers, and tests.

## Establish inputs

Require one supported reference name, an owner, a contact, a real submission date, and an output directory. Default the modality to text unless the user provides a different value. Never invent personal details.

In the Codex app, require the output directory to be inside the current writable workspace unless the user has explicitly granted another directory. Do not disable the host sandbox or redirect outputs into the plugin installation/cache directory.

Resolve the default Frontier-Bench root from the skill directory as `../../fb`. The bundled snapshot uses short physical directory names so Git can install it on Windows without `core.longpaths`; the public reference names remain unchanged. Run:

```text
python scripts/validate_reference_bundle.py BUNDLED_FRONTIER_ROOT --reference REFERENCE --json
```

Use the returned `task`, `checks`, `rubric`, `taxonomy`, and `template` paths instead of constructing them. The resolver understands both the bundled short layout and a canonical external Frontier-Bench checkout. Accept an external root only when the user explicitly supplies one and it validates successfully. Build paths with `pathlib` or the host's native path utilities; do not hard-code `/` or `\\` as a filesystem separator.

Read [references/reference-profiles.md](references/reference-profiles.md) for the selected reference, including its resource and feasibility profile and domain authoring lens. Run the runnability report and factor image size, build-time network needs, compute class, and validation wall-clock into the three task designs; choose a reference the user's hardware can build and validate:

```text
python scripts/runnability_report.py BUNDLED_FRONTIER_ROOT --reference REFERENCE
```

Then inspect its `instruction.md`, `task.toml`, `README.md`, `environment/`, `solution/`, and `tests/` in that order. Read [references/frontier-standards.md](references/frontier-standards.md) before designing or validating tasks.

Treat the selected bundled or explicitly supplied Frontier-Bench root as the source of truth when it conflicts with examples in the skill references. Do not browse for or copy other task-specific solutions.

## Design three original tasks

Pick one design direction family for the selected reference before drafting
concept cards, so repeated runs do not converge on the same ideas:

```text
python scripts/select_variant.py --reference REFERENCE --seed SEED
```

Use the same seed for the whole run and record seed + variant in the package
README (init records both via `--seed` / `--variant`). If the user supplied a
variant, use it. If a recent run of the same reference already used the sampled
family, sample again or choose an unused family. Keep all three tasks inside
the selected family's scope; do not drift into another family.

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
  --owner OWNER --contact CONTACT --category CATEGORY --subcategory SUBCATEGORY \
  --reference REFERENCE --reference-link REFERENCE_LINK --date YYYYMMDD \
  --seed SEED --variant FAMILY_ID \
  --slug FIRST_SLUG --slug SECOND_SLUG --slug THIRD_SLUG
```

Pass the seed and variant chosen above; `init` records them under `## Design
provenance` in the package README and warns if the variant is not in the
reference's pool (custom families are allowed but should be deliberate).

Use lowercase **single-token** slugs (e.g. `replica`, `lease`, `index`). The bundled `check-task-slug.sh` counts the whole directory name, so the created directory `task-N-<slug>` must have at most three hyphen-separated tokens. The command creates `OWNER_submission/README.md` and exactly three `task-N-<slug>` directories. Replace every `TODO` and tailor every generated file; the skeleton is not a completed task.

Before implementing files, validate each concept card against the selected reference profile. Reject any idea whose oracle reduces to a compact pure-function stub or removes the reference's coupled multi-module, concurrent-visibility, crash-consistency, or long-horizon reasoning work. Preserve the abstract difficulty mechanism, not the implementation.

Use this cross-reference table to check that every concept preserves the right difficulty class across all seven supported references:

| Reference | Abstract difficulty mechanism the new task must preserve |
| --- | --- |
| `wal-recovery-ordering` | Coupled storage-pipeline bugs; crash consistency; concurrent visibility; durable-prefix/isolation invariants |
| `ontology-kg-querying` | Reverse-engineer a rich schema; reconcile heterogeneous/temporal records; reasoning and hidden future bundles |
| `rs-archive-clone` | Black-box behavioral reimplementation; layered binary formats; error correction; byte-level compatibility |
| `lean-midpoint-proof` | Reusable formalization ladder; exact declarations/axioms; lemma dependency graph; no unproved steps |
| `ks-solver-cpp` | High-accuracy nonlinear PDE on nontrivial geometry; oracle-only boundary/forcing; adaptive resolution |
| `vllm-deepseek-streaming` | Intermittent protocol bug in a multi-layer serving stack; streaming chunk boundaries; focused regression |
| `biped-contact-dynamics` | Hybrid-mode trajectory generation; hidden configurations; multibody consistency from first principles |

If a concept would allow the oracle to be a one-page pure function, it is not preserving the reference mechanism. Redesign.


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
5. Run every repository static check and the implementation rubric, including the bundled `check-task-slug.sh` and `submission_tool.py validate`. Treat every ERROR as blocking.

6. Inspect the final container boundary for answer leakage and artifact bloat.
7. Compare instruction requirements against tests in both directions.

Before declaring the author stage ready, complete four hardening sweeps for every task:

1. **Contract matrix:** enumerate every observable instruction requirement and cite the test that enforces it; enumerate every test assertion and cite its instruction text.
2. **Input/domain totality:** enumerate every accepted structured input, persisted record, declaration, parameter regime, protocol transition, or physical mode relevant to the selected reference. Exercise malformed, boundary, degenerate, transition, ordering, and scale cases where applicable. Trace every accepted value or state through the relevant validation, normalization, compilation, recovery, simulation, and output path so it cannot later raise, silently change meaning, or escape verification.
3. **Verifier adversarial:** use seeded/generated or verifier-owned hidden variation, independent recomputation or invariants, and probes for empty/constant output, visible-case lookup, malformed artifacts, mutation, reward overwrite, and process survival as applicable.
4. **Runtime harness:** execute the exact submitted verifier wrapper as its final unprivileged user. Confirm the CTRF destination is writable, reward files are root-controlled and binary, oracle earns `1`, nop earns `0`, and failures still emit usable evidence.

Do not stop these sweeps after finding the first defect. Fix all observed material issues, rerun the full set, and treat every structural-validator warning as unresolved until it is either fixed or recorded with concrete counter-evidence.

Use the repository commands in [references/frontier-standards.md](references/frontier-standards.md). Pay special attention to the task-directory naming rule: `task-N-<single-token-slug>` with at most three tokens total.
 If Harbor or Docker cannot run, complete all available static/unit checks and record the exact blocker and substitute evidence in the package README; never claim an unrun check passed.

Run the bundled static validator from the skill directory:

```text
python scripts/submission_tool.py validate PATH_TO/OWNER_submission
```

Fix every `ERROR`. Review each `WARNING` instead of suppressing it.

## Package and report

Update the package `README.md` with owner/contact, reference name and link, one-sentence summaries of all three tasks, modality, and exact validation status. Remove scratch artifacts, caches, generated build outputs, and unused files.

When an orchestrator identifies this as the author or repair stage, do not create a zip. Leave the live submission unpacked so independent review and repair cannot make an earlier archive stale. Package only in standalone use or the isolated release stage, and only after validation succeeds:

```text
python scripts/submission_tool.py package PATH_TO/OWNER_submission \
  --category CATEGORY --subcategory SUBCATEGORY --date YYYYMMDD
```

Expect `OWNER_Category_Subcategory_YYYYMMDD.zip`. Open the archive listing and confirm it contains one submission root, its README, and exactly three independent task directories.

In the final response, report the skill path, selected reference, three task names, zip path, oracle/nop/static results, and any checks not run. Do not present scaffolding as a finished submission.
