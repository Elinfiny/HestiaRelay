# HestiaRelay work state

Canonical main SHA: `a5180502d7b347ff41c696bc2c5104c91c69d896`.
Post-merge CI [34745237742](https://github.com/Elinfiny/HestiaRelay/actions/runs/34745237742)
SUCCESS: all four jobs. Main ref and logs read back on 2026-09-13.
PR #15 merged; Issue #14 closed only after confirmed post-merge completion.
This next-package checkpoint is on `feature/submission-rehearsal-v1` and does
not claim its own future commit hash as canonical main.

## Current phase

**Phase 4B complete within its scoped release-audit and draft-video remit.**
**Phase 5 started: submission rehearsal and final visual decision, Issue #16.**
The English rehearsal checklist and factual product-feedback notes are prepared.
The exact video candidate is ready for the owner decision requested by the
original mandate. No Devpost Project Details story or video field is edited.

## Completed gates

- Final PR CI 34744985406 and main CI 34745237742: all four jobs SUCCESS.
- Ruff PASS; 150 tests PASS; 98.11% meaningful application coverage, both local
  and main CI. The known Starlette/AnyIO deprecation warning is not a test failure.
- Real SDK/TCP MCP and Inspector 2.6.0 negotiate 2025-11-25. Canonical three
  sessions, exact approve/reject, context invalidation and restart persistence PASS.
- Real non-root/read-only container; shared SQLite survives container recreation.
  Actual container backup/restore reproduces the saved household and consent.
- Desktop 1440px/mobile 390px Chromium, TLS/Host/Origin/CSRF boundaries, session
  revocation/recovery and same-household MCP checks PASS. No console errors in
  the recorded demonstration. Technical frames and mobile screenshots inspected;
  no physical-device, screen-reader or full manual-interaction certification.
- Source-bound runtime/build/proof Python and Inspector/npm advisory scans,
  image/SBOM/notices, full Git history and artifact secret checks completed.
  Main history contains 60 scanned commits; one exact historical source-hash
  false positive is documented in the narrow Gitleaks ignore entry.
- Main image: `sha256:072afddba77b5f5a4f09ed1e8d163592f57643b9c3b8c8879449604c400a2ac0`.
  Main artifacts: container 10312644689, browser 10314305185, validation
  10313654525. Their GitHub-reported identities are recorded in Issue #14;
  they do not replace the separately downloaded and visually reviewed candidate.
- Anonymous repository/README/license access PASS. CI video downloads can
  require authentication; public video playback is a separate outstanding gate.

## Audit limits that must persist

[Release receipt](evidence/release-20260913.json) and
[audit scope](RELEASE_AUDIT.md) preserve the selected image's raw findings:
0 critical, 44 high, 48 medium, 57 low and 1 unknown-severity package/advisory
records. No vendor-fix-available record remains in that scan. Nine exact
source/component/control-bound decisions mark 45 high/unknown records not
reachable in the reviewed runtime; these decisions expire **2026-09-27**.
This is not a zero-CVE image, an independent third-party attestation or public
hosting approval. New source/control/advisory changes fail the applicability
gate when they invalidate its scope. Refresh the audit before final submission.

## Exact visual candidate

- CI 34744690053; browser artifact 10313078678; original recording checkout
  `fae4f056d7d140d04958ce6e29b2ac339227eaa1`.
- MP4: **87.84 seconds**, silent with English captions, actual UI and MCP.
  Three sessions, exact approval, actual restart and rejection are recorded.
- Video SHA-256:
  `95eeb6f2dea2a8dd3287eb91368a99f98b86398a94746a26fb21d289316c47bd`.
- ZIP digest, CRC, safe paths and inner manifests verified. The selected
  implementation head differs from merged main in four documentation files only.
- **Owner visual approval PENDING for this exact file.** A new CI video is not
  automatically an approved replacement. No AWS call or household side effect
  occurred in this deterministic recording.

## Historical AWS proof and authority

Source `56dd5ad6375a668645eec7d8018430479f308267` performed one actual Nova Micro
Converse call on 2026-09-12 in temporary CodeBuild. Original usage: 222 input
and 230 output tokens; observed call duration 1,114.44 ms. The same historical
build passed 83 tests with 98.86% coverage. Preserve that source/date; do not
present it as execution of today's release or the deterministic recording.
[Original receipt](evidence/bedrock-20260912.json) and
[reviewed log](evidence/bedrock-20260912.log.txt) preserve the evidence.
Temporary stack/project/role/log group removal was verified at
2026-09-12T20:59:47.983512+00:00. No unrelated resource changed.

The one-build/one-call authorization is consumed. **No new AWS spending,
inference or resources are authorized.** Historical list-price calculation was
USD 0.030039970 before small logs/taxes; actual billing and requested hackathon
promotional award remain unconfirmed. No owner PC is an execution dependency.

## Competition readiness and open gates

Demonstrated: guided Alexa+ simulation, real MCP, cross-session persistence,
exact consent, optional authenticated single-household judge mode and one
historical Bedrock call. Not demonstrated: live Alexa+, AgentCore, Strands,
public application hosting or measured real-user impact. The project remains
public MIT and supports fictional data with one worker/household.

The immediate external gate is the owner's exact final visual decision.
Public YouTube/Vimeo publication and signed-out playback, final submission
materials, private owner eligibility/representation and refreshed final audits
remain later submission gates. These are pending/unknown, never silently PASS.
Personal information must not be written to the public repository.

## Next executable package

[Issue #16](https://github.com/Elinfiny/HestiaRelay/issues/16), already started:
[submission rehearsal](SUBMISSION_REHEARSAL.md),
[product feedback preparation](PRODUCT_FEEDBACK.md), and existing
[judge evidence map](JUDGE_EVIDENCE_MAP.md).
Present the exact candidate for the mandated visual decision. After that
response, apply requested edits or prepare its permitted publication route;
verify the actual uploaded identity and anonymous playback. Continue ordinary
technical work automatically. Keep Devpost fields untouched until final
materials are stable, audited and within the owner's publication authority.
