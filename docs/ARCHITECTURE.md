# HestiaRelay Architecture

## Product promise

HestiaRelay is a persistent household continuity agent for Alexa+. It carries a household goal across sessions, preserves relevant constraints, coordinates low-risk planning, and stops at consent gates before sensitive actions.

## Trust boundaries

```text
User / Alexa+ simulation
        │
        ▼
MCP Streamable HTTP endpoint
        │
        ▼
HestiaRelay orchestration core
   ┌────────┬───────────┬──────────────┐
   ▼        ▼           ▼              ▼
state    risk gate   plan adapter   proposal ledger
   │                    │              │
   │                    ▼              │
   │              Amazon Bedrock       │
   │                    │              │
   └────────────────────┴──────────────┘
                        │
                        ▼
             future AgentCore / Strands
```

## Current validated foundation

- Public MIT-licensed repository.
- Python package with MCP SDK runtime dependency.
- MCP server built with `MCPServer` and Streamable HTTP.
- Persistent local SQLite development state.
- Explicit safe/review/protected action classification.
- Exact-proposal approval or rejection.
- Amazon Bedrock `converse` adapter behind environment configuration.
- Deterministic planning fallback when Bedrock is not configured.
- CI, unit tests, threat model, scoring matrix, roadmap, and friction log.

## MCP surface

The server exposes bounded household capabilities instead of arbitrary execution:

1. `start_household_goal`
2. `remember_household_preference`
3. `get_continuity_brief`
4. `generate_household_plan`
5. `propose_household_action`
6. `decide_sensitive_action`

The service is intended to run over Streamable HTTP and meet or exceed the hackathon MCP baseline 2025-11-25.

## Continuity model

During development, SQLite proves cross-session state continuity without requiring cloud credentials. The cloud milestone will introduce AgentCore-backed memory while keeping the same typed domain boundary so local and cloud modes can be compared and tested.

## AWS integration strategy

Amazon Bedrock is a real runtime integration, not a README-only claim: `BedrockPlanner` calls the Bedrock Runtime `converse` API when `HESTIA_BEDROCK_MODEL_ID` is configured.

The next AWS milestone will evaluate AgentCore Memory and Strands against three gates:

- measurable improvement to continuity or orchestration;
- clean failure behavior without credentials or service availability;
- reproducible tests and demo evidence.

## Consent model

A sensitive action is first represented as an immutable-scope proposal. Approval changes only that proposal's status. Approval does not grant general permission to future actions.

The bootstrap deliberately does not perform real purchases or external-account changes. Later integrations must preserve this proposal/consent boundary.

## Demo spine

The canonical demo remains:

1. “We’re having six people over Friday evening, budget $120.”
2. In a later session: “Remember Ana is allergic to nuts.”
3. In a later session: “Are we ready for Friday?”
4. The agent reconstructs context and plan.
5. A proposed purchase is visibly consent-gated instead of silently executed.

This demo directly proves continuity, orchestration, memory, and safety rather than a single-turn chat interaction.
