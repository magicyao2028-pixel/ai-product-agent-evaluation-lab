from __future__ import annotations

from typing import Any


def build_feedback_regression_pack(review_report: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    """Bind accepted feedback to current cases without changing evaluation evidence."""
    if not isinstance(review_report, dict) or review_report.get("raw_evaluation_mutated") is not False:
        raise ValueError("review report must preserve immutable evaluation evidence")
    if not isinstance(replay, dict) or replay.get("evaluation_mutated") is not False or replay.get("release_authority") is not False:
        raise ValueError("feedback replay must remain non-authoritative")
    accepted = replay.get("replayed")
    if not isinstance(accepted, list) or not accepted:
        raise ValueError("feedback replay must contain accepted records")

    cases = review_report.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("review report must contain cases")
    annotations: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict) or not str(case.get("case_id", "")).strip():
            raise ValueError("review report cases are invalid")
        for annotation in case.get("annotations", []):
            if isinstance(annotation, dict) and str(annotation.get("annotation_id", "")).strip():
                annotation_id = str(annotation["annotation_id"])
                if annotation_id in annotations:
                    raise ValueError("review report annotation IDs must be unique")
                annotations[annotation_id] = {
                    "case_id": str(case["case_id"]),
                    "automated_passed": case.get("automated_passed"),
                    "effective_decision": str(case.get("effective_decision", "")),
                }
    if not annotations:
        raise ValueError("review report must contain annotations")

    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for record in accepted:
        if not isinstance(record, dict):
            raise ValueError("accepted feedback records must be objects")
        feedback_id = str(record.get("feedback_id", "")).strip()
        annotation_id = str(record.get("annotation_id", "")).strip()
        if not feedback_id or feedback_id in seen:
            raise ValueError("accepted feedback IDs must be unique")
        seen.add(feedback_id)
        if annotation_id not in annotations:
            raise ValueError("accepted feedback must reference a current annotation")
        if record.get("status") != "accepted" or record.get("passed") is not True:
            raise ValueError("regression pack accepts only validated accepted feedback")
        context = annotations[annotation_id]
        expected_gate = "blocked" if context["automated_passed"] is False else "unchanged"
        items.append({
            "feedback_id": feedback_id,
            "annotation_id": annotation_id,
            "case_id": context["case_id"],
            "expected_gate": expected_gate,
            "effective_decision": context["effective_decision"],
            "execution_status": "not_executed",
        })
    items.sort(key=lambda item: (item["case_id"], item["feedback_id"]))
    return {
        "schema_version": "1.0",
        "item_count": len(items),
        "items": items,
        "evaluation_mutated": False,
        "release_authority": False,
        "regression_execution_executed": False,
        "boundary": "The pack identifies accepted feedback for a future regression run; it does not edit evidence, execute cases or grant release authority.",
    }


__all__ = ["build_feedback_regression_pack"]
