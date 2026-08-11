from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluator import evaluate_run, load_json
from .rubric import RubricConfig, load_rubric


def compare_files(
    suite_path: Path,
    baseline_path: Path,
    candidate_path: Path,
    rubric_path: Path | None = None,
) -> dict[str, Any]:
    rubric = load_rubric(rubric_path) if rubric_path else None
    return compare_runs(
        load_json(suite_path), load_json(baseline_path), load_json(candidate_path), rubric
    )


def compare_runs(
    suite: dict[str, Any],
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    rubric: RubricConfig | None = None,
) -> dict[str, Any]:
    baseline_id = str(baseline.get("candidate_id", "")).strip()
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    if not baseline_id or not candidate_id:
        raise ValueError("Baseline and candidate IDs must not be blank")
    if baseline_id == candidate_id:
        raise ValueError("Baseline and candidate IDs must be different")

    baseline_report = evaluate_run(suite, baseline, rubric)
    candidate_report = evaluate_run(suite, candidate, rubric)
    baseline_cases = {item["case_id"]: item for item in baseline_report["cases"]}
    case_deltas = []
    for candidate_case in candidate_report["cases"]:
        baseline_case = baseline_cases[candidate_case["case_id"]]
        delta = round(candidate_case["score"] - baseline_case["score"], 3)
        if candidate_case["passed"] and not baseline_case["passed"]:
            classification = "improved"
        elif baseline_case["passed"] and not candidate_case["passed"]:
            classification = "regressed"
        elif delta > 0:
            classification = "improved"
        elif delta < 0:
            classification = "regressed"
        else:
            classification = "unchanged"
        changed_dimensions = [
            name for name, score in candidate_case["dimensions"].items()
            if score != baseline_case["dimensions"][name]
        ]
        case_deltas.append({
            "case_id": candidate_case["case_id"],
            "category": candidate_case["category"],
            "classification": classification,
            "baseline_score": baseline_case["score"],
            "candidate_score": candidate_case["score"],
            "score_delta": delta,
            "baseline_passed": baseline_case["passed"],
            "candidate_passed": candidate_case["passed"],
            "changed_dimensions": changed_dimensions,
            "candidate_failed_dimensions": candidate_case["failed_dimensions"],
            "rubric_id": candidate_case["score_calculation"]["rubric_id"],
        })

    aggregate_delta = round(
        candidate_report["summary"]["aggregate_score"] - baseline_report["summary"]["aggregate_score"],
        3,
    )
    improvements = [item["case_id"] for item in case_deltas if item["classification"] == "improved"]
    regressions = [item["case_id"] for item in case_deltas if item["classification"] == "regressed"]
    return {
        "comparison_version": "0.3",
        "suite_id": baseline_report["suite_id"],
        "baseline_id": baseline_id,
        "candidate_id": candidate_id,
        "method": "deterministic case-score comparison; no LLM judge",
        "effective_rubric": candidate_report["effective_rubric"],
        "summary": {
            "baseline_aggregate_score": baseline_report["summary"]["aggregate_score"],
            "candidate_aggregate_score": candidate_report["summary"]["aggregate_score"],
            "aggregate_delta": aggregate_delta,
            "improved_cases": len(improvements),
            "regressed_cases": len(regressions),
            "unchanged_cases": len(case_deltas) - len(improvements) - len(regressions),
        },
        "release_gate": {
            "baseline_passed": baseline_report["release_gate"]["passed"],
            "candidate_passed": candidate_report["release_gate"]["passed"],
            "candidate_reasons": candidate_report["release_gate"]["reasons"],
            "decision": "eligible_for_human_release_review" if candidate_report["release_gate"]["passed"] else "blocked",
        },
        "improvements": improvements,
        "regressions": regressions,
        "cases": case_deltas,
        "interpretation": [
            "Aggregate improvement does not override a safety-critical regression.",
            "The named baseline is a comparison reference, not a universal benchmark.",
            "A human reviewer must decide whether the suite and changed behavior match the intended business policy.",
        ],
    }


def write_comparison(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Agent Baseline Comparison",
        "",
        f"- Suite: `{report['suite_id']}`",
        f"- Baseline: `{report['baseline_id']}`",
        f"- Candidate: `{report['candidate_id']}`",
        f"- Rubric: `{report['effective_rubric']['rubric_id']}` v{report['effective_rubric']['version']}",
        f"- Aggregate: **{report['summary']['baseline_aggregate_score']:.3f} → {report['summary']['candidate_aggregate_score']:.3f}** ({report['summary']['aggregate_delta']:+.3f})",
        f"- Candidate release gate: **{'PASS' if report['release_gate']['candidate_passed'] else 'FAIL'}**",
        "",
        "| Case | Classification | Baseline | Candidate | Delta | Changed dimensions |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in report["cases"]:
        dimensions = ", ".join(item["changed_dimensions"]) or "none"
        rows.append(
            f"| {item['case_id']} | {item['classification']} | {item['baseline_score']:.3f} | "
            f"{item['candidate_score']:.3f} | {item['score_delta']:+.3f} | {dimensions} |"
        )
    rows.extend(["", "## Release decision", ""])
    reasons = report["release_gate"]["candidate_reasons"] or ["Candidate passed every configured gate."]
    rows.extend(f"- {reason}" for reason in reasons)
    rows.extend(["", "## Interpretation boundary", ""])
    rows.extend(f"- {item}" for item in report["interpretation"])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
