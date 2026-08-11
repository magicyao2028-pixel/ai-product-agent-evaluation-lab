# Handoff

## Current state

- Release stage: v0.3 product-validation prototype.
- Maintenance completed: M2/10.
- Core flow: suite + versioned rubric + named baseline + candidate run → validated weights and thresholds → four-dimension scores with contributions → case deltas → improvement/regression classification → explainable release gate.
- Sample result: 4/5 cases pass; a deliberate prohibited-claim failure blocks release.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agent_evaluation_lab.cli data/evaluation_suite.json data/candidate_run.json --rubric data/rubric.json --json-output reports/evaluation_report.json --markdown-output reports/evaluation_report.md
PYTHONPATH=src python -m agent_evaluation_lab.comparison_cli data/evaluation_suite.json data/baseline_run.json data/candidate_run.json --rubric data/rubric.json --json-output reports/comparison_report.json --markdown-output reports/comparison_report.md
```

## Next maintenance round

M3 should add a failure taxonomy and trend summary. It must distinguish task, evidence, schema, safety and evaluation-contract failures; keep raw case evidence visible; and avoid claiming statistical trends from the five-case sample.

## Known limitations

- phrase-level deterministic rules only;
- five synthetic cases;
- one named baseline only; no trend history;
- no model execution, latency or cost evidence;
- no database, accounts, hosted API or real user study;
- browser view uses the bundled sample report.
