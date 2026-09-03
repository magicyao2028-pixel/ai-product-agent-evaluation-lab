import unittest

from agent_evaluation_lab.feedback_replay import replay_reviewer_feedback


class FeedbackReplayTests(unittest.TestCase):
    def setUp(self):
        self.report = {"cases": [{"annotations": [{"annotation_id": "A-1"}, {"annotation_id": "A-2"}]}]}
        self.batch = [
            {"feedback_id": "F-1", "annotation_id": "A-1", "recorded_on": "2026-08-01", "status": "accepted", "summary": "ok", "applied": False},
            {"feedback_id": "F-2", "annotation_id": "A-2", "recorded_on": "2026-08-02", "status": "pending", "summary": "wait", "applied": False},
        ]

    def test_replays_only_accepted_feedback(self):
        result = replay_reviewer_feedback(self.batch, self.report)
        self.assertEqual(result["replayed_count"], 1)
        self.assertEqual(result["excluded_count"], 1)
        self.assertFalse(result["evaluation_mutated"])

    def test_unknown_annotation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "review report"):
            replay_reviewer_feedback([dict(self.batch[0], annotation_id="A-X")], self.report)

    def test_applied_feedback_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "apply review changes"):
            replay_reviewer_feedback([dict(self.batch[0], applied=True)], self.report)


if __name__ == "__main__":
    unittest.main()
