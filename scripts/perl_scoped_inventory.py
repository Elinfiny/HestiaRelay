"""SOURCE_ONLY unit15. Future read-only scoped probe; never executed in unit15.

Use inside an independently admitted exact image with read-only application and
scripts mounts. Evidence output is an owned writable mount, not product storage.
No Perl execution, module imports, package changes, network, or expiry updates.
"""

import argparse
import contextlib
import hashlib
import json
import os
import re
import stat
import time
from pathlib import Path

import healthcheck_qualification as command_helper

EXPECTED = "5.40.1-6+deb13u1"
MAX_OWNED_ENTRIES = 1024
MAX_SELECTED_PATHS = 32
MAX_COMMANDS = 16
MAX_ORIGINAL_BYTES = 1024 * 1024
MAX_REPORT_BYTES = 1024 * 1024
MAX_FILE_BYTES = 1024 * 1024
MAX_SOURCE_FILES = 96
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_CALLSITES = 256
TOTAL_SECONDS = 30


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--image-id", required=True)
    args = ap.parse_args()
    args.output.mkdir(mode=0o700, exist_ok=False)
    start = time.monotonic()
    state = {"calls": [], "first_unknown": None, "retained_bytes": 0, "cleanup_issued": []}
    command_helper.MAX_ORIGINAL_BYTES = MAX_ORIGINAL_BYTES
    report = {
        "schema": "HESTIA_PERL_SCOPED_INVENTORY15_V1",
        "state": "UNKNOWN",
        "image_id_asserted_by_caller": args.image_id,
        "image_binding": "REQUIRES_EXTERNAL_PROVIDER_IMAGE_SOURCE_PROOF",
        "expected_perl_base": EXPECTED,
        "security_acceptance": False,
        "applicability_expiry_changed": False,
        "owned_enumeration_complete": False,
        "module_subscope_complete": False,
        "source_callsite_subscope_complete": False,
        "absence_scope": (
            "Only explicitly listed paths and selected source"
            " files at sample; no global filesystem or interp"
            "reter absence"
        ),
        "bounds": {
            "seconds": TOTAL_SECONDS,
            "dpkg_commands": MAX_COMMANDS,
            "original_bytes": MAX_ORIGINAL_BYTES,
            "report_bytes": MAX_REPORT_BYTES,
            "owned_entries": MAX_OWNED_ENTRIES,
            "selected_paths": MAX_SELECTED_PATHS,
            "source_files": MAX_SOURCE_FILES,
            "source_bytes": MAX_SOURCE_BYTES,
            "callsites": MAX_CALLSITES,
        },
    }

    def check():
        if state["first_unknown"] is not None or time.monotonic() - start >= TOTAL_SECONDS:
            raise ValueError("firstUNKNOWN_or_absolute_deadline; no next functional read/command")

    def command(label, argv):
        check()
        if len(state["calls"]) >= MAX_COMMANDS:
            raise ValueError("commandcount bound")
        return command_helper.bounded_command(
            label, argv, min(5, TOTAL_SECONDS - (time.monotonic() - start)), args.output, state
        )

    def read_regular(path, cap=MAX_FILE_BYTES):
        check()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as f:
            before = os.fstat(f.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
                raise ValueError("filetype/size bound")
            data = f.read(cap + 1)
            after = os.fstat(f.fileno())
        if len(data) != before.st_size or (
            before.st_ino,
            before.st_dev,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("changing_file/no_complete_claim")
        check()
        return data

    try:
        version = (
            command(
                "perl-package-version",
                ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Architecture}\n", "perl-base"],
            )
            .decode()
            .strip()
            .split("\t")
        )
        report["package_observed"] = version
        if len(version) != 3 or version[0] != "perl-base" or version[1] != EXPECTED:
            raise ValueError("package_identity_drift")
        raw = command("perl-owned-files", ["dpkg-query", "-L", "perl-base"])
        owned = raw.decode().splitlines()
        if len(owned) > MAX_OWNED_ENTRIES or any(
            not p.startswith("/") or len(p.encode()) > 512 or ".." in Path(p).parts for p in owned
        ):
            raise ValueError("owned_entry/path bound")
        report.update(
            owned_files=owned,
            owned_entries=len(owned),
            owned_list_sha256=sha(raw),
            owned_enumeration_complete=True,
        )
        # Explicit finite module paths, no recursive /usr or site-packages walks.
        roots = [
            "/usr/share/perl/5.40",
            "/usr/share/perl/5.40.1",
            "/usr/share/perl5",
            "/usr/lib/x86_64-linux-gnu/perl-base",
            "/usr/lib/x86_64-linux-gnu/perl/5.40.1",
            "/usr/lib/aarch64-linux-gnu/perl/5.40.1",
        ]
        suffixes = ["Pod/Text.pm", "Pod/Text/Termcap.pm", "Pod/Man.pm", "podlators.pm"]
        selected = sorted(
            {str(Path(root) / suffix) for root in roots for suffix in suffixes}
            | {p for p in owned if "/Pod/Text" in p or "podlators" in p.lower()}
        )
        if len(selected) > MAX_SELECTED_PATHS:
            raise ValueError("selected_path bound")
        modules = []
        owner_versions = {}
        for name in selected:
            check()
            path = Path(name)
            try:
                mode = path.lstat().st_mode
            except FileNotFoundError:
                modules.append({"path": name, "state": "ABSENT_EXPLICIT_PATH_AT_SAMPLE"})
                continue
            if not stat.S_ISREG(mode):
                modules.append({"path": name, "state": "NONREGULAR_UNRESOLVED"})
                continue
            data = read_regular(path)
            owner = (
                command("module-owner-" + str(len(modules)), ["dpkg-query", "-S", name])
                .decode()
                .splitlines()
            )
            for owner_line in owner:
                package = owner_line.rsplit(": ", 1)[0]
                if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9]+)?", package):
                    raise ValueError("ambiguous module package owner")
                if package not in owner_versions:
                    owner_versions[package] = (
                        command(
                            "module-owner-version-" + str(len(owner_versions)),
                            [
                                "dpkg-query",
                                "-W",
                                "-f=${binary:Package}\t${Version}\t${Architecture}\n",
                                package,
                            ],
                        )
                        .decode()
                        .splitlines()
                    )
            versions = re.findall(rb"(?:our\s+)?\$VERSION\s*=\s*[\x27\x22]([^\x27\x22]+)", data)
            modules.append(
                {
                    "path": name,
                    "state": "PRESENT_READONLY_HASHED",
                    "bytes": len(data),
                    "sha256": sha(data),
                    "dpkg_ownership_original": owner,
                    "version_literals": [v.decode("ascii", errors="strict") for v in versions],
                    "version_literal_is_not_vendor_fixed_status": True,
                }
            )
        report["modules"] = modules
        report["module_owner_package_versions"] = owner_versions
        report["module_subscope_complete"] = True
        source = args.source
        chosen = [source / "Dockerfile", source / "requirements-runtime.txt"] + [
            source / p
            for p in [
                "scripts/container_qa.py",
                "scripts/release_audit.sh",
                "scripts/release_inventory.py",
                "scripts/run_cloud_proof.sh",
            ]
        ]
        for path in (source / "src/hestiarelay").glob("*.py"):
            check()
            chosen.append(path)
            if len(chosen) > MAX_SOURCE_FILES:
                raise ValueError("source_filecount bound")
        chosen = sorted(chosen)
        if len(chosen) > MAX_SOURCE_FILES:
            raise ValueError("source_filecount bound")
        source_rows, callsites, used = [], [], 0
        pattern = re.compile(
            r"(?i)perl|pod2|pod::|podlators|subprocess|Popen|os\.(?:system|popen|exec)"
        )
        for path in chosen:
            data = read_regular(path, MAX_SOURCE_BYTES - used)
            used += len(data)
            rel = path.relative_to(source).as_posix()
            source_rows.append({"path": rel, "bytes": len(data), "sha256": sha(data)})
            for number, line in enumerate(data.decode().splitlines(), 1):
                if pattern.search(line):
                    if len(callsites) >= MAX_CALLSITES or len(line.encode()) > 512:
                        raise ValueError("callsite/output bound; no truncated completeness")
                    callsites.append({"path": rel, "line": number, "text": line})
        report.update(
            source_files=source_rows,
            source_callsites=callsites,
            source_callsite_subscope_complete=True,
            state="COMPLETE_SUBSCOPES_AT_SAMPLE_NOT_SECURITY_ACCEPTANCE",
        )
        check()
    except Exception as error:
        report.update(
            state="UNKNOWN",
            error={"type": type(error).__name__, "message": str(error)},
            first_unknown=state["first_unknown"],
        )
    report["command_receipts"] = state["calls"]
    report["observed_seconds"] = time.monotonic() - start
    encoded = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    if len(encoded) > MAX_REPORT_BYTES:
        report["state"] = "UNKNOWN"
        encoded = (
            json.dumps(
                {
                    "state": "UNKNOWN",
                    "reason": "metadata_bound_no_complete_export",
                    "originals_runner_local": True,
                    "security_acceptance": False,
                }
            )
            + "\n"
        ).encode()
    with (args.output / "PERL_SCOPED_INVENTORY.json").open("xb") as f:
        f.write(encoded)
        f.flush()
        os.fsync(f.fileno())
    if time.monotonic() - start >= TOTAL_SECONDS:
        report["state"] = "UNKNOWN"
        with contextlib.suppress(Exception):
            command_helper.write(
                args.output / "PERL_FINAL_CLOSEOUT.json",
                {
                    "state": "UNKNOWN",
                    "reason": "final_persist_return_late",
                    "original_report_unchanged": True,
                    "security_acceptance": False,
                },
            )
    print(
        json.dumps(
            {
                "state": report["state"],
                "security_acceptance": False,
                "report_sha256": sha(encoded),
                "final_postpersist_seconds": time.monotonic() - start,
            }
        )
    )
    return 0 if report["state"].startswith("COMPLETE_SUBSCOPES") else 2


if __name__ == "__main__":
    raise SystemExit(main())
