from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import repair_tool


WORKSPACE = Path(__file__).resolve().parents[3]
SUBMISSION = WORKSPACE / "skills" / "create-wh-frontier-tasks"
REFERENCE = WORKSPACE / "frontier-bench" / "tasks" / "wal-recovery-ordering"


def load_review_tool():
    path = WORKSPACE / "skills" / "verify-wh-frontier-tasks" / "scripts" / "review_tool.py"
    spec = importlib.util.spec_from_file_location("review_tool_for_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def base_ledger() -> dict:
    current = repair_tool.fingerprint(SUBMISSION)
    tasks = ["task-1-a", "task-2-b", "task-3-c"]
    return {
        "schema_version": 1,
        "submission": str(SUBMISSION.resolve()),
        "baseline_fingerprint": current,
        "post_repair_fingerprint": current,
        "overall_status": "complete",
        "summary": "All reviewed items were resolved with evidence.",
        "items": [],
        "item_manifest_fingerprint": repair_tool.item_manifest_fingerprint([]),
        "task_manifest": tasks,
        "task_manifest_fingerprint": repair_tool.task_manifest_fingerprint(tasks),
        "regression": [
            {
                "task": task,
                "checks": [
                    {"kind": kind, "status": "PASS", "command": f"run-{kind}", "evidence": f"{kind}.log"}
                    for kind in ("static", "oracle", "nop")
                ],
            }
            for task in tasks
        ],
    }


def base_ledger_v2() -> dict:
    ledger = base_ledger()
    ledger["schema_version"] = 2
    ledger["hardening"] = [
        {
            "task": task,
            "checks": [
                {"name": name, "status": "PASS", "command": f"audit-{name}", "evidence": f"{name}.md"}
                for name in sorted(repair_tool.HARDENING_SWEEPS)
            ],
        }
        for task in ledger["task_manifest"]
    ]
    return ledger


class RepairToolTest(unittest.TestCase):
    def test_fingerprint_matches_verification_skill(self) -> None:
        review_tool = load_review_tool()
        packet = review_tool.build_snapshot(SUBMISSION.resolve(), REFERENCE.resolve())
        self.assertEqual(repair_tool.fingerprint(SUBMISSION.resolve()), packet["source_fingerprint"])

    def test_item_builder_orders_material_findings_first(self) -> None:
        review = {
            "findings": [
                {"id": "minor", "status": "open", "task": "package", "criterion": "packaging", "severity": "minor", "title": "Minor", "evidence": ["a"], "required_creator_action": "fix"},
                {"id": "blocker", "status": "open", "task": "task-1-a", "criterion": "structure", "severity": "blocker", "title": "Blocker", "evidence": ["b"], "required_creator_action": "fix"},
            ],
            "criteria": [],
            "task_results": [],
            "limitations": [],
        }
        items = repair_tool.build_items(review)
        self.assertEqual([item["id"] for item in items], ["blocker", "minor"])

    def test_unchanged_file_is_not_repair_evidence(self) -> None:
        baseline = {"SKILL.md": repair_tool.sha256(SUBMISSION / "SKILL.md")}
        changed, reason = repair_tool.changed_from_baseline("SKILL.md", SUBMISSION.resolve(), baseline)
        self.assertFalse(changed)
        self.assertIn("unchanged", reason)

    def test_complete_rejected_item_can_close_with_counter_evidence(self) -> None:
        ledger = base_ledger()
        ledger["items"] = [{
            "id": "rejected-1",
            "source": "finding",
            "task": "package",
            "criterion": "structure",
            "severity": "minor",
            "title": "Incorrect structure claim",
            "report_evidence": ["SKILL.md:1"],
            "requested_action": "Investigate the claim.",
            "decision": "rejected",
            "rationale": "The cited current file directly disproves the claim.",
            "changed_files": [],
            "validation": [{"command": "unit-test", "status": "PASS", "evidence": "test log"}],
        }]
        ledger["item_manifest_fingerprint"] = repair_tool.item_manifest_fingerprint(ledger["items"])
        self.assertEqual(repair_tool.validate_ledger(ledger, SUBMISSION.resolve()), [])

    def test_complete_cannot_hide_blocked_item(self) -> None:
        ledger = base_ledger()
        ledger["items"] = [{
            "id": "blocked-1",
            "source": "execution",
            "task": "task-1-a",
            "criterion": "solvability_oracle",
            "severity": "major",
            "title": "Oracle runtime unavailable",
            "report_evidence": ["runtime log"],
            "requested_action": "Run the oracle.",
            "decision": "blocked",
            "rationale": "Required runtime is unavailable.",
            "changed_files": [],
            "validation": [],
        }]
        ledger["item_manifest_fingerprint"] = repair_tool.item_manifest_fingerprint(ledger["items"])
        errors = repair_tool.validate_ledger(ledger, SUBMISSION.resolve())
        self.assertTrue(any("complete ledger" in error for error in errors))

    def test_rejected_item_requires_passing_counter_evidence(self) -> None:
        ledger = base_ledger()
        ledger["items"] = [{
            "id": "rejected-weak",
            "source": "finding",
            "task": "package",
            "criterion": "structure",
            "severity": "major",
            "title": "Unsupported rejection",
            "report_evidence": ["review.log"],
            "requested_action": "Fix the issue.",
            "decision": "rejected",
            "rationale": "I disagree.",
            "changed_files": [],
            "validation": [],
        }]
        ledger["item_manifest_fingerprint"] = repair_tool.item_manifest_fingerprint(ledger["items"])
        errors = repair_tool.validate_ledger(ledger, SUBMISSION.resolve())
        self.assertTrue(any("passing counter-evidence" in error for error in errors))

    def test_complete_requires_full_regression(self) -> None:
        ledger = base_ledger()
        ledger["regression"][0]["checks"][1]["status"] = "NOT_RUN"
        errors = repair_tool.validate_ledger(ledger, SUBMISSION.resolve())
        self.assertTrue(any("regression PASS" in error for error in errors))

    def test_schema_two_complete_requires_full_hardening(self) -> None:
        ledger = base_ledger_v2()
        self.assertEqual(repair_tool.validate_ledger(ledger, SUBMISSION.resolve()), [])
        ledger["hardening"][0]["checks"][0]["status"] = "NOT_RUN"
        errors = repair_tool.validate_ledger(ledger, SUBMISSION.resolve())
        self.assertTrue(any("hardening sweep" in error for error in errors))

    def test_schema_two_hardening_covers_every_task(self) -> None:
        ledger = base_ledger_v2()
        ledger["hardening"].pop()
        errors = repair_tool.validate_ledger(ledger, SUBMISSION.resolve())
        self.assertTrue(any("hardening must cover every task" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
