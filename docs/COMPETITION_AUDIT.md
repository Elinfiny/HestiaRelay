# Competition and presentation audit

Reviewed September 13, 2026 UTC (September 14 in Bucharest), from main
`bd1bef108152b1faaaaaee6c9fc3966905acfd43`, on
`feature/judge-presentation-audit-v1`. This is an executor self-review,
not independent certification or a completed entry.

## Sources and deadline

The current [official rules](https://amazonappdev2026.devpost.com/rules),
[overview](https://amazonappdev2026.devpost.com/),
[resources](https://amazonappdev2026.devpost.com/resources) and
[updates](https://amazonappdev2026.devpost.com/updates) were read, together with
the incorporated [Devpost terms](https://info.devpost.com/terms)
(last updated December 5, 2025). Rules control over general platform terms
for this contest. Recheck both before final submission.

Submission closes **October 23, 2026, 12:00 PDT / 19:00 UTC / 22:00 Bucharest**.
Judging runs November 9–20; source, instructions and public video must remain
usable for evaluation. The repository was created September 12, within the
published August 31–October 23 submission window. The September 27 date in
security receipts is an internal audit expiry, not the contest deadline.

## Requirement-to-evidence review

| Requirement | HestiaRelay evidence | Result / remaining action |
| --- | --- | --- |
| Eligible entrant and authorized representation | Public GitHub identity is Elinfiny. This does not establish age, residence, conflicts, employer rights or team authorization. | Private declaration required at submission; no personal data goes in this repository. |
| Register and submit through the contest | Project materials are prepared here; no final form receipt is recorded. | Registration/account state, selected categories, complete fields and successful submission readback remain unverified. |
| Work created during the permitted period | Public repository created September 12; implementation PR history is retained. | Repository timing passes; entrant must confirm originality and rights beyond what source history can prove. |
| Working Alexa+ entry | Guided browser simulation uses the real application and persistent household service. | The rules expressly allow a simulation alternative. A live Alexa+ integration is not required for this route. |
| MCP route, if claimed | SDK/TCP and Inspector proof negotiate 2025-11-25 over Streamable HTTP. | Implemented in addition to the simulation; do not imply live Alexa onboarding or remote multi-household authorization. |
| Public source and open-source license | Public repository, README/run instructions, MIT LICENSE and detected license metadata. | Verified at baseline; fresh PR/main CI verifies the delivered source. |
| English-accessible presentation | English app, story, instructions, captions and prepared narration. | Existing public recording is accepted; new audio candidate requires final visual/listening acceptance. |
| Working public video under three minutes | Published 87.84-second YouTube recording; complete signed-out viewing and readable English reported in Brave. | Original passes the approved human method. Hosted bot-gate failure remains a failure; a new local render is not yet public. |
| Video material rights | Original app capture, fictional data, no added music or borrowed promotional footage. New stock narration has pinned model provenance and notices. | Technical provenance reviewed; creator's final rights/representation declaration remains required. |
| Product feedback for tools used | [Tool-by-tool notes](PRODUCT_FEEDBACK.md) cover use, onboarding, what worked, problems and reuse decisions. | Expanded from the earlier grouped draft; copy the final factual version into the required field. |
| Track and mini-challenge selection | Alexa+ primary; AWS Builder and Open Source intended. | Selection in the actual form is not yet verified. |
| AWS Builder explanation and feedback | Optional Converse adapter and one historical Nova Micro call; usage, source and cleanup receipts. | Real but narrow evidence. No new invocation, current cloud hosting or broad service adoption is claimed. |
| Open Source contribution details | Elinfiny; same public repo; [PR #3](https://github.com/Elinfiny/HestiaRelay/pull/3) and [PR #15](https://github.com/Elinfiny/HestiaRelay/pull/15) show continuity and hardening contributions. | Explain the contribution and household benefit; include both repo and contribution URLs. No invented upstream acceptance. |
| Four equally weighted judging criteria | [Evidence map](JUDGE_EVIDENCE_MAP.md) and [scoring matrix](SCORING_MATRIX.md). | Technical and design evidence exists; impact is a reasoned hypothesis, not measured adoption. |
| Optional friction submission | [Friction log](FRICTION_LOG.md) separates task, steps, observed outcome, workaround and improvement. | Optional bonus material; retain only real observations. It is not a mandatory AWS deployment requirement. |
| Availability, originality and final receipt | Public source, preserved original recording and review history; final form untouched. | Keep evidence accessible through judging; confirm declarations and received submission before calling the entry complete. |

The rules allow entry in both targeted mini-challenges but limit a project to
one mini-challenge prize, alongside at most one primary-track prize. Suggested
technologies and sophisticated examples are not mandatory integrations.
Hackathon promotional credits are explicitly offered; their requested status
does not prove an award or authorize more spending. Unrelated prior funding,
conflicts and rights cannot be inferred from this repository.

The rules and platform terms require accurate representation and appropriate
rights/credit. Natural prose is an editorial improvement, not a reason to hide
AI assistance, invent personal experiences or label synthetic speech as a
person's recorded voice. The prepared story acknowledges AI-assisted development.
No new contractual acceptance or submission has been performed by this audit.

## Corrections made in this package

| Finding | Correction | Verification |
| --- | --- | --- |
| README called the accepted public video a draft awaiting approval. | Present the working dinner story and existing public demo; technical review history is linked separately. | Diff review and current publication receipts. |
| Public description exposed internal “owner accepted” language. | Saved conversational English focused on the demonstration, with accurate simulation and consent limits. | Separate Studio page read back the exact [description](YOUTUBE_DESCRIPTION.txt), with Save disabled. |
| Repository About implied broader AWS orchestration. | Changed to “Household plans that persist across conversations: an Alexa+ simulation with real MCP and exact consent.” | GitHub repository API readback confirmed the saved value. |
| Checklist implied AgentCore/Strands and an end-to-end live AWS demo were required. | Distinguish official requirements, implemented proof and optional future work. | Fresh official rules/resources comparison. |
| Feedback grouped several tools without answering each requested dimension. | Expanded per-tool feedback, with limitations grounded in the actual work. | Source/dependency/workflow inventory comparison. |
| Public footage contained a draft-review footer and had no narration. | Preserve the accepted original; prepare a separately identified narrated candidate with a clean caption band. Future recordings also use a product-focused closing caption. | Source hash, scene timing, audio and frame verification in the narration receipt; final human review remains open. |

## Technical and supply-chain audit scope

The application, consent policy, MCP protocol, runtime locks, cloud proposal and
workflow permissions are unchanged by this package. The new media renderer is
an isolated authoring tool: it checks the original capture and model hashes,
rejects overlapping scenes or clipped speech, refuses an existing output
directory, and makes no network call or publication request. Model downloads
are public and documented separately. Media dependencies are excluded from the
application image and audited separately.

The baseline main CI is [34787002311](https://github.com/Elinfiny/HestiaRelay/actions/runs/34787002311),
four successful jobs at `bd1bef1`. Baseline application evidence is 150 passing
tests and 98.11% coverage. This package requires its own Ruff, tests, browser/
container/proof jobs, advisory/secret reports, diff audit and post-merge CI;
exact new results belong in the closing Issue #16 receipt, not a guessed SHA here.

The retained [release audit](RELEASE_AUDIT.md) is scoped to a fictional,
single-household prototype. Its image scan contains unfixed high-severity
package records and exact, expiring non-reachability decisions. It is not a
zero-CVE claim. Their expiry remains **September 27, 2026**; no exception was
broadened or extended. Main currently reports no GitHub-enforced branch
protection. The executor uses guarded PR merges and reads CI, but this does
not substitute for a provider-enforced repository policy.

No new AWS operation, credential, account permission, charge, upload, channel
change or Devpost edit is included. No private project material was imported.
Historical failed playback evidence and approvals retain their original hashes.

## Exit decision

This package can establish technical and editorial readiness of the reviewed
candidate. **Final submission readiness is still pending** until the exact
narrated candidate is accepted (or the existing accepted recording is retained),
private eligibility/rights declarations are completed, live rules and expiring
security evidence are refreshed, and the actual form is submitted and read back.
These are concrete remaining gates, not a prediction about organizer acceptance
or winning. Issue #16 stays OPEN.
