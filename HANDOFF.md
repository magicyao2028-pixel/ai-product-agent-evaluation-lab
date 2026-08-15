# Handoff

## Current state

- Release stage: v0.4 product-validation prototype.
- Maintenance completed: M3/10.
- Core flow: suite + versioned rubric + ordered named runs → validated contracts → four-dimension scores → stable failure events → adjacent transitions → raw regression evidence → explainable release gate.
- Sample result: 4/5 cases pass; a deliberate prohibited-claim failure blocks release.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agent_evaluation_lab.cli data/evaluation_suite.json data/candidate_run.json --rubric data/rubric.json --json-output reports/evaluation_report.json --markdown-output reports/evaluation_report.md
PYTHONPATH=src python -m agent_evaluation_lab.comparison_cli data/evaluation_suite.json data/baseline_run.json data/candidate_run.json --rubric data/rubric.json --json-output reports/comparison_report.json --markdown-output reports/comparison_report.md
PYTHONPATH=src python -m agent_evaluation_lab.trend_cli data/evaluation_suite.json data/baseline_run.json data/trial_run.json data/candidate_run.json --rubric data/rubric.json --json-output reports/trend_report.json --markdown-output reports/trend_report.md
```

## Next maintenance round

M4 should add human-review annotations and disagreement tracking. It must keep automated observations separate from reviewer decisions, identify synthetic annotations, and never overwrite raw evaluation evidence.

## Known limitations

- phrase-level deterministic rules only;
- five synthetic cases;
- one three-run synthetic history only; no persistence or real reviewer history;
- no model execution, latency or cost evidence;
- no database, accounts, hosted API or real user study;
- browser view uses the bundled sample report.
