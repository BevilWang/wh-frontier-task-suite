# Independent review rubric

Evaluate every criterion as `PASS`, `FAIL`, `WARN`, or `NOT_RUN`. A `FAIL` with severity `blocker` or `major` forces overall `FAIL`. `NOT_RUN` on static, oracle, or nop evidence prevents overall `PASS`.

## Required criteria

Before assigning criterion verdicts, complete four exhaustive source sweeps for each task and keep reading after any first blocker:

- `contract_test_matrix`: map every observable promise to tests and every graded behavior back to instruction text;
- `input_domain_totality`: enumerate every accepted input, state, declaration, parameter regime, protocol transition, or physical mode, then trace it through the relevant validation, normalization, compilation, recovery, simulation, and output paths; cover malformed, boundary, degenerate, transition, ordering, and scale cases where applicable;
- `verifier_adversarial`: assess generated/hidden variation, independent expected-state computation, and credible shortcuts rather than counting tests;
- `runtime_harness`: inspect and, when feasible, execute privilege drop, CTRF/reward permissions, binary scoring, failure paths, and process cleanup.

A runtime blocker does not excuse the source sweeps. A failed sweep requires an open blocker/major finding and a task `FAIL`.

### structure

Confirm one package README, exactly three independent `task-N-slug` directories, required task files/directories, valid task names and taxonomy, complete metadata, canary, absolute paths, timeout sentence, anti-cheat sentence, and correct zip naming when an archive exists.

### originality

Compare each task with the selected reference across objective, environment/data, core reasoning, artifacts, oracle, hidden variation, and verifier. Fail renamed scenarios, constant changes, data reskins, translated theorem equivalents, transplanted bugs, reused thresholds, or copied fixtures/tests. Shared Harbor structure is expected and is not copying.

### specification_test_alignment

Build a bidirectional mapping. Every promised behavior must have meaningful coverage; every graded behavior must be disclosed. Flag hidden requirements, accidental implementation mandates, weak assertions, tolerance ambiguity, and filenames or side effects tested but not specified.

### solvability_oracle

Require a legitimate oracle that passes from a clean environment within resources. Check that it generalizes beyond visible inputs and does not read verifier truth, hard-code fixtures, or exploit the reward channel. Source inspection alone cannot earn `PASS` for runtime solvability.

### nop_resistance

Require nop reward `0`. Probe trivial constants, empty outputs, copied inputs, visible-case lookup tables, malformed artifacts, and shortcut strategies appropriate to the domain. Treat untested credible shortcuts as findings.

### verifier_quality

Require deterministic, efficient, independent outcome verification. Check hidden variation, independent recomputation/invariants, error-path handling, binary rewards, CTRF for discrete suites, pinned/baked verifier dependencies, and repeated runs for flaky domains.

### isolation_leakage

Confirm separate verifier mode, narrow artifacts, no solution/tests/truth in the agent image, enforced preservation constraints, unprivileged execution of agent code, protected reward directory, process cleanup, and no agent-controlled expected values.

### difficulty_value

Confirm professional-level, realistic, useful difficulty with a plausible expert time. Reject difficulty caused mainly by missing specifications, volume, internet denial, obscure facts, arbitrary formatting, or an unsolved research problem.

### packaging

Confirm the package README includes owner/contact, reference/link, three summaries, modality, and honest validation status. Reject caches, dependency trees, build products, scratch files, or unrelated material.

## Finding format

Each finding must contain:

- `id`: stable identifier such as `task-2-alignment-01`;
- `task`: exact task name or `package`;
- `criterion`: one required criterion name;
- `severity`: `blocker`, `major`, `minor`, or `info`;
- `status`: `open`, `resolved`, `accepted`, or `info`;
- `title`: concise title;
- `evidence`: non-empty list of file/line references or command/log paths;
- `observed_fact`: directly observed fact;
- `impact`: why it matters;
- `required_creator_action`: requested correction, without implementing it;
- `confidence`: number from 0.0 to 1.0.

Do not reveal hidden expected outputs or copy substantial oracle code into the report.

## Verdict rules

- `PASS`: all nine criteria pass for all tasks; static checks, oracle, and nop are observed and correct; source unchanged; no blockers/majors.
- `FAIL`: any blocker/major failure, failed oracle, passing nop, source mutation, material leakage, copied task, or invalid verifier.
- `PROVISIONAL`: no observed blocker/major, but runtime/environment limitations leave a required check not run.

Confidence does not override evidence. A high-confidence opinion cannot replace a missing oracle or nop run.
