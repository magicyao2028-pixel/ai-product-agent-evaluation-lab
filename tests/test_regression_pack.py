import unittest

from agent_evaluation_lab.regression_pack import build_feedback_regression_pack


class RegressionPackTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "raw_evaluation_mutated": False,
            "cases": [{
                "case_id": "CASE-1", "automated_passed": False,
                "effective_decision": "blocked_by_automated_gate",
                "annotations": [{"annotation_id": "ANN-1"}],
            }],
        }
        self.replay = {
            "evaluation_mutated": False, "release_authority": False,
            "replayed": [{"feedback_id": "FB-1", "annotation_id": "ANN-1", "status": "accepted", "passed": True}],
        }

    def test_builds_non_executing_regression_item(self):
        result = build_feedback_regression_pack(self.report, self.replay)
        self.assertEqual(result["item_count"], 1)
        self.assertEqual(result["items"][0]["expected_gate"], "blocked")
        self.assertFalse(result["regression_execution_executed"])

    def test_rejects_mutated_review_report(self):
        self.report["raw_evaluation_mutated"] = True
        with self.assertRaisesRegex(ValueError, "immutable"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_rejects_authoritative_replay(self):
        self.replay["release_authority"] = True
        with self.assertRaisesRegex(ValueError, "non-authoritative"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_rejects_empty_accepted_records(self):
        self.replay["replayed"] = []
        with self.assertRaisesRegex(ValueError, "accepted records"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_rejects_unknown_annotation(self):
        self.replay["replayed"][0]["annotation_id"] = "ANN-X"
        with self.assertRaisesRegex(ValueError, "current annotation"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_rejects_nonaccepted_record(self):
        self.replay["replayed"][0]["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "accepted feedback"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_rejects_duplicate_feedback_ids(self):
        self.replay["replayed"].append(dict(self.replay["replayed"][0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_rejects_duplicate_annotation_ids(self):
        self.report["cases"].append({
            "case_id": "CASE-2", "automated_passed": True,
            "effective_decision": "passed",
            "annotations": [{"annotation_id": "ANN-1"}],
        })
        with self.assertRaisesRegex(ValueError, "annotation IDs must be unique"):
            build_feedback_regression_pack(self.report, self.replay)

    def test_passed_case_keeps_gate_unchanged(self):
        self.report["cases"][0]["automated_passed"] = True
        result = build_feedback_regression_pack(self.report, self.replay)
        self.assertEqual(result["items"][0]["expected_gate"], "unchanged")


if __name__ == "__main__":
    unittest.main()
