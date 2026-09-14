# Developer Friction Log

Record only real issues encountered while building HestiaRelay. Each entry must be reproducible and useful to the product team.

## Entry template

### F-XXX — Short title

- **Date:** YYYY-MM-DD
- **Area:** Alexa+ / MCP / AWS / Bedrock / AgentCore / Strands / Devpost / documentation / tooling
- **Task attempted:**
- **Environment:**
- **Steps taken:**
  1. ...
  2. ...
- **Expected result:**
- **Actual result:**
- **Severity:** low / medium / high / blocker
- **Workaround:**
- **Actionable suggestion:**
- **Evidence:** links, logs, screenshots, commit, or issue
- **Status:** open / worked around / resolved

---

## F-001 — Repository creation not available through connected GitHub action

- **Date:** 2026-09-12
- **Area:** Tooling / GitHub
- **Task attempted:** Create the public HestiaRelay repository through the connected automation surface.
- **Environment:** ChatGPT connected GitHub integration.
- **Steps taken:** Checked available repository actions and attempted authenticated browser automation as a fallback.
- **Expected result:** Create one public repository with README, Python `.gitignore`, and MIT license.
- **Actual result:** The GitHub connector exposed repository content and mutation actions but not repository creation; the separate browser automation session did not share the authenticated GitHub session.
- **Severity:** low
- **Workaround:** Repository creation was completed manually in GitHub; all subsequent repository work is automated through the connected GitHub integration.
- **Actionable suggestion:** Provide an explicit create-repository action or a documented handoff path from connected GitHub identity to browser automation.
- **Evidence:** Initial repository commit `d834190` and the bootstrap branch history.
- **Status:** worked around

## F-002 — Separate cloud browser cannot reach the development loopback

- **Date:** 2026-09-12
- **Area:** Tooling / browser QA
- **Task attempted:** Open the running simulator at `http://127.0.0.1:8000/`.
- **Environment:** Cloud executor with a separate managed Chrome browser.
- **Steps:** Start the loopback server; navigate the managed browser to the URL.
- **Expected:** Simulator page reachable for desktop/mobile QA.
- **Actual:** `net::ERR_BLOCKED_BY_CLIENT`; Python HTTP tests can reach the server.
- **Severity:** medium
- **Workaround:** Run Chromium beside the real server in GitHub Actions; preserve
  screenshots and traces for visual inspection. Do not expose the development
  endpoint publicly or describe this as an Alexa+ service issue.
- **Suggestion:** Provide an authenticated executor-to-browser preview route.
- **Evidence:** `scripts/browser_qa.py`, CI browser job and `docs/DEMO_GUIDE.md`.
- **Status:** worked around; CI run 34710345180 browser job PASS;
  desktop/mobile screenshots manually inspected.

## F-003 — AWS Core installation does not expose AWS operations in this session

- **Date:** 2026-09-12
- **Area:** Tooling / AWS connection
- **Task attempted:** Inspect account/model/credit readiness without a paid call.
- **Environment:** ChatGPT Work cloud executor; AWS Core enabled by the owner.
- **Steps:** Verify the plugin's installed/enabled state, inspect its declared
  dependency and discover AWS API/MCP tools; check the official cloud CLI route.
- **Expected:** An authenticated AWS operation surface or a usable sign-in path.
- **Actual:** Plugin installation and Bedrock/SDK/billing skills are confirmed;
  no AWS operation tools are exposed in this session. The CLI is absent and
  downloading the official installer fails with `Proxy CONNECT aborted due to
  timeout`. The earlier console page displays `Site Unavailable`.
- **Severity:** blocker for live AWS verification only.
- **Workaround:** Continue offline implementation and tests; keep real account,
  credits and model access unverified. Do not infer an AWS service outage.
- **Suggestion:** Display separate plugin-installed, transport-ready and
  account-authenticated states, with a supported secure recovery action.
