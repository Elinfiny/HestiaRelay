"""Bind scanner reports, installed package licenses and OS inventory to this checkout."""

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from release_review import review_findings

OUT = Path("qa-artifacts/release")


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def write_evidence(path, value):
    data = (json.dumps(value, indent=2) + "\n").encode()
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    assert path.read_bytes() == data, "Evidence readback mismatch"


# Auditor V28 direction06: these public inputs and these exact redacted findings only.
NPM_INPUT_SHA256 = {
    "tools/inspector/package.json":
        "b47d1d4dd8226a3ffe73eab9eec3018c20376da82845c8017309ffcdc5df6249",
    "tools/inspector/package-lock.json":
        "a99ecfb538177004d7c794fc1efd5d1aa6667750a7aa89c80d0a15c9e580f9e1",
    "qa-artifacts/inspector-package-lock.json":
        "a99ecfb538177004d7c794fc1efd5d1aa6667750a7aa89c80d0a15c9e580f9e1",
}
INSPECTOR_IDENTITY = {
    "version": "2.9.0",
    "package_name": "@modelcontextprotocol/inspector",
    "manifest_sha256": "aa417adfb4f8e75722ac551a6f79da421beef8bfd69b7cc4aaa3e19e84d80e7e",
    "entry_sha256": "21ca6e6e031713e5ae040ecf71f8fd0b0ef9a4ece4131fd03d3b01aeae5415f4",
}
PUBLIC_ACCESS_SHA256 = "22f9f84189c9999d1b365c682ce86a096758676ff6019f84b59cf41c38b954a9"
NATIVE_MEMBER = "qa-artifacts/native-surface-observation.json"
# Full reviewed finding metadata, including coordinates; changed/new matches get no waiver.
REVIEWED_ARTIFACT_FINDING = {
    "RuleID": "generic-api-key",
    "Description": "Detected a Generic API Key, potentially exposing access to various services "
                   "and sensitive operations.",
    "StartLine": 1, "EndLine": 1, "StartColumn": 55791, "EndColumn": 55867,
    "Match": 'access.py":"REDACTED"', "Secret": "REDACTED",
    "File": NATIVE_MEMBER, "SymlinkFile": "", "Commit": "", "Entropy": 3.7189703,
    "Author": "", "Email": "", "Date": "", "Message": "", "Tags": [],
    "Fingerprint": NATIVE_MEMBER + ":generic-api-key:1",
}


def unique_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON member")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


def inspector_audit_identity():
    root = Path("tools/inspector/node_modules/@modelcontextprotocol/inspector")
    manifest = (root / "package.json").read_bytes()
    package = unique_json(manifest)
    entry = (root / package["bin"]["mcp-inspector"]).resolve(strict=True)
    assert entry == Path(
        "tools/inspector/node_modules/.bin/mcp-inspector"
    ).resolve(strict=True)
    identity = {
        "version": package["version"], "package_name": package["name"],
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "entry_sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
    }
    return identity


def capture_npm_binding():
    report = {
        "schema": 1, "status": "BLOCK",
        "source_commit": command("git", "rev-parse", "HEAD"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "prefix": "tools/inspector",
    }
    try:
        hashes = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                  for name in NPM_INPUT_SHA256}
        report["input_sha256"] = hashes
        assert hashes == NPM_INPUT_SHA256
        identity = inspector_audit_identity()
        report["installed_inspector"] = identity
        assert identity == INSPECTOR_IDENTITY
        report["status"] = "PASS"
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        report["error_type"] = type(error).__name__
    write_evidence(OUT / "npm-audit-binding.json", report)
    assert report["status"] == "PASS", "Inspector audit input binding failed"


def verify_npm_binding(report, attempt, container, audit, capture_status):
    assert capture_status == 0 and report["status"] == "PASS", "NPM input binding failed"
    assert report["prefix"] == "tools/inspector"
    assert report["input_sha256"] == NPM_INPUT_SHA256
    assert all(hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
               for name, digest in NPM_INPUT_SHA256.items()), "NPM lock/source drift"
    assert report["installed_inspector"] == INSPECTOR_IDENTITY
    assert inspector_audit_identity() == report["installed_inspector"], "Installed CLI drift"
    assert all(container["mcp_inspector"].get(k) == v for k, v in INSPECTOR_IDENTITY.items())
    assert all(report[k] == attempt[k] for k in ("source_commit", "run_id", "run_attempt"))
    assert isinstance(audit, dict) and "error" not in audit, "NPM scan error"
    counts = audit["metadata"]["vulnerabilities"]
    assert set(counts) == {"info", "low", "moderate", "high", "critical", "total"}
    assert all(type(v) is int and v == 0 for v in counts.values()), "NPM findings"
    assert audit["vulnerabilities"] == {}, "NPM findings"


