# HestiaRelay work state

Canonical validated Phase 1 main SHA: `c5739b76d54dc4dda140e2b373d5822a91413d29`.
This is the last verified implementation baseline at this checkpoint; the current
GitHub `main` ref is authoritative for later documentation/preparation commits.

Current phase: **Phase 1 COMPLETE; Phase 2 AWS proof preparation in progress (#4).**

## Completed gates

- PR #3 merged; Issue #2 closed after main CI confirmation.
- Main CI run 34710656387: SUCCESS on c5739b7 (validation + Chromium).
- Phase 1: Ruff, 46 tests, 98.95% coverage, canonical three-session continuity,
  exact approval/rejection and stale-context protection PASS.
- Real SDK/TCP MCP negotiated 2025-11-25 on three connections, plus explicit
  baseline request; actual server restart persistence PASS.
- Chromium 1440×1000 and 390×844: zero console errors/overflow; canonical clicks,
  consent, reload, fresh browser context and keyboard focus PASS.
- Initial/session-3 screenshots manually reviewed. No interactive managed-browser
  run claimed; that browser could not reach executor loopback.
- Final browser archive 10303640584: SHA-256
  `6af74928430b7dd5abba8314d1e292d29bf203579e6e5ec180fba178cd90cf2c`,
  CRC/safe paths and 7/7 manifest rows PASS.
- Secret-pattern scan, changed-file scope and misleading-claim diff review PASS.

## Phase 2 preparation

Branch: `feature/bedrock-evidence-prep`. Added opt-in one-call Bedrock evidence
probe, default offline path, explicit mock labeling, redacted latency/usage
reporting and AWS runbook. Local validation: Ruff PASS; 55 tests PASS; 98.87%
application coverage. Offline probe: zero Converse calls, no live AWS proof,
credits unverified and cost unknown. Preparation PR/CI is the next gate.

## Open blockers and readiness

Live AWS requires secure account access, verified model/region and credit/pricing
status, and a bounded spending authorization. No AWS credentials, paid call,
IAM grant, model subscription, cloud resource or live workflow was created.
Competition readiness: functioning simulation and MCP evidence; live AWS,
public judge deployment, user impact validation and final submission remain open.
No live Alexa+, AgentCore or Strands integration. Devpost story/video untouched.

Next executable package: merge the tested offline AWS preparation through PR/CI;
verify the owner's AWS account read-only; select the exact model and one-call
cost boundary; run the live probe only after the account/financial gate passes.
