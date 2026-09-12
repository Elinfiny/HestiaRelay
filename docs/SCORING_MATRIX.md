# Hackathon Scoring Matrix

HestiaRelay is developed against the four official judging criteria instead of treating judging as a final-stage documentation task.

| Criterion | Target evidence | Bootstrap status | Exit gate |
| --- | --- | --- | --- |
| Technical Implementation | Real MCP over Streamable HTTP, runtime Alexa+ technology path, Amazon Bedrock call path, persistent continuity, tests, CI | Foundation implemented | Live end-to-end MCP + AWS demo; cloud memory validated |
| Design | Voice-first flow, visual continuity timeline, clear safe vs consent-gated states, understandable recovery | Not yet implemented | Desktop/mobile Alexa+ simulation passes usability review |
| Potential Impact | Household planning use case, repeat-session value, concrete target users, measurable time/coordination savings | Problem defined | User story and demo show value beyond hackathon |
| Quality of Idea | Cross-session state, service orchestration, consent-aware autonomy, not single-turn Q&A | Core architecture defined | Demo visibly proves continuity and multi-step orchestration |

## Bonus target: friction log

Every real developer-experience problem is recorded in `docs/FRICTION_LOG.md` with reproduction steps, severity, workaround, and an actionable suggestion. No issue is fabricated for bonus scoring.

## Primary-track proof checklist

- [ ] Working MCP server shown in demo.
- [ ] Streamable HTTP connection shown or verifiably exercised.
- [ ] Repository runtime code imports and calls MCP SDK.
- [ ] Alexa+ experience or simulation shown functioning.
- [ ] Cross-session context visibly recovered.
- [ ] Sensitive action visibly blocked behind consent.

## AWS Builder proof checklist

- [x] Bedrock Runtime adapter exists in runtime code.
- [ ] Live Bedrock call validated with hackathon AWS account/credits.
- [ ] AWS integration produces user-visible value in demo.
- [ ] AgentCore Memory evaluated and integrated if it improves continuity.
- [ ] Strands evaluated and integrated if it improves orchestration.
- [ ] README documents exact AWS services and configuration.

## Open Source proof checklist

- [x] Repository created during hackathon window.
- [x] Repository is public.
- [x] MIT license exists.
- [x] Source and documentation are public.
- [ ] Public contribution URL recorded in final submission evidence.
- [ ] Setup/run instructions validated on a clean environment.

## Final submission quality gates

- Video under three minutes and in English.
- Public repository is judge-accessible without credentials.
- README claims match tested behavior exactly.
- Installation path is independently reproduced.
- No secrets or private-project material exist in Git history.
- Submission text maps each major feature to judging evidence.
