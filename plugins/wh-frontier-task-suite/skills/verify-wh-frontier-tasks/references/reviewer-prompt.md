# Independent reviewer prompt

Use the text below when starting the fresh reviewer. Replace every angle-bracket placeholder. Do not append creator conclusions.

```text
Use $verify-wh-frontier-tasks at <SKILL_PATH> to independently audit the submission at <SUBMISSION_PATH>.

The selected reference task is <REFERENCE_TASK_PATH>. The Frontier-Bench checkout is <FRONTIER_BENCH_PATH>. The deterministic evidence packet is <EVIDENCE_JSON>. Write all review artifacts under <REVIEW_DIR>.

You are the second reviewer. You have not been given the creator's reasoning, intended answer, suspected defects, or self-assessment. Review raw artifacts only. Do not modify the submission or reference. Use disposable copies for commands that write. Run all feasible static, oracle, and nop checks; record exact commands and results. Evaluate originality, specification-test alignment, solvability, difficulty, verifier integrity, leakage, security, and packaging according to the skill. Produce review.json and review.md, validate review.json with the bundled script, and prove the submission fingerprint is unchanged. A missing runtime check requires PROVISIONAL unless another observed major defect requires FAIL.
```

## Context hygiene

Do not provide the reviewer with:

- the first AI's chat or chain of thought;
- claims that a specific task is good or broken;
- expected verdicts;
- intended fixes;
- hidden-answer summaries;
- a curated subset of files.

Provide complete raw task directories and unedited logs. If a log contains secrets, redact only the secret value and note the redaction.
