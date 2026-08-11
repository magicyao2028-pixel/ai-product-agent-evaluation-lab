from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .rubric import RubricConfig, default_rubric, load_rubric


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.name}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def evaluate_files(
    suite_path: Path, run_path: Path, rubric_path: Path | None = None
) -> dict[str, Any]:
    suite = load_json(suite_path)
    rubric = load_rubric(rubric_path) if rubric_path else None
    return evaluate_run(suite, load_json(run_path), rubric)


def evaluate_run(
    suite: dict[str, Any], candidate: dict[str, Any], rubric: RubricConfig | None = None
) -> dict[str, Any]:
    effective_rubric = rubric or default_rubric(suite)
    cases = _indexed_items(suite.get("cases"), "case_id", "evaluation cases")
    results = _indexed_items(candidate.get("results"), "case_id", "candidate results")
    missing = sorted(set(cases).difference(results))
    unknown = sorted(set(results).difference(cases))
    if missing or unknown:
        details = []
        if missing:
            details.append(f"missing results: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown results: {', '.join(unknown)}")
        raise ValueError("Candidate case coverage mismatch; " + "; ".join(details))

    minimum_score = effective_rubric.release_minimum_aggregate_score
    case_reports = [
        _evaluate_case(cases[case_id], results[case_id], effective_rubric) for case_id in cases
    ]
    aggregate_score = round(sum(item["score"] for item in case_reports) / len(case_reports), 3)
    safety_failures = [item["case_id"] for item in case_reports if item["safety_critical"] and not item["passed"]]
    reasons = []
    if aggregate_score < minimum_score:
        reasons.append(f"aggregate score {aggregate_score:.3f} is below {minimum_score:.3f}")
    if effective_rubric.require_all_safety_cases and safety_failures:
        reasons.append("safety-critical cases failed: " + ", ".join(safety_failures))

    return {
        "report_version": "0.3",
        "suite_id": str(suite.get("suite_id", "")),
        "candidate_id": str(candidate.get("candidate_id", "")),
        "method": "deterministic contract evaluation; no LLM judge",
        "summary": {
            "total_cases": len(case_reports),
            "passed_cases": sum(item["passed"] for item in case_reports),
            "failed_cases": sum(not item["passed"] for item in case_reports),
            "aggregate_score": aggregate_score,
            "minimum_aggregate_score": minimum_score,
            "case_pass_threshold": effective_rubric.case_pass_threshold,
        },
        "release_gate": {
            "passed": not reasons,
            "reasons": reasons,
            "safety_critical_failures": safety_failures,
        },
        "dimension_weights": effective_rubric.dimension_weights,
        "effective_rubric": effective_rubric.to_dict(),
        "cases": case_reports,
        "limitations": [
            "Rules measure declared contracts and text evidence, not semantic truth or model intelligence.",
            "Synthetic cases do not estimate production accuracy, latency, cost or user value.",
            "A human must review the suite, thresholds and every safety-critical failure before release.",
        ],
    }


def write_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Agent Evaluation Report",
        "",
        f"- Suite: `{report['suite_id']}`",
        f"- Candidate: `{report['candidate_id']}`",
        f"- Method: {report['method']}",
        f"- Rubric: `{report['effective_rubric']['rubric_id']}` v{report['effective_rubric']['version']}",
        f"- Aggregate score: **{report['summary']['aggregate_score']:.3f}**",
        f"- Release gate: **{'PASS' if report['release_gate']['passed'] else 'FAIL'}**",
        "",
        "| Case | Category | Score | Result | Failed dimensions |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in report["cases"]:
        failures = ", ".join(item["failed_dimensions"]) or "none"
        rows.append(f"| {item['case_id']} | {item['category']} | {item['score']:.3f} | {'PASS' if item['passed'] else 'FAIL'} | {failures} |")
    rows.extend(["", "## Release-gate reasons", ""])
    reasons = report["release_gate"]["reasons"] or ["All configured release-gate conditions passed."]
    rows.extend(f"- {reason}" for reason in reasons)
    rows.extend(["", "## Interpretation boundary", ""])
    rows.extend(f"- {item}" for item in report["limitations"])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _evaluate_case(
    case: dict[str, Any], result: dict[str, Any], rubric: RubricConfig
) -> dict[str, Any]:
    expected_status = str(case.get("expected_status", ""))
    actual_status = str(result.get("status", ""))
    required_terms = [str(item).casefold() for item in case.get("required_evidence_terms", [])]
    haystack = _flatten_text(result).casefold()
    matched_terms = [term for term in required_terms if term in haystack]
    evidence_score = len(matched_terms) / len(required_terms) if required_terms else 1.0

    required_fields = [str(item) for item in case.get("required_fields", [])]
    present_fields = [field for field in required_fields if field in result and result[field] not in (None, "", [])]
    schema_score = len(present_fields) / len(required_fields) if required_fields else 1.0

    forbidden_terms = [str(item).casefold() for item in case.get("forbidden_terms", [])]
    found_forbidden = [term for term in forbidden_terms if term in haystack]
    scores = {
        "task_status": 1.0 if actual_status == expected_status else 0.0,
        "evidence_coverage": round(evidence_score, 3),
        "schema_completeness": round(schema_score, 3),
        "safety": 0.0 if found_forbidden else 1.0,
    }
    contributions = {
        name: round(scores[name] * weight, 3)
        for name, weight in rubric.dimension_weights.items()
    }
    total = round(sum(contributions.values()), 3)
    failed_dimensions = [name for name, score in scores.items() if score < 1.0]
    threshold_failures = [
        name for name, minimum in rubric.minimum_dimension_scores.items()
        if scores[name] < minimum
    ]
    return {
        "case_id": str(case.get("case_id", "")),
        "category": str(case.get("category", "general")),
        "safety_critical": bool(case.get("safety_critical", False)),
        "expected_status": expected_status,
        "actual_status": actual_status,
        "score": total,
        "passed": total >= rubric.case_pass_threshold and not threshold_failures,
        "dimensions": scores,
        "score_calculation": {
            "rubric_id": rubric.rubric_id,
            "weights": dict(rubric.dimension_weights),
            "weighted_contributions": contributions,
            "case_pass_threshold": rubric.case_pass_threshold,
            "minimum_dimension_scores": dict(rubric.minimum_dimension_scores),
            "minimum_dimension_failures": threshold_failures,
        },
        "matched_evidence_terms": matched_terms,
        "missing_evidence_terms": sorted(set(required_terms).difference(matched_terms)),
        "missing_fields": sorted(set(required_fields).difference(present_fields)),
        "found_forbidden_terms": found_forbidden,
        "failed_dimensions": failed_dimensions,
    }


def _indexed_items(value: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    indexed: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"Every item in {label} must be an object")
        item_id = str(item.get(key, "")).strip()
        if not item_id or item_id in indexed:
            raise ValueError(f"{key} values in {label} must be present and unique")
        indexed[item_id] = item
    return indexed


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)
