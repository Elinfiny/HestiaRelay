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
