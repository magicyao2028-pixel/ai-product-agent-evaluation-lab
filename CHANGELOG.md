# Changelog

## 0.9.0 - 2026-08-31

- Added review-history visibility summary with deterministic status/source counts.
- Preserved immutable automated evidence and zero release authority.

## 0.8.0 - 2026-08-29

- added a deterministic reviewer-decision export for blocked, disputed and review-blocked cases;
- preserved immutable automated evidence, no-decision-application and no-release-authority boundaries;
- added snapshot-consistency validation, trial evidence and regression coverage.

## 0.7.0 - 2026-08-26

- added a versioned append-only review-history fixture and validator;
- added a CLI path that preserves snapshot digests and review status without release authority;
- extended trial evidence and regression coverage while retaining synthetic/offline boundaries.

## 0.6.0 - 2026-08-23

- added a bounded review-queue export for failed, disputed and adjudication-required cases;
- added a versioned adjudication receipt that records requested decisions without reopening automated safety failures;
- added synthetic trial evidence and regression tests for queue priority, unknown cases and authority preservation.

## 0.5.0 - 2026-08-18

- added separate synthetic reviewer annotations with consensus and disagreement states;
- retained a canonical hash and the original failure events without mutation;
- prevented reviewer approval from overriding an automated safety failure;
- screened Argilla and Label Studio without forcing unnecessary platform scope into the offline default;
- added a deterministic trial-readiness report, evidence index and synthetic feedback regression.

## 0.4.0 - 2026-08-15

- added stable task, evidence, schema, safety and evaluation-contract failure codes;
- retained triggering status, missing terms, missing fields and forbidden terms as raw failure evidence;
- added ordered multi-run analysis with new, resolved and persistent failure lifecycles;
- added a three-run synthetic fixture and explicit regression evidence report;
- added a dedicated CLI and six regression tests while rejecting statistical and production-accuracy claims.

## 0.3.0 - 2026-08-11

- added a validated rubric schema for dimension weights, case thresholds, dimension floors and release gates;
- preserved deterministic defaults while allowing an explicit rubric file in both evaluation CLIs;
- added per-case weighted contributions and effective-rubric identity to every score;
- required comparison runs to evaluate baseline and candidate under one identical rubric;
- added seven focused rubric and threshold validation tests.

## 0.2.0 - 2026-08-06

- added a named synthetic baseline run;
- added per-case and per-dimension candidate comparison;
- added explicit improvement, regression and unchanged classifications;
- added deterministic JSON/Markdown comparison reports and a dedicated CLI;
- demonstrated that aggregate improvement cannot override a safety-critical regression;
- added four comparison regression tests and browser-visible comparison evidence.

## 0.1.0 - 2026-08-04

- added validated synthetic evaluation suite and candidate run;
- added task-status, evidence, schema and safety dimensions;
- added explainable safety-critical release gate;
- added deterministic JSON and Markdown reports;
- added CLI, tests, product documentation and static browser prototype;
- documented the ten-round maintenance path and honest evaluation boundaries.
