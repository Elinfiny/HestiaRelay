"""Real shared app boundaries: denials leave state and planner calls unchanged."""

import asyncio
import importlib
import secrets
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from hestiarelay.access import CHALLENGE, COOKIE, AccessConfig, JudgeAccess, digest
from hestiarelay.service import CANONICAL_MESSAGES
from hestiarelay.web import LocalBoundary

ORIGIN = "https://judge.example"


@pytest.fixture
def judge(tmp_path, monkeypatch):
    key = secrets.token_urlsafe(32)
    secret = tmp_path / "access.key"
    secret.write_text(key)
    secret.chmod(0o600)
    monkeypatch.setenv("HESTIA_ACCESS_MODE", "judge")
    monkeypatch.setenv("HESTIA_PUBLIC_ORIGIN", ORIGIN)
    monkeypatch.setenv("HESTIA_LOGIN_KEY_FILE", str(secret))
    monkeypatch.setenv("HESTIA_STATE_DB", str(tmp_path / "state.db"))
    monkeypatch.setenv("HESTIA_BEDROCK_MODEL_ID", "")
    module = importlib.reload(importlib.import_module("hestiarelay.server"))
    calls = []
    original = module.planner.generate_plan
    monkeypatch.setattr(
        module.planner, "generate_plan", lambda *a, **kw: (calls.append(1), original(*a, **kw))[1]
    )
    with TestClient(module.app, base_url=ORIGIN, follow_redirects=False) as client:
        yield module, client, key, calls


def login(client, key):
    csrf = client.get("/auth/session").json()["csrf_token"]
    response = client.post(
        "/auth/login", json={"key": key}, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}
    )
    assert response.status_code == 200, response.text
    client.headers.update({"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]})
    return response


def test_login_continuity_logout_and_revoked_replay(judge):
    module, client, key, calls = judge
    assert client.get("/").headers["location"] == "/login"
    assert client.get("/login").status_code == 200
    assert client.get("/static/login.js").status_code == 200
    response = login(client, key)
    cookies = response.headers.get_list("set-cookie")
    assert all("Secure" in c and "HttpOnly" in c and "SameSite=strict" in c for c in cookies)
    assert all("Domain=" not in c for c in cookies)
    assert key not in response.text and key not in repr(module.access_config)
    assert client.get("/login").headers["location"] == "/"
    for text in CANONICAL_MESSAGES:
        session = str(uuid4())
        assert client.post("/api/session", json={"session_id": session}).status_code == 200
        assert (
            client.post(
                "/api/message",
                json={"session_id": session, "request_id": str(uuid4()), "text": text},
            ).status_code
            == 200
        )
    state = client.get("/api/state").json()["state"]
    assert len(state["sessions"]) == 3 and state["preferences"][0]["person"] == "Ana"
    proposal = state["proposals"][0]
    assert (
        client.post(
            "/api/decision", json={"action_id": proposal["action_id"], "approved": True}
        ).status_code
        == 200
    )
    before = module.engine.store.path.read_bytes()
    old_cookie = client.cookies.get(COOKIE)
    assert client.post("/auth/logout", json={}).status_code == 200
    assert client.get("/api/state").status_code == 401
    client.cookies.set(COOKIE, old_cookie)
    assert client.get("/api/state").status_code == 401
    client.cookies.clear()
    login(client, key)
    assert module.engine.store.path.read_bytes() == before
    assert client.get("/api/state").json()["state"]["proposals"][0]["status"] == "approved"
    assert calls and client.get("/mcp").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/state",
        "/api/session",
        "/api/message",
        "/api/decision",
        "/mcp",
        "/mcp/",
        "/static/app.js",
    ],
)
def test_unauthenticated_no_state_or_planner_effect(judge, path):
    module, client, _, calls = judge
    before = module.engine.store.path.read_bytes()
    r = (
        client.get(path)
        if path in {"/api/state", "/static/app.js"}
        else client.post(path, json={}, headers={"Origin": ORIGIN})
    )
    assert r.status_code in {401, 404}
    assert module.engine.store.path.read_bytes() == before and not calls
    assert r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
        {"Host": "evil.example"},
        {"Host": "judge.example:443"},
        {"X-Forwarded-Host": "judge.example"},
        {"X-Forwarded-Proto": "https"},
        {"Forwarded": "host=judge.example;proto=https"},
        {"X-Real-IP": "127.0.0.1"},
        {"X-Remote-User": "owner"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Host": "judge.example:99999"},
        {"Host": "judge..example"},
    ],
)
def test_spoofed_ingress_denied_even_when_authenticated(judge, headers):
    module, client, key, calls = judge
    login(client, key)
    before = module.engine.store.path.read_bytes()
    assert client.get("/api/state", headers=headers).status_code == 403
    assert module.engine.store.path.read_bytes() == before and not calls