- **Evidence:** [Issue #4](https://github.com/Elinfiny/HestiaRelay/issues/4),
  cloud capability readbacks. No account identifiers or credentials published.
- **Status:** resolved for AWS Core operations on 2026-09-12. On the later
  continuation, operation tools became exposed; STS, Bedrock model availability,
  Billing GetCredits and Price List reads succeeded. The original session
  observations remain historical; no service outage or owner-side repair is
  inferred. The managed cloud proof proposal now uses that authenticated route.

## F-004 — First managed proof spends most of its time provisioning

- **Date:** 2026-09-12
- **Area:** AWS / CodeBuild developer experience
- **Task attempted:** Run the approved immutable-source Bedrock proof.
- **Environment:** On-demand Linux general1.small, pinned curated image
  `aws/codebuild/standard:7.0-26.07.29`, us-east-1.
- **Steps:** Create the reviewed project; start exactly one build; inspect
  BatchGetBuilds phases and its CloudWatch log.
- **Expected:** A visible distinction between environment startup and app latency.
- **Actual:** PROVISIONING took 288 seconds; BUILD took 30 seconds; the observed
  Converse request took 1,114.44 ms. The complete run succeeded. This is one
  observation, not a universal cold-start benchmark; the underlying cause was
  not determined and no AWS outage is inferred.
- **Severity:** low.
- **Workaround:** Show provider phase separately, budget for the full submitted
  build duration and keep the model latency separate. Do not restart a healthy
  provisioning build to make the demo appear faster.
- **Suggestion:** Surface image provisioning progress and its billable duration
  prominently for first-time users.
- **Evidence:** [Machine evidence](evidence/bedrock-20260912.json),
  [reviewed original log](evidence/bedrock-20260912.log.txt).
- **Status:** worked around; the single approved attempt succeeded.

## F-005 — Browser runner has no video encoder by default

- **Date:** 2026-09-13
- **Area:** Tooling / GitHub Actions / demonstration capture
- **Task attempted:** Encode the actual Playwright recording with English captions.
- **Environment:** GitHub-hosted Ubuntu browser job, Python 3.12.14,
  Playwright 1.62.0; the cloud editing executor separately had FFmpeg installed.
- **Steps:** Run the real three-session/consent/restart/MCP sequence, then invoke
  FFmpeg to encode the captured WebM as an MP4 with a separate caption band.
- **Expected:** The encoder is available to the recording script.
- **Actual:** UI and MCP interactions succeeded; encoding raised
  `FileNotFoundError: ffmpeg` in CI 34743407436, browser job 103686835298.
- **Severity:** medium, demonstration packaging only.
- **Workaround:** Explicitly install FFmpeg in the browser job. CI 34743686022
  produced an 87.68-second video and passed browser validation. Visual review
  then corrected caption font size; no application-response substitution occurred.
- **Suggestion:** Declare media encoder dependencies separately from browser
  dependencies and verify the exact execution environment before recording.
- **Evidence:** `scripts/record_demo.py`, CI workflow, archived raw recording.
- **Status:** resolved; final candidate review remains a separate gate.

## F-006 — Browser review blocks the active YouTube subtitle dialog

- **Date:** 2026-09-13
- **Area:** Cloud browser approval review / video publication tooling
- **Task attempted:** Add the original timed English captions to the existing,
  owner-authorized upload before publishing it.
- **Environment:** Authenticated cloud YouTube Studio, existing upload wizard,
  English-subtitles dialog; one uploaded video, last observed saved as private.
- **Steps:** Click the observed Upload file button inside that dialog through
  the existing tab handle. After rejection, request a read-only DOM snapshot
  from that same handle, without navigation or reloading.
- **Expected:** Interact with or inspect the current dialog without changing its
  location. A rejection should identify the actual proposed action.
- **Actual:** Automatic review rejected both operations as navigation to the
  Studio origin that might discard unsaved upload/subtitle state. Neither
  submitted command contained navigation. The reason for this mismatch is
  unknown; it is not evidence of a YouTube or AWS service outage.
- **Severity:** blocker for continuing this publication route only.
- **Workaround:** None established. Stop browser interaction, preserve the video
  ID and last confirmed state, and continue repository documentation. Do not
  retry indirectly, create another upload or claim public playback.
- **Suggestion:** Distinguish existing-tab DOM operations from navigation in
  approval review and provide a supported recovery that preserves draft state.
- **Evidence:** [Upload receipt](evidence/video-upload-20260913.json), Issue #16;
  the upload-terms and publication authorization was already explicitly given.
- **Status:** resolved for the next continuation. The owner explicitly approved
  reopening Studio despite possible unsaved-dialog loss. That navigation
  succeeded; the same saved draft and metadata were recovered, original SRT
  saved, and Public publication confirmed. No duplicate video upload.

## F-007 — PR merge returns server-response errors

- **Date:** 2026-09-13
- **Area:** GitHub publication tooling
- **Task attempted:** Merge reviewed PR #18 after all four CI jobs passed.
- **Steps:** Submit the connector merge with the exact reviewed head; reconcile
  the PR after each failed response. In the next continuation, inspect the
  authenticated GitHub PR page and its Ready to merge state, then confirm merge.
- **Actual:** Connector responses included ReadTimeout and internal MCP errors.
  The GitHub UI displayed "Unable to read response from the server. Please try
  again later." PR readbacks remained OPEN with main unchanged.
- **Severity:** blocker for merging this PR; no code or data loss demonstrated.
- **Workaround:** None established. Keep the feature branch and CI evidence;
  reconcile before any future attempt. Do not change protection, repository
  auto-merge settings or credential scopes to force completion.
- **Evidence:** PR #18, head 3068bcdaa7042a0541a9f391cf58742c2286cb13,
  CI 34748295910; Issue #16 records the later publication separately.
- **Status:** open; underlying cause unknown, no GitHub-wide outage inferred.
- **Later result:** resolved for PR #18 at 2026-09-13T22:15:08Z. One ordinary
  connector merge with expected head `081d288591a21f0b4905cdb75aadecd1e71781a5`
  succeeded after the current gates passed under the owner's explicit human
  playback method. Independent PR/main reads confirm merge
  `9b41158373dd89d34fc4e9ef41c3be8d48a43a9d`. No protection or permission changed;
  this does not establish the cause of the earlier server errors.

## F-008 — Public watch metadata loads but cloud media does not start

- **Date:** 2026-09-13
- **Area:** Cloud browser / YouTube playback verification
- **Task attempted:** Play the newly published 1:28 HestiaRelay video.
- **Steps:** Open the published link, inspect matching title/channel, use the
  ordinary Play control and inspect the visible player and media state.
- **Actual:** The page and Public publication readbacks succeeded, but the
  black player stayed at 0:00. The media element reported readyState 0, no
  played ranges and no media error. No bot challenge was displayed.
- **Severity:** blocker for playback validation in this browser only.
- **Workaround:** None demonstrated. A separate mandatory signed-out check is
  prepared in a fresh GitHub-hosted context, with no imported login state,
  fingerprints, proxies, response substitution or automatic retries.
- **Evidence:** [Publication receipt](evidence/video-publication-20260913.json),
  `scripts/verify_public_video.py`.
- **Status:** open; neither successful playback nor a site outage is inferred.
- **Later disposition:** this original cloud-browser limitation remains
  unremediated. A different hosted observation encountered an explicit bot gate
  (F-010). The owner-approved human verification subsequently passed in Brave;
  it is an alternative source of evidence, not a repair of this browser.

## F-009 — GitHub Actions remains queued without creating jobs

- **Date:** 2026-09-13
- **Area:** GitHub Actions dispatch / supported recovery
- **Task attempted:** Validate exact PR #18 head `081d288` using its existing
  CI and public-playback workflows.
- **Steps:** Inspect runs 34749218708 and 34749218515 after their 09:16:11 UTC
  creation. Compare REST and UI, jobs, artifacts and pending approvals. Request
  ordinary cancellation exactly once per run, then reconcile the results.
- **Expected:** The existing runs create jobs or reach a truthful terminal state.
- **Actual:** Both stayed QUEUED, attempt 1, with zero jobs/artifacts for hours.
  Both cancellation controls reported failure; REST remained QUEUED. No
  application or playback result existed at this stage.
- **Severity:** blocker for this package's validation.
- **Workaround:** One existing support ticket, #4754431, requested reconciliation.
  An engineer reported marking both complete on the backend; separate REST/UI
  reads confirmed completed/cancelled before one owner-authorized full re-run
  per existing run. Attempt 2 created jobs. CI passed four jobs; the separate
  playback failure is F-010. No force-cancel, trigger commit or repeated re-run.
- **Suggestion:** Expose orphaned-dispatch state and a reliable terminal-state
  reconciliation instead of leaving a QUEUED record without diagnostic jobs.
- **Evidence:** Issue #16 recovery comments and the two public run histories.
  Private support account/contact data is intentionally excluded.
- **Status:** queue recovery resolved; GitHub's internal root cause was not
  demonstrated. The generic initial support suggestion was not engineer evidence.

## F-010 — YouTube blocks the fresh hosted playback check

- **Date:** 2026-09-13
- **Area:** Public video verification from a GitHub-hosted Chromium browser
- **Task attempted:** Observe the same approved public video completely while
  signed out, without imported browser state.
- **Steps:** Execute the existing bounded verifier in run 34749218515 attempt 2.
  Inspect its actual result JSON and final-page screenshot.
- **Expected:** Ordinary complete playback, or an honest stop at an access gate.
- **Actual:** YouTube displayed "Sign in to confirm you're not a bot". The
  verifier stopped at 0:00 with no played range and recorded BLOCKED. HTTP 200
  and Public metadata were not substituted for playback.
- **Severity:** blocker for this automated evidence method only.
- **Workaround:** No automated bypass attempted. The owner explicitly authorized
  human verification, then confirmed signed-out viewing to the end in Brave with
  readable English text. The failed workflow remains failed; its stop is intact.
- **Suggestion:** Provide a supported, credential-free way to verify public
  demonstration availability without requiring bot-challenge evasion.
- **Evidence:** [Playback receipt](evidence/video-playback-20260913.json), artifact
  10325769333, original result JSON and screenshot hashes.
- **Status:** automated route remains blocked; scoped human evidence accepted.

## F-011 — YouTube Studio SRT chooser resets the browser-control session

- **Date:** 2026-09-14
- **Area:** YouTube Studio caption authoring
- **Task attempted:** Attach the reviewed 1,438-byte English SRT to the newly
  uploaded narrated video.
- **Steps:** Set English as the video language, choose Subtitles > Add > Upload
  file > With timing, and select the synchronized SRT through the documented
  browser file chooser.
- **Expected:** Studio imports the existing twelve timed captions.
- **Actual:** The file was visible at the documented shared path, but both
  `setFiles` attempts timed out and reset the browser-control session. Fresh
  readback still showed the pre-selection dialog, disabled save controls and no
  imported rows; no uncertain effect or duplicate track was inferred.
- **Severity:** bounded authoring-tool failure; the video upload was unaffected.
- **Workaround:** Cancel the unchanged chooser and use YouTube Auto-sync with
  the exact twelve-scene English transcript. Studio saved it and generated
  timed rows, then reported that processing may take a few hours. A later
  independent Studio readback showed the English track Published. Burned-in
  English captions remain visible independently of that track.
- **Evidence:** [Narrated publication receipt](evidence/narrated-video-publication-20260914.json),
  source SRT SHA-256 `0362d1c2598e18a4dabfccfc12a37c2d3bf0cc1dafd45392f6c2b1bd7b80bc3a`.
- **Status:** resolved through a native Studio authoring route; the selectable
  English track is Published.
