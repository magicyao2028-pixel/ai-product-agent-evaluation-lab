# Security and Governance

- Public fixtures are synthetic and contain no customer, employee or company-confidential data.
- The evaluator makes no network request and requires no API key.
- Candidate results are treated as untrusted input; malformed shapes and coverage mismatches fail clearly.
- The v0.1 CLI does not provide access control, encryption, retention or tamper-evident logs.
- Forbidden-phrase checks are narrow safeguards, not a full moderation or policy engine.
- A production system would require authenticated projects, permissions, encrypted storage, audit events and independent security review.
- Reviewer IDs and annotations in v0.5 are synthetic fixtures. They confer no identity assurance, approval authority or production adoption.
- Human annotations never overwrite automated failure evidence; safety-gate changes require a reviewed rubric or candidate change and a new evaluation snapshot.