@pytest.mark.parametrize(
    "headers",
    [
        [("Host", "evil.example"), ("Host", "judge.example")],
        [("Origin", "https://evil.example"), ("Origin", ORIGIN)],
        [("Cookie", "x=y"), ("Cookie", "z=y")],
        [("X-CSRF-Token", "a"), ("X-CSRF-Token", "b")],
        [("Host", "judge.example\t")],
    ],
)
def test_raw_duplicate_headers_fail_before_app(judge, headers):
    module, _, _, calls = judge
    messages = []
    raw = [(k.lower().encode(), v.encode()) for k, v in headers]
    if not any(k == b"host" for k, _ in raw):
        raw.append((b"host", b"judge.example"))

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(msg):
        messages.append(msg)

    asyncio.run(
        module.app(
            {
                "type": "http",
                "headers": raw,
                "scheme": "https",
                "path": "/api/state",
                "method": "GET",
            },
            receive,
            send,
        )
    )
    assert messages[0]["status"] == 403 and not calls


def test_csrf_http_query_and_method_boundaries(judge):
    module, client, key, calls = judge
    login(client, key)
    before = module.engine.store.path.read_bytes()
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/session", json={"session_id": str(uuid4())}).status_code == 403
    assert client.post("/auth/logout", json={}).status_code == 403
    client.headers["X-CSRF-Token"] = secrets.token_urlsafe(32)
    assert client.post("/api/session", json={}).status_code == 403
    client.headers.pop("Origin")
    assert client.post("/api/session", json={}).status_code == 403
    assert client.get("/api/state?key=redacted").status_code == 400
    assert client.get("/auth/logout").status_code == 404
    assert client.get("http://judge.example/api/state").status_code == 403
    assert module.engine.store.path.read_bytes() == before and not calls


def test_expiry_rotation_and_restart_revoke_sessions(judge):
    module, client, key, _ = judge
    clock = [100.0]
    module.app.access.clock = lambda: clock[0]
    login(client, key)
    old = client.cookies.get(COOKIE)
    clock[0] += 900
    assert client.get("/api/state").status_code == 401
    login(client, key)
    assert client.cookies.get(COOKIE) != old
    # Absolute expiry despite periodic activity.
    for _ in range(4):
        clock[0] += 800
        assert client.get("/api/state").status_code == 200
    clock[0] += 400
    assert client.get("/api/state").status_code == 401
    login(client, key)
    module.app.access = JudgeAccess(module.access_config)
    assert client.get("/api/state").status_code == 401


@pytest.mark.parametrize(
    "payload", [{"key": "wrong"}, {"key": 1}, {}, [], {"key": "x", "extra": True}, "bad"]
)
def test_invalid_login_has_no_effect(judge, payload):
    module, client, _, calls = judge
    csrf = client.get("/auth/session").json()["csrf_token"]
    assert (
        client.post(
            "/auth/login", json=payload, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}
        ).status_code
        == 401
    )
    assert not module.app.access.sessions and not calls


