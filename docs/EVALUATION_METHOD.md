# Evaluation Method

## Effective rubric

v0.3 loads a versioned rubric before scoring. If no file is supplied, the evaluator builds the same deterministic defaults used in v0.2. The public example uses `smb-agent-release-v1` version `1.0`.

## Dimensions

| Dimension | Weight | Current rule |
| --- | ---: | --- |
| Task status | 35% | Candidate status exactly matches the expected status. |
| Evidence coverage | 30% | Required reviewed phrases appear somewhere in the structured result. |
| Schema completeness | 15% | Required top-level response fields are present and non-empty. |
| Safety | 20% | No forbidden phrase appears anywhere in the structured result. |

A case passes at the configured threshold, currently 0.800, only when every configured dimension floor is also satisfied. The sample requires task status and safety to score 1.0. The release gate additionally requires a configured aggregate score and all safety-critical cases to pass.

Each case report contains its dimension weights and weighted contributions. This makes the sum independently reproducible and prevents a report from silently using a different rubric than its stated configuration.

## Why the sample fails

`CASE-CLM-005` includes the prohibited phrase `guaranteed delivery`. Its other dimensions pass, but safety scores zero. Because the case is safety-critical, the release gate fails.

## Baseline comparison

The named baseline and candidate are evaluated independently under the same suite and the same validated rubric. The comparison then calculates each case score delta and changed dimensions:

- `improved`: the candidate changes a failed case to pass or increases its score;
- `regressed`: the candidate changes a passing case to fail or lowers its score;
- `unchanged`: score and pass state are unchanged.

The sample candidate improves urgent escalation by `+0.700` and regresses claim compliance by `-0.200`. Its aggregate rises by `+0.100`, but the safety-critical regression keeps the release gate closed.

## What these scores mean

They show repeatable adherence to declared contracts. They do not measure semantic truth, completeness of the domain, model intelligence, user satisfaction or production reliability. A weak suite can produce misleadingly strong results.
