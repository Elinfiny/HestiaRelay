# Run the restricted fictional household

The default `local` mode and real local MCP endpoint remain credential-free.
The optional `judge` mode protects the same application with a shared access key
and expiring browser sessions. It represents one fictional household, not an
identity provider or a multi-tenant service. No public deployment is created.

## Reproduce the full proof in a cloud runner

The existing `browser` GitHub Actions job now also runs:

```bash
python scripts/judge_qa.py
```

It starts the real application over TLS on loopback, exercises login, three
sessions, exact approval/rejection, logout, revoked-cookie replay, re-login,
a live SQLite snapshot, restore into a fresh database and server restart.
Desktop 1440x1000 and mobile 390x844 use real Chromium. Python trusts only the
generated test certificate; Chromium pins that certificate's public key for
this test. This is encrypted local CI traffic, not public CA or domain proof.
The artifact contains screenshots and redacted JSON; authentication traces,
keys and cookies are deliberately not archived.

## Configure an isolated environment

Use Linux, one worker and one state volume. Keep all key files outside the
repository in an owner-only directory. Generate an access key without printing
it or putting its value in shell history:

```python
import os
import secrets
from pathlib import Path

# Select an existing private directory outside the repository.
path = Path("/run/hestiarelay/login.key")
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as handle:
    handle.write(secrets.token_urlsafe(32))
```

Provide the generated key to the intended reviewer through an approved private
credential channel. Never put it in a URL, GitHub issue, screenshot or log.
Runtime configuration contains file paths, not secret values:

```bash
export HESTIA_ACCESS_MODE=judge
export HESTIA_PUBLIC_ORIGIN=https://judge.example
export HESTIA_LOGIN_KEY_FILE=/run/hestiarelay/login.key
export HESTIA_STATE_DB=/data/hestiarelay.db
export HESTIA_BEDROCK_MODEL_ID=
python -m uvicorn hestiarelay.server:app --host 127.0.0.1 --port 8000 \
  --workers 1 --no-proxy-headers --no-access-log \
  --ssl-keyfile /run/hestiarelay/tls.key \
  --ssl-certfile /run/hestiarelay/tls.crt
```

`judge.example` is a placeholder, not a provisioned domain. A public reverse
proxy must preserve the exact configured Host and re-encrypt the upstream
connection; strip forwarding/identity assertions instead of trusting them.
The application requires an actual HTTPS ASGI connection. Simply sending
`X-Forwarded-Proto: https` cannot enable access. Domain/certificate/provider
configuration and the resulting public request path require a separate proof.
The default container health check uses HTTP for local mode; a future judge
container deployment must configure a TLS-aware check for its exact origin.

## Access behavior and revocation

- A random 256-bit key establishes a server-side opaque session. Only the key's
  SHA-256 digest is retained by the application after configuration. This is a
  high-entropy generated key, not a user-selected password.
- Cookies use the `__Host-` prefix, Secure, HttpOnly, SameSite=Strict and Path=/.
  Sessions expire after one hour or 15 minutes idle. They are memory-only and
  bounded to 64 per worker; a restart revokes all sessions and retains SQLite.
- Login has a five-minute CSRF challenge bound to an HttpOnly cookie. Every
  browser mutation also requires exact Origin and its authenticated CSRF token.
  Login attempts are bounded to 20 per minute for this one environment. This
  is a modest abuse limit, not public DDoS protection or per-user rate limiting.
- Sign out revokes the current session. Rotate the key file and restart the
  service to revoke all access. A key file edit alone does not rotate the
  in-memory configuration. In-flight authorized work may finish during logout.
- Host/Origin ambiguity, untrusted forwarding headers, HTTP, cross-site fetches
  and query parameters are rejected. Health contains no household state.
- `/mcp` is unavailable in judge mode, including to a logged-in browser.
  The separately validated local MCP path remains available in local mode.
  Remote MCP OAuth authorization is not implemented by this browser gate.

## Consistent backup and restore

Run under the database owner in a private directory. The source must contain a
saved household. The command opens it read-only and uses SQLite's backup API,
so committed WAL state is included without copying an inconsistent live file.

```bash
python -m hestiarelay.recovery backup /data/hestiarelay.db /backup/snapshot-001.db
python -m hestiarelay.recovery restore /backup/snapshot-001.db /restore/hestiarelay.db \
  --sha256 <sha256-from-the-backup-receipt>
```

Save the first command's JSON receipt separately. Restore checks that exact
file digest, SQLite integrity, the single-table schema and the domain model;
it reads the verified bytes without incorporating an unverified sidecar file.
Both commands require a new destination. Atomic publication refuses even a
concurrent destination creation; existing data is never overwritten. Temporary
files and the result are owner-only. A missing, empty, corrupt or incompatible
source fails with no destination and no silent initialization.

Point an isolated service at the restored database and compare the full
snapshot before promotion. Keep the prior source, receipt and image identity
for rollback. Live replacement is a separate operation. These are unencrypted
local snapshots for fictional data; remote encrypted backups, independent
copies, retention, production RPO/RTO and disaster recovery are not claimed.

References checked during implementation:
[OWASP sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html),
[OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
[Python SQLite backup](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup).
