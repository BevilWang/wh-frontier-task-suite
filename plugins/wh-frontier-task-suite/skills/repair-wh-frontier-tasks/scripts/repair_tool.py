#!/usr/bin/env python3
"""Create and validate a repair ledger from an independent review report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2, "info": 3}
DECISIONS = {"pending", "fixed", "rejected", "not_applicable", "blocked"}
VALIDATION_STATUSES = {"PASS", "FAIL", "NOT_RUN"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    directories = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    for directory in directories:
        digest.update(b"D\0")
        digest.update(directory.encode("utf-8"))
        digest.update(b"\n")
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        digest.update(b"F\0")
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_mode & 0o777).encode("ascii"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def item_from_finding(finding: dict) -> dict:
    return {
        "id": finding["id"],
        "source": "finding",
        "task": finding.get("task", "package"),
        "criterion": finding.get("criterion", "structure"),
        "severity": finding.get("severity", "major"),
        "title": finding.get("title", finding["id"]),
        "report_evidence": finding.get("evidence", []),
        "requested_action": finding.get("required_creator_action", "Investigate and resolve the finding."),
        "decision": "pending",
        "rationale": "TODO",
        "changed_files": [],
        "validation": [],
    }


def item_manifest_fingerprint(items: list[dict]) -> str:
    immutable_keys = (
        "id", "source", "task", "criterion", "severity", "title",
        "report_evidence", "requested_action",
    )
    manifest = [{key: item.get(key) for key in immutable_keys} for item in items]
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def changed_from_baseline(relative: str, submission: Path, baseline: dict[str, str]) -> tuple[bool, str]:
    path = (submission / relative).resolve()
    try:
        path.relative_to(submission)
    except ValueError:
        return False, "path escapes submission"
    old_hash = baseline.get(Path(relative).as_posix())
    if path.exists() and path.is_file():
        new_hash = sha256(path)
        if old_hash == new_hash:
            return False, "file hash is unchanged from reviewed evidence"
        return True, "file was added or changed"
    if old_hash is not None and not path.exists():
        return True, "reviewed file was deleted"
    return False, "path neither exists now nor appeared in reviewed evidence"


def build_items(report: dict) -> list[dict]:
    items = [item_from_finding(finding) for finding in report.get("findings", []) if finding.get("status") == "open"]
    represented = {(item["criterion"], item["task"]) for item in items}

    for criterion in report.get("criteria", []):
        status = criterion.get("status")
        if status not in {"FAIL", "WARN", "NOT_RUN"}:
            continue
        key = (criterion.get("name"), "package")
        if key in represented:
            continue
        severity = criterion.get("severity", "major")
        if status == "WARN" and severity in {"blocker", "major"}:
            severity = "minor"
        items.append({
            "id": f"criterion-{criterion.get('name')}",
            "source": "criterion",
            "task": "package",
            "criterion": criterion.get("name"),
            "severity": severity,
            "title": f"Resolve {status} criterion: {criterion.get('name')}",
            "report_evidence": criterion.get("evidence", []),
            "requested_action": criterion.get("rationale", "Investigate the failed criterion."),
            "decision": "pending",
            "rationale": "TODO",
            "changed_files": [],
            "validation": [],
        })

    for task_result in report.get("task_results", []):
        for execution in task_result.get("execution", []):
            if execution.get("status") == "PASS":
                continue
            kind = execution.get("kind", "unknown")
            status = execution.get("status", "NOT_RUN")
            items.append({
                "id": f"execution-{task_result.get('task')}-{kind}",
                "source": "execution",
                "task": task_result.get("task"),
                "criterion": {"oracle": "solvability_oracle", "nop": "nop_resistance", "static": "structure"}.get(kind, "verifier_quality"),
                "severity": "blocker" if status == "FAIL" else "major",
                "title": f"{kind} execution is {status}",
                "report_evidence": [execution.get("evidence", "")],
                "requested_action": f"Run and resolve the {kind} check; record observed evidence.",
                "decision": "pending",
                "rationale": "TODO",
                "changed_files": [],
                "validation": [],
            })

    for index, limitation in enumerate(report.get("limitations", []), 1):
        if not limitation:
            continue
        items.append({
            "id": f"limitation-{index}",
            "source": "limitation",
            "task": "package",
            "criterion": "verifier_quality",
            "severity": "minor",
            "title": "Resolve review limitation",
            "report_evidence": [limitation],
            "requested_action": "Remove the limitation or document why it remains.",
            "decision": "pending",
            "rationale": "TODO",
            "changed_files": [],
            "validation": [],
        })

    ids: dict[str, int] = {}
    for item in items:
        base = item["id"]
        ids[base] = ids.get(base, 0) + 1
        if ids[base] > 1:
            item["id"] = f"{base}-{ids[base]}"
    return sorted(items, key=lambda item: (SEVERITY_ORDER.get(item["severity"], 9), item["task"], item["id"]))


def cmd_intake(args: argparse.Namespace) -> int:
    submission = Path(args.submission).resolve()
    review_path = Path(args.review).resolve()
    evidence_path = Path(args.evidence).resolve()
    output = Path(args.output).resolve()
    if not submission.is_dir():
        raise SystemExit("submission directory does not exist")
    if output == review_path or output == evidence_path:
        raise SystemExit("do not overwrite review evidence")
    if is_within(output, submission):
        raise SystemExit("write the repair ledger outside the submission")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if review.get("schema_version") != 1 or evidence.get("schema_version") != 1:
        raise SystemExit("unsupported review or evidence schema")
    if Path(review.get("submission", "")).resolve() != submission or Path(evidence.get("submission", "")).resolve() != submission:
        raise SystemExit("review/evidence submission path does not match the requested submission")
    if review.get("verdict") not in {"PASS", "FAIL", "PROVISIONAL"}:
        raise SystemExit("review verdict is invalid")
    if "TODO" in json.dumps(review, ensure_ascii=False):
        raise SystemExit("review report contains unresolved TODO values")
    for finding in review.get("findings", []):
        if not finding.get("id"):
            raise SystemExit("every review finding must have an id")
    expected = evidence.get("source_fingerprint")
    if review.get("source_fingerprint") != expected:
        raise SystemExit("review and evidence fingerprints differ")
    current = fingerprint(submission)
    if current != expected:
        raise SystemExit(f"stale review: current fingerprint {current} differs from reviewed {expected}")
    items = build_items(review)
    ledger = {
        "schema_version": 1,
        "submission": str(submission),
        "review": str(review_path),
        "evidence": str(evidence_path),
        "baseline_fingerprint": expected,
        "review_verdict": review.get("verdict"),
        "overall_status": "in_progress",
        "items": items,
        "item_manifest_fingerprint": item_manifest_fingerprint(items),
        "post_repair_fingerprint": "TODO",
        "summary": "TODO",
    }
    write_json(output, ledger)
    print(f"{output}\nitems={len(ledger['items'])}")
    return 0


def validate_ledger(ledger: dict, submission: Path) -> list[str]:
    errors: list[str] = []
    if ledger.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if Path(ledger.get("submission", "")).resolve() != submission:
        errors.append("ledger submission path does not match")
    current = fingerprint(submission)
    if ledger.get("post_repair_fingerprint") != current:
        errors.append(f"post_repair_fingerprint must equal current fingerprint {current}")
    if ledger.get("overall_status") not in {"in_progress", "complete", "blocked"}:
        errors.append("overall_status must be in_progress, complete, or blocked")
    if not ledger.get("summary") or ledger.get("summary") == "TODO":
        errors.append("summary must be completed")

    items = ledger.get("items", [])
    if ledger.get("item_manifest_fingerprint") != item_manifest_fingerprint(items):
        errors.append("item manifest changed; do not delete or rewrite imported review items")
    baseline: dict[str, str] = {}
    evidence_path = Path(ledger.get("evidence", ""))
    if any(item.get("decision") == "fixed" for item in items):
        if not evidence_path.is_file():
            errors.append("fixed items require the original evidence file")
        else:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            baseline = {entry["path"]: entry["sha256"] for entry in evidence.get("files", [])}

    seen: set[str] = set()
    has_pending = False
    has_blocked = False
    for item in items:
        item_id = item.get("id", "<unknown>")
        if item_id in seen:
            errors.append(f"duplicate item id: {item_id}")
        seen.add(item_id)
        decision = item.get("decision")
        if decision not in DECISIONS:
            errors.append(f"{item_id}: invalid decision")
            continue
        has_pending |= decision == "pending"
        has_blocked |= decision == "blocked"
        if not item.get("rationale") or item.get("rationale") == "TODO":
            errors.append(f"{item_id}: rationale must be completed")
        validations = item.get("validation", [])
        for check in validations:
            if check.get("status") not in VALIDATION_STATUSES:
                errors.append(f"{item_id}: invalid validation status")
            if not check.get("command") or not check.get("evidence"):
                errors.append(f"{item_id}: validation requires command and evidence")
        if decision == "fixed":
            changed = item.get("changed_files", [])
            if not changed:
                errors.append(f"{item_id}: fixed item must list changed_files")
            for relative in changed:
                changed_ok, reason = changed_from_baseline(relative, submission, baseline)
                if not changed_ok:
                    errors.append(f"{item_id}: {relative}: {reason}")
            if not validations or any(check.get("status") != "PASS" for check in validations):
                errors.append(f"{item_id}: fixed item requires passing validation evidence")
        if decision in {"rejected", "not_applicable"} and not validations and not item.get("report_evidence"):
            errors.append(f"{item_id}: {decision} requires counter-evidence")

    if ledger.get("overall_status") == "complete" and (has_pending or has_blocked):
        errors.append("complete ledger cannot contain pending or blocked items")
    if ledger.get("overall_status") == "blocked" and not has_blocked:
        errors.append("blocked ledger must contain a blocked item")
    if ledger.get("overall_status") == "in_progress" and not has_pending and not has_blocked:
        errors.append("use complete when every item is closed")
    if "TODO" in json.dumps(ledger, ensure_ascii=False):
        errors.append("ledger contains unresolved TODO values")
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger).resolve()
    submission = Path(args.submission).resolve()
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    errors = validate_ledger(ledger, submission)
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Ledger validation complete: {len(errors)} error(s)")
    return 1 if errors else 0


def cmd_stamp(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger).resolve()
    submission = Path(args.submission).resolve()
    if not submission.is_dir():
        raise SystemExit("submission directory does not exist")
    if is_within(ledger_path, submission):
        raise SystemExit("repair ledger must remain outside the submission")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["post_repair_fingerprint"] = fingerprint(submission)
    write_json(ledger_path, ledger)
    print(ledger["post_repair_fingerprint"])
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    intake = sub.add_parser("intake")
    intake.add_argument("submission")
    intake.add_argument("review")
    intake.add_argument("evidence")
    intake.add_argument("--output", required=True)
    intake.set_defaults(func=cmd_intake)
    validate = sub.add_parser("validate-ledger")
    validate.add_argument("ledger")
    validate.add_argument("submission")
    validate.set_defaults(func=cmd_validate)
    stamp = sub.add_parser("stamp-ledger")
    stamp.add_argument("ledger")
    stamp.add_argument("submission")
    stamp.set_defaults(func=cmd_stamp)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
