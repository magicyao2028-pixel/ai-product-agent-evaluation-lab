# Handoff

## Current state

- Release stage: v0.8 trial-readiness prototype.
- Maintenance completed: M7/10.
- Core flow: suite + rubric + candidate → automated failure evidence → separate human annotations → consensus/disagreement → non-overridable safety gate → deterministic trial evidence.
- Sample result: 4/5 cases pass; a deliberate prohibited-claim failure blocks release.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agent_evaluation_lab.cli data/evaluation_suite.json data/candidate_run.json --rubric data/rubric.json --json-output reports/evaluation_report.json --markdown-output reports/evaluation_report.md
PYTHONPATH=src python -m agent_evaluation_lab.comparison_cli data/evaluation_suite.json data/baseline_run.json data/candidate_run.json --rubric data/rubric.json --json-output reports/comparison_report.json --markdown-output reports/comparison_report.md
PYTHONPATH=src python -m agent_evaluation_lab.trend_cli data/evaluation_suite.json data/baseline_run.json data/trial_run.json data/candidate_run.json --rubric data/rubric.json --json-output reports/trend_report.json --markdown-output reports/trend_report.md
PYTHONPATH=src python -m agent_evaluation_lab.review_cli reports/evaluation_report.json data/review_annotations.json --json-output reports/review_report.json --markdown-output reports/review_report.md
PYTHONPATH=src python -m agent_evaluation_lab.trial_cli
```

## M6 result

- Added a bounded queue for failed, disputed and adjudication-required cases.
- Added a synthetic adjudication receipt that records reviewer accountability but cannot reopen an automated safety failure.
- The trial now verifies queue export, receipt validation and authority preservation.
- Added a chronological, append-only review-history fixture and validator. It preserves snapshot digests and review status while explicitly granting no release authority.
- Added a deterministic reviewer-decision export that maps blocked, disputed and review-blocked cases to bounded next actions without applying decisions or changing automated evidence.

## Next maintenance round

M8 can add bounded history/feedback replay visibility, only if it preserves immutable automated evidence and the same synthetic/public-safe boundary.

## Known limitations

- phrase-level deterministic rules only;
- five synthetic cases;
- one three-run synthetic history only; no persistence or real reviewer history;
- no model execution, latency or cost evidence;
- no database, accounts, hosted API or real user study;
- browser view uses the bundled sample report.
