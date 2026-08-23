from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .taxonomy import EvaluationContractError


DECISIONS = {"approve", "block", "needs_changes"}
SOURCE_TYPES = {"real", "synthetic"}
ADJUDICATION_DECISIONS = {"approve", "block", "needs_changes"}


def load_review_annotations(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationContractError(f"Invalid review annotation JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise EvaluationContractError("Review annotations must contain a JSON object")
    return payload


def _snapshot_hash(report: dict[str, Any]) -> str:
    normalized = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def analyze_review_annotations(
    evaluation_report: dict[str, Any], review_payload: dict[str, Any]
) -> dict[str, Any]:
    source_type = review_payload.get("source_type")
    if source_type not in SOURCE_TYPES:
        raise EvaluationContractError("Review source_type must be real or synthetic")
    batch_id = str(review_payload.get("review_batch_id", "")).strip()
    if not batch_id:
        raise EvaluationContractError("review_batch_id must not be blank")
    try:
        date.fromisoformat(str(review_payload.get("recorded_on", "")))
    except ValueError as exc:
        raise EvaluationContractError("recorded_on must be an ISO-8601 date") from exc
    cases = evaluation_report.get("cases")
    if not isinstance(cases, list) or not cases:
        raise EvaluationContractError("Evaluation report must contain cases")
    case_by_id = {str(case.get("case_id", "")): case for case in cases}
    if "" in case_by_id or len(case_by_id) != len(cases):
        raise EvaluationContractError("Evaluation case IDs must be present and unique")
    annotations = review_payload.get("annotations")
    if not isinstance(annotations, list) or not annotations:
        raise EvaluationContractError("annotations must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in annotations:
        if not isinstance(item, dict):
            raise EvaluationContractError("Every annotation must be an object")
        annotation_id = str(item.get("annotation_id", "")).strip()
        reviewer_id = str(item.get("reviewer_id", "")).strip()
        reviewer_role = str(item.get("reviewer_role", "")).strip()
        case_id = str(item.get("case_id", "")).strip()
        decision = str(item.get("decision", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        if not all((annotation_id, reviewer_id, reviewer_role, case_id, decision, rationale)):
            raise EvaluationContractError("Annotation identity, case, decision and rationale must not be blank")
        if annotation_id in seen_ids:
            raise EvaluationContractError("annotation_id values must be unique")
        seen_ids.add(annotation_id)
        if case_id not in case_by_id:
            raise EvaluationContractError(f"Unknown annotation case_id: {case_id}")
        if decision not in DECISIONS:
            raise EvaluationContractError(f"Unsupported review decision: {decision}")
        cited = item.get("cited_failure_codes", [])
        if not isinstance(cited, list) or not all(isinstance(code, str) and code.strip() for code in cited):
            raise EvaluationContractError("cited_failure_codes must be a list of non-blank strings")
        actual_codes = {event["code"] for event in case_by_id[case_id].get("failure_events", [])}
        unsupported = sorted(set(cited) - actual_codes)
        if unsupported:
            raise EvaluationContractError(
                f"Annotation cites failure codes absent from raw evaluation evidence: {', '.join(unsupported)}"
            )
        record = {
            "annotation_id": annotation_id,
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "case_id": case_id,
            "decision": decision,
            "rationale": rationale,
            "cited_failure_codes": sorted(set(cited)),
        }
        normalized.append(record)
        grouped[case_id].append(record)

    reviewed_cases = []
    disagreements = []
    for case_id in sorted(grouped):
        case = case_by_id[case_id]
        decisions = sorted({item["decision"] for item in grouped[case_id]})
        state = "disagreement" if len(decisions) > 1 else "consensus"
        if not case.get("passed", False):
            effective = "blocked_by_automated_gate"
        elif state == "disagreement":
            effective = "needs_adjudication"
        elif decisions == ["approve"]:
            effective = "eligible_for_human_release_review"
        else:
            effective = "blocked_by_review"
        summary = {
            "case_id": case_id,
            "automated_passed": bool(case.get("passed", False)),
            "automated_failure_events": json.loads(json.dumps(case.get("failure_events", []))),
            "review_state": state,
            "review_decisions": decisions,
            "effective_decision": effective,
            "annotations": grouped[case_id],
        }
        reviewed_cases.append(summary)
        if state == "disagreement":
            disagreements.append({"case_id": case_id, "decisions": decisions, "requires_adjudication": True})

    automated_release_passed = bool(evaluation_report.get("release_gate", {}).get("passed", False))
    if not automated_release_passed:
        release_status = "blocked_by_automated_gate"
    elif disagreements:
        release_status = "needs_adjudication"
    elif any(item["effective_decision"] == "blocked_by_review" for item in reviewed_cases):
        release_status = "blocked_by_review"
    else:
        release_status = "eligible_for_human_release_review"
    return {
        "review_version": "0.5",
        "review_batch_id": batch_id,
        "source_type": source_type,
        "recorded_on": review_payload["recorded_on"],
        "evaluation_snapshot_sha256": _snapshot_hash(evaluation_report),
        "raw_evaluation_mutated": False,
        "summary": {
            "annotations": len(normalized),
            "reviewed_cases": len(reviewed_cases),
            "disagreements": len(disagreements),
            "automated_release_passed": automated_release_passed,
            "release_status": release_status,
        },
        "cases": reviewed_cases,
        "disagreements": disagreements,
        "authority_boundary": [
            "Annotations are separate review evidence and never overwrite automated observations or raw failure events.",
            "A reviewer approval cannot reopen a case blocked by the configured automated gate.",
            "Disagreement requires accountable adjudication; this public fixture grants no release authority.",
        ],
    }


def analyze_review_files(evaluation_path: Path, annotation_path: Path) -> dict[str, Any]:
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if not isinstance(evaluation, dict):
        raise EvaluationContractError("Evaluation report must contain a JSON object")
    return analyze_review_annotations(evaluation, load_review_annotations(annotation_path))


def build_review_queue(evaluation_report: dict[str, Any], review_report: dict[str, Any]) -> dict[str, Any]:
    """Export bounded review work without changing automated evidence."""
    queue: list[dict[str, Any]] = []
    for case in review_report.get("cases", []):
        failures = case.get("automated_failure_events", [])
        if not failures and case.get("effective_decision") == "eligible_for_human_release_review":
            continue
        priority = "critical" if failures else "high" if case.get("review_state") == "disagreement" else "normal"
        queue.append(
            {
                "case_id": case["case_id"],
                "priority": priority,
                "review_state": case["review_state"],
                "effective_decision": case["effective_decision"],
                "failure_codes": sorted({event["code"] for event in failures}),
                "requires_adjudication": case["review_state"] == "disagreement",
            }
        )
    queue.sort(key=lambda item: (item["priority"] != "critical", item["case_id"]))
    return {
        "queue_version": "0.6",
        "evaluation_snapshot_sha256": review_report.get("evaluation_snapshot_sha256"),
        "automated_release_passed": bool(evaluation_report.get("release_gate", {}).get("passed", False)),
        "items": queue,
        "authority_boundary": "Queue export organizes review work; it does not approve, block or mutate automated evidence.",
    }


def create_adjudication_receipt(review_report: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate an adjudication record while preserving automated safety authority."""
    required = {"receipt_id", "adjudicator_id", "recorded_on", "decision", "rationale", "case_ids"}
    if required.difference(payload) or any(not str(payload[key]).strip() for key in required - {"case_ids"}):
        raise EvaluationContractError("Adjudication receipt is incomplete")
    try:
        date.fromisoformat(str(payload["recorded_on"]))
    except ValueError as exc:
        raise EvaluationContractError("Adjudication recorded_on must be an ISO-8601 date") from exc
    if payload["decision"] not in ADJUDICATION_DECISIONS:
        raise EvaluationContractError("Adjudication decision is unsupported")
    case_ids = payload["case_ids"]
    if not isinstance(case_ids, list) or not case_ids or any(not isinstance(case_id, str) or not case_id.strip() for case_id in case_ids):
        raise EvaluationContractError("Adjudication case_ids must be a non-empty list")
    cases = {case["case_id"]: case for case in review_report.get("cases", [])}
    if any(case_id not in cases for case_id in case_ids):
        raise EvaluationContractError("Adjudication references an unknown case")
    affected = [cases[case_id] for case_id in case_ids]
    automated_block = any(not case.get("automated_passed", False) for case in affected)
    return {
        "receipt_version": "0.6",
        "receipt_id": str(payload["receipt_id"]).strip(),
        "adjudicator_id": str(payload["adjudicator_id"]).strip(),
        "recorded_on": str(payload["recorded_on"]),
        "requested_decision": payload["decision"],
        "rationale": str(payload["rationale"]).strip(),
        "case_ids": sorted(set(case_ids)),
        "effective_decision": "blocked_by_automated_gate" if automated_block else payload["decision"],
        "automated_gate_overrode_request": automated_block,
        "authority_boundary": "Adjudication records accountability and cannot reopen an automated safety failure.",
    }


def write_review_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Human Review and Disagreement Report",
        "",
        f"- Batch: `{report['review_batch_id']}`",
        f"- Source type: `{report['source_type']}`",
        f"- Evaluation snapshot: `{report['evaluation_snapshot_sha256']}`",
        f"- Release status: **{report['summary']['release_status']}**",
        f"- Disagreements: {report['summary']['disagreements']}",
        "",
        "| Case | Automated | Review state | Decisions | Effective decision |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        rows.append(
            f"| {case['case_id']} | {'PASS' if case['automated_passed'] else 'FAIL'} | "
            f"{case['review_state']} | {', '.join(case['review_decisions'])} | {case['effective_decision']} |"
        )
    rows.extend(["", "## Authority boundary", ""])
    rows.extend(f"- {item}" for item in report["authority_boundary"])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
