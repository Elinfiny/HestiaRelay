# Canonical demo and validation

## 90-second judge path

1. Run `python -m hestiarelay.server`; open `http://127.0.0.1:8000/`.
2. Click **Make a plan**. Read six guests, Friday evening and $120. Observe
   `deterministic` provenance without AWS configuration. Note the persisted goal ID.
3. Click **Add what matters**. A new session sends only Ana's constraint. The
   existing goal ID remains. The checklist and plan now include that constraint.
4. Click **Bring it all together**. The new session reconstructs the goal and
   constraints. Read “Not ready yet” and the preparation tasks. Open the exact
   scope of the illustrative $74.50 proposal; no merchant has been selected.
5. Approve or reject that one proposal. The result explicitly says nothing was
   executed. Reload the page: the decision, transcript and preferences remain.
6. Stop and restart the server using the same `HESTIA_STATE_DB`. Context remains.

The top three controls each create a distinct session. **Start another session**
opens another without resetting state. Supported free-text patterns are the
three examples, with variable English counts (one through ten or numeric),
dates, budgets and person/constraint text. Unsupported input is rejected visibly.

## Automated evidence

```bash
ruff check .
pytest --cov=hestiarelay --cov-report=term-missing -s
```

`test_mcp_http.py` starts a real server twice, creates three SDK transport
connections, lists tools, executes the canonical scenario and checks identical
goal identity after restart. It also requests protocol `2025-11-25` explicitly.
The printed `MCP_EVIDENCE` records observed versions, not inferred compatibility.
This is an SDK interoperability smoke, not an MCP Inspector certification.

GitHub Actions executes Chromium against the real Python service. The `browser-qa`
artifact contains initial and session-3 screenshots for desktop 1440×1000 and
mobile-width 390×844, browser traces, and `browser-qa.json`. Assertions cover
session recovery, UI budget/constraint/provenance, approve/reject, reload,
fresh browser context, keyboard focus, horizontal overflow and console errors.
Images must be manually inspected before merging; scripted assertions alone do
not validate design. The suite does not claim physical-device or screen-reader
certification. API validation-error cases are covered by pytest.

## Honest limits

- No live Alexa+, AgentCore or Strands integration.
- No successful live Bedrock call proven by the deterministic or mocked tests.
- No voice capture/speech synthesis. No allergy-safety certification.
- SQLite is single-household development persistence; public deployment needs
  TLS, authentication, tenancy, origin policy, retention and operational review.
- No real shopping prices, inventory, merchant order, message or payment.
