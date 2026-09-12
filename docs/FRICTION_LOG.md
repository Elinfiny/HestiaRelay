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
- **Status:** open; plugin installation alone has not resolved account access.
