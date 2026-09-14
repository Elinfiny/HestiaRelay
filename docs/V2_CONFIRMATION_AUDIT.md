# V2 confirmation audit — September 14, 2026

This audit starts from main `1cdde1a89dd99a6c30c00445776d942b3de25198`.
It preserves the completed PR #23 package and does not repeat publication,
cloud calls or other historical effects. A full baseline Git bundle was verified
before the isolated candidate was changed.

## Reproduced defects and corrections

| Finding | Before | Correction and evidence |
| --- | --- | --- |
| V2-F1: unavailable saved state | Invalid JSON/model state or damaged SQLite bytes produced generic 500 responses, or incorrectly blamed valid POST input with 422. Six regression cases failed. | A distinct persisted-state exception and route-level storage error handling return redacted JSON 503. All six GET/POST cases pass, preserve the damaged bytes and recover the identical household snapshot after restoring the backup. |
| V2-F2: incomplete MCP estimate | A valid generic MCP proposal with missing or incorrectly typed estimate details broke the entire proposal list at `items.join`. The DOM reproduction rendered zero cards and an error. | Rich estimate rendering requires complete typed fields. Otherwise the proposal remains visible with its exact original scope and an incomplete-details message. All four malformed payloads render in the DOM reproduction. The real MCP/Chromium suite additionally verifies reload, rejection and unchanged payloads. |

Neither correction authorizes external execution or alters the consent ledger.
No state is silently reset. The canonical dinner flow and complete estimate
presentation remain intact.

## Local evidence

- Baseline: 150 tests passed, 98.11% application coverage.
- Candidate: 156 tests passed, 98.14% application coverage; Ruff passed;
  Bandit reported zero findings.
- Proof, runtime and narration dependency audits reported no known advisory.
- The frontend before/after reproduction used jsdom with snapshots produced by
  the real domain engine. It is not a substitute for Chromium evidence.
- Chromium download timed out in this workspace; Docker was unavailable.
  Real browser, TLS, container recreation, MCP Inspector and image checks run
  in the protected CI jobs on the exact candidate. No local PASS is claimed
  for those unavailable environments.

## Security applicability review

All nine Debian tracker references in
[release-applicability.json](evidence/release-applicability.json) were read on
September 14. They still identify the recorded trixie package versions as
vulnerable; fixes in other Debian releases do not establish a trixie fix.
The mitigation claims remain narrowly tied to absent affected executables,
unloaded privileged libraries, absent Python XZ binding and the restricted
runtime. Raw image findings must stay published.

The changed Python code only classifies saved-state failures and returns a
redacted API error. It adds no archive, shell, mount, ACL, namespace or privilege
operation. Dockerfile, dependencies and required runtime restrictions are
unchanged. Only the reviewed `store.py` and `web.py` source hashes are updated;
expiry remains September 27. Fresh image scanning and measured runtime surface
must agree with the review before acceptance. A new applicable finding, fixed
package, changed source or expired review fails the gate.

## Acceptance and submission

The candidate requires all four exact-head CI jobs (`validate`, `browser`,
`cloud-proof-package`, `container-judge`), protected merge and post-merge success.
Final provider identifiers and inspected artifact outcomes are recorded in
[Issue #16](https://github.com/Elinfiny/HestiaRelay/issues/16), rather than
asserting a result before those jobs run.

The latest official rules support the documented Alexa+ simulation route.
Devpost still requires entrant authentication and private declarations. The
prepared package is not a submission receipt; no entry is claimed submitted.
