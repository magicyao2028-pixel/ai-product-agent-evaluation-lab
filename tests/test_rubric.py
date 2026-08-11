import json
import unittest
from pathlib import Path

from agent_evaluation_lab import RubricConfig, compare_files, evaluate_files, evaluate_run, load_rubric


ROOT = Path(__file__).parents[1]
SUITE = ROOT / "data" / "evaluation_suite.json"
BASELINE = ROOT / "data" / "baseline_run.json"
CANDIDATE = ROOT / "data" / "candidate_run.json"
RUBRIC = ROOT / "data" / "rubric.json"


def rubric_payload() -> dict:
    return json.loads(RUBRIC.read_text(encoding="utf-8"))


class RubricTests(unittest.TestCase):
    def test_reports_effective_rubric_for_every_case_score(self):
        report = evaluate_files(SUITE, CANDIDATE, RUBRIC)

        self.assertEqual(report["effective_rubric"]["rubric_id"], "smb-agent-release-v1")
        for case in report["cases"]:
            calculation = case["score_calculation"]
            self.assertEqual(calculation["rubric_id"], "smb-agent-release-v1")
            self.assertEqual(calculation["weights"], report["effective_rubric"]["dimension_weights"])
            self.assertAlmostEqual(sum(calculation["weighted_contributions"].values()), case["score"])

    def test_custom_weights_change_scores_deterministically(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        payload = rubric_payload()
        payload["rubric_id"] = "safety-heavy-v1"
        payload["dimension_weights"] = {
            "task_status": 0.25,
            "evidence_coverage": 0.20,
            "schema_completeness": 0.15,
            "safety": 0.40,
        }
        report = evaluate_run(suite, candidate, RubricConfig.from_mapping(payload))
        claim_case = next(item for item in report["cases"] if item["case_id"] == "CASE-CLM-005")

        self.assertEqual(claim_case["score"], 0.6)
        self.assertEqual(report["summary"]["aggregate_score"], 0.92)
        self.assertFalse(report["release_gate"]["passed"])

    def test_comparison_uses_one_effective_rubric(self):
        report = compare_files(SUITE, BASELINE, CANDIDATE, RUBRIC)
        self.assertEqual(report["effective_rubric"]["rubric_id"], "smb-agent-release-v1")
        self.assertTrue(all(item["rubric_id"] == "smb-agent-release-v1" for item in report["cases"]))

    def test_rejects_missing_unknown_or_unbalanced_weights(self):
        payload = rubric_payload()
        del payload["dimension_weights"]["safety"]
        with self.assertRaisesRegex(ValueError, "Missing dimensions"):
            RubricConfig.from_mapping(payload)

        payload = rubric_payload()
        payload["dimension_weights"]["style"] = 0.1
        with self.assertRaisesRegex(ValueError, "Unknown dimensions"):
            RubricConfig.from_mapping(payload)

        payload = rubric_payload()
        payload["dimension_weights"]["task_status"] = 0.34
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            RubricConfig.from_mapping(payload)

    def test_rejects_invalid_thresholds_and_boolean_numbers(self):
        payload = rubric_payload()
        payload["case_pass_threshold"] = 1.1
        with self.assertRaisesRegex(ValueError, "finite number between 0 and 1"):
            RubricConfig.from_mapping(payload)

        payload = rubric_payload()
        payload["dimension_weights"]["task_status"] = True
        with self.assertRaisesRegex(ValueError, "finite number between 0 and 1"):
            RubricConfig.from_mapping(payload)

        payload = rubric_payload()
        payload["release_gate"]["minimum_aggregate_score"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite number between 0 and 1"):
            RubricConfig.from_mapping(payload)

    def test_rejects_missing_status_or_safety_floor(self):
        payload = rubric_payload()
        del payload["minimum_dimension_scores"]["safety"]
        with self.assertRaisesRegex(ValueError, "must include task_status and safety"):
            RubricConfig.from_mapping(payload)

    def test_loaded_rubric_preserves_strict_release_gate(self):
        rubric = load_rubric(RUBRIC)
        self.assertEqual(rubric.case_pass_threshold, 0.8)
        self.assertEqual(rubric.release_minimum_aggregate_score, 0.9)
        self.assertTrue(rubric.require_all_safety_cases)


if __name__ == "__main__":
    unittest.main()
