import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_evaluation_lab import evaluate_files
from agent_evaluation_lab.reviews import (
    analyze_review_annotations,
    build_review_queue,
    create_adjudication_receipt,
    write_review_report,
)
from agent_evaluation_lab.reviewer_decisions import build_reviewer_decision_export


ROOT = Path(__file__).parents[1]


class HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.evaluation = evaluate_files(
            ROOT / "data" / "evaluation_suite.json",
            ROOT / "data" / "candidate_run.json",
            ROOT / "data" / "rubric.json",
        )
        self.annotations = json.loads((ROOT / "data" / "review_annotations.json").read_text(encoding="utf-8"))

    def test_tracks_consensus_and_disagreement_without_overwriting_evidence(self):
        before = copy.deepcopy(self.evaluation)
        report = analyze_review_annotations(self.evaluation, self.annotations)
        self.assertEqual(self.evaluation, before)
        self.assertFalse(report["raw_evaluation_mutated"])
        self.assertEqual(report["summary"]["disagreements"], 1)
        claim = next(case for case in report["cases"] if case["case_id"] == "CASE-CLM-005")
        self.assertEqual(claim["review_state"], "disagreement")
        self.assertEqual(claim["effective_decision"], "blocked_by_automated_gate")
        self.assertEqual(claim["automated_failure_events"][0]["code"], "SAFETY_FORBIDDEN_CONTENT")

    def test_approval_cannot_override_automated_safety_failure(self):
        changed = copy.deepcopy(self.annotations)
        changed["annotations"] = [changed["annotations"][2]]
        report = analyze_review_annotations(self.evaluation, changed)
        self.assertEqual(report["summary"]["release_status"], "blocked_by_automated_gate")
        self.assertEqual(report["cases"][0]["effective_decision"], "blocked_by_automated_gate")

    def test_rejects_unknown_case_duplicate_annotation_and_false_failure_code(self):
        unknown = copy.deepcopy(self.annotations)
        unknown["annotations"][0]["case_id"] = "CASE-UNKNOWN"
        with self.assertRaisesRegex(ValueError, "Unknown annotation case_id"):
            analyze_review_annotations(self.evaluation, unknown)
        duplicate = copy.deepcopy(self.annotations)
        duplicate["annotations"][1]["annotation_id"] = duplicate["annotations"][0]["annotation_id"]
        with self.assertRaisesRegex(ValueError, "must be unique"):
            analyze_review_annotations(self.evaluation, duplicate)
        false_code = copy.deepcopy(self.annotations)
        false_code["annotations"][0]["cited_failure_codes"] = ["SAFETY_FORBIDDEN_CONTENT"]
        with self.assertRaisesRegex(ValueError, "absent from raw"):
            analyze_review_annotations(self.evaluation, false_code)

    def test_review_reports_are_reproducible(self):
        report = analyze_review_annotations(self.evaluation, self.annotations)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "review.json"
            md_path = Path(directory) / "review.md"
            write_review_report(report, json_path, md_path)
            first = (json_path.read_bytes(), md_path.read_bytes())
            write_review_report(report, json_path, md_path)
            self.assertEqual(first, (json_path.read_bytes(), md_path.read_bytes()))

    def test_review_queue_and_adjudication_preserve_safety_authority(self):
        report = analyze_review_annotations(self.evaluation, self.annotations)
        queue = build_review_queue(self.evaluation, report)
        receipt = create_adjudication_receipt(
            report,
            {
                "receipt_id": "ADJ-TEST-001",
                "adjudicator_id": "review-lead",
                "recorded_on": "2026-08-23",
                "decision": "approve",
                "rationale": "Approval is recorded for audit but cannot reopen the automated failure.",
                "case_ids": ["CASE-CLM-005"],
            },
        )

        self.assertTrue(queue["items"])
        self.assertEqual(queue["items"][0]["priority"], "critical")
        self.assertTrue(receipt["automated_gate_overrode_request"])
        self.assertEqual(receipt["effective_decision"], "blocked_by_automated_gate")

    def test_adjudication_rejects_unknown_case(self):
        report = analyze_review_annotations(self.evaluation, self.annotations)
        with self.assertRaisesRegex(ValueError, "unknown case"):
            create_adjudication_receipt(
                report,
                {
                    "receipt_id": "ADJ-TEST-002",
                    "adjudicator_id": "review-lead",
                    "recorded_on": "2026-08-23",
                    "decision": "needs_changes",
                    "rationale": "Unknown case should fail closed.",
                    "case_ids": ["CASE-UNKNOWN"],
                },
            )

    def test_reviewer_decision_export_is_bounded_and_preserves_safety(self):
        report = analyze_review_annotations(self.evaluation, self.annotations)
        queue = build_review_queue(self.evaluation, report)
        receipt = create_adjudication_receipt(
            report,
            {
                "receipt_id": "ADJ-TEST-003",
                "adjudicator_id": "review-lead",
                "recorded_on": "2026-08-23",
                "decision": "approve",
                "rationale": "Record only; automated safety remains authoritative.",
                "case_ids": ["CASE-CLM-005"],
            },
        )
        exported = build_reviewer_decision_export(self.evaluation, report, queue, receipt)
        safety = next(item for item in exported["decisions"] if item["case_id"] == "CASE-CLM-005")
        self.assertEqual(safety["status"], "blocked")
        self.assertEqual(safety["recommended_action"], "fix_candidate_and_rerun_evaluation")
        self.assertFalse(exported["decisions_applied"])
        self.assertFalse(exported["release_authority"])
        self.assertEqual(exported["external_actions_executed"], 0)

    def test_reviewer_decision_export_rejects_snapshot_mismatch(self):
        report = analyze_review_annotations(self.evaluation, self.annotations)
        queue = build_review_queue(self.evaluation, report)
        queue["evaluation_snapshot_sha256"] = "sha256:wrong"
        receipt = create_adjudication_receipt(
            report,
            {
                "receipt_id": "ADJ-TEST-004",
                "adjudicator_id": "review-lead",
                "recorded_on": "2026-08-23",
                "decision": "needs_changes",
                "rationale": "Snapshot mismatch must fail closed.",
                "case_ids": ["CASE-CLM-005"],
            },
        )
        with self.assertRaisesRegex(ValueError, "snapshot"):
            build_reviewer_decision_export(self.evaluation, report, queue, receipt)


if __name__ == "__main__":
    unittest.main()