def classify_artifact_findings(raw_report, scanner_status, raw_member, public_source, binding,
                               container):
    """Pure exact disposition; raw status/report stay unchanged, all drift fails closed."""
    result = {"schema": 1, "raw_scanner_status": scanner_status, "blocking": True,
              "decision": "BLOCK", "accepted_count": 0, "universal_secret_absence": False,
              "raw_report_sha256": hashlib.sha256(raw_report).hexdigest()}
    try:
        findings = unique_json(raw_report)
        assert type(scanner_status) is int and scanner_status in (0, 1), "Scanner error status"
        assert isinstance(findings, list), "Malformed report"
        if scanner_status == 0:
            assert findings == [], "Finding with clean exit"
            result.update(blocking=False, decision="NO_FINDINGS_IN_THIS_REPORT")
            return result
        assert findings == [REVIEWED_ARTIFACT_FINDING], "New or changed finding"
        text = raw_member.decode("ascii")
        assert len(raw_member) <= 1048576 and len(text.splitlines()) == 1, "Member bounds"
        native = unique_json(raw_member)
        assert native["schema"] == "HESTIA_NATIVE_SURFACE_OBSERVATION_V1", "Member schema"
        source_sha = hashlib.sha256(public_source).hexdigest()
        assert source_sha == PUBLIC_ACCESS_SHA256, "Public source drift"
        field = '"/app/src/hestiarelay/access.py":"' + source_sha + '"'
        start, end = findings[0]["StartColumn"] - 1, findings[0]["EndColumn"]
        assert 0 <= start < end <= len(text.splitlines()[0]), "Column bounds"
        assert text[start:end] == 'access.py":"' + source_sha + '"', "Slice drift"
        assert text.count(field) == 1, "Ambiguous member"
        assert text.index(field) + len('"/app/src/hestiarelay/') == start, "Field drift"
        # Require this token in the actual image_source_sha256 object, not a lookalike field.
        encoded_map = json.dumps(native["image_source_sha256"], sort_keys=True,
                                 separators=(",", ":"))
        marker = '"image_source_sha256":' + encoded_map
        assert text.count(marker) == 1 and field in encoded_map, "Map serialization drift"
        offset = text.index(marker)
        assert offset <= start < end <= offset + len(marker), "Wrong JSON field"
        assert native["image_source_sha256"]["/app/src/hestiarelay/access.py"] == source_sha
        assert binding["source_sha256"]["src/hestiarelay/access.py"] == source_sha
        assert binding["image_id"] == binding["scanner_image_id"] == container["image_id"]
        assert container["source_commit"] == binding["source_commit"], "Container source drift"
        for key in ("source_commit", "run_id", "run_attempt", "image_id"):
            assert isinstance(binding[key], str) and binding[key], "Missing binding"
            assert native["binding"][key] == binding[key], "Native binding drift"
        assert native["binding"]["primary_qa_error"] is None, "Primary QA error"
        assert native["binding"]["probe_sha256"] == (
            "642530112b7fdfc79689d06509be8623b2a25b22874577de10ebffed8383cdfa"
        ), "Probe drift"
        assert native["binding"]["source_sha256"]["tools/inspector/package-lock.json"] == (
            NPM_INPUT_SHA256["tools/inspector/package-lock.json"]
        ), "Inspector lock drift"
        assert native["image_runtime_lock_sha256"] == container["dependency_lock_sha256"]
        result.update(
            blocking=False, decision="NONSECRET_PUBLIC_SOURCE_SHA256_EXACT_REVIEW",
            accepted_count=1, fingerprint=findings[0]["Fingerprint"],
            source_sha256=source_sha, member_sha256=hashlib.sha256(raw_member).hexdigest(),
            source_commit=binding["source_commit"], run_id=binding["run_id"],
            run_attempt=binding["run_attempt"], image_id=binding["image_id"],
            native_reachability="NOT_DECIDED",
        )
    except (ValueError, KeyError, TypeError, AssertionError, UnicodeError, IndexError) as error:
        result["refusal_type"] = type(error).__name__
    return result



