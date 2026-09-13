# Submission rehearsal — candidate review

Prepared 2026-09-13 for [Issue #16](https://github.com/Elinfiny/HestiaRelay/issues/16).
This is a repository checklist, not a completed submission. Devpost Project
Details story and video fields remain untouched.

## Exact candidate

- Merged implementation: `a5180502d7b347ff41c696bc2c5104c91c69d896` (PR #15).
- Selected recording: CI [34744690053](https://github.com/Elinfiny/HestiaRelay/actions/runs/34744690053),
  `browser-qa` artifact `10313078678`, `demo/hestiarelay-candidate.mp4`.
- Original recording checkout: `fae4f056d7d140d04958ce6e29b2ac339227eaa1`.
  Its implementation head is `5c57917395adf3b247c77f06dcf9338557e826fe`;
  only four documentation files differ between that head and merged main.
- Duration: **87.84 seconds**. Audio: none; English captions.
- MP4 SHA-256: `95eeb6f2dea2a8dd3287eb91368a99f98b86398a94746a26fb21d289316c47bd`.
- Owner visual decision: **ACCEPTED on 2026-09-13**; see the
  [approval receipt](evidence/video-approval-20260913.json). A later CI recording
  is a different artifact and must not silently replace this candidate.

The [release receipt](evidence/release-20260913.json) preserves ZIP digests,
inner-file verification, technical visual review and actual MCP results.
GitHub may require authentication to download CI artifacts; this is not the
public video URL required for final submission.

## Watch sequence

| Approximate time | Actual demonstration | Claim supported |
| --- | --- | --- |
| 0:07 | Six guests, Friday evening, $120 | A saved household goal |
| 0:13 | New session adds Ana's nut allergy constraint | Existing context is recovered without resubmitting the goal |
| 0:19 | New session asks about readiness | Goal, budget, people, preferences and tasks persist |
| 0:27 | Planner source shown | Deterministic simulation is explicitly identified |
| 0:33–0:49 | Exact proposal, approval, actual server restart | Scoped consent and state survive restart; nothing is executed |
| 0:57–1:04 | Changed context and rejected proposal | Earlier approval does not become general permission |
| 1:11 | Real MCP receipt from the same running household | Streamable HTTP tool call and protocol 2025-11-25 |

## Reproduction handoff

The [README](../README.md) supplies the Python path;
the [container guide](CONTAINER_GUIDE.md) supplies the non-root Docker path.
Use fictional details. Default operation requires no AWS credentials. A judge
can follow the three built-in session buttons and inspect the saved context,
planner source and consent ledger. Restart with the same SQLite database to
preserve the household; a new database intentionally starts a new household.

CI independently exercises real MCP/Inspector clients, separate sessions,
container recreation, desktop/mobile Chromium, authenticated TLS boundaries
and backup/restore. This evidence does not certify every physical device or a
screen reader. Optional authenticated judge mode disables remote MCP; local
MCP interoperability is tested separately. No public app endpoint is claimed.

## Submission acceptance inventory

The [official rules](https://amazonappdev2026.devpost.com/rules), checked
2026-09-13, allow an Alexa+ simulation. They require an English-compatible
submission, public source, functioning demonstration, public YouTube/Vimeo
video, product feedback and the selected track/challenge details. Repository
and video can support evaluation without public application hosting. Personal
eligibility and final acceptance remain organizer decisions.

| Item | Current evidence / state |
| --- | --- |
| Primary track | Alexa+; guided text simulation with an additional working MCP server |
| Source and license | Public [repository](https://github.com/Elinfiny/HestiaRelay), MIT; anonymous repository/README/license reads pass in CI |
| Working demonstration | Exact candidate above; owner acceptance recorded |
| Public video and signed-out playback | PENDING; video `_YTQcGxBMrA` uploaded once, last observed private; browser review blocks continuing the existing subtitle dialog ([receipt](evidence/video-upload-20260913.json)) |
| Product feedback | Evidence-based [draft notes](PRODUCT_FEEDBACK.md); no Devpost field written |
| AWS Builder | One historical Bedrock Converse on 2026-09-12; original source and usage in [receipt](evidence/bedrock-20260912.json) |
| Open Source | Owner **Elinfiny**; [implementation contribution PR #3](https://github.com/Elinfiny/HestiaRelay/pull/3), [release contribution PR #15](https://github.com/Elinfiny/HestiaRelay/pull/15), same public repository |
| Four judging criteria | [Evidence map](JUDGE_EVIDENCE_MAP.md); household benefit remains an unmeasured hypothesis |
| Final story, media and submission | Story and video metadata prepared from stable behavior; Devpost untouched |
| Personal eligibility / representation | UNKNOWN; verify privately at the actual submission gate, never infer from a username |
| Current-source security and CI | Phase 4B evidence is dated and scoped; refresh before final submission; applicability decisions expire **2026-09-27** |

Mini-challenge targets are AWS Builder and Open Source. The rules limit awards
to one primary-track prize and one mini-challenge prize per project; targeting
both does not imply eligibility to receive both mini-challenge prizes.

## Publication handoff after the visual decision

The owner's acceptance is recorded against the MP4 digest above. If revisions are
requested, retain this candidate and produce a separately identified replacement.
The permitted YouTube upload has created the video recorded above; exact
publication and upload-terms authorization are already received. Resolve the
browser-access rejection, resume that existing video and verify its actual public
effect, then verify signed-out playback, captions and complete duration.
Never replace a failed upload with a claim of publication or use CI download
access as evidence of public playback. Any platform authentication or new
publication permission gate must concern the prepared, exact action.

Before final submission, recheck the live rules, all mandatory items and every
external link. Rebuild and rerun the existing gates on the selected source;
resolve any new findings rather than reusing expired applicability decisions.
No additional AWS call, resource, charge or public app hosting is included.
