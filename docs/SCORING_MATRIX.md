# Judging criteria and current evidence

Reviewed against the [official rules](https://amazonappdev2026.devpost.com/rules)
on September 13, 2026. These are our assessments of the work, not predicted scores.

| Criterion | What HestiaRelay demonstrates | Next improvement |
| --- | --- | --- |
| Technical Implementation | Shared browser/MCP service, protocol 2025-11-25 over Streamable HTTP, persistent SQLite, exact consent and real restart tests | Keep reproduction simple and verify the final source with current CI |
| Design | Three guided sessions, remembered context, visible planner source, decisions and recovery; desktop/mobile QA | Natural narration and concise explanations; screen-reader and real-user testing remain unperformed |
| Potential Impact | One recognizable dinner plan carried across interruptions and changing requirements | Measure whether people can resume the plan and identify unfinished work with less repetition |
| Quality of Idea | Goals, constraints, tasks and consent stay together; changed context cannot inherit approval | Demonstrate this relationship clearly, without adding unproved services |

The strongest present case is **Alexa+ continuity and a reusable open-source
pattern**. The AWS adapter is real, but its one historical Bedrock call is a
limited mini-challenge demonstration. A multi-service AWS architecture is not
implemented. AgentCore, Strands and public cloud memory are possible future
work, not mandatory completion gates for this simulation.

## Primary-track evidence

- [x] The public video shows the working simulation and a real MCP client call.
- [x] Actual SDK/TCP and Inspector 2.6.0 checks negotiate protocol 2025-11-25.
- [x] Runtime source imports and calls the MCP SDK.
- [x] Separate sessions recover the same goal and later constraints.
- [x] Exact approval/rejection, changed context and restart are demonstrated.
- [x] The demo clearly identifies the Alexa+ simulation and deterministic planner.

## Mini-challenge evidence

| Target | Existing contribution | Limit |
| --- | --- | --- |
| Open Source | Public MIT repository created September 12, 2026; [implementation PR #3](https://github.com/Elinfiny/HestiaRelay/pull/3), tests, shared MCP/UI design and run instructions; username Elinfiny | Final Devpost fields are not submitted |
| AWS Builder | Bedrock adapter and one actual Nova Micro Converse call on September 12, 2026, with temporary CodeBuild execution and preserved usage/output | Historical proof; the public video contains no live AWS call; requested promotional award remains unconfirmed |

The [product feedback](PRODUCT_FEEDBACK.md) describes the tools actually used.
The [friction log](FRICTION_LOG.md) retains reproducible observations, including
which belong to Amazon services and which belong to development tooling.
No bonus or award is assumed.

## Final release and submission gates

Use the [requirements audit](COMPETITION_AUDIT.md) for mandatory items and
remaining unknowns, and the [judge evidence map](JUDGE_EVIDENCE_MAP.md) to find
the relevant demonstration. Personal eligibility, exact final media selection,
current-source security validation and the submission receipt remain distinct.
