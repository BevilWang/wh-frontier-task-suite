from __future__ import annotations

import copy
import unittest

import review_tool


def packet() -> dict:
    return {
        "submission": "C:/submission",
        "source_fingerprint": "abc123",
        "tasks": ["task-1-a", "task-2-b", "task-3-c"],
    }


def report(status: str = "PASS", verdict: str = "PASS") -> dict:
    return {
        "schema_version": 1,
        "submission": "C:/submission",
        "source_fingerprint": "abc123",
        "reviewer": {"independent": True, "creator_context_seen": False, "identity": "fresh-reviewer"},
        "verdict": verdict,
        "confidence": 0.9,
        "summary": "Independent evidence review completed.",
        "criteria": [
            {"name": name, "status": status, "severity": "info", "evidence": ["log"], "rationale": "Observed evidence supports this result."}
            for name in review_tool.CRITERIA
        ],
        "task_results": [
            {
                "task": task,
                "verdict": verdict,
                "execution": [
                    {"kind": kind, "status": status if status != "WARN" else "PASS", "command": "command", "evidence": "log"}
                    for kind in sorted(review_tool.EXECUTION_KINDS)
                ],
            }
            for task in packet()["tasks"]
        ],
        "findings": [],
        "limitations": [],
    }


class ReviewToolTest(unittest.TestCase):
    def test_complete_pass_is_valid(self) -> None:
        self.assertEqual(review_tool.validate_report(packet(), report()), [])

    def test_pass_cannot_hide_not_run(self) -> None:
        candidate = report()
        candidate["task_results"][0]["execution"][0]["status"] = "NOT_RUN"
        errors = review_tool.validate_report(packet(), candidate)
        self.assertTrue(any("PASS requires" in error for error in errors))

    def test_overall_pass_cannot_hide_provisional_tasks_or_limitations(self) -> None:
        candidate = report()
        for task_result in candidate["task_results"]:
            task_result["verdict"] = "PROVISIONAL"
        candidate["limitations"] = ["Runtime evidence is incomplete."]
        errors = review_tool.validate_report(packet(), candidate)
        self.assertTrue(any("every task" in error for error in errors))

    def test_pass_requires_criterion_and_execution_evidence(self) -> None:
        candidate = report()
        candidate["criteria"][0]["evidence"] = []
        candidate["task_results"][0]["execution"][0]["command"] = ""
        candidate["task_results"][0]["execution"][0]["evidence"] = ""
        errors = review_tool.validate_report(packet(), candidate)
        self.assertTrue(any("criterion" in error and "evidence" in error for error in errors))
        self.assertTrue(any("requires command" in error for error in errors))
        self.assertTrue(any("requires evidence" in error for error in errors))

    def test_provisional_allows_not_run_but_not_failure(self) -> None:
        candidate = report("NOT_RUN", "PROVISIONAL")
        self.assertEqual(review_tool.validate_report(packet(), candidate), [])
        failed = copy.deepcopy(candidate)
        failed["criteria"][0]["status"] = "FAIL"
        errors = review_tool.validate_report(packet(), failed)
        self.assertTrue(any("PROVISIONAL cannot hide" in error for error in errors))

    def test_provisional_cannot_hide_failed_task_verdict(self) -> None:
        candidate = report("NOT_RUN", "PROVISIONAL")
        candidate["task_results"][0]["verdict"] = "FAIL"
        errors = review_tool.validate_report(packet(), candidate)
        self.assertTrue(any("failed task" in error for error in errors))

    def test_fingerprint_mismatch_is_rejected(self) -> None:
        candidate = report()
        candidate["source_fingerprint"] = "changed"
        errors = review_tool.validate_report(packet(), candidate)
        self.assertTrue(any("source_fingerprint" in error for error in errors))

    def test_material_finding_forces_fail(self) -> None:
        candidate = report("NOT_RUN", "PROVISIONAL")
        candidate["findings"] = [{
            "id": "task-1-a-structure-01",
            "task": "task-1-a",
            "criterion": "structure",
            "severity": "major",
            "status": "open",
            "title": "Missing task implementation",
            "evidence": ["task-1-a/instruction.md:1"],
            "observed_fact": "The task is incomplete.",
            "impact": "The task cannot be solved or graded.",
            "required_creator_action": "Implement the task.",
            "confidence": 1.0,
        }]
        errors = review_tool.validate_report(packet(), candidate)
        self.assertTrue(any("PROVISIONAL cannot hide" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
