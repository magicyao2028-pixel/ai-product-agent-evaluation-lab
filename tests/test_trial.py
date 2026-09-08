import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_evaluation_lab.trial import (
    load_json_object,
    run_trial,
    validate_evidence_index,
    validate_external_intake,
    validate_feedback,
    write_trial_report,
)
from agent_evaluation_lab.review_history import validate_review_history


ROOT = Path(__file__).parents[1]


class TrialReadinessTests(unittest.TestCase):
    def test_complete_trial_passes_and_preserves_safety_gate(self):
        report = run_trial(ROOT)
        self.assertTrue(report["overall_passed"])
        self.assertFalse(report["core_flow"]["automated_release_passed"])
        self.assertEqual(report["core_flow"]["disagreements"], 1)
        self.assertEqual(report["core_flow"]["claim_effective_decision"], "blocked_by_automated_gate")
        self.assertFalse(report["reviewer_decision_export"]["decisions_applied"])
        self.assertFalse(report["review_history_summary"]["evaluation_mutated"])
        self.assertEqual(report["reviewer_decision_export"]["decision_count"], len(report["review_queue"]["items"]))

    def test_evidence_index_links_eleven_real_claims(self):
        result = validate_evidence_index(ROOT, load_json_object(ROOT / "evidence/evidence_index.json"))
        self.assertEqual(len(result), 13)

    def test_external_intake_rejects_short_sha_and_false_adoption(self):
        payload = load_json_object(ROOT / "evidence/external_intake.json")
        short = deepcopy(payload)
        short["candidates"][0]["commit"] = "abc123"
        with self.assertRaisesRegex(ValueError, "full commit SHA"):
            validate_external_intake(short)
        inconsistent = deepcopy(payload)
        inconsistent["candidates"][0]["code_adopted"] = True
        with self.assertRaisesRegex(ValueError, "must agree"):
            validate_external_intake(inconsistent)

    def test_feedback_source_must_be_explicit(self):
        payload = load_json_object(ROOT / "evidence/feedback_case.json")
        payload["source_type"] = "operator"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_feedback(ROOT, payload)

        payload = load_json_object(ROOT / "evidence/feedback_case.json")
        payload["classification"] = "anything"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_feedback(ROOT, payload)

        payload = load_json_object(ROOT / "evidence/feedback_case.json")
        payload["decision"] = "rejected"
        with self.assertRaisesRegex(ValueError, "accepted decision"):
            validate_feedback(ROOT, payload)

    def test_trial_report_is_reproducible(self):
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "trial.json"
            markdown_path = Path(directory) / "trial.md"
            first = write_trial_report(ROOT, json_path, markdown_path)
            first_bytes = (json_path.read_bytes(), markdown_path.read_bytes())
            second = write_trial_report(ROOT, json_path, markdown_path)
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, (json_path.read_bytes(), markdown_path.read_bytes()))
            self.assertTrue(json.loads(json_path.read_text(encoding="utf-8"))["overall_passed"])

    def test_review_history_is_chronological_and_non_authoritative(self):
        report = validate_review_history(load_json_object(ROOT / "data/review_history.json"))
        self.assertEqual(report["entry_count"], 2)
        self.assertEqual(report["latest_batch_id"], "SYN-REVIEW-BATCH-002")
        self.assertFalse(report["release_authority"])


if __name__ == "__main__":
    unittest.main()