def test_login_body_challenge_and_rate_limit(judge):
    module, client, key, _ = judge
    assert (
        client.post("/auth/login", json={"key": key}, headers={"Origin": ORIGIN}).status_code == 403
    )
    csrf = client.get("/auth/session").json()["csrf_token"]
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    assert client.post("/auth/login", content="{}", headers=headers).status_code == 415
    headers["Content-Type"] = "application/json"
    assert client.post("/auth/login", content="{", headers=headers).status_code == 401
    assert client.post("/auth/login", content="x" * 1025, headers=headers).status_code == 413
    for _ in range(20):
        r = client.post("/auth/login", json={"key": "wrong"}, headers=headers)
    assert r.status_code == 429 and r.headers["retry-after"] == "60"
    module.app.access.clock = lambda: __import__("time").monotonic() + 61
    assert client.post("/auth/login", json={"key": key}, headers=headers).status_code == 200
    assert client.get("/health").json() == {"status": "ok", "service": "hestiarelay"}


def test_challenge_expiry_and_duplicate_cookie(judge):
    module, client, key, _ = judge
    csrf = client.get("/auth/session").json()["csrf_token"]
    module.app.access.clock = lambda: __import__("time").monotonic() + 301
    assert (
        client.post(
            "/auth/login", json={"key": key}, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}
        ).status_code
        == 403
    )
    login(client, key)
    token = client.cookies.get(COOKIE)
    assert (
        client.get(
            "/api/state", headers={"Cookie": f"{COOKIE}={token}; {COOKIE}={token}"}
        ).status_code
        == 401
    )
    assert not client.cookies.get(CHALLENGE)


@pytest.mark.parametrize(
    "origin",
    [
        "http://judge.example",
        "https://judge.example/",
        "https://judge.example/path",
        "https://user@judge.example",
        "https://*.example",
        "https://judge.example#x",
        "https://judge.example:0",
        "https://judge.example:65536",
    ],
)
def test_invalid_deployment_config_fails_closed(monkeypatch, origin):
    monkeypatch.setenv("HESTIA_ACCESS_MODE", "judge")
    monkeypatch.setenv("HESTIA_PUBLIC_ORIGIN", origin)
    with pytest.raises(ValueError):
        AccessConfig.from_env()


def test_key_and_mode_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("HESTIA_ACCESS_MODE", "unknown")
    with pytest.raises(ValueError):
        AccessConfig.from_env()
    monkeypatch.setenv("HESTIA_ACCESS_MODE", "local")
    assert AccessConfig.from_env() is None
    monkeypatch.setenv("HESTIA_ACCESS_MODE", "judge")
    monkeypatch.setenv("HESTIA_PUBLIC_ORIGIN", ORIGIN)
    monkeypatch.setenv("HESTIA_LOGIN_KEY_FILE", "relative")
    with pytest.raises(ValueError):
        AccessConfig.from_env()
    p = tmp_path / "key"
    p.write_text(secrets.token_urlsafe(32))
    p.chmod(0o644)
    monkeypatch.setenv("HESTIA_LOGIN_KEY_FILE", str(p))
    with pytest.raises(ValueError):
        AccessConfig.from_env()
    p.chmod(0o600)
    for raw in [b"short", b"\xff" * 43, b"a" * 130]:
        p.write_bytes(raw)
        with pytest.raises(ValueError):
            AccessConfig.from_env()
    p.write_text(secrets.token_urlsafe(32))
    assert AccessConfig.from_env().key_digest == digest(p.read_text())
    link = tmp_path / "link"
    link.symlink_to(p)
    monkeypatch.setenv("HESTIA_LOGIN_KEY_FILE", str(link))
    with pytest.raises(OSError):
        AccessConfig.from_env()


def test_websocket_denied():
    messages = []

    async def send(msg):
        messages.append(msg)

    asyncio.run(LocalBoundary(None)({"type": "websocket"}, None, send))
    assert messages == [{"type": "websocket.close", "code": 1008}]
