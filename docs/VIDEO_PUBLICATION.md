# Video publication package

Updated 2026-09-13. This package records an accepted visual candidate and exact
publication metadata. **Published Public on YouTube; full playback unverified.**
Devpost story/video fields remain untouched.

## Accepted input

- Original file: `demo/hestiarelay-candidate.mp4` in browser artifact 10313078678,
  [CI 34744690053](https://github.com/Elinfiny/HestiaRelay/actions/runs/34744690053).
- SHA-256: `95eeb6f2dea2a8dd3287eb91368a99f98b86398a94746a26fb21d289316c47bd`.
- 87.84 seconds; H.264 MP4, silent with English captions.
- The owner accepted the pending candidate review after the coverage
  clarification. [Approval receipt](evidence/video-approval-20260913.json).
- Preserve the original bytes, including the recording's draft-review footer.
  Approval changes its review status, not the original video or capture report.
  No replacement render or edited caption is included in this approval.

## Target and current gate

Verified target: **Tomescu Marius**, public channel ID
`UCFNZRod5B5_zl5U2C6UbBGg`, through YouTube Studio after secure sign-in.
The owner explicitly responded **“Aprob”** to uploading and publishing the
unchanged recording on this channel, including the upload dialog's YouTube
Terms of Service and Community Guidelines acknowledgment. That permission
remains valid; no repeated publication or contractual approval is needed.

YouTube created video ID **`_YTQcGxBMrA`** and displayed
`https://youtu.be/_YTQcGxBMrA`. After the owner approved reopening Studio with
possible loss of unsaved dialog changes, the same draft was recovered with its
saved title and description intact. The original SRT was imported once and
saved as **English by you**. No video was uploaded again or regenerated.

Public was selected and Publish clicked once. YouTube displayed **Video
published**, then channel Content read back **Public / Published Sep 13, 2026**.
Checks reported **No issues found** and the preview duration was **1:28**.
The public watch page opened at the exact post-redirect URL
[youtube.com/watch?v=_YTQcGxBMrA](https://www.youtube.com/watch?v=_YTQcGxBMrA),
with the matching title and channel. The
[publication receipt](evidence/video-publication-20260913.json) records these
effects separately from the historical private-[upload receipt](evidence/video-upload-20260913.json).

The cloud watch player remained at 0:00 with no loaded media after ordinary
Play interaction. Its media element reported readyState 0 and no media error;
the underlying cause is unknown. The page's title, duration and Public status
do not prove complete playback. No bot challenge or service outage is inferred.
The supplemental caption track is confirmed saved in Studio; public selectable
caption availability remains unverified. The MP4's burned-in captions remain.

`scripts/verify_public_video.py` prepares one ordinary, fresh-context Chromium
check in GitHub Actions with no account cookies or credentials. It checks
signed-out UI, the exact URL/title, continuous playback without seeking and
hosted duration, preserving actual JSON and screenshots on failure as well as
success. Explicit site gates stop it without sign-in, retries or evasion.
Its result is pending and must not be replaced with publication metadata.

YouTube also displayed a channel-verification requirement for clickable external
description links. Text URLs are saved, but clickability is not claimed. No
channel verification, identity expansion or new account was initiated.

Connected-tool discovery found no direct YouTube/Vimeo upload tool. Directory
results included analytics/social tools, none already connected for this route.
The existing cloud browser is the prepared route; an additional plugin, paid
plan, owner-side recording or owner PC is not required by this package.

## Title

HestiaRelay | A household plan that survives the next conversation

## Description

HestiaRelay preserves a household plan across separate sessions: six people,
Friday evening, a $120 budget, and a later allergy constraint. This prototype
demonstration shows the real browser application, actual restart persistence,
exact-proposal approval and rejection, and a real MCP client reading the same
household over Streamable HTTP.

The video is a guided Alexa+ experience simulation with a deterministic planner.
It is not a live Alexa+ connection. Consent is recorded; no purchase, payment,
message or external-account action is executed. Fictional household data only.
Planning advice does not verify food safety. Silent video with English captions.
The original capture retains its draft-review footer; the owner subsequently
accepted this exact recording.

00:00 HestiaRelay
00:07 Session 1: six guests, Friday, $120
00:13 Session 2: Ana's allergy constraint
00:19 Session 3: recovered readiness context
00:27 Visible deterministic planner provenance
00:33 Exact proposal and consent
00:49 Actual server restart
00:57 Changed context and rejection
01:11 Real MCP client evidence

Public MIT source and run instructions: https://github.com/Elinfiny/HestiaRelay

A separate historical AWS proof performed one actual Bedrock Nova Micro
Converse call on September 12, 2026. Its original source and usage are recorded
at https://github.com/Elinfiny/HestiaRelay/blob/main/docs/evidence/bedrock-20260912.json
No live AWS call occurs in this video. AgentCore and Strands are not integrated.

Prepared for the Amazon Developer Hackathon 2026, Alexa+ track, with AWS Builder
and Open Source mini-challenge targets. Participation does not imply organizer
endorsement or an award.

## Upload and verification sequence

1. Completed: secure sign-in, actual channel readback, exact contractual
   authorization and source rehash before the single file selection.
2. Completed: upload identity, saved title/description, factual audience settings,
   English video language and successful YouTube checks. No new render is used.
3. Completed: owner-authorized Studio recovery, same draft and metadata readback,
   and original English SRT import/save. F-006 is resolved for this continuation.
4. Completed: successful checks, Public selection, one Publish click and actual
   published-state readbacks. Do not publish or upload another copy.
5. Use the approved public-video route required by the
   [competition rules](https://amazonappdev2026.devpost.com/rules), checked
   2026-09-13. Preserve the actual video ID, URL and destination readback.
6. Verify signed-out playback, the complete sequence, English captions and
   duration. Record that hosted transcoding changes bytes; distinguish source
   SHA-256 integrity from visual/playback identity of the hosted video.
7. Update the issue and submission inventory only after these checks pass.
   A local file, CI artifact link or upload-success message alone does not prove
   public playback. Devpost fields require the completed, audited final package.
