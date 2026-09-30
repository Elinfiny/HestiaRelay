"""Bind scanner reports, installed package licenses and OS inventory to this checkout."""

import hashlib
import importlib.metadata
import json
import os
import subprocess
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


def main():
    # A previous attempt is evidence, never reusable input or current success.
    outputs = [
        "public-judge-path.json", "build-packages.json", "os-packages.tsv",
        "upstream-notices.json", "runtime-surface.json", "evidence-binding.json",
        "applicability.json", "audit-result.json", "sha256.json",
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
    ]
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
    assert all(v == 0 for v in statuses.values()), "Scanner failure or findings: review reports"
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
    main()
