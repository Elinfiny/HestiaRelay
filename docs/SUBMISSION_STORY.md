# HestiaRelay — submission story

Prepared from the validated implementation on 2026-09-13. Repository text only;
Devpost Project Details fields have not been edited. The public video URL must
be verified before the final submission package is complete.

## Project name

HestiaRelay

## Tagline

A household plan that remembers the context and respects your decisions.

## Inspiration

Household plans rarely arrive in one complete conversation. First comes the
dinner invitation. Later, the budget changes or someone remembers a guest's
allergy. By Friday, the useful question is not how to start planning again:
it is what is already remembered, what changed, and what still needs attention.

HestiaRelay explores that continuity through an Alexa+ experience simulation.
The idea is to preserve the household's evolving plan together with the exact
decisions it has made.

## What it does

Start with: “We're having six people over Friday evening, budget $120.”
In a separate session, add: “Remember Ana is allergic to nuts.”
Then return and ask: “Are we ready for Friday?”

HestiaRelay recovers the same goal, budget, people, preferences, preparation
tasks, planner provenance and consent history. Each new session sends only its
new message. SQLite persistence carries the thread across sessions and actual
server restarts.

The interface makes remembered context and unfinished work visible. Planning
advice identifies whether it came from the deterministic planner or Bedrock.
Sensitive proposals stop at an exact-proposal consent gate. Approval applies
to the saved details and current context; it does not authorize a changed
proposal. Rejection is recorded alongside the plan.

This prototype records consent but executes no purchase, payment, message or
external-account change. Allergy information is a planning constraint, not
food-safety verification.

## How we built it

The guided English browser simulation and a real Streamable HTTP MCP server
share the same Python household service and domain engine. The server exposes
bounded tools rather than arbitrary execution. Real SDK and MCP Inspector
clients have negotiated protocol 2025-11-25 and retrieved persisted state.

The optional Amazon Bedrock Runtime adapter calls `converse` through boto3.
One controlled Nova Micro proof ran in temporary AWS CodeBuild on September 12,
2026; its source, usage and reviewed output are preserved. The demonstration
video uses the deterministic planner and makes no live AWS call. The service
also works without AWS credentials.

The public MIT repository includes setup instructions, a non-root container,
an optional authenticated single-household judge mode, backup/restore tooling,
tests and four GitHub Actions jobs.

## Challenges and accomplishments

The central challenge was keeping state and consent coherent across separate
sessions, changed context and restarts. The demonstration follows the real
application through all three sessions, an exact approval, a process restart,
a changed constraint and a rejection. A real MCP client then reads the same
running household.

Validation includes 150 passing tests with 98.11% application coverage,
desktop/mobile Chromium checks, actual container recreation, authenticated TLS
and recovery checks. The release audit preserves dependency inventories,
upstream notices, raw findings and expiring applicability decisions; it is a
scoped prototype assessment, not a vulnerability-free deployment claim.

## What we learned

Useful continuity requires preserving decisions and their context as carefully
as the original goal. Explicit planner provenance also matters: deterministic
fallback and historical cloud evidence must remain distinguishable from a live
model response. The recorded friction log separates actual provider experience
from tooling and test-environment limitations.

## What's next

Test whether households can resume plans with less repetition and clearer
understanding of unfinished work. That benefit is currently a hypothesis;
real-user time savings have not been measured. Further work would address
broader language interaction, accessibility validation and isolated households
before any public multi-user deployment.

The current product is a guided text simulation with real MCP integration.
Live Alexa+, AgentCore and Strands are not demonstrated. External execution
would require a separately designed and validated consent-bound adapter.

## Submission references

- Primary track: **Alexa+**. Mini-challenge targets: **AWS Builder**, **Open Source**.
- Built with: Python, MCP Python SDK, Streamable HTTP, SQLite, Pydantic,
  Starlette, Uvicorn, HTML/CSS/JavaScript, Amazon Bedrock Runtime, boto3,
  AWS CodeBuild, CloudFormation, IAM, CloudWatch, Docker, GitHub Actions,
  pytest, Ruff, Playwright and FFmpeg. AWS infrastructure was temporary.
- Public source: [Elinfiny/HestiaRelay](https://github.com/Elinfiny/HestiaRelay).
- GitHub contributor: **Elinfiny**; [implementation PR #3](https://github.com/Elinfiny/HestiaRelay/pull/3)
  and [release PR #15](https://github.com/Elinfiny/HestiaRelay/pull/15).
- Contribution: created the public continuity service and simulation, shared
  MCP runtime, persistent state and exact consent ledger; added reproducible
  tests and evidence so others can inspect and extend the prototype.
- [Product feedback](PRODUCT_FEEDBACK.md), [friction log](FRICTION_LOG.md),
  [judge evidence map](JUDGE_EVIDENCE_MAP.md), [release receipt](evidence/release-20260913.json),
  [historical AWS proof](evidence/bedrock-20260912.json).
