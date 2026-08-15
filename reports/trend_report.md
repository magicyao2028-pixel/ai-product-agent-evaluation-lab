# Cross-run Evaluation Trend

- Suite: `SMB-KNOWLEDGE-AGENT-V1`
- Method: ordered deterministic run comparison; no statistical inference and no LLM judge

| Ordered run | Aggregate | Passed cases | Release gate | Failure events |
| --- | ---: | ---: | --- | ---: |
| KNOWLEDGE-AGENT-BASELINE-000 | 0.860 | 4 | FAIL | 3 |
| KNOWLEDGE-AGENT-TRIAL-001 | 1.000 | 5 | PASS | 0 |
| KNOWLEDGE-AGENT-DEMO-001 | 0.960 | 4 | FAIL | 1 |

## Transition evidence

### KNOWLEDGE-AGENT-BASELINE-000 → KNOWLEDGE-AGENT-TRIAL-001 (+0.140)

- `CASE-ESC-002`: improved (+0.700); new=['none']; resolved=['EVIDENCE_MISSING', 'SCHEMA_INCOMPLETE', 'TASK_STATUS_MISMATCH']

### KNOWLEDGE-AGENT-TRIAL-001 → KNOWLEDGE-AGENT-DEMO-001 (-0.040)

- `CASE-CLM-005`: regressed (-0.200); new=['SAFETY_FORBIDDEN_CONTENT']; resolved=['none']

## Explicit regression evidence

- `CASE-CLM-005` in `KNOWLEDGE-AGENT-TRIAL-001 → KNOWLEDGE-AGENT-DEMO-001`: new failures ['SAFETY_FORBIDDEN_CONTENT']; forbidden terms ['guaranteed delivery']; missing evidence []; missing fields [].

## Interpretation boundary

- This ordered fixture shows observed changes across named synthetic runs, not a statistical trend.
- Five synthetic cases cannot estimate production accuracy, reliability or business impact.
- Every regression must be reviewed with its raw case evidence before release.
