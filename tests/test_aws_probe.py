import hashlib
import json
from datetime import datetime

import pytest
from botocore.exceptions import NoCredentialsError

from hestiarelay.aws_probe import ObservedClient, main, run_probe


class FakeClient:
    def converse(self, **kwargs):
        assert kwargs["inferenceConfig"]["maxTokens"] == 600
        return {
            "output": {"message": {"content": [{"text": "Review ingredients; no actions taken."}]}},
            "usage": {"inputTokens": 100, "outputTokens": 30, "totalTokens": 130},
            "stopReason": "end_turn",
        }


def test_offline_never_constructs_aws_client_even_with_model_env(monkeypatch):
    monkeypatch.setenv("HESTIA_BEDROCK_MODEL_ID", "ambient-model")

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline mode must not resolve an AWS client")

    monkeypatch.setattr("hestiarelay.bedrock.boto3.client", forbidden)
    report = run_probe()
    assert report["converse_calls"] == 0
    assert report["planner_source"] == "deterministic"
    assert report["live_aws_validated"] is False


@pytest.mark.parametrize(
    "args", [{"live": True}, {"live": True, "approved": True}, {"live": True, "model_id": "model"}]
)
def test_live_gate_prevents_call(args):
    with pytest.raises(ValueError):
        run_probe(**args)


def test_injected_evidence_is_not_live_proof():
    report = run_probe(live=True, approved=True, model_id="test.model", client=FakeClient())
    assert report["status"] == "MOCK_PASS"
    assert report["live_aws_validated"] is False
    assert report["usage"]["totalTokens"] == 130
    assert report["usage_complete"]
    assert report["cost_usd"] is None
    assert report["credits_verified"] is False
    assert report["converse_calls"] == 1
    assert report["elapsed_ms"] >= 0
    assert report["evidence_complete"]
    assert report["phase2_complete"] is False
    assert report["evidence_errors"] == []
    assert len(report["request_sha256"]) == 64
    assert datetime.fromisoformat(report["invoked_at_utc"]).tzinfo is not None


def test_failure_never_becomes_live_pass():
    class FailingClient:
        def converse(self, **kwargs):
            raise NoCredentialsError()

    report = run_probe(live=True, approved=True, model_id="test.model", client=FailingClient())
    assert report["status"] == "BLOCKED"
    assert report["planner_source"] == "deterministic"
    assert report["converse_calls"] == 1


def test_client_discovery_failure_is_redacted(monkeypatch):
    def fail(*args, **kwargs):
        raise NoCredentialsError()

    monkeypatch.setattr("hestiarelay.bedrock.boto3.client", fail)
    report = run_probe(live=True, approved=True, model_id="test.model")
    assert report["status"] == "BLOCKED"
    assert report["converse_calls"] == 0
    assert "credentials" not in json.dumps(report).lower()


def test_one_call_ceiling():
    client = ObservedClient(FakeClient())
    kwargs = {"inferenceConfig": {"maxTokens": 600}}
    client.converse(**kwargs)
    with pytest.raises(ValueError, match="one Converse"):
        client.converse(**kwargs)


def test_cli_defaults_offline_and_live_flag_alone_fails(capsys, monkeypatch):
    monkeypatch.delenv("HESTIA_BEDROCK_MODEL_ID", raising=False)
    assert main([]) == 0
    assert json.loads(capsys.readouterr().out)["mode"] == "offline"
    assert main(["--live"]) == 2
    assert json.loads(capsys.readouterr().out)["converse_calls"] == 0


@pytest.mark.parametrize(
    "usage,stop_reason,error",
    [
        (None, "end_turn", "usage_missing_or_invalid"),
        ([], "end_turn", "usage_missing_or_invalid"),
        ({"inputTokens": 100, "outputTokens": 30}, "end_turn", "usage_missing_or_invalid"),
        (
            {"inputTokens": True, "outputTokens": 30, "totalTokens": 31},
            "end_turn",
            "usage_missing_or_invalid",
        ),
        (
            {"inputTokens": -1, "outputTokens": 30, "totalTokens": 29},
            "end_turn",
            "usage_missing_or_invalid",
        ),
        (
            {"inputTokens": "100", "outputTokens": 30, "totalTokens": 130},
            "end_turn",
            "usage_missing_or_invalid",
        ),
        (
            {"inputTokens": 100, "outputTokens": 30, "totalTokens": 999},
            "end_turn",
            "usage_total_mismatch",
        ),
        (
            {"inputTokens": 100, "outputTokens": 601, "totalTokens": 701},
            "end_turn",
            "output_limit_exceeded",
        ),
        (
            {"inputTokens": 100, "outputTokens": 30, "totalTokens": 130},
            "max_tokens",
            "completion_not_confirmed",
        ),
        (
            {"inputTokens": 100, "outputTokens": 30, "totalTokens": 130},
            "tool_use",
            "completion_not_confirmed",
        ),
        (
            {"inputTokens": 100, "outputTokens": 30, "totalTokens": 130},
            "guardrail_intervened",
            "completion_not_confirmed",
        ),
        (
            {"inputTokens": 100, "outputTokens": 30, "totalTokens": 130},
            None,
            "completion_not_confirmed",
        ),
    ],
)
def test_incomplete_evidence_never_passes(usage, stop_reason, error, monkeypatch):
    class IncompleteClient(FakeClient):
        calls = 0

        def converse(self, **kwargs):
            self.calls += 1
            return super().converse(**kwargs) | {"usage": usage, "stopReason": stop_reason}

    client = IncompleteClient()
    # Exercise the non-injected decision branch without real AWS credentials or traffic.
    monkeypatch.setattr("hestiarelay.bedrock.boto3.client", lambda *a, **kw: client)
    report = run_probe(live=True, approved=True, model_id="test.model")
    assert report["status"] == "EVIDENCE_INCOMPLETE"
    assert report["live_aws_validated"] is False
    assert report["evidence_complete"] is False
    assert error in report["evidence_errors"]
    assert client.calls == report["converse_calls"] == 1


def test_request_fingerprint_matches_actual_call_without_disclosing_text():
    class RecordingClient(FakeClient):
        def converse(self, **kwargs):
            self.request = kwargs
            return super().converse(**kwargs)

    client = RecordingClient()
    report = run_probe(live=True, approved=True, model_id="test.model", client=client)
    encoded = json.dumps(client.request, sort_keys=True, separators=(",", ":")).encode()
    assert report["request_sha256"] == hashlib.sha256(encoded).hexdigest()
    assert "Fictional dinner" not in json.dumps(report)
    assert "Review ingredients" not in json.dumps(report)


def test_cli_incomplete_evidence_returns_failure_without_retry(monkeypatch, capsys):
    class IncompleteClient(FakeClient):
        calls = 0

        def converse(self, **kwargs):
            self.calls += 1
            return super().converse(**kwargs) | {"usage": {}}

    client = IncompleteClient()
    monkeypatch.setattr("hestiarelay.bedrock.boto3.client", lambda *a, **kw: client)
    monkeypatch.setenv("HESTIA_BEDROCK_MODEL_ID", "test.model")
    assert main(["--live", "--approve-one-call"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "EVIDENCE_INCOMPLETE"
    assert client.calls == 1
