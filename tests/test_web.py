from __future__ import annotations

import importlib
import json
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from hestiarelay.service import CANONICAL_MESSAGES


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("HESTIA_STATE_DB", str(tmp_path / "web.db"))
    monkeypatch.delenv("HESTIA_BEDROCK_MODEL_ID", raising=False)
    return importlib.reload(importlib.import_module("hestiarelay.server"))


@pytest.fixture
def client(server):
    with TestClient(server.app, base_url="http://127.0.0.1") as client:
        yield client


def test_browser_api_canonical_flow_and_exact_consent(client):
    snapshots = []
    for text in CANONICAL_MESSAGES:
        session = str(uuid4())
        assert client.post("/api/session", json={"session_id": session}).status_code == 200
        response = client.post(
            "/api/message", json={"session_id": session, "request_id": str(uuid4()), "text": text}
        )
        assert response.status_code == 200
        snapshots.append(response.json())
    assert len({s["state"]["goal"]["goal_id"] for s in snapshots}) == 1
    proposal = snapshots[-1]["state"]["proposals"][0]
    rejected = client.post(
        "/api/decision", json={"action_id": proposal["action_id"], "approved": False}
    )
    assert rejected.json()["state"]["proposals"][0]["status"] == "rejected"
    assert rejected.json()["external_actions_performed"] == 0
    assert client.get("/api/state").json() == rejected.json()
    assert client.get("/health").json()["transport"] == "streamable-http"


@pytest.mark.parametrize("path", ["/", "/static/app.js", "/static/style.css", "/static/mark.svg"])
def test_packaged_assets_and_security_headers(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert len(response.content) > 100
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_asset_allowlist_and_mobile_accessibility_contract(client):
    assert client.get("/static/secret.txt").status_code == 404
    html = client.get("/").text
    assert 'name="viewport"' in html
    assert 'aria-live="polite"' in html
    assert 'label for="message"' in html
    assert "even after approval" in html
    assert "max-width:720px" in client.get("/static/style.css").text
    assert "innerHTML" not in client.get("/static/app.js").text


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://untrusted.example"},
        {"Origin": "null"},
        {"Host": "untrusted.example"},
        {"Host": "localhost.attacker.example"},
    ],
)
def test_origin_and_dns_rebinding_blocked(client, headers):
    assert client.get("/api/state", headers=headers).status_code == 403


def test_same_origin_is_accepted(client):
    assert client.get("/api/state", headers={"Origin": "http://127.0.0.1"}).status_code == 200


def test_invalid_inputs_cannot_authorize_action(client):
    assert client.post("/api/session", content="{}").status_code == 415
    assert (
        client.post(
            "/api/session", content="{" * 5000, headers={"content-type": "application/json"}
        ).status_code
        == 413
    )
    assert client.post("/api/session", json={"session_id": "bad"}).status_code == 422
    assert (
        client.post(
            "/api/decision", json={"action_id": str(uuid4()), "approved": "false"}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/decision", json={"action_id": str(uuid4()), "approved": True}).status_code
        == 404
    )
    assert (
        client.post(
            "/api/message",
            json={"session_id": str(uuid4()), "request_id": str(uuid4()), "text": "hi"},
        ).status_code
        == 404
    )
    session = str(uuid4())
    client.post("/api/session", json={"session_id": session})
    assert (
        client.post(
            "/api/message",
            json={"session_id": session, "request_id": str(uuid4()), "text": "Buy now"},
        ).status_code
        == 409
    )


def test_mcp_and_http_share_domain_state(server, client):
    initial = json.loads(server.start_household_goal("Dinner", "Friday", 6, 120))
    server.remember_household_preference("Ana", "Nut allergy")
    assert "Ana" in server.get_continuity_brief()
    assert json.loads(server.generate_household_plan())["source"] == "deterministic"
    proposal = json.loads(
        server.propose_household_action(
            "calendar_write", "Draft guest reminder", '{"recipient":"fictional guest"}'
        )
    )
    assert client.get("/api/state").json()["state"]["goal"]["goal_id"] == initial["goal"]["goal_id"]
    result = client.post(
        "/api/decision", json={"action_id": proposal["action_id"], "approved": True}
    )
    assert result.json()["state"]["proposals"][0]["risk"] == "review"
    assert (
        json.loads(server.decide_sensitive_action(proposal["action_id"], True))["status"]
        == "approved"
    )
    with pytest.raises(ValueError):
        server.propose_household_action("purchase", "Invalid payload", "[]")
    session = str(uuid4())
    server.start_simulator_session(session)
    reply = server.send_simulator_message(session, str(uuid4()), CANONICAL_MESSAGES[2])
    assert reply["state"]["goal"]["goal_id"] == initial["goal"]["goal_id"]
    assert len(client.get("/api/state").json()["state"]["turns"]) == 1
