# HestiaRelay Architecture

## Product promise

HestiaRelay is a persistent household continuity agent for Alexa+. It carries a household goal across sessions, preserves relevant constraints, coordinates low-risk planning, and stops at consent gates before sensitive actions.

## Trust boundaries

The browser JSON API and MCP tools share `HouseholdService` and
`HouseholdEngine`. All mutations enter a nested SQLite `BEGIN IMMEDIATE`
transaction, so state, planner provenance and transcript commit together.
Bedrock text is advisory output only; it cannot invoke a tool or authorize a
proposal. No external side-effect adapter is present.


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

## Phase 1 additions

`SessionRecord` preserves a unique session ID, sequence and recovered goal ID.
`TurnRecord` stores only the new user message, response, goal ID and that turn's
planner result. A repeated request ID with the same input is idempotent;
conflicting reuse fails. New sessions never reset household state.

Plans and preferences survive process recreation. Existing bootstrap SQLite
JSON loads with defaults for the additive history fields. Planning is not task
completion; the UI never marks food safety or purchases as complete.

Approval and rejection are final for one action ID. Context hashes bind new
proposals to the goal and preferences at proposal time. Approval after a context
change fails; rejection is still allowed. Legacy proposals without a context
hash cannot be approved and should be rejected and replaced.

The simulator serves packaged static assets using the real MCP application's
custom routes. `LocalBoundary` protects **all** HTTP routes with localhost Host
checks and same-origin checks. It also sets CSP, no-store and nosniff headers.
The entrypoint runs that wrapped application through Uvicorn on loopback.
Only fictional single-household development data is in scope. No public hosting
claim or multi-tenant authorization is implied.

Bedrock failures (including credentials, access errors and malformed responses)
produce `deterministic` provenance with a redacted `aws_unavailable` reason.
Success records `amazon-bedrock`, model ID and timestamp. Mocked-client tests
prove adapter behavior; they do not prove AWS account access. API timeouts and
zero configured SDK retries bound ordinary service errors. Credential-provider
resolution can add latency and requires a separate live-account check.

## Temporary managed Bedrock proof

The cloud proof runner executes the existing BedrockPlanner and aws_probe from
an immutable public GitHub commit in a dedicated CodeBuild service role. Its
source/request/role/approval guards are operational gates; they do not replace
the household domain's exact-proposal consent. Creating the three-resource
CloudFormation stack never starts a build. CI and ordinary simulator runs do
not invoke AWS. See `CLOUD_PROOF_PROPOSAL.md` for scope, cost assumptions and
evidence/cleanup acceptance. This package is not a public application deployment.
