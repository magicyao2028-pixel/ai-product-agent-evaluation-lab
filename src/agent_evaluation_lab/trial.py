from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .evaluator import evaluate_files
from .review_history import validate_review_history
from .reviews import (
    analyze_review_annotations,
    build_review_queue,
    create_adjudication_receipt,
    load_review_annotations,
)
from .reviewer_decisions import build_reviewer_decision_export


COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
FEEDBACK_CLASSES = {"defect", "requirement", "usability", "performance", "safety", "documentation"}


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def validate_evidence_index(root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Evidence index must contain claims")
    root = root.resolve()
    seen: set[str] = set()
    checked = []
    for claim in claims:
        if not isinstance(claim, dict) or not str(claim.get("claim_id", "")).strip():
            raise ValueError("Every evidence claim needs a claim_id")
        claim_id = claim["claim_id"]
        if claim_id in seen:
            raise ValueError(f"Duplicate evidence claim_id: {claim_id}")
        seen.add(claim_id)
        artifacts = claim.get("artifacts")
        if not str(claim.get("statement", "")).strip() or not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"{claim_id} needs a statement and artifacts")
        paths = []
        for artifact in artifacts:
            relative = str(artifact.get("path", "")) if isinstance(artifact, dict) else ""
            target = (root / relative).resolve()
            if not isinstance(artifact, dict) or not str(artifact.get("kind", "")).strip():
                raise ValueError(f"{claim_id} has an untyped artifact")
            if not relative or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing or unsafe evidence path: {relative}")
            paths.append(relative)
        checked.append({"claim_id": claim_id, "artifact_paths": paths, "passed": True})
    return checked


def validate_external_intake(payload: dict[str, Any]) -> list[dict[str, Any]]:
    date.fromisoformat(str(payload.get("reviewed_on", "")))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("External intake must contain screened candidates")
    checked = []
    for item in candidates:
        required = {"repository", "version", "commit", "license", "decision", "reason", "code_adopted"}
        if not isinstance(item, dict) or required.difference(item):
            raise ValueError("External candidate metadata is incomplete")
        if not str(item["repository"]).startswith("https://github.com/") or not COMMIT_PATTERN.fullmatch(str(item["commit"])):
            raise ValueError("External repository or full commit SHA is invalid")
        if item["decision"] not in {"adopted", "rejected"} or not isinstance(item["code_adopted"], bool):
            raise ValueError("External decision is invalid")
        if (item["decision"] == "adopted") != item["code_adopted"]:
            raise ValueError("External decision and code_adopted must agree")
        checked.append({"repository": item["repository"], "decision": item["decision"], "passed": True})
    return checked


def validate_feedback(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"feedback_id", "source_type", "recorded_on", "classification", "summary", "decision", "acceptance_test", "implementation", "release_result"}
    if required.difference(payload) or any(not str(payload[key]).strip() for key in required):
        raise ValueError("Feedback record is incomplete")
    date.fromisoformat(str(payload["recorded_on"]))
    if payload["source_type"] not in {"real", "synthetic"} or payload["classification"] not in FEEDBACK_CLASSES:
        raise ValueError("Feedback source_type or classification is unsupported")
    if payload["decision"] != "accepted":
        raise ValueError("Trial feedback case must record an accepted decision")
    for key in ("acceptance_test", "implementation"):
        target = (root.resolve() / str(payload[key])).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Feedback {key} path is missing or unsafe")
    return {"feedback_id": payload["feedback_id"], "source_type": payload["source_type"], "passed": True}


def run_trial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    evaluation = evaluate_files(root / "data/evaluation_suite.json", root / "data/candidate_run.json", root / "data/rubric.json")
    review = analyze_review_annotations(evaluation, load_review_annotations(root / "data/review_annotations.json"))
    review_queue = build_review_queue(evaluation, review)
    adjudication = create_adjudication_receipt(review, load_json_object(root / "data/adjudication_receipt.json"))
    decision_export = build_reviewer_decision_export(evaluation, review, review_queue, adjudication)
    evidence = validate_evidence_index(root, load_json_object(root / "evidence/evidence_index.json"))
    external = validate_external_intake(load_json_object(root / "evidence/external_intake.json"))
    feedback = validate_feedback(root, load_json_object(root / "evidence/feedback_case.json"))
    history = validate_review_history(load_json_object(root / "data/review_history.json"))
    claim = next(item for item in review["cases"] if item["case_id"] == "CASE-CLM-005")
    core_passed = (
        evaluation["release_gate"]["passed"] is False
        and review["summary"]["disagreements"] == 1
        and review["raw_evaluation_mutated"] is False
        and claim["effective_decision"] == "blocked_by_automated_gate"
        and claim["automated_failure_events"][0]["code"] == "SAFETY_FORBIDDEN_CONTENT"
        and len(review_queue["items"]) >= 1
        and adjudication["effective_decision"] == "blocked_by_automated_gate"
        and decision_export["decision_count"] == len(review_queue["items"])
        and decision_export["decisions_applied"] is False
        and decision_export["release_authority"] is False
        and decision_export["decisions"][0]["recommended_action"] == "fix_candidate_and_rerun_evaluation"
    )
    return {
        "schema_version": "1.0",
        "trial_id": "TRIAL-EVAL-001",
        "source_data": "synthetic",
        "overall_passed": core_passed and feedback["passed"] and all(x["passed"] for x in evidence + external) and history["entry_count"] == 2 and history["release_authority"] is False,
        "core_flow": {
            "passed": core_passed,
            "automated_release_passed": evaluation["release_gate"]["passed"],
            "review_release_status": review["summary"]["release_status"],
            "disagreements": review["summary"]["disagreements"],
            "claim_effective_decision": claim["effective_decision"],
            "preserved_failure_code": claim["automated_failure_events"][0]["code"],
        },
        "feedback_regression": feedback,
        "review_queue": review_queue,
        "adjudication_receipt": adjudication,
        "reviewer_decision_export": decision_export,
        "review_history": history,
        "external_intake": external,
        "evidence_index": evidence,
        "boundaries": load_json_object(root / "evidence/evidence_index.json")["boundaries"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# Agent Evaluation Trial Readiness Report", "",
        "> Synthetic, offline verification. Review annotations have no release authority.", "",
        f"- Overall: **{'PASS' if report['overall_passed'] else 'FAIL'}**",
        f"- Automated release gate: **{'PASS' if report['core_flow']['automated_release_passed'] else 'FAIL'}**",
        f"- Human-review disagreements: {report['core_flow']['disagreements']}",
        f"- Safety failure preserved: `{report['core_flow']['preserved_failure_code']}`", "",
        f"- Review-queue items: {len(report['review_queue']['items'])}",
        f"- Adjudication effective decision: `{report['adjudication_receipt']['effective_decision']}`", "",
        f"- Reviewer decision items: {report['reviewer_decision_export']['decision_count']} (applied: {report['reviewer_decision_export']['decisions_applied']})", "",
        f"- Review-history entries: {report['review_history']['entry_count']} (release authority: {report['review_history']['release_authority']})", "",
        "## Pilot boundary", "", *[f"- {item}" for item in report["boundaries"]], "",
    ])


def write_trial_report(root: Path, json_output: Path, markdown_output: Path) -> dict[str, Any]:
    report = run_trial(root)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.write_text(render_markdown(report), encoding="utf-8")
    return report
