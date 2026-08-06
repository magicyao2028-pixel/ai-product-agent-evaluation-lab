# Product Requirements Document

## 1. Document control

| Field | Value |
| --- | --- |
| Product | AI Product & Agent Evaluation Lab |
| Version | 0.2 |
| Status | Product-validation MVP |
| Primary user | AI product owner or operations lead in a small or medium-sized enterprise |
| Public data policy | Synthetic evaluation cases and candidate outputs only |

## 2. Problem statement

An AI workflow can look useful in a demonstration while failing repeatable business rules. A product owner needs evidence that expected statuses, supporting information, response contracts and safety boundaries still hold after each change.

## 3. Product hypothesis

If a team converts acceptance expectations into a small reviewed suite and obtains an explainable report before release, it can identify obvious regressions earlier and discuss risk using concrete evidence rather than impressions.

This hypothesis has not been validated with real teams. v0.2 tests deterministic product behavior and iteration comparison only.

## 4. v0.2 scope

### In scope

1. Validate one suite, one named baseline and one candidate-run JSON file.
2. Require complete, unique case coverage.
3. Score task status, evidence coverage, schema completeness and safety.
4. Explain missing terms, missing fields and forbidden claims.
5. Apply an aggregate threshold and safety-critical gate.
6. Export deterministic JSON and Markdown reports.
7. Run without a paid API or external data transfer.
8. Classify case-level improvements, regressions and unchanged behavior.
9. Keep safety-critical regressions visible even when the aggregate score rises.

### Out of scope

- LLM-as-judge or semantic correctness claims;
- model execution, provider credentials or prompt optimization;
- latency, token cost or load testing;
- database, accounts, roles or hosted API;
- production accuracy or business-performance claims.

## 5. Functional requirements

| ID | Requirement | Priority | Acceptance criterion |
| --- | --- | --- | --- |
| FR-01 | Validate coverage | Must | Missing, unknown or duplicate case IDs fail clearly. |
| FR-02 | Score dimensions | Must | Every case receives four visible scores and one weighted total. |
| FR-03 | Explain failures | Must | Missing evidence, schema fields and forbidden terms are named. |
| FR-04 | Protect safety gate | Must | A failed safety-critical case blocks release. |
| FR-05 | Export reports | Should | JSON and Markdown reports are deterministic and reproducible. |
| FR-06 | Preserve boundaries | Must | Reports state that deterministic fixtures are not production accuracy. |
| FR-07 | Compare baseline | Must | Every case shows baseline, candidate, delta and changed dimensions. |
| FR-08 | Preserve regression | Must | Aggregate improvement cannot convert a failed candidate gate into a pass. |

## 6. Release gate

The sample gate requires an aggregate score of at least 0.900 and all safety-critical cases to pass. Thresholds require domain-owner review before any private pilot.
