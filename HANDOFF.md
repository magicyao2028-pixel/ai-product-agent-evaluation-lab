# Handoff

## Current state

- Release stage: v0.1 product-validation prototype.
- Maintenance completed: 0/10.
- Core flow: suite + candidate run → coverage validation → four-dimension scores → explainable release gate → JSON/Markdown reports.
- Sample result: 4/5 cases pass; a deliberate prohibited-claim failure blocks release.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agent_evaluation_lab.cli data/evaluation_suite.json data/candidate_run.json --json-output reports/evaluation_report.json --markdown-output reports/evaluation_report.md
```

## Next maintenance round

M1 should compare a named baseline run with a candidate run and report per-case regressions and improvements. It should preserve the current deterministic evaluator and must not add an LLM judge yet.

## Known limitations

- phrase-level deterministic rules only;
- five synthetic cases;
- no baseline comparison or trend history;
- no model execution, latency or cost evidence;
- no database, accounts, hosted API or real user study;
- browser view uses the bundled sample report.
