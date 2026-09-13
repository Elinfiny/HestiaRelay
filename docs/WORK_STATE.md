# HestiaRelay work state

Canonical main SHA: `61496e94cb22dd1b444f72607982b1af6652b7e8`.
Post-merge CI [34721784644](https://github.com/Elinfiny/HestiaRelay/actions/runs/34721784644)
SUCCESS: all four jobs. Main ref readback matches. PR #13 merged; Issue #12
closed after validation. This Phase 4B checkpoint is on
`feature/release-audit-v1`; PR #15 is open. Phase 4B container/toolchain
remediation and the real demonstration candidate are under validation.

Previous Phase 3 main: `e13cef9d3d7a0cd346e4ce59c1810db2e6e3b247`,
CI 34720181231 SUCCESS; Issue #10 closed.
Live-executed AWS source: `56dd5ad6375a668645eec7d8018430479f308267`.
The one-build/one-Converse authorization is consumed and resources were removed;
no new AWS spending or invocation is authorized.

## Current phase

**Phase 4A complete. Phase 4B started: release audit and judge demonstration.**
Issue #14 is the executable specification. The first source-bound inventory is
`docs/evidence/release-inventory-20260912.json`: 43 pinned Python packages,
container base identity, dependency constraints, Actions, Inspector and browser
versions. The first completed scan and preserved failures are recorded in
`docs/evidence/release-initial-scan-20260913.json`. `docs/RELEASE_AUDIT.md`
records targeted remediation and the expiring applicability gate. Final PR/main
CI and candidate integrity/visual review are still pending at this checkpoint.
The judged runtime is one fictional household and one worker; public hosting,
remote MCP authorization and complete release security remain separate gates.

## Phase 4A delivery gates

- Local and main CI Ruff PASS; 141 tests PASS; 98.11% application coverage.
- PR CI 34721663874 and main CI 34721784644: all four jobs SUCCESS.
- Actual main image:
  `sha256:961bbff2734fe28fe1b8728211024735c291154d07d740f47aebc46fd34a8b3e`.
- Main browser artifact 10307120082; main container artifact 10306537165.
  Their identities were read from GitHub; the separately downloaded/reviewed
  final PR artifact is recorded below in the durable Phase 4A evidence.
- Shared authentication/CSRF/TLS boundaries, denial/no-planner-effect checks,
  canonical continuity, exact consent, real browser revocation recovery,
  backup/WAL/digest/no-overwrite restore and existing MCP/Inspector/container
  regressions PASS. No new AWS call or public endpoint was created.

## Completed gates

- Real SDK/TCP MCP negotiated 2025-11-25 on separate connections, including
  actual process-restart persistence. Canonical three-session continuity and
  exact-proposal approve/reject/context invalidation tests pass.
- Desktop 1440x1000 and mobile 390x844 Chromium regressions pass. Phase 1
  screenshots were manually inspected; no new manual interaction, physical
  device or screen-reader certification is claimed for this evidence package.
- Local post-proof Ruff PASS; 83 tests PASS; 98.86% application coverage.
  The same 83 tests passed inside the actual AWS CodeBuild job (Python 3.12.13).
- AWS account identity, authorized Nova Micro and enabled applicable existing
  credits verified read-only. Requested hackathon promotional award unverified.
- Owner explicitly approved the exact one-build/one-call proposal and cleanup.
  Schema, custom cfn-guard, change-set and deployed IAM scope checks passed.
- One build SUCCEEDED; one real Converse call returned LIVE_CALL_PASS:
  222 input tokens, 230 output tokens, 1,114.44 ms, completed consistent usage.
  Request/source/role bindings and reviewed fictional response digests match.
- No completed external household action or allergy safety certification in the
  output. The response is advisory; its tendency to ask confirmation for some
  low-risk reviews remains a planner UX limitation, not a runtime failure.
- Original report and reviewed log exported to GitHub and reread exactly before
  cleanup. A final log-cursor read returned zero additional events.
- Stack DELETE_COMPLETE; project absent; dedicated role absent; log group absent,
  verified 2026-09-12T20:59:47.983512+00:00. No unrelated resource changed.
- List-price calculation: Bedrock USD 0.000039970; six rounded build minutes
  USD 0.030; combined USD 0.030039970 before small logs/taxes. Final billing and
  credit application remain unconfirmed. Approved operational budget: USD 0.10.
- [Machine evidence](evidence/bedrock-20260912.json) preserves original probe
  flags; account/cost/output/cleanup checks are recorded in separate fields.
- [Reviewed original log](evidence/bedrock-20260912.log.txt) preserves the live
  result and AWS-side test evidence without account identifiers or credentials.

## Delivery and remaining gates

Phase 3 PR CI 34720085807 and post-merge CI 34720181231 passed validate,
browser, cloud-proof-package and container-judge; Issue #10 records the final
merge and closure. Public repository,
MIT license, domain boundaries and deterministic fallback remain intact.
No second build/call is authorized by the consumed proof proposal.

No external access blocker remains for the completed proof. Public deployment
requires prepared TLS, Host/Origin, household authorization, persistence and
operating-cost gates. The current singleton localhost service must not be
exposed as a multi-user household application.

## Competition readiness

Demonstrated: guided Alexa+ simulation, real MCP interoperability, persistent
cross-session state, exact consent and one real Bedrock runtime call.
Not demonstrated: live Alexa+, AgentCore, Strands, judge-accessible hosting or
measured real-user impact. Final video/submission audit remain open. Devpost
story/video fields are untouched.

## Phase 3 evidence

- Post-merge run 34720181231 executed Phase 3 main
  `e13cef9d3d7a0cd346e4ce59c1810db2e6e3b247`. Its image:
  `sha256:ad44ebcb5ca2dce2baf5808895a7a1832863594dfb545054f890acb8cf2341a8`.
  Container artifact 10306064051 has GitHub-reported ZIP digest
  `05a32b0ec1b896b4cb2d876d19e8a913d9523018b9807a9509fb90a91151a87e`.
  This later archive was not downloaded again; the reviewed archive is below.

- CI 34719571606: all four jobs PASS at feature head
  `2c98e07b008107d95db015ef5b0bb1b16cbb0a36`. Actual PR merge checkout:
  `f8e77d67a2ae8ef8a6dcd4cd5a7de18ee0981744` (parents verified).
- Actual image: `sha256:ec20243738e71ec0033c8c8b5ad0d61c689be53ad1ae48352f09f55fde463d80`.
- Canonical three separate MCP sessions; two container recreations with the
  same volume; goal, budget, preferences and exact approved/rejected consent
  recovered. Non-root, read-only root and hostile Host/Origin checks PASS.
- Inspector 2.6.0 initialization, strict tool listing and continuity-brief call
  PASS; observed SDK and Inspector protocol `2025-11-25`.
- Container-backed desktop 1440x1000/mobile 390x844: no console errors, failed
  requests or horizontal overflow. Both Session 3 screenshots visually reviewed.
- Artifact 10305424084 downloaded and SHA-256/ZIP CRC/path/browser manifest
  verified. Durable result: [container evidence](evidence/container-20260912.json).
- No source application behavior changed and no additional AWS call occurred.
  The initial CI base-tag inspection defect was corrected before the passing run.

## Next executable package

[Issue #14](https://github.com/Elinfiny/HestiaRelay/issues/14): complete the
source/image/dependency/history/artifact security audit, resolve demonstrated
material findings through validated changes, and prepare a scripted English
judge demonstration candidate under three minutes. Use the real app and MCP
evidence. If historical Bedrock evidence appears, label its original source/date
and do not imply a new live call. Preserve artifacts and hashes; request final
visual approval only when a concrete candidate exists. Devpost fields stay
untouched and no owner PC is required.

## Phase 4A verified evidence

- Feature head `1041c0505dfd4c3ab890954935f52282ad69f2e2`; actual PR merge checkout
  `45ff5f2f489abbd0af3dd4c6bd4b01818fe5ad3c`; CI 34721431414, four jobs PASS.
- Browser artifact 10306905225 downloaded; SHA-256, ZIP CRC and safe paths PASS.
  Durable evidence: [judge access](evidence/judge-access-20260912.json).
- Login desktop/mobile and authenticated mobile continuity screenshots from
  initial run 34721340043 visually reviewed. The follow-up changes only handle
  mid-interaction revocation and add its real browser test.
- Existing real MCP/Inspector and container restart suites remain green.
- Scope/secret/claim review: application auth/recovery only; dependencies and
  pinned image base unchanged. This is not a complete vulnerability-free image
  attestation or public deployment review. Those gates remain explicit.

## Phase 4B current checkpoint

- PR #15; initial source 0fc7a419804c50037ab5ce0df6d86f8196afdedf,
  scan CI 34743407436 failed as intended on actual dependency/image findings.
- Pytest CVE-2025-71176 fixed at 9.0.3; Python/build/npm advisory scans passed
  in CI 34743686022. Full Git history and container-artifact secret scans passed.
- Official Python 3.12.14 Trixie digest observed in CI, pinned in Dockerfile.
  Runtime dependency closure reduced to 32 packages; package installer removed.
- CI 34743936152 passed browser/demo, validation, cloud-proof-package and all
  container functional/recovery checks, but image audit still blocked on OS
  patches and component applicability. No unchanged failed run was retried.
- Candidate video from CI 34743686022 is 87.68 seconds, real UI/MCP, English
  captions, deterministic, zero AWS/external household actions. Its archive and
  inner hashes were verified; caption placement was corrected in the next head.
- Current local validation: Ruff PASS, 150 tests PASS, 98.11% application coverage.
- Pending: verify exact Debian patches and runtime component-absence probes;
  review final image/SBOM/notices and all demo artifacts; green PR and main CI.
- Owner visual approval applies only to the concrete final video candidate;
  Devpost fields remain untouched. No new AWS authorization is requested.
