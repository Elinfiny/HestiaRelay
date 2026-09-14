# Submission rehearsal

This is the final dry run, not a completed Devpost submission. The current
field-ready material is in [FINAL_SUBMISSION_PACKAGE.md](FINAL_SUBMISSION_PACKAGE.md).

## Judge path

1. Open the public [repository](https://github.com/Elinfiny/HestiaRelay) and
   confirm the MIT license and Quick start.
2. Watch the public narrated
   [1:28 demonstration](https://www.youtube.com/watch?v=NC2oy4x9Xdw).
3. Run the three built-in sessions with deterministic planning; no AWS account
   is needed.
4. Inspect the timeline, planner source and consent ledger.
5. Restart the server with the same SQLite path and confirm that the household
   and decisions return.
6. Use the documented MCP client path to read the same household state over
   Streamable HTTP.

## Video sequence

| Time | What the judge sees | Evidence |
| --- | --- | --- |
| 0:07 | Six guests, Friday evening and a $120 budget | A saved household goal |
| 0:13 | A new session adds Ana's nut-allergy constraint | Earlier context is recovered |
| 0:19 | A third session asks if the household is ready | Goal, people, budget, preferences and tasks persist |
| 0:27 | Deterministic planner source | The no-credentials path is explicit |
| 0:33–0:49 | Exact proposal, approval and a real restart | Consent and state survive restart; nothing external executes |
| 0:57–1:04 | Changed context and rejection | Old consent is not general permission |
| 1:11 | A real MCP client reads the same household | Streamable HTTP and protocol 2025-11-25 |

## Rehearsal verdict

| Gate | State |
| --- | --- |
| English project copy | Ready in repository |
| Public source and license | PASS |
| Public narrated video under three minutes | PASS; creator-reported complete Brave playback |
| Reproducible no-AWS route | PASS |
| Alexa+ simulation disclosure | PASS |
| Exact consent and no false side effects | PASS |
| Product feedback | Prepared |
| Open Source details | Prepared |
| AWS Builder details | Prepared; historical one-call scope is explicit |
| Current four-job CI | Must pass on the final exact branch and merged main |
| Security evidence | Refresh required after 2026-09-27 |
| Entrant eligibility and rights | Private declaration required |
| Devpost form and received receipt | Not yet completed |

The earlier silent recording is preserved as unlisted technical history and is
not the submission video. It is not promoted in the judge path.

## Final protected gate

Immediately before submitting, recheck the live rules, deadline and every
external link; refresh the release evidence; confirm the exact selected track
and mini-challenges; privately complete the entrant declarations; paste only the
audited English copy; preview the entry; submit once; and read back the received
submission. Do not turn a browser timeout, upload acknowledgement or draft save
into a claim of successful submission.
