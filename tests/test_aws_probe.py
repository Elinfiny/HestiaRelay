import json

import pytest
from botocore.exceptions import NoCredentialsError

from hestiarelay.aws_probe import ObservedClient, main, run_probe


class FakeClient:
    def converse(self, **kwargs):
        assert kwargs["inferenceConfig"]["maxTokens"] == 600
        return {
            "output": {"message": {"content": [{"text": "Review ingredients; no actions taken."}]}},
            "usage": {"inputTokens": 100, "outputTokens": 30, "totalTokens": 130},
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
