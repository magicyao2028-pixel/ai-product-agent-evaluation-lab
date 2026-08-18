# Reviewer Trial Guide

## Purpose

This 15–20 minute offline trial evaluates one synthetic Agent run, applies the configured release gate, adds separate synthetic human-review annotations and proves that reviewer approval cannot erase an automated safety failure.

## Clean start

```bash
python -m venv .venv
python -m pip install -e .
agent-eval-trial
```

The command writes `reports/trial_report.json` and `reports/trial_report.md`.

## Expected result

- `overall_passed` is `true`, meaning the trial controls behaved as specified;
- the product release gate itself remains `false` because the deliberate forbidden claim is preserved;
- two reviewers disagree on `CASE-CLM-005`;
- the effective case decision remains `blocked_by_automated_gate`;
- all seven evidence claims and two external-component decisions validate.

## Important interpretation

A passing trial does not mean the candidate Agent is approved. It means the evaluator reliably preserved the known failure and its human-review disagreement. All fixtures are synthetic. A real pilot requires accountable reviewer identities, access control, retention, privacy review and a documented adjudication owner.
