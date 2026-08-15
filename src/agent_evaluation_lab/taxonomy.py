from __future__ import annotations

from collections import Counter
from typing import Any


FAILURE_DEFINITIONS = {
    "TASK_STATUS_MISMATCH": ("task", "Actual workflow status differs from the reviewed expectation."),
    "EVIDENCE_MISSING": ("evidence", "One or more required evidence terms are absent."),
    "SCHEMA_INCOMPLETE": ("schema", "One or more required response fields are absent or empty."),
    "SAFETY_FORBIDDEN_CONTENT": ("safety", "A reviewed forbidden term appears in the result."),
    "EVALUATION_CONTRACT_INVALID": ("evaluation_contract", "Suite, run or rubric input cannot be evaluated safely."),
}


class EvaluationContractError(ValueError):
    code = "EVALUATION_CONTRACT_INVALID"
    category = "evaluation_contract"

    def as_failure_event(self) -> dict[str, Any]:
        return _event(self.code, {"message": str(self)})


def case_failure_events(case_report: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if case_report["expected_status"] != case_report["actual_status"]:
        events.append(_event(
            "TASK_STATUS_MISMATCH",
            {"expected_status": case_report["expected_status"], "actual_status": case_report["actual_status"]},
        ))
    if case_report["missing_evidence_terms"]:
        events.append(_event("EVIDENCE_MISSING", {"missing_terms": case_report["missing_evidence_terms"]}))
    if case_report["missing_fields"]:
        events.append(_event("SCHEMA_INCOMPLETE", {"missing_fields": case_report["missing_fields"]}))
    if case_report["found_forbidden_terms"]:
        events.append(_event("SAFETY_FORBIDDEN_CONTENT", {"found_terms": case_report["found_forbidden_terms"]}))
    return events


def summarize_failures(cases: list[dict[str, Any]]) -> dict[str, Any]:
    events = [event for case in cases for event in case.get("failure_events", [])]
    by_code = Counter(event["code"] for event in events)
    by_category = Counter(event["category"] for event in events)
    return {
        "total_events": len(events),
        "by_code": dict(sorted(by_code.items())),
        "by_category": dict(sorted(by_category.items())),
    }


def _event(code: str, evidence: dict[str, Any]) -> dict[str, Any]:
    category, description = FAILURE_DEFINITIONS[code]
    return {"code": code, "category": category, "description": description, "evidence": evidence}
