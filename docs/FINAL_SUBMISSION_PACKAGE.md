# Final submission package

Prepared English copy for the Amazon Developer Hackathon 2026. This document is
the source for the final form; it is not proof that the form was submitted.

## Core fields

**Project name:** HestiaRelay

**Tagline:** Pick up where life left off. Your household plan comes with you.

**Primary track:** Alexa+

**Mini-challenges:** AWS Builder; Open Source

**Public repository:** https://github.com/Elinfiny/HestiaRelay

**Demo video:** https://www.youtube.com/watch?v=NC2oy4x9Xdw

**GitHub username:** Elinfiny

**Built with:** Python, MCP Python SDK, SQLite, Pydantic, Starlette, Uvicorn,
HTML, CSS, JavaScript, Amazon Bedrock Runtime, Amazon Nova Micro, boto3,
AWS CodeBuild, AWS CloudFormation, AWS IAM, Amazon CloudWatch Logs, Docker,
GitHub Actions, Playwright and pytest.

Use the polished project story from [SUBMISSION_STORY.md](SUBMISSION_STORY.md).
It covers inspiration, behavior, implementation, the hardest problem, working
evidence and next steps without claiming a live Alexa+ integration or an
external action.

## Short description

HestiaRelay is a persistent household continuity agent demonstrated through a
guided Alexa+ simulation and a real MCP server. Across three separate sessions,
it remembers a dinner plan, budget, guests, dietary constraint, tasks, planner
source and consent state. Sensitive proposals require an exact approval or
rejection, and changed context invalidates earlier approval. The reproducible
demo works without AWS credentials; one separate historical Bedrock Converse
call proves the optional adapter path.

## Testing instructions

1. Follow the README Quick start with Python 3.12.
2. Open the local URL printed by the server.
3. Select Session 1, Session 2 and Session 3 in order. Each request contains
   only its new message.
4. Confirm that the six guests, Friday timing, $120 budget and Ana's nut-allergy
   constraint remain visible in Session 3.
5. Review the exact proposal, approve it, restart with the same database, then
   change the context and reject the replacement proposal.
6. Follow the README MCP smoke command to read the same household state.

Default mode is deterministic and performs no external action. Use fictional
data. Approval only records consent: it does not purchase, pay, message or
change an account. Allergy information is a planning constraint, not a food-
safety guarantee.

## Alexa+ track explanation

The entry uses the rules' simulation route. The browser experience demonstrates
how an Alexa+ household assistant could continue a goal across conversations,
while the working MCP service exposes the same bounded household capabilities.
It is not connected to live Alexa+. The key product idea is continuity with
control: remembered context changes the plan, but never silently expands an
earlier approval.

## AWS Builder explanation

HestiaRelay includes a boto3 Amazon Bedrock Runtime adapter using the Converse
API and Amazon Nova Micro. Development started with deterministic and mocked
paths, then one approved live call ran in an isolated temporary AWS CodeBuild
project on September 12, 2026. CloudFormation defined the project, dedicated IAM
role and CloudWatch Logs; the response, token usage, source SHA and verified
cleanup are preserved in
[the evidence receipt](evidence/bedrock-20260912.json). The call used 222 input
tokens and 230 output tokens. No AWS call occurs in the video or default judge
path, and the historical proof is not presented as current hosting.

## Open Source contribution

HestiaRelay is a public MIT-licensed implementation, not a private code import.
The contribution is a shared service for browser and MCP clients, persistent
household context, an exact-consent ledger, restart/backup recovery, a non-root
container and reproducible tests. Representative contribution links:

- https://github.com/Elinfiny/HestiaRelay/pull/3
- https://github.com/Elinfiny/HestiaRelay/pull/15

The same public repository contains setup instructions, architecture, threat
model, friction log and evidence boundaries so others can inspect or extend the
pattern.

## Product feedback

Use [PRODUCT_FEEDBACK.md](PRODUCT_FEEDBACK.md) for the required per-tool
feedback. The strongest concise points are:

- Bedrock Converse offered a clean typed boundary for swapping deterministic,
  mocked and real planning while preserving provider provenance.
- Small proofs still need explicit source/role binding, redacted logs and
  cleanup; provisioning time should be shown separately from inference latency.
- MCP Streamable HTTP made browser and agent clients share one real domain
  service, but remote authorization remains an application responsibility.
- GitHub Actions made the demo reproducible across tests, browser, container and
  cloud-proof packaging, while provider queue incidents required careful state
  reconciliation rather than duplicate retries.
- AI assistance helped keep implementation and evidence aligned, but generated
  wording still needed human editorial review and could never grant permission
  for sensitive actions.

## Friction and feature requests

Only submit observations supported by [FRICTION_LOG.md](FRICTION_LOG.md). Useful
examples include clearer connector capability discovery, better differentiation
between queued and running GitHub Actions, more reliable public-video validation
without bot ambiguity, and smoother caption-file transfer. Do not convert these
incidents into claims of an AWS or YouTube outage unless the evidence says so.

## Evidence for the four judging criteria

| Criterion | Best evidence |
| --- | --- |
| Technical Implementation | Three-session/restart tests, real MCP clients, exact consent invalidation, 150-test baseline, browser/container recovery evidence |
| Design | One clear dinner story, visible planner provenance, exact proposal scope, readable desktop and 390px layouts |
| Potential Impact | Less repeated household context and fewer missed constraints are concrete hypotheses for user testing, not measured adoption |
| Quality of Idea | Persistent context and revocable consent solve a gap that grows across conversations rather than within one prompt |

See [JUDGE_EVIDENCE_MAP.md](JUDGE_EVIDENCE_MAP.md) for exact links and limits.

## Disclosure

Development used AI assistance through ChatGPT/Codex. The public repository
preserves implementation, review history and reproducible checks. Synthetic
English narration uses a documented stock voice; it is not Alexa, a cloned
voice or the entrant's recorded voice.

## Private entrant checklist

Complete these in the authenticated Devpost session; never place personal data
in this repository:

- eligibility, age and residence;
- conflicts, employer permission and team/representation authority;
- originality and rights to code, visuals, narration and submitted material;
- category selections and required platform terms;
- correct entrant/contact information.

## Final readback checklist

- Refresh the official rules and the expiring release evidence.
- Verify repository, license, Quick start and video anonymously.
- Confirm the narrated video is Public, 1:28, English and still plays through.
- Compare every pasted field with this package; remove internal process wording.
- Preview before submission.
- Submit once, then read back the received project, categories, URLs and status.
- Record only the receipt identifiers needed for project continuity; keep
  personal details private.
