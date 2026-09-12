# Issue 12 implementation start

Read-only boundary audit against Phase 3 main
`e13cef9d3d7a0cd346e4ce59c1810db2e6e3b247`.
The deployment contract is in `JUDGE_DEPLOYMENT_DESIGN.md`; no access control is
claimed implemented by this checkpoint.

## Existing integration points

- `server.py` creates one `HouseholdService` and wraps the entire MCP ASGI app
  in `LocalBoundary`. Put deployment access checks outside the shared app so
  custom routes and MCP cannot bypass them through a second mount.
- `web.py` accepts JSON-only mutations capped at 4096 bytes and uses strict
  request models. Preserve those boundaries, canonical request IDs and service
  transactions when adding session and CSRF checks.
- `LocalBoundary` currently converts headers to a dictionary and uses a simple
  host split. Deployment validation must inspect raw header multiplicity before
  normalization and reject malformed/ambiguous values. This is a design finding,
  not a demonstrated exploit of the loopback-only deployment.
- `store.py` owns SQLite transactions and creates an empty schema at startup.
  Recovery tooling must open an existing source explicitly and fail on missing
  or invalid backups instead of invoking initialization and silently succeeding.
- MCP tools call the existing engine/service directly. Blocking only `/api/*`
  would leave an authorization gap in a public deployment. Preserve the local
  MCP path; disable the remote path until separately authenticated and tested.

## Bounded implementation order

1. Add strict deployment configuration and shared request-boundary denial tests.
2. Implement expiring opaque sessions and CSRF with a small English login/logout
   flow. Verify no household read, write or model call occurs on denial.
3. Add backup/restore validation against a fresh volume, preserving consent and
   planner provenance. Never overwrite an existing destination implicitly.
4. Exercise the authenticated browser path through the real service and repeat
   the current four CI jobs. Review the complete diff before merging.

No new infrastructure, credentials, public endpoint or AWS request is part of
this checkpoint. The exact hosting/account/cost proposal follows offline gates.
