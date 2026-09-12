# Hackathon Scoring Matrix

HestiaRelay is developed against the four official judging criteria instead of treating judging as a final-stage documentation task.

| Criterion | Target evidence | Implementation status | Exit gate |
| --- | --- | --- | --- |
| Technical Implementation | Real MCP over Streamable HTTP, runtime Alexa+ technology path, Amazon Bedrock call path, persistent continuity, tests, CI | MCP, persistence and simulator tested; one live Bedrock call verified | Live end-to-end MCP + AWS demo; cloud memory validated |
| Design | Voice-first flow, visual continuity timeline, clear safe vs consent-gated states, understandable recovery | Responsive simulator implemented; Chromium QA and screenshot review PASS | Desktop/mobile Alexa+ simulation passes usability review |
| Potential Impact | Household planning use case, repeat-session value, concrete target users, measurable time/coordination savings | Three-session scenario implemented; user impact measurements pending | User story and demo show value beyond hackathon |
| Quality of Idea | Cross-session state, service orchestration, consent-aware autonomy, not single-turn Q&A | Cross-session demo and exact-proposal consent tested | Demo visibly proves continuity and multi-step orchestration |

## Bonus target: friction log

Every real developer-experience problem is recorded in `docs/FRICTION_LOG.md` with reproduction steps, severity, workaround, and an actionable suggestion. No issue is fabricated for bonus scoring.

## Primary-track proof checklist

- [ ] Working MCP server shown in demo.
- [x] Streamable HTTP connection verifiably exercised by real SDK/TCP smoke.
- [x] Official MCP Inspector 2.6.0 verified against the real container;
  observed protocol 2025-11-25, strict tool list and continuity-brief call PASS.
- [x] Repository runtime code imports and calls MCP SDK.
- [x] Alexa+ experience simulation exercised in Chromium; no live Alexa+ claim.
- [x] Cross-session context visibly recovered with the same goal ID.
- [x] Sensitive action visibly blocked behind exact-proposal consent.

## AWS Builder proof checklist

- [x] Bedrock Runtime adapter exists in runtime code.
- [x] One live Bedrock call verified with the owner account and existing applicable credits.
  The separately requested hackathon credit award remains unverified.
- [ ] AWS integration produces user-visible value in demo.
- [ ] AgentCore Memory evaluated and integrated if it improves continuity.
- [ ] Strands evaluated and integrated if it improves orchestration.
- [x] README and AWS runbook document the real Bedrock/temporary CodeBuild proof.

## Open Source proof checklist

- [x] Repository created during hackathon window.
- [x] Repository is public.
- [x] MIT license exists.
- [x] Source and documentation are public.
- [ ] Public contribution URL recorded in final submission evidence.
- [x] Clean GitHub runner built the Docker image and exercised the documented
  non-root persistent-volume path; CI 34719571606 and durable container evidence.

## Final submission quality gates

- Video under three minutes and in English.
- Public repository is judge-accessible without credentials.
- README claims match tested behavior exactly.
- Installation path is independently reproduced.
- No secrets or private-project material exist in Git history.
- Submission text maps each major feature to judging evidence.
