# HestiaRelay AI Development Contract

## Mission
Build the strongest possible Alexa+ submission for the 2026 Amazon Developer Hackathon while preserving truth, isolation, reproducibility, and safety.

## Scope
Work only in `Elinfiny/HestiaRelay`. Do not import code, prompts, credentials, receipts, business logic, or proprietary data from any private project.

## Competition invariants
- Primary track: Alexa+.
- Repository remains public and MIT licensed.
- The MCP runtime must use Streamable HTTP and remain compatible with the hackathon minimum protocol baseline 2025-11-25.
- Runtime Amazon/AWS claims must be backed by code that imports and actually calls the relevant technology.
- Submission materials must remain in English.
- Friction findings must be real, reproducible, and recorded when encountered.

## Safety invariants
- No arbitrary shell execution from user or model input.
- No committed credentials, tokens, AWS keys, personal data, or real household secrets.
- Purchase, money movement, destructive operations, external-account mutation, and disclosure of sensitive information require an explicit consent gate.
- A consent decision authorizes only the exact proposal being approved; it must not create a general permission.
- Development adapters may simulate side effects. A simulation must never be described as a real external action.

## Engineering rules
1. Audit before editing.
2. Prefer typed boundaries and deterministic validation.
3. Add or update tests for every behavior change.
4. Keep AWS integrations behind explicit adapters and dependency injection so tests never require live credentials.
5. Preserve a deterministic local path for development and judging fallback, but do not hide when AWS is unavailable.
6. Do not weaken policy checks to make a demo pass.
7. Run `ruff check .` and `pytest --cov=hestiarelay --cov-report=term-missing` before completion.
8. Record architecture decisions that materially affect judging or safety.

## Publishing gate
Do not merge a feature branch into `main` until automated validation is green and the diff has been reviewed for secrets, scope drift, misleading claims, and regressions.
