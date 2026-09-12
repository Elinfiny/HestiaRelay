# HestiaRelay work state

Canonical main baseline for Phase 3:
`f48c902e5035b6fa33be0e36334afd414f1fbe7e` (CI 34718967183 SUCCESS).
Live-executed source: `56dd5ad6375a668645eec7d8018430479f308267`.
Resolve GitHub's `main` ref for the latest repository head. Issue #10 records
this delivery's final merge SHA and post-merge CI after confirmation; a commit
cannot contain its own SHA. Phase 1 delivery:
`c5739b76d54dc4dda140e2b373d5822a91413d29` (CI 34710656387 SUCCESS).

## Current phase

**Phase 1 and Phase 2 complete. Phase 3 implementation and execution gates PASS; final delivery CI pending.**
PR #9 preserves the live proof and cleanup evidence; Issue #4 is closed.
Phase 3 delivers the reproducible container and clean-room judge package
in Issue #10. No extra AWS spending or public deployment is authorized.

Phase 2 delivery is now confirmed: PR #9 merged at
`f48c902e5035b6fa33be0e36334afd414f1fbe7e`; post-merge CI 34718967183 SUCCESS,
all three jobs. Issue #4 is closed after readback. This is the canonical main
baseline for the Phase 3 container package.

## Completed gates

- Real SDK/TCP MCP negotiated 2025-11-25 on separate connections, including
  actual process-restart persistence. Canonical three-session continuity and
  exact-proposal approve/reject/context invalidation tests pass.
- Desktop 1440x1000 and mobile 390x844 Chromium regressions pass. Phase 1
  screenshots were manually inspected; no new manual interaction, physical
  device or screen-reader certification is claimed for this evidence package.
- Local post-proof Ruff PASS; 83 tests PASS; 98.86% application coverage.
  The same 83 tests passed inside the actual AWS CodeBuild job (Python 3.12.13).
- AWS account identity, authorized Nova Micro and enabled applicable existing
  credits verified read-only. Requested hackathon promotional award unverified.
- Owner explicitly approved the exact one-build/one-call proposal and cleanup.
  Schema, custom cfn-guard, change-set and deployed IAM scope checks passed.
- One build SUCCEEDED; one real Converse call returned LIVE_CALL_PASS:
  222 input tokens, 230 output tokens, 1,114.44 ms, completed consistent usage.
  Request/source/role bindings and reviewed fictional response digests match.
- No completed external household action or allergy safety certification in the
  output. The response is advisory; its tendency to ask confirmation for some
  low-risk reviews remains a planner UX limitation, not a runtime failure.
- Original report and reviewed log exported to GitHub and reread exactly before
  cleanup. A final log-cursor read returned zero additional events.
- Stack DELETE_COMPLETE; project absent; dedicated role absent; log group absent,
  verified 2026-09-12T20:59:47.983512+00:00. No unrelated resource changed.
- List-price calculation: Bedrock USD 0.000039970; six rounded build minutes
  USD 0.030; combined USD 0.030039970 before small logs/taxes. Final billing and
  credit application remain unconfirmed. Approved operational budget: USD 0.10.
- [Machine evidence](evidence/bedrock-20260912.json) preserves original probe
  flags; account/cost/output/cleanup checks are recorded in separate fields.
- [Reviewed original log](evidence/bedrock-20260912.log.txt) preserves the live
  result and AWS-side test evidence without account identifiers or credentials.

## Delivery and remaining gates

PR and post-merge CI must pass validate, browser, cloud-proof-package and
container-judge jobs; Issue #10 records final run identities and closing readback. Public repository,
MIT license, domain boundaries and deterministic fallback remain intact.
No second build/call is authorized by the consumed proof proposal.

No external access blocker remains for the completed proof. Public deployment
requires prepared TLS, Host/Origin, household authorization, persistence and
operating-cost gates. The current singleton localhost service must not be
exposed as a multi-user household application.

## Competition readiness

Demonstrated: guided Alexa+ simulation, real MCP interoperability, persistent
cross-session state, exact consent and one real Bedrock runtime call.
Not demonstrated: live Alexa+, AgentCore, Strands, judge-accessible hosting or
measured real-user impact. Final video/submission audit remain open. Devpost
story/video fields are untouched.

## Phase 3 evidence

- CI 34719571606: all four jobs PASS at feature head
  `2c98e07b008107d95db015ef5b0bb1b16cbb0a36`. Actual PR merge checkout:
  `f8e77d67a2ae8ef8a6dcd4cd5a7de18ee0981744` (parents verified).
- Actual image: `sha256:ec20243738e71ec0033c8c8b5ad0d61c689be53ad1ae48352f09f55fde463d80`.
- Canonical three separate MCP sessions; two container recreations with the
  same volume; goal, budget, preferences and exact approved/rejected consent
  recovered. Non-root, read-only root and hostile Host/Origin checks PASS.
- Inspector 2.6.0 initialization, strict tool listing and continuity-brief call
  PASS; observed SDK and Inspector protocol `2025-11-25`.
- Container-backed desktop 1440x1000/mobile 390x844: no console errors, failed
  requests or horizontal overflow. Both Session 3 screenshots visually reviewed.
- Artifact 10305424084 downloaded and SHA-256/ZIP CRC/path/browser manifest
  verified. Durable result: [container evidence](evidence/container-20260912.json).
- No source application behavior changed and no additional AWS call occurred.
  The initial CI base-tag inspection defect was corrected before the passing run.

## Next executable package

Restricted judge access and release hardening: implement the authenticated
single-fictional-household browser path, exact deployment Host/Origin and CSRF
boundaries, and backup/restore checks described in
[JUDGE_DEPLOYMENT_DESIGN.md](JUDGE_DEPLOYMENT_DESIGN.md). Preserve loopback defaults
and real MCP; public MCP requires its own compatible authorization proof.
The design and initial boundary audit are complete; implementation can proceed
offline. A public endpoint still requires a concrete account/domain/cost proposal.
