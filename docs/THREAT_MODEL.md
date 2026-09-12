# Threat Model

## Assets to protect

- Household preferences and constraints.
- Household plans and budgets.
- External-account authority.
- Purchase and payment authority.
- AWS credentials and configuration.
- Integrity of consent decisions.

## Primary threats

### Prompt-to-action escalation
A user or model attempts to convert a planning request into an external side effect without a consent gate.

**Control:** action kinds are classified before execution; protected kinds become pending proposals.

### Consent broadening
Approval for one proposal is incorrectly treated as permission for future or unrelated actions.

**Control:** approval is bound to a unique `action_id` and changes only that proposal's status.

### Unknown-tool bypass
A newly introduced action type accidentally defaults to safe.

**Control:** unknown action kinds default to `review`, never `safe`.

### Secret exposure
Credentials or tokens are committed or surfaced in prompts, logs, or receipts.

**Control:** credentials are environment-only; `.env*` is ignored except the safe template; raw exception text must not be used as user-facing provenance if it may include sensitive content.

### Misleading simulation
A development adapter reports that a real purchase, message, or account mutation occurred when it only simulated one.

**Control:** simulations must be explicitly labeled and may not claim external completion.

### Cross-project leakage
Private project code or business data is copied into the public hackathon repository.

**Control:** repository contract explicitly forbids importing private code, prompts, receipts, credentials, or proprietary data.

### MCP transport exposure
The Streamable HTTP server is deployed with permissive host/origin settings or without appropriate transport security.

**Control:** localhost is the only bootstrap deployment. Any public deployment requires explicit host/origin allowlists, TLS, and a deployment-specific security review.

## Non-goals in bootstrap

- Real payments.
- Real purchases.
- Real door/access control.
- Real account mutation.
- Storage of real household PII.

These remain blocked until a later milestone proves the integration, consent UX, logging, and rollback model.

## Simulator controls

- JSON API validates UUID identities, rejects extra fields and non-boolean
  approval values, and bounds request bodies. Text and model output render via
  `textContent`, not HTML. Static assets are allowlisted and CSP forbids inline
  scripts and third-party assets.
- Host and Origin checks cover both JSON and MCP routes. They are development
  boundaries, not user authentication. A trusted local caller can use MCP consent
  tools; a public deployment must add authenticated user/household authorization.
- SQLite transactions prevent concurrent updates from losing state. Session
  creation and message request IDs provide idempotent recovery. There is no
  public reset/delete API.
- Changed goals/preferences invalidate pending approval scope. Approval cannot
  reverse rejection, authorize a different ID, or trigger an external adapter.
- Generated text is advisory and untrusted. UI labels distinguish it from the
  authoritative state and consent ledger. Neither planner certifies food safety.
- AWS prompts include only goal, preferences and checklist, excluding transcript
  and consent ledger. Live AWS use still requires the owner's account/privacy
  gate. Tests use fictional state and injected clients.

## Restricted judge mode

- Optional outer authentication covers every household API read/write before the
  shared service runs. Remote MCP is blocked in this mode; local MCP is preserved.
- Exact HTTPS Host/Origin, raw-header duplicate rejection and rejection of proxy
  identity assertions prevent the browser gate from trusting caller-supplied
  forwarding data. TLS termination alone with an HTTP upstream is not supported.
- Opaque Secure/HttpOnly/SameSite sessions and separate synchronizer CSRF tokens
  protect login and mutation. Sessions expire, logout revokes the current token,
  and process restart revokes all sessions. Only one worker is supported.
- Generated high-entropy key files are owner-only, external to Git, never placed
  in URLs or logs. QA excludes auth traces, cookies and key files from artifacts.
- Snapshot publication is create-if-absent. Restore rejects mismatched digests,
  unverified WAL state, incompatible schemas and missing/empty/corrupt sources.
  This provides local fictional-state recovery, not encrypted remote backup.
- Remaining public gates: domain/TLS proxy proof, infrastructure cost approval,
  public abuse controls, independent dependency/image review and, if required,
  standards-conformant remote MCP authorization. No public exposure is authorized.
