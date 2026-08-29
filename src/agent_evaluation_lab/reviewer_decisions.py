from __future__ import annotations

from typing import Any


def build_reviewer_decision_export(
    evaluation_report: dict[str, Any],
    review_report: dict[str, Any],
    review_queue: dict[str, Any],
    adjudication: dict[str, Any],
) -> dict[str, Any]:
    """Create a bounded, non-authoritative action sheet from review evidence."""
    snapshot = review_report.get("evaluation_snapshot_sha256")
    if not isinstance(snapshot, str) or not snapshot:
        raise ValueError("Review report must contain an evaluation snapshot")
    if review_queue.get("evaluation_snapshot_sha256") != snapshot:
        raise ValueError("Review queue snapshot does not match review report")
    if not isinstance(adjudication, dict) or not adjudication.get("receipt_id"):
        raise ValueError("Adjudication receipt is required")

    decisions: list[dict[str, Any]] = []
    for item in review_queue.get("items", []):
        if not isinstance(item, dict) or not str(item.get("case_id", "")).strip():
            raise ValueError("Review queue items must contain a case_id")
        effective = item.get("effective_decision")
        if effective == "blocked_by_automated_gate":
            action, status = "fix_candidate_and_rerun_evaluation", "blocked"
        elif item.get("requires_adjudication"):
            action, status = "adjudicate_reviewer_disagreement", "pending"
        elif effective == "blocked_by_review":
            action, status = "request_reviewer_changes", "pending"
        else:
            action, status = "complete_human_release_review", "pending"
        decisions.append(
            {
                "case_id": item["case_id"],
                "priority": item.get("priority", "normal"),
                "review_state": item.get("review_state"),
                "effective_decision": effective,
                "failure_codes": sorted(set(item.get("failure_codes", []))),
                "requires_adjudication": bool(item.get("requires_adjudication", False)),
                "status": status,
                "recommended_action": action,
            }
        )
    decisions.sort(key=lambda row: (row["priority"] != "critical", row["case_id"]))
    return {
        "schema_version": "1.0",
        "decision_export_version": "0.7",
        "evaluation_snapshot_sha256": snapshot,
        "automated_release_passed": bool(evaluation_report.get("release_gate", {}).get("passed", False)),
        "adjudication_receipt_id": adjudication["receipt_id"],
        "decisions": decisions,
        "decision_count": len(decisions),
        "decisions_applied": False,
        "release_authority": False,
        "external_actions_executed": 0,
        "authority_boundary": "This export organizes human follow-up only; it cannot approve, release, mutate evidence or override an automated safety failure.",
    }
