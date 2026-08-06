# Handoff

## Current state

- Release stage: v0.2 product-validation prototype.
- Maintenance completed: M1/10.
- Core flow: suite + named baseline + candidate run → four-dimension scores → case deltas → improvement/regression classification → explainable release gate.
- Sample result: 4/5 cases pass; a deliberate prohibited-claim failure blocks release.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agent_evaluation_lab.cli data/evaluation_suite.json data/candidate_run.json --json-output reports/evaluation_report.json --markdown-output reports/evaluation_report.md
PYTHONPATH=src python -m agent_evaluation_lab.comparison_cli data/evaluation_suite.json data/baseline_run.json data/candidate_run.json --json-output reports/comparison_report.json --markdown-output reports/comparison_report.md
```

## Next maintenance round

M2 should add configurable rubric weights and strict threshold validation. It must preserve deterministic defaults and report the effective rubric used for every score.

## Known limitations

- phrase-level deterministic rules only;
- five synthetic cases;
- one named baseline only; no trend history;
- no model execution, latency or cost evidence;
- no database, accounts, hosted API or real user study;
- browser view uses the bundled sample report.
