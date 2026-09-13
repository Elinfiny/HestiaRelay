"""Bind scanner reports, installed package licenses and OS inventory to this checkout."""

import hashlib
import importlib.metadata
import json
import os
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

OUT = Path("qa-artifacts/release")


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
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
            "hestiarelay:judge",
            "dpkg-query",
            "-W",
            "-f=${Package}\t${Version}\t${Architecture}\n",
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
    report = {
        "schema": 1,
        "captured_utc": datetime.now(UTC).isoformat(),
        "source_commit": command("git", "rev-parse", "HEAD"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "git_commits_scanned": int(command("git", "rev-list", "--all", "--count")),
        "git_shallow": command("git", "rev-parse", "--is-shallow-repository"),
        "image_id": command(
            "docker", "image", "inspect", "hestiarelay:judge", "--format", "{{.Id}}"
        ),
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
        "aws_calls": 0,
        "public_deployment": False,
        "scope": "Known-advisory and secret scans, not proof of absence of vulnerabilities",
    }
    (OUT / "audit-result.json").write_text(json.dumps(report, indent=2) + "\n")
    files = {
        str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(OUT.rglob("*"))
        if p.is_file() and p.name != "sha256.json"
    }
    (OUT / "sha256.json").write_text(json.dumps(files, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    assert report["git_shallow"] == "false"
    assert all(v == 0 for v in statuses.values()), "Scanner failure or findings: review reports"
    assert not any(v.get("Severity") in {"HIGH", "CRITICAL"} for v in findings), (
        "High/critical image findings require review and targeted remediation"
    )


if __name__ == "__main__":
    main()
