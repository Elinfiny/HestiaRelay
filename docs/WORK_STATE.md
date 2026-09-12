# HestiaRelay work state

Canonical main at this checkpoint: `30ed49b10afddda76994724dfb4ca6942338f5cb`.
This is the last verified main, not a self-referential hash of this document.

Phase: 1 — Issue #2, implementation candidate on `feature/alexa-simulator-v1`.

Completed: mandatory read-only audit; bootstrap main CI PASS; responsive simulator,
shared MCP/API service, persisted session/turn/provenance records, explicit AWS
fallback, transactional writes, exact consent and context-change checks.
45 behavior/API tests passed with 98.94% application coverage before the new
real-network MCP smoke was added. Ruff passed. Final full-suite results pending.

In progress: real TCP MCP interoperability and process restart, GitHub Actions
browser suite, manual screenshot review, final secret/scope/claims diff audit.
No merge or Issue #2 closure yet. Main remains the recoverable baseline.

Blockers: managed cloud browser cannot reach executor loopback; CI-owned Chromium
is the prepared route for reproducible UI evidence and manual visual inspection.
AWS credentials/account/model are unverified and do not block deterministic work.

Competition readiness: Phase 1 candidate only. No live Alexa+, Bedrock, AgentCore
or Strands evidence. Devpost story and video fields untouched.

Next executable package: complete PR gates, merge, verify main CI and close #2;
then prepare the bounded live AWS validation package before requesting account access.
