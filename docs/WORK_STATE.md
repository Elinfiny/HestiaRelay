# HestiaRelay work state

Canonical main at this checkpoint: `30ed49b10afddda76994724dfb4ca6942338f5cb`.
This is the last verified main, not a self-referential hash of this document.

Phase: 1 — Issue #2, implementation candidate on `feature/alexa-simulator-v1`.

Completed: mandatory read-only audit; bootstrap main CI PASS; responsive simulator,
shared MCP/API service, persisted session/turn/provenance records, explicit AWS
fallback, transactional writes, exact consent and context-change checks.
46 tests PASS; 98.95% application coverage; Ruff PASS. Real MCP/TCP smoke
negotiated 2025-11-25 across three sessions and recovered state after restart.
CI run 34710345180 passed validate and browser jobs at candidate 09c92c6.
Chromium 1440×1000 and 390×844 passed with zero console errors, no overflow,
keyboard focus, approve/reject, reload and fresh-context persistence. Initial
and session-3 screenshots were manually inspected: coherent layout and readable
controls, context and consent; no clipping or overlap identified.

In progress: final evidence-manifest/documentation update and exact-head CI;
final secret/scope/claims audit before merge.
No merge or Issue #2 closure yet. Main remains the recoverable baseline.

Phase 1 blockers: none. Managed browser loopback access is unavailable; actual
browser interactions ran in CI-owned Chromium, followed by manual screenshot
inspection. This does not claim a manual interactive cloud-browser session.
AWS credentials/account/model are unverified and do not block deterministic work.

Competition readiness: Phase 1 candidate only. No live Alexa+, Bedrock, AgentCore
or Strands evidence. Devpost story and video fields untouched.

Next executable package: complete PR gates, merge, verify main CI and close #2;
then prepare the bounded live AWS validation package before requesting account access.
