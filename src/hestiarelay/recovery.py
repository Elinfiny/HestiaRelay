"""Consistent, verified SQLite snapshots into new owner-only destinations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from hestiarelay.models import HouseholdState


def validate(connection):
    connection.execute("PRAGMA trusted_schema=OFF")
    if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise ValueError("Database integrity check failed")
    schema = connection.execute(
        "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
    ).fetchall()
    if schema != [("table", "household_state")]:
        raise ValueError("Unexpected household database schema")
    rows = connection.execute("SELECT singleton, state_json FROM household_state").fetchall()
    if len(rows) != 1 or rows[0][0] != 1:
        raise ValueError("Backup requires exactly one saved household state")
    state = HouseholdState.model_validate_json(rows[0][1])
    return hashlib.sha256(state.model_dump_json().encode()).hexdigest()


def snapshot(source: Path, destination: Path, *, expected_sha256: str | None = None):
    """Never overwrite; the caller retains the receipt outside the state directory."""
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Source must be an existing regular database of at most 64 MiB")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Destination already exists; choose a new path")
    verified_bytes = None
    if expected_sha256 is not None:
        verified_bytes = source.read_bytes()
        if hashlib.sha256(verified_bytes).hexdigest() != expected_sha256:
            raise ValueError("Backup SHA-256 does not match the selected receipt")
    fd, temporary = tempfile.mkstemp(prefix=".hestia-snapshot-", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary)
    restored_input = None
    try:
        if verified_bytes is not None:
            fd, name = tempfile.mkstemp(prefix=".hestia-verified-", dir=destination.parent)
            restored_input = Path(name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(verified_bytes)
            # Open exactly the verified bytes, never an unverified WAL or changed source.
            source = restored_input
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as src:
            src.execute("BEGIN")
            state_digest = validate(src)
            with closing(sqlite3.connect(temporary)) as out:
                src.backup(out)
                if validate(out) != state_digest:
                    raise ValueError("Snapshot state does not match its source transaction")
        data = temporary.read_bytes()
        receipt = {
            "status": "PASS",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "state_sha256": state_digest,
            "integrity_check": "PASS",
            "overwrite": False,
            "encrypted": False,
            "remote_copy": False,
        }
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        # Hard-link promotion is atomic create-if-absent, including destination races.
        os.link(temporary, destination)
        directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return receipt
    finally:
        temporary.unlink(missing_ok=True)
        if restored_input is not None:
            restored_input.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["backup", "restore"])
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--sha256", help="Required for restore: selected backup receipt digest")
    args = parser.parse_args()
    if args.operation == "restore" and not args.sha256:
        parser.error("restore requires --sha256 from the selected backup receipt")
    try:
        result = snapshot(args.source, args.destination, expected_sha256=args.sha256)
    except (OSError, ValueError, sqlite3.Error):
        parser.exit(1, "Recovery failed; source preserved. Check paths, receipt and database.\n")
    print(json.dumps({"operation": args.operation, **result}, indent=2))


if __name__ == "__main__":
    main()
