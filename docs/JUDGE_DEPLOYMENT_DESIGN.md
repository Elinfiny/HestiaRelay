# Restricted judge deployment design

Status: implementation specification, not a deployed service or spending approval.
Start with one fictional household per isolated environment. The existing
container, shared service, MCP runtime and SQLite remain the application.

## Access and runtime contract

| Boundary | Required behavior before deployment |
| --- | --- |
| Network | A TLS reverse proxy exposes only HTTPS 443. The application listens on a private interface/loopback port 8000; no direct public application port. |
| Host and Origin | Configure one exact public hostname and HTTPS origin. Reject unknown values, wildcards, duplicate/ambiguous host headers and untrusted forwarding headers. Preserve the current loopback-only default. |
| Browser access | Authenticate before any household read or write. Use an opaque, expiring server-side session with Secure, HttpOnly, SameSite cookies. Login secrets stay outside Git and URLs; failed authentication reveals no household data. |
| Mutation protection | Require the authenticated session, exact same-origin validation and CSRF protection for browser mutations. Login and state-changing operations must not use GET. Logout/revocation invalidates the session. |
| Household scope | The authenticated identity belongs to this one fictional environment. Separate environments use separate state volumes and credentials. Do not claim multi-tenant isolation from a singleton database. |
| MCP access | Preserve local Inspector/SDK interoperability. Keep remote MCP unavailable until a standards-conformant authorization path has passed an actual compatible-client test. Browser cookies alone do not demonstrate MCP authorization. |
| Container | Run the pinned image as UID/GID 10001, read-only root, dropped capabilities, no privilege escalation, bounded memory/PIDs and private persistent storage. |
| Planner | Deterministic by default. A live planner is an explicit separately funded mode with visible provenance, bounded calls and failure recovery; the completed one-call approval cannot be reused. |

## State, recovery and observability

Keep `/data` on one dedicated persistent volume with one application writer.
Before an upgrade, make a consistent SQLite backup and verify restoration into
a fresh temporary volume. Exercise all three sessions and the recorded consent
after recreation and restore. Retain the prior image identity for rollback;
do not silently reset the household when a mount or schema fails.

Use fictional data only. Record health, status, duration and correlation IDs;
exclude conversation text, auth cookies, credentials and raw authorization
headers from infrastructure logs. A health endpoint must reveal no household
state. Expire the environment after the approved judging window and delete its
dedicated volume only after exporting the reviewed fictional evidence.

## Acceptance before any public endpoint

- Deny unauthenticated reads/writes, missing/expired/revoked sessions, cross-origin
  mutations and spoofed Host/forwarded identity. Authentication failure must not
  invoke a planner or mutate SQLite.
- Repeat canonical continuity, consent, restart/backup restore, desktop/mobile
  and keyboard/error checks behind a local test TLS/proxy configuration.
- Verify remote MCP authorization independently if it is included in the
  deployment. Otherwise document that MCP remains available through the tested
  local container path; do not label the browser deployment a remote MCP proof.
- Review the complete image/dependency surface and secret/scope/claim diff;
  require all CI jobs green and inspect the signed-out entry path.

## Account and cost gate

The next package can implement and validate these controls offline. It does not
need AWS credentials, an owner PC, DNS changes or a paid model call. Before
deployment, prepare one concrete provider/region proposal with an immutable
source/image, exact resource inventory, domain/TLS ownership, runtime duration,
current compute/storage/network/log rates, bounded inference count and maximum
pre-credit spend. Include cleanup commands and resource readback checks.

Only then request the owner's precise account/domain or financial action that
cannot be completed through existing authorization. No provider is provisioned
and no cost estimate for a future service is asserted by this design.
