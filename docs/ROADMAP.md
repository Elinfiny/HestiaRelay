# HestiaRelay Roadmap

The roadmap is gate-driven. A later phase does not replace a validated earlier phase without evidence.

## Phase 0 — Repository foundation

- [x] Public repository created during hackathon window.
- [x] MIT license.
- [x] Operating contract.
- [x] MCP Streamable HTTP server foundation.
- [x] Persistent local continuity state.
- [x] Risk and consent model.
- [x] Bedrock runtime adapter.
- [x] Unit tests and CI.
- [x] Threat model, scoring matrix, and friction log.

**Gate:** CI green and bootstrap diff reviewed before merge.

## Phase 1 — Alexa+ simulation MVP — COMPLETE

Build a polished web simulation that demonstrates the intended Alexa+ interaction model:

- voice-style conversation transcript;
- household goal card;
- persistent context timeline;
- checklist and budget state;
- visible planner provenance;
- consent card for sensitive proposals;
- session restart / continuity demonstration.

**Gate PASS:** canonical three-session demo, real MCP process-restart smoke,
Chromium desktop/mobile and manual screenshot review. PR #3 merged; main CI
34710656387 SUCCESS.

## Phase 2 — Live AWS Builder integration — PREPARATION STARTED (#4)

- Validate AWS promotional credits/account path.
- Enable one appropriate Amazon Bedrock model.
- Prove live `converse` calls through the runtime adapter.
- Record cost/latency evidence.
- Integrate AgentCore Memory if it materially improves cross-session continuity.
- Evaluate Strands for agent orchestration and adopt only if it improves the architecture.

**Gate:** end-to-end AWS path passes deterministic tests plus one controlled live integration suite.

## Phase 3 — MCP compliance and deployment

- Verify MCP Inspector interoperability.
- Confirm negotiated protocol meets hackathon minimum 2025-11-25.
- Validate Streamable HTTP lifecycle and session behavior.
- Add deployment-specific Host/Origin allowlists and TLS plan.
- Deploy judge-accessible instance or provide zero-friction local testing path.

**Gate:** clean-room MCP client can connect and exercise all submission-critical tools.

## Phase 4 — Product hardening

- failure/retry behavior;
- consent regression tests;
- accessibility;
- responsive visual simulator;
- observability and redaction;
- fresh-install test;
- dependency/security review;
- repository secret scan.

**Gate:** independent audit has no P0/P1 findings.

## Phase 5 — Submission package

- Freeze final functionality.
- Generate final Devpost story from implemented behavior only.
- Produce architecture image and screenshots.
- Record one final demo under three minutes.
- Verify repository, setup, AWS evidence, MCP evidence, friction logs, and open-source contribution URL.
- Run final signed-out/judge-path audit.

**Gate:** submission checklist 100% PASS before Devpost submit.
