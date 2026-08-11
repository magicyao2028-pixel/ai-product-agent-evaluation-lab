# Rubric Configuration

## Purpose

M2 makes scoring policy explicit. A product owner can review one versioned rubric instead of relying on weights and thresholds hidden in code.

## Required structure

The rubric defines:

- a stable `rubric_id` and `version`;
- exactly four positive dimension weights that sum to `1.0`;
- a case pass threshold between `0` and `1`;
- minimum scores for at least `task_status` and `safety`;
- an aggregate release threshold and a boolean safety-case gate.

## Strict validation

Evaluation stops before scoring when the rubric has missing or unknown dimensions, duplicate policy through unknown fields, zero or negative weights, weights that do not sum to `1.0`, booleans disguised as numbers, non-finite values, thresholds outside `0..1`, or an incomplete release gate.

## Score evidence

Every case contains:

```json
{
  "score_calculation": {
    "rubric_id": "smb-agent-release-v1",
    "weights": {},
    "weighted_contributions": {},
    "case_pass_threshold": 0.8,
    "minimum_dimension_scores": {},
    "minimum_dimension_failures": []
  }
}
```

The baseline and candidate in a comparison are evaluated with the same `RubricConfig` object. A higher aggregate score still cannot override a failed configured safety floor or safety-critical release gate.
