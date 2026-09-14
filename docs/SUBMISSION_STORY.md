# HestiaRelay

Prepared submission copy. Devpost fields have not been changed.

## Tagline

Pick up where life left off. Your household plan comes with you.

## Inspiration

Planning dinner rarely happens in one sitting. You invite six people. Later,
someone mentions an allergy. By Friday, you want to know what is ready and what
still needs doing, without explaining the whole evening again.

That is the small, everyday problem behind HestiaRelay. A helpful assistant
should carry a plan forward as life adds details, while leaving the decisions
with the people who will live with them.

## What it does

The demo starts with a simple request: “We're having six people over Friday
evening, budget $120.” HestiaRelay saves the plan and creates a preparation list.

In a new session: “Remember Ana is allergic to nuts.” The detail joins the
existing plan. The guest count and budget do not need to be entered again.

In a third session: “Are we ready for Friday?” HestiaRelay brings back the plan,
the people, the constraint and the unfinished work. Its timeline shows how those
pieces arrived in different conversations. Restarting the server keeps them.

Decisions stay with the plan too. A sensitive proposal shows its exact details
before approval or rejection. If the household context changes, an earlier
approval cannot authorize the new proposal. In this prototype, approval records
consent only: no purchase, payment, message or account change is carried out.
Allergy information is a planning constraint, not a food-safety guarantee.

## How it works

The guided browser experience and a real Streamable HTTP MCP server use the
same Python service and SQLite database. A new session sends only its new
message; the service retrieves the saved context. The video finishes with a real
MCP client reading the same household shown in the browser.

The planner has two explicit sources. The demonstration uses deterministic
planning, so anyone can reproduce it without an AWS account. The optional
Amazon Bedrock adapter calls `converse` through boto3. One Nova Micro call was
tested in temporary AWS CodeBuild on September 12, 2026, with its response and
usage recorded. That historical cloud test is separate from the video.

This is an Alexa+ experience simulation, with working MCP integration. It is
not connected to live Alexa+. AgentCore and Strands are not integrated.

## The hardest part

Remembering a fact is only part of continuity. The harder question is what
that fact changes. A new dietary constraint can make an old proposal unsuitable;
an approval must not quietly carry over. HestiaRelay stores the proposal's
context and checks it when a decision is made.

The same care applies after a restart. The demo closes the actual server
process and starts another against the same database. The household and its
decisions return together. Tests also cover rejection, changed context, failed
planner calls and backup restoration.

## What is working

The public MIT project includes the simulator, MCP server, a non-root Docker
setup and instructions for trying the three-session story. Validation covers
150 tests with 98.11% application coverage, real MCP clients, desktop and mobile
Chromium, container recreation and authenticated recovery checks. Detailed
results and security limits are linked below.

The useful distinction is visible in the demo: you can return to the same plan
without surrendering control over what happens next.

## What comes next

The first audience is people who coordinate meals and small household events.
The next product test is straightforward: can someone return to a plan, spot
the unfinished work and understand what they approved without repeating the
earlier context? Time savings and fewer mistakes are hypotheses to test, not
results already measured.

The prototype currently supports guided English messages and one fictional
household. Broader conversation, screen-reader testing and household isolation
are the next steps before a public multi-user service. Any future shopping or
messaging integration would need its own consent-bound execution adapter.

## Submission references

- Primary track: **Alexa+**. Mini-challenges: **Open Source** and **AWS Builder**.
- [Watch the public narrated demonstration](https://www.youtube.com/watch?v=NC2oy4x9Xdw).
- [Public MIT source and run instructions](https://github.com/Elinfiny/HestiaRelay).
- GitHub username: **Elinfiny**. Contribution: [implementation PR #3](https://github.com/Elinfiny/HestiaRelay/pull/3),
  [release PR #15](https://github.com/Elinfiny/HestiaRelay/pull/15).
- Open Source contribution: built a shared household service for the browser
  and MCP, persistent context and an exact-consent ledger, with tests and run
  instructions so other developers can reproduce and extend the pattern.
- Built with: Python, MCP Python SDK, SQLite, Pydantic, Starlette, Uvicorn,
  HTML/CSS/JavaScript, Amazon Bedrock, boto3, Docker and GitHub Actions.
  The full development-tool feedback and temporary AWS services are listed in
  [product feedback](PRODUCT_FEEDBACK.md).
- Development used AI assistance through ChatGPT/Codex. The repository preserves
  the implementation, review history and reproducible checks; generated advice
  is never treated as permission to act.
- [Judge evidence map](JUDGE_EVIDENCE_MAP.md), [friction log](FRICTION_LOG.md),
  [release audit](RELEASE_AUDIT.md), [historical Bedrock proof](evidence/bedrock-20260912.json).
