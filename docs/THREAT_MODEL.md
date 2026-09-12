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
