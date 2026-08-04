import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_evaluation_lab import evaluate_files, evaluate_run, write_report


ROOT = Path(__file__).parents[1]
SUITE = ROOT / "data" / "evaluation_suite.json"
CANDIDATE = ROOT / "data" / "candidate_run.json"


class AgentEvaluationTests(unittest.TestCase):
    def test_sample_run_exposes_claim_failure_and_blocks_release(self):
        report = evaluate_files(SUITE, CANDIDATE)

        self.assertEqual(report["summary"]["passed_cases"], 4)
        self.assertFalse(report["release_gate"]["passed"])
        self.assertEqual(report["release_gate"]["safety_critical_failures"], ["CASE-CLM-005"])
        claim_case = next(item for item in report["cases"] if item["case_id"] == "CASE-CLM-005")
        self.assertIn("guaranteed delivery", claim_case["found_forbidden_terms"])

    def test_corrected_claim_passes_release_gate(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        candidate["results"][-1]["answer"] = "Use only approved delivery data and obtain human approval before publishing."

        report = evaluate_run(suite, candidate)

        self.assertTrue(report["release_gate"]["passed"])
        self.assertEqual(report["summary"]["passed_cases"], 5)

    def test_rejects_missing_candidate_case(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        candidate["results"].pop()

        with self.assertRaisesRegex(ValueError, "missing results"):
            evaluate_run(suite, candidate)

    def test_rejects_duplicate_case_ids(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        suite["cases"].append(copy.deepcopy(suite["cases"][0]))

        with self.assertRaisesRegex(ValueError, "present and unique"):
            evaluate_run(suite, candidate)

    def test_missing_schema_field_is_visible(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        candidate["results"][0].pop("trace")

        report = evaluate_run(suite, candidate)

        self.assertEqual(report["cases"][0]["missing_fields"], ["trace"])
        self.assertLess(report["cases"][0]["dimensions"]["schema_completeness"], 1)

    def test_writes_reproducible_json_and_markdown(self):
        report = evaluate_files(SUITE, CANDIDATE)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "report.json"
            markdown_path = Path(directory) / "report.md"
            write_report(report, json_path, markdown_path)

            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            self.assertIn("Release gate: **FAIL**", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
