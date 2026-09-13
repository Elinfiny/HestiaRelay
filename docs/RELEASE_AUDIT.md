# Release audit — Phase 4B

Scope: source, full fetched Git history, pinned runtime/proof dependencies,
resolved CI build tools, Inspector npm dependencies, the actual container OS,
upstream license notices and the recorded judge candidate. A clean scan means
no finding in the named database and scope at that time; it cannot prove the
absence of every vulnerability. Public hosting remains a separate gate.

## Preserved baseline and actual findings

Accepted main before this package: `61496e94cb22dd1b444f72607982b1af6652b7e8`,
CI 34721784644, all four jobs successful. Original evidence stays unchanged.
The first scan ran at PR merge checkout
`36e0adc10897d0b4d05519e01dd60c411558957e`, CI
[34743407436](https://github.com/Elinfiny/HestiaRelay/actions/runs/34743407436).
Its [source-bound receipt](evidence/release-initial-scan-20260913.json) preserves
the failed decision and verified artifact identity. The image had 275
package/advisory records (not 275 unique CVEs), including 62 high/critical
records. No high/critical ignore list was introduced.

- Pytest 8.4.2 was affected by
  [CVE-2025-71176](https://github.com/advisories/GHSA-6w46-j5rx-g56g).
  The minimum upstream fix is
  [9.0.3](https://github.com/pytest-dev/pytest/releases/tag/9.0.3).
  Update only that proof pin and the compatible development constraint.
  All 141 application tests and 98.11% coverage passed locally after the change.
- The Bookworm base contained unresolved findings in SQLite and base utilities.
  Debian records fixes in Trixie for
  [SQLite CVE-2025-7458](https://security-tracker.debian.org/tracker/CVE-2025-7458),
  [util-linux CVE-2026-53613](https://security-tracker.debian.org/tracker/CVE-2026-53613)
  and [Perl CVE-2026-13221](https://security-tracker.debian.org/tracker/CVE-2026-13221).
  Keep Python 3.12.14; use its official Trixie variant pinned by the observed
  digest `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`.
  Registry inspection is preserved in CI 34743686022, artifact 10313128693.
- The old image included test tools and an affected pip installer. The runtime
  lock now follows the installed metadata dependency closure of the five direct
  application packages: 32 exact packages. Proof/testing remains separate.
  Build with patched pip 26.2 and binary wheels; remove pip after `pip check`.
  The runtime does not need a package installer or pytest.
- Existing Actions tags were mutable. Pin their verified current commit IDs
  without changing the selected major versions or increasing permissions.
  GitHub's Node 24 default remains enabled; no insecure runtime override is used.

This is targeted remediation prompted by measured findings. No application
schema, planner model, consent contract or AWS adapter behavior changed. Rollback
source and the earlier pinned base remain in Git history. Container persistence
and full backup/restore checks gate the base change.

## Reproduction and evidence

CI executes Gitleaks 8.30.1 (full `--all` Git history and decoded/archive artifact
scan, redacted reports), pip-audit 2.10.1 (strict PyPI advisory lookup), npm audit,
and Trivy 0.74.0 (image OS/Python advisories and CycloneDX SBOM). Scanner release
archives are verified against their upstream SHA-256 digests before execution.
No automatic dependency fix, blanket ignore, or `continue-on-error` gate is used.
Exit codes, database identity, OS package versions, installed build dependency
metadata, upstream notices, source/image identity and report hashes are exported.

The `container-judge` artifact contains `release/` and the exact Inspector npm
lock. `browser-qa` contains the real UI/TLS evidence and `demo/` candidate.
The latter has its own SHA-256 manifest, actual MCP response and fictional state.
Auth recording is excluded: judge-mode login keys, cookies and private TLS keys
are not included in browser traces or video. The demo uses local deterministic
mode with no credentials, public endpoint or external household action.

Anonymous reads of the public repository, README and MIT license are performed
without tokens or cookies and recorded in `public-judge-path.json`. Artifact
download access is a separate GitHub policy; this check does not claim anonymous
video access. GitHub-hosted runner OS and platform infrastructure are provider
managed and are not represented as a fully audited machine image.

## Licenses and notices

HestiaRelay's own source is MIT licensed. Dependencies retain their upstream
licenses; the container as a whole is not relicensed MIT. Python/build metadata
and the 231-entry Inspector lock in the initial audit had no missing package
license fields. The initial image SBOM identified 151 components; five OS/meta
entries lacked inferred licenses. `upstream-notices.json` additionally preserves
actual Debian copyright/common-license and Python distribution notice files,
including symlinked notices. Review the candidate's SBOM and notices together.
No third-party license files are deliberately removed from the runtime packages.

The image is built and tested in CI; no binary image registry release is made
by this package. A future binary distribution must retain notices and meet the
source-availability requirements of its included OS components.

## Current result

Candidate image scan, final artifact review and main CI remain pending at this
checkpoint. No release-ready or vulnerability-free declaration is made here.
The completed result belongs in the dated machine receipt and WORK_STATE.

Primary tooling references, checked 2026-09-13:
[Gitleaks](https://github.com/gitleaks/gitleaks),
[pip-audit](https://github.com/pypa/pip-audit),
[Trivy image scanning](https://trivy.dev/docs/latest/target/container_image/),
[GitHub Actions security](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions),
[official Python image source](https://github.com/docker-library/python/tree/688a0b86bb44289df16a363e9f41d90514c1a5f9/3.12/slim-trixie).

## Vendor fixes and scoped applicability

The first Trixie scan still required six exact Debian security package updates:
gzip, libc-bin/libc6, libpcre2-8-0, libsqlite3-0 and perl-base. Dockerfile records
the exact fixed versions; APT signature verification remains enabled. This is
not a claim that switching distribution tags alone eliminates findings.

Eight unfixed CVE identities and one unresolved-severity XZ advisory need a
component-level applicability decision. The raw scanner findings are retained.
[release-applicability.json](evidence/release-applicability.json) records exact
package versions, vendor sources, source/lock/image-definition hashes, required
runtime facts and expiry **2026-09-27**. Critical, newly fixable, new-ID,
changed-package/version and expired decisions block CI. Regression tests verify
that no earlier decision can authorize that changed scope.

- `mount`, `nsenter`, `infocmp` and Perl interpreter entry points are removed
  from the final image. The util-linux mount/nsenter and ncurses infocmp CVEs
  concern these CLI paths; the removed Perl interpreter cannot extract archives.
- `systemd-homed` is absent. The service does not load libsystemd, libudev or
  libacl and has no privileged ACL/group/namespace interface.
- The optional Python `_lzma` extension is removed, and liblzma is not loaded
  by the service. No XZ decoder/upload/extraction API exists in the reviewed
  runtime. The upstream package advisory remains open; no vendor-fix claim is
  made for it.
- The actual image probe verifies the above absences and unloaded libraries,
  UID 10001, zero effective capabilities and `no_new_privileges`. The real
  container suite independently checks read-only root and full recovery.

These are scoped non-reachability decisions, not a zero-CVE image declaration.
They do not authorize public deployment, new subprocess/native-library routes,
untrusted code execution or different runtime privileges. Medium/low OS records
remain visible for reassessment with future vendor updates. This bounded scope
is sufficient only for the fictional local/cloud-CI demonstration candidate.

## Secret-scanner false positive, narrowly resolved

CI 34744445964 flagged `release-applicability.json` line 10 as `generic-api-key`.
The value is the SHA-256 of public `src/hestiarelay/access.py`, independently
recomputed from that file and checked by the release gate. It is not a credential.
`.gitleaksignore` records only the exact historical commit/path/rule/line
fingerprint. It does not suppress this file, hash patterns, later commits or any
actual secret. The original redacted finding remains in artifact 10313444442;
its downloaded archive and report manifest were verified before classification.
