# See HestiaRelay work

[Watch the 1:28 narrated demonstration](https://www.youtube.com/watch?v=NC2oy4x9Xdw),
then try the [Python setup](../README.md#local-setup) or
[Docker instructions](CONTAINER_GUIDE.md). No AWS account is needed for the
default demonstration.

The story is simple: six people are coming on Friday, the budget is $120, and
Ana's nut allergy is added in another conversation. When you come back,
HestiaRelay remembers the plan and shows what still needs attention.

## Moments to look for

| Time | What happens | Why it matters |
| --- | --- | --- |
| 0:07 | The first session saves the dinner plan | A goal becomes a persistent household record |
| 0:13 | A new session adds Ana's constraint | Earlier details are recovered without being sent again |
| 0:19 | A third session asks about Friday | The goal, budget, preferences and unfinished tasks return together |
| 0:33 | An exact proposal is reviewed and approved | The decision belongs to these details, not to future actions |
| 0:49 | The server restarts | All three sessions and the saved decision survive |
| 0:57 | A new constraint leads to a new proposal and rejection | Earlier approval does not transfer to changed context |
| 1:11 | A real MCP client reads the household | The browser and MCP share the same working service |

This is a guided Alexa+ web simulation with deterministic planning. It is not
a live Alexa+ connection. Approval records consent; no purchase, payment,
message or account change is executed. The example household is fictional,
and planner advice does not verify food safety.

## Check the implementation

| Area | Evidence | Scope |
| --- | --- | --- |
| Continuity | [Real MCP process-restart test](../tests/test_mcp_http.py), [session tests](../tests/test_simulator.py) | SQLite, one household and worker |
| Decisions | [Domain tests](../tests/test_engine.py), [shared service](../src/hestiarelay/service.py) | Exact approval/rejection and changed-context checks; no external executor |
| Browser experience | [Browser QA](../scripts/browser_qa.py), [authenticated QA](../scripts/judge_qa.py) | Desktop 1440px/mobile 390px Chromium; no screen-reader certification |
| MCP interoperability | [Container QA](../scripts/container_qa.py), [container receipt](evidence/container-20260912.json) | Actual SDK and Inspector 2.6.0, protocol 2025-11-25 |
| Security and recovery | [Threat model](THREAT_MODEL.md), [release audit](RELEASE_AUDIT.md), [judge access guide](JUDGE_ACCESS_GUIDE.md) | Scoped prototype review; dated vulnerability findings and applicability limits |
| Open Source | [Implementation PR #3](https://github.com/Elinfiny/HestiaRelay/pull/3), [release PR #15](https://github.com/Elinfiny/HestiaRelay/pull/15) | Public MIT source, contribution by Elinfiny |

The potential benefit is less repeated context and clearer household decisions.
Real-user time savings have not been measured. The [project story](SUBMISSION_STORY.md)
explains the intended audience and next product test.

## Historical Bedrock test

On September 12, 2026, the repository's optional adapter made one real Nova Micro
Converse call in temporary AWS CodeBuild. It returned a plan from the fictional
household constraints: 222 input tokens, 230 output tokens and an observed call
duration of 1,114.44 ms. See the [original receipt](evidence/bedrock-20260912.json)
and [reviewed output](evidence/bedrock-20260912.log.txt).

This is separate from the deterministic video. Temporary resources were
removed. AgentCore, Strands and a public hosted application are not demonstrated.

## Reproduce and inspect the recording

`python scripts/record_demo.py` records the real app and MCP interaction when
the documented Python dependencies, Chromium and FFmpeg are installed. It adds
captions outside the application image; it does not inject application data or
responses. CI preserves the recording, actual MCP output, screenshots and hashes.

The narrated demonstration's exact identity and publication readback are in the
[publication record](VIDEO_PUBLICATION.md). The accepted silent original and its
complete signed-out Brave viewing report remain in the historical record. The
separate automated YouTube check for that original stopped at a bot challenge;
that failed result remains in the
[playback receipt](evidence/video-playback-20260913.json) and is not attributed
to the narrated video.
GitHub artifact downloads may require sign-in; the public video above is the
viewing route. The [requirements audit](COMPETITION_AUDIT.md) tracks final
submission readiness.
