import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_evaluation_lab import EvaluationContractError, analyze_files, analyze_runs, evaluate_files, write_trend


ROOT = Path(__file__).parents[1]
SUITE = ROOT / "data" / "evaluation_suite.json"
BASELINE = ROOT / "data" / "baseline_run.json"
TRIAL = ROOT / "data" / "trial_run.json"
CANDIDATE = ROOT / "data" / "candidate_run.json"
RUBRIC = ROOT / "data" / "rubric.json"


class FailureTaxonomyAndTrendTests(unittest.TestCase):
    def test_case_report_has_stable_failure_taxonomy_and_raw_evidence(self):
        report = evaluate_files(SUITE, CANDIDATE, RUBRIC)
        claim = next(case for case in report["cases"] if case["case_id"] == "CASE-CLM-005")
        self.assertEqual([event["code"] for event in claim["failure_events"]], ["SAFETY_FORBIDDEN_CONTENT"])
        self.assertEqual(claim["failure_events"][0]["evidence"]["found_terms"], ["guaranteed delivery"])
        self.assertEqual(report["failure_summary"]["by_category"], {"safety": 1})

    def test_distinguishes_task_evidence_schema_and_safety_failures(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        broken = candidate["results"][0]
        broken["status"] = "no_evidence"
        broken["answer"] = "automatic refund"
        broken.pop("trace")
        report = analyze_runs(suite, [json.loads(BASELINE.read_text()), candidate])
        case = next(item for item in report["regression_evidence"] if item["case_id"] == "CASE-RET-001")
        self.assertEqual(
            case["new_failures"],
            ["EVIDENCE_MISSING", "SAFETY_FORBIDDEN_CONTENT", "SCHEMA_INCOMPLETE", "TASK_STATUS_MISMATCH"],
        )

    def test_three_run_summary_preserves_explicit_regression_evidence(self):
        report = analyze_files(SUITE, [BASELINE, TRIAL, CANDIDATE], RUBRIC)
        self.assertEqual([run["aggregate_score"] for run in report["runs"]], [0.86, 1.0, 0.96])
        self.assertEqual(report["transitions"][0]["improved_cases"], ["CASE-ESC-002"])
        self.assertEqual(report["transitions"][1]["regressed_cases"], ["CASE-CLM-005"])
        evidence = report["regression_evidence"][0]
        self.assertEqual(evidence["new_failures"], ["SAFETY_FORBIDDEN_CONTENT"])
        self.assertEqual(evidence["raw_case_evidence"]["found_forbidden_terms"], ["guaranteed delivery"])

    def test_rejects_too_few_or_duplicate_ordered_runs(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "at least two"):
            analyze_runs(suite, [baseline])
        with self.assertRaisesRegex(ValueError, "present and unique"):
            analyze_runs(suite, [baseline, copy.deepcopy(baseline)])

    def test_contract_error_exposes_machine_readable_taxonomy(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        candidate["results"].pop()
        with self.assertRaises(EvaluationContractError) as caught:
            analyze_runs(suite, [json.loads(BASELINE.read_text()), candidate])
        event = caught.exception.as_failure_event()
        self.assertEqual(event["code"], "EVALUATION_CONTRACT_INVALID")
        self.assertEqual(event["category"], "evaluation_contract")

    def test_writes_reproducible_trend_reports_with_boundary(self):
        report = analyze_files(SUITE, [BASELINE, TRIAL, CANDIDATE], RUBRIC)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "trend.json"
            markdown_path = Path(directory) / "trend.md"
            write_trend(report, json_path, markdown_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("Explicit regression evidence", markdown)
            self.assertIn("not a statistical trend", markdown)


if __name__ == "__main__":
    unittest.main()
