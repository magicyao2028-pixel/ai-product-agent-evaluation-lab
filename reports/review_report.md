# Human Review and Disagreement Report

- Batch: `SYN-REVIEW-BATCH-001`
- Source type: `synthetic`
- Evaluation snapshot: `sha256:a0e4e2f90e529b626b7c70b492c3d5f34a8e70245c47db33cf28bf35007ea184`
- Release status: **blocked_by_automated_gate**
- Disagreements: 1

| Case | Automated | Review state | Decisions | Effective decision |
| --- | --- | --- | --- | --- |
| CASE-CLM-005 | FAIL | disagreement | approve, block | blocked_by_automated_gate |
| CASE-RET-001 | PASS | consensus | approve | eligible_for_human_release_review |

## Authority boundary

- Annotations are separate review evidence and never overwrite automated observations or raw failure events.
- A reviewer approval cannot reopen a case blocked by the configured automated gate.
- Disagreement requires accountable adjudication; this public fixture grants no release authority.
