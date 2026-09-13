# Judge evidence map — review candidate

HestiaRelay preserves a household plan across separate conversations, including
what changed and exactly what the household approved. The intended benefit is
less repeated context and fewer coordination mistakes. Real-user time savings
have not been measured.

## Watch and reproduce

The `browser-qa` artifact in the Phase 4B CI run contains
`demo/hestiarelay-candidate.mp4`, English `captions.srt`, scene screenshots,
`demo-report.json`, the actual `mcp-evidence.json`, and SHA-256 hashes.
The video is a silent captioned **draft for owner visual review**. It records
real browser interactions with a real service and SQLite. Captions occupy a
separate video band; the script never injects responses or modifies the app DOM.

Run the repository CI or, with Python dependencies, Chromium and FFmpeg installed:

```bash
python scripts/record_demo.py
```

The scripted sequence shows the canonical three sessions, deterministic planner
provenance, an exact approval, a server-process restart with identical recovered
state, a new constraint and exact rejection, then an actual MCP client reading
the same running household. Only fictional data is used; no AWS call occurs.
Desktop/mobile and TLS/recovery QA remain separate mandatory CI checks.

## Evidence by criterion

| Criterion / target | Demonstrated evidence | Practical limit |
| --- | --- | --- |
| Technical Implementation | Shared service behind real Streamable HTTP MCP and UI; persistent SQLite; actual restart; exact consent; SDK and Inspector checks; coverage and CI | Single household/worker; no public hosted service or live Alexa+ connection |
| Design | Guided three-session flow, visible remembered context, planner source, readable consent and continuity timeline; desktop 1440px and mobile 390px QA | Guided English text; no voice or screen-reader certification |
| Potential Impact | A dinner plan retains six people, Friday, $120 and a later allergy constraint without repeating the goal | Intended household coordination benefit; no measured user savings or food-safety certification |
| Quality of Idea | Goals, preferences, tasks, provenance and scoped decisions persist together; changed context cannot inherit old approval | No shopping, payment, messaging or external-account executor |
| AWS Builder | One real Bedrock Runtime Converse through the repository adapter, with original source/date, response and usage evidence | Historical 2026-09-12 proof, not this deterministic recording; no additional invocation authorized |
| Open Source | Public MIT repository, code and reproduction guides; PR history and CI artifacts | Final submission fields and contribution description are not published |

Public contribution: [Elinfiny/HestiaRelay](https://github.com/Elinfiny/HestiaRelay),
GitHub username **Elinfiny**. Implementation and evidence contributions are visible
in [merged pull requests](https://github.com/Elinfiny/HestiaRelay/pulls?q=is%3Apr+is%3Amerged).

## Historical AWS proof, separately identified

On **2026-09-12**, source `56dd5ad6375a668645eec7d8018430479f308267`
executed one `amazon.nova-micro-v1:0` Converse request in temporary CodeBuild.
The reviewed response used the fictional household constraints; 222 input and
230 output tokens were reported, with 1,114.44 ms observed model-call duration.
The [machine receipt](evidence/bedrock-20260912.json) and
[original reviewed output](evidence/bedrock-20260912.log.txt) preserve the result.
Temporary resources were removed after verified evidence export. These facts
must not be represented as a new live call, live Alexa+, AgentCore or Strands.

## Review and publication boundary

The current candidate is prepared for review, not final submission publication.
The owner must approve the concrete visual candidate. Devpost Project Details
and video fields remain untouched. CI artifacts are review evidence; GitHub may
require sign-in to download them. Anonymous repository/README/license access is
checked separately and does not imply anonymous video or hosted-app access.

The official [Alexa+ resources](https://amazonappdev2026.devpost.com/resources)
allow a simulated web experience with a working MCP integration (checked
2026-09-13). Eligibility and prize decisions remain with the organizer.
