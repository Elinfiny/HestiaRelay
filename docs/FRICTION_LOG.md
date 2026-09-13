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
