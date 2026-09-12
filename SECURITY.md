# Security Policy

HestiaRelay is a hackathon project that handles simulated household context and consent-gated actions. Do not submit real credentials, personal data, payment information, access-control secrets, or other sensitive household data to public issues or test fixtures.

## Reporting a vulnerability

Please report security-sensitive findings privately to the repository owner rather than opening a public issue containing exploit details or secrets.

A useful report should include:

- affected commit or version;
- reproduction steps;
- expected and actual behavior;
- potential impact;
- a minimal proof of concept without real credentials or personal data.

## Security invariants

- Unknown action types default to review, never safe.
- Sensitive side effects require exact-proposal confirmation.
- The bootstrap does not perform real purchases, payments, access-control changes, destructive actions, or external-account mutations.
- AWS credentials are resolved outside the repository and must never be committed.
- Any public MCP deployment requires a dedicated Host/Origin/TLS review before exposure.

See `docs/THREAT_MODEL.md` for the current threat model.