def main():
    # A previous attempt is evidence, never reusable input or current success.
    outputs = [
        "public-judge-path.json", "build-packages.json", "os-packages.tsv",
        "upstream-notices.json", "runtime-surface.json", "evidence-binding.json",
        "applicability.json", "audit-result.json", "sha256.json", "secret-dispositions.json",
    ]
    assert not any(os.path.lexists(OUT / name) for name in outputs), "Stale inventory output"
    attempt = {
        "schema": 1,
        "captured_utc": datetime.now(UTC).isoformat(),
        "source_commit": command("git", "rev-parse", "HEAD"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "evaluation": "NOT_EVALUATED",
    }
    write_evidence(OUT / "inventory-attempt.json", attempt)
    image_id = command("docker", "image", "inspect", "hestiarelay:judge", "--format", "{{.Id}}")
    # Anonymous HTTP reads: no connector token, cookies or signed-in browser.
    public_reads = []
    for target in [
        "https://github.com/Elinfiny/HestiaRelay",
        "https://raw.githubusercontent.com/Elinfiny/HestiaRelay/main/README.md",
        "https://raw.githubusercontent.com/Elinfiny/HestiaRelay/main/LICENSE",
    ]:
        with urllib.request.urlopen(target, timeout=30) as response:
            body = response.read()
            assert response.status == 200
            assert b"HestiaRelay" in body or b"MIT License" in body
            public_reads.append(
                {
                    "url": target,
                    "status": response.status,
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "authentication": "none",
                }
            )
    (OUT / "public-judge-path.json").write_text(json.dumps(public_reads, indent=2) + "\n")
    packages = []
    for package in importlib.metadata.distributions():
        metadata = package.metadata
        packages.append(
            {
                "name": metadata["Name"],
                "version": package.version,
                "license_expression": metadata.get("License-Expression"),
                "license": metadata.get("License"),
                "license_classifiers": [
                    v for v in metadata.get_all("Classifier", []) if v.startswith("License ::")
                ],
                "requires_dist": metadata.get_all("Requires-Dist", []),
            }
        )
    (OUT / "build-packages.json").write_text(json.dumps(packages, indent=2) + "\n")
    (OUT / "os-packages.tsv").write_text(
        command(
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            image_id,
            "dpkg-query",
            "-W",
            "-f=${Package}\t${Version}\t${Architecture}\n",
        )
        + "\n"
    )
    # Preserve upstream notices, including symlinked Debian copyright files which
    # package-level SBOM license inference can miss. No credentials exist in the image.
    notice_code = """
import hashlib, importlib.metadata, json
from pathlib import Path
paths = list(Path('/usr/share/doc').glob('*/copyright'))
paths += list(Path('/usr/share/common-licenses').glob('*'))
paths += [Path('/usr/local/lib/python3.12/LICENSE.txt')]
for package in importlib.metadata.distributions():
    for file in package.files or []:
        if any(word in str(file).lower() for word in ['license', 'notice', 'copying']):
            paths.append(Path(package.locate_file(file)))
notices = {}
for path in paths:
    if path.is_file() and path.stat().st_size < 2000000:
        data = path.read_bytes()
        notices[str(path)] = {'sha256': hashlib.sha256(data).hexdigest(),
                             'text': data.decode('utf-8', errors='replace')}
print(json.dumps(notices, indent=2))
"""
    (OUT / "upstream-notices.json").write_text(
        command(
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            image_id,
            "python",
            "-c",
            notice_code,
        )
        + "\n"
    )
    statuses = dict(
        zip(
            [
                "history_secrets",
                "artifact_secrets",
                "python_advisories",
                "build_advisories",
                "source_static_analysis",
                "npm_advisories",
                "image_scan",
                "sbom",
            ],
            map(int, os.environ["HESTIA_SCAN_STATUSES"].split()),
            strict=True,
        )
    )
    image = json.loads((OUT / "image-advisories.json").read_text())
    findings = [v for r in image.get("Results", []) for v in r.get("Vulnerabilities", [])]
    surface_code = """
import importlib.util, json, os, platform, shutil
from pathlib import Path
import hestiarelay.server
maps = Path('/proc/self/maps').read_text()
status = Path('/proc/self/status').read_text()
print(json.dumps({
 'machine': platform.machine(),
 'perl_entrypoints': sorted(str(p) for p in Path('/usr/bin').glob('perl*')),
 'pod_text_modules': sorted(str(p) for base in ['/usr/share', '/usr/lib']
     for p in Path(base).glob('perl*/**/Pod/Text.pm')),
 'pcre2_loaded': 'libpcre2' in maps,
 'pcre2grep_path': shutil.which('pcre2grep'),
 'uid': os.getuid(), 'mount_absent': shutil.which('mount') is None,
 'nsenter_absent': shutil.which('nsenter') is None,
 'infocmp_absent': shutil.which('infocmp') is None,
 'perl_absent': shutil.which('perl') is None,
 'homed_absent': not Path('/usr/lib/systemd/systemd-homed').exists(),
 'lzma_binding_absent': importlib.util.find_spec('_lzma') is None,
 'privileged_libraries_unloaded': not any(
     s in maps for s in ['libacl.', 'libsystemd.', 'libudev.', 'liblzma.']),
 'capabilities_zero': 'CapEff:\t0000000000000000' in status,
 'no_new_privileges': 'NoNewPrivs:\t1' in status,
}))
"""
    surface = json.loads(
        command(
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--tmpfs",
            "/data:uid=10001,gid=10001",
            image_id,
            "python",
            "-c",
            surface_code,
        )
    )
    container_result = json.loads(Path("qa-artifacts/container-qa.json").read_text())
    review = json.loads(Path("docs/evidence/release-applicability.json").read_text())
    source_hashes = {
        name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
        for name in review["source_sha256"]
    }
    write_evidence(OUT / "runtime-surface.json", surface)
    inputs = [
        OUT / "image-advisories.json", OUT / "scanner-version.json",
        OUT / "os-packages.tsv", OUT / "runtime-surface.json",
        Path("qa-artifacts/container-qa.json"), Path("docs/evidence/release-applicability.json"),
        Path(__file__), Path(__file__).with_name("release_review.py"),
        OUT / "artifact-secrets.json", OUT / "npm-advisories.json",
        OUT / "npm-audit-binding.json",
    ]
    if statuses["artifact_secrets"] == 1:
        inputs.extend([Path(NATIVE_MEMBER), Path("src/hestiarelay/access.py")])
    binding = {
        **attempt,
        "image_id": image_id,
        "scanner_image_id": image["Metadata"]["ImageID"],
        "scanner": json.loads((OUT / "scanner-version.json").read_text()),
        "scanner_exit_codes": statuses,
        "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        "source_sha256": source_hashes,
        "runtime_probe_sha256": hashlib.sha256(surface_code.encode()).hexdigest(),
    }
    write_evidence(OUT / "evidence-binding.json", binding)
    # Persist an exact, separate disposition before any applicability/readiness gate.
    # Error exits, malformed/new findings and missing inputs can never become nonsecret.
    raw_artifact = (OUT / "artifact-secrets.json").read_bytes()
    disposition = classify_artifact_findings(
        raw_artifact, statuses["artifact_secrets"],
        Path(NATIVE_MEMBER).read_bytes() if statuses["artifact_secrets"] == 1 else b"",
        Path("src/hestiarelay/access.py").read_bytes()
        if statuses["artifact_secrets"] == 1 else b"",
        binding, container_result,
    )
    write_evidence(OUT / "secret-dispositions.json", disposition)
    npm_binding = unique_json((OUT / "npm-audit-binding.json").read_bytes())
    npm_report = unique_json((OUT / "npm-advisories.json").read_bytes())
    verify_npm_binding(npm_binding, attempt, container_result, npm_report,
                       int(os.environ["HESTIA_NPM_BINDING_STATUS"]))
    assert container_result["status"] == "PASS"
    assert container_result["container_backup_restore"] == "PASS"
    assert container_result["image_id"] == image_id == binding["scanner_image_id"]
    applicability = review_findings(findings, review, surface, source_hashes)
    report = {
        "schema": 1,
        "captured_utc": datetime.now(UTC).isoformat(),
        "source_commit": attempt["source_commit"],
        "run_id": attempt["run_id"],
        "git_commits_scanned": int(command("git", "rev-list", "--all", "--count")),
        "git_shallow": command("git", "rev-parse", "--is-shallow-repository"),
        "image_id": image_id,
        "exit_codes": statuses,
        "artifact_secret_disposition": disposition,
        "npm_audit_binding": npm_binding,
        "image_findings": [
            {
                k: v.get(k)
                for k in (
                    "VulnerabilityID",
                    "PkgName",
                    "InstalledVersion",
                    "FixedVersion",
                    "Severity",
                    "Status",
                    "PrimaryURL",
                    "DataSource",
                )
            }
            for v in findings
        ],
        "scoped_applicability": applicability,
        "aws_calls": 0,
        "public_deployment": False,
        "scope": "Known-advisory and secret scans, not proof of absence of vulnerabilities",
    }
    assert report["git_shallow"] == "false"
    # Only the independently reviewed artifact finding may have raw exit1.
    # Every other scanner still requires exit0; a disposition never rewrites raw status.
    assert not disposition["blocking"], "Artifact scanner error or unreviewed finding"
    assert all(v == 0 for k, v in statuses.items() if k != "artifact_secrets"), (
        "Scanner failure or findings: review reports"
    )
    assert not applicability["blocking_findings"], "Unresolved material image findings"
    write_evidence(OUT / "applicability.json", applicability)
    (OUT / "audit-result.json").write_text(json.dumps(report, indent=2) + "\n")
    files = {
        str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(OUT.rglob("*"))
        if p.is_file() and p.name != "sha256.json"
    }
    (OUT / "sha256.json").write_text(json.dumps(files, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["--npm-audit-binding"]:
        capture_npm_binding()
    else:
        assert len(sys.argv) == 1, "Unsupported collector argument"
        main()
