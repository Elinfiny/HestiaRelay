import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from hestiarelay.aws_probe import run_probe
from hestiarelay.cloud_probe import execute, main, validate_gate, verify_identity

COMMIT = "a" * 40
ROLE = "arn:aws:iam::123456789012:role/hestia-proof"
ENV = {
    "HESTIA_EXECUTION_APPROVED": "YES",
    "HESTIA_SOURCE_COMMIT": COMMIT,
    "HESTIA_REQUEST_SHA256": "b" * 64,
    "HESTIA_PROJECT_NAME": "hestia-proof",
    "CODEBUILD_BUILD_ID": "hestia-proof:fixture",
    "HESTIA_ROLE_ARN": ROLE,
}
IDENTITY = {
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/hestia-proof/build",
}


@pytest.mark.parametrize(
    "changes",
    [
        {"HESTIA_EXECUTION_APPROVED": "NO"},
        {"HESTIA_SOURCE_COMMIT": "c" * 40},
        {"HESTIA_SOURCE_COMMIT": "main"},
        {"HESTIA_REQUEST_SHA256": ""},
        {"CODEBUILD_BUILD_ID": "other-project:fixture"},
        {"HESTIA_ROLE_ARN": "arn:aws:iam::123456789012:root"},
    ],
)
def test_invalid_gate_rejects_before_aws(changes):
    with pytest.raises(ValueError):
        validate_gate(ENV | changes, COMMIT)


def test_valid_gate_and_identity():
    validate_gate(ENV, COMMIT)
    verify_identity(ROLE, IDENTITY)


@pytest.mark.parametrize(
    "identity",
    [
        {"Account": "000000000000", "Arn": IDENTITY["Arn"]},
        {"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:root"},
        {"Account": "123456789012", "Arn": "arn:aws:sts::123456789012:assumed-role/other/build"},
    ],
)
def test_other_identity_cannot_invoke(identity):
    with pytest.raises(ValueError, match="identity_mismatch"):
        verify_identity(ROLE, identity)


def test_default_execution_cannot_construct_client(monkeypatch, capsys):
    def forbidden(*a, **kw):
        raise AssertionError("No AWS client before approval")

    monkeypatch.delenv("HESTIA_EXECUTION_APPROVED", raising=False)
    monkeypatch.setattr("hestiarelay.cloud_probe.boto3.client", forbidden)
    assert main() == 2
    assert '"status": "BLOCKED"' in capsys.readouterr().out


def test_managed_execution_and_repeated_attempt_guard(monkeypatch, tmp_path):
    class Sts:
        def get_caller_identity(self):
            return IDENTITY

    calls = []
    monkeypatch.setattr("hestiarelay.cloud_probe.boto3.client", lambda *a, **kw: Sts())
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: COMMIT)
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: None)

    def probe(**kwargs):
        calls.append(kwargs)
        return {"status": "LIVE_CALL_PASS"}

    monkeypatch.setattr("hestiarelay.cloud_probe.run_probe", probe)
    marker = tmp_path / "attempt"
    report = execute(ENV, marker)
    assert report["source_commit"] == COMMIT
    assert report["dedicated_role_verified"] is True
    assert calls[0]["expected_request_sha256"] == ENV["HESTIA_REQUEST_SHA256"]
    with pytest.raises(FileExistsError):
        execute(ENV, marker)
    assert len(calls) == 1


def test_request_is_repeatable_and_wrong_hash_never_calls_transport():
    class Capture:
        calls = 0

        def converse(self, **kwargs):
            self.calls += 1
            self.request = kwargs
            return {
                "output": {"message": {"content": [{"text": "Fictional reviewed plan."}]}},
                "usage": {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
                "stopReason": "end_turn",
            }

    first, second = Capture(), Capture()
    a = run_probe(live=True, approved=True, model_id="amazon.nova-micro-v1:0", client=first)
    b = run_probe(
        live=True,
        approved=True,
        model_id="amazon.nova-micro-v1:0",
        client=second,
        expected_request_sha256=a["request_sha256"],
        include_response=True,
    )
    assert first.request == second.request
    reviewed = json.loads(Path("infra/bedrock-proof-request.json").read_text())
    assert first.request == reviewed
    assert b["request_sha256"] == a["request_sha256"]
    assert "response_text" not in a
    assert hashlib.sha256(b["response_text"].encode()).hexdigest() == b["response_text_sha256"]
    assert b["status"] == "MOCK_PASS" and b["live_aws_validated"] is False
    rejected = Capture()
    c = run_probe(
        live=True,
        approved=True,
        model_id="amazon.nova-micro-v1:0",
        client=rejected,
        expected_request_sha256="0" * 64,
        include_response=True,
    )
    assert c["status"] == "BLOCKED" and rejected.calls == c["converse_calls"] == 0
    assert "response_text" not in c
    assert "Fictional reviewed plan" not in json.dumps(c)
