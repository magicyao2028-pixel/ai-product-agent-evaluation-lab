# Changelog

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
