from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluator import evaluate_run, load_json
from .rubric import RubricConfig, load_rubric
from .taxonomy import EvaluationContractError


def analyze_files(
    suite_path: Path, run_paths: list[Path], rubric_path: Path | None = None
) -> dict[str, Any]:
    rubric = load_rubric(rubric_path) if rubric_path else None
    return analyze_runs(load_json(suite_path), [load_json(path) for path in run_paths], rubric)


def analyze_runs(
    suite: dict[str, Any], runs: list[dict[str, Any]], rubric: RubricConfig | None = None
) -> dict[str, Any]:
    if len(runs) < 2:
        raise EvaluationContractError("Trend analysis requires at least two ordered runs")
    run_ids = [str(run.get("candidate_id", "")).strip() for run in runs]
    if any(not run_id for run_id in run_ids) or len(set(run_ids)) != len(run_ids):
        raise EvaluationContractError("Ordered run candidate IDs must be present and unique")

    reports = [evaluate_run(suite, run, rubric) for run in runs]
    transitions = []
    regression_evidence = []
    for before, after in zip(reports, reports[1:]):
        before_cases = {case["case_id"]: case for case in before["cases"]}
        case_changes = []
        for after_case in after["cases"]:
            before_case = before_cases[after_case["case_id"]]
            before_codes = {event["code"] for event in before_case["failure_events"]}
            after_codes = {event["code"] for event in after_case["failure_events"]}
            delta = round(after_case["score"] - before_case["score"], 3)
            new_failures = sorted(after_codes - before_codes)
            resolved_failures = sorted(before_codes - after_codes)
            persistent_failures = sorted(before_codes & after_codes)
            if delta < 0 or new_failures or (before_case["passed"] and not after_case["passed"]):
                classification = "regressed"
            elif delta > 0 or resolved_failures or (after_case["passed"] and not before_case["passed"]):
                classification = "improved"
            else:
                classification = "unchanged"
            change = {
                "case_id": after_case["case_id"],
                "classification": classification,
                "score_delta": delta,
                "new_failures": new_failures,
                "resolved_failures": resolved_failures,
                "persistent_failures": persistent_failures,
            }
            case_changes.append(change)
            if classification == "regressed":
                regression_evidence.append({
                    "from_run": before["candidate_id"],
                    "to_run": after["candidate_id"],
                    "case_id": after_case["case_id"],
                    "score_delta": delta,
                    "new_failures": new_failures,
                    "raw_case_evidence": {
                        "expected_status": after_case["expected_status"],
                        "actual_status": after_case["actual_status"],
                        "missing_evidence_terms": after_case["missing_evidence_terms"],
                        "missing_fields": after_case["missing_fields"],
                        "found_forbidden_terms": after_case["found_forbidden_terms"],
                    },
                })
        transitions.append({
            "from_run": before["candidate_id"],
            "to_run": after["candidate_id"],
            "aggregate_delta": round(after["summary"]["aggregate_score"] - before["summary"]["aggregate_score"], 3),
            "regressed_cases": [item["case_id"] for item in case_changes if item["classification"] == "regressed"],
            "improved_cases": [item["case_id"] for item in case_changes if item["classification"] == "improved"],
            "cases": case_changes,
        })

    return {
        "trend_version": "0.4",
        "suite_id": reports[0]["suite_id"],
        "method": "ordered deterministic run comparison; no statistical inference and no LLM judge",
        "effective_rubric": reports[0]["effective_rubric"],
        "runs": [{
            "candidate_id": report["candidate_id"],
            "aggregate_score": report["summary"]["aggregate_score"],
            "passed_cases": report["summary"]["passed_cases"],
            "release_gate_passed": report["release_gate"]["passed"],
            "failure_summary": report["failure_summary"],
        } for report in reports],
        "transitions": transitions,
        "regression_evidence": regression_evidence,
        "interpretation": [
            "This ordered fixture shows observed changes across named synthetic runs, not a statistical trend.",
            "Five synthetic cases cannot estimate production accuracy, reliability or business impact.",
            "Every regression must be reviewed with its raw case evidence before release.",
        ],
    }


def write_trend(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Cross-run Evaluation Trend",
        "",
        f"- Suite: `{report['suite_id']}`",
        f"- Method: {report['method']}",
        "",
        "| Ordered run | Aggregate | Passed cases | Release gate | Failure events |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for run in report["runs"]:
        rows.append(
            f"| {run['candidate_id']} | {run['aggregate_score']:.3f} | {run['passed_cases']} | "
            f"{'PASS' if run['release_gate_passed'] else 'FAIL'} | {run['failure_summary']['total_events']} |"
        )
    rows.extend(["", "## Transition evidence", ""])
    for transition in report["transitions"]:
        rows.append(f"### {transition['from_run']} → {transition['to_run']} ({transition['aggregate_delta']:+.3f})")
        rows.append("")
        for case in transition["cases"]:
            if case["classification"] != "unchanged":
                rows.append(
                    f"- `{case['case_id']}`: {case['classification']} ({case['score_delta']:+.3f}); "
                    f"new={case['new_failures'] or ['none']}; resolved={case['resolved_failures'] or ['none']}"
                )
        rows.append("")
    rows.extend(["## Explicit regression evidence", ""])
    if not report["regression_evidence"]:
        rows.append("- No regression was observed in these ordered runs.")
    for item in report["regression_evidence"]:
        evidence = item["raw_case_evidence"]
        rows.append(
            f"- `{item['case_id']}` in `{item['from_run']} → {item['to_run']}`: "
            f"new failures {item['new_failures']}; forbidden terms {evidence['found_forbidden_terms']}; "
            f"missing evidence {evidence['missing_evidence_terms']}; missing fields {evidence['missing_fields']}."
        )
    rows.extend(["", "## Interpretation boundary", ""])
    rows.extend(f"- {item}" for item in report["interpretation"])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
