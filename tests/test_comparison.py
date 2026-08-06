import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_evaluation_lab import compare_files, compare_runs, write_comparison


ROOT = Path(__file__).parents[1]
SUITE = ROOT / "data" / "evaluation_suite.json"
BASELINE = ROOT / "data" / "baseline_run.json"
CANDIDATE = ROOT / "data" / "candidate_run.json"


class BaselineComparisonTests(unittest.TestCase):
    def test_identifies_improvement_and_regression(self):
        report = compare_files(SUITE, BASELINE, CANDIDATE)

        self.assertEqual(report["improvements"], ["CASE-ESC-002"])
        self.assertEqual(report["regressions"], ["CASE-CLM-005"])
        self.assertEqual(report["summary"]["aggregate_delta"], 0.1)
        self.assertEqual(report["release_gate"]["decision"], "blocked")

    def test_aggregate_gain_does_not_override_safety_regression(self):
        report = compare_files(SUITE, BASELINE, CANDIDATE)

        self.assertGreater(report["summary"]["candidate_aggregate_score"], report["summary"]["baseline_aggregate_score"])
        self.assertFalse(report["release_gate"]["candidate_passed"])
        self.assertIn("CASE-CLM-005", " ".join(report["release_gate"]["candidate_reasons"]))

    def test_rejects_identical_baseline_and_candidate_ids(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(ValueError, "must be different"):
            compare_runs(suite, baseline, baseline)

    def test_writes_reproducible_comparison_reports(self):
        report = compare_files(SUITE, BASELINE, CANDIDATE)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "comparison.json"
            markdown_path = Path(directory) / "comparison.md"
            write_comparison(report, json_path, markdown_path)

            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("CASE-ESC-002 | improved", markdown)
            self.assertIn("CASE-CLM-005 | regressed", markdown)


if __name__ == "__main__":
    unittest.main()
