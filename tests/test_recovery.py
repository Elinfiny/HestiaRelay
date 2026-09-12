"""Restore into a new database and prove the domain state, not just file hashes."""

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from test_simulator import make_service, send

from hestiarelay.recovery import snapshot
from hestiarelay.service import CANONICAL_MESSAGES


def seeded(path):
    service = make_service(path)
    for text in CANONICAL_MESSAGES:
        send(service, text)
    first = service.snapshot()["state"]["proposals"][0]
    service.decide(action_id=first["action_id"], approved=True)
    send(service, "Remember Lee is vegetarian.")
    send(service, CANONICAL_MESSAGES[2])
    pending = next(p for p in service.snapshot()["state"]["proposals"] if p["status"] == "pending")
    service.decide(action_id=pending["action_id"], approved=False)
    return service


def test_consistent_backup_and_verified_restore_preserve_complete_state(tmp_path):
    source, backup, restored = [tmp_path / n for n in ("source.db", "backup.db", "restored.db")]
    service = seeded(source)
    before = service.snapshot()
    original_bytes = source.read_bytes()
    receipt = snapshot(source, backup)
    assert receipt["sha256"] == hashlib.sha256(backup.read_bytes()).hexdigest()
    assert backup.stat().st_mode & 0o777 == 0o600
    restored_receipt = snapshot(backup, restored, expected_sha256=receipt["sha256"])
    assert restored_receipt["state_sha256"] == receipt["state_sha256"]
    assert source.read_bytes() == original_bytes
    assert make_service(restored).snapshot() == before
    assert {p["status"] for p in before["state"]["proposals"]} == {"approved", "rejected"}
    assert all(p["execution"] == "not_executed" for p in before["state"]["proposals"])
    assert not list(tmp_path.glob(".hestia-*"))


def test_live_wal_committed_state_is_backed_up(tmp_path):
    source, backup = tmp_path / "wal.db", tmp_path / "backup.db"
    service = seeded(source)
    with sqlite3.connect(source) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        send(service, "Remember Mia is vegetarian.")
        before = service.snapshot()
        writer.execute("UPDATE household_state SET state_json=state_json")
        writer.commit()
        assert Path(str(source) + "-wal").exists()
        snapshot(source, backup)
    assert make_service(backup).snapshot() == before


@pytest.mark.parametrize(
    "kind",
    ["missing", "directory", "symlink", "corrupt", "empty", "other_schema", "invalid_json", "view"],
)
def test_invalid_sources_fail_without_creating_destination(tmp_path, kind):
    source, destination = tmp_path / "source.db", tmp_path / "restored.db"
    if kind == "directory":
        source.mkdir()
    elif kind == "symlink":
        source.symlink_to(tmp_path / "missing.db")
    elif kind == "corrupt":
        source.write_bytes(b"not a sqlite database")
    elif kind in {"empty", "other_schema", "invalid_json", "view"}:
        with sqlite3.connect(source) as c:
            c.execute("CREATE TABLE household_state(singleton INTEGER, state_json TEXT)")
            if kind == "other_schema":
                c.execute("CREATE TABLE secret(value TEXT)")
            if kind == "invalid_json":
                c.execute("INSERT INTO household_state VALUES(1, 'not json')")
            if kind == "view":
                c.execute("DROP TABLE household_state")
                c.execute(
                    "CREATE VIEW household_state AS SELECT 1 AS singleton, '{}' AS state_json"
                )
    with pytest.raises((ValueError, sqlite3.Error)):
        snapshot(source, destination)
    assert not destination.exists()
    assert not list(tmp_path.glob(".hestia-*"))


def test_refuse_overwrite_wrong_digest_and_destination_race(tmp_path, monkeypatch):
    import hestiarelay.recovery as recovery

    source, destination = tmp_path / "source.db", tmp_path / "restore.db"
    seeded(source)
    destination.write_bytes(b"preserve me")
    with pytest.raises(FileExistsError):
        snapshot(source, destination)
    assert destination.read_bytes() == b"preserve me"
    with pytest.raises(ValueError, match="SHA-256"):
        snapshot(source, tmp_path / "wrong.db", expected_sha256="0" * 64)
    target = tmp_path / "raced.db"
    original = recovery.os.link

    def race(src, dst):
        target.write_bytes(b"concurrent owner")
        original(src, dst)

    monkeypatch.setattr(recovery.os, "link", race)
    with pytest.raises(FileExistsError):
        snapshot(source, target)
    assert target.read_bytes() == b"concurrent owner"
    assert not list(tmp_path.glob(".hestia-*"))


def test_restore_uses_exact_verified_bytes_despite_source_change(tmp_path, monkeypatch):
    import hestiarelay.recovery as recovery

    source, backup, restored = [tmp_path / n for n in ("source.db", "backup.db", "restore.db")]
    before = seeded(source).snapshot()
    receipt = snapshot(source, backup)
    original = recovery.tempfile.mkstemp

    def mutate_after_hash(*args, **kwargs):
        backup.write_bytes(b"source replaced after verification")
        return original(*args, **kwargs)

    monkeypatch.setattr(recovery.tempfile, "mkstemp", mutate_after_hash)
    snapshot(backup, restored, expected_sha256=receipt["sha256"])
    assert make_service(restored).snapshot() == before


def test_cli_backup_restore_and_failure_messages(tmp_path):
    source, backup, restored = [tmp_path / n for n in ("source.db", "backup.db", "restore.db")]
    before = seeded(source).snapshot()
    command = [sys.executable, "-m", "hestiarelay.recovery"]
    r = subprocess.run(
        command + ["backup", str(source), str(backup)], capture_output=True, text=True
    )
    assert r.returncode == 0
    receipt = json.loads(r.stdout)
    r = subprocess.run(
        command + ["restore", str(backup), str(restored), "--sha256", receipt["sha256"]],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0 and make_service(restored).snapshot() == before
    r = subprocess.run(
        command + ["restore", str(backup), str(restored)], capture_output=True, text=True
    )
    assert r.returncode != 0 and "requires --sha256" in r.stderr
    r = subprocess.run(
        command + ["backup", str(source), str(backup)], capture_output=True, text=True
    )
    assert r.returncode == 1 and "source preserved" in r.stderr
